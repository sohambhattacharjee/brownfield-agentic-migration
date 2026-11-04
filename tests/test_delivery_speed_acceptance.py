import json
import os
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from app import legacy_monolith as legacy
from app import shipping_service
from http_harness import request_json


class DeliverySpeedAcceptanceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.old_path = legacy.DB_PATH
        legacy.DB_PATH = os.path.join(self.temp.name, "delivery.sqlite3")
        legacy.initialize()

    def tearDown(self):
        legacy.DB_PATH = self.old_path
        self.temp.cleanup()

    def response(self, quote):
        class Response:
            def __enter__(self):
                return self
            def __exit__(self, *args):
                return False
            def read(self):
                return json.dumps(quote).encode("utf-8")
        return Response()

    def mug_stock(self):
        return next(p["stock"] for p in legacy.all_products() if p["sku"] == "MUG-BLUE")

    def test_standard_speed_is_default_and_preserves_existing_totals(self):
        payload = {"customer": "Example Customer", "city": "Oakland",
                   "items": [{"sku": "MUG-BLUE", "qty": 2}]}
        sent = {}
        def quote_request(request, timeout=2):
            sent.update(json.loads(request.data.decode("utf-8")))
            return self.response({"shipping_cents": 575})
        with patch("app.legacy_monolith.urlopen", side_effect=quote_request):
            status, result = legacy.place_order(payload, "http://shipping.test/quote")
        self.assertEqual(status, 201)
        self.assertEqual(result["total_cents"], 2975)
        self.assertEqual(sent.get("delivery_speed"), "standard")
        self.assertNotIn("delivery_speed", result)
        self.assertNotIn("delivery_speed", legacy.all_orders()[0])

    def test_express_speed_is_forwarded_persisted_and_surcharged(self):
        payload = {"customer": "Example Customer", "city": "Oakland",
                   "delivery_speed": "express",
                   "items": [{"sku": "MUG-BLUE", "qty": 2}]}
        sent = {}
        def quote_request(request, timeout=2):
            sent.update(json.loads(request.data.decode("utf-8")))
            speed = sent.get("delivery_speed", "standard")
            return self.response(shipping_service.quote(sent["city"], sent["subtotal_cents"], speed))
        with patch("app.legacy_monolith.urlopen", side_effect=quote_request):
            status, result = legacy.place_order(payload, "http://shipping.test/quote")
        self.assertEqual(status, 201)
        self.assertEqual(sent.get("delivery_speed"), "express")
        self.assertEqual(result["shipping_cents"], 1375)
        self.assertEqual(result["delivery_speed"], "express")
        self.assertEqual(legacy.all_orders()[0]["delivery_speed"], "express")

    def test_unsupported_speed_is_rejected_before_shipping_or_mutation(self):
        payload = {"customer": "Example Customer", "city": "Oakland",
                   "delivery_speed": "rocket",
                   "items": [{"sku": "MUG-BLUE", "qty": 2}]}
        with patch("app.legacy_monolith.urlopen") as call:
            status, result = legacy.place_order(payload, "http://shipping.test/quote")
        self.assertEqual(status, 400)
        self.assertEqual(result["error"], "invalid_delivery_speed")
        call.assert_not_called()
        self.assertEqual(legacy.all_orders(), [])
        self.assertEqual(self.mug_stock(), 18)

    def test_shipping_http_contract_keeps_standard_default_and_supports_express(self):
        standard_status, standard = request_json(
            shipping_service.Handler, "POST", "/quote",
            {"city": "Oakland", "subtotal_cents": 2400})
        express_status, express = request_json(
            shipping_service.Handler, "POST", "/quote",
            {"city": "Oakland", "subtotal_cents": 2400, "delivery_speed": "express"})
        invalid_status, invalid = request_json(
            shipping_service.Handler, "POST", "/quote",
            {"city": "Oakland", "subtotal_cents": 2400, "delivery_speed": "rocket"})
        self.assertEqual(standard_status, 200)
        self.assertEqual(standard, {"city": "Oakland", "zone": 1, "shipping_cents": 575})
        self.assertEqual(express_status, 200)
        self.assertEqual(express["shipping_cents"], 1375)
        self.assertEqual(express["delivery_speed"], "express")
        self.assertEqual(invalid_status, 400)
        self.assertEqual(invalid["error"], "invalid_request")

    def test_legacy_schema_migration_defaults_existing_orders_to_standard(self):
        legacy.DB_PATH = os.path.join(self.temp.name, "legacy.sqlite3")
        db = sqlite3.connect(legacy.DB_PATH)
        db.executescript("""
            CREATE TABLE products (sku TEXT PRIMARY KEY, name TEXT NOT NULL, price_cents INTEGER NOT NULL, stock INTEGER NOT NULL);
            CREATE TABLE orders (id INTEGER PRIMARY KEY AUTOINCREMENT, customer TEXT NOT NULL, city TEXT NOT NULL, subtotal_cents INTEGER NOT NULL, shipping_cents INTEGER NOT NULL, total_cents INTEGER NOT NULL, status TEXT NOT NULL DEFAULT 'active');
            CREATE TABLE order_items (order_id INTEGER NOT NULL, sku TEXT NOT NULL, qty INTEGER NOT NULL, unit_price_cents INTEGER NOT NULL);
            INSERT INTO products VALUES ('MUG-BLUE', 'Blue Mug', 1200, 16);
            INSERT INTO orders VALUES (9, 'Legacy Customer', 'Oakland', 2400, 575, 2975, 'active');
            INSERT INTO order_items VALUES (9, 'MUG-BLUE', 2, 1200);
        """)
        db.commit()
        db.close()
        legacy.initialize()
        db = legacy.connect()
        columns = {row["name"] for row in db.execute("PRAGMA table_info(orders)")}
        speed = db.execute("SELECT delivery_speed FROM orders WHERE id = 9").fetchone()[0]
        db.close()
        self.assertIn("delivery_speed", columns)
        self.assertEqual(speed, "standard")


if __name__ == "__main__":
    unittest.main()
