"""Scenario 5 - the long-form showrunner.

Audience: creators producing 5-15 minute documentaries, video essays, or devlogs.

Short clips are one mode. creatorforge also plans long-form the way the industry
does: a format (beat order) x a cinematic style (pacing, shots, color, music) x
the platform algorithm playbook x your voice — allocated across the runtime into
timed scenes with multi-camera shot lists, per-beat retention moves, narration, a
music/SFX cue sheet, chapters, titles, and thumbnails. The plan a showrunner hands
a crew — generated offline, no render models required.
"""
from _common import rule, field, bullet, sample_voice

from creatorforge.longform import LongformBrief, build_longform


def main() -> None:
    rule("LONG-FORM STUDIO  -  a 12-minute documentary plan, structured like the pros")

    voice = sample_voice()
    brief = LongformBrief(
        topic="owning your AI content stack",
        format="documentary", style="epic_doc",
        target_minutes=12, niche="independent AI", audience="builders",
    )
    plan = build_longform(brief, voice)

    b = plan["brief"]
    print(f"\n{b['format']} / {b['style']} on {b['platform']} — "
          f"target {b['target_minutes']} min, built to {plan['runtime_seconds']}s\n")
    field("narration", f"{plan['narration_word_count']} words")
    field("hook lands by", f"{plan['hook_lands_by_s']}s")
    field("pattern interrupts", ", ".join(f"{s}s" for s in plan["pattern_interrupts_s"][:6]) + " …")
    field("cameras needed", ", ".join(plan["multicam"]["cameras_needed"]))
    field("signature shots", str(plan["multicam"]["signature_shots"]))

    print("\nSCENES (beat -> seconds, retention move, shots)\n")
    for s in plan["scenes"]:
        bullet(f"{s['beat']:<14} {s['seconds']:>5}s  [{s['retention_move'][:32]:<32}]  "
               f"{len(s['shots'])} shot(s)")
    # one scene's shot list, in detail
    cold = plan["scenes"][0]
    print(f"\n   '{cold['beat']}' shot list:")
    for shot in cold["shots"][:3]:
        print(f"       {shot['cam']:<8} {shot['move']:<14} {shot['description'][:46]}")
    print(f"   narration: \"{cold['narration'][:70]}…\"")

    print("\nCHAPTERS")
    for ch in plan["chapters"][:5]:
        bullet(f"{ch['start_s']:>4}s  {ch['label']}")

    print("\nTITLE OPTIONS")
    for t in plan["title_options"][:3]:
        bullet(t)

    print("\nA studio-grade plan — structure, coverage, pacing, sound — on a laptop, offline.")


if __name__ == "__main__":
    main()
