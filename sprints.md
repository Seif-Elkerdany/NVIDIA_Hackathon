# BenefitBridge — Dependency-Ordered Micro-Sprints

**BenefitBridge · Best Apps and Agents · Six-person implementation package · 4 October 2026**

[requirements.md](requirements.md) | [userStory.md](userStory.md) | [sprints.md](sprints.md) | [design.md](design.md) | [API.md](API.md) | [plan.md](plan.md) | [agent.md](agent.md)

## Operating definition

There are **89 micro-sprints: 85 P0 and four P1**. Each is one bounded AI implementation assignment with one copy-paste prompt in plan.md, one owner, explicit write scope and concrete scenario checks. A micro-sprint is not a multi-day Agile sprint. Most are estimated at 2.5–3 human-hours including local implementation/checking and handoff preparation; AI generation time alone is not the estimate. Peer review, real-provider experiments and human research still require people.

Prerequisites mean **merged, interface available and its own acceptance checks passed**, not merely started. Task numbers are a valid topological order, but the team must use the dependency graph and owner availability, not execute all 89 serially. No P0 task depends on a P1 task. An owner works on one code unit at a time; independent tasks owned by different members can overlap. The owner-constrained schedule in plan.md is the operational ordering. Unlisted transitive prerequisites still apply through their parent tasks.

Expected input is the seven-file contract, the relevant requirement/story/API definitions, a clean scoped branch and the named prerequisite outputs. Expected outcome is the specific implementation described below, checked and ready for peer review. Exact prompts repeat these task-specific inputs and outputs rather than leaving placeholders to fill in.

## Index and immediate prerequisites

| ID | Priority | Owner | Micro-sprint | Must wait for | Estimate h |
| --- | --- | --- | --- | --- | --- |
| MS-001 | P0 | M1 | Repository, reproducible commands and configuration | None — project documents only | 3 |
| MS-002 | P0 | M4 | Shared domain schemas and enums | MS-001 | 3 |
| MS-003 | P0 | M3 | Provider and stage interfaces | MS-002 | 3 |
| MS-004 | P0 | M2 | Web shell and state conventions | MS-002 | 2.5 |
| MS-005 | P0 | M6 | CI and reusable test harness | MS-001 | 2.5 |
| MS-006 | P0 | M5 | Source and normalized span contract | MS-002 | 2.5 |
| MS-007 | P0 | M1 | Account and profile schema | MS-002, MS-005 | 3 |
| MS-008 | P0 | M1 | JWT authentication and account API | MS-007, MS-003 | 3 |
| MS-009 | P0 | M2 | Managed-auth and consent screens | MS-008, MS-004 | 2.5 |
| MS-010 | P0 | M3 | Model registry and capability preflight | MS-003 | 2.5 |
| MS-011 | P0 | M4 | Deterministic fact predicates | MS-002, MS-005 | 3 |
| MS-012 | P0 | M5 | Bounded digital PDF parsing | MS-006, MS-003, MS-005 | 3 |
| MS-013 | P0 | M6 | Dataset manifest and split validator | MS-002, MS-005 | 2.5 |
| MS-014 | P0 | M1 | Public sources and opportunity schema | MS-007, MS-006 | 2.5 |
| MS-015 | P0 | M1 | Durable runs, outbox, budget and receipt schema | MS-014, MS-003 | 3 |
| MS-016 | P0 | M3 | Leased PostgreSQL job dispatcher | MS-015, MS-003, MS-005 | 3 |
| MS-017 | P0 | M1 | Versioned profile read and edit API | MS-008, MS-015 | 3 |
| MS-018 | P0 | M2 | Structured profile editor | MS-017, MS-009 | 2.5 |
| MS-019 | P0 | M3 | Atomic cost reservations and fairness | MS-015, MS-010 | 3 |
| MS-020 | P0 | M3 | Nebius structured inference adapter | MS-010, MS-019, MS-003 | 3 |
| MS-021 | P0 | M5 | Safe fetching and untrusted-content boundary | MS-003, MS-006, MS-005 | 3 |
| MS-022 | P0 | M5 | Tavily discovery and source fetch adapter | MS-003, MS-019, MS-021 | 3 |
| MS-023 | P0 | M4 | Three-valued graph evaluation | MS-011, MS-002 | 3 |
| MS-024 | P0 | M6 | Annotation and adjudication tooling | MS-013 | 2.5 |
| MS-025 | P0 | M1 | Private evidence schema | MS-015 | 2.5 |
| MS-026 | P0 | M1 | Document upload and read API | MS-025, MS-008, MS-003 | 3 |
| MS-027 | P0 | M5 | PDF to reviewable fact candidates | MS-026, MS-012, MS-020, MS-016 | 3 |
| MS-028 | P0 | M1 | Fact candidate review API | MS-027, MS-017 | 2.5 |
| MS-029 | P0 | M2 | Upload and fact review experience | MS-028, MS-018 | 2.5 |
| MS-030 | P0 | M3 | Run control and authenticated event stream | MS-016, MS-008 | 3 |
| MS-031 | P0 | M2 | Durable progress components | MS-030, MS-004, MS-009 | 2.5 |
| MS-032 | P0 | M5 | Public snapshot storage and authority resolution | MS-014, MS-022, MS-006 | 3 |
| MS-033 | P0 | M5 | Conservative opportunity canonicalization | MS-032 | 2.5 |
| MS-034 | P0 | M3 | Bounded redacted goal planner | MS-020, MS-022, MS-002 | 2.5 |
| MS-035 | P0 | M4 | Requirement AST extraction | MS-020, MS-006, MS-002 | 3 |
| MS-036 | P0 | M4 | Requirement publication validator | MS-035, MS-023 | 3 |
| MS-037 | P0 | M5 | Owner-scoped evidence retrieval | MS-028, MS-006 | 2.5 |
| MS-038 | P0 | M1 | Requirement and evaluation persistence | MS-025, MS-014 | 3 |
| MS-039 | P0 | M4 | Bounded semantic predicate evaluator | MS-020, MS-037, MS-023 | 3 |
| MS-040 | P0 | M4 | Eligibility aggregation and publication guards | MS-039, MS-036 | 3 |
| MS-041 | P0 | M4 | Decision and citation verification | MS-040 | 3 |
| MS-042 | P0 | M4 | Availability, fit, readiness and sorting | MS-040, MS-011 | 2.5 |
| MS-043 | P0 | M3 | Discovery stage graph and candidate persistence | MS-034, MS-033, MS-036, MS-038, MS-016, MS-021 | 3 |
| MS-044 | P0 | M3 | Evaluation workflow stage | MS-041, MS-042, MS-038, MS-016 | 3 |
| MS-045 | P0 | M5 | Public opportunity and source reads | MS-038, MS-033, MS-008 | 2.5 |
| MS-046 | P0 | M3 | Discovery and URL-import commands | MS-043, MS-044, MS-030, MS-017 | 2.5 |
| MS-047 | P0 | M4 | Explicit evaluation API | MS-044, MS-045, MS-008 | 2.5 |
| MS-048 | P0 | M2 | Discovery form and results feed | MS-046, MS-045, MS-031, MS-018 | 2.5 |
| MS-049 | P0 | M2 | Decision and evidence detail screen | MS-047, MS-048 | 2.5 |
| MS-050 | P0 | M3 | Clarification persistence and resumption | MS-044, MS-017, MS-030 | 3 |
| MS-051 | P0 | M2 | Targeted fact clarification UI | MS-050, MS-049 | 2.5 |
| MS-052 | P0 | M1 | Application and shortlist schema | MS-038 | 3 |
| MS-053 | P0 | M1 | Saved opportunity endpoints | MS-052, MS-045 | 2.5 |
| MS-054 | P0 | M2 | Shortlist screen | MS-053, MS-049 | 2.5 |
| MS-055 | P0 | M4 | Deterministic application checklist builder | MS-042, MS-036 | 2.5 |
| MS-056 | P0 | M4 | Application and checklist API | MS-052, MS-055, MS-047 | 3 |
| MS-057 | P0 | M3 | Grounded statement generation stage | MS-020, MS-056 | 3 |
| MS-058 | P0 | M4 | Draft claim validation and acceptance rules | MS-057, MS-041 | 3 |
| MS-059 | P0 | M3 | Draft versions, review and export API | MS-058, MS-056, MS-016 | 3 |
| MS-060 | P0 | M2 | Application preparation workspace | MS-059, MS-054 | 2.5 |
| MS-061 | P0 | M5 | Source refresh and structural change detection | MS-043, MS-047 | 3 |
| MS-062 | P0 | M1 | Dependency invalidation handler | MS-052, MS-016, MS-061, MS-017 | 3 |
| MS-063 | P0 | M5 | Document revoke and purge workflow | MS-062, MS-026, MS-016 | 3 |
| MS-064 | P0 | M1 | Account purge and capability receipt | MS-063, MS-008, MS-015 | 3 |
| MS-065 | P0 | M6 | Two-tenant and deletion security suite | MS-064, MS-059, MS-050, MS-030 | 3 |
| MS-066 | P0 | M6 | Failure and concurrency recovery suite | MS-044, MS-064, MS-019 | 3 |
| MS-067 | P0 | M3 | Public reuse and private cache invalidation | MS-062, MS-044, MS-019 | 2.5 |
| MS-068 | P0 | M3 | Usage and capability read endpoints | MS-019, MS-008, MS-010 | 2.5 |
| MS-069 | P0 | M2 | Usage, settings and deletion controls | MS-068, MS-064, MS-060 | 2.5 |
| MS-070 | P1 | M1 | Optional watch persistence | MS-052 | 2.5 |
| MS-071 | P1 | M5 | Optional saved-page watch scheduler | MS-070, MS-061, MS-062 | 2.5 |
| MS-072 | P1 | M5 | Optional watch and notification API | MS-071, MS-008 | 2.5 |
| MS-073 | P1 | M2 | Optional watch controls and notification inbox | MS-072, MS-054 | 2.5 |
| MS-074 | P0 | M3 | Redacted operational metrics and health | MS-016, MS-010, MS-067, MS-068 | 2.5 |
| MS-075 | P0 | M3 | Production dependency composition | MS-074, MS-046, MS-050, MS-059, MS-064, MS-027, MS-061 | 3 |
| MS-076 | P0 | M6 | API and generated client contract gate | MS-075 | 3 |
| MS-077 | P0 | M6 | Requirement and grounding evaluation harness | MS-024, MS-036 | 2.5 |
| MS-078 | P0 | M6 | Eligibility and coverage evaluation harness | MS-024, MS-041 | 3 |
| MS-079 | P0 | M5 | Frozen and live discovery evaluation harness | MS-024, MS-033, MS-034 | 2.5 |
| MS-080 | P0 | M6 | Paired model and cost experiment runner | MS-078, MS-077, MS-019, MS-010 | 3 |
| MS-081 | P0 | M2 | Main journey browser acceptance suite | MS-069, MS-051, MS-076 | 3 |
| MS-082 | P0 | M6 | Capacity and queue load experiment | MS-075, MS-066 | 2.5 |
| MS-083 | P0 | M1 | Deployment and migration release assets | MS-075, MS-065, MS-066 | 3 |
| MS-084 | P0 | M5 | Isolated synthetic demo scenarios and reset | MS-075, MS-056, MS-027, MS-083 | 3 |
| MS-085 | P0 | M6 | Reproducible result report generator | MS-080, MS-079, MS-082, MS-065 | 2.5 |
| MS-086 | P0 | M2 | User study task and observation kit | MS-049, MS-060 | 2.5 |
| MS-087 | P0 | M2 | Video storyboard and submission materials | MS-084, MS-085, MS-086 | 2.5 |
| MS-088 | P0 | M1 | Operations, retention and incident runbook | MS-083, MS-064, MS-074 | 2.5 |
| MS-089 | P0 | M6 | Release readiness evidence collector | MS-076, MS-081, MS-085, MS-088, MS-087 | 3 |

## Detailed task cards

### MS-001 — Repository, reproducible commands and configuration

- **Owner / reviewer / priority:** M1 / M3 / P0.
- **Strict prerequisites:** None; this is the repository foundation.
- **Requirements:** R16.01, R16.02.
- **Stories:** US-16.01, US-16.02.
- **Expected input:** relevant package contracts and the merged artifacts from every prerequisite above. External adapters use deterministic fixtures until configured live integration is explicitly run.
- **Write scope:** `pyproject.toml`; `uv.lock`; `frontend/package.json`; `frontend/pnpm-lock.yaml`; `Makefile`; `.env.example`; `compose.yaml`; `backend/src/benefitbridge/config.py`; `backend/src/benefitbridge/main.py`; directly corresponding tests, plus mechanical generated contracts where needed.
- **Implementation / expected outcome:** Create Python 3.12 FastAPI and TypeScript React/Vite workspaces, pinned lockfiles, local Postgres 17, commands and strict configuration validation. main.py delegates routers to the explicit registry contract in design.md; no production fake providers.
- **API operations:** No new public endpoint; preserve the existing API contract.
- **Acceptance scenarios:** Clean checkout installs; make check passes scaffold checks; missing production secrets fail startup.
- **Handoff:** diff, actual check results, schema/config impact and reviewer note. Copy the matching prompt from plan.md.

### MS-002 — Shared domain schemas and enums

- **Owner / reviewer / priority:** M4 / M6 / P0.
- **Strict prerequisites:** MS-001 (Repository, reproducible commands and configuration)
- **Requirements:** R02.01, R02.02, R05.03, R06.01, R06.02, R07.01, R08.01, R16.01.
- **Stories:** US-02.01, US-02.02, US-05.03, US-06.01, US-06.02, US-07.01, US-08.01, US-16.01.
- **Expected input:** relevant package contracts and the merged artifacts from every prerequisite above. External adapters use deterministic fixtures until configured live integration is explicitly run.
- **Write scope:** `backend/src/benefitbridge/domain/`; `frontend/src/generated/`; directly corresponding tests, plus mechanical generated contracts where needed.
- **Implementation / expected outcome:** Implement the DTOs, tagged fact union, rule AST, status enums and pure validation in API.md. Export a minimal OpenAPI 3.1 components-only document from the Pydantic models and generate frontend types; the ports task later adds implemented routes to this same schema source.
- **API operations:** No new public endpoint; preserve the existing API contract.
- **Acceptance scenarios:** Reject extra fields, wrong GPA tags, dangling graph nodes, ambiguous timestamps and invalid enum values.
- **Handoff:** diff, actual check results, schema/config impact and reviewer note. Copy the matching prompt from plan.md.

