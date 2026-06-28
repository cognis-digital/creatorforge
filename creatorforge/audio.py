"""Audio production — voiceover + music into a finished, leveled track.

  * **ffmpeg** → mix a voiceover over a music bed, loop/trim the bed, and
    loudness-normalize to a broadcast target. The real production path.
  * **stdlib `wave`** → when ffmpeg isn't present, pass a voiceover through, or
    synthesize a simple bed, so you always get a valid WAV out.

`music_backend()` detects a local open music generator (AudioCraft / MusicGen)
for original beds on a capable GPU; without it, you mix what you have.
"""

from __future__ import annotations

import os
import shutil
from typing import Optional

from .hardware import ffmpeg_exe


def _wave_bed(out_path: str, seconds: float = 8.0, rate: int = 44100,
              freq: float = 196.0, volume: float = 0.06) -> str:
    """A soft tonal bed written with the standard library (no deps)."""
    import math
    import struct
    import wave

    n = int(seconds * rate)
    with wave.open(out_path, "w") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        frames = bytearray()
        for i in range(n):
            # gentle two-note pad with a slow fade in/out
            env = min(1.0, i / (rate * 0.5), (n - i) / (rate * 0.5))
            s = volume * env * (math.sin(2 * math.pi * freq * i / rate)
                                + 0.5 * math.sin(2 * math.pi * freq * 1.5 * i / rate))
            frames += struct.pack("<h", int(max(-1.0, min(1.0, s)) * 32767))
        w.writeframesraw(bytes(frames))
    return out_path


def _produce_ffmpeg(out_path: str, voiceover: Optional[str], music: Optional[str],
                    seconds: float, target_lufs: float) -> dict:
    import subprocess

    ff = ffmpeg_exe()
    path = out_path if out_path.endswith((".wav", ".mp3", ".m4a")) else out_path + ".m4a"
    if voiceover and music:
        # duck the music under the voiceover, then normalize loudness
        flt = (f"[1:a]volume=0.25,aloop=loop=-1:size=2e9[bed];"
               f"[0:a][bed]amix=inputs=2:duration=first:dropout_transition=2,"
               f"loudnorm=I={target_lufs}:TP=-1.5[a]")
        cmd = [ff, "-y", "-i", voiceover, "-i", music, "-filter_complex", flt,
               "-map", "[a]", "-shortest", path]
    elif voiceover:
        cmd = [ff, "-y", "-i", voiceover,
               "-af", f"loudnorm=I={target_lufs}:TP=-1.5", path]
    elif music:
        cmd = [ff, "-y", "-i", music, "-t", str(seconds),
               "-af", f"loudnorm=I={target_lufs}:TP=-1.5", path]
    else:
        return _produce_wave(out_path, None, seconds)
    subprocess.run(cmd, check=True, capture_output=True, text=True)
    return {"path": path, "backend": "ffmpeg"}


def _produce_wave(out_path: str, voiceover: Optional[str], seconds: float) -> dict:
    path = out_path if out_path.endswith(".wav") else out_path + ".wav"
    if voiceover and os.path.exists(voiceover):
        shutil.copyfile(voiceover, path)
        return {"path": path, "backend": "wave-passthrough"}
    _wave_bed(path, seconds)
    return {"path": path, "backend": "wave-synth"}


def produce(out_path: str, *, voiceover: Optional[str] = None, music: Optional[str] = None,
            seconds: float = 8.0, target_lufs: float = -14.0, backend: str = "auto") -> dict:
    """Produce a finished audio track. backend: auto | ffmpeg | wave."""
    if backend == "auto":
        backend = "ffmpeg" if ffmpeg_exe() else "wave"
    if backend == "ffmpeg":
        return _produce_ffmpeg(out_path, voiceover, music, seconds, target_lufs)
    if backend == "wave":
        return _produce_wave(out_path, voiceover, seconds)
    raise ValueError(f"unknown audio backend: {backend}")


def music_backend() -> Optional[str]:
    """Detect a local open music generator (MusicGen) if the GPU can run one."""
    from .hardware import recommend
    rec = recommend()
    if rec["music"] and rec["device"] == "cuda":
        try:
            import audiocraft  # noqa: F401
            return rec["music"]
        except Exception:
            return None
    return None
