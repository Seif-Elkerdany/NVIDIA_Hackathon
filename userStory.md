# BenefitBridge — Epics and User Stories

**BenefitBridge · Best Apps and Agents · Six-person implementation package · 4 October 2026**

[requirements.md](requirements.md) | [userStory.md](userStory.md) | [sprints.md](sprints.md) | [design.md](design.md) | [API.md](API.md) | [plan.md](plan.md) | [agent.md](agent.md)

Each low-level requirement has one explicit user story. Acceptance criteria are behavioral and include a failure or edge case. A story may require several micro-sprints; completing one code unit does not automatically complete the story.

## E01 — Identity, consent, and account lifecycle

**Requirement group:** R01. **Primary actor:** applicant.

### US-01.01 — Sign in to a private account

As an applicant, I want to sign in to a private account so that I can resume my work securely.

- **Priority / requirement:** P0 / R01.01.
- **Acceptance:** Given authorized inputs and satisfied prerequisites, verify JWT signature, issuer, audience, expiry and active account status on each protected request.
- **Edge acceptance:** Reject expired tokens and tokens for another project.
- **Implementation:** MS-008, MS-009.
- **Evidence of completion:** reviewer-observed behavior and the scenario checks attached to those micro-sprints; measured gates where applicable.

### US-01.02 — Review and accept processing terms

As an applicant, I want to review and accept processing terms so that I understand where relevant excerpts are processed.

- **Priority / requirement:** P0 / R01.02.
- **Acceptance:** Given authorized inputs and satisfied prerequisites, persist consent version and timestamp before document or inference operations.
- **Edge acceptance:** Reject processing without current consent.
- **Implementation:** MS-008, MS-009.
- **Evidence of completion:** reviewer-observed behavior and the scenario checks attached to those micro-sprints; measured gates where applicable.

### US-01.03 — Maintain one applicant profile per account

As an applicant, I want to maintain one applicant profile per account so that my evidence remains clearly attributable.

- **Priority / requirement:** P0 / R01.03.
- **Acceptance:** Given authorized inputs and satisfied prerequisites, create one empty versioned profile on first account initialization.
- **Edge acceptance:** A caller cannot supply or override owner_id.
- **Implementation:** MS-007, MS-008.
- **Evidence of completion:** reviewer-observed behavior and the scenario checks attached to those micro-sprints; measured gates where applicable.

### US-01.04 — View and change my account preferences

As an applicant, I want to view and change my account preferences so that the interface uses my chosen name and timezone.

- **Priority / requirement:** P0 / R01.04.
- **Acceptance:** Given authorized inputs and satisfied prerequisites, validate display name and IANA timezone without changing identity.
- **Edge acceptance:** Reject unknown fields and invalid timezones.
- **Implementation:** MS-008, MS-069.
- **Evidence of completion:** reviewer-observed behavior and the scenario checks attached to those micro-sprints; measured gates where applicable.

### US-01.05 — Delete my account and obtain a receipt

As an applicant, I want to delete my account and obtain a receipt so that I can remove my private information.

- **Priority / requirement:** P0 / R01.05.
- **Acceptance:** Given authorized inputs and satisfied prerequisites, immediately tombstone access and queue a durable purge with a separate receipt capability.
- **Edge acceptance:** Existing tokens cannot access private objects after tombstoning.
- **Implementation:** MS-015, MS-064, MS-069.
- **Evidence of completion:** reviewer-observed behavior and the scenario checks attached to those micro-sprints; measured gates where applicable.

## E02 — Structured applicant facts and versions

**Requirement group:** R02. **Primary actor:** applicant.

### US-02.01 — Enter structured education, location, and skills

As an applicant, I want to enter structured education, location, and skills so that the service can compare explicit facts.

- **Priority / requirement:** P0 / R02.01.
- **Acceptance:** Given authorized inputs and satisfied prerequisites, validate the typed fact catalog and keep residence, citizenship and authorization distinct.
- **Edge acceptance:** Missing facts never become false or unrestricted eligibility.
- **Implementation:** MS-002, MS-007, MS-017, MS-018.
- **Evidence of completion:** reviewer-observed behavior and the scenario checks attached to those micro-sprints; measured gates where applicable.

### US-02.02 — Record gpa with its original scale

As an applicant, I want to record GPA with its original scale so that numerical rules are evaluated correctly.

- **Priority / requirement:** P0 / R02.02.
- **Acceptance:** Given authorized inputs and satisfied prerequisites, use decimal strings and compatible scales without ad hoc conversion.
- **Edge acceptance:** 3.5 on a 5-point scale cannot satisfy 3.0 on a 4-point scale automatically.
- **Implementation:** MS-002, MS-011, MS-017, MS-018.
- **Evidence of completion:** reviewer-observed behavior and the scenario checks attached to those micro-sprints; measured gates where applicable.

### US-02.03 — Review extracted facts before publication

As an applicant, I want to review extracted facts before publication so that incorrect extraction does not control my decisions.

- **Priority / requirement:** P0 / R02.03.
- **Acceptance:** Given authorized inputs and satisfied prerequisites, accept, correct or reject candidate facts in one version-checked transaction.
- **Edge acceptance:** Unreviewed candidate facts are excluded from the active profile.
- **Implementation:** MS-027, MS-028, MS-029.
- **Evidence of completion:** reviewer-observed behavior and the scenario checks attached to those micro-sprints; measured gates where applicable.

### US-02.04 — Correct information with history

As an applicant, I want to correct information with history so that I can understand which facts produced a result.

- **Priority / requirement:** P0 / R02.04.
- **Acceptance:** Given authorized inputs and satisfied prerequisites, create immutable profile versions and expose historical versions to their owner.
- **Edge acceptance:** Concurrent stale edits return conflict without losing either version.
- **Implementation:** MS-007, MS-017, MS-018, MS-028, MS-062.
- **Evidence of completion:** reviewer-observed behavior and the scenario checks attached to those micro-sprints; measured gates where applicable.

### US-02.05 — See evidence status and disagreements

As an applicant, I want to see evidence status and disagreements so that I know what supports a claim.

