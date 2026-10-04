# BenefitBridge — Requirements

**BenefitBridge · Best Apps and Agents · Six-person implementation package · 4 October 2026**

[requirements.md](requirements.md) | [userStory.md](userStory.md) | [sprints.md](sprints.md) | [design.md](design.md) | [API.md](API.md) | [plan.md](plan.md) | [agent.md](agent.md)

BenefitBridge helps undergraduate and early-career applicants discover internships/research placements and scholarships/funded student programs, compare published requirements with their confirmed facts and evidence, and prepare an application. The product reports what the supplied policy and evidence justify; the provider makes the actual selection decision.

P0 uses English official HTML pages and readable PDFs, applicants based in Egypt with potentially international opportunities, one applicant per account, structured facts, optional documents, bounded live discovery, explicit refresh, evidence-backed tri-state decisions and reviewed Markdown export. P1 contains only the saved-page watch slice in this package. OCR, Arabic documents, unrestricted grants/public benefits, advisor tenants, autonomous submission, email/calendar integrations, embeddings, training and microservices remain deferred.

This is a design and execution package. No application, deployment, benchmark result or user-study result is claimed as completed. Acceptance numbers are proposed gates, not measurements. A single prompt defines one bounded implementation assignment; code review and the specified checks remain mandatory.

## Source basis and precedence

The local `BenefitBridge_Hackathon_Proposal(1).md` establishes the product idea. `BenefitBridge_System_Design_and_Evaluation.md` (3 October 2026) supplies the narrowed scope, evidence semantics, benchmark protocol and hackathon constraints. This package makes those decisions executable. Where the older proposal is broader, the narrowed design takes precedence. The package explicitly refines upload transport to an authenticated streaming endpoint, clarifies account deletion receipts and makes model roles configurable.

Inside this package, `requirements.md` defines behavior; `API.md` is the authoritative wire contract; `design.md` defines internal invariants; `sprints.md` defines task boundaries/dependencies; `plan.md` assigns work and supplies prompts; `agent.md` governs implementation consistency. Any contradiction must be resolved in the affected documents before changing public behavior; no agent may silently choose its own contract. Requirement IDs are stable and trace to stories and micro-sprints.

## Exactly what the user enters and receives

| Input stage | User enters | Constraints | System returns |
| --- | --- | --- | --- |
| Account | Email/password or supported managed-auth login; name/timezone; consent | Only login and consent required before processing | Private account and empty versioned profile |
| Profile | Country of residence; degree level/field; enrollment; graduation precision; original GPA/scale; skills and relevant experience | Each fact may remain unknown; citizenship and work authorization requested separately only when relevant | Confirmed typed facts, provenance and immutable profile version |
| Documents | Optional digital English CV, transcript or enrollment PDF; choose document kind | 10 MiB/file, 20 pages, 10 files and 50 MiB/account; no scans/OCR in P0 | Processing status, evidence passages and candidate facts awaiting review |
| Goal | Example: Find funded AI research internships for undergraduate students in 2027 | 20–1000 characters, one opportunity lane, country/remote/field/funding preferences | Bounded search plan, source-resolved candidate list, progress and funnel counts |
| Existing listing | Optional public HTTPS opportunity URL | Official/public content; no login bypass; unsupported sources labeled | Imported opportunity, source status, requirements and evaluation run |
| Clarification | Answer a specific typed question, or choose unknown/skip | At most 3 questions/round and 2 rounds/run | New profile version, resumed decision and unresolved reasons if still insufficient |
| Application | Select opportunity, mark supported task completion, request statement, edit and explicitly accept | No unreviewed text accepted; factual claims checked; current input versions required | Checklist fraction, truthful reviewed statement and Markdown export |
| Ongoing control | Save, refresh, cancel, delete document/account; optional watch toggle | Owner-only operations, quota and current-version checks | Persistent shortlist, version changes, purge receipt or in-app P1 notifications |

A first useful session requires an account, processing consent, a goal and whichever facts the user knows. A CV is optional. Unknown facts are acceptable inputs and can lead to targeted questions or UNKNOWN decisions. Residence, citizenship and work authorization are separate facts; an Egyptian residence alone never establishes the other two.

## High-level and low-level requirements

### R01 — Identity, consent, and account lifecycle

