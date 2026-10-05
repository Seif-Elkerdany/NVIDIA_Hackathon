"""MS-021: pinned public HTTPS and an explicit untrusted-text boundary.

R04.03/R13.03: every hop passes URL, source-policy, DNS and actual-peer checks.
R13.02: no search, cookies, authorization, subresource loading or script execution.
R13.05: only opaque reservation IDs, codes, counts and durations enter diagnostics.

Use GuardedFetcher(clock, AllowedHosts(...)) as the MS-003 Fetch binding, or
bind_fetch_guard(existing_dependencies, fetcher). Native TLS uses a numeric
socket target and the original hostname for certificate verification/SNI; h11
is already pinned by the existing HTTP stack. Production has no mock fallback.
The caller reserves page/cost budget (including redirect hops) and enforces
consent/currentness. AllowedHosts is network-fetch permission, not source authority
or proof of ATS affiliation; those checks remain with the source registry owners. HTML/plain
text is normalized separately by sanitize_source; PDFs go to the MS-012 parser.
Unsupported encodings/compression, login/CAPTCHA content and ambiguous hidden HTML
fail explicitly. Source facts are not sanitized by heuristically deleting visible
instructions: UntrustedContent preserves them as JSON data and cannot dispatch tools.
Neither sanitizer nor parser loads linked resources or expands external entities.

Design references: OWASP SSRF Prevention Cheat Sheet (validate all DNS results and
redirects), Python 3.12 asyncio streams (preconnected sockets, verified TLS SNI),
and the locked h11 streaming HTTP parser. No dependency, schema, migration, central
configuration or public endpoint change; production supplies an explicit SourcePolicy.
Reviewer M4: inspect pin/peer equality, conservative address ranges, normalized
citation offsets and raw-versus-normalized hashes. Run targeted scenarios with
``uv run --frozen --offline python -m pytest tests/security/test_fetch_guard.py``.
Global production-handler readiness remains governed by the MS-003 composition.
"""

import asyncio
import ipaddress
import json
import logging
import re
import socket
import ssl
import unicodedata
from dataclasses import dataclass, field, replace
from hashlib import sha256
from html.parser import HTMLParser
from typing import Literal, Protocol
from urllib.parse import parse_qsl, quote, urljoin, urlsplit, urlunsplit

import h11

from benefitbridge.composition import Dependencies
from benefitbridge.config import ConfigurationError
from benefitbridge.domain.errors import DomainError
from benefitbridge.ports import Clock, Fetch, FetchedResource, FetchRequest
from benefitbridge.sources.contracts import NormalizedText, normalize_document

logger = logging.getLogger(__name__)
Address = ipaddress.IPv4Address | ipaddress.IPv6Address
_IPV6_PUBLIC = ipaddress.ip_network("2000::/3")
_EXCLUDED = tuple(
    ipaddress.ip_network(value)
    for value in (
        "192.0.0.0/24",
        "192.88.99.0/24",
        "168.63.129.16/32",
        "2001::/23",
        "2002::/16",
        "3fff::/20",
    )
)
_SECRET_KEYS = frozenset(
    {
        "token",
        "access_token",
        "api_key",
        "apikey",
        "key",
        "password",
        "authorization",
        "auth",
        "session",
        "jwt",
        "sig",
        "signature",
        "x-amz-signature",
        "x-amz-credential",
        "email",
    }
)


class FetchFailure(DomainError):
    def __init__(self, code: str, *, retryable: bool = False) -> None:
        status = 503 if retryable else 400
        super().__init__(
            code, "The public source could not be safely retrieved.", status, retryable
        )


def public_address(value: str) -> Address:
    try:
        if "%" in value:
            raise ValueError("Scoped addresses are not public targets")
        address = ipaddress.ip_address(value)
    except ValueError:
        raise FetchFailure("NETWORK_TARGET_REJECTED") from None
    if (
        not address.is_global
        or address.is_multicast
        or address.is_reserved
        or address.is_unspecified
        or address.is_loopback
        or address.is_link_local
        or (isinstance(address, ipaddress.IPv6Address) and address not in _IPV6_PUBLIC)
        or any(address.version == network.version and address in network for network in _EXCLUDED)
    ):
        raise FetchFailure("NETWORK_TARGET_REJECTED")
    return address


