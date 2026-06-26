"""Render print-ready files for a paid order and email them to the shop owner."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
sys.path.insert(0, str(ROOT))

from batch_print import save_pdf  # noqa: E402
from card_render import render_card_back, render_card_front  # noqa: E402
from order_email import send_order_email, smtp_configured  # noqa: E402

ORDERS_DIR = ROOT / "orders"


def order_dir(order_id: str) -> Path:
    return ORDERS_DIR / order_id


def load_order(order_id: str) -> tuple[Path, dict]:
    path = order_dir(order_id) / "order.json"
    if not path.exists():
        raise FileNotFoundError(f"Order not found: {order_id}")
    return path, json.loads(path.read_text(encoding="utf-8-sig"))


def save_order(order_path: Path, order: dict) -> None:
    order_path.write_text(json.dumps(order, indent=2), encoding="utf-8")


def _find_file(folder: Path, names: tuple[str, ...]) -> Path | None:
    for name in names:
        candidate = folder / name
        if candidate.exists():
            return candidate
    return None


def render_custom_back(path: Path, width: int, height: int) -> Image.Image:
    img = Image.open(path).convert("RGB")
    img_aspect = img.width / img.height
    card_aspect = width / height
    if img_aspect >= card_aspect:
        draw_h = height
        draw_w = int(height * img_aspect)
        draw_x = (width - draw_w) // 2
        draw_y = 0
    else:
        draw_w = width
        draw_h = int(width / img_aspect)
        draw_x = 0
        draw_y = (height - draw_h) // 2

    canvas = Image.new("RGB", (width, height), (0, 0, 0))
    resized = img.resize((draw_w, draw_h), Image.Resampling.LANCZOS)
    canvas.paste(resized, (draw_x, draw_y))
    return canvas


def render_print_assets(order_id: str) -> list[Path]:
    folder = order_dir(order_id)
    _, order = load_order(order_id)
    card = order.get("card", {})

    photo = _find_file(folder, ("front-photo.jpg", "front-photo.jpeg", "front-photo.png"))
    front = render_card_front(
        identity_id=card.get("identityId", "pride"),
        name=str(card.get("name", "")),
        member_number=str(card.get("memberNumber") or card.get("member_number") or ""),
        community_since=str(card.get("communitySince") or card.get("memberSince") or ""),
        pronouns=str(card.get("pronouns", "")),
        photo_path=photo,
        hue=float(card.get("hue") or 0),
        saturation=float(card.get("saturation") or 100),
    )

    front_path = folder / "print-front.png"
    front.save(front_path, "PNG", optimize=True)

    pages = [front]
    attachments = [front_path]

    custom_back = _find_file(folder, ("custom-back.jpg", "custom-back.jpeg", "custom-back.png"))
    if order.get("custom_back") and custom_back:
        back = render_custom_back(custom_back, front.width, front.height)
    else:
        back = render_card_back(front.width, front.height)

    back_path = folder / "print-back.png"
    back.save(back_path, "PNG", optimize=True)
    pages.append(back)
    attachments.append(back_path)

    pdf_path = folder / "print-ready.pdf"
    save_pdf(pages, pdf_path)
    attachments.append(pdf_path)

    return attachments


def fulfill_and_notify(order_id: str) -> dict:
    order_path, order = load_order(order_id)

    if order.get("fulfillment_email_sent_at"):
        return {"orderId": order_id, "skipped": True, "reason": "already_sent"}

    attachments = render_print_assets(order_id)

    if not smtp_configured():
        order["print_files_ready_at"] = datetime.now(timezone.utc).isoformat()
        order["fulfillment_error"] = (
            "Print files generated but email not sent — configure SMTP_USER and SMTP_PASSWORD."
        )
        save_order(order_path, order)
        return {
            "orderId": order_id,
            "attachments": [str(p) for p in attachments],
            "emailSent": False,
            "error": order["fulfillment_error"],
        }

    send_order_email(order, attachments)

    order["print_files_ready_at"] = datetime.now(timezone.utc).isoformat()
    order["fulfillment_email_sent_at"] = datetime.now(timezone.utc).isoformat()
    order.pop("fulfillment_error", None)
    save_order(order_path, order)

    return {
        "orderId": order_id,
        "attachments": [str(p) for p in attachments],
        "emailSent": True,
        "recipients": order.get("notify_recipients"),
    }


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Render and email print-ready files for a paid order")
    parser.add_argument("order_id", help="Order ID, e.g. PP-20260626-AB12CD34")
    parser.add_argument("--render-only", action="store_true", help="Generate files without sending email")
    args = parser.parse_args()

    if args.render_only:
        paths = render_print_assets(args.order_id)
        print(f"Created {len(paths)} file(s) for {args.order_id}")
        for path in paths:
            print(f"  {path}")
        return

    result = fulfill_and_notify(args.order_id)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()