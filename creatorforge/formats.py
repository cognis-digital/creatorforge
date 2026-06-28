"""Long-form formats — the proven structures behind the videos that hold attention.

Each format is a sequence of named beats with a relative weight (how much of the
runtime it gets) and a purpose. These are the standard structures documentary,
video-essay, devlog, and promo editors actually use — encoded so the engine can
allocate a 5–15 minute runtime across them and write to each beat's job.
"""

from __future__ import annotations

# beat = (name, weight, purpose). weights are relative; they're normalized to runtime.
FORMATS = {
    "documentary": {
        "default_minutes": 12,
        "default_style": "epic_doc",
        "beats": [
            ("cold_open", 1.0, "a gripping 15-30s moment that poses the question"),
            ("thesis", 0.8, "state what this film is really about"),
            ("context", 1.5, "the background the viewer needs"),
            ("rising_action", 2.5, "develop the story, raise the stakes"),
            ("turn", 1.2, "the complication or revelation"),
            ("climax", 1.8, "the peak — the answer or the confrontation"),
            ("resolution", 1.2, "what it means now"),
            ("outro", 0.6, "reflective close + subscribe/next"),
        ],
    },
    "video_essay": {
        "default_minutes": 10,
        "default_style": "arthouse_slowburn",
        "beats": [
            ("hook", 0.8, "a provocative claim or question"),
            ("premise", 1.0, "frame the argument"),
            ("evidence_1", 1.6, "first pillar of the argument"),
            ("evidence_2", 1.6, "second pillar"),
            ("counterpoint", 1.2, "steelman the other side"),
            ("synthesis", 1.4, "resolve the tension"),
            ("conclusion", 0.9, "land the thesis + call to think"),
        ],
    },
    "devlog": {
        "default_minutes": 8,
        "default_style": "kinetic_vlog",
        "beats": [
            ("recap", 0.6, "where we left off"),
            ("goal", 0.8, "what we're building this episode"),
            ("build", 2.2, "the work, montage-paced"),
            ("obstacle", 1.2, "what broke and why"),
            ("breakthrough", 1.4, "the fix / the win"),
            ("demo", 1.2, "show it working"),
            ("next_steps", 0.6, "tease next episode + CTA"),
        ],
    },
    "promotional": {
        "default_minutes": 5,
        "default_style": "blockbuster",
        "beats": [
            ("hook", 1.0, "stop-the-scroll opener"),
            ("problem", 1.0, "the pain the viewer feels"),
            ("agitate", 0.8, "make the cost of inaction real"),
            ("solution", 1.4, "introduce the product as the answer"),
            ("proof", 1.2, "demos, results, credibility"),
            ("offer", 0.8, "what they get and how"),
            ("cta", 0.6, "one clear action"),
        ],
    },
}


def get_format(name: str) -> dict:
    if name not in FORMATS:
        raise ValueError(f"unknown format: {name}. Known: {', '.join(FORMATS)}")
    return FORMATS[name]


def allocate(beats, total_seconds: float) -> list:
    """Distribute runtime across beats by weight. Returns [(name, purpose, seconds)]."""
    total_weight = sum(w for _n, w, _p in beats) or 1.0
    return [(n, p, round(total_seconds * w / total_weight, 1)) for n, w, p in beats]
