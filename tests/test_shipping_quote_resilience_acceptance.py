"""Fixed acceptance tests for malformed downstream shipping quotes."""
import os
import tempfile
import unittest
from unittest.mock import patch

from app import legacy_monolith as legacy


class ShippingQuoteResilienceAcceptanceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.old_path = legacy.DB_PATH
        legacy.DB_PATH = os.path.join(self.temp.name, "shipping-resilience.sqlite3")
        legacy.initialize()

    def tearDown(self):
        legacy.DB_PATH = self.old_path
        self.temp.cleanup()

    def response(self, body):
        class Response:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self):
                return body
        return Response()

    def submit_with_quote(self, body):
        payload = {
            "customer": "Example Customer",
            "city": "Oakland",
            "items": [{"sku": "MUG-BLUE", "qty": 2}],
        }
        stock_before = next(p["stock"] for p in legacy.all_products()
                            if p["sku"] == "MUG-BLUE")
        with patch("app.legacy_monolith.urlopen", return_value=self.response(body)):
            status, result = legacy.place_order(payload, "http://shipping.test/quote")
        self.assertEqual(status, 503)
        self.assertEqual(result.get("error"), "shipping_unavailable")
        self.assertEqual(legacy.all_orders(), [])
        stock_after = next(p["stock"] for p in legacy.all_products()
                           if p["sku"] == "MUG-BLUE")
        self.assertEqual(stock_after, stock_before)

    def test_malformed_json_does_not_create_order_or_change_stock(self):
        self.submit_with_quote(b'{"shipping_cents":')

    def test_non_object_json_does_not_create_order_or_change_stock(self):
        self.submit_with_quote(b'[]')

    def test_missing_shipping_cost_does_not_create_order_or_change_stock(self):
        self.submit_with_quote(b'{}')

    def test_string_shipping_cost_does_not_create_order_or_change_stock(self):
        self.submit_with_quote(b'{"shipping_cents":"575"}')

    def test_fractional_shipping_cost_does_not_create_order_or_change_stock(self):
        self.submit_with_quote(b'{"shipping_cents":575.0}')

    def test_boolean_shipping_cost_does_not_create_order_or_change_stock(self):
        self.submit_with_quote(b'{"shipping_cents":true}')

    def test_negative_shipping_cost_does_not_create_order_or_change_stock(self):
        self.submit_with_quote(b'{"shipping_cents":-1}')


if __name__ == "__main__":
    unittest.main()
