"""Captions — on-screen text overlays and timed subtitles (SRT).

`to_overlays` turns each script beat into a short punchy on-screen line; `to_srt`
times the full spoken track into standard SRT cues (by speaking pace), ready to
drop into any editor or upload as a subtitle track.
"""

from __future__ import annotations

from typing import List

WPM = 150


def spoken_lines(script: dict) -> List[str]:
    lines = [script.get("hook", ""), script.get("intro", "")]
    lines += [b.get("detail", "") for b in script.get("beats", [])]
    lines.append(script.get("cta", ""))
    return [ln for ln in lines if ln.strip()]


def to_overlays(script: dict, max_words: int = 6) -> List[str]:
    overlays = []
    for b in script.get("beats", []):
        words = b.get("point", "").split()
        overlays.append(" ".join(words[:max_words]).upper())
    return overlays


def _stamp(seconds: float) -> str:
    ms = int(round(seconds * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def to_srt(script: dict, wpm: int = WPM) -> str:
    cues = []
    t = 0.0
    for i, line in enumerate(spoken_lines(script), start=1):
        words = len(line.split())
        dur = max(1.2, words / wpm * 60)
        cues.append(f"{i}\n{_stamp(t)} --> {_stamp(t + dur)}\n{line}\n")
        t += dur
    return "\n".join(cues)