### MS-003 — Provider and stage interfaces

- **Owner / reviewer / priority:** M3 / M1 / P0.
- **Strict prerequisites:** MS-002 (Shared domain schemas and enums)
- **Requirements:** R10.02, R14.02, R16.01.
- **Stories:** US-10.02, US-14.02, US-16.01.
- **Expected input:** relevant package contracts and the merged artifacts from every prerequisite above. External adapters use deterministic fixtures until configured live integration is explicitly run.
- **Write scope:** `backend/src/benefitbridge/ports.py`; `backend/src/benefitbridge/composition.py`; `backend/src/benefitbridge/api/registry.py`; `scripts/export_openapi.py`; `scripts/generate_client.sh`; directly corresponding tests, plus mechanical generated contracts where needed.
- **Implementation / expected outcome:** Define Protocols for clock, LLM, search, fetch, storage, repositories and stage handlers. Create explicit allowlisted optional-development router loading and typed dependency injection. Production requires all P0 routers and handlers. Add deterministic OpenAPI/client generation commands.
- **API operations:** No new public endpoint; preserve the existing API contract.
- **Acceptance scenarios:** Fake adapters implement the same protocols; a missing P0 handler prevents production readiness; OpenAPI generation is stable.
- **Handoff:** diff, actual check results, schema/config impact and reviewer note. Copy the matching prompt from plan.md.

### MS-004 — Web shell and state conventions

- **Owner / reviewer / priority:** M2 / M6 / P0.
- **Strict prerequisites:** MS-002 (Shared domain schemas and enums)
- **Requirements:** R12.01, R12.03, R12.04.
- **Stories:** US-12.01, US-12.03, US-12.04.
- **Expected input:** relevant package contracts and the merged artifacts from every prerequisite above. External adapters use deterministic fixtures until configured live integration is explicitly run.
- **Write scope:** `frontend/src/app/`; `frontend/src/components/`; `frontend/src/lib/api.ts`; `frontend/src/styles/`; directly corresponding tests, plus mechanical generated contracts where needed.
- **Implementation / expected outcome:** Build accessible navigation, route shells, API error display, request cancellation and design tokens. Use generated types and a typed mock transport only in tests/development.
- **API operations:** No new public endpoint; preserve the existing API contract.
- **Acceptance scenarios:** Keyboard focus and unknown/error/empty states render; raw HTML is never used for model output.
- **Handoff:** diff, actual check results, schema/config impact and reviewer note. Copy the matching prompt from plan.md.

### MS-005 — CI and reusable test harness

- **Owner / reviewer / priority:** M6 / M4 / P0.
- **Strict prerequisites:** MS-001 (Repository, reproducible commands and configuration)
- **Requirements:** R15.05, R16.01, R16.02.
- **Stories:** US-15.05, US-16.01, US-16.02.
- **Expected input:** relevant package contracts and the merged artifacts from every prerequisite above. External adapters use deterministic fixtures until configured live integration is explicitly run.
- **Write scope:** `tests/conftest.py`; `tests/fakes/`; `.github/workflows/ci.yml`; `scripts/check_contract.py`; directly corresponding tests, plus mechanical generated contracts where needed.
- **Implementation / expected outcome:** Wire lint, type checks, unit/integration test commands and deterministic clock/provider fixtures. Separate paid live tests from ordinary CI.
- **API operations:** No new public endpoint; preserve the existing API contract.
- **Acceptance scenarios:** CI cannot contact paid endpoints; failed lint and mismatched generated schemas fail the gate.
- **Handoff:** diff, actual check results, schema/config impact and reviewer note. Copy the matching prompt from plan.md.

### MS-006 — Source and normalized span contract

- **Owner / reviewer / priority:** M5 / M4 / P0.
- **Strict prerequisites:** MS-002 (Shared domain schemas and enums)
- **Requirements:** R03.03, R05.01, R05.03, R06.03.
- **Stories:** US-03.03, US-05.01, US-05.03, US-06.03.
- **Expected input:** relevant package contracts and the merged artifacts from every prerequisite above. External adapters use deterministic fixtures until configured live integration is explicitly run.
- **Write scope:** `backend/src/benefitbridge/sources/contracts.py`; `tests/sources/test_spans.py`; directly corresponding tests, plus mechanical generated contracts where needed.
- **Implementation / expected outcome:** Define normalized Unicode text, page markers, half-open character spans, quote validation and source authority metadata. Hash normalized UTF-8 text independently of raw-file hashes.
- **API operations:** No new public endpoint; preserve the existing API contract.
- **Acceptance scenarios:** Round-trip spans including Unicode, PDF page boundaries and invalid offsets are deterministic.
- **Handoff:** diff, actual check results, schema/config impact and reviewer note. Copy the matching prompt from plan.md.

### MS-007 — Account and profile schema

- **Owner / reviewer / priority:** M1 / M3 / P0.
- **Strict prerequisites:** MS-002 (Shared domain schemas and enums), MS-005 (CI and reusable test harness)
- **Requirements:** R01.03, R02.01, R02.04, R13.01.
- **Stories:** US-01.03, US-02.01, US-02.04, US-13.01.
- **Expected input:** relevant package contracts and the merged artifacts from every prerequisite above. External adapters use deterministic fixtures until configured live integration is explicitly run.
- **Write scope:** `backend/migrations/versions/0001_identity.py`; `backend/src/benefitbridge/db/base.py`; `backend/src/benefitbridge/db/profiles.py`; directly corresponding tests, plus mechanical generated contracts where needed.
- **Implementation / expected outcome:** Create accounts, profiles, immutable profile_versions, facts, profile_version_facts and deleted_subjects HMAC deny ledger; transaction-local owner context, RLS policies and owner-consistent foreign keys.
- **API operations:** No new public endpoint; preserve the existing API contract.
- **Acceptance scenarios:** Migrate empty DB; cross-owner links fail; version uniqueness holds under concurrent writes.
- **Handoff:** diff, actual check results, schema/config impact and reviewer note. Copy the matching prompt from plan.md.

### MS-008 — JWT authentication and account API

- **Owner / reviewer / priority:** M1 / M3 / P0.
- **Strict prerequisites:** MS-007 (Account and profile schema), MS-003 (Provider and stage interfaces)
- **Requirements:** R01.01, R01.02, R01.03, R01.04, R13.01.
- **Stories:** US-01.01, US-01.02, US-01.03, US-01.04, US-13.01.
- **Expected input:** relevant package contracts and the merged artifacts from every prerequisite above. External adapters use deterministic fixtures until configured live integration is explicitly run.
- **Write scope:** `backend/src/benefitbridge/auth.py`; `backend/src/benefitbridge/api/accounts.py`; `tests/api/test_accounts.py`; directly corresponding tests, plus mechanical generated contracts where needed.
- **Implementation / expected outcome:** Verify managed-auth JWT against issuer JWKS with bounded cache and fixed algorithms. Initialize account/profile atomically; implement consent/name/timezone update and active-account guard. Check the deleted_subjects deny ledger before bootstrap so an unexpired token cannot recreate a purged account.
- **API operations:** get_me, patch_me
- **Acceptance scenarios:** Expired, wrong-issuer and tombstoned credentials fail; concurrent bootstrap creates one account.
- **Handoff:** diff, actual check results, schema/config impact and reviewer note. Copy the matching prompt from plan.md.

### MS-009 — Managed-auth and consent screens

- **Owner / reviewer / priority:** M2 / M6 / P0.
- **Strict prerequisites:** MS-008 (JWT authentication and account API), MS-004 (Web shell and state conventions)
- **Requirements:** R01.01, R01.02, R12.01.
- **Stories:** US-01.01, US-01.02, US-12.01.
- **Expected input:** relevant package contracts and the merged artifacts from every prerequisite above. External adapters use deterministic fixtures until configured live integration is explicitly run.
- **Write scope:** `frontend/src/features/auth/`; directly corresponding tests, plus mechanical generated contracts where needed.
- **Implementation / expected outcome:** Use Supabase Auth SDK for signup/login/reset and memory-only sessions; API bearer injection, explicit re-login after reload and consent screen. Configure recovery route without storing tokens in localStorage.
- **API operations:** No new public endpoint; preserve the existing API contract.
- **Acceptance scenarios:** Session expiry returns to login; decline consent blocks processing; auth URLs do not leak tokens into logs.
- **Handoff:** diff, actual check results, schema/config impact and reviewer note. Copy the matching prompt from plan.md.

### MS-010 — Model registry and capability preflight

- **Owner / reviewer / priority:** M3 / M1 / P0.
- **Strict prerequisites:** MS-003 (Provider and stage interfaces)
- **Requirements:** R14.02.
- **Stories:** US-14.02.
- **Expected input:** relevant package contracts and the merged artifacts from every prerequisite above. External adapters use deterministic fixtures until configured live integration is explicitly run.
- **Write scope:** `backend/src/benefitbridge/inference/registry.py`; `scripts/preflight_models.py`; directly corresponding tests, plus mechanical generated contracts where needed.
- **Implementation / expected outcome:** Implement FAST, REASON and optional DEEP roles from environment/registry configuration with price version, context limits and schema/tool support. Provide explicit opt-in real preflight using tiny nonprivate prompts.
- **API operations:** No new public endpoint; preserve the existing API contract.
- **Acceptance scenarios:** Missing DEEP is allowed; missing REASON prevents inference readiness; no tests assume model names or prices.
- **Handoff:** diff, actual check results, schema/config impact and reviewer note. Copy the matching prompt from plan.md.

### MS-011 — Deterministic fact predicates

- **Owner / reviewer / priority:** M4 / M6 / P0.
- **Strict prerequisites:** MS-002 (Shared domain schemas and enums), MS-005 (CI and reusable test harness)
- **Requirements:** R02.02, R06.05, R07.02.
- **Stories:** US-02.02, US-06.05, US-07.02.
- **Expected input:** relevant package contracts and the merged artifacts from every prerequisite above. External adapters use deterministic fixtures until configured live integration is explicitly run.
- **Write scope:** `backend/src/benefitbridge/eligibility/predicates.py`; `tests/eligibility/test_predicates.py`; directly corresponding tests, plus mechanical generated contracts where needed.
- **Implementation / expected outcome:** Implement Decimal comparisons, set/category membership, compatible GPA, date interval precision and union-of-overlapping experience intervals. Unsupported conversion returns UNKNOWN.
- **API operations:** No new public endpoint; preserve the existing API contract.
- **Acceptance scenarios:** Equality boundaries, absent scale, timezones, unknown date precision and overlapping jobs are covered.
- **Handoff:** diff, actual check results, schema/config impact and reviewer note. Copy the matching prompt from plan.md.

### MS-012 — Bounded digital PDF parsing

- **Owner / reviewer / priority:** M5 / M4 / P0.
- **Strict prerequisites:** MS-006 (Source and normalized span contract), MS-003 (Provider and stage interfaces), MS-005 (CI and reusable test harness)
- **Requirements:** R03.01, R03.03, R03.04.
- **Stories:** US-03.01, US-03.03, US-03.04.
- **Expected input:** relevant package contracts and the merged artifacts from every prerequisite above. External adapters use deterministic fixtures until configured live integration is explicitly run.
- **Write scope:** `backend/src/benefitbridge/documents/parser.py`; `tests/documents/test_parser.py`; directly corresponding tests, plus mechanical generated contracts where needed.
- **Implementation / expected outcome:** Parse in an isolated subprocess with byte/page/time/memory limits. Preserve page-normalized spans, detect unreadable text and reject encrypted or malformed PDFs.
- **API operations:** No new public endpoint; preserve the existing API contract.
- **Acceptance scenarios:** 20 versus 21 pages, forged content types, decompression stress and empty/scanned pages produce expected typed failures.
- **Handoff:** diff, actual check results, schema/config impact and reviewer note. Copy the matching prompt from plan.md.

### MS-013 — Dataset manifest and split validator

- **Owner / reviewer / priority:** M6 / M4 / P0.
- **Strict prerequisites:** MS-002 (Shared domain schemas and enums), MS-005 (CI and reusable test harness)
- **Requirements:** R15.01.
- **Stories:** US-15.01.
- **Expected input:** relevant package contracts and the merged artifacts from every prerequisite above. External adapters use deterministic fixtures until configured live integration is explicitly run.
- **Write scope:** `evaluation/schemas/`; `evaluation/validate_manifest.py`; `evaluation/README.md`; directly corresponding tests, plus mechanical generated contracts where needed.
- **Implementation / expected outcome:** Define source/profile/pair/query/claim schemas and provider-family/profile-family grouped splits; license/permission metadata, clock and content hashes. Build validation only, never invent gold labels.
- **API operations:** No new public endpoint; preserve the existing API contract.
- **Acceptance scenarios:** Duplicate hashes and leakage across splits fail; absent labels are marked pending rather than generated as truth.
- **Handoff:** diff, actual check results, schema/config impact and reviewer note. Copy the matching prompt from plan.md.

### MS-014 — Public sources and opportunity schema

- **Owner / reviewer / priority:** M1 / M3 / P0.
- **Strict prerequisites:** MS-007 (Account and profile schema), MS-006 (Source and normalized span contract)
- **Requirements:** R05.01, R05.02, R05.03, R06.03.
- **Stories:** US-05.01, US-05.02, US-05.03, US-06.03.
- **Expected input:** relevant package contracts and the merged artifacts from every prerequisite above. External adapters use deterministic fixtures until configured live integration is explicitly run.
- **Write scope:** `backend/migrations/versions/0002_sources.py`; `backend/src/benefitbridge/db/sources.py`; directly corresponding tests, plus mechanical generated contracts where needed.
- **Implementation / expected outcome:** Create provider registry, source snapshots/spans, opportunities, immutable opportunity_versions and version_sources. Enforce current-version pointers and canonical unique identities.
- **API operations:** No new public endpoint; preserve the existing API contract.
- **Acceptance scenarios:** Distinct intakes remain distinct; snapshot hash deduplication preserves fetch records and citations.
- **Handoff:** diff, actual check results, schema/config impact and reviewer note. Copy the matching prompt from plan.md.

### MS-015 — Durable runs, outbox, budget and receipt schema