@dataclass(frozen=True)
class PublicUrl:
    url: str = field(repr=False)
    hostname: str = field(repr=False)
    authority: str = field(repr=False)
    target: str = field(repr=False)


def validate_url(value: str) -> PublicUrl:
    if (
        not isinstance(value, str)
        or not 1 <= len(value) <= 2048
        or "\\" in value
        or any(char.isspace() or unicodedata.category(char).startswith("C") for char in value)
    ):
        raise FetchFailure("URL_REJECTED")
    try:
        parsed = urlsplit(value)
        if (
            parsed.scheme != "https"
            or not parsed.netloc
            or parsed.username is not None
            or parsed.password is not None
            or parsed.fragment
            or parsed.port not in {None, 443}
            or parsed.netloc.endswith(":")
        ):
            raise ValueError("Only unauthenticated HTTPS on port 443 is permitted")
        host = (parsed.hostname or "").removesuffix(".").encode("idna").decode("ascii").lower()
        if not host or "%" in host:
            raise ValueError("Invalid hostname")
        try:
            address = ipaddress.ip_address(host)
        except ValueError:
            labels = host.split(".")
            if (
                len(host) > 253
                or len(labels) < 2
                or any(
                    not re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?", label)
                    for label in labels
                )
                or all(re.fullmatch(r"(?:[0-9]+|0x[0-9a-f]+)", label) for label in labels)
                or host.endswith((".localhost", ".local", ".internal"))
            ):
                raise ValueError("Ambiguous or local hostname") from None
            authority = host
        else:
            public_address(str(address))
            host = str(address)
            authority = f"[{host}]" if address.version == 6 else host
        if any(key.lower() in _SECRET_KEYS or "%" in key for key, _ in parse_qsl(parsed.query)):
            raise ValueError("Credential query is not a public-source request")
        path = quote(parsed.path or "/", safe="/%:@!$&'()*+,;=-._~")
        query = quote(parsed.query, safe="%/?@:!$&'()*+,;=-._~")
        target = path + ("?" + query if query else "")
        canonical = urlunsplit(("https", authority, path, query, ""))
        if len(canonical) > 2048:
            raise ValueError("Encoded URL exceeds the source URL limit")
        return PublicUrl(canonical, host, authority, target)
    except (ValueError, UnicodeError):
        raise FetchFailure("URL_REJECTED") from None


class SourcePolicy(Protocol):
    def permits(self, target: PublicUrl) -> bool: ...


@dataclass(frozen=True)
class AllowedHosts:
    """Explicit exact host policy; redirect affiliates require their own approval."""

    hosts: frozenset[str] = field(repr=False)

    def __post_init__(self) -> None:
        normalized = set()
        for host in self.hosts:
            if not isinstance(host, str) or any(char in host for char in "/?#@\\"):
                raise ConfigurationError("Source policy requires hostnames, not URLs")
            authority = f"[{host}]" if ":" in host and not host.startswith("[") else host
            try:
                target = validate_url("https://" + authority + "/")
            except FetchFailure:
                raise ConfigurationError("Source policy requires valid public hosts") from None
            normalized.add(target.hostname)
        if not normalized:
            raise ConfigurationError("Source policy requires explicit allowed hosts")
        object.__setattr__(self, "hosts", frozenset(normalized))

    def permits(self, target: PublicUrl) -> bool:
        return target.hostname in self.hosts


class Resolver(Protocol):
    async def resolve(self, hostname: str) -> tuple[str, ...]: ...


class SystemResolver:
    async def resolve(self, hostname: str) -> tuple[str, ...]:
        answers = await asyncio.get_running_loop().getaddrinfo(
            hostname, 443, type=socket.SOCK_STREAM, proto=socket.IPPROTO_TCP
        )
        return tuple(dict.fromkeys(str(answer[4][0]) for answer in answers))


class Writer(Protocol):
    def write(self, data: bytes) -> None: ...
    async def drain(self) -> None: ...
    def close(self) -> None: ...
    async def wait_closed(self) -> None: ...
    def get_extra_info(self, name: str) -> object: ...


