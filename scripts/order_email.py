"""Send order fulfillment emails with print-ready attachments."""
from __future__ import annotations

import mimetypes
import os
import smtplib
import ssl
from email.message import EmailMessage
from pathlib import Path
from typing import Iterable

from config.pricing import SITE_NAME, SUPPORT_EMAIL

ROOT = Path(__file__).resolve().parent.parent


def _smtp_settings() -> dict | None:
    user = os.environ.get("SMTP_USER", "").strip()
    password = os.environ.get("SMTP_PASSWORD", "").strip()
    if not user or not password:
        return None
    return {
        "host": os.environ.get("SMTP_HOST", "smtp.gmail.com").strip(),
        "port": int(os.environ.get("SMTP_PORT", "587")),
        "user": user,
        "password": password,
        "from_addr": os.environ.get("SMTP_FROM", user).strip(),
        "use_tls": os.environ.get("SMTP_USE_TLS", "true").strip().lower() != "false",
    }


def notify_recipients() -> list[str]:
    raw = os.environ.get("ORDER_NOTIFY_EMAIL", SUPPORT_EMAIL).strip()
    return [addr.strip() for addr in raw.split(",") if addr.strip()]


def smtp_configured() -> bool:
    return _smtp_settings() is not None and bool(notify_recipients())


def build_order_email(order: dict, attachments: Iterable[Path]) -> EmailMessage:
    order_id = order.get("order_id", "unknown")
    card = order.get("card", {})
    customer = order.get("customer", {})
    identity = card.get("identity_label") or card.get("identityId", "")
    customer_name = customer.get("name") or card.get("name", "")
    customer_email = customer.get("email", "")

    msg = EmailMessage()
    msg["Subject"] = f"{SITE_NAME} print order — {order_id}"
    msg["From"] = _smtp_settings()["from_addr"]  # type: ignore[index]
    msg["To"] = ", ".join(notify_recipients())
    if customer_email:
        msg["Reply-To"] = customer_email

    lines = [
        f"New paid order ready to print: {order_id}",
        "",
        f"Customer: {customer_name}",
        f"Email: {customer_email}",
        f"Design: {identity}",
        f"Name on card: {card.get('name', '')}",
        f"Pronouns: {card.get('pronouns', '') or '—'}",
        f"Member/Community since: {card.get('memberSince') or card.get('communitySince') or '—'}",
        f"Hue: {card.get('hue', 0)}°",
        f"Saturation: {card.get('saturation', 100)}%",
        f"Custom back: {'yes' if order.get('custom_back') else 'no'}",
        f"Shipping: {order.get('shipping_method', 'standard')}",
        "",
        "Attached: CR80 print-ready PDF and PNG(s) for Evolis Primacy 2.",
        "",
        f"— {SITE_NAME} automated fulfillment",
    ]
    msg.set_content("\n".join(lines))

    for path in attachments:
        path = Path(path)
        if not path.exists():
            continue
        mime, _ = mimetypes.guess_type(path.name)
        maintype, subtype = (mime or "application/octet-stream").split("/", 1)
        msg.add_attachment(
            path.read_bytes(),
            maintype=maintype,
            subtype=subtype,
            filename=path.name,
        )

    return msg


def send_order_email(order: dict, attachments: Iterable[Path]) -> None:
    settings = _smtp_settings()
    if not settings:
        raise RuntimeError(
            "Email not configured. Set SMTP_USER and SMTP_PASSWORD "
            "(Gmail app password works: https://support.google.com/accounts/answer/185833)."
        )

    recipients = notify_recipients()
    if not recipients:
        raise RuntimeError("No ORDER_NOTIFY_EMAIL recipients configured.")

    message = build_order_email(order, attachments)

    if settings["use_tls"]:
        context = ssl.create_default_context()
        with smtplib.SMTP(settings["host"], settings["port"], timeout=30) as smtp:
            smtp.ehlo()
            smtp.starttls(context=context)
            smtp.ehlo()
            smtp.login(settings["user"], settings["password"])
            smtp.send_message(message)
    else:
        with smtplib.SMTP(settings["host"], settings["port"], timeout=30) as smtp:
            smtp.login(settings["user"], settings["password"])
            smtp.send_message(message)