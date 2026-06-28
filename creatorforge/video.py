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

import shutil
from typing import List, Optional

from .captions import to_overlays
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

        cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat)]
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
        if shutil.which("ffmpeg") and _pil_available():
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
