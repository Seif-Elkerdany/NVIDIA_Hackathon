# BenefitBridge — REST API Contract

**BenefitBridge · Best Apps and Agents · Six-person implementation package · 4 October 2026**

[requirements.md](requirements.md) | [userStory.md](userStory.md) | [sprints.md](sprints.md) | [design.md](design.md) | [API.md](API.md) | [plan.md](plan.md) | [agent.md](agent.md)

## Protocol and authentication

Use REST JSON under `/api/v1`; GraphQL is intentionally not added. Python Pydantic models are the executable schema source, FastAPI emits OpenAPI 3.1, and the TypeScript client/types are generated from that schema. Keep the stable operation IDs below. Every object rejects unknown keys. All examples are illustrative and synthetic; they are not a seeded relational database. Strings abbreviated for display are explicitly identified. Implement contract fixtures with fully valid values and actual source/evidence relations.

- **USER:** `Authorization: Bearer <managed-auth access token>`; verify fixed algorithm allowlist, issuer, audience, signature, expiry and active local account. Resolve `owner_id` exclusively from verified JWT `sub`. Do not accept it in paths or bodies. All private references are owner checked. Sources/opportunities are shared public data but these routes still require USER to limit abuse.
- **DEMO:** USER plus `is_demo=true` and enabled demo capability. No shared global mutable demo tenant.
- **RECEIPT:** `Authorization: DeletionReceipt <opaque token>` for the single deletion-receipt route; it grants no other access.
- **PUBLIC:** no auth; strictly nonprivate health/capability information.
- Signup, login, email verification, password reset and token refresh use the Supabase Auth SDK directly. They are not duplicate application endpoints. Browser session is memory-only in P0 (`persistSession=false`); refresh while the page is open, re-login after reload. Bearer tokens are never placed in URLs, localStorage, logs or analytics. Use a strict CSP and no unsafe HTML. A later cookie/BFF design requires a separate decision and CSRF contract.
- Processing routes require current consent; account reads, consent update, settings, deletion and health remain available without processing consent. A failed JWT gives 401; a valid JWT without consent gives 403 `CONSENT_REQUIRED`. Foreign private IDs return the same 404 as nonexistent IDs.

### Headers, encoding and concurrency

`Content-Type: application/json` except raw PDF upload and explicit streaming/export responses. UTF-8 everywhere. All application timestamps are RFC3339 UTC with `Z`; date-only policy values retain their separate precision. UUIDs are RFC4122 strings; all path IDs are UUIDs except event sequences. Monetary usage is integer micro-USD. GPA and other exact decimal quantities are strings parsed with Decimal; never binary floats. Counts/revisions are nonnegative integers, revisions start at 1. Boolean values are actual JSON booleans, not strings.

Every response has `X-Request-ID`; accept a valid opaque caller request ID up to 64 characters or generate one. Normal success JSON is `{ "data": <payload>, "request_id": "..." }`. List payloads are `{ "items": [...], "next_cursor": null|string }`. The endpoint examples below show this complete envelope. `204` has no body. SSE, Markdown exports and binary uploads are explicit exceptions. Sensitive reads use `Cache-Control: no-store`; public artifact reuse occurs server-side.

Commands marked **Idempotency required** require `Idempotency-Key` (opaque 16–128 characters; browser should use a new UUID per intentional command). Store owner + operation + key + canonical request hash and the committed response for 24 hours. Replays return the original status/body plus `Idempotency-Replayed: true`. Different payload under the same key →409 `IDEMPOTENCY_CONFLICT`. Record response and side effects atomically; a crashed in-progress command may retry only through its same state machine. Intrinsically idempotent PUT/DELETE operations identified below do not need the header. Missing required header →400. Account deletion has its explicit tombstone replay exception and encrypted replay body.

Updates use explicit `base_profile_version_id`, `base_revision` or `revision` fields; stale bases →409. Do not introduce a second If-Match/ETag update scheme in P0. UTC `created_at DESC,id DESC` is the default stable pagination order. Cursor is opaque signed data bound to owner, filters, order and last key; max 100 items. In a ranked run, use stored rank then ID. Invalid cursor →400; a cursor cannot select a different owner or filter. JSON request bodies are capped at 256 KiB except the bounded PDF stream. Text fields and arrays use their documented smaller limits. Public catalog pages may change as new data arrives; cursor paging is keyset based, not a claim of a frozen database snapshot.

### Error contract

Use `application/problem+json` for all non-2xx application errors, including normalized validation errors. Never return Python stack traces, secrets or raw provider bodies. Validation errors use safe field paths and short messages. Standard shape:

```json
{
  "type": "urn:benefitbridge:problem:version-conflict",
  "title": "Version conflict",
  "status": 409,
  "detail": "Reload the current profile before applying this change.",
  "code": "VERSION_CONFLICT",
  "request_id": "req-example-001",
  "errors": [{"path": "base_profile_version_id", "message": "Current version differs."}],
  "retryable": false
}
```

| HTTP | Stable code families | Client behavior |
| --- | --- | --- |
| 400 | BAD_REQUEST, INVALID_CURSOR, IDEMPOTENCY_KEY_REQUIRED | Fix malformed input |
| 401 | UNAUTHENTICATED, INVALID_RECEIPT | Reauthenticate; receipt failures expose no existence |
| 403 | CONSENT_REQUIRED, FEATURE_DISABLED, ACCOUNT_DELETING | Show the allowed next action |
| 404 | NOT_FOUND, EVIDENCE_UNAVAILABLE | Treat resource as unavailable; no owner hint |
| 409 | VERSION_CONFLICT, IDEMPOTENCY_CONFLICT, SOURCE_STALE, APPLICATION_STALE, DRAFT_NOT_VALID, INVALID_RUN_STATE and endpoint-specific state codes | Refresh state or take indicated action; do not blind-retry writes |
| 410 | EVENT_CURSOR_EXPIRED, UPLOAD_EXPIRED, CLARIFICATION_EXPIRED | Use status read/new intent or current decision as appropriate |
| 413 | PAYLOAD_TOO_LARGE | Reduce file/body size |
| 415 | UNSUPPORTED_MEDIA_TYPE | Upload a supported digital PDF |
| 422 | VALIDATION_ERROR, CONTENT_MISMATCH, UNSAFE_URL, SOURCE_UNSUPPORTED | Correct field/content; no automatic retry |
| 429 | RATE_LIMITED, BUDGET_EXCEEDED, QUOTA_EXCEEDED | Respect Retry-After; show budget state |
| 500 | INTERNAL_ERROR | Display request ID; retain accepted run state |
| 503 | DEPENDENCY_UNAVAILABLE, SERVICE_NOT_READY | Retry safe reads with backoff; command retries use same idempotency key |

Job-level provider failures usually appear in Run.failure_code/warnings after a successful 202. A synchronous acceptance must never claim provider processing has completed. Rate limit defaults: 60 authenticated reads/minute/account, 10 command requests/minute/account, two active workflow runs/account; uploads additionally use storage quota. These are starting deployment controls to validate under load, not capacity guarantees.

## Typed applicant fact values

Each fact uses `attribute`, the value union below, provenance and optional evidence links. Unknown is represented by `{ "type": "UNKNOWN", "reason": "USER_UNSURE" }` or an absent attribute; it is never false, zero, an empty unrestricted set or a guessed nationality. A confirmed empty set is semantically different from UNKNOWN. `null` is only legal where specified.

| Tag | Required keys besides type | Validation |
| --- | --- | --- |
| STRING | value:string | 1–500 characters; per-attribute allowlisted normalization preserves original source title |
| BOOLEAN | value:boolean | Absence never implies false |
| COUNTRY_SET | values:string[] | Unique uppercase ISO-3166 alpha-2, 0–20 entries; explicit empty set is known empty |
| STRING_SET | values:string[] | Unique 1–80 character strings, 0–50 entries |
| GPA | number:decimal-string, scale_max:decimal-string | 0 ≤ number ≤ scale_max; scale_max >0; scale required; no improvised equivalence |
| DATE | value:string, precision:DAY or MONTH or YEAR, expected:boolean | ISO YYYY-MM-DD / YYYY-MM / YYYY matches precision; compare possible intervals |
| EXPERIENCE | entries:array | Up to 20 {role, start, end, relevant}; dates YYYY-MM-DD, end nullable for current; relevant boolean or null; merge overlap for elapsed-duration predicates |
| LANGUAGE_TESTS | entries:array | Up to 10 {test, total:decimal-string, components:object of decimal strings, taken_on:YYYY-MM-DD}; apply explicit provider scale and validity rules |
| UNKNOWN | reason:string | USER_UNSURE, NOT_PROVIDED or CONFLICTING_EVIDENCE |

| Attribute | Value type | Notes |
| --- | --- | --- |
| location.country | COUNTRY_SET | Exactly one residence country when known |
| citizenship.countries | COUNTRY_SET | Distinct from residence |
| work_authorization.countries | COUNTRY_SET | Countries with confirmed current authorization; empty means known none |
| education.enrolled | BOOLEAN | Current enrollment fact; date validity may be bounded |
| education.level | STRING | UNDERGRADUATE, GRADUATE, RECENT_GRADUATE or original unresolved title |
| education.field, education.institution | STRING | Preserve original label before normalization |
| education.graduation, date_of_birth | DATE | Collect birth date only if a supported requirement needs it; do not infer |
| education.gpa | GPA | Cumulative versus semester discrepancy becomes conflict |
| skills | STRING_SET | Self-reported or documented skill claims, not certified proficiency |
| experience | EXPERIENCE | Exact overlap handling; ambiguous full-time equivalence is unknown |
| language_tests | LANGUAGE_TESTS | Validity and component minimums are policy-specific |

## Rule graph and reason codes

Nodes discriminate on `type`. ALL/ANY use `children:string[]`; NOT uses `child:string`; PREDICATE uses the fields in RequirementSet. Empty roots cannot mean automatically eligible: `mandatory_root:null` with incomplete context yields UNKNOWN. Predicates use `EQ`, `NE`, `GT`, `GTE`, `LT`, `LTE`, `IN`, `NOT_IN`, `BEFORE`, `AFTER`, `OVERLAPS`, `EXISTS`, or `SEMANTIC_MATCH`; expected value is a compatible typed value or a documented typed interval. `EXISTS` tests known possession of an explicitly required credential, never general absence-of-data. Predicates on unavailable/unsupported attributes return UNKNOWN. Date BEFORE/AFTER are strict; inclusive comparisons use LTE/GTE over explicit dates. Rule interval values use `{ "type":"INTERVAL", "lower":<typed scalar>, "upper":<typed scalar>, "lower_inclusive":true, "upper_inclusive":true }`, only in rule expected values.

Allowed reference_time: APPLICATION, PROGRAM_START or EXPLICIT; EXPLICIT requires a source-supported reference_date field using the DATE tagged value with precision DAY/MONTH/YEAR; omit reference_date for other reference_time values. Provenance supports every operator, bound and qualifier. Semantic predicate outputs contain truth, concise explanation, cited fact/evidence/source IDs and reason codes; they cannot create new confirmed facts.

Decision reason-code catalog: `MISSING_PROFILE_FACT`, `MISSING_SOURCE`, `SOURCE_CONFLICT`, `AMBIGUOUS_POLICY`, `UNSUPPORTED_RULE`, `STALE_EVIDENCE`, `EXTRACTION_INCOMPLETE`, `INCOMPATIBLE_SCALE`, `DATE_PRECISION_INSUFFICIENT`, `UNSUPPORTED_CLAIM`, `BUDGET_LIMIT`, `PROVIDER_FAILURE`, `INPUT_VERSION_CHANGED`. Keep technical failures in Run state and evaluation metrics; do not disguise an unexecuted evaluator as a correct semantic UNKNOWN.

## Response DTO catalog

All displayed fields are required in the wire DTO unless explicitly nullable/optional. Arrays can be empty where meaningful. Objects are immutable value snapshots except the documented metadata; nested DTOs use the same schema. Each example is a complete payload before the standard envelope.
### Account

status ACTIVE or DELETING; consent is null until accepted; display_name 1–80 Unicode characters; timezone valid IANA ID. No email is returned by this application API.

```json
{
  "id": "00000000-0000-4000-8000-000000000001",
  "display_name": "Demo applicant",
  "timezone": "Africa/Cairo",
  "status": "ACTIVE",
  "consent": {
    "version": "2026-10-01",
    "accepted_at": "2026-10-20T12:00:00Z"
  },
  "is_demo": false,
  "created_at": "2026-10-20T12:00:00Z"
}
```

### Fact

attribute from the fact catalog; value is the tagged union below; provenance USER_CONFIRMED, USER_CONFIRMED_DOCUMENT or CONFLICTING; evidence_ids all belong to owner; valid dates nullable. Immutable inside a profile version.

```json
{
  "id": "00000000-0000-4000-8000-000000000003",
  "attribute": "education.gpa",
  "value": {
    "type": "GPA",
    "number": "3.70",
    "scale_max": "4.00"
  },
  "provenance": "USER_CONFIRMED_DOCUMENT",
  "evidence_ids": [
    "00000000-0000-4000-8000-000000000006"
  ],
  "confirmed_at": "2026-10-20T12:00:00Z",
  "valid_from": null,
  "valid_until": null,
  "conflict": false
}
```

### Profile

One current profile per owner. version_number positive integer. facts max 100, with one effective fact per scalar attribute; arrays live in one typed fact; unresolved conflicts remain flagged.

```json
{
  "id": "00000000-0000-4000-8000-000000000023",
  "version_id": "00000000-0000-4000-8000-000000000002",
  "version_number": 1,
  "facts": [
    {
      "id": "00000000-0000-4000-8000-000000000003",
      "attribute": "education.gpa",
      "value": {
        "type": "GPA",
        "number": "3.70",
        "scale_max": "4.00"
      },
      "provenance": "USER_CONFIRMED_DOCUMENT",
      "evidence_ids": [
        "00000000-0000-4000-8000-000000000006"
      ],
      "confirmed_at": "2026-10-20T12:00:00Z",
      "valid_from": null,
      "valid_until": null,
      "conflict": false
    }
  ],
  "updated_at": "2026-10-20T12:00:00Z"
}
```

### Document

kind CV, TRANSCRIPT or ENROLLMENT; status UPLOADING, UPLOADED, QUEUED, PARSING, READY, FAILED or DELETING; version/page_count/quality nullable before parsing. quality READABLE or MANUAL_ENTRY_REQUIRED; content SHA is lower-case hex.

```json
{
  "id": "00000000-0000-4000-8000-000000000004",
  "filename": "synthetic-transcript.pdf",
  "kind": "TRANSCRIPT",
  "status": "READY",
  "size_bytes": 48012,
  "sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "version_id": "00000000-0000-4000-8000-000000000005",
  "page_count": 2,
  "quality": "READABLE",
  "failure_code": null,
  "created_at": "2026-10-20T12:00:00Z",
  "deleted_at": null
}
```

### Evidence

Offsets are Unicode code-point half-open offsets within normalized page text, page 1-based; quote must equal text[start:end]. The quote length must equal end minus start. Deleted evidence returns 404, including historical reads.

```json
{
  "id": "00000000-0000-4000-8000-000000000006",
  "document_id": "00000000-0000-4000-8000-000000000004",
  "document_version_id": "00000000-0000-4000-8000-000000000005",
  "page": 1,
  "start": 0,
  "end": 26,
  "quote": "Cumulative GPA: 3.70 / 4.0",
  "normalized_text_hash": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
}
```

### FactCandidate

state PENDING, ACCEPTED, CORRECTED or REJECTED; all candidates require explicit review; issues contains stable reason-code strings.

```json
{
  "id": "00000000-0000-4000-8000-000000000007",
  "document_id": "00000000-0000-4000-8000-000000000004",
  "attribute": "education.gpa",
  "value": {
    "type": "GPA",
    "number": "3.70",
    "scale_max": "4.00"
  },
  "evidence_ids": [
    "00000000-0000-4000-8000-000000000006"
  ],
  "state": "PENDING",
  "issues": []
}
```

### RunReceipt

202 command receipt. status is QUEUED when first accepted; idempotent replay returns original receipt even if current run is now terminal; fetch status_url for current state.

```json
{
  "run_id": "00000000-0000-4000-8000-000000000013",
  "status": "QUEUED",
  "status_url": "/api/v1/runs/00000000-0000-4000-8000-000000000013",
  "events_url": "/api/v1/runs/00000000-0000-4000-8000-000000000013/events"
}
```

### Run

kind DOCUMENT_PARSE, DISCOVERY, IMPORT, EVALUATE, DRAFT_GENERATE, DRAFT_VALIDATE, REFRESH, DOCUMENT_DELETE, ACCOUNT_DELETE or DEMO_RESET. status QUEUED, RUNNING, WAITING_USER, SUCCEEDED, PARTIAL, FAILED or CANCELLED. progress.total_units may be null when unknown; do not fabricate percentages. profile_version_id nullable for source-only/deletion jobs.

```json
{
  "id": "00000000-0000-4000-8000-000000000013",
  "kind": "DISCOVERY",
  "status": "RUNNING",
  "stage": "FETCH",
  "profile_version_id": "00000000-0000-4000-8000-000000000002",
  "cancel_requested": false,
  "progress": {
    "completed_units": 2,
    "total_units": 5
  },
  "funnel": {
    "raw_hits": 24,
    "canonical": 9,
    "official": 6,
    "parsed": 5,
    "evaluated": 2
  },
  "result_refs": {
    "opportunity_ids": [
      "00000000-0000-4000-8000-000000000008"
    ],
    "evaluation_ids": [
      "00000000-0000-4000-8000-000000000014"
    ],
    "draft_ids": []
  },
  "warnings": [],
  "failure_code": null,
  "created_at": "2026-10-20T12:00:00Z",
  "updated_at": "2026-10-20T12:00:00Z"
}
```

### Deadline

precision INSTANT, DATE, MONTH, YEAR or UNKNOWN. Exactly the matching representation is set: at RFC3339 for INSTANT; date ISO YYYY-MM-DD, YYYY-MM or YYYY for DATE/MONTH/YEAR. timezone IANA or null; no implied timestamp. ambiguity is null or reason string.

```json
{
  "raw_text": "Apply by 30 November 2026",
  "precision": "DATE",
  "date": "2026-11-30",
  "at": null,
  "timezone": null,
  "ambiguity": null
}
```

### Opportunity

lane INTERNSHIP_RESEARCH or SCHOLARSHIP_PROGRAM; authority OFFICIAL, CORROBORATED, DISCOVERY_ONLY or UNRESOLVED; availability OPEN, CLOSED, NOT_YET_OPEN, UNKNOWN or UNAVAILABLE. freshness.state FRESH, STALE or UNAVAILABLE. evaluation_state CURRENT, STALE or NOT_EVALUATED; evaluation_id nullable and always caller-owned. Countries describe location, never authorization.

```json
{
  "id": "00000000-0000-4000-8000-000000000008",
  "version_id": "00000000-0000-4000-8000-000000000009",
  "title": "Synthetic Student Research Program",
  "provider": "Synthetic Research Institute",
  "lane": "INTERNSHIP_RESEARCH",
  "cycle": "2027",
  "location_countries": [
    "EG"
  ],
  "remote": true,
  "official_url": "https://example.org/program",
  "authority": "OFFICIAL",
  "availability": "OPEN",
  "deadline": {
    "raw_text": "Apply by 30 November 2026",
    "precision": "DATE",
    "date": "2026-11-30",
    "at": null,
    "timezone": null,
    "ambiguity": null
  },
  "freshness": {
    "state": "FRESH",
    "checked_at": "2026-10-20T12:00:00Z",
    "expires_at": "2026-10-21T12:00:00Z"
  },
  "requirement_set_id": "00000000-0000-4000-8000-000000000012",
  "evaluation_id": null,
  "evaluation_state": "NOT_EVALUATED"
}
```

### Source

Source read returns cited spans and metadata, not unlimited copyrighted page text. quote must be exact normalized text slice. completeness COMPLETE, INCOMPLETE or CONFLICTED. page nullable for HTML; offsets refer to normalized document text when page null.

```json
{
  "id": "00000000-0000-4000-8000-000000000010",
  "url": "https://example.org/program",
  "snapshot_id": "00000000-0000-4000-8000-000000000011",
  "retrieved_at": "2026-10-20T12:00:00Z",
  "content_hash": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
  "authority": "OFFICIAL",
  "completeness": "COMPLETE",
  "spans": [
    {
      "id": "00000000-0000-4000-8000-000000000024",
      "page": null,
      "start": 0,
      "end": 28,
      "quote": "Applicants must be enrolled."
    }
  ]
}
```

### RequirementSet

AST max 100 nodes, depth 12; node IDs unique within set. ALL/ANY require 1–50 children; NOT exactly one child; PREDICATE no children. Task source span ids must exist in the actual source bundle (examples across operations are independent). interpretation DIRECT, SEMANTIC_REVIEWED or UNRESOLVED; evidence_expectation KNOWN_FACT or REQUIRED_CREDENTIAL.

```json
{
  "id": "00000000-0000-4000-8000-000000000012",
  "opportunity_version_id": "00000000-0000-4000-8000-000000000009",
  "schema_version": "1.0.0",
  "completeness": "COMPLETE",
  "mandatory_root": "root",
  "preferred_roots": [],
  "nodes": [
    {
      "id": "root",
      "type": "ALL",
      "children": [
        "r-enrolled"
      ]
    },
    {
      "id": "r-enrolled",
      "type": "PREDICATE",
      "modality": "MANDATORY",
      "attribute": "education.enrolled",
      "operator": "EQ",
      "expected": {
        "type": "BOOLEAN",
        "value": true
      },
      "source_span_ids": [
        "00000000-0000-4000-8000-000000000024"
      ],
      "scope": {
        "cycle": "2027",
        "location_countries": [
          "EG"
        ]
      },
      "reference_time": "APPLICATION",
      "interpretation": "DIRECT",
      "evidence_expectation": "KNOWN_FACT"
    }
  ],
  "application_tasks": [
    {
      "key": "statement",
      "label": "Review statement",
      "required": true,
      "kind": "STATEMENT",
      "applicability": "APPLIES",
      "source_span_ids": [
        "00000000-0000-4000-8000-000000000025"
      ]
    }
  ],
  "issues": []
}
```

### Evaluation

eligibility MET, NOT_MET or UNKNOWN. leaf truth TRUE, FALSE, UNKNOWN; method DETERMINISTIC or SEMANTIC. currentness CURRENT, STALE or HISTORICAL. fit.score 0–100 or null; coverage 0–1. readiness.percent integer rounded half-up or null for zero denominator/unknown applicability. Components reconcile the weighted score over known values; null components reduce coverage. No admission probability.

```json
{
  "id": "00000000-0000-4000-8000-000000000014",
  "opportunity_id": "00000000-0000-4000-8000-000000000008",
  "opportunity_version_id": "00000000-0000-4000-8000-000000000009",
  "profile_version_id": "00000000-0000-4000-8000-000000000002",
  "requirement_set_id": "00000000-0000-4000-8000-000000000012",
  "eligibility": "UNKNOWN",
  "availability": "OPEN",
  "fit": {
    "score": 75,
    "coverage": 0.8,
    "components": [
      {
        "name": "field",
        "weight": 0.4,
        "value": 1.0
      },
      {
        "name": "funding",
        "weight": 0.2,
        "value": 1.0
      },
      {
        "name": "location",
        "weight": 0.2,
        "value": 0.0
      },
      {
        "name": "start",
        "weight": 0.2,
        "value": null
      }
    ]
  },
  "readiness": {
    "completed": 2,
    "required": 3,
    "percent": 67,
    "unknown_applicability": 0
  },
  "currentness": "CURRENT",
  "reason_codes": [
    "MISSING_PROFILE_FACT"
  ],
  "leaves": [
    {
      "node_id": "r-enrolled",
      "truth": "UNKNOWN",
      "method": "DETERMINISTIC",
      "fact_ids": [],
      "evidence_ids": [],
      "source_span_ids": [
        "00000000-0000-4000-8000-000000000024"
      ],
      "reason_codes": [
        "MISSING_PROFILE_FACT"
      ],
      "explanation": "Enrollment status has not been confirmed."
    }
  ],
  "as_of": "2026-10-20T12:00:00Z",
  "valid_until": "2026-10-21T12:00:00Z",
  "versions": {
    "evaluator": "1.0.0",
    "prompts": "p1",
    "registry": "m1",
    "freshness": "f1"
  }
}
```

### ClarificationSet

At most 3 questions per set, 2 sets per run. Each question maps to a fact attribute and node. valid value_type from fact union; skip answer records UNKNOWN. Set expires after 24h; expiry makes run PARTIAL with preserved results.

```json
{
  "id": "00000000-0000-4000-8000-000000000015",
  "run_id": "00000000-0000-4000-8000-000000000013",
  "revision": 1,
  "round": 1,
  "base_profile_version_id": "00000000-0000-4000-8000-000000000002",
  "questions": [
    {
      "id": "q-enrolled",
      "attribute": "education.enrolled",
      "prompt": "Are you currently enrolled?",
      "value_type": "BOOLEAN",
      "reason": "The program requires current enrollment.",
      "required_for_nodes": [
        "r-enrolled"
      ]
    }
  ],
  "expires_at": "2026-10-21T12:00:00Z"
}
```

### Saved

Unique owner/opportunity pair; current_evaluation_id nullable. Removing save does not remove evaluations or applications.

```json
{
  "opportunity_id": "00000000-0000-4000-8000-000000000008",
  "saved_at": "2026-10-20T12:00:00Z",
  "current_evaluation_id": "00000000-0000-4000-8000-000000000014",
  "evaluation_state": "CURRENT"
}
```

