"""Small, newer HTTP service integrated with the legacy order monolith."""

from http.server import BaseHTTPRequestHandler, HTTPServer
import json


def quote(city, subtotal_cents, delivery_speed="standard"):
    """Return a deterministic fictional shipping quote."""
    if not isinstance(city, str) or not city.strip():
        raise ValueError("city is required")
    if delivery_speed not in ("standard", "express"):
        raise ValueError("delivery_speed is invalid")
    city_key = city.strip().lower()
    zones = {"oakland": 1, "berkeley": 1, "san jose": 2, "sacramento": 3}
    zone = zones.get(city_key, 4)
    base = {1: 450, 2: 700, 3: 950, 4: 1200}[zone]
    handling = 0 if subtotal_cents >= 5000 else 125
    shipping_cents = base + handling + (800 if delivery_speed == "express" else 0)
    result = {"city": city.strip(), "zone": zone, "shipping_cents": shipping_cents}
    if delivery_speed != "standard":
        result["delivery_speed"] = delivery_speed
    return result


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            self._send(200, {"status": "ok", "service": "shipping"})
        else:
            self._send(404, {"error": "not_found"})

    def do_POST(self):
        if self.path != "/quote":
            self._send(404, {"error": "not_found"})
            return
        try:
            body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", "0"))))
            result = quote(body.get("city"), int(body.get("subtotal_cents", 0)),
                           body.get("delivery_speed", "standard"))
            self._send(200, result)
        except (ValueError, TypeError, json.JSONDecodeError) as exc:
            self._send(400, {"error": "invalid_request", "detail": str(exc)})

    def _send(self, status, payload):
        encoded = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def log_message(self, fmt, *args):
        print("shipping: " + (fmt % args))


if __name__ == "__main__":
    HTTPServer(("127.0.0.1", 8091), Handler).serve_forever()
