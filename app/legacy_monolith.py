"""Legacy-style order API. Persistence and business rules intentionally share this module."""

from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os
import sqlite3
from urllib.error import URLError
from urllib.request import Request, urlopen


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.environ.get("STORE_DB", os.path.join(ROOT, "data", "store.sqlite3"))
SEED_PATH = os.path.join(ROOT, "data", "seed_products.json")
SHIP_URL = os.environ.get("SHIPPING_URL", "http://127.0.0.1:8091/quote")


def connect():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    return db


def initialize():
    db = connect()
    db.executescript("""
        CREATE TABLE IF NOT EXISTS products (
            sku TEXT PRIMARY KEY, name TEXT NOT NULL, price_cents INTEGER NOT NULL,
            stock INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT, customer TEXT NOT NULL,
            city TEXT NOT NULL, subtotal_cents INTEGER NOT NULL,
            shipping_cents INTEGER NOT NULL, total_cents INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'active'
        );
        CREATE TABLE IF NOT EXISTS order_items (
            order_id INTEGER NOT NULL, sku TEXT NOT NULL, qty INTEGER NOT NULL,
            unit_price_cents INTEGER NOT NULL,
            FOREIGN KEY(order_id) REFERENCES orders(id)
        );
    """)
    order_columns = {row["name"] for row in db.execute("PRAGMA table_info(orders)")}
    if "status" not in order_columns:
        db.execute("ALTER TABLE orders ADD COLUMN status TEXT NOT NULL DEFAULT 'active'")
    if db.execute("SELECT COUNT(*) FROM products").fetchone()[0] == 0:
        with open(SEED_PATH, encoding="utf-8") as seed_file:
            products = json.load(seed_file)
        db.executemany("INSERT INTO products VALUES (?, ?, ?, ?)", [
            (p["sku"], p["name"], p["price_cents"], p["stock"]) for p in products
        ])
    db.commit()
    db.close()


def all_products():
    db = connect()
    rows = db.execute("SELECT sku, name, price_cents, stock FROM products ORDER BY sku").fetchall()
    db.close()
    return [dict(row) for row in rows]


def all_orders():
    db = connect()
    rows = db.execute("SELECT id, customer, city, subtotal_cents, shipping_cents, total_cents FROM orders ORDER BY id").fetchall()
    result = []
    for row in rows:
        order = dict(row)
        order["items"] = [dict(item) for item in db.execute(
            "SELECT sku, qty, unit_price_cents FROM order_items WHERE order_id = ?", (order["id"],)
        ).fetchall()]
        state = db.execute("SELECT status FROM orders WHERE id = ?", (order["id"],)).fetchone()[0]
        if state != "active":
            order["status"] = state
        result.append(order)
    db.close()
    return result


def order_by_id(order_id):
    """Return one order using the same JSON shape as the order listing."""
    db = connect()
    try:
        row = db.execute(
            "SELECT id, customer, city, subtotal_cents, shipping_cents, total_cents, status "
            "FROM orders WHERE id = ?", (order_id,)
        ).fetchone()
        if row is None:
            return 404, {"error": "order_not_found"}
        order = dict(row)
        if order["status"] == "active":
            order.pop("status")
        order["items"] = [dict(item) for item in db.execute(
            "SELECT sku, qty, unit_price_cents FROM order_items WHERE order_id = ?", (order_id,)
        ).fetchall()]
        return 200, order
    finally:
        db.close()


def cancel_order(order_id):
    """Cancel one order atomically and restore its inventory exactly once."""
    db = connect()
    try:
        db.execute("BEGIN IMMEDIATE")
        order = db.execute("SELECT status FROM orders WHERE id = ?", (order_id,)).fetchone()
        if order is None:
            db.rollback()
            return 404, {"error": "order_not_found"}
        if order["status"] == "canceled":
            db.rollback()
            return 409, {"error": "already_canceled"}
        db.execute("UPDATE orders SET status = 'canceled' WHERE id = ?", (order_id,))
        items = db.execute("SELECT sku, qty FROM order_items WHERE order_id = ?", (order_id,)).fetchall()
        for item in items:
            db.execute("UPDATE products SET stock = stock + ? WHERE sku = ?",
                       (item["qty"], item["sku"]))
        db.commit()
        return 200, {"status": "canceled"}
    except sqlite3.Error as exc:
        db.rollback()
        return 500, {"error": "persistence_error", "detail": str(exc)}
    finally:
        db.close()


