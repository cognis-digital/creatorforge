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


def _default_piper_voice() -> Optional[str]:
    """Find a Piper voice .onnx: $CREATORFORGE_PIPER_VOICE, else a local _voices dir."""
    import glob
    import os
    env = os.environ.get("CREATORFORGE_PIPER_VOICE")
    if env and os.path.exists(env):
        return env
    for pat in (os.path.expanduser(r"~/_voices/*.onnx"), r"C:\Users\user\_voices\*.onnx",
                "voices/*.onnx"):
        hits = glob.glob(pat)
        if hits:
            return hits[0]
    return None


def piper_available() -> bool:
    try:
        import piper  # noqa: F401
        return _default_piper_voice() is not None
    except Exception:
        return False


def sapi_available() -> bool:
    """Offline OS TTS (Windows SAPI / macOS / espeak) via pyttsx3."""
    try:
        import pyttsx3  # noqa: F401
        return True
    except Exception:
        return False


def _synth_sapi(text: str, out_path: str) -> dict:
    import pyttsx3
    path = out_path if out_path.endswith(".wav") else out_path + ".wav"
    engine = pyttsx3.init()
    engine.save_to_file(text, path)
    engine.runAndWait()
    return {"path": path, "backend": "sapi"}


def xtts_available() -> bool:
    try:
        import TTS  # noqa: F401
        return True
    except Exception:
        return False


def capabilities() -> dict:
    return {"piper": piper_available(), "xtts": xtts_available(), "sapi": sapi_available()}


def _synth_piper(text: str, out_path: str, voice_model: Optional[str]) -> dict:
    import subprocess
    import sys
    vm = voice_model or _default_piper_voice()
    if not vm:
        raise ValueError("piper needs a voice .onnx (pass voice_model or set CREATORFORGE_PIPER_VOICE)")
    path = out_path if out_path.endswith(".wav") else out_path + ".wav"
    proc = subprocess.run([sys.executable, "-m", "piper", "-m", vm, "-f", path],
                          input=text.encode("utf-8"), capture_output=True)
    if proc.returncode != 0:
        raise RuntimeError(f"piper failed: {proc.stderr.decode('utf-8', 'replace')[:200]}")
    return {"path": path, "backend": "piper"}


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
            backend = "xtts"           # voice cloning when a reference is given
        elif piper_available():
            backend = "piper"          # best CPU neural voice
        elif sapi_available():
            backend = "sapi"           # offline OS voice — always works
        elif xtts_available():
            backend = "xtts"
        else:
            raise RuntimeError(
                "no local TTS available: install pyttsx3 (offline OS voice), "
                "Piper (pip install piper-tts), or Coqui TTS for cloning")
    if backend == "piper":
        return _synth_piper(text, out_path, voice_model)
    if backend == "sapi":
        return _synth_sapi(text, out_path)
    if backend == "xtts":
        return _synth_xtts(text, out_path, speaker_wav, language)
    raise ValueError(f"unknown tts backend: {backend}")
