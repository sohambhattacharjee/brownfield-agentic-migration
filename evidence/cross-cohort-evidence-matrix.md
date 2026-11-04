# Cross-cohort evidence matrix

| Cohort | Task | Proposals | Acceptance | Regression | All checks passed | Saved reviews |
|---|---|---:|---:|---:|---:|---:|
| `cohort-2026-11-03-key-verified` | Order cancellation | 25 | 75/75 | 125/125 | 25/25 | 5 (5 approve) |
| `cohort-order-detail-2026-11-04-followup` | Order detail retrieval | 15 | 45/45 | 165/165 | 15/15 | 3 (3 approve) |
| `cohort-express-delivery-2026-11-03-stage` | Express delivery across services | 15 | 75/75 | 210/210 | 15/15 | 3 (3 approve) |

## Interpretation limits

- The tasks are separate cohorts on different pinned application revisions; do not pool them as one treatment comparison.
- All corrected fixed suites reached a pass ceiling. Report this as an exploratory practical case study, not evidence that one profile is more effective.
- Reviews came from the same model as proposal generation, so they are second-pass checks rather than independent reviews.
- Protocol amendments and superseded scores are retained in the cohort JSON and raw archive.
- Per-profile timing, token, file-count, and patch-size summaries are in the machine-readable JSON.
- An earlier interrupted review request has no saved response; whether it reached the provider is unknown.

Raw per-run files are preserved in [`run-archive/`](run-archive/); the archive manifest contains SHA-256 digests.
