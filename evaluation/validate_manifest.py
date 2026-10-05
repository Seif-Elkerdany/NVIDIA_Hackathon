"""Offline, read-only validation of a frozen benchmark and its local assets."""

import argparse
import hashlib
import json
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import cast

from evaluation.schemas import Asset, Claim, Manifest, Pair, Profile, Query, Record, Source, Split
from pydantic import ValidationError

from benefitbridge.domain.base import utc_timestamp
from benefitbridge.ports import Clock

MAX_MANIFEST_BYTES = 10 * 1024 * 1024
MAX_ASSET_BYTES = 32 * 1024 * 1024


@dataclass(frozen=True)
class ValidationReport:
    errors: tuple[str, ...]
    pending: tuple[str, ...]
    counts: dict[str, int]

    @property
    def valid(self) -> bool:
        return not self.errors

    @property
    def ready(self) -> bool:
        return self.valid and not self.pending


def validate_manifest(manifest: Manifest, root: Path, *, clock: Clock) -> ValidationReport:
    """Pending annotation is distinct from the domain's UNKNOWN eligibility label."""
    errors: list[str] = []
    pending: list[str] = []
    counts: Counter[str] = Counter()
    groups: dict[tuple[str, str], Split] = {}
    hashes: dict[str, str] = {}
    assets: dict[str, str] = {}
    root = root.resolve()

    def fail(code: str, key: str) -> None:
        errors.append(f"{code}:{key}")

    def asset_check(asset: Asset, key: str) -> None:
        # A shared asset is not a loophole for duplicate cases or document templates.
        previous = hashes.setdefault(asset.content_hash, key)
        if previous != key:
            fail("DUPLICATE_HASH", key)
        path = (root / asset.path).resolve()
        if Path(asset.path).is_absolute() or not path.is_relative_to(root):
            fail("ASSET_PATH", key)
            return
        if not path.is_file():
            fail("ASSET_UNAVAILABLE", key)
            return
        previous_hash = assets.setdefault(str(path), asset.content_hash)
        if previous_hash != asset.content_hash:
            fail("ASSET_HASH_CONFLICT", key)
        try:
            with path.open("rb") as stream:
                content = stream.read(MAX_ASSET_BYTES + 1)
        except OSError:
            fail("ASSET_UNAVAILABLE", key)
            return
        if len(content) > MAX_ASSET_BYTES:
            fail("ASSET_TOO_LARGE", key)
        elif hashlib.sha256(content).hexdigest() != asset.content_hash:
            fail("HASH_MISMATCH", key)

    def group(namespace: str, family: str, record: Record) -> None:
        previous = groups.setdefault((namespace, family), record.split)
        if previous != record.split:
            fail("SPLIT_LEAKAGE", f"{namespace}.{record.id}")

    collections: dict[str, tuple[Source | Profile | Pair | Query | Claim, ...]] = {
        "source": manifest.sources,
        "profile": manifest.profiles,
        "pair": manifest.pairs,
        "query": manifest.queries,
        "claim": manifest.claims,
    }
    if manifest.reference_time > manifest.frozen_at or manifest.frozen_at > clock.now():
        fail("CLOCK_ORDER", "manifest")
    for kind, records in collections.items():
        seen: set[str] = set()
        for record in records:
            key = f"{kind}.{record.id}"
            if record.id in seen:
                fail("DUPLICATE_ID", key)
            seen.add(record.id)
            counts[f"{kind}.{record.split}"] += 1
            asset_check(record.asset, key)
            gold = record.gold
            if gold is None:
                pending.append(key)
            else:
                if gold.annotated_at > manifest.frozen_at:
                    fail("ANNOTATION_AFTER_FREEZE", key)
                if gold.guide_version != manifest.annotation_guide_version:
                    fail("GUIDE_VERSION", key)
                if isinstance(gold.value, Asset):
                    asset_check(gold.value, f"{key}.gold")
    sources = {s.id: s for s in manifest.sources}
    profiles = {p.id: p for p in manifest.profiles}
    pairs = {p.id: p for p in manifest.pairs}

    def reference(table: dict[str, Record], identifier: str, record: Record) -> None:
        target = table.get(identifier)
        if target is None:
            fail("MISSING_REFERENCE", record.id)
        elif target.split != record.split:
            fail("REFERENCE_SPLIT", record.id)

    for source in manifest.sources:
        for field in (
            "provider_family",
            "program_family",
            "intake_lineage",
            "policy_template_family",
        ):
            group(field, getattr(source, field), source)
        counts[f"lane.{source.split}.{source.lane}"] += 1
        if source.retrieved_at > manifest.frozen_at:
            fail("RETRIEVAL_AFTER_FREEZE", source.id)
    for profile in manifest.profiles:
        group("profile_family", profile.profile_family, profile)
        group("document_template_family", profile.document_template_family, profile)
        for index, document in enumerate(profile.documents):
            asset_check(document, f"profile.{profile.id}.document.{index}")
    seen_pairs: set[tuple[str, str]] = set()
    for pair in manifest.pairs:
        reference(cast(dict[str, Record], sources), pair.source_id, pair)
        reference(cast(dict[str, Record], profiles), pair.profile_id, pair)
        identity = (pair.source_id, pair.profile_id)
        if identity in seen_pairs:
            fail("DUPLICATE_PAIR", pair.id)
        seen_pairs.add(identity)
        if pair.gold is not None:
            counts[f"label.{pair.split}.{pair.gold.value}"] += 1
    for query in manifest.queries:
        candidates = query.candidate_source_ids
        if len(set(candidates)) != len(candidates):
            fail("DUPLICATE_CANDIDATE", query.id)
        for identifier in candidates:
            reference(cast(dict[str, Record], sources), identifier, query)
        if query.gold is not None:
            judged = [item.source_id for item in query.gold.value]
            if len(set(judged)) != len(judged) or set(judged) != set(candidates):
                fail("INCOMPLETE_RELEVANCE", query.id)
    for claim in manifest.claims:
        reference(cast(dict[str, Record], pairs), claim.pair_id, claim)
    return ValidationReport(
        tuple(sorted(set(errors))), tuple(sorted(pending)), dict(sorted(counts.items()))
    )


