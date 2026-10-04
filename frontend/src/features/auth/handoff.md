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

Mount `AuthBoundary` beneath the shell QueryClientProvider. Account/confirmation/
recovery routes use `AccountScreen`; consent uses `ConsentScreen`.
Wrap processing routes in `ProcessingGuard`. Account/preferences/deletion routes
remain available without processing consent. `useProcessingAccess` exposes
confirmed consent and account state, never token contents. Generated Account and
PatchMe are consumed without a parallel DTO. Old private queries are cancelled
and removed on identity transitions. Backend authorization remains authoritative.

Next owners can mount the profile editor in MS-018 and progress views in MS-031
when their other prerequisites are met. M6 should review callback sanitation,
SDK/session expiry, stale consent and the guarded-route browser checks.
