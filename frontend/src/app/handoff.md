# MS-004 handoff — M2 to M6

Implemented on `feat/ms-004-ui-base`, based on merged MS-002/MS-003 at `80db101`.
The user approved the necessary HTML/package/lockfile handoff and instructed merge
and push. MS-002 generated DTOs and enums were verified before implementation.

## Delivered behavior

- R12.01 / US-12.01: `app/App.tsx` supplies accessible account, consent,
  profile/goal, optional-document and discovery navigation, plus saved,
  application and settings route shells. Documents are explicitly optional.
- R12.03 / US-12.03: `components/StateView.tsx`, `StatusLabel.tsx` and `lib/api.ts`
  expose empty, loading, partial, unknown, stale, unavailable, cancelled and error
  states. Structured errors show field messages and request references. TanStack
  Query owns capabilities data. Finite timeouts, explicit retries and abort signals
  stop browser requests without invoking durable server cancellation.
- R12.04 / US-12.04: `app/App.tsx` and `styles/` supply semantic landmarks,
  current-link labels, skip navigation, route-heading focus, browser history,
  responsive layout, visible focus, text labels and reduced-motion support.
- `components/PlainText.tsx` escapes untrusted provider text. Typed synthetic
  transports and state fixtures live only under tests and are absent from the
  production bundle. The live entry never falls back to synthetic account data.
- `index.html`, `package.json`, `pnpm-lock.yaml`, `app/main.tsx` and
  `app/vite.config.ts` wire the real shell. Development `/api` traffic proxies to
  the existing API at `http://127.0.0.1:8000`; production uses same-origin HTTPS.

## Dependency and contract impact

Exact runtime dependencies: React Router 7.18.4 and TanStack Query 5.104.1 (MIT).
Router 7 preserves the repository's Node >=22.12 contract; Router 8.4 requires
Node >=22.22. Vite was patched from 7.3.1 to 7.3.6 (MIT), removing its high-severity
advisories. No migrations, DTO/enum changes, generated drift or public endpoints.
No paid providers were called.

The existing transitive esbuild 0.27.7 has one low-severity Windows `servedir`
advisory. This application does not invoke esbuild's serving API; no incompatible
transitive override was forced. `pnpm audit --audit-level high` passes.

## Commands and actual outcomes

Commands from the repository root:

| Command                                                                                                 | Outcome                                                      |
| ------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------ |
| `pnpm.cmd --dir frontend install --frozen-lockfile`                                                     | Passed                                                       |
| `pnpm.cmd --dir frontend lint`                                                                          | Passed Prettier and strict app/domain/test TypeScript checks |
| `pnpm.cmd --dir frontend test`                                                                          | 11 passed, including 9 API boundary tests                    |
| `pnpm.cmd --dir frontend build`                                                                         | Production build passed                                      |
| `python -m uv run --frozen --offline ruff check backend tests frontend/tests/shell_browser.py`          | Passed                                                       |
| `python -m uv run --frozen --offline ruff format --check backend tests frontend/tests/shell_browser.py` | Passed                                                       |
| `python -m uv run --frozen --offline mypy`                                                              | Passed, 14 source files                                      |
| `python -m uv run --frozen --offline pytest -q`                                                         | 345 passed                                                   |
| `python -m uv run --frozen --offline python scripts/export_openapi.py --check`                          | Passed; generated contracts unchanged                        |
| `pnpm.cmd --dir frontend audit --audit-level high`                                                      | Passed; one low-severity esbuild finding remains             |
| `pnpm.cmd --dir frontend dev --port 5173 --strictPort`                                                  | Real repository server started                               |
| `python frontend/tests/shell_browser.py http://127.0.0.1:5173`                                          | Passed in installed Edge against the real repository         |

Browser checks cover keyboard skip, route focus/current links/history, error and
retry rendering, browser abort without a server mutation, unknown/empty/partial/
stale states, escaped HTML injection text, and desktop/mobile horizontal overflow.
Desktop 1440px and mobile 390px screenshots were inspected. Browser tooling is
locally installed Playwright 1.63.0 with Edge; no browser package was added to the
repository. Vite reports ignored library `use client` directives while bundling;
the production build succeeds. No synthetic transport or fixture identifier was
found in the production bundle.

GNU Make is unavailable here; its available lint/type/unit/contract commands were
executed directly. The repository scripts now include the new source and API
checks; Node 22 uses the explicit `--experimental-strip-types` flag for API tests.

## Boundaries and review

The MS-004 implementation gates pass in the actual repository. There is no pending
wiring approval. Authentication, consent persistence and feature data APIs belong
to their later tasks; their route shells honestly report absence until those
owners deliver them. No production success placeholders replace missing services.

M6 review has not been performed. Reviewer focus: keyboard/history focus,
state-label distinctions, browser abort versus durable cancellation, safe error
and model rendering, and separation of eligibility from availability/fit/readiness.