- **Priority / requirement:** P0 / R02.05.
- **Acceptance:** Given authorized inputs and satisfied prerequisites, distinguish confirmed self-report, document-supported and conflicting evidence.
- **Edge acceptance:** A document is never described as issuer-authenticated.
- **Implementation:** MS-017, MS-018, MS-027, MS-028.
- **Evidence of completion:** reviewer-observed behavior and the scenario checks attached to those micro-sprints; measured gates where applicable.

## E03 — Document intake and evidence

**Requirement group:** R03. **Primary actor:** applicant.

### US-03.01 — Upload a readable cv or student document

As an applicant, I want to upload a readable CV or student document so that I can avoid retyping supported facts.

- **Priority / requirement:** P0 / R03.01.
- **Acceptance:** Given authorized inputs and satisfied prerequisites, accept digital English PDFs up to 10 MiB and 20 pages using authenticated bounded streaming.
- **Edge acceptance:** Reject forged MIME, oversize, encrypted or malformed documents.
- **Implementation:** MS-012, MS-025, MS-026, MS-029.
- **Evidence of completion:** reviewer-observed behavior and the scenario checks attached to those micro-sprints; measured gates where applicable.

### US-03.02 — Follow document processing

As an applicant, I want to follow document processing so that I know when extracted facts can be reviewed.

- **Priority / requirement:** P0 / R03.02.
- **Acceptance:** Given authorized inputs and satisfied prerequisites, persist upload, queued, parsing, ready and failed states with useful failure reasons.
- **Edge acceptance:** Parser failure does not erase manually entered profile facts.
- **Implementation:** MS-025, MS-026, MS-027, MS-029.
- **Evidence of completion:** reviewer-observed behavior and the scenario checks attached to those micro-sprints; measured gates where applicable.

### US-03.03 — Inspect exact supporting passages

As an applicant, I want to inspect exact supporting passages so that I can check an explanation.

- **Priority / requirement:** P0 / R03.03.
- **Acceptance:** Given authorized inputs and satisfied prerequisites, preserve document version, page, normalized offsets, quote and text hash.
- **Edge acceptance:** Reject citations outside the stored normalized text.
- **Implementation:** MS-006, MS-012, MS-025, MS-026, MS-028, MS-029, MS-037.
- **Evidence of completion:** reviewer-observed behavior and the scenario checks attached to those micro-sprints; measured gates where applicable.

### US-03.04 — Use manual entry when extraction is poor

As an applicant, I want to use manual entry when extraction is poor so that I can continue with a readable alternative.

- **Priority / requirement:** P0 / R03.04.
- **Acceptance:** Given authorized inputs and satisfied prerequisites, mark poor extraction and expose a replacement or structured-entry action.
- **Edge acceptance:** Scanned PDFs are not silently treated as fully parsed.
- **Implementation:** MS-012, MS-027, MS-029.
- **Evidence of completion:** reviewer-observed behavior and the scenario checks attached to those micro-sprints; measured gates where applicable.

### US-03.05 — Remove an uploaded document

As an applicant, I want to remove an uploaded document so that its contents stop supporting new decisions.

- **Priority / requirement:** P0 / R03.05.
- **Acceptance:** Given authorized inputs and satisfied prerequisites, revoke access immediately, invalidate dependent private artifacts and purge objects within configured retention.
- **Edge acceptance:** A cached draft cannot expose text from deleted evidence.
- **Implementation:** MS-063.
- **Evidence of completion:** reviewer-observed behavior and the scenario checks attached to those micro-sprints; measured gates where applicable.

## E04 — Goals, discovery, and candidate intake

**Requirement group:** R04. **Primary actor:** applicant.

### US-04.01 — Describe the opportunities i want

As an applicant, I want to describe the opportunities I want so that the service searches for relevant programs.

- **Priority / requirement:** P0 / R04.01.
- **Acceptance:** Given authorized inputs and satisfied prerequisites, accept a 20–1000 character goal, one lane and bounded preferences.
- **Edge acceptance:** Do not infer citizenship, work authorization or GPA from the goal.
- **Implementation:** MS-034, MS-046, MS-048.
- **Evidence of completion:** reviewer-observed behavior and the scenario checks attached to those micro-sprints; measured gates where applicable.

### US-04.02 — Run a bounded discovery workflow

As an applicant, I want to run a bounded discovery workflow so that I receive useful results without unlimited spend.

- **Priority / requirement:** P0 / R04.02.
- **Acceptance:** Given authorized inputs and satisfied prerequisites, start with up to three queries and allow at most two follow-ups and 40 raw hits.
- **Edge acceptance:** Exhausted budget produces an explicit partial result.
- **Implementation:** MS-022, MS-034, MS-043, MS-046.
- **Evidence of completion:** reviewer-observed behavior and the scenario checks attached to those micro-sprints; measured gates where applicable.

### US-04.03 — Import a public opportunity url

As an applicant, I want to import a public opportunity URL so that I can evaluate a listing I already found.

- **Priority / requirement:** P0 / R04.03.
- **Acceptance:** Given authorized inputs and satisfied prerequisites, accept HTTPS URLs after public-network and source-policy checks.
- **Edge acceptance:** Reject private-network targets, credentials in URLs and login bypasses.
- **Implementation:** MS-021, MS-022, MS-046.
- **Evidence of completion:** reviewer-observed behavior and the scenario checks attached to those micro-sprints; measured gates where applicable.

### US-04.04 — Understand the discovery funnel

As an applicant, I want to understand the discovery funnel so that I know which candidates were actually evaluated.

- **Priority / requirement:** P0 / R04.04.
- **Acceptance:** Given authorized inputs and satisfied prerequisites, show hit, canonical, authoritative, parsed and evaluated counts.
- **Edge acceptance:** Unevaluated candidates cannot be labeled ineligible.
- **Implementation:** MS-043, MS-048.
- **Evidence of completion:** reviewer-observed behavior and the scenario checks attached to those micro-sprints; measured gates where applicable.

### US-04.05 — Receive results as they become available

As an applicant, I want to receive results as they become available so that one failed source does not hide useful work.