- **High-level requirement:** Enable identity, consent, and account lifecycle under the system-wide privacy, versioning and budget rules.
  - **R01.01 · P0 — Sign in to a private account.**
    - Function: Verify JWT signature, issuer, audience, expiry and active account status on each protected request.
    - Failure/edge behavior: Reject expired tokens and tokens for another project.
    - Acceptance trace: US-01.01; MS-008, MS-009.
  - **R01.02 · P0 — Review and accept processing terms.**
    - Function: Persist consent version and timestamp before document or inference operations.
    - Failure/edge behavior: Reject processing without current consent.
    - Acceptance trace: US-01.02; MS-008, MS-009.
  - **R01.03 · P0 — Maintain one applicant profile per account.**
    - Function: Create one empty versioned profile on first account initialization.
    - Failure/edge behavior: A caller cannot supply or override owner_id.
    - Acceptance trace: US-01.03; MS-007, MS-008.
  - **R01.04 · P0 — View and change my account preferences.**
    - Function: Validate display name and IANA timezone without changing identity.
    - Failure/edge behavior: Reject unknown fields and invalid timezones.
    - Acceptance trace: US-01.04; MS-008, MS-069.
  - **R01.05 · P0 — Delete my account and obtain a receipt.**
    - Function: Immediately tombstone access and queue a durable purge with a separate receipt capability.
    - Failure/edge behavior: Existing tokens cannot access private objects after tombstoning.
    - Acceptance trace: US-01.05; MS-015, MS-064, MS-069.

### R02 — Structured applicant facts and versions

- **High-level requirement:** Enable structured applicant facts and versions under the system-wide privacy, versioning and budget rules.
  - **R02.01 · P0 — Enter structured education, location, and skills.**
    - Function: Validate the typed fact catalog and keep residence, citizenship and authorization distinct.
    - Failure/edge behavior: Missing facts never become false or unrestricted eligibility.
    - Acceptance trace: US-02.01; MS-002, MS-007, MS-017, MS-018.
  - **R02.02 · P0 — Record gpa with its original scale.**
    - Function: Use decimal strings and compatible scales without ad hoc conversion.
    - Failure/edge behavior: 3.5 on a 5-point scale cannot satisfy 3.0 on a 4-point scale automatically.
    - Acceptance trace: US-02.02; MS-002, MS-011, MS-017, MS-018.
  - **R02.03 · P0 — Review extracted facts before publication.**
    - Function: Accept, correct or reject candidate facts in one version-checked transaction.
    - Failure/edge behavior: Unreviewed candidate facts are excluded from the active profile.
    - Acceptance trace: US-02.03; MS-027, MS-028, MS-029.
  - **R02.04 · P0 — Correct information with history.**
    - Function: Create immutable profile versions and expose historical versions to their owner.
    - Failure/edge behavior: Concurrent stale edits return conflict without losing either version.
    - Acceptance trace: US-02.04; MS-007, MS-017, MS-018, MS-028, MS-062.
  - **R02.05 · P0 — See evidence status and disagreements.**
    - Function: Distinguish confirmed self-report, document-supported and conflicting evidence.
    - Failure/edge behavior: A document is never described as issuer-authenticated.
    - Acceptance trace: US-02.05; MS-017, MS-018, MS-027, MS-028.

### R03 — Document intake and evidence

- **High-level requirement:** Enable document intake and evidence under the system-wide privacy, versioning and budget rules.
  - **R03.01 · P0 — Upload a readable cv or student document.**
    - Function: Accept digital English PDFs up to 10 MiB and 20 pages using authenticated bounded streaming.
    - Failure/edge behavior: Reject forged MIME, oversize, encrypted or malformed documents.
    - Acceptance trace: US-03.01; MS-012, MS-025, MS-026, MS-029.
  - **R03.02 · P0 — Follow document processing.**
    - Function: Persist upload, queued, parsing, ready and failed states with useful failure reasons.
    - Failure/edge behavior: Parser failure does not erase manually entered profile facts.
    - Acceptance trace: US-03.02; MS-025, MS-026, MS-027, MS-029.
  - **R03.03 · P0 — Inspect exact supporting passages.**
    - Function: Preserve document version, page, normalized offsets, quote and text hash.
    - Failure/edge behavior: Reject citations outside the stored normalized text.
    - Acceptance trace: US-03.03; MS-006, MS-012, MS-025, MS-026, MS-028, MS-029, MS-037.
  - **R03.04 · P0 — Use manual entry when extraction is poor.**
    - Function: Mark poor extraction and expose a replacement or structured-entry action.
    - Failure/edge behavior: Scanned PDFs are not silently treated as fully parsed.
    - Acceptance trace: US-03.04; MS-012, MS-027, MS-029.
  - **R03.05 · P0 — Remove an uploaded document.**
    - Function: Revoke access immediately, invalidate dependent private artifacts and purge objects within configured retention.
    - Failure/edge behavior: A cached draft cannot expose text from deleted evidence.
    - Acceptance trace: US-03.05; MS-063.

