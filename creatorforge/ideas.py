"""Idea generation — a steady pipeline of angles so you never stare at a blank page.

Ideas come from crossing proven *formats* with *angles* against your niche. Each
idea carries the format, the angle, which platforms it fits, and a hook seed to
feed the hook writer. Deterministic and de-duplicated.
"""

from __future__ import annotations

from typing import List, Optional

from .voice import VoiceProfile

FORMATS = [
    ("listicle", ["youtube", "tiktok", "reels", "x"]),
    ("tutorial", ["youtube", "youtube_shorts"]),
    ("story", ["reels", "tiktok", "youtube_shorts"]),
    ("myth-bust", ["youtube", "tiktok", "x"]),
    ("case study", ["youtube", "linkedin"]),
    ("reaction", ["youtube_shorts", "tiktok"]),
    ("day in the life", ["reels", "tiktok"]),
    ("comparison", ["youtube", "x"]),
    ("Q&A", ["youtube", "linkedin"]),
    ("behind the scenes", ["reels", "tiktok"]),
]

ANGLES = [
    "beginner mistakes", "advanced tactics", "the contrarian take",
    "this week's trend", "the tool stack", "real results, broken down",
    "step by step", "the mindset shift", "fast wins under 5 minutes",
    "the deep dive",
]

_TITLE = {
    "listicle": "{n} {angle} for {niche}",
    "tutorial": "How to master {niche}: {angle}",
    "story": "How {angle} changed my {niche}",
    "myth-bust": "The biggest {niche} myth: {angle}",
    "case study": "{niche} case study — {angle}",
    "reaction": "Reacting to {niche} takes: {angle}",
    "day in the life": "A day of {niche}: {angle}",
    "comparison": "{niche} compared: {angle}",
    "Q&A": "Your {niche} questions answered — {angle}",
    "behind the scenes": "Behind the scenes of {niche}: {angle}",
}


def generate_ideas(niche: str, voice: Optional[VoiceProfile] = None, n: int = 10) -> List[dict]:
    voice = voice or VoiceProfile()
    ideas: List[dict] = []
    seen = set()
    i = 0
    while len(ideas) < n and i < n * len(ANGLES) + len(FORMATS):
        fmt, fits = FORMATS[i % len(FORMATS)]
        angle = ANGLES[(i // len(FORMATS)) % len(ANGLES)]
        number = (i % 5) + 5
        title = _TITLE[fmt].format(n=number, angle=angle, niche=niche)
        key = (fmt, angle)
        i += 1
        if key in seen:
            continue
        seen.add(key)
        ideas.append({
            "title": title,
            "format": fmt,
            "angle": angle,
            "platforms": fits,
            "hook_seed": f"{angle} in {niche}",
        })
    return ideas
