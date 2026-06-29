"""Video production — assemble a finished short from a script.

Two production paths, by what your machine has:

  * **ffmpeg** → a real MP4 (vertical 9:16), caption frames timed to the script,
    optional voiceover/music muxed in. The standard, shareable output.
  * **PIL** → an animated video (GIF/WebP) of the caption frames when ffmpeg
    isn't installed — silent, but a genuine moving file you can preview.

And for those with the GPU for it, `text2video_backend()` detects a local
open text-to-video model (LTX-Video / CogVideoX via ComfyUI or diffusers) for
true generated b-roll; without it, we assemble from frames — which runs anywhere.
"""

from __future__ import annotations

from typing import List, Optional

from .captions import to_overlays
from .hardware import ffmpeg_exe
from .images import _font, _pil_available

_PALETTE = {"bg": "#0E1517", "accent": "#F4B400", "text": "#FFFFFF"}


def storyboard(script: dict) -> List[dict]:
    """A list of {text, seconds} caption frames derived from the script."""
    frames = [{"text": script.get("hook", ""), "seconds": 3.0, "role": "hook"}]
    overlays = to_overlays(script)
    beats = script.get("beats", [])
    for i, b in enumerate(beats):
        text = overlays[i] if i < len(overlays) else b.get("point", "")
        words = len(b.get("detail", "").split())
        frames.append({"text": text, "seconds": max(2.0, round(words / 2.5, 1)), "role": "beat"})
    frames.append({"text": script.get("cta", ""), "seconds": 2.5, "role": "cta"})
    return [f for f in frames if f["text"].strip()]


