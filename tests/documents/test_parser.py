"""Synthetic PDF structure, provenance and OS-process boundary regressions."""

import json
import sys
import zlib
from hashlib import sha256
from io import BytesIO
from pathlib import Path
from uuid import UUID

import pytest
from pypdf import PdfWriter
from pypdf.generic import (
    DecodedStreamObject,
    DictionaryObject,
    EncodedStreamObject,
    NameObject,
    NumberObject,
)

from benefitbridge.documents import parser
from benefitbridge.documents.parser import (
    MIB,
    PdfFailure,
    PdfLimits,
    PdfParseError,
    parse_pdf,
)
from benefitbridge.domain.enums import DocumentQuality
from benefitbridge.sources.contracts import PAGE_SEPARATOR, normalized_text_hash


def pdf(
    pages: list[str | None],
    *,
    encrypted: bool = False,
    compressed: bytes | None = None,
    scanned: bool = False,
    unicode_text: bool = False,
) -> bytes:
    writer = PdfWriter()
    for text in pages:
        page = writer.add_blank_page(width=612, height=792)
        font = DictionaryObject(
            {
                NameObject("/Type"): NameObject("/Font"),
                NameObject("/Subtype"): NameObject("/Type1"),
                NameObject("/BaseFont"): NameObject("/Helvetica"),
            }
        )
        if unicode_text:
            cmap = DecodedStreamObject()
            cmap.set_data(b"""/CIDInit /ProcSet findresource begin
12 dict begin begincmap
/CIDSystemInfo << /Registry (Synthetic) /Ordering (Unicode) /Supplement 0 >> def
/CMapName /Synthetic def /CMapType 2 def
1 begincodespacerange <00> <ff> endcodespacerange
5 beginbfchar
<01> <0043> <02> <0061> <03> <0066> <04> <00650301> <05> <D83DDE80>
endbfchar endcmap CMapName currentdict /CMap defineresource pop end end
""")
            font[NameObject("/ToUnicode")] = writer._add_object(cmap)
        page[NameObject("/Resources")] = DictionaryObject(
            {NameObject("/Font"): DictionaryObject({NameObject("/F1"): writer._add_object(font)})}
        )
        if text is not None:
            if compressed is None:
                stream = DecodedStreamObject()
                encoded_text = (
                    b"<0102030405>"
                    if unicode_text
                    else (
                        b"("
                        + text.encode("ascii")
                        .replace(b"\\", b"\\\\")
                        .replace(b"(", b"\\(")
                        .replace(b")", b"\\)")
                        + b")"
                    )
                )
                stream.set_data(b"BT /F1 12 Tf 72 720 Td " + encoded_text + b" Tj ET")
            else:
                stream = EncodedStreamObject()
                stream._data = compressed
                stream[NameObject("/Filter")] = NameObject("/FlateDecode")
            page[NameObject("/Contents")] = writer._add_object(stream)
        if scanned:
            image = DecodedStreamObject()
            image.set_data(b"\x00\x00\x00")
            image.update(
                {
                    NameObject("/Type"): NameObject("/XObject"),
                    NameObject("/Subtype"): NameObject("/Image"),
                    NameObject("/Width"): NumberObject(1),
                    NameObject("/Height"): NumberObject(1),
                    NameObject("/ColorSpace"): NameObject("/DeviceRGB"),
                    NameObject("/BitsPerComponent"): NumberObject(8),
                }
            )
            page[NameObject("/Resources")][NameObject("/XObject")] = DictionaryObject(
                {NameObject("/Im1"): writer._add_object(image)}
            )
            content = DecodedStreamObject()
            content.set_data(b"q 100 0 0 100 0 0 cm /Im1 Do Q")
            page[NameObject("/Contents")] = writer._add_object(content)
    if encrypted:
        writer.encrypt("")  # Even empty-password encrypted documents are unsupported.
    target = BytesIO()
    writer.write(target)
    writer.close()
    return target.getvalue()


def failure(data: bytes, reason: PdfFailure, **options: object) -> PdfParseError:
    with pytest.raises(PdfParseError) as caught:
        parse_pdf(data, content_type="application/pdf", **options)
    assert caught.value.reason == reason
    assert data[:100].decode("ascii", errors="ignore") not in str(caught.value)
    return caught.value


def test_twenty_pages_preserve_page_identity_and_hashes():
    raw = pdf([f"Synthetic English page {page}" for page in range(1, 21)])
    parsed = parse_pdf(raw, content_type="application/pdf")
    assert parsed.page_count == 20
    assert parsed.quality == DocumentQuality.READABLE
    assert parsed.unreadable_pages == ()
    assert parsed.raw_file_hash == sha256(raw).hexdigest()
    assert parsed.raw_file_hash != parsed.normalized.normalized_text_hash
    assert parsed.normalized.text == PAGE_SEPARATOR.join(
        f"Synthetic English page {page}" for page in range(1, 21)
    )
    for marker in parsed.normalized.pages:
        text = parsed.normalized.page_text(marker.page)
        assert parsed.normalized.text[marker.start : marker.end] == text
        assert marker.normalized_text_hash == normalized_text_hash(text)


