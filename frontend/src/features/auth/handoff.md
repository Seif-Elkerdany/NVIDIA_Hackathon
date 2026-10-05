# MS-009 integration and operator contract

Auth uses the real Supabase SDK with `persistSession=false`, memory storage,
automatic refresh while the page is open and `detectSessionInUrl=false`.
Reloading creates an unauthenticated session. SDK access is confined to the
provider adapter. The application API uses the shared transport with bearer
headers. Recovery sessions cannot supply application bearer credentials.

The frontend requires `VITE_SUPABASE_URL`, `VITE_SUPABASE_PUBLISHABLE_KEY`,
`VITE_PROCESSING_NOTICE_VERSION` and `VITE_PROCESSING_NOTICE_TEXT`. The notice
version must match backend `PROCESSING_NOTICE_VERSION`. The text is the complete
operator-approved notice, including actual provider handling, retention and
deletion-marker purpose. It renders as escaped plain text. Missing production
configuration fails closed; development can display an unavailable account
service. A service-role/secret key is rejected by the browser config validator.
Copy `frontend/.env.example` to `frontend/.env.local` and supply those values
before starting Vite. They are public browser configuration, not backend or
service-role credentials. Vite embeds them at build time for production.

## Email configuration

Configure Supabase Site URL to the exact application origin. Allowlist
`https://YOUR_ORIGIN/account/confirm` and
`https://YOUR_ORIGIN/account/recovery` (loopback HTTP is development only).
Configure confirmation and password recovery templates to use one-time hashes
in fragments, rather than bearer tokens or query strings:

```html
<!-- Confirmation template -->
<a href="{{ .RedirectTo }}#token_hash={{ .TokenHash }}&type=email"
  >Confirm email</a
>
<!-- Recovery template -->
<a href="{{ .RedirectTo }}#token_hash={{ .TokenHash }}&type=recovery"
  >Reset password</a
>
```

The browser immediately replaces the callback URL and history state, then
verifies the hash through `verifyOtp`. No callback token is stored in browser
storage or query caches. Fragment hashes are not sent to the hosting server.
Invalid, duplicate, implicit-bearer and query-based callbacks are scrubbed and
rejected. Do not attach analytics before callback consumption, log browser
locations, or record request bodies. Configure hosting access-log redaction for
query strings, a strict CSP permitting only the configured auth origin, and
SPA fallback for both recovery and confirmation paths. These are deployment
controls; this sprint does not deploy or send live recovery email.

The implementation follows [Supabase session configuration](https://supabase.com/docs/reference/javascript/initializing)
and [email template/hash verification](https://supabase.com/docs/guides/auth/auth-email-templates).

## Dependent feature interface

The app entry creates the SDK provider, consumes callbacks before rendering and
binds bearer injection and account consent PATCH to the shared API transport.
`AuthBoundary` is mounted beneath the shell QueryClientProvider. Account/confirmation/
recovery routes use `AccountScreen`; consent uses `ConsentScreen`.
Processing routes are wrapped in `ProcessingGuard`. Account/preferences/deletion routes
remain available without processing consent. `useProcessingAccess` exposes
confirmed consent and account state, never token contents. Generated Account and
PatchMe are consumed without a parallel DTO. Old private queries are cancelled
and removed on identity transitions. Backend authorization remains authoritative.

Next owners can mount the profile editor in MS-018 and progress views in MS-031
when their other prerequisites are met. M6 should review callback sanitation,
SDK/session expiry, stale consent and the guarded-route browser checks.

## Verification

The pinned SDK dependency is `@supabase/supabase-js@2.117.2` (MIT, Node >=22).
The standard frontend `test`, `lint` and `typecheck` commands now include auth.
Run `pnpm --dir frontend install --frozen-lockfile`, `make check` and
`pnpm --dir frontend build` for installation, static, unit and contract checks.
No schema, migration or public endpoint changes are required.

For browser checks, run a local Vite server with this synthetic environment:

```text
VITE_SUPABASE_URL=https://synthetic.supabase.invalid
VITE_SUPABASE_PUBLISHABLE_KEY=sb_publishable_synthetic
VITE_PROCESSING_NOTICE_VERSION=2026-10-01
VITE_PROCESSING_NOTICE_TEXT=Synthetic processing notice. <script>private()</script>
```

Then run these from the repository root with local Edge installed:

```sh
uv run --frozen --with playwright==1.63.0 python frontend/tests/auth_browser.py
uv run --frozen --with playwright==1.63.0 python frontend/tests/shell_browser.py
```

Browser checks use the real SDK with intercepted synthetic HTTP. They cover
signup/login/reset/recovery, memory-only sessions and reload, bearer injection,
consent decline/failed PATCH/acceptance, expiry/401, stale consent responses after
sign-out, callback cleanup, storage isolation, route focus and mobile layout.
They do not verify delivery of live provider emails or hosting settings.

## Completion handoff

R01.01 / US-01.01: the SDK and account routes are connected, API requests use
memory-only bearer credentials, and reload/expiry/401 require sign-in again.
R01.02 / US-01.02: consent is recorded through the documented account PATCH;
decline, an obsolete notice or a failed write blocks processing.
R12.01 / US-12.01: account, consent and guarded profile/document routes follow
the shell onboarding sequence, with documents remaining optional.

Integration changes are in `frontend/package.json`, `frontend/pnpm-lock.yaml`,
`frontend/tsconfig.json`, `frontend/.env.example`, `frontend/index.html`,
`frontend/src/app/{App,main}.tsx`, `frontend/src/lib/api.ts` and the auth feature.
Corresponding checks are in `frontend/tests/{api.test.mjs,auth_browser.py,shell_browser.py}`
and `tests/foundation/test_scaffold.py`.

Executed on local `main`: frozen offline pnpm install passed;
`make PNPM=pnpm.cmd check` passed (526 Python unit tests, 21 frontend tests,
11 scaffold/schema checks, lint and types); production build passed;
`scripts/check_contract.py` passed with no drift; both browser scripts and their
Ruff checks passed. Vite emitted dependency `use client` and chunk-size warnings.
No live provider, email delivery or deployment was exercised.

Default reviewer M6: review memory/callback privacy, consent and identity races,
and accessible guarded routes. M3 should review the shared transport PATCH and
401 callback. Real sign-in requires the public frontend configuration and the
provider redirect/email settings described above; there is no remaining code
prerequisite blocker for this auth UI integration.
