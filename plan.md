# BenefitBridge — Six-Developer Execution Plan

**BenefitBridge · Best Apps and Agents · Six-person implementation package · 4 October 2026**

[requirements.md](requirements.md) | [userStory.md](userStory.md) | [sprints.md](sprints.md) | [design.md](design.md) | [API.md](API.md) | [plan.md](plan.md) | [agent.md](agent.md)

## 1. Delivery objective and working agreement

Deliver a hosted, private multi-user web application that turns a goal and confirmed applicant facts into source-grounded opportunity decisions and a reviewed application draft. The demonstrable path is profile → evidence review → live discovery → rule/evidence explanation → one clarification → checklist → truthful draft acceptance → export. The system must also preserve job durability, deletion, cost controls and measured quality. Optional watch functionality is the first scope cut.

Use the common system prompt and the owner's role block in agent.md, then copy one numbered prompt below into an isolated developer session. Every task has one reviewable code output, explicit prerequisites and a default reviewer. A single prompt is the assignment boundary, not a guarantee that no debugging or human review will be needed. The current task requested this design only; deployment, paid experiments and code implementation occur later under the team's execution process.

## 2. Six-person ownership and review

| Member | Suggested background | Primary ownership | Default reviewer | P0 implementation hours |
| --- | --- | --- | --- | --- |
| M1 | Software Engineering | Platform and data | M3 | 45.5 |
| M2 | Software Engineering | Frontend and user experience | M6 | 35.5 |
| M3 | AI Engineering | Workflow and inference | M1 | 48.0 |
| M4 | AI Science | Rules and verification | M6 | 37.5 |
| M5 | AI Engineering | Sources and evidence | M4 | 36.5 |
| M6 | AI Science | Evaluation and quality | M4 | 33.0 |

M1 leads data/tenancy/release operations; M3 leads interfaces and integration; M6 maintains the board, dependency status and release evidence. M2 owns product flow and demo narration; M4 owns decision semantics; M5 owns source/evidence quality. People may pair, but each task has exactly one merge owner. Reviewers check invariants relevant to the change; M1 additionally reviews all migrations/security-sensitive data writes, M3 registry/queue changes and M4 rule/claim semantics.

Keep branches short and scope one PR to one micro-sprint. Before starting, pull merged prerequisites, inspect their actual interfaces and preserve unrelated work. Default WIP limit: one implementation task/member plus one small review. Reserve a daily 15-minute dependency check and a working integration window; do not count an unfinished prerequisite as ready because its API shape was discussed.

## 3. Capacity, dates and dependency schedule

Planning baseline: roughly 22 hours/person/week for 3.5 weeks, about 462 team-hours. Core micro-sprints total 236 estimated human-hours; the four optional watch tasks add 10. Reserve about 85 hours for source collection/double annotation/adjudication, 12 for user sessions and analysis, 34 for provider setup/live integration/deployment/operations preparation and 16 for demo recording/submission. That totals 383 P0 hours and leaves approximately 79 hours for review overlap, defects and uncertainty. Annotation may require 80–110 hours; if it reaches the high end, remaining contingency falls to about 54 hours. Re-estimate with actual team availability on 4 October.

The table below is a **resource-constrained planning model**, not a promise. It enforces task prerequisites and one coding unit per owner. Offsets are hours within shared implementation/handoff windows, not elapsed wall-clock latency of the application. Map four coordinated hours per day from 4 October to calendar targets; members use idle dependency windows for their assigned annotation/review work. This requires reliable handoffs even when their personal active coding hours are lower. Reviewer availability, paid-job duration and external access can add delay; the buffer days exist for that reason.

The pure dependency critical path is **69.5 hours**. The greedy owner-constrained P0 code schedule spans **86 shared-window hours**, targeting code/gate tooling completion around **25 October**. Human evidence gates complete separately. Critical dependency chain: `MS-001 → MS-002 → MS-007 → MS-014 → MS-015 → MS-019 → MS-020 → MS-027 → MS-028 → MS-037 → MS-039 → MS-040 → MS-041 → MS-044 → MS-047 → MS-056 → MS-057 → MS-058 → MS-059 → MS-075 → MS-083 → MS-084 → MS-087 → MS-089`. A critical path is a lower bound; it is not the sum of all team-hours.

| Window | Required milestone | Parallel human work / decision |
| --- | --- | --- |
| 4–6 October | Repository/domain/ports and account/data foundations; provision provider access | All members calibrate annotation guide on development cases; M1/M3 record actual quotas and model capability |
| 7–10 October | Profile editing, document schemas, queue/budget and safe source adapters | M5 curates policy families; M6 validates split manifest; two-person annotation begins |
| 11–15 October | Reviewable document facts, source canonicalization and requirement/decision engine slices | Test graphs and factual boundary cases; isolate locked test labels from prompt authors |
| 16–19 October | End-to-end development discovery/detail/clarification and application APIs | Freeze intended benchmark scope; check annotation throughput; no optional watch if behind |
| 20–23 October | Application UI, privacy lifecycle, production composition, isolated demo and deployment assets | Freeze prompts/routing before locked test; finish gold by 21 October or declare reduced set; rehearse live setup |
| 24–26 October | Contract/browser/security/load evidence, report generator and measured runs; eight-person study | Use fixed code/config for final comparison; record failures; narrow claims if gates fail |
| 27–28 October | Fix release blockers, verify hosted judge path, record video and public materials | No new features; rollback/restore/purge drill and funding reserve; retest affected gates only |
| 29 October | Internal submission deadline, link/video/license/roster verification | All six sign off factual claims and responsibilities; record official submission receipt |
| 30 October 17:00 UTC | Official deadline anchor | Keep buffer for submission access problems; do not plan core implementation here |
| 31 October–16 December UTC | Hosted judge access and operation | M1/M3 operator rota, low-cost synthetic checks, funded balance and incident response |

### Owner-constrained task schedule

Tasks whose intervals overlap can run in parallel because their owners differ and prerequisites are satisfied. All offsets start at hour zero. A task can start early only if every prerequisite is actually merged and its owner is free. The full prerequisite list remains in sprints.md and each prompt.

| ID | Owner | Start–finish h | Calendar target | Work |
| --- | --- | --- | --- | --- |
| MS-001 | M1 | 0–3 | 04 Oct | Repository, reproducible commands and configuration |
| MS-002 | M4 | 3–6 | 04 Oct–05 Oct | Shared domain schemas and enums |
| MS-005 | M6 | 3–5.5 | 04 Oct–05 Oct | CI and reusable test harness |
| MS-007 | M1 | 6–9 | 05 Oct–06 Oct | Account and profile schema |
| MS-004 | M2 | 6–8.5 | 05 Oct–06 Oct | Web shell and state conventions |
| MS-003 | M3 | 6–9 | 05 Oct–06 Oct | Provider and stage interfaces |
| MS-011 | M4 | 6–9 | 05 Oct–06 Oct | Deterministic fact predicates |
| MS-006 | M5 | 6–8.5 | 05 Oct–06 Oct | Source and normalized span contract |
| MS-013 | M6 | 6–8.5 | 05 Oct–06 Oct | Dataset manifest and split validator |
| MS-024 | M6 | 8.5–11 | 06 Oct | Annotation and adjudication tooling |
| MS-008 | M1 | 9–12 | 06 Oct | JWT authentication and account API |
| MS-010 | M3 | 9–11.5 | 06 Oct | Model registry and capability preflight |
| MS-023 | M4 | 9–12 | 06 Oct | Three-valued graph evaluation |
| MS-012 | M5 | 9–12 | 06 Oct | Bounded digital PDF parsing |
| MS-014 | M1 | 12–14.5 | 07 Oct | Public sources and opportunity schema |
| MS-009 | M2 | 12–14.5 | 07 Oct | Managed-auth and consent screens |
| MS-021 | M5 | 12–15 | 07 Oct | Safe fetching and untrusted-content boundary |
| MS-015 | M1 | 14.5–17.5 | 07 Oct–08 Oct | Durable runs, outbox, budget and receipt schema |
| MS-017 | M1 | 17.5–20.5 | 08 Oct–09 Oct | Versioned profile read and edit API |
| MS-016 | M3 | 17.5–20.5 | 08 Oct–09 Oct | Leased PostgreSQL job dispatcher |
| MS-025 | M1 | 20.5–23 | 09 Oct | Private evidence schema |
| MS-018 | M2 | 20.5–23 | 09 Oct | Structured profile editor |
| MS-019 | M3 | 20.5–23.5 | 09 Oct | Atomic cost reservations and fairness |
| MS-026 | M1 | 23–26 | 09 Oct–10 Oct | Document upload and read API |
| MS-020 | M3 | 23.5–26.5 | 09 Oct–10 Oct | Nebius structured inference adapter |
| MS-022 | M5 | 23.5–26.5 | 09 Oct–10 Oct | Tavily discovery and source fetch adapter |
| MS-038 | M1 | 26–29 | 10 Oct–11 Oct | Requirement and evaluation persistence |
| MS-030 | M3 | 26.5–29.5 | 10 Oct–11 Oct | Run control and authenticated event stream |
| MS-035 | M4 | 26.5–29.5 | 10 Oct–11 Oct | Requirement AST extraction |
| MS-027 | M5 | 26.5–29.5 | 10 Oct–11 Oct | PDF to reviewable fact candidates |
| MS-052 | M1 | 29–32 | 11 Oct | Application and shortlist schema |
| MS-031 | M2 | 29.5–32 | 11 Oct | Durable progress components |
| MS-034 | M3 | 29.5–32 | 11 Oct | Bounded redacted goal planner |
| MS-036 | M4 | 29.5–32.5 | 11 Oct–12 Oct | Requirement publication validator |
| MS-032 | M5 | 29.5–32.5 | 11 Oct–12 Oct | Public snapshot storage and authority resolution |
| MS-028 | M1 | 32–34.5 | 12 Oct | Fact candidate review API |
| MS-068 | M3 | 32–34.5 | 12 Oct | Usage and capability read endpoints |
| MS-033 | M5 | 32.5–35 | 12 Oct | Conservative opportunity canonicalization |
| MS-077 | M6 | 32.5–35 | 12 Oct | Requirement and grounding evaluation harness |
| MS-029 | M2 | 34.5–37 | 12 Oct–13 Oct | Upload and fact review experience |
| MS-043 | M3 | 35–38 | 12 Oct–13 Oct | Discovery stage graph and candidate persistence |
| MS-037 | M5 | 35–37.5 | 12 Oct–13 Oct | Owner-scoped evidence retrieval |
| MS-039 | M4 | 37.5–40.5 | 13 Oct–14 Oct | Bounded semantic predicate evaluator |
| MS-045 | M5 | 37.5–40 | 13 Oct | Public opportunity and source reads |
| MS-053 | M1 | 40–42.5 | 14 Oct | Saved opportunity endpoints |
| MS-079 | M5 | 40–42.5 | 14 Oct | Frozen and live discovery evaluation harness |
| MS-040 | M4 | 40.5–43.5 | 14 Oct | Eligibility aggregation and publication guards |
| MS-041 | M4 | 43.5–46.5 | 14 Oct–15 Oct | Decision and citation verification |
| MS-042 | M4 | 46.5–49 | 15 Oct–16 Oct | Availability, fit, readiness and sorting |
| MS-078 | M6 | 46.5–49.5 | 15 Oct–16 Oct | Eligibility and coverage evaluation harness |
| MS-044 | M3 | 49–52 | 16 Oct | Evaluation workflow stage |
| MS-055 | M4 | 49–51.5 | 16 Oct | Deterministic application checklist builder |
| MS-080 | M6 | 49.5–52.5 | 16 Oct–17 Oct | Paired model and cost experiment runner |
| MS-046 | M3 | 52–54.5 | 17 Oct | Discovery and URL-import commands |
| MS-047 | M4 | 52–54.5 | 17 Oct | Explicit evaluation API |
| MS-048 | M2 | 54.5–57 | 17 Oct–18 Oct | Discovery form and results feed |
| MS-050 | M3 | 54.5–57.5 | 17 Oct–18 Oct | Clarification persistence and resumption |
| MS-056 | M4 | 54.5–57.5 | 17 Oct–18 Oct | Application and checklist API |
| MS-061 | M5 | 54.5–57.5 | 17 Oct–18 Oct | Source refresh and structural change detection |
| MS-049 | M2 | 57–59.5 | 18 Oct | Decision and evidence detail screen |
| MS-062 | M1 | 57.5–60.5 | 18 Oct–19 Oct | Dependency invalidation handler |
| MS-057 | M3 | 57.5–60.5 | 18 Oct–19 Oct | Grounded statement generation stage |
| MS-051 | M2 | 59.5–62 | 18 Oct–19 Oct | Targeted fact clarification UI |
| MS-067 | M3 | 60.5–63 | 19 Oct | Public reuse and private cache invalidation |
| MS-058 | M4 | 60.5–63.5 | 19 Oct | Draft claim validation and acceptance rules |
| MS-063 | M5 | 60.5–63.5 | 19 Oct | Document revoke and purge workflow |
| MS-054 | M2 | 62–64.5 | 19 Oct–20 Oct | Shortlist screen |
| MS-074 | M3 | 63–65.5 | 19 Oct–20 Oct | Redacted operational metrics and health |
| MS-064 | M1 | 63.5–66.5 | 19 Oct–20 Oct | Account purge and capability receipt |
| MS-059 | M3 | 65.5–68.5 | 20 Oct–21 Oct | Draft versions, review and export API |
| MS-066 | M6 | 66.5–69.5 | 20 Oct–21 Oct | Failure and concurrency recovery suite |
| MS-060 | M2 | 68.5–71 | 21 Oct | Application preparation workspace |
| MS-075 | M3 | 68.5–71.5 | 21 Oct | Production dependency composition |
| MS-065 | M6 | 69.5–72.5 | 21 Oct–22 Oct | Two-tenant and deletion security suite |
| MS-069 | M2 | 71–73.5 | 21 Oct–22 Oct | Usage, settings and deletion controls |
| MS-083 | M1 | 72.5–75.5 | 22 Oct | Deployment and migration release assets |
| MS-076 | M6 | 72.5–75.5 | 22 Oct | API and generated client contract gate |
| MS-086 | M2 | 73.5–76 | 22 Oct | User study task and observation kit |
| MS-088 | M1 | 75.5–78 | 22 Oct–23 Oct | Operations, retention and incident runbook |
| MS-084 | M5 | 75.5–78.5 | 22 Oct–23 Oct | Isolated synthetic demo scenarios and reset |
| MS-082 | M6 | 75.5–78 | 22 Oct–23 Oct | Capacity and queue load experiment |
| MS-081 | M2 | 76–79 | 23 Oct | Main journey browser acceptance suite |
| MS-085 | M6 | 78–80.5 | 23 Oct–24 Oct | Reproducible result report generator |
| MS-087 | M2 | 80.5–83 | 24 Oct | Video storyboard and submission materials |
| MS-089 | M6 | 83–86 | 24 Oct–25 Oct | Release readiness evidence collector |

### Per-owner pull order

| Owner | P0 task order | Optional after gates |
| --- | --- | --- |
| M1 | MS-001 → MS-007 → MS-008 → MS-014 → MS-015 → MS-017 → MS-025 → MS-026 → MS-038 → MS-052 → MS-028 → MS-053 → MS-062 → MS-064 → MS-083 → MS-088 | MS-070 |
| M2 | MS-004 → MS-009 → MS-018 → MS-031 → MS-029 → MS-048 → MS-049 → MS-051 → MS-054 → MS-060 → MS-069 → MS-086 → MS-081 → MS-087 | MS-073 |
| M3 | MS-003 → MS-010 → MS-016 → MS-019 → MS-020 → MS-030 → MS-034 → MS-068 → MS-043 → MS-044 → MS-046 → MS-050 → MS-057 → MS-067 → MS-074 → MS-059 → MS-075 | None |
| M4 | MS-002 → MS-011 → MS-023 → MS-035 → MS-036 → MS-039 → MS-040 → MS-041 → MS-042 → MS-055 → MS-047 → MS-056 → MS-058 | None |
| M5 | MS-006 → MS-012 → MS-021 → MS-022 → MS-027 → MS-032 → MS-033 → MS-037 → MS-045 → MS-079 → MS-061 → MS-063 → MS-084 | MS-071, MS-072 |
| M6 | MS-005 → MS-013 → MS-024 → MS-077 → MS-078 → MS-080 → MS-066 → MS-065 → MS-076 → MS-082 → MS-085 → MS-089 | None |

### Human/operator work packages — not one-prompt coding tasks

| ID | Owners | Inputs and start condition | Deliverable and completion gate |
| --- | --- | --- | --- |
| H01 Provider access and pilot budget | M1 + M3, M5 for Tavily | 4–5 October; team accounts, actual credit terms and hosting choice | Registered team/representative, usable runtime NVIDIA/Nebius endpoint, verified capabilities/prices, search access, deployment secrets and funded global cap; no assumed pooled credits |
| H02 Source corpus, annotation and adjudication | All six; M6 custodian; M5 curator | Start with 10 development cases in week one; manifest/guidelines from MS-013/MS-024 | Target 60 opportunities, 80 profiles, 120 synthetic documents and 480 pairs; two independent labels, third adjudication, source rights metadata and grouped splits. Final gold by 21 October; if needed use design.md's declared 36/48/288 reduced benchmark. No unreviewed gold |
| H03 Actual frozen and live experiments | M6 + M3/M5, M4 reviews development errors | Harnesses ready; gold frozen; prompts/config committed; paid budget explicitly reserved | Execute required variants and ≥50 attempted nominal/burst live workflows if budget allows; exact counts, failures, cost, intervals and gates recorded. If fewer runs are affordable, report smaller sample and unverified targets; do not fabricate success |
| H04 Participant study | M2 lead, M6 analysis; others observe | Kit ready; integrated browser flow stable; synthetic tasks; participant agreement | Target eight non-team students, minimum six for a limited exploratory report; counterbalanced task order, timing/correctness/evidence-location data and actual sample size. No causal population claims |
| H05 Deploy and operating rehearsal | M1 + M3, M5 demo provisioning | Deployment assets, isolation/recovery checks, configured retention and synthetic data | Real hosted app and unique judge tenants, confirmed HTTPS/SSE/uploads, migration/rollback/restore-purge rehearsal, credits/hosting reserved through judging; do not infer deployment from a Docker build |
| H06 Demo, license and submission | M2 producer; M1 representative; all review | Measured report, hosted system and validated claims | Team-approved open-source license, public repo/setup, public ≤3-minute YouTube video, demo URL, tool feedback and verified submission. Confirm actual licenses/rights rather than assuming the plan grants them |

Allocate approximately 14–15 hours of H02 to each member. M3/M4/M5 concentrate on development/validation families; M1/M2/M6 handle independent locked-test annotation with M6 controlling access. A person cannot be both independent annotators for one case. The third adjudicator sees both rationales only after initial labels are recorded. Prompt authors do not inspect test labels before final freeze; labels can be stored separately with restricted access and only released to the final evaluator. Test-data familiarity is documented as a limitation if this separation cannot be maintained.

H03, H04 and H05 are dependencies of final human release approval even though the code-generation MS-089 can build an evidence collector before those activities finish. Missing human evidence produces BLOCKED, never a fake GO. H06 is the external delivery step; public links and submission are verified by people. The official overview/rules are linked in design.md and must be checked again before H06.

## 4. Integration milestones and scope cuts

- **Contract gate:** after MS-001–MS-008, confirm names/types/ports and tenancy model before dependent UI work. Generated client changes follow actual backend schemas.
- **Evidence slice:** after MS-026–MS-029, a synthetic PDF yields reviewable facts and a versioned profile with exact passages; missing parser capability is visible.
- **Decision slice:** after MS-043–MS-051, a development-mode run shows real stage progress, bounded retrieval, requirement/evidence details and targeted clarification.
- **Preparation slice:** after MS-056–MS-060, checklist and validated draft acceptance work without invented claims or automatic submission.
- **Isolation and lifecycle gate:** after MS-061–MS-067, source/profile/evidence changes cannot leave a stale current decision, and deletion prevents private resurrection.
- **Release gate:** code checks plus H01–H05 evidence are assessed by MS-089 tooling; H06 publishes only verified claims and working links.

If late, cut in this order: all P1 watch work; B5/all-DEEP and optional ablations; visual polish beyond accessible main flow; additional source adapters; extra opportunity breadth. Use the declared smaller benchmark only when annotation quality would otherwise suffer, with its smaller denominators and uncertainty. Do not cut tenant isolation, source/evidence trace, uncertainty handling, idempotency, deletion, acceptance review or truthful reporting. A failed positive-decision gate can require limiting supported rules/sources or retaining UNKNOWN; changing the test labels is never a valid fix.

## 5. Exact micro-sprint prompts

The developer pastes the matching block without filling in a template. File paths are relative to the implementation repository root. All prerequisite IDs, operation IDs and required outputs are already resolved. The expected input/outcome outside each prompt supports planning; the same operational details are included inside the copyable prompt. Use the common and owner system prompts from agent.md for every session.

### MS-001 — Repository, reproducible commands and configuration

**Owner:** M1. **Reviewer:** M3. **Priority:** P0. **Estimate:** 3 hours.

**Expected input:** The package contracts for R16.01, R16.02 and US-16.01, US-16.02; an otherwise unimplemented repository with these planning files.

**Blocked until:** None: the seven design files are the starting input; create the implementation scaffold.

**Expected outcome:** Create Python 3.12 FastAPI and TypeScript React/Vite workspaces, pinned lockfiles, local Postgres 17, commands and strict configuration validation. main.py delegates routers to the explicit registry contract in design.md; no production fake providers.

**Acceptance:** Clean checkout installs; make check passes scaffold checks; missing production secrets fail startup.

**Exact prompt:**

```text
Implement MS-001 — Repository, reproducible commands and configuration for BenefitBridge as M1.
Use the common system prompt and M1 role rules in agent.md. Work on branch feat/ms-001-foundation. Preserve unrelated changes.

EXPECTED INPUT
The package contracts for R16.01, R16.02 and US-16.01, US-16.02; an otherwise unimplemented repository with these planning files.
Strict prerequisites: None: the seven design files are the starting input; create the implementation scaffold.
Verify prerequisite interfaces exist before editing. A missing prerequisite is a blocker, not permission to build an incompatible stub.

READ AND RESPECT
Read requirements.md entries R16.01, R16.02, userStory.md entries US-16.01, US-16.02, this sprint in sprints.md, relevant design.md invariants, API.md common conventions/DTOs and the operations listed below. Follow agent.md style, privacy, versioning, error and ownership rules.

WRITE SCOPE
pyproject.toml; uv.lock; frontend/package.json; frontend/pnpm-lock.yaml; Makefile; .env.example; compose.yaml; backend/src/benefitbridge/config.py; backend/src/benefitbridge/main.py.
Also edit only directly corresponding tests and mechanically regenerated OpenAPI/client files when affected. Shared domain, registry or migration changes outside this scope require an explicit owner handoff; do not silently expand the task.

IMPLEMENTATION AND EXPECTED OUTCOME
Create Python 3.12 FastAPI and TypeScript React/Vite workspaces, pinned lockfiles, local Postgres 17, commands and strict configuration validation. main.py delegates routers to the explicit registry contract in design.md; no production fake providers.
Implement only this unit. Produce the scoped typed implementation and its usable interface in the development composition. Production behavior must pass the specified checks.

API CONTRACT
- No new public endpoint in this task. Preserve the documented API and expose only the internal interface required by dependent tasks.

ACCEPTANCE AND VERIFICATION
Clean checkout installs; make check passes scaffold checks; missing production secrets fail startup.
Create the baseline Makefile commands and smoke checks in this task before invoking them; no application implementation is assumed to exist yet. Use deterministic synthetic fixtures and the injected clock/provider ports where relevant. Run targeted checks for these scenarios and the relevant available lint/type/contract gates from the Makefile. Do not call paid providers or fabricate measured results. Regenerate contracts if changed, and inspect the diff for unrelated edits.

HANDOFF
Return the implemented paths, behavior mapped to the requirement IDs, exact commands and actual outcomes, schema/config/API impact, unresolved blockers and reviewer focus. Default reviewer: M3. Leave production TODO placeholders out of the delivered behavior; if a required check could not run, state the reason and keep the completion gate unverified.
```

### MS-002 — Shared domain schemas and enums

**Owner:** M4. **Reviewer:** M6. **Priority:** P0. **Estimate:** 3 hours.

**Expected input:** The package contracts for R02.01, R02.02, R05.03, R06.01, R06.02, R07.01, R08.01, R16.01 and US-02.01, US-02.02, US-05.03, US-06.01, US-06.02, US-07.01, US-08.01, US-16.01; merged, tested outputs of MS-001.

**Blocked until:** MS-001 — Repository, reproducible commands and configuration

**Expected outcome:** Implement the DTOs, tagged fact union, rule AST, status enums and pure validation in API.md. Export a minimal OpenAPI 3.1 components-only document from the Pydantic models and generate frontend types; the ports task later adds implemented routes to this same schema source.

**Acceptance:** Reject extra fields, wrong GPA tags, dangling graph nodes, ambiguous timestamps and invalid enum values.

**Exact prompt:**

```text
Implement MS-002 — Shared domain schemas and enums for BenefitBridge as M4.
Use the common system prompt and M4 role rules in agent.md. Work on branch feat/ms-002-domain. Preserve unrelated changes.

EXPECTED INPUT
The package contracts for R02.01, R02.02, R05.03, R06.01, R06.02, R07.01, R08.01, R16.01 and US-02.01, US-02.02, US-05.03, US-06.01, US-06.02, US-07.01, US-08.01, US-16.01; merged, tested outputs of MS-001.
Strict prerequisites: MS-001 — Repository, reproducible commands and configuration
Verify prerequisite interfaces exist before editing. A missing prerequisite is a blocker, not permission to build an incompatible stub.

READ AND RESPECT
Read requirements.md entries R02.01, R02.02, R05.03, R06.01, R06.02, R07.01, R08.01, R16.01, userStory.md entries US-02.01, US-02.02, US-05.03, US-06.01, US-06.02, US-07.01, US-08.01, US-16.01, this sprint in sprints.md, relevant design.md invariants, API.md common conventions/DTOs and the operations listed below. Follow agent.md style, privacy, versioning, error and ownership rules.

WRITE SCOPE
backend/src/benefitbridge/domain/; frontend/src/generated/.
Also edit only directly corresponding tests and mechanically regenerated OpenAPI/client files when affected. Shared domain, registry or migration changes outside this scope require an explicit owner handoff; do not silently expand the task.

IMPLEMENTATION AND EXPECTED OUTCOME
Implement the DTOs, tagged fact union, rule AST, status enums and pure validation in API.md. Export a minimal OpenAPI 3.1 components-only document from the Pydantic models and generate frontend types; the ports task later adds implemented routes to this same schema source.
Implement only this unit. Produce the scoped typed implementation and its usable interface in the development composition. Production behavior must pass the specified checks.

API CONTRACT
- No new public endpoint in this task. Preserve the documented API and expose only the internal interface required by dependent tasks.

ACCEPTANCE AND VERIFICATION
Reject extra fields, wrong GPA tags, dangling graph nodes, ambiguous timestamps and invalid enum values.
Use deterministic synthetic fixtures and the injected clock/provider ports where relevant. Run targeted checks for these scenarios and the relevant available lint/type/contract gates from the Makefile. Do not call paid providers or fabricate measured results. Regenerate contracts if changed, and inspect the diff for unrelated edits.

HANDOFF
Return the implemented paths, behavior mapped to the requirement IDs, exact commands and actual outcomes, schema/config/API impact, unresolved blockers and reviewer focus. Default reviewer: M6. Leave production TODO placeholders out of the delivered behavior; if a required check could not run, state the reason and keep the completion gate unverified.
```

### MS-003 — Provider and stage interfaces

**Owner:** M3. **Reviewer:** M1. **Priority:** P0. **Estimate:** 3 hours.

**Expected input:** The package contracts for R10.02, R14.02, R16.01 and US-10.02, US-14.02, US-16.01; merged, tested outputs of MS-002.

**Blocked until:** MS-002 — Shared domain schemas and enums

**Expected outcome:** Define Protocols for clock, LLM, search, fetch, storage, repositories and stage handlers. Create explicit allowlisted optional-development router loading and typed dependency injection. Production requires all P0 routers and handlers. Add deterministic OpenAPI/client generation commands.

**Acceptance:** Fake adapters implement the same protocols; a missing P0 handler prevents production readiness; OpenAPI generation is stable.

**Exact prompt:**

```text
Implement MS-003 — Provider and stage interfaces for BenefitBridge as M3.
Use the common system prompt and M3 role rules in agent.md. Work on branch feat/ms-003-ports. Preserve unrelated changes.

EXPECTED INPUT
The package contracts for R10.02, R14.02, R16.01 and US-10.02, US-14.02, US-16.01; merged, tested outputs of MS-002.
Strict prerequisites: MS-002 — Shared domain schemas and enums
Verify prerequisite interfaces exist before editing. A missing prerequisite is a blocker, not permission to build an incompatible stub.

READ AND RESPECT
Read requirements.md entries R10.02, R14.02, R16.01, userStory.md entries US-10.02, US-14.02, US-16.01, this sprint in sprints.md, relevant design.md invariants, API.md common conventions/DTOs and the operations listed below. Follow agent.md style, privacy, versioning, error and ownership rules.

WRITE SCOPE
backend/src/benefitbridge/ports.py; backend/src/benefitbridge/composition.py; backend/src/benefitbridge/api/registry.py; scripts/export_openapi.py; scripts/generate_client.sh.
Also edit only directly corresponding tests and mechanically regenerated OpenAPI/client files when affected. Shared domain, registry or migration changes outside this scope require an explicit owner handoff; do not silently expand the task.

IMPLEMENTATION AND EXPECTED OUTCOME
Define Protocols for clock, LLM, search, fetch, storage, repositories and stage handlers. Create explicit allowlisted optional-development router loading and typed dependency injection. Production requires all P0 routers and handlers. Add deterministic OpenAPI/client generation commands.
Implement only this unit. Produce the scoped typed implementation and its usable interface in the development composition. Production behavior must pass the specified checks.

API CONTRACT
- No new public endpoint in this task. Preserve the documented API and expose only the internal interface required by dependent tasks.

ACCEPTANCE AND VERIFICATION
Fake adapters implement the same protocols; a missing P0 handler prevents production readiness; OpenAPI generation is stable.
Use deterministic synthetic fixtures and the injected clock/provider ports where relevant. Run targeted checks for these scenarios and the relevant available lint/type/contract gates from the Makefile. Do not call paid providers or fabricate measured results. Regenerate contracts if changed, and inspect the diff for unrelated edits.

HANDOFF
Return the implemented paths, behavior mapped to the requirement IDs, exact commands and actual outcomes, schema/config/API impact, unresolved blockers and reviewer focus. Default reviewer: M1. Leave production TODO placeholders out of the delivered behavior; if a required check could not run, state the reason and keep the completion gate unverified.
```

### MS-004 — Web shell and state conventions

**Owner:** M2. **Reviewer:** M6. **Priority:** P0. **Estimate:** 2.5 hours.

**Expected input:** The package contracts for R12.01, R12.03, R12.04 and US-12.01, US-12.03, US-12.04; merged, tested outputs of MS-002.

**Blocked until:** MS-002 — Shared domain schemas and enums

**Expected outcome:** Build accessible navigation, route shells, API error display, request cancellation and design tokens. Use generated types and a typed mock transport only in tests/development.

**Acceptance:** Keyboard focus and unknown/error/empty states render; raw HTML is never used for model output.

**Exact prompt:**

```text
Implement MS-004 — Web shell and state conventions for BenefitBridge as M2.
Use the common system prompt and M2 role rules in agent.md. Work on branch feat/ms-004-ui-base. Preserve unrelated changes.

EXPECTED INPUT
The package contracts for R12.01, R12.03, R12.04 and US-12.01, US-12.03, US-12.04; merged, tested outputs of MS-002.
Strict prerequisites: MS-002 — Shared domain schemas and enums
Verify prerequisite interfaces exist before editing. A missing prerequisite is a blocker, not permission to build an incompatible stub.

READ AND RESPECT
Read requirements.md entries R12.01, R12.03, R12.04, userStory.md entries US-12.01, US-12.03, US-12.04, this sprint in sprints.md, relevant design.md invariants, API.md common conventions/DTOs and the operations listed below. Follow agent.md style, privacy, versioning, error and ownership rules.

WRITE SCOPE
frontend/src/app/; frontend/src/components/; frontend/src/lib/api.ts; frontend/src/styles/.
Also edit only directly corresponding tests and mechanically regenerated OpenAPI/client files when affected. Shared domain, registry or migration changes outside this scope require an explicit owner handoff; do not silently expand the task.

IMPLEMENTATION AND EXPECTED OUTCOME
Build accessible navigation, route shells, API error display, request cancellation and design tokens. Use generated types and a typed mock transport only in tests/development.
Implement only this unit. Produce the scoped typed implementation and its usable interface in the development composition. Production behavior must pass the specified checks.

API CONTRACT
- No new public endpoint in this task. Preserve the documented API and expose only the internal interface required by dependent tasks.

ACCEPTANCE AND VERIFICATION
Keyboard focus and unknown/error/empty states render; raw HTML is never used for model output.
Use deterministic synthetic fixtures and the injected clock/provider ports where relevant. Run targeted checks for these scenarios and the relevant available lint/type/contract gates from the Makefile. Do not call paid providers or fabricate measured results. Regenerate contracts if changed, and inspect the diff for unrelated edits.

HANDOFF
Return the implemented paths, behavior mapped to the requirement IDs, exact commands and actual outcomes, schema/config/API impact, unresolved blockers and reviewer focus. Default reviewer: M6. Leave production TODO placeholders out of the delivered behavior; if a required check could not run, state the reason and keep the completion gate unverified.
```

### MS-005 — CI and reusable test harness

**Owner:** M6. **Reviewer:** M4. **Priority:** P0. **Estimate:** 2.5 hours.

**Expected input:** The package contracts for R15.05, R16.01, R16.02 and US-15.05, US-16.01, US-16.02; merged, tested outputs of MS-001.

**Blocked until:** MS-001 — Repository, reproducible commands and configuration

**Expected outcome:** Wire lint, type checks, unit/integration test commands and deterministic clock/provider fixtures. Separate paid live tests from ordinary CI.

**Acceptance:** CI cannot contact paid endpoints; failed lint and mismatched generated schemas fail the gate.

**Exact prompt:**

```text
Implement MS-005 — CI and reusable test harness for BenefitBridge as M6.
Use the common system prompt and M6 role rules in agent.md. Work on branch feat/ms-005-quality. Preserve unrelated changes.

EXPECTED INPUT
The package contracts for R15.05, R16.01, R16.02 and US-15.05, US-16.01, US-16.02; merged, tested outputs of MS-001.
Strict prerequisites: MS-001 — Repository, reproducible commands and configuration
Verify prerequisite interfaces exist before editing. A missing prerequisite is a blocker, not permission to build an incompatible stub.

READ AND RESPECT
Read requirements.md entries R15.05, R16.01, R16.02, userStory.md entries US-15.05, US-16.01, US-16.02, this sprint in sprints.md, relevant design.md invariants, API.md common conventions/DTOs and the operations listed below. Follow agent.md style, privacy, versioning, error and ownership rules.

WRITE SCOPE
tests/conftest.py; tests/fakes/; .github/workflows/ci.yml; scripts/check_contract.py.
Also edit only directly corresponding tests and mechanically regenerated OpenAPI/client files when affected. Shared domain, registry or migration changes outside this scope require an explicit owner handoff; do not silently expand the task.

IMPLEMENTATION AND EXPECTED OUTCOME
Wire lint, type checks, unit/integration test commands and deterministic clock/provider fixtures. Separate paid live tests from ordinary CI.
Implement only this unit. Produce the scoped typed implementation and its usable interface in the development composition. Production behavior must pass the specified checks.

API CONTRACT
- No new public endpoint in this task. Preserve the documented API and expose only the internal interface required by dependent tasks.

ACCEPTANCE AND VERIFICATION
CI cannot contact paid endpoints; failed lint and mismatched generated schemas fail the gate.
Use deterministic synthetic fixtures and the injected clock/provider ports where relevant. Run targeted checks for these scenarios and the relevant available lint/type/contract gates from the Makefile. Do not call paid providers or fabricate measured results. Regenerate contracts if changed, and inspect the diff for unrelated edits.

HANDOFF
Return the implemented paths, behavior mapped to the requirement IDs, exact commands and actual outcomes, schema/config/API impact, unresolved blockers and reviewer focus. Default reviewer: M4. Leave production TODO placeholders out of the delivered behavior; if a required check could not run, state the reason and keep the completion gate unverified.
```

### MS-006 — Source and normalized span contract

**Owner:** M5. **Reviewer:** M4. **Priority:** P0. **Estimate:** 2.5 hours.

**Expected input:** The package contracts for R03.03, R05.01, R05.03, R06.03 and US-03.03, US-05.01, US-05.03, US-06.03; merged, tested outputs of MS-002.

**Blocked until:** MS-002 — Shared domain schemas and enums

**Expected outcome:** Define normalized Unicode text, page markers, half-open character spans, quote validation and source authority metadata. Hash normalized UTF-8 text independently of raw-file hashes.

**Acceptance:** Round-trip spans including Unicode, PDF page boundaries and invalid offsets are deterministic.

**Exact prompt:**

