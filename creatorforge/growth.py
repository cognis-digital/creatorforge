"""Growth playbook — mirror how the major AI companies actually got big.

A curated set of the growth plays that repeatedly worked for the AI companies
that broke out — and a `launch_strategy` that turns them into a concrete 30-day
content calendar for *your* repo. These are well-documented patterns (a runnable
demo over a pitch deck, building in public, a benchmark moment, developer-first
distribution), not secrets — the edge is executing them consistently.
"""

from __future__ import annotations

from typing import List

GROWTH_PLAYS = [
    {"play": "runnable demo > pitch", "why": "people share a thing they can try, not a claim",
     "how": "ship a one-command demo and a 60s 'watch it work' video on day one"},
    {"play": "build in public", "why": "the journey compounds attention and trust",
     "how": "weekly devlogs showing real progress, wins, and failures"},
    {"play": "show, don't tell", "why": "a live demo beats any adjective",
     "how": "screen-recorded product moments, no slides, real output on screen"},
    {"play": "a benchmark/leaderboard moment", "why": "a concrete number is inherently shareable",
     "how": "publish a reproducible benchmark and a chart that travels"},
    {"play": "developer-first distribution", "why": "devs adopt then evangelize",
     "how": "great README + Show HN / Product Hunt / dev communities, not ads"},
    {"play": "founder-led content", "why": "a face and a POV out-perform a logo",
     "how": "the founder narrates the why; opinions, not press releases"},
    {"play": "free + open core", "why": "zero-friction trial seeds the funnel",
     "how": "free/open tier that's genuinely useful; monetize the edges"},
    {"play": "name the category", "why": "owning the term frames every comparison",
     "how": "coin and repeat a crisp category line in every asset"},
]

# proven launch sequence: (day, play, format, platform)
_SEQUENCE = [
    (1, "runnable demo > pitch", "promotional", "youtube"),
    (1, "name the category", "promotional", "x"),
    (2, "show, don't tell", "devlog", "youtube_shorts"),
    (4, "developer-first distribution", "promotional", "linkedin"),
    (7, "build in public", "devlog", "youtube"),
    (10, "a benchmark/leaderboard moment", "video_essay", "x"),
    (14, "founder-led content", "documentary", "youtube"),
    (21, "build in public", "devlog", "youtube"),
    (28, "free + open core", "promotional", "linkedin"),
]


def growth_playbook() -> List[dict]:
    return GROWTH_PLAYS


def launch_strategy(name: str, topic: str = "", niche: str = "") -> dict:
    """A 30-day, play-by-play launch content calendar for a project."""
    topic = topic or name
    calendar = []
    for day, play, fmt, platform in _SEQUENCE:
        calendar.append({
            "day": day, "play": play, "format": fmt, "platform": platform,
            "title": _title_for(play, name, topic),
        })
    return {
        "project": name,
        "positioning": f"the open, runnable way to {topic.lower()}",
        "category_line": f"{name}: {niche or topic} you can run yourself",
        "channels": ["YouTube", "X", "LinkedIn", "Show HN", "Product Hunt", "dev communities"],
        "plays": GROWTH_PLAYS,
        "content_calendar": calendar,
        "north_star": "weekly shipped + weekly demo; let the runnable thing do the selling",
    }


def _title_for(play: str, name: str, topic: str) -> str:
    templates = {
        "runnable demo > pitch": f"I built {name} — watch it work in 60 seconds",
        "name the category": f"{name}: the open way to {topic.lower()}",
        "show, don't tell": f"{name} in action (no slides)",
        "developer-first distribution": f"Why we open-sourced {name}",
        "build in public": f"Building {name}: this week's progress",
        "a benchmark/leaderboard moment": f"{name} vs the alternatives — the numbers",
        "founder-led content": f"The real reason I built {name}",
        "free + open core": f"{name} is free and yours — here's how to start",
    }
    return templates.get(play, f"{name}: {topic}")
