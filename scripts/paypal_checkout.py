"""PayPal Checkout (Orders API v2) for PridePass orders."""
from __future__ import annotations

import base64
import json
import os
import urllib.error
import urllib.request
from datetime import datetime, timezone
from typing import Any

from scripts.checkout import save_order_payload
from config.pricing import (
    CARD_CENTS,
    CUSTOM_BACK_CENTS,
    SHIPPING_EXPRESS_CENTS,
    SHIPPING_STANDARD_CENTS,
    SITE_NAME,
)


def _cents_to_value(cents: int) -> str:
    return f"{cents / 100:.2f}"


def _paypal_base() -> str:
    mode = os.environ.get("PAYPAL_MODE", "sandbox").strip().lower()
    if mode == "live":
        return "https://api-m.paypal.com"
    return "https://api-m.sandbox.paypal.com"


def _credentials() -> tuple[str, str]:
    client_id = os.environ.get("PAYPAL_CLIENT_ID", "").strip()
    secret = os.environ.get("PAYPAL_CLIENT_SECRET", "").strip()
    if not client_id or not secret:
        raise RuntimeError("PAYPAL_CLIENT_ID and PAYPAL_CLIENT_SECRET are not configured.")
    return client_id, secret


def _request(method: str, path: str, body: dict | None = None, access_token: str | None = None) -> dict:
    url = f"{_paypal_base()}{path}"
    headers = {"Accept": "application/json"}
    data = None
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    if access_token:
        headers["Authorization"] = f"Bearer {access_token}"

    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"PayPal API error ({exc.code}): {detail}") from exc


def get_access_token() -> str:
    client_id, secret = _credentials()
    auth = base64.b64encode(f"{client_id}:{secret}".encode()).decode()
    req = urllib.request.Request(
        f"{_paypal_base()}/v1/oauth2/token",
        data=b"grant_type=client_credentials",
        headers={
            "Authorization": f"Basic {auth}",
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"PayPal auth failed ({exc.code}): {detail}") from exc
    token = payload.get("access_token")
    if not token:
        raise RuntimeError("PayPal auth returned no access token.")
    return token


def build_paypal_items(custom_back: bool, shipping_method: str) -> tuple[list[dict], int]:
    items: list[dict] = [
        {
            "name": "PridePass Community Card",
            "quantity": "1",
            "unit_amount": {"currency_code": "AUD", "value": _cents_to_value(CARD_CENTS)},
            "category": "PHYSICAL_GOODS",
        }
    ]
    total_cents = CARD_CENTS

    if custom_back:
        items.append({
            "name": "Custom Card Back",
            "quantity": "1",
            "unit_amount": {"currency_code": "AUD", "value": _cents_to_value(CUSTOM_BACK_CENTS)},
            "category": "PHYSICAL_GOODS",
        })
        total_cents += CUSTOM_BACK_CENTS
    else:
        ship_cents = SHIPPING_EXPRESS_CENTS if shipping_method == "express" else SHIPPING_STANDARD_CENTS
        ship_label = "Express Shipping" if shipping_method == "express" else "Standard Shipping"
        items.append({
            "name": ship_label,
            "quantity": "1",
            "unit_amount": {"currency_code": "AUD", "value": _cents_to_value(ship_cents)},
            "category": "PHYSICAL_GOODS",
        })
        total_cents += ship_cents

    return items, total_cents


def create_paypal_order(
    order_id: str,
    card_data: dict,
    customer: dict,
    custom_back: bool,
    shipping_method: str,
    base_url: str,
) -> dict[str, Any]:
    token = get_access_token()
    items, total_cents = build_paypal_items(custom_back, shipping_method)
    identity_label = card_data.get("identity_label", card_data.get("identityId", ""))

    body = {
        "intent": "CAPTURE",
        "purchase_units": [
            {
                "reference_id": order_id,
                "description": f"{SITE_NAME} — {identity_label}",
                "custom_id": order_id,
                "amount": {
                    "currency_code": "AUD",
                    "value": _cents_to_value(total_cents),
                    "breakdown": {
                        "item_total": {
                            "currency_code": "AUD",
                            "value": _cents_to_value(total_cents),
                        }
                    },
                },
                "items": items,
            }
        ],
        "payer": {
            "email_address": customer.get("email", ""),
        },
        "application_context": {
            "brand_name": SITE_NAME,
            "landing_page": "NO_PREFERENCE",
            "user_action": "PAY_NOW",
            "shipping_preference": "GET_FROM_FILE",
            "return_url": f"{base_url}/success.html?order_id={order_id}",
            "cancel_url": f"{base_url}/cancel.html?order_id={order_id}",
        },
    }

    order = _request("POST", "/v2/checkout/orders", body, token)
    approve_url = next(
        (link["href"] for link in order.get("links", []) if link.get("rel") == "approve"),
        None,
    )
    if not approve_url:
        raise RuntimeError("PayPal did not return an approval URL.")

    return {
        "id": order.get("id"),
        "url": approve_url,
        "status": order.get("status"),
    }


def capture_paypal_order(paypal_order_id: str, order_id: str) -> dict[str, Any]:
    token = get_access_token()
    result = _request("POST", f"/v2/checkout/orders/{paypal_order_id}/capture", {}, token)
    status = result.get("status", "")
    if status != "COMPLETED":
        raise RuntimeError(f"PayPal capture incomplete (status: {status or 'unknown'}).")

    capture_id = None
    for unit in result.get("purchase_units", []):
        payments = unit.get("payments", {})
        for capture in payments.get("captures", []):
            capture_id = capture.get("id")
            break

    return {
        "status": status,
        "captureId": capture_id,
        "paypalOrderId": paypal_order_id,
        "orderId": order_id,
    }


def create_checkout_session(
    card_data: dict,
    customer: dict,
    custom_back: bool,
    shipping_method: str,
    front_bytes: bytes | None = None,
    back_bytes: bytes | None = None,
    origin: str | None = None,
) -> dict:
    import uuid
    from config.pricing import SITE_URL

    base_url = (origin or SITE_URL).rstrip("/")
    order_id = f"PP-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"

    payload = {
        "order_id": order_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "pending_payment",
        "payment_provider": "paypal",
        "custom_back": custom_back,
        "shipping_method": "free" if custom_back else shipping_method,
        "card": card_data,
        "customer": customer,
    }
    save_order_payload(order_id, payload, front_bytes, back_bytes)

    paypal_order = create_paypal_order(
        order_id=order_id,
        card_data=card_data,
        customer=customer,
        custom_back=custom_back,
        shipping_method=shipping_method,
        base_url=base_url,
    )

    payload["paypal_order_id"] = paypal_order["id"]
    save_order_payload(order_id, payload, front_bytes, back_bytes)

    return {
        "url": paypal_order["url"],
        "orderId": order_id,
        "provider": "paypal",
        "paypalOrderId": paypal_order["id"],
    }