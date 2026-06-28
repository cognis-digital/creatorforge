"""Platform specs and packaging — one idea, tailored for every channel.

Each platform has its own shape: aspect ratio, length sweet spot, title/caption
limits, hashtag norms. `package` takes a core piece of content and produces a
ready-to-post deliverable that respects those constraints.
"""

from __future__ import annotations

from typing import Optional

from .voice import VoiceProfile

PLATFORMS = {
    "youtube": {"aspect": "16:9", "max_title": 100, "max_caption": 5000,
                "hashtags": 3, "ideal_seconds": 600, "kind": "long"},
    "youtube_shorts": {"aspect": "9:16", "max_title": 100, "max_caption": 100,
                       "hashtags": 3, "ideal_seconds": 45, "kind": "short"},
    "tiktok": {"aspect": "9:16", "max_title": 0, "max_caption": 2200,
               "hashtags": 5, "ideal_seconds": 27, "kind": "short"},
    "reels": {"aspect": "9:16", "max_title": 0, "max_caption": 2200,
              "hashtags": 5, "ideal_seconds": 60, "kind": "short"},
    "x": {"aspect": "16:9", "max_title": 0, "max_caption": 280,
          "hashtags": 2, "ideal_seconds": 45, "kind": "text"},
    "linkedin": {"aspect": "1:1", "max_title": 0, "max_caption": 3000,
                 "hashtags": 3, "ideal_seconds": 90, "kind": "text"},
}


def platform_spec(name: str) -> dict:
    if name not in PLATFORMS:
        raise ValueError(f"unknown platform: {name}. Known: {', '.join(PLATFORMS)}")
    return PLATFORMS[name]


def _clip(text: str, limit: int) -> str:
    if limit <= 0 or len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def _hashtags(niche: str, voice: VoiceProfile, count: int) -> list[str]:
    seed = [niche.replace(" ", "")] + list(voice.top_terms)
    tags, seen = [], set()
    for term in seed:
        t = "#" + "".join(ch for ch in term if ch.isalnum())
        if t.lower() not in seen and len(t) > 1:
            seen.add(t.lower())
            tags.append(t)
        if len(tags) >= count:
            break
    return tags


def package(core: dict, platform: str, voice: Optional[VoiceProfile] = None) -> dict:
    """core: {topic, hook, summary, niche}. Returns a per-platform deliverable."""
    voice = voice or VoiceProfile()
    spec = platform_spec(platform)
    topic = core.get("topic", "")
    hook = core.get("hook", topic)
    summary = core.get("summary", "")
    niche = core.get("niche", topic)
    tags = _hashtags(niche, voice, spec["hashtags"])

    if spec["kind"] == "text":
        if platform == "x":
            body = _clip(f"{hook}\n\n{summary}", spec["max_caption"] - 12)
            caption = f"{body}\n{' '.join(tags)}".strip()
        else:  # linkedin
            caption = _clip(f"{hook}\n\n{summary}\n\n{' '.join(tags)}", spec["max_caption"])
        return {"platform": platform, "aspect": spec["aspect"], "caption": caption,
                "hashtags": tags, "target_seconds": spec["ideal_seconds"]}

    title = _clip(hook, spec["max_title"]) if spec["max_title"] else ""
    cap_body = f"{summary} {' '.join(tags)}".strip() if summary else " ".join(tags)
    caption = _clip(cap_body, spec["max_caption"])
    return {
        "platform": platform,
        "aspect": spec["aspect"],
        "title": title,
        "caption": caption,
        "hashtags": tags,
        "target_seconds": spec["ideal_seconds"],
    }