- **Owner / reviewer / priority:** M1 / M3 / P0.
- **Strict prerequisites:** MS-014 (Public sources and opportunity schema), MS-003 (Provider and stage interfaces)
- **Requirements:** R01.05, R10.01, R10.02, R10.04, R14.01.
- **Stories:** US-01.05, US-10.01, US-10.02, US-10.04, US-14.01.
- **Expected input:** relevant package contracts and the merged artifacts from every prerequisite above. External adapters use deterministic fixtures until configured live integration is explicitly run.
- **Write scope:** `backend/migrations/versions/0003_jobs.py`; `backend/src/benefitbridge/db/jobs.py`; directly corresponding tests, plus mechanical generated contracts where needed.
- **Implementation / expected outcome:** Create runs, jobs, outbox, run_events, stage_outputs, idempotency_records, usage_reservations, usage_entries and deletion_receipts. Model PUBLIC versus PRIVATE maintenance scope as specified in design.md; include lease/fencing tokens, unique logical stage keys and encrypted replay bodies.
- **API operations:** No new public endpoint; preserve the existing API contract.
- **Acceptance scenarios:** Transaction rollback leaves neither accepted run nor orphan outbox; unique keys prevent duplicate stages.
- **Handoff:** diff, actual check results, schema/config impact and reviewer note. Copy the matching prompt from plan.md.

### MS-016 — Leased PostgreSQL job dispatcher

- **Owner / reviewer / priority:** M3 / M1 / P0.
- **Strict prerequisites:** MS-015 (Durable runs, outbox, budget and receipt schema), MS-003 (Provider and stage interfaces), MS-005 (CI and reusable test harness)
- **Requirements:** R10.01, R10.02, R10.03, R10.04, R10.05.
- **Stories:** US-10.01, US-10.02, US-10.03, US-10.04, US-10.05.
- **Expected input:** relevant package contracts and the merged artifacts from every prerequisite above. External adapters use deterministic fixtures until configured live integration is explicitly run.
- **Write scope:** `backend/src/benefitbridge/workflows/queue.py`; `backend/src/benefitbridge/workflows/worker.py`; directly corresponding tests, plus mechanical generated contracts where needed.
- **Implementation / expected outcome:** Implement transactional outbox dispatch and SKIP LOCKED job claims, lease heartbeat, fencing checks, safe cancellation and bounded jitter retries. Stage outputs commit idempotently before transition.
- **API operations:** No new public endpoint; preserve the existing API contract.
- **Acceptance scenarios:** Kill worker after claim and after artifact commit; replacement worker recovers without duplicate artifacts.
- **Handoff:** diff, actual check results, schema/config impact and reviewer note. Copy the matching prompt from plan.md.

### MS-017 — Versioned profile read and edit API

- **Owner / reviewer / priority:** M1 / M3 / P0.
- **Strict prerequisites:** MS-008 (JWT authentication and account API), MS-015 (Durable runs, outbox, budget and receipt schema)
- **Requirements:** R02.01, R02.02, R02.04, R02.05.
- **Stories:** US-02.01, US-02.02, US-02.04, US-02.05.
- **Expected input:** relevant package contracts and the merged artifacts from every prerequisite above. External adapters use deterministic fixtures until configured live integration is explicitly run.
- **Write scope:** `backend/src/benefitbridge/api/profiles.py`; `backend/src/benefitbridge/profiles/service.py`; `tests/api/test_profiles.py`; directly corresponding tests, plus mechanical generated contracts where needed.
- **Implementation / expected outcome:** Implement typed patch with base_profile_version_id, immutable publication and transactional invalidation outbox. Provide owner-only current/history views. Missing attributes stay absent.
- **API operations:** get_profile, patch_profile, list_profile_versions, get_profile_version
- **Acceptance scenarios:** Two simultaneous edits yield one success and one 409; user cannot attach another owner evidence.
- **Handoff:** diff, actual check results, schema/config impact and reviewer note. Copy the matching prompt from plan.md.

### MS-018 — Structured profile editor

- **Owner / reviewer / priority:** M2 / M6 / P0.
- **Strict prerequisites:** MS-017 (Versioned profile read and edit API), MS-009 (Managed-auth and consent screens)
- **Requirements:** R02.01, R02.02, R02.04, R02.05, R12.01.
- **Stories:** US-02.01, US-02.02, US-02.04, US-02.05, US-12.01.
- **Expected input:** relevant package contracts and the merged artifacts from every prerequisite above. External adapters use deterministic fixtures until configured live integration is explicitly run.
- **Write scope:** `frontend/src/features/profile/`; directly corresponding tests, plus mechanical generated contracts where needed.
- **Implementation / expected outcome:** Build typed form controls, explicit unknown values, original GPA scale and conflict reload UI. Present provenance labels and source dates.
- **API operations:** No new public endpoint; preserve the existing API contract.
- **Acceptance scenarios:** Correct GPA and unknown authorization render without accidental conversion or assumptions.
- **Handoff:** diff, actual check results, schema/config impact and reviewer note. Copy the matching prompt from plan.md.

### MS-019 — Atomic cost reservations and fairness

- **Owner / reviewer / priority:** M3 / M1 / P0.
- **Strict prerequisites:** MS-015 (Durable runs, outbox, budget and receipt schema), MS-010 (Model registry and capability preflight)
- **Requirements:** R14.01, R14.05.
- **Stories:** US-14.01, US-14.05.
- **Expected input:** relevant package contracts and the merged artifacts from every prerequisite above. External adapters use deterministic fixtures until configured live integration is explicitly run.
- **Write scope:** `backend/src/benefitbridge/usage/budget.py`; `tests/usage/test_budget.py`; directly corresponding tests, plus mechanical generated contracts where needed.
- **Implementation / expected outcome:** Reserve maximum configured cost before each provider call, cap per-run/user/global concurrency and reconcile actual usage with integer micro-USD. Retain uncertain charges until reconciliation.
- **API operations:** No new public endpoint; preserve the existing API contract.
- **Acceptance scenarios:** Concurrent reservations cannot exceed limits; timeout charges cannot be silently refunded.
- **Handoff:** diff, actual check results, schema/config impact and reviewer note. Copy the matching prompt from plan.md.

### MS-020 — Nebius structured inference adapter

- **Owner / reviewer / priority:** M3 / M1 / P0.
- **Strict prerequisites:** MS-010 (Model registry and capability preflight), MS-019 (Atomic cost reservations and fairness), MS-003 (Provider and stage interfaces)
- **Requirements:** R07.03, R13.02, R14.02.
- **Stories:** US-07.03, US-13.02, US-14.02.
- **Expected input:** relevant package contracts and the merged artifacts from every prerequisite above. External adapters use deterministic fixtures until configured live integration is explicitly run.
- **Write scope:** `backend/src/benefitbridge/inference/nebius.py`; `backend/src/benefitbridge/inference/prompts/`; directly corresponding tests, plus mechanical generated contracts where needed.
- **Implementation / expected outcome:** Implement schema-validated responses, token limits, redacted metadata and at most one bounded repair; route unsupported schemas safely. No chain-of-thought persistence.
- **API operations:** No new public endpoint; preserve the existing API contract.
- **Acceptance scenarios:** Invalid JSON, truncation, 429 and missing model fail or retry within the same budget; secrets stay out of logs.
- **Handoff:** diff, actual check results, schema/config impact and reviewer note. Copy the matching prompt from plan.md.

### MS-021 — Safe fetching and untrusted-content boundary

- **Owner / reviewer / priority:** M5 / M4 / P0.
- **Strict prerequisites:** MS-003 (Provider and stage interfaces), MS-006 (Source and normalized span contract), MS-005 (CI and reusable test harness)
- **Requirements:** R04.03, R13.02, R13.03, R13.05.
- **Stories:** US-04.03, US-13.02, US-13.03, US-13.05.
- **Expected input:** relevant package contracts and the merged artifacts from every prerequisite above. External adapters use deterministic fixtures until configured live integration is explicitly run.
- **Write scope:** `backend/src/benefitbridge/security/fetch_guard.py`; `tests/security/test_fetch_guard.py`; directly corresponding tests, plus mechanical generated contracts where needed.
- **Implementation / expected outcome:** Implement HTTPS public-network checks on DNS resolution and every redirect, pinned safe connection targets, size/time limits and content sanitization. Separate document/source text from tool instructions.
- **API operations:** No new public endpoint; preserve the existing API contract.
- **Acceptance scenarios:** Private IPv4/IPv6, DNS rebinding, redirect-to-metadata, credential URLs and prompt injection fixtures fail safely.
- **Handoff:** diff, actual check results, schema/config impact and reviewer note. Copy the matching prompt from plan.md.

### MS-022 — Tavily discovery and source fetch adapter

- **Owner / reviewer / priority:** M5 / M4 / P0.
- **Strict prerequisites:** MS-003 (Provider and stage interfaces), MS-019 (Atomic cost reservations and fairness), MS-021 (Safe fetching and untrusted-content boundary)
- **Requirements:** R04.02, R04.03, R05.01, R13.02.
- **Stories:** US-04.02, US-04.03, US-05.01, US-13.02.
- **Expected input:** relevant package contracts and the merged artifacts from every prerequisite above. External adapters use deterministic fixtures until configured live integration is explicitly run.
- **Write scope:** `backend/src/benefitbridge/sources/tavily.py`; `backend/src/benefitbridge/sources/fetch.py`; directly corresponding tests, plus mechanical generated contracts where needed.
- **Implementation / expected outcome:** Implement bounded generalized-query search and full-context fetch with official domain registry validation. Snippets are discovery leads, never full policy.
- **API operations:** No new public endpoint; preserve the existing API contract.
- **Acceptance scenarios:** PII canaries never enter queries; provider failures preserve typed reasons; redirects pass fetch guard.
- **Handoff:** diff, actual check results, schema/config impact and reviewer note. Copy the matching prompt from plan.md.

### MS-023 — Three-valued graph evaluation

- **Owner / reviewer / priority:** M4 / M6 / P0.
- **Strict prerequisites:** MS-011 (Deterministic fact predicates), MS-002 (Shared domain schemas and enums)
- **Requirements:** R06.02, R07.01, R07.02.
- **Stories:** US-06.02, US-07.01, US-07.02.
- **Expected input:** relevant package contracts and the merged artifacts from every prerequisite above. External adapters use deterministic fixtures until configured live integration is explicitly run.
- **Write scope:** `backend/src/benefitbridge/eligibility/logic.py`; `tests/eligibility/test_logic.py`; directly corresponding tests, plus mechanical generated contracts where needed.
- **Implementation / expected outcome:** Implement ALL/ANY/NOT with strong Kleene logic, modality separation and decisive trace paths. Validate DAG and unsupported predicates.
- **API operations:** No new public endpoint; preserve the existing API contract.
- **Acceptance scenarios:** Exhaustive truth tables pass; UNKNOWN cannot become TRUE through missing children.
- **Handoff:** diff, actual check results, schema/config impact and reviewer note. Copy the matching prompt from plan.md.

### MS-024 — Annotation and adjudication tooling

- **Owner / reviewer / priority:** M6 / M4 / P0.
- **Strict prerequisites:** MS-013 (Dataset manifest and split validator)
- **Requirements:** R15.01.
- **Stories:** US-15.01.
- **Expected input:** relevant package contracts and the merged artifacts from every prerequisite above. External adapters use deterministic fixtures until configured live integration is explicitly run.
- **Write scope:** `evaluation/annotation/`; `evaluation/adjudicate.py`; directly corresponding tests, plus mechanical generated contracts where needed.
- **Implementation / expected outcome:** Create two-blind-annotator templates, disagreement report, third-adjudicator workflow and immutable gold manifest finalization. This task creates tools, not labels.
- **API operations:** No new public endpoint; preserve the existing API contract.
- **Acceptance scenarios:** Conflicting labels cannot enter frozen gold without adjudication metadata; inter-rater agreement excludes post-adjudication labels.
- **Handoff:** diff, actual check results, schema/config impact and reviewer note. Copy the matching prompt from plan.md.

### MS-025 — Private evidence schema

- **Owner / reviewer / priority:** M1 / M3 / P0.
- **Strict prerequisites:** MS-015 (Durable runs, outbox, budget and receipt schema)
- **Requirements:** R03.01, R03.02, R03.03, R13.01.
- **Stories:** US-03.01, US-03.02, US-03.03, US-13.01.
- **Expected input:** relevant package contracts and the merged artifacts from every prerequisite above. External adapters use deterministic fixtures until configured live integration is explicitly run.
- **Write scope:** `backend/migrations/versions/0004_documents.py`; `backend/src/benefitbridge/db/documents.py`; directly corresponding tests, plus mechanical generated contracts where needed.
- **Implementation / expected outcome:** Create documents, document_versions, evidence_spans and fact_candidates with quota reservations, tombstones and owner-composite foreign keys. Add fact evidence links to existing schema.
- **API operations:** No new public endpoint; preserve the existing API contract.
- **Acceptance scenarios:** Cross-owner references fail at DB level; deleted evidence cannot be selected as active.
- **Handoff:** diff, actual check results, schema/config impact and reviewer note. Copy the matching prompt from plan.md.

### MS-026 — Document upload and read API

- **Owner / reviewer / priority:** M1 / M3 / P0.
- **Strict prerequisites:** MS-025 (Private evidence schema), MS-008 (JWT authentication and account API), MS-003 (Provider and stage interfaces)
- **Requirements:** R03.01, R03.02, R03.03.
- **Stories:** US-03.01, US-03.02, US-03.03.
- **Expected input:** relevant package contracts and the merged artifacts from every prerequisite above. External adapters use deterministic fixtures until configured live integration is explicitly run.
- **Write scope:** `backend/src/benefitbridge/api/documents.py`; `backend/src/benefitbridge/documents/storage.py`; directly corresponding tests, plus mechanical generated contracts where needed.
- **Implementation / expected outcome:** Implement five-minute upload intent, authenticated streaming PUT, checksum-verified completion and queued parse run; owner-only list/detail/download. Downloads use verified short-lived private storage links.
- **API operations:** create_document_upload, put_document_content, complete_document_upload, list_documents, get_document, get_document_download
- **Acceptance scenarios:** 10 MiB cap holds during chunked upload; failed upload releases quota; completing identical upload is idempotent.
- **Handoff:** diff, actual check results, schema/config impact and reviewer note. Copy the matching prompt from plan.md.

### MS-027 — PDF to reviewable fact candidates