### R04 — Goals, discovery, and candidate intake

- **High-level requirement:** Enable goals, discovery, and candidate intake under the system-wide privacy, versioning and budget rules.
  - **R04.01 · P0 — Describe the opportunities i want.**
    - Function: Accept a 20–1000 character goal, one lane and bounded preferences.
    - Failure/edge behavior: Do not infer citizenship, work authorization or GPA from the goal.
    - Acceptance trace: US-04.01; MS-034, MS-046, MS-048.
  - **R04.02 · P0 — Run a bounded discovery workflow.**
    - Function: Start with up to three queries and allow at most two follow-ups and 40 raw hits.
    - Failure/edge behavior: Exhausted budget produces an explicit partial result.
    - Acceptance trace: US-04.02; MS-022, MS-034, MS-043, MS-046.
  - **R04.03 · P0 — Import a public opportunity url.**
    - Function: Accept HTTPS URLs after public-network and source-policy checks.
    - Failure/edge behavior: Reject private-network targets, credentials in URLs and login bypasses.
    - Acceptance trace: US-04.03; MS-021, MS-022, MS-046.
  - **R04.04 · P0 — Understand the discovery funnel.**
    - Function: Show hit, canonical, authoritative, parsed and evaluated counts.
    - Failure/edge behavior: Unevaluated candidates cannot be labeled ineligible.
    - Acceptance trace: US-04.04; MS-043, MS-048.
  - **R04.05 · P0 — Receive results as they become available.**
    - Function: Persist candidate results and ordered progress events.
    - Failure/edge behavior: A single fetch timeout cannot erase successful candidates.
    - Acceptance trace: US-04.05; MS-031, MS-043, MS-048.

### R05 — Authoritative sources, identity, and freshness

- **High-level requirement:** Enable authoritative sources, identity, and freshness under the system-wide privacy, versioning and budget rules.
  - **R05.01 · P0 — See the official source for each requirement.**
    - Function: Classify current official listings, validated ATS pages and discovery-only reposts.
    - Failure/edge behavior: Search snippets alone cannot support an overall positive decision.
    - Acceptance trace: US-05.01; MS-006, MS-014, MS-022, MS-032, MS-043, MS-045.
  - **R05.02 · P0 — Avoid duplicate listings without losing distinct intakes.**
    - Function: Canonicalize provider, external identifier, intake and location conservatively.
    - Failure/edge behavior: Do not merge different years or regions solely by title.
    - Acceptance trace: US-05.02; MS-014, MS-033.
  - **R05.03 · P0 — Inspect the exact source version.**
    - Function: Store immutable normalized text, content hash, retrieval time and source spans.
    - Failure/edge behavior: New page content creates a new version instead of rewriting history.
    - Acceptance trace: US-05.03; MS-002, MS-006, MS-014, MS-032, MS-045.
  - **R05.04 · P0 — See freshness and availability separately.**
    - Function: Use 24-hour job and near-deadline freshness, 72-hour program freshness and explicit availability.
    - Failure/edge behavior: Inaccessible means UNAVAILABLE rather than automatically CLOSED.
    - Acceptance trace: US-05.04; MS-032, MS-042, MS-061.
  - **R05.05 · P0 — Refresh an opportunity and see material changes.**
    - Function: Fetch within budgets, detect semantic changes and invalidate affected evaluations.
    - Failure/edge behavior: Fetch timestamp alone cannot resolve conflicting official policies.
    - Acceptance trace: US-05.05; MS-061, MS-062.

### R06 — Requirement graph extraction

