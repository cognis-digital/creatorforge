"""Scenario 4 - the multi-platform publisher.

Audience: a team repurposing one idea across every channel without breaking each
platform's rules.

YouTube wants a 16:9 title + long description; X caps you at 280 characters;
TikTok/Reels are vertical, caption-and-hashtag driven; LinkedIn is a 1:1,
story-led first line. `package` takes ONE core idea and produces a ready-to-post
deliverable for each, respecting every limit — and the algorithm `playbook` tells
production exactly what each platform rewards. All offline and deterministic.
"""
from _common import rule, field, bullet, sample_voice

from creatorforge.hooks import write_hooks
from creatorforge.script import write_script
from creatorforge.platforms import PLATFORMS, package, platform_spec
from creatorforge.playbook import production_notes


def main() -> None:
    rule("MULTI-PLATFORM  -  one idea, tailored for every channel")

    voice = sample_voice()
    topic = "batch a month of content in one afternoon"
    hook = write_hooks(topic, voice, 1)[0]["hook"]
    script = write_script(topic, voice, "youtube")
    core = {"topic": topic, "hook": hook, "summary": script["intro"], "niche": "content systems"}

    print(f"\nCore idea:  {topic}")
    print(f"Hook:       {hook}\n")

    print("PACKAGED PER PLATFORM (every limit respected)\n")
    for name in PLATFORMS:
        spec = platform_spec(name)
        pkg = package(core, name, voice)
        cap = pkg["caption"]
        limit = spec["max_caption"]
        within = "ok" if (limit == 0 or len(cap) <= limit) else "OVER"
        field(name, f"{spec['aspect']:<5} ~{spec['ideal_seconds']}s  "
                    f"caption {len(cap)}/{limit or '∞'} [{within}]  tags={' '.join(pkg['hashtags'])}")

    print("\nX post (hard 280-char limit), in full:\n")
    x_caption = package(core, "x", voice)["caption"]
    print("   " + "\n   ".join(x_caption.splitlines()))
    print(f"   ({len(x_caption)} chars)")

    print("\nALGORITHM PLAYBOOK  -  what each surface actually rewards\n")
    for name in ("youtube_shorts", "tiktok", "linkedin"):
        notes = production_notes(name)
        bullet(f"{name:<15} hook by {notes['hook_must_land_by_s']}s, "
               f"re-hook every {notes['re_hook_every_s']}s — {notes['retention_tactics'][0]}")

    print("\nOne idea, six channels, every constraint honored — and tuned to each algorithm.")


if __name__ == "__main__":
    main()