### ChecklistItem

kind DOCUMENT, TASK or STATEMENT; applicability APPLIES, DOES_NOT_APPLY or UNKNOWN; status TODO or DONE. Only acceptance can complete a STATEMENT item. User completion of DOCUMENT requires active owner evidence or explicit confirmed availability under documented task policy.

```json
{
  "id": "00000000-0000-4000-8000-000000000017",
  "key": "cv",
  "label": "Prepare CV",
  "kind": "DOCUMENT",
  "required": true,
  "applicability": "APPLIES",
  "status": "TODO",
  "evidence_ids": [],
  "draft_id": null
}
```

### Application

state CURRENT or STALE. revision increases on checklist/draft/acceptance/currentness mutations. One current workspace per owner/opportunity cycle; refresh/rebase is explicitly created via create_application with replace_stale=true.

```json
{
  "id": "00000000-0000-4000-8000-000000000016",
  "opportunity_id": "00000000-0000-4000-8000-000000000008",
  "opportunity_version_id": "00000000-0000-4000-8000-000000000009",
  "profile_version_id": "00000000-0000-4000-8000-000000000002",
  "evaluation_id": "00000000-0000-4000-8000-000000000014",
  "revision": 1,
  "state": "CURRENT",
  "items": [
    {
      "id": "00000000-0000-4000-8000-000000000017",
      "key": "cv",
      "label": "Prepare CV",
      "kind": "DOCUMENT",
      "required": true,
      "applicability": "APPLIES",
      "status": "TODO",
      "evidence_ids": [],
      "draft_id": null
    }
  ],
  "readiness": {
    "completed": 0,
    "required": 1,
    "percent": 0,
    "unknown_applicability": 0
  },
  "latest_draft_id": null,
  "accepted_draft_id": null,
  "created_at": "2026-10-20T12:00:00Z"
}
```

### Draft

validation PENDING, VALID, INVALID or UNKNOWN. Example text is abbreviated for schema illustration; actual statement must have 150–500 words. claims contain {id,start,end,text,fact_ids,evidence_ids,status}; offsets code points within draft; status SUPPORTED, CONTRADICTED or UNVERIFIABLE. Immutable text; validation/acceptance metadata append audited events.

```json
{
  "id": "00000000-0000-4000-8000-000000000018",
  "application_id": "00000000-0000-4000-8000-000000000016",
  "version_number": 1,
  "profile_version_id": "00000000-0000-4000-8000-000000000002",
  "opportunity_version_id": "00000000-0000-4000-8000-000000000009",
  "text": "I am interested in this student research program.",
  "validation": "PENDING",
  "claims": [],
  "issues": [],
  "accepted_at": null,
  "created_at": "2026-10-20T12:00:00Z"
}
```

### Watch

P1; interval_hours 24 or 72; only saved opportunities; one watch per owner/opportunity. Deadline-near policy may make actual refresh cadence shorter through shared public refresh, without extra private watch notifications.

```json
{
  "id": "00000000-0000-4000-8000-000000000019",
  "opportunity_id": "00000000-0000-4000-8000-000000000008",
  "revision": 1,
  "enabled": true,
  "interval_hours": 24,
  "next_due_at": "2026-10-21T12:00:00Z"
}
```

### Notification

P1; kind SOURCE_CHANGED or SOURCE_UNAVAILABLE; unique watch/version/kind event. No emails are sent.

```json
{
  "id": "00000000-0000-4000-8000-000000000020",
  "watch_id": "00000000-0000-4000-8000-000000000019",
  "opportunity_id": "00000000-0000-4000-8000-000000000008",
  "opportunity_version_id": "00000000-0000-4000-8000-000000000009",
  "kind": "SOURCE_CHANGED",
  "summary": "Published deadline changed.",
  "read_at": null,
  "created_at": "2026-10-20T12:00:00Z"
}
```

### Usage

Integer nonnegative micro-USD accounting, UTC daily window; configured limits are pilot defaults, not vendor price claims. Includes retries; unresolved charges remain reserved.

```json
{
  "period_start": "2026-10-20T00:00:00Z",
  "period_end": "2026-10-21T00:00:00Z",
  "currency": "USD",
  "spent_microusd": 125000,
  "reserved_microusd": 100000,
  "limit_microusd": 2000000,
  "active_runs": 1,
  "active_run_limit": 2
}
```

### Capabilities

Public nonsecret flags; readiness may change inference_available. No keys, vendor account balances, private limits or exact internal hosts.

```json
{
  "api_version": "1",
  "watch": false,
  "demo_reset": true,
  "supported_lanes": [
    "INTERNSHIP_RESEARCH",
    "SCHOLARSHIP_PROGRAM"
  ],
  "supported_document_types": [
    "application/pdf"
  ],
  "max_document_bytes": 10485760,
  "max_document_pages": 20,
  "inference_available": true,
  "deep_available": false
}
```

## Endpoint index

| Operation ID | Method and path | Auth | Success | Idempotency | Micro-sprint |
| --- | --- | --- | --- | --- | --- |
| get_me | GET /api/v1/me | USER / P0 | 200 | Not required | MS-008 |
| patch_me | PATCH /api/v1/me | USER / P0 | 200 | Not required | MS-008 |
| get_profile | GET /api/v1/profile | USER / P0 | 200 | Not required | MS-017 |
| patch_profile | PATCH /api/v1/profile | USER / P0 | 200 | Required | MS-017 |
| list_profile_versions | GET /api/v1/profile/versions | USER / P0 | 200 | Not required | MS-017 |
| get_profile_version | GET /api/v1/profile/versions/{profile_version_id} | USER / P0 | 200 | Not required | MS-017 |
| create_document_upload | POST /api/v1/documents/uploads | USER / P0 | 201 | Required | MS-026 |
| put_document_content | PUT /api/v1/documents/{document_id}/content | USER / P0 | 200 | Not required | MS-026 |
| complete_document_upload | POST /api/v1/documents/{document_id}/complete | USER / P0 | 202 | Required | MS-026 |
| list_documents | GET /api/v1/documents | USER / P0 | 200 | Not required | MS-026 |
| get_document | GET /api/v1/documents/{document_id} | USER / P0 | 200 | Not required | MS-026 |
| get_document_download | GET /api/v1/documents/{document_id}/download | USER / P0 | 200 | Not required | MS-026 |
| delete_document | DELETE /api/v1/documents/{document_id} | USER / P0 | 202 | Required | MS-063 |
| list_fact_candidates | GET /api/v1/fact-candidates | USER / P0 | 200 | Not required | MS-028 |
| review_fact_candidates | POST /api/v1/fact-candidates/reviews | USER / P0 | 200 | Required | MS-028 |
| get_evidence | GET /api/v1/evidence/{evidence_id} | USER / P0 | 200 | Not required | MS-028 |
| start_discovery | POST /api/v1/discovery-runs | USER / P0 | 202 | Required | MS-046 |
| import_opportunity | POST /api/v1/opportunity-imports | USER / P0 | 202 | Required | MS-046 |
| list_runs | GET /api/v1/runs | USER / P0 | 200 | Not required | MS-030 |
| get_run | GET /api/v1/runs/{run_id} | USER / P0 | 200 | Not required | MS-030 |
| cancel_run | POST /api/v1/runs/{run_id}/cancel | USER / P0 | 200 | Required | MS-030 |
| get_run_events | GET /api/v1/runs/{run_id}/events | USER / P0 | 200 | Not required | MS-030 |
| get_clarifications | GET /api/v1/runs/{run_id}/clarifications | USER / P0 | 200 | Not required | MS-050 |
| answer_clarifications | POST /api/v1/runs/{run_id}/clarifications/{clarification_set_id}/answers | USER / P0 | 202 | Required | MS-050 |
| list_opportunities | GET /api/v1/opportunities | USER / P0 | 200 | Not required | MS-045 |
| get_opportunity | GET /api/v1/opportunities/{opportunity_id} | USER / P0 | 200 | Not required | MS-045 |
| get_opportunity_version | GET /api/v1/opportunities/{opportunity_id}/versions/{opportunity_version_id} | USER / P0 | 200 | Not required | MS-045 |
| get_requirements | GET /api/v1/requirement-sets/{requirement_set_id} | USER / P0 | 200 | Not required | MS-045 |
| get_source | GET /api/v1/sources/{source_snapshot_id} | USER / P0 | 200 | Not required | MS-045 |
| start_evaluation | POST /api/v1/evaluations | USER / P0 | 202 | Required | MS-047 |
| get_evaluation | GET /api/v1/evaluations/{evaluation_id} | USER / P0 | 200 | Not required | MS-047 |
| refresh_opportunity | POST /api/v1/opportunities/{opportunity_id}/refresh | USER / P0 | 202 | Required | MS-061 |
| list_saved | GET /api/v1/saved-opportunities | USER / P0 | 200 | Not required | MS-053 |
| save_opportunity | PUT /api/v1/saved-opportunities/{opportunity_id} | USER / P0 | 200 | Not required | MS-053 |
| delete_saved | DELETE /api/v1/saved-opportunities/{opportunity_id} | USER / P0 | 204 | Not required | MS-053 |
| list_applications | GET /api/v1/applications | USER / P0 | 200 | Not required | MS-056 |
| create_application | POST /api/v1/applications | USER / P0 | 201 | Required | MS-056 |
| get_application | GET /api/v1/applications/{application_id} | USER / P0 | 200 | Not required | MS-056 |
| patch_checklist_item | PATCH /api/v1/applications/{application_id}/items/{item_id} | USER / P0 | 200 | Required | MS-056 |
| start_draft | POST /api/v1/applications/{application_id}/drafts | USER / P0 | 202 | Required | MS-059 |
| get_draft | GET /api/v1/drafts/{draft_id} | USER / P0 | 200 | Not required | MS-059 |
| edit_draft | POST /api/v1/drafts/{draft_id}/versions | USER / P0 | 202 | Required | MS-059 |
| accept_draft | POST /api/v1/drafts/{draft_id}/accept | USER / P0 | 200 | Required | MS-059 |
| export_application | GET /api/v1/applications/{application_id}/export | USER / P0 | 200 | Not required | MS-059 |
| get_usage | GET /api/v1/usage | USER / P0 | 200 | Not required | MS-068 |
| delete_account | DELETE /api/v1/me | USER / P0 | 202 | Required | MS-064 |
| get_deletion_receipt | GET /api/v1/deletion-receipts/{receipt_id} | RECEIPT / P0 | 200 | Not required | MS-064 |
| health_live | GET /api/v1/health/live | PUBLIC / P0 | 200 | Not required | MS-074 |
| health_ready | GET /api/v1/health/ready | PUBLIC / P0 | 200 | Not required | MS-074 |
| get_capabilities | GET /api/v1/capabilities | PUBLIC / P0 | 200 | Not required | MS-068 |
| reset_demo | POST /api/v1/demo/reset | DEMO / P0 | 202 | Required | MS-084 |
| list_watches | GET /api/v1/watches | USER / P1 | 200 | Not required | MS-072 |
| create_watch | POST /api/v1/watches | USER / P1 | 201 | Required | MS-072 |
| patch_watch | PATCH /api/v1/watches/{watch_id} | USER / P1 | 200 | Required | MS-072 |
| delete_watch | DELETE /api/v1/watches/{watch_id} | USER / P1 | 204 | Not required | MS-072 |
| list_notifications | GET /api/v1/notifications | USER / P1 | 200 | Not required | MS-072 |
| read_notification | PUT /api/v1/notifications/{notification_id}/read | USER / P1 | 200 | Not required | MS-072 |

## Endpoint specifications

Payload keys are required unless the endpoint says otherwise. For every endpoint, common auth, validation, quota and server errors above apply in addition to the listed state errors. Path identifiers use UUID validation and resource association checks. An empty JSON body is `{}`; “No body” means send no JSON. Lists use the common page contract.

### `get_me` — GET `/api/v1/me`

- **Auth / priority:** USER / P0.
- **Implementation:** MS-008.
- **Idempotency required:** No.
- **Query/headers:** No operation-specific query parameters.
- **Rules:** Idempotent account bootstrap after JWT verification and deleted-subject deny check; processing consent not required. A purged subject cannot recreate its account with a still-valid old token.
- **Additional state errors:** Common errors only.

**Request**

No body.

**Response — HTTP 200**

```json
{
  "data": {
    "id": "00000000-0000-4000-8000-000000000001",
    "display_name": "Demo applicant",
    "timezone": "Africa/Cairo",
    "status": "ACTIVE",
    "consent": {
      "version": "2026-10-01",
      "accepted_at": "2026-10-20T12:00:00Z"
    },
    "is_demo": false,
    "created_at": "2026-10-20T12:00:00Z"
  },
  "request_id": "req-example-001"
}
```

### `patch_me` — PATCH `/api/v1/me`

