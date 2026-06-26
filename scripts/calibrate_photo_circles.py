"""Detect photo circle center on each card PNG and verify CARD_LAYOUT.photo."""
from __future__ import annotations

from collections import deque
from pathlib import Path

import numpy as np
from PIL import Image

from identities_data import CARD_LAYOUT

ROOT = Path(__file__).resolve().parent.parent
CARDS_DIR = ROOT / "assets" / "cards"


def _largest_blob(mask: np.ndarray) -> list[tuple[int, int]] | None:
    h, w = mask.shape
    visited = np.zeros_like(mask, dtype=bool)
    best: list[tuple[int, int]] | None = None
    best_size = 0
    for y in range(h):
        for x in range(w):
            if not mask[y, x] or visited[y, x]:
                continue
            q: deque[tuple[int, int]] = deque([(x, y)])
            visited[y, x] = True
            pts: list[tuple[int, int]] = []
            while q:
                cx, cy = q.popleft()
                pts.append((cx, cy))
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = cx + dx, cy + dy
                    if 0 <= nx < w and 0 <= ny < h and mask[ny, nx] and not visited[ny, nx]:
                        visited[ny, nx] = True
                        q.append((nx, ny))
            if len(pts) > best_size:
                best_size = len(pts)
                best = pts
    return best


def detect_photo_circle(path: Path) -> tuple[float, float, float] | None:
    img = Image.open(path).convert("RGB")
    w, h = img.size
    arr = np.array(img, dtype=np.float32)
    lum = 0.299 * arr[:, :, 0] + 0.587 * arr[:, :, 1] + 0.114 * arr[:, :, 2]
    dark = lum < 45
    x0, x1 = int(w * 0.02), int(w * 0.28)
    y0, y1 = int(h * 0.38), int(h * 0.72)
    pts = _largest_blob(dark[y0:y1, x0:x1])
    if not pts or len(pts) < 800:
        return None
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    cx = (min(xs) + max(xs)) / 2 + x0
    cy = (min(ys) + max(ys)) / 2 + y0
    rw = (max(xs) - min(xs)) / 2
    rh = (max(ys) - min(ys)) / 2
    r_px = min(rw, rh) * 0.92
    return round(cx / w, 4), round(cy / h, 4), round(r_px / h, 4)


def main() -> None:
    layouts: dict[str, tuple[float, float, float] | None] = {}
    for path in sorted(CARDS_DIR.glob("*.png")):
        layouts[path.stem] = detect_photo_circle(path)

    unique = {v for v in layouts.values() if v}
    print(f"Detected {len(layouts)} cards, {len(unique)} unique layout(s)")
    for layout in sorted(unique):
        ids = [k for k, v in layouts.items() if v == layout]
        print(f"  {layout} -> {len(ids)} cards (e.g. {ids[0]})")

    current = (
        CARD_LAYOUT["photo"]["cx"],
        CARD_LAYOUT["photo"]["cy"],
        CARD_LAYOUT["photo"]["r"],
    )
    print(f"CARD_LAYOUT.photo = cx={current[0]}, cy={current[1]}, r={current[2]}")


if __name__ == "__main__":
    main()