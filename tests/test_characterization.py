import json
import os
import tempfile
import unittest
from urllib.error import URLError
from unittest.mock import patch

from app import legacy_monolith as legacy
from app import shipping_service


class CharacterizationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.old_path = legacy.DB_PATH
        legacy.DB_PATH = os.path.join(self.temp.name, "test.sqlite3")
        legacy.initialize()

    def tearDown(self):
        legacy.DB_PATH = self.old_path
        self.temp.cleanup()

    def test_seeded_products_are_stable(self):
        products = legacy.all_products()
        self.assertEqual([p["sku"] for p in products], ["BAG-CANVAS", "MUG-BLUE", "NOTE-GRID"])
        self.assertEqual(next(p["stock"] for p in products if p["sku"] == "MUG-BLUE"), 18)

    def test_order_persists_total_items_and_stock_decrement(self):
        class Response:
            def __enter__(self):
                return self
            def __exit__(self, *args):
                return False
            def read(self):
                return b'{"shipping_cents":450}'

        payload = {"customer": "Example Customer", "city": "Oakland",
                   "items": [{"sku": "MUG-BLUE", "qty": 2}]}
        with patch("app.legacy_monolith.urlopen", return_value=Response()):
            status, result = legacy.place_order(payload, "http://shipping.test/quote")
        self.assertEqual(status, 201)
        self.assertEqual(result["total_cents"], 2850)
        self.assertEqual(legacy.all_orders()[0]["items"][0]["qty"], 2)
        self.assertEqual(next(p["stock"] for p in legacy.all_products() if p["sku"] == "MUG-BLUE"), 16)

    def test_insufficient_stock_does_not_call_shipping_service(self):
        payload = {"customer": "Example Customer", "city": "Oakland",
                   "items": [{"sku": "MUG-BLUE", "qty": 99}]}
        with patch("app.legacy_monolith.urlopen") as call:
            status, result = legacy.place_order(payload)
        self.assertEqual(status, 409)
        self.assertEqual(result["error"], "insufficient_stock")
        call.assert_not_called()

    def test_shipping_unavailable_does_not_create_order_or_change_stock(self):
        payload = {"customer": "Example Customer", "city": "Oakland",
                   "items": [{"sku": "MUG-BLUE", "qty": 2}]}
        with patch("app.legacy_monolith.urlopen", side_effect=URLError("synthetic outage")):
            status, result = legacy.place_order(payload, "http://shipping.test/quote")
        self.assertEqual(status, 503)
        self.assertEqual(result["error"], "shipping_unavailable")
        self.assertEqual(legacy.all_orders(), [])
        self.assertEqual(next(p["stock"] for p in legacy.all_products() if p["sku"] == "MUG-BLUE"), 18)

    def test_shipping_zone_quote_is_deterministic(self):
        self.assertEqual(shipping_service.quote("Oakland", 1200),
                         {"city": "Oakland", "zone": 1, "shipping_cents": 575})


if __name__ == "__main__":
    unittest.main()
