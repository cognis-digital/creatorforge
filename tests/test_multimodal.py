import wave
from pathlib import Path

from creatorforge.audio import produce
from creatorforge.capabilities import capabilities
from creatorforge.hardware import detect, recommend
from creatorforge.images import generate_thumbnail, get_image_backend, render_png
from creatorforge.providers import OllamaProvider
from creatorforge.script import write_script
from creatorforge.thumbnails import thumbnail_concepts
from creatorforge.video import render, storyboard


def test_hardware_recommend_has_all_modalities():
    rec = recommend()
    assert set(rec) >= {"device", "llm", "transcribe", "image", "tts", "video", "music"}
    assert detect().device in ("cuda", "mps", "cpu")


def test_capabilities_report_runs():
    cap = capabilities()
    for k in ("hardware", "text", "transcribe", "voice", "image", "video", "audio"):
        assert k in cap


def test_render_png_is_real_png():
    concept = thumbnail_concepts("morning routines", None, 1)[0]
    png = render_png(concept)
    assert png[:8] == b"\x89PNG\r\n\x1a\n"      # PNG magic number


def test_generate_thumbnail_falls_back_to_raster(tmp_path):
    concept = thumbnail_concepts("habits", None, 1)[0]
    res = generate_thumbnail(concept, str(tmp_path / "t"), backend=None)
    assert res["backend"] in ("pil-raster", "svg")   # no GPU/server in CI
    assert Path(res["path"]).exists()


def test_video_storyboard_and_gif(tmp_path):
    script = write_script("habits", None, "youtube_shorts")
    sb = storyboard(script)
    assert sb and all("text" in f and "seconds" in f for f in sb)
    res = render(sb, str(tmp_path / "short"), backend="gif")
    assert Path(res["path"]).exists()
    assert res["backend"] == "pil-gif" and res["frames"] >= 3


def test_audio_wave_bed(tmp_path):
    res = produce(str(tmp_path / "track"), backend="wave", seconds=1.0)
    assert res["backend"] == "wave-synth"
    with wave.open(res["path"]) as w:
        assert w.getframerate() == 44100 and w.getnframes() > 0


def test_audio_passthrough(tmp_path):
    src = tmp_path / "v.wav"
    with wave.open(str(src), "w") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(8000)
        w.writeframes(b"\x00\x00" * 200)
    res = produce(str(tmp_path / "out"), voiceover=str(src), backend="wave")
    assert res["backend"] == "wave-passthrough" and Path(res["path"]).exists()


def test_ollama_best_model_preference(monkeypatch):
    op = OllamaProvider()
    monkeypatch.setattr(op, "list_models", lambda: ["codellama:13b", "llama3:latest", "x:7b"])
    assert op.best_model() == "llama3:latest"     # llama3 outranks codellama
    monkeypatch.setattr(op, "list_models", lambda: [])
    assert op.best_model() is None


def test_image_backend_none_without_servers():
    b = get_image_backend("automatic1111")
    assert b is None or hasattr(b, "generate")    # None in CI; backend if one is up
