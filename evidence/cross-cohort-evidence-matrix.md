# Cross-cohort evidence matrix

| Cohort | Task | Proposals | Acceptance | Regression | All checks passed | Saved reviews |
|---|---|---:|---:|---:|---:|---:|
| `cohort-2026-11-03-key-verified` | Order cancellation | 25 | 75/75 | 125/125 | 25/25 | 5 (5 approve) |
| `cohort-order-detail-2026-11-04-followup` | Order detail retrieval | 15 | 45/45 | 165/165 | 15/15 | 3 (3 approve) |
| `cohort-express-delivery-2026-11-03-stage` | Express delivery across services | 15 | 75/75 | 210/210 | 15/15 | 3 (3 approve) |
| `cohort-shipping-resilience-2026-11-04-stage` | Shipping quote resilience across services | 15 | 105/105 | 285/285 | 15/15 | 3 (3 approve) |

## Interpretation limits

- The four tasks are separate cohorts on different pinned application revisions; do not pool them as one treatment comparison.
- Corrected fixed suites reached a pass ceiling in every cohort. These are exploratory practical case studies, not evidence that one profile is more effective.
- Reviews came from the proposal model, so they are second-pass checks rather than independent review.
- Protocol amendments and superseded scores are preserved in the run archive.
- Per-profile time, token, file-count, and patch-size summaries are in the machine-readable JSON.
- One earlier interrupted review request from the first cohort has no saved response; whether it reached the provider is unknown.
- A Keychain read failed before a resilience-cohort provider request and was resumed after the user approved access; no response is missing from the 15 frozen proposal slots.
- No generated proposal was transferred into application source.

Raw per-run records, including the fourth cohort, are in [`run-archive/`](run-archive/); the archive manifest contains SHA-256 digests.
