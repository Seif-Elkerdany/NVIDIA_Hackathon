# BenefitBridge-Bench manifest validation

MS-013 implements R15.01 / US-15.01: versioned, frozen benchmark metadata and
offline split validation. This is a team-created benchmark, not a standard
external dataset. No corpus or gold annotations ship with this unit.

Run from the repository root with the locked Python environment:

```powershell
python -m uv run --frozen --offline python -m evaluation.validate_manifest path/to/manifest.json --as-of 2026-10-04T12:00:00Z
python -m uv run --frozen --offline python -m evaluation.validate_manifest path/to/manifest.json --as-of 2026-10-04T12:00:00Z --require-labels
python -m uv run --frozen --offline python -m pytest tests/evaluation --suite unit
python -m uv run --frozen --offline ruff check evaluation tests/evaluation
python -m uv run --frozen --offline mypy evaluation
```

Exit 0 means structurally valid; exit 1 means invalid metadata/assets/splits;
exit 2 means valid but pending annotations when `--require-labels` is supplied.
The JSON report contains safe record identifiers, failures, pending records,
achieved split/lane counts and supplied pair-label distributions. It never
prints annotation text or invents labels. A valid manifest with missing labels
has `ready: false`. UNKNOWN is a supplied human eligibility label, not an
automatic replacement for missing annotations.

`schemas.Manifest` is the executable Pydantic schema source. Consumers can call
`Manifest.model_json_schema()` or use `load_manifest(path)` and
`validate_manifest(manifest, root, clock=...)`; the clock implements the existing
MS-003 `Clock` port. The CLI requires an explicit UTC verification clock; it
never consults wall time. All frozen metadata is read-only. Validation does not
attest label correctness, annotation agreement or redistribution authorization.

The manifest requires `schema_version: "1.0.0"`, `benchmark:
"BenefitBridge-Bench"`, `provenance: "team-created"`, `dataset_version`,
`reference_time`, `frozen_at`, `annotation_guide_version`,
`test_label_custodian`, and the five record arrays: `sources`, `profiles`,
`pairs`, `queries`, `claims`. Empty arrays are allowed for collection in progress;
the design's target sizes are planning targets, not fabricated acceptance counts.
Every record requires a unique identifier within its kind, positive version,
split (`development`, `validation`, `test`), and `asset` with local relative
`path` and lowercase SHA-256 `content_hash`. Hashes describe exact file bytes,
distinct from MS-006 normalized-text hashes. Store source snapshots, synthetic
profile inputs, pair specifications, discovery intents and draft claim inputs
as their respective asset files. Preserve their original bytes.

Sources require provider/program/intake/policy-template family IDs, the shared
`Lane` enum, published/synthetic origin, provider name, retrieval time and
permission metadata. Published policies require an HTTPS URL. Synthetic policies
have no published-provider URL and must use fictional provider names (human
review checks this). Profiles require synthetic origin, profile/document-template
family IDs, permission metadata, and optional hashed document assets. Private
student records are not accepted as a profile origin. Permission metadata records
the license, permission basis, permission reference, and whether redistribution
is permitted or restricted. Restricted assets stay in the custodian's authorized
local storage; validation does not grant publication permission.

Pairs reference one source and one profile. Queries specify a lane and the
complete frozen candidate source IDs. Claims reference their parent pair.
References must exist in the same split. Provider/program/intake/template and
profile/document-template groups cannot cross splits. Exact duplicate content
hashes, duplicate pairs, ambiguous IDs and duplicate query candidates fail.
Family IDs must be assigned before split allocation; the validator cannot infer
paraphrases or near duplicates from bytes. M4 should review family assignments.

An omitted or null `gold` is pending. Supplied gold requires `value`, two distinct
`annotators`, a distinct third `adjudicator`, `guide_version`, UTC `annotated_at`,
and a rationale. Source/profile values point to separately hashed annotation
assets, preserving detailed MS-002 policy/fact contracts without another public
DTO catalog. Pair values use shared `Eligibility`; claim values use shared
`ClaimStatus`. Query values are source/grade objects (integer grades 0/1/2), with
exactly one judgment for every candidate, including zero grades. Gold guide
versions must match the manifest and annotations must predate the freeze.
Annotation tooling and actual human adjudication belong to MS-024.

Keep locked test manifests/labels with the named custodian. Development and tuning
consumers must use development-only manifests and never access test labels. This
offline validator neither exposes a dataset server nor implements filesystem
permissions; custody and human review remain operational responsibilities.
Do not revise labels after inspecting model predictions. Record new dataset
versions for authorized changes, retain prior frozen assets/manifests, and hash
the manifest itself in the later evaluation-run record.

Manifest reads are capped at 10 MiB and asset reads at 32 MiB. Absolute paths,
resolved paths outside the manifest directory, unavailable/non-file assets,
hash mismatches, duplicate JSON keys, extra fields and invalid UTC timestamps
fail. No URL is fetched, provider is called, or file is modified. Repeated checks
of identical assets and the same injected clock produce identical reports.

There are no dependency, database, configuration or public API changes. Existing
unit commands collect `tests/evaluation`; the evaluation source lint/type commands
above supplement the current Makefile's backend-only source lists. CI wiring
outside this sprint's scope requires the foundation owner's handoff. The existing
PostgreSQL integration gate requires `BB_TEST_DB_URL`; this unit does not replace
or skip that gate.

## M4 handoff and verification

Implemented paths are `evaluation/schemas/__init__.py`,
`evaluation/validate_manifest.py`, this README and
`tests/evaluation/test_manifest.py`. R15.01 / US-15.01 map to versioned immutable
metadata, frozen clocks, permission records, verified asset hashes, grouped
splits and pending human annotations. M4 should review family assignments,
source/profile annotation asset contracts, permission evidence and test-label
custody. No real benchmark labels, measured model results or paid calls exist
in this change.

Actual local checks (5 October 2026), run with the frozen environment:

| Exact command | Outcome |
|---|---|
| `python -m uv run --frozen --offline python -m pytest tests/evaluation --suite unit -q` | 34 passed |
| `python -m uv run --frozen --offline python -m pytest --suite unit -q` | 605 passed, 23 integration cases deselected |
| `python -m uv run --frozen --offline ruff check backend tests evaluation` | Passed |
| `python -m uv run --frozen --offline ruff format --check backend tests evaluation` | 61 files passed |
| `python -m uv run --frozen --offline mypy` | 22 application files passed |
| `python -m uv run --frozen --offline mypy evaluation` | 2 evaluation files passed |
| `python -m uv run --frozen --offline python scripts/check_contract.py` | Deterministic OpenAPI/client matched committed artifacts |
| `pnpm.cmd --dir frontend lint` | Passed |
| `pnpm.cmd --dir frontend typecheck` | Passed |
| `pnpm.cmd --dir frontend test` | 21 passed |
| `python -m uv run --frozen --offline python -m pytest --suite integration -q --tb=short` | 2 passed; 21 setup errors require `BB_TEST_DB_URL` |

GNU Make is unavailable locally, so its underlying commands were run directly.
The repository-wide integration completion gate remains unverified; the
PostgreSQL environment and hosted CI database wiring require a separate owner
handoff. No gates were disabled.
