"""Scriptwriting — a full, structured script you can read off-camera.

Produces a hook, a setup, a sequence of value beats (each with a point, a detail,
and a b-roll suggestion), and a call to action, sized to the target platform's
ideal length. The structure is deterministic; an optional provider rewrites the
prose in the creator's voice.
"""

from __future__ import annotations

from typing import List, Optional

from .hooks import write_hooks
from .platforms import platform_spec
from .providers import Provider, TemplateProvider
from .voice import VoiceProfile

WPM = 150  # average speaking pace

_BEAT_POINTS = [
    "the problem most people hit",
    "why the usual advice fails",
    "the approach that actually works",
    "a concrete example",
    "the mistake to avoid",
    "how to start today",
    "the result you can expect",
]


def _beats_for_seconds(seconds: int) -> int:
    if seconds <= 60:
        return 3
    if seconds <= 180:
        return 4
    return min(7, 4 + seconds // 180)


def write_script(topic: str, voice: Optional[VoiceProfile] = None,
                 platform: str = "youtube", *, provider: Optional[Provider] = None) -> dict:
    voice = voice or VoiceProfile()
    provider = provider or TemplateProvider()
    spec = platform_spec(platform)
    target = spec["ideal_seconds"]
    n_beats = _beats_for_seconds(target)

    hook = write_hooks(topic, voice, 1)[0]["hook"]
    intro = f"In the next {_human_time(target)}, here's exactly how to get {topic} right."
    beats: List[dict] = []
    for i in range(n_beats):
        point = _BEAT_POINTS[i % len(_BEAT_POINTS)]
        beats.append({
            "point": point.capitalize(),
            "detail": f"On {topic}: {point}. Show, don't just tell — give the viewer the specific move.",
            "broll": f"b-roll: illustrate '{point}' for {topic}",
        })
    cta = (voice.cta_phrases[0].capitalize() + " for more."
           if voice.cta_phrases else f"Follow for more on {topic}.")

    spoken = [hook, intro] + [b["detail"] for b in beats] + [cta]
    word_count = sum(len(s.split()) for s in spoken)
    script = {
        "topic": topic,
        "platform": platform,
        "hook": hook,
        "intro": intro,
        "beats": beats,
        "cta": cta,
        "word_count": word_count,
        "est_seconds": round(word_count / WPM * 60),
    }

    if getattr(provider, "available", False) and not isinstance(provider, TemplateProvider):
        body = "\n".join(f"- {s}" for s in spoken)
        polished = provider.rewrite(body, voice, instruction=f"Rewrite this {platform} script:")
        script["polished"] = polished
    return script


def _human_time(seconds: int) -> str:
    if seconds < 90:
        return f"{seconds} seconds"
    return f"{round(seconds / 60)} minutes"