class Connector(Protocol):
    async def connect(
        self, target: PublicUrl, address: Address, timeout: float, header_limit: int
    ) -> tuple[asyncio.StreamReader, Writer]: ...


class TLSConnector:
    async def connect(
        self, target: PublicUrl, address: Address, timeout: float, header_limit: int
    ) -> tuple[asyncio.StreamReader, Writer]:
        context = ssl.create_default_context()
        context.minimum_version = ssl.TLSVersion.TLSv1_2
        context.set_alpn_protocols(["http/1.1"])
        family = socket.AF_INET6 if address.version == 6 else socket.AF_INET
        connection = socket.socket(family, socket.SOCK_STREAM)
        connection.setblocking(False)
        transferred = False
        try:
            # A numeric sockaddr avoids a second hostname lookup after authorization.
            await asyncio.get_running_loop().sock_connect(connection, (str(address), 443))
            reader, writer = await asyncio.open_connection(
                sock=connection,
                ssl=context,
                server_hostname=target.hostname,
                ssl_handshake_timeout=timeout,
                ssl_shutdown_timeout=1,
                limit=header_limit,
            )
            transferred = True
            return reader, writer
        finally:
            # open_connection transfers ownership on success; close only failed sockets.
            if not transferred:
                connection.close()


@dataclass(frozen=True)
class GuardLimits:
    max_bytes: int = 10 * 1024 * 1024
    max_redirects: int = 5
    timeout_seconds: float = 30
    max_header_bytes: int = 16_384
    max_dns_answers: int = 32

    def __post_init__(self) -> None:
        if (
            any(
                type(value) is not int or value <= 0
                for value in (self.max_bytes, self.max_header_bytes, self.max_dns_answers)
            )
            or type(self.max_redirects) is not int
            or self.max_redirects < 0
            or not 0 < self.timeout_seconds <= 120
        ):
            raise ValueError("Fetch policy requires bounded bytes, redirects, DNS and time")


@dataclass(frozen=True)
class Hop:
    status: int
    headers: dict[str, str] = field(repr=False)
    body: bytes = field(repr=False)


def _headers(response: h11.Response, limit: int) -> dict[str, str]:
    size = len(response.http_version) + len(response.reason) + 12
    size += sum(len(key) + len(value) + 4 for key, value in response.headers)
    if size > limit:
        raise FetchFailure("HEADER_LIMIT_EXCEEDED")
    result: dict[str, str] = {}
    for key, value in response.headers:
        name = key.decode("ascii").lower()
        if name in result and name in {
            "location",
            "content-length",
            "transfer-encoding",
            "content-type",
            "content-encoding",
        }:
            raise FetchFailure("INVALID_RESPONSE")
        result[name] = value.decode("latin-1")
    if "content-length" in result and "transfer-encoding" in result:
        raise FetchFailure("INVALID_RESPONSE")
    return result


def _media_type(value: str) -> str:
    sections = value.lower().split(";")
    media = sections[0].strip()
    if media not in {"text/html", "application/xhtml+xml", "text/plain", "application/pdf"}:
        raise FetchFailure("UNSUPPORTED_MEDIA")
    for section in sections[1:]:
        key, _, parameter = section.strip().partition("=")
        if key.strip() == "charset" and parameter.strip().strip('"') not in {
            "utf-8",
            "utf8",
            "us-ascii",
        }:
            raise FetchFailure("UNSUPPORTED_ENCODING")
    return media