- **Owner / reviewer / priority:** M5 / M4 / P0.
- **Strict prerequisites:** MS-026 (Document upload and read API), MS-012 (Bounded digital PDF parsing), MS-020 (Nebius structured inference adapter), MS-016 (Leased PostgreSQL job dispatcher)
- **Requirements:** R02.03, R02.05, R03.02, R03.04.
- **Stories:** US-02.03, US-02.05, US-03.02, US-03.04.
- **Expected input:** relevant package contracts and the merged artifacts from every prerequisite above. External adapters use deterministic fixtures until configured live integration is explicitly run.
- **Write scope:** `backend/src/benefitbridge/documents/stages.py`; `backend/src/benefitbridge/documents/extraction.py`; directly corresponding tests, plus mechanical generated contracts where needed.
- **Implementation / expected outcome:** Persist parsed spans and schema-validated candidate facts with exact evidence links, conflicts and quality flags. Do not publish profile facts until review.
- **API operations:** No new public endpoint; preserve the existing API contract.
- **Acceptance scenarios:** Unsupported GPA scale and conflicting documents remain reviewable; worker replay reuses the same candidate IDs.
- **Handoff:** diff, actual check results, schema/config impact and reviewer note. Copy the matching prompt from plan.md.

### MS-028 — Fact candidate review API

- **Owner / reviewer / priority:** M1 / M3 / P0.
- **Strict prerequisites:** MS-027 (PDF to reviewable fact candidates), MS-017 (Versioned profile read and edit API)
- **Requirements:** R02.03, R02.04, R02.05, R03.03.
- **Stories:** US-02.03, US-02.04, US-02.05, US-03.03.
- **Expected input:** relevant package contracts and the merged artifacts from every prerequisite above. External adapters use deterministic fixtures until configured live integration is explicitly run.
- **Write scope:** `backend/src/benefitbridge/api/facts.py`; `backend/src/benefitbridge/profiles/review.py`; directly corresponding tests, plus mechanical generated contracts where needed.
- **Implementation / expected outcome:** Expose candidates and evidence; accept/correct/reject batch atomically with profile base version and candidate state checks. Queue invalidation on publication.
- **API operations:** list_fact_candidates, review_fact_candidates, get_evidence
- **Acceptance scenarios:** A stale review returns 409; rejected candidate cannot silently reappear as a confirmed fact.
- **Handoff:** diff, actual check results, schema/config impact and reviewer note. Copy the matching prompt from plan.md.

### MS-029 — Upload and fact review experience

- **Owner / reviewer / priority:** M2 / M6 / P0.
- **Strict prerequisites:** MS-028 (Fact candidate review API), MS-018 (Structured profile editor)
- **Requirements:** R02.03, R03.01, R03.02, R03.03, R03.04.
- **Stories:** US-02.03, US-03.01, US-03.02, US-03.03, US-03.04.
- **Expected input:** relevant package contracts and the merged artifacts from every prerequisite above. External adapters use deterministic fixtures until configured live integration is explicitly run.
- **Write scope:** `frontend/src/features/documents/`; directly corresponding tests, plus mechanical generated contracts where needed.
- **Implementation / expected outcome:** Build bounded upload progress, document status, evidence passage review and atomic candidate review. Render unreadable-document alternatives.
- **API operations:** No new public endpoint; preserve the existing API contract.
- **Acceptance scenarios:** Rejected and corrected GPA actions produce the right request; reload preserves server processing state.
- **Handoff:** diff, actual check results, schema/config impact and reviewer note. Copy the matching prompt from plan.md.

### MS-030 — Run control and authenticated event stream

- **Owner / reviewer / priority:** M3 / M1 / P0.
- **Strict prerequisites:** MS-016 (Leased PostgreSQL job dispatcher), MS-008 (JWT authentication and account API)
- **Requirements:** R10.01, R10.02, R10.03, R10.05.
- **Stories:** US-10.01, US-10.02, US-10.03, US-10.05.
- **Expected input:** relevant package contracts and the merged artifacts from every prerequisite above. External adapters use deterministic fixtures until configured live integration is explicitly run.
- **Write scope:** `backend/src/benefitbridge/api/runs.py`; `backend/src/benefitbridge/workflows/events.py`; directly corresponding tests, plus mechanical generated contracts where needed.
- **Implementation / expected outcome:** Implement run list/detail/cancel and fetch-based SSE replay using event sequence IDs and owner checks. Heartbeats do not create persisted events.
- **API operations:** list_runs, get_run, cancel_run, get_run_events
- **Acceptance scenarios:** Reconnect after seq N receives N+1 onward; expired cursor uses 410; terminal run stream closes.
- **Handoff:** diff, actual check results, schema/config impact and reviewer note. Copy the matching prompt from plan.md.

### MS-031 — Durable progress components

- **Owner / reviewer / priority:** M2 / M6 / P0.
- **Strict prerequisites:** MS-030 (Run control and authenticated event stream), MS-004 (Web shell and state conventions), MS-009 (Managed-auth and consent screens)
- **Requirements:** R04.05, R10.02, R10.03, R10.05, R12.03.
- **Stories:** US-04.05, US-10.02, US-10.03, US-10.05, US-12.03.
- **Expected input:** relevant package contracts and the merged artifacts from every prerequisite above. External adapters use deterministic fixtures until configured live integration is explicitly run.
- **Write scope:** `frontend/src/features/runs/`; directly corresponding tests, plus mechanical generated contracts where needed.
- **Implementation / expected outcome:** Use authenticated fetch streaming with AbortController, last-event cursor and poll fallback. Group progress by actual persisted stage; support cancel and reload.
- **API operations:** No new public endpoint; preserve the existing API contract.
- **Acceptance scenarios:** Duplicate replay events are ignored; HTTP disconnect does not cancel the server run.
- **Handoff:** diff, actual check results, schema/config impact and reviewer note. Copy the matching prompt from plan.md.

### MS-032 — Public snapshot storage and authority resolution

- **Owner / reviewer / priority:** M5 / M4 / P0.
- **Strict prerequisites:** MS-014 (Public sources and opportunity schema), MS-022 (Tavily discovery and source fetch adapter), MS-006 (Source and normalized span contract)
- **Requirements:** R05.01, R05.03, R05.04.
- **Stories:** US-05.01, US-05.03, US-05.04.
- **Expected input:** relevant package contracts and the merged artifacts from every prerequisite above. External adapters use deterministic fixtures until configured live integration is explicitly run.
- **Write scope:** `backend/src/benefitbridge/sources/service.py`; `backend/src/benefitbridge/sources/authority.py`; directly corresponding tests, plus mechanical generated contracts where needed.
- **Implementation / expected outcome:** Persist immutable snapshots/spans and permitted metadata, classify official links and ATS affiliation, calculate freshness without overriding policy dates.
- **API operations:** No new public endpoint; preserve the existing API contract.
- **Acceptance scenarios:** Unknown repost stays tentative; changed content creates version; inaccessible source is unavailable.
- **Handoff:** diff, actual check results, schema/config impact and reviewer note. Copy the matching prompt from plan.md.

### MS-033 — Conservative opportunity canonicalization

- **Owner / reviewer / priority:** M5 / M4 / P0.
- **Strict prerequisites:** MS-032 (Public snapshot storage and authority resolution)
- **Requirements:** R05.02.
- **Stories:** US-05.02.
- **Expected input:** relevant package contracts and the merged artifacts from every prerequisite above. External adapters use deterministic fixtures until configured live integration is explicitly run.
- **Write scope:** `backend/src/benefitbridge/sources/canonical.py`; `tests/sources/test_canonical.py`; directly corresponding tests, plus mechanical generated contracts where needed.
- **Implementation / expected outcome:** Normalize tracking parameters and match provider/external ID/intake/location; preserve uncertain matches and alias discovery URLs.
- **API operations:** No new public endpoint; preserve the existing API contract.
- **Acceptance scenarios:** Same title different year/region stays separate; repeated canonical import is idempotent.
- **Handoff:** diff, actual check results, schema/config impact and reviewer note. Copy the matching prompt from plan.md.

### MS-034 — Bounded redacted goal planner

- **Owner / reviewer / priority:** M3 / M1 / P0.
- **Strict prerequisites:** MS-020 (Nebius structured inference adapter), MS-022 (Tavily discovery and source fetch adapter), MS-002 (Shared domain schemas and enums)
- **Requirements:** R04.01, R04.02, R13.02.
- **Stories:** US-04.01, US-04.02, US-13.02.
- **Expected input:** relevant package contracts and the merged artifacts from every prerequisite above. External adapters use deterministic fixtures until configured live integration is explicitly run.
- **Write scope:** `backend/src/benefitbridge/discovery/planner.py`; directly corresponding tests, plus mechanical generated contracts where needed.
- **Implementation / expected outcome:** Validate goal/preferences, minimize search context and generate up to three initial and two follow-up intents. Enforce server caps independently of model output.
- **API operations:** No new public endpoint; preserve the existing API contract.
- **Acceptance scenarios:** Injected goals cannot increase budgets; names/email/document text are removed from outgoing search requests.
- **Handoff:** diff, actual check results, schema/config impact and reviewer note. Copy the matching prompt from plan.md.

### MS-035 — Requirement AST extraction

- **Owner / reviewer / priority:** M4 / M6 / P0.
- **Strict prerequisites:** MS-020 (Nebius structured inference adapter), MS-006 (Source and normalized span contract), MS-002 (Shared domain schemas and enums)
- **Requirements:** R06.01, R06.02, R06.03, R06.04, R06.05.
- **Stories:** US-06.01, US-06.02, US-06.03, US-06.04, US-06.05.
- **Expected input:** relevant package contracts and the merged artifacts from every prerequisite above. External adapters use deterministic fixtures until configured live integration is explicitly run.
- **Write scope:** `backend/src/benefitbridge/requirements/extract.py`; `backend/src/benefitbridge/requirements/prompts/`; directly corresponding tests, plus mechanical generated contracts where needed.
- **Implementation / expected outcome:** Extract bounded AST with mandatory/preferred roots, source spans, scope, dates and documentary tasks; incomplete linked policy yields explicit issues.
- **API operations:** No new public endpoint; preserve the existing API contract.
- **Acceptance scenarios:** Mandatory versus preferred, exception wording, missing linked policy and source conflicts remain distinct.
- **Handoff:** diff, actual check results, schema/config impact and reviewer note. Copy the matching prompt from plan.md.

### MS-036 — Requirement publication validator

- **Owner / reviewer / priority:** M4 / M6 / P0.
- **Strict prerequisites:** MS-035 (Requirement AST extraction), MS-023 (Three-valued graph evaluation)
- **Requirements:** R06.02, R06.03, R06.04, R07.04.
- **Stories:** US-06.02, US-06.03, US-06.04, US-07.04.
- **Expected input:** relevant package contracts and the merged artifacts from every prerequisite above. External adapters use deterministic fixtures until configured live integration is explicitly run.
- **Write scope:** `backend/src/benefitbridge/requirements/validate.py`; `tests/requirements/test_validate.py`; directly corresponding tests, plus mechanical generated contracts where needed.
- **Implementation / expected outcome:** Validate AST limits, span entailment checks, quotation offsets, matching intake and completeness. Preserve unresolved ambiguity rather than inventing rules.
- **API operations:** No new public endpoint; preserve the existing API contract.
- **Acceptance scenarios:** Bad quotes, wrong intake, missing mandatory context and unsupported predicates block COMPLETE status.
- **Handoff:** diff, actual check results, schema/config impact and reviewer note. Copy the matching prompt from plan.md.

### MS-037 — Owner-scoped evidence retrieval

- **Owner / reviewer / priority:** M5 / M4 / P0.
- **Strict prerequisites:** MS-028 (Fact candidate review API), MS-006 (Source and normalized span contract)
- **Requirements:** R03.03, R07.03, R13.01.
- **Stories:** US-03.03, US-07.03, US-13.01.
- **Expected input:** relevant package contracts and the merged artifacts from every prerequisite above. External adapters use deterministic fixtures until configured live integration is explicitly run.
- **Write scope:** `backend/src/benefitbridge/evidence/retrieve.py`; `tests/evidence/test_retrieve.py`; directly corresponding tests, plus mechanical generated contracts where needed.
- **Implementation / expected outcome:** Retrieve exact typed attributes then at most five lexical evidence spans for unresolved semantic predicates. Preserve adjacent negation and time context.
- **API operations:** No new public endpoint; preserve the existing API contract.
- **Acceptance scenarios:** Cross-owner spans never enter candidate set; no experience is not evidence of experience.
- **Handoff:** diff, actual check results, schema/config impact and reviewer note. Copy the matching prompt from plan.md.

### MS-038 — Requirement and evaluation persistence

- **Owner / reviewer / priority:** M1 / M3 / P0.
- **Strict prerequisites:** MS-025 (Private evidence schema), MS-014 (Public sources and opportunity schema)
- **Requirements:** R06.02, R07.01, R07.04, R08.03, R08.04.
- **Stories:** US-06.02, US-07.01, US-07.04, US-08.03, US-08.04.
- **Expected input:** relevant package contracts and the merged artifacts from every prerequisite above. External adapters use deterministic fixtures until configured live integration is explicitly run.
- **Write scope:** `backend/migrations/versions/0005_evaluations.py`; `backend/src/benefitbridge/db/evaluations.py`; directly corresponding tests, plus mechanical generated contracts where needed.
- **Implementation / expected outcome:** Create requirement_sets, evaluations, leaf_results, decision_dependencies, clarification_sets and answers with immutable input version references.
- **API operations:** No new public endpoint; preserve the existing API contract.
- **Acceptance scenarios:** Source spans must belong to the referenced opportunity version; private evaluation inputs enforce owner consistency.
- **Handoff:** diff, actual check results, schema/config impact and reviewer note. Copy the matching prompt from plan.md.

### MS-039 — Bounded semantic predicate evaluator

- **Owner / reviewer / priority:** M4 / M6 / P0.
- **Strict prerequisites:** MS-020 (Nebius structured inference adapter), MS-037 (Owner-scoped evidence retrieval), MS-023 (Three-valued graph evaluation)
- **Requirements:** R07.03, R07.05.
- **Stories:** US-07.03, US-07.05.
- **Expected input:** relevant package contracts and the merged artifacts from every prerequisite above. External adapters use deterministic fixtures until configured live integration is explicitly run.
- **Write scope:** `backend/src/benefitbridge/eligibility/semantic.py`; directly corresponding tests, plus mechanical generated contracts where needed.
- **Implementation / expected outcome:** Evaluate only SEMANTIC_MATCH predicates using supported spans; return TRUE/FALSE/UNKNOWN, concise justification and evidence IDs. Escalate at most once to configured DEEP if budget allows.
- **API operations:** No new public endpoint; preserve the existing API contract.
- **Acceptance scenarios:** No evidence, mismatched time and unsupported relatedness produce UNKNOWN; no confidence score becomes truth.
- **Handoff:** diff, actual check results, schema/config impact and reviewer note. Copy the matching prompt from plan.md.