- **High-level requirement:** Enable requirement graph extraction under the system-wide privacy, versioning and budget rules.
  - **R06.01 · P0 — See mandatory and preferred requirements separately.**
    - Function: Preserve MANDATORY, PREFERRED, OPTIONAL and AMBIGUOUS modalities.
    - Failure/edge behavior: Preferred criteria must not enter the mandatory root.
    - Acceptance trace: US-06.01; MS-002, MS-035, MS-045, MS-049.
  - **R06.02 · P0 — Understand alternatives and exceptions.**
    - Function: Represent ALL, ANY, NOT and typed predicate nodes with stable IDs.
    - Failure/edge behavior: Reject cycles, dangling children and unsupported operators.
    - Acceptance trace: US-06.02; MS-002, MS-023, MS-035, MS-036, MS-038.
  - **R06.03 · P0 — See provenance for every material rule.**
    - Function: Attach exact source spans and applicable intake/scope to every predicate.
    - Failure/edge behavior: Invented or unrelated quotations fail publication checks.
    - Acceptance trace: US-06.03; MS-006, MS-014, MS-035, MS-036, MS-045.
  - **R06.04 · P0 — Know when source context is incomplete.**
    - Function: Record COMPLETE, INCOMPLETE or CONFLICTED completeness and extraction issues.
    - Failure/edge behavior: Incomplete extraction blocks an overall MET publication.
    - Acceptance trace: US-06.04; MS-035, MS-036, MS-043.
  - **R06.05 · P0 — Preserve dates, scales and policy ambiguity.**
    - Function: Keep date precision, timezone, GPA scale and reference event explicit.
    - Failure/edge behavior: Date-only deadlines cannot become invented midnight timestamps.
    - Acceptance trace: US-06.05; MS-011, MS-035.

### R07 — Eligibility and decision verification

- **High-level requirement:** Enable eligibility and decision verification under the system-wide privacy, versioning and budget rules.
  - **R07.01 · P0 — Receive a reproducible requirements decision.**
    - Function: Evaluate typed predicates with three-valued logic and expose MET, NOT_MET or UNKNOWN.
    - Failure/edge behavior: Missing information cannot be promoted to MET.
    - Acceptance trace: US-07.01; MS-002, MS-023, MS-038, MS-040, MS-044, MS-047.
  - **R07.02 · P0 — Have numerical and logical rules evaluated deterministically.**
    - Function: Use Decimal, tested date intervals and complete truth tables.
    - Failure/edge behavior: Do not execute model-generated code or arithmetic expressions.
    - Acceptance trace: US-07.02; MS-011, MS-023.
  - **R07.03 · P0 — Receive supported semantic interpretations.**
    - Function: Use bounded evidence bundles and schema-constrained model outputs for allowlisted semantic predicates.
    - Failure/edge behavior: Unsupported entailment yields UNKNOWN.
    - Acceptance trace: US-07.03; MS-020, MS-037, MS-039.
  - **R07.04 · P0 — See a checked explanation of the decision.**
    - Function: Validate source IDs, evidence ownership, input versions and decisive paths before publication.
    - Failure/edge behavior: Invalid grounding downgrades or blocks the affected decision.
    - Acceptance trace: US-07.04; MS-036, MS-038, MS-040, MS-041, MS-044, MS-047, MS-049.
  - **R07.05 · P0 — Understand unresolved cases.**
    - Function: Expose reason codes and exact missing attributes without fabricated certainty.
    - Failure/edge behavior: Model self-confidence is not an eligibility probability.
    - Acceptance trace: US-07.05; MS-039, MS-040, MS-041, MS-047, MS-049.

### R08 — Ranking, readiness, and clarification

- **High-level requirement:** Enable ranking, readiness, and clarification under the system-wide privacy, versioning and budget rules.
  - **R08.01 · P0 — See eligibility, availability, fit and readiness separately.**
    - Function: Display four independent fields and their explanations.
    - Failure/edge behavior: A high fit score cannot hide a failed mandatory condition.
    - Acceptance trace: US-08.01; MS-002, MS-040, MS-042, MS-044, MS-048.
  - **R08.02 · P0 — Receive a transparent result ordering.**
    - Function: Use deterministic group ordering and explicit preference weights.
    - Failure/edge behavior: Unknown components cannot be silently assigned perfect fit.
    - Acceptance trace: US-08.02; MS-042, MS-048.
  - **R08.03 · P0 — Answer targeted clarification questions.**
    - Function: Ask at most three supported fact questions per round and two rounds per run.
    - Failure/edge behavior: A repeated unanswered question cannot trigger an infinite loop.
    - Acceptance trace: US-08.03; MS-038, MS-050, MS-051.
  - **R08.04 · P0 — Resume evaluation after clarification.**
    - Function: Create a new profile version and resume from a pinned evaluation checkpoint.
    - Failure/edge behavior: Concurrent profile edits cause a conflict instead of overwriting.
    - Acceptance trace: US-08.04; MS-038, MS-050, MS-051.
  - **R08.05 · P0 — See application readiness as completed tasks.**
    - Function: Calculate completed applicable required items divided by known applicable required items.
    - Failure/edge behavior: Generated but unaccepted text does not count as complete.
    - Acceptance trace: US-08.05; MS-042, MS-055, MS-056.

