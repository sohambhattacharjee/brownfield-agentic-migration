# Brownfield Agentic Migration Study

An independently created synthetic application for a reproducible study of staged onboarding to an agentic software factory. It contains a tightly coupled order-management monolith and a newer shipping-quote service integrated over HTTP.

## Scope and boundary

All names, requirements, rules, sample records, and code in this repository are fictional and created for this study. Do not add employer code, documents, prompts, configurations, operational data, or proprietary workflows. This separation does not determine intellectual-property ownership; review applicable employment and invention-assignment obligations before publication.

## Run locally

Requires Python 3.9 or later and uses only the Python standard library.

```sh
./scripts/run-local.sh
```

The monolith listens on `http://127.0.0.1:8080`; the shipping service listens on `http://127.0.0.1:8091`. The SQLite database is created at `data/store.sqlite3` and seeded on first run.

Reset the local synthetic data to its seeded state before a fresh evidence run:

```sh
python3 scripts/reset-local-data.py
```

Create an order:

```sh
curl -sS -X POST http://127.0.0.1:8080/api/orders \
  -H 'Content-Type: application/json' \
  -d '{"customer":"Example Customer","city":"Oakland","items":[{"sku":"MUG-BLUE","qty":2}]}'
```

List products and orders at `/api/products` and `/api/orders`. Both services expose `/health`.

## Reproduce the baseline

```sh
python3 -m unittest discover -s tests -p 'test_characterization.py' -v
```

The baseline snapshot and evidence protocol are in [`evidence/baseline/`](evidence/baseline/). Do not overwrite that snapshot after factory onboarding begins; append later observations under versioned stage directories.

The cancellation task has a separate fixed acceptance suite at `tests/test_cancellation_acceptance.py`. On the prepared pre-implementation revision, those three checks are expected to fail because cancellation is not implemented; the characterization suite above should continue to pass. Use the full suite as the factory's verification command.

## Repository map

- `app/legacy_monolith.py` — legacy order workflow, persistence, validation, and shipping-service client in one module.
- `app/shipping_service.py` — newer integrated service with a small JSON HTTP contract.
- `data/seed_products.json` — fictional initial product and stock records.
- `tests/` — characterization checks for current observable behavior.
- `evidence/` — baseline and later experimental records.
- `manuscript/outline.md` — rough structure and evidence placeholders only; manuscript prose is intentionally left to the author.

The independent factory prototype is maintained separately in the private companion repository `agentic-software-factory-study`. Its CLI requires this repository's `.research-scope.json` marker and writes proposals only to a disposable workspace.