class GuardedFetcher:
    def __init__(
        self,
        clock: Clock,
        policy: SourcePolicy,
        *,
        limits: GuardLimits | None = None,
        mode: Literal["real", "fixture"] = "real",
        resolver: Resolver | None = None,
        connector: Connector | None = None,
    ) -> None:
        if mode not in {"real", "fixture"} or (mode == "real" and (resolver or connector)):
            raise ConfigurationError("Custom network adapters require explicit fixture mode")
        if mode == "fixture" and (resolver is None or connector is None):
            raise ConfigurationError("Fixture fetch requires explicit resolver and connector")
        self.clock, self.policy, self.limits = clock, policy, limits or GuardLimits()
        self._mode, self._resolver, self._connector = (
            mode,
            resolver or SystemResolver(),
            connector or TLSConnector(),
        )

    @property
    def mode(self) -> Literal["real", "fixture"]:
        return self._mode

    async def fetch(self, request: FetchRequest) -> FetchedResource:
        started, redirects, count, code = self.clock.monotonic(), 0, 0, "SUCCEEDED"
        try:
            if (
                type(request.max_bytes) is not int
                or not 0 < request.max_bytes <= self.limits.max_bytes
                or type(request.max_redirects) is not int
                or not 0 <= request.max_redirects <= self.limits.max_redirects
                or isinstance(request.timeout_seconds, bool)
                or request.timeout_seconds > self.limits.timeout_seconds
            ):
                raise FetchFailure("FETCH_LIMIT_EXCEEDED")
            deadline = started + request.timeout_seconds
            visited: set[str] = set()
            async with asyncio.timeout(request.timeout_seconds):
                target = validate_url(request.url)
                while True:
                    if target.url in visited:
                        raise FetchFailure("REDIRECT_LOOP")
                    visited.add(target.url)
                    if not self.policy.permits(target):
                        raise FetchFailure("SOURCE_POLICY_REJECTED")
                    try:
                        numeric = ipaddress.ip_address(target.hostname)
                    except ValueError:
                        answers = await self._resolver.resolve(target.hostname)
                    else:
                        answers = (str(numeric),)
                    if not 1 <= len(answers) <= self.limits.max_dns_answers:
                        raise FetchFailure("NETWORK_TARGET_REJECTED")
                    addresses = tuple(public_address(answer) for answer in answers)
                    remaining = deadline - self.clock.monotonic()
                    if remaining <= 0:
                        raise FetchFailure("FETCH_TIMEOUT", retryable=True)
                    hop = await self._hop(target, addresses[0], request.max_bytes, remaining)
                    if hop.status in {301, 302, 303, 307, 308}:
                        if redirects >= request.max_redirects:
                            raise FetchFailure("REDIRECT_LIMIT_EXCEEDED")
                        location = hop.headers.get("location")
                        if not location:
                            raise FetchFailure("INVALID_RESPONSE")
                        if "\\" in location or any(
                            char.isspace() or unicodedata.category(char).startswith("C")
                            for char in location
                        ):
                            raise FetchFailure("URL_REJECTED")
                        target = validate_url(urljoin(target.url, location))
                        redirects += 1
                        continue
                    if hop.status != 200:
                        raise FetchFailure(
                            "SOURCE_UNAVAILABLE", retryable=hop.status in {429, 500, 502, 503, 504}
                        )
                    media = _media_type(hop.headers.get("content-type", ""))
                    if media == "application/pdf" and not hop.body.startswith(b"%PDF-"):
                        raise FetchFailure("INVALID_CONTENT")
                    count = len(hop.body)
                    return FetchedResource(
                        target.url, media, hop.body, self.clock.now(), sha256(hop.body).hexdigest()
                    )
        except TimeoutError:
            code = "FETCH_TIMEOUT"
            raise FetchFailure(code, retryable=True) from None
        except (
            OSError,
            asyncio.IncompleteReadError,
            h11.RemoteProtocolError,
            h11.LocalProtocolError,
            UnicodeError,
        ):
            code = "INVALID_RESPONSE"
            raise FetchFailure(code) from None
        except asyncio.CancelledError:
            code = "CANCELLED"
            raise
        except FetchFailure as failure:
            code = failure.code
            raise
        finally:
            logger.info(
                "guarded_fetch",
                extra={
                    "event_code": code,
                    "reservation_id": str(request.reservation_id),
                    "redirects": redirects,
                    "body_bytes": count,
                    "duration_ms": max(0, int((self.clock.monotonic() - started) * 1000)),
                },
            )

    async def _hop(
        self, target: PublicUrl, address: Address, max_bytes: int, timeout: float
    ) -> Hop:
        reader, writer = await self._connector.connect(
            target, address, timeout, self.limits.max_header_bytes
        )
        try:
            peer = writer.get_extra_info("peername")
            if (
                not isinstance(peer, tuple)
                or not peer
                or not isinstance(peer[0], str)
                or public_address(peer[0]) != address
            ):
                raise FetchFailure("CONNECTION_TARGET_MISMATCH")
            connection = h11.Connection(
                h11.CLIENT, max_incomplete_event_size=self.limits.max_header_bytes
            )
            packet = connection.send(
                h11.Request(
                    method=b"GET",
                    target=target.target.encode("ascii"),
                    headers=[
                        (b"Host", target.authority.encode("ascii")),
                        (b"Accept", b"text/html, text/plain, application/pdf"),
                        (b"Accept-Encoding", b"identity"),
                        (b"Connection", b"close"),
                        (b"User-Agent", b"BenefitBridge-public-fetch/1"),
                    ],
                )
            )
            writer.write(packet or b"")
            writer.write(connection.send(h11.EndOfMessage()) or b"")
            await writer.drain()
            headers: dict[str, str] | None = None
            status = interim = wire_header_bytes = 0
            body = bytearray()
            while True:
                event = connection.next_event()
                if event is h11.NEED_DATA:
                    chunk = await reader.read(min(8192, self.limits.max_header_bytes))
                    if headers is None:
                        wire_header_bytes += len(chunk)
                        if wire_header_bytes > self.limits.max_header_bytes + 8192:
                            raise FetchFailure("HEADER_LIMIT_EXCEEDED")
                    connection.receive_data(chunk)
                elif isinstance(event, h11.InformationalResponse):
                    interim += 1
                    if interim > 3 or event.status_code == 101:
                        raise FetchFailure("INVALID_RESPONSE")
                elif isinstance(event, h11.Response):
                    headers, status = (
                        _headers(event, self.limits.max_header_bytes),
                        event.status_code,
                    )
                    if status != 200:
                        return Hop(status, headers, b"")
                    if headers.get("content-encoding", "identity").lower() != "identity":
                        raise FetchFailure("UNSUPPORTED_ENCODING")
                    length = headers.get("content-length")
                    if length is not None and (
                        not re.fullmatch(r"[0-9]{1,12}", length) or int(length) > max_bytes
                    ):
                        raise FetchFailure("BODY_LIMIT_EXCEEDED")
                    _media_type(headers.get("content-type", ""))
                elif isinstance(event, h11.Data):
                    if len(body) + len(event.data) > max_bytes:
                        raise FetchFailure("BODY_LIMIT_EXCEEDED")
                    body.extend(event.data)
                elif isinstance(event, h11.EndOfMessage):
                    if headers is None or event.headers:
                        raise FetchFailure("INVALID_RESPONSE")
                    return Hop(status, headers, bytes(body))
                else:
                    raise FetchFailure("INVALID_RESPONSE")
        finally:
            writer.close()
            try:
                async with asyncio.timeout(1):
                    await writer.wait_closed()
            except (TimeoutError, OSError):
                pass  # The socket is already closed; cleanup must not mask the typed failure.