def place_order(payload, shipping_url=None):
    """Validate and persist one order; returns (status, response) for the HTTP layer."""
    if not isinstance(payload, dict):
        return 400, {"error": "invalid_request"}
    customer = payload.get("customer")
    city = payload.get("city")
    items = payload.get("items")
    if not isinstance(customer, str) or not customer.strip() or not isinstance(city, str) or not city.strip():
        return 400, {"error": "customer_and_city_required"}
    if not isinstance(items, list) or not items:
        return 400, {"error": "items_required"}

    db = connect()
    normalized = []
    subtotal = 0
    for item in items:
        if not isinstance(item, dict):
            db.close()
            return 400, {"error": "invalid_item"}
        sku = item.get("sku")
        qty = item.get("qty")
        if not isinstance(sku, str) or not isinstance(qty, int) or isinstance(qty, bool) or qty < 1:
            db.close()
            return 400, {"error": "invalid_item"}
        product = db.execute("SELECT sku, name, price_cents, stock FROM products WHERE sku = ?", (sku,)).fetchone()
        if product is None:
            db.close()
            return 404, {"error": "unknown_sku", "sku": sku}
        if product["stock"] < qty:
            db.close()
            return 409, {"error": "insufficient_stock", "sku": sku, "available": product["stock"]}
        normalized.append((sku, qty, product["price_cents"]))
        subtotal += product["price_cents"] * qty

    encoded = json.dumps({"city": city, "subtotal_cents": subtotal}).encode("utf-8")
    request = Request(shipping_url or SHIP_URL, data=encoded, headers={"Content-Type": "application/json"})
    try:
        with urlopen(request, timeout=2) as response:
            shipping = json.loads(response.read().decode("utf-8"))
    except (URLError, TimeoutError, json.JSONDecodeError) as exc:
        db.close()
        return 503, {"error": "shipping_unavailable", "detail": str(exc)}

    shipping_cost = int(shipping["shipping_cents"])
    try:
        db.execute("BEGIN")
        cur = db.execute(
            "INSERT INTO orders (customer, city, subtotal_cents, shipping_cents, total_cents) VALUES (?, ?, ?, ?, ?)",
            (customer.strip(), city.strip(), subtotal, shipping_cost, subtotal + shipping_cost),
        )
        order_id = cur.lastrowid
        for sku, qty, price in normalized:
            db.execute("UPDATE products SET stock = stock - ? WHERE sku = ?", (qty, sku))
            db.execute("INSERT INTO order_items VALUES (?, ?, ?, ?)", (order_id, sku, qty, price))
        db.commit()
    except sqlite3.Error as exc:
        db.rollback()
        db.close()
        return 500, {"error": "persistence_error", "detail": str(exc)}
    db.close()
    return 201, {"id": order_id, "customer": customer.strip(), "city": city.strip(),
                 "subtotal_cents": subtotal, "shipping_cents": shipping_cost,
                 "total_cents": subtotal + shipping_cost}


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            self._send(200, {"status": "ok", "service": "legacy-order-api"})
        elif self.path == "/api/products":
            self._send(200, all_products())
        elif self.path == "/api/orders":
            self._send(200, all_orders())
        elif self.path.startswith("/api/orders/"):
            raw_id = self.path[len("/api/orders/"):]
            if not raw_id.isascii() or not raw_id.isdigit():
                self._send(400, {"error": "invalid_order_id"})
                return
            status, payload = order_by_id(int(raw_id))
            self._send(status, payload)
        else:
            self._send(404, {"error": "not_found"})

    def do_DELETE(self):
        prefix = "/api/orders/"
        if not self.path.startswith(prefix):
            self._send(404, {"error": "not_found"})
            return
        raw_id = self.path[len(prefix):]
        if not raw_id.isascii() or not raw_id.isdigit():
            self._send(400, {"error": "invalid_order_id"})
            return
        status, payload = cancel_order(int(raw_id))
        self._send(status, payload)

    def do_POST(self):
        if self.path != "/api/orders":
            self._send(404, {"error": "not_found"})
            return
        try:
            payload = json.loads(self.rfile.read(int(self.headers.get("Content-Length", "0"))))
            status, response = place_order(payload)
            self._send(status, response)
        except (ValueError, json.JSONDecodeError) as exc:
            self._send(400, {"error": "invalid_json", "detail": str(exc)})

    def _send(self, status, payload):
        encoded = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def log_message(self, fmt, *args):
        print("legacy: " + (fmt % args))


if __name__ == "__main__":
    initialize()
    HTTPServer(("127.0.0.1", 8080), Handler).serve_forever()