- **Auth / priority:** USER / P0.
- **Implementation:** MS-008.
- **Idempotency required:** No.
- **Query/headers:** No operation-specific query parameters.
- **Rules:** All three fields optional but at least one; consent_version must equal currently advertised processing notice version. No owner/status edits.
- **Additional state errors:** Common errors only.

**Request**

```json
{
  "display_name": "Demo applicant",
  "timezone": "Africa/Cairo",
  "consent_version": "2026-10-01"
}
```

**Response — HTTP 200**

```json
{
  "data": {
    "id": "00000000-0000-4000-8000-000000000001",
    "display_name": "Demo applicant",
    "timezone": "Africa/Cairo",
    "status": "ACTIVE",
    "consent": {
      "version": "2026-10-01",
      "accepted_at": "2026-10-20T12:00:00Z"
    },
    "is_demo": false,
    "created_at": "2026-10-20T12:00:00Z"
  },
  "request_id": "req-example-001"
}
```

### `get_profile` — GET `/api/v1/profile`

- **Auth / priority:** USER / P0.
- **Implementation:** MS-017.
- **Idempotency required:** No.
- **Query/headers:** No operation-specific query parameters.
- **Rules:** Common protocol, consent and ownership rules apply.
- **Additional state errors:** Common errors only.

**Request**

No body.

**Response — HTTP 200**

```json
{
  "data": {
    "id": "00000000-0000-4000-8000-000000000023",
    "version_id": "00000000-0000-4000-8000-000000000002",
    "version_number": 1,
    "facts": [
      {
        "id": "00000000-0000-4000-8000-000000000003",
        "attribute": "education.gpa",
        "value": {
          "type": "GPA",
          "number": "3.70",
          "scale_max": "4.00"
        },
        "provenance": "USER_CONFIRMED_DOCUMENT",
        "evidence_ids": [
          "00000000-0000-4000-8000-000000000006"
        ],
        "confirmed_at": "2026-10-20T12:00:00Z",
        "valid_from": null,
        "valid_until": null,
        "conflict": false
      }
    ],
    "updated_at": "2026-10-20T12:00:00Z"
  },
  "request_id": "req-example-001"
}
```

### `patch_profile` — PATCH `/api/v1/profile`

- **Auth / priority:** USER / P0.
- **Implementation:** MS-017.
- **Idempotency required:** Yes.
- **Query/headers:** No operation-specific query parameters.
- **Rules:** All fields required. 1–100 total changes/removals; no attribute repeated or both changed/removed; evidence optional only as empty array. Require current consent. Changes confirm self-report; document provenance only with active matching spans.
- **Additional state errors:** VERSION_CONFLICT, EVIDENCE_UNAVAILABLE

**Request**

```json
{
  "base_profile_version_id": "00000000-0000-4000-8000-000000000002",
  "changes": [
    {
      "attribute": "education.gpa",
      "value": {
        "type": "GPA",
        "number": "3.70",
        "scale_max": "4.00"
      },
      "evidence_ids": [
        "00000000-0000-4000-8000-000000000006"
      ]
    }
  ],
  "remove_attributes": []
}
```

**Response — HTTP 200**

```json
{
  "data": {
    "id": "00000000-0000-4000-8000-000000000023",
    "version_id": "00000000-0000-4000-8000-000000000002",
    "version_number": 1,
    "facts": [
      {
        "id": "00000000-0000-4000-8000-000000000003",
        "attribute": "education.gpa",
        "value": {
          "type": "GPA",
          "number": "3.70",
          "scale_max": "4.00"
        },
        "provenance": "USER_CONFIRMED_DOCUMENT",
        "evidence_ids": [
          "00000000-0000-4000-8000-000000000006"
        ],
        "confirmed_at": "2026-10-20T12:00:00Z",
        "valid_from": null,
        "valid_until": null,
        "conflict": false
      }
    ],
    "updated_at": "2026-10-20T12:00:00Z"
  },
  "request_id": "req-example-001"
}
```

### `list_profile_versions` — GET `/api/v1/profile/versions`

- **Auth / priority:** USER / P0.
- **Implementation:** MS-017.
- **Idempotency required:** No.
- **Query/headers:** limit=20 (1–100); cursor opaque optional; newest version first.
- **Rules:** Common protocol, consent and ownership rules apply.
- **Additional state errors:** Common errors only.

**Request**

No body.

**Response — HTTP 200**

```json
{
  "data": {
    "items": [
      {
        "id": "00000000-0000-4000-8000-000000000023",
        "version_id": "00000000-0000-4000-8000-000000000002",
        "version_number": 1,
        "facts": [
          {
            "id": "00000000-0000-4000-8000-000000000003",
            "attribute": "education.gpa",
            "value": {
              "type": "GPA",
              "number": "3.70",
              "scale_max": "4.00"
            },
            "provenance": "USER_CONFIRMED_DOCUMENT",
            "evidence_ids": [
              "00000000-0000-4000-8000-000000000006"
            ],
            "confirmed_at": "2026-10-20T12:00:00Z",
            "valid_from": null,
            "valid_until": null,
            "conflict": false
          }
        ],
        "updated_at": "2026-10-20T12:00:00Z"
      }
    ],
    "next_cursor": null
  },
  "request_id": "req-example-001"
}
```

### `get_profile_version` — GET `/api/v1/profile/versions/{profile_version_id}`

- **Auth / priority:** USER / P0.
- **Implementation:** MS-017.
- **Idempotency required:** No.
- **Query/headers:** No operation-specific query parameters.
- **Rules:** Owner only. Suppress deleted evidence quote data even on historical versions.
- **Additional state errors:** Common errors only.

**Request**

No body.

**Response — HTTP 200**

```json
{
  "data": {
    "id": "00000000-0000-4000-8000-000000000023",
    "version_id": "00000000-0000-4000-8000-000000000002",
    "version_number": 1,
    "facts": [
      {
        "id": "00000000-0000-4000-8000-000000000003",
        "attribute": "education.gpa",
        "value": {
          "type": "GPA",
          "number": "3.70",
          "scale_max": "4.00"
        },
        "provenance": "USER_CONFIRMED_DOCUMENT",
        "evidence_ids": [
          "00000000-0000-4000-8000-000000000006"
        ],
        "confirmed_at": "2026-10-20T12:00:00Z",
        "valid_from": null,
        "valid_until": null,
        "conflict": false
      }
    ],
    "updated_at": "2026-10-20T12:00:00Z"
  },
  "request_id": "req-example-001"
}
```

### `create_document_upload` — POST `/api/v1/documents/uploads`

- **Auth / priority:** USER / P0.
- **Implementation:** MS-026.
- **Idempotency required:** Yes.
- **Query/headers:** No operation-specific query parameters.
- **Rules:** All fields required; filename 1–120 characters basename only; reserve declared quota, maximum 10 MiB each/10 active documents/50 MiB owner total. Five-minute owner-bound intent. SHA verifies actual bytes.
- **Additional state errors:** Common errors only.

**Request**

```json
{
  "filename": "synthetic-transcript.pdf",
  "kind": "TRANSCRIPT",
  "content_type": "application/pdf",
  "size_bytes": 48012,
  "sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
}
```

**Response — HTTP 201**

```json
{
  "data": {
    "document_id": "00000000-0000-4000-8000-000000000004",
    "upload_url": "/api/v1/documents/00000000-0000-4000-8000-000000000004/content",
    "upload_method": "PUT",
    "expires_at": "2026-10-20T12:05:00Z",
    "max_bytes": 10485760
  },
  "request_id": "req-example-001"
}
```

### `put_document_content` — PUT `/api/v1/documents/{document_id}/content`

- **Auth / priority:** USER / P0.
- **Implementation:** MS-026.
- **Idempotency required:** No.
- **Query/headers:** No operation-specific query parameters.
- **Rules:** Content-Type application/pdf; raw byte stream (not multipart/JSON); Authorization required even though upload_url is returned. Intent unexpired and upload owned. Bound stream without trusting Content-Length; atomic private-object promotion. Repeat identical body is safe.
- **Additional state errors:** UPLOAD_EXPIRED, CONTENT_MISMATCH, PAYLOAD_TOO_LARGE

**Request**

Raw PDF bytes with `Content-Type: application/pdf`. No JSON or multipart wrapper.

**Response — HTTP 200**

```json
{
  "data": {
    "id": "00000000-0000-4000-8000-000000000004",
    "filename": "synthetic-transcript.pdf",
    "kind": "TRANSCRIPT",
    "status": "READY",
    "size_bytes": 48012,
    "sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    "version_id": "00000000-0000-4000-8000-000000000005",
    "page_count": 2,
    "quality": "READABLE",
    "failure_code": null,
    "created_at": "2026-10-20T12:00:00Z",
    "deleted_at": null
  },
  "request_id": "req-example-001"
}
```

### `complete_document_upload` — POST `/api/v1/documents/{document_id}/complete`

- **Auth / priority:** USER / P0.
- **Implementation:** MS-026.
- **Idempotency required:** Yes.
- **Query/headers:** No operation-specific query parameters.
- **Rules:** Require actual complete private object and matching recorded/actual SHA; atomically create DOCUMENT_PARSE run; immutable document version.
- **Additional state errors:** UPLOAD_INCOMPLETE, CONTENT_MISMATCH

**Request**

```json
{
  "sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
}
```

**Response — HTTP 202**

```json
{
  "data": {
    "run_id": "00000000-0000-4000-8000-000000000013",
    "status": "QUEUED",
    "status_url": "/api/v1/runs/00000000-0000-4000-8000-000000000013",
    "events_url": "/api/v1/runs/00000000-0000-4000-8000-000000000013/events"
  },
  "request_id": "req-example-001"
}
```

### `list_documents` — GET `/api/v1/documents`

- **Auth / priority:** USER / P0.
- **Implementation:** MS-026.
- **Idempotency required:** No.
- **Query/headers:** limit=20 (1–100); cursor optional; exclude tombstoned.
- **Rules:** Common protocol, consent and ownership rules apply.
- **Additional state errors:** Common errors only.

**Request**

No body.

**Response — HTTP 200**

```json
{
  "data": {
    "items": [
      {
        "id": "00000000-0000-4000-8000-000000000004",
        "filename": "synthetic-transcript.pdf",
        "kind": "TRANSCRIPT",
        "status": "READY",
        "size_bytes": 48012,
        "sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        "version_id": "00000000-0000-4000-8000-000000000005",
        "page_count": 2,
        "quality": "READABLE",
        "failure_code": null,
        "created_at": "2026-10-20T12:00:00Z",
        "deleted_at": null
      }
    ],
    "next_cursor": null
  },
  "request_id": "req-example-001"
}
```

### `get_document` — GET `/api/v1/documents/{document_id}`

- **Auth / priority:** USER / P0.
- **Implementation:** MS-026.
- **Idempotency required:** No.
- **Query/headers:** No operation-specific query parameters.
- **Rules:** Common protocol, consent and ownership rules apply.
- **Additional state errors:** Common errors only.

**Request**

No body.

**Response — HTTP 200**

```json
{
  "data": {
    "id": "00000000-0000-4000-8000-000000000004",
    "filename": "synthetic-transcript.pdf",
    "kind": "TRANSCRIPT",
    "status": "READY",
    "size_bytes": 48012,
    "sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    "version_id": "00000000-0000-4000-8000-000000000005",
    "page_count": 2,
    "quality": "READABLE",
    "failure_code": null,
    "created_at": "2026-10-20T12:00:00Z",
    "deleted_at": null
  },
  "request_id": "req-example-001"
}
```

### `get_document_download` — GET `/api/v1/documents/{document_id}/download`

- **Auth / priority:** USER / P0.
- **Implementation:** MS-026.
- **Idempotency required:** No.
- **Query/headers:** No operation-specific query parameters.
- **Rules:** Owner/active-state check before private signed URL; max five-minute expiry verified against storage adapter. Cache-Control no-store. Returned URL is illustrative, not a working signed URL.
- **Additional state errors:** Common errors only.

**Request**

No body.

**Response — HTTP 200**

```json
{
  "data": {
    "url": "https://storage.example.org/temporary-download",
    "expires_at": "2026-10-20T12:05:00Z"
  },
  "request_id": "req-example-001"
}
```

### `delete_document` — DELETE `/api/v1/documents/{document_id}`

- **Auth / priority:** USER / P0.
- **Implementation:** MS-063.
- **Idempotency required:** Yes.
- **Query/headers:** No operation-specific query parameters.
- **Rules:** Immediately revoke application access and queue purge/invalidation. Previously issued signed URLs can remain usable up to their configured expiry; purge object as soon as possible. Existing idempotency key returns original receipt.
- **Additional state errors:** Common errors only.

**Request**

No body.

**Response — HTTP 202**

```json
{
  "data": {
    "run_id": "00000000-0000-4000-8000-000000000013",
    "status": "QUEUED",
    "status_url": "/api/v1/runs/00000000-0000-4000-8000-000000000013",
    "events_url": "/api/v1/runs/00000000-0000-4000-8000-000000000013/events"
  },
  "request_id": "req-example-001"
}
```

