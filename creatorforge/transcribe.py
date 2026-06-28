"""Transcription — turn filmed footage into text with local Whisper.

Uses `faster-whisper` (CTranslate2) entirely on your machine — no upload. The
model size is chosen to fit your hardware (large-v3 on a capable GPU down to
base on CPU). Transcripts feed two things: learning your voice from how you
actually *talk*, and repurposing long footage into posts, clips, and captions.
"""

from __future__ import annotations

from typing import List, Optional

from .hardware import detect, recommend
from .voice import VoiceProfile, analyze


def available() -> bool:
    try:
        import faster_whisper  # noqa: F401
        return True
    except Exception:
        return False


def transcribe(audio_path: str, model: Optional[str] = None,
               device: str = "auto", compute_type: str = "auto") -> dict:
    """Transcribe one audio/video file. Returns text + timed segments."""
    if not available():
        raise RuntimeError(
            "transcription needs faster-whisper: pip install faster-whisper")
    from faster_whisper import WhisperModel

    hw = detect()
    model = model or recommend()["transcribe"]
    if device == "auto":
        device = "cuda" if hw.device == "cuda" else "cpu"
    if compute_type == "auto":
        compute_type = "float16" if device == "cuda" else "int8"

    wm = WhisperModel(model, device=device, compute_type=compute_type)
    segments, info = wm.transcribe(audio_path)
    segs = [{"start": round(s.start, 2), "end": round(s.end, 2), "text": s.text.strip()}
            for s in segments]
    return {
        "model": model,
        "language": info.language,
        "text": " ".join(s["text"] for s in segs).strip(),
        "segments": segs,
    }


def voice_from_audio(audio_paths: List[str], model: Optional[str] = None) -> VoiceProfile:
    """Learn a VoiceProfile from how the creator speaks, via transcripts."""
    texts = [transcribe(p, model=model)["text"] for p in audio_paths]
    return analyze(texts)
