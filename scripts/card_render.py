"""Server-side card compositing — mirrors browser renderer for batch PDF output."""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from identities_data import CARD_LAYOUT, resolve_identity

ROOT = Path(__file__).resolve().parent.parent
CARDS_DIR = ROOT / "assets" / "cards"
FONT_CANDIDATES = [
    Path(r"C:\Windows\Fonts\segoeuib.ttf"),
    Path(r"C:\Windows\Fonts\arialbd.ttf"),
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
]


def _load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for path in FONT_CANDIDATES:
        if path.exists():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def _resolve_layout(width: int, height: int) -> dict:
    layout = CARD_LAYOUT
    return {
        "photo": {
            "cx": layout["photo"]["cx"] * width,
            "cy": layout["photo"]["cy"] * height,
            "r": layout["photo"]["r"] * height,
        },
        "name": {
            "x": layout["name"]["x"] * width,
            "y": layout["name"]["y"] * height,
            "maxWidth": layout["name"]["maxWidth"] * width,
            "fontSize": layout["name"]["fontSize"] * height,
        },
        "field2": {
            "x": layout["field2"]["x"] * width,
            "y": layout["field2"]["y"] * height,
            "maxWidth": layout["field2"]["maxWidth"] * width,
            "fontSize": layout["field2"]["fontSize"] * height,
        },
        "pronouns": {
            "x": layout["pronouns"]["x"] * width,
            "y": layout["pronouns"]["y"] * height,
            "fontSize": layout["pronouns"]["fontSize"] * height,
        },
    }


def apply_hue_saturation(image: Image.Image, hue: float = 0, saturation: float = 100) -> Image.Image:
    hue = float(hue or 0)
    saturation = float(saturation or 100)
    if hue == 0 and saturation == 100:
        return image.copy()

    rgba = image.convert("RGBA")
    alpha = rgba.split()[3]
    rgb = rgba.convert("RGB")
    hsv = np.array(rgb.convert("HSV"), dtype=np.float32)
    if hue:
        hsv[:, :, 0] = (hsv[:, :, 0] + (hue / 360.0) * 255.0) % 255.0
    if saturation != 100:
        hsv[:, :, 1] = np.clip(hsv[:, :, 1] * (saturation / 100.0), 0, 255)
    shifted = Image.fromarray(hsv.astype(np.uint8), mode="HSV").convert("RGB")
    shifted.putalpha(alpha)
    return shifted


def _fit_font(draw: ImageDraw.ImageDraw, text: str, max_width: float, font_size: float) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    size = max(12, int(font_size))
    while size > 10:
        font = _load_font(size)
        bbox = draw.textbbox((0, 0), text, font=font)
        if bbox[2] - bbox[0] <= max_width:
            return font
        size -= 1
    return _load_font(size)


def _draw_text(draw: ImageDraw.ImageDraw, text: str, x: float, y: float, max_width: float, font_size: float):
    if not text:
        return
    font = _fit_font(draw, text, max_width, font_size)
    draw.text((x, y), text, font=font, fill=(248, 250, 252), anchor="lm")


def _paste_circular_photo(base: Image.Image, photo: Image.Image, cx: float, cy: float, r: float):
    photo = photo.convert("RGBA")
    diameter = int(r * 2)
    aspect = photo.width / photo.height
    if aspect >= 1:
        nh = diameter
        nw = int(diameter * aspect)
    else:
        nw = diameter
        nh = int(diameter / aspect)
    photo = photo.resize((nw, nh), Image.Resampling.LANCZOS)
    left = int(cx - nw / 2)
    top = int(cy - nh / 2)

    mask = Image.new("L", (nw, nh), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, nw, nh), fill=255)
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    layer.paste(photo, (left, top), mask)
    base.alpha_composite(layer)


def render_card_front(
    identity_id: str,
    name: str = "",
    member_number: str = "",
    community_since: str = "",
    pronouns: str = "",
    photo_path: Path | None = None,
    hue: float = 0,
    saturation: float = 100,
) -> Image.Image:
    identity = resolve_identity(identity_id)
    if not identity:
        raise ValueError(f"Unknown identity: {identity_id}")

    card_path = CARDS_DIR / f"{identity['id']}.png"
    if not card_path.exists():
        raise FileNotFoundError(f"Missing card asset: {card_path}")

    bg = Image.open(card_path).convert("RGBA")
    bg = apply_hue_saturation(bg, hue, saturation)
    layout = _resolve_layout(bg.width, bg.height)
    draw = ImageDraw.Draw(bg)

    if photo_path and photo_path.exists():
        photo = Image.open(photo_path)
        _paste_circular_photo(
            bg, photo,
            layout["photo"]["cx"], layout["photo"]["cy"], layout["photo"]["r"],
        )

    _draw_text(draw, name, layout["name"]["x"], layout["name"]["y"], layout["name"]["maxWidth"], layout["name"]["fontSize"])

    second = community_since or member_number
    _draw_text(draw, second, layout["field2"]["x"], layout["field2"]["y"], layout["field2"]["maxWidth"], layout["field2"]["fontSize"])

    if pronouns and pronouns != "name only":
        font = _fit_font(draw, pronouns, layout["name"]["maxWidth"], layout["pronouns"]["fontSize"])
        draw.text(
            (layout["pronouns"]["x"], layout["pronouns"]["y"]),
            pronouns,
            font=font,
            fill=(248, 250, 252, 217),
        )

    return bg.convert("RGB")


def render_card_back(width: int, height: int) -> Image.Image:
    img = Image.new("RGB", (width, height), (15, 23, 42))
    draw = ImageDraw.Draw(img)
    title_font = _load_font(max(28, int(height * 0.065)))
    body_font = _load_font(max(14, int(height * 0.028)))
    small_font = _load_font(max(11, int(height * 0.018)))

    draw.rectangle((24, 24, width - 24, height - 24), outline=(255, 255, 255, 30), width=2)
    draw.text((width / 2, height * 0.18), "LGBTIQASB+", font=title_font, fill=(255, 255, 255), anchor="mm")
    draw.text((width / 2, height * 0.27), "Community Access Card", font=body_font, fill=(226, 232, 240), anchor="mm")

    lines = [
        "This card affirms your identity within our community.",
        "Carry it with pride. You belong here.",
        "",
        "Premium PVC • CR80 • Evolis Primacy 2 ready",
        "Printed in Australia • Respectful • Inclusive",
    ]
    y = height * 0.38
    for line in lines:
        draw.text((width / 2, y), line, font=body_font, fill=(203, 213, 225), anchor="mm")
        y += height * 0.05

    draw.rectangle((0, int(height * 0.84), width, height), fill=(49, 46, 129))
    draw.text((width / 2, height * 0.89), "YOUR IDENTITY • YOUR COMMUNITY • YOU BELONG", font=body_font, fill=(255, 255, 255), anchor="mm")
    draw.text((48, height * 0.96), "Premium Community Access Card • Printed on high-quality PVC", font=small_font, fill=(148, 163, 184), anchor="ls")
    return img