### `list_fact_candidates` — GET `/api/v1/fact-candidates`

- **Auth / priority:** USER / P0.
- **Implementation:** MS-028.
- **Idempotency required:** No.
- **Query/headers:** document_id UUID optional; state=PENDING optional; limit=20 (1–100); cursor optional.
- **Rules:** Common protocol, consent and ownership rules apply.
- **Additional state errors:** Common errors only.

**Request**

No body.

**Response — HTTP 200**

```json
{
  "data": {
    "items": [
      {
        "id": "00000000-0000-4000-8000-000000000007",
        "document_id": "00000000-0000-4000-8000-000000000004",
        "attribute": "education.gpa",
        "value": {
          "type": "GPA",
          "number": "3.70",
          "scale_max": "4.00"
        },
        "evidence_ids": [
          "00000000-0000-4000-8000-000000000006"
        ],
        "state": "PENDING",
        "issues": []
      }
    ],
    "next_cursor": null
  },
  "request_id": "req-example-001"
}
```

### `review_fact_candidates` — POST `/api/v1/fact-candidates/reviews`

- **Auth / priority:** USER / P0.
- **Implementation:** MS-028.
- **Idempotency required:** Yes.
- **Query/headers:** No operation-specific query parameters.
- **Rules:** 1–50 decisions; action ACCEPT, CORRECT or REJECT. CORRECT requires value tagged union and explanation 1–500 chars; other actions forbid those keys. Atomic candidate review plus immutable profile version; reject-only batch may retain same profile version.
- **Additional state errors:** VERSION_CONFLICT, CANDIDATE_ALREADY_REVIEWED

**Request**

```json
{
  "base_profile_version_id": "00000000-0000-4000-8000-000000000002",
  "decisions": [
    {
      "candidate_id": "00000000-0000-4000-8000-000000000007",
      "action": "ACCEPT"
    }
  ]
}
```

**Response — HTTP 200**

```json
{
  "data": {
    "id": "00000000-0000-4000-8000-000000000023",
    "version_id": "00000000-0000-4000-8000-000000000002",
    "version_number": 1,
    "facts": [
      {
        "id": "00000000-0000-4000-8000-000000000003",
        "attribute": "education.gpa",
        "value": {
          "type": "GPA",
          "number": "3.70",
          "scale_max": "4.00"
        },
        "provenance": "USER_CONFIRMED_DOCUMENT",
        "evidence_ids": [
          "00000000-0000-4000-8000-000000000006"
        ],
        "confirmed_at": "2026-10-20T12:00:00Z",
        "valid_from": null,
        "valid_until": null,
        "conflict": false
      }
    ],
    "updated_at": "2026-10-20T12:00:00Z"
  },
  "request_id": "req-example-001"
}
```

### `get_evidence` — GET `/api/v1/evidence/{evidence_id}`

- **Auth / priority:** USER / P0.
- **Implementation:** MS-028.
- **Idempotency required:** No.
- **Query/headers:** No operation-specific query parameters.
- **Rules:** Common protocol, consent and ownership rules apply.
- **Additional state errors:** Common errors only.

**Request**

No body.

**Response — HTTP 200**

```json
{
  "data": {
    "id": "00000000-0000-4000-8000-000000000006",
    "document_id": "00000000-0000-4000-8000-000000000004",
    "document_version_id": "00000000-0000-4000-8000-000000000005",
    "page": 1,
    "start": 0,
    "end": 26,
    "quote": "Cumulative GPA: 3.70 / 4.0",
    "normalized_text_hash": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
  },
  "request_id": "req-example-001"
}
```

### `start_discovery` — POST `/api/v1/discovery-runs`

- **Auth / priority:** USER / P0.
- **Implementation:** MS-046.
- **Idempotency required:** Yes.
- **Query/headers:** No operation-specific query parameters.
- **Rules:** All fields required; goal 20–1000 chars; countries ISO-3166 alpha-2 max 10; fields max 10 strings 1–80 chars; booleans or null indicate no preference. Pin supplied current profile version; budgets controlled by server. Preferences are search/fit intent, never legal eligibility.
- **Additional state errors:** VERSION_CONFLICT, CONSENT_REQUIRED, BUDGET_EXCEEDED

**Request**

```json
{
  "profile_version_id": "00000000-0000-4000-8000-000000000002",
  "goal": "Find funded AI research internships for undergraduate students.",
  "lane": "INTERNSHIP_RESEARCH",
  "preferences": {
    "countries": [
      "EG"
    ],
    "remote": true,
    "fields": [
      "AI"
    ],
    "funding_required": true
  }
}
```

**Response — HTTP 202**

```json
{
  "data": {
    "run_id": "00000000-0000-4000-8000-000000000013",
    "status": "QUEUED",
    "status_url": "/api/v1/runs/00000000-0000-4000-8000-000000000013",
    "events_url": "/api/v1/runs/00000000-0000-4000-8000-000000000013/events"
  },
  "request_id": "req-example-001"
}
```

### `import_opportunity` — POST `/api/v1/opportunity-imports`

- **Auth / priority:** USER / P0.
- **Implementation:** MS-046.
- **Idempotency required:** Yes.
- **Query/headers:** No operation-specific query parameters.
- **Rules:** Both required; URL absolute HTTPS up to 2048 chars; public-network/redirect policy enforced; pin current profile. Does not bypass login or scrape restricted platforms.
- **Additional state errors:** UNSAFE_URL, SOURCE_UNSUPPORTED

**Request**

```json
{
  "profile_version_id": "00000000-0000-4000-8000-000000000002",
  "url": "https://example.org/program"
}
```

**Response — HTTP 202**

```json
{
  "data": {
    "run_id": "00000000-0000-4000-8000-000000000013",
    "status": "QUEUED",
    "status_url": "/api/v1/runs/00000000-0000-4000-8000-000000000013",
    "events_url": "/api/v1/runs/00000000-0000-4000-8000-000000000013/events"
  },
  "request_id": "req-example-001"
}
```

### `list_runs` — GET `/api/v1/runs`

- **Auth / priority:** USER / P0.
- **Implementation:** MS-030.
- **Idempotency required:** No.
- **Query/headers:** status optional enum; kind optional enum; limit=20 (1–100); cursor optional.
- **Rules:** Common protocol, consent and ownership rules apply.
- **Additional state errors:** Common errors only.

**Request**

No body.

**Response — HTTP 200**

```json
{
  "data": {
    "items": [
      {
        "id": "00000000-0000-4000-8000-000000000013",
        "kind": "DISCOVERY",
        "status": "RUNNING",
        "stage": "FETCH",
        "profile_version_id": "00000000-0000-4000-8000-000000000002",
        "cancel_requested": false,
        "progress": {
          "completed_units": 2,
          "total_units": 5
        },
        "funnel": {
          "raw_hits": 24,
          "canonical": 9,
          "official": 6,
          "parsed": 5,
          "evaluated": 2
        },
        "result_refs": {
          "opportunity_ids": [
            "00000000-0000-4000-8000-000000000008"
          ],
          "evaluation_ids": [
            "00000000-0000-4000-8000-000000000014"
          ],
          "draft_ids": []
        },
        "warnings": [],
        "failure_code": null,
        "created_at": "2026-10-20T12:00:00Z",
        "updated_at": "2026-10-20T12:00:00Z"
      }
    ],
    "next_cursor": null
  },
  "request_id": "req-example-001"
}
```

### `get_run` — GET `/api/v1/runs/{run_id}`

- **Auth / priority:** USER / P0.
- **Implementation:** MS-030.
- **Idempotency required:** No.
- **Query/headers:** No operation-specific query parameters.
- **Rules:** Common protocol, consent and ownership rules apply.
- **Additional state errors:** Common errors only.

**Request**

No body.

**Response — HTTP 200**

```json
{
  "data": {
    "id": "00000000-0000-4000-8000-000000000013",
    "kind": "DISCOVERY",
    "status": "RUNNING",
    "stage": "FETCH",
    "profile_version_id": "00000000-0000-4000-8000-000000000002",
    "cancel_requested": false,
    "progress": {
      "completed_units": 2,
      "total_units": 5
    },
    "funnel": {
      "raw_hits": 24,
      "canonical": 9,
      "official": 6,
      "parsed": 5,
      "evaluated": 2
    },
    "result_refs": {
      "opportunity_ids": [
        "00000000-0000-4000-8000-000000000008"
      ],
      "evaluation_ids": [
        "00000000-0000-4000-8000-000000000014"
      ],
      "draft_ids": []
    },
    "warnings": [],
    "failure_code": null,
    "created_at": "2026-10-20T12:00:00Z",
    "updated_at": "2026-10-20T12:00:00Z"
  },
  "request_id": "req-example-001"
}
```

### `cancel_run` — POST `/api/v1/runs/{run_id}/cancel`

- **Auth / priority:** USER / P0.
- **Implementation:** MS-030.
- **Idempotency required:** Yes.
- **Query/headers:** No operation-specific query parameters.
- **Rules:** Set cancel_requested for QUEUED/RUNNING/WAITING_USER; worker commits CANCELLED at safe checkpoint. Already CANCELLED returns 200; other terminal states return 409.
- **Additional state errors:** RUN_TERMINAL

**Request**

```json
{}
```

**Response — HTTP 200**

```json
{
  "data": {
    "id": "00000000-0000-4000-8000-000000000013",
    "kind": "DISCOVERY",
    "status": "RUNNING",
    "stage": "FETCH",
    "profile_version_id": "00000000-0000-4000-8000-000000000002",
    "cancel_requested": false,
    "progress": {
      "completed_units": 2,
      "total_units": 5
    },
    "funnel": {
      "raw_hits": 24,
      "canonical": 9,
      "official": 6,
      "parsed": 5,
      "evaluated": 2
    },
    "result_refs": {
      "opportunity_ids": [
        "00000000-0000-4000-8000-000000000008"
      ],
      "evaluation_ids": [
        "00000000-0000-4000-8000-000000000014"
      ],
      "draft_ids": []
    },
    "warnings": [],
    "failure_code": null,
    "created_at": "2026-10-20T12:00:00Z",
    "updated_at": "2026-10-20T12:00:00Z"
  },
  "request_id": "req-example-001"
}
```

### `get_run_events` — GET `/api/v1/runs/{run_id}/events`

- **Auth / priority:** USER / P0.
- **Implementation:** MS-030.
- **Idempotency required:** No.
- **Query/headers:** No operation-specific query parameters.
- **Rules:** Accept text/event-stream; Authorization bearer through fetch streaming. Last-Event-ID optional nonnegative integer event sequence; heartbeat every 15 seconds; close after terminal event; 24h minimum retention then 410 with GET-run recovery.
- **Additional state errors:** EVENT_CURSOR_EXPIRED

**Request**

No body.

**Response — HTTP 200**

`Content-Type: text/event-stream`; disable proxy buffering. Persisted events use sequence `id`, event `progress`, `result`, `clarification`, `warning` or `terminal`. JSON data is a RunEvent, not the ordinary envelope. Example:

```text
id: 12
event: progress
data: {"run_id":"00000000-0000-4000-8000-000000000013","seq":12,"stage":"FETCH","status":"RUNNING","message_code":"SOURCE_FETCHED","artifact_ref":null,"at":"2026-10-20T12:00:00Z"}

```

RunEvent fields shown are required; artifact_ref nullable or `{ "type":"opportunity|evaluation|draft", "id":"UUID" }` with the actual enum value, never private text. Once stream headers are sent, terminal errors are encoded as a persisted event and current Run state; do not attempt a late HTTP JSON error. Clients deduplicate sequence IDs and recover a lost cursor by fetching Run first.

### `get_clarifications` — GET `/api/v1/runs/{run_id}/clarifications`

- **Auth / priority:** USER / P0.
- **Implementation:** MS-050.
- **Idempotency required:** No.
- **Query/headers:** No operation-specific query parameters.
- **Rules:** Return active set; 404 if none. Only WAITING_USER accepts answers.
- **Additional state errors:** Common errors only.

**Request**

No body.

**Response — HTTP 200**

```json
{
  "data": {
    "id": "00000000-0000-4000-8000-000000000015",
    "run_id": "00000000-0000-4000-8000-000000000013",
    "revision": 1,
    "round": 1,
    "base_profile_version_id": "00000000-0000-4000-8000-000000000002",
    "questions": [
      {
        "id": "q-enrolled",
        "attribute": "education.enrolled",
        "prompt": "Are you currently enrolled?",
        "value_type": "BOOLEAN",
        "reason": "The program requires current enrollment.",
        "required_for_nodes": [
          "r-enrolled"
        ]
      }
    ],
    "expires_at": "2026-10-21T12:00:00Z"
  },
  "request_id": "req-example-001"
}
```

### `answer_clarifications` — POST `/api/v1/runs/{run_id}/clarifications/{clarification_set_id}/answers`

