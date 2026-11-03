import json
import io
import os
import tempfile
import unittest

from app import legacy_monolith as legacy


class HandlerHarness(legacy.Handler):
    """Run one request handler method without opening a network socket."""

    def __init__(self, path):
        self.path = path
        self.rfile = io.BytesIO()
        self.wfile = io.BytesIO()
        self.status = None

    def send_response(self, status, message=None):
        self.status = status

    def send_header(self, name, value):
        pass

    def end_headers(self):
        pass

    def send_error(self, status, message=None, explain=None):
        self.status = status


class CancellationAcceptanceTests(unittest.TestCase):
    """Fixed HTTP acceptance contract for the synthetic cancellation task."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.old_path = legacy.DB_PATH
        legacy.DB_PATH = os.path.join(self.temp.name, "acceptance.sqlite3")
        legacy.initialize()
        db = legacy.connect()
        db.execute("UPDATE products SET stock = 16 WHERE sku = 'MUG-BLUE'")
        cursor = db.execute(
            "INSERT INTO orders (customer, city, subtotal_cents, shipping_cents, total_cents) "
            "VALUES (?, ?, ?, ?, ?)",
            ("Example Customer", "Oakland", 2400, 575, 2975),
        )
        self.order_id = cursor.lastrowid
        db.execute("INSERT INTO order_items VALUES (?, ?, ?, ?)",
                   (self.order_id, "MUG-BLUE", 2, 1200))
        db.commit()
        db.close()

    def tearDown(self):
        legacy.DB_PATH = self.old_path
        self.temp.cleanup()

    def request_json(self, path, method="GET"):
        handler = HandlerHarness(path)
        method_handler = getattr(handler, "do_" + method, None)
        if method_handler is None:
            handler.send_error(501)
        else:
            method_handler()
        body = handler.wfile.getvalue()
        payload = json.loads(body.decode("utf-8")) if body else {}
        return handler.status, payload

    def mug_stock(self):
        return next(p["stock"] for p in legacy.all_products() if p["sku"] == "MUG-BLUE")

    def test_cancel_marks_order_and_restores_stock(self):
        status, result = self.request_json("/api/orders/%d" % self.order_id, "DELETE")
        self.assertEqual(status, 200)
        self.assertEqual(result["status"], "canceled")
        list_status, orders = self.request_json("/api/orders")
        self.assertEqual(list_status, 200)
        self.assertEqual(orders[0]["status"], "canceled")
        self.assertEqual(self.mug_stock(), 18)

    def test_cancel_unknown_order_returns_not_found(self):
        status, result = self.request_json("/api/orders/99999", "DELETE")
        self.assertEqual(status, 404)
        self.assertEqual(result["error"], "order_not_found")

    def test_repeated_cancel_does_not_restore_stock_twice(self):
        first_status, _ = self.request_json("/api/orders/%d" % self.order_id, "DELETE")
        second_status, result = self.request_json("/api/orders/%d" % self.order_id, "DELETE")
        self.assertEqual(first_status, 200)
        self.assertEqual(second_status, 409)
        self.assertEqual(result["error"], "already_canceled")
        self.assertEqual(self.mug_stock(), 18)


if __name__ == "__main__":
    unittest.main()
