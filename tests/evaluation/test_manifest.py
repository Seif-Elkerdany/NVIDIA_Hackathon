"""Synthetic custody/partition fixtures; no benchmark gold is created here."""

import copy
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest
from evaluation import validate_manifest as validator
from evaluation.schemas import Manifest
from evaluation.validate_manifest import load_manifest, validate_manifest
from pydantic import ValidationError
from tests.fakes.providers import FakeClock

ROOT = Path(__file__).resolve().parents[2]
NOW = "2026-10-04T12:00:00Z"


@pytest.fixture
def data(tmp_path: Path) -> dict[str, Any]:
    def record(identifier: str) -> dict[str, Any]:
        content = f"Synthetic fixture {identifier}".encode()
        (tmp_path / f"{identifier}.txt").write_bytes(content)
        return {
            "id": identifier,
            "version": 1,
            "split": "development",
            "asset": {
                "path": f"{identifier}.txt",
                "content_hash": hashlib.sha256(content).hexdigest(),
            },
        }

    permission = {
        "license": "CC0-1.0",
        "permission_basis": "Team-created fixture",
        "permission_reference": "synthetic-test",
        "redistribution": "permitted",
    }
    source = {
        **record("source-1"),
        "provider_family": "provider-1",
        "program_family": "program-1",
        "intake_lineage": "intake-1",
        "policy_template_family": "policy-1",
        "lane": "INTERNSHIP_RESEARCH",
        "origin": "synthetic",
        "provider_name": "Fictional Fixture Provider",
        "retrieved_at": NOW,
        "permission": permission,
    }
    profile = {
        **record("profile-1"),
        "profile_family": "profile-family-1",
        "document_template_family": "document-1",
        "origin": "synthetic",
        "permission": permission,
    }
    return {
        "schema_version": "1.0.0",
        "benchmark": "BenefitBridge-Bench",
        "provenance": "team-created",
        "dataset_version": "fixture-v1",
        "reference_time": NOW,
        "frozen_at": NOW,
        "annotation_guide_version": "guide-1",
        "test_label_custodian": "custodian-1",
        "sources": [source],
        "profiles": [profile],
        "pairs": [{**record("pair-1"), "source_id": "source-1", "profile_id": "profile-1"}],
        "queries": [
            {
                **record("query-1"),
                "lane": "INTERNSHIP_RESEARCH",
                "candidate_source_ids": ["source-1"],
            }
        ],
        "claims": [{**record("claim-1"), "pair_id": "pair-1"}],
    }


def check(data: dict[str, Any], tmp_path: Path, fake_clock: FakeClock) -> Any:
    return validate_manifest(Manifest.model_validate(data), tmp_path, clock=fake_clock)


def test_pending_never_becomes_unknown(
    data: dict[str, Any], tmp_path: Path, fake_clock: FakeClock
) -> None:
    before = copy.deepcopy(data)
    report = check(data, tmp_path, fake_clock)
    assert report.valid and not report.ready
    assert len(report.pending) == 5
    assert not any(key.startswith("label.") for key in report.counts)
    assert data == before
    assert report == check(data, tmp_path, fake_clock)


@pytest.mark.parametrize(
    "kind,field",
    [
        ("sources", "provider_family"),
        ("sources", "program_family"),
        ("sources", "intake_lineage"),
        ("sources", "policy_template_family"),
        ("profiles", "profile_family"),
        ("profiles", "document_template_family"),
    ],
)
def test_group_leakage(
    data: dict[str, Any], tmp_path: Path, fake_clock: FakeClock, kind: str, field: str
) -> None:
    other = copy.deepcopy(data[kind][0])
    other["id"] = "other"
    other["split"] = "test"
    for name in (
        "provider_family",
        "program_family",
        "intake_lineage",
        "policy_template_family",
        "profile_family",
        "document_template_family",
    ):
        if name in other and name != field:
            other[name] = "other"
    data[kind].append(other)
    assert any(
        error.startswith("SPLIT_LEAKAGE:") for error in check(data, tmp_path, fake_clock).errors
    )


@pytest.mark.parametrize("split", ["development", "test"])
def test_duplicate_content(
    data: dict[str, Any], tmp_path: Path, fake_clock: FakeClock, split: str
) -> None:
    data["profiles"][0]["asset"] = data["sources"][0]["asset"]
    data["profiles"][0]["split"] = split
    assert "DUPLICATE_HASH:profile.profile-1" in check(data, tmp_path, fake_clock).errors


@pytest.mark.parametrize(
    "change,expected",
    [
        ("hash", "HASH_MISMATCH"),
        ("path", "ASSET_PATH"),
        ("missing", "ASSET_UNAVAILABLE"),
        ("ref", "MISSING_REFERENCE"),
        ("split", "REFERENCE_SPLIT"),
        ("duplicate_id", "DUPLICATE_ID"),
        ("pair", "DUPLICATE_PAIR"),
        ("candidate", "DUPLICATE_CANDIDATE"),
        ("clock", "CLOCK_ORDER"),
    ],
)
def test_invalid_manifest(
    data: dict[str, Any], tmp_path: Path, fake_clock: FakeClock, change: str, expected: str
) -> None:
    if change == "hash":
        data["sources"][0]["asset"]["content_hash"] = "0" * 64
    elif change == "path":
        data["sources"][0]["asset"]["path"] = "../private.txt"
    elif change == "missing":
        (tmp_path / "source-1.txt").unlink()
    elif change == "ref":
        data["pairs"][0]["source_id"] = "missing"
    elif change == "split":
        data["pairs"][0]["split"] = "test"
    elif change == "duplicate_id":
        data["sources"].append(copy.deepcopy(data["sources"][0]))
    elif change == "pair":
        pair = copy.deepcopy(data["pairs"][0])
        pair["id"] = "pair-2"
        data["pairs"].append(pair)
    elif change == "candidate":
        data["queries"][0]["candidate_source_ids"].append("source-1")
    else:
        data["frozen_at"] = "2026-10-05T12:00:00Z"
    assert any(e.startswith(expected + ":") for e in check(data, tmp_path, fake_clock).errors)


