# MS-004 implementation handoff — M2 to M6

Branch: `feat/ms-004-ui-base`, based on merged MS-002/MS-003 at `80db101`.
MS-002 prerequisite verified: generated `components`, domain status enums, Problem,
Capabilities and their envelopes exist. No shared schema was changed.

## Behavior and paths

- R12.01 / US-12.01: `app/App.tsx` provides the account, consent, profile/goal,
  optional-document and discovery route sequence. It also provides saved,
  application and settings shells. Account/profile operations remain with their
  downstream owners; the shell reports absence honestly.
- R12.03 / US-12.03: `components/StateView.tsx`, `StatusLabel.tsx` and `lib/api.ts`
  provide loading, empty, partial, unknown, stale, unavailable, cancelled and
  structured-error conventions. TanStack Query owns fetched capabilities;
  requests have a finite timeout, no automatic retry loop, explicit retry and
  browser cancellation. No server cancellation endpoint is invoked.
- R12.04 / US-12.04: `app/App.tsx` and `styles/` provide semantic navigation,
  current-link labels, a skip link, route-heading focus, history, visible focus,
  responsive layout, text state labels and reduced-motion support.
- `components/PlainText.tsx` escapes provider text. No raw HTML/Markdown renderer
  exists. `tests/mockTransport.ts` uses generated DTOs and the real transport
  interface; the production entrypoint never imports it.
- `app/main.tsx` defaults to real same-origin fetch; `app/vite.config.ts` proxies
  development `/api` requests to the existing local API on port 8000.

## Actual verification

Commands from the repository root unless otherwise noted:

| Command                                                                                                                                                                               | Actual outcome                                                                                                                                                               |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `python -m uv run --frozen --offline ruff check backend tests`                                                                                                                        | Passed                                                                                                                                                                       |
| `python -m uv run --frozen --offline mypy`                                                                                                                                            | Passed: 14 source files                                                                                                                                                      |
| `python -m uv run --frozen --offline pytest -q`                                                                                                                                       | 345 passed                                                                                                                                                                   |
| `pnpm.cmd --dir frontend lint`                                                                                                                                                        | Passed existing gates                                                                                                                                                        |
| `pnpm.cmd --dir frontend typecheck`                                                                                                                                                   | Passed existing scaffold/domain checks                                                                                                                                       |
| `pnpm.cmd --dir frontend test`                                                                                                                                                        | 2 passed                                                                                                                                                                     |
| `node --test tests/api.test.mjs` (frontend cwd)                                                                                                                                       | 9 passed                                                                                                                                                                     |
| `pnpm.cmd exec prettier --check src/app src/components src/lib/api.ts src/styles tests/api.test.mjs tests/mockTransport.ts tests/state-fixture.tsx tests/fixture.html` (frontend cwd) | Passed                                                                                                                                                                       |
| `python frontend/tests/shell_browser.py http://127.0.0.1:5173`                                                                                                                        | Passed in installed Edge: keyboard skip, focus/history, error/retry, cancellation without server mutation, all state panels, escaped injection text, desktop/mobile overflow |

Full app verification used an ignored isolated copy at `.pytest_cache/ms004-web`
with React Router 8.4.0 and TanStack Query 5.104.1 installed (both MIT). This avoids
modifying the dependency files while the requested scope handoff is pending.
Commands in that copy:

```powershell
node node_modules/typescript/bin/tsc --noEmit --strict --noUnusedLocals --noUnusedParameters --target ES2022 --module ESNext --moduleResolution bundler --jsx react-jsx --lib ES2022,DOM,DOM.Iterable src/app/main.tsx src/app/vite.config.ts tests/mockTransport.ts tests/state-fixture.tsx
node node_modules/vite/bin/vite.js build --config src/app/vite.config.ts
node node_modules/vite/bin/vite.js --config src/app/vite.config.ts --port 5173 --strictPort
```

Strict app checks and the production bundle passed. Vite emitted benign ignored
`use client` directives from the two libraries. Desktop 1440px and mobile 390px
screenshots were inspected. Browser tooling was installed locally:
`python -m pip install playwright` (1.63.0); no browser package was added to the
repository or paid provider called. Browser tests use installed Edge.

## Pending wiring handoff and completion gate

Repository `pnpm dev/build` cannot yet start this shell: the explicit MS-004 write
scope omits `frontend/index.html`, `frontend/package.json` and
`frontend/pnpm-lock.yaml`. A scope handoff was requested before those changes;
no answer has been received. The completion gate remains unverified in the actual
repository until that wiring is approved, installed, locked and checked.

Concrete proposed changes:

- Add the root HTML entry with `lang="en"`, viewport metadata, `#root`, and
  `/src/app/main.tsx` as its module entry.
- Add exact runtime dependencies `react-router@8.4.0` and
  `@tanstack/react-query@5.104.1`, regenerate the pnpm lock, and install frozen.
- Point `dev` and `build` at `--config src/app/vite.config.ts`; include the app,
  typed mock and state fixture in strict typechecks; add `api.test.mjs` to unit
  checks; include scoped source in Prettier checks.

`npm audit --json` in the isolated copy found the existing Vite 7.3.1 high-severity
development-server advisories and a low-severity esbuild advisory. It recommends
Vite 7.3.6. No automatic upgrade or unrelated dependency change was made; the
foundation owner should review this patch upgrade alongside the wiring handoff.

No migration, public API, DTO, enum or production feature-flag change. Existing
downstream account and capabilities APIs are not supplied by this unit; production
shows unavailable/error states when those services are absent.

M6 reviewer focus: keyboard/history focus behavior, state labels, request abort
versus durable cancellation, safe error/model rendering, and separation of
eligibility from availability/fit/readiness. M6 review has not been performed.

GNU Make is unavailable in this environment; the available Makefile gate commands
were executed directly as listed above. The new browser helper also passed Ruff
lint/format checks. Existing repository scripts do not yet include all new source
checks; that change belongs to the pending wiring handoff. The proposed API-test
command should use `node --experimental-strip-types --test` for Node 22.12 support.