def bind_fetch_guard(dependencies: Dependencies, fetcher: GuardedFetcher) -> Dependencies:
    provider: Fetch = fetcher
    return replace(dependencies, fetch=provider, provider_mode=fetcher.mode)


class _TextExtractor(HTMLParser):
    _INERT = frozenset(
        {
            "script",
            "style",
            "template",
            "svg",
            "canvas",
            "noscript",
            "iframe",
            "object",
            "embed",
            "form",
        }
    )
    _VOID = frozenset(
        {
            "area",
            "base",
            "br",
            "col",
            "embed",
            "hr",
            "img",
            "input",
            "link",
            "meta",
            "param",
            "source",
            "track",
            "wbr",
        }
    )
    _BLOCK = frozenset(
        {
            "p",
            "div",
            "section",
            "article",
            "h1",
            "h2",
            "h3",
            "h4",
            "li",
            "ul",
            "ol",
            "tr",
            "td",
            "th",
            "table",
            "br",
            "hr",
        }
    )

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.characters = 0
        self.maximum = 200_000
        self.stack: list[tuple[str, bool]] = []
        self.restricted = False

    def append(self, text: str) -> None:
        self.characters += len(text)
        if self.characters > self.maximum:
            raise FetchFailure("TEXT_LIMIT_EXCEEDED")
        self.parts.append(text)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if (
            tag == "meta"
            and attributes.get("charset")
            and (attributes["charset"] or "").lower() not in {"utf-8", "utf8", "us-ascii"}
        ):
            raise FetchFailure("UNSUPPORTED_ENCODING")
        if (
            tag == "input"
            and (attributes.get("type") or "").lower() == "password"
            or "data-sitekey" in attributes
            or attributes.get("class", "") in {"g-recaptcha", "cf-turnstile"}
        ):
            self.restricted = True
        style = (attributes.get("style") or "").replace(" ", "").lower()
        hidden = (
            tag in self._INERT
            or "hidden" in attributes
            or attributes.get("aria-hidden") == "true"
            or "display:none" in style
            or "visibility:hidden" in style
            or bool(self.stack and self.stack[-1][1])
        )
        if not hidden and tag in self._BLOCK:
            self.append("\n")
        if tag not in self._VOID:
            if len(self.stack) >= 256:
                raise FetchFailure("INVALID_CONTENT")
            self.stack.append((tag, hidden))

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)
        if tag not in self._VOID:
            self.handle_endtag(tag)

    def handle_endtag(self, tag: str) -> None:
        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index][0] == tag:
                if any(hidden for _, hidden in self.stack[index + 1 :]):
                    raise FetchFailure("INVALID_CONTENT")
                hidden = self.stack[index][1]
                del self.stack[index:]
                if tag in self._BLOCK and not hidden:
                    self.append("\n")
                break

    def handle_data(self, data: str) -> None:
        if not self.stack or not self.stack[-1][1]:
            self.append(data)