- **Auth / priority:** USER / P0.
- **Implementation:** MS-050.
- **Idempotency required:** Yes.
- **Query/headers:** No operation-specific query parameters.
- **Rules:** All questions answered exactly once; skip=true requires value=null. Match active set revision and current base profile. Atomic new profile version plus run resume; no new search phase.
- **Additional state errors:** VERSION_CONFLICT, CLARIFICATION_EXPIRED, INVALID_RUN_STATE

**Request**

```json
{
  "revision": 1,
  "base_profile_version_id": "00000000-0000-4000-8000-000000000002",
  "answers": [
    {
      "question_id": "q-enrolled",
      "value": {
        "type": "BOOLEAN",
        "value": true
      },
      "skip": false
    }
  ]
}
```

**Response — HTTP 202**

```json
{
  "data": {
    "run_id": "00000000-0000-4000-8000-000000000013",
    "status": "QUEUED",
    "status_url": "/api/v1/runs/00000000-0000-4000-8000-000000000013",
    "events_url": "/api/v1/runs/00000000-0000-4000-8000-000000000013/events"
  },
  "request_id": "req-example-001"
}
```

### `list_opportunities` — GET `/api/v1/opportunities`

- **Auth / priority:** USER / P0.
- **Implementation:** MS-045.
- **Idempotency required:** No.
- **Query/headers:** lane optional; run_id optional owner-scoped membership; availability optional enum; limit=20 (1–100); cursor optional; sort=created_at_desc fixed in P0. Ranked run order is returned using run_id and stored rank; cursor binds filters.
- **Rules:** Common protocol, consent and ownership rules apply.
- **Additional state errors:** Common errors only.

**Request**

No body.

**Response — HTTP 200**

```json
{
  "data": {
    "items": [
      {
        "id": "00000000-0000-4000-8000-000000000008",
        "version_id": "00000000-0000-4000-8000-000000000009",
        "title": "Synthetic Student Research Program",
        "provider": "Synthetic Research Institute",
        "lane": "INTERNSHIP_RESEARCH",
        "cycle": "2027",
        "location_countries": [
          "EG"
        ],
        "remote": true,
        "official_url": "https://example.org/program",
        "authority": "OFFICIAL",
        "availability": "OPEN",
        "deadline": {
          "raw_text": "Apply by 30 November 2026",
          "precision": "DATE",
          "date": "2026-11-30",
          "at": null,
          "timezone": null,
          "ambiguity": null
        },
        "freshness": {
          "state": "FRESH",
          "checked_at": "2026-10-20T12:00:00Z",
          "expires_at": "2026-10-21T12:00:00Z"
        },
        "requirement_set_id": "00000000-0000-4000-8000-000000000012",
        "evaluation_id": null,
        "evaluation_state": "NOT_EVALUATED"
      }
    ],
    "next_cursor": null
  },
  "request_id": "req-example-001"
}
```

### `get_opportunity` — GET `/api/v1/opportunities/{opportunity_id}`

- **Auth / priority:** USER / P0.
- **Implementation:** MS-045.
- **Idempotency required:** No.
- **Query/headers:** No operation-specific query parameters.
- **Rules:** Common protocol, consent and ownership rules apply.
- **Additional state errors:** Common errors only.

**Request**

No body.

**Response — HTTP 200**

```json
{
  "data": {
    "id": "00000000-0000-4000-8000-000000000008",
    "version_id": "00000000-0000-4000-8000-000000000009",
    "title": "Synthetic Student Research Program",
    "provider": "Synthetic Research Institute",
    "lane": "INTERNSHIP_RESEARCH",
    "cycle": "2027",
    "location_countries": [
      "EG"
    ],
    "remote": true,
    "official_url": "https://example.org/program",
    "authority": "OFFICIAL",
    "availability": "OPEN",
    "deadline": {
      "raw_text": "Apply by 30 November 2026",
      "precision": "DATE",
      "date": "2026-11-30",
      "at": null,
      "timezone": null,
      "ambiguity": null
    },
    "freshness": {
      "state": "FRESH",
      "checked_at": "2026-10-20T12:00:00Z",
      "expires_at": "2026-10-21T12:00:00Z"
    },
    "requirement_set_id": "00000000-0000-4000-8000-000000000012",
    "evaluation_id": null,
    "evaluation_state": "NOT_EVALUATED"
  },
  "request_id": "req-example-001"
}
```

### `get_opportunity_version` — GET `/api/v1/opportunities/{opportunity_id}/versions/{opportunity_version_id}`

- **Auth / priority:** USER / P0.
- **Implementation:** MS-045.
- **Idempotency required:** No.
- **Query/headers:** No operation-specific query parameters.
- **Rules:** Version must belong to opportunity. Public policy data still requires application authentication for abuse control.
- **Additional state errors:** Common errors only.

**Request**

No body.

**Response — HTTP 200**

```json
{
  "data": {
    "id": "00000000-0000-4000-8000-000000000008",
    "version_id": "00000000-0000-4000-8000-000000000009",
    "title": "Synthetic Student Research Program",
    "provider": "Synthetic Research Institute",
    "lane": "INTERNSHIP_RESEARCH",
    "cycle": "2027",
    "location_countries": [
      "EG"
    ],
    "remote": true,
    "official_url": "https://example.org/program",
    "authority": "OFFICIAL",
    "availability": "OPEN",
    "deadline": {
      "raw_text": "Apply by 30 November 2026",
      "precision": "DATE",
      "date": "2026-11-30",
      "at": null,
      "timezone": null,
      "ambiguity": null
    },
    "freshness": {
      "state": "FRESH",
      "checked_at": "2026-10-20T12:00:00Z",
      "expires_at": "2026-10-21T12:00:00Z"
    },
    "requirement_set_id": "00000000-0000-4000-8000-000000000012",
    "evaluation_id": null,
    "evaluation_state": "NOT_EVALUATED"
  },
  "request_id": "req-example-001"
}
```

### `get_requirements` — GET `/api/v1/requirement-sets/{requirement_set_id}`

- **Auth / priority:** USER / P0.
- **Implementation:** MS-045.
- **Idempotency required:** No.
- **Query/headers:** No operation-specific query parameters.
- **Rules:** Common protocol, consent and ownership rules apply.
- **Additional state errors:** Common errors only.

**Request**

No body.

**Response — HTTP 200**

```json
{
  "data": {
    "id": "00000000-0000-4000-8000-000000000012",
    "opportunity_version_id": "00000000-0000-4000-8000-000000000009",
    "schema_version": "1.0.0",
    "completeness": "COMPLETE",
    "mandatory_root": "root",
    "preferred_roots": [],
    "nodes": [
      {
        "id": "root",
        "type": "ALL",
        "children": [
          "r-enrolled"
        ]
      },
      {
        "id": "r-enrolled",
        "type": "PREDICATE",
        "modality": "MANDATORY",
        "attribute": "education.enrolled",
        "operator": "EQ",
        "expected": {
          "type": "BOOLEAN",
          "value": true
        },
        "source_span_ids": [
          "00000000-0000-4000-8000-000000000024"
        ],
        "scope": {
          "cycle": "2027",
          "location_countries": [
            "EG"
          ]
        },
        "reference_time": "APPLICATION",
        "interpretation": "DIRECT",
        "evidence_expectation": "KNOWN_FACT"
      }
    ],
    "application_tasks": [
      {
        "key": "statement",
        "label": "Review statement",
        "required": true,
        "kind": "STATEMENT",
        "applicability": "APPLIES",
        "source_span_ids": [
          "00000000-0000-4000-8000-000000000025"
        ]
      }
    ],
    "issues": []
  },
  "request_id": "req-example-001"
}
```

### `get_source` — GET `/api/v1/sources/{source_snapshot_id}`

- **Auth / priority:** USER / P0.
- **Implementation:** MS-045.
- **Idempotency required:** No.
- **Query/headers:** No operation-specific query parameters.
- **Rules:** Path ID is immutable snapshot ID; Source.id is logical source ID. Only public source content; private uploads use evidence endpoint.
- **Additional state errors:** Common errors only.

**Request**

No body.

**Response — HTTP 200**

```json
{
  "data": {
    "id": "00000000-0000-4000-8000-000000000010",
    "url": "https://example.org/program",
    "snapshot_id": "00000000-0000-4000-8000-000000000011",
    "retrieved_at": "2026-10-20T12:00:00Z",
    "content_hash": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
    "authority": "OFFICIAL",
    "completeness": "COMPLETE",
    "spans": [
      {
        "id": "00000000-0000-4000-8000-000000000024",
        "page": null,
        "start": 0,
        "end": 28,
        "quote": "Applicants must be enrolled."
      }
    ]
  },
  "request_id": "req-example-001"
}
```

### `start_evaluation` — POST `/api/v1/evaluations`

- **Auth / priority:** USER / P0.
- **Implementation:** MS-047.
- **Idempotency required:** Yes.
- **Query/headers:** No operation-specific query parameters.
- **Rules:** Both required and current at acceptance; explicitly evaluate one pair under budgets. Source stale requires refresh first, reported as 409 with refresh action.
- **Additional state errors:** VERSION_CONFLICT, SOURCE_STALE, BUDGET_EXCEEDED

**Request**

```json
{
  "opportunity_version_id": "00000000-0000-4000-8000-000000000009",
  "profile_version_id": "00000000-0000-4000-8000-000000000002"
}
```

**Response — HTTP 202**

```json
{
  "data": {
    "run_id": "00000000-0000-4000-8000-000000000013",
    "status": "QUEUED",
    "status_url": "/api/v1/runs/00000000-0000-4000-8000-000000000013",
    "events_url": "/api/v1/runs/00000000-0000-4000-8000-000000000013/events"
  },
  "request_id": "req-example-001"
}
```

### `get_evaluation` — GET `/api/v1/evaluations/{evaluation_id}`

- **Auth / priority:** USER / P0.
- **Implementation:** MS-047.
- **Idempotency required:** No.
- **Query/headers:** No operation-specific query parameters.
- **Rules:** Owner only; currentness computed against current profile/opportunity/config/time even if invalidation worker is delayed.
- **Additional state errors:** Common errors only.

**Request**

No body.

**Response — HTTP 200**

```json
{
  "data": {
    "id": "00000000-0000-4000-8000-000000000014",
    "opportunity_id": "00000000-0000-4000-8000-000000000008",
    "opportunity_version_id": "00000000-0000-4000-8000-000000000009",
    "profile_version_id": "00000000-0000-4000-8000-000000000002",
    "requirement_set_id": "00000000-0000-4000-8000-000000000012",
    "eligibility": "UNKNOWN",
    "availability": "OPEN",
    "fit": {
      "score": 75,
      "coverage": 0.8,
      "components": [
        {
          "name": "field",
          "weight": 0.4,
          "value": 1.0
        },
        {
          "name": "funding",
          "weight": 0.2,
          "value": 1.0
        },
        {
          "name": "location",
          "weight": 0.2,
          "value": 0.0
        },
        {
          "name": "start",
          "weight": 0.2,
          "value": null
        }
      ]
    },
    "readiness": {
      "completed": 2,
      "required": 3,
      "percent": 67,
      "unknown_applicability": 0
    },
    "currentness": "CURRENT",
    "reason_codes": [
      "MISSING_PROFILE_FACT"
    ],
    "leaves": [
      {
        "node_id": "r-enrolled",
        "truth": "UNKNOWN",
        "method": "DETERMINISTIC",
        "fact_ids": [],
        "evidence_ids": [],
        "source_span_ids": [
          "00000000-0000-4000-8000-000000000024"
        ],
        "reason_codes": [
          "MISSING_PROFILE_FACT"
        ],
        "explanation": "Enrollment status has not been confirmed."
      }
    ],
    "as_of": "2026-10-20T12:00:00Z",
    "valid_until": "2026-10-21T12:00:00Z",
    "versions": {
      "evaluator": "1.0.0",
      "prompts": "p1",
      "registry": "m1",
      "freshness": "f1"
    }
  },
  "request_id": "req-example-001"
}
```

### `refresh_opportunity` — POST `/api/v1/opportunities/{opportunity_id}/refresh`

- **Auth / priority:** USER / P0.
- **Implementation:** MS-061.
- **Idempotency required:** Yes.
- **Query/headers:** No operation-specific query parameters.
- **Rules:** Source-level refresh is shared but run and optional caller reevaluation are private. Rate-limit to one pending canonical refresh; link caller to public result without disclosing other users.
- **Additional state errors:** Common errors only.

**Request**

```json
{}
```

**Response — HTTP 202**

```json
{
  "data": {
    "run_id": "00000000-0000-4000-8000-000000000013",
    "status": "QUEUED",
    "status_url": "/api/v1/runs/00000000-0000-4000-8000-000000000013",
    "events_url": "/api/v1/runs/00000000-0000-4000-8000-000000000013/events"
  },
  "request_id": "req-example-001"
}
```

### `list_saved` — GET `/api/v1/saved-opportunities`

