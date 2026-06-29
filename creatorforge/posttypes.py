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
              "demo", "expertise", "business", "comparison", "thread", "lesson"]


def _tags(name: str, extra=("AI", "OpenSource")) -> str:
    base = "".join(ch for ch in name if ch.isalnum())
    return " ".join("#" + t for t in ([base] + list(extra)))


def _bullets(features: List[str], k: int = 4) -> str:
    return "\n".join(f"• {f}" for f in features[:k]) if features else "• built to be small, readable, and yours"


def make_post(ptype: str, ctx: dict, hook: Optional[str] = None) -> dict:
    name = ctx.get("name", "this")
    summary = ctx.get("summary", "").strip().rstrip(".").strip()
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
    elif ptype == "comparison":
        text = (f"{hook or f'{name}: owned vs. rented.'}\n\n"
                f"The usual trade: hand your data to a vendor to get the capability.\n\n"
                f"{name} takes the other path — {summary or name}:\n"
                f"• Runs on infrastructure you own\n"
                f"• Nothing sent to a third party\n"
                f"• Open source, inspectable, yours\n\n"
                f"Same capability. None of the lock-in.{link}\n\n{tags}")
    elif ptype == "thread":
        text = (f"{hook or f'A short thread on {name}. 🧵'}\n\n"
                f"1/ The problem: {summary or name}\n\n"
                f"2/ Why it's hard: most tools make you choose between control and capability.\n\n"
                f"3/ The approach:\n{_bullets(feats, 3)}\n\n"
                f"4/ The result: it runs on your hardware, with a clear audit trail.\n\n"
                f"5/ It's open source — start here:{link}\n\n{tags}")
    elif ptype == "lesson":
        text = (f"{hook or f'What building {name} taught us.'}\n\n"
                f"Teams keep hitting the same wall: they need this capability but can't "
                f"send their data to a vendor to get it.\n\n"
                f"So the design constraint became the feature: build it to run locally, "
                f"prove what it did, and keep it open.\n\n{_bullets(feats, 3)}\n\n"
                f"If you're wrestling with the same trade-off:{link}\n\n{tags}")
    else:
        raise ValueError(f"unknown post type: {ptype}")
    return {"type": ptype, "name": name, "text": text.strip()}


def suite_posts() -> List[dict]:
    """Cross-cutting, suite-level thought-leadership posts (not tied to one repo)."""
    tags = "#AccountableAI #OpenSource #AIEngineering"
    url = "https://github.com/cognis-digital"
    posts = [
        ("manifesto", "The next decade of AI tooling belongs to whoever owns the stack.",
         "Rented intelligence is convenient until the day it isn't — the price changes, "
         "the model changes, your data is somewhere you can't see.\n\n"
         "We build the other kind: accountable, owned AI tooling that runs on your "
         "infrastructure and can prove what it did. Code graphs, signed ledgers, policy "
         "governance, repo guards — all open, all yours."),
        ("category", "\"Accountable AI engineering\" isn't a feature. It's a category.",
         "Five open tools, one principle: you should be able to run your AI stack, "
         "inspect it, and prove what it did to a regulator — without sending a byte to a "
         "vendor. That's the suite we're building at Cognis Digital."),
        ("founder", "Why we open-sourced the whole accountable-AI suite.",
         "Trust you can't inspect isn't trust. So we made the tooling open: read the code, "
         "run it on your own hardware, verify the audit chain yourself. If your world is "
         "regulated, high-stakes, security-first — this was built for you."),
    ]
    out = []
    for slug, hook, body in posts:
        out.append({"type": f"suite_{slug}", "name": "suite",
                    "text": f"{hook}\n\n{body}\n\n→ {url}\n\n{tags}"})
    return out


def mixed_posts(ctx: dict, types: Optional[List[str]] = None,
                hook: Optional[str] = None) -> List[dict]:
    return [make_post(t, ctx, hook) for t in (types or POST_TYPES)]
