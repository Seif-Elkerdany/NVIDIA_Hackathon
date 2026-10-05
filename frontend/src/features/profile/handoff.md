# MS-018: structured profile editor

Owner M2; reviewer M6. Prerequisites MS-017 and MS-009 are present on merged main.

## Feature interface and requirement mapping

- R02.01 / US-02.01: `ProfileScreen` and `FieldEditor` provide the shared typed
  catalog, with residence, citizenship and work authorization edited separately.
  Known empty country sets require explicit confirmation. Missing facts remain
  absent from patches; unknown values include the shared reason enum.
- R02.02 / US-02.02: GPA number and original scale remain decimal strings.
  BigInt comparison validates the range without floating-point conversion.
- R02.05 / US-02.05: current facts and read-only history display provenance,
  confirmation dates and supplied validity dates. Profile DTOs do not include
  document issue/source dates, so those dates are explicitly unavailable rather
  than inferred from confirmation dates. Support does not verify the issuer.
- R02.04 / US-02.04: patches pin `base_profile_version_id`, require user review,
  retain drafts after 409 and failed reload, and never reapply stale edits.
  Changed values become self-report without copying earlier document citations.
  Timeout retries preserve the original command body and idempotency key.
- R12.01 / US-12.01: labeled keyboard-accessible controls, responsive groups,
  visible loading/error/cancelled/empty states and optional-document navigation.
  React escapes every value; no raw HTML rendering is used.

`createProfileApi` consumes the shared bearer client through a typed
`ProfileWireClient`. `ProfileScreen` requires the authenticated subject and
session generation as `identity`; those values separate private query caches
and unmount drafts on account changes. It never receives or persists tokens.
Production uses existing HTTP transport; synthetic adapters reside in tests.

## Integration handoff

The shared API client initially lacks profile PATCH, and the app mounts a
placeholder at /profile. The user explicitly declined the proposed two-file
M2 integration handoff and requested the original scope only. Therefore this
merge delivers the feature interface and isolated development/test composition;
the shared client and application route remain unchanged. Application integration
and the overall sprint completion gate remain unverified. The next authorized M2
integration must add generated-type `patchProfile` with Idempotency-Key to the
existing transport and mount `ProfileScreen` inside ProcessingGuard. Do not
replace this missing wiring with a production mock or a second HTTP client.

## Design reference lock and review

Primary references: existing shell tokens, authentication screens, and bundled
Refero form/focus craft guidance. Keep the established off-white canvas, dark
ink, green accent, Segoe UI, spacing and modest radii. Use grouped fieldsets
with visible saved values and provenance. Preserve dates, unknowns and separate
country facts as the product's distinctive evidence presentation. Native
controls and explicit conflict review fit this settings workflow. No media or
animation is needed. Mobile uses a single column and desktop two columns.

Decision ledger: generated types rather than a parallel DTO; original decimal
strings rather than normalized scores; field-local provenance rather than a
summary badge; explicit confirmation and reload rather than autosave; missing
source dates labeled unavailable rather than invented. Desktop 1280px and
mobile 390px screenshots were inspected. Local subjective rubric review:
AI Slop 2/10 (adapted conventional form layout and familiar typography),
distinctiveness 8/10 (evidence-first facts, clear source limitations and explicit
unknown/conflict interactions). These are design judgments, not measured gates.

## Verification of the scoped delivery

From the repository root, PowerShell uses pnpm.cmd:

- `pnpm.cmd --dir frontend lint`: passed formatting and TypeScript.
- `pnpm.cmd --dir frontend test`: 33 tests passed, including 12 profile cases.
  The corresponding API test imports the profile suite so ordinary CI runs it.
- `pnpm.cmd --dir frontend build`: passed. Existing Vite third-party directive
  and large-chunk notices remain; no dependency or build configuration changes.
- `python -m uv run --frozen --offline python scripts/check_contract.py`: passed;
  deterministic OpenAPI/client match the backend, with no regeneration needed.
- `python frontend/tests/profile_browser.py http://127.0.0.1:5173`: passed
  synthetic GPA/unknowns, keyboard focus, mobile overflow, history pagination,
  conflict/reload failure, idempotent retry, identity fencing, loading cancellation
  and initial error recovery. Run against `pnpm.cmd --dir frontend dev --port 5173`
  with Playwright and local Edge installed. No paid endpoints are contacted.
- `python -m uv run --frozen --offline ruff check backend tests frontend/tests/profile_browser.py`:
  passed; `python -m uv run --frozen --offline ruff format --check backend tests frontend/tests/profile_browser.py`
  also passed (81 files).
- `python -m uv run --frozen --offline mypy`: passed, 31 source files.
- `python -m uv run --frozen --offline python -m pytest tests/foundation/test_scaffold.py tests/domain/test_schema.py`:
  11 passed.
- `python -m uv run --frozen --offline ruff check frontend/tests/profile_browser.py`:
  passed. GNU Make is unavailable; corresponding gate commands are run directly.

No schema, migration, API endpoint, configuration or dependency changes.
Reviewer focus: original GPA/unknown semantics, history/privacy on identity
changes, replay of ambiguous saves, and the remaining route/client integration.
