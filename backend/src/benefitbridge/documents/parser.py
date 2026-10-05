"""Bounded digital PDF adapter (R03.01/03/04); no OCR, files, or provider calls.

Call parse_pdf outside a database transaction (or await asyncio.to_thread).
The subprocess receives raw bytes over stdin and returns only bounded page text.
Linux uses RLIMIT_AS; Windows uses a process-memory Job Object. Failure to install
the OS limit fails closed before PDF bytes are read. These resource limits are
not a substitute for the deployment worker's OS/container security sandbox.
"""

import ctypes
import json
import logging
import math
import os
import re
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from enum import StrEnum
from hashlib import sha256
from io import BytesIO
from pathlib import Path
from unicodedata import category
from uuid import UUID

from pydantic import ValidationError

from benefitbridge.domain.enums import DocumentQuality
from benefitbridge.domain.errors import DomainError
from benefitbridge.sources.contracts import (
    PAGE_SEPARATOR,
    DocumentText,
    NormalizedText,
    normalize_pages,
    normalize_text,
)

PARSER_VERSION = "pdf-v1/pypdf-6.19.0/nfc-lf-v1"
MIB = 1024 * 1024
# Win32 CREATE_NO_WINDOW; subprocess exposes the named flag only on Windows.
_WINDOWS_NO_CONSOLE = 0x08000000


@dataclass(frozen=True)
class PdfLimits:
    """Explicit per-invocation limits may tighten, never exceed the P0 caps."""

    max_bytes: int = 10 * MIB
    max_pages: int = 20
    timeout_seconds: float = 30.0
    memory_bytes: int = 512 * MIB
    max_text_chars: int = 200_000
    max_stream_bytes: int = 8 * MIB
    max_decoded_bytes: int = 32 * MIB

    def __post_init__(self) -> None:
        for value, maximum in (
            (self.max_bytes, 10 * MIB),
            (self.max_pages, 20),
            (self.memory_bytes, 512 * MIB),
            (self.max_text_chars, 200_000),
            (self.max_stream_bytes, 32 * MIB),
            (self.max_decoded_bytes, 64 * MIB),
        ):
            if type(value) is not int or not 0 < value <= maximum:
                raise ValueError("PDF limits must be positive integers within the P0 caps")
        if self.memory_bytes < 64 * MIB:
            raise ValueError("PDF subprocess requires at least 64 MiB")
        if (
            isinstance(self.timeout_seconds, bool)
            or not math.isfinite(self.timeout_seconds)
            or not 0 < self.timeout_seconds <= 30
        ):
            raise ValueError("PDF timeout must be positive and at most 30 seconds")


class PdfFailure(StrEnum):
    MEDIA_TYPE = "MEDIA_TYPE"
    BYTE_LIMIT = "BYTE_LIMIT"
    CONTENT_MISMATCH = "CONTENT_MISMATCH"
    MALFORMED = "MALFORMED"
    ENCRYPTED = "ENCRYPTED"
    PAGE_LIMIT = "PAGE_LIMIT"
    DECOMPRESSION_LIMIT = "DECOMPRESSION_LIMIT"
    TEXT_LIMIT = "TEXT_LIMIT"
    MEMORY_LIMIT = "MEMORY_LIMIT"
    TIME_LIMIT = "TIME_LIMIT"
    ISOLATION_UNAVAILABLE = "ISOLATION_UNAVAILABLE"
    WORKER_FAILED = "WORKER_FAILED"


