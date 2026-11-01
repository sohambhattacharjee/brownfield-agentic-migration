# Baseline evidence record

This directory is the immutable pre-factory baseline snapshot. Add measurements without replacing the source snapshot; later experimental results belong in `evidence/stages/<stage-id>/`.

## Environment

- Python: record the exact interpreter version used for each run.
- Dependencies: Python standard library only (`requirements.txt` is intentionally empty).
- Storage: SQLite, initialized from `data/seed_products.json`.
- Services: legacy order API on `127.0.0.1:8080`; shipping quote API on `127.0.0.1:8091`.

## Baseline procedure

1. Record commit, date/time, OS, Python version, and operator.
2. Start both services using `scripts/run-local.sh`.
3. Capture `/health` from both services and the initial `/api/products` response.
4. Submit a fixed successful order and capture response, resulting stock, and order record.
5. Submit fixed invalid-SKU, insufficient-stock, and shipping-unavailable cases; record status, response, and whether state changed.
6. Run `python3 -m unittest discover -s tests -v`; record command, exit code, duration, and failures.
7. Record manual interventions and anomalies. Keep raw outputs in a dated, stage-specific subfolder.

## Fixed task set for later comparison

The exact tasks and acceptance criteria must be frozen before factory-assisted runs. Candidate task themes: add order cancellation with stock restoration; correct a shipping boundary rule; expose order-item details consistently. Do not silently repair baseline defects before the initial baseline is recorded.

## Current snapshot

- Application state: initial synthetic implementation, before agentic-factory onboarding.
- Local validation run: 5 characterization checks passed on Python 3.9.6, Darwin 25.6.0 (arm64); command `python3 -m unittest discover -s tests -v`; reported duration 0.010 seconds. The suite includes a synthetic shipping-outage case.
- Service smoke capture: recorded in [`run-2026-10-31.json`](run-2026-10-31.json).
- Fixed task runs: not yet performed.
- Measurements: pending first local execution.
- Factory stage: not onboarded; factory URL and onboarding constraints are pending from the author.