def gold(value: object) -> dict[str, Any]:
    return {
        "value": value,
        "annotators": ["human-1", "human-2"],
        "adjudicator": "human-3",
        "guide_version": "guide-1",
        "annotated_at": NOW,
        "rationale": "Synthetic test only",
    }


def test_supplied_label_is_preserved(
    data: dict[str, Any], tmp_path: Path, fake_clock: FakeClock
) -> None:
    data["pairs"][0]["gold"] = gold("UNKNOWN")
    report = check(data, tmp_path, fake_clock)
    assert report.valid
    assert "pair.pair-1" not in report.pending
    assert report.counts["label.development.UNKNOWN"] == 1


@pytest.mark.parametrize(
    "change,expected",
    [
        ("guide", "GUIDE_VERSION"),
        ("date", "ANNOTATION_AFTER_FREEZE"),
        ("relevance", "INCOMPLETE_RELEVANCE"),
    ],
)
def test_gold_metadata(
    data: dict[str, Any], tmp_path: Path, fake_clock: FakeClock, change: str, expected: str
) -> None:
    annotation = gold("MET")
    data["pairs"][0]["gold"] = annotation
    if change == "guide":
        annotation["guide_version"] = "other"
    elif change == "date":
        annotation["annotated_at"] = "2026-10-05T12:00:00Z"
    else:
        data["queries"][0]["gold"] = gold([])
    assert any(e.startswith(expected + ":") for e in check(data, tmp_path, fake_clock).errors)


@pytest.mark.parametrize("change", ["permission", "origin", "utc", "hash", "unknown", "human"])
def test_strict_schema(data: dict[str, Any], change: str) -> None:
    if change == "permission":
        del data["sources"][0]["permission"]
    elif change == "origin":
        data["profiles"][0]["origin"] = "real-student"
    elif change == "utc":
        data["reference_time"] = "2026-10-04T12:00:00+02:00"
    elif change == "hash":
        data["sources"][0]["asset"]["content_hash"] = "INVALID"
    elif change == "human":
        annotation = gold("MET")
        annotation["adjudicator"] = "human-1"
        data["pairs"][0]["gold"] = annotation
    else:
        data["generated_gold"] = True
    with pytest.raises(ValidationError):
        Manifest.model_validate(data)


def test_cli_pending_and_read_only(data: dict[str, Any], tmp_path: Path) -> None:
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    before = path.read_bytes()
    for options, code in [([], 0), (["--require-labels"], 2)]:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "evaluation.validate_manifest",
                str(path),
                "--as-of",
                NOW,
                *options,
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == code, result.stderr
        assert len(json.loads(result.stdout)["pending"]) == 5
    assert path.read_bytes() == before


def test_duplicate_json_keys(tmp_path: Path) -> None:
    path = tmp_path / "manifest.json"
    path.write_text('{"schema_version":"1.0.0","schema_version":"2.0.0"}', encoding="utf-8")
    with pytest.raises(ValueError, match="Duplicate JSON key"):
        load_manifest(path)


def test_bounded_reads(
    data: dict[str, Any], tmp_path: Path, fake_clock: FakeClock, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(validator, "MAX_ASSET_BYTES", 4)
    assert any(e.startswith("ASSET_TOO_LARGE:") for e in check(data, tmp_path, fake_clock).errors)
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    monkeypatch.setattr(validator, "MAX_MANIFEST_BYTES", 4)
    with pytest.raises(ValueError, match="size limit"):
        load_manifest(path)


def test_complete_supplied_annotations(
    data: dict[str, Any], tmp_path: Path, fake_clock: FakeClock
) -> None:
    for kind in ("sources", "profiles"):
        content = f"Synthetic {kind} annotation fixture".encode()
        path = tmp_path / f"{kind}-gold.json"
        path.write_bytes(content)
        data[kind][0]["gold"] = gold(
            {"path": path.name, "content_hash": hashlib.sha256(content).hexdigest()}
        )
    data["pairs"][0]["gold"] = gold("UNKNOWN")
    data["queries"][0]["gold"] = gold([{"source_id": "source-1", "grade": 0}])
    data["claims"][0]["gold"] = gold("UNVERIFIABLE")
    before = copy.deepcopy(data)
    assert check(data, tmp_path, fake_clock).ready
    assert data == before
    (tmp_path / "sources-gold.json").write_text("changed", encoding="utf-8")
    assert "HASH_MISMATCH:source.source-1.gold" in check(data, tmp_path, fake_clock).errors


def test_schema_is_deterministic() -> None:
    assert Manifest.model_json_schema() == Manifest.model_json_schema()


def test_cli_invalid_input_is_redacted(tmp_path: Path) -> None:
    path = tmp_path / "manifest.json"
    path.write_text('{"secret":"private fixture content"}', encoding="utf-8")
    result = subprocess.run(
        [sys.executable, "-m", "evaluation.validate_manifest", str(path), "--as-of", NOW],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 1
    assert "private fixture content" not in result.stdout + result.stderr
    assert json.loads(result.stdout)["errors"] == ["INVALID_MANIFEST_OR_CLOCK"]