- **Auth / priority:** USER / P0.
- **Implementation:** MS-053.
- **Idempotency required:** No.
- **Query/headers:** limit=20 (1–100); cursor optional; saved_at descending.
- **Rules:** Common protocol, consent and ownership rules apply.
- **Additional state errors:** Common errors only.

**Request**

No body.

**Response — HTTP 200**

```json
{
  "data": {
    "items": [
      {
        "opportunity_id": "00000000-0000-4000-8000-000000000008",
        "saved_at": "2026-10-20T12:00:00Z",
        "current_evaluation_id": "00000000-0000-4000-8000-000000000014",
        "evaluation_state": "CURRENT"
      }
    ],
    "next_cursor": null
  },
  "request_id": "req-example-001"
}
```

### `save_opportunity` — PUT `/api/v1/saved-opportunities/{opportunity_id}`

- **Auth / priority:** USER / P0.
- **Implementation:** MS-053.
- **Idempotency required:** No.
- **Query/headers:** No operation-specific query parameters.
- **Rules:** Idempotent by owner/opportunity; existing save returns 200. Requires existing opportunity.
- **Additional state errors:** Common errors only.

**Request**

```json
{}
```

**Response — HTTP 200**

```json
{
  "data": {
    "opportunity_id": "00000000-0000-4000-8000-000000000008",
    "saved_at": "2026-10-20T12:00:00Z",
    "current_evaluation_id": "00000000-0000-4000-8000-000000000014",
    "evaluation_state": "CURRENT"
  },
  "request_id": "req-example-001"
}
```

### `delete_saved` — DELETE `/api/v1/saved-opportunities/{opportunity_id}`

- **Auth / priority:** USER / P0.
- **Implementation:** MS-053.
- **Idempotency required:** No.
- **Query/headers:** No operation-specific query parameters.
- **Rules:** Idempotent even when missing; disable corresponding P1 watch if installed. No response body.
- **Additional state errors:** Common errors only.

**Request**

No body.

**Response — HTTP 204**

No response body.

### `list_applications` — GET `/api/v1/applications`

- **Auth / priority:** USER / P0.
- **Implementation:** MS-056.
- **Idempotency required:** No.
- **Query/headers:** state optional CURRENT or STALE; limit=20 (1–100); cursor optional.
- **Rules:** Common protocol, consent and ownership rules apply.
- **Additional state errors:** Common errors only.

**Request**

No body.

**Response — HTTP 200**

```json
{
  "data": {
    "items": [
      {
        "id": "00000000-0000-4000-8000-000000000016",
        "opportunity_id": "00000000-0000-4000-8000-000000000008",
        "opportunity_version_id": "00000000-0000-4000-8000-000000000009",
        "profile_version_id": "00000000-0000-4000-8000-000000000002",
        "evaluation_id": "00000000-0000-4000-8000-000000000014",
        "revision": 1,
        "state": "CURRENT",
        "items": [
          {
            "id": "00000000-0000-4000-8000-000000000017",
            "key": "cv",
            "label": "Prepare CV",
            "kind": "DOCUMENT",
            "required": true,
            "applicability": "APPLIES",
            "status": "TODO",
            "evidence_ids": [],
            "draft_id": null
          }
        ],
        "readiness": {
          "completed": 0,
          "required": 1,
          "percent": 0,
          "unknown_applicability": 0
        },
        "latest_draft_id": null,
        "accepted_draft_id": null,
        "created_at": "2026-10-20T12:00:00Z"
      }
    ],
    "next_cursor": null
  },
  "request_id": "req-example-001"
}
```

### `create_application` — POST `/api/v1/applications`

- **Auth / priority:** USER / P0.
- **Implementation:** MS-056.
- **Idempotency required:** Yes.
- **Query/headers:** No operation-specific query parameters.
- **Rules:** Current evaluation required; UNKNOWN or NOT_MET is allowed with visible unresolved blockers, never represented as eligibility approval. Existing current workspace returns 200; an existing stale workspace with replace_stale=false returns 409 APPLICATION_EXISTS. replace_stale=true rebases stale workspace into new revision, preserves only still-valid completed tasks and clears draft acceptance.
- **Additional state errors:** EVALUATION_STALE, APPLICATION_EXISTS

**Request**

```json
{
  "evaluation_id": "00000000-0000-4000-8000-000000000014",
  "replace_stale": false
}
```

**Response — HTTP 201**

```json
{
  "data": {
    "id": "00000000-0000-4000-8000-000000000016",
    "opportunity_id": "00000000-0000-4000-8000-000000000008",
    "opportunity_version_id": "00000000-0000-4000-8000-000000000009",
    "profile_version_id": "00000000-0000-4000-8000-000000000002",
    "evaluation_id": "00000000-0000-4000-8000-000000000014",
    "revision": 1,
    "state": "CURRENT",
    "items": [
      {
        "id": "00000000-0000-4000-8000-000000000017",
        "key": "cv",
        "label": "Prepare CV",
        "kind": "DOCUMENT",
        "required": true,
        "applicability": "APPLIES",
        "status": "TODO",
        "evidence_ids": [],
        "draft_id": null
      }
    ],
    "readiness": {
      "completed": 0,
      "required": 1,
      "percent": 0,
      "unknown_applicability": 0
    },
    "latest_draft_id": null,
    "accepted_draft_id": null,
    "created_at": "2026-10-20T12:00:00Z"
  },
  "request_id": "req-example-001"
}
```

### `get_application` — GET `/api/v1/applications/{application_id}`

- **Auth / priority:** USER / P0.
- **Implementation:** MS-056.
- **Idempotency required:** No.
- **Query/headers:** No operation-specific query parameters.
- **Rules:** Common protocol, consent and ownership rules apply.
- **Additional state errors:** Common errors only.

**Request**

No body.

**Response — HTTP 200**

```json
{
  "data": {
    "id": "00000000-0000-4000-8000-000000000016",
    "opportunity_id": "00000000-0000-4000-8000-000000000008",
    "opportunity_version_id": "00000000-0000-4000-8000-000000000009",
    "profile_version_id": "00000000-0000-4000-8000-000000000002",
    "evaluation_id": "00000000-0000-4000-8000-000000000014",
    "revision": 1,
    "state": "CURRENT",
    "items": [
      {
        "id": "00000000-0000-4000-8000-000000000017",
        "key": "cv",
        "label": "Prepare CV",
        "kind": "DOCUMENT",
        "required": true,
        "applicability": "APPLIES",
        "status": "TODO",
        "evidence_ids": [],
        "draft_id": null
      }
    ],
    "readiness": {
      "completed": 0,
      "required": 1,
      "percent": 0,
      "unknown_applicability": 0
    },
    "latest_draft_id": null,
    "accepted_draft_id": null,
    "created_at": "2026-10-20T12:00:00Z"
  },
  "request_id": "req-example-001"
}
```

### `patch_checklist_item` — PATCH `/api/v1/applications/{application_id}/items/{item_id}`

- **Auth / priority:** USER / P0.
- **Implementation:** MS-056.
- **Idempotency required:** Yes.
- **Query/headers:** No operation-specific query parameters.
- **Rules:** All fields required; status TODO or DONE; evidence_ids max 10. Statement item completion is controlled solely by draft acceptance, not this endpoint.
- **Additional state errors:** VERSION_CONFLICT, DRAFT_REVIEW_REQUIRED, EVIDENCE_UNAVAILABLE

**Request**

```json
{
  "base_revision": 1,
  "status": "DONE",
  "evidence_ids": [
    "00000000-0000-4000-8000-000000000006"
  ]
}
```

**Response — HTTP 200**

```json
{
  "data": {
    "id": "00000000-0000-4000-8000-000000000016",
    "opportunity_id": "00000000-0000-4000-8000-000000000008",
    "opportunity_version_id": "00000000-0000-4000-8000-000000000009",
    "profile_version_id": "00000000-0000-4000-8000-000000000002",
    "evaluation_id": "00000000-0000-4000-8000-000000000014",
    "revision": 1,
    "state": "CURRENT",
    "items": [
      {
        "id": "00000000-0000-4000-8000-000000000017",
        "key": "cv",
        "label": "Prepare CV",
        "kind": "DOCUMENT",
        "required": true,
        "applicability": "APPLIES",
        "status": "TODO",
        "evidence_ids": [],
        "draft_id": null
      }
    ],
    "readiness": {
      "completed": 0,
      "required": 1,
      "percent": 0,
      "unknown_applicability": 0
    },
    "latest_draft_id": null,
    "accepted_draft_id": null,
    "created_at": "2026-10-20T12:00:00Z"
  },
  "request_id": "req-example-001"
}
```

### `start_draft` — POST `/api/v1/applications/{application_id}/drafts`

- **Auth / priority:** USER / P0.
- **Implementation:** MS-059.
- **Idempotency required:** Yes.
- **Query/headers:** No operation-specific query parameters.
- **Rules:** Current workspace, target_words integer 150–500 and known source writing instructions. Reject if no statement task or stale input. Store generated draft ID in run result_refs.
- **Additional state errors:** VERSION_CONFLICT, APPLICATION_STALE, NO_STATEMENT_TASK

**Request**

```json
{
  "base_revision": 1,
  "target_words": 250
}
```

**Response — HTTP 202**

```json
{
  "data": {
    "run_id": "00000000-0000-4000-8000-000000000013",
    "status": "QUEUED",
    "status_url": "/api/v1/runs/00000000-0000-4000-8000-000000000013",
    "events_url": "/api/v1/runs/00000000-0000-4000-8000-000000000013/events"
  },
  "request_id": "req-example-001"
}
```

### `get_draft` — GET `/api/v1/drafts/{draft_id}`

- **Auth / priority:** USER / P0.
- **Implementation:** MS-059.
- **Idempotency required:** No.
- **Query/headers:** No operation-specific query parameters.
- **Rules:** Owner only; refuse content access if material backing evidence was deleted and privacy invalidation requires suppression.
- **Additional state errors:** Common errors only.

**Request**

No body.

**Response — HTTP 200**

```json
{
  "data": {
    "id": "00000000-0000-4000-8000-000000000018",
    "application_id": "00000000-0000-4000-8000-000000000016",
    "version_number": 1,
    "profile_version_id": "00000000-0000-4000-8000-000000000002",
    "opportunity_version_id": "00000000-0000-4000-8000-000000000009",
    "text": "I am interested in this student research program.",
    "validation": "PENDING",
    "claims": [],
    "issues": [],
    "accepted_at": null,
    "created_at": "2026-10-20T12:00:00Z"
  },
  "request_id": "req-example-001"
}
```

### `edit_draft` — POST `/api/v1/drafts/{draft_id}/versions`

- **Auth / priority:** USER / P0.
- **Implementation:** MS-059.
- **Idempotency required:** Yes.
- **Query/headers:** No operation-specific query parameters.
- **Rules:** text shown abbreviated only; real payload 150–500 words/max 8000 characters. Create new draft UUID/version, clear acceptance and enqueue DRAFT_VALIDATE; response draft.validation PENDING. User edits also require claim validation.
- **Additional state errors:** VERSION_CONFLICT, APPLICATION_STALE

**Request**

```json
{
  "base_application_revision": 2,
  "text": "An applicant-authored revised statement of 150 to 500 words is supplied here."
}
```

**Response — HTTP 202**

```json
{
  "data": {
    "draft": {
      "id": "00000000-0000-4000-8000-000000000018",
      "application_id": "00000000-0000-4000-8000-000000000016",
      "version_number": 1,
      "profile_version_id": "00000000-0000-4000-8000-000000000002",
      "opportunity_version_id": "00000000-0000-4000-8000-000000000009",
      "text": "I am interested in this student research program.",
      "validation": "PENDING",
      "claims": [],
      "issues": [],
      "accepted_at": null,
      "created_at": "2026-10-20T12:00:00Z"
    },
    "validation_run": {
      "run_id": "00000000-0000-4000-8000-000000000013",
      "status": "QUEUED",
      "status_url": "/api/v1/runs/00000000-0000-4000-8000-000000000013",
      "events_url": "/api/v1/runs/00000000-0000-4000-8000-000000000013/events"
    }
  },
  "request_id": "req-example-001"
}
```

### `accept_draft` — POST `/api/v1/drafts/{draft_id}/accept`

- **Auth / priority:** USER / P0.
- **Implementation:** MS-059.
- **Idempotency required:** Yes.
- **Query/headers:** No operation-specific query parameters.
- **Rules:** Exactly true confirmation; validate ownership, latest draft, VALID validation, no deleted support and current pinned versions at transaction time. Bind acceptance to hash/version and complete statement task.
- **Additional state errors:** VERSION_CONFLICT, DRAFT_NOT_VALID, DRAFT_NOT_CURRENT

**Request**

```json
{
  "base_application_revision": 3,
  "confirmed_review": true
}
```

**Response — HTTP 200**