class PdfParseError(DomainError):
    """Internal reason is stable; HTTP adapters reuse the common error family."""

    def __init__(self, reason: PdfFailure) -> None:
        self.reason = reason
        code, status, message = {
            PdfFailure.MEDIA_TYPE: ("UNSUPPORTED_MEDIA_TYPE", 415, "Upload a digital PDF."),
            PdfFailure.BYTE_LIMIT: ("PAYLOAD_TOO_LARGE", 413, "PDF exceeds the byte limit."),
            PdfFailure.PAGE_LIMIT: ("PAYLOAD_TOO_LARGE", 413, "PDF exceeds the page limit."),
            PdfFailure.CONTENT_MISMATCH: ("CONTENT_MISMATCH", 422, "Content is not a PDF."),
            PdfFailure.MALFORMED: ("CONTENT_MISMATCH", 422, "PDF structure is invalid."),
            PdfFailure.ENCRYPTED: ("CONTENT_MISMATCH", 422, "Encrypted PDFs are unsupported."),
            PdfFailure.DECOMPRESSION_LIMIT: (
                "CONTENT_MISMATCH",
                422,
                "PDF exceeds the decoded content limit.",
            ),
            PdfFailure.TEXT_LIMIT: ("CONTENT_MISMATCH", 422, "PDF exceeds the text limit."),
            PdfFailure.MEMORY_LIMIT: ("CONTENT_MISMATCH", 422, "PDF exceeds the memory limit."),
            PdfFailure.TIME_LIMIT: ("CONTENT_MISMATCH", 422, "PDF exceeds the parsing time limit."),
            PdfFailure.ISOLATION_UNAVAILABLE: (
                "DEPENDENCY_UNAVAILABLE",
                503,
                "Bounded PDF parsing is unavailable.",
            ),
            PdfFailure.WORKER_FAILED: ("INTERNAL_ERROR", 500, "PDF parsing did not complete."),
        }[reason]
        super().__init__(code, message, status, reason == PdfFailure.ISOLATION_UNAVAILABLE)


@dataclass(frozen=True)
class ParsedPdf:
    normalized: NormalizedText = field(repr=False)
    raw_file_hash: str
    quality: DocumentQuality
    unreadable_pages: tuple[int, ...]
    parser_version: str = PARSER_VERSION

    @property
    def page_count(self) -> int:
        return len(self.normalized.pages)

    def document_text(self, document_id: UUID, document_version_id: UUID) -> DocumentText:
        """Ingestion binds trusted immutable IDs, never caller-supplied ownership."""
        return DocumentText(
            document_id=document_id,
            document_version_id=document_version_id,
            normalized=self.normalized,
            raw_file_hash=self.raw_file_hash,
        )


def _command(limits: PdfLimits) -> list[str]:
    # -I ignores PYTHONPATH/site user customizations; only our trusted package is added.
    bootstrap = (
        "import sys; sys.path.insert(0, sys.argv[1]); "
        "from benefitbridge.documents.parser import _worker_main; _worker_main()"
    )
    return [
        sys.executable,
        "-I",
        "-c",
        bootstrap,
        str(Path(__file__).resolve().parents[2]),
        json.dumps(asdict(limits)),
    ]


def _unreadable(text: str) -> bool:
    visible = [char for char in text if not char.isspace()]
    if not visible or not any(char.isalpha() for char in visible):
        return True
    corrupt = sum(char == "\ufffd" or category(char) in {"Cc", "Cs", "Co"} for char in visible)
    return corrupt * 10 >= len(visible) or re.search(r"\(cid:\d+\)", text) is not None


def parse_pdf(data: bytes, *, content_type: str, limits: PdfLimits | None = None) -> ParsedPdf:
    """Never trust MIME alone; no repaired/truncated extraction is a success.

    Empty or corrupt text retains page identity and MANUAL_ENTRY_REQUIRED quality;
    it cannot be advertised as completely readable or silently OCR'd. Quality is
    a conservative extraction signal, not proof of a document's authenticity.
    """
    limits = limits if limits is not None else PdfLimits()
    if not isinstance(data, bytes):
        raise TypeError("PDF input must be immutable bytes")
    if content_type.strip().lower() != "application/pdf":
        raise PdfParseError(PdfFailure.MEDIA_TYPE)
    if len(data) > limits.max_bytes:
        raise PdfParseError(PdfFailure.BYTE_LIMIT)
    if not re.match(rb"%PDF-(?:1\.[0-7]|2\.0)(?:\r\n|\r|\n)", data):
        raise PdfParseError(PdfFailure.CONTENT_MISMATCH)
    # Do not persist applicant input or pass environment credentials to the parser.
    environment = {key: os.environ[key] for key in ("SystemRoot",) if key in os.environ}
    try:
        process = subprocess.Popen(
            _command(limits),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            env=environment,
            close_fds=True,
            creationflags=_WINDOWS_NO_CONSOLE if sys.platform == "win32" else 0,
        )
    except OSError:
        raise PdfParseError(PdfFailure.ISOLATION_UNAVAILABLE) from None
    try:
        output, _ = process.communicate(data, timeout=limits.timeout_seconds)
    except subprocess.TimeoutExpired:
        process.kill()
        process.communicate()
        raise PdfParseError(PdfFailure.TIME_LIMIT) from None
    finally:
        if process.poll() is None:
            process.kill()
            process.wait()
    if process.returncode != 0 or len(output) > limits.max_text_chars * 12 + 4096:
        raise PdfParseError(PdfFailure.WORKER_FAILED)
    try:
        result = json.loads(output)
        if not isinstance(result, dict):
            raise ValueError
        if set(result) == {"failure"}:
            raise PdfParseError(PdfFailure(result["failure"]))
        pages = result.get("pages")
        if (
            set(result) != {"pages"}
            or not isinstance(pages, list)
            or not 1 <= len(pages) <= limits.max_pages
            or not all(isinstance(page, str) for page in pages)
            or sum(len(page) for page in pages) > limits.max_text_chars
        ):
            raise ValueError
        normalized = normalize_pages(pages)
        if len(normalized.text) > limits.max_text_chars:
            raise PdfParseError(PdfFailure.TEXT_LIMIT)
    except (ValueError, TypeError, ValidationError):
        raise PdfParseError(PdfFailure.WORKER_FAILED) from None
    unreadable = tuple(
        marker.page for marker in normalized.pages if _unreadable(normalized.page_text(marker.page))
    )
    return ParsedPdf(
        normalized,
        sha256(data).hexdigest(),
        DocumentQuality.MANUAL_ENTRY_REQUIRED if unreadable else DocumentQuality.READABLE,
        unreadable,
    )


