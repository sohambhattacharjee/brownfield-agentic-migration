import json
import os
import tempfile
import unittest

from http_harness import request_json

from app import legacy_monolith as legacy


class OrderDetailAcceptanceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.old_path = legacy.DB_PATH
        legacy.DB_PATH = os.path.join(self.temp.name, "detail.sqlite3")
        legacy.initialize()
        db = legacy.connect()
        cursor = db.execute(
            "INSERT INTO orders (customer, city, subtotal_cents, shipping_cents, total_cents) "
            "VALUES (?, ?, ?, ?, ?)",
            ("Detail Customer", "Oakland", 2400, 575, 2975),
        )
        self.order_id = cursor.lastrowid
        db.execute("INSERT INTO order_items VALUES (?, ?, ?, ?)",
                   (self.order_id, "MUG-BLUE", 2, 1200))
        db.commit()
        db.close()

    def tearDown(self):
        legacy.DB_PATH = self.old_path
        self.temp.cleanup()

    def test_detail_endpoint_returns_same_representation_as_order_list(self):
        list_status, orders = request_json(legacy.Handler, "GET", "/api/orders")
        detail_status, detail = request_json(legacy.Handler, "GET", "/api/orders/%d" % self.order_id)
        self.assertEqual(list_status, 200)
        self.assertEqual(detail_status, 200)
        self.assertEqual(detail, orders[0])
        self.assertEqual(detail["items"], [{"sku": "MUG-BLUE", "qty": 2, "unit_price_cents": 1200}])

    def test_detail_unknown_order_returns_not_found(self):
        status, payload = request_json(legacy.Handler, "GET", "/api/orders/99999")
        self.assertEqual(status, 404)
        self.assertEqual(payload, {"error": "order_not_found"})

    def test_detail_malformed_order_id_returns_bad_request(self):
        status, payload = request_json(legacy.Handler, "GET", "/api/orders/not-a-number")
        self.assertEqual(status, 400)
        self.assertEqual(payload, {"error": "invalid_order_id"})


if __name__ == "__main__":
    unittest.main()