- **Priority / requirement:** P0 / R04.05.
- **Acceptance:** Given authorized inputs and satisfied prerequisites, persist candidate results and ordered progress events.
- **Edge acceptance:** A single fetch timeout cannot erase successful candidates.
- **Implementation:** MS-031, MS-043, MS-048.
- **Evidence of completion:** reviewer-observed behavior and the scenario checks attached to those micro-sprints; measured gates where applicable.

## E05 — Authoritative sources, identity, and freshness

**Requirement group:** R05. **Primary actor:** applicant.

### US-05.01 — See the official source for each requirement

As an applicant, I want to see the official source for each requirement so that I can verify the published policy.

- **Priority / requirement:** P0 / R05.01.
- **Acceptance:** Given authorized inputs and satisfied prerequisites, classify current official listings, validated ATS pages and discovery-only reposts.
- **Edge acceptance:** Search snippets alone cannot support an overall positive decision.
- **Implementation:** MS-006, MS-014, MS-022, MS-032, MS-043, MS-045.
- **Evidence of completion:** reviewer-observed behavior and the scenario checks attached to those micro-sprints; measured gates where applicable.

### US-05.02 — Avoid duplicate listings without losing distinct intakes

As an applicant, I want to avoid duplicate listings without losing distinct intakes so that the result list represents real choices.

- **Priority / requirement:** P0 / R05.02.
- **Acceptance:** Given authorized inputs and satisfied prerequisites, canonicalize provider, external identifier, intake and location conservatively.
- **Edge acceptance:** Do not merge different years or regions solely by title.
- **Implementation:** MS-014, MS-033.
- **Evidence of completion:** reviewer-observed behavior and the scenario checks attached to those micro-sprints; measured gates where applicable.

### US-05.03 — Inspect the exact source version

As an applicant, I want to inspect the exact source version so that a decision can be reproduced.

- **Priority / requirement:** P0 / R05.03.
- **Acceptance:** Given authorized inputs and satisfied prerequisites, store immutable normalized text, content hash, retrieval time and source spans.
- **Edge acceptance:** New page content creates a new version instead of rewriting history.
- **Implementation:** MS-002, MS-006, MS-014, MS-032, MS-045.
- **Evidence of completion:** reviewer-observed behavior and the scenario checks attached to those micro-sprints; measured gates where applicable.

### US-05.04 — See freshness and availability separately

As an applicant, I want to see freshness and availability separately so that an old or inaccessible listing does not mislead me.

- **Priority / requirement:** P0 / R05.04.
- **Acceptance:** Given authorized inputs and satisfied prerequisites, use 24-hour job and near-deadline freshness, 72-hour program freshness and explicit availability.
- **Edge acceptance:** Inaccessible means UNAVAILABLE rather than automatically CLOSED.
- **Implementation:** MS-032, MS-042, MS-061.
- **Evidence of completion:** reviewer-observed behavior and the scenario checks attached to those micro-sprints; measured gates where applicable.

### US-05.05 — Refresh an opportunity and see material changes

As an applicant, I want to refresh an opportunity and see material changes so that I can act on current requirements.

- **Priority / requirement:** P0 / R05.05.
- **Acceptance:** Given authorized inputs and satisfied prerequisites, fetch within budgets, detect semantic changes and invalidate affected evaluations.
- **Edge acceptance:** Fetch timestamp alone cannot resolve conflicting official policies.
- **Implementation:** MS-061, MS-062.
- **Evidence of completion:** reviewer-observed behavior and the scenario checks attached to those micro-sprints; measured gates where applicable.

## E06 — Requirement graph extraction

**Requirement group:** R06. **Primary actor:** applicant.

### US-06.01 — See mandatory and preferred requirements separately

As an applicant, I want to see mandatory and preferred requirements separately so that preferences do not incorrectly exclude me.

- **Priority / requirement:** P0 / R06.01.
- **Acceptance:** Given authorized inputs and satisfied prerequisites, preserve MANDATORY, PREFERRED, OPTIONAL and AMBIGUOUS modalities.
- **Edge acceptance:** Preferred criteria must not enter the mandatory root.
- **Implementation:** MS-002, MS-035, MS-045, MS-049.
- **Evidence of completion:** reviewer-observed behavior and the scenario checks attached to those micro-sprints; measured gates where applicable.

### US-06.02 — Understand alternatives and exceptions

As an applicant, I want to understand alternatives and exceptions so that the decision reflects the actual policy.

- **Priority / requirement:** P0 / R06.02.
- **Acceptance:** Given authorized inputs and satisfied prerequisites, represent ALL, ANY, NOT and typed predicate nodes with stable IDs.
- **Edge acceptance:** Reject cycles, dangling children and unsupported operators.
- **Implementation:** MS-002, MS-023, MS-035, MS-036, MS-038.
- **Evidence of completion:** reviewer-observed behavior and the scenario checks attached to those micro-sprints; measured gates where applicable.

### US-06.03 — See provenance for every material rule

As an applicant, I want to see provenance for every material rule so that I can audit extraction.

- **Priority / requirement:** P0 / R06.03.
- **Acceptance:** Given authorized inputs and satisfied prerequisites, attach exact source spans and applicable intake/scope to every predicate.
- **Edge acceptance:** Invented or unrelated quotations fail publication checks.
- **Implementation:** MS-006, MS-014, MS-035, MS-036, MS-045.
- **Evidence of completion:** reviewer-observed behavior and the scenario checks attached to those micro-sprints; measured gates where applicable.

### US-06.04 — Know when source context is incomplete

As an applicant, I want to know when source context is incomplete so that the service does not assume missing rules.

- **Priority / requirement:** P0 / R06.04.
- **Acceptance:** Given authorized inputs and satisfied prerequisites, record COMPLETE, INCOMPLETE or CONFLICTED completeness and extraction issues.
- **Edge acceptance:** Incomplete extraction blocks an overall MET publication.
- **Implementation:** MS-035, MS-036, MS-043.
- **Evidence of completion:** reviewer-observed behavior and the scenario checks attached to those micro-sprints; measured gates where applicable.

### US-06.05 — Preserve dates, scales and policy ambiguity

As an applicant, I want to preserve dates, scales and policy ambiguity so that rules are compared without invented assumptions.

