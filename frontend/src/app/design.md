# MS-004 design reference lock

Designing a private opportunity workspace for students and early-career applicants.
The primary action is progressing from confirmed facts to evidence-backed decisions.
This sprint builds route shells and state conventions, without inventing connected
profiles, discoveries, authentication or completed workflows.

Live Refero tools were unavailable. The direct-build target uses the bundled craft
references and the existing screen/state contract in design.md section 2.

Primary reference: anti-ai-slop-ui `references/visual_directions.md`, Research Archive.
Preserve its paper/ink palette, restrained accent, source-oriented hierarchy and
readable evidence/status labels. Borrow persistent sidebar navigation only from its
Enterprise Control Plane direction; keep applicant-facing language and modest density.

| Decision                                        | Source and role                                                        | Implementation                                                               |
| ----------------------------------------------- | ---------------------------------------------------------------------- | ---------------------------------------------------------------------------- |
| Off-white canvas, dark ink, green action accent | Research Archive palette; Refero color guide sections 0–2              | Semantic CSS tokens; semantic error red remains separate                     |
| One readable UI font, five type sizes           | Refero typography guide sections 0–3                                   | Segoe UI for platform familiarity; mono only for request references          |
| Persistent navigation and setup sequence        | design.md screen contract; Enterprise Control Plane navigation pattern | Main workflow links plus account/consent/profile/document/goal onboarding    |
| Visible state panels, no invented statistics    | R12.03; Research Archive evidence-first hierarchy                      | Empty/loading/error/unknown/partial/stale states have text and next actions  |
| Skip link and route-heading focus               | R12.04; Refero craft-details sections 1, 6, 7                          | Semantic landmarks, visible focus, browser-history navigation                |
| Plain provider text                             | agent.md security/UI rules                                             | Escaped React text, no raw HTML or Markdown injection                        |
| Minimal motion and no photography               | Functional shell; Refero motion/craft guidance                         | Short control transitions; reduced-motion support; no decorative asset slots |

Reject decorative dashboards, invented opportunity counts, gradients, oversized
marketing heroes, pill-shaped controls and color-only eligibility labels. Public
capabilities may show an unavailable response until their owning API task is merged.
Mock transports must be explicitly selected for tests/development and excluded from
the production entrypoint.
