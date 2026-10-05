# MS-020 ? Nebius structured inference

Owner M3; reviewer M1. Prerequisites MS-003, MS-010 and MS-019 are merged.

## Delivered interfaces

`NebiusLLM` implements the same typed LLM port as deterministic fake adapters.
Its `generate(LlmRequest, response_model)` makes exactly one **pre-reserved**
HTTP attempt. The caller must acquire the reservation and reconcile it; a random
UUID in CallLimits is not evidence of funding. This is the existing MS-003 port
contract, not a new public API.

`BudgetedInference(llm, budget, run_id=...).infer(InferenceTask(...), response_model,
total_timeout_seconds=..., allow_repair=True)` is the funded composition for
normal tasks. Supply the existing MS-019 BudgetService with verified actor context
and a persisted private run, or its public-maintenance configuration with no run.
It reserves configured maximum token cost before every attempt. Transactions
close before HTTP I/O. Only SCHEMA_INVALID may trigger one additional, separately
reserved call. The invalid response and validation details are never inserted
into a repair prompt. Rate limits, outages and truncation return typed failures
for the existing bounded workflow retry policy; the adapter never retries them.
Retry-After is preserved as bounded, safe metadata, not an automatic sleep.

The facade checks an overall 1?120 second deadline, the model's timeout and each
reservation's expiry. Expired funding cannot start a request. Cancellation awaits
shielded accounting. Unknown charges remain held, including successful token
usage without a verified bill. Price-based estimates are never fabricated as
provider-billed cost. Explicit zero is recorded only when a reserved attempt is
rejected locally before HTTP begins.

`bind_nebius(existing_dependencies, adapter)` returns an explicit real-mode
Dependencies binding without editing the shared registry/composition. The
existing readiness validation still rejects missing production handlers or fake
provider bindings. No provider is auto-loaded or silently replaced with a fake.

Construct the adapter with a configured ModelRegistry, trusted real preflight
report, injected Clock, SecretStr credential, AsyncClient and **verified local
model token counter**. The counter receives the complete request payload and
must include chat-template and schema overhead. No generic guessed tokenizer,
model name, price or endpoint is supplied. The existing MODEL_REGISTRY_JSON and
NEBIUS_API_KEY configuration names are sufficient; no new environment settings,
SDK dependencies or central configuration changes are introduced. The supplied
HTTP client must use a normal nonretrying transport and must not log private
bodies or credentials. Production must not use test MockTransport/counters.

The surrounding authenticated stage retains responsibility for consent,
minimal relevant evidence selection, input currentness, citation validation and
fenced publication. This adapter does not fetch documents or send search queries.

## Requirement and safety trace

- R07.03 / US-07.03: Pydantic-schema responses, duplicate/nonfinite JSON rejection,
  output token/context limits, tool/refusal rejection and one bounded repair.
  Unsupported schemas fail explicitly; task owners decide the appropriate UNKNOWN
  semantic outcome. No unconstrained JSON fallback or invented inference result.
- R13.02 / US-13.02: bounded task-data message, fixed versioned safety policy,
  no tools, no raw response replay and hashes/counts-only transport telemetry.
  Provider reasoning_content is discarded and is neither returned nor persisted.
- R14.02 / US-14.02: configured role resolution and fresh real preflight required;
  optional FAST fallback follows the existing registry, while missing DEEP fails.
  No hard-coded model IDs or capability escalation. Five consecutive retryable
  failures open a 60-second circuit; one funded probe is allowed after cooldown.

The payload uses JSON-schema response_format and max_completion_tokens, which
bounds both visible and reasoning tokens. It follows the
[Nebius structured output documentation](https://docs.tokenfactory.nebius.com/ai-models-inference/json)
and [published inference API schema](https://api.tokenfactory.nebius.com/openapi.json).
Redirects, streaming generation and compressed responses are refused. Request,
schema and response byte caps are configurable internal AdapterLimits. Errors
expose safe codes, counts and retry timing, never provider response text or secrets.

## Verification and reviewer handoff

Commands run from the repository root (GNU Make is unavailable, so its relevant
commands were run directly):

- `python -m uv run --frozen --offline python -m pytest tests/inference/test_nebius.py -q --tb=short`:
  47 scenarios passed.
- `python -m uv run --frozen --offline python -m pytest --suite unit -q --tb=short`:
  690 passed, 137 integration/live cases deselected. The added oversized-token-count
  regression also passed in the targeted 47-case suite.
- `python -m uv run --frozen --offline ruff check backend tests` and
  `python -m uv run --frozen --offline ruff format --check backend tests`: passed.
- `python -m uv run --frozen --offline mypy`: passed, 33 source files.
- `python -m uv run --frozen --offline python scripts/check_contract.py`: passed;
  deterministic OpenAPI/client remain unchanged.
- `pnpm.cmd --dir frontend lint`: passed formatting and TypeScript.
- `pnpm.cmd --dir frontend test`: 33 passed.

All inference HTTP is intercepted by deterministic MockTransport under the
ordinary CI network guard; synthetic token counter, clock, preflight evidence
and ledger are explicitly fixtures. No measured provider performance or pricing
claim is made. PostgreSQL integration was not rerun for this adapter-only change;
MS-019 remains the atomic database implementation. Live provider smoke/preflight
for a deployment is NOT_RUN and requires separately approved paid execution.

Changed source paths: inference/nebius.py and inference/prompts/; corresponding
checks: tests/inference/test_nebius.py. No schema/API, migration, configuration,
registry or shared-port changes, and no regenerated artifacts. No missing strict
prerequisite or source-scope handoff is needed.

M1 reviewer focus: reserve/reconcile ordering, unknown billing retention,
reservation/deadline races, cancellation and circuit probes; check real deployment
counter/preflight bindings before allowing funded production execution.
Next-ready consumers: MS-027, MS-034, MS-035 and MS-039 through these interfaces.
