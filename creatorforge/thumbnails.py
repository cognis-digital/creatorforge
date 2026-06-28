"""Thumbnail concepts — and a rendered SVG mockup for each.

The thumbnail decides the click. `thumbnail_concepts` proposes headline + visual
+ emotion + layout combinations; `render_svg` turns a concept into an actual
1280×720 SVG you can preview in a browser or hand to a designer as a brief.
"""

from __future__ import annotations

import html
import re
from typing import List, Optional

from .voice import VoiceProfile

_EMOTIONS = ["shock", "curiosity", "authority", "urgency"]
_LAYOUTS = ["left-text / right-subject", "center-bold", "split-screen", "top-banner"]
_PALETTES = [
    {"bg": "#0E1517", "accent": "#F4B400", "text": "#FFFFFF"},
    {"bg": "#14110F", "accent": "#FF5252", "text": "#FFF8E7"},
    {"bg": "#0B1E2D", "accent": "#34D399", "text": "#EAF6FF"},
]
_POWER = ["SECRETS", "TRUTH", "MISTAKES", "BLUEPRINT", "IN 60s", "EXPOSED"]


def _keyword(topic: str) -> str:
    words = re.findall(r"[A-Za-z][A-Za-z0-9'-]+", topic)
    return (max(words, key=len) if words else topic).upper()


def thumbnail_concepts(topic: str, voice: Optional[VoiceProfile] = None, n: int = 3) -> List[dict]:
    voice = voice or VoiceProfile()
    kw = _keyword(topic)
    concepts = []
    for i in range(n):
        concepts.append({
            "headline": f"{kw} {_POWER[i % len(_POWER)]}",
            "subtext": topic,
            "visual": f"expressive subject reacting to {topic.lower()}",
            "emotion": _EMOTIONS[i % len(_EMOTIONS)],
            "layout": _LAYOUTS[i % len(_LAYOUTS)],
            "palette": _PALETTES[i % len(_PALETTES)],
        })
    return concepts


def _wrap(text: str, per_line: int = 12) -> List[str]:
    words, lines, cur = text.split(), [], ""
    for w in words:
        if len(cur) + len(w) + 1 > per_line and cur:
            lines.append(cur)
            cur = w
        else:
            cur = f"{cur} {w}".strip()
    if cur:
        lines.append(cur)
    return lines[:3]


def render_svg(concept: dict, width: int = 1280, height: int = 720) -> str:
    p = concept.get("palette", _PALETTES[0])
    lines = _wrap(concept.get("headline", ""), per_line=12)
    fs = 150 if len(lines) <= 1 else 120
    y0 = height // 2 - (len(lines) - 1) * fs // 2
    texts = "".join(
        f'<text x="64" y="{y0 + i * fs}" font-family="Arial Black, Arial, sans-serif" '
        f'font-size="{fs}" font-weight="900" fill="{p["text"]}">{html.escape(ln)}</text>'
        for i, ln in enumerate(lines)
    )
    sub = html.escape(concept.get("subtext", ""))
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">'
        f'<rect width="{width}" height="{height}" fill="{p["bg"]}"/>'
        f'<rect x="0" y="0" width="18" height="{height}" fill="{p["accent"]}"/>'
        f'{texts}'
        f'<rect x="64" y="{height - 120}" width="520" height="8" fill="{p["accent"]}"/>'
        f'<text x="64" y="{height - 70}" font-family="Arial, sans-serif" font-size="40" '
        f'fill="{p["accent"]}">{sub}</text>'
        f'</svg>'
    )
