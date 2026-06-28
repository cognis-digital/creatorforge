"""The pipeline — one call that does what the agency's team does in a week.

Give it a topic, a niche, and your platforms; get back a research brief, a batch
of ideas, hooks, a full script for your primary platform, on-screen captions +
SRT, thumbnail concepts, per-platform packaged posts, and (optionally) a posting
calendar. Bring your voice profile and a model provider to make it sing.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from .captions import to_overlays, to_srt
from .calendar import build_calendar
from .hooks import write_hooks
from .ideas import FORMATS, generate_ideas
from .platforms import package
from .providers import Provider, TemplateProvider
from .script import write_script
from .thumbnails import thumbnail_concepts
from .voice import VoiceProfile


@dataclass
class ContentBrief:
    topic: str
    niche: str = ""
    audience: str = "people"
    goal: str = "grow reach and leads"
    platforms: List[str] = field(default_factory=lambda: ["youtube", "tiktok", "x"])
    n_ideas: int = 10
    n_hooks: int = 8
    start_date: Optional[str] = None   # "YYYY-MM-DD" enables the calendar
    per_week: int = 3
    weeks: int = 4


def _research_brief(brief: ContentBrief, voice: VoiceProfile) -> dict:
    niche = brief.niche or brief.topic
    keywords = voice.top_terms[:8] or [w for w in niche.split() if len(w) > 3]
    return {
        "niche": niche,
        "audience": brief.audience,
        "goal": brief.goal,
        "content_pillars": [f[0] for f in FORMATS[:5]],
        "audience_pains": [
            f"not enough time to make content about {niche}",
            f"unsure what {niche} content actually converts",
            f"inconsistent posting in {niche}",
        ],
        "keyword_targets": keywords,
        "suggested_cadence": f"{brief.per_week}x / week",
    }


def run_pipeline(brief: ContentBrief, voice: Optional[VoiceProfile] = None,
                 provider: Optional[Provider] = None) -> dict:
    voice = voice or VoiceProfile()
    provider = provider or TemplateProvider()
    primary = brief.platforms[0]

    research = _research_brief(brief, voice)
    idea_list = generate_ideas(brief.niche or brief.topic, voice, brief.n_ideas)
    hooks = write_hooks(brief.topic, voice, brief.n_hooks, audience=brief.audience)
    script = write_script(brief.topic, voice, primary, provider=provider)
    captions = {"overlays": to_overlays(script), "srt": to_srt(script)}
    thumbs = thumbnail_concepts(brief.topic, voice, 3)

    core = {"topic": brief.topic, "hook": hooks[0]["hook"],
            "summary": script["intro"], "niche": brief.niche or brief.topic}
    packages = {p: package(core, p, voice) for p in brief.platforms}

    calendar = (build_calendar(idea_list, brief.start_date, brief.per_week, brief.weeks)
                if brief.start_date else [])

    return {
        "brief": {"topic": brief.topic, "niche": brief.niche, "audience": brief.audience,
                  "goal": brief.goal, "platforms": brief.platforms},
        "voice": voice.style_brief(),
        "research_brief": research,
        "ideas": idea_list,
        "hooks": hooks,
        "script": script,
        "captions": captions,
        "thumbnails": thumbs,
        "packages": packages,
        "calendar": calendar,
        "provider": provider.name,
    }
