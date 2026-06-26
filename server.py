"""PridePass shop server — static files, Stripe checkout, batch print."""
import http.server
import json
import os
import re
import socket
import socketserver
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from config.pricing import (  # noqa: E402
    CARD_CENTS,
    CUSTOM_BACK_CENTS,
    SHIPPING_EXPRESS_CENTS,
    SHIPPING_STANDARD_CENTS,
    SITE_NAME,
    SITE_URL,
    SUPPORT_EMAIL,
)

PORT = int(os.environ.get("PORT", "8765"))

MIME = {
    ".html": "text/html; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".csv": "text/csv; charset=utf-8",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".pdf": "application/pdf",
    ".json": "application/json; charset=utf-8",
}


def parse_multipart(body: bytes, content_type: str) -> dict:
    match = re.search(r'boundary=(?:"([^"]+)"|([^\s;]+))', content_type)
    if not match:
        raise ValueError("Missing multipart boundary")
    boundary = match.group(1) or match.group(2)
    delim = f"--{boundary}".encode()
    parts = body.split(delim)
    fields: dict[str, list] = {}

    for part in parts:
        if not part or part in (b"--", b"--\r\n"):
            continue
        chunk = part.lstrip(b"\r\n").rstrip(b"\r\n")
        if not chunk:
            continue
        header_blob, _, content = chunk.partition(b"\r\n\r\n")
        headers = header_blob.decode("utf-8", errors="replace")
        name_match = re.search(r'name="([^"]+)"', headers)
        file_match = re.search(r'filename="([^"]*)"', headers)
        if not name_match:
            continue
        name = name_match.group(1)
        filename = file_match.group(1) if file_match else ""
        fields.setdefault(name, []).append({"filename": filename, "data": content})

    return fields


