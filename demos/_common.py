"""Shared helpers for the demo scenarios.

Every demo runs **fully offline**: no network, no GPU, no model download. They use
the deterministic engine and the default `TemplateProvider`, so the same inputs
always give the same output — the demos double as smoke tests.
"""
from __future__ import annotations

import os
import sys

# allow `python demos/NN_name.py` from anywhere
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from creatorforge.voice import VoiceProfile, analyze  # noqa: E402

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAMPLE_CORPUS = os.path.join(REPO_ROOT, "examples", "sample_corpus")

# A small, vivid set of past posts to learn a creator voice from — short, punchy,
# emoji-heavy, ALLCAPS emphasis, explicit CTAs. Bundled so demos never touch disk
# state that another run might have changed.
SAMPLE_POSTS = [
    "🚀 Stop scrolling. This ONE habit changed how I ship. Follow for more 🔥",
    "Most creators burn out for ONE reason: they post without a system.\n"
    "Here's the fix 👇 Batch. Template. Repurpose. Comment 'SYSTEM' and I'll send mine.",
    "I tried posting daily for 30 days. The results SHOCKED me. Save this 📌",
    "Nobody tells you this about growth: consistency beats genius. Every. Single. Time. ⚡",
    "3 tools that 10x'd my output. No fluff. Link in bio 🛠️",
]


def sample_voice() -> VoiceProfile:
    """A reproducible creator voice profile, learned from SAMPLE_POSTS."""
    return analyze(SAMPLE_POSTS)


def rule(title: str) -> None:
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def field(label: str, value: str = "") -> None:
    print(f"  {label:<22} {value}")


def bullet(text: str) -> None:
    print(f"     - {text}")
