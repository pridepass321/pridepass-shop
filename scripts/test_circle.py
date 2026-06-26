"""Quick visual test for photo circle sizing."""
import sys
import tempfile
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import identities_data
from card_render import render_card_front

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "output"

photo = Image.new("RGB", (400, 400), (255, 100, 150))
tmp = Path(tempfile.gettempdir()) / "lgbt_test_photo.png"
photo.save(tmp)

candidates = [
    ("old", {"cx": 0.772, "cy": 0.368, "r": 0.126}),
    ("new", {"cx": 0.788, "cy": 0.408, "r": 0.188}),
    ("alt", {"cx": 0.785, "cy": 0.400, "r": 0.175}),
]

for label, layout in candidates:
    identities_data.CARD_LAYOUT["photo"] = layout
    img = render_card_front(
        "pangender",
        name="TEST NAME",
        community_since="2026",
        photo_path=tmp,
    )
    path = OUT / f"circle-test-{label}.png"
    img.save(path)
    print(f"saved {path}")