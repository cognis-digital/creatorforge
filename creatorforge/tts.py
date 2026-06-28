"""Voice / text-to-speech — local voiceover, including voice cloning.

Two open, local backends, picked for hardware reality:

  * **Piper** — tiny, fast, CPU-only neural TTS. The default; runs anywhere.
  * **XTTS-v2** (Coqui TTS) — voice *cloning* from a short reference clip, on GPU.

Generate a voiceover for any script, in a stock voice or cloned from a sample
of the creator's own voice. Nothing leaves the machine.
"""

from __future__ import annotations

import shutil
from typing import Optional


def piper_available() -> bool:
    return shutil.which("piper") is not None


def xtts_available() -> bool:
    try:
        import TTS  # noqa: F401
        return True
    except Exception:
        return False


def capabilities() -> dict:
    return {"piper": piper_available(), "xtts": xtts_available()}


def _synth_piper(text: str, out_path: str, voice_model: Optional[str]) -> dict:
    import subprocess
    if not voice_model:
        raise ValueError("piper needs --voice pointing at a .onnx voice model")
    proc = subprocess.run(["piper", "--model", voice_model, "--output_file", out_path],
                          input=text.encode("utf-8"), capture_output=True)
    if proc.returncode != 0:
        raise RuntimeError(f"piper failed: {proc.stderr.decode('utf-8', 'replace')[:200]}")
    return {"path": out_path, "backend": "piper"}


def _synth_xtts(text: str, out_path: str, speaker_wav: Optional[str], language: str) -> dict:
    from TTS.api import TTS
    tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2")
    tts.tts_to_file(text=text, file_path=out_path, speaker_wav=speaker_wav, language=language)
    return {"path": out_path, "backend": "xtts-v2", "cloned": bool(speaker_wav)}


def synthesize(text: str, out_path: str, *, backend: str = "auto",
               voice_model: Optional[str] = None, speaker_wav: Optional[str] = None,
               language: str = "en") -> dict:
    """Synthesize speech to `out_path`. backend: auto | piper | xtts.

    'auto' prefers a cloned voice (xtts + speaker_wav) when available, else Piper.
    """
    if backend == "auto":
        if speaker_wav and xtts_available():
            backend = "xtts"
        elif piper_available():
            backend = "piper"
        elif xtts_available():
            backend = "xtts"
        else:
            raise RuntimeError(
                "no local TTS available: install Piper (pip install piper-tts) "
                "or Coqui TTS (pip install TTS) for voice cloning")
    if backend == "piper":
        return _synth_piper(text, out_path, voice_model)
    if backend == "xtts":
        return _synth_xtts(text, out_path, speaker_wav, language)
    raise ValueError(f"unknown tts backend: {backend}")