- **Priority / requirement:** P0 / R06.05.
- **Acceptance:** Given authorized inputs and satisfied prerequisites, keep date precision, timezone, GPA scale and reference event explicit.
- **Edge acceptance:** Date-only deadlines cannot become invented midnight timestamps.
- **Implementation:** MS-011, MS-035.
- **Evidence of completion:** reviewer-observed behavior and the scenario checks attached to those micro-sprints; measured gates where applicable.

## E07 — Eligibility and decision verification

**Requirement group:** R07. **Primary actor:** applicant.

### US-07.01 — Receive a reproducible requirements decision

As an applicant, I want to receive a reproducible requirements decision so that I understand whether published mandatory conditions are met.

- **Priority / requirement:** P0 / R07.01.
- **Acceptance:** Given authorized inputs and satisfied prerequisites, evaluate typed predicates with three-valued logic and expose MET, NOT_MET or UNKNOWN.
- **Edge acceptance:** Missing information cannot be promoted to MET.
- **Implementation:** MS-002, MS-023, MS-038, MS-040, MS-044, MS-047.
- **Evidence of completion:** reviewer-observed behavior and the scenario checks attached to those micro-sprints; measured gates where applicable.

### US-07.02 — Have numerical and logical rules evaluated deterministically

As an applicant, I want to have numerical and logical rules evaluated deterministically so that simple comparisons remain reliable.

- **Priority / requirement:** P0 / R07.02.
- **Acceptance:** Given authorized inputs and satisfied prerequisites, use Decimal, tested date intervals and complete truth tables.
- **Edge acceptance:** Do not execute model-generated code or arithmetic expressions.
- **Implementation:** MS-011, MS-023.
- **Evidence of completion:** reviewer-observed behavior and the scenario checks attached to those micro-sprints; measured gates where applicable.

### US-07.03 — Receive supported semantic interpretations

As an applicant, I want to receive supported semantic interpretations so that related experience can be considered carefully.

- **Priority / requirement:** P0 / R07.03.
- **Acceptance:** Given authorized inputs and satisfied prerequisites, use bounded evidence bundles and schema-constrained model outputs for allowlisted semantic predicates.
- **Edge acceptance:** Unsupported entailment yields UNKNOWN.
- **Implementation:** MS-020, MS-037, MS-039.
- **Evidence of completion:** reviewer-observed behavior and the scenario checks attached to those micro-sprints; measured gates where applicable.

### US-07.04 — See a checked explanation of the decision

As an applicant, I want to see a checked explanation of the decision so that every decisive claim has support.

- **Priority / requirement:** P0 / R07.04.
- **Acceptance:** Given authorized inputs and satisfied prerequisites, validate source IDs, evidence ownership, input versions and decisive paths before publication.
- **Edge acceptance:** Invalid grounding downgrades or blocks the affected decision.
- **Implementation:** MS-036, MS-038, MS-040, MS-041, MS-044, MS-047, MS-049.
- **Evidence of completion:** reviewer-observed behavior and the scenario checks attached to those micro-sprints; measured gates where applicable.

### US-07.05 — Understand unresolved cases

As an applicant, I want to understand unresolved cases so that I know the specific next action.

- **Priority / requirement:** P0 / R07.05.
- **Acceptance:** Given authorized inputs and satisfied prerequisites, expose reason codes and exact missing attributes without fabricated certainty.
- **Edge acceptance:** Model self-confidence is not an eligibility probability.
- **Implementation:** MS-039, MS-040, MS-041, MS-047, MS-049.
- **Evidence of completion:** reviewer-observed behavior and the scenario checks attached to those micro-sprints; measured gates where applicable.

## E08 — Ranking, readiness, and clarification

**Requirement group:** R08. **Primary actor:** applicant.

### US-08.01 — See eligibility, availability, fit and readiness separately

As an applicant, I want to see eligibility, availability, fit and readiness separately so that I can distinguish qualification from preparation.

- **Priority / requirement:** P0 / R08.01.
- **Acceptance:** Given authorized inputs and satisfied prerequisites, display four independent fields and their explanations.
- **Edge acceptance:** A high fit score cannot hide a failed mandatory condition.
- **Implementation:** MS-002, MS-040, MS-042, MS-044, MS-048.
- **Evidence of completion:** reviewer-observed behavior and the scenario checks attached to those micro-sprints; measured gates where applicable.

### US-08.02 — Receive a transparent result ordering

As an applicant, I want to receive a transparent result ordering so that the most actionable opportunities appear first.

- **Priority / requirement:** P0 / R08.02.
- **Acceptance:** Given authorized inputs and satisfied prerequisites, use deterministic group ordering and explicit preference weights.
- **Edge acceptance:** Unknown components cannot be silently assigned perfect fit.
- **Implementation:** MS-042, MS-048.
- **Evidence of completion:** reviewer-observed behavior and the scenario checks attached to those micro-sprints; measured gates where applicable.

### US-08.03 — Answer targeted clarification questions

As an applicant, I want to answer targeted clarification questions so that only relevant missing facts interrupt my progress.

- **Priority / requirement:** P0 / R08.03.
- **Acceptance:** Given authorized inputs and satisfied prerequisites, ask at most three supported fact questions per round and two rounds per run.
- **Edge acceptance:** A repeated unanswered question cannot trigger an infinite loop.
- **Implementation:** MS-038, MS-050, MS-051.
- **Evidence of completion:** reviewer-observed behavior and the scenario checks attached to those micro-sprints; measured gates where applicable.

### US-08.04 — Resume evaluation after clarification

As an applicant, I want to resume evaluation after clarification so that my answers update the correct decision.

- **Priority / requirement:** P0 / R08.04.
- **Acceptance:** Given authorized inputs and satisfied prerequisites, create a new profile version and resume from a pinned evaluation checkpoint.
- **Edge acceptance:** Concurrent profile edits cause a conflict instead of overwriting.
- **Implementation:** MS-038, MS-050, MS-051.
- **Evidence of completion:** reviewer-observed behavior and the scenario checks attached to those micro-sprints; measured gates where applicable.

### US-08.05 — See application readiness as completed tasks

As an applicant, I want to see application readiness as completed tasks so that I know what remains to prepare.