def sanitize_source(resource: FetchedResource, *, max_characters: int = 200_000) -> NormalizedText:
    """Extract inert text before MS-006 normalization/citation selection; never truncate."""
    if (
        type(max_characters) is not int
        or not 1 <= max_characters <= 200_000
        or len(resource.body) > 10 * 1024 * 1024
    ):
        raise FetchFailure("TEXT_LIMIT_EXCEEDED")
    if resource.media_type not in {"text/html", "application/xhtml+xml", "text/plain"}:
        raise FetchFailure("UNSUPPORTED_TEXT_CONTENT")
    try:
        text = resource.body.decode("utf-8-sig")
    except UnicodeError:
        raise FetchFailure("UNREADABLE_CONTENT") from None
    if resource.media_type != "text/plain":
        extractor = _TextExtractor()
        extractor.maximum = max_characters
        extractor.feed(text)
        extractor.close()
        if any(hidden for _, hidden in extractor.stack):
            raise FetchFailure("INVALID_CONTENT")
        if extractor.restricted:
            raise FetchFailure("AUTHENTICATION_REQUIRED")
        text = "".join(extractor.parts)
    if not text.strip() or len(text) > max_characters:
        raise FetchFailure("TEXT_LIMIT_EXCEEDED" if text.strip() else "UNREADABLE_CONTENT")
    if any(unicodedata.category(char) == "Cc" and char not in "\n\r\t\f" for char in text):
        raise FetchFailure("UNREADABLE_CONTENT")
    return normalize_document(text)


@dataclass(frozen=True)
class UntrustedContent:
    normalized: NormalizedText = field(repr=False)
    origin: Literal["SOURCE", "DOCUMENT"]

    def __post_init__(self) -> None:
        if self.origin not in {"SOURCE", "DOCUMENT"}:
            raise FetchFailure("INVALID_CONTENT")

    def as_data(self, *, max_characters: int) -> str:
        """For the model's data message only, never a system prompt or tool invocation."""
        if (
            type(max_characters) is not int
            or not 1 <= max_characters <= 200_000
            or not 0 < len(self.normalized.text) <= max_characters
        ):
            raise FetchFailure("TEXT_LIMIT_EXCEEDED")
        return json.dumps(
            {
                "trust": "UNTRUSTED_DATA",
                "origin": self.origin,
                "normalization_version": self.normalized.normalization_version,
                "content_hash": self.normalized.normalized_text_hash,
                "text": self.normalized.text,
            },
            ensure_ascii=True,
            separators=(",", ":"),
        )
