"""Scenario 2 - the agency deliverable, owned.

Audience: a business owner weighing a five-figure "done-for-you content team."

This is the exact bundle an agency installs for a retainer — research brief,
idea pipeline, hooks, a primary script, captions + SRT, thumbnail concepts,
per-platform packaged posts, and a posting calendar — produced by a single
`run_pipeline` call. It runs on your hardware, in your voice, for free. When you
read this output, you're reading what you'd otherwise rent.
"""
from _common import rule, field, bullet, sample_voice

from creatorforge.pipeline import ContentBrief, run_pipeline


def main() -> None:
    rule("AGENCY DELIVERABLE  -  the whole content team, in one call")

    voice = sample_voice()
    brief = ContentBrief(
        topic="why you should own your AI content stack",
        niche="AI for small business",
        audience="founders",
        goal="grow reach and inbound leads",
        platforms=["youtube", "tiktok", "x", "linkedin"],
        n_ideas=6, n_hooks=5,
        start_date="2026-07-06", per_week=3, weeks=2,
    )
    plan = run_pipeline(brief, voice)

    print(f"\nProvider: {plan['provider']} (offline, deterministic)   Voice: {plan['voice'][:60]}…\n")

    rb = plan["research_brief"]
    print("RESEARCH BRIEF")
    field("audience / goal", f"{rb['audience']}  ->  {rb['goal']}")
    field("content pillars", ", ".join(rb["content_pillars"]))
    field("keyword targets", ", ".join(rb["keyword_targets"][:6]))

    print("\nIDEA PIPELINE")
    for i in plan["ideas"][:5]:
        bullet(f"[{i['format']:<14}] {i['title']}")

    print("\nHOOKS")
    for h in plan["hooks"][:4]:
        bullet(h["hook"])

    print("\nPRIMARY SCRIPT (youtube)")
    field("hook", plan["script"]["hook"])
    field("length", f"{plan['script']['word_count']} words, {len(plan['script']['beats'])} beats")
    field("overlays", " | ".join(plan["captions"]["overlays"][:3]) + " …")

    print("\nPER-PLATFORM PACKAGES")
    for p, pkg in plan["packages"].items():
        title = pkg.get("title") or "(no title field)"
        field(p, f"{pkg['aspect']}  tags={' '.join(pkg['hashtags'])}  | {title[:42]}")

    print("\nPOSTING CALENDAR")
    for slot in plan["calendar"]:
        bullet(f"{slot['date']} ({slot['weekday'][:3]})  {slot['platform']:<8}  {slot['title']}")

    print("\nThat is the agency bundle. No retainer, no cloud, no black box — you own it.")


if __name__ == "__main__":
    main()