- **Priority / requirement:** P0 / R08.05.
- **Acceptance:** Given authorized inputs and satisfied prerequisites, calculate completed applicable required items divided by known applicable required items.
- **Edge acceptance:** Generated but unaccepted text does not count as complete.
- **Implementation:** MS-042, MS-055, MS-056.
- **Evidence of completion:** reviewer-observed behavior and the scenario checks attached to those micro-sprints; measured gates where applicable.

## E09 — Application workspaces and truthful drafts

**Requirement group:** R09. **Primary actor:** applicant.

### US-09.01 — Create an application workspace

As an applicant, I want to create an application workspace so that my checklist and materials stay together.

- **Priority / requirement:** P0 / R09.01.
- **Acceptance:** Given authorized inputs and satisfied prerequisites, pin opportunity and evaluation inputs and create deterministic checklist items.
- **Edge acceptance:** Do not create a current application from stale or foreign-owned inputs.
- **Implementation:** MS-052, MS-056, MS-060.
- **Evidence of completion:** reviewer-observed behavior and the scenario checks attached to those micro-sprints; measured gates where applicable.

### US-09.02 — Track required application tasks

As an applicant, I want to track required application tasks so that I can prepare an application systematically.

- **Priority / requirement:** P0 / R09.02.
- **Acceptance:** Given authorized inputs and satisfied prerequisites, expose task evidence, completion state and version-checked updates.
- **Edge acceptance:** Optional or nonapplicable tasks cannot inflate the required denominator.
- **Implementation:** MS-052, MS-055, MS-056, MS-060.
- **Evidence of completion:** reviewer-observed behavior and the scenario checks attached to those micro-sprints; measured gates where applicable.

### US-09.03 — Generate a concise statement grounded in my facts

As an applicant, I want to generate a concise statement grounded in my facts so that I can start writing without invented qualifications.

- **Priority / requirement:** P0 / R09.03.
- **Acceptance:** Given authorized inputs and satisfied prerequisites, generate one 150–500 word statement with claim-to-fact links and no unsupported material claims.
- **Edge acceptance:** Unsupported claims must be removed or explicitly requested as missing input.
- **Implementation:** MS-057, MS-058, MS-059, MS-060.
- **Evidence of completion:** reviewer-observed behavior and the scenario checks attached to those micro-sprints; measured gates where applicable.

### US-09.04 — Review and accept a specific draft version

As an applicant, I want to review and accept a specific draft version so that I remain responsible for application materials.

- **Priority / requirement:** P0 / R09.04.
- **Acceptance:** Given authorized inputs and satisfied prerequisites, validate edits and bind acceptance to exact draft and input versions.
- **Edge acceptance:** Edited or invalidated drafts lose acceptance.
- **Implementation:** MS-052, MS-058, MS-059, MS-060.
- **Evidence of completion:** reviewer-observed behavior and the scenario checks attached to those micro-sprints; measured gates where applicable.

### US-09.05 — Export reviewed materials

As an applicant, I want to export reviewed materials so that I can submit through the provider myself.

- **Priority / requirement:** P0 / R09.05.
- **Acceptance:** Given authorized inputs and satisfied prerequisites, export UTF-8 Markdown containing current accepted text, checklist and source links.
- **Edge acceptance:** Do not send emails, submit forms or sign declarations.
- **Implementation:** MS-059, MS-060.
- **Evidence of completion:** reviewer-observed behavior and the scenario checks attached to those micro-sprints; measured gates where applicable.

## E10 — Durable workflows and user progress

**Requirement group:** R10. **Primary actor:** applicant.

### US-10.01 — Start a job safely even if the network retries

As an applicant, I want to start a job safely even if the network retries so that my request is executed once logically.

- **Priority / requirement:** P0 / R10.01.
- **Acceptance:** Given authorized inputs and satisfied prerequisites, use idempotency keys and a transactional run/outbox insert.
- **Edge acceptance:** Reusing a key with a different payload returns conflict.
- **Implementation:** MS-015, MS-016, MS-030, MS-046, MS-066.
- **Evidence of completion:** reviewer-observed behavior and the scenario checks attached to those micro-sprints; measured gates where applicable.

### US-10.02 — See durable workflow status

As an applicant, I want to see durable workflow status so that I can leave and return.

- **Priority / requirement:** P0 / R10.02.
- **Acceptance:** Given authorized inputs and satisfied prerequisites, persist QUEUED, RUNNING, WAITING_USER and terminal states with ordered events.
- **Edge acceptance:** No browser connection is required to keep work alive.
- **Implementation:** MS-003, MS-015, MS-016, MS-030, MS-031.
- **Evidence of completion:** reviewer-observed behavior and the scenario checks attached to those micro-sprints; measured gates where applicable.

### US-10.03 — Cancel expensive work

As an applicant, I want to cancel expensive work so that I can stop further processing.

- **Priority / requirement:** P0 / R10.03.
- **Acceptance:** Given authorized inputs and satisfied prerequisites, set cancel_requested and stop at safe checkpoints while retaining completed artifacts.
- **Edge acceptance:** Do not claim an in-flight provider request can always be recalled.
- **Implementation:** MS-016, MS-030, MS-031, MS-066.
- **Evidence of completion:** reviewer-observed behavior and the scenario checks attached to those micro-sprints; measured gates where applicable.

### US-10.04 — Recover from worker or provider failures

As an applicant, I want to recover from worker or provider failures so that accepted work is not lost.

- **Priority / requirement:** P0 / R10.04.
- **Acceptance:** Given authorized inputs and satisfied prerequisites, use leases, heartbeats, bounded retries and idempotent stage outputs.
- **Edge acceptance:** Repeated worker delivery cannot duplicate a published evaluation.
- **Implementation:** MS-015, MS-016, MS-044, MS-066.
- **Evidence of completion:** reviewer-observed behavior and the scenario checks attached to those micro-sprints; measured gates where applicable.

### US-10.05 — Resume event streaming after disconnection

As an applicant, I want to resume event streaming after disconnection so that the progress view remains accurate.

- **Priority / requirement:** P0 / R10.05.
- **Acceptance:** Given authorized inputs and satisfied prerequisites, replay monotonic owner-scoped event IDs with a bounded retention policy.
- **Edge acceptance:** Events from another account return the same not-found response.
- **Implementation:** MS-016, MS-030, MS-031.
- **Evidence of completion:** reviewer-observed behavior and the scenario checks attached to those micro-sprints; measured gates where applicable.