### MS-040 — Eligibility aggregation and publication guards

- **Owner / reviewer / priority:** M4 / M6 / P0.
- **Strict prerequisites:** MS-039 (Bounded semantic predicate evaluator), MS-036 (Requirement publication validator)
- **Requirements:** R07.01, R07.04, R07.05, R08.01.
- **Stories:** US-07.01, US-07.04, US-07.05, US-08.01.
- **Expected input:** relevant package contracts and the merged artifacts from every prerequisite above. External adapters use deterministic fixtures until configured live integration is explicitly run.
- **Write scope:** `backend/src/benefitbridge/eligibility/decision.py`; directly corresponding tests, plus mechanical generated contracts where needed.
- **Implementation / expected outcome:** Combine deterministic and semantic results; publish MET only for complete coherent sources and all required paths supported. Preserve a supported decisive NOT_MET despite unrelated unknowns.
- **API operations:** No new public endpoint; preserve the existing API contract.
- **Acceptance scenarios:** Incomplete positive becomes UNKNOWN; authoritative decisive false remains NOT_MET; availability stays independent.
- **Handoff:** diff, actual check results, schema/config impact and reviewer note. Copy the matching prompt from plan.md.

### MS-041 — Decision and citation verification

- **Owner / reviewer / priority:** M4 / M6 / P0.
- **Strict prerequisites:** MS-040 (Eligibility aggregation and publication guards)
- **Requirements:** R07.04, R07.05.
- **Stories:** US-07.04, US-07.05.
- **Expected input:** relevant package contracts and the merged artifacts from every prerequisite above. External adapters use deterministic fixtures until configured live integration is explicitly run.
- **Write scope:** `backend/src/benefitbridge/eligibility/verify.py`; directly corresponding tests, plus mechanical generated contracts where needed.
- **Implementation / expected outcome:** Check referential integrity, ownership, quotes, evidence support, pinned versions and decisive paths; independently inspect risky semantic conclusions using REASON within caps.
- **API operations:** No new public endpoint; preserve the existing API contract.
- **Acceptance scenarios:** Missing or non-entailing decisive evidence invalidates that leaf and recomputes aggregate; verifier cannot invent facts.
- **Handoff:** diff, actual check results, schema/config impact and reviewer note. Copy the matching prompt from plan.md.

### MS-042 — Availability, fit, readiness and sorting

- **Owner / reviewer / priority:** M4 / M6 / P0.
- **Strict prerequisites:** MS-040 (Eligibility aggregation and publication guards), MS-011 (Deterministic fact predicates)
- **Requirements:** R05.04, R08.01, R08.02, R08.05.
- **Stories:** US-05.04, US-08.01, US-08.02, US-08.05.
- **Expected input:** relevant package contracts and the merged artifacts from every prerequisite above. External adapters use deterministic fixtures until configured live integration is explicitly run.
- **Write scope:** `backend/src/benefitbridge/ranking.py`; `backend/src/benefitbridge/readiness.py`; directly corresponding tests, plus mechanical generated contracts where needed.
- **Implementation / expected outcome:** Implement separate availability state, explained 0–100 preference fit with coverage and deterministic group ordering; readiness uses applicable required items only.
- **API operations:** No new public endpoint; preserve the existing API contract.
- **Acceptance scenarios:** Closed MET stays MET but sorts below actionable results; zero known required tasks yields null readiness.
- **Handoff:** diff, actual check results, schema/config impact and reviewer note. Copy the matching prompt from plan.md.

### MS-043 — Discovery stage graph and candidate persistence

- **Owner / reviewer / priority:** M3 / M1 / P0.
- **Strict prerequisites:** MS-034 (Bounded redacted goal planner), MS-033 (Conservative opportunity canonicalization), MS-036 (Requirement publication validator), MS-038 (Requirement and evaluation persistence), MS-016 (Leased PostgreSQL job dispatcher), MS-021 (Safe fetching and untrusted-content boundary)
- **Requirements:** R04.02, R04.04, R04.05, R05.01, R06.04.
- **Stories:** US-04.02, US-04.04, US-04.05, US-05.01, US-06.04.
- **Expected input:** relevant package contracts and the merged artifacts from every prerequisite above. External adapters use deterministic fixtures until configured live integration is explicitly run.
- **Write scope:** `backend/src/benefitbridge/discovery/stages.py`; directly corresponding tests, plus mechanical generated contracts where needed.
- **Implementation / expected outcome:** Orchestrate plan, search, resolve, fetch and parse; persist candidate funnel and requirement sets; pick at most five deep-evaluation candidates and retain other candidates as unevaluated.
- **API operations:** No new public endpoint; preserve the existing API contract.
- **Acceptance scenarios:** One failing source yields PARTIAL with successes; follow-ups cannot exceed query/page/call budgets.
- **Handoff:** diff, actual check results, schema/config impact and reviewer note. Copy the matching prompt from plan.md.

### MS-044 — Evaluation workflow stage

- **Owner / reviewer / priority:** M3 / M1 / P0.
- **Strict prerequisites:** MS-041 (Decision and citation verification), MS-042 (Availability, fit, readiness and sorting), MS-038 (Requirement and evaluation persistence), MS-016 (Leased PostgreSQL job dispatcher)
- **Requirements:** R07.01, R07.04, R08.01, R10.04.
- **Stories:** US-07.01, US-07.04, US-08.01, US-10.04.
- **Expected input:** relevant package contracts and the merged artifacts from every prerequisite above. External adapters use deterministic fixtures until configured live integration is explicitly run.
- **Write scope:** `backend/src/benefitbridge/workflows/evaluate.py`; directly corresponding tests, plus mechanical generated contracts where needed.
- **Implementation / expected outcome:** Evaluate a pinned profile/opportunity pair, persist atomic leaf results and dependencies, enforce currentness at publication and emit incremental events.
- **API operations:** No new public endpoint; preserve the existing API contract.
- **Acceptance scenarios:** Concurrent profile edits mark output historical; retries publish one evaluation; stale decisions never become current.
- **Handoff:** diff, actual check results, schema/config impact and reviewer note. Copy the matching prompt from plan.md.

### MS-045 — Public opportunity and source reads

- **Owner / reviewer / priority:** M5 / M4 / P0.
- **Strict prerequisites:** MS-038 (Requirement and evaluation persistence), MS-033 (Conservative opportunity canonicalization), MS-008 (JWT authentication and account API)
- **Requirements:** R05.01, R05.03, R06.01, R06.03.
- **Stories:** US-05.01, US-05.03, US-06.01, US-06.03.
- **Expected input:** relevant package contracts and the merged artifacts from every prerequisite above. External adapters use deterministic fixtures until configured live integration is explicitly run.
- **Write scope:** `backend/src/benefitbridge/api/opportunities.py`; `backend/src/benefitbridge/api/sources.py`; directly corresponding tests, plus mechanical generated contracts where needed.
- **Implementation / expected outcome:** Expose list/current/history, requirement graph and cited public source records; join only caller-owned evaluation summaries.
- **API operations:** list_opportunities, get_opportunity, get_opportunity_version, get_requirements, get_source
- **Acceptance scenarios:** Changing owner cannot reveal private summaries; cursor order is stable under new records.
- **Handoff:** diff, actual check results, schema/config impact and reviewer note. Copy the matching prompt from plan.md.

### MS-046 — Discovery and URL-import commands

- **Owner / reviewer / priority:** M3 / M1 / P0.
- **Strict prerequisites:** MS-043 (Discovery stage graph and candidate persistence), MS-044 (Evaluation workflow stage), MS-030 (Run control and authenticated event stream), MS-017 (Versioned profile read and edit API)
- **Requirements:** R04.01, R04.02, R04.03, R10.01.
- **Stories:** US-04.01, US-04.02, US-04.03, US-10.01.
- **Expected input:** relevant package contracts and the merged artifacts from every prerequisite above. External adapters use deterministic fixtures until configured live integration is explicitly run.
- **Write scope:** `backend/src/benefitbridge/api/discovery.py`; directly corresponding tests, plus mechanical generated contracts where needed.
- **Implementation / expected outcome:** Implement idempotent run creation with pinned profile, generalized goal, URL validation and transactional outbox. Share command validation with worker.
- **API operations:** start_discovery, import_opportunity
- **Acceptance scenarios:** Duplicate keys replay receipt; changed payload returns 409; missing consent returns 403.
- **Handoff:** diff, actual check results, schema/config impact and reviewer note. Copy the matching prompt from plan.md.

### MS-047 — Explicit evaluation API

- **Owner / reviewer / priority:** M4 / M6 / P0.
- **Strict prerequisites:** MS-044 (Evaluation workflow stage), MS-045 (Public opportunity and source reads), MS-008 (JWT authentication and account API)
- **Requirements:** R07.01, R07.04, R07.05.
- **Stories:** US-07.01, US-07.04, US-07.05.
- **Expected input:** relevant package contracts and the merged artifacts from every prerequisite above. External adapters use deterministic fixtures until configured live integration is explicitly run.
- **Write scope:** `backend/src/benefitbridge/api/evaluations.py`; directly corresponding tests, plus mechanical generated contracts where needed.
- **Implementation / expected outcome:** Implement explicit evaluation command and owner-only result read with currentness metadata and independent status fields.
- **API operations:** start_evaluation, get_evaluation
- **Acceptance scenarios:** Unknown-version IDs fail before queueing; stale input is marked rather than silently rebased.
- **Handoff:** diff, actual check results, schema/config impact and reviewer note. Copy the matching prompt from plan.md.

### MS-048 — Discovery form and results feed

- **Owner / reviewer / priority:** M2 / M6 / P0.
- **Strict prerequisites:** MS-046 (Discovery and URL-import commands), MS-045 (Public opportunity and source reads), MS-031 (Durable progress components), MS-018 (Structured profile editor)
- **Requirements:** R04.01, R04.04, R04.05, R08.01, R08.02.
- **Stories:** US-04.01, US-04.04, US-04.05, US-08.01, US-08.02.
- **Expected input:** relevant package contracts and the merged artifacts from every prerequisite above. External adapters use deterministic fixtures until configured live integration is explicitly run.
- **Write scope:** `frontend/src/features/discovery/`; directly corresponding tests, plus mechanical generated contracts where needed.
- **Implementation / expected outcome:** Build goal entry, lane/preferences, URL import and incrementally loaded results. Show unevaluated and partial candidates with funnel counts.
- **API operations:** No new public endpoint; preserve the existing API contract.
- **Acceptance scenarios:** Unavailable and UNKNOWN differ visually and in text; no fake percentage eligibility.
- **Handoff:** diff, actual check results, schema/config impact and reviewer note. Copy the matching prompt from plan.md.

### MS-049 — Decision and evidence detail screen

- **Owner / reviewer / priority:** M2 / M6 / P0.
- **Strict prerequisites:** MS-047 (Explicit evaluation API), MS-048 (Discovery form and results feed)
- **Requirements:** R06.01, R07.04, R07.05, R12.02, R12.04.
- **Stories:** US-06.01, US-07.04, US-07.05, US-12.02, US-12.04.
- **Expected input:** relevant package contracts and the merged artifacts from every prerequisite above. External adapters use deterministic fixtures until configured live integration is explicitly run.
- **Write scope:** `frontend/src/features/opportunity/`; directly corresponding tests, plus mechanical generated contracts where needed.
- **Implementation / expected outcome:** Render each leaf with source passage, applicant fact, evidence provenance, method and next action; show historical/current versions distinctly.
- **API operations:** No new public endpoint; preserve the existing API contract.
- **Acceptance scenarios:** A judge can keyboard-navigate source and evidence; stale input warning remains visible.
- **Handoff:** diff, actual check results, schema/config impact and reviewer note. Copy the matching prompt from plan.md.

### MS-050 — Clarification persistence and resumption

- **Owner / reviewer / priority:** M3 / M1 / P0.
- **Strict prerequisites:** MS-044 (Evaluation workflow stage), MS-017 (Versioned profile read and edit API), MS-030 (Run control and authenticated event stream)
- **Requirements:** R08.03, R08.04.
- **Stories:** US-08.03, US-08.04.
- **Expected input:** relevant package contracts and the merged artifacts from every prerequisite above. External adapters use deterministic fixtures until configured live integration is explicitly run.
- **Write scope:** `backend/src/benefitbridge/api/clarifications.py`; `backend/src/benefitbridge/workflows/clarify.py`; directly corresponding tests, plus mechanical generated contracts where needed.
- **Implementation / expected outcome:** Create up to three attribute questions per round, two rounds maximum. Validate answers against base profile and clarification-set revision; atomically publish profile version and requeue only evaluation.
- **API operations:** get_clarifications, answer_clarifications
- **Acceptance scenarios:** Duplicate answer retries do not create duplicate versions; unrelated concurrent profile edit returns 409.
- **Handoff:** diff, actual check results, schema/config impact and reviewer note. Copy the matching prompt from plan.md.

### MS-051 — Targeted fact clarification UI

- **Owner / reviewer / priority:** M2 / M6 / P0.
- **Strict prerequisites:** MS-050 (Clarification persistence and resumption), MS-049 (Decision and evidence detail screen)
- **Requirements:** R08.03, R08.04, R12.03.
- **Stories:** US-08.03, US-08.04, US-12.03.
- **Expected input:** relevant package contracts and the merged artifacts from every prerequisite above. External adapters use deterministic fixtures until configured live integration is explicitly run.
- **Write scope:** `frontend/src/features/clarifications/`; directly corresponding tests, plus mechanical generated contracts where needed.
- **Implementation / expected outcome:** Render typed questions, explain why each matters, allow unknown/skip, handle 409 reload and resume the linked run.
- **API operations:** No new public endpoint; preserve the existing API contract.
- **Acceptance scenarios:** Skipped unknown cannot become false; no indefinite round loop.
- **Handoff:** diff, actual check results, schema/config impact and reviewer note. Copy the matching prompt from plan.md.

### MS-052 — Application and shortlist schema