```text
Implement MS-006 — Source and normalized span contract for BenefitBridge as M5.
Use the common system prompt and M5 role rules in agent.md. Work on branch feat/ms-006-source-contract. Preserve unrelated changes.

EXPECTED INPUT
The package contracts for R03.03, R05.01, R05.03, R06.03 and US-03.03, US-05.01, US-05.03, US-06.03; merged, tested outputs of MS-002.
Strict prerequisites: MS-002 — Shared domain schemas and enums
Verify prerequisite interfaces exist before editing. A missing prerequisite is a blocker, not permission to build an incompatible stub.

READ AND RESPECT
Read requirements.md entries R03.03, R05.01, R05.03, R06.03, userStory.md entries US-03.03, US-05.01, US-05.03, US-06.03, this sprint in sprints.md, relevant design.md invariants, API.md common conventions/DTOs and the operations listed below. Follow agent.md style, privacy, versioning, error and ownership rules.

WRITE SCOPE
backend/src/benefitbridge/sources/contracts.py; tests/sources/test_spans.py.
Also edit only directly corresponding tests and mechanically regenerated OpenAPI/client files when affected. Shared domain, registry or migration changes outside this scope require an explicit owner handoff; do not silently expand the task.

IMPLEMENTATION AND EXPECTED OUTCOME
Define normalized Unicode text, page markers, half-open character spans, quote validation and source authority metadata. Hash normalized UTF-8 text independently of raw-file hashes.
Implement only this unit. Produce the scoped typed implementation and its usable interface in the development composition. Production behavior must pass the specified checks.

API CONTRACT
- No new public endpoint in this task. Preserve the documented API and expose only the internal interface required by dependent tasks.

ACCEPTANCE AND VERIFICATION
Round-trip spans including Unicode, PDF page boundaries and invalid offsets are deterministic.
Use deterministic synthetic fixtures and the injected clock/provider ports where relevant. Run targeted checks for these scenarios and the relevant available lint/type/contract gates from the Makefile. Do not call paid providers or fabricate measured results. Regenerate contracts if changed, and inspect the diff for unrelated edits.

HANDOFF
Return the implemented paths, behavior mapped to the requirement IDs, exact commands and actual outcomes, schema/config/API impact, unresolved blockers and reviewer focus. Default reviewer: M4. Leave production TODO placeholders out of the delivered behavior; if a required check could not run, state the reason and keep the completion gate unverified.
```

### MS-007 — Account and profile schema

**Owner:** M1. **Reviewer:** M3. **Priority:** P0. **Estimate:** 3 hours.

**Expected input:** The package contracts for R01.03, R02.01, R02.04, R13.01 and US-01.03, US-02.01, US-02.04, US-13.01; merged, tested outputs of MS-002, MS-005.

**Blocked until:** MS-002 — Shared domain schemas and enums; MS-005 — CI and reusable test harness

**Expected outcome:** Create accounts, profiles, immutable profile_versions, facts, profile_version_facts and deleted_subjects HMAC deny ledger; transaction-local owner context, RLS policies and owner-consistent foreign keys.

**Acceptance:** Migrate empty DB; cross-owner links fail; version uniqueness holds under concurrent writes.

**Exact prompt:**

```text
Implement MS-007 — Account and profile schema for BenefitBridge as M1.
Use the common system prompt and M1 role rules in agent.md. Work on branch feat/ms-007-db-profile. Preserve unrelated changes.

EXPECTED INPUT
The package contracts for R01.03, R02.01, R02.04, R13.01 and US-01.03, US-02.01, US-02.04, US-13.01; merged, tested outputs of MS-002, MS-005.
Strict prerequisites: MS-002 — Shared domain schemas and enums; MS-005 — CI and reusable test harness
Verify prerequisite interfaces exist before editing. A missing prerequisite is a blocker, not permission to build an incompatible stub.

READ AND RESPECT
Read requirements.md entries R01.03, R02.01, R02.04, R13.01, userStory.md entries US-01.03, US-02.01, US-02.04, US-13.01, this sprint in sprints.md, relevant design.md invariants, API.md common conventions/DTOs and the operations listed below. Follow agent.md style, privacy, versioning, error and ownership rules.

WRITE SCOPE
backend/migrations/versions/0001_identity.py; backend/src/benefitbridge/db/base.py; backend/src/benefitbridge/db/profiles.py.
Also edit only directly corresponding tests and mechanically regenerated OpenAPI/client files when affected. Shared domain, registry or migration changes outside this scope require an explicit owner handoff; do not silently expand the task.

IMPLEMENTATION AND EXPECTED OUTCOME
Create accounts, profiles, immutable profile_versions, facts, profile_version_facts and deleted_subjects HMAC deny ledger; transaction-local owner context, RLS policies and owner-consistent foreign keys.
Implement only this unit. Produce the scoped typed implementation and its usable interface in the development composition. Production behavior must pass the specified checks.

API CONTRACT
- No new public endpoint in this task. Preserve the documented API and expose only the internal interface required by dependent tasks.

ACCEPTANCE AND VERIFICATION
Migrate empty DB; cross-owner links fail; version uniqueness holds under concurrent writes.
Use deterministic synthetic fixtures and the injected clock/provider ports where relevant. Run targeted checks for these scenarios and the relevant available lint/type/contract gates from the Makefile. Do not call paid providers or fabricate measured results. Regenerate contracts if changed, and inspect the diff for unrelated edits.

HANDOFF
Return the implemented paths, behavior mapped to the requirement IDs, exact commands and actual outcomes, schema/config/API impact, unresolved blockers and reviewer focus. Default reviewer: M3. Leave production TODO placeholders out of the delivered behavior; if a required check could not run, state the reason and keep the completion gate unverified.
```

### MS-008 — JWT authentication and account API

**Owner:** M1. **Reviewer:** M3. **Priority:** P0. **Estimate:** 3 hours.

**Expected input:** The package contracts for R01.01, R01.02, R01.03, R01.04, R13.01 and US-01.01, US-01.02, US-01.03, US-01.04, US-13.01; merged, tested outputs of MS-007, MS-003.

**Blocked until:** MS-007 — Account and profile schema; MS-003 — Provider and stage interfaces

**Expected outcome:** Verify managed-auth JWT against issuer JWKS with bounded cache and fixed algorithms. Initialize account/profile atomically; implement consent/name/timezone update and active-account guard. Check the deleted_subjects deny ledger before bootstrap so an unexpired token cannot recreate a purged account.

**Acceptance:** Expired, wrong-issuer and tombstoned credentials fail; concurrent bootstrap creates one account.

**Exact prompt:**

```text
Implement MS-008 — JWT authentication and account API for BenefitBridge as M1.
Use the common system prompt and M1 role rules in agent.md. Work on branch feat/ms-008-auth-api. Preserve unrelated changes.

EXPECTED INPUT
The package contracts for R01.01, R01.02, R01.03, R01.04, R13.01 and US-01.01, US-01.02, US-01.03, US-01.04, US-13.01; merged, tested outputs of MS-007, MS-003.
Strict prerequisites: MS-007 — Account and profile schema; MS-003 — Provider and stage interfaces
Verify prerequisite interfaces exist before editing. A missing prerequisite is a blocker, not permission to build an incompatible stub.

READ AND RESPECT
Read requirements.md entries R01.01, R01.02, R01.03, R01.04, R13.01, userStory.md entries US-01.01, US-01.02, US-01.03, US-01.04, US-13.01, this sprint in sprints.md, relevant design.md invariants, API.md common conventions/DTOs and the operations listed below. Follow agent.md style, privacy, versioning, error and ownership rules.

WRITE SCOPE
backend/src/benefitbridge/auth.py; backend/src/benefitbridge/api/accounts.py; tests/api/test_accounts.py.
Also edit only directly corresponding tests and mechanically regenerated OpenAPI/client files when affected. Shared domain, registry or migration changes outside this scope require an explicit owner handoff; do not silently expand the task.

IMPLEMENTATION AND EXPECTED OUTCOME
Verify managed-auth JWT against issuer JWKS with bounded cache and fixed algorithms. Initialize account/profile atomically; implement consent/name/timezone update and active-account guard. Check the deleted_subjects deny ledger before bootstrap so an unexpired token cannot recreate a purged account.
Implement only this unit. Produce the scoped typed implementation and its usable interface in the development composition. Production behavior must pass the specified checks.

API CONTRACT
- get_me: GET /api/v1/me; auth=USER; success=200; idempotency=as specified; implement its exact request/response/validation in API.md.
- patch_me: PATCH /api/v1/me; auth=USER; success=200; idempotency=as specified; implement its exact request/response/validation in API.md.

ACCEPTANCE AND VERIFICATION
Expired, wrong-issuer and tombstoned credentials fail; concurrent bootstrap creates one account.
Use deterministic synthetic fixtures and the injected clock/provider ports where relevant. Run targeted checks for these scenarios and the relevant available lint/type/contract gates from the Makefile. Do not call paid providers or fabricate measured results. Regenerate contracts if changed, and inspect the diff for unrelated edits.

HANDOFF
Return the implemented paths, behavior mapped to the requirement IDs, exact commands and actual outcomes, schema/config/API impact, unresolved blockers and reviewer focus. Default reviewer: M3. Leave production TODO placeholders out of the delivered behavior; if a required check could not run, state the reason and keep the completion gate unverified.
```

### MS-009 — Managed-auth and consent screens

**Owner:** M2. **Reviewer:** M6. **Priority:** P0. **Estimate:** 2.5 hours.

**Expected input:** The package contracts for R01.01, R01.02, R12.01 and US-01.01, US-01.02, US-12.01; merged, tested outputs of MS-008, MS-004.

**Blocked until:** MS-008 — JWT authentication and account API; MS-004 — Web shell and state conventions

**Expected outcome:** Use Supabase Auth SDK for signup/login/reset and memory-only sessions; API bearer injection, explicit re-login after reload and consent screen. Configure recovery route without storing tokens in localStorage.

**Acceptance:** Session expiry returns to login; decline consent blocks processing; auth URLs do not leak tokens into logs.

**Exact prompt:**

```text
Implement MS-009 — Managed-auth and consent screens for BenefitBridge as M2.
Use the common system prompt and M2 role rules in agent.md. Work on branch feat/ms-009-auth-ui. Preserve unrelated changes.

EXPECTED INPUT
The package contracts for R01.01, R01.02, R12.01 and US-01.01, US-01.02, US-12.01; merged, tested outputs of MS-008, MS-004.
Strict prerequisites: MS-008 — JWT authentication and account API; MS-004 — Web shell and state conventions
Verify prerequisite interfaces exist before editing. A missing prerequisite is a blocker, not permission to build an incompatible stub.

READ AND RESPECT
Read requirements.md entries R01.01, R01.02, R12.01, userStory.md entries US-01.01, US-01.02, US-12.01, this sprint in sprints.md, relevant design.md invariants, API.md common conventions/DTOs and the operations listed below. Follow agent.md style, privacy, versioning, error and ownership rules.

WRITE SCOPE
frontend/src/features/auth/.
Also edit only directly corresponding tests and mechanically regenerated OpenAPI/client files when affected. Shared domain, registry or migration changes outside this scope require an explicit owner handoff; do not silently expand the task.

IMPLEMENTATION AND EXPECTED OUTCOME
Use Supabase Auth SDK for signup/login/reset and memory-only sessions; API bearer injection, explicit re-login after reload and consent screen. Configure recovery route without storing tokens in localStorage.
Implement only this unit. Produce the scoped typed implementation and its usable interface in the development composition. Production behavior must pass the specified checks.

API CONTRACT
- No new public endpoint in this task. Preserve the documented API and expose only the internal interface required by dependent tasks.

ACCEPTANCE AND VERIFICATION
Session expiry returns to login; decline consent blocks processing; auth URLs do not leak tokens into logs.
Use deterministic synthetic fixtures and the injected clock/provider ports where relevant. Run targeted checks for these scenarios and the relevant available lint/type/contract gates from the Makefile. Do not call paid providers or fabricate measured results. Regenerate contracts if changed, and inspect the diff for unrelated edits.

HANDOFF
Return the implemented paths, behavior mapped to the requirement IDs, exact commands and actual outcomes, schema/config/API impact, unresolved blockers and reviewer focus. Default reviewer: M6. Leave production TODO placeholders out of the delivered behavior; if a required check could not run, state the reason and keep the completion gate unverified.
```

### MS-010 — Model registry and capability preflight

**Owner:** M3. **Reviewer:** M1. **Priority:** P0. **Estimate:** 2.5 hours.

**Expected input:** The package contracts for R14.02 and US-14.02; merged, tested outputs of MS-003.

**Blocked until:** MS-003 — Provider and stage interfaces

**Expected outcome:** Implement FAST, REASON and optional DEEP roles from environment/registry configuration with price version, context limits and schema/tool support. Provide explicit opt-in real preflight using tiny nonprivate prompts.

**Acceptance:** Missing DEEP is allowed; missing REASON prevents inference readiness; no tests assume model names or prices.

**Exact prompt:**

```text
Implement MS-010 — Model registry and capability preflight for BenefitBridge as M3.
Use the common system prompt and M3 role rules in agent.md. Work on branch feat/ms-010-registry. Preserve unrelated changes.

EXPECTED INPUT
The package contracts for R14.02 and US-14.02; merged, tested outputs of MS-003.
Strict prerequisites: MS-003 — Provider and stage interfaces
Verify prerequisite interfaces exist before editing. A missing prerequisite is a blocker, not permission to build an incompatible stub.

READ AND RESPECT
Read requirements.md entries R14.02, userStory.md entries US-14.02, this sprint in sprints.md, relevant design.md invariants, API.md common conventions/DTOs and the operations listed below. Follow agent.md style, privacy, versioning, error and ownership rules.

WRITE SCOPE
backend/src/benefitbridge/inference/registry.py; scripts/preflight_models.py.
Also edit only directly corresponding tests and mechanically regenerated OpenAPI/client files when affected. Shared domain, registry or migration changes outside this scope require an explicit owner handoff; do not silently expand the task.

IMPLEMENTATION AND EXPECTED OUTCOME
Implement FAST, REASON and optional DEEP roles from environment/registry configuration with price version, context limits and schema/tool support. Provide explicit opt-in real preflight using tiny nonprivate prompts.
Implement only this unit. Produce the scoped typed implementation and its usable interface in the development composition. Production behavior must pass the specified checks.

API CONTRACT
- No new public endpoint in this task. Preserve the documented API and expose only the internal interface required by dependent tasks.

ACCEPTANCE AND VERIFICATION
Missing DEEP is allowed; missing REASON prevents inference readiness; no tests assume model names or prices.
Use deterministic synthetic fixtures and the injected clock/provider ports where relevant. Run targeted checks for these scenarios and the relevant available lint/type/contract gates from the Makefile. Do not call paid providers or fabricate measured results. Regenerate contracts if changed, and inspect the diff for unrelated edits.

HANDOFF
Return the implemented paths, behavior mapped to the requirement IDs, exact commands and actual outcomes, schema/config/API impact, unresolved blockers and reviewer focus. Default reviewer: M1. Leave production TODO placeholders out of the delivered behavior; if a required check could not run, state the reason and keep the completion gate unverified.
```

### MS-011 — Deterministic fact predicates

**Owner:** M4. **Reviewer:** M6. **Priority:** P0. **Estimate:** 3 hours.

**Expected input:** The package contracts for R02.02, R06.05, R07.02 and US-02.02, US-06.05, US-07.02; merged, tested outputs of MS-002, MS-005.

**Blocked until:** MS-002 — Shared domain schemas and enums; MS-005 — CI and reusable test harness

**Expected outcome:** Implement Decimal comparisons, set/category membership, compatible GPA, date interval precision and union-of-overlapping experience intervals. Unsupported conversion returns UNKNOWN.

**Acceptance:** Equality boundaries, absent scale, timezones, unknown date precision and overlapping jobs are covered.

**Exact prompt:**

```text
Implement MS-011 — Deterministic fact predicates for BenefitBridge as M4.
Use the common system prompt and M4 role rules in agent.md. Work on branch feat/ms-011-numeric. Preserve unrelated changes.

EXPECTED INPUT
The package contracts for R02.02, R06.05, R07.02 and US-02.02, US-06.05, US-07.02; merged, tested outputs of MS-002, MS-005.
Strict prerequisites: MS-002 — Shared domain schemas and enums; MS-005 — CI and reusable test harness
Verify prerequisite interfaces exist before editing. A missing prerequisite is a blocker, not permission to build an incompatible stub.

READ AND RESPECT
Read requirements.md entries R02.02, R06.05, R07.02, userStory.md entries US-02.02, US-06.05, US-07.02, this sprint in sprints.md, relevant design.md invariants, API.md common conventions/DTOs and the operations listed below. Follow agent.md style, privacy, versioning, error and ownership rules.

WRITE SCOPE
backend/src/benefitbridge/eligibility/predicates.py; tests/eligibility/test_predicates.py.
Also edit only directly corresponding tests and mechanically regenerated OpenAPI/client files when affected. Shared domain, registry or migration changes outside this scope require an explicit owner handoff; do not silently expand the task.

IMPLEMENTATION AND EXPECTED OUTCOME
Implement Decimal comparisons, set/category membership, compatible GPA, date interval precision and union-of-overlapping experience intervals. Unsupported conversion returns UNKNOWN.
Implement only this unit. Produce the scoped typed implementation and its usable interface in the development composition. Production behavior must pass the specified checks.

API CONTRACT
- No new public endpoint in this task. Preserve the documented API and expose only the internal interface required by dependent tasks.

ACCEPTANCE AND VERIFICATION
Equality boundaries, absent scale, timezones, unknown date precision and overlapping jobs are covered.
Use deterministic synthetic fixtures and the injected clock/provider ports where relevant. Run targeted checks for these scenarios and the relevant available lint/type/contract gates from the Makefile. Do not call paid providers or fabricate measured results. Regenerate contracts if changed, and inspect the diff for unrelated edits.

HANDOFF
Return the implemented paths, behavior mapped to the requirement IDs, exact commands and actual outcomes, schema/config/API impact, unresolved blockers and reviewer focus. Default reviewer: M6. Leave production TODO placeholders out of the delivered behavior; if a required check could not run, state the reason and keep the completion gate unverified.
```

### MS-012 — Bounded digital PDF parsing

**Owner:** M5. **Reviewer:** M4. **Priority:** P0. **Estimate:** 3 hours.

**Expected input:** The package contracts for R03.01, R03.03, R03.04 and US-03.01, US-03.03, US-03.04; merged, tested outputs of MS-006, MS-003, MS-005.

**Blocked until:** MS-006 — Source and normalized span contract; MS-003 — Provider and stage interfaces; MS-005 — CI and reusable test harness

**Expected outcome:** Parse in an isolated subprocess with byte/page/time/memory limits. Preserve page-normalized spans, detect unreadable text and reject encrypted or malformed PDFs.

**Acceptance:** 20 versus 21 pages, forged content types, decompression stress and empty/scanned pages produce expected typed failures.

**Exact prompt:**

```text
Implement MS-012 — Bounded digital PDF parsing for BenefitBridge as M5.
Use the common system prompt and M5 role rules in agent.md. Work on branch feat/ms-012-pdf-parser. Preserve unrelated changes.

EXPECTED INPUT
The package contracts for R03.01, R03.03, R03.04 and US-03.01, US-03.03, US-03.04; merged, tested outputs of MS-006, MS-003, MS-005.
Strict prerequisites: MS-006 — Source and normalized span contract; MS-003 — Provider and stage interfaces; MS-005 — CI and reusable test harness
Verify prerequisite interfaces exist before editing. A missing prerequisite is a blocker, not permission to build an incompatible stub.

READ AND RESPECT
Read requirements.md entries R03.01, R03.03, R03.04, userStory.md entries US-03.01, US-03.03, US-03.04, this sprint in sprints.md, relevant design.md invariants, API.md common conventions/DTOs and the operations listed below. Follow agent.md style, privacy, versioning, error and ownership rules.

WRITE SCOPE
backend/src/benefitbridge/documents/parser.py; tests/documents/test_parser.py.
Also edit only directly corresponding tests and mechanically regenerated OpenAPI/client files when affected. Shared domain, registry or migration changes outside this scope require an explicit owner handoff; do not silently expand the task.

IMPLEMENTATION AND EXPECTED OUTCOME
Parse in an isolated subprocess with byte/page/time/memory limits. Preserve page-normalized spans, detect unreadable text and reject encrypted or malformed PDFs.
Implement only this unit. Produce the scoped typed implementation and its usable interface in the development composition. Production behavior must pass the specified checks.

API CONTRACT
- No new public endpoint in this task. Preserve the documented API and expose only the internal interface required by dependent tasks.

ACCEPTANCE AND VERIFICATION
20 versus 21 pages, forged content types, decompression stress and empty/scanned pages produce expected typed failures.
Use deterministic synthetic fixtures and the injected clock/provider ports where relevant. Run targeted checks for these scenarios and the relevant available lint/type/contract gates from the Makefile. Do not call paid providers or fabricate measured results. Regenerate contracts if changed, and inspect the diff for unrelated edits.

HANDOFF
Return the implemented paths, behavior mapped to the requirement IDs, exact commands and actual outcomes, schema/config/API impact, unresolved blockers and reviewer focus. Default reviewer: M4. Leave production TODO placeholders out of the delivered behavior; if a required check could not run, state the reason and keep the completion gate unverified.
```

### MS-013 — Dataset manifest and split validator

**Owner:** M6. **Reviewer:** M4. **Priority:** P0. **Estimate:** 2.5 hours.

**Expected input:** The package contracts for R15.01 and US-15.01; merged, tested outputs of MS-002, MS-005.

**Blocked until:** MS-002 — Shared domain schemas and enums; MS-005 — CI and reusable test harness

**Expected outcome:** Define source/profile/pair/query/claim schemas and provider-family/profile-family grouped splits; license/permission metadata, clock and content hashes. Build validation only, never invent gold labels.

**Acceptance:** Duplicate hashes and leakage across splits fail; absent labels are marked pending rather than generated as truth.

**Exact prompt:**

```text
Implement MS-013 — Dataset manifest and split validator for BenefitBridge as M6.
Use the common system prompt and M6 role rules in agent.md. Work on branch feat/ms-013-bench-manifest. Preserve unrelated changes.

EXPECTED INPUT
The package contracts for R15.01 and US-15.01; merged, tested outputs of MS-002, MS-005.
Strict prerequisites: MS-002 — Shared domain schemas and enums; MS-005 — CI and reusable test harness
Verify prerequisite interfaces exist before editing. A missing prerequisite is a blocker, not permission to build an incompatible stub.

READ AND RESPECT
Read requirements.md entries R15.01, userStory.md entries US-15.01, this sprint in sprints.md, relevant design.md invariants, API.md common conventions/DTOs and the operations listed below. Follow agent.md style, privacy, versioning, error and ownership rules.

WRITE SCOPE
evaluation/schemas/; evaluation/validate_manifest.py; evaluation/README.md.
Also edit only directly corresponding tests and mechanically regenerated OpenAPI/client files when affected. Shared domain, registry or migration changes outside this scope require an explicit owner handoff; do not silently expand the task.

IMPLEMENTATION AND EXPECTED OUTCOME
Define source/profile/pair/query/claim schemas and provider-family/profile-family grouped splits; license/permission metadata, clock and content hashes. Build validation only, never invent gold labels.
Implement only this unit. Produce the scoped typed implementation and its usable interface in the development composition. Production behavior must pass the specified checks.

API CONTRACT
- No new public endpoint in this task. Preserve the documented API and expose only the internal interface required by dependent tasks.

ACCEPTANCE AND VERIFICATION
Duplicate hashes and leakage across splits fail; absent labels are marked pending rather than generated as truth.
Use deterministic synthetic fixtures and the injected clock/provider ports where relevant. Run targeted checks for these scenarios and the relevant available lint/type/contract gates from the Makefile. Do not call paid providers or fabricate measured results. Regenerate contracts if changed, and inspect the diff for unrelated edits.

HANDOFF
Return the implemented paths, behavior mapped to the requirement IDs, exact commands and actual outcomes, schema/config/API impact, unresolved blockers and reviewer focus. Default reviewer: M4. Leave production TODO placeholders out of the delivered behavior; if a required check could not run, state the reason and keep the completion gate unverified.
```

### MS-014 — Public sources and opportunity schema

**Owner:** M1. **Reviewer:** M3. **Priority:** P0. **Estimate:** 2.5 hours.

**Expected input:** The package contracts for R05.01, R05.02, R05.03, R06.03 and US-05.01, US-05.02, US-05.03, US-06.03; merged, tested outputs of MS-007, MS-006.

**Blocked until:** MS-007 — Account and profile schema; MS-006 — Source and normalized span contract

**Expected outcome:** Create provider registry, source snapshots/spans, opportunities, immutable opportunity_versions and version_sources. Enforce current-version pointers and canonical unique identities.

**Acceptance:** Distinct intakes remain distinct; snapshot hash deduplication preserves fetch records and citations.

**Exact prompt:**

```text
Implement MS-014 — Public sources and opportunity schema for BenefitBridge as M1.
Use the common system prompt and M1 role rules in agent.md. Work on branch feat/ms-014-db-sources. Preserve unrelated changes.

EXPECTED INPUT
The package contracts for R05.01, R05.02, R05.03, R06.03 and US-05.01, US-05.02, US-05.03, US-06.03; merged, tested outputs of MS-007, MS-006.
Strict prerequisites: MS-007 — Account and profile schema; MS-006 — Source and normalized span contract
Verify prerequisite interfaces exist before editing. A missing prerequisite is a blocker, not permission to build an incompatible stub.

READ AND RESPECT
Read requirements.md entries R05.01, R05.02, R05.03, R06.03, userStory.md entries US-05.01, US-05.02, US-05.03, US-06.03, this sprint in sprints.md, relevant design.md invariants, API.md common conventions/DTOs and the operations listed below. Follow agent.md style, privacy, versioning, error and ownership rules.

WRITE SCOPE
backend/migrations/versions/0002_sources.py; backend/src/benefitbridge/db/sources.py.
Also edit only directly corresponding tests and mechanically regenerated OpenAPI/client files when affected. Shared domain, registry or migration changes outside this scope require an explicit owner handoff; do not silently expand the task.

IMPLEMENTATION AND EXPECTED OUTCOME
Create provider registry, source snapshots/spans, opportunities, immutable opportunity_versions and version_sources. Enforce current-version pointers and canonical unique identities.
Implement only this unit. Produce the scoped typed implementation and its usable interface in the development composition. Production behavior must pass the specified checks.

API CONTRACT
- No new public endpoint in this task. Preserve the documented API and expose only the internal interface required by dependent tasks.

ACCEPTANCE AND VERIFICATION
Distinct intakes remain distinct; snapshot hash deduplication preserves fetch records and citations.
Use deterministic synthetic fixtures and the injected clock/provider ports where relevant. Run targeted checks for these scenarios and the relevant available lint/type/contract gates from the Makefile. Do not call paid providers or fabricate measured results. Regenerate contracts if changed, and inspect the diff for unrelated edits.

HANDOFF
Return the implemented paths, behavior mapped to the requirement IDs, exact commands and actual outcomes, schema/config/API impact, unresolved blockers and reviewer focus. Default reviewer: M3. Leave production TODO placeholders out of the delivered behavior; if a required check could not run, state the reason and keep the completion gate unverified.
```

### MS-015 — Durable runs, outbox, budget and receipt schema

**Owner:** M1. **Reviewer:** M3. **Priority:** P0. **Estimate:** 3 hours.

**Expected input:** The package contracts for R01.05, R10.01, R10.02, R10.04, R14.01 and US-01.05, US-10.01, US-10.02, US-10.04, US-14.01; merged, tested outputs of MS-014, MS-003.

**Blocked until:** MS-014 — Public sources and opportunity schema; MS-003 — Provider and stage interfaces

**Expected outcome:** Create runs, jobs, outbox, run_events, stage_outputs, idempotency_records, usage_reservations, usage_entries and deletion_receipts. Model PUBLIC versus PRIVATE maintenance scope as specified in design.md; include lease/fencing tokens, unique logical stage keys and encrypted replay bodies.

**Acceptance:** Transaction rollback leaves neither accepted run nor orphan outbox; unique keys prevent duplicate stages.

**Exact prompt:**

```text
Implement MS-015 — Durable runs, outbox, budget and receipt schema for BenefitBridge as M1.
Use the common system prompt and M1 role rules in agent.md. Work on branch feat/ms-015-db-jobs. Preserve unrelated changes.

EXPECTED INPUT
The package contracts for R01.05, R10.01, R10.02, R10.04, R14.01 and US-01.05, US-10.01, US-10.02, US-10.04, US-14.01; merged, tested outputs of MS-014, MS-003.
Strict prerequisites: MS-014 — Public sources and opportunity schema; MS-003 — Provider and stage interfaces
Verify prerequisite interfaces exist before editing. A missing prerequisite is a blocker, not permission to build an incompatible stub.

READ AND RESPECT
Read requirements.md entries R01.05, R10.01, R10.02, R10.04, R14.01, userStory.md entries US-01.05, US-10.01, US-10.02, US-10.04, US-14.01, this sprint in sprints.md, relevant design.md invariants, API.md common conventions/DTOs and the operations listed below. Follow agent.md style, privacy, versioning, error and ownership rules.

WRITE SCOPE
backend/migrations/versions/0003_jobs.py; backend/src/benefitbridge/db/jobs.py.
Also edit only directly corresponding tests and mechanically regenerated OpenAPI/client files when affected. Shared domain, registry or migration changes outside this scope require an explicit owner handoff; do not silently expand the task.

IMPLEMENTATION AND EXPECTED OUTCOME
Create runs, jobs, outbox, run_events, stage_outputs, idempotency_records, usage_reservations, usage_entries and deletion_receipts. Model PUBLIC versus PRIVATE maintenance scope as specified in design.md; include lease/fencing tokens, unique logical stage keys and encrypted replay bodies.
Implement only this unit. Produce the scoped typed implementation and its usable interface in the development composition. Production behavior must pass the specified checks.

API CONTRACT
- No new public endpoint in this task. Preserve the documented API and expose only the internal interface required by dependent tasks.

ACCEPTANCE AND VERIFICATION
Transaction rollback leaves neither accepted run nor orphan outbox; unique keys prevent duplicate stages.
Use deterministic synthetic fixtures and the injected clock/provider ports where relevant. Run targeted checks for these scenarios and the relevant available lint/type/contract gates from the Makefile. Do not call paid providers or fabricate measured results. Regenerate contracts if changed, and inspect the diff for unrelated edits.

HANDOFF
Return the implemented paths, behavior mapped to the requirement IDs, exact commands and actual outcomes, schema/config/API impact, unresolved blockers and reviewer focus. Default reviewer: M3. Leave production TODO placeholders out of the delivered behavior; if a required check could not run, state the reason and keep the completion gate unverified.
```

### MS-016 — Leased PostgreSQL job dispatcher

**Owner:** M3. **Reviewer:** M1. **Priority:** P0. **Estimate:** 3 hours.

**Expected input:** The package contracts for R10.01, R10.02, R10.03, R10.04, R10.05 and US-10.01, US-10.02, US-10.03, US-10.04, US-10.05; merged, tested outputs of MS-015, MS-003, MS-005.

**Blocked until:** MS-015 — Durable runs, outbox, budget and receipt schema; MS-003 — Provider and stage interfaces; MS-005 — CI and reusable test harness

**Expected outcome:** Implement transactional outbox dispatch and SKIP LOCKED job claims, lease heartbeat, fencing checks, safe cancellation and bounded jitter retries. Stage outputs commit idempotently before transition.

**Acceptance:** Kill worker after claim and after artifact commit; replacement worker recovers without duplicate artifacts.

**Exact prompt:**

```text
Implement MS-016 — Leased PostgreSQL job dispatcher for BenefitBridge as M3.
Use the common system prompt and M3 role rules in agent.md. Work on branch feat/ms-016-queue. Preserve unrelated changes.

EXPECTED INPUT
The package contracts for R10.01, R10.02, R10.03, R10.04, R10.05 and US-10.01, US-10.02, US-10.03, US-10.04, US-10.05; merged, tested outputs of MS-015, MS-003, MS-005.
Strict prerequisites: MS-015 — Durable runs, outbox, budget and receipt schema; MS-003 — Provider and stage interfaces; MS-005 — CI and reusable test harness
Verify prerequisite interfaces exist before editing. A missing prerequisite is a blocker, not permission to build an incompatible stub.

READ AND RESPECT
Read requirements.md entries R10.01, R10.02, R10.03, R10.04, R10.05, userStory.md entries US-10.01, US-10.02, US-10.03, US-10.04, US-10.05, this sprint in sprints.md, relevant design.md invariants, API.md common conventions/DTOs and the operations listed below. Follow agent.md style, privacy, versioning, error and ownership rules.

WRITE SCOPE
backend/src/benefitbridge/workflows/queue.py; backend/src/benefitbridge/workflows/worker.py.
Also edit only directly corresponding tests and mechanically regenerated OpenAPI/client files when affected. Shared domain, registry or migration changes outside this scope require an explicit owner handoff; do not silently expand the task.

IMPLEMENTATION AND EXPECTED OUTCOME
Implement transactional outbox dispatch and SKIP LOCKED job claims, lease heartbeat, fencing checks, safe cancellation and bounded jitter retries. Stage outputs commit idempotently before transition.
Implement only this unit. Produce the scoped typed implementation and its usable interface in the development composition. Production behavior must pass the specified checks.

API CONTRACT
- No new public endpoint in this task. Preserve the documented API and expose only the internal interface required by dependent tasks.

ACCEPTANCE AND VERIFICATION
Kill worker after claim and after artifact commit; replacement worker recovers without duplicate artifacts.
Use deterministic synthetic fixtures and the injected clock/provider ports where relevant. Run targeted checks for these scenarios and the relevant available lint/type/contract gates from the Makefile. Do not call paid providers or fabricate measured results. Regenerate contracts if changed, and inspect the diff for unrelated edits.

HANDOFF
Return the implemented paths, behavior mapped to the requirement IDs, exact commands and actual outcomes, schema/config/API impact, unresolved blockers and reviewer focus. Default reviewer: M1. Leave production TODO placeholders out of the delivered behavior; if a required check could not run, state the reason and keep the completion gate unverified.
```

### MS-017 — Versioned profile read and edit API

**Owner:** M1. **Reviewer:** M3. **Priority:** P0. **Estimate:** 3 hours.

**Expected input:** The package contracts for R02.01, R02.02, R02.04, R02.05 and US-02.01, US-02.02, US-02.04, US-02.05; merged, tested outputs of MS-008, MS-015.

**Blocked until:** MS-008 — JWT authentication and account API; MS-015 — Durable runs, outbox, budget and receipt schema

**Expected outcome:** Implement typed patch with base_profile_version_id, immutable publication and transactional invalidation outbox. Provide owner-only current/history views. Missing attributes stay absent.

**Acceptance:** Two simultaneous edits yield one success and one 409; user cannot attach another owner evidence.

**Exact prompt:**

```text
Implement MS-017 — Versioned profile read and edit API for BenefitBridge as M1.
Use the common system prompt and M1 role rules in agent.md. Work on branch feat/ms-017-profile-api. Preserve unrelated changes.

EXPECTED INPUT
The package contracts for R02.01, R02.02, R02.04, R02.05 and US-02.01, US-02.02, US-02.04, US-02.05; merged, tested outputs of MS-008, MS-015.
Strict prerequisites: MS-008 — JWT authentication and account API; MS-015 — Durable runs, outbox, budget and receipt schema
Verify prerequisite interfaces exist before editing. A missing prerequisite is a blocker, not permission to build an incompatible stub.

READ AND RESPECT
Read requirements.md entries R02.01, R02.02, R02.04, R02.05, userStory.md entries US-02.01, US-02.02, US-02.04, US-02.05, this sprint in sprints.md, relevant design.md invariants, API.md common conventions/DTOs and the operations listed below. Follow agent.md style, privacy, versioning, error and ownership rules.

WRITE SCOPE
backend/src/benefitbridge/api/profiles.py; backend/src/benefitbridge/profiles/service.py; tests/api/test_profiles.py.
Also edit only directly corresponding tests and mechanically regenerated OpenAPI/client files when affected. Shared domain, registry or migration changes outside this scope require an explicit owner handoff; do not silently expand the task.

IMPLEMENTATION AND EXPECTED OUTCOME
Implement typed patch with base_profile_version_id, immutable publication and transactional invalidation outbox. Provide owner-only current/history views. Missing attributes stay absent.
Implement only this unit. Produce the scoped typed implementation and its usable interface in the development composition. Production behavior must pass the specified checks.

API CONTRACT
- get_profile: GET /api/v1/profile; auth=USER; success=200; idempotency=as specified; implement its exact request/response/validation in API.md.
- patch_profile: PATCH /api/v1/profile; auth=USER; success=200; idempotency=required; implement its exact request/response/validation in API.md.
- list_profile_versions: GET /api/v1/profile/versions; auth=USER; success=200; idempotency=as specified; implement its exact request/response/validation in API.md.
- get_profile_version: GET /api/v1/profile/versions/{profile_version_id}; auth=USER; success=200; idempotency=as specified; implement its exact request/response/validation in API.md.

ACCEPTANCE AND VERIFICATION
Two simultaneous edits yield one success and one 409; user cannot attach another owner evidence.
Use deterministic synthetic fixtures and the injected clock/provider ports where relevant. Run targeted checks for these scenarios and the relevant available lint/type/contract gates from the Makefile. Do not call paid providers or fabricate measured results. Regenerate contracts if changed, and inspect the diff for unrelated edits.

HANDOFF
Return the implemented paths, behavior mapped to the requirement IDs, exact commands and actual outcomes, schema/config/API impact, unresolved blockers and reviewer focus. Default reviewer: M3. Leave production TODO placeholders out of the delivered behavior; if a required check could not run, state the reason and keep the completion gate unverified.
```

### MS-018 — Structured profile editor

**Owner:** M2. **Reviewer:** M6. **Priority:** P0. **Estimate:** 2.5 hours.

**Expected input:** The package contracts for R02.01, R02.02, R02.04, R02.05, R12.01 and US-02.01, US-02.02, US-02.04, US-02.05, US-12.01; merged, tested outputs of MS-017, MS-009.

**Blocked until:** MS-017 — Versioned profile read and edit API; MS-009 — Managed-auth and consent screens

**Expected outcome:** Build typed form controls, explicit unknown values, original GPA scale and conflict reload UI. Present provenance labels and source dates.

**Acceptance:** Correct GPA and unknown authorization render without accidental conversion or assumptions.

**Exact prompt:**