## E11 — Saved opportunities and optional watch

**Requirement group:** R11. **Primary actor:** applicant.

### US-11.01 — Save and remove opportunities

As an applicant, I want to save and remove opportunities so that I can return to my shortlist.

- **Priority / requirement:** P0 / R11.01.
- **Acceptance:** Given authorized inputs and satisfied prerequisites, provide owner-scoped idempotent save and delete operations.
- **Edge acceptance:** Saving a public opportunity must not expose another applicant evaluation.
- **Implementation:** MS-052, MS-053, MS-054.
- **Evidence of completion:** reviewer-observed behavior and the scenario checks attached to those micro-sprints; measured gates where applicable.

### US-11.02 — Review saved opportunities after changes

As an applicant, I want to review saved opportunities after changes so that my shortlist does not show stale decisions as current.

- **Priority / requirement:** P0 / R11.02.
- **Acceptance:** Given authorized inputs and satisfied prerequisites, show invalidated badges and enqueue deduplicated refresh or reevaluation.
- **Edge acceptance:** Old immutable evaluations remain historical, never relabeled as fresh.
- **Implementation:** MS-053, MS-054, MS-061, MS-062.
- **Evidence of completion:** reviewer-observed behavior and the scenario checks attached to those micro-sprints; measured gates where applicable.

### US-11.03 — Watch selected saved opportunities

As an applicant, I want to watch selected saved opportunities so that I learn of changed public requirements.

- **Priority / requirement:** P1 / R11.03.
- **Acceptance:** Given authorized inputs and satisfied prerequisites, poll only saved official pages at a configured cadence with bounded fanout.
- **Edge acceptance:** Repeated unchanged content creates no notification.
- **Implementation:** MS-070, MS-071, MS-072, MS-073.
- **Evidence of completion:** reviewer-observed behavior and the scenario checks attached to those micro-sprints; measured gates where applicable.

### US-11.04 — Receive in-app change notifications

As an applicant, I want to receive in-app change notifications so that I know what to review.

- **Priority / requirement:** P1 / R11.04.
- **Acceptance:** Given authorized inputs and satisfied prerequisites, create one owner-scoped notification per material source version change.
- **Edge acceptance:** No external email or calendar integration is implied.
- **Implementation:** MS-070, MS-071, MS-072, MS-073.
- **Evidence of completion:** reviewer-observed behavior and the scenario checks attached to those micro-sprints; measured gates where applicable.

### US-11.05 — Pause a watch

As an applicant, I want to pause a watch so that I control recurring processing.

- **Priority / requirement:** P1 / R11.05.
- **Acceptance:** Given authorized inputs and satisfied prerequisites, disable scheduled work without deleting the saved opportunity.
- **Edge acceptance:** A paused watch cannot enqueue new refresh jobs.
- **Implementation:** MS-070, MS-071, MS-072, MS-073.
- **Evidence of completion:** reviewer-observed behavior and the scenario checks attached to those micro-sprints; measured gates where applicable.

## E12 — Usable and accessible web interface

**Requirement group:** R12. **Primary actor:** applicant.

### US-12.01 — Follow a clear onboarding flow

As an applicant, I want to follow a clear onboarding flow so that I can reach my first useful result.

- **Priority / requirement:** P0 / R12.01.
- **Acceptance:** Given authorized inputs and satisfied prerequisites, offer account, consent, profile, optional documents and goal steps.
- **Edge acceptance:** Uploading a document is not mandatory to try the service.
- **Implementation:** MS-004, MS-009, MS-018.
- **Evidence of completion:** reviewer-observed behavior and the scenario checks attached to those micro-sprints; measured gates where applicable.

### US-12.02 — Inspect decision details in one place

As an applicant, I want to inspect decision details in one place so that I can trace policy to applicant evidence.

- **Priority / requirement:** P0 / R12.02.
- **Acceptance:** Given authorized inputs and satisfied prerequisites, present requirement, source passage, applicant fact, outcome and next action together.
- **Edge acceptance:** Do not render private provider internals as product guidance.
- **Implementation:** MS-049.
- **Evidence of completion:** reviewer-observed behavior and the scenario checks attached to those micro-sprints; measured gates where applicable.

### US-12.03 — Understand empty, loading and failure states

As an applicant, I want to understand empty, loading and failure states so that I know what to do next.

- **Priority / requirement:** P0 / R12.03.
- **Acceptance:** Given authorized inputs and satisfied prerequisites, design every main screen for empty, pending, partial, failed and stale data.
- **Edge acceptance:** Errors cannot be represented by endless spinners.
- **Implementation:** MS-004, MS-031, MS-051.
- **Evidence of completion:** reviewer-observed behavior and the scenario checks attached to those micro-sprints; measured gates where applicable.

### US-12.04 — Use the application by keyboard

As an applicant, I want to use the application by keyboard so that the main workflow is accessible.

- **Priority / requirement:** P0 / R12.04.
- **Acceptance:** Given authorized inputs and satisfied prerequisites, provide semantic controls, focus management, readable contrast and text status labels.
- **Edge acceptance:** Color alone cannot communicate eligibility.
- **Implementation:** MS-004, MS-049, MS-081, MS-086.
- **Evidence of completion:** reviewer-observed behavior and the scenario checks attached to those micro-sprints; measured gates where applicable.

### US-12.05 — Try a synthetic judge scenario

As an applicant, I want to try a synthetic judge scenario so that I can evaluate the product without private documents.

- **Priority / requirement:** P0 / R12.05.
- **Acceptance:** Given authorized inputs and satisfied prerequisites, provide isolated demo tenants and explicit synthetic-data labels.
- **Edge acceptance:** Reset affects only the requesting demo tenant.
- **Implementation:** MS-084.
- **Evidence of completion:** reviewer-observed behavior and the scenario checks attached to those micro-sprints; measured gates where applicable.

## E13 — Privacy and abuse resistance

**Requirement group:** R13. **Primary actor:** applicant.

### US-13.01 — Keep my evidence isolated

As an applicant, I want to keep my evidence isolated so that other accounts cannot access my private work.