- **Owner / reviewer / priority:** M1 / M3 / P0.
- **Strict prerequisites:** MS-038 (Requirement and evaluation persistence)
- **Requirements:** R09.01, R09.02, R09.04, R11.01.
- **Stories:** US-09.01, US-09.02, US-09.04, US-11.01.
- **Expected input:** relevant package contracts and the merged artifacts from every prerequisite above. External adapters use deterministic fixtures until configured live integration is explicitly run.
- **Write scope:** `backend/migrations/versions/0006_applications.py`; `backend/src/benefitbridge/db/applications.py`; directly corresponding tests, plus mechanical generated contracts where needed.
- **Implementation / expected outcome:** Create saved_opportunities, applications, checklist_items, drafts, draft_claims and acceptance records with revision checks and version-bound acceptance.
- **API operations:** No new public endpoint; preserve the existing API contract.
- **Acceptance scenarios:** Foreign-owner facts in claims fail; one active application per owner/opportunity cycle is enforced.
- **Handoff:** diff, actual check results, schema/config impact and reviewer note. Copy the matching prompt from plan.md.

### MS-053 — Saved opportunity endpoints

- **Owner / reviewer / priority:** M1 / M3 / P0.
- **Strict prerequisites:** MS-052 (Application and shortlist schema), MS-045 (Public opportunity and source reads)
- **Requirements:** R11.01, R11.02.
- **Stories:** US-11.01, US-11.02.
- **Expected input:** relevant package contracts and the merged artifacts from every prerequisite above. External adapters use deterministic fixtures until configured live integration is explicitly run.
- **Write scope:** `backend/src/benefitbridge/api/saved.py`; directly corresponding tests, plus mechanical generated contracts where needed.
- **Implementation / expected outcome:** Implement owner-scoped save, list and delete with current evaluation joins and stale badges; save does not automatically trigger unbounded evaluation.
- **API operations:** list_saved, save_opportunity, delete_saved
- **Acceptance scenarios:** Repeated PUT is safe; deleting another owner save yields no disclosed metadata.
- **Handoff:** diff, actual check results, schema/config impact and reviewer note. Copy the matching prompt from plan.md.

### MS-054 — Shortlist screen

- **Owner / reviewer / priority:** M2 / M6 / P0.
- **Strict prerequisites:** MS-053 (Saved opportunity endpoints), MS-049 (Decision and evidence detail screen)
- **Requirements:** R11.01, R11.02.
- **Stories:** US-11.01, US-11.02.
- **Expected input:** relevant package contracts and the merged artifacts from every prerequisite above. External adapters use deterministic fixtures until configured live integration is explicitly run.
- **Write scope:** `frontend/src/features/saved/`; directly corresponding tests, plus mechanical generated contracts where needed.
- **Implementation / expected outcome:** Build save controls, shortlist filters and stale/refresh actions from API state.
- **API operations:** No new public endpoint; preserve the existing API contract.
- **Acceptance scenarios:** Reload preserves saves; removing a save does not delete public opportunities.
- **Handoff:** diff, actual check results, schema/config impact and reviewer note. Copy the matching prompt from plan.md.

### MS-055 — Deterministic application checklist builder

- **Owner / reviewer / priority:** M4 / M6 / P0.
- **Strict prerequisites:** MS-042 (Availability, fit, readiness and sorting), MS-036 (Requirement publication validator)
- **Requirements:** R08.05, R09.02.
- **Stories:** US-08.05, US-09.02.
- **Expected input:** relevant package contracts and the merged artifacts from every prerequisite above. External adapters use deterministic fixtures until configured live integration is explicitly run.
- **Write scope:** `backend/src/benefitbridge/applications/checklist.py`; directly corresponding tests, plus mechanical generated contracts where needed.
- **Implementation / expected outcome:** Map applicable documentary requirements and tasks to stable keys with evidence expectations; include required statement only when requested by source.
- **API operations:** No new public endpoint; preserve the existing API contract.
- **Acceptance scenarios:** Unknown applicability is a blocker, not a completed task; recomputation preserves valid manual task states.
- **Handoff:** diff, actual check results, schema/config impact and reviewer note. Copy the matching prompt from plan.md.

### MS-056 — Application and checklist API

- **Owner / reviewer / priority:** M4 / M6 / P0.
- **Strict prerequisites:** MS-052 (Application and shortlist schema), MS-055 (Deterministic application checklist builder), MS-047 (Explicit evaluation API)
- **Requirements:** R09.01, R09.02, R08.05.
- **Stories:** US-09.01, US-09.02, US-08.05.
- **Expected input:** relevant package contracts and the merged artifacts from every prerequisite above. External adapters use deterministic fixtures until configured live integration is explicitly run.
- **Write scope:** `backend/src/benefitbridge/api/applications.py`; directly corresponding tests, plus mechanical generated contracts where needed.
- **Implementation / expected outcome:** Create version-pinned application; expose list/detail; update non-draft checklist items with application revision and owner evidence validation.
- **API operations:** list_applications, create_application, get_application, patch_checklist_item
- **Acceptance scenarios:** Stale evaluation blocks creation; draft task cannot be completed manually to bypass review.
- **Handoff:** diff, actual check results, schema/config impact and reviewer note. Copy the matching prompt from plan.md.

### MS-057 — Grounded statement generation stage

- **Owner / reviewer / priority:** M3 / M1 / P0.
- **Strict prerequisites:** MS-020 (Nebius structured inference adapter), MS-056 (Application and checklist API)
- **Requirements:** R09.03, R13.02.
- **Stories:** US-09.03, US-13.02.
- **Expected input:** relevant package contracts and the merged artifacts from every prerequisite above. External adapters use deterministic fixtures until configured live integration is explicitly run.
- **Write scope:** `backend/src/benefitbridge/applications/generate.py`; directly corresponding tests, plus mechanical generated contracts where needed.
- **Implementation / expected outcome:** Generate a 150–500 word statement from confirmed facts and selected source instructions, with claim-to-fact/evidence links. Unsupported qualifications become missing-input items.
- **API operations:** No new public endpoint; preserve the existing API contract.
- **Acceptance scenarios:** Prompt injection cannot add qualifications; call budget and statement bounds enforced.
- **Handoff:** diff, actual check results, schema/config impact and reviewer note. Copy the matching prompt from plan.md.

### MS-058 — Draft claim validation and acceptance rules

- **Owner / reviewer / priority:** M4 / M6 / P0.
- **Strict prerequisites:** MS-057 (Grounded statement generation stage), MS-041 (Decision and citation verification)
- **Requirements:** R09.03, R09.04.
- **Stories:** US-09.03, US-09.04.
- **Expected input:** relevant package contracts and the merged artifacts from every prerequisite above. External adapters use deterministic fixtures until configured live integration is explicitly run.
- **Write scope:** `backend/src/benefitbridge/applications/verify_draft.py`; directly corresponding tests, plus mechanical generated contracts where needed.
- **Implementation / expected outcome:** Validate each material qualification, citations and input currentness. Persist VALID, INVALID or UNKNOWN validation with explanatory issues; only VALID current versions are acceptable.
- **API operations:** No new public endpoint; preserve the existing API contract.
- **Acceptance scenarios:** Fabricated award, stale GPA and deleted evidence block acceptance; optional style sentences need no invented evidence.
- **Handoff:** diff, actual check results, schema/config impact and reviewer note. Copy the matching prompt from plan.md.

### MS-059 — Draft versions, review and export API

- **Owner / reviewer / priority:** M3 / M1 / P0.
- **Strict prerequisites:** MS-058 (Draft claim validation and acceptance rules), MS-056 (Application and checklist API), MS-016 (Leased PostgreSQL job dispatcher)
- **Requirements:** R09.03, R09.04, R09.05.
- **Stories:** US-09.03, US-09.04, US-09.05.
- **Expected input:** relevant package contracts and the merged artifacts from every prerequisite above. External adapters use deterministic fixtures until configured live integration is explicitly run.
- **Write scope:** `backend/src/benefitbridge/api/drafts.py`; `backend/src/benefitbridge/applications/export.py`; directly corresponding tests, plus mechanical generated contracts where needed.
- **Implementation / expected outcome:** Queue generation/edit-validation, expose immutable versions, accept exact validated version with revision guard and export only current accepted text plus checklist.
- **API operations:** start_draft, get_draft, edit_draft, accept_draft, export_application
- **Acceptance scenarios:** Editing clears acceptance; stale export returns 409; unaccepted draft never counts toward readiness.
- **Handoff:** diff, actual check results, schema/config impact and reviewer note. Copy the matching prompt from plan.md.

### MS-060 — Application preparation workspace

- **Owner / reviewer / priority:** M2 / M6 / P0.
- **Strict prerequisites:** MS-059 (Draft versions, review and export API), MS-054 (Shortlist screen)
- **Requirements:** R09.01, R09.02, R09.03, R09.04, R09.05.
- **Stories:** US-09.01, US-09.02, US-09.03, US-09.04, US-09.05.
- **Expected input:** relevant package contracts and the merged artifacts from every prerequisite above. External adapters use deterministic fixtures until configured live integration is explicitly run.
- **Write scope:** `frontend/src/features/applications/`; directly corresponding tests, plus mechanical generated contracts where needed.
- **Implementation / expected outcome:** Build checklist, generation, claim review, edited-version validation, explicit acceptance and Markdown export. Keep provider submission external and user-driven.
- **API operations:** No new public endpoint; preserve the existing API contract.
- **Acceptance scenarios:** Generating text alone leaves readiness incomplete; acceptance of valid current version updates fraction.
- **Handoff:** diff, actual check results, schema/config impact and reviewer note. Copy the matching prompt from plan.md.

### MS-061 — Source refresh and structural change detection

- **Owner / reviewer / priority:** M5 / M4 / P0.
- **Strict prerequisites:** MS-043 (Discovery stage graph and candidate persistence), MS-047 (Explicit evaluation API)
- **Requirements:** R05.04, R05.05, R11.02.
- **Stories:** US-05.04, US-05.05, US-11.02.
- **Expected input:** relevant package contracts and the merged artifacts from every prerequisite above. External adapters use deterministic fixtures until configured live integration is explicitly run.
- **Write scope:** `backend/src/benefitbridge/sources/refresh.py`; `backend/src/benefitbridge/api/refresh.py`; directly corresponding tests, plus mechanical generated contracts where needed.
- **Implementation / expected outcome:** Queue explicit bounded refresh, compare hashes then semantic fields, create new versions only for changes and emit deduplicated invalidation outbox.
- **API operations:** refresh_opportunity
- **Acceptance scenarios:** Unchanged source refresh updates fetch freshness only; failed fetch preserves last-known content.
- **Handoff:** diff, actual check results, schema/config impact and reviewer note. Copy the matching prompt from plan.md.

### MS-062 — Dependency invalidation handler

- **Owner / reviewer / priority:** M1 / M3 / P0.
- **Strict prerequisites:** MS-052 (Application and shortlist schema), MS-016 (Leased PostgreSQL job dispatcher), MS-061 (Source refresh and structural change detection), MS-017 (Versioned profile read and edit API)
- **Requirements:** R02.04, R05.05, R11.02, R14.03.
- **Stories:** US-02.04, US-05.05, US-11.02, US-14.03.
- **Expected input:** relevant package contracts and the merged artifacts from every prerequisite above. External adapters use deterministic fixtures until configured live integration is explicitly run.
- **Write scope:** `backend/src/benefitbridge/invalidation.py`; directly corresponding tests, plus mechanical generated contracts where needed.
- **Implementation / expected outcome:** Consume profile/evidence/source change outbox to mark affected evaluations/applications/drafts stale, clear acceptance and enqueue bounded reevaluations for saved items. Use conservative owner-wide fallback.
- **API operations:** No new public endpoint; preserve the existing API contract.
- **Acceptance scenarios:** Repeated events are idempotent; global source change fans out through paginated jobs, never an unbounded transaction.
- **Handoff:** diff, actual check results, schema/config impact and reviewer note. Copy the matching prompt from plan.md.

### MS-063 — Document revoke and purge workflow

- **Owner / reviewer / priority:** M5 / M4 / P0.
- **Strict prerequisites:** MS-062 (Dependency invalidation handler), MS-026 (Document upload and read API), MS-016 (Leased PostgreSQL job dispatcher)
- **Requirements:** R03.05, R13.04.
- **Stories:** US-03.05, US-13.04.
- **Expected input:** relevant package contracts and the merged artifacts from every prerequisite above. External adapters use deterministic fixtures until configured live integration is explicitly run.
- **Write scope:** `backend/src/benefitbridge/documents/delete.py`; `backend/src/benefitbridge/api/document_delete.py`; directly corresponding tests, plus mechanical generated contracts where needed.
- **Implementation / expected outcome:** Tombstone document synchronously; queue object/span/candidate purge and dependent fact support revocation. Retain a fact only if independently user-confirmed; otherwise remove it in a new profile version.
- **API operations:** delete_document
- **Acceptance scenarios:** Signed download initiation fails immediately; old drafts/evidence reads are suppressed; purge retry is safe.
- **Handoff:** diff, actual check results, schema/config impact and reviewer note. Copy the matching prompt from plan.md.

### MS-064 — Account purge and capability receipt

- **Owner / reviewer / priority:** M1 / M3 / P0.
- **Strict prerequisites:** MS-063 (Document revoke and purge workflow), MS-008 (JWT authentication and account API), MS-015 (Durable runs, outbox, budget and receipt schema)
- **Requirements:** R01.05, R13.04.
- **Stories:** US-01.05, US-13.04.
- **Expected input:** relevant package contracts and the merged artifacts from every prerequisite above. External adapters use deterministic fixtures until configured live integration is explicitly run.
- **Write scope:** `backend/src/benefitbridge/accounts/delete.py`; `backend/src/benefitbridge/api/account_delete.py`; directly corresponding tests, plus mechanical generated contracts where needed.
- **Implementation / expected outcome:** Tombstone account, persist the subject-denial HMAC, cancel jobs, revoke private access and enqueue idempotent storage/DB/managed-auth purge. Return a one-time random receipt token; store only its hash and encrypted idempotent response. Receipt read uses no JWT.
- **API operations:** delete_account, get_deletion_receipt
- **Acceptance scenarios:** Old JWTs fail; purge crash resumes; receipt cannot expose profile data or be used as an API token.
- **Handoff:** diff, actual check results, schema/config impact and reviewer note. Copy the matching prompt from plan.md.

### MS-065 — Two-tenant and deletion security suite