```text
Implement MS-018 — Structured profile editor for BenefitBridge as M2.
Use the common system prompt and M2 role rules in agent.md. Work on branch feat/ms-018-profile-ui. Preserve unrelated changes.

EXPECTED INPUT
The package contracts for R02.01, R02.02, R02.04, R02.05, R12.01 and US-02.01, US-02.02, US-02.04, US-02.05, US-12.01; merged, tested outputs of MS-017, MS-009.
Strict prerequisites: MS-017 — Versioned profile read and edit API; MS-009 — Managed-auth and consent screens
Verify prerequisite interfaces exist before editing. A missing prerequisite is a blocker, not permission to build an incompatible stub.

READ AND RESPECT
Read requirements.md entries R02.01, R02.02, R02.04, R02.05, R12.01, userStory.md entries US-02.01, US-02.02, US-02.04, US-02.05, US-12.01, this sprint in sprints.md, relevant design.md invariants, API.md common conventions/DTOs and the operations listed below. Follow agent.md style, privacy, versioning, error and ownership rules.

WRITE SCOPE
frontend/src/features/profile/.
Also edit only directly corresponding tests and mechanically regenerated OpenAPI/client files when affected. Shared domain, registry or migration changes outside this scope require an explicit owner handoff; do not silently expand the task.

IMPLEMENTATION AND EXPECTED OUTCOME
Build typed form controls, explicit unknown values, original GPA scale and conflict reload UI. Present provenance labels and source dates.
Implement only this unit. Produce the scoped typed implementation and its usable interface in the development composition. Production behavior must pass the specified checks.

API CONTRACT
- No new public endpoint in this task. Preserve the documented API and expose only the internal interface required by dependent tasks.

ACCEPTANCE AND VERIFICATION
Correct GPA and unknown authorization render without accidental conversion or assumptions.
Use deterministic synthetic fixtures and the injected clock/provider ports where relevant. Run targeted checks for these scenarios and the relevant available lint/type/contract gates from the Makefile. Do not call paid providers or fabricate measured results. Regenerate contracts if changed, and inspect the diff for unrelated edits.

HANDOFF
Return the implemented paths, behavior mapped to the requirement IDs, exact commands and actual outcomes, schema/config/API impact, unresolved blockers and reviewer focus. Default reviewer: M6. Leave production TODO placeholders out of the delivered behavior; if a required check could not run, state the reason and keep the completion gate unverified.
```

### MS-019 — Atomic cost reservations and fairness

**Owner:** M3. **Reviewer:** M1. **Priority:** P0. **Estimate:** 3 hours.

**Expected input:** The package contracts for R14.01, R14.05 and US-14.01, US-14.05; merged, tested outputs of MS-015, MS-010.

**Blocked until:** MS-015 — Durable runs, outbox, budget and receipt schema; MS-010 — Model registry and capability preflight

**Expected outcome:** Reserve maximum configured cost before each provider call, cap per-run/user/global concurrency and reconcile actual usage with integer micro-USD. Retain uncertain charges until reconciliation.

**Acceptance:** Concurrent reservations cannot exceed limits; timeout charges cannot be silently refunded.

**Exact prompt:**

```text
Implement MS-019 — Atomic cost reservations and fairness for BenefitBridge as M3.
Use the common system prompt and M3 role rules in agent.md. Work on branch feat/ms-019-budget. Preserve unrelated changes.

EXPECTED INPUT
The package contracts for R14.01, R14.05 and US-14.01, US-14.05; merged, tested outputs of MS-015, MS-010.
Strict prerequisites: MS-015 — Durable runs, outbox, budget and receipt schema; MS-010 — Model registry and capability preflight
Verify prerequisite interfaces exist before editing. A missing prerequisite is a blocker, not permission to build an incompatible stub.

READ AND RESPECT
Read requirements.md entries R14.01, R14.05, userStory.md entries US-14.01, US-14.05, this sprint in sprints.md, relevant design.md invariants, API.md common conventions/DTOs and the operations listed below. Follow agent.md style, privacy, versioning, error and ownership rules.

WRITE SCOPE
backend/src/benefitbridge/usage/budget.py; tests/usage/test_budget.py.
Also edit only directly corresponding tests and mechanically regenerated OpenAPI/client files when affected. Shared domain, registry or migration changes outside this scope require an explicit owner handoff; do not silently expand the task.

IMPLEMENTATION AND EXPECTED OUTCOME
Reserve maximum configured cost before each provider call, cap per-run/user/global concurrency and reconcile actual usage with integer micro-USD. Retain uncertain charges until reconciliation.
Implement only this unit. Produce the scoped typed implementation and its usable interface in the development composition. Production behavior must pass the specified checks.

API CONTRACT
- No new public endpoint in this task. Preserve the documented API and expose only the internal interface required by dependent tasks.

ACCEPTANCE AND VERIFICATION
Concurrent reservations cannot exceed limits; timeout charges cannot be silently refunded.
Use deterministic synthetic fixtures and the injected clock/provider ports where relevant. Run targeted checks for these scenarios and the relevant available lint/type/contract gates from the Makefile. Do not call paid providers or fabricate measured results. Regenerate contracts if changed, and inspect the diff for unrelated edits.

HANDOFF
Return the implemented paths, behavior mapped to the requirement IDs, exact commands and actual outcomes, schema/config/API impact, unresolved blockers and reviewer focus. Default reviewer: M1. Leave production TODO placeholders out of the delivered behavior; if a required check could not run, state the reason and keep the completion gate unverified.
```

### MS-020 — Nebius structured inference adapter

**Owner:** M3. **Reviewer:** M1. **Priority:** P0. **Estimate:** 3 hours.

**Expected input:** The package contracts for R07.03, R13.02, R14.02 and US-07.03, US-13.02, US-14.02; merged, tested outputs of MS-010, MS-019, MS-003.

**Blocked until:** MS-010 — Model registry and capability preflight; MS-019 — Atomic cost reservations and fairness; MS-003 — Provider and stage interfaces

**Expected outcome:** Implement schema-validated responses, token limits, redacted metadata and at most one bounded repair; route unsupported schemas safely. No chain-of-thought persistence.

**Acceptance:** Invalid JSON, truncation, 429 and missing model fail or retry within the same budget; secrets stay out of logs.

**Exact prompt:**

```text
Implement MS-020 — Nebius structured inference adapter for BenefitBridge as M3.
Use the common system prompt and M3 role rules in agent.md. Work on branch feat/ms-020-llm. Preserve unrelated changes.

EXPECTED INPUT
The package contracts for R07.03, R13.02, R14.02 and US-07.03, US-13.02, US-14.02; merged, tested outputs of MS-010, MS-019, MS-003.
Strict prerequisites: MS-010 — Model registry and capability preflight; MS-019 — Atomic cost reservations and fairness; MS-003 — Provider and stage interfaces
Verify prerequisite interfaces exist before editing. A missing prerequisite is a blocker, not permission to build an incompatible stub.

READ AND RESPECT
Read requirements.md entries R07.03, R13.02, R14.02, userStory.md entries US-07.03, US-13.02, US-14.02, this sprint in sprints.md, relevant design.md invariants, API.md common conventions/DTOs and the operations listed below. Follow agent.md style, privacy, versioning, error and ownership rules.

WRITE SCOPE
backend/src/benefitbridge/inference/nebius.py; backend/src/benefitbridge/inference/prompts/.
Also edit only directly corresponding tests and mechanically regenerated OpenAPI/client files when affected. Shared domain, registry or migration changes outside this scope require an explicit owner handoff; do not silently expand the task.

IMPLEMENTATION AND EXPECTED OUTCOME
Implement schema-validated responses, token limits, redacted metadata and at most one bounded repair; route unsupported schemas safely. No chain-of-thought persistence.
Implement only this unit. Produce the scoped typed implementation and its usable interface in the development composition. Production behavior must pass the specified checks.

API CONTRACT
- No new public endpoint in this task. Preserve the documented API and expose only the internal interface required by dependent tasks.

ACCEPTANCE AND VERIFICATION
Invalid JSON, truncation, 429 and missing model fail or retry within the same budget; secrets stay out of logs.
Use deterministic synthetic fixtures and the injected clock/provider ports where relevant. Run targeted checks for these scenarios and the relevant available lint/type/contract gates from the Makefile. Do not call paid providers or fabricate measured results. Regenerate contracts if changed, and inspect the diff for unrelated edits.

HANDOFF
Return the implemented paths, behavior mapped to the requirement IDs, exact commands and actual outcomes, schema/config/API impact, unresolved blockers and reviewer focus. Default reviewer: M1. Leave production TODO placeholders out of the delivered behavior; if a required check could not run, state the reason and keep the completion gate unverified.
```

### MS-021 — Safe fetching and untrusted-content boundary

**Owner:** M5. **Reviewer:** M4. **Priority:** P0. **Estimate:** 3 hours.

**Expected input:** The package contracts for R04.03, R13.02, R13.03, R13.05 and US-04.03, US-13.02, US-13.03, US-13.05; merged, tested outputs of MS-003, MS-006, MS-005.

**Blocked until:** MS-003 — Provider and stage interfaces; MS-006 — Source and normalized span contract; MS-005 — CI and reusable test harness

**Expected outcome:** Implement HTTPS public-network checks on DNS resolution and every redirect, pinned safe connection targets, size/time limits and content sanitization. Separate document/source text from tool instructions.

**Acceptance:** Private IPv4/IPv6, DNS rebinding, redirect-to-metadata, credential URLs and prompt injection fixtures fail safely.

**Exact prompt:**

```text
Implement MS-021 — Safe fetching and untrusted-content boundary for BenefitBridge as M5.
Use the common system prompt and M5 role rules in agent.md. Work on branch feat/ms-021-security-guard. Preserve unrelated changes.

EXPECTED INPUT
The package contracts for R04.03, R13.02, R13.03, R13.05 and US-04.03, US-13.02, US-13.03, US-13.05; merged, tested outputs of MS-003, MS-006, MS-005.
Strict prerequisites: MS-003 — Provider and stage interfaces; MS-006 — Source and normalized span contract; MS-005 — CI and reusable test harness
Verify prerequisite interfaces exist before editing. A missing prerequisite is a blocker, not permission to build an incompatible stub.

READ AND RESPECT
Read requirements.md entries R04.03, R13.02, R13.03, R13.05, userStory.md entries US-04.03, US-13.02, US-13.03, US-13.05, this sprint in sprints.md, relevant design.md invariants, API.md common conventions/DTOs and the operations listed below. Follow agent.md style, privacy, versioning, error and ownership rules.

WRITE SCOPE
backend/src/benefitbridge/security/fetch_guard.py; tests/security/test_fetch_guard.py.
Also edit only directly corresponding tests and mechanically regenerated OpenAPI/client files when affected. Shared domain, registry or migration changes outside this scope require an explicit owner handoff; do not silently expand the task.

IMPLEMENTATION AND EXPECTED OUTCOME
Implement HTTPS public-network checks on DNS resolution and every redirect, pinned safe connection targets, size/time limits and content sanitization. Separate document/source text from tool instructions.
Implement only this unit. Produce the scoped typed implementation and its usable interface in the development composition. Production behavior must pass the specified checks.

API CONTRACT
- No new public endpoint in this task. Preserve the documented API and expose only the internal interface required by dependent tasks.

ACCEPTANCE AND VERIFICATION
Private IPv4/IPv6, DNS rebinding, redirect-to-metadata, credential URLs and prompt injection fixtures fail safely.
Use deterministic synthetic fixtures and the injected clock/provider ports where relevant. Run targeted checks for these scenarios and the relevant available lint/type/contract gates from the Makefile. Do not call paid providers or fabricate measured results. Regenerate contracts if changed, and inspect the diff for unrelated edits.

HANDOFF
Return the implemented paths, behavior mapped to the requirement IDs, exact commands and actual outcomes, schema/config/API impact, unresolved blockers and reviewer focus. Default reviewer: M4. Leave production TODO placeholders out of the delivered behavior; if a required check could not run, state the reason and keep the completion gate unverified.
```

### MS-022 — Tavily discovery and source fetch adapter

**Owner:** M5. **Reviewer:** M4. **Priority:** P0. **Estimate:** 3 hours.

**Expected input:** The package contracts for R04.02, R04.03, R05.01, R13.02 and US-04.02, US-04.03, US-05.01, US-13.02; merged, tested outputs of MS-003, MS-019, MS-021.

**Blocked until:** MS-003 — Provider and stage interfaces; MS-019 — Atomic cost reservations and fairness; MS-021 — Safe fetching and untrusted-content boundary

**Expected outcome:** Implement bounded generalized-query search and full-context fetch with official domain registry validation. Snippets are discovery leads, never full policy.

**Acceptance:** PII canaries never enter queries; provider failures preserve typed reasons; redirects pass fetch guard.

**Exact prompt:**

```text
Implement MS-022 — Tavily discovery and source fetch adapter for BenefitBridge as M5.
Use the common system prompt and M5 role rules in agent.md. Work on branch feat/ms-022-search. Preserve unrelated changes.

EXPECTED INPUT
The package contracts for R04.02, R04.03, R05.01, R13.02 and US-04.02, US-04.03, US-05.01, US-13.02; merged, tested outputs of MS-003, MS-019, MS-021.
Strict prerequisites: MS-003 — Provider and stage interfaces; MS-019 — Atomic cost reservations and fairness; MS-021 — Safe fetching and untrusted-content boundary
Verify prerequisite interfaces exist before editing. A missing prerequisite is a blocker, not permission to build an incompatible stub.

READ AND RESPECT
Read requirements.md entries R04.02, R04.03, R05.01, R13.02, userStory.md entries US-04.02, US-04.03, US-05.01, US-13.02, this sprint in sprints.md, relevant design.md invariants, API.md common conventions/DTOs and the operations listed below. Follow agent.md style, privacy, versioning, error and ownership rules.

WRITE SCOPE
backend/src/benefitbridge/sources/tavily.py; backend/src/benefitbridge/sources/fetch.py.
Also edit only directly corresponding tests and mechanically regenerated OpenAPI/client files when affected. Shared domain, registry or migration changes outside this scope require an explicit owner handoff; do not silently expand the task.

IMPLEMENTATION AND EXPECTED OUTCOME
Implement bounded generalized-query search and full-context fetch with official domain registry validation. Snippets are discovery leads, never full policy.
Implement only this unit. Produce the scoped typed implementation and its usable interface in the development composition. Production behavior must pass the specified checks.

API CONTRACT
- No new public endpoint in this task. Preserve the documented API and expose only the internal interface required by dependent tasks.

ACCEPTANCE AND VERIFICATION
PII canaries never enter queries; provider failures preserve typed reasons; redirects pass fetch guard.
Use deterministic synthetic fixtures and the injected clock/provider ports where relevant. Run targeted checks for these scenarios and the relevant available lint/type/contract gates from the Makefile. Do not call paid providers or fabricate measured results. Regenerate contracts if changed, and inspect the diff for unrelated edits.

HANDOFF
Return the implemented paths, behavior mapped to the requirement IDs, exact commands and actual outcomes, schema/config/API impact, unresolved blockers and reviewer focus. Default reviewer: M4. Leave production TODO placeholders out of the delivered behavior; if a required check could not run, state the reason and keep the completion gate unverified.
```

### MS-023 — Three-valued graph evaluation

**Owner:** M4. **Reviewer:** M6. **Priority:** P0. **Estimate:** 3 hours.

**Expected input:** The package contracts for R06.02, R07.01, R07.02 and US-06.02, US-07.01, US-07.02; merged, tested outputs of MS-011, MS-002.

**Blocked until:** MS-011 — Deterministic fact predicates; MS-002 — Shared domain schemas and enums

**Expected outcome:** Implement ALL/ANY/NOT with strong Kleene logic, modality separation and decisive trace paths. Validate DAG and unsupported predicates.

**Acceptance:** Exhaustive truth tables pass; UNKNOWN cannot become TRUE through missing children.

**Exact prompt:**

```text
Implement MS-023 — Three-valued graph evaluation for BenefitBridge as M4.
Use the common system prompt and M4 role rules in agent.md. Work on branch feat/ms-023-logic. Preserve unrelated changes.

EXPECTED INPUT
The package contracts for R06.02, R07.01, R07.02 and US-06.02, US-07.01, US-07.02; merged, tested outputs of MS-011, MS-002.
Strict prerequisites: MS-011 — Deterministic fact predicates; MS-002 — Shared domain schemas and enums
Verify prerequisite interfaces exist before editing. A missing prerequisite is a blocker, not permission to build an incompatible stub.

READ AND RESPECT
Read requirements.md entries R06.02, R07.01, R07.02, userStory.md entries US-06.02, US-07.01, US-07.02, this sprint in sprints.md, relevant design.md invariants, API.md common conventions/DTOs and the operations listed below. Follow agent.md style, privacy, versioning, error and ownership rules.

WRITE SCOPE
backend/src/benefitbridge/eligibility/logic.py; tests/eligibility/test_logic.py.
Also edit only directly corresponding tests and mechanically regenerated OpenAPI/client files when affected. Shared domain, registry or migration changes outside this scope require an explicit owner handoff; do not silently expand the task.

IMPLEMENTATION AND EXPECTED OUTCOME
Implement ALL/ANY/NOT with strong Kleene logic, modality separation and decisive trace paths. Validate DAG and unsupported predicates.
Implement only this unit. Produce the scoped typed implementation and its usable interface in the development composition. Production behavior must pass the specified checks.

API CONTRACT
- No new public endpoint in this task. Preserve the documented API and expose only the internal interface required by dependent tasks.

ACCEPTANCE AND VERIFICATION
Exhaustive truth tables pass; UNKNOWN cannot become TRUE through missing children.
Use deterministic synthetic fixtures and the injected clock/provider ports where relevant. Run targeted checks for these scenarios and the relevant available lint/type/contract gates from the Makefile. Do not call paid providers or fabricate measured results. Regenerate contracts if changed, and inspect the diff for unrelated edits.

HANDOFF
Return the implemented paths, behavior mapped to the requirement IDs, exact commands and actual outcomes, schema/config/API impact, unresolved blockers and reviewer focus. Default reviewer: M6. Leave production TODO placeholders out of the delivered behavior; if a required check could not run, state the reason and keep the completion gate unverified.
```

### MS-024 — Annotation and adjudication tooling

**Owner:** M6. **Reviewer:** M4. **Priority:** P0. **Estimate:** 2.5 hours.

**Expected input:** The package contracts for R15.01 and US-15.01; merged, tested outputs of MS-013.

**Blocked until:** MS-013 — Dataset manifest and split validator

**Expected outcome:** Create two-blind-annotator templates, disagreement report, third-adjudicator workflow and immutable gold manifest finalization. This task creates tools, not labels.

**Acceptance:** Conflicting labels cannot enter frozen gold without adjudication metadata; inter-rater agreement excludes post-adjudication labels.

**Exact prompt:**

```text
Implement MS-024 — Annotation and adjudication tooling for BenefitBridge as M6.
Use the common system prompt and M6 role rules in agent.md. Work on branch feat/ms-024-bench-goldtools. Preserve unrelated changes.

EXPECTED INPUT
The package contracts for R15.01 and US-15.01; merged, tested outputs of MS-013.
Strict prerequisites: MS-013 — Dataset manifest and split validator
Verify prerequisite interfaces exist before editing. A missing prerequisite is a blocker, not permission to build an incompatible stub.

READ AND RESPECT
Read requirements.md entries R15.01, userStory.md entries US-15.01, this sprint in sprints.md, relevant design.md invariants, API.md common conventions/DTOs and the operations listed below. Follow agent.md style, privacy, versioning, error and ownership rules.

WRITE SCOPE
evaluation/annotation/; evaluation/adjudicate.py.
Also edit only directly corresponding tests and mechanically regenerated OpenAPI/client files when affected. Shared domain, registry or migration changes outside this scope require an explicit owner handoff; do not silently expand the task.

IMPLEMENTATION AND EXPECTED OUTCOME
Create two-blind-annotator templates, disagreement report, third-adjudicator workflow and immutable gold manifest finalization. This task creates tools, not labels.
Implement only this unit. Produce the scoped typed implementation and its usable interface in the development composition. Production behavior must pass the specified checks.

API CONTRACT
- No new public endpoint in this task. Preserve the documented API and expose only the internal interface required by dependent tasks.

ACCEPTANCE AND VERIFICATION
Conflicting labels cannot enter frozen gold without adjudication metadata; inter-rater agreement excludes post-adjudication labels.
Use deterministic synthetic fixtures and the injected clock/provider ports where relevant. Run targeted checks for these scenarios and the relevant available lint/type/contract gates from the Makefile. Do not call paid providers or fabricate measured results. Regenerate contracts if changed, and inspect the diff for unrelated edits.

HANDOFF
Return the implemented paths, behavior mapped to the requirement IDs, exact commands and actual outcomes, schema/config/API impact, unresolved blockers and reviewer focus. Default reviewer: M4. Leave production TODO placeholders out of the delivered behavior; if a required check could not run, state the reason and keep the completion gate unverified.
```

### MS-025 — Private evidence schema

**Owner:** M1. **Reviewer:** M3. **Priority:** P0. **Estimate:** 2.5 hours.

**Expected input:** The package contracts for R03.01, R03.02, R03.03, R13.01 and US-03.01, US-03.02, US-03.03, US-13.01; merged, tested outputs of MS-015.

**Blocked until:** MS-015 — Durable runs, outbox, budget and receipt schema

**Expected outcome:** Create documents, document_versions, evidence_spans and fact_candidates with quota reservations, tombstones and owner-composite foreign keys. Add fact evidence links to existing schema.

**Acceptance:** Cross-owner references fail at DB level; deleted evidence cannot be selected as active.

**Exact prompt:**

```text
Implement MS-025 — Private evidence schema for BenefitBridge as M1.
Use the common system prompt and M1 role rules in agent.md. Work on branch feat/ms-025-db-documents. Preserve unrelated changes.

EXPECTED INPUT
The package contracts for R03.01, R03.02, R03.03, R13.01 and US-03.01, US-03.02, US-03.03, US-13.01; merged, tested outputs of MS-015.
Strict prerequisites: MS-015 — Durable runs, outbox, budget and receipt schema
Verify prerequisite interfaces exist before editing. A missing prerequisite is a blocker, not permission to build an incompatible stub.

READ AND RESPECT
Read requirements.md entries R03.01, R03.02, R03.03, R13.01, userStory.md entries US-03.01, US-03.02, US-03.03, US-13.01, this sprint in sprints.md, relevant design.md invariants, API.md common conventions/DTOs and the operations listed below. Follow agent.md style, privacy, versioning, error and ownership rules.

WRITE SCOPE
backend/migrations/versions/0004_documents.py; backend/src/benefitbridge/db/documents.py.
Also edit only directly corresponding tests and mechanically regenerated OpenAPI/client files when affected. Shared domain, registry or migration changes outside this scope require an explicit owner handoff; do not silently expand the task.

IMPLEMENTATION AND EXPECTED OUTCOME
Create documents, document_versions, evidence_spans and fact_candidates with quota reservations, tombstones and owner-composite foreign keys. Add fact evidence links to existing schema.
Implement only this unit. Produce the scoped typed implementation and its usable interface in the development composition. Production behavior must pass the specified checks.

API CONTRACT
- No new public endpoint in this task. Preserve the documented API and expose only the internal interface required by dependent tasks.

ACCEPTANCE AND VERIFICATION
Cross-owner references fail at DB level; deleted evidence cannot be selected as active.
Use deterministic synthetic fixtures and the injected clock/provider ports where relevant. Run targeted checks for these scenarios and the relevant available lint/type/contract gates from the Makefile. Do not call paid providers or fabricate measured results. Regenerate contracts if changed, and inspect the diff for unrelated edits.

HANDOFF
Return the implemented paths, behavior mapped to the requirement IDs, exact commands and actual outcomes, schema/config/API impact, unresolved blockers and reviewer focus. Default reviewer: M3. Leave production TODO placeholders out of the delivered behavior; if a required check could not run, state the reason and keep the completion gate unverified.
```

### MS-026 — Document upload and read API

**Owner:** M1. **Reviewer:** M3. **Priority:** P0. **Estimate:** 3 hours.

**Expected input:** The package contracts for R03.01, R03.02, R03.03 and US-03.01, US-03.02, US-03.03; merged, tested outputs of MS-025, MS-008, MS-003.

**Blocked until:** MS-025 — Private evidence schema; MS-008 — JWT authentication and account API; MS-003 — Provider and stage interfaces

**Expected outcome:** Implement five-minute upload intent, authenticated streaming PUT, checksum-verified completion and queued parse run; owner-only list/detail/download. Downloads use verified short-lived private storage links.

**Acceptance:** 10 MiB cap holds during chunked upload; failed upload releases quota; completing identical upload is idempotent.

**Exact prompt:**

```text
Implement MS-026 — Document upload and read API for BenefitBridge as M1.
Use the common system prompt and M1 role rules in agent.md. Work on branch feat/ms-026-upload-api. Preserve unrelated changes.

EXPECTED INPUT
The package contracts for R03.01, R03.02, R03.03 and US-03.01, US-03.02, US-03.03; merged, tested outputs of MS-025, MS-008, MS-003.
Strict prerequisites: MS-025 — Private evidence schema; MS-008 — JWT authentication and account API; MS-003 — Provider and stage interfaces
Verify prerequisite interfaces exist before editing. A missing prerequisite is a blocker, not permission to build an incompatible stub.

READ AND RESPECT
Read requirements.md entries R03.01, R03.02, R03.03, userStory.md entries US-03.01, US-03.02, US-03.03, this sprint in sprints.md, relevant design.md invariants, API.md common conventions/DTOs and the operations listed below. Follow agent.md style, privacy, versioning, error and ownership rules.

WRITE SCOPE
backend/src/benefitbridge/api/documents.py; backend/src/benefitbridge/documents/storage.py.
Also edit only directly corresponding tests and mechanically regenerated OpenAPI/client files when affected. Shared domain, registry or migration changes outside this scope require an explicit owner handoff; do not silently expand the task.

IMPLEMENTATION AND EXPECTED OUTCOME
Implement five-minute upload intent, authenticated streaming PUT, checksum-verified completion and queued parse run; owner-only list/detail/download. Downloads use verified short-lived private storage links.
Implement only this unit. Produce the scoped typed implementation and its usable interface in the development composition. Production behavior must pass the specified checks.

API CONTRACT
- create_document_upload: POST /api/v1/documents/uploads; auth=USER; success=201; idempotency=required; implement its exact request/response/validation in API.md.
- put_document_content: PUT /api/v1/documents/{document_id}/content; auth=USER; success=200; idempotency=as specified; implement its exact request/response/validation in API.md.
- complete_document_upload: POST /api/v1/documents/{document_id}/complete; auth=USER; success=202; idempotency=required; implement its exact request/response/validation in API.md.
- list_documents: GET /api/v1/documents; auth=USER; success=200; idempotency=as specified; implement its exact request/response/validation in API.md.
- get_document: GET /api/v1/documents/{document_id}; auth=USER; success=200; idempotency=as specified; implement its exact request/response/validation in API.md.
- get_document_download: GET /api/v1/documents/{document_id}/download; auth=USER; success=200; idempotency=as specified; implement its exact request/response/validation in API.md.

ACCEPTANCE AND VERIFICATION
10 MiB cap holds during chunked upload; failed upload releases quota; completing identical upload is idempotent.
Use deterministic synthetic fixtures and the injected clock/provider ports where relevant. Run targeted checks for these scenarios and the relevant available lint/type/contract gates from the Makefile. Do not call paid providers or fabricate measured results. Regenerate contracts if changed, and inspect the diff for unrelated edits.

HANDOFF
Return the implemented paths, behavior mapped to the requirement IDs, exact commands and actual outcomes, schema/config/API impact, unresolved blockers and reviewer focus. Default reviewer: M3. Leave production TODO placeholders out of the delivered behavior; if a required check could not run, state the reason and keep the completion gate unverified.
```

### MS-027 — PDF to reviewable fact candidates

**Owner:** M5. **Reviewer:** M4. **Priority:** P0. **Estimate:** 3 hours.

**Expected input:** The package contracts for R02.03, R02.05, R03.02, R03.04 and US-02.03, US-02.05, US-03.02, US-03.04; merged, tested outputs of MS-026, MS-012, MS-020, MS-016.

**Blocked until:** MS-026 — Document upload and read API; MS-012 — Bounded digital PDF parsing; MS-020 — Nebius structured inference adapter; MS-016 — Leased PostgreSQL job dispatcher

**Expected outcome:** Persist parsed spans and schema-validated candidate facts with exact evidence links, conflicts and quality flags. Do not publish profile facts until review.

**Acceptance:** Unsupported GPA scale and conflicting documents remain reviewable; worker replay reuses the same candidate IDs.

**Exact prompt:**

```text
Implement MS-027 — PDF to reviewable fact candidates for BenefitBridge as M5.
Use the common system prompt and M5 role rules in agent.md. Work on branch feat/ms-027-doc-stage. Preserve unrelated changes.

EXPECTED INPUT
The package contracts for R02.03, R02.05, R03.02, R03.04 and US-02.03, US-02.05, US-03.02, US-03.04; merged, tested outputs of MS-026, MS-012, MS-020, MS-016.
Strict prerequisites: MS-026 — Document upload and read API; MS-012 — Bounded digital PDF parsing; MS-020 — Nebius structured inference adapter; MS-016 — Leased PostgreSQL job dispatcher
Verify prerequisite interfaces exist before editing. A missing prerequisite is a blocker, not permission to build an incompatible stub.

READ AND RESPECT
Read requirements.md entries R02.03, R02.05, R03.02, R03.04, userStory.md entries US-02.03, US-02.05, US-03.02, US-03.04, this sprint in sprints.md, relevant design.md invariants, API.md common conventions/DTOs and the operations listed below. Follow agent.md style, privacy, versioning, error and ownership rules.

WRITE SCOPE
backend/src/benefitbridge/documents/stages.py; backend/src/benefitbridge/documents/extraction.py.
Also edit only directly corresponding tests and mechanically regenerated OpenAPI/client files when affected. Shared domain, registry or migration changes outside this scope require an explicit owner handoff; do not silently expand the task.

IMPLEMENTATION AND EXPECTED OUTCOME
Persist parsed spans and schema-validated candidate facts with exact evidence links, conflicts and quality flags. Do not publish profile facts until review.
Implement only this unit. Produce the scoped typed implementation and its usable interface in the development composition. Production behavior must pass the specified checks.

API CONTRACT
- No new public endpoint in this task. Preserve the documented API and expose only the internal interface required by dependent tasks.

ACCEPTANCE AND VERIFICATION
Unsupported GPA scale and conflicting documents remain reviewable; worker replay reuses the same candidate IDs.
Use deterministic synthetic fixtures and the injected clock/provider ports where relevant. Run targeted checks for these scenarios and the relevant available lint/type/contract gates from the Makefile. Do not call paid providers or fabricate measured results. Regenerate contracts if changed, and inspect the diff for unrelated edits.

HANDOFF
Return the implemented paths, behavior mapped to the requirement IDs, exact commands and actual outcomes, schema/config/API impact, unresolved blockers and reviewer focus. Default reviewer: M4. Leave production TODO placeholders out of the delivered behavior; if a required check could not run, state the reason and keep the completion gate unverified.
```

### MS-028 — Fact candidate review API

**Owner:** M1. **Reviewer:** M3. **Priority:** P0. **Estimate:** 2.5 hours.

**Expected input:** The package contracts for R02.03, R02.04, R02.05, R03.03 and US-02.03, US-02.04, US-02.05, US-03.03; merged, tested outputs of MS-027, MS-017.

**Blocked until:** MS-027 — PDF to reviewable fact candidates; MS-017 — Versioned profile read and edit API

**Expected outcome:** Expose candidates and evidence; accept/correct/reject batch atomically with profile base version and candidate state checks. Queue invalidation on publication.

**Acceptance:** A stale review returns 409; rejected candidate cannot silently reappear as a confirmed fact.

**Exact prompt:**

```text
Implement MS-028 — Fact candidate review API for BenefitBridge as M1.
Use the common system prompt and M1 role rules in agent.md. Work on branch feat/ms-028-fact-api. Preserve unrelated changes.

EXPECTED INPUT
The package contracts for R02.03, R02.04, R02.05, R03.03 and US-02.03, US-02.04, US-02.05, US-03.03; merged, tested outputs of MS-027, MS-017.
Strict prerequisites: MS-027 — PDF to reviewable fact candidates; MS-017 — Versioned profile read and edit API
Verify prerequisite interfaces exist before editing. A missing prerequisite is a blocker, not permission to build an incompatible stub.

READ AND RESPECT
Read requirements.md entries R02.03, R02.04, R02.05, R03.03, userStory.md entries US-02.03, US-02.04, US-02.05, US-03.03, this sprint in sprints.md, relevant design.md invariants, API.md common conventions/DTOs and the operations listed below. Follow agent.md style, privacy, versioning, error and ownership rules.

WRITE SCOPE
backend/src/benefitbridge/api/facts.py; backend/src/benefitbridge/profiles/review.py.
Also edit only directly corresponding tests and mechanically regenerated OpenAPI/client files when affected. Shared domain, registry or migration changes outside this scope require an explicit owner handoff; do not silently expand the task.

IMPLEMENTATION AND EXPECTED OUTCOME
Expose candidates and evidence; accept/correct/reject batch atomically with profile base version and candidate state checks. Queue invalidation on publication.
Implement only this unit. Produce the scoped typed implementation and its usable interface in the development composition. Production behavior must pass the specified checks.

API CONTRACT
- list_fact_candidates: GET /api/v1/fact-candidates; auth=USER; success=200; idempotency=as specified; implement its exact request/response/validation in API.md.
- review_fact_candidates: POST /api/v1/fact-candidates/reviews; auth=USER; success=200; idempotency=required; implement its exact request/response/validation in API.md.
- get_evidence: GET /api/v1/evidence/{evidence_id}; auth=USER; success=200; idempotency=as specified; implement its exact request/response/validation in API.md.

ACCEPTANCE AND VERIFICATION
A stale review returns 409; rejected candidate cannot silently reappear as a confirmed fact.
Use deterministic synthetic fixtures and the injected clock/provider ports where relevant. Run targeted checks for these scenarios and the relevant available lint/type/contract gates from the Makefile. Do not call paid providers or fabricate measured results. Regenerate contracts if changed, and inspect the diff for unrelated edits.

HANDOFF
Return the implemented paths, behavior mapped to the requirement IDs, exact commands and actual outcomes, schema/config/API impact, unresolved blockers and reviewer focus. Default reviewer: M3. Leave production TODO placeholders out of the delivered behavior; if a required check could not run, state the reason and keep the completion gate unverified.
```

### MS-029 — Upload and fact review experience

**Owner:** M2. **Reviewer:** M6. **Priority:** P0. **Estimate:** 2.5 hours.

**Expected input:** The package contracts for R02.03, R03.01, R03.02, R03.03, R03.04 and US-02.03, US-03.01, US-03.02, US-03.03, US-03.04; merged, tested outputs of MS-028, MS-018.

**Blocked until:** MS-028 — Fact candidate review API; MS-018 — Structured profile editor

**Expected outcome:** Build bounded upload progress, document status, evidence passage review and atomic candidate review. Render unreadable-document alternatives.

**Acceptance:** Rejected and corrected GPA actions produce the right request; reload preserves server processing state.

**Exact prompt:**

```text
Implement MS-029 — Upload and fact review experience for BenefitBridge as M2.
Use the common system prompt and M2 role rules in agent.md. Work on branch feat/ms-029-doc-ui. Preserve unrelated changes.

EXPECTED INPUT
The package contracts for R02.03, R03.01, R03.02, R03.03, R03.04 and US-02.03, US-03.01, US-03.02, US-03.03, US-03.04; merged, tested outputs of MS-028, MS-018.
Strict prerequisites: MS-028 — Fact candidate review API; MS-018 — Structured profile editor
Verify prerequisite interfaces exist before editing. A missing prerequisite is a blocker, not permission to build an incompatible stub.

READ AND RESPECT
Read requirements.md entries R02.03, R03.01, R03.02, R03.03, R03.04, userStory.md entries US-02.03, US-03.01, US-03.02, US-03.03, US-03.04, this sprint in sprints.md, relevant design.md invariants, API.md common conventions/DTOs and the operations listed below. Follow agent.md style, privacy, versioning, error and ownership rules.

WRITE SCOPE
frontend/src/features/documents/.
Also edit only directly corresponding tests and mechanically regenerated OpenAPI/client files when affected. Shared domain, registry or migration changes outside this scope require an explicit owner handoff; do not silently expand the task.

IMPLEMENTATION AND EXPECTED OUTCOME
Build bounded upload progress, document status, evidence passage review and atomic candidate review. Render unreadable-document alternatives.
Implement only this unit. Produce the scoped typed implementation and its usable interface in the development composition. Production behavior must pass the specified checks.

API CONTRACT
- No new public endpoint in this task. Preserve the documented API and expose only the internal interface required by dependent tasks.

ACCEPTANCE AND VERIFICATION
Rejected and corrected GPA actions produce the right request; reload preserves server processing state.
Use deterministic synthetic fixtures and the injected clock/provider ports where relevant. Run targeted checks for these scenarios and the relevant available lint/type/contract gates from the Makefile. Do not call paid providers or fabricate measured results. Regenerate contracts if changed, and inspect the diff for unrelated edits.

HANDOFF
Return the implemented paths, behavior mapped to the requirement IDs, exact commands and actual outcomes, schema/config/API impact, unresolved blockers and reviewer focus. Default reviewer: M6. Leave production TODO placeholders out of the delivered behavior; if a required check could not run, state the reason and keep the completion gate unverified.
```

### MS-030 — Run control and authenticated event stream

**Owner:** M3. **Reviewer:** M1. **Priority:** P0. **Estimate:** 3 hours.

**Expected input:** The package contracts for R10.01, R10.02, R10.03, R10.05 and US-10.01, US-10.02, US-10.03, US-10.05; merged, tested outputs of MS-016, MS-008.

**Blocked until:** MS-016 — Leased PostgreSQL job dispatcher; MS-008 — JWT authentication and account API