### R09 — Application workspaces and truthful drafts

- **High-level requirement:** Enable application workspaces and truthful drafts under the system-wide privacy, versioning and budget rules.
  - **R09.01 · P0 — Create an application workspace.**
    - Function: Pin opportunity and evaluation inputs and create deterministic checklist items.
    - Failure/edge behavior: Do not create a current application from stale or foreign-owned inputs.
    - Acceptance trace: US-09.01; MS-052, MS-056, MS-060.
  - **R09.02 · P0 — Track required application tasks.**
    - Function: Expose task evidence, completion state and version-checked updates.
    - Failure/edge behavior: Optional or nonapplicable tasks cannot inflate the required denominator.
    - Acceptance trace: US-09.02; MS-052, MS-055, MS-056, MS-060.
  - **R09.03 · P0 — Generate a concise statement grounded in my facts.**
    - Function: Generate one 150–500 word statement with claim-to-fact links and no unsupported material claims.
    - Failure/edge behavior: Unsupported claims must be removed or explicitly requested as missing input.
    - Acceptance trace: US-09.03; MS-057, MS-058, MS-059, MS-060.
  - **R09.04 · P0 — Review and accept a specific draft version.**
    - Function: Validate edits and bind acceptance to exact draft and input versions.
    - Failure/edge behavior: Edited or invalidated drafts lose acceptance.
    - Acceptance trace: US-09.04; MS-052, MS-058, MS-059, MS-060.
  - **R09.05 · P0 — Export reviewed materials.**
    - Function: Export UTF-8 Markdown containing current accepted text, checklist and source links.
    - Failure/edge behavior: Do not send emails, submit forms or sign declarations.
    - Acceptance trace: US-09.05; MS-059, MS-060.

### R10 — Durable workflows and user progress

- **High-level requirement:** Enable durable workflows and user progress under the system-wide privacy, versioning and budget rules.
  - **R10.01 · P0 — Start a job safely even if the network retries.**
    - Function: Use idempotency keys and a transactional run/outbox insert.
    - Failure/edge behavior: Reusing a key with a different payload returns conflict.
    - Acceptance trace: US-10.01; MS-015, MS-016, MS-030, MS-046, MS-066.
  - **R10.02 · P0 — See durable workflow status.**
    - Function: Persist QUEUED, RUNNING, WAITING_USER and terminal states with ordered events.
    - Failure/edge behavior: No browser connection is required to keep work alive.
    - Acceptance trace: US-10.02; MS-003, MS-015, MS-016, MS-030, MS-031.
  - **R10.03 · P0 — Cancel expensive work.**
    - Function: Set cancel_requested and stop at safe checkpoints while retaining completed artifacts.
    - Failure/edge behavior: Do not claim an in-flight provider request can always be recalled.
    - Acceptance trace: US-10.03; MS-016, MS-030, MS-031, MS-066.
  - **R10.04 · P0 — Recover from worker or provider failures.**
    - Function: Use leases, heartbeats, bounded retries and idempotent stage outputs.
    - Failure/edge behavior: Repeated worker delivery cannot duplicate a published evaluation.
    - Acceptance trace: US-10.04; MS-015, MS-016, MS-044, MS-066.
  - **R10.05 · P0 — Resume event streaming after disconnection.**
    - Function: Replay monotonic owner-scoped event IDs with a bounded retention policy.
    - Failure/edge behavior: Events from another account return the same not-found response.
    - Acceptance trace: US-10.05; MS-016, MS-030, MS-031.

### R11 — Saved opportunities and optional watch

