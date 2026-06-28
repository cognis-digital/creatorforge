"""Generative audio — music and sound effects from open local models.

  * **MusicGen** (Meta AudioCraft) → original music beds from a text prompt.
  * **AudioGen** (Meta AudioCraft) → realistic sound effects / foley from a prompt.

Both run locally on a capable GPU. When they're not available, we fall back to a
synthesized WAV bed (stdlib) so a production still gets an audio track — and you
can drop in a licensed track later. All open weights, all local.
"""

from __future__ import annotations

from typing import Optional

from .audio import _wave_bed


def _audiocraft_ready() -> bool:
    try:
        import audiocraft  # noqa: F401
        from .hardware import detect
        return detect().has_gpu
    except Exception:
        return False


def music_available() -> bool:
    return _audiocraft_ready()


def sfx_available() -> bool:
    return _audiocraft_ready()


def _generate_audiocraft(kind: str, prompt: str, seconds: float, out_path: str,
                         model_size: str) -> dict:
    from audiocraft.data.audio import audio_write
    if kind == "music":
        from audiocraft.models import MusicGen
        model = MusicGen.get_pretrained(f"facebook/musicgen-{model_size}")
    else:
        from audiocraft.models import AudioGen
        model = AudioGen.get_pretrained(f"facebook/audiogen-{model_size}")
    model.set_generation_params(duration=seconds)
    wav = model.generate([prompt])
    base = out_path[:-4] if out_path.endswith(".wav") else out_path
    audio_write(base, wav[0].cpu(), model.sample_rate, strategy="loudness")
    return {"path": base + ".wav", "backend": f"{kind}-{model_size}", "prompt": prompt}


def generate_music(prompt: str, seconds: float, out_path: str,
                   model_size: str = "small") -> dict:
    """Generate a music bed. MusicGen if available, else a synthesized WAV bed."""
    if music_available():
        try:
            return _generate_audiocraft("music", prompt, seconds, out_path, model_size)
        except Exception:
            pass
    path = out_path if out_path.endswith(".wav") else out_path + ".wav"
    _wave_bed(path, seconds)
    return {"path": path, "backend": "wave-bed", "prompt": prompt}


def generate_sfx(prompt: str, seconds: float, out_path: str,
                 model_size: str = "medium") -> dict:
    """Generate a sound effect. AudioGen if available, else a short WAV bed."""
    if sfx_available():
        try:
            return _generate_audiocraft("sfx", prompt, min(seconds, 5.0), out_path, model_size)
        except Exception:
            pass
    path = out_path if out_path.endswith(".wav") else out_path + ".wav"
    _wave_bed(path, min(seconds, 2.0), freq=440, volume=0.05)
    return {"path": path, "backend": "wave-bed", "prompt": prompt}