**Expected outcome:** Implement run list/detail/cancel and fetch-based SSE replay using event sequence IDs and owner checks. Heartbeats do not create persisted events.

**Acceptance:** Reconnect after seq N receives N+1 onward; expired cursor uses 410; terminal run stream closes.

**Exact prompt:**

```text
Implement MS-030 — Run control and authenticated event stream for BenefitBridge as M3.
Use the common system prompt and M3 role rules in agent.md. Work on branch feat/ms-030-run-api. Preserve unrelated changes.

EXPECTED INPUT
The package contracts for R10.01, R10.02, R10.03, R10.05 and US-10.01, US-10.02, US-10.03, US-10.05; merged, tested outputs of MS-016, MS-008.
Strict prerequisites: MS-016 — Leased PostgreSQL job dispatcher; MS-008 — JWT authentication and account API
Verify prerequisite interfaces exist before editing. A missing prerequisite is a blocker, not permission to build an incompatible stub.

READ AND RESPECT
Read requirements.md entries R10.01, R10.02, R10.03, R10.05, userStory.md entries US-10.01, US-10.02, US-10.03, US-10.05, this sprint in sprints.md, relevant design.md invariants, API.md common conventions/DTOs and the operations listed below. Follow agent.md style, privacy, versioning, error and ownership rules.

WRITE SCOPE
backend/src/benefitbridge/api/runs.py; backend/src/benefitbridge/workflows/events.py.
Also edit only directly corresponding tests and mechanically regenerated OpenAPI/client files when affected. Shared domain, registry or migration changes outside this scope require an explicit owner handoff; do not silently expand the task.

IMPLEMENTATION AND EXPECTED OUTCOME
Implement run list/detail/cancel and fetch-based SSE replay using event sequence IDs and owner checks. Heartbeats do not create persisted events.
Implement only this unit. Produce the scoped typed implementation and its usable interface in the development composition. Production behavior must pass the specified checks.

API CONTRACT
- list_runs: GET /api/v1/runs; auth=USER; success=200; idempotency=as specified; implement its exact request/response/validation in API.md.
- get_run: GET /api/v1/runs/{run_id}; auth=USER; success=200; idempotency=as specified; implement its exact request/response/validation in API.md.
- cancel_run: POST /api/v1/runs/{run_id}/cancel; auth=USER; success=200; idempotency=required; implement its exact request/response/validation in API.md.
- get_run_events: GET /api/v1/runs/{run_id}/events; auth=USER; success=200; idempotency=as specified; implement its exact request/response/validation in API.md.

ACCEPTANCE AND VERIFICATION
Reconnect after seq N receives N+1 onward; expired cursor uses 410; terminal run stream closes.
Use deterministic synthetic fixtures and the injected clock/provider ports where relevant. Run targeted checks for these scenarios and the relevant available lint/type/contract gates from the Makefile. Do not call paid providers or fabricate measured results. Regenerate contracts if changed, and inspect the diff for unrelated edits.

HANDOFF
Return the implemented paths, behavior mapped to the requirement IDs, exact commands and actual outcomes, schema/config/API impact, unresolved blockers and reviewer focus. Default reviewer: M1. Leave production TODO placeholders out of the delivered behavior; if a required check could not run, state the reason and keep the completion gate unverified.
```

### MS-031 — Durable progress components

**Owner:** M2. **Reviewer:** M6. **Priority:** P0. **Estimate:** 2.5 hours.

**Expected input:** The package contracts for R04.05, R10.02, R10.03, R10.05, R12.03 and US-04.05, US-10.02, US-10.03, US-10.05, US-12.03; merged, tested outputs of MS-030, MS-004, MS-009.

**Blocked until:** MS-030 — Run control and authenticated event stream; MS-004 — Web shell and state conventions; MS-009 — Managed-auth and consent screens

**Expected outcome:** Use authenticated fetch streaming with AbortController, last-event cursor and poll fallback. Group progress by actual persisted stage; support cancel and reload.

**Acceptance:** Duplicate replay events are ignored; HTTP disconnect does not cancel the server run.

**Exact prompt:**

```text
Implement MS-031 — Durable progress components for BenefitBridge as M2.
Use the common system prompt and M2 role rules in agent.md. Work on branch feat/ms-031-run-ui. Preserve unrelated changes.

EXPECTED INPUT
The package contracts for R04.05, R10.02, R10.03, R10.05, R12.03 and US-04.05, US-10.02, US-10.03, US-10.05, US-12.03; merged, tested outputs of MS-030, MS-004, MS-009.
Strict prerequisites: MS-030 — Run control and authenticated event stream; MS-004 — Web shell and state conventions; MS-009 — Managed-auth and consent screens
Verify prerequisite interfaces exist before editing. A missing prerequisite is a blocker, not permission to build an incompatible stub.

READ AND RESPECT
Read requirements.md entries R04.05, R10.02, R10.03, R10.05, R12.03, userStory.md entries US-04.05, US-10.02, US-10.03, US-10.05, US-12.03, this sprint in sprints.md, relevant design.md invariants, API.md common conventions/DTOs and the operations listed below. Follow agent.md style, privacy, versioning, error and ownership rules.

WRITE SCOPE
frontend/src/features/runs/.
Also edit only directly corresponding tests and mechanically regenerated OpenAPI/client files when affected. Shared domain, registry or migration changes outside this scope require an explicit owner handoff; do not silently expand the task.

IMPLEMENTATION AND EXPECTED OUTCOME
Use authenticated fetch streaming with AbortController, last-event cursor and poll fallback. Group progress by actual persisted stage; support cancel and reload.
Implement only this unit. Produce the scoped typed implementation and its usable interface in the development composition. Production behavior must pass the specified checks.

API CONTRACT
- No new public endpoint in this task. Preserve the documented API and expose only the internal interface required by dependent tasks.

ACCEPTANCE AND VERIFICATION
Duplicate replay events are ignored; HTTP disconnect does not cancel the server run.
Use deterministic synthetic fixtures and the injected clock/provider ports where relevant. Run targeted checks for these scenarios and the relevant available lint/type/contract gates from the Makefile. Do not call paid providers or fabricate measured results. Regenerate contracts if changed, and inspect the diff for unrelated edits.

HANDOFF
Return the implemented paths, behavior mapped to the requirement IDs, exact commands and actual outcomes, schema/config/API impact, unresolved blockers and reviewer focus. Default reviewer: M6. Leave production TODO placeholders out of the delivered behavior; if a required check could not run, state the reason and keep the completion gate unverified.
```

### MS-032 — Public snapshot storage and authority resolution

**Owner:** M5. **Reviewer:** M4. **Priority:** P0. **Estimate:** 3 hours.

**Expected input:** The package contracts for R05.01, R05.03, R05.04 and US-05.01, US-05.03, US-05.04; merged, tested outputs of MS-014, MS-022, MS-006.

**Blocked until:** MS-014 — Public sources and opportunity schema; MS-022 — Tavily discovery and source fetch adapter; MS-006 — Source and normalized span contract

**Expected outcome:** Persist immutable snapshots/spans and permitted metadata, classify official links and ATS affiliation, calculate freshness without overriding policy dates.

**Acceptance:** Unknown repost stays tentative; changed content creates version; inaccessible source is unavailable.

**Exact prompt:**

```text
Implement MS-032 — Public snapshot storage and authority resolution for BenefitBridge as M5.
Use the common system prompt and M5 role rules in agent.md. Work on branch feat/ms-032-source-store. Preserve unrelated changes.

EXPECTED INPUT
The package contracts for R05.01, R05.03, R05.04 and US-05.01, US-05.03, US-05.04; merged, tested outputs of MS-014, MS-022, MS-006.
Strict prerequisites: MS-014 — Public sources and opportunity schema; MS-022 — Tavily discovery and source fetch adapter; MS-006 — Source and normalized span contract
Verify prerequisite interfaces exist before editing. A missing prerequisite is a blocker, not permission to build an incompatible stub.

READ AND RESPECT
Read requirements.md entries R05.01, R05.03, R05.04, userStory.md entries US-05.01, US-05.03, US-05.04, this sprint in sprints.md, relevant design.md invariants, API.md common conventions/DTOs and the operations listed below. Follow agent.md style, privacy, versioning, error and ownership rules.

WRITE SCOPE
backend/src/benefitbridge/sources/service.py; backend/src/benefitbridge/sources/authority.py.
Also edit only directly corresponding tests and mechanically regenerated OpenAPI/client files when affected. Shared domain, registry or migration changes outside this scope require an explicit owner handoff; do not silently expand the task.

IMPLEMENTATION AND EXPECTED OUTCOME
Persist immutable snapshots/spans and permitted metadata, classify official links and ATS affiliation, calculate freshness without overriding policy dates.
Implement only this unit. Produce the scoped typed implementation and its usable interface in the development composition. Production behavior must pass the specified checks.

API CONTRACT
- No new public endpoint in this task. Preserve the documented API and expose only the internal interface required by dependent tasks.

ACCEPTANCE AND VERIFICATION
Unknown repost stays tentative; changed content creates version; inaccessible source is unavailable.
Use deterministic synthetic fixtures and the injected clock/provider ports where relevant. Run targeted checks for these scenarios and the relevant available lint/type/contract gates from the Makefile. Do not call paid providers or fabricate measured results. Regenerate contracts if changed, and inspect the diff for unrelated edits.

HANDOFF
Return the implemented paths, behavior mapped to the requirement IDs, exact commands and actual outcomes, schema/config/API impact, unresolved blockers and reviewer focus. Default reviewer: M4. Leave production TODO placeholders out of the delivered behavior; if a required check could not run, state the reason and keep the completion gate unverified.
```

### MS-033 — Conservative opportunity canonicalization

**Owner:** M5. **Reviewer:** M4. **Priority:** P0. **Estimate:** 2.5 hours.

**Expected input:** The package contracts for R05.02 and US-05.02; merged, tested outputs of MS-032.

**Blocked until:** MS-032 — Public snapshot storage and authority resolution

**Expected outcome:** Normalize tracking parameters and match provider/external ID/intake/location; preserve uncertain matches and alias discovery URLs.

**Acceptance:** Same title different year/region stays separate; repeated canonical import is idempotent.

**Exact prompt:**

```text
Implement MS-033 — Conservative opportunity canonicalization for BenefitBridge as M5.
Use the common system prompt and M5 role rules in agent.md. Work on branch feat/ms-033-canonical. Preserve unrelated changes.

EXPECTED INPUT
The package contracts for R05.02 and US-05.02; merged, tested outputs of MS-032.
Strict prerequisites: MS-032 — Public snapshot storage and authority resolution
Verify prerequisite interfaces exist before editing. A missing prerequisite is a blocker, not permission to build an incompatible stub.

READ AND RESPECT
Read requirements.md entries R05.02, userStory.md entries US-05.02, this sprint in sprints.md, relevant design.md invariants, API.md common conventions/DTOs and the operations listed below. Follow agent.md style, privacy, versioning, error and ownership rules.

WRITE SCOPE
backend/src/benefitbridge/sources/canonical.py; tests/sources/test_canonical.py.
Also edit only directly corresponding tests and mechanically regenerated OpenAPI/client files when affected. Shared domain, registry or migration changes outside this scope require an explicit owner handoff; do not silently expand the task.

IMPLEMENTATION AND EXPECTED OUTCOME
Normalize tracking parameters and match provider/external ID/intake/location; preserve uncertain matches and alias discovery URLs.
Implement only this unit. Produce the scoped typed implementation and its usable interface in the development composition. Production behavior must pass the specified checks.

API CONTRACT
- No new public endpoint in this task. Preserve the documented API and expose only the internal interface required by dependent tasks.

ACCEPTANCE AND VERIFICATION
Same title different year/region stays separate; repeated canonical import is idempotent.
Use deterministic synthetic fixtures and the injected clock/provider ports where relevant. Run targeted checks for these scenarios and the relevant available lint/type/contract gates from the Makefile. Do not call paid providers or fabricate measured results. Regenerate contracts if changed, and inspect the diff for unrelated edits.

HANDOFF
Return the implemented paths, behavior mapped to the requirement IDs, exact commands and actual outcomes, schema/config/API impact, unresolved blockers and reviewer focus. Default reviewer: M4. Leave production TODO placeholders out of the delivered behavior; if a required check could not run, state the reason and keep the completion gate unverified.
```

### MS-034 — Bounded redacted goal planner

**Owner:** M3. **Reviewer:** M1. **Priority:** P0. **Estimate:** 2.5 hours.

**Expected input:** The package contracts for R04.01, R04.02, R13.02 and US-04.01, US-04.02, US-13.02; merged, tested outputs of MS-020, MS-022, MS-002.

**Blocked until:** MS-020 — Nebius structured inference adapter; MS-022 — Tavily discovery and source fetch adapter; MS-002 — Shared domain schemas and enums

**Expected outcome:** Validate goal/preferences, minimize search context and generate up to three initial and two follow-up intents. Enforce server caps independently of model output.

**Acceptance:** Injected goals cannot increase budgets; names/email/document text are removed from outgoing search requests.

**Exact prompt:**

```text
Implement MS-034 — Bounded redacted goal planner for BenefitBridge as M3.
Use the common system prompt and M3 role rules in agent.md. Work on branch feat/ms-034-planner. Preserve unrelated changes.

EXPECTED INPUT
The package contracts for R04.01, R04.02, R13.02 and US-04.01, US-04.02, US-13.02; merged, tested outputs of MS-020, MS-022, MS-002.
Strict prerequisites: MS-020 — Nebius structured inference adapter; MS-022 — Tavily discovery and source fetch adapter; MS-002 — Shared domain schemas and enums
Verify prerequisite interfaces exist before editing. A missing prerequisite is a blocker, not permission to build an incompatible stub.

READ AND RESPECT
Read requirements.md entries R04.01, R04.02, R13.02, userStory.md entries US-04.01, US-04.02, US-13.02, this sprint in sprints.md, relevant design.md invariants, API.md common conventions/DTOs and the operations listed below. Follow agent.md style, privacy, versioning, error and ownership rules.

WRITE SCOPE
backend/src/benefitbridge/discovery/planner.py.
Also edit only directly corresponding tests and mechanically regenerated OpenAPI/client files when affected. Shared domain, registry or migration changes outside this scope require an explicit owner handoff; do not silently expand the task.

IMPLEMENTATION AND EXPECTED OUTCOME
Validate goal/preferences, minimize search context and generate up to three initial and two follow-up intents. Enforce server caps independently of model output.
Implement only this unit. Produce the scoped typed implementation and its usable interface in the development composition. Production behavior must pass the specified checks.

API CONTRACT
- No new public endpoint in this task. Preserve the documented API and expose only the internal interface required by dependent tasks.

ACCEPTANCE AND VERIFICATION
Injected goals cannot increase budgets; names/email/document text are removed from outgoing search requests.
Use deterministic synthetic fixtures and the injected clock/provider ports where relevant. Run targeted checks for these scenarios and the relevant available lint/type/contract gates from the Makefile. Do not call paid providers or fabricate measured results. Regenerate contracts if changed, and inspect the diff for unrelated edits.

HANDOFF
Return the implemented paths, behavior mapped to the requirement IDs, exact commands and actual outcomes, schema/config/API impact, unresolved blockers and reviewer focus. Default reviewer: M1. Leave production TODO placeholders out of the delivered behavior; if a required check could not run, state the reason and keep the completion gate unverified.
```

### MS-035 — Requirement AST extraction

**Owner:** M4. **Reviewer:** M6. **Priority:** P0. **Estimate:** 3 hours.

**Expected input:** The package contracts for R06.01, R06.02, R06.03, R06.04, R06.05 and US-06.01, US-06.02, US-06.03, US-06.04, US-06.05; merged, tested outputs of MS-020, MS-006, MS-002.

**Blocked until:** MS-020 — Nebius structured inference adapter; MS-006 — Source and normalized span contract; MS-002 — Shared domain schemas and enums

**Expected outcome:** Extract bounded AST with mandatory/preferred roots, source spans, scope, dates and documentary tasks; incomplete linked policy yields explicit issues.

**Acceptance:** Mandatory versus preferred, exception wording, missing linked policy and source conflicts remain distinct.

**Exact prompt:**

```text
Implement MS-035 — Requirement AST extraction for BenefitBridge as M4.
Use the common system prompt and M4 role rules in agent.md. Work on branch feat/ms-035-requirements-parser. Preserve unrelated changes.

EXPECTED INPUT
The package contracts for R06.01, R06.02, R06.03, R06.04, R06.05 and US-06.01, US-06.02, US-06.03, US-06.04, US-06.05; merged, tested outputs of MS-020, MS-006, MS-002.
Strict prerequisites: MS-020 — Nebius structured inference adapter; MS-006 — Source and normalized span contract; MS-002 — Shared domain schemas and enums
Verify prerequisite interfaces exist before editing. A missing prerequisite is a blocker, not permission to build an incompatible stub.

READ AND RESPECT
Read requirements.md entries R06.01, R06.02, R06.03, R06.04, R06.05, userStory.md entries US-06.01, US-06.02, US-06.03, US-06.04, US-06.05, this sprint in sprints.md, relevant design.md invariants, API.md common conventions/DTOs and the operations listed below. Follow agent.md style, privacy, versioning, error and ownership rules.

WRITE SCOPE
backend/src/benefitbridge/requirements/extract.py; backend/src/benefitbridge/requirements/prompts/.
Also edit only directly corresponding tests and mechanically regenerated OpenAPI/client files when affected. Shared domain, registry or migration changes outside this scope require an explicit owner handoff; do not silently expand the task.

IMPLEMENTATION AND EXPECTED OUTCOME
Extract bounded AST with mandatory/preferred roots, source spans, scope, dates and documentary tasks; incomplete linked policy yields explicit issues.
Implement only this unit. Produce the scoped typed implementation and its usable interface in the development composition. Production behavior must pass the specified checks.

API CONTRACT
- No new public endpoint in this task. Preserve the documented API and expose only the internal interface required by dependent tasks.

ACCEPTANCE AND VERIFICATION
Mandatory versus preferred, exception wording, missing linked policy and source conflicts remain distinct.
Use deterministic synthetic fixtures and the injected clock/provider ports where relevant. Run targeted checks for these scenarios and the relevant available lint/type/contract gates from the Makefile. Do not call paid providers or fabricate measured results. Regenerate contracts if changed, and inspect the diff for unrelated edits.

HANDOFF
Return the implemented paths, behavior mapped to the requirement IDs, exact commands and actual outcomes, schema/config/API impact, unresolved blockers and reviewer focus. Default reviewer: M6. Leave production TODO placeholders out of the delivered behavior; if a required check could not run, state the reason and keep the completion gate unverified.
```

### MS-036 — Requirement publication validator

**Owner:** M4. **Reviewer:** M6. **Priority:** P0. **Estimate:** 3 hours.

**Expected input:** The package contracts for R06.02, R06.03, R06.04, R07.04 and US-06.02, US-06.03, US-06.04, US-07.04; merged, tested outputs of MS-035, MS-023.

**Blocked until:** MS-035 — Requirement AST extraction; MS-023 — Three-valued graph evaluation

**Expected outcome:** Validate AST limits, span entailment checks, quotation offsets, matching intake and completeness. Preserve unresolved ambiguity rather than inventing rules.

**Acceptance:** Bad quotes, wrong intake, missing mandatory context and unsupported predicates block COMPLETE status.

**Exact prompt:**

```text
Implement MS-036 — Requirement publication validator for BenefitBridge as M4.
Use the common system prompt and M4 role rules in agent.md. Work on branch feat/ms-036-parse-verify. Preserve unrelated changes.

EXPECTED INPUT
The package contracts for R06.02, R06.03, R06.04, R07.04 and US-06.02, US-06.03, US-06.04, US-07.04; merged, tested outputs of MS-035, MS-023.
Strict prerequisites: MS-035 — Requirement AST extraction; MS-023 — Three-valued graph evaluation
Verify prerequisite interfaces exist before editing. A missing prerequisite is a blocker, not permission to build an incompatible stub.

READ AND RESPECT
Read requirements.md entries R06.02, R06.03, R06.04, R07.04, userStory.md entries US-06.02, US-06.03, US-06.04, US-07.04, this sprint in sprints.md, relevant design.md invariants, API.md common conventions/DTOs and the operations listed below. Follow agent.md style, privacy, versioning, error and ownership rules.

WRITE SCOPE
backend/src/benefitbridge/requirements/validate.py; tests/requirements/test_validate.py.
Also edit only directly corresponding tests and mechanically regenerated OpenAPI/client files when affected. Shared domain, registry or migration changes outside this scope require an explicit owner handoff; do not silently expand the task.

IMPLEMENTATION AND EXPECTED OUTCOME
Validate AST limits, span entailment checks, quotation offsets, matching intake and completeness. Preserve unresolved ambiguity rather than inventing rules.
Implement only this unit. Produce the scoped typed implementation and its usable interface in the development composition. Production behavior must pass the specified checks.

API CONTRACT
- No new public endpoint in this task. Preserve the documented API and expose only the internal interface required by dependent tasks.

ACCEPTANCE AND VERIFICATION
Bad quotes, wrong intake, missing mandatory context and unsupported predicates block COMPLETE status.
Use deterministic synthetic fixtures and the injected clock/provider ports where relevant. Run targeted checks for these scenarios and the relevant available lint/type/contract gates from the Makefile. Do not call paid providers or fabricate measured results. Regenerate contracts if changed, and inspect the diff for unrelated edits.

HANDOFF
Return the implemented paths, behavior mapped to the requirement IDs, exact commands and actual outcomes, schema/config/API impact, unresolved blockers and reviewer focus. Default reviewer: M6. Leave production TODO placeholders out of the delivered behavior; if a required check could not run, state the reason and keep the completion gate unverified.
```

### MS-037 — Owner-scoped evidence retrieval

**Owner:** M5. **Reviewer:** M4. **Priority:** P0. **Estimate:** 2.5 hours.

**Expected input:** The package contracts for R03.03, R07.03, R13.01 and US-03.03, US-07.03, US-13.01; merged, tested outputs of MS-028, MS-006.

**Blocked until:** MS-028 — Fact candidate review API; MS-006 — Source and normalized span contract

**Expected outcome:** Retrieve exact typed attributes then at most five lexical evidence spans for unresolved semantic predicates. Preserve adjacent negation and time context.

**Acceptance:** Cross-owner spans never enter candidate set; no experience is not evidence of experience.

**Exact prompt:**

```text
Implement MS-037 — Owner-scoped evidence retrieval for BenefitBridge as M5.
Use the common system prompt and M5 role rules in agent.md. Work on branch feat/ms-037-evidence-query. Preserve unrelated changes.

EXPECTED INPUT
The package contracts for R03.03, R07.03, R13.01 and US-03.03, US-07.03, US-13.01; merged, tested outputs of MS-028, MS-006.
Strict prerequisites: MS-028 — Fact candidate review API; MS-006 — Source and normalized span contract
Verify prerequisite interfaces exist before editing. A missing prerequisite is a blocker, not permission to build an incompatible stub.

READ AND RESPECT
Read requirements.md entries R03.03, R07.03, R13.01, userStory.md entries US-03.03, US-07.03, US-13.01, this sprint in sprints.md, relevant design.md invariants, API.md common conventions/DTOs and the operations listed below. Follow agent.md style, privacy, versioning, error and ownership rules.

WRITE SCOPE
backend/src/benefitbridge/evidence/retrieve.py; tests/evidence/test_retrieve.py.
Also edit only directly corresponding tests and mechanically regenerated OpenAPI/client files when affected. Shared domain, registry or migration changes outside this scope require an explicit owner handoff; do not silently expand the task.

IMPLEMENTATION AND EXPECTED OUTCOME
Retrieve exact typed attributes then at most five lexical evidence spans for unresolved semantic predicates. Preserve adjacent negation and time context.
Implement only this unit. Produce the scoped typed implementation and its usable interface in the development composition. Production behavior must pass the specified checks.

API CONTRACT
- No new public endpoint in this task. Preserve the documented API and expose only the internal interface required by dependent tasks.

ACCEPTANCE AND VERIFICATION
Cross-owner spans never enter candidate set; no experience is not evidence of experience.
Use deterministic synthetic fixtures and the injected clock/provider ports where relevant. Run targeted checks for these scenarios and the relevant available lint/type/contract gates from the Makefile. Do not call paid providers or fabricate measured results. Regenerate contracts if changed, and inspect the diff for unrelated edits.

HANDOFF
Return the implemented paths, behavior mapped to the requirement IDs, exact commands and actual outcomes, schema/config/API impact, unresolved blockers and reviewer focus. Default reviewer: M4. Leave production TODO placeholders out of the delivered behavior; if a required check could not run, state the reason and keep the completion gate unverified.
```

### MS-038 — Requirement and evaluation persistence

**Owner:** M1. **Reviewer:** M3. **Priority:** P0. **Estimate:** 3 hours.

**Expected input:** The package contracts for R06.02, R07.01, R07.04, R08.03, R08.04 and US-06.02, US-07.01, US-07.04, US-08.03, US-08.04; merged, tested outputs of MS-025, MS-014.

**Blocked until:** MS-025 — Private evidence schema; MS-014 — Public sources and opportunity schema

**Expected outcome:** Create requirement_sets, evaluations, leaf_results, decision_dependencies, clarification_sets and answers with immutable input version references.

**Acceptance:** Source spans must belong to the referenced opportunity version; private evaluation inputs enforce owner consistency.

**Exact prompt:**

```text
Implement MS-038 — Requirement and evaluation persistence for BenefitBridge as M1.
Use the common system prompt and M1 role rules in agent.md. Work on branch feat/ms-038-db-evaluation. Preserve unrelated changes.

EXPECTED INPUT
The package contracts for R06.02, R07.01, R07.04, R08.03, R08.04 and US-06.02, US-07.01, US-07.04, US-08.03, US-08.04; merged, tested outputs of MS-025, MS-014.
Strict prerequisites: MS-025 — Private evidence schema; MS-014 — Public sources and opportunity schema
Verify prerequisite interfaces exist before editing. A missing prerequisite is a blocker, not permission to build an incompatible stub.

READ AND RESPECT
Read requirements.md entries R06.02, R07.01, R07.04, R08.03, R08.04, userStory.md entries US-06.02, US-07.01, US-07.04, US-08.03, US-08.04, this sprint in sprints.md, relevant design.md invariants, API.md common conventions/DTOs and the operations listed below. Follow agent.md style, privacy, versioning, error and ownership rules.

WRITE SCOPE
backend/migrations/versions/0005_evaluations.py; backend/src/benefitbridge/db/evaluations.py.
Also edit only directly corresponding tests and mechanically regenerated OpenAPI/client files when affected. Shared domain, registry or migration changes outside this scope require an explicit owner handoff; do not silently expand the task.

IMPLEMENTATION AND EXPECTED OUTCOME
Create requirement_sets, evaluations, leaf_results, decision_dependencies, clarification_sets and answers with immutable input version references.
Implement only this unit. Produce the scoped typed implementation and its usable interface in the development composition. Production behavior must pass the specified checks.

API CONTRACT
- No new public endpoint in this task. Preserve the documented API and expose only the internal interface required by dependent tasks.

ACCEPTANCE AND VERIFICATION
Source spans must belong to the referenced opportunity version; private evaluation inputs enforce owner consistency.
Use deterministic synthetic fixtures and the injected clock/provider ports where relevant. Run targeted checks for these scenarios and the relevant available lint/type/contract gates from the Makefile. Do not call paid providers or fabricate measured results. Regenerate contracts if changed, and inspect the diff for unrelated edits.

HANDOFF
Return the implemented paths, behavior mapped to the requirement IDs, exact commands and actual outcomes, schema/config/API impact, unresolved blockers and reviewer focus. Default reviewer: M3. Leave production TODO placeholders out of the delivered behavior; if a required check could not run, state the reason and keep the completion gate unverified.
```

### MS-039 — Bounded semantic predicate evaluator

**Owner:** M4. **Reviewer:** M6. **Priority:** P0. **Estimate:** 3 hours.

**Expected input:** The package contracts for R07.03, R07.05 and US-07.03, US-07.05; merged, tested outputs of MS-020, MS-037, MS-023.

**Blocked until:** MS-020 — Nebius structured inference adapter; MS-037 — Owner-scoped evidence retrieval; MS-023 — Three-valued graph evaluation

**Expected outcome:** Evaluate only SEMANTIC_MATCH predicates using supported spans; return TRUE/FALSE/UNKNOWN, concise justification and evidence IDs. Escalate at most once to configured DEEP if budget allows.

**Acceptance:** No evidence, mismatched time and unsupported relatedness produce UNKNOWN; no confidence score becomes truth.

**Exact prompt:**

```text
Implement MS-039 — Bounded semantic predicate evaluator for BenefitBridge as M4.
Use the common system prompt and M4 role rules in agent.md. Work on branch feat/ms-039-semantic. Preserve unrelated changes.

EXPECTED INPUT
The package contracts for R07.03, R07.05 and US-07.03, US-07.05; merged, tested outputs of MS-020, MS-037, MS-023.
Strict prerequisites: MS-020 — Nebius structured inference adapter; MS-037 — Owner-scoped evidence retrieval; MS-023 — Three-valued graph evaluation
Verify prerequisite interfaces exist before editing. A missing prerequisite is a blocker, not permission to build an incompatible stub.

READ AND RESPECT
Read requirements.md entries R07.03, R07.05, userStory.md entries US-07.03, US-07.05, this sprint in sprints.md, relevant design.md invariants, API.md common conventions/DTOs and the operations listed below. Follow agent.md style, privacy, versioning, error and ownership rules.

WRITE SCOPE
backend/src/benefitbridge/eligibility/semantic.py.
Also edit only directly corresponding tests and mechanically regenerated OpenAPI/client files when affected. Shared domain, registry or migration changes outside this scope require an explicit owner handoff; do not silently expand the task.

IMPLEMENTATION AND EXPECTED OUTCOME
Evaluate only SEMANTIC_MATCH predicates using supported spans; return TRUE/FALSE/UNKNOWN, concise justification and evidence IDs. Escalate at most once to configured DEEP if budget allows.
Implement only this unit. Produce the scoped typed implementation and its usable interface in the development composition. Production behavior must pass the specified checks.

API CONTRACT
- No new public endpoint in this task. Preserve the documented API and expose only the internal interface required by dependent tasks.

ACCEPTANCE AND VERIFICATION
No evidence, mismatched time and unsupported relatedness produce UNKNOWN; no confidence score becomes truth.
Use deterministic synthetic fixtures and the injected clock/provider ports where relevant. Run targeted checks for these scenarios and the relevant available lint/type/contract gates from the Makefile. Do not call paid providers or fabricate measured results. Regenerate contracts if changed, and inspect the diff for unrelated edits.

HANDOFF
Return the implemented paths, behavior mapped to the requirement IDs, exact commands and actual outcomes, schema/config/API impact, unresolved blockers and reviewer focus. Default reviewer: M6. Leave production TODO placeholders out of the delivered behavior; if a required check could not run, state the reason and keep the completion gate unverified.
```

### MS-040 — Eligibility aggregation and publication guards

**Owner:** M4. **Reviewer:** M6. **Priority:** P0. **Estimate:** 3 hours.

**Expected input:** The package contracts for R07.01, R07.04, R07.05, R08.01 and US-07.01, US-07.04, US-07.05, US-08.01; merged, tested outputs of MS-039, MS-036.

**Blocked until:** MS-039 — Bounded semantic predicate evaluator; MS-036 — Requirement publication validator

**Expected outcome:** Combine deterministic and semantic results; publish MET only for complete coherent sources and all required paths supported. Preserve a supported decisive NOT_MET despite unrelated unknowns.

**Acceptance:** Incomplete positive becomes UNKNOWN; authoritative decisive false remains NOT_MET; availability stays independent.

**Exact prompt:**

```text
Implement MS-040 — Eligibility aggregation and publication guards for BenefitBridge as M4.
Use the common system prompt and M4 role rules in agent.md. Work on branch feat/ms-040-decision. Preserve unrelated changes.

EXPECTED INPUT
The package contracts for R07.01, R07.04, R07.05, R08.01 and US-07.01, US-07.04, US-07.05, US-08.01; merged, tested outputs of MS-039, MS-036.
Strict prerequisites: MS-039 — Bounded semantic predicate evaluator; MS-036 — Requirement publication validator
Verify prerequisite interfaces exist before editing. A missing prerequisite is a blocker, not permission to build an incompatible stub.

READ AND RESPECT
Read requirements.md entries R07.01, R07.04, R07.05, R08.01, userStory.md entries US-07.01, US-07.04, US-07.05, US-08.01, this sprint in sprints.md, relevant design.md invariants, API.md common conventions/DTOs and the operations listed below. Follow agent.md style, privacy, versioning, error and ownership rules.

WRITE SCOPE
backend/src/benefitbridge/eligibility/decision.py.
Also edit only directly corresponding tests and mechanically regenerated OpenAPI/client files when affected. Shared domain, registry or migration changes outside this scope require an explicit owner handoff; do not silently expand the task.

IMPLEMENTATION AND EXPECTED OUTCOME
Combine deterministic and semantic results; publish MET only for complete coherent sources and all required paths supported. Preserve a supported decisive NOT_MET despite unrelated unknowns.
Implement only this unit. Produce the scoped typed implementation and its usable interface in the development composition. Production behavior must pass the specified checks.

API CONTRACT
- No new public endpoint in this task. Preserve the documented API and expose only the internal interface required by dependent tasks.

ACCEPTANCE AND VERIFICATION
Incomplete positive becomes UNKNOWN; authoritative decisive false remains NOT_MET; availability stays independent.
Use deterministic synthetic fixtures and the injected clock/provider ports where relevant. Run targeted checks for these scenarios and the relevant available lint/type/contract gates from the Makefile. Do not call paid providers or fabricate measured results. Regenerate contracts if changed, and inspect the diff for unrelated edits.

HANDOFF
Return the implemented paths, behavior mapped to the requirement IDs, exact commands and actual outcomes, schema/config/API impact, unresolved blockers and reviewer focus. Default reviewer: M6. Leave production TODO placeholders out of the delivered behavior; if a required check could not run, state the reason and keep the completion gate unverified.
```

### MS-041 — Decision and citation verification

**Owner:** M4. **Reviewer:** M6. **Priority:** P0. **Estimate:** 3 hours.

**Expected input:** The package contracts for R07.04, R07.05 and US-07.04, US-07.05; merged, tested outputs of MS-040.

**Blocked until:** MS-040 — Eligibility aggregation and publication guards

**Expected outcome:** Check referential integrity, ownership, quotes, evidence support, pinned versions and decisive paths; independently inspect risky semantic conclusions using REASON within caps.

**Acceptance:** Missing or non-entailing decisive evidence invalidates that leaf and recomputes aggregate; verifier cannot invent facts.

**Exact prompt:**

```text
Implement MS-041 — Decision and citation verification for BenefitBridge as M4.
Use the common system prompt and M4 role rules in agent.md. Work on branch feat/ms-041-verifier. Preserve unrelated changes.

EXPECTED INPUT
The package contracts for R07.04, R07.05 and US-07.04, US-07.05; merged, tested outputs of MS-040.
Strict prerequisites: MS-040 — Eligibility aggregation and publication guards
Verify prerequisite interfaces exist before editing. A missing prerequisite is a blocker, not permission to build an incompatible stub.

READ AND RESPECT
Read requirements.md entries R07.04, R07.05, userStory.md entries US-07.04, US-07.05, this sprint in sprints.md, relevant design.md invariants, API.md common conventions/DTOs and the operations listed below. Follow agent.md style, privacy, versioning, error and ownership rules.

WRITE SCOPE
backend/src/benefitbridge/eligibility/verify.py.
Also edit only directly corresponding tests and mechanically regenerated OpenAPI/client files when affected. Shared domain, registry or migration changes outside this scope require an explicit owner handoff; do not silently expand the task.

IMPLEMENTATION AND EXPECTED OUTCOME
Check referential integrity, ownership, quotes, evidence support, pinned versions and decisive paths; independently inspect risky semantic conclusions using REASON within caps.
Implement only this unit. Produce the scoped typed implementation and its usable interface in the development composition. Production behavior must pass the specified checks.

API CONTRACT
- No new public endpoint in this task. Preserve the documented API and expose only the internal interface required by dependent tasks.

ACCEPTANCE AND VERIFICATION
Missing or non-entailing decisive evidence invalidates that leaf and recomputes aggregate; verifier cannot invent facts.
Use deterministic synthetic fixtures and the injected clock/provider ports where relevant. Run targeted checks for these scenarios and the relevant available lint/type/contract gates from the Makefile. Do not call paid providers or fabricate measured results. Regenerate contracts if changed, and inspect the diff for unrelated edits.

HANDOFF
Return the implemented paths, behavior mapped to the requirement IDs, exact commands and actual outcomes, schema/config/API impact, unresolved blockers and reviewer focus. Default reviewer: M6. Leave production TODO placeholders out of the delivered behavior; if a required check could not run, state the reason and keep the completion gate unverified.
```

### MS-042 — Availability, fit, readiness and sorting

**Owner:** M4. **Reviewer:** M6. **Priority:** P0. **Estimate:** 2.5 hours.

**Expected input:** The package contracts for R05.04, R08.01, R08.02, R08.05 and US-05.04, US-08.01, US-08.02, US-08.05; merged, tested outputs of MS-040, MS-011.

**Blocked until:** MS-040 — Eligibility aggregation and publication guards; MS-011 — Deterministic fact predicates

**Expected outcome:** Implement separate availability state, explained 0–100 preference fit with coverage and deterministic group ordering; readiness uses applicable required items only.

**Acceptance:** Closed MET stays MET but sorts below actionable results; zero known required tasks yields null readiness.

**Exact prompt:**