- **High-level requirement:** Enable saved opportunities and optional watch under the system-wide privacy, versioning and budget rules.
  - **R11.01 · P0 — Save and remove opportunities.**
    - Function: Provide owner-scoped idempotent save and delete operations.
    - Failure/edge behavior: Saving a public opportunity must not expose another applicant evaluation.
    - Acceptance trace: US-11.01; MS-052, MS-053, MS-054.
  - **R11.02 · P0 — Review saved opportunities after changes.**
    - Function: Show invalidated badges and enqueue deduplicated refresh or reevaluation.
    - Failure/edge behavior: Old immutable evaluations remain historical, never relabeled as fresh.
    - Acceptance trace: US-11.02; MS-053, MS-054, MS-061, MS-062.
  - **R11.03 · P1 — Watch selected saved opportunities.**
    - Function: Poll only saved official pages at a configured cadence with bounded fanout.
    - Failure/edge behavior: Repeated unchanged content creates no notification.
    - Acceptance trace: US-11.03; MS-070, MS-071, MS-072, MS-073.
  - **R11.04 · P1 — Receive in-app change notifications.**
    - Function: Create one owner-scoped notification per material source version change.
    - Failure/edge behavior: No external email or calendar integration is implied.
    - Acceptance trace: US-11.04; MS-070, MS-071, MS-072, MS-073.
  - **R11.05 · P1 — Pause a watch.**
    - Function: Disable scheduled work without deleting the saved opportunity.
    - Failure/edge behavior: A paused watch cannot enqueue new refresh jobs.
    - Acceptance trace: US-11.05; MS-070, MS-071, MS-072, MS-073.

### R12 — Usable and accessible web interface

- **High-level requirement:** Enable usable and accessible web interface under the system-wide privacy, versioning and budget rules.
  - **R12.01 · P0 — Follow a clear onboarding flow.**
    - Function: Offer account, consent, profile, optional documents and goal steps.
    - Failure/edge behavior: Uploading a document is not mandatory to try the service.
    - Acceptance trace: US-12.01; MS-004, MS-009, MS-018.
  - **R12.02 · P0 — Inspect decision details in one place.**
    - Function: Present requirement, source passage, applicant fact, outcome and next action together.
    - Failure/edge behavior: Do not render private provider internals as product guidance.
    - Acceptance trace: US-12.02; MS-049.
  - **R12.03 · P0 — Understand empty, loading and failure states.**
    - Function: Design every main screen for empty, pending, partial, failed and stale data.
    - Failure/edge behavior: Errors cannot be represented by endless spinners.
    - Acceptance trace: US-12.03; MS-004, MS-031, MS-051.
  - **R12.04 · P0 — Use the application by keyboard.**
    - Function: Provide semantic controls, focus management, readable contrast and text status labels.
    - Failure/edge behavior: Color alone cannot communicate eligibility.
    - Acceptance trace: US-12.04; MS-004, MS-049, MS-081, MS-086.
  - **R12.05 · P0 — Try a synthetic judge scenario.**
    - Function: Provide isolated demo tenants and explicit synthetic-data labels.
    - Failure/edge behavior: Reset affects only the requesting demo tenant.
    - Acceptance trace: US-12.05; MS-084.

### R13 — Privacy and abuse resistance

- **High-level requirement:** Enable privacy and abuse resistance under the system-wide privacy, versioning and budget rules.
  - **R13.01 · P0 — Keep my evidence isolated.**
    - Function: Enforce server ownership checks, row-level security and composite foreign keys.
    - Failure/edge behavior: Guessed IDs, exports, streams and signed links cannot cross tenants.
    - Acceptance trace: US-13.01; MS-007, MS-008, MS-025, MS-037, MS-065.
  - **R13.02 · P0 — Limit information sent to providers.**
    - Function: Search receives generalized goals; inference receives minimum necessary spans.
    - Failure/edge behavior: Raw CVs, names, email and private URLs cannot enter search queries.
    - Acceptance trace: US-13.02; MS-020, MS-021, MS-022, MS-034, MS-057, MS-065.
  - **R13.03 · P0 — Have untrusted content treated as data.**
    - Function: Use allowlisted actions, schema validation, fixed budgets and SSRF-safe fetching.
    - Failure/edge behavior: Instructions embedded in pages or documents cannot change system permissions.
    - Acceptance trace: US-13.03; MS-021, MS-065.
  - **R13.04 · P0 — Understand and exercise retention controls.**
    - Function: Publish actual configured retention and implement active-store purge plus receipt status.
    - Failure/edge behavior: Do not claim deletion from backups sooner than verified provider policy.
    - Acceptance trace: US-13.04; MS-063, MS-064, MS-065, MS-069, MS-088.
  - **R13.05 · P0 — Have sensitive data excluded from diagnostics.**
    - Function: Log opaque IDs, hashes, timing and reason codes with secret redaction.
    - Failure/edge behavior: No raw document text, tokens, signed URLs or prompts with personal text in general logs.
    - Acceptance trace: US-13.05; MS-021, MS-065, MS-074.

