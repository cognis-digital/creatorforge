"""Engagement craft — the techniques great filmmakers and top creators use to keep
you watching, encoded as production moves.

Two lineages, both as *technique* (not impersonation):

  * **Filmmaker grammar** — in-media-res openings, the "but/therefore" causal
    chain, show-don't-tell, escalating stakes, tension-and-release, the match
    cut, motivated camera moves, the Kuleshov effect.
  * **Modern retention** (MrBeast-style) — front-load the payoff, escalate every
    segment, reset the hook on a cadence, concrete stakes/numbers, no dead air,
    constantly tease what's coming, pay off the emotion.

`engagement_plan` turns these into per-beat retention moves the long-form engine
applies, so structure isn't just correct — it's *sticky*.
"""

from __future__ import annotations

FILMMAKER_TECHNIQUES = [
    ("in_media_res", "Open in the middle of the action, not the setup."),
    ("but_therefore", "Link beats with 'but/therefore', never 'and then' — keep causality."),
    ("show_dont_tell", "Reveal through visuals and action, not narration alone."),
    ("escalating_stakes", "Raise what's at risk with each act."),
    ("tension_release", "Build pressure, then release it — then build again."),
    ("match_cut", "Cut on a visual/idea rhyme to feel seamless."),
    ("motivated_moves", "Every camera move has a reason (reveal, emphasis, unease)."),
    ("kuleshov", "Juxtapose shots so meaning emerges from the edit."),
]

# well-documented modern retention tactics (MrBeast-style)
RETENTION_TACTICS = [
    ("front_load_payoff", "Show the most compelling moment in the first seconds."),
    ("escalate", "Make every segment bigger/higher-stakes than the last."),
    ("reset_hook", "Re-hook on a cadence — a new question/visual/stake every ~30-40s."),
    ("concrete_stakes", "Use specific numbers and clear, visible stakes."),
    ("no_dead_air", "Cut anything that doesn't move the story forward."),
    ("tease_ahead", "Constantly promise what's coming ('but it gets crazier…')."),
    ("emotional_payoff", "Land an emotional beat, not just information."),
    ("pattern_interrupt", "Change location/pace/visual to reset attention."),
]

# the retention move to deploy at each beat role
_BEAT_MOVE = {
    "cold_open": "front_load_payoff + open loop you close at the end",
    "hook": "front_load_payoff + concrete stake",
    "thesis": "concrete_stakes — name the number / what's at risk",
    "context": "but_therefore — make it causal, not a list",
    "premise": "tease_ahead — promise the payoff",
    "rising_action": "escalate — raise the stakes",
    "build": "escalate + no_dead_air montage",
    "evidence_1": "show_dont_tell",
    "evidence_2": "escalate over evidence_1",
    "counterpoint": "tension_release — steelman then resolve",
    "turn": "pattern_interrupt + reveal (biggest re-hook)",
    "obstacle": "tension — make failure feel real",
    "climax": "emotional_payoff — the biggest moment",
    "breakthrough": "release — pay off the tension",
    "synthesis": "match_cut back to the opening idea",
    "demo": "show_dont_tell — let it play",
    "proof": "concrete_stakes — receipts",
    "resolution": "emotional_payoff — what it means",
    "conclusion": "close the open loop from the cold open",
    "offer": "concrete_stakes — exactly what they get",
    "outro": "tease_ahead — the next video",
    "next_steps": "tease_ahead",
    "cta": "one clear action, no menu",
}


def retention_move(beat: str) -> str:
    return _BEAT_MOVE.get(beat, "reset_hook — keep momentum")


def engagement_plan(fmt: str, style: str) -> dict:
    return {
        "filmmaker_techniques": [{"name": n, "technique": t} for n, t in FILMMAKER_TECHNIQUES],
        "retention_tactics": [{"name": n, "tactic": t} for n, t in RETENTION_TACTICS],
        "principles": [
            "Earn the next second of attention, always.",
            "Open loops early; close them late.",
            "Escalate — never plateau.",
            "Cut on causality (but/therefore), not chronology (and then).",
        ],
        "format": fmt,
        "style": style,
    }