```text
Implement MS-042 — Availability, fit, readiness and sorting for BenefitBridge as M4.
Use the common system prompt and M4 role rules in agent.md. Work on branch feat/ms-042-ranking. Preserve unrelated changes.

EXPECTED INPUT
The package contracts for R05.04, R08.01, R08.02, R08.05 and US-05.04, US-08.01, US-08.02, US-08.05; merged, tested outputs of MS-040, MS-011.
Strict prerequisites: MS-040 — Eligibility aggregation and publication guards; MS-011 — Deterministic fact predicates
Verify prerequisite interfaces exist before editing. A missing prerequisite is a blocker, not permission to build an incompatible stub.

READ AND RESPECT
Read requirements.md entries R05.04, R08.01, R08.02, R08.05, userStory.md entries US-05.04, US-08.01, US-08.02, US-08.05, this sprint in sprints.md, relevant design.md invariants, API.md common conventions/DTOs and the operations listed below. Follow agent.md style, privacy, versioning, error and ownership rules.

WRITE SCOPE
backend/src/benefitbridge/ranking.py; backend/src/benefitbridge/readiness.py.
Also edit only directly corresponding tests and mechanically regenerated OpenAPI/client files when affected. Shared domain, registry or migration changes outside this scope require an explicit owner handoff; do not silently expand the task.

IMPLEMENTATION AND EXPECTED OUTCOME
Implement separate availability state, explained 0–100 preference fit with coverage and deterministic group ordering; readiness uses applicable required items only.
Implement only this unit. Produce the scoped typed implementation and its usable interface in the development composition. Production behavior must pass the specified checks.

API CONTRACT
- No new public endpoint in this task. Preserve the documented API and expose only the internal interface required by dependent tasks.

ACCEPTANCE AND VERIFICATION
Closed MET stays MET but sorts below actionable results; zero known required tasks yields null readiness.
Use deterministic synthetic fixtures and the injected clock/provider ports where relevant. Run targeted checks for these scenarios and the relevant available lint/type/contract gates from the Makefile. Do not call paid providers or fabricate measured results. Regenerate contracts if changed, and inspect the diff for unrelated edits.

HANDOFF
Return the implemented paths, behavior mapped to the requirement IDs, exact commands and actual outcomes, schema/config/API impact, unresolved blockers and reviewer focus. Default reviewer: M6. Leave production TODO placeholders out of the delivered behavior; if a required check could not run, state the reason and keep the completion gate unverified.
```

### MS-043 — Discovery stage graph and candidate persistence

**Owner:** M3. **Reviewer:** M1. **Priority:** P0. **Estimate:** 3 hours.

**Expected input:** The package contracts for R04.02, R04.04, R04.05, R05.01, R06.04 and US-04.02, US-04.04, US-04.05, US-05.01, US-06.04; merged, tested outputs of MS-034, MS-033, MS-036, MS-038, MS-016, MS-021.

**Blocked until:** MS-034 — Bounded redacted goal planner; MS-033 — Conservative opportunity canonicalization; MS-036 — Requirement publication validator; MS-038 — Requirement and evaluation persistence; MS-016 — Leased PostgreSQL job dispatcher; MS-021 — Safe fetching and untrusted-content boundary

**Expected outcome:** Orchestrate plan, search, resolve, fetch and parse; persist candidate funnel and requirement sets; pick at most five deep-evaluation candidates and retain other candidates as unevaluated.

**Acceptance:** One failing source yields PARTIAL with successes; follow-ups cannot exceed query/page/call budgets.

**Exact prompt:**

```text
Implement MS-043 — Discovery stage graph and candidate persistence for BenefitBridge as M3.
Use the common system prompt and M3 role rules in agent.md. Work on branch feat/ms-043-discovery-stage. Preserve unrelated changes.

EXPECTED INPUT
The package contracts for R04.02, R04.04, R04.05, R05.01, R06.04 and US-04.02, US-04.04, US-04.05, US-05.01, US-06.04; merged, tested outputs of MS-034, MS-033, MS-036, MS-038, MS-016, MS-021.
Strict prerequisites: MS-034 — Bounded redacted goal planner; MS-033 — Conservative opportunity canonicalization; MS-036 — Requirement publication validator; MS-038 — Requirement and evaluation persistence; MS-016 — Leased PostgreSQL job dispatcher; MS-021 — Safe fetching and untrusted-content boundary
Verify prerequisite interfaces exist before editing. A missing prerequisite is a blocker, not permission to build an incompatible stub.

READ AND RESPECT
Read requirements.md entries R04.02, R04.04, R04.05, R05.01, R06.04, userStory.md entries US-04.02, US-04.04, US-04.05, US-05.01, US-06.04, this sprint in sprints.md, relevant design.md invariants, API.md common conventions/DTOs and the operations listed below. Follow agent.md style, privacy, versioning, error and ownership rules.

WRITE SCOPE
backend/src/benefitbridge/discovery/stages.py.
Also edit only directly corresponding tests and mechanically regenerated OpenAPI/client files when affected. Shared domain, registry or migration changes outside this scope require an explicit owner handoff; do not silently expand the task.

IMPLEMENTATION AND EXPECTED OUTCOME
Orchestrate plan, search, resolve, fetch and parse; persist candidate funnel and requirement sets; pick at most five deep-evaluation candidates and retain other candidates as unevaluated.
Implement only this unit. Produce the scoped typed implementation and its usable interface in the development composition. Production behavior must pass the specified checks.

API CONTRACT
- No new public endpoint in this task. Preserve the documented API and expose only the internal interface required by dependent tasks.

ACCEPTANCE AND VERIFICATION
One failing source yields PARTIAL with successes; follow-ups cannot exceed query/page/call budgets.
Use deterministic synthetic fixtures and the injected clock/provider ports where relevant. Run targeted checks for these scenarios and the relevant available lint/type/contract gates from the Makefile. Do not call paid providers or fabricate measured results. Regenerate contracts if changed, and inspect the diff for unrelated edits.

HANDOFF
Return the implemented paths, behavior mapped to the requirement IDs, exact commands and actual outcomes, schema/config/API impact, unresolved blockers and reviewer focus. Default reviewer: M1. Leave production TODO placeholders out of the delivered behavior; if a required check could not run, state the reason and keep the completion gate unverified.
```

### MS-044 — Evaluation workflow stage

**Owner:** M3. **Reviewer:** M1. **Priority:** P0. **Estimate:** 3 hours.

**Expected input:** The package contracts for R07.01, R07.04, R08.01, R10.04 and US-07.01, US-07.04, US-08.01, US-10.04; merged, tested outputs of MS-041, MS-042, MS-038, MS-016.

**Blocked until:** MS-041 — Decision and citation verification; MS-042 — Availability, fit, readiness and sorting; MS-038 — Requirement and evaluation persistence; MS-016 — Leased PostgreSQL job dispatcher

**Expected outcome:** Evaluate a pinned profile/opportunity pair, persist atomic leaf results and dependencies, enforce currentness at publication and emit incremental events.

**Acceptance:** Concurrent profile edits mark output historical; retries publish one evaluation; stale decisions never become current.

**Exact prompt:**

```text
Implement MS-044 — Evaluation workflow stage for BenefitBridge as M3.
Use the common system prompt and M3 role rules in agent.md. Work on branch feat/ms-044-evaluation-stage. Preserve unrelated changes.

EXPECTED INPUT
The package contracts for R07.01, R07.04, R08.01, R10.04 and US-07.01, US-07.04, US-08.01, US-10.04; merged, tested outputs of MS-041, MS-042, MS-038, MS-016.
Strict prerequisites: MS-041 — Decision and citation verification; MS-042 — Availability, fit, readiness and sorting; MS-038 — Requirement and evaluation persistence; MS-016 — Leased PostgreSQL job dispatcher
Verify prerequisite interfaces exist before editing. A missing prerequisite is a blocker, not permission to build an incompatible stub.

READ AND RESPECT
Read requirements.md entries R07.01, R07.04, R08.01, R10.04, userStory.md entries US-07.01, US-07.04, US-08.01, US-10.04, this sprint in sprints.md, relevant design.md invariants, API.md common conventions/DTOs and the operations listed below. Follow agent.md style, privacy, versioning, error and ownership rules.

WRITE SCOPE
backend/src/benefitbridge/workflows/evaluate.py.
Also edit only directly corresponding tests and mechanically regenerated OpenAPI/client files when affected. Shared domain, registry or migration changes outside this scope require an explicit owner handoff; do not silently expand the task.

IMPLEMENTATION AND EXPECTED OUTCOME
Evaluate a pinned profile/opportunity pair, persist atomic leaf results and dependencies, enforce currentness at publication and emit incremental events.
Implement only this unit. Produce the scoped typed implementation and its usable interface in the development composition. Production behavior must pass the specified checks.

API CONTRACT
- No new public endpoint in this task. Preserve the documented API and expose only the internal interface required by dependent tasks.

ACCEPTANCE AND VERIFICATION
Concurrent profile edits mark output historical; retries publish one evaluation; stale decisions never become current.
Use deterministic synthetic fixtures and the injected clock/provider ports where relevant. Run targeted checks for these scenarios and the relevant available lint/type/contract gates from the Makefile. Do not call paid providers or fabricate measured results. Regenerate contracts if changed, and inspect the diff for unrelated edits.

HANDOFF
Return the implemented paths, behavior mapped to the requirement IDs, exact commands and actual outcomes, schema/config/API impact, unresolved blockers and reviewer focus. Default reviewer: M1. Leave production TODO placeholders out of the delivered behavior; if a required check could not run, state the reason and keep the completion gate unverified.
```

### MS-045 — Public opportunity and source reads

**Owner:** M5. **Reviewer:** M4. **Priority:** P0. **Estimate:** 2.5 hours.

**Expected input:** The package contracts for R05.01, R05.03, R06.01, R06.03 and US-05.01, US-05.03, US-06.01, US-06.03; merged, tested outputs of MS-038, MS-033, MS-008.

**Blocked until:** MS-038 — Requirement and evaluation persistence; MS-033 — Conservative opportunity canonicalization; MS-008 — JWT authentication and account API

**Expected outcome:** Expose list/current/history, requirement graph and cited public source records; join only caller-owned evaluation summaries.

**Acceptance:** Changing owner cannot reveal private summaries; cursor order is stable under new records.

**Exact prompt:**

```text
Implement MS-045 — Public opportunity and source reads for BenefitBridge as M5.
Use the common system prompt and M5 role rules in agent.md. Work on branch feat/ms-045-opportunity-api. Preserve unrelated changes.

EXPECTED INPUT
The package contracts for R05.01, R05.03, R06.01, R06.03 and US-05.01, US-05.03, US-06.01, US-06.03; merged, tested outputs of MS-038, MS-033, MS-008.
Strict prerequisites: MS-038 — Requirement and evaluation persistence; MS-033 — Conservative opportunity canonicalization; MS-008 — JWT authentication and account API
Verify prerequisite interfaces exist before editing. A missing prerequisite is a blocker, not permission to build an incompatible stub.

READ AND RESPECT
Read requirements.md entries R05.01, R05.03, R06.01, R06.03, userStory.md entries US-05.01, US-05.03, US-06.01, US-06.03, this sprint in sprints.md, relevant design.md invariants, API.md common conventions/DTOs and the operations listed below. Follow agent.md style, privacy, versioning, error and ownership rules.

WRITE SCOPE
backend/src/benefitbridge/api/opportunities.py; backend/src/benefitbridge/api/sources.py.
Also edit only directly corresponding tests and mechanically regenerated OpenAPI/client files when affected. Shared domain, registry or migration changes outside this scope require an explicit owner handoff; do not silently expand the task.

IMPLEMENTATION AND EXPECTED OUTCOME
Expose list/current/history, requirement graph and cited public source records; join only caller-owned evaluation summaries.
Implement only this unit. Produce the scoped typed implementation and its usable interface in the development composition. Production behavior must pass the specified checks.

API CONTRACT
- list_opportunities: GET /api/v1/opportunities; auth=USER; success=200; idempotency=as specified; implement its exact request/response/validation in API.md.
- get_opportunity: GET /api/v1/opportunities/{opportunity_id}; auth=USER; success=200; idempotency=as specified; implement its exact request/response/validation in API.md.
- get_opportunity_version: GET /api/v1/opportunities/{opportunity_id}/versions/{opportunity_version_id}; auth=USER; success=200; idempotency=as specified; implement its exact request/response/validation in API.md.
- get_requirements: GET /api/v1/requirement-sets/{requirement_set_id}; auth=USER; success=200; idempotency=as specified; implement its exact request/response/validation in API.md.
- get_source: GET /api/v1/sources/{source_snapshot_id}; auth=USER; success=200; idempotency=as specified; implement its exact request/response/validation in API.md.

ACCEPTANCE AND VERIFICATION
Changing owner cannot reveal private summaries; cursor order is stable under new records.
Use deterministic synthetic fixtures and the injected clock/provider ports where relevant. Run targeted checks for these scenarios and the relevant available lint/type/contract gates from the Makefile. Do not call paid providers or fabricate measured results. Regenerate contracts if changed, and inspect the diff for unrelated edits.

HANDOFF
Return the implemented paths, behavior mapped to the requirement IDs, exact commands and actual outcomes, schema/config/API impact, unresolved blockers and reviewer focus. Default reviewer: M4. Leave production TODO placeholders out of the delivered behavior; if a required check could not run, state the reason and keep the completion gate unverified.
```

### MS-046 — Discovery and URL-import commands

**Owner:** M3. **Reviewer:** M1. **Priority:** P0. **Estimate:** 2.5 hours.

**Expected input:** The package contracts for R04.01, R04.02, R04.03, R10.01 and US-04.01, US-04.02, US-04.03, US-10.01; merged, tested outputs of MS-043, MS-044, MS-030, MS-017.

**Blocked until:** MS-043 — Discovery stage graph and candidate persistence; MS-044 — Evaluation workflow stage; MS-030 — Run control and authenticated event stream; MS-017 — Versioned profile read and edit API

**Expected outcome:** Implement idempotent run creation with pinned profile, generalized goal, URL validation and transactional outbox. Share command validation with worker.

**Acceptance:** Duplicate keys replay receipt; changed payload returns 409; missing consent returns 403.

**Exact prompt:**

```text
Implement MS-046 — Discovery and URL-import commands for BenefitBridge as M3.
Use the common system prompt and M3 role rules in agent.md. Work on branch feat/ms-046-discovery-api. Preserve unrelated changes.

EXPECTED INPUT
The package contracts for R04.01, R04.02, R04.03, R10.01 and US-04.01, US-04.02, US-04.03, US-10.01; merged, tested outputs of MS-043, MS-044, MS-030, MS-017.
Strict prerequisites: MS-043 — Discovery stage graph and candidate persistence; MS-044 — Evaluation workflow stage; MS-030 — Run control and authenticated event stream; MS-017 — Versioned profile read and edit API
Verify prerequisite interfaces exist before editing. A missing prerequisite is a blocker, not permission to build an incompatible stub.

READ AND RESPECT
Read requirements.md entries R04.01, R04.02, R04.03, R10.01, userStory.md entries US-04.01, US-04.02, US-04.03, US-10.01, this sprint in sprints.md, relevant design.md invariants, API.md common conventions/DTOs and the operations listed below. Follow agent.md style, privacy, versioning, error and ownership rules.

WRITE SCOPE
backend/src/benefitbridge/api/discovery.py.
Also edit only directly corresponding tests and mechanically regenerated OpenAPI/client files when affected. Shared domain, registry or migration changes outside this scope require an explicit owner handoff; do not silently expand the task.

IMPLEMENTATION AND EXPECTED OUTCOME
Implement idempotent run creation with pinned profile, generalized goal, URL validation and transactional outbox. Share command validation with worker.
Implement only this unit. Produce the scoped typed implementation and its usable interface in the development composition. Production behavior must pass the specified checks.

API CONTRACT
- start_discovery: POST /api/v1/discovery-runs; auth=USER; success=202; idempotency=required; implement its exact request/response/validation in API.md.
- import_opportunity: POST /api/v1/opportunity-imports; auth=USER; success=202; idempotency=required; implement its exact request/response/validation in API.md.

ACCEPTANCE AND VERIFICATION
Duplicate keys replay receipt; changed payload returns 409; missing consent returns 403.
Use deterministic synthetic fixtures and the injected clock/provider ports where relevant. Run targeted checks for these scenarios and the relevant available lint/type/contract gates from the Makefile. Do not call paid providers or fabricate measured results. Regenerate contracts if changed, and inspect the diff for unrelated edits.

HANDOFF
Return the implemented paths, behavior mapped to the requirement IDs, exact commands and actual outcomes, schema/config/API impact, unresolved blockers and reviewer focus. Default reviewer: M1. Leave production TODO placeholders out of the delivered behavior; if a required check could not run, state the reason and keep the completion gate unverified.
```

### MS-047 — Explicit evaluation API

**Owner:** M4. **Reviewer:** M6. **Priority:** P0. **Estimate:** 2.5 hours.

**Expected input:** The package contracts for R07.01, R07.04, R07.05 and US-07.01, US-07.04, US-07.05; merged, tested outputs of MS-044, MS-045, MS-008.

**Blocked until:** MS-044 — Evaluation workflow stage; MS-045 — Public opportunity and source reads; MS-008 — JWT authentication and account API

**Expected outcome:** Implement explicit evaluation command and owner-only result read with currentness metadata and independent status fields.

**Acceptance:** Unknown-version IDs fail before queueing; stale input is marked rather than silently rebased.

**Exact prompt:**

```text
Implement MS-047 — Explicit evaluation API for BenefitBridge as M4.
Use the common system prompt and M4 role rules in agent.md. Work on branch feat/ms-047-eval-api. Preserve unrelated changes.

EXPECTED INPUT
The package contracts for R07.01, R07.04, R07.05 and US-07.01, US-07.04, US-07.05; merged, tested outputs of MS-044, MS-045, MS-008.
Strict prerequisites: MS-044 — Evaluation workflow stage; MS-045 — Public opportunity and source reads; MS-008 — JWT authentication and account API
Verify prerequisite interfaces exist before editing. A missing prerequisite is a blocker, not permission to build an incompatible stub.

READ AND RESPECT
Read requirements.md entries R07.01, R07.04, R07.05, userStory.md entries US-07.01, US-07.04, US-07.05, this sprint in sprints.md, relevant design.md invariants, API.md common conventions/DTOs and the operations listed below. Follow agent.md style, privacy, versioning, error and ownership rules.

WRITE SCOPE
backend/src/benefitbridge/api/evaluations.py.
Also edit only directly corresponding tests and mechanically regenerated OpenAPI/client files when affected. Shared domain, registry or migration changes outside this scope require an explicit owner handoff; do not silently expand the task.

IMPLEMENTATION AND EXPECTED OUTCOME
Implement explicit evaluation command and owner-only result read with currentness metadata and independent status fields.
Implement only this unit. Produce the scoped typed implementation and its usable interface in the development composition. Production behavior must pass the specified checks.

API CONTRACT
- start_evaluation: POST /api/v1/evaluations; auth=USER; success=202; idempotency=required; implement its exact request/response/validation in API.md.
- get_evaluation: GET /api/v1/evaluations/{evaluation_id}; auth=USER; success=200; idempotency=as specified; implement its exact request/response/validation in API.md.

ACCEPTANCE AND VERIFICATION
Unknown-version IDs fail before queueing; stale input is marked rather than silently rebased.
Use deterministic synthetic fixtures and the injected clock/provider ports where relevant. Run targeted checks for these scenarios and the relevant available lint/type/contract gates from the Makefile. Do not call paid providers or fabricate measured results. Regenerate contracts if changed, and inspect the diff for unrelated edits.

HANDOFF
Return the implemented paths, behavior mapped to the requirement IDs, exact commands and actual outcomes, schema/config/API impact, unresolved blockers and reviewer focus. Default reviewer: M6. Leave production TODO placeholders out of the delivered behavior; if a required check could not run, state the reason and keep the completion gate unverified.
```

### MS-048 — Discovery form and results feed

**Owner:** M2. **Reviewer:** M6. **Priority:** P0. **Estimate:** 2.5 hours.

**Expected input:** The package contracts for R04.01, R04.04, R04.05, R08.01, R08.02 and US-04.01, US-04.04, US-04.05, US-08.01, US-08.02; merged, tested outputs of MS-046, MS-045, MS-031, MS-018.

**Blocked until:** MS-046 — Discovery and URL-import commands; MS-045 — Public opportunity and source reads; MS-031 — Durable progress components; MS-018 — Structured profile editor

**Expected outcome:** Build goal entry, lane/preferences, URL import and incrementally loaded results. Show unevaluated and partial candidates with funnel counts.

**Acceptance:** Unavailable and UNKNOWN differ visually and in text; no fake percentage eligibility.

**Exact prompt:**

```text
Implement MS-048 — Discovery form and results feed for BenefitBridge as M2.
Use the common system prompt and M2 role rules in agent.md. Work on branch feat/ms-048-explore-ui. Preserve unrelated changes.

EXPECTED INPUT
The package contracts for R04.01, R04.04, R04.05, R08.01, R08.02 and US-04.01, US-04.04, US-04.05, US-08.01, US-08.02; merged, tested outputs of MS-046, MS-045, MS-031, MS-018.
Strict prerequisites: MS-046 — Discovery and URL-import commands; MS-045 — Public opportunity and source reads; MS-031 — Durable progress components; MS-018 — Structured profile editor
Verify prerequisite interfaces exist before editing. A missing prerequisite is a blocker, not permission to build an incompatible stub.

READ AND RESPECT
Read requirements.md entries R04.01, R04.04, R04.05, R08.01, R08.02, userStory.md entries US-04.01, US-04.04, US-04.05, US-08.01, US-08.02, this sprint in sprints.md, relevant design.md invariants, API.md common conventions/DTOs and the operations listed below. Follow agent.md style, privacy, versioning, error and ownership rules.

WRITE SCOPE
frontend/src/features/discovery/.
Also edit only directly corresponding tests and mechanically regenerated OpenAPI/client files when affected. Shared domain, registry or migration changes outside this scope require an explicit owner handoff; do not silently expand the task.

IMPLEMENTATION AND EXPECTED OUTCOME
Build goal entry, lane/preferences, URL import and incrementally loaded results. Show unevaluated and partial candidates with funnel counts.
Implement only this unit. Produce the scoped typed implementation and its usable interface in the development composition. Production behavior must pass the specified checks.

API CONTRACT
- No new public endpoint in this task. Preserve the documented API and expose only the internal interface required by dependent tasks.

ACCEPTANCE AND VERIFICATION
Unavailable and UNKNOWN differ visually and in text; no fake percentage eligibility.
Use deterministic synthetic fixtures and the injected clock/provider ports where relevant. Run targeted checks for these scenarios and the relevant available lint/type/contract gates from the Makefile. Do not call paid providers or fabricate measured results. Regenerate contracts if changed, and inspect the diff for unrelated edits.

HANDOFF
Return the implemented paths, behavior mapped to the requirement IDs, exact commands and actual outcomes, schema/config/API impact, unresolved blockers and reviewer focus. Default reviewer: M6. Leave production TODO placeholders out of the delivered behavior; if a required check could not run, state the reason and keep the completion gate unverified.
```

### MS-049 — Decision and evidence detail screen

**Owner:** M2. **Reviewer:** M6. **Priority:** P0. **Estimate:** 2.5 hours.

**Expected input:** The package contracts for R06.01, R07.04, R07.05, R12.02, R12.04 and US-06.01, US-07.04, US-07.05, US-12.02, US-12.04; merged, tested outputs of MS-047, MS-048.

**Blocked until:** MS-047 — Explicit evaluation API; MS-048 — Discovery form and results feed

**Expected outcome:** Render each leaf with source passage, applicant fact, evidence provenance, method and next action; show historical/current versions distinctly.

**Acceptance:** A judge can keyboard-navigate source and evidence; stale input warning remains visible.

**Exact prompt:**

```text
Implement MS-049 — Decision and evidence detail screen for BenefitBridge as M2.
Use the common system prompt and M2 role rules in agent.md. Work on branch feat/ms-049-detail-ui. Preserve unrelated changes.

EXPECTED INPUT
The package contracts for R06.01, R07.04, R07.05, R12.02, R12.04 and US-06.01, US-07.04, US-07.05, US-12.02, US-12.04; merged, tested outputs of MS-047, MS-048.
Strict prerequisites: MS-047 — Explicit evaluation API; MS-048 — Discovery form and results feed
Verify prerequisite interfaces exist before editing. A missing prerequisite is a blocker, not permission to build an incompatible stub.

READ AND RESPECT
Read requirements.md entries R06.01, R07.04, R07.05, R12.02, R12.04, userStory.md entries US-06.01, US-07.04, US-07.05, US-12.02, US-12.04, this sprint in sprints.md, relevant design.md invariants, API.md common conventions/DTOs and the operations listed below. Follow agent.md style, privacy, versioning, error and ownership rules.

WRITE SCOPE
frontend/src/features/opportunity/.
Also edit only directly corresponding tests and mechanically regenerated OpenAPI/client files when affected. Shared domain, registry or migration changes outside this scope require an explicit owner handoff; do not silently expand the task.

IMPLEMENTATION AND EXPECTED OUTCOME
Render each leaf with source passage, applicant fact, evidence provenance, method and next action; show historical/current versions distinctly.
Implement only this unit. Produce the scoped typed implementation and its usable interface in the development composition. Production behavior must pass the specified checks.

API CONTRACT
- No new public endpoint in this task. Preserve the documented API and expose only the internal interface required by dependent tasks.

ACCEPTANCE AND VERIFICATION
A judge can keyboard-navigate source and evidence; stale input warning remains visible.
Use deterministic synthetic fixtures and the injected clock/provider ports where relevant. Run targeted checks for these scenarios and the relevant available lint/type/contract gates from the Makefile. Do not call paid providers or fabricate measured results. Regenerate contracts if changed, and inspect the diff for unrelated edits.

HANDOFF
Return the implemented paths, behavior mapped to the requirement IDs, exact commands and actual outcomes, schema/config/API impact, unresolved blockers and reviewer focus. Default reviewer: M6. Leave production TODO placeholders out of the delivered behavior; if a required check could not run, state the reason and keep the completion gate unverified.
```

### MS-050 — Clarification persistence and resumption

**Owner:** M3. **Reviewer:** M1. **Priority:** P0. **Estimate:** 3 hours.

**Expected input:** The package contracts for R08.03, R08.04 and US-08.03, US-08.04; merged, tested outputs of MS-044, MS-017, MS-030.

**Blocked until:** MS-044 — Evaluation workflow stage; MS-017 — Versioned profile read and edit API; MS-030 — Run control and authenticated event stream

**Expected outcome:** Create up to three attribute questions per round, two rounds maximum. Validate answers against base profile and clarification-set revision; atomically publish profile version and requeue only evaluation.

**Acceptance:** Duplicate answer retries do not create duplicate versions; unrelated concurrent profile edit returns 409.

**Exact prompt:**

```text
Implement MS-050 — Clarification persistence and resumption for BenefitBridge as M3.
Use the common system prompt and M3 role rules in agent.md. Work on branch feat/ms-050-clarify. Preserve unrelated changes.

EXPECTED INPUT
The package contracts for R08.03, R08.04 and US-08.03, US-08.04; merged, tested outputs of MS-044, MS-017, MS-030.
Strict prerequisites: MS-044 — Evaluation workflow stage; MS-017 — Versioned profile read and edit API; MS-030 — Run control and authenticated event stream
Verify prerequisite interfaces exist before editing. A missing prerequisite is a blocker, not permission to build an incompatible stub.

READ AND RESPECT
Read requirements.md entries R08.03, R08.04, userStory.md entries US-08.03, US-08.04, this sprint in sprints.md, relevant design.md invariants, API.md common conventions/DTOs and the operations listed below. Follow agent.md style, privacy, versioning, error and ownership rules.

WRITE SCOPE
backend/src/benefitbridge/api/clarifications.py; backend/src/benefitbridge/workflows/clarify.py.
Also edit only directly corresponding tests and mechanically regenerated OpenAPI/client files when affected. Shared domain, registry or migration changes outside this scope require an explicit owner handoff; do not silently expand the task.

IMPLEMENTATION AND EXPECTED OUTCOME
Create up to three attribute questions per round, two rounds maximum. Validate answers against base profile and clarification-set revision; atomically publish profile version and requeue only evaluation.
Implement only this unit. Produce the scoped typed implementation and its usable interface in the development composition. Production behavior must pass the specified checks.

API CONTRACT
- get_clarifications: GET /api/v1/runs/{run_id}/clarifications; auth=USER; success=200; idempotency=as specified; implement its exact request/response/validation in API.md.
- answer_clarifications: POST /api/v1/runs/{run_id}/clarifications/{clarification_set_id}/answers; auth=USER; success=202; idempotency=required; implement its exact request/response/validation in API.md.

ACCEPTANCE AND VERIFICATION
Duplicate answer retries do not create duplicate versions; unrelated concurrent profile edit returns 409.
Use deterministic synthetic fixtures and the injected clock/provider ports where relevant. Run targeted checks for these scenarios and the relevant available lint/type/contract gates from the Makefile. Do not call paid providers or fabricate measured results. Regenerate contracts if changed, and inspect the diff for unrelated edits.

HANDOFF
Return the implemented paths, behavior mapped to the requirement IDs, exact commands and actual outcomes, schema/config/API impact, unresolved blockers and reviewer focus. Default reviewer: M1. Leave production TODO placeholders out of the delivered behavior; if a required check could not run, state the reason and keep the completion gate unverified.
```

### MS-051 — Targeted fact clarification UI

**Owner:** M2. **Reviewer:** M6. **Priority:** P0. **Estimate:** 2.5 hours.

**Expected input:** The package contracts for R08.03, R08.04, R12.03 and US-08.03, US-08.04, US-12.03; merged, tested outputs of MS-050, MS-049.

**Blocked until:** MS-050 — Clarification persistence and resumption; MS-049 — Decision and evidence detail screen

**Expected outcome:** Render typed questions, explain why each matters, allow unknown/skip, handle 409 reload and resume the linked run.

**Acceptance:** Skipped unknown cannot become false; no indefinite round loop.

**Exact prompt:**

```text
Implement MS-051 — Targeted fact clarification UI for BenefitBridge as M2.
Use the common system prompt and M2 role rules in agent.md. Work on branch feat/ms-051-clarify-ui. Preserve unrelated changes.

EXPECTED INPUT
The package contracts for R08.03, R08.04, R12.03 and US-08.03, US-08.04, US-12.03; merged, tested outputs of MS-050, MS-049.
Strict prerequisites: MS-050 — Clarification persistence and resumption; MS-049 — Decision and evidence detail screen
Verify prerequisite interfaces exist before editing. A missing prerequisite is a blocker, not permission to build an incompatible stub.

READ AND RESPECT
Read requirements.md entries R08.03, R08.04, R12.03, userStory.md entries US-08.03, US-08.04, US-12.03, this sprint in sprints.md, relevant design.md invariants, API.md common conventions/DTOs and the operations listed below. Follow agent.md style, privacy, versioning, error and ownership rules.

WRITE SCOPE
frontend/src/features/clarifications/.
Also edit only directly corresponding tests and mechanically regenerated OpenAPI/client files when affected. Shared domain, registry or migration changes outside this scope require an explicit owner handoff; do not silently expand the task.

IMPLEMENTATION AND EXPECTED OUTCOME
Render typed questions, explain why each matters, allow unknown/skip, handle 409 reload and resume the linked run.
Implement only this unit. Produce the scoped typed implementation and its usable interface in the development composition. Production behavior must pass the specified checks.

API CONTRACT
- No new public endpoint in this task. Preserve the documented API and expose only the internal interface required by dependent tasks.

ACCEPTANCE AND VERIFICATION
Skipped unknown cannot become false; no indefinite round loop.
Use deterministic synthetic fixtures and the injected clock/provider ports where relevant. Run targeted checks for these scenarios and the relevant available lint/type/contract gates from the Makefile. Do not call paid providers or fabricate measured results. Regenerate contracts if changed, and inspect the diff for unrelated edits.

HANDOFF
Return the implemented paths, behavior mapped to the requirement IDs, exact commands and actual outcomes, schema/config/API impact, unresolved blockers and reviewer focus. Default reviewer: M6. Leave production TODO placeholders out of the delivered behavior; if a required check could not run, state the reason and keep the completion gate unverified.
```

### MS-052 — Application and shortlist schema

**Owner:** M1. **Reviewer:** M3. **Priority:** P0. **Estimate:** 3 hours.

**Expected input:** The package contracts for R09.01, R09.02, R09.04, R11.01 and US-09.01, US-09.02, US-09.04, US-11.01; merged, tested outputs of MS-038.

**Blocked until:** MS-038 — Requirement and evaluation persistence

**Expected outcome:** Create saved_opportunities, applications, checklist_items, drafts, draft_claims and acceptance records with revision checks and version-bound acceptance.

**Acceptance:** Foreign-owner facts in claims fail; one active application per owner/opportunity cycle is enforced.

**Exact prompt:**

```text
Implement MS-052 — Application and shortlist schema for BenefitBridge as M1.
Use the common system prompt and M1 role rules in agent.md. Work on branch feat/ms-052-db-app. Preserve unrelated changes.

EXPECTED INPUT
The package contracts for R09.01, R09.02, R09.04, R11.01 and US-09.01, US-09.02, US-09.04, US-11.01; merged, tested outputs of MS-038.
Strict prerequisites: MS-038 — Requirement and evaluation persistence
Verify prerequisite interfaces exist before editing. A missing prerequisite is a blocker, not permission to build an incompatible stub.

READ AND RESPECT
Read requirements.md entries R09.01, R09.02, R09.04, R11.01, userStory.md entries US-09.01, US-09.02, US-09.04, US-11.01, this sprint in sprints.md, relevant design.md invariants, API.md common conventions/DTOs and the operations listed below. Follow agent.md style, privacy, versioning, error and ownership rules.

WRITE SCOPE
backend/migrations/versions/0006_applications.py; backend/src/benefitbridge/db/applications.py.
Also edit only directly corresponding tests and mechanically regenerated OpenAPI/client files when affected. Shared domain, registry or migration changes outside this scope require an explicit owner handoff; do not silently expand the task.

IMPLEMENTATION AND EXPECTED OUTCOME
Create saved_opportunities, applications, checklist_items, drafts, draft_claims and acceptance records with revision checks and version-bound acceptance.
Implement only this unit. Produce the scoped typed implementation and its usable interface in the development composition. Production behavior must pass the specified checks.

API CONTRACT
- No new public endpoint in this task. Preserve the documented API and expose only the internal interface required by dependent tasks.

ACCEPTANCE AND VERIFICATION
Foreign-owner facts in claims fail; one active application per owner/opportunity cycle is enforced.
Use deterministic synthetic fixtures and the injected clock/provider ports where relevant. Run targeted checks for these scenarios and the relevant available lint/type/contract gates from the Makefile. Do not call paid providers or fabricate measured results. Regenerate contracts if changed, and inspect the diff for unrelated edits.

HANDOFF
Return the implemented paths, behavior mapped to the requirement IDs, exact commands and actual outcomes, schema/config/API impact, unresolved blockers and reviewer focus. Default reviewer: M3. Leave production TODO placeholders out of the delivered behavior; if a required check could not run, state the reason and keep the completion gate unverified.
```

### MS-053 — Saved opportunity endpoints

**Owner:** M1. **Reviewer:** M3. **Priority:** P0. **Estimate:** 2.5 hours.

**Expected input:** The package contracts for R11.01, R11.02 and US-11.01, US-11.02; merged, tested outputs of MS-052, MS-045.

**Blocked until:** MS-052 — Application and shortlist schema; MS-045 — Public opportunity and source reads

**Expected outcome:** Implement owner-scoped save, list and delete with current evaluation joins and stale badges; save does not automatically trigger unbounded evaluation.

**Acceptance:** Repeated PUT is safe; deleting another owner save yields no disclosed metadata.

**Exact prompt:**

```text
Implement MS-053 — Saved opportunity endpoints for BenefitBridge as M1.
Use the common system prompt and M1 role rules in agent.md. Work on branch feat/ms-053-saved-api. Preserve unrelated changes.

EXPECTED INPUT
The package contracts for R11.01, R11.02 and US-11.01, US-11.02; merged, tested outputs of MS-052, MS-045.
Strict prerequisites: MS-052 — Application and shortlist schema; MS-045 — Public opportunity and source reads
Verify prerequisite interfaces exist before editing. A missing prerequisite is a blocker, not permission to build an incompatible stub.

READ AND RESPECT
Read requirements.md entries R11.01, R11.02, userStory.md entries US-11.01, US-11.02, this sprint in sprints.md, relevant design.md invariants, API.md common conventions/DTOs and the operations listed below. Follow agent.md style, privacy, versioning, error and ownership rules.

WRITE SCOPE
backend/src/benefitbridge/api/saved.py.
Also edit only directly corresponding tests and mechanically regenerated OpenAPI/client files when affected. Shared domain, registry or migration changes outside this scope require an explicit owner handoff; do not silently expand the task.

IMPLEMENTATION AND EXPECTED OUTCOME
Implement owner-scoped save, list and delete with current evaluation joins and stale badges; save does not automatically trigger unbounded evaluation.
Implement only this unit. Produce the scoped typed implementation and its usable interface in the development composition. Production behavior must pass the specified checks.

API CONTRACT
- list_saved: GET /api/v1/saved-opportunities; auth=USER; success=200; idempotency=as specified; implement its exact request/response/validation in API.md.
- save_opportunity: PUT /api/v1/saved-opportunities/{opportunity_id}; auth=USER; success=200; idempotency=as specified; implement its exact request/response/validation in API.md.
- delete_saved: DELETE /api/v1/saved-opportunities/{opportunity_id}; auth=USER; success=204; idempotency=as specified; implement its exact request/response/validation in API.md.

ACCEPTANCE AND VERIFICATION
Repeated PUT is safe; deleting another owner save yields no disclosed metadata.
Use deterministic synthetic fixtures and the injected clock/provider ports where relevant. Run targeted checks for these scenarios and the relevant available lint/type/contract gates from the Makefile. Do not call paid providers or fabricate measured results. Regenerate contracts if changed, and inspect the diff for unrelated edits.

HANDOFF
Return the implemented paths, behavior mapped to the requirement IDs, exact commands and actual outcomes, schema/config/API impact, unresolved blockers and reviewer focus. Default reviewer: M3. Leave production TODO placeholders out of the delivered behavior; if a required check could not run, state the reason and keep the completion gate unverified.
```

