"""Hardware detection and hardware-aware model recommendation.

Everything in creatorforge runs on what you have. This module figures out what
that is — GPU and VRAM if any, otherwise CPU — and recommends the largest
open-source model in each modality that will actually fit, so we never try to
load a model your machine can't run.

Detection is best-effort and dependency-free: it uses `torch` if it happens to
be installed, else `nvidia-smi`, else assumes CPU. Nothing here requires a GPU.
"""

from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from functools import lru_cache


@dataclass(frozen=True)
class Hardware:
    device: str            # "cuda" | "mps" | "cpu"
    vram_gb: float         # 0.0 on CPU/unknown
    gpu_name: str = ""

    @property
    def has_gpu(self) -> bool:
        return self.device in ("cuda", "mps")


def _via_torch():
    try:
        import torch
    except Exception:
        return None
    try:
        if torch.cuda.is_available():
            props = torch.cuda.get_device_properties(0)
            return Hardware("cuda", round(props.total_memory / 1024**3, 1), props.name)
        if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
            # Apple Silicon shares system memory; report it as a soft budget
            import psutil  # optional
            gb = round(psutil.virtual_memory().total / 1024**3, 1)
            return Hardware("mps", gb, "Apple Silicon (unified memory)")
    except Exception:
        return None
    return None


def _via_nvidia_smi():
    exe = shutil.which("nvidia-smi")
    if not exe:
        return None
    try:
        out = subprocess.run(
            [exe, "--query-gpu=memory.total,name", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=5, check=True).stdout.strip()
        line = out.splitlines()[0]
        mem, name = line.split(",", 1)
        return Hardware("cuda", round(float(mem) / 1024, 1), name.strip())
    except Exception:
        return None


@lru_cache(maxsize=1)
def detect() -> Hardware:
    return _via_torch() or _via_nvidia_smi() or Hardware("cpu", 0.0, "")


def ffmpeg_exe() -> "Optional[str]":
    """Path to an ffmpeg binary: system PATH first, then the imageio-ffmpeg
    bundled binary (pip install imageio-ffmpeg) so real MP4s work without a
    system install."""
    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return None


# (model, min_vram_gb) ladders — biggest-that-fits wins. CPU tier is the floor.
_LLM_TIERS = [
    ("qwen2.5:32b", 24), ("llama3.1:8b", 8), ("qwen2.5:7b", 6), ("llama3.2:3b", 0),
]
_WHISPER_TIERS = [
    ("large-v3", 10), ("medium", 6), ("small", 3), ("base", 0),
]
# photorealistic open models — the open/local answer to "nano-banana"-class image gen
_IMAGE_TIERS = [
    ("flux.1-schnell", 12), ("sdxl-turbo", 8), ("stable-diffusion-1.5", 4), (None, 0),
]
_TTS_TIERS = [
    ("xtts-v2", 6),        # voice cloning, GPU
    ("piper", 0),          # fast, CPU, tiny
]
# local open text-to-video — heavy; None on no/low GPU (fall back to assembled video)
_VIDEO_TIERS = [
    ("ltx-video", 12), ("cogvideox-2b", 8), (None, 0),
]
# local open music generation (AudioCraft / MusicGen)
_MUSIC_TIERS = [
    ("musicgen-medium", 8), ("musicgen-small", 4), (None, 0),
]


def _pick(tiers, vram):
    for name, need in tiers:
        if vram >= need:
            return name
    return tiers[-1][0]


def recommend(hw: Hardware | None = None) -> dict:
    """Recommended open model per modality for this machine."""
    hw = hw or detect()
    v = hw.vram_gb if hw.has_gpu else 0.0
    return {
        "device": hw.device,
        "vram_gb": hw.vram_gb,
        "gpu": hw.gpu_name,
        "llm": _pick(_LLM_TIERS, v),
        "transcribe": _pick(_WHISPER_TIERS, v),
        "image": _pick(_IMAGE_TIERS, v),       # None when no GPU -> raster/SVG fallback
        "tts": _pick(_TTS_TIERS, v),
        "video": _pick(_VIDEO_TIERS, v),       # None -> assemble video from frames+audio
        "music": _pick(_MUSIC_TIERS, v),       # None -> mix existing audio only
    }