def _windows_memory_limit(memory_bytes: int) -> int:
    """Keep the returned job handle open for the child's lifetime (Win32 contract)."""
    if sys.platform != "win32":
        raise OSError("Windows Job Objects require Windows")
    from ctypes import wintypes

    class BasicLimits(ctypes.Structure):
        _fields_ = [
            ("process_time", ctypes.c_int64),
            ("job_time", ctypes.c_int64),
            ("flags", wintypes.DWORD),
            ("min_working_set", ctypes.c_size_t),
            ("max_working_set", ctypes.c_size_t),
            ("active_processes", wintypes.DWORD),
            ("affinity", ctypes.c_size_t),
            ("priority", wintypes.DWORD),
            ("scheduling", wintypes.DWORD),
        ]

    class IoCounters(ctypes.Structure):
        _fields_ = [
            (name, ctypes.c_uint64)
            for name in (
                "read_ops",
                "write_ops",
                "other_ops",
                "read_bytes",
                "write_bytes",
                "other_bytes",
            )
        ]

    class ExtendedLimits(ctypes.Structure):
        _fields_ = [
            ("basic", BasicLimits),
            ("io", IoCounters),
            ("process_memory", ctypes.c_size_t),
            ("job_memory", ctypes.c_size_t),
            ("peak_process_memory", ctypes.c_size_t),
            ("peak_job_memory", ctypes.c_size_t),
        ]

    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
    kernel.CreateJobObjectW.restype = wintypes.HANDLE
    kernel.GetCurrentProcess.restype = wintypes.HANDLE
    kernel.SetInformationJobObject.argtypes = [
        wintypes.HANDLE,
        ctypes.c_int,
        ctypes.c_void_p,
        wintypes.DWORD,
    ]
    kernel.SetInformationJobObject.restype = wintypes.BOOL
    kernel.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
    kernel.AssignProcessToJobObject.restype = wintypes.BOOL
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    handle = kernel.CreateJobObjectW(None, None)
    if not handle:
        raise OSError("Job Object unavailable")
    info = ExtendedLimits()
    # JOB_OBJECT_LIMIT_PROCESS_MEMORY | JOB_OBJECT_LIMIT_ACTIVE_PROCESS.
    info.basic.flags = 0x100 | 0x8
    info.basic.active_processes = 1
    info.process_memory = memory_bytes
    if not kernel.SetInformationJobObject(
        handle, 9, ctypes.byref(info), ctypes.sizeof(info)
    ) or not (kernel.AssignProcessToJobObject(handle, kernel.GetCurrentProcess())):
        kernel.CloseHandle(handle)
        raise OSError("Job Object limits unavailable")
    return int(handle)