```json
{
  "data": {
    "id": "00000000-0000-4000-8000-000000000016",
    "opportunity_id": "00000000-0000-4000-8000-000000000008",
    "opportunity_version_id": "00000000-0000-4000-8000-000000000009",
    "profile_version_id": "00000000-0000-4000-8000-000000000002",
    "evaluation_id": "00000000-0000-4000-8000-000000000014",
    "revision": 1,
    "state": "CURRENT",
    "items": [
      {
        "id": "00000000-0000-4000-8000-000000000017",
        "key": "cv",
        "label": "Prepare CV",
        "kind": "DOCUMENT",
        "required": true,
        "applicability": "APPLIES",
        "status": "TODO",
        "evidence_ids": [],
        "draft_id": null
      }
    ],
    "readiness": {
      "completed": 0,
      "required": 1,
      "percent": 0,
      "unknown_applicability": 0
    },
    "latest_draft_id": null,
    "accepted_draft_id": null,
    "created_at": "2026-10-20T12:00:00Z"
  },
  "request_id": "req-example-001"
}
```

### `export_application` — GET `/api/v1/applications/{application_id}/export`

- **Auth / priority:** USER / P0.
- **Implementation:** MS-059.
- **Idempotency required:** No.
- **Query/headers:** format=markdown only; default markdown.
- **Rules:** Only current accepted draft if statement task exists. Include checklist and links; no implicit submission. Content-Disposition attachment with server-controlled filename.
- **Additional state errors:** APPLICATION_STALE, DRAFT_REVIEW_REQUIRED

**Request**

No body.

**Response — HTTP 200**

`Content-Type: text/markdown; charset=utf-8`; attachment filename `benefitbridge-application.md`; UTF-8 text contains opportunity/version/source URLs, checklist and current accepted statement if applicable. JSON errors still use the common problem contract. Exports contain only the caller’s data and never auto-submit to a provider.

### `get_usage` — GET `/api/v1/usage`

- **Auth / priority:** USER / P0.
- **Implementation:** MS-068.
- **Idempotency required:** No.
- **Query/headers:** No operation-specific query parameters.
- **Rules:** Common protocol, consent and ownership rules apply.
- **Additional state errors:** Common errors only.

**Request**

No body.

**Response — HTTP 200**

```json
{
  "data": {
    "period_start": "2026-10-20T00:00:00Z",
    "period_end": "2026-10-21T00:00:00Z",
    "currency": "USD",
    "spent_microusd": 125000,
    "reserved_microusd": 100000,
    "limit_microusd": 2000000,
    "active_runs": 1,
    "active_run_limit": 2
  },
  "request_id": "req-example-001"
}
```

### `delete_account` — DELETE `/api/v1/me`

- **Auth / priority:** USER / P0.
- **Implementation:** MS-064.
- **Idempotency required:** Yes.
- **Query/headers:** No operation-specific query parameters.
- **Rules:** Current JWT and confirmation required; generate random 256-bit token, persist SHA-256 only except encrypted 24h idempotency replay record. Immediately tombstone. Ordinary run URLs are no longer accessible; receipt capability is the only post-deletion status path. Replayed same-key DELETE accepted only for same still-verifiable JWT subject within replay TTL.
- **Additional state errors:** Common errors only.

**Request**

```json
{
  "confirmation": "DELETE"
}
```

**Response — HTTP 202**

```json
{
  "data": {
    "receipt_id": "00000000-0000-4000-8000-000000000021",
    "receipt_token": "synthetic-example-token-not-a-real-secret",
    "receipt_url": "/api/v1/deletion-receipts/00000000-0000-4000-8000-000000000021",
    "status": "PENDING",
    "expires_at": "2026-10-27T12:00:00Z"
  },
  "request_id": "req-example-001"
}
```

### `get_deletion_receipt` — GET `/api/v1/deletion-receipts/{receipt_id}`

- **Auth / priority:** RECEIPT / P0.
- **Implementation:** MS-064.
- **Idempotency required:** No.
- **Query/headers:** No operation-specific query parameters.
- **Rules:** Authorization: DeletionReceipt token. Constant-time hash check; token expires seven days after request. status PENDING, COMPLETE or FAILED; no personal data or raw error details. backup_retention_until populated from verified policy, not guessed.
- **Additional state errors:** Common errors only.

**Request**

No body.

**Response — HTTP 200**

```json
{
  "data": {
    "id": "00000000-0000-4000-8000-000000000021",
    "status": "PENDING",
    "requested_at": "2026-10-20T12:00:00Z",
    "active_store_deleted_at": null,
    "backup_retention_until": null
  },
  "request_id": "req-example-001"
}
```

### `health_live` — GET `/api/v1/health/live`

- **Auth / priority:** PUBLIC / P0.
- **Implementation:** MS-074.
- **Idempotency required:** No.
- **Query/headers:** No operation-specific query parameters.
- **Rules:** Process alive, no expensive dependencies.
- **Additional state errors:** Common errors only.

**Request**

No body.

**Response — HTTP 200**

```json
{
  "data": {
    "status": "ok"
  },
  "request_id": "req-example-001"
}
```

### `health_ready` — GET `/api/v1/health/ready`

- **Auth / priority:** PUBLIC / P0.
- **Implementation:** MS-074.
- **Idempotency required:** No.
- **Query/headers:** No operation-specific query parameters.
- **Rules:** Return 200 when DB, schema, required config and worker heartbeat healthy, otherwise 503 standard problem body. No paid inference request per probe.
- **Additional state errors:** Common errors only.

**Request**

No body.

**Response — HTTP 200**

```json
{
  "data": {
    "status": "ready"
  },
  "request_id": "req-example-001"
}
```

### `get_capabilities` — GET `/api/v1/capabilities`

- **Auth / priority:** PUBLIC / P0.
- **Implementation:** MS-068.
- **Idempotency required:** No.
- **Query/headers:** No operation-specific query parameters.
- **Rules:** Common protocol, consent and ownership rules apply.
- **Additional state errors:** Common errors only.

**Request**

No body.

**Response — HTTP 200**

```json
{
  "data": {
    "api_version": "1",
    "watch": false,
    "demo_reset": true,
    "supported_lanes": [
      "INTERNSHIP_RESEARCH",
      "SCHOLARSHIP_PROGRAM"
    ],
    "supported_document_types": [
      "application/pdf"
    ],
    "max_document_bytes": 10485760,
    "max_document_pages": 20,
    "inference_available": true,
    "deep_available": false
  },
  "request_id": "req-example-001"
}
```

### `reset_demo` — POST `/api/v1/demo/reset`

- **Auth / priority:** DEMO / P0.
- **Implementation:** MS-084.
- **Idempotency required:** Yes.
- **Query/headers:** No operation-specific query parameters.
- **Rules:** DEMO_ENABLED and verified account.is_demo required. scenario MET_READY, GPA_NOT_MET or UNKNOWN_AUTHORIZATION. Only reset current tenant; rate limit one/minute, serialize reset, block conflicting runs during reset.
- **Additional state errors:** FEATURE_DISABLED, RESET_IN_PROGRESS

**Request**

```json
{
  "scenario": "UNKNOWN_AUTHORIZATION"
}
```

**Response — HTTP 202**

```json
{
  "data": {
    "run_id": "00000000-0000-4000-8000-000000000013",
    "status": "QUEUED",
    "status_url": "/api/v1/runs/00000000-0000-4000-8000-000000000013",
    "events_url": "/api/v1/runs/00000000-0000-4000-8000-000000000013/events"
  },
  "request_id": "req-example-001"
}
```

### `list_watches` — GET `/api/v1/watches`

- **Auth / priority:** USER / P1.
- **Implementation:** MS-072.
- **Idempotency required:** No.
- **Query/headers:** limit=20 (1–100); cursor optional.
- **Rules:** Common protocol, consent and ownership rules apply.
- **Additional state errors:** Common errors only.

**Request**

No body.

**Response — HTTP 200**

```json
{
  "data": {
    "items": [
      {
        "id": "00000000-0000-4000-8000-000000000019",
        "opportunity_id": "00000000-0000-4000-8000-000000000008",
        "revision": 1,
        "enabled": true,
        "interval_hours": 24,
        "next_due_at": "2026-10-21T12:00:00Z"
      }
    ],
    "next_cursor": null
  },
  "request_id": "req-example-001"
}
```

### `create_watch` — POST `/api/v1/watches`

- **Auth / priority:** USER / P1.
- **Implementation:** MS-072.
- **Idempotency required:** Yes.
- **Query/headers:** No operation-specific query parameters.
- **Rules:** Saved opportunity required; interval 24 or 72; at most 10 active watches/account.
- **Additional state errors:** WATCH_EXISTS, NOT_SAVED, QUOTA_EXCEEDED

**Request**

```json
{
  "opportunity_id": "00000000-0000-4000-8000-000000000008",
  "interval_hours": 24
}
```

**Response — HTTP 201**

```json
{
  "data": {
    "id": "00000000-0000-4000-8000-000000000019",
    "opportunity_id": "00000000-0000-4000-8000-000000000008",
    "revision": 1,
    "enabled": true,
    "interval_hours": 24,
    "next_due_at": "2026-10-21T12:00:00Z"
  },
  "request_id": "req-example-001"
}
```

### `patch_watch` — PATCH `/api/v1/watches/{watch_id}`

- **Auth / priority:** USER / P1.
- **Implementation:** MS-072.
- **Idempotency required:** Yes.
- **Query/headers:** No operation-specific query parameters.
- **Rules:** base_revision required; at least one of enabled or interval_hours. Disabled watches retain state.
- **Additional state errors:** VERSION_CONFLICT

**Request**

```json
{
  "base_revision": 1,
  "enabled": false,
  "interval_hours": 72
}
```

**Response — HTTP 200**

```json
{
  "data": {
    "id": "00000000-0000-4000-8000-000000000019",
    "opportunity_id": "00000000-0000-4000-8000-000000000008",
    "revision": 1,
    "enabled": true,
    "interval_hours": 24,
    "next_due_at": "2026-10-21T12:00:00Z"
  },
  "request_id": "req-example-001"
}
```

### `delete_watch` — DELETE `/api/v1/watches/{watch_id}`

- **Auth / priority:** USER / P1.
- **Implementation:** MS-072.
- **Idempotency required:** No.
- **Query/headers:** No operation-specific query parameters.
- **Rules:** Idempotent owner-scoped delete; retain notifications per account retention.
- **Additional state errors:** Common errors only.

**Request**

No body.

**Response — HTTP 204**

No response body.

### `list_notifications` — GET `/api/v1/notifications`

- **Auth / priority:** USER / P1.
- **Implementation:** MS-072.
- **Idempotency required:** No.
- **Query/headers:** unread optional boolean; limit=20 (1–100); cursor optional.
- **Rules:** Common protocol, consent and ownership rules apply.
- **Additional state errors:** Common errors only.

**Request**

No body.

**Response — HTTP 200**

```json
{
  "data": {
    "items": [
      {
        "id": "00000000-0000-4000-8000-000000000020",
        "watch_id": "00000000-0000-4000-8000-000000000019",
        "opportunity_id": "00000000-0000-4000-8000-000000000008",
        "opportunity_version_id": "00000000-0000-4000-8000-000000000009",
        "kind": "SOURCE_CHANGED",
        "summary": "Published deadline changed.",
        "read_at": null,
        "created_at": "2026-10-20T12:00:00Z"
      }
    ],
    "next_cursor": null
  },
  "request_id": "req-example-001"
}
```

### `read_notification` — PUT `/api/v1/notifications/{notification_id}/read`

- **Auth / priority:** USER / P1.
- **Implementation:** MS-072.
- **Idempotency required:** No.
- **Query/headers:** No operation-specific query parameters.
- **Rules:** Idempotent; first read_at retained.
- **Additional state errors:** Common errors only.

**Request**

```json
{}
```

**Response — HTTP 200**

```json
{
  "data": {
    "id": "00000000-0000-4000-8000-000000000020",
    "watch_id": "00000000-0000-4000-8000-000000000019",
    "opportunity_id": "00000000-0000-4000-8000-000000000008",
    "opportunity_version_id": "00000000-0000-4000-8000-000000000009",
    "kind": "SOURCE_CHANGED",
    "summary": "Published deadline changed.",
    "read_at": null,
    "created_at": "2026-10-20T12:00:00Z"
  },
  "request_id": "req-example-001"
}
```

## Operational boundaries

No public administrative data API is introduced. Provider-registry updates, annotation imports, demo account provisioning, migrations and release checks are controlled CLI/operator tasks under repository access; they must use the same service layer and audit rules. The only P1 endpoints are watches and notifications and they return 403 FEATURE_DISABLED when disabled. P1 operations enter generated OpenAPI when their implementation is merged. A central prefix feature gate returns FEATURE_DISABLED while watch is off, including before those routers are installed; no P0 client depends on a P1 generated type.

Supabase auth/database/storage and Nebius/Tavily calls are external integrations described in design.md; their credentials and provider-specific endpoints are not exposed to users. Tests use equivalent fake adapters. Frontend must not query application tables directly through Supabase SDK or bypass API ownership/currentness rules.
