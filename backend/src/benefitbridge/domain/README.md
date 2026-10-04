# Shared domain contract — MS-002

`facts` defines the tagged value union and attribute compatibility. `rules` defines
the bounded AST and validates graph structure and source-bundle membership.
`dto` and `requests` define API.md payloads; `enums` defines the closed wire enums.
`errors.DomainError` is the service error interface for the later API boundary.

All models reject unknown fields. Snapshots use frozen models, tuples and a read-only
language-score mapping. Exact quantities use Decimal internally and strings on the
wire. UTC timestamps require `Z` on the wire, with up to six fractional digits;
naive timestamps, offsets and precision that Python would truncate are rejected.
Date-only values retain DAY/MONTH/YEAR precision. No validator reads the clock.

Unsupported predicate attributes are allowed for later UNKNOWN evaluation. Graph
validation does not evaluate eligibility. Source membership checks need the caller's
pinned span IDs; ownership, exact normalized-text matching, entailment, currentness,
consent and transactional version checks remain with their assigned service/adapters.
The `reference_date` field is omitted unless the reference time is EXPLICIT.

From the repository root, after the foundation's frozen setup:

```sh
uv run --frozen --offline python -m benefitbridge.domain.schema
uv run --frozen --offline python -m benefitbridge.domain.schema --check
uv run --frozen --offline pytest tests/domain
pnpm --dir frontend exec tsc --noEmit --strict --target ES2022 --module ESNext --moduleResolution bundler tests/domain.test.ts
make check
```

The generator writes `frontend/src/generated/openapi.json` and `api.ts` directly
from Pydantic. OpenAPI 3.1 has empty paths until MS-003 supplies implemented routes.
The TypeScript projection contains no independent field or enum definitions and
fails for unsupported schema shapes. Runtime cross-field and numerical constraints
stay in Python. `build_openapi()` is the integration interface for MS-003; that task
owns `make schema` and M6/MS-005 owns expanding the existing contract/test gates.

`make check` includes the foundation and domain tests, generated-artifact drift
checks and the TypeScript contract assertions in `tests/domain.test.ts`. Pytest
uses `.pytest_cache/tmp` so it does not depend on the system temporary directory.
Each run clears that test directory; concurrent runs need separate `--basetemp`
paths. Git keeps text files in LF format to match the formatting checks on Windows.

In PowerShell, use `python -m uv` and `pnpm.cmd` if executable discovery or script
execution policy prevents invoking the package managers directly:

```powershell
python -m uv sync --frozen --python 3.12
pnpm.cmd --dir frontend install --frozen-lockfile
python -m uv run --frozen --offline pytest
python -m uv run --frozen --offline ruff check backend tests
python -m uv run --frozen --offline ruff format --check backend tests
python -m uv run --frozen --offline mypy
python -m uv run --frozen --offline python -m benefitbridge.domain.schema --check
pnpm.cmd --dir frontend lint
pnpm.cmd --dir frontend test
```

`reference_data.json` contains country codes and timezone **names**, extracted from
public-domain IANA tzdb 2026e (`iso3166.tab`, Zone records and backward-compatible
Link records). Its source URL and archive SHA-256 are recorded in the file. This
keeps name validation deterministic on Windows and Linux without adding a package
dependency. It is not a timezone conversion database or an implicit policy timezone.

Tests use synthetic examples. API.md's illustrative span offsets and abbreviated
draft prose are corrected only in test inputs; invalid production inputs are rejected.