def _apply_resource_limits(limits: PdfLimits) -> int | None:
    if sys.platform == "win32":
        return _windows_memory_limit(limits.memory_bytes)
    if sys.platform != "linux":
        raise OSError("PDF resource limits are not supported on this platform")
    import resource

    resource.setrlimit(resource.RLIMIT_AS, (limits.memory_bytes, limits.memory_bytes))
    seconds = math.ceil(limits.timeout_seconds)
    resource.setrlimit(resource.RLIMIT_CPU, (seconds, seconds))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    resource.setrlimit(resource.RLIMIT_FSIZE, (0, 0))
    return None


def _deny_external_access(event: str, args: tuple[object, ...]) -> None:
    if event.startswith(("socket.", "subprocess.", "os.exec", "os.spawn")) or event in {
        "os.system",
        "os.posix_spawn",
        "os.fork",
        "os.forkpty",
    }:
        raise PermissionError("PDF child cannot contact providers or launch processes")


def _extract_pages(data: bytes, limits: PdfLimits) -> list[str]:
    # Import only after the OS resource limits are installed in the isolated child.
    from pypdf import PdfReader, overwrite_configuration

    overwrite_configuration(
        maximum_declared_stream_length=limits.max_stream_bytes,
        array_based_stream_maximum_output_length=limits.max_stream_bytes,
        zlib_maximum_output_length=limits.max_stream_bytes,
        zlib_maximum_recovery_input_length=limits.max_bytes,
        lzw_maximum_output_length=limits.max_stream_bytes,
        run_length_maximum_output_length=limits.max_stream_bytes,
        jbig2_maximum_output_length=limits.max_stream_bytes,
        image_maximum_buffer_size=limits.max_stream_bytes,
        jbig2dec_binary=None,
        page_tree_maximum_entries=128,
        page_tree_maximum_depth=32,
        xform_maximum_invocations_per_extraction=1000,
    )
    reader = PdfReader(BytesIO(data), strict=True)
    try:
        if reader.is_encrypted:
            raise PdfParseError(PdfFailure.ENCRYPTED)
        count = len(reader.pages)
        if count > limits.max_pages:
            raise PdfParseError(PdfFailure.PAGE_LIMIT)
        if count == 0:
            raise PdfParseError(PdfFailure.MALFORMED)
        pages: list[str] = []
        chars = decoded = 0
        for page in reader.pages:
            contents = page.get_contents()
            decoded += len(contents.get_data()) if contents is not None else 0
            if decoded > limits.max_decoded_bytes:
                raise PdfParseError(PdfFailure.DECOMPRESSION_LIMIT)
            text = normalize_text(page.extract_text())
            chars += len(text) + (len(PAGE_SEPARATOR) if pages else 0)
            if chars > limits.max_text_chars:
                raise PdfParseError(PdfFailure.TEXT_LIMIT)
            pages.append(text)
        return pages
    finally:
        reader.close()


def _worker_main() -> None:
    logging.disable(logging.CRITICAL)
    limits = PdfLimits(**json.loads(sys.argv[2]))
    try:
        # The handle stays live until process exit; no applicant input is read yet.
        job_handle = _apply_resource_limits(limits)
    except (OSError, ValueError):
        sys.stdout.write(json.dumps({"failure": PdfFailure.ISOLATION_UNAVAILABLE}))
        return
    sys.dont_write_bytecode = True
    sys.addaudithook(_deny_external_access)
    from pypdf.errors import LimitReachedError, PyPdfError

    result: dict[str, list[str] | PdfFailure]
    try:
        data = sys.stdin.buffer.read(limits.max_bytes + 1)
        if len(data) > limits.max_bytes:
            raise PdfParseError(PdfFailure.BYTE_LIMIT)
        result = {"pages": _extract_pages(data, limits)}
    except PdfParseError as error:
        result = {"failure": error.reason}
    except LimitReachedError:
        result = {"failure": PdfFailure.DECOMPRESSION_LIMIT}
    except MemoryError:
        result = {"failure": PdfFailure.MEMORY_LIMIT}
    except (
        PyPdfError,
        ValueError,
        TypeError,
        KeyError,
        IndexError,
        RecursionError,
        UnicodeError,
        NotImplementedError,
    ):
        result = {"failure": PdfFailure.MALFORMED}
    sys.stdout.write(json.dumps(result, ensure_ascii=True))
    sys.stdout.flush()
    # Do not close the Windows job early; OS teardown releases the handle.
    del job_handle