- **Owner / reviewer / priority:** M6 / M4 / P0.
- **Strict prerequisites:** MS-064 (Account purge and capability receipt), MS-059 (Draft versions, review and export API), MS-050 (Clarification persistence and resumption), MS-030 (Run control and authenticated event stream)
- **Requirements:** R13.01, R13.02, R13.03, R13.04, R13.05, R15.05.
- **Stories:** US-13.01, US-13.02, US-13.03, US-13.04, US-13.05, US-15.05.
- **Expected input:** relevant package contracts and the merged artifacts from every prerequisite above. External adapters use deterministic fixtures until configured live integration is explicitly run.
- **Write scope:** `tests/security/test_isolation.py`; `tests/security/test_deletion.py`; directly corresponding tests, plus mechanical generated contracts where needed.
- **Implementation / expected outcome:** Exercise every private endpoint with two real synthetic tenants, RLS SQL access, streams, exports, cache and evidence IDs. Include tombstone versus in-flight worker race.
- **API operations:** No new public endpoint; preserve the existing API contract.
- **Acceptance scenarios:** Any cross-owner success or post-tombstone private publication fails release.
- **Handoff:** diff, actual check results, schema/config impact and reviewer note. Copy the matching prompt from plan.md.

### MS-066 — Failure and concurrency recovery suite

- **Owner / reviewer / priority:** M6 / M4 / P0.
- **Strict prerequisites:** MS-044 (Evaluation workflow stage), MS-064 (Account purge and capability receipt), MS-019 (Atomic cost reservations and fairness)
- **Requirements:** R10.01, R10.03, R10.04, R14.01, R15.05.
- **Stories:** US-10.01, US-10.03, US-10.04, US-14.01, US-15.05.
- **Expected input:** relevant package contracts and the merged artifacts from every prerequisite above. External adapters use deterministic fixtures until configured live integration is explicitly run.
- **Write scope:** `tests/integration/test_recovery.py`; directly corresponding tests, plus mechanical generated contracts where needed.
- **Implementation / expected outcome:** Inject provider 429/timeouts, worker death, duplicate jobs, DB rollback, stale lease completion and concurrent version updates. Verify artifact identity and budget reconciliation.
- **API operations:** No new public endpoint; preserve the existing API contract.
- **Acceptance scenarios:** Every accepted run reaches recoverable or terminal state; no duplicate visible writes or uncharged retry loops.
- **Handoff:** diff, actual check results, schema/config impact and reviewer note. Copy the matching prompt from plan.md.

### MS-067 — Public reuse and private cache invalidation

- **Owner / reviewer / priority:** M3 / M1 / P0.
- **Strict prerequisites:** MS-062 (Dependency invalidation handler), MS-044 (Evaluation workflow stage), MS-019 (Atomic cost reservations and fairness)
- **Requirements:** R14.03.
- **Stories:** US-14.03.
- **Expected input:** relevant package contracts and the merged artifacts from every prerequisite above. External adapters use deterministic fixtures until configured live integration is explicitly run.
- **Write scope:** `backend/src/benefitbridge/cache.py`; `tests/integration/test_cache.py`; directly corresponding tests, plus mechanical generated contracts where needed.
- **Implementation / expected outcome:** Implement immutable public source/parse reuse and owner-scoped decision keys including all versions and valid_until. Store no shared personal prompt completions.
- **API operations:** No new public endpoint; preserve the existing API contract.
- **Acceptance scenarios:** Profile/source/deadline changes invalidate keys; two users never share private evaluation payloads.
- **Handoff:** diff, actual check results, schema/config impact and reviewer note. Copy the matching prompt from plan.md.

### MS-068 — Usage and capability read endpoints

- **Owner / reviewer / priority:** M3 / M1 / P0.
- **Strict prerequisites:** MS-019 (Atomic cost reservations and fairness), MS-008 (JWT authentication and account API), MS-010 (Model registry and capability preflight)
- **Requirements:** R14.01, R14.02, R14.04.
- **Stories:** US-14.01, US-14.02, US-14.04.
- **Expected input:** relevant package contracts and the merged artifacts from every prerequisite above. External adapters use deterministic fixtures until configured live integration is explicitly run.
- **Write scope:** `backend/src/benefitbridge/api/usage.py`; directly corresponding tests, plus mechanical generated contracts where needed.
- **Implementation / expected outcome:** Expose user budget/actual/reserved usage, nonsecret deployment capabilities and disabled feature flags.
- **API operations:** get_usage, get_capabilities
- **Acceptance scenarios:** User cannot query another ledger; registry secrets/prices not intended for UI are not exposed.
- **Handoff:** diff, actual check results, schema/config impact and reviewer note. Copy the matching prompt from plan.md.

### MS-069 — Usage, settings and deletion controls

- **Owner / reviewer / priority:** M2 / M6 / P0.
- **Strict prerequisites:** MS-068 (Usage and capability read endpoints), MS-064 (Account purge and capability receipt), MS-060 (Application preparation workspace)
- **Requirements:** R01.04, R01.05, R13.04, R14.01.
- **Stories:** US-01.04, US-01.05, US-13.04, US-14.01.
- **Expected input:** relevant package contracts and the merged artifacts from every prerequisite above. External adapters use deterministic fixtures until configured live integration is explicitly run.
- **Write scope:** `frontend/src/features/settings/`; directly corresponding tests, plus mechanical generated contracts where needed.
- **Implementation / expected outcome:** Show relevant usage limits, timezone/profile privacy, document/account deletion and copyable receipt. Confirm irreversible account deletion with exact DELETE text.
- **API operations:** No new public endpoint; preserve the existing API contract.
- **Acceptance scenarios:** After tombstone local auth state is cleared; receipt status works without account session.
- **Handoff:** diff, actual check results, schema/config impact and reviewer note. Copy the matching prompt from plan.md.

### MS-070 — Optional watch persistence

- **Owner / reviewer / priority:** M1 / M3 / P1.
- **Strict prerequisites:** MS-052 (Application and shortlist schema)
- **Requirements:** R11.03, R11.04, R11.05.
- **Stories:** US-11.03, US-11.04, US-11.05.
- **Expected input:** relevant package contracts and the merged artifacts from every prerequisite above. External adapters use deterministic fixtures until configured live integration is explicitly run.
- **Write scope:** `backend/migrations/versions/0007_watch.py`; `backend/src/benefitbridge/db/watch.py`; directly corresponding tests, plus mechanical generated contracts where needed.
- **Implementation / expected outcome:** Add watches and notifications with owner FK, cadence, pause, next_due and unique version-change keys. Always ship schema safely; feature remains disabled unless enabled.
- **API operations:** No new public endpoint; preserve the existing API contract.
- **Acceptance scenarios:** P0 behavior unchanged when flag off; duplicate notifications blocked.
- **Handoff:** diff, actual check results, schema/config impact and reviewer note. Copy the matching prompt from plan.md.

### MS-071 — Optional saved-page watch scheduler

- **Owner / reviewer / priority:** M5 / M4 / P1.
- **Strict prerequisites:** MS-070 (Optional watch persistence), MS-061 (Source refresh and structural change detection), MS-062 (Dependency invalidation handler)
- **Requirements:** R11.03, R11.04, R11.05.
- **Stories:** US-11.03, US-11.04, US-11.05.
- **Expected input:** relevant package contracts and the merged artifacts from every prerequisite above. External adapters use deterministic fixtures until configured live integration is explicitly run.
- **Write scope:** `backend/src/benefitbridge/watch/scheduler.py`; directly corresponding tests, plus mechanical generated contracts where needed.
- **Implementation / expected outcome:** Poll only due enabled saved-page watches with shared-source deduplication, quotas and paginated fanout. Emit in-app notification after material version change.
- **API operations:** No new public endpoint; preserve the existing API contract.
- **Acceptance scenarios:** Paused watches do not queue; unchanged content produces none; source failure yields status not false closure.
- **Handoff:** diff, actual check results, schema/config impact and reviewer note. Copy the matching prompt from plan.md.

### MS-072 — Optional watch and notification API

- **Owner / reviewer / priority:** M5 / M4 / P1.
- **Strict prerequisites:** MS-071 (Optional saved-page watch scheduler), MS-008 (JWT authentication and account API)
- **Requirements:** R11.03, R11.04, R11.05.
- **Stories:** US-11.03, US-11.04, US-11.05.
- **Expected input:** relevant package contracts and the merged artifacts from every prerequisite above. External adapters use deterministic fixtures until configured live integration is explicitly run.
- **Write scope:** `backend/src/benefitbridge/api/watch.py`; directly corresponding tests, plus mechanical generated contracts where needed.
- **Implementation / expected outcome:** Implement flag-gated watch CRUD and notification list/read using revision guards and owner checks.
- **API operations:** list_watches, create_watch, patch_watch, delete_watch, list_notifications, read_notification
- **Acceptance scenarios:** Disabled feature returns FEATURE_DISABLED; another owner ID returns 404.
- **Handoff:** diff, actual check results, schema/config impact and reviewer note. Copy the matching prompt from plan.md.

### MS-073 — Optional watch controls and notification inbox

- **Owner / reviewer / priority:** M2 / M6 / P1.
- **Strict prerequisites:** MS-072 (Optional watch and notification API), MS-054 (Shortlist screen)
- **Requirements:** R11.03, R11.04, R11.05.
- **Stories:** US-11.03, US-11.04, US-11.05.
- **Expected input:** relevant package contracts and the merged artifacts from every prerequisite above. External adapters use deterministic fixtures until configured live integration is explicitly run.
- **Write scope:** `frontend/src/features/watch/`; directly corresponding tests, plus mechanical generated contracts where needed.
- **Implementation / expected outcome:** Add cadence/pause controls and notifications only when capabilities enable watch.
- **API operations:** No new public endpoint; preserve the existing API contract.
- **Acceptance scenarios:** Hidden feature has no live requests; read state and pause survive reload.
- **Handoff:** diff, actual check results, schema/config impact and reviewer note. Copy the matching prompt from plan.md.

### MS-074 — Redacted operational metrics and health

- **Owner / reviewer / priority:** M3 / M1 / P0.
- **Strict prerequisites:** MS-016 (Leased PostgreSQL job dispatcher), MS-010 (Model registry and capability preflight), MS-067 (Public reuse and private cache invalidation), MS-068 (Usage and capability read endpoints)
- **Requirements:** R13.05, R14.04.
- **Stories:** US-13.05, US-14.04.
- **Expected input:** relevant package contracts and the merged artifacts from every prerequisite above. External adapters use deterministic fixtures until configured live integration is explicitly run.
- **Write scope:** `backend/src/benefitbridge/observability.py`; `backend/src/benefitbridge/api/health.py`; directly corresponding tests, plus mechanical generated contracts where needed.
- **Implementation / expected outcome:** Expose liveness/readiness, queue lag, stage failure, cost and invalidation metrics; configure low-frequency synthetic checks separately from probes.
- **API operations:** health_live, health_ready
- **Acceptance scenarios:** No PII canaries in logs; readiness detects DB/worker/config failures without paid calls.
- **Handoff:** diff, actual check results, schema/config impact and reviewer note. Copy the matching prompt from plan.md.

### MS-075 — Production dependency composition

- **Owner / reviewer / priority:** M3 / M1 / P0.
- **Strict prerequisites:** MS-074 (Redacted operational metrics and health), MS-046 (Discovery and URL-import commands), MS-050 (Clarification persistence and resumption), MS-059 (Draft versions, review and export API), MS-064 (Account purge and capability receipt), MS-027 (PDF to reviewable fact candidates), MS-061 (Source refresh and structural change detection)
- **Requirements:** R16.01, R16.03.
- **Stories:** US-16.01, US-16.03.
- **Expected input:** relevant package contracts and the merged artifacts from every prerequisite above. External adapters use deterministic fixtures until configured live integration is explicitly run.
- **Write scope:** `backend/src/benefitbridge/composition.py`; `backend/src/benefitbridge/api/registry.py`; `backend/src/benefitbridge/workflows/registry.py`; directly corresponding tests, plus mechanical generated contracts where needed.
- **Implementation / expected outcome:** Bind every P0 router/provider/stage to real configured dependencies; require explicit test mode for fakes. Include DEMO_RESET interface registration with disabled-until-installed behavior.
- **API operations:** No new public endpoint; preserve the existing API contract.
- **Acceptance scenarios:** Startup identifies missing P0 dependencies; ordinary request and worker processes use the same schemas.
- **Handoff:** diff, actual check results, schema/config impact and reviewer note. Copy the matching prompt from plan.md.

### MS-076 — API and generated client contract gate

- **Owner / reviewer / priority:** M6 / M4 / P0.
- **Strict prerequisites:** MS-075 (Production dependency composition)
- **Requirements:** R16.01, R15.05.
- **Stories:** US-16.01, US-15.05.
- **Expected input:** relevant package contracts and the merged artifacts from every prerequisite above. External adapters use deterministic fixtures until configured live integration is explicitly run.
- **Write scope:** `tests/contracts/`; `scripts/check_contract.py`; directly corresponding tests, plus mechanical generated contracts where needed.
- **Implementation / expected outcome:** Validate every P0 operation, sample, error envelope and generated client against exported OpenAPI. Gate operation IDs and forbidden DTO drift.
- **API operations:** No new public endpoint; preserve the existing API contract.
- **Acceptance scenarios:** Unknown fields, UUIDs, decimal strings and SSE exceptions match API.md; generation leaves no unexplained diff.
- **Handoff:** diff, actual check results, schema/config impact and reviewer note. Copy the matching prompt from plan.md.

### MS-077 — Requirement and grounding evaluation harness

- **Owner / reviewer / priority:** M6 / M4 / P0.
- **Strict prerequisites:** MS-024 (Annotation and adjudication tooling), MS-036 (Requirement publication validator)
- **Requirements:** R15.01, R15.02.
- **Stories:** US-15.01, US-15.02.
- **Expected input:** relevant package contracts and the merged artifacts from every prerequisite above. External adapters use deterministic fixtures until configured live integration is explicitly run.
- **Write scope:** `evaluation/extraction.py`; `evaluation/grounding.py`; directly corresponding tests, plus mechanical generated contracts where needed.
- **Implementation / expected outcome:** Compute typed leaf matching, mandatory recall, graph exact match and quote validity from frozen examples; produce blinded human entailment review sample.
- **API operations:** No new public endpoint; preserve the existing API contract.
- **Acceptance scenarios:** Known perfect/missing/spurious examples yield exact expected counts; invalid citations count as errors.
- **Handoff:** diff, actual check results, schema/config impact and reviewer note. Copy the matching prompt from plan.md.

### MS-078 — Eligibility and coverage evaluation harness