### MS-054 — Shortlist screen

**Owner:** M2. **Reviewer:** M6. **Priority:** P0. **Estimate:** 2.5 hours.

**Expected input:** The package contracts for R11.01, R11.02 and US-11.01, US-11.02; merged, tested outputs of MS-053, MS-049.

**Blocked until:** MS-053 — Saved opportunity endpoints; MS-049 — Decision and evidence detail screen

**Expected outcome:** Build save controls, shortlist filters and stale/refresh actions from API state.

**Acceptance:** Reload preserves saves; removing a save does not delete public opportunities.

**Exact prompt:**

```text
Implement MS-054 — Shortlist screen for BenefitBridge as M2.
Use the common system prompt and M2 role rules in agent.md. Work on branch feat/ms-054-saved-ui. Preserve unrelated changes.

EXPECTED INPUT
The package contracts for R11.01, R11.02 and US-11.01, US-11.02; merged, tested outputs of MS-053, MS-049.
Strict prerequisites: MS-053 — Saved opportunity endpoints; MS-049 — Decision and evidence detail screen
Verify prerequisite interfaces exist before editing. A missing prerequisite is a blocker, not permission to build an incompatible stub.

READ AND RESPECT
Read requirements.md entries R11.01, R11.02, userStory.md entries US-11.01, US-11.02, this sprint in sprints.md, relevant design.md invariants, API.md common conventions/DTOs and the operations listed below. Follow agent.md style, privacy, versioning, error and ownership rules.

WRITE SCOPE
frontend/src/features/saved/.
Also edit only directly corresponding tests and mechanically regenerated OpenAPI/client files when affected. Shared domain, registry or migration changes outside this scope require an explicit owner handoff; do not silently expand the task.

IMPLEMENTATION AND EXPECTED OUTCOME
Build save controls, shortlist filters and stale/refresh actions from API state.
Implement only this unit. Produce the scoped typed implementation and its usable interface in the development composition. Production behavior must pass the specified checks.

API CONTRACT
- No new public endpoint in this task. Preserve the documented API and expose only the internal interface required by dependent tasks.

ACCEPTANCE AND VERIFICATION
Reload preserves saves; removing a save does not delete public opportunities.
Use deterministic synthetic fixtures and the injected clock/provider ports where relevant. Run targeted checks for these scenarios and the relevant available lint/type/contract gates from the Makefile. Do not call paid providers or fabricate measured results. Regenerate contracts if changed, and inspect the diff for unrelated edits.

HANDOFF
Return the implemented paths, behavior mapped to the requirement IDs, exact commands and actual outcomes, schema/config/API impact, unresolved blockers and reviewer focus. Default reviewer: M6. Leave production TODO placeholders out of the delivered behavior; if a required check could not run, state the reason and keep the completion gate unverified.
```

### MS-055 — Deterministic application checklist builder

**Owner:** M4. **Reviewer:** M6. **Priority:** P0. **Estimate:** 2.5 hours.

**Expected input:** The package contracts for R08.05, R09.02 and US-08.05, US-09.02; merged, tested outputs of MS-042, MS-036.

**Blocked until:** MS-042 — Availability, fit, readiness and sorting; MS-036 — Requirement publication validator

**Expected outcome:** Map applicable documentary requirements and tasks to stable keys with evidence expectations; include required statement only when requested by source.

**Acceptance:** Unknown applicability is a blocker, not a completed task; recomputation preserves valid manual task states.

**Exact prompt:**

```text
Implement MS-055 — Deterministic application checklist builder for BenefitBridge as M4.
Use the common system prompt and M4 role rules in agent.md. Work on branch feat/ms-055-checklist. Preserve unrelated changes.

EXPECTED INPUT
The package contracts for R08.05, R09.02 and US-08.05, US-09.02; merged, tested outputs of MS-042, MS-036.
Strict prerequisites: MS-042 — Availability, fit, readiness and sorting; MS-036 — Requirement publication validator
Verify prerequisite interfaces exist before editing. A missing prerequisite is a blocker, not permission to build an incompatible stub.

READ AND RESPECT
Read requirements.md entries R08.05, R09.02, userStory.md entries US-08.05, US-09.02, this sprint in sprints.md, relevant design.md invariants, API.md common conventions/DTOs and the operations listed below. Follow agent.md style, privacy, versioning, error and ownership rules.

WRITE SCOPE
backend/src/benefitbridge/applications/checklist.py.
Also edit only directly corresponding tests and mechanically regenerated OpenAPI/client files when affected. Shared domain, registry or migration changes outside this scope require an explicit owner handoff; do not silently expand the task.

IMPLEMENTATION AND EXPECTED OUTCOME
Map applicable documentary requirements and tasks to stable keys with evidence expectations; include required statement only when requested by source.
Implement only this unit. Produce the scoped typed implementation and its usable interface in the development composition. Production behavior must pass the specified checks.

API CONTRACT
- No new public endpoint in this task. Preserve the documented API and expose only the internal interface required by dependent tasks.

ACCEPTANCE AND VERIFICATION
Unknown applicability is a blocker, not a completed task; recomputation preserves valid manual task states.
Use deterministic synthetic fixtures and the injected clock/provider ports where relevant. Run targeted checks for these scenarios and the relevant available lint/type/contract gates from the Makefile. Do not call paid providers or fabricate measured results. Regenerate contracts if changed, and inspect the diff for unrelated edits.

HANDOFF
Return the implemented paths, behavior mapped to the requirement IDs, exact commands and actual outcomes, schema/config/API impact, unresolved blockers and reviewer focus. Default reviewer: M6. Leave production TODO placeholders out of the delivered behavior; if a required check could not run, state the reason and keep the completion gate unverified.
```

### MS-056 — Application and checklist API

**Owner:** M4. **Reviewer:** M6. **Priority:** P0. **Estimate:** 3 hours.

**Expected input:** The package contracts for R09.01, R09.02, R08.05 and US-09.01, US-09.02, US-08.05; merged, tested outputs of MS-052, MS-055, MS-047.

**Blocked until:** MS-052 — Application and shortlist schema; MS-055 — Deterministic application checklist builder; MS-047 — Explicit evaluation API

**Expected outcome:** Create version-pinned application; expose list/detail; update non-draft checklist items with application revision and owner evidence validation.

**Acceptance:** Stale evaluation blocks creation; draft task cannot be completed manually to bypass review.

**Exact prompt:**

```text
Implement MS-056 — Application and checklist API for BenefitBridge as M4.
Use the common system prompt and M4 role rules in agent.md. Work on branch feat/ms-056-app-api. Preserve unrelated changes.

EXPECTED INPUT
The package contracts for R09.01, R09.02, R08.05 and US-09.01, US-09.02, US-08.05; merged, tested outputs of MS-052, MS-055, MS-047.
Strict prerequisites: MS-052 — Application and shortlist schema; MS-055 — Deterministic application checklist builder; MS-047 — Explicit evaluation API
Verify prerequisite interfaces exist before editing. A missing prerequisite is a blocker, not permission to build an incompatible stub.

READ AND RESPECT
Read requirements.md entries R09.01, R09.02, R08.05, userStory.md entries US-09.01, US-09.02, US-08.05, this sprint in sprints.md, relevant design.md invariants, API.md common conventions/DTOs and the operations listed below. Follow agent.md style, privacy, versioning, error and ownership rules.

WRITE SCOPE
backend/src/benefitbridge/api/applications.py.
Also edit only directly corresponding tests and mechanically regenerated OpenAPI/client files when affected. Shared domain, registry or migration changes outside this scope require an explicit owner handoff; do not silently expand the task.

IMPLEMENTATION AND EXPECTED OUTCOME
Create version-pinned application; expose list/detail; update non-draft checklist items with application revision and owner evidence validation.
Implement only this unit. Produce the scoped typed implementation and its usable interface in the development composition. Production behavior must pass the specified checks.

API CONTRACT
- list_applications: GET /api/v1/applications; auth=USER; success=200; idempotency=as specified; implement its exact request/response/validation in API.md.
- create_application: POST /api/v1/applications; auth=USER; success=201; idempotency=required; implement its exact request/response/validation in API.md.
- get_application: GET /api/v1/applications/{application_id}; auth=USER; success=200; idempotency=as specified; implement its exact request/response/validation in API.md.
- patch_checklist_item: PATCH /api/v1/applications/{application_id}/items/{item_id}; auth=USER; success=200; idempotency=required; implement its exact request/response/validation in API.md.

ACCEPTANCE AND VERIFICATION
Stale evaluation blocks creation; draft task cannot be completed manually to bypass review.
Use deterministic synthetic fixtures and the injected clock/provider ports where relevant. Run targeted checks for these scenarios and the relevant available lint/type/contract gates from the Makefile. Do not call paid providers or fabricate measured results. Regenerate contracts if changed, and inspect the diff for unrelated edits.

HANDOFF
Return the implemented paths, behavior mapped to the requirement IDs, exact commands and actual outcomes, schema/config/API impact, unresolved blockers and reviewer focus. Default reviewer: M6. Leave production TODO placeholders out of the delivered behavior; if a required check could not run, state the reason and keep the completion gate unverified.
```

### MS-057 — Grounded statement generation stage

**Owner:** M3. **Reviewer:** M1. **Priority:** P0. **Estimate:** 3 hours.

**Expected input:** The package contracts for R09.03, R13.02 and US-09.03, US-13.02; merged, tested outputs of MS-020, MS-056.

**Blocked until:** MS-020 — Nebius structured inference adapter; MS-056 — Application and checklist API

**Expected outcome:** Generate a 150–500 word statement from confirmed facts and selected source instructions, with claim-to-fact/evidence links. Unsupported qualifications become missing-input items.

**Acceptance:** Prompt injection cannot add qualifications; call budget and statement bounds enforced.

**Exact prompt:**

```text
Implement MS-057 — Grounded statement generation stage for BenefitBridge as M3.
Use the common system prompt and M3 role rules in agent.md. Work on branch feat/ms-057-draft-gen. Preserve unrelated changes.

EXPECTED INPUT
The package contracts for R09.03, R13.02 and US-09.03, US-13.02; merged, tested outputs of MS-020, MS-056.
Strict prerequisites: MS-020 — Nebius structured inference adapter; MS-056 — Application and checklist API
Verify prerequisite interfaces exist before editing. A missing prerequisite is a blocker, not permission to build an incompatible stub.

READ AND RESPECT
Read requirements.md entries R09.03, R13.02, userStory.md entries US-09.03, US-13.02, this sprint in sprints.md, relevant design.md invariants, API.md common conventions/DTOs and the operations listed below. Follow agent.md style, privacy, versioning, error and ownership rules.

WRITE SCOPE
backend/src/benefitbridge/applications/generate.py.
Also edit only directly corresponding tests and mechanically regenerated OpenAPI/client files when affected. Shared domain, registry or migration changes outside this scope require an explicit owner handoff; do not silently expand the task.

IMPLEMENTATION AND EXPECTED OUTCOME
Generate a 150–500 word statement from confirmed facts and selected source instructions, with claim-to-fact/evidence links. Unsupported qualifications become missing-input items.
Implement only this unit. Produce the scoped typed implementation and its usable interface in the development composition. Production behavior must pass the specified checks.

API CONTRACT
- No new public endpoint in this task. Preserve the documented API and expose only the internal interface required by dependent tasks.

ACCEPTANCE AND VERIFICATION
Prompt injection cannot add qualifications; call budget and statement bounds enforced.
Use deterministic synthetic fixtures and the injected clock/provider ports where relevant. Run targeted checks for these scenarios and the relevant available lint/type/contract gates from the Makefile. Do not call paid providers or fabricate measured results. Regenerate contracts if changed, and inspect the diff for unrelated edits.

HANDOFF
Return the implemented paths, behavior mapped to the requirement IDs, exact commands and actual outcomes, schema/config/API impact, unresolved blockers and reviewer focus. Default reviewer: M1. Leave production TODO placeholders out of the delivered behavior; if a required check could not run, state the reason and keep the completion gate unverified.
```

### MS-058 — Draft claim validation and acceptance rules

**Owner:** M4. **Reviewer:** M6. **Priority:** P0. **Estimate:** 3 hours.

**Expected input:** The package contracts for R09.03, R09.04 and US-09.03, US-09.04; merged, tested outputs of MS-057, MS-041.

**Blocked until:** MS-057 — Grounded statement generation stage; MS-041 — Decision and citation verification

**Expected outcome:** Validate each material qualification, citations and input currentness. Persist VALID, INVALID or UNKNOWN validation with explanatory issues; only VALID current versions are acceptable.

**Acceptance:** Fabricated award, stale GPA and deleted evidence block acceptance; optional style sentences need no invented evidence.

**Exact prompt:**

```text
Implement MS-058 — Draft claim validation and acceptance rules for BenefitBridge as M4.
Use the common system prompt and M4 role rules in agent.md. Work on branch feat/ms-058-draft-verify. Preserve unrelated changes.

EXPECTED INPUT
The package contracts for R09.03, R09.04 and US-09.03, US-09.04; merged, tested outputs of MS-057, MS-041.
Strict prerequisites: MS-057 — Grounded statement generation stage; MS-041 — Decision and citation verification
Verify prerequisite interfaces exist before editing. A missing prerequisite is a blocker, not permission to build an incompatible stub.

READ AND RESPECT
Read requirements.md entries R09.03, R09.04, userStory.md entries US-09.03, US-09.04, this sprint in sprints.md, relevant design.md invariants, API.md common conventions/DTOs and the operations listed below. Follow agent.md style, privacy, versioning, error and ownership rules.

WRITE SCOPE
backend/src/benefitbridge/applications/verify_draft.py.
Also edit only directly corresponding tests and mechanically regenerated OpenAPI/client files when affected. Shared domain, registry or migration changes outside this scope require an explicit owner handoff; do not silently expand the task.

IMPLEMENTATION AND EXPECTED OUTCOME
Validate each material qualification, citations and input currentness. Persist VALID, INVALID or UNKNOWN validation with explanatory issues; only VALID current versions are acceptable.
Implement only this unit. Produce the scoped typed implementation and its usable interface in the development composition. Production behavior must pass the specified checks.

API CONTRACT
- No new public endpoint in this task. Preserve the documented API and expose only the internal interface required by dependent tasks.

ACCEPTANCE AND VERIFICATION
Fabricated award, stale GPA and deleted evidence block acceptance; optional style sentences need no invented evidence.
Use deterministic synthetic fixtures and the injected clock/provider ports where relevant. Run targeted checks for these scenarios and the relevant available lint/type/contract gates from the Makefile. Do not call paid providers or fabricate measured results. Regenerate contracts if changed, and inspect the diff for unrelated edits.

HANDOFF
Return the implemented paths, behavior mapped to the requirement IDs, exact commands and actual outcomes, schema/config/API impact, unresolved blockers and reviewer focus. Default reviewer: M6. Leave production TODO placeholders out of the delivered behavior; if a required check could not run, state the reason and keep the completion gate unverified.
```

### MS-059 — Draft versions, review and export API

**Owner:** M3. **Reviewer:** M1. **Priority:** P0. **Estimate:** 3 hours.

**Expected input:** The package contracts for R09.03, R09.04, R09.05 and US-09.03, US-09.04, US-09.05; merged, tested outputs of MS-058, MS-056, MS-016.

**Blocked until:** MS-058 — Draft claim validation and acceptance rules; MS-056 — Application and checklist API; MS-016 — Leased PostgreSQL job dispatcher

**Expected outcome:** Queue generation/edit-validation, expose immutable versions, accept exact validated version with revision guard and export only current accepted text plus checklist.

**Acceptance:** Editing clears acceptance; stale export returns 409; unaccepted draft never counts toward readiness.

**Exact prompt:**

```text
Implement MS-059 — Draft versions, review and export API for BenefitBridge as M3.
Use the common system prompt and M3 role rules in agent.md. Work on branch feat/ms-059-draft-api. Preserve unrelated changes.

EXPECTED INPUT
The package contracts for R09.03, R09.04, R09.05 and US-09.03, US-09.04, US-09.05; merged, tested outputs of MS-058, MS-056, MS-016.
Strict prerequisites: MS-058 — Draft claim validation and acceptance rules; MS-056 — Application and checklist API; MS-016 — Leased PostgreSQL job dispatcher
Verify prerequisite interfaces exist before editing. A missing prerequisite is a blocker, not permission to build an incompatible stub.

READ AND RESPECT
Read requirements.md entries R09.03, R09.04, R09.05, userStory.md entries US-09.03, US-09.04, US-09.05, this sprint in sprints.md, relevant design.md invariants, API.md common conventions/DTOs and the operations listed below. Follow agent.md style, privacy, versioning, error and ownership rules.

WRITE SCOPE
backend/src/benefitbridge/api/drafts.py; backend/src/benefitbridge/applications/export.py.
Also edit only directly corresponding tests and mechanically regenerated OpenAPI/client files when affected. Shared domain, registry or migration changes outside this scope require an explicit owner handoff; do not silently expand the task.

IMPLEMENTATION AND EXPECTED OUTCOME
Queue generation/edit-validation, expose immutable versions, accept exact validated version with revision guard and export only current accepted text plus checklist.
Implement only this unit. Produce the scoped typed implementation and its usable interface in the development composition. Production behavior must pass the specified checks.

API CONTRACT
- start_draft: POST /api/v1/applications/{application_id}/drafts; auth=USER; success=202; idempotency=required; implement its exact request/response/validation in API.md.
- get_draft: GET /api/v1/drafts/{draft_id}; auth=USER; success=200; idempotency=as specified; implement its exact request/response/validation in API.md.
- edit_draft: POST /api/v1/drafts/{draft_id}/versions; auth=USER; success=202; idempotency=required; implement its exact request/response/validation in API.md.
- accept_draft: POST /api/v1/drafts/{draft_id}/accept; auth=USER; success=200; idempotency=required; implement its exact request/response/validation in API.md.
- export_application: GET /api/v1/applications/{application_id}/export; auth=USER; success=200; idempotency=as specified; implement its exact request/response/validation in API.md.

ACCEPTANCE AND VERIFICATION
Editing clears acceptance; stale export returns 409; unaccepted draft never counts toward readiness.
Use deterministic synthetic fixtures and the injected clock/provider ports where relevant. Run targeted checks for these scenarios and the relevant available lint/type/contract gates from the Makefile. Do not call paid providers or fabricate measured results. Regenerate contracts if changed, and inspect the diff for unrelated edits.

HANDOFF
Return the implemented paths, behavior mapped to the requirement IDs, exact commands and actual outcomes, schema/config/API impact, unresolved blockers and reviewer focus. Default reviewer: M1. Leave production TODO placeholders out of the delivered behavior; if a required check could not run, state the reason and keep the completion gate unverified.
```

### MS-060 — Application preparation workspace

**Owner:** M2. **Reviewer:** M6. **Priority:** P0. **Estimate:** 2.5 hours.

**Expected input:** The package contracts for R09.01, R09.02, R09.03, R09.04, R09.05 and US-09.01, US-09.02, US-09.03, US-09.04, US-09.05; merged, tested outputs of MS-059, MS-054.

**Blocked until:** MS-059 — Draft versions, review and export API; MS-054 — Shortlist screen

**Expected outcome:** Build checklist, generation, claim review, edited-version validation, explicit acceptance and Markdown export. Keep provider submission external and user-driven.

**Acceptance:** Generating text alone leaves readiness incomplete; acceptance of valid current version updates fraction.

**Exact prompt:**

```text
Implement MS-060 — Application preparation workspace for BenefitBridge as M2.
Use the common system prompt and M2 role rules in agent.md. Work on branch feat/ms-060-app-ui. Preserve unrelated changes.

EXPECTED INPUT
The package contracts for R09.01, R09.02, R09.03, R09.04, R09.05 and US-09.01, US-09.02, US-09.03, US-09.04, US-09.05; merged, tested outputs of MS-059, MS-054.
Strict prerequisites: MS-059 — Draft versions, review and export API; MS-054 — Shortlist screen
Verify prerequisite interfaces exist before editing. A missing prerequisite is a blocker, not permission to build an incompatible stub.

READ AND RESPECT
Read requirements.md entries R09.01, R09.02, R09.03, R09.04, R09.05, userStory.md entries US-09.01, US-09.02, US-09.03, US-09.04, US-09.05, this sprint in sprints.md, relevant design.md invariants, API.md common conventions/DTOs and the operations listed below. Follow agent.md style, privacy, versioning, error and ownership rules.

WRITE SCOPE
frontend/src/features/applications/.
Also edit only directly corresponding tests and mechanically regenerated OpenAPI/client files when affected. Shared domain, registry or migration changes outside this scope require an explicit owner handoff; do not silently expand the task.

IMPLEMENTATION AND EXPECTED OUTCOME
Build checklist, generation, claim review, edited-version validation, explicit acceptance and Markdown export. Keep provider submission external and user-driven.
Implement only this unit. Produce the scoped typed implementation and its usable interface in the development composition. Production behavior must pass the specified checks.

API CONTRACT
- No new public endpoint in this task. Preserve the documented API and expose only the internal interface required by dependent tasks.

ACCEPTANCE AND VERIFICATION
Generating text alone leaves readiness incomplete; acceptance of valid current version updates fraction.
Use deterministic synthetic fixtures and the injected clock/provider ports where relevant. Run targeted checks for these scenarios and the relevant available lint/type/contract gates from the Makefile. Do not call paid providers or fabricate measured results. Regenerate contracts if changed, and inspect the diff for unrelated edits.

HANDOFF
Return the implemented paths, behavior mapped to the requirement IDs, exact commands and actual outcomes, schema/config/API impact, unresolved blockers and reviewer focus. Default reviewer: M6. Leave production TODO placeholders out of the delivered behavior; if a required check could not run, state the reason and keep the completion gate unverified.
```

### MS-061 — Source refresh and structural change detection

**Owner:** M5. **Reviewer:** M4. **Priority:** P0. **Estimate:** 3 hours.

**Expected input:** The package contracts for R05.04, R05.05, R11.02 and US-05.04, US-05.05, US-11.02; merged, tested outputs of MS-043, MS-047.

**Blocked until:** MS-043 — Discovery stage graph and candidate persistence; MS-047 — Explicit evaluation API

**Expected outcome:** Queue explicit bounded refresh, compare hashes then semantic fields, create new versions only for changes and emit deduplicated invalidation outbox.

**Acceptance:** Unchanged source refresh updates fetch freshness only; failed fetch preserves last-known content.

**Exact prompt:**

```text
Implement MS-061 — Source refresh and structural change detection for BenefitBridge as M5.
Use the common system prompt and M5 role rules in agent.md. Work on branch feat/ms-061-refresh. Preserve unrelated changes.

EXPECTED INPUT
The package contracts for R05.04, R05.05, R11.02 and US-05.04, US-05.05, US-11.02; merged, tested outputs of MS-043, MS-047.
Strict prerequisites: MS-043 — Discovery stage graph and candidate persistence; MS-047 — Explicit evaluation API
Verify prerequisite interfaces exist before editing. A missing prerequisite is a blocker, not permission to build an incompatible stub.

READ AND RESPECT
Read requirements.md entries R05.04, R05.05, R11.02, userStory.md entries US-05.04, US-05.05, US-11.02, this sprint in sprints.md, relevant design.md invariants, API.md common conventions/DTOs and the operations listed below. Follow agent.md style, privacy, versioning, error and ownership rules.

WRITE SCOPE
backend/src/benefitbridge/sources/refresh.py; backend/src/benefitbridge/api/refresh.py.
Also edit only directly corresponding tests and mechanically regenerated OpenAPI/client files when affected. Shared domain, registry or migration changes outside this scope require an explicit owner handoff; do not silently expand the task.

IMPLEMENTATION AND EXPECTED OUTCOME
Queue explicit bounded refresh, compare hashes then semantic fields, create new versions only for changes and emit deduplicated invalidation outbox.
Implement only this unit. Produce the scoped typed implementation and its usable interface in the development composition. Production behavior must pass the specified checks.

API CONTRACT
- refresh_opportunity: POST /api/v1/opportunities/{opportunity_id}/refresh; auth=USER; success=202; idempotency=required; implement its exact request/response/validation in API.md.

ACCEPTANCE AND VERIFICATION
Unchanged source refresh updates fetch freshness only; failed fetch preserves last-known content.
Use deterministic synthetic fixtures and the injected clock/provider ports where relevant. Run targeted checks for these scenarios and the relevant available lint/type/contract gates from the Makefile. Do not call paid providers or fabricate measured results. Regenerate contracts if changed, and inspect the diff for unrelated edits.

HANDOFF
Return the implemented paths, behavior mapped to the requirement IDs, exact commands and actual outcomes, schema/config/API impact, unresolved blockers and reviewer focus. Default reviewer: M4. Leave production TODO placeholders out of the delivered behavior; if a required check could not run, state the reason and keep the completion gate unverified.
```

### MS-062 — Dependency invalidation handler

**Owner:** M1. **Reviewer:** M3. **Priority:** P0. **Estimate:** 3 hours.

**Expected input:** The package contracts for R02.04, R05.05, R11.02, R14.03 and US-02.04, US-05.05, US-11.02, US-14.03; merged, tested outputs of MS-052, MS-016, MS-061, MS-017.

**Blocked until:** MS-052 — Application and shortlist schema; MS-016 — Leased PostgreSQL job dispatcher; MS-061 — Source refresh and structural change detection; MS-017 — Versioned profile read and edit API

**Expected outcome:** Consume profile/evidence/source change outbox to mark affected evaluations/applications/drafts stale, clear acceptance and enqueue bounded reevaluations for saved items. Use conservative owner-wide fallback.

**Acceptance:** Repeated events are idempotent; global source change fans out through paginated jobs, never an unbounded transaction.

**Exact prompt:**

```text
Implement MS-062 — Dependency invalidation handler for BenefitBridge as M1.
Use the common system prompt and M1 role rules in agent.md. Work on branch feat/ms-062-invalidation. Preserve unrelated changes.

EXPECTED INPUT
The package contracts for R02.04, R05.05, R11.02, R14.03 and US-02.04, US-05.05, US-11.02, US-14.03; merged, tested outputs of MS-052, MS-016, MS-061, MS-017.
Strict prerequisites: MS-052 — Application and shortlist schema; MS-016 — Leased PostgreSQL job dispatcher; MS-061 — Source refresh and structural change detection; MS-017 — Versioned profile read and edit API
Verify prerequisite interfaces exist before editing. A missing prerequisite is a blocker, not permission to build an incompatible stub.

READ AND RESPECT
Read requirements.md entries R02.04, R05.05, R11.02, R14.03, userStory.md entries US-02.04, US-05.05, US-11.02, US-14.03, this sprint in sprints.md, relevant design.md invariants, API.md common conventions/DTOs and the operations listed below. Follow agent.md style, privacy, versioning, error and ownership rules.

WRITE SCOPE
backend/src/benefitbridge/invalidation.py.
Also edit only directly corresponding tests and mechanically regenerated OpenAPI/client files when affected. Shared domain, registry or migration changes outside this scope require an explicit owner handoff; do not silently expand the task.

IMPLEMENTATION AND EXPECTED OUTCOME
Consume profile/evidence/source change outbox to mark affected evaluations/applications/drafts stale, clear acceptance and enqueue bounded reevaluations for saved items. Use conservative owner-wide fallback.
Implement only this unit. Produce the scoped typed implementation and its usable interface in the development composition. Production behavior must pass the specified checks.

API CONTRACT
- No new public endpoint in this task. Preserve the documented API and expose only the internal interface required by dependent tasks.

ACCEPTANCE AND VERIFICATION
Repeated events are idempotent; global source change fans out through paginated jobs, never an unbounded transaction.
Use deterministic synthetic fixtures and the injected clock/provider ports where relevant. Run targeted checks for these scenarios and the relevant available lint/type/contract gates from the Makefile. Do not call paid providers or fabricate measured results. Regenerate contracts if changed, and inspect the diff for unrelated edits.

HANDOFF
Return the implemented paths, behavior mapped to the requirement IDs, exact commands and actual outcomes, schema/config/API impact, unresolved blockers and reviewer focus. Default reviewer: M3. Leave production TODO placeholders out of the delivered behavior; if a required check could not run, state the reason and keep the completion gate unverified.
```

### MS-063 — Document revoke and purge workflow

**Owner:** M5. **Reviewer:** M4. **Priority:** P0. **Estimate:** 3 hours.

**Expected input:** The package contracts for R03.05, R13.04 and US-03.05, US-13.04; merged, tested outputs of MS-062, MS-026, MS-016.

**Blocked until:** MS-062 — Dependency invalidation handler; MS-026 — Document upload and read API; MS-016 — Leased PostgreSQL job dispatcher

**Expected outcome:** Tombstone document synchronously; queue object/span/candidate purge and dependent fact support revocation. Retain a fact only if independently user-confirmed; otherwise remove it in a new profile version.

**Acceptance:** Signed download initiation fails immediately; old drafts/evidence reads are suppressed; purge retry is safe.

**Exact prompt:**

```text
Implement MS-063 — Document revoke and purge workflow for BenefitBridge as M5.
Use the common system prompt and M5 role rules in agent.md. Work on branch feat/ms-063-doc-delete. Preserve unrelated changes.

EXPECTED INPUT
The package contracts for R03.05, R13.04 and US-03.05, US-13.04; merged, tested outputs of MS-062, MS-026, MS-016.
Strict prerequisites: MS-062 — Dependency invalidation handler; MS-026 — Document upload and read API; MS-016 — Leased PostgreSQL job dispatcher
Verify prerequisite interfaces exist before editing. A missing prerequisite is a blocker, not permission to build an incompatible stub.

READ AND RESPECT
Read requirements.md entries R03.05, R13.04, userStory.md entries US-03.05, US-13.04, this sprint in sprints.md, relevant design.md invariants, API.md common conventions/DTOs and the operations listed below. Follow agent.md style, privacy, versioning, error and ownership rules.

WRITE SCOPE
backend/src/benefitbridge/documents/delete.py; backend/src/benefitbridge/api/document_delete.py.
Also edit only directly corresponding tests and mechanically regenerated OpenAPI/client files when affected. Shared domain, registry or migration changes outside this scope require an explicit owner handoff; do not silently expand the task.

IMPLEMENTATION AND EXPECTED OUTCOME
Tombstone document synchronously; queue object/span/candidate purge and dependent fact support revocation. Retain a fact only if independently user-confirmed; otherwise remove it in a new profile version.
Implement only this unit. Produce the scoped typed implementation and its usable interface in the development composition. Production behavior must pass the specified checks.

API CONTRACT
- delete_document: DELETE /api/v1/documents/{document_id}; auth=USER; success=202; idempotency=required; implement its exact request/response/validation in API.md.

ACCEPTANCE AND VERIFICATION
Signed download initiation fails immediately; old drafts/evidence reads are suppressed; purge retry is safe.
Use deterministic synthetic fixtures and the injected clock/provider ports where relevant. Run targeted checks for these scenarios and the relevant available lint/type/contract gates from the Makefile. Do not call paid providers or fabricate measured results. Regenerate contracts if changed, and inspect the diff for unrelated edits.

HANDOFF
Return the implemented paths, behavior mapped to the requirement IDs, exact commands and actual outcomes, schema/config/API impact, unresolved blockers and reviewer focus. Default reviewer: M4. Leave production TODO placeholders out of the delivered behavior; if a required check could not run, state the reason and keep the completion gate unverified.
```

### MS-064 — Account purge and capability receipt

**Owner:** M1. **Reviewer:** M3. **Priority:** P0. **Estimate:** 3 hours.

**Expected input:** The package contracts for R01.05, R13.04 and US-01.05, US-13.04; merged, tested outputs of MS-063, MS-008, MS-015.

**Blocked until:** MS-063 — Document revoke and purge workflow; MS-008 — JWT authentication and account API; MS-015 — Durable runs, outbox, budget and receipt schema

**Expected outcome:** Tombstone account, persist the subject-denial HMAC, cancel jobs, revoke private access and enqueue idempotent storage/DB/managed-auth purge. Return a one-time random receipt token; store only its hash and encrypted idempotent response. Receipt read uses no JWT.

**Acceptance:** Old JWTs fail; purge crash resumes; receipt cannot expose profile data or be used as an API token.

**Exact prompt:**

```text
Implement MS-064 — Account purge and capability receipt for BenefitBridge as M1.
Use the common system prompt and M1 role rules in agent.md. Work on branch feat/ms-064-account-delete. Preserve unrelated changes.

EXPECTED INPUT
The package contracts for R01.05, R13.04 and US-01.05, US-13.04; merged, tested outputs of MS-063, MS-008, MS-015.
Strict prerequisites: MS-063 — Document revoke and purge workflow; MS-008 — JWT authentication and account API; MS-015 — Durable runs, outbox, budget and receipt schema
Verify prerequisite interfaces exist before editing. A missing prerequisite is a blocker, not permission to build an incompatible stub.

READ AND RESPECT
Read requirements.md entries R01.05, R13.04, userStory.md entries US-01.05, US-13.04, this sprint in sprints.md, relevant design.md invariants, API.md common conventions/DTOs and the operations listed below. Follow agent.md style, privacy, versioning, error and ownership rules.

WRITE SCOPE
backend/src/benefitbridge/accounts/delete.py; backend/src/benefitbridge/api/account_delete.py.
Also edit only directly corresponding tests and mechanically regenerated OpenAPI/client files when affected. Shared domain, registry or migration changes outside this scope require an explicit owner handoff; do not silently expand the task.

IMPLEMENTATION AND EXPECTED OUTCOME
Tombstone account, persist the subject-denial HMAC, cancel jobs, revoke private access and enqueue idempotent storage/DB/managed-auth purge. Return a one-time random receipt token; store only its hash and encrypted idempotent response. Receipt read uses no JWT.
Implement only this unit. Produce the scoped typed implementation and its usable interface in the development composition. Production behavior must pass the specified checks.

API CONTRACT
- delete_account: DELETE /api/v1/me; auth=USER; success=202; idempotency=required; implement its exact request/response/validation in API.md.
- get_deletion_receipt: GET /api/v1/deletion-receipts/{receipt_id}; auth=RECEIPT; success=200; idempotency=as specified; implement its exact request/response/validation in API.md.

ACCEPTANCE AND VERIFICATION
Old JWTs fail; purge crash resumes; receipt cannot expose profile data or be used as an API token.
Use deterministic synthetic fixtures and the injected clock/provider ports where relevant. Run targeted checks for these scenarios and the relevant available lint/type/contract gates from the Makefile. Do not call paid providers or fabricate measured results. Regenerate contracts if changed, and inspect the diff for unrelated edits.

HANDOFF
Return the implemented paths, behavior mapped to the requirement IDs, exact commands and actual outcomes, schema/config/API impact, unresolved blockers and reviewer focus. Default reviewer: M3. Leave production TODO placeholders out of the delivered behavior; if a required check could not run, state the reason and keep the completion gate unverified.
```

### MS-065 — Two-tenant and deletion security suite

**Owner:** M6. **Reviewer:** M4. **Priority:** P0. **Estimate:** 3 hours.

**Expected input:** The package contracts for R13.01, R13.02, R13.03, R13.04, R13.05, R15.05 and US-13.01, US-13.02, US-13.03, US-13.04, US-13.05, US-15.05; merged, tested outputs of MS-064, MS-059, MS-050, MS-030.

**Blocked until:** MS-064 — Account purge and capability receipt; MS-059 — Draft versions, review and export API; MS-050 — Clarification persistence and resumption; MS-030 — Run control and authenticated event stream

**Expected outcome:** Exercise every private endpoint with two real synthetic tenants, RLS SQL access, streams, exports, cache and evidence IDs. Include tombstone versus in-flight worker race.

**Acceptance:** Any cross-owner success or post-tombstone private publication fails release.

**Exact prompt:**

```text
Implement MS-065 — Two-tenant and deletion security suite for BenefitBridge as M6.
Use the common system prompt and M6 role rules in agent.md. Work on branch feat/ms-065-isolation-suite. Preserve unrelated changes.

EXPECTED INPUT
The package contracts for R13.01, R13.02, R13.03, R13.04, R13.05, R15.05 and US-13.01, US-13.02, US-13.03, US-13.04, US-13.05, US-15.05; merged, tested outputs of MS-064, MS-059, MS-050, MS-030.
Strict prerequisites: MS-064 — Account purge and capability receipt; MS-059 — Draft versions, review and export API; MS-050 — Clarification persistence and resumption; MS-030 — Run control and authenticated event stream
Verify prerequisite interfaces exist before editing. A missing prerequisite is a blocker, not permission to build an incompatible stub.

READ AND RESPECT
Read requirements.md entries R13.01, R13.02, R13.03, R13.04, R13.05, R15.05, userStory.md entries US-13.01, US-13.02, US-13.03, US-13.04, US-13.05, US-15.05, this sprint in sprints.md, relevant design.md invariants, API.md common conventions/DTOs and the operations listed below. Follow agent.md style, privacy, versioning, error and ownership rules.

WRITE SCOPE
tests/security/test_isolation.py; tests/security/test_deletion.py.
Also edit only directly corresponding tests and mechanically regenerated OpenAPI/client files when affected. Shared domain, registry or migration changes outside this scope require an explicit owner handoff; do not silently expand the task.

IMPLEMENTATION AND EXPECTED OUTCOME
Exercise every private endpoint with two real synthetic tenants, RLS SQL access, streams, exports, cache and evidence IDs. Include tombstone versus in-flight worker race.
Implement only this unit. Produce the scoped typed implementation and its usable interface in the development composition. Production behavior must pass the specified checks.

API CONTRACT
- No new public endpoint in this task. Preserve the documented API and expose only the internal interface required by dependent tasks.

ACCEPTANCE AND VERIFICATION
Any cross-owner success or post-tombstone private publication fails release.
Use deterministic synthetic fixtures and the injected clock/provider ports where relevant. Run targeted checks for these scenarios and the relevant available lint/type/contract gates from the Makefile. Do not call paid providers or fabricate measured results. Regenerate contracts if changed, and inspect the diff for unrelated edits.

HANDOFF
Return the implemented paths, behavior mapped to the requirement IDs, exact commands and actual outcomes, schema/config/API impact, unresolved blockers and reviewer focus. Default reviewer: M4. Leave production TODO placeholders out of the delivered behavior; if a required check could not run, state the reason and keep the completion gate unverified.
```

