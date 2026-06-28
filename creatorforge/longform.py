"""Long-form production engine — 5–15 minute videos, structured like the pros.

Fuses four things into one production plan:

  * a **format** (documentary / video-essay / devlog / promo) for the beat order,
  * a **cinematic style** for pacing, shots, color, and music mood,
  * the **algorithm playbook** for the platform (hook timing, re-hooks, chapters),
  * your **voice** (and an optional local model to polish the narration).

It allocates the target runtime across beats, breaks each beat into timed shots,
writes narration to each shot's purpose, lays a music + SFX cue sheet, builds
chapters and pattern-interrupt markers, and proposes titles and thumbnails. The
plan is what a showrunner hands a crew — then `studio` assembles it with whatever
render models you have.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from . import camera, engagement, formats, playbook, styles
from .hooks import write_hooks
from .providers import Provider, TemplateProvider
from .thumbnails import thumbnail_concepts
from .voice import VoiceProfile

WPM = 150

# narration scaffolding keyed by the *role* of a beat (generic across topics)
_OPENERS = {
    "cold_open": "Picture this.", "hook": "Here's something most people miss.",
    "thesis": "This is really about one thing.", "premise": "Start from a simple idea.",
    "context": "To understand it, go back.", "recap": "Last time, we left off here.",
    "goal": "Today we're after one outcome.", "rising_action": "But it goes deeper.",
    "build": "So we get to work.", "evidence_1": "Consider the first piece.",
    "evidence_2": "Now the second.", "counterpoint": "Of course, there's another side.",
    "turn": "And then everything changes.", "obstacle": "That's when it broke.",
    "climax": "This is the moment it all turns on.", "breakthrough": "Then it clicked.",
    "synthesis": "Put it together and a pattern emerges.", "demo": "Watch it work.",
    "resolution": "So where does that leave us.", "conclusion": "Which brings us back to the start.",
    "proof": "And here's the proof.", "problem": "But there's a problem.",
    "agitate": "Left alone, it only gets worse.", "solution": "Here's the way through.",
    "offer": "Here's exactly what you get.", "outro": "If this resonated,",
    "next_steps": "Next episode,", "cta": "So here's your one move.",
}


@dataclass
class LongformBrief:
    topic: str
    format: str = "documentary"
    style: Optional[str] = None
    target_minutes: Optional[float] = None
    niche: str = ""
    audience: str = "people"
    platform: Optional[str] = None


def _narration(beat: str, purpose: str, topic: str, tone: str, seconds: float) -> str:
    budget = max(12, int(seconds * WPM / 60))
    opener = _OPENERS.get(beat, "Here's the thing.")
    base = [
        f"{opener}",
        f"When it comes to {topic}, {purpose}.",
        f"Most coverage of {topic} stops at the surface — we won't.",
        f"Stay with me, because this reframes how you see {topic}.",
    ]
    text = " ".join(base)
    # pad to roughly the word budget with on-purpose connective lines (tone-flavored)
    fillers = [
        f"Notice what's really happening with {topic} here.",
        f"That detail about {topic} matters more than it looks.",
        f"Hold that thought — it pays off.",
    ]
    i = 0
    while len(text.split()) < budget:
        text += " " + fillers[i % len(fillers)]
        i += 1
    return text


def _music_for(beat: str, mood: str) -> str:
    intensity = {"cold_open": "tease", "hook": "tease", "climax": "peak",
                 "turn": "rise", "breakthrough": "rise", "outro": "resolve",
                 "conclusion": "resolve", "cta": "button"}.get(beat, "bed")
    return f"{mood} — {intensity}"


def _sfx_for(beat: str) -> str:
    return {
        "cold_open": "ambience swell + low boom", "hook": "whoosh in",
        "climax": "impact hit + riser", "turn": "reverse cymbal",
        "breakthrough": "success chime", "demo": "UI clicks", "cta": "soft button",
        "outro": "tail-out reverb",
    }.get(beat, "subtle room tone")


def _chapter_label(beat: str, topic: str) -> str:
    return {
        "cold_open": f"The moment", "thesis": f"What this is really about",
        "context": "How we got here", "rising_action": "It gets deeper",
        "turn": "The twist", "climax": "The turning point",
        "resolution": "What it means", "outro": "Where to go next",
    }.get(beat, beat.replace("_", " ").title())


def build_longform(brief: LongformBrief, voice: Optional[VoiceProfile] = None,
                   provider: Optional[Provider] = None) -> dict:
    voice = voice or VoiceProfile()
    provider = provider or TemplateProvider()
    fmt = formats.get_format(brief.format)
    style_name = brief.style or fmt["default_style"]
    style = styles.get_style(style_name)
    minutes = brief.target_minutes or fmt["default_minutes"]
    platform = brief.platform or playbook.long_platform_for(brief.format)
    notes = playbook.production_notes(platform, brief.format)

    total_seconds = minutes * 60
    allocation = formats.allocate(fmt["beats"], total_seconds)
    scene_len = style["scene_seconds"]
    shot_vocab = style["shot_vocab"]

    scenes: List[dict] = []
    chapters: List[dict] = []
    cue_sheet: List[dict] = []
    t = 0.0
    for beat, purpose, seconds in allocation:
        n_shots = max(1, round(seconds / scene_len))
        shots = camera.coverage(beat, purpose, brief.topic, style, n_shots)
        narration = _narration(beat, purpose, brief.topic, style["narration_tone"], seconds)
        music = _music_for(beat, style["music_mood"])
        sfx = _sfx_for(beat)
        scenes.append({
            "beat": beat, "purpose": purpose, "seconds": seconds,
            "shots": shots, "retention_move": engagement.retention_move(beat),
            "narration": narration, "music_cue": music, "sfx": sfx,
        })
        chapters.append({"start_s": round(t), "label": _chapter_label(beat, brief.topic)})
        cue_sheet.append({"at_s": round(t), "music": music, "sfx": sfx})
        t += seconds

    # algorithm-aware retention markers
    interrupt = notes["re_hook_every_s"]
    pattern_interrupts = [round(s) for s in _frange(interrupt, total_seconds, interrupt)]

    titles = [h["hook"] for h in write_hooks(brief.topic, voice, 5, audience=brief.audience,
                                             provider=provider)]
    thumbs = thumbnail_concepts(brief.topic, voice, 3)

    narration_words = sum(len(s["narration"].split()) for s in scenes)
    plan = {
        "brief": {"topic": brief.topic, "format": brief.format, "style": style_name,
                  "platform": platform, "target_minutes": minutes, "niche": brief.niche},
        "style": {"name": style_name, **style},
        "production_notes": notes,
        "scenes": scenes,
        "chapters": chapters,
        "sound_cue_sheet": cue_sheet,
        "pattern_interrupts_s": pattern_interrupts,
        "title_options": titles,
        "thumbnail_concepts": thumbs,
        "engagement_plan": engagement.engagement_plan(brief.format, style_name),
        "multicam": camera.multicam_plan(scenes),
        "runtime_seconds": round(t),
        "narration_word_count": narration_words,
        "hook_lands_by_s": min(notes["hook_must_land_by_s"], scenes[0]["seconds"]) if scenes else 0,
        "provider": provider.name,
    }

    if getattr(provider, "available", False) and not isinstance(provider, TemplateProvider):
        full = "\n\n".join(f"[{s['beat']}] {s['narration']}" for s in scenes)
        plan["narration_polished"] = provider.rewrite(
            full, voice, instruction=f"Polish this {brief.format} narration in a {style['narration_tone']} tone:")
    return plan


def _frange(start, stop, step):
    x = start
    while x < stop:
        yield x
        x += step
