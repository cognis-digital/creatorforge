"""creatorforge command line.

    creatorforge profile  ./my_posts/ --out voice.json
    creatorforge ideas    --niche "real estate" --voice voice.json -n 10
    creatorforge hooks    --topic "first-time home buyers" --voice voice.json
    creatorforge script   --topic "..." --platform youtube --provider ollama --model llama3
    creatorforge package  --topic "..." --niche "..." --platforms youtube,tiktok,x
    creatorforge calendar --niche "..." --start 2026-07-01 --per-week 3 --weeks 4
    creatorforge thumbnail --topic "..." --svg out      # writes out-1.svg, out-2.svg, ...
    creatorforge pipeline --topic "..." --niche "..." --platforms youtube,tiktok,x --out plan.json
    creatorforge serve                                   # MCP server over stdio
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

from . import __version__, audio as _audio, transcribe as _transcribe, tts as _tts
from .calendar import build_calendar
from .capabilities import capabilities
from .hooks import write_hooks
from .ideas import generate_ideas
from .images import generate_thumbnail, get_image_backend
from .pipeline import ContentBrief, run_pipeline
from .platforms import package
from .providers import get_provider
from .publish import to_outbox
from .script import write_script
from .thumbnails import render_svg, thumbnail_concepts
from .video import render as render_video, storyboard
from .voice import VoiceProfile, analyze


def _print(obj) -> None:
    print(json.dumps(obj, indent=2, default=str))


def _voice(args) -> VoiceProfile:
    path = getattr(args, "voice", None)
    return VoiceProfile.load(path) if path else VoiceProfile()


def _provider(args):
    name = getattr(args, "provider", None) or "template"
    if name == "ollama":
        return get_provider("ollama", model=getattr(args, "model", "llama3"))
    return get_provider(name)


def _read_corpus(paths) -> list:
    texts = []
    for p in paths:
        path = Path(p)
        files = sorted(path.rglob("*")) if path.is_dir() else [path]
        for f in files:
            if f.is_file() and f.suffix.lower() in (".txt", ".md", ""):
                try:
                    texts.append(f.read_text(encoding="utf-8", errors="replace"))
                except OSError:
                    pass
    return texts


def cmd_profile(args) -> int:
    texts = _read_corpus(args.paths)
    profile = analyze(texts)
    if args.out:
        profile.save(args.out)
    _print({"samples": profile.samples, "style": profile.style_brief(),
            "out": args.out, "profile": profile.to_dict()})
    return 0


def cmd_ideas(args) -> int:
    _print({"ideas": generate_ideas(args.niche, _voice(args), args.n)})
    return 0


def cmd_hooks(args) -> int:
    _print({"hooks": write_hooks(args.topic, _voice(args), args.n, audience=args.audience)})
    return 0


def cmd_script(args) -> int:
    _print({"script": write_script(args.topic, _voice(args), args.platform,
                                    provider=_provider(args))})
    return 0


def cmd_package(args) -> int:
    voice = _voice(args)
    hook = write_hooks(args.topic, voice, 1)[0]["hook"]
    core = {"topic": args.topic, "hook": hook, "summary": "", "niche": args.niche or args.topic}
    out = {p: package(core, p, voice) for p in args.platforms.split(",")}
    _print({"packages": out})
    return 0


def cmd_calendar(args) -> int:
    ideas = generate_ideas(args.niche, _voice(args), args.n)
    _print({"calendar": build_calendar(ideas, args.start, args.per_week, args.weeks)})
    return 0


def cmd_thumbnail(args) -> int:
    voice = _voice(args)
    concepts = thumbnail_concepts(args.topic, voice, args.n)
    written = []
    if args.svg:
        for i, c in enumerate(concepts, 1):
            path = f"{args.svg}-{i}.svg"
            Path(path).write_text(render_svg(c), encoding="utf-8")
            written.append(path)
    _print({"concepts": concepts, "svg_written": written})
    return 0


def cmd_pipeline(args) -> int:
    brief = ContentBrief(
        topic=args.topic, niche=args.niche, audience=args.audience,
        platforms=args.platforms.split(","), start_date=args.start,
        per_week=args.per_week, weeks=args.weeks,
    )
    result = run_pipeline(brief, _voice(args), _provider(args))
    if args.out:
        Path(args.out).write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
    _print({"out": args.out, "summary": {
        "ideas": len(result["ideas"]), "hooks": len(result["hooks"]),
        "platforms": list(result["packages"]), "calendar_slots": len(result["calendar"]),
        "provider": result["provider"]}})
    return 0


def cmd_capabilities(args) -> int:
    _print(capabilities())
    return 0


def cmd_transcribe(args) -> int:
    _print(_transcribe.transcribe(args.audio, model=args.model))
    return 0


def cmd_voiceover(args) -> int:
    text = args.text
    if args.from_script:
        with open(args.from_script, encoding="utf-8") as fh:
            s = json.load(fh)
        s = s.get("script", s)
        from .captions import spoken_lines
        text = " ".join(spoken_lines(s))
    out = _tts.synthesize(text, args.out, backend=args.backend,
                          voice_model=args.voice_model, speaker_wav=args.speaker)
    _print(out)
    return 0


def cmd_image(args) -> int:
    concept = thumbnail_concepts(args.topic, _voice(args), 1)[0]
    backend = None if args.backend == "auto" else get_image_backend(args.backend)
    _print(generate_thumbnail(concept, args.out, backend=backend))
    return 0


def cmd_video(args) -> int:
    script = write_script(args.topic, _voice(args), args.platform, provider=_provider(args))
    out = render_video(storyboard(script), args.out, audio_path=args.audio, backend=args.backend)
    _print(out)
    return 0


def cmd_audio(args) -> int:
    _print(_audio.produce(args.out, voiceover=args.voiceover, music=args.music,
                          seconds=args.seconds, backend=args.backend))
    return 0


def cmd_produce(args) -> int:
    from pathlib import Path
    voice = _voice(args)
    brief = ContentBrief(topic=args.topic, niche=args.niche, audience=args.audience,
                         platforms=args.platforms.split(","))
    result = run_pipeline(brief, voice, _provider(args))
    outdir = Path(args.out)
    outdir.mkdir(parents=True, exist_ok=True)

    assets = {}
    assets["thumbnail"] = generate_thumbnail(result["thumbnails"][0], str(outdir / "thumbnail"))
    assets["video"] = render_video(storyboard(result["script"]), str(outdir / "short"))
    assets["audio"] = _audio.produce(str(outdir / "track"),
                                     seconds=result["script"]["est_seconds"])
    assets["outbox"] = to_outbox(result["packages"], str(outdir / "outbox"))
    (outdir / "plan.json").write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")

    _print({"outdir": str(outdir), "assets": {
        "thumbnail": assets["thumbnail"], "video": assets["video"],
        "audio": assets["audio"], "outbox_files": len(assets["outbox"]),
        "plan": str(outdir / "plan.json")}})
    return 0


def cmd_serve(args) -> int:
    from .mcp_server import MCPServer
    print("creatorforge MCP server over stdio", file=sys.stderr)
    MCPServer().serve_forever()
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="creatorforge", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--version", action="version", version=f"creatorforge {__version__}")
    sub = p.add_subparsers(dest="cmd", required=True)

    pp = sub.add_parser("profile", help="learn a voice profile from a corpus")
    pp.add_argument("paths", nargs="+")
    pp.add_argument("--out", default=None)
    pp.set_defaults(func=cmd_profile)

    pi = sub.add_parser("ideas", help="generate content ideas")
    pi.add_argument("--niche", required=True); pi.add_argument("--voice"); pi.add_argument("-n", type=int, default=10)
    pi.set_defaults(func=cmd_ideas)

    ph = sub.add_parser("hooks", help="write hooks for a topic")
    ph.add_argument("--topic", required=True); ph.add_argument("--voice"); ph.add_argument("-n", type=int, default=8)
    ph.add_argument("--audience", default="people")
    ph.set_defaults(func=cmd_hooks)

    ps = sub.add_parser("script", help="write a platform script")
    ps.add_argument("--topic", required=True); ps.add_argument("--voice")
    ps.add_argument("--platform", default="youtube")
    ps.add_argument("--provider", default="template"); ps.add_argument("--model", default="llama3")
    ps.set_defaults(func=cmd_script)

    pk = sub.add_parser("package", help="package a topic for multiple platforms")
    pk.add_argument("--topic", required=True); pk.add_argument("--niche", default=""); pk.add_argument("--voice")
    pk.add_argument("--platforms", default="youtube,tiktok,x")
    pk.set_defaults(func=cmd_package)

    pc = sub.add_parser("calendar", help="build a posting calendar")
    pc.add_argument("--niche", required=True); pc.add_argument("--voice"); pc.add_argument("-n", type=int, default=12)
    pc.add_argument("--start", required=True); pc.add_argument("--per-week", dest="per_week", type=int, default=3)
    pc.add_argument("--weeks", type=int, default=4)
    pc.set_defaults(func=cmd_calendar)

    pt = sub.add_parser("thumbnail", help="thumbnail concepts (+ optional SVG render)")
    pt.add_argument("--topic", required=True); pt.add_argument("--voice"); pt.add_argument("-n", type=int, default=3)
    pt.add_argument("--svg", default=None, help="path prefix to write SVG mockups")
    pt.set_defaults(func=cmd_thumbnail)

    pl = sub.add_parser("pipeline", help="run the full content pipeline")
    pl.add_argument("--topic", required=True); pl.add_argument("--niche", default=""); pl.add_argument("--voice")
    pl.add_argument("--audience", default="people")
    pl.add_argument("--platforms", default="youtube,tiktok,x")
    pl.add_argument("--provider", default="template"); pl.add_argument("--model", default="llama3")
    pl.add_argument("--start", default=None); pl.add_argument("--per-week", dest="per_week", type=int, default=3)
    pl.add_argument("--weeks", type=int, default=4)
    pl.add_argument("--out", default=None)
    pl.set_defaults(func=cmd_pipeline)

    sub.add_parser("capabilities", help="report which local models/backends are available")\
        .set_defaults(func=cmd_capabilities)

    ptr = sub.add_parser("transcribe", help="transcribe audio/video with local Whisper")
    ptr.add_argument("audio"); ptr.add_argument("--model", default=None)
    ptr.set_defaults(func=cmd_transcribe)

    pvo = sub.add_parser("voiceover", help="synthesize a voiceover (local TTS)")
    pvo.add_argument("--text", default=""); pvo.add_argument("--from-script", dest="from_script")
    pvo.add_argument("--out", required=True)
    pvo.add_argument("--backend", default="auto", choices=["auto", "piper", "xtts"])
    pvo.add_argument("--voice-model", dest="voice_model"); pvo.add_argument("--speaker")
    pvo.set_defaults(func=cmd_voiceover)

    pim = sub.add_parser("image", help="generate a thumbnail image (diffusion/raster/svg)")
    pim.add_argument("--topic", required=True); pim.add_argument("--voice"); pim.add_argument("--out", required=True)
    pim.add_argument("--backend", default="auto", choices=["auto", "automatic1111", "diffusers"])
    pim.set_defaults(func=cmd_image)

    pvi = sub.add_parser("video", help="produce a short video from a script")
    pvi.add_argument("--topic", required=True); pvi.add_argument("--voice"); pvi.add_argument("--out", required=True)
    pvi.add_argument("--platform", default="youtube_shorts")
    pvi.add_argument("--provider", default="template"); pvi.add_argument("--model", default="auto")
    pvi.add_argument("--audio", default=None)
    pvi.add_argument("--backend", default="auto", choices=["auto", "ffmpeg", "gif"])
    pvi.set_defaults(func=cmd_video)

    pau = sub.add_parser("audio", help="produce an audio track (voiceover + music)")
    pau.add_argument("--out", required=True); pau.add_argument("--voiceover"); pau.add_argument("--music")
    pau.add_argument("--seconds", type=float, default=8.0)
    pau.add_argument("--backend", default="auto", choices=["auto", "ffmpeg", "wave"])
    pau.set_defaults(func=cmd_audio)

    ppr = sub.add_parser("produce", help="full production: plan + thumbnail + video + audio + outbox")
    ppr.add_argument("--topic", required=True); ppr.add_argument("--niche", default=""); ppr.add_argument("--voice")
    ppr.add_argument("--audience", default="people")
    ppr.add_argument("--platforms", default="youtube,tiktok,x")
    ppr.add_argument("--provider", default="template"); ppr.add_argument("--model", default="auto")
    ppr.add_argument("--out", default="production")
    ppr.set_defaults(func=cmd_produce)

    sub.add_parser("serve", help="serve the engine to agents over MCP (stdio)").set_defaults(func=cmd_serve)
    return p


def main(argv=None) -> int:
    try:  # emoji-safe output on legacy (cp1252) consoles
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