### MS-066 — Failure and concurrency recovery suite

**Owner:** M6. **Reviewer:** M4. **Priority:** P0. **Estimate:** 3 hours.

**Expected input:** The package contracts for R10.01, R10.03, R10.04, R14.01, R15.05 and US-10.01, US-10.03, US-10.04, US-14.01, US-15.05; merged, tested outputs of MS-044, MS-064, MS-019.

**Blocked until:** MS-044 — Evaluation workflow stage; MS-064 — Account purge and capability receipt; MS-019 — Atomic cost reservations and fairness

**Expected outcome:** Inject provider 429/timeouts, worker death, duplicate jobs, DB rollback, stale lease completion and concurrent version updates. Verify artifact identity and budget reconciliation.

**Acceptance:** Every accepted run reaches recoverable or terminal state; no duplicate visible writes or uncharged retry loops.

**Exact prompt:**

```text
Implement MS-066 — Failure and concurrency recovery suite for BenefitBridge as M6.
Use the common system prompt and M6 role rules in agent.md. Work on branch feat/ms-066-failure-suite. Preserve unrelated changes.

EXPECTED INPUT
The package contracts for R10.01, R10.03, R10.04, R14.01, R15.05 and US-10.01, US-10.03, US-10.04, US-14.01, US-15.05; merged, tested outputs of MS-044, MS-064, MS-019.
Strict prerequisites: MS-044 — Evaluation workflow stage; MS-064 — Account purge and capability receipt; MS-019 — Atomic cost reservations and fairness
Verify prerequisite interfaces exist before editing. A missing prerequisite is a blocker, not permission to build an incompatible stub.

READ AND RESPECT
Read requirements.md entries R10.01, R10.03, R10.04, R14.01, R15.05, userStory.md entries US-10.01, US-10.03, US-10.04, US-14.01, US-15.05, this sprint in sprints.md, relevant design.md invariants, API.md common conventions/DTOs and the operations listed below. Follow agent.md style, privacy, versioning, error and ownership rules.

WRITE SCOPE
tests/integration/test_recovery.py.
Also edit only directly corresponding tests and mechanically regenerated OpenAPI/client files when affected. Shared domain, registry or migration changes outside this scope require an explicit owner handoff; do not silently expand the task.

IMPLEMENTATION AND EXPECTED OUTCOME
Inject provider 429/timeouts, worker death, duplicate jobs, DB rollback, stale lease completion and concurrent version updates. Verify artifact identity and budget reconciliation.
Implement only this unit. Produce the scoped typed implementation and its usable interface in the development composition. Production behavior must pass the specified checks.

API CONTRACT
- No new public endpoint in this task. Preserve the documented API and expose only the internal interface required by dependent tasks.

ACCEPTANCE AND VERIFICATION
Every accepted run reaches recoverable or terminal state; no duplicate visible writes or uncharged retry loops.
Use deterministic synthetic fixtures and the injected clock/provider ports where relevant. Run targeted checks for these scenarios and the relevant available lint/type/contract gates from the Makefile. Do not call paid providers or fabricate measured results. Regenerate contracts if changed, and inspect the diff for unrelated edits.

HANDOFF
Return the implemented paths, behavior mapped to the requirement IDs, exact commands and actual outcomes, schema/config/API impact, unresolved blockers and reviewer focus. Default reviewer: M4. Leave production TODO placeholders out of the delivered behavior; if a required check could not run, state the reason and keep the completion gate unverified.
```

### MS-067 — Public reuse and private cache invalidation

**Owner:** M3. **Reviewer:** M1. **Priority:** P0. **Estimate:** 2.5 hours.

**Expected input:** The package contracts for R14.03 and US-14.03; merged, tested outputs of MS-062, MS-044, MS-019.

**Blocked until:** MS-062 — Dependency invalidation handler; MS-044 — Evaluation workflow stage; MS-019 — Atomic cost reservations and fairness

**Expected outcome:** Implement immutable public source/parse reuse and owner-scoped decision keys including all versions and valid_until. Store no shared personal prompt completions.

**Acceptance:** Profile/source/deadline changes invalidate keys; two users never share private evaluation payloads.

**Exact prompt:**

```text
Implement MS-067 — Public reuse and private cache invalidation for BenefitBridge as M3.
Use the common system prompt and M3 role rules in agent.md. Work on branch feat/ms-067-cache. Preserve unrelated changes.

EXPECTED INPUT
The package contracts for R14.03 and US-14.03; merged, tested outputs of MS-062, MS-044, MS-019.
Strict prerequisites: MS-062 — Dependency invalidation handler; MS-044 — Evaluation workflow stage; MS-019 — Atomic cost reservations and fairness
Verify prerequisite interfaces exist before editing. A missing prerequisite is a blocker, not permission to build an incompatible stub.

READ AND RESPECT
Read requirements.md entries R14.03, userStory.md entries US-14.03, this sprint in sprints.md, relevant design.md invariants, API.md common conventions/DTOs and the operations listed below. Follow agent.md style, privacy, versioning, error and ownership rules.

WRITE SCOPE
backend/src/benefitbridge/cache.py; tests/integration/test_cache.py.
Also edit only directly corresponding tests and mechanically regenerated OpenAPI/client files when affected. Shared domain, registry or migration changes outside this scope require an explicit owner handoff; do not silently expand the task.

IMPLEMENTATION AND EXPECTED OUTCOME
Implement immutable public source/parse reuse and owner-scoped decision keys including all versions and valid_until. Store no shared personal prompt completions.
Implement only this unit. Produce the scoped typed implementation and its usable interface in the development composition. Production behavior must pass the specified checks.

API CONTRACT
- No new public endpoint in this task. Preserve the documented API and expose only the internal interface required by dependent tasks.

ACCEPTANCE AND VERIFICATION
Profile/source/deadline changes invalidate keys; two users never share private evaluation payloads.
Use deterministic synthetic fixtures and the injected clock/provider ports where relevant. Run targeted checks for these scenarios and the relevant available lint/type/contract gates from the Makefile. Do not call paid providers or fabricate measured results. Regenerate contracts if changed, and inspect the diff for unrelated edits.

HANDOFF
Return the implemented paths, behavior mapped to the requirement IDs, exact commands and actual outcomes, schema/config/API impact, unresolved blockers and reviewer focus. Default reviewer: M1. Leave production TODO placeholders out of the delivered behavior; if a required check could not run, state the reason and keep the completion gate unverified.
```

### MS-068 — Usage and capability read endpoints

**Owner:** M3. **Reviewer:** M1. **Priority:** P0. **Estimate:** 2.5 hours.

**Expected input:** The package contracts for R14.01, R14.02, R14.04 and US-14.01, US-14.02, US-14.04; merged, tested outputs of MS-019, MS-008, MS-010.

**Blocked until:** MS-019 — Atomic cost reservations and fairness; MS-008 — JWT authentication and account API; MS-010 — Model registry and capability preflight

**Expected outcome:** Expose user budget/actual/reserved usage, nonsecret deployment capabilities and disabled feature flags.

**Acceptance:** User cannot query another ledger; registry secrets/prices not intended for UI are not exposed.

**Exact prompt:**

```text
Implement MS-068 — Usage and capability read endpoints for BenefitBridge as M3.
Use the common system prompt and M3 role rules in agent.md. Work on branch feat/ms-068-usage-api. Preserve unrelated changes.

EXPECTED INPUT
The package contracts for R14.01, R14.02, R14.04 and US-14.01, US-14.02, US-14.04; merged, tested outputs of MS-019, MS-008, MS-010.
Strict prerequisites: MS-019 — Atomic cost reservations and fairness; MS-008 — JWT authentication and account API; MS-010 — Model registry and capability preflight
Verify prerequisite interfaces exist before editing. A missing prerequisite is a blocker, not permission to build an incompatible stub.

READ AND RESPECT
Read requirements.md entries R14.01, R14.02, R14.04, userStory.md entries US-14.01, US-14.02, US-14.04, this sprint in sprints.md, relevant design.md invariants, API.md common conventions/DTOs and the operations listed below. Follow agent.md style, privacy, versioning, error and ownership rules.

WRITE SCOPE
backend/src/benefitbridge/api/usage.py.
Also edit only directly corresponding tests and mechanically regenerated OpenAPI/client files when affected. Shared domain, registry or migration changes outside this scope require an explicit owner handoff; do not silently expand the task.

IMPLEMENTATION AND EXPECTED OUTCOME
Expose user budget/actual/reserved usage, nonsecret deployment capabilities and disabled feature flags.
Implement only this unit. Produce the scoped typed implementation and its usable interface in the development composition. Production behavior must pass the specified checks.

API CONTRACT
- get_usage: GET /api/v1/usage; auth=USER; success=200; idempotency=as specified; implement its exact request/response/validation in API.md.
- get_capabilities: GET /api/v1/capabilities; auth=PUBLIC; success=200; idempotency=as specified; implement its exact request/response/validation in API.md.

ACCEPTANCE AND VERIFICATION
User cannot query another ledger; registry secrets/prices not intended for UI are not exposed.
Use deterministic synthetic fixtures and the injected clock/provider ports where relevant. Run targeted checks for these scenarios and the relevant available lint/type/contract gates from the Makefile. Do not call paid providers or fabricate measured results. Regenerate contracts if changed, and inspect the diff for unrelated edits.

HANDOFF
Return the implemented paths, behavior mapped to the requirement IDs, exact commands and actual outcomes, schema/config/API impact, unresolved blockers and reviewer focus. Default reviewer: M1. Leave production TODO placeholders out of the delivered behavior; if a required check could not run, state the reason and keep the completion gate unverified.
```

### MS-069 — Usage, settings and deletion controls

**Owner:** M2. **Reviewer:** M6. **Priority:** P0. **Estimate:** 2.5 hours.

**Expected input:** The package contracts for R01.04, R01.05, R13.04, R14.01 and US-01.04, US-01.05, US-13.04, US-14.01; merged, tested outputs of MS-068, MS-064, MS-060.

**Blocked until:** MS-068 — Usage and capability read endpoints; MS-064 — Account purge and capability receipt; MS-060 — Application preparation workspace

**Expected outcome:** Show relevant usage limits, timezone/profile privacy, document/account deletion and copyable receipt. Confirm irreversible account deletion with exact DELETE text.

**Acceptance:** After tombstone local auth state is cleared; receipt status works without account session.

**Exact prompt:**

```text
Implement MS-069 — Usage, settings and deletion controls for BenefitBridge as M2.
Use the common system prompt and M2 role rules in agent.md. Work on branch feat/ms-069-ops-ui. Preserve unrelated changes.

EXPECTED INPUT
The package contracts for R01.04, R01.05, R13.04, R14.01 and US-01.04, US-01.05, US-13.04, US-14.01; merged, tested outputs of MS-068, MS-064, MS-060.
Strict prerequisites: MS-068 — Usage and capability read endpoints; MS-064 — Account purge and capability receipt; MS-060 — Application preparation workspace
Verify prerequisite interfaces exist before editing. A missing prerequisite is a blocker, not permission to build an incompatible stub.

READ AND RESPECT
Read requirements.md entries R01.04, R01.05, R13.04, R14.01, userStory.md entries US-01.04, US-01.05, US-13.04, US-14.01, this sprint in sprints.md, relevant design.md invariants, API.md common conventions/DTOs and the operations listed below. Follow agent.md style, privacy, versioning, error and ownership rules.

WRITE SCOPE
frontend/src/features/settings/.
Also edit only directly corresponding tests and mechanically regenerated OpenAPI/client files when affected. Shared domain, registry or migration changes outside this scope require an explicit owner handoff; do not silently expand the task.

IMPLEMENTATION AND EXPECTED OUTCOME
Show relevant usage limits, timezone/profile privacy, document/account deletion and copyable receipt. Confirm irreversible account deletion with exact DELETE text.
Implement only this unit. Produce the scoped typed implementation and its usable interface in the development composition. Production behavior must pass the specified checks.

API CONTRACT
- No new public endpoint in this task. Preserve the documented API and expose only the internal interface required by dependent tasks.

ACCEPTANCE AND VERIFICATION
After tombstone local auth state is cleared; receipt status works without account session.
Use deterministic synthetic fixtures and the injected clock/provider ports where relevant. Run targeted checks for these scenarios and the relevant available lint/type/contract gates from the Makefile. Do not call paid providers or fabricate measured results. Regenerate contracts if changed, and inspect the diff for unrelated edits.

HANDOFF
Return the implemented paths, behavior mapped to the requirement IDs, exact commands and actual outcomes, schema/config/API impact, unresolved blockers and reviewer focus. Default reviewer: M6. Leave production TODO placeholders out of the delivered behavior; if a required check could not run, state the reason and keep the completion gate unverified.
```

### MS-070 — Optional watch persistence

**Owner:** M1. **Reviewer:** M3. **Priority:** P1. **Estimate:** 2.5 hours.

**Expected input:** The package contracts for R11.03, R11.04, R11.05 and US-11.03, US-11.04, US-11.05; merged, tested outputs of MS-052.

**Blocked until:** MS-052 — Application and shortlist schema

**Expected outcome:** Add watches and notifications with owner FK, cadence, pause, next_due and unique version-change keys. Always ship schema safely; feature remains disabled unless enabled.

**Acceptance:** P0 behavior unchanged when flag off; duplicate notifications blocked.

**Exact prompt:**

```text
Implement MS-070 — Optional watch persistence for BenefitBridge as M1.
This is P1. Start only after the P0 release gates pass, watch is explicitly selected, and all listed prerequisites are merged. Keep the feature disabled by default.
Use the common system prompt and M1 role rules in agent.md. Work on branch feat/ms-070-watch-schema. Preserve unrelated changes.

EXPECTED INPUT
The package contracts for R11.03, R11.04, R11.05 and US-11.03, US-11.04, US-11.05; merged, tested outputs of MS-052.
Strict prerequisites: MS-052 — Application and shortlist schema
Verify prerequisite interfaces exist before editing. A missing prerequisite is a blocker, not permission to build an incompatible stub.

READ AND RESPECT
Read requirements.md entries R11.03, R11.04, R11.05, userStory.md entries US-11.03, US-11.04, US-11.05, this sprint in sprints.md, relevant design.md invariants, API.md common conventions/DTOs and the operations listed below. Follow agent.md style, privacy, versioning, error and ownership rules.

WRITE SCOPE
backend/migrations/versions/0007_watch.py; backend/src/benefitbridge/db/watch.py.
Also edit only directly corresponding tests and mechanically regenerated OpenAPI/client files when affected. Shared domain, registry or migration changes outside this scope require an explicit owner handoff; do not silently expand the task.

IMPLEMENTATION AND EXPECTED OUTCOME
Add watches and notifications with owner FK, cadence, pause, next_due and unique version-change keys. Always ship schema safely; feature remains disabled unless enabled.
Implement only this unit. Produce the scoped typed implementation and its usable interface in the development composition. Production behavior must pass the specified checks.

API CONTRACT
- No new public endpoint in this task. Preserve the documented API and expose only the internal interface required by dependent tasks.

ACCEPTANCE AND VERIFICATION
P0 behavior unchanged when flag off; duplicate notifications blocked.
Use deterministic synthetic fixtures and the injected clock/provider ports where relevant. Run targeted checks for these scenarios and the relevant available lint/type/contract gates from the Makefile. Do not call paid providers or fabricate measured results. Regenerate contracts if changed, and inspect the diff for unrelated edits.

HANDOFF
Return the implemented paths, behavior mapped to the requirement IDs, exact commands and actual outcomes, schema/config/API impact, unresolved blockers and reviewer focus. Default reviewer: M3. Leave production TODO placeholders out of the delivered behavior; if a required check could not run, state the reason and keep the completion gate unverified.
```

### MS-071 — Optional saved-page watch scheduler

**Owner:** M5. **Reviewer:** M4. **Priority:** P1. **Estimate:** 2.5 hours.

**Expected input:** The package contracts for R11.03, R11.04, R11.05 and US-11.03, US-11.04, US-11.05; merged, tested outputs of MS-070, MS-061, MS-062.

**Blocked until:** MS-070 — Optional watch persistence; MS-061 — Source refresh and structural change detection; MS-062 — Dependency invalidation handler

**Expected outcome:** Poll only due enabled saved-page watches with shared-source deduplication, quotas and paginated fanout. Emit in-app notification after material version change.

**Acceptance:** Paused watches do not queue; unchanged content produces none; source failure yields status not false closure.

**Exact prompt:**

```text
Implement MS-071 — Optional saved-page watch scheduler for BenefitBridge as M5.
This is P1. Start only after the P0 release gates pass, watch is explicitly selected, and all listed prerequisites are merged. Keep the feature disabled by default.
Use the common system prompt and M5 role rules in agent.md. Work on branch feat/ms-071-watch. Preserve unrelated changes.

EXPECTED INPUT
The package contracts for R11.03, R11.04, R11.05 and US-11.03, US-11.04, US-11.05; merged, tested outputs of MS-070, MS-061, MS-062.
Strict prerequisites: MS-070 — Optional watch persistence; MS-061 — Source refresh and structural change detection; MS-062 — Dependency invalidation handler
Verify prerequisite interfaces exist before editing. A missing prerequisite is a blocker, not permission to build an incompatible stub.

READ AND RESPECT
Read requirements.md entries R11.03, R11.04, R11.05, userStory.md entries US-11.03, US-11.04, US-11.05, this sprint in sprints.md, relevant design.md invariants, API.md common conventions/DTOs and the operations listed below. Follow agent.md style, privacy, versioning, error and ownership rules.

WRITE SCOPE
backend/src/benefitbridge/watch/scheduler.py.
Also edit only directly corresponding tests and mechanically regenerated OpenAPI/client files when affected. Shared domain, registry or migration changes outside this scope require an explicit owner handoff; do not silently expand the task.

IMPLEMENTATION AND EXPECTED OUTCOME
Poll only due enabled saved-page watches with shared-source deduplication, quotas and paginated fanout. Emit in-app notification after material version change.
Implement only this unit. Produce the scoped typed implementation and its usable interface in the development composition. Production behavior must pass the specified checks.

API CONTRACT
- No new public endpoint in this task. Preserve the documented API and expose only the internal interface required by dependent tasks.

ACCEPTANCE AND VERIFICATION
Paused watches do not queue; unchanged content produces none; source failure yields status not false closure.
Use deterministic synthetic fixtures and the injected clock/provider ports where relevant. Run targeted checks for these scenarios and the relevant available lint/type/contract gates from the Makefile. Do not call paid providers or fabricate measured results. Regenerate contracts if changed, and inspect the diff for unrelated edits.

HANDOFF
Return the implemented paths, behavior mapped to the requirement IDs, exact commands and actual outcomes, schema/config/API impact, unresolved blockers and reviewer focus. Default reviewer: M4. Leave production TODO placeholders out of the delivered behavior; if a required check could not run, state the reason and keep the completion gate unverified.
```

### MS-072 — Optional watch and notification API

**Owner:** M5. **Reviewer:** M4. **Priority:** P1. **Estimate:** 2.5 hours.

**Expected input:** The package contracts for R11.03, R11.04, R11.05 and US-11.03, US-11.04, US-11.05; merged, tested outputs of MS-071, MS-008.

**Blocked until:** MS-071 — Optional saved-page watch scheduler; MS-008 — JWT authentication and account API

**Expected outcome:** Implement flag-gated watch CRUD and notification list/read using revision guards and owner checks.

**Acceptance:** Disabled feature returns FEATURE_DISABLED; another owner ID returns 404.

**Exact prompt:**

```text
Implement MS-072 — Optional watch and notification API for BenefitBridge as M5.
This is P1. Start only after the P0 release gates pass, watch is explicitly selected, and all listed prerequisites are merged. Keep the feature disabled by default.
Use the common system prompt and M5 role rules in agent.md. Work on branch feat/ms-072-watch-api. Preserve unrelated changes.

EXPECTED INPUT
The package contracts for R11.03, R11.04, R11.05 and US-11.03, US-11.04, US-11.05; merged, tested outputs of MS-071, MS-008.
Strict prerequisites: MS-071 — Optional saved-page watch scheduler; MS-008 — JWT authentication and account API
Verify prerequisite interfaces exist before editing. A missing prerequisite is a blocker, not permission to build an incompatible stub.

READ AND RESPECT
Read requirements.md entries R11.03, R11.04, R11.05, userStory.md entries US-11.03, US-11.04, US-11.05, this sprint in sprints.md, relevant design.md invariants, API.md common conventions/DTOs and the operations listed below. Follow agent.md style, privacy, versioning, error and ownership rules.

WRITE SCOPE
backend/src/benefitbridge/api/watch.py.
Also edit only directly corresponding tests and mechanically regenerated OpenAPI/client files when affected. Shared domain, registry or migration changes outside this scope require an explicit owner handoff; do not silently expand the task.

IMPLEMENTATION AND EXPECTED OUTCOME
Implement flag-gated watch CRUD and notification list/read using revision guards and owner checks.
Implement only this unit. Produce the scoped typed implementation and its usable interface in the development composition. Production behavior must pass the specified checks.

API CONTRACT
- list_watches: GET /api/v1/watches; auth=USER; success=200; idempotency=as specified; implement its exact request/response/validation in API.md.
- create_watch: POST /api/v1/watches; auth=USER; success=201; idempotency=required; implement its exact request/response/validation in API.md.
- patch_watch: PATCH /api/v1/watches/{watch_id}; auth=USER; success=200; idempotency=required; implement its exact request/response/validation in API.md.
- delete_watch: DELETE /api/v1/watches/{watch_id}; auth=USER; success=204; idempotency=as specified; implement its exact request/response/validation in API.md.
- list_notifications: GET /api/v1/notifications; auth=USER; success=200; idempotency=as specified; implement its exact request/response/validation in API.md.
- read_notification: PUT /api/v1/notifications/{notification_id}/read; auth=USER; success=200; idempotency=as specified; implement its exact request/response/validation in API.md.

ACCEPTANCE AND VERIFICATION
Disabled feature returns FEATURE_DISABLED; another owner ID returns 404.
Use deterministic synthetic fixtures and the injected clock/provider ports where relevant. Run targeted checks for these scenarios and the relevant available lint/type/contract gates from the Makefile. Do not call paid providers or fabricate measured results. Regenerate contracts if changed, and inspect the diff for unrelated edits.

HANDOFF
Return the implemented paths, behavior mapped to the requirement IDs, exact commands and actual outcomes, schema/config/API impact, unresolved blockers and reviewer focus. Default reviewer: M4. Leave production TODO placeholders out of the delivered behavior; if a required check could not run, state the reason and keep the completion gate unverified.
```

### MS-073 — Optional watch controls and notification inbox

**Owner:** M2. **Reviewer:** M6. **Priority:** P1. **Estimate:** 2.5 hours.

**Expected input:** The package contracts for R11.03, R11.04, R11.05 and US-11.03, US-11.04, US-11.05; merged, tested outputs of MS-072, MS-054.

**Blocked until:** MS-072 — Optional watch and notification API; MS-054 — Shortlist screen

**Expected outcome:** Add cadence/pause controls and notifications only when capabilities enable watch.

**Acceptance:** Hidden feature has no live requests; read state and pause survive reload.

**Exact prompt:**

```text
Implement MS-073 — Optional watch controls and notification inbox for BenefitBridge as M2.
This is P1. Start only after the P0 release gates pass, watch is explicitly selected, and all listed prerequisites are merged. Keep the feature disabled by default.
Use the common system prompt and M2 role rules in agent.md. Work on branch feat/ms-073-watch-ui. Preserve unrelated changes.

EXPECTED INPUT
The package contracts for R11.03, R11.04, R11.05 and US-11.03, US-11.04, US-11.05; merged, tested outputs of MS-072, MS-054.
Strict prerequisites: MS-072 — Optional watch and notification API; MS-054 — Shortlist screen
Verify prerequisite interfaces exist before editing. A missing prerequisite is a blocker, not permission to build an incompatible stub.

READ AND RESPECT
Read requirements.md entries R11.03, R11.04, R11.05, userStory.md entries US-11.03, US-11.04, US-11.05, this sprint in sprints.md, relevant design.md invariants, API.md common conventions/DTOs and the operations listed below. Follow agent.md style, privacy, versioning, error and ownership rules.

WRITE SCOPE
frontend/src/features/watch/.
Also edit only directly corresponding tests and mechanically regenerated OpenAPI/client files when affected. Shared domain, registry or migration changes outside this scope require an explicit owner handoff; do not silently expand the task.

IMPLEMENTATION AND EXPECTED OUTCOME
Add cadence/pause controls and notifications only when capabilities enable watch.
Implement only this unit. Produce the scoped typed implementation and its usable interface in the development composition. Production behavior must pass the specified checks.

API CONTRACT
- No new public endpoint in this task. Preserve the documented API and expose only the internal interface required by dependent tasks.

ACCEPTANCE AND VERIFICATION
Hidden feature has no live requests; read state and pause survive reload.
Use deterministic synthetic fixtures and the injected clock/provider ports where relevant. Run targeted checks for these scenarios and the relevant available lint/type/contract gates from the Makefile. Do not call paid providers or fabricate measured results. Regenerate contracts if changed, and inspect the diff for unrelated edits.

HANDOFF
Return the implemented paths, behavior mapped to the requirement IDs, exact commands and actual outcomes, schema/config/API impact, unresolved blockers and reviewer focus. Default reviewer: M6. Leave production TODO placeholders out of the delivered behavior; if a required check could not run, state the reason and keep the completion gate unverified.
```

### MS-074 — Redacted operational metrics and health

**Owner:** M3. **Reviewer:** M1. **Priority:** P0. **Estimate:** 2.5 hours.

**Expected input:** The package contracts for R13.05, R14.04 and US-13.05, US-14.04; merged, tested outputs of MS-016, MS-010, MS-067, MS-068.

**Blocked until:** MS-016 — Leased PostgreSQL job dispatcher; MS-010 — Model registry and capability preflight; MS-067 — Public reuse and private cache invalidation; MS-068 — Usage and capability read endpoints

**Expected outcome:** Expose liveness/readiness, queue lag, stage failure, cost and invalidation metrics; configure low-frequency synthetic checks separately from probes.

**Acceptance:** No PII canaries in logs; readiness detects DB/worker/config failures without paid calls.

**Exact prompt:**

```text
Implement MS-074 — Redacted operational metrics and health for BenefitBridge as M3.
Use the common system prompt and M3 role rules in agent.md. Work on branch feat/ms-074-alerts. Preserve unrelated changes.

EXPECTED INPUT
The package contracts for R13.05, R14.04 and US-13.05, US-14.04; merged, tested outputs of MS-016, MS-010, MS-067, MS-068.
Strict prerequisites: MS-016 — Leased PostgreSQL job dispatcher; MS-010 — Model registry and capability preflight; MS-067 — Public reuse and private cache invalidation; MS-068 — Usage and capability read endpoints
Verify prerequisite interfaces exist before editing. A missing prerequisite is a blocker, not permission to build an incompatible stub.

READ AND RESPECT
Read requirements.md entries R13.05, R14.04, userStory.md entries US-13.05, US-14.04, this sprint in sprints.md, relevant design.md invariants, API.md common conventions/DTOs and the operations listed below. Follow agent.md style, privacy, versioning, error and ownership rules.

WRITE SCOPE
backend/src/benefitbridge/observability.py; backend/src/benefitbridge/api/health.py.
Also edit only directly corresponding tests and mechanically regenerated OpenAPI/client files when affected. Shared domain, registry or migration changes outside this scope require an explicit owner handoff; do not silently expand the task.

IMPLEMENTATION AND EXPECTED OUTCOME
Expose liveness/readiness, queue lag, stage failure, cost and invalidation metrics; configure low-frequency synthetic checks separately from probes.
Implement only this unit. Produce the scoped typed implementation and its usable interface in the development composition. Production behavior must pass the specified checks.

API CONTRACT
- health_live: GET /api/v1/health/live; auth=PUBLIC; success=200; idempotency=as specified; implement its exact request/response/validation in API.md.
- health_ready: GET /api/v1/health/ready; auth=PUBLIC; success=200; idempotency=as specified; implement its exact request/response/validation in API.md.

ACCEPTANCE AND VERIFICATION
No PII canaries in logs; readiness detects DB/worker/config failures without paid calls.
Use deterministic synthetic fixtures and the injected clock/provider ports where relevant. Run targeted checks for these scenarios and the relevant available lint/type/contract gates from the Makefile. Do not call paid providers or fabricate measured results. Regenerate contracts if changed, and inspect the diff for unrelated edits.

HANDOFF
Return the implemented paths, behavior mapped to the requirement IDs, exact commands and actual outcomes, schema/config/API impact, unresolved blockers and reviewer focus. Default reviewer: M1. Leave production TODO placeholders out of the delivered behavior; if a required check could not run, state the reason and keep the completion gate unverified.
```

### MS-075 — Production dependency composition

**Owner:** M3. **Reviewer:** M1. **Priority:** P0. **Estimate:** 3 hours.

**Expected input:** The package contracts for R16.01, R16.03 and US-16.01, US-16.03; merged, tested outputs of MS-074, MS-046, MS-050, MS-059, MS-064, MS-027, MS-061.

**Blocked until:** MS-074 — Redacted operational metrics and health; MS-046 — Discovery and URL-import commands; MS-050 — Clarification persistence and resumption; MS-059 — Draft versions, review and export API; MS-064 — Account purge and capability receipt; MS-027 — PDF to reviewable fact candidates; MS-061 — Source refresh and structural change detection

**Expected outcome:** Bind every P0 router/provider/stage to real configured dependencies; require explicit test mode for fakes. Include DEMO_RESET interface registration with disabled-until-installed behavior.

**Acceptance:** Startup identifies missing P0 dependencies; ordinary request and worker processes use the same schemas.

**Exact prompt:**

```text
Implement MS-075 — Production dependency composition for BenefitBridge as M3.
Use the common system prompt and M3 role rules in agent.md. Work on branch feat/ms-075-runtime-comp. Preserve unrelated changes.

EXPECTED INPUT
The package contracts for R16.01, R16.03 and US-16.01, US-16.03; merged, tested outputs of MS-074, MS-046, MS-050, MS-059, MS-064, MS-027, MS-061.
Strict prerequisites: MS-074 — Redacted operational metrics and health; MS-046 — Discovery and URL-import commands; MS-050 — Clarification persistence and resumption; MS-059 — Draft versions, review and export API; MS-064 — Account purge and capability receipt; MS-027 — PDF to reviewable fact candidates; MS-061 — Source refresh and structural change detection
Verify prerequisite interfaces exist before editing. A missing prerequisite is a blocker, not permission to build an incompatible stub.

READ AND RESPECT
Read requirements.md entries R16.01, R16.03, userStory.md entries US-16.01, US-16.03, this sprint in sprints.md, relevant design.md invariants, API.md common conventions/DTOs and the operations listed below. Follow agent.md style, privacy, versioning, error and ownership rules.

WRITE SCOPE
backend/src/benefitbridge/composition.py; backend/src/benefitbridge/api/registry.py; backend/src/benefitbridge/workflows/registry.py.
Also edit only directly corresponding tests and mechanically regenerated OpenAPI/client files when affected. Shared domain, registry or migration changes outside this scope require an explicit owner handoff; do not silently expand the task.

IMPLEMENTATION AND EXPECTED OUTCOME
Bind every P0 router/provider/stage to real configured dependencies; require explicit test mode for fakes. Include DEMO_RESET interface registration with disabled-until-installed behavior.
Implement only this unit. Produce the scoped typed implementation and its usable interface in the development composition. Production behavior must pass the specified checks.

API CONTRACT
- No new public endpoint in this task. Preserve the documented API and expose only the internal interface required by dependent tasks.

ACCEPTANCE AND VERIFICATION
Startup identifies missing P0 dependencies; ordinary request and worker processes use the same schemas.
Use deterministic synthetic fixtures and the injected clock/provider ports where relevant. Run targeted checks for these scenarios and the relevant available lint/type/contract gates from the Makefile. Do not call paid providers or fabricate measured results. Regenerate contracts if changed, and inspect the diff for unrelated edits.

HANDOFF
Return the implemented paths, behavior mapped to the requirement IDs, exact commands and actual outcomes, schema/config/API impact, unresolved blockers and reviewer focus. Default reviewer: M1. Leave production TODO placeholders out of the delivered behavior; if a required check could not run, state the reason and keep the completion gate unverified.
```

### MS-076 — API and generated client contract gate

**Owner:** M6. **Reviewer:** M4. **Priority:** P0. **Estimate:** 3 hours.

**Expected input:** The package contracts for R16.01, R15.05 and US-16.01, US-15.05; merged, tested outputs of MS-075.

**Blocked until:** MS-075 — Production dependency composition

**Expected outcome:** Validate every P0 operation, sample, error envelope and generated client against exported OpenAPI. Gate operation IDs and forbidden DTO drift.

**Acceptance:** Unknown fields, UUIDs, decimal strings and SSE exceptions match API.md; generation leaves no unexplained diff.

**Exact prompt:**

```text
Implement MS-076 — API and generated client contract gate for BenefitBridge as M6.
Use the common system prompt and M6 role rules in agent.md. Work on branch feat/ms-076-contract-test. Preserve unrelated changes.

EXPECTED INPUT
The package contracts for R16.01, R15.05 and US-16.01, US-15.05; merged, tested outputs of MS-075.
Strict prerequisites: MS-075 — Production dependency composition
Verify prerequisite interfaces exist before editing. A missing prerequisite is a blocker, not permission to build an incompatible stub.

READ AND RESPECT
Read requirements.md entries R16.01, R15.05, userStory.md entries US-16.01, US-15.05, this sprint in sprints.md, relevant design.md invariants, API.md common conventions/DTOs and the operations listed below. Follow agent.md style, privacy, versioning, error and ownership rules.

WRITE SCOPE
tests/contracts/; scripts/check_contract.py.
Also edit only directly corresponding tests and mechanically regenerated OpenAPI/client files when affected. Shared domain, registry or migration changes outside this scope require an explicit owner handoff; do not silently expand the task.

IMPLEMENTATION AND EXPECTED OUTCOME
Validate every P0 operation, sample, error envelope and generated client against exported OpenAPI. Gate operation IDs and forbidden DTO drift.
Implement only this unit. Produce the scoped typed implementation and its usable interface in the development composition. Production behavior must pass the specified checks.

API CONTRACT
- No new public endpoint in this task. Preserve the documented API and expose only the internal interface required by dependent tasks.

ACCEPTANCE AND VERIFICATION
Unknown fields, UUIDs, decimal strings and SSE exceptions match API.md; generation leaves no unexplained diff.
Use deterministic synthetic fixtures and the injected clock/provider ports where relevant. Run targeted checks for these scenarios and the relevant available lint/type/contract gates from the Makefile. Do not call paid providers or fabricate measured results. Regenerate contracts if changed, and inspect the diff for unrelated edits.

HANDOFF
Return the implemented paths, behavior mapped to the requirement IDs, exact commands and actual outcomes, schema/config/API impact, unresolved blockers and reviewer focus. Default reviewer: M4. Leave production TODO placeholders out of the delivered behavior; if a required check could not run, state the reason and keep the completion gate unverified.
```

### MS-077 — Requirement and grounding evaluation harness

**Owner:** M6. **Reviewer:** M4. **Priority:** P0. **Estimate:** 2.5 hours.

**Expected input:** The package contracts for R15.01, R15.02 and US-15.01, US-15.02; merged, tested outputs of MS-024, MS-036.

**Blocked until:** MS-024 — Annotation and adjudication tooling; MS-036 — Requirement publication validator

**Expected outcome:** Compute typed leaf matching, mandatory recall, graph exact match and quote validity from frozen examples; produce blinded human entailment review sample.

**Acceptance:** Known perfect/missing/spurious examples yield exact expected counts; invalid citations count as errors.

**Exact prompt:**

```text
Implement MS-077 — Requirement and grounding evaluation harness for BenefitBridge as M6.
Use the common system prompt and M6 role rules in agent.md. Work on branch feat/ms-077-bench-extraction. Preserve unrelated changes.

EXPECTED INPUT
The package contracts for R15.01, R15.02 and US-15.01, US-15.02; merged, tested outputs of MS-024, MS-036.
Strict prerequisites: MS-024 — Annotation and adjudication tooling; MS-036 — Requirement publication validator
Verify prerequisite interfaces exist before editing. A missing prerequisite is a blocker, not permission to build an incompatible stub.

READ AND RESPECT
Read requirements.md entries R15.01, R15.02, userStory.md entries US-15.01, US-15.02, this sprint in sprints.md, relevant design.md invariants, API.md common conventions/DTOs and the operations listed below. Follow agent.md style, privacy, versioning, error and ownership rules.

WRITE SCOPE
evaluation/extraction.py; evaluation/grounding.py.
Also edit only directly corresponding tests and mechanically regenerated OpenAPI/client files when affected. Shared domain, registry or migration changes outside this scope require an explicit owner handoff; do not silently expand the task.

IMPLEMENTATION AND EXPECTED OUTCOME
Compute typed leaf matching, mandatory recall, graph exact match and quote validity from frozen examples; produce blinded human entailment review sample.
Implement only this unit. Produce the scoped typed implementation and its usable interface in the development composition. Production behavior must pass the specified checks.

API CONTRACT
- No new public endpoint in this task. Preserve the documented API and expose only the internal interface required by dependent tasks.

ACCEPTANCE AND VERIFICATION
Known perfect/missing/spurious examples yield exact expected counts; invalid citations count as errors.
Use deterministic synthetic fixtures and the injected clock/provider ports where relevant. Run targeted checks for these scenarios and the relevant available lint/type/contract gates from the Makefile. Do not call paid providers or fabricate measured results. Regenerate contracts if changed, and inspect the diff for unrelated edits.

HANDOFF
Return the implemented paths, behavior mapped to the requirement IDs, exact commands and actual outcomes, schema/config/API impact, unresolved blockers and reviewer focus. Default reviewer: M4. Leave production TODO placeholders out of the delivered behavior; if a required check could not run, state the reason and keep the completion gate unverified.
```

