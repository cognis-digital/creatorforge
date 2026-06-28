"""What can THIS machine do? — a single honest capability report.

Probes every modality and tells you which backend is live right now and which
open model is recommended for your hardware. Use it to know, before you run a
pipeline, whether you'll get photorealistic images or SVG mockups, an MP4 or an
animated GIF, a cloned voice or none.
"""

from __future__ import annotations

import shutil


def capabilities() -> dict:
    from . import transcribe, tts
    from .hardware import recommend
    from .images import Automatic1111Backend, DiffusersBackend, _pil_available
    from .providers import OllamaProvider

    rec = recommend()
    op = OllamaProvider()
    models = op.list_models()
    has_ffmpeg = bool(shutil.which("ffmpeg"))

    return {
        "hardware": {"device": rec["device"], "vram_gb": rec["vram_gb"], "gpu": rec["gpu"]},
        "text": {
            "ollama": bool(models),
            "models": models,
            "selected": op.best_model(),
            "recommended": rec["llm"],
        },
        "transcribe": {
            "faster_whisper": transcribe.available(),
            "recommended": rec["transcribe"],
        },
        "voice": {
            **tts.capabilities(),
            "recommended": rec["tts"],
        },
        "image": {
            "automatic1111": Automatic1111Backend().available,
            "diffusers": DiffusersBackend().available,
            "pil_raster": _pil_available(),
            "recommended": rec["image"] or "pil-raster / svg fallback",
        },
        "video": {
            "ffmpeg": has_ffmpeg,
            "pil": _pil_available(),
            "text2video": rec["video"] or "assemble from frames",
        },
        "audio": {
            "ffmpeg": has_ffmpeg,
            "wave_fallback": True,
            "music": rec["music"] or "mix only",
        },
    }
