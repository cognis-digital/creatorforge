"""Platform & algorithm intelligence — what actually performs, turned into directives.

These are the well-documented signals each platform's algorithm optimizes for and
the retention tactics top creators use, encoded so production decisions are made
*for* the algorithm, not against it. They're established practice (watch-time /
AVD on YouTube, completion-rate and rewatches on TikTok/Reels, early engagement
velocity, the first-few-seconds hook), not guesses — and `production_notes`
turns them into concrete instructions the long-form engine applies.

(For a live refresh of trends, `creatorforge` can pair with a research pass; the
durable signals below change slowly and are the safe default.)
"""

from __future__ import annotations

PLATFORM_PLAYBOOKS = {
    "youtube_long": {
        "optimal_minutes": (8, 14),
        "hook_window_s": 30,
        "pattern_interrupt_s": 40,
        "chapters": True,
        "end_screen": True,
        "algorithm_signals": ["average view duration", "watch time", "click-through rate",
                              "session watch time", "viewer satisfaction"],
        "retention_tactics": [
            "open on the payoff/question in the first 30s (no long intro)",
            "re-hook every ~40s with a new question, visual, or stakes raise",
            "use chapters; label them with curiosity, not topics",
            "front-load the most compelling b-roll",
            "tease a later moment early ('but first…') to extend AVD",
        ],
        "title_formula": "specific outcome + curiosity gap (≤60 chars)",
        "thumbnail_formula": "one bold idea, ≤4 words, expressive face or hero object, high contrast",
        "cadence": "1-2x / week, consistent day",
    },
    "youtube_shorts": {
        "optimal_minutes": (0.25, 1.0), "hook_window_s": 2, "pattern_interrupt_s": 6,
        "chapters": False, "end_screen": False,
        "algorithm_signals": ["completion rate", "rewatches", "swipe-away rate", "shares"],
        "retention_tactics": ["hook in <2s", "loop the ending to the start", "one idea only",
                              "captions always on", "fast cuts every 2-3s"],
        "title_formula": "punchy + keyword", "thumbnail_formula": "n/a (vertical, first frame is the hook)",
        "cadence": "daily",
    },
    "tiktok": {
        "optimal_minutes": (0.2, 0.6), "hook_window_s": 2, "pattern_interrupt_s": 5,
        "chapters": False, "end_screen": False,
        "algorithm_signals": ["completion rate", "rewatches", "shares", "comments",
                              "early engagement velocity"],
        "retention_tactics": ["native hook in <2s", "ride a trending sound", "text hook on screen",
                              "open loop you close at the end", "reply-to-comment follow-ups"],
        "title_formula": "conversational + 3-5 niche hashtags", "thumbnail_formula": "n/a",
        "cadence": "1-3x / day",
    },
    "reels": {
        "optimal_minutes": (0.25, 1.5), "hook_window_s": 2, "pattern_interrupt_s": 6,
        "chapters": False, "end_screen": False,
        "algorithm_signals": ["completion rate", "shares to DMs", "saves", "rewatches"],
        "retention_tactics": ["visual hook + text hook together", "make it saveable/shareable",
                              "trending audio", "tight 7-15s for reach, longer for depth"],
        "title_formula": "value-promise caption", "thumbnail_formula": "clean cover frame",
        "cadence": "daily",
    },
    "linkedin": {
        "optimal_minutes": (0.5, 2.0), "hook_window_s": 3, "pattern_interrupt_s": 20,
        "chapters": False, "end_screen": False,
        "algorithm_signals": ["dwell time", "comments", "reshares", "early engagement"],
        "retention_tactics": ["first line is the hook (it's the preview)", "1 idea, story-led",
                              "native upload", "ask one specific question to drive comments"],
        "title_formula": "contrarian or lesson-led first line", "thumbnail_formula": "captioned still",
        "cadence": "2-4x / week",
    },
}

# map a content format to its best long/short platform context
_FORMAT_PLATFORM = {
    "documentary": "youtube_long", "video_essay": "youtube_long",
    "devlog": "youtube_long", "promotional": "youtube_long",
}


def playbook_for(platform: str) -> dict:
    return PLATFORM_PLAYBOOKS.get(platform, PLATFORM_PLAYBOOKS["youtube_long"])


def production_notes(platform: str, fmt: str = "documentary") -> dict:
    """Concrete production directives for a platform + format."""
    pb = playbook_for(platform)
    lo, hi = pb["optimal_minutes"]
    return {
        "platform": platform,
        "target_minutes_range": [lo, hi],
        "hook_must_land_by_s": pb["hook_window_s"],
        "re_hook_every_s": pb["pattern_interrupt_s"],
        "use_chapters": pb["chapters"],
        "algorithm_optimizes_for": pb["algorithm_signals"],
        "retention_tactics": pb["retention_tactics"],
        "title_formula": pb["title_formula"],
        "thumbnail_formula": pb["thumbnail_formula"],
        "posting_cadence": pb["cadence"],
    }


def long_platform_for(fmt: str) -> str:
    return _FORMAT_PLATFORM.get(fmt, "youtube_long")
