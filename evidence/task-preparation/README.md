# Cancellation task evidence

- [`add-cancellation-2026-11-03.json`](add-cancellation-2026-11-03.json) records the pre-implementation task baseline.
- [`preregistration-2026-11-03.json`](preregistration-2026-11-03.json) freezes the exploratory pilot conditions and scoring before model-backed runs.
- [`api-authentication-check-2026-11-03.json`](api-authentication-check-2026-11-03.json) records the first API attempt, which was rejected with HTTP 401 before returning output; it is not a scored result.
- [`api-credential-check-2026-11-03.json`](api-credential-check-2026-11-03.json) records the user-requested diagnostic retry, which returned `invalid_api_key`; it is not a scored result and contains no key fragment.
- [`replacement-key-check-2026-11-03.json`](replacement-key-check-2026-11-03.json) records the follow-up after key replacement; it returned the same `invalid_api_key` result and produced no model output.
- [`api-key-diagnostic-2026-11-03.json`](api-key-diagnostic-2026-11-03.json) records a later successful connection check; it produced a response but is excluded from the scored cohort.

## Shipping quote resilience task

- [`shipping-quote-resilience-task.md`](shipping-quote-resilience-task.md) is the frozen task text; the normalized task SHA-256 appears in the preregistration and per-run records.
- [`baseline-shipping-quote-resilience-2026-11-04.json`](baseline-shipping-quote-resilience-2026-11-04.json) records the 1/7 acceptance baseline and 19 passing regression checks.
- [`preregistration-shipping-quote-resilience-2026-11-04.json`](preregistration-shipping-quote-resilience-2026-11-04.json) records the target revision, profile schedule, model settings, run count, and scoring rules before the cohort.
- [`../scored-cohort-shipping-resilience-2026-11-04.json`](../scored-cohort-shipping-resilience-2026-11-04.json) records all 15 proposals, test outcomes, review results, and descriptive per-profile measures.
