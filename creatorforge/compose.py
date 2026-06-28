"""Compositing — turn a real photo into a designed, graded thumbnail.

This is the other half of punching above your weight class: once you've *sourced*
a real, no-watermark photo, design it like an editor would — cover-crop to frame,
apply a cinematic grade, lay a legibility scrim, and set a bold headline. A real
photo treated this way reads as professional, no diffusion model required.
"""

from __future__ import annotations

from typing import Optional

from .images import _font
from .thumbnails import _wrap


def _cover(img, w: int, h: int):
    """Resize+center-crop so the image fully covers the WxH frame."""
    iw, ih = img.size
    scale = max(w / iw, h / ih)
    nw, nh = int(iw * scale + 0.5), int(ih * scale + 0.5)
    img = img.resize((nw, nh))
    left, top = (nw - w) // 2, (nh - h) // 2
    return img.crop((left, top, left + w, top + h))


def _grade(img, grade: str):
    from PIL import ImageEnhance, ImageOps
    if grade == "noir":
        img = ImageOps.grayscale(img).convert("RGB")
        return ImageEnhance.Contrast(img).enhance(1.25)
    if grade == "warm":
        r, g, b = img.split()
        r = r.point(lambda v: min(255, int(v * 1.08)))
        b = b.point(lambda v: int(v * 0.94))
        from PIL import Image
        img = Image.merge("RGB", (r, g, b))
    # default "cinematic": a touch more contrast + saturation, slightly darker
    img = ImageEnhance.Contrast(img).enhance(1.12)
    img = ImageEnhance.Color(img).enhance(1.12)
    img = ImageEnhance.Brightness(img).enhance(0.94)
    return img


def _scrim(img, accent: str):
    """Darken left + bottom with a gradient so headline text stays legible."""
    from PIL import Image

    w, h = img.size
    overlay = Image.new("L", (w, 1))
    for x in range(w):
        overlay.putpixel((x, 0), int(200 * max(0.0, 1 - x / (w * 0.7))))  # dark left → clear right
    grad = overlay.resize((w, h))
    black = Image.new("RGB", (w, h), (0, 0, 0))
    img = Image.composite(black, img, grad)
    # bottom band for subtext
    band = Image.new("L", (1, h))
    for y in range(h):
        band.putpixel((0, y), int(180 * max(0.0, (y - h * 0.72) / (h * 0.28))))
    img = Image.composite(black, img, band.resize((w, h)))
    return img


def compose_thumbnail(hero_path: str, concept: dict, out_path: str, *,
                      width: int = 1280, height: int = 720, grade: str = "cinematic") -> dict:
    """Composite a headline over a graded real photo. Returns {path, backend}."""
    from PIL import Image, ImageDraw

    p = concept.get("palette", {"accent": "#F4B400", "text": "#FFFFFF"})
    img = Image.open(hero_path).convert("RGB")
    img = _cover(img, width, height)
    img = _grade(img, grade)
    img = _scrim(img, p.get("accent", "#F4B400"))

    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 18, height], fill=p.get("accent", "#F4B400"))
    lines = _wrap(concept.get("headline", ""), per_line=12)
    fs = 150 if len(lines) <= 1 else 120
    font = _font(fs)
    y = height // 2 - (len(lines) - 1) * fs // 2 - fs // 2
    for ln in lines:
        # subtle drop shadow for pop
        d.text((66, y + 3), ln, fill="#000000", font=font)
        d.text((64, y), ln, fill=p.get("text", "#FFFFFF"), font=font)
        y += fs
    d.rectangle([64, height - 120, 584, height - 112], fill=p.get("accent", "#F4B400"))
    d.text((64, height - 95), concept.get("subtext", ""), fill=p.get("accent", "#F4B400"),
           font=_font(40))

    path = out_path if out_path.endswith(".png") else out_path + ".png"
    img.save(path, format="PNG")
    return {"path": path, "backend": "composite-photo", "hero": hero_path, "grade": grade}
