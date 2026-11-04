import json
import os
import sqlite3
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from urllib.request import Request, urlopen
from urllib.error import HTTPError

from app import legacy_monolith as legacy


class CancellationHardeningTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.old_path = legacy.DB_PATH
        legacy.DB_PATH = os.path.join(self.temp.name, "test.sqlite3")
        legacy.initialize()
        db = legacy.connect()
        db.execute("UPDATE products SET stock = 16 WHERE sku = 'MUG-BLUE'")
        cur = db.execute(
            "INSERT INTO orders (customer, city, subtotal_cents, shipping_cents, total_cents) "
            "VALUES (?, ?, ?, ?, ?)",
            ("Example Customer", "Oakland", 2400, 575, 2975),
        )
        self.order_id = cur.lastrowid
        db.execute("INSERT INTO order_items VALUES (?, ?, ?, ?)",
                   (self.order_id, "MUG-BLUE", 2, 1200))
        db.commit()
        db.close()

    def tearDown(self):
        legacy.DB_PATH = self.old_path
        self.temp.cleanup()

    def mug_stock(self):
        return next(p["stock"] for p in legacy.all_products() if p["sku"] == "MUG-BLUE")

    def test_initialize_migrates_legacy_orders_and_is_idempotent(self):
        legacy.DB_PATH = os.path.join(self.temp.name, "legacy.sqlite3")
        db = sqlite3.connect(legacy.DB_PATH)
        db.executescript("""
            CREATE TABLE products (sku TEXT PRIMARY KEY, name TEXT NOT NULL, price_cents INTEGER NOT NULL, stock INTEGER NOT NULL);
            CREATE TABLE orders (id INTEGER PRIMARY KEY AUTOINCREMENT, customer TEXT NOT NULL, city TEXT NOT NULL, subtotal_cents INTEGER NOT NULL, shipping_cents INTEGER NOT NULL, total_cents INTEGER NOT NULL);
            CREATE TABLE order_items (order_id INTEGER NOT NULL, sku TEXT NOT NULL, qty INTEGER NOT NULL, unit_price_cents INTEGER NOT NULL, FOREIGN KEY(order_id) REFERENCES orders(id));
            INSERT INTO products VALUES ('MUG-BLUE', 'Blue Mug', 1200, 16);
            INSERT INTO orders VALUES (41, 'Legacy Customer', 'Oakland', 2400, 575, 2975);
            INSERT INTO order_items VALUES (41, 'MUG-BLUE', 2, 1200);
        """)
        db.commit()
        db.close()

        legacy.initialize()
        legacy.initialize()
        order = legacy.all_orders()[0]
        self.assertEqual(order["id"], 41)
        self.assertEqual(order["items"][0]["qty"], 2)
        self.assertNotIn("status", order)
        db = legacy.connect()
        columns = {row["name"] for row in db.execute("PRAGMA table_info(orders)")}
        status = db.execute("SELECT status FROM orders WHERE id = 41").fetchone()[0]
        db.close()
        self.assertIn("status", columns)
        self.assertEqual(status, "active")

    def test_concurrent_cancellation_restores_stock_once(self):
        barrier = threading.Barrier(3)
        results = []
        result_lock = threading.Lock()

        def cancel():
            barrier.wait()
            result = legacy.cancel_order(self.order_id)
            with result_lock:
                results.append(result)

        threads = [threading.Thread(target=cancel) for _ in range(2)]
        for thread in threads:
            thread.start()
        barrier.wait()
        for thread in threads:
            thread.join(timeout=6)
        self.assertTrue(all(not thread.is_alive() for thread in threads))
        self.assertCountEqual([status for status, _ in results], [200, 409])
        self.assertEqual(self.mug_stock(), 18)

    def test_http_server_routes_delete_and_returns_canceled_order_status(self):
        server = ThreadingHTTPServer(("127.0.0.1", 0), legacy.Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base = "http://127.0.0.1:%d" % server.server_address[1]
        try:
            request = Request(base + "/api/orders/%d" % self.order_id, method="DELETE")
            with urlopen(request, timeout=3) as response:
                self.assertEqual(response.status, 200)
                deleted = json.loads(response.read().decode("utf-8"))
            self.assertEqual(deleted["status"], "canceled")

            with urlopen(base + "/api/orders", timeout=3) as response:
                orders = json.loads(response.read().decode("utf-8"))
            self.assertEqual(orders[0]["status"], "canceled")
            self.assertEqual(self.mug_stock(), 18)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=3)


if __name__ == "__main__":
    unittest.main()
