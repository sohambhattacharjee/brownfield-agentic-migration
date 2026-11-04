# Task: validate shipping-service quote responses before order persistence

The order endpoint calls the integrated shipping service and trusts its JSON response. Harden this boundary in the existing brownfield application.

Acceptance criteria:

1. Treat a response as valid only when it is a JSON object containing `shipping_cents` whose value is a non-negative integer. Booleans, fractional values, numeric strings, missing fields, and non-object JSON are invalid.
2. If the shipping response is malformed or violates that contract, return HTTP-layer status 503 with an error value of `shipping_unavailable`.
3. On an invalid shipping response, create no order and leave product stock unchanged.
4. Preserve current order creation behavior for valid standard and express shipping quotes, including totals and delivery-speed behavior.
5. Change only `app/legacy_monolith.py`; do not edit tests, seed data, service behavior, or other files.

The target includes a fixed acceptance suite at `tests/test_shipping_quote_resilience_acceptance.py`. Use it together with the complete existing test suite.

Return a JSON proposal containing complete file contents only for files that must change. Do not execute commands or modify the target directly.
