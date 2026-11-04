import json
import os
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.request import urlopen

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
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), legacy.Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = "http://127.0.0.1:%d" % self.server.server_address[1]

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=3)
        legacy.DB_PATH = self.old_path
        self.temp.cleanup()

    def test_detail_endpoint_returns_same_representation_as_order_list(self):
        with urlopen(self.base + "/api/orders", timeout=3) as response:
            orders = json.loads(response.read().decode("utf-8"))
        with urlopen(self.base + "/api/orders/%d" % self.order_id, timeout=3) as response:
            detail = json.loads(response.read().decode("utf-8"))
        self.assertEqual(detail, orders[0])
        self.assertEqual(detail["items"], [{"sku": "MUG-BLUE", "qty": 2, "unit_price_cents": 1200}])

    def test_detail_unknown_order_returns_not_found(self):
        with self.assertRaises(HTTPError) as caught:
            urlopen(self.base + "/api/orders/99999", timeout=3)
        self.assertEqual(caught.exception.code, 404)
        self.assertEqual(json.loads(caught.exception.read().decode("utf-8")),
                         {"error": "order_not_found"})

    def test_detail_malformed_order_id_returns_bad_request(self):
        with self.assertRaises(HTTPError) as caught:
            urlopen(self.base + "/api/orders/not-a-number", timeout=3)
        self.assertEqual(caught.exception.code, 400)
        self.assertEqual(json.loads(caught.exception.read().decode("utf-8")),
                         {"error": "invalid_order_id"})


if __name__ == "__main__":
    unittest.main()
