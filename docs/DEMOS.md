# Demos

Five runnable scenarios in [`../demos/`](../demos/), each targeting a different
audience. Every scenario runs **fully offline** — no network, no GPU, no model
download — on the deterministic engine and the default `TemplateProvider`, so you
can run them in any order or on their own, and they double as smoke tests.

```bash
# cp1252 consoles (Windows): PYTHONUTF8=1 makes the emoji/ALLCAPS output render
PYTHONUTF8=1 python demos/run_all.py            # all five, end to end
PYTHONUTF8=1 python demos/02_agency_full_pipeline.py   # or just one
```

| # | Scenario | Audience | What it shows |
|---|----------|----------|---------------|
| 1 | [`01_creator_voice_to_post.py`](../demos/01_creator_voice_to_post.py) | Solo creators | Learn a voice from past posts, then write hooks, a full script, on-screen overlays, and timed SRT subtitles in that voice. |
| 2 | [`02_agency_full_pipeline.py`](../demos/02_agency_full_pipeline.py) | Business owners | The whole agency bundle from one `run_pipeline` call — research brief, ideas, hooks, script, captions, per-platform packages, and a posting calendar. |
| 3 | [`03_devrel_repo_launch.py`](../demos/03_devrel_repo_launch.py) | DevRel & marketing | Point it at a repo (reads the README, offline), get multi-platform launch content plus a 30-day launch calendar modeled on the AI breakouts. |
| 4 | [`04_multiplatform_repurpose.py`](../demos/04_multiplatform_repurpose.py) | Multi-platform publishers | One idea packaged for all six channels with every caption/length limit honored, plus the algorithm playbook per surface. |
| 5 | [`05_longform_studio.py`](../demos/05_longform_studio.py) | Long-form showrunners | A 12-minute documentary plan: timed scenes, multi-camera shot lists, per-beat retention moves, narration, chapters, and titles. |

## 1. Creator — *learn my voice, then write the whole piece*
**Audience:** creators who film but dread everything around it.
The agency's first move is "we'll learn your voice." This does it in front of
you: it measures the style features that make you recognizable (no training,
nothing uploaded), then writes hooks, a script, overlays, and SRT in that voice.

## 2. Agency deliverable — *the whole content team, in one call*
**Audience:** owners weighing a five-figure "done-for-you" retainer.
`run_pipeline` produces the exact bundle an agency installs — research brief,
idea pipeline, hooks, primary script, captions, per-platform packages, and a
dated posting calendar — on your hardware, in your voice, for free.

## 3. DevRel — *point it at a repo, get the launch*
**Audience:** teams launching an open-source project.
It reads a real local README (this repo, offline), derives what the project is,
and produces multi-platform launch content plus a 30-day calendar built on the
plays the AI breakouts actually used (runnable demo over pitch, build in public,
name the category).

## 4. Multi-platform — *one idea, tailored for every channel*
**Audience:** publishers repurposing across surfaces.
One core idea becomes a YouTube long description, a 280-char X post, vertical
TikTok/Reels captions, and a LinkedIn first-line hook — every limit respected —
with the algorithm playbook telling production what each surface rewards.

## 5. Long-form studio — *structured like the pros*
**Audience:** documentary / video-essay / devlog producers.
Format × cinematic style × algorithm playbook × voice, allocated across a
12-minute runtime into timed scenes with multi-camera shot lists, per-beat
retention moves, narration, a cue sheet, chapters, titles, and thumbnails — no
render models required.

---

Each demo prints clear, narrated output and exits 0, so they double as smoke
tests — `tests/` covers the same code paths under `pytest`.