### MS-078 — Eligibility and coverage evaluation harness

**Owner:** M6. **Reviewer:** M4. **Priority:** P0. **Estimate:** 3 hours.

**Expected input:** The package contracts for R15.03 and US-15.03; merged, tested outputs of MS-024, MS-041.

**Blocked until:** MS-024 — Annotation and adjudication tooling; MS-041 — Decision and citation verification

**Expected outcome:** Report three-label confusion including technical failures, MET precision, unsafe promotion, unknown recall, coverage and opportunity-family grouped intervals. Include rare-event bounds with assumptions.

**Acceptance:** All-UNKNOWN baseline fails coverage; failures stay in denominator; zero errors are not reported as zero risk.

**Exact prompt:**

```text
Implement MS-078 — Eligibility and coverage evaluation harness for BenefitBridge as M6.
Use the common system prompt and M6 role rules in agent.md. Work on branch feat/ms-078-bench-eligibility. Preserve unrelated changes.

EXPECTED INPUT
The package contracts for R15.03 and US-15.03; merged, tested outputs of MS-024, MS-041.
Strict prerequisites: MS-024 — Annotation and adjudication tooling; MS-041 — Decision and citation verification
Verify prerequisite interfaces exist before editing. A missing prerequisite is a blocker, not permission to build an incompatible stub.

READ AND RESPECT
Read requirements.md entries R15.03, userStory.md entries US-15.03, this sprint in sprints.md, relevant design.md invariants, API.md common conventions/DTOs and the operations listed below. Follow agent.md style, privacy, versioning, error and ownership rules.

WRITE SCOPE
evaluation/eligibility.py; evaluation/statistics.py.
Also edit only directly corresponding tests and mechanically regenerated OpenAPI/client files when affected. Shared domain, registry or migration changes outside this scope require an explicit owner handoff; do not silently expand the task.

IMPLEMENTATION AND EXPECTED OUTCOME
Report three-label confusion including technical failures, MET precision, unsafe promotion, unknown recall, coverage and opportunity-family grouped intervals. Include rare-event bounds with assumptions.
Implement only this unit. Produce the scoped typed implementation and its usable interface in the development composition. Production behavior must pass the specified checks.

API CONTRACT
- No new public endpoint in this task. Preserve the documented API and expose only the internal interface required by dependent tasks.

ACCEPTANCE AND VERIFICATION
All-UNKNOWN baseline fails coverage; failures stay in denominator; zero errors are not reported as zero risk.
Use deterministic synthetic fixtures and the injected clock/provider ports where relevant. Run targeted checks for these scenarios and the relevant available lint/type/contract gates from the Makefile. Do not call paid providers or fabricate measured results. Regenerate contracts if changed, and inspect the diff for unrelated edits.

HANDOFF
Return the implemented paths, behavior mapped to the requirement IDs, exact commands and actual outcomes, schema/config/API impact, unresolved blockers and reviewer focus. Default reviewer: M4. Leave production TODO placeholders out of the delivered behavior; if a required check could not run, state the reason and keep the completion gate unverified.
```

### MS-079 — Frozen and live discovery evaluation harness

**Owner:** M5. **Reviewer:** M4. **Priority:** P0. **Estimate:** 2.5 hours.

**Expected input:** The package contracts for R15.02 and US-15.02; merged, tested outputs of MS-024, MS-033, MS-034.

**Blocked until:** MS-024 — Annotation and adjudication tooling; MS-033 — Conservative opportunity canonicalization; MS-034 — Bounded redacted goal planner

**Expected outcome:** Create deterministic corpus adapter, query relevance judgments and Precision@5/Recall@10/nDCG; record separate live runs and funnel stages.

**Acceptance:** Truncated candidate tail is unevaluated; frozen recall is labeled bounded-corpus recall.

**Exact prompt:**

```text
Implement MS-079 — Frozen and live discovery evaluation harness for BenefitBridge as M5.
Use the common system prompt and M5 role rules in agent.md. Work on branch feat/ms-079-bench-retrieval. Preserve unrelated changes.

EXPECTED INPUT
The package contracts for R15.02 and US-15.02; merged, tested outputs of MS-024, MS-033, MS-034.
Strict prerequisites: MS-024 — Annotation and adjudication tooling; MS-033 — Conservative opportunity canonicalization; MS-034 — Bounded redacted goal planner
Verify prerequisite interfaces exist before editing. A missing prerequisite is a blocker, not permission to build an incompatible stub.

READ AND RESPECT
Read requirements.md entries R15.02, userStory.md entries US-15.02, this sprint in sprints.md, relevant design.md invariants, API.md common conventions/DTOs and the operations listed below. Follow agent.md style, privacy, versioning, error and ownership rules.

WRITE SCOPE
evaluation/retrieval.py; evaluation/live_discovery.py.
Also edit only directly corresponding tests and mechanically regenerated OpenAPI/client files when affected. Shared domain, registry or migration changes outside this scope require an explicit owner handoff; do not silently expand the task.

IMPLEMENTATION AND EXPECTED OUTCOME
Create deterministic corpus adapter, query relevance judgments and Precision@5/Recall@10/nDCG; record separate live runs and funnel stages.
Implement only this unit. Produce the scoped typed implementation and its usable interface in the development composition. Production behavior must pass the specified checks.

API CONTRACT
- No new public endpoint in this task. Preserve the documented API and expose only the internal interface required by dependent tasks.

ACCEPTANCE AND VERIFICATION
Truncated candidate tail is unevaluated; frozen recall is labeled bounded-corpus recall.
Use deterministic synthetic fixtures and the injected clock/provider ports where relevant. Run targeted checks for these scenarios and the relevant available lint/type/contract gates from the Makefile. Do not call paid providers or fabricate measured results. Regenerate contracts if changed, and inspect the diff for unrelated edits.

HANDOFF
Return the implemented paths, behavior mapped to the requirement IDs, exact commands and actual outcomes, schema/config/API impact, unresolved blockers and reviewer focus. Default reviewer: M4. Leave production TODO placeholders out of the delivered behavior; if a required check could not run, state the reason and keep the completion gate unverified.
```

### MS-080 — Paired model and cost experiment runner

**Owner:** M6. **Reviewer:** M4. **Priority:** P0. **Estimate:** 3 hours.

**Expected input:** The package contracts for R15.04 and US-15.04; merged, tested outputs of MS-078, MS-077, MS-019, MS-010.

**Blocked until:** MS-078 — Eligibility and coverage evaluation harness; MS-077 — Requirement and grounding evaluation harness; MS-019 — Atomic cost reservations and fairness; MS-010 — Model registry and capability preflight

**Expected outcome:** Run B0, B1, B3 and B4 with frozen manifests, same sources/budgets and retries charged; optional B5 only after budget approval. Separate warm/cold cache and deterministic clocks.

**Acceptance:** Variant configuration hashes differ intentionally; results cannot omit failed cases or tune on test.

**Exact prompt:**

```text
Implement MS-080 — Paired model and cost experiment runner for BenefitBridge as M6.
Use the common system prompt and M6 role rules in agent.md. Work on branch feat/ms-080-bench-routing. Preserve unrelated changes.

EXPECTED INPUT
The package contracts for R15.04 and US-15.04; merged, tested outputs of MS-078, MS-077, MS-019, MS-010.
Strict prerequisites: MS-078 — Eligibility and coverage evaluation harness; MS-077 — Requirement and grounding evaluation harness; MS-019 — Atomic cost reservations and fairness; MS-010 — Model registry and capability preflight
Verify prerequisite interfaces exist before editing. A missing prerequisite is a blocker, not permission to build an incompatible stub.

READ AND RESPECT
Read requirements.md entries R15.04, userStory.md entries US-15.04, this sprint in sprints.md, relevant design.md invariants, API.md common conventions/DTOs and the operations listed below. Follow agent.md style, privacy, versioning, error and ownership rules.

WRITE SCOPE
evaluation/experiments.py; evaluation/variants.yaml.
Also edit only directly corresponding tests and mechanically regenerated OpenAPI/client files when affected. Shared domain, registry or migration changes outside this scope require an explicit owner handoff; do not silently expand the task.

IMPLEMENTATION AND EXPECTED OUTCOME
Run B0, B1, B3 and B4 with frozen manifests, same sources/budgets and retries charged; optional B5 only after budget approval. Separate warm/cold cache and deterministic clocks.
Implement only this unit. Produce the scoped typed implementation and its usable interface in the development composition. Production behavior must pass the specified checks.

API CONTRACT
- No new public endpoint in this task. Preserve the documented API and expose only the internal interface required by dependent tasks.

ACCEPTANCE AND VERIFICATION
Variant configuration hashes differ intentionally; results cannot omit failed cases or tune on test.
Use deterministic synthetic fixtures and the injected clock/provider ports where relevant. Run targeted checks for these scenarios and the relevant available lint/type/contract gates from the Makefile. Do not call paid providers or fabricate measured results. Regenerate contracts if changed, and inspect the diff for unrelated edits.

HANDOFF
Return the implemented paths, behavior mapped to the requirement IDs, exact commands and actual outcomes, schema/config/API impact, unresolved blockers and reviewer focus. Default reviewer: M4. Leave production TODO placeholders out of the delivered behavior; if a required check could not run, state the reason and keep the completion gate unverified.
```

### MS-081 — Main journey browser acceptance suite

**Owner:** M2. **Reviewer:** M6. **Priority:** P0. **Estimate:** 3 hours.

**Expected input:** The package contracts for R12.04, R15.05 and US-12.04, US-15.05; merged, tested outputs of MS-069, MS-051, MS-076.

**Blocked until:** MS-069 — Usage, settings and deletion controls; MS-051 — Targeted fact clarification UI; MS-076 — API and generated client contract gate

**Expected outcome:** Automate synthetic-account profile, upload, discovery, evidence, UNKNOWN clarification, draft acceptance, export and deletion using deterministic provider fixtures.

**Acceptance:** Keyboard paths and error recovery pass; no paid endpoints in ordinary CI.

**Exact prompt:**

```text
Implement MS-081 — Main journey browser acceptance suite for BenefitBridge as M2.
Use the common system prompt and M2 role rules in agent.md. Work on branch feat/ms-081-browser-e2e. Preserve unrelated changes.

EXPECTED INPUT
The package contracts for R12.04, R15.05 and US-12.04, US-15.05; merged, tested outputs of MS-069, MS-051, MS-076.
Strict prerequisites: MS-069 — Usage, settings and deletion controls; MS-051 — Targeted fact clarification UI; MS-076 — API and generated client contract gate
Verify prerequisite interfaces exist before editing. A missing prerequisite is a blocker, not permission to build an incompatible stub.

READ AND RESPECT
Read requirements.md entries R12.04, R15.05, userStory.md entries US-12.04, US-15.05, this sprint in sprints.md, relevant design.md invariants, API.md common conventions/DTOs and the operations listed below. Follow agent.md style, privacy, versioning, error and ownership rules.

WRITE SCOPE
frontend/e2e/.
Also edit only directly corresponding tests and mechanically regenerated OpenAPI/client files when affected. Shared domain, registry or migration changes outside this scope require an explicit owner handoff; do not silently expand the task.

IMPLEMENTATION AND EXPECTED OUTCOME
Automate synthetic-account profile, upload, discovery, evidence, UNKNOWN clarification, draft acceptance, export and deletion using deterministic provider fixtures.
Implement only this unit. Produce the scoped typed implementation and its usable interface in the development composition. Production behavior must pass the specified checks.

API CONTRACT
- No new public endpoint in this task. Preserve the documented API and expose only the internal interface required by dependent tasks.

ACCEPTANCE AND VERIFICATION
Keyboard paths and error recovery pass; no paid endpoints in ordinary CI.
Use deterministic synthetic fixtures and the injected clock/provider ports where relevant. Run targeted checks for these scenarios and the relevant available lint/type/contract gates from the Makefile. Do not call paid providers or fabricate measured results. Regenerate contracts if changed, and inspect the diff for unrelated edits.

HANDOFF
Return the implemented paths, behavior mapped to the requirement IDs, exact commands and actual outcomes, schema/config/API impact, unresolved blockers and reviewer focus. Default reviewer: M6. Leave production TODO placeholders out of the delivered behavior; if a required check could not run, state the reason and keep the completion gate unverified.
```

### MS-082 — Capacity and queue load experiment

**Owner:** M6. **Reviewer:** M4. **Priority:** P0. **Estimate:** 2.5 hours.

**Expected input:** The package contracts for R14.05, R15.05 and US-14.05, US-15.05; merged, tested outputs of MS-075, MS-066.

**Blocked until:** MS-075 — Production dependency composition; MS-066 — Failure and concurrency recovery suite

**Expected outcome:** Build separate cached browsing and discovery-burst scenarios, latency distributions, queue delay and fairness reports. Real-provider run is explicit opt-in with reserved cost.

**Acceptance:** 20 browsing sessions and 10 discovery bursts are separately measured; full/partial/failure outcomes remain distinct.

**Exact prompt:**

```text
Implement MS-082 — Capacity and queue load experiment for BenefitBridge as M6.
Use the common system prompt and M6 role rules in agent.md. Work on branch feat/ms-082-load-harness. Preserve unrelated changes.

EXPECTED INPUT
The package contracts for R14.05, R15.05 and US-14.05, US-15.05; merged, tested outputs of MS-075, MS-066.
Strict prerequisites: MS-075 — Production dependency composition; MS-066 — Failure and concurrency recovery suite
Verify prerequisite interfaces exist before editing. A missing prerequisite is a blocker, not permission to build an incompatible stub.

READ AND RESPECT
Read requirements.md entries R14.05, R15.05, userStory.md entries US-14.05, US-15.05, this sprint in sprints.md, relevant design.md invariants, API.md common conventions/DTOs and the operations listed below. Follow agent.md style, privacy, versioning, error and ownership rules.

WRITE SCOPE
evaluation/load/.
Also edit only directly corresponding tests and mechanically regenerated OpenAPI/client files when affected. Shared domain, registry or migration changes outside this scope require an explicit owner handoff; do not silently expand the task.

IMPLEMENTATION AND EXPECTED OUTCOME
Build separate cached browsing and discovery-burst scenarios, latency distributions, queue delay and fairness reports. Real-provider run is explicit opt-in with reserved cost.
Implement only this unit. Produce the scoped typed implementation and its usable interface in the development composition. Production behavior must pass the specified checks.

API CONTRACT
- No new public endpoint in this task. Preserve the documented API and expose only the internal interface required by dependent tasks.

ACCEPTANCE AND VERIFICATION
20 browsing sessions and 10 discovery bursts are separately measured; full/partial/failure outcomes remain distinct.
Use deterministic synthetic fixtures and the injected clock/provider ports where relevant. Run targeted checks for these scenarios and the relevant available lint/type/contract gates from the Makefile. Do not call paid providers or fabricate measured results. Regenerate contracts if changed, and inspect the diff for unrelated edits.

HANDOFF
Return the implemented paths, behavior mapped to the requirement IDs, exact commands and actual outcomes, schema/config/API impact, unresolved blockers and reviewer focus. Default reviewer: M4. Leave production TODO placeholders out of the delivered behavior; if a required check could not run, state the reason and keep the completion gate unverified.
```

### MS-083 — Deployment and migration release assets

**Owner:** M1. **Reviewer:** M3. **Priority:** P0. **Estimate:** 3 hours.

**Expected input:** The package contracts for R16.03 and US-16.03; merged, tested outputs of MS-075, MS-065, MS-066.

**Blocked until:** MS-075 — Production dependency composition; MS-065 — Two-tenant and deletion security suite; MS-066 — Failure and concurrency recovery suite

**Expected outcome:** Create immutable API/worker image, reverse proxy/SSE settings, migration job, secrets mapping, private storage settings, health checks and rollback commands. Do not deploy during this sprint.

**Acceptance:** Local image startup and migration smoke pass; no secrets in image; rollback documents DB compatibility.

**Exact prompt:**

```text
Implement MS-083 — Deployment and migration release assets for BenefitBridge as M1.
Use the common system prompt and M1 role rules in agent.md. Work on branch feat/ms-083-deploy-config. Preserve unrelated changes.

EXPECTED INPUT
The package contracts for R16.03 and US-16.03; merged, tested outputs of MS-075, MS-065, MS-066.
Strict prerequisites: MS-075 — Production dependency composition; MS-065 — Two-tenant and deletion security suite; MS-066 — Failure and concurrency recovery suite
Verify prerequisite interfaces exist before editing. A missing prerequisite is a blocker, not permission to build an incompatible stub.

READ AND RESPECT
Read requirements.md entries R16.03, userStory.md entries US-16.03, this sprint in sprints.md, relevant design.md invariants, API.md common conventions/DTOs and the operations listed below. Follow agent.md style, privacy, versioning, error and ownership rules.

WRITE SCOPE
Dockerfile; deploy/; scripts/migrate_release.sh.
Also edit only directly corresponding tests and mechanically regenerated OpenAPI/client files when affected. Shared domain, registry or migration changes outside this scope require an explicit owner handoff; do not silently expand the task.

IMPLEMENTATION AND EXPECTED OUTCOME
Create immutable API/worker image, reverse proxy/SSE settings, migration job, secrets mapping, private storage settings, health checks and rollback commands. Do not deploy during this sprint.
Implement only this unit. Produce reproducible deployment assets with local smoke evidence; actual hosted deployment is H05.

API CONTRACT
- No new public endpoint in this task. Preserve the documented API and expose only the internal interface required by dependent tasks.

ACCEPTANCE AND VERIFICATION
Local image startup and migration smoke pass; no secrets in image; rollback documents DB compatibility.
Use deterministic synthetic fixtures and the injected clock/provider ports where relevant. Run targeted checks for these scenarios and the relevant available lint/type/contract gates from the Makefile. Do not call paid providers or fabricate measured results. Regenerate contracts if changed, and inspect the diff for unrelated edits.

HANDOFF
Return the implemented paths, behavior mapped to the requirement IDs, exact commands and actual outcomes, schema/config/API impact, unresolved blockers and reviewer focus. Default reviewer: M3. Leave production TODO placeholders out of the delivered behavior; if a required check could not run, state the reason and keep the completion gate unverified.
```

### MS-084 — Isolated synthetic demo scenarios and reset

**Owner:** M5. **Reviewer:** M4. **Priority:** P0. **Estimate:** 3 hours.

**Expected input:** The package contracts for R12.05, R16.04 and US-12.05, US-16.04; merged, tested outputs of MS-075, MS-056, MS-027, MS-083.

**Blocked until:** MS-075 — Production dependency composition; MS-056 — Application and checklist API; MS-027 — PDF to reviewable fact candidates; MS-083 — Deployment and migration release assets

**Expected outcome:** Create clearly synthetic applicant/source/evidence fixtures for MET, NOT_MET and UNKNOWN; implement owner-scoped DEMO_RESET run and register handler through the existing demo hook.

**Acceptance:** Reset cannot target arbitrary accounts; concurrent resets serialize and invalidate old demo artifacts.

**Exact prompt:**

```text
Implement MS-084 — Isolated synthetic demo scenarios and reset for BenefitBridge as M5.
Use the common system prompt and M5 role rules in agent.md. Work on branch feat/ms-084-demo-seed. Preserve unrelated changes.

EXPECTED INPUT
The package contracts for R12.05, R16.04 and US-12.05, US-16.04; merged, tested outputs of MS-075, MS-056, MS-027, MS-083.
Strict prerequisites: MS-075 — Production dependency composition; MS-056 — Application and checklist API; MS-027 — PDF to reviewable fact candidates; MS-083 — Deployment and migration release assets
Verify prerequisite interfaces exist before editing. A missing prerequisite is a blocker, not permission to build an incompatible stub.

READ AND RESPECT
Read requirements.md entries R12.05, R16.04, userStory.md entries US-12.05, US-16.04, this sprint in sprints.md, relevant design.md invariants, API.md common conventions/DTOs and the operations listed below. Follow agent.md style, privacy, versioning, error and ownership rules.

WRITE SCOPE
backend/src/benefitbridge/demo/; backend/src/benefitbridge/api/demo.py; tests/demo/.
Also edit only directly corresponding tests and mechanically regenerated OpenAPI/client files when affected. Shared domain, registry or migration changes outside this scope require an explicit owner handoff; do not silently expand the task.

IMPLEMENTATION AND EXPECTED OUTCOME
Create clearly synthetic applicant/source/evidence fixtures for MET, NOT_MET and UNKNOWN; implement owner-scoped DEMO_RESET run and register handler through the existing demo hook.
Implement only this unit. Produce the scoped typed implementation and its usable interface in the development composition. Production behavior must pass the specified checks.

API CONTRACT
- reset_demo: POST /api/v1/demo/reset; auth=DEMO; success=202; idempotency=required; implement its exact request/response/validation in API.md.

ACCEPTANCE AND VERIFICATION
Reset cannot target arbitrary accounts; concurrent resets serialize and invalidate old demo artifacts.
Use deterministic synthetic fixtures and the injected clock/provider ports where relevant. Run targeted checks for these scenarios and the relevant available lint/type/contract gates from the Makefile. Do not call paid providers or fabricate measured results. Regenerate contracts if changed, and inspect the diff for unrelated edits.

HANDOFF
Return the implemented paths, behavior mapped to the requirement IDs, exact commands and actual outcomes, schema/config/API impact, unresolved blockers and reviewer focus. Default reviewer: M4. Leave production TODO placeholders out of the delivered behavior; if a required check could not run, state the reason and keep the completion gate unverified.
```

### MS-085 — Reproducible result report generator

**Owner:** M6. **Reviewer:** M4. **Priority:** P0. **Estimate:** 2.5 hours.

**Expected input:** The package contracts for R15.01, R15.02, R15.03, R15.04, R15.05 and US-15.01, US-15.02, US-15.03, US-15.04, US-15.05; merged, tested outputs of MS-080, MS-079, MS-082, MS-065.

**Blocked until:** MS-080 — Paired model and cost experiment runner; MS-079 — Frozen and live discovery evaluation harness; MS-082 — Capacity and queue load experiment; MS-065 — Two-tenant and deletion security suite

**Expected outcome:** Generate tables, denominators, confidence intervals, slices, provenance and gate status from actual run manifests. Unrun studies remain NOT_RUN.

**Acceptance:** Missing results never become zero failures or passing gates; grouped confidence intervals identify grouping.

**Exact prompt:**

```text
Implement MS-085 — Reproducible result report generator for BenefitBridge as M6.
Use the common system prompt and M6 role rules in agent.md. Work on branch feat/ms-085-benchmark-report. Preserve unrelated changes.

EXPECTED INPUT
The package contracts for R15.01, R15.02, R15.03, R15.04, R15.05 and US-15.01, US-15.02, US-15.03, US-15.04, US-15.05; merged, tested outputs of MS-080, MS-079, MS-082, MS-065.
Strict prerequisites: MS-080 — Paired model and cost experiment runner; MS-079 — Frozen and live discovery evaluation harness; MS-082 — Capacity and queue load experiment; MS-065 — Two-tenant and deletion security suite
Verify prerequisite interfaces exist before editing. A missing prerequisite is a blocker, not permission to build an incompatible stub.

READ AND RESPECT
Read requirements.md entries R15.01, R15.02, R15.03, R15.04, R15.05, userStory.md entries US-15.01, US-15.02, US-15.03, US-15.04, US-15.05, this sprint in sprints.md, relevant design.md invariants, API.md common conventions/DTOs and the operations listed below. Follow agent.md style, privacy, versioning, error and ownership rules.

WRITE SCOPE
evaluation/report.py; evaluation/report_template.md.
Also edit only directly corresponding tests and mechanically regenerated OpenAPI/client files when affected. Shared domain, registry or migration changes outside this scope require an explicit owner handoff; do not silently expand the task.

IMPLEMENTATION AND EXPECTED OUTCOME
Generate tables, denominators, confidence intervals, slices, provenance and gate status from actual run manifests. Unrun studies remain NOT_RUN.
Implement only this unit. Produce the scoped typed implementation and its usable interface in the development composition. Production behavior must pass the specified checks.

API CONTRACT
- No new public endpoint in this task. Preserve the documented API and expose only the internal interface required by dependent tasks.

ACCEPTANCE AND VERIFICATION
Missing results never become zero failures or passing gates; grouped confidence intervals identify grouping.
Use deterministic synthetic fixtures and the injected clock/provider ports where relevant. Run targeted checks for these scenarios and the relevant available lint/type/contract gates from the Makefile. Do not call paid providers or fabricate measured results. Regenerate contracts if changed, and inspect the diff for unrelated edits.

HANDOFF
Return the implemented paths, behavior mapped to the requirement IDs, exact commands and actual outcomes, schema/config/API impact, unresolved blockers and reviewer focus. Default reviewer: M4. Leave production TODO placeholders out of the delivered behavior; if a required check could not run, state the reason and keep the completion gate unverified.
```

### MS-086 — User study task and observation kit

**Owner:** M2. **Reviewer:** M6. **Priority:** P0. **Estimate:** 2.5 hours.

**Expected input:** The package contracts for R15.05, R12.04 and US-15.05, US-12.04; merged, tested outputs of MS-049, MS-060.

**Blocked until:** MS-049 — Decision and evidence detail screen; MS-060 — Application preparation workspace

**Expected outcome:** Prepare eight-participant counterbalanced manual-search versus BenefitBridge tasks, consent script, timing sheet and blinded correctness rubric. This sprint prepares the study, not participant sessions.

**Acceptance:** Task order and success definitions are fixed before recruitment; no fabricated study outcomes.

**Exact prompt:**

```text
Implement MS-086 — User study task and observation kit for BenefitBridge as M2.
Use the common system prompt and M2 role rules in agent.md. Work on branch feat/ms-086-usability-kit. Preserve unrelated changes.

EXPECTED INPUT
The package contracts for R15.05, R12.04 and US-15.05, US-12.04; merged, tested outputs of MS-049, MS-060.
Strict prerequisites: MS-049 — Decision and evidence detail screen; MS-060 — Application preparation workspace
Verify prerequisite interfaces exist before editing. A missing prerequisite is a blocker, not permission to build an incompatible stub.

READ AND RESPECT
Read requirements.md entries R15.05, R12.04, userStory.md entries US-15.05, US-12.04, this sprint in sprints.md, relevant design.md invariants, API.md common conventions/DTOs and the operations listed below. Follow agent.md style, privacy, versioning, error and ownership rules.

WRITE SCOPE
research/usability/.
Also edit only directly corresponding tests and mechanically regenerated OpenAPI/client files when affected. Shared domain, registry or migration changes outside this scope require an explicit owner handoff; do not silently expand the task.

IMPLEMENTATION AND EXPECTED OUTCOME
Prepare eight-participant counterbalanced manual-search versus BenefitBridge tasks, consent script, timing sheet and blinded correctness rubric. This sprint prepares the study, not participant sessions.
Implement only this unit. Produce the reviewable documents, templates and checklists named in this task; record human execution as pending until H04/H06 actually occur.

API CONTRACT
- No new public endpoint in this task. Preserve the documented API and expose only the internal interface required by dependent tasks.

ACCEPTANCE AND VERIFICATION
Task order and success definitions are fixed before recruitment; no fabricated study outcomes.
Use deterministic synthetic fixtures and the injected clock/provider ports where relevant. Run targeted checks for these scenarios and the relevant available lint/type/contract gates from the Makefile. Do not call paid providers or fabricate measured results. Regenerate contracts if changed, and inspect the diff for unrelated edits.

HANDOFF
Return the implemented paths, behavior mapped to the requirement IDs, exact commands and actual outcomes, schema/config/API impact, unresolved blockers and reviewer focus. Default reviewer: M6. Leave production TODO placeholders out of the delivered behavior; if a required check could not run, state the reason and keep the completion gate unverified.
```

### MS-087 — Video storyboard and submission materials

**Owner:** M2. **Reviewer:** M6. **Priority:** P0. **Estimate:** 2.5 hours.

**Expected input:** The package contracts for R16.04, R16.05 and US-16.04, US-16.05; merged, tested outputs of MS-084, MS-085, MS-086.

**Blocked until:** MS-084 — Isolated synthetic demo scenarios and reset; MS-085 — Reproducible result report generator; MS-086 — User study task and observation kit

**Expected outcome:** Write a 2:50 working-demo storyboard, source-to-evidence walkthrough, UNKNOWN moment, benchmark claims from actual report and setup instructions. Select MIT license only after team confirmation recorded in release checklist.

**Acceptance:** Video allocation totals 170 seconds; unmeasured claims stay labeled; setup describes real credentials and synthetic fixture mode.

**Exact prompt:**

```text
Implement MS-087 — Video storyboard and submission materials for BenefitBridge as M2.
Use the common system prompt and M2 role rules in agent.md. Work on branch feat/ms-087-demo-docs. Preserve unrelated changes.

EXPECTED INPUT
The package contracts for R16.04, R16.05 and US-16.04, US-16.05; merged, tested outputs of MS-084, MS-085, MS-086.
Strict prerequisites: MS-084 — Isolated synthetic demo scenarios and reset; MS-085 — Reproducible result report generator; MS-086 — User study task and observation kit
Verify prerequisite interfaces exist before editing. A missing prerequisite is a blocker, not permission to build an incompatible stub.

READ AND RESPECT
Read requirements.md entries R16.04, R16.05, userStory.md entries US-16.04, US-16.05, this sprint in sprints.md, relevant design.md invariants, API.md common conventions/DTOs and the operations listed below. Follow agent.md style, privacy, versioning, error and ownership rules.

WRITE SCOPE
docs/demo.md; docs/submission.md; README.md; LICENSE.
Also edit only directly corresponding tests and mechanically regenerated OpenAPI/client files when affected. Shared domain, registry or migration changes outside this scope require an explicit owner handoff; do not silently expand the task.

IMPLEMENTATION AND EXPECTED OUTCOME
Write a 2:50 working-demo storyboard, source-to-evidence walkthrough, UNKNOWN moment, benchmark claims from actual report and setup instructions. Select MIT license only after team confirmation recorded in release checklist.
Implement only this unit. Produce the reviewable documents, templates and checklists named in this task; record human execution as pending until H04/H06 actually occur.

API CONTRACT
- No new public endpoint in this task. Preserve the documented API and expose only the internal interface required by dependent tasks.

ACCEPTANCE AND VERIFICATION
Video allocation totals 170 seconds; unmeasured claims stay labeled; setup describes real credentials and synthetic fixture mode.
Use deterministic synthetic fixtures and the injected clock/provider ports where relevant. Run targeted checks for these scenarios and the relevant available lint/type/contract gates from the Makefile. Do not call paid providers or fabricate measured results. Regenerate contracts if changed, and inspect the diff for unrelated edits.

HANDOFF
Return the implemented paths, behavior mapped to the requirement IDs, exact commands and actual outcomes, schema/config/API impact, unresolved blockers and reviewer focus. Default reviewer: M6. Leave production TODO placeholders out of the delivered behavior; if a required check could not run, state the reason and keep the completion gate unverified.
```

### MS-088 — Operations, retention and incident runbook

**Owner:** M1. **Reviewer:** M3. **Priority:** P0. **Estimate:** 2.5 hours.

**Expected input:** The package contracts for R13.04, R14.04, R16.03 and US-13.04, US-14.04, US-16.03; merged, tested outputs of MS-083, MS-064, MS-074.

**Blocked until:** MS-083 — Deployment and migration release assets; MS-064 — Account purge and capability receipt; MS-074 — Redacted operational metrics and health

**Expected outcome:** Document verified provider retention, restore/purge replay, judge-access checks, budget reserve, incident ownership and operation through 16 December UTC.

**Acceptance:** Restore cannot resurrect tombstoned users; operator drill includes exhausted credits and dead worker.

**Exact prompt:**

```text
Implement MS-088 — Operations, retention and incident runbook for BenefitBridge as M1.
Use the common system prompt and M1 role rules in agent.md. Work on branch feat/ms-088-runbook. Preserve unrelated changes.

EXPECTED INPUT
The package contracts for R13.04, R14.04, R16.03 and US-13.04, US-14.04, US-16.03; merged, tested outputs of MS-083, MS-064, MS-074.
Strict prerequisites: MS-083 — Deployment and migration release assets; MS-064 — Account purge and capability receipt; MS-074 — Redacted operational metrics and health
Verify prerequisite interfaces exist before editing. A missing prerequisite is a blocker, not permission to build an incompatible stub.

READ AND RESPECT
Read requirements.md entries R13.04, R14.04, R16.03, userStory.md entries US-13.04, US-14.04, US-16.03, this sprint in sprints.md, relevant design.md invariants, API.md common conventions/DTOs and the operations listed below. Follow agent.md style, privacy, versioning, error and ownership rules.

WRITE SCOPE
docs/runbook.md; docs/retention.md.
Also edit only directly corresponding tests and mechanically regenerated OpenAPI/client files when affected. Shared domain, registry or migration changes outside this scope require an explicit owner handoff; do not silently expand the task.

IMPLEMENTATION AND EXPECTED OUTCOME
Document verified provider retention, restore/purge replay, judge-access checks, budget reserve, incident ownership and operation through 16 December UTC.
Implement only this unit. Produce the reviewable documents, templates and checklists named in this task; record human execution as pending until H04/H06 actually occur.

API CONTRACT
- No new public endpoint in this task. Preserve the documented API and expose only the internal interface required by dependent tasks.

ACCEPTANCE AND VERIFICATION
Restore cannot resurrect tombstoned users; operator drill includes exhausted credits and dead worker.
Use deterministic synthetic fixtures and the injected clock/provider ports where relevant. Run targeted checks for these scenarios and the relevant available lint/type/contract gates from the Makefile. Do not call paid providers or fabricate measured results. Regenerate contracts if changed, and inspect the diff for unrelated edits.

HANDOFF
Return the implemented paths, behavior mapped to the requirement IDs, exact commands and actual outcomes, schema/config/API impact, unresolved blockers and reviewer focus. Default reviewer: M3. Leave production TODO placeholders out of the delivered behavior; if a required check could not run, state the reason and keep the completion gate unverified.
```

### MS-089 — Release readiness evidence collector

**Owner:** M6. **Reviewer:** M4. **Priority:** P0. **Estimate:** 3 hours.

**Expected input:** The package contracts for R16.02, R16.03, R16.04, R16.05 and US-16.02, US-16.03, US-16.04, US-16.05; merged, tested outputs of MS-076, MS-081, MS-085, MS-088, MS-087.

**Blocked until:** MS-076 — API and generated client contract gate; MS-081 — Main journey browser acceptance suite; MS-085 — Reproducible result report generator; MS-088 — Operations, retention and incident runbook; MS-087 — Video storyboard and submission materials

**Expected outcome:** Collect commit/config/dataset hashes and gate outcomes, verify public links manually through checklist, and produce explicit GO/BLOCKED report. Do not fabricate human signoffs or execute deployment.

**Acceptance:** Any isolation failure, missing live runtime proof, absent license or unverified judge access blocks GO.

**Exact prompt:**

```text
Implement MS-089 — Release readiness evidence collector for BenefitBridge as M6.
Use the common system prompt and M6 role rules in agent.md. Work on branch feat/ms-089-release. Preserve unrelated changes.

EXPECTED INPUT
The package contracts for R16.02, R16.03, R16.04, R16.05 and US-16.02, US-16.03, US-16.04, US-16.05; merged, tested outputs of MS-076, MS-081, MS-085, MS-088, MS-087.
Strict prerequisites: MS-076 — API and generated client contract gate; MS-081 — Main journey browser acceptance suite; MS-085 — Reproducible result report generator; MS-088 — Operations, retention and incident runbook; MS-087 — Video storyboard and submission materials
Verify prerequisite interfaces exist before editing. A missing prerequisite is a blocker, not permission to build an incompatible stub.

READ AND RESPECT
Read requirements.md entries R16.02, R16.03, R16.04, R16.05, userStory.md entries US-16.02, US-16.03, US-16.04, US-16.05, this sprint in sprints.md, relevant design.md invariants, API.md common conventions/DTOs and the operations listed below. Follow agent.md style, privacy, versioning, error and ownership rules.

WRITE SCOPE
scripts/release_check.py; docs/release_checklist.md.
Also edit only directly corresponding tests and mechanically regenerated OpenAPI/client files when affected. Shared domain, registry or migration changes outside this scope require an explicit owner handoff; do not silently expand the task.

IMPLEMENTATION AND EXPECTED OUTCOME
Collect commit/config/dataset hashes and gate outcomes, verify public links manually through checklist, and produce explicit GO/BLOCKED report. Do not fabricate human signoffs or execute deployment.
Implement only this unit. Produce the scoped typed implementation and its usable interface in the development composition. Production behavior must pass the specified checks.

API CONTRACT
- No new public endpoint in this task. Preserve the documented API and expose only the internal interface required by dependent tasks.

ACCEPTANCE AND VERIFICATION
Any isolation failure, missing live runtime proof, absent license or unverified judge access blocks GO.
Use deterministic synthetic fixtures and the injected clock/provider ports where relevant. Run targeted checks for these scenarios and the relevant available lint/type/contract gates from the Makefile. Do not call paid providers or fabricate measured results. Regenerate contracts if changed, and inspect the diff for unrelated edits.

HANDOFF
Return the implemented paths, behavior mapped to the requirement IDs, exact commands and actual outcomes, schema/config/API impact, unresolved blockers and reviewer focus. Default reviewer: M4. Leave production TODO placeholders out of the delivered behavior; if a required check could not run, state the reason and keep the completion gate unverified.
```

## 6. Final completion evidence

M6 records the code commit, config/registry/prompt versions, source/dataset hashes, contract/test reports, measured benchmark denominators, live workflow trace, participant count, deployment/retention checks and human signoffs. M1 verifies access, budgets and the operator rota. M2 verifies public video length and that every spoken metric exists in the report. All six confirm their contributions and source/license rights. Unverified evidence remains explicitly unverified; this plan is complete when these actions are concrete and assigned, while the future implementation is complete only when its gates have actually passed.