- **Priority / requirement:** P0 / R13.01.
- **Acceptance:** Given authorized inputs and satisfied prerequisites, enforce server ownership checks, row-level security and composite foreign keys.
- **Edge acceptance:** Guessed IDs, exports, streams and signed links cannot cross tenants.
- **Implementation:** MS-007, MS-008, MS-025, MS-037, MS-065.
- **Evidence of completion:** reviewer-observed behavior and the scenario checks attached to those micro-sprints; measured gates where applicable.

### US-13.02 — Limit information sent to providers

As an applicant, I want to limit information sent to providers so that external processing uses only relevant context.

- **Priority / requirement:** P0 / R13.02.
- **Acceptance:** Given authorized inputs and satisfied prerequisites, search receives generalized goals; inference receives minimum necessary spans.
- **Edge acceptance:** Raw CVs, names, email and private URLs cannot enter search queries.
- **Implementation:** MS-020, MS-021, MS-022, MS-034, MS-057, MS-065.
- **Evidence of completion:** reviewer-observed behavior and the scenario checks attached to those micro-sprints; measured gates where applicable.

### US-13.03 — Have untrusted content treated as data

As an applicant, I want to have untrusted content treated as data so that source text cannot take control of tools.

- **Priority / requirement:** P0 / R13.03.
- **Acceptance:** Given authorized inputs and satisfied prerequisites, use allowlisted actions, schema validation, fixed budgets and SSRF-safe fetching.
- **Edge acceptance:** Instructions embedded in pages or documents cannot change system permissions.
- **Implementation:** MS-021, MS-065.
- **Evidence of completion:** reviewer-observed behavior and the scenario checks attached to those micro-sprints; measured gates where applicable.

### US-13.04 — Understand and exercise retention controls

As an applicant, I want to understand and exercise retention controls so that private data is removed predictably.

- **Priority / requirement:** P0 / R13.04.
- **Acceptance:** Given authorized inputs and satisfied prerequisites, publish actual configured retention and implement active-store purge plus receipt status.
- **Edge acceptance:** Do not claim deletion from backups sooner than verified provider policy.
- **Implementation:** MS-063, MS-064, MS-065, MS-069, MS-088.
- **Evidence of completion:** reviewer-observed behavior and the scenario checks attached to those micro-sprints; measured gates where applicable.

### US-13.05 — Have sensitive data excluded from diagnostics

As an applicant, I want to have sensitive data excluded from diagnostics so that operational logs do not become a second evidence store.

- **Priority / requirement:** P0 / R13.05.
- **Acceptance:** Given authorized inputs and satisfied prerequisites, log opaque IDs, hashes, timing and reason codes with secret redaction.
- **Edge acceptance:** No raw document text, tokens, signed URLs or prompts with personal text in general logs.
- **Implementation:** MS-021, MS-065, MS-074.
- **Evidence of completion:** reviewer-observed behavior and the scenario checks attached to those micro-sprints; measured gates where applicable.

## E14 — Efficiency, capacity, and operations

**Requirement group:** R14. **Primary actor:** operator.

### US-14.01 — Enforce shared and per-user budgets

As an operator, I want to enforce shared and per-user budgets so that a pilot remains affordable and fair.

- **Priority / requirement:** P0 / R14.01.
- **Acceptance:** Given authorized inputs and satisfied prerequisites, reserve maximum call cost atomically and reconcile actual usage.
- **Edge acceptance:** Concurrent requests cannot overspend a shared budget by racing checks.
- **Implementation:** MS-015, MS-019, MS-066, MS-068, MS-069.
- **Evidence of completion:** reviewer-observed behavior and the scenario checks attached to those micro-sprints; measured gates where applicable.

### US-14.02 — Route model work by measured need

As an operator, I want to route model work by measured need so that inference stays useful within latency and cost limits.

- **Priority / requirement:** P0 / R14.02.
- **Acceptance:** Given authorized inputs and satisfied prerequisites, configure FAST, REASON and optional DEEP roles with capability preflight.
- **Edge acceptance:** Do not hard-code unverified model IDs or assume DEEP availability.
- **Implementation:** MS-003, MS-010, MS-020, MS-068.
- **Evidence of completion:** reviewer-observed behavior and the scenario checks attached to those micro-sprints; measured gates where applicable.

### US-14.03 — Reuse safe cached artifacts

As an operator, I want to reuse safe cached artifacts so that repeated work costs less.

- **Priority / requirement:** P0 / R14.03.
- **Acceptance:** Given authorized inputs and satisfied prerequisites, share public parsing only; key private decisions by owner and all input/config versions.
- **Edge acceptance:** Cache reuse cannot cross users or survive invalidation boundaries.
- **Implementation:** MS-062, MS-067.
- **Evidence of completion:** reviewer-observed behavior and the scenario checks attached to those micro-sprints; measured gates where applicable.

### US-14.04 — Observe reliability without exposing applicant data

As an operator, I want to observe reliability without exposing applicant data so that I can diagnose issues promptly.

- **Priority / requirement:** P0 / R14.04.
- **Acceptance:** Given authorized inputs and satisfied prerequisites, expose liveness, readiness, redacted metrics and alert thresholds.
- **Edge acceptance:** Readiness probes must not call paid models.
- **Implementation:** MS-068, MS-074, MS-088.
- **Evidence of completion:** reviewer-observed behavior and the scenario checks attached to those micro-sprints; measured gates where applicable.

### US-14.05 — Serve multiple users at a tested capacity

As an operator, I want to serve multiple users at a tested capacity so that accepted jobs remain responsive under contention.

- **Priority / requirement:** P0 / R14.05.
- **Acceptance:** Given authorized inputs and satisfied prerequisites, validate 20 browsing sessions and a separate burst of 10 discoveries with bounded concurrency.
- **Edge acceptance:** Registered-user count cannot be presented as simultaneous-job capacity.
- **Implementation:** MS-019, MS-082.
- **Evidence of completion:** reviewer-observed behavior and the scenario checks attached to those micro-sprints; measured gates where applicable.

## E15 — Benchmarking and evaluation

**Requirement group:** R15. **Primary actor:** evaluator.

### US-15.01 — Use a frozen human-adjudicated benchmark

