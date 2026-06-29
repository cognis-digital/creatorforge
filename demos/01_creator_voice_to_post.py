"""Scenario 1 - the solo creator.

Audience: a creator who films but dreads everything around the film.

The agency's first move is "we'll learn your voice." creatorforge does it in
front of you: it reads your past posts, measures the *style* that makes you
recognizable (no model training, nothing uploaded), then writes hooks, a full
script, on-screen captions, and timed SRT subtitles in that voice — from one
topic. You film; the engine did the rest. Fully offline.
"""
from _common import rule, field, bullet, sample_voice

from creatorforge.hooks import write_hooks
from creatorforge.script import write_script
from creatorforge.captions import to_overlays, to_srt


def main() -> None:
    rule("CREATOR  -  learn my voice, then write the whole piece")

    voice = sample_voice()
    print("\n1) Voice learned from your own past posts (measured, not trained):\n")
    field("samples / words", f"{voice.samples} posts, {voice.words} words")
    field("avg sentence", f"{voice.avg_sentence_len} words  (punchy={voice.punchy})")
    field("emoji / energetic", f"{voice.emoji_per_100w}/100w, energetic={voice.energetic}")
    field("style brief", voice.style_brief())

    topic = "the content system that beats burnout"
    print(f"\n2) Hooks for \"{topic}\" — in your voice:\n")
    for h in write_hooks(topic, voice, n=5):
        bullet(f"[{h['formula']:<16}] {h['hook']}")

    print("\n3) A full short-form script, sized to YouTube Shorts:\n")
    script = write_script(topic, voice, "youtube_shorts")
    field("hook", script["hook"])
    field("beats", str(len(script["beats"])))
    field("spoken length", f"{script['word_count']} words ≈ {script['est_seconds']}s")
    for b in script["beats"]:
        bullet(f"{b['point']}  ({b['broll']})")

    print("\n4) On-screen overlays + timed SRT subtitles, ready to upload:\n")
    for o in to_overlays(script):
        bullet(o)
    srt = to_srt(script)
    first_cue = "\n     ".join(srt.split("\n\n")[0].splitlines())
    print(f"\n   SRT (first cue):\n     {first_cue}")

    print("\nOne topic in -> hooks, script, captions, subtitles out. You film; the engine ships.")


if __name__ == "__main__":
    main()
