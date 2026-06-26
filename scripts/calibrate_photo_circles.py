"""Detect emblem photo circle center on each card PNG and write data/photo_layouts.json."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from PIL import Image

from identities_data import CARD_LAYOUT

ROOT = Path(__file__).resolve().parent.parent
CARDS_DIR = ROOT / "assets" / "cards"
OUT_PATH = ROOT / "data" / "photo_layouts.json"


def detect_emblem_photo_circle(path: Path) -> dict[str, float] | None:
    img = Image.open(path).convert("RGBA")
    w, h = img.size
    arr = np.array(img, dtype=np.float32)
    r, g, b = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]
    lum = 0.299 * r + 0.587 * g + 0.114 * b
    x0, x1 = int(w * 0.55), int(w * 0.96)
    y0, y1 = int(h * 0.15), int(h * 0.75)
    sub_lum = lum[y0:y1, x0:x1]
    sub_r, sub_g, sub_b = r[y0:y1, x0:x1], g[y0:y1, x0:x1], b[y0:y1, x0:x1]
    inner = (sub_lum < 40) | ((sub_b > 90) & (sub_b > sub_r + 25) & (sub_b > sub_g + 15))
    if inner.sum() < 200:
        inner = (sub_lum > 15) & (sub_lum < 80)
    if inner.sum() < 100:
        return None
    yy, xx = np.where(inner)
    cx = round((xx.mean() + x0) / w, 4)
    cy = round((yy.mean() + y0) / h, 4)
    dx = xx - (cx * w - x0)
    dy = yy - (cy * h - y0)
    dist = np.sqrt(dx * dx + dy * dy)
    r_frac = round(float(np.percentile(dist, 88) * 0.46 / h), 4)
    return {"cx": cx, "cy": cy, "r": r_frac}


def main() -> None:
    layouts: dict[str, dict[str, float]] = {}
    for path in sorted(CARDS_DIR.glob("*.png")):
        detected = detect_emblem_photo_circle(path)
        if detected:
            layouts[path.stem] = detected

    OUT_PATH.parent.mkdir(exist_ok=True)
    OUT_PATH.write_text(json.dumps(layouts, indent=2), encoding="utf-8")
    print(f"Wrote {OUT_PATH} ({len(layouts)} cards)")
    print(f"Default CARD_LAYOUT.photo = {CARD_LAYOUT['photo']}")
    if "pride" in layouts:
        print(f"pride = {layouts['pride']}")


if __name__ == "__main__":
    main()