"""MrBeast-style thumbnails + high-energy hooks.

The grammar of a high-CTR thumbnail: one huge high-contrast phrase (3-5 words),
a bright accent, a heavy dark scrim over a real image so text always reads, and a
small credibility badge. Built over the repo's real GitHub social card when we
have it, so the thumbnail shows the actual project — not a stock mockup.
"""

from __future__ import annotations

import os
import textwrap
from typing import List, Optional

from PIL import Image, ImageDraw, ImageFilter, ImageFont

YELLOW = (255, 209, 0)
RED = (255, 59, 48)
GREEN = (35, 209, 96)
WHITE = (245, 248, 250)
INK = (10, 12, 16)


def _font(size: int, bold: bool = True):
    names = (["arialbd.ttf", "Arial Bold.ttf", "arial.ttf"] if bold
             else ["arial.ttf", "DejaVuSans.ttf"])
    for n in names:
        try:
            return ImageFont.truetype(n, size)
        except Exception:
            continue
    return ImageFont.load_default(size=size)


def _outlined(d: ImageDraw.ImageDraw, xy, text, font, fill, outline=INK, w=6):
    x, y = xy
    for dx in range(-w, w + 1, 2):
        for dy in range(-w, w + 1, 2):
            if dx * dx + dy * dy <= w * w:
                d.text((x + dx, y + dy), text, font=font, fill=outline)
    d.text((x, y), text, font=font, fill=fill)


def mrbeast_thumbnail(headline: str, badge: str, out_path: str,
                      hero: Optional[str] = None, size=(1280, 720),
                      accent=YELLOW) -> str:
    """Bold, high-contrast thumbnail. `hero` is a background image (repo card)."""
    W, H = size
    if hero and os.path.exists(hero):
        bg = Image.open(hero).convert("RGB")
        # cover-fit the hero, blur + darken into a dramatic backdrop
        scale = max(W / bg.width, H / bg.height)
        bg = bg.resize((int(bg.width * scale) + 1, int(bg.height * scale) + 1))
        bg = bg.crop((0, 0, W, H)).filter(ImageFilter.GaussianBlur(6))
        dark = Image.new("RGB", (W, H), INK)
        bg = Image.blend(bg, dark, 0.55)
    else:
        bg = Image.new("RGB", (W, H), (16, 20, 28))
    img = bg.copy()
    d = ImageDraw.Draw(img)

    # left accent slab for energy
    d.rectangle([0, 0, 16, H], fill=accent)
    d.rectangle([0, H - 16, W, H], fill=accent)

    # giant headline (2-3 lines), auto-sized to fit
    words = headline.upper()
    for fs, width in ((150, 11), (120, 14), (96, 18), (78, 22), (64, 26)):
        font = _font(fs)
        lines = textwrap.wrap(words, width=width)
        lh = fs + 12
        if len(lines) <= 3 and len(lines) * lh < H - 200:
            break
    total = len(lines) * lh
    y = (H - total) // 2 - 20
    for i, ln in enumerate(lines):
        bb = d.textbbox((0, 0), ln, font=font)
        tw = bb[2] - bb[0]
        col = accent if i == len(lines) - 1 else WHITE
        _outlined(d, ((W - tw) // 2, y), ln, font, col, w=7)
        y += lh

    # credibility badge (top-left) + brand (bottom-right)
    bf = _font(40)
    bb = d.textbbox((0, 0), badge, font=bf)
    pad = 18
    d.rectangle([40, 36, 40 + (bb[2] - bb[0]) + pad * 2, 36 + (bb[3] - bb[1]) + pad * 2],
                fill=RED)
    d.text((40 + pad, 36 + pad - bb[1]), badge, font=bf, fill=WHITE)

    brand = "COGNIS DIGITAL"
    sf = _font(34)
    sbb = d.textbbox((0, 0), brand, font=sf)
    _outlined(d, (W - (sbb[2] - sbb[0]) - 40, H - 70), brand, sf, accent, w=4)

    # white Cognis logo, top-right (dark scrim behind keeps it readable)
    for lp in (os.environ.get("COGNIS_LOGO_WHITE"), r"C:\Users\user\_brand\logo_white.png",
               os.path.expanduser("~/_brand/logo_white.png")):
        if lp and os.path.exists(lp):
            try:
                logo = Image.open(lp).convert("RGBA")
                sz = 96
                logo.thumbnail((sz, sz))
                img.paste(logo, (W - sz - 36, 30), logo)
            except Exception:
                pass
            break

    img.save(out_path)
    return out_path


# High-energy opening hooks — punchy, but no fabricated claims or fake numbers.
HOOKS: List[str] = [
    "Stop scrolling. The AI tool the big labs don't want you running yourself just shipped.",
    "Everyone is renting their AI. We built one you actually own. Watch this.",
    "This runs entirely on your machine. No cloud. No vendor. Let me show you.",
    "What if your AI stack was provable, auditable, and yours? It can be. Here is how.",
]


def hook_for(name: str, summary: str, i: int = 0) -> str:
    base = HOOKS[i % len(HOOKS)]
    return base