### R14 — Efficiency, capacity, and operations

- **High-level requirement:** Enable efficiency, capacity, and operations under the system-wide privacy, versioning and budget rules.
  - **R14.01 · P0 — Enforce shared and per-user budgets.**
    - Function: Reserve maximum call cost atomically and reconcile actual usage.
    - Failure/edge behavior: Concurrent requests cannot overspend a shared budget by racing checks.
    - Acceptance trace: US-14.01; MS-015, MS-019, MS-066, MS-068, MS-069.
  - **R14.02 · P0 — Route model work by measured need.**
    - Function: Configure FAST, REASON and optional DEEP roles with capability preflight.
    - Failure/edge behavior: Do not hard-code unverified model IDs or assume DEEP availability.
    - Acceptance trace: US-14.02; MS-003, MS-010, MS-020, MS-068.
  - **R14.03 · P0 — Reuse safe cached artifacts.**
    - Function: Share public parsing only; key private decisions by owner and all input/config versions.
    - Failure/edge behavior: Cache reuse cannot cross users or survive invalidation boundaries.
    - Acceptance trace: US-14.03; MS-062, MS-067.
  - **R14.04 · P0 — Observe reliability without exposing applicant data.**
    - Function: Expose liveness, readiness, redacted metrics and alert thresholds.
    - Failure/edge behavior: Readiness probes must not call paid models.
    - Acceptance trace: US-14.04; MS-068, MS-074, MS-088.
  - **R14.05 · P0 — Serve multiple users at a tested capacity.**
    - Function: Validate 20 browsing sessions and a separate burst of 10 discoveries with bounded concurrency.
    - Failure/edge behavior: Registered-user count cannot be presented as simultaneous-job capacity.
    - Acceptance trace: US-14.05; MS-019, MS-082.

### R15 — Benchmarking and evaluation

- **High-level requirement:** Enable benchmarking and evaluation under the system-wide privacy, versioning and budget rules.
  - **R15.01 · P0 — Use a frozen human-adjudicated benchmark.**
    - Function: Version sources, profiles, labels, splits, clock and manifests.
    - Failure/edge behavior: Test labels cannot be used for prompt tuning.
    - Acceptance trace: US-15.01; MS-013, MS-024, MS-077, MS-085.
  - **R15.02 · P0 — Measure retrieval and requirement extraction separately.**
    - Function: Report bounded-corpus ranking metrics, predicate and mandatory-condition recall and graph accuracy.
    - Failure/edge behavior: Local corpus recall cannot be described as total-web recall.
    - Acceptance trace: US-15.02; MS-077, MS-079, MS-085.
  - **R15.03 · P0 — Measure risky eligibility mistakes and abstention.**
    - Function: Report three-label confusion matrix, MET precision, false promotions, unknown recall and coverage.
    - Failure/edge behavior: Blanket UNKNOWN predictions cannot satisfy the coverage gate.
    - Acceptance trace: US-15.03; MS-078, MS-085.
  - **R15.04 · P0 — Compare model routing fairly.**
    - Function: Freeze prompts and budgets, record paired cases, retries, tokens and latency.
    - Failure/edge behavior: Failed runs stay in the denominator.
    - Acceptance trace: US-15.04; MS-080, MS-085.
  - **R15.05 · P0 — Measure system reliability and user usefulness.**
    - Function: Run isolation, failure recovery, controlled load and a task study targeting eight participants; report actual enrollment and completions.
    - Failure/edge behavior: Report observed sample sizes and limitations instead of universal accuracy.
    - Acceptance trace: US-15.05; MS-005, MS-065, MS-066, MS-076, MS-081, MS-082, MS-085, MS-086.

### R16 — Delivery, demo, and team integration

