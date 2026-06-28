"""Cinematic styles and story structures — the craft of the entertainment industry,
encoded as technique.

A *style* is a coherent set of choices the great directors and documentary teams
are known for — pacing, shot vocabulary, color, music mood, editing rhythm — that
the engine applies to a production so it doesn't feel like generic content. These
are described as **techniques and lineages** (homage), not impersonations: you're
borrowing the grammar of the form, the way film schools teach it.

A *structure* is a story skeleton (three-act, the Story Circle, the Hero's
Journey) that orders the emotional beats. Formats pick one by default; you can
override it.
"""

from __future__ import annotations

STYLES = {
    "epic_doc": {
        "scene_seconds": 9, "music_mood": "sweeping orchestral, slow build",
        "palette": "warm amber + deep teal, filmic", "narration_tone": "measured, authoritative",
        "shot_vocab": ["slow push-in", "drone establishing", "archival inserts", "Ken Burns on stills"],
        "editing": "long takes, motivated cuts", "homage": "prestige nature/history docs",
    },
    "true_crime": {
        "scene_seconds": 7, "music_mood": "tense drones, ticking pulse",
        "palette": "desaturated cold, pools of light", "narration_tone": "hushed, ominous",
        "shot_vocab": ["macro evidence", "reenactment silhouettes", "map zooms", "interview crops"],
        "editing": "withholding cuts, cliffhanger act-outs", "homage": "investigative true-crime series",
    },
    "kinetic_vlog": {
        "scene_seconds": 4, "music_mood": "upbeat lo-fi / hip-hop, driving",
        "palette": "bright, punchy, high saturation", "narration_tone": "fast, casual, energetic",
        "shot_vocab": ["handheld whip-pan", "jump cuts", "screen capture", "POV"],
        "editing": "fast, beat-synced, zooms on emphasis", "homage": "modern creator vlog/devlog",
    },
    "arthouse_slowburn": {
        "scene_seconds": 11, "music_mood": "minimal ambient, single motif",
        "palette": "muted naturalistic, soft grain", "narration_tone": "intimate, essayistic",
        "shot_vocab": ["static wides", "symmetry", "negative space", "slow zoom"],
        "editing": "patient, dissolves, breathing room", "homage": "indie/A24-style slow cinema",
    },
    "blockbuster": {
        "scene_seconds": 5, "music_mood": "big percussive trailer score, risers",
        "palette": "high-contrast teal & orange", "narration_tone": "bold, confident, punchy",
        "shot_vocab": ["hero low-angle", "speed ramps", "parallax title cards", "macro product"],
        "editing": "trailer-cut, hit on the beat, hard cuts", "homage": "tentpole trailer grammar",
    },
    "retro_vhs": {
        "scene_seconds": 6, "music_mood": "synthwave, analog warmth",
        "palette": "VHS chroma bleed, scanlines, neon", "narration_tone": "playful, nostalgic",
        "shot_vocab": ["CRT overlays", "tape glitch transitions", "grainy zoom"],
        "editing": "rhythmic, glitch wipes", "homage": "80s/90s analog aesthetic",
    },
    "minimalist_clean": {
        "scene_seconds": 7, "music_mood": "clean corporate ambient, gentle",
        "palette": "white space, one accent, flat", "narration_tone": "clear, calm, precise",
        "shot_vocab": ["centered product", "soft gradient bg", "kinetic typography"],
        "editing": "smooth, motion-graphics led", "homage": "modern product/keynote film",
    },
}

# story skeletons — ordered emotional beats (used when you want to override a format)
STRUCTURES = {
    "three_act": ["setup", "inciting incident", "rising action", "midpoint",
                  "crisis", "climax", "resolution"],
    "story_circle": ["you (comfort)", "need", "go (cross threshold)", "search (adapt)",
                     "find", "take (pay the price)", "return", "change"],
    "hero_journey": ["ordinary world", "call to adventure", "refusal", "mentor",
                     "threshold", "trials", "ordeal", "reward", "road back", "return"],
}


def get_style(name: str) -> dict:
    if name not in STYLES:
        raise ValueError(f"unknown style: {name}. Known: {', '.join(STYLES)}")
    return STYLES[name]


def list_styles() -> list:
    return sorted(STYLES)