def test_twenty_one_pages_are_rejected():
    error = failure(pdf(["Synthetic page"] * 21), PdfFailure.PAGE_LIMIT)
    assert error.status == 413 and error.code == "PAYLOAD_TOO_LARGE"


@pytest.mark.parametrize(
    "media_type",
    ["text/html", "image/png", "application/octet-stream", "application/pdf; charset=utf-8"],
)
def test_wrong_content_type_is_rejected(media_type):
    with pytest.raises(PdfParseError) as caught:
        parse_pdf(pdf(["Synthetic"]), content_type=media_type)
    assert caught.value.reason == PdfFailure.MEDIA_TYPE
    assert caught.value.status == 415


@pytest.mark.parametrize("data", [b"", b"<html>private synthetic text</html>", b"%PDF-forged\n"])
def test_forged_pdf_type_is_rejected(data):
    with pytest.raises(PdfParseError) as caught:
        parse_pdf(data, content_type="application/pdf")
    assert caught.value.reason == PdfFailure.CONTENT_MISMATCH


def test_byte_limit_checked_before_launch(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("Oversized inputs must not launch a parser")

    monkeypatch.setattr(parser.subprocess, "Popen", forbidden)
    limits = PdfLimits(max_bytes=10)
    failure(b"%PDF-1.3\n" + b" " * 2, PdfFailure.BYTE_LIMIT, limits=limits)


def test_exact_byte_boundary():
    raw = pdf(["Synthetic English"])
    assert (
        parse_pdf(
            raw, content_type="application/pdf", limits=PdfLimits(max_bytes=len(raw))
        ).page_count
        == 1
    )
    failure(raw, PdfFailure.BYTE_LIMIT, limits=PdfLimits(max_bytes=len(raw) - 1))


@pytest.mark.parametrize(
    "data", [b"%PDF-1.3\nnot a real document\n%%EOF\n", pdf(["Synthetic"])[:-50], pdf([])]
)
def test_malformed_and_truncated_pdfs_are_not_repaired(data):
    failure(data, PdfFailure.MALFORMED)


def test_encrypted_pdf_rejected_even_when_empty_password_unlocks_it():
    failure(pdf(["Synthetic"], encrypted=True), PdfFailure.ENCRYPTED)


@pytest.mark.parametrize("scanned", [False, True])
def test_blank_or_scanned_pdf_requires_manual_entry(scanned):
    parsed = parse_pdf(pdf([None], scanned=scanned), content_type="application/pdf")
    assert parsed.quality == DocumentQuality.MANUAL_ENTRY_REQUIRED
    assert parsed.normalized.text == ""
    assert parsed.unreadable_pages == (1,)
    assert parsed.normalized.pages[0].start == parsed.normalized.pages[0].end == 0


def test_blank_middle_page_is_not_renumbered_or_claimed_readable():
    parsed = parse_pdf(
        pdf(["First English page", None, "Third English page"]), content_type="application/pdf"
    )
    assert parsed.unreadable_pages == (2,)
    assert parsed.quality == DocumentQuality.MANUAL_ENTRY_REQUIRED
    assert parsed.normalized.page_text(3) == "Third English page"


def test_unicode_evidence_round_trip_is_page_local_and_normalized():
    parsed = parse_pdf(pdf(["Synthetic"], unicode_text=True), content_type="application/pdf")
    assert parsed.normalized.text == "Caf\u00e9\U0001f680"
    assert parsed.quality == DocumentQuality.READABLE
    document = parsed.document_text(UUID(int=1), UUID(int=2))
    evidence = document.evidence(UUID(int=3), 1, 3, 5)
    assert evidence.quote == "\u00e9\U0001f680"
    assert evidence.end == 5  # Unicode code points, never UTF-16 units or UTF-8 bytes.
    document.validate_evidence(evidence)
    with pytest.raises(ValueError):
        document.evidence(UUID(int=4), 1, 0, 6)
    assert "Caf" not in repr(parsed)


@pytest.mark.parametrize("text", ["!!!!!!!!!!!!!!!!!!!", "(cid:12) (cid:13)"])
def test_scrambled_extraction_requires_manual_entry(text):
    parsed = parse_pdf(pdf([text]), content_type="application/pdf")
    assert parsed.quality == DocumentQuality.MANUAL_ENTRY_REQUIRED


def test_text_limit_includes_page_separator():
    raw = pdf(["English"] * 2)
    assert (
        len(
            parse_pdf(
                raw, content_type="application/pdf", limits=PdfLimits(max_text_chars=17)
            ).normalized.text
        )
        == 17
    )
    failure(raw, PdfFailure.TEXT_LIMIT, limits=PdfLimits(max_text_chars=16))


def test_high_compression_stream_rejected_before_text_extraction():
    raw = pdf(["unused"], compressed=zlib.compress(b" " * (2 * MIB)))
    assert len(raw) < 10_000
    failure(raw, PdfFailure.DECOMPRESSION_LIMIT, limits=PdfLimits(max_stream_bytes=MIB))


def test_default_decompression_limit_rejects_a_small_compression_bomb():
    raw = pdf(["unused"], compressed=zlib.compress(b" " * (8 * MIB + 1)))
    assert len(raw) < 20_000
    failure(raw, PdfFailure.DECOMPRESSION_LIMIT)


def test_aggregate_decoded_stream_budget():
    raw = pdf(["English"] * 3, compressed=zlib.compress(b" " * 4096))
    failure(
        raw,
        PdfFailure.DECOMPRESSION_LIMIT,
        limits=PdfLimits(max_stream_bytes=8192, max_decoded_bytes=8192),
    )


@pytest.mark.parametrize(
    "change",
    [
        {"max_bytes": 10 * MIB + 1},
        {"max_pages": 21},
        {"timeout_seconds": 31},
        {"memory_bytes": 513 * MIB},
        {"max_text_chars": 200_001},
        {"max_pages": True},
        {"timeout_seconds": float("nan")},
        {"memory_bytes": 63 * MIB},
    ],
)
def test_limits_cannot_disable_or_expand_p0_bounds(change):
    with pytest.raises(ValueError):
        PdfLimits(**change)


def probe_command(code: str) -> list[str]:
    source = str(Path(parser.__file__).resolve().parents[2])
    return [
        sys.executable,
        "-I",
        "-c",
        "import sys; sys.path.insert(0, sys.argv[1]); " + code,
        source,
    ]


def test_parent_deadline_kills_and_reaps_hung_child(monkeypatch):
    processes = []
    popen = parser.subprocess.Popen

    def capture(*args, **kwargs):
        process = popen(*args, **kwargs)
        processes.append(process)
        return process

    monkeypatch.setattr(parser.subprocess, "Popen", capture)
    monkeypatch.setattr(
        parser, "_command", lambda limits: probe_command("import time; time.sleep(60)")
    )
    failure(pdf(["English"]), PdfFailure.TIME_LIMIT, limits=PdfLimits(timeout_seconds=0.2))
    assert len(processes) == 1
    assert processes[0].poll() is not None


def test_real_os_memory_limit_is_enforced_in_child(monkeypatch):
    code = """
from benefitbridge.documents.parser import _apply_resource_limits, PdfLimits
handle = _apply_resource_limits(PdfLimits(memory_bytes=64*1024*1024))
try:
    allocation = bytearray(128*1024*1024)
except MemoryError:
    print('{"failure":"MEMORY_LIMIT"}')
else:
    print('{"pages":["Incorrect unrestricted extraction"]}')
"""
    monkeypatch.setattr(parser, "_command", lambda limits: probe_command(code))
    failure(pdf(["English"]), PdfFailure.MEMORY_LIMIT)


def test_missing_os_isolation_fails_closed(monkeypatch):
    code = """
import json
from benefitbridge.documents import parser
def unavailable(limits):
    raise OSError('private internal platform error')
parser._apply_resource_limits = unavailable
parser._worker_main()
"""
    monkeypatch.setattr(parser, "_command", lambda limits: [*probe_command(code), json.dumps({})])
    error = failure(pdf(["English"]), PdfFailure.ISOLATION_UNAVAILABLE)
    assert error.status == 503 and error.retryable


def test_child_environment_has_no_provider_secrets_and_logs_are_discarded(monkeypatch, capsys):
    monkeypatch.setenv("NEBIUS_API_KEY", "synthetic-private-secret")
    code = """
import os
assert 'NEBIUS_API_KEY' not in os.environ
sys.stderr.write('synthetic-private-secret')
print('{"pages":["English synthetic text"]}')
"""
    monkeypatch.setattr(parser, "_command", lambda limits: probe_command(code))
    assert parse_pdf(pdf(["English"]), content_type="application/pdf").page_count == 1
    assert "synthetic-private-secret" not in str(capsys.readouterr())


@pytest.mark.parametrize(
    "output",
    [
        "not-json",
        '{"pages":[]}',
        '{"pages":[1]}',
        '{"failure":"invented"}',
        '{"pages":["English"],"extra":1}',
    ],
)
def test_worker_protocol_rejects_invalid_output(monkeypatch, output):
    monkeypatch.setattr(parser, "_command", lambda limits: probe_command(f"print({output!r})"))
    failure(pdf(["English"]), PdfFailure.WORKER_FAILED)


def test_child_crash_is_not_a_successful_empty_parse(monkeypatch):
    monkeypatch.setattr(parser, "_command", lambda limits: probe_command("sys.exit(7)"))
    failure(pdf(["English"]), PdfFailure.WORKER_FAILED)


def test_child_denies_network_and_process_creation():
    for event in (
        "socket.connect",
        "socket.__new__",
        "subprocess.Popen",
        "os.system",
        "os.spawn",
        "os.posix_spawn",
        "os.fork",
        "os.forkpty",
    ):
        with pytest.raises(PermissionError):
            parser._deny_external_access(event, ())