As an evaluator, I want to use a frozen human-adjudicated benchmark so that quality measurements are reproducible.

- **Priority / requirement:** P0 / R15.01.
- **Acceptance:** Given authorized inputs and satisfied prerequisites, version sources, profiles, labels, splits, clock and manifests.
- **Edge acceptance:** Test labels cannot be used for prompt tuning.
- **Implementation:** MS-013, MS-024, MS-077, MS-085.
- **Evidence of completion:** reviewer-observed behavior and the scenario checks attached to those micro-sprints; measured gates where applicable.

### US-15.02 — Measure retrieval and requirement extraction separately

As an evaluator, I want to measure retrieval and requirement extraction separately so that I can locate errors in the pipeline.

- **Priority / requirement:** P0 / R15.02.
- **Acceptance:** Given authorized inputs and satisfied prerequisites, report bounded-corpus ranking metrics, predicate and mandatory-condition recall and graph accuracy.
- **Edge acceptance:** Local corpus recall cannot be described as total-web recall.
- **Implementation:** MS-077, MS-079, MS-085.
- **Evidence of completion:** reviewer-observed behavior and the scenario checks attached to those micro-sprints; measured gates where applicable.

### US-15.03 — Measure risky eligibility mistakes and abstention

As an evaluator, I want to measure risky eligibility mistakes and abstention so that accuracy cannot hide false positive decisions.

- **Priority / requirement:** P0 / R15.03.
- **Acceptance:** Given authorized inputs and satisfied prerequisites, report three-label confusion matrix, MET precision, false promotions, unknown recall and coverage.
- **Edge acceptance:** Blanket UNKNOWN predictions cannot satisfy the coverage gate.
- **Implementation:** MS-078, MS-085.
- **Evidence of completion:** reviewer-observed behavior and the scenario checks attached to those micro-sprints; measured gates where applicable.

### US-15.04 — Compare model routing fairly

As an evaluator, I want to compare model routing fairly so that cost and quality trade-offs are defensible.

- **Priority / requirement:** P0 / R15.04.
- **Acceptance:** Given authorized inputs and satisfied prerequisites, freeze prompts and budgets, record paired cases, retries, tokens and latency.
- **Edge acceptance:** Failed runs stay in the denominator.
- **Implementation:** MS-080, MS-085.
- **Evidence of completion:** reviewer-observed behavior and the scenario checks attached to those micro-sprints; measured gates where applicable.

### US-15.05 — Measure system reliability and user usefulness

As an evaluator, I want to measure system reliability and user usefulness so that a working demo is supported by evidence.

- **Priority / requirement:** P0 / R15.05.
- **Acceptance:** Given authorized inputs and satisfied prerequisites, run isolation, failure recovery, controlled load and a task study targeting eight participants; report actual enrollment and completions.
- **Edge acceptance:** Report observed sample sizes and limitations instead of universal accuracy.
- **Implementation:** MS-005, MS-065, MS-066, MS-076, MS-081, MS-082, MS-085, MS-086.
- **Evidence of completion:** reviewer-observed behavior and the scenario checks attached to those micro-sprints; measured gates where applicable.

## E16 — Delivery, demo, and team integration

**Requirement group:** R16. **Primary actor:** team member.

### US-16.01 — Share one executable contract

As a team member, I want to share one executable contract so that six development sessions integrate predictably.

- **Priority / requirement:** P0 / R16.01.
- **Acceptance:** Given authorized inputs and satisfied prerequisites, use one domain schema, generated client types and common agent rules.
- **Edge acceptance:** No second independently maintained client DTO model.
- **Implementation:** MS-001, MS-002, MS-003, MS-005, MS-075, MS-076.
- **Evidence of completion:** reviewer-observed behavior and the scenario checks attached to those micro-sprints; measured gates where applicable.

### US-16.02 — Work in bounded dependency-aware tasks

As a team member, I want to work in bounded dependency-aware tasks so that AI-assisted work can be reviewed and merged.

- **Priority / requirement:** P0 / R16.02.
- **Acceptance:** Given authorized inputs and satisfied prerequisites, each micro-sprint has one prompt, explicit paths, prerequisites and acceptance checks.
- **Edge acceptance:** A blocked task cannot mark itself complete using placeholder production code.
- **Implementation:** MS-001, MS-005, MS-089.
- **Evidence of completion:** reviewer-observed behavior and the scenario checks attached to those micro-sprints; measured gates where applicable.

### US-16.03 — Deploy and operate a reproducible pilot

As a team member, I want to deploy and operate a reproducible pilot so that judges can use the service through judging.

- **Priority / requirement:** P0 / R16.03.
- **Acceptance:** Given authorized inputs and satisfied prerequisites, create deployment configuration, migrations, rollback and a funded operations rota.
- **Edge acceptance:** A local-only demo does not satisfy the hosted-release gate.
- **Implementation:** MS-075, MS-083, MS-088, MS-089.
- **Evidence of completion:** reviewer-observed behavior and the scenario checks attached to those micro-sprints; measured gates where applicable.

### US-16.04 — Present a concise working demonstration

As a team member, I want to present a concise working demonstration so that judges understand the product and its limits.

- **Priority / requirement:** P0 / R16.04.
- **Acceptance:** Given authorized inputs and satisfied prerequisites, prepare a 2:50 script, live trace, uncertainty case and source/evidence update.
- **Edge acceptance:** Replays are labeled and never represented as fresh inference.
- **Implementation:** MS-084, MS-087, MS-089.
- **Evidence of completion:** reviewer-observed behavior and the scenario checks attached to those micro-sprints; measured gates where applicable.

### US-16.05 — Submit verifiable project materials

As a team member, I want to submit verifiable project materials so that the entry meets the published deliverable requirements.

- **Priority / requirement:** P0 / R16.05.
- **Acceptance:** Given authorized inputs and satisfied prerequisites, prepare public repository, license, setup, demo link, public video and provider feedback.
- **Edge acceptance:** Do not publish unsupported benchmark numbers or unimplemented features.
- **Implementation:** MS-087, MS-089.
- **Evidence of completion:** reviewer-observed behavior and the scenario checks attached to those micro-sprints; measured gates where applicable.
