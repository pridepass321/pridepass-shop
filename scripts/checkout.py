"""Stripe Checkout session creation for PridePass orders."""
from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
import sys
sys.path.insert(0, str(ROOT))

from config.pricing import (  # noqa: E402
    CARD_CENTS,
    CURRENCY,
    CUSTOM_BACK_CENTS,
    SHIPPING_EXPRESS_CENTS,
    SHIPPING_STANDARD_CENTS,
    SITE_NAME,
    SITE_URL,
)

try:
    import stripe
except ImportError:
    stripe = None

ORDERS_DIR = ROOT / "orders"


def _cents_to_display(cents: int) -> str:
    return f"${cents / 100:.2f}"


def build_line_items(custom_back: bool, shipping_method: str) -> list[dict]:
    items = [
        {
            "price_data": {
                "currency": CURRENCY,
                "product_data": {"name": "PridePass Community Card"},
                "unit_amount": CARD_CENTS,
            },
            "quantity": 1,
        }
    ]
    if custom_back:
        items.append({
            "price_data": {
                "currency": CURRENCY,
                "product_data": {"name": "Custom Card Back — your upload"},
                "unit_amount": CUSTOM_BACK_CENTS,
            },
            "quantity": 1,
        })
    else:
        ship_cents = SHIPPING_EXPRESS_CENTS if shipping_method == "express" else SHIPPING_STANDARD_CENTS
        ship_label = "Express Shipping" if shipping_method == "express" else "Standard Shipping"
        items.append({
            "price_data": {
                "currency": CURRENCY,
                "product_data": {"name": ship_label},
                "unit_amount": ship_cents,
            },
            "quantity": 1,
        })
    return items


def save_order_payload(order_id: str, payload: dict, front_bytes: bytes | None, back_bytes: bytes | None) -> Path:
    order_dir = ORDERS_DIR / order_id
    order_dir.mkdir(parents=True, exist_ok=True)
    (order_dir / "order.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    if front_bytes:
        (order_dir / "front-photo.jpg").write_bytes(front_bytes)
    if back_bytes:
        (order_dir / "custom-back.jpg").write_bytes(back_bytes)
    return order_dir


def resolve_payment_provider() -> str:
    explicit = os.environ.get("PAYMENT_PROVIDER", "").strip().lower()
    if explicit in ("paypal", "stripe"):
        return explicit
    if os.environ.get("PAYPAL_CLIENT_ID", "").strip() and os.environ.get("PAYPAL_CLIENT_SECRET", "").strip():
        return "paypal"
    if os.environ.get("STRIPE_SECRET_KEY", "").strip():
        return "stripe"
    return ""


def create_checkout_session(
    card_data: dict,
    customer: dict,
    custom_back: bool,
    shipping_method: str,
    front_bytes: bytes | None = None,
    back_bytes: bytes | None = None,
    origin: str | None = None,
) -> dict:
    provider = resolve_payment_provider()
    if provider == "paypal":
        from scripts.paypal_checkout import create_checkout_session as create_paypal_checkout_session
        return create_paypal_checkout_session(
            card_data=card_data,
            customer=customer,
            custom_back=custom_back,
            shipping_method=shipping_method,
            front_bytes=front_bytes,
            back_bytes=back_bytes,
            origin=origin,
        )

    secret = os.environ.get("STRIPE_SECRET_KEY", "").strip()
    if not secret:
        raise RuntimeError(
            "No payment provider configured. Set PAYPAL_CLIENT_ID/PAYPAL_CLIENT_SECRET or STRIPE_SECRET_KEY."
        )
    if stripe is None:
        raise RuntimeError("stripe package not installed. Run: pip install stripe")

    stripe.api_key = secret
    base_url = (origin or SITE_URL).rstrip("/")
    order_id = f"PP-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"

    payload = {
        "order_id": order_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "pending_payment",
        "custom_back": custom_back,
        "shipping_method": "free" if custom_back else shipping_method,
        "card": card_data,
        "customer": customer,
    }
    save_order_payload(order_id, payload, front_bytes, back_bytes)

    identity_label = card_data.get("identity_label", card_data.get("identityId", ""))
    session = stripe.checkout.Session.create(
        mode="payment",
        payment_method_types=["card"],
        line_items=build_line_items(custom_back, shipping_method),
        customer_email=customer.get("email"),
        success_url=f"{base_url}/success.html?session_id={{CHECKOUT_SESSION_ID}}&order_id={order_id}",
        cancel_url=f"{base_url}/cancel.html?order_id={order_id}",
        metadata={
            "order_id": order_id,
            "identity": identity_label,
            "custom_back": "yes" if custom_back else "no",
            "shipping": payload["shipping_method"],
        },
        shipping_address_collection={"allowed_countries": ["AU", "NZ", "US", "GB", "CA"]},
    )

    payload["stripe_session_id"] = session.id
    save_order_payload(order_id, payload, front_bytes, back_bytes)

    return {"sessionId": session.id, "url": session.url, "orderId": order_id}