class ReuseTCPServer(socketserver.TCPServer):
    allow_reuse_address = True


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def guess_type(self, path):
        ext = Path(path).suffix.lower()
        return MIME.get(ext, super().guess_type(path))

    def do_GET(self):
        if self.path == "/api/config":
            self.handle_config()
        else:
            super().do_GET()

    def do_POST(self):
        if self.path == "/api/batch-print":
            self.handle_batch_print()
        elif self.path == "/api/create-checkout-session":
            self.handle_checkout()
        elif self.path == "/api/capture-paypal-order":
            self.handle_paypal_capture()
        elif self.path == "/api/webhook/stripe":
            self.handle_stripe_webhook()
        else:
            self.send_error(404)

    def origin(self) -> str:
        host = self.headers.get("Host", "localhost")
        scheme = "https" if os.environ.get("RENDER") else "http"
        return f"{scheme}://{host}"

    def _payment_provider(self) -> str:
        from scripts.checkout import resolve_payment_provider
        return resolve_payment_provider()

    def handle_config(self):
        provider = self._payment_provider()
        self.send_json(200, {
            "siteName": SITE_NAME,
            "siteUrl": SITE_URL,
            "supportEmail": SUPPORT_EMAIL,
            "paymentProvider": provider,
            "paypalClientId": os.environ.get("PAYPAL_CLIENT_ID", "") if provider == "paypal" else "",
            "paypalMode": os.environ.get("PAYPAL_MODE", "sandbox") if provider == "paypal" else "",
            "stripePublishableKey": os.environ.get("STRIPE_PUBLISHABLE_KEY", "") if provider == "stripe" else "",
            "pricing": {
                "card": CARD_CENTS / 100,
                "customBack": CUSTOM_BACK_CENTS / 100,
                "shippingStandard": SHIPPING_STANDARD_CENTS / 100,
                "shippingExpress": SHIPPING_EXPRESS_CENTS / 100,
                "currency": "AUD",
            },
        })

    def handle_checkout(self):
        try:
            length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(length)
            content_type = self.headers.get("Content-Type", "")
            if "multipart/form-data" not in content_type:
                raise ValueError("Expected multipart/form-data")

            form = parse_multipart(body, content_type)
            order_json = form.get("order", [{}])[0]["data"].decode("utf-8")
            order = json.loads(order_json)

            card_data = order.get("card", {})
            customer = order.get("customer", {})
            custom_back = bool(order.get("customBack"))
            shipping_method = order.get("shippingMethod", "standard")

            if not customer.get("email"):
                raise ValueError("Email is required")
            if not card_data.get("name"):
                raise ValueError("Name on card is required")

            front_bytes = None
            back_bytes = None
            front_items = form.get("front_photo", [])
            if front_items and front_items[0].get("data"):
                front_bytes = front_items[0]["data"]
            if custom_back:
                back_items = form.get("custom_back", [])
                if not back_items or not back_items[0].get("data"):
                    raise ValueError("Upload a custom back image or remove the add-on")
                back_bytes = back_items[0]["data"]

            from scripts.checkout import create_checkout_session
            result = create_checkout_session(
                card_data=card_data,
                customer=customer,
                custom_back=custom_back,
                shipping_method=shipping_method,
                front_bytes=front_bytes,
                back_bytes=back_bytes,
                origin=self.origin(),
            )
            self.send_json(200, result)
        except Exception as exc:
            self.send_json(400, {"error": str(exc)})

    def handle_paypal_capture(self):
        try:
            length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(length)
            data = json.loads(body.decode("utf-8") or "{}")
            paypal_order_id = (data.get("paypalOrderId") or data.get("token") or "").strip()
            order_id = (data.get("orderId") or data.get("order_id") or "").strip()
            if not paypal_order_id or not order_id:
                raise ValueError("paypalOrderId and orderId are required")

            order_path = ROOT / "orders" / order_id / "order.json"
            if not order_path.exists():
                raise ValueError(f"Unknown order: {order_id}")

            order_data = json.loads(order_path.read_text(encoding="utf-8"))
            if order_data.get("status") == "paid":
                self.send_json(200, {"status": "paid", "orderId": order_id, "alreadyCaptured": True})
                return

            sys.path.insert(0, str(ROOT / "scripts"))
            from paypal_checkout import capture_paypal_order
            result = capture_paypal_order(paypal_order_id, order_id)

            order_data["status"] = "paid"
            order_data["paypal_capture_id"] = result.get("captureId")
            order_data["paypal_order_id"] = paypal_order_id
            order_data["paid_at"] = datetime.now(timezone.utc).isoformat()
            order_path.write_text(json.dumps(order_data, indent=2), encoding="utf-8")

            self.send_json(200, result)
        except Exception as exc:
            self.send_json(400, {"error": str(exc)})

    def handle_stripe_webhook(self):
        try:
            secret = os.environ.get("STRIPE_WEBHOOK_SECRET", "").strip()
            if not secret:
                self.send_json(400, {"error": "Webhook secret not configured"})
                return

            import stripe
            payload = self.rfile.read(int(self.headers.get("Content-Length", "0")))
            sig = self.headers.get("Stripe-Signature", "")
            stripe.api_key = os.environ.get("STRIPE_SECRET_KEY", "")
            event = stripe.Webhook.construct_event(payload, sig, secret)

            if event["type"] == "checkout.session.completed":
                session = event["data"]["object"]
                order_id = session.get("metadata", {}).get("order_id")
                if order_id:
                    order_path = ROOT / "orders" / order_id / "order.json"
                    if order_path.exists():
                        data = json.loads(order_path.read_text(encoding="utf-8"))
                        data["status"] = "paid"
                        data["stripe_payment_status"] = session.get("payment_status")
                        order_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

            self.send_json(200, {"received": True})
        except Exception as exc:
            self.send_json(400, {"error": str(exc)})

    def handle_batch_print(self):
        try:
            length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(length)
            content_type = self.headers.get("Content-Type", "")
            if "multipart/form-data" not in content_type:
                raise ValueError("Expected multipart/form-data")

            form = parse_multipart(body, content_type)
            sheets = form.get("spreadsheet", [])
            if not sheets or not sheets[0].get("filename"):
                raise ValueError("No spreadsheet uploaded")

            include_vals = form.get("include_back", [{"data": b"true"}])
            include_back = include_vals[0]["data"].decode().strip().lower() != "false"

            with tempfile.TemporaryDirectory() as tmp:
                tmp_path = Path(tmp)
                sheet_item = sheets[0]
                sheet_path = tmp_path / Path(sheet_item["filename"]).name
                sheet_path.write_bytes(sheet_item["data"])

                photos_dir = tmp_path / "photos"
                photos_dir.mkdir(exist_ok=True)
                for item in form.get("photos", []):
                    if item.get("filename"):
                        dest = photos_dir / Path(item["filename"]).name
                        dest.write_bytes(item["data"])

                out_pdf = tmp_path / "batch-output.pdf"
                cmd = [
                    sys.executable,
                    str(ROOT / "scripts" / "batch_print.py"),
                    str(sheet_path),
                    "--photos-dir", str(photos_dir),
                    "--output", str(out_pdf),
                ]
                if not include_back:
                    cmd.append("--no-back")

                result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(ROOT))
                if result.returncode != 0:
                    msg = (result.stderr or result.stdout or "Batch print failed").strip()
                    self.send_json(500, {"error": msg})
                    return

                data = out_pdf.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "application/pdf")
                self.send_header("Content-Disposition", 'attachment; filename="pridepass-batch.pdf"')
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
        except Exception as exc:
            self.send_json(400, {"error": str(exc)})

    def send_json(self, code, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def find_free_port(start: int = PORT, attempts: int = 10) -> int:
    for port in range(start, start + attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("", port))
                return port
            except OSError:
                continue
    return start


if __name__ == "__main__":
    port = find_free_port() if not os.environ.get("PORT") else PORT
    with ReuseTCPServer(("", port), Handler) as httpd:
        print(f"PridePass → http://localhost:{port}")
        print("Checkout API → POST /api/create-checkout-session")
        if port != PORT and not os.environ.get("PORT"):
            print(f"(Port {PORT} was busy — using {port})")
        httpd.serve_forever()