def _render_frame(text: str, size, role: str = "beat"):
    from PIL import Image, ImageDraw
    from .thumbnails import _wrap

    w, h = size
    img = Image.new("RGB", (w, h), _PALETTE["bg"])
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, w, 12], fill=_PALETTE["accent"])
    d.rectangle([0, h - 12, w, h], fill=_PALETTE["accent"])
    lines = _wrap(text, per_line=14)
    fs = max(48, min(120, int(w / 9)))
    font = _font(fs)
    total_h = len(lines) * fs
    y = (h - total_h) // 2
    for ln in lines:
        bbox = d.textbbox((0, 0), ln, font=font)
        tw = bbox[2] - bbox[0]
        color = _PALETTE["accent"] if role == "hook" else _PALETTE["text"]
        d.text(((w - tw) // 2, y), ln, fill=color, font=font)
        y += fs
    return img


def _render_gif(frames, out_path, size) -> dict:
    imgs = [_render_frame(f["text"], size, f.get("role", "beat")) for f in frames]
    durations = [int(f["seconds"] * 1000) for f in frames]
    path = out_path if out_path.endswith(".gif") else out_path + ".gif"
    imgs[0].save(path, save_all=True, append_images=imgs[1:], duration=durations,
                 loop=0, optimize=True)
    return {"path": path, "backend": "pil-gif", "frames": len(imgs),
            "seconds": round(sum(f["seconds"] for f in frames), 1)}


def _render_ffmpeg(frames, out_path, size, fps, audio_path) -> dict:
    import subprocess
    import tempfile
    from pathlib import Path

    path = out_path if out_path.endswith(".mp4") else out_path + ".mp4"
    with tempfile.TemporaryDirectory(prefix="cf-vid-") as tmp:
        listing = []
        for i, f in enumerate(frames):
            img = _render_frame(f["text"], size, f.get("role", "beat"))
            p = Path(tmp) / f"f{i:03d}.png"
            img.save(p)
            listing.append(f"file '{p.as_posix()}'\nduration {f['seconds']}")
        listing.append(f"file '{(Path(tmp) / f'f{len(frames)-1:03d}.png').as_posix()}'")
        concat = Path(tmp) / "list.txt"
        concat.write_text("\n".join(listing), encoding="utf-8")

        cmd = [ffmpeg_exe(), "-y", "-f", "concat", "-safe", "0", "-i", str(concat)]
        if audio_path:
            cmd += ["-i", audio_path, "-shortest"]
        cmd += ["-vf", f"scale={size[0]}:{size[1]},format=yuv420p", "-r", str(fps), path]
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    return {"path": path, "backend": "ffmpeg", "frames": len(frames),
            "seconds": round(sum(f["seconds"] for f in frames), 1)}


def render(frames: List[dict], out_path: str, *, size=(1080, 1920), fps: int = 24,
           audio_path: Optional[str] = None, backend: str = "auto") -> dict:
    """Render a storyboard to a finished short. backend: auto | ffmpeg | gif."""
    if not frames:
        raise ValueError("no frames to render")
    if backend == "auto":
        if ffmpeg_exe() and _pil_available():
            backend = "ffmpeg"
        elif _pil_available():
            backend = "gif"
        else:
            raise RuntimeError("video needs ffmpeg or Pillow installed")
    if backend == "ffmpeg":
        return _render_ffmpeg(frames, out_path, size, fps, audio_path)
    if backend == "gif":
        return _render_gif(frames, out_path, size)
    raise ValueError(f"unknown video backend: {backend}")


def render_kenburns(images: List, out_path: str, *, audio_path: Optional[str] = None,
                    size=(1080, 1920), fps: int = 24) -> dict:
    """Ken Burns: pan/zoom over each image, concat, and mux a voiceover.

    images: list of (image_path, seconds). Alternating zoom-in/zoom-out gives
    motion; the result is muxed to the audio track (trimmed to whichever ends
    first). Requires ffmpeg.
    """
    import subprocess
    import tempfile
    from pathlib import Path

    ff = ffmpeg_exe()
    if not ff:
        raise RuntimeError("ken burns needs ffmpeg")
    w, h = size
    path = out_path if out_path.endswith(".mp4") else out_path + ".mp4"
    with tempfile.TemporaryDirectory(prefix="cf-kb-") as tmp:
        clips = []
        for i, (img, secs) in enumerate(images):
            secs = max(1.5, float(secs))
            frames = int(secs * fps)
            # zoom in on even scenes, out on odd — keeps the eye moving
            z = "min(zoom+0.0012,1.35)" if i % 2 == 0 else \
                "if(lte(zoom,1.0),1.35,max(1.001,zoom-0.0012))"
            clip = str(Path(tmp) / f"c{i:03d}.mp4")
            # work on a modest 1.25x canvas (not 2x) — zoompan stays smooth but
            # renders far faster on CPU
            cw, ch = int(w * 1.25), int(h * 1.25)
            vf = (f"scale={cw}:{ch}:force_original_aspect_ratio=increase,"
                  f"crop={cw}:{ch},"
                  f"zoompan=z='{z}':d={frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
                  f"s={w}x{h}:fps={fps},format=yuv420p")
            subprocess.run([ff, "-y", "-loop", "1", "-t", str(secs), "-i", img,
                            "-vf", vf, "-r", str(fps), clip],
                           check=True, capture_output=True, text=True)
            clips.append(clip)
        lf = Path(tmp) / "list.txt"
        lf.write_text("\n".join(f"file '{Path(c).as_posix()}'" for c in clips), encoding="utf-8")
        base = [ff, "-y", "-f", "concat", "-safe", "0", "-i", str(lf)]
        if audio_path:
            base += ["-i", audio_path, "-map", "0:v", "-map", "1:a", "-c:a", "aac", "-shortest"]
        base += ["-c:v", "libx264", "-pix_fmt", "yuv420p", path]
        subprocess.run(base, check=True, capture_output=True, text=True)
    return {"path": path, "backend": "kenburns", "clips": len(images),
            "seconds": round(sum(max(1.5, float(s)) for _, s in images), 1)}


def stills_to_video(items: List, out_path: str, *, audio_path: Optional[str] = None,
                    size=(1280, 720), fps: int = 24) -> dict:
    """Assemble held stills into a video (no zoompan — fast even for many minutes).

    items: list of (image_path, seconds). Each image is padded to `size` and
    held for its duration; clips are concatenated and the voiceover is muxed.
    This is what makes long narrated video-essays feasible on CPU.
    """
    import subprocess
    import tempfile
    from pathlib import Path

    ff = ffmpeg_exe()
    if not ff:
        raise RuntimeError("needs ffmpeg")
    w, h = size
    path = out_path if out_path.endswith(".mp4") else out_path + ".mp4"
    total = sum(max(0.5, float(s)) for _, s in items)
    with tempfile.TemporaryDirectory(prefix="cf-still-") as tmp:
        clips = []
        for i, (img, secs) in enumerate(items):
            clip = str(Path(tmp) / f"c{i:04d}.mp4")
            vf = (f"scale={w}:{h}:force_original_aspect_ratio=decrease,"
                  f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:color=0x0D1117,format=yuv420p")
            subprocess.run([ff, "-y", "-loop", "1", "-t", f"{max(0.5, float(secs)):.2f}",
                            "-i", img, "-vf", vf, "-r", str(fps), clip],
                           check=True, capture_output=True, text=True)
            clips.append(clip)
        lf = Path(tmp) / "list.txt"
        lf.write_text("\n".join(f"file '{Path(c).as_posix()}'" for c in clips), encoding="utf-8")
        cmd = [ff, "-y", "-f", "concat", "-safe", "0", "-i", str(lf)]
        if audio_path:
            cmd += ["-i", audio_path, "-map", "0:v", "-map", "1:a", "-c:a", "aac",
                    "-t", f"{total:.2f}"]
        cmd += ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", str(fps), path]
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    return {"path": path, "backend": "stills", "clips": len(items), "seconds": round(total, 1)}


def text2video_backend() -> Optional[str]:
    """Detect a local open text-to-video model, if the GPU can run one."""
    from .hardware import recommend
    rec = recommend()
    if rec["video"] and rec["device"] == "cuda":
        try:
            import diffusers  # noqa: F401
            return rec["video"]
        except Exception:
            return None
    return None
