"""Scenario 3 - developer relations & marketing.

Audience: a devrel/marketing team launching an open-source project.

Point creatorforge at a repository and it writes the launch content *for* it —
reading the README to derive what the project is, then producing multi-platform
content plus a 30-day launch calendar modeled on how the AI companies that broke
out actually grew (runnable demo over pitch, build in public, name the category).
This demo reads a real local repo (creatorforge itself) — no network, no `gh`.
"""
import os

from _common import rule, field, bullet, sample_voice, REPO_ROOT

from creatorforge.repos import repo_meta, content_for_repo
from creatorforge.growth import growth_playbook, launch_strategy


def main() -> None:
    rule("DEVREL  -  point it at a repo, get the launch")

    voice = sample_voice()
    # use this very repository as the subject — a real local README, offline.
    spec = REPO_ROOT
    meta = repo_meta(spec)
    print(f"\nRead README of '{meta['name']}':\n")
    field("title", meta["title"])
    field("description", (meta["description"] or "")[:64] + "…")
    print("  features derived:")
    for f in meta["features"][:4]:
        bullet(f[:70])

    print("\nMULTI-PLATFORM LAUNCH CONTENT (promotional)\n")
    plan = content_for_repo(spec, fmt="promotional",
                            platforms=["youtube", "x", "linkedin"], voice=voice)
    field("topic", plan["brief"]["topic"][:60])
    field("hook", plan["hooks"][0]["hook"][:60])
    for p, pkg in plan["packages"].items():
        field(p, (pkg.get("title") or pkg["caption"])[:56])

    print("\nGROWTH PLAYBOOK  (how the AI breakouts actually grew)\n")
    for play in growth_playbook()[:4]:
        bullet(f"{play['play']:<28} — {play['why']}")

    print("\n30-DAY LAUNCH CALENDAR\n")
    strat = launch_strategy(meta["name"], topic=meta["title"], niche=meta["description"])
    field("category line", strat["category_line"][:62])
    for item in strat["content_calendar"][:6]:
        bullet(f"day {item['day']:<2} [{item['platform']:<14}] {item['title']}")

    print("\nA repo in -> posts, a script, and a play-by-play launch out. Ship the demo; let it sell.")


if __name__ == "__main__":
    main()
