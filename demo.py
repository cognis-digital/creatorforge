#!/usr/bin/env python3
"""End-to-end demo: learn a voice, then run the full content pipeline.

    python demo.py
"""

import sys
from pathlib import Path

try:  # emoji-safe output on legacy (cp1252) consoles
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

from creatorforge import analyze, run_pipeline
from creatorforge.pipeline import ContentBrief

CORPUS = Path(__file__).resolve().parent / "examples" / "sample_corpus"


def main() -> None:
    voice = analyze([f.read_text(encoding="utf-8") for f in CORPUS.glob("*.txt")])
    print("== learned voice ==")
    print(" ", voice.style_brief(), "\n")

    brief = ContentBrief(topic="why you should own your AI stack",
                         niche="AI for business", audience="founders",
                         platforms=["youtube", "tiktok", "x", "linkedin"],
                         start_date="2026-07-06")
    out = run_pipeline(brief, voice)

    print("== top hooks ==")
    for h in out["hooks"][:3]:
        print(f"  [{h['formula']}] {h['hook']}")

    print("\n== ideas ==")
    for i in out["ideas"][:3]:
        print(f"  {i['title']}  ({i['format']} · {', '.join(i['platforms'][:2])})")

    print("\n== script (primary platform) ==")
    s = out["script"]
    print(f"  {s['platform']}: {len(s['beats'])} beats, ~{s['est_seconds']}s")

    print("\n== packaged for ==", ", ".join(out["packages"]))
    print("== calendar slots ==", len(out["calendar"]),
          "starting", out["calendar"][0]["date"] if out["calendar"] else "-")
    print("\nProvider:", out["provider"], "(plug in Ollama or a cloud model to sharpen the prose)")


if __name__ == "__main__":
    main()