def load_manifest(path: Path) -> Manifest:
    def unique_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("Duplicate JSON key")
            result[key] = value
        return result

    with path.open("rb") as stream:
        content = stream.read(MAX_MANIFEST_BYTES + 1)
    if len(content) > MAX_MANIFEST_BYTES:
        raise ValueError("Manifest exceeds size limit")
    return Manifest.model_validate(json.loads(content, object_pairs_hook=unique_keys))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--as-of", required=True, help="Injected UTC validation clock (RFC3339 Z)")
    parser.add_argument("--require-labels", action="store_true")
    args = parser.parse_args()
    try:
        instant = utc_timestamp(args.as_of)
        manifest = load_manifest(args.manifest)
    except (OSError, ValueError, ValidationError):
        # Do not echo raw payloads, private asset paths or annotation text.
        print(json.dumps({"valid": False, "errors": ["INVALID_MANIFEST_OR_CLOCK"]}))
        return 1

    class FrozenClock:
        def now(self) -> datetime:
            return instant

        def monotonic(self) -> float:
            return 0.0

    report = validate_manifest(manifest, args.manifest.parent, clock=FrozenClock())
    print(
        json.dumps(
            {
                "valid": report.valid,
                "ready": report.ready,
                "errors": report.errors,
                "pending": report.pending,
                "counts": report.counts,
            },
            sort_keys=True,
        )
    )
    return 1 if not report.valid else (2 if args.require_labels and not report.ready else 0)


if __name__ == "__main__":
    raise SystemExit(main())
