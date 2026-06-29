"""Post types — a mix of LinkedIn-ready formats, not just promos.

A healthy feed mixes formats: a whitepaper-style thesis, a case study, a data
report, a launch announcement, a straight promotion, a demo. Each is built to
LinkedIn's grammar (a strong first line — it's the preview — short paragraphs, a
few bullets, one CTA, a couple of hashtags), grounded in the repo's real summary
and features. Drop in a sharpened hook for the opening line and an optional model
to polish the body.
"""

from __future__ import annotations

from typing import List, Optional

POST_TYPES = ["whitepaper", "case_study", "report", "repo_announcement", "promotion",
              "demo", "expertise", "business"]


def _tags(name: str, extra=("AI", "OpenSource")) -> str:
    base = "".join(ch for ch in name if ch.isalnum())
    return " ".join("#" + t for t in ([base] + list(extra)))


def _bullets(features: List[str], k: int = 4) -> str:
    return "\n".join(f"• {f}" for f in features[:k]) if features else "• built to be small, readable, and yours"


def make_post(ptype: str, ctx: dict, hook: Optional[str] = None) -> dict:
    name = ctx.get("name", "this")
    summary = ctx.get("summary", "").strip()
    url = ctx.get("url", "")
    feats = ctx.get("features", [])
    tags = _tags(name)
    link = f"\n\n→ {url}" if url else ""

    if ptype == "whitepaper":
        text = (f"{hook or f'A short write-up on {name}.'}\n\n"
                f"The problem: most tools in this space make you trade control for capability.\n\n"
                f"The approach: {summary or name}.\n\n"
                f"Why it matters: it runs on infrastructure you own, with nothing sent to a vendor.\n\n"
                f"Full write-up + code:{link}\n\n{tags}")
    elif ptype == "case_study":
        text = (f"{hook or f'Case study: {name} in practice.'}\n\n"
                f"The challenge: teams need this capability but can't send their data to the cloud.\n\n"
                f"What we built: {summary or name}.\n\n"
                f"The result:\n{_bullets(feats)}\n\nRead how it works:{link}\n\n{tags}")
    elif ptype == "report":
        text = (f"{hook or f'{name}: what we found.'}\n\n"
                f"The headline: structure and provability beat raw scale for this problem.\n\n"
                f"What the work shows:\n{_bullets(feats)}\n\n"
                f"The implication: you can run this yourself, today.{link}\n\n{tags}")
    elif ptype == "repo_announcement":
        text = (f"{hook or f'Just shipped: {name}.'}\n\n{summary or name}\n\n"
                f"What it does:\n{_bullets(feats)}\n\n"
                f"Open source, dependency-light, runs on your hardware.{link}\n\n{tags}")
    elif ptype == "promotion":
        text = (f"{hook or f'You should look at {name}.'}\n\n{summary or name}\n\n"
                f"No vendor lock-in. No data leaving your machine. Free and open.\n\n"
                f"Start here:{link}\n\n{tags}")
    elif ptype == "demo":
        text = (f"{hook or f'Watch {name} work.'}\n\n"
                f"In under a minute: {summary or name}.\n\n{_bullets(feats, 3)}\n\n"
                f"Try it yourself:{link}\n\n{tags}")
    elif ptype == "expertise":
        text = (f"{hook or f'A lesson from building {name}.'}\n\n"
                f"The pattern I keep seeing: teams want this capability but can't hand their data to a "
                f"vendor to get it. So we built it to run on your own infrastructure.\n\n"
                f"What held up in practice:\n{_bullets(feats)}\n\n"
                f"If you're wrestling with the same trade-off, this is how we think about it.{link}\n\n{tags}")
    elif ptype == "business":
        text = (f"{hook or f'Why we built {name} at Cognis Digital.'}\n\n{summary or name}\n\n"
                f"We build accountable, owned AI tooling for teams that can't outsource trust — "
                f"regulated, high-stakes, security-first. Open by default; your hardware, your data.\n\n"
                f"If that's your world, let's talk.{link}\n\n{tags}")
    else:
        raise ValueError(f"unknown post type: {ptype}")
    return {"type": ptype, "name": name, "text": text.strip()}


def mixed_posts(ctx: dict, types: Optional[List[str]] = None,
                hook: Optional[str] = None) -> List[dict]:
    return [make_post(t, ctx, hook) for t in (types or POST_TYPES)]
