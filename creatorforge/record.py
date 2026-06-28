"""Demo recorder — run real commands and turn their real output into video.

The most honest "footage" for a software project is the software actually
running. `capture` executes a real command (a demo, a test suite, a CLI) and
records its true stdout/stderr, exit code, and duration. `render_terminal`
renders those captures as a terminal-cast video — a dark console with the real
output revealed line by line — which encodes fast on CPU (no heavy filters).

This is "real code running, recorded": nothing is mocked; the bytes on screen
are the bytes the program produced.
"""

from __future__ import annotations

import subprocess
import time
from dataclasses import dataclass, field
from typing import List, Optional

from .hardware import ffmpeg_exe
from .images import _pil_available


@dataclass
class Capture:
    command: str
    output: str
    returncode: int
    seconds: float
    title: str = ""

    def lines(self) -> List[str]:
        return (f"$ {self.command}\n" + self.output).splitlines() or [f"$ {self.command}"]


def capture(command: str, cwd: Optional[str] = None, title: str = "",
            timeout: float = 600) -> Capture:
    """Run a real command and record its real output."""
    t0 = time.time()
    proc = subprocess.run(command, cwd=cwd, shell=True, capture_output=True,
                          text=True, timeout=timeout)
    out = (proc.stdout or "") + (proc.stderr or "")
    return Capture(command, out.rstrip("\n"), proc.returncode,
                   round(time.time() - t0, 2), title or command)


# ---- terminal-cast rendering --------------------------------------------
_BG = (13, 17, 23)        # github-dark console
_FG = (220, 224, 228)
_PROMPT = (88, 166, 255)
_OK = (63, 185, 80)


def _term_font(size: int):
    from PIL import ImageFont
    for name in ("consola.ttf", "Consolas.ttf", "DejaVuSansMono.ttf", "cour.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except Exception:
            continue
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def _frame(visible: List[str], size, font, title: str):
    from PIL import Image, ImageDraw
    w, h = size
    img = Image.new("RGB", (w, h), _BG)
    d = ImageDraw.Draw(img)
    # title bar with traffic lights
    d.rectangle([0, 0, w, 44], fill=(22, 27, 34))
    for i, c in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
        d.ellipse([20 + i * 26, 15, 34 + i * 26, 29], fill=c)
    d.text((120, 14), title[:80], fill=(139, 148, 158), font=_term_font(20))
    y = 60
    lh = font.size + 6
    for ln in visible:
        color = _FG
        if ln.startswith("$ "):
            color = _PROMPT
        elif "passed" in ln or "OK" in ln or "intact=True" in ln or "✓" in ln:
            color = _OK
        d.text((24, y), ln[:120], fill=color, font=font)
        y += lh
        if y > h - lh:
            break
    return img


def render_terminal(captures: List[Capture], out_path: str, *, audio_path: Optional[str] = None,
                    size=(1280, 720), fps: int = 12, lines_per_sec: float = 4.0) -> dict:
    """Render captures as a terminal-cast MP4 (real output revealed line by line)."""
    import tempfile
    from pathlib import Path

    if not _pil_available():
        raise RuntimeError("terminal render needs Pillow")
    ff = ffmpeg_exe()
    if not ff:
        raise RuntimeError("terminal render needs ffmpeg")
    w, h = size
    font = _term_font(max(16, w // 64))
    max_rows = (h - 70) // (font.size + 6)
    path = out_path if out_path.endswith(".mp4") else out_path + ".mp4"

    # build the full line stream across captures
    stream: List[tuple] = []  # (line, title)
    for cap in captures:
        for ln in cap.lines():
            stream.append((ln, cap.title))
        stream.append(("", cap.title))  # gap between captures

    frames_dir = tempfile.mkdtemp(prefix="cf-term-")
    step = max(1, int(round(fps / lines_per_sec)))  # frames per new line
    fi = 0
    for reveal in range(1, len(stream) + 1):
        window = stream[max(0, reveal - max_rows):reveal]
        title = window[-1][1] if window else ""
        img = _frame([l for l, _ in window], size, font, title)
        for _ in range(step):
            img.save(f"{frames_dir}/f{fi:05d}.png")
            fi += 1
    # hold last frame ~1.5s
    for _ in range(int(fps * 1.5)):
        img.save(f"{frames_dir}/f{fi:05d}.png")
        fi += 1

    video_seconds = fi / fps
    cmd = [ff, "-y", "-framerate", str(fps), "-i", f"{frames_dir}/f%05d.png"]
    if audio_path:
        # the recorded demo drives the length; a shorter voiceover just narrates
        # the opening (don't -shortest, or it would truncate the demo)
        cmd += ["-i", audio_path, "-map", "0:v", "-map", "1:a", "-c:a", "aac",
                "-t", f"{video_seconds:.2f}"]
    cmd += ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", str(fps), path]
    subprocess.run(cmd, check=True, capture_output=True, text=True)
    return {"path": path, "backend": "terminal-cast", "frames": fi,
            "seconds": round(fi / fps, 1), "captures": len(captures)}