- **High-level requirement:** Enable delivery, demo, and team integration under the system-wide privacy, versioning and budget rules.
  - **R16.01 · P0 — Share one executable contract.**
    - Function: Use one domain schema, generated client types and common agent rules.
    - Failure/edge behavior: No second independently maintained client DTO model.
    - Acceptance trace: US-16.01; MS-001, MS-002, MS-003, MS-005, MS-075, MS-076.
  - **R16.02 · P0 — Work in bounded dependency-aware tasks.**
    - Function: Each micro-sprint has one prompt, explicit paths, prerequisites and acceptance checks.
    - Failure/edge behavior: A blocked task cannot mark itself complete using placeholder production code.
    - Acceptance trace: US-16.02; MS-001, MS-005, MS-089.
  - **R16.03 · P0 — Deploy and operate a reproducible pilot.**
    - Function: Create deployment configuration, migrations, rollback and a funded operations rota.
    - Failure/edge behavior: A local-only demo does not satisfy the hosted-release gate.
    - Acceptance trace: US-16.03; MS-075, MS-083, MS-088, MS-089.
  - **R16.04 · P0 — Present a concise working demonstration.**
    - Function: Prepare a 2:50 script, live trace, uncertainty case and source/evidence update.
    - Failure/edge behavior: Replays are labeled and never represented as fresh inference.
    - Acceptance trace: US-16.04; MS-084, MS-087, MS-089.
  - **R16.05 · P0 — Submit verifiable project materials.**
    - Function: Prepare public repository, license, setup, demo link, public video and provider feedback.
    - Failure/edge behavior: Do not publish unsupported benchmark numbers or unimplemented features.
    - Acceptance trace: US-16.05; MS-087, MS-089.

## Nonfunctional release requirements

| ID | Area | Target | Verification owner/method |
| --- | --- | --- | --- |
| NFR-01 | Isolation | Zero successful cross-tenant accesses in the release suite; 404 for foreign private IDs | M1/M6; DB and API adversarial suite |
| NFR-02 | Decision quality | Mandatory recall ≥95%; macro-F1 ≥0.88; MET precision ≥98% with ≥40 predicted-MET cases | M4/M6; locked benchmark and denominators |
| NFR-03 | Unknown handling | UNKNOWN recall ≥90%; determinate coverage ≥85% on gold-determinate cases | M6; three-way confusion plus failure column |
| NFR-04 | Grounding | 100% citation validity; ≥95% human material entailment; no observed fabricated material qualifications in reviewed release drafts | M4/M6; sample size disclosed |
| NFR-05 | Latency | Cached browse p95 ≤3s; first useful live result p95 ≤60s at nominal load; synchronous command acceptance p95 ≤1s excluding upload | M3/M6; queue and provider time separated |
| NFR-06 | Capacity | 100 registered synthetic accounts; 20 active browsing sessions; separate 10-run discovery burst; ≥95% full workflow success at nominal load | M6; load report, full versus partial distinguished |
| NFR-07 | Durability | All acknowledged jobs recover after worker death; no duplicate published stage results; terminal/blocked state explicit | M3/M6; kill-and-replay tests |
| NFR-08 | Limits | No unbounded loops; atomic cost reservations; 2 active runs/account, 4 discovery workers initially, provider semaphores configurable | M3; race tests and usage ledger |
| NFR-09 | Privacy | Immediate application-level revocation; active-store purge within configured 24h target; backup policy verified and disclosed | M1/M5; deletion and restore drill |
| NFR-10 | Accessibility | WCAG 2.2 AA-oriented main flows: keyboard, visible focus, labels, contrast; no claim of certification | M2; automated checks and manual keyboard task |
| NFR-11 | Reproducibility | Every reported run has commit, data/config/model/prompt/source hashes, clock, retries, tokens, costs and duration | M6; manifest validation |
| NFR-12 | Operations | Free judge access through judging; maintain service to at least 16 December 2026 UTC, subject to live rules verification | M1; operator rota, funding and synthetic checks |

## Release boundary

All P0 behavior must be implemented, integrated and assessed against the release gates. A failed quality gate requires a narrower supported scope or a visible unresolved state and a revised release decision; it cannot be fixed by relabeling test data. P1 is enabled only after P0 passes and operational budget remains. Any confirmed data leak blocks release. Each selected model endpoint must pass a real, small capability preflight; fake adapters are restricted to explicitly labeled test/fixture modes.