- **Owner / reviewer / priority:** M6 / M4 / P0.
- **Strict prerequisites:** MS-024 (Annotation and adjudication tooling), MS-041 (Decision and citation verification)
- **Requirements:** R15.03.
- **Stories:** US-15.03.
- **Expected input:** relevant package contracts and the merged artifacts from every prerequisite above. External adapters use deterministic fixtures until configured live integration is explicitly run.
- **Write scope:** `evaluation/eligibility.py`; `evaluation/statistics.py`; directly corresponding tests, plus mechanical generated contracts where needed.
- **Implementation / expected outcome:** Report three-label confusion including technical failures, MET precision, unsafe promotion, unknown recall, coverage and opportunity-family grouped intervals. Include rare-event bounds with assumptions.
- **API operations:** No new public endpoint; preserve the existing API contract.
- **Acceptance scenarios:** All-UNKNOWN baseline fails coverage; failures stay in denominator; zero errors are not reported as zero risk.
- **Handoff:** diff, actual check results, schema/config impact and reviewer note. Copy the matching prompt from plan.md.

### MS-079 — Frozen and live discovery evaluation harness

- **Owner / reviewer / priority:** M5 / M4 / P0.
- **Strict prerequisites:** MS-024 (Annotation and adjudication tooling), MS-033 (Conservative opportunity canonicalization), MS-034 (Bounded redacted goal planner)
- **Requirements:** R15.02.
- **Stories:** US-15.02.
- **Expected input:** relevant package contracts and the merged artifacts from every prerequisite above. External adapters use deterministic fixtures until configured live integration is explicitly run.
- **Write scope:** `evaluation/retrieval.py`; `evaluation/live_discovery.py`; directly corresponding tests, plus mechanical generated contracts where needed.
- **Implementation / expected outcome:** Create deterministic corpus adapter, query relevance judgments and Precision@5/Recall@10/nDCG; record separate live runs and funnel stages.
- **API operations:** No new public endpoint; preserve the existing API contract.
- **Acceptance scenarios:** Truncated candidate tail is unevaluated; frozen recall is labeled bounded-corpus recall.
- **Handoff:** diff, actual check results, schema/config impact and reviewer note. Copy the matching prompt from plan.md.

### MS-080 — Paired model and cost experiment runner

- **Owner / reviewer / priority:** M6 / M4 / P0.
- **Strict prerequisites:** MS-078 (Eligibility and coverage evaluation harness), MS-077 (Requirement and grounding evaluation harness), MS-019 (Atomic cost reservations and fairness), MS-010 (Model registry and capability preflight)
- **Requirements:** R15.04.
- **Stories:** US-15.04.
- **Expected input:** relevant package contracts and the merged artifacts from every prerequisite above. External adapters use deterministic fixtures until configured live integration is explicitly run.
- **Write scope:** `evaluation/experiments.py`; `evaluation/variants.yaml`; directly corresponding tests, plus mechanical generated contracts where needed.
- **Implementation / expected outcome:** Run B0, B1, B3 and B4 with frozen manifests, same sources/budgets and retries charged; optional B5 only after budget approval. Separate warm/cold cache and deterministic clocks.
- **API operations:** No new public endpoint; preserve the existing API contract.
- **Acceptance scenarios:** Variant configuration hashes differ intentionally; results cannot omit failed cases or tune on test.
- **Handoff:** diff, actual check results, schema/config impact and reviewer note. Copy the matching prompt from plan.md.

### MS-081 — Main journey browser acceptance suite

- **Owner / reviewer / priority:** M2 / M6 / P0.
- **Strict prerequisites:** MS-069 (Usage, settings and deletion controls), MS-051 (Targeted fact clarification UI), MS-076 (API and generated client contract gate)
- **Requirements:** R12.04, R15.05.
- **Stories:** US-12.04, US-15.05.
- **Expected input:** relevant package contracts and the merged artifacts from every prerequisite above. External adapters use deterministic fixtures until configured live integration is explicitly run.
- **Write scope:** `frontend/e2e/`; directly corresponding tests, plus mechanical generated contracts where needed.
- **Implementation / expected outcome:** Automate synthetic-account profile, upload, discovery, evidence, UNKNOWN clarification, draft acceptance, export and deletion using deterministic provider fixtures.
- **API operations:** No new public endpoint; preserve the existing API contract.
- **Acceptance scenarios:** Keyboard paths and error recovery pass; no paid endpoints in ordinary CI.
- **Handoff:** diff, actual check results, schema/config impact and reviewer note. Copy the matching prompt from plan.md.

### MS-082 — Capacity and queue load experiment

- **Owner / reviewer / priority:** M6 / M4 / P0.
- **Strict prerequisites:** MS-075 (Production dependency composition), MS-066 (Failure and concurrency recovery suite)
- **Requirements:** R14.05, R15.05.
- **Stories:** US-14.05, US-15.05.
- **Expected input:** relevant package contracts and the merged artifacts from every prerequisite above. External adapters use deterministic fixtures until configured live integration is explicitly run.
- **Write scope:** `evaluation/load/`; directly corresponding tests, plus mechanical generated contracts where needed.
- **Implementation / expected outcome:** Build separate cached browsing and discovery-burst scenarios, latency distributions, queue delay and fairness reports. Real-provider run is explicit opt-in with reserved cost.
- **API operations:** No new public endpoint; preserve the existing API contract.
- **Acceptance scenarios:** 20 browsing sessions and 10 discovery bursts are separately measured; full/partial/failure outcomes remain distinct.
- **Handoff:** diff, actual check results, schema/config impact and reviewer note. Copy the matching prompt from plan.md.

### MS-083 — Deployment and migration release assets

- **Owner / reviewer / priority:** M1 / M3 / P0.
- **Strict prerequisites:** MS-075 (Production dependency composition), MS-065 (Two-tenant and deletion security suite), MS-066 (Failure and concurrency recovery suite)
- **Requirements:** R16.03.
- **Stories:** US-16.03.
- **Expected input:** relevant package contracts and the merged artifacts from every prerequisite above. External adapters use deterministic fixtures until configured live integration is explicitly run.
- **Write scope:** `Dockerfile`; `deploy/`; `scripts/migrate_release.sh`; directly corresponding tests, plus mechanical generated contracts where needed.
- **Implementation / expected outcome:** Create immutable API/worker image, reverse proxy/SSE settings, migration job, secrets mapping, private storage settings, health checks and rollback commands. Do not deploy during this sprint.
- **API operations:** No new public endpoint; preserve the existing API contract.
- **Acceptance scenarios:** Local image startup and migration smoke pass; no secrets in image; rollback documents DB compatibility.
- **Handoff:** diff, actual check results, schema/config impact and reviewer note. Copy the matching prompt from plan.md.

### MS-084 — Isolated synthetic demo scenarios and reset

- **Owner / reviewer / priority:** M5 / M4 / P0.
- **Strict prerequisites:** MS-075 (Production dependency composition), MS-056 (Application and checklist API), MS-027 (PDF to reviewable fact candidates), MS-083 (Deployment and migration release assets)
- **Requirements:** R12.05, R16.04.
- **Stories:** US-12.05, US-16.04.
- **Expected input:** relevant package contracts and the merged artifacts from every prerequisite above. External adapters use deterministic fixtures until configured live integration is explicitly run.
- **Write scope:** `backend/src/benefitbridge/demo/`; `backend/src/benefitbridge/api/demo.py`; `tests/demo/`; directly corresponding tests, plus mechanical generated contracts where needed.
- **Implementation / expected outcome:** Create clearly synthetic applicant/source/evidence fixtures for MET, NOT_MET and UNKNOWN; implement owner-scoped DEMO_RESET run and register handler through the existing demo hook.
- **API operations:** reset_demo
- **Acceptance scenarios:** Reset cannot target arbitrary accounts; concurrent resets serialize and invalidate old demo artifacts.
- **Handoff:** diff, actual check results, schema/config impact and reviewer note. Copy the matching prompt from plan.md.

### MS-085 — Reproducible result report generator

- **Owner / reviewer / priority:** M6 / M4 / P0.
- **Strict prerequisites:** MS-080 (Paired model and cost experiment runner), MS-079 (Frozen and live discovery evaluation harness), MS-082 (Capacity and queue load experiment), MS-065 (Two-tenant and deletion security suite)
- **Requirements:** R15.01, R15.02, R15.03, R15.04, R15.05.
- **Stories:** US-15.01, US-15.02, US-15.03, US-15.04, US-15.05.
- **Expected input:** relevant package contracts and the merged artifacts from every prerequisite above. External adapters use deterministic fixtures until configured live integration is explicitly run.
- **Write scope:** `evaluation/report.py`; `evaluation/report_template.md`; directly corresponding tests, plus mechanical generated contracts where needed.
- **Implementation / expected outcome:** Generate tables, denominators, confidence intervals, slices, provenance and gate status from actual run manifests. Unrun studies remain NOT_RUN.
- **API operations:** No new public endpoint; preserve the existing API contract.
- **Acceptance scenarios:** Missing results never become zero failures or passing gates; grouped confidence intervals identify grouping.
- **Handoff:** diff, actual check results, schema/config impact and reviewer note. Copy the matching prompt from plan.md.

### MS-086 — User study task and observation kit

- **Owner / reviewer / priority:** M2 / M6 / P0.
- **Strict prerequisites:** MS-049 (Decision and evidence detail screen), MS-060 (Application preparation workspace)
- **Requirements:** R15.05, R12.04.
- **Stories:** US-15.05, US-12.04.
- **Expected input:** relevant package contracts and the merged artifacts from every prerequisite above. External adapters use deterministic fixtures until configured live integration is explicitly run.
- **Write scope:** `research/usability/`; directly corresponding tests, plus mechanical generated contracts where needed.
- **Implementation / expected outcome:** Prepare eight-participant counterbalanced manual-search versus BenefitBridge tasks, consent script, timing sheet and blinded correctness rubric. This sprint prepares the study, not participant sessions.
- **API operations:** No new public endpoint; preserve the existing API contract.
- **Acceptance scenarios:** Task order and success definitions are fixed before recruitment; no fabricated study outcomes.
- **Handoff:** diff, actual check results, schema/config impact and reviewer note. Copy the matching prompt from plan.md.

### MS-087 — Video storyboard and submission materials

- **Owner / reviewer / priority:** M2 / M6 / P0.
- **Strict prerequisites:** MS-084 (Isolated synthetic demo scenarios and reset), MS-085 (Reproducible result report generator), MS-086 (User study task and observation kit)
- **Requirements:** R16.04, R16.05.
- **Stories:** US-16.04, US-16.05.
- **Expected input:** relevant package contracts and the merged artifacts from every prerequisite above. External adapters use deterministic fixtures until configured live integration is explicitly run.
- **Write scope:** `docs/demo.md`; `docs/submission.md`; `README.md`; `LICENSE`; directly corresponding tests, plus mechanical generated contracts where needed.
- **Implementation / expected outcome:** Write a 2:50 working-demo storyboard, source-to-evidence walkthrough, UNKNOWN moment, benchmark claims from actual report and setup instructions. Select MIT license only after team confirmation recorded in release checklist.
- **API operations:** No new public endpoint; preserve the existing API contract.
- **Acceptance scenarios:** Video allocation totals 170 seconds; unmeasured claims stay labeled; setup describes real credentials and synthetic fixture mode.
- **Handoff:** diff, actual check results, schema/config impact and reviewer note. Copy the matching prompt from plan.md.

### MS-088 — Operations, retention and incident runbook

- **Owner / reviewer / priority:** M1 / M3 / P0.
- **Strict prerequisites:** MS-083 (Deployment and migration release assets), MS-064 (Account purge and capability receipt), MS-074 (Redacted operational metrics and health)
- **Requirements:** R13.04, R14.04, R16.03.
- **Stories:** US-13.04, US-14.04, US-16.03.
- **Expected input:** relevant package contracts and the merged artifacts from every prerequisite above. External adapters use deterministic fixtures until configured live integration is explicitly run.
- **Write scope:** `docs/runbook.md`; `docs/retention.md`; directly corresponding tests, plus mechanical generated contracts where needed.
- **Implementation / expected outcome:** Document verified provider retention, restore/purge replay, judge-access checks, budget reserve, incident ownership and operation through 16 December UTC.
- **API operations:** No new public endpoint; preserve the existing API contract.
- **Acceptance scenarios:** Restore cannot resurrect tombstoned users; operator drill includes exhausted credits and dead worker.
- **Handoff:** diff, actual check results, schema/config impact and reviewer note. Copy the matching prompt from plan.md.

### MS-089 — Release readiness evidence collector

- **Owner / reviewer / priority:** M6 / M4 / P0.
- **Strict prerequisites:** MS-076 (API and generated client contract gate), MS-081 (Main journey browser acceptance suite), MS-085 (Reproducible result report generator), MS-088 (Operations, retention and incident runbook), MS-087 (Video storyboard and submission materials)
- **Requirements:** R16.02, R16.03, R16.04, R16.05.
- **Stories:** US-16.02, US-16.03, US-16.04, US-16.05.
- **Expected input:** relevant package contracts and the merged artifacts from every prerequisite above. External adapters use deterministic fixtures until configured live integration is explicitly run.
- **Write scope:** `scripts/release_check.py`; `docs/release_checklist.md`; directly corresponding tests, plus mechanical generated contracts where needed.
- **Implementation / expected outcome:** Collect commit/config/dataset hashes and gate outcomes, verify public links manually through checklist, and produce explicit GO/BLOCKED report. Do not fabricate human signoffs or execute deployment.
- **API operations:** No new public endpoint; preserve the existing API contract.
- **Acceptance scenarios:** Any isolation failure, missing live runtime proof, absent license or unverified judge access blocks GO.
- **Handoff:** diff, actual check results, schema/config impact and reviewer note. Copy the matching prompt from plan.md.

## Work that must not be disguised as a one-prompt coding sprint

Accounts/credits and provider entitlement checks, source permission review, double annotation and adjudication, recruitment and eight participant sessions, paid live benchmarks, actual deployment, a public video recording, licensing agreement and final submission are human/operator work packages H01–H06 in plan.md. The coding micro-sprints create their tooling and reviewable assets; they do not automatically complete those activities. Benchmark harness success is not a passing model benchmark. A report generator cannot invent results.

## Dependency change control

If a task discovers a missing interface, identify its owning prerequisite and update both the dependency table and plan prompt before proceeding. Add a small prerequisite task only when unavoidable and give it a new stable ID; never renumber merged work. Recompute owner scheduling and critical path after scope changes. M6 tracks actual completion, blocked time and gate failures daily. M1 reviews schema changes, M3 interface/composition changes and M4 semantic contract changes.
