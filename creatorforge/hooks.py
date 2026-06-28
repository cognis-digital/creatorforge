"""Hooks — the first 3 seconds that decide whether anyone watches.

A library of hook *formulas* that consistently stop the scroll, instantiated for
the topic and styled to the creator's voice. Deterministic: the same inputs give
the same hooks, so you can regenerate and diff. Plug a model in to rewrite them
into sharper prose; the formulas alone are already usable.
"""

from __future__ import annotations

import re
from typing import List, Optional

from .voice import VoiceProfile

# (label, template) — slots: topic, audience, pain, outcome, obstacle, n, keyword
_FORMULAS = [
    ("curiosity-gap", "The truth about {topic} nobody tells you"),
    ("transformation", "I tried {topic} for 30 days — here's what actually happened"),
    ("pattern-interrupt", "Stop everything you know about {topic}"),
    ("loss-aversion", "{n} {topic} mistakes quietly costing you {pain}"),
    ("how-to-without", "How to {outcome} without {obstacle}"),
    ("contrarian", "Everyone is wrong about {topic}. Here's the proof."),
    ("dead-trend", "{topic} as you know it is over — here's what's replacing it"),
    ("authority", "I asked 100 {audience} about {topic}. The answers surprised me."),
    ("fast-win", "The fastest way to {outcome} (most people do this backwards)"),
    ("listicle", "{n} {topic} tips I wish I knew earlier"),
]


def _keyword(topic: str) -> str:
    words = re.findall(r"[A-Za-z][A-Za-z0-9'-]+", topic)
    return max(words, key=len) if words else topic


def _style(text: str, voice: VoiceProfile, i: int) -> str:
    out = text
    if voice.caps_emphasis_rate >= 2.0:
        kw = _keyword(text)
        out = out.replace(kw, kw.upper(), 1)
    if voice.energetic and not out.endswith(("!", "?")):
        out += "!"
    if voice.emoji_heavy and voice.signature_emojis:
        emoji = voice.signature_emojis[i % len(voice.signature_emojis)]
        out = f"{emoji} {out}"
    return out


def write_hooks(topic: str, voice: Optional[VoiceProfile] = None, n: int = 8, *,
                audience: str = "people", pain: str = "time and reach",
                outcome: Optional[str] = None, obstacle: str = "a big budget") -> List[dict]:
    voice = voice or VoiceProfile()
    outcome = outcome or f"win with {topic}"
    slots = {"topic": topic, "audience": audience, "pain": pain,
             "outcome": outcome, "obstacle": obstacle}
    hooks: List[dict] = []
    for i in range(n):
        label, template = _FORMULAS[i % len(_FORMULAS)]
        number = (i % 5) + 3  # 3..7, stable
        text = template.format(n=number, **slots)
        hooks.append({"hook": _style(text, voice, i), "formula": label})
    return hooks
