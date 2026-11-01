"""Restore the ignored local SQLite database to the public synthetic seed state."""

import json
import os
import sqlite3

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.environ.get("STORE_DB", os.path.join(ROOT, "data", "store.sqlite3"))
SEED_PATH = os.path.join(ROOT, "data", "seed_products.json")

with open(SEED_PATH, encoding="utf-8") as seed_file:
    products = json.load(seed_file)

os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
db = sqlite3.connect(DB_PATH)
db.execute("PRAGMA foreign_keys = ON")
db.execute("DELETE FROM order_items")
db.execute("DELETE FROM orders")
for product in products:
    db.execute("UPDATE products SET stock = ? WHERE sku = ?", (product["stock"], product["sku"]))
db.execute("DELETE FROM sqlite_sequence WHERE name = 'orders'")
db.commit()
db.close()
print("Local synthetic orders and stock restored to seed state.")
