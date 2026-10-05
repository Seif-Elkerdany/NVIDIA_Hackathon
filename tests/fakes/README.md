# MS-005 reusable offline harness — M6 handoff to M4

Branch: `feat/ms-005-quality`, based on `main` at `d154fcc`. MS-001 prerequisite
commit `25254da` is an ancestor; frozen configuration, dependency locks and commands
exist. MS-002/003 ports and schemas are reused, without editing their contracts.

## Delivered interfaces and requirement mapping

- R15.05 / US-15.05: `tests/conftest.py` and `tests/fakes/providers.py` expose fresh
  `fake_clock`, `fake_llm`, `fake_search`, `fake_fetch`, `fake_dependencies` and
  `fixture_settings` fixtures. Scripted LLM failures/recovery have exact call
  counts; clocks advance without sleeping; fetch timestamps use that clock.
  Existing MS-003 storage/repository fakes are reused. No participant study,
  benchmark quality or controlled-load result is claimed by this foundational unit.
- R16.01 / US-16.01: `scripts/check_contract.py` uses MS-003's existing exporter to
  compare deterministic OpenAPI/client bytes against committed files. Missing,
  modified or nondeterministic artifacts fail. The gate never rewrites artifacts
  or maintains parallel DTOs. Ruff, mypy, strict frontend checks and unit tests
  also fail the CI job on nonzero status.
- R16.02 / US-16.02: `.github/workflows/ci.yml` installs frozen dependencies, then
  runs fail-fast offline unit, integration and contract checks in a new Linux
  network namespace with only loopback, no external route, dropped capabilities,
  cleared supplementary groups and no privilege escalation. Isolation failure
  is a failure, covering Node and subprocesses as well as Python. Dependency/tool
  downloads happen before test isolation; no provider credentials are configured.
  Integration gates use the same pinned PostgreSQL 17 image as development, with
  `--network none`, TCP listening disabled and an authenticated filesystem Unix
  socket shared with the runner. `BB_TEST_DB_URL` selects that socket, which stays
  accessible inside the offline namespace. The disposable container and its data
  volume are removed even when a gate fails.

The root Python guard runs before test collection and denies external DNS,
TCP connect/connect_ex and UDP sendto. Numeric loopback remains available for
Windows asyncio socketpairs and future local services. Synthetic environment
fixtures strip application settings/credentials and prevent reading a developer
`.env`. Fixture adapters never make external requests or fall back to live SDKs.

## Commands

```sh
uv run --frozen --offline python -m pytest --suite unit
uv run --frozen --offline python -m pytest --suite integration
uv run --frozen --offline python scripts/check_contract.py
```

Default `pytest` runs both ordinary suites, excluding `live`. Mark tests with
`@pytest.mark.integration` or `@pytest.mark.live`; paths under `tests/integration/`
or `tests/live/` receive those classifications automatically. An empty selected
suite retains pytest's nonzero exit, never a successful placeholder.

Current integration checks compose real FastAPI dependency injection with fake
ports and verify mutable-adapter isolation. They do not claim PostgreSQL, queue
or migration coverage; those modules and drivers are not implemented yet. The
existing Makefile database-integration gate is deliberately unchanged.

Paid execution is separate, local and disabled by default. A later authorized,
implemented live suite must be selected with all three explicit inputs:

```sh
uv run --frozen --offline python -m pytest --suite live --allow-paid-live --live-budget-microusd <approved-positive-budget>
```

This is an opt-in gate, not a replacement for the provider's real budget ledger.
`paid_live_budget_microusd` exposes the approved cap to future live fixtures. All
live opt-in is rejected when `CI` or `GITHUB_ACTIONS` is present. No live tests or
paid smoke tests were executed or fabricated in MS-005.

## Actual local verification

Windows commands used `python -m uv` and `pnpm.cmd`:

| Command | Actual outcome |
| --- | --- |
| `uv run --frozen --offline python -m pytest tests/quality -q` | 19 passed, including drift, missing artifact, failing lint, live exclusion and CI rejection regressions |
| `uv run --frozen --offline python -m pytest --suite unit -q` | 362 passed; 2 integration tests deselected |
| `uv run --frozen --offline python -m pytest --suite integration -q` | 2 passed; 362 unit tests deselected |
| `uv run --frozen --offline ruff check backend tests scripts/check_contract.py` | Passed |
| `uv run --frozen --offline ruff format --check backend tests scripts/check_contract.py` | Passed |
| `uv run --frozen --offline mypy` | Passed; 14 application files |
| `uv run --frozen --offline mypy --follow-imports silent tests/fakes tests/conftest.py` | Passed; 4 harness files |
| `uv run --frozen --offline python scripts/check_contract.py` | Passed; deterministic committed artifacts match |
| `pnpm --dir frontend lint` | Passed formatting and strict TypeScript |
| `pnpm --dir frontend test` | 11 passed |
| `pnpm --dir frontend build` | Passed production build |
| `actionlint -shellcheck= -pyflakes= .github/workflows/ci.yml` | Passed using checksum-verified actionlint 1.7.12 |

GNU Make is unavailable locally; available Makefile lint/type/unit/contract
commands were executed directly and expanded by CI. No dependencies, package
locks, API endpoints, application config, registry, schema or migrations changed.
The listed file scope is preserved. New negative tests use synthetic temporary
artifacts and separate child pytest temp roots to preserve parent test files.

## Remaining verification and reviewer focus

Local tests and workflow validation passed. GitHub's Ubuntu runner also executed
the complete network-isolated gate successfully at `314b22b`:
[hosted CI evidence](https://github.com/Seif-Elkerdany/Seekstride/actions/runs/37232410539).
This verifies Linux isolation, dropped privileges, lint, types, both Python suites,
frontend tests, contract comparison and the production bundle on a fresh checkout.
The harness initializes missing pytest cache parents, including child test roots;
CI preserves the invoking runner's home when dropping root privileges so uv uses
its existing cache. M4 review has not been performed.

M4 focus: network isolation and privilege dropping, paid-suite authorization,
test-selection denominators, fresh protocol-compliant adapters, read-only
generated-contract drift detection, and downstream database coverage boundaries.
