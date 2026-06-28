"""Photorealistic image generation — the open, local answer to Nano-Banana-class models.

Generates real thumbnail/visual images from a concept using whatever open model
your hardware can run:

  * Automatic1111 / SD-WebUI HTTP API (any SD/SDXL/FLUX checkpoint you've loaded),
  * a local `diffusers` pipeline (FLUX.1-schnell, SDXL-Turbo, or SD 1.5 — picked
    to fit your VRAM by `hardware.recommend`),
  * and, when there's no GPU at all, a clean **SVG mockup** so the pipeline still
    produces a usable thumbnail and never hard-fails.

All open weights, all local, all free. Nothing is sent to a cloud image API.
"""

from __future__ import annotations

import base64
from typing import Optional

from .hardware import detect, recommend
from .thumbnails import _wrap, render_svg


def _pil_available() -> bool:
    try:
        import PIL  # noqa: F401
        return True
    except Exception:
        return False


def _font(size: int):
    from PIL import ImageFont
    for name in ("arialbd.ttf", "arial.ttf", "DejaVuSans-Bold.ttf", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except Exception:
            continue
    try:
        return ImageFont.load_default(size=size)
    except TypeError:  # older Pillow
        return ImageFont.load_default()


def render_png(concept: dict, width: int = 1280, height: int = 720) -> bytes:
    """A real composited raster thumbnail via PIL — runs on CPU, no model needed."""
    import io
    from PIL import Image, ImageDraw

    p = concept.get("palette", {"bg": "#0E1517", "accent": "#F4B400", "text": "#FFFFFF"})
    img = Image.new("RGB", (width, height), p["bg"])
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 18, height], fill=p["accent"])
    lines = _wrap(concept.get("headline", ""), 12)
    fs = 150 if len(lines) <= 1 else 120
    font = _font(fs)
    y = height // 2 - (len(lines) - 1) * fs // 2 - fs // 2
    for ln in lines:
        d.text((64, y), ln, fill=p["text"], font=font)
        y += fs
    d.rectangle([64, height - 120, 584, height - 112], fill=p["accent"])
    d.text((64, height - 95), concept.get("subtext", ""), fill=p["accent"], font=_font(40))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def thumbnail_prompt(concept: dict) -> str:
    """Turn a thumbnail concept into a photorealistic txt2img prompt."""
    visual = concept.get("visual", "a striking subject")
    emotion = concept.get("emotion", "curiosity")
    return (
        f"{visual}, {emotion} expression, bold cinematic lighting, high contrast, "
        f"photorealistic, ultra-detailed, 8k, sharp focus, professional YouTube "
        f"thumbnail composition with clear space for a headline"
    )


class ImageBackend:
    name = "abstract"

    @property
    def available(self) -> bool:
        return False

    def generate(self, prompt: str, width: int, height: int, steps: int = 20) -> bytes:
        raise NotImplementedError


class Automatic1111Backend(ImageBackend):
    """txt2img via the standard SD-WebUI / Automatic1111 HTTP API."""

    name = "automatic1111"

    def __init__(self, host: str = "http://127.0.0.1:7860"):
        self.host = host.rstrip("/")

    @property
    def available(self) -> bool:
        import urllib.request
        try:
            with urllib.request.urlopen(f"{self.host}/sdapi/v1/sd-models", timeout=2):
                return True
        except Exception:
            return False

    def generate(self, prompt: str, width: int, height: int, steps: int = 20) -> bytes:
        import json
        import urllib.request

        body = json.dumps({
            "prompt": prompt, "steps": steps, "width": width, "height": height,
            "sampler_name": "DPM++ 2M Karras",
        }).encode("utf-8")
        req = urllib.request.Request(f"{self.host}/sdapi/v1/txt2img", data=body,
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=300) as r:
            images = json.loads(r.read()).get("images") or []
        if not images:
            raise RuntimeError("automatic1111 returned no image")
        return base64.b64decode(images[0])


class DiffusersBackend(ImageBackend):
    """In-process generation via Hugging Face `diffusers` (local weights)."""

    name = "diffusers"
    _MODEL_IDS = {
        "flux.1-schnell": "black-forest-labs/FLUX.1-schnell",
        "sdxl-turbo": "stabilityai/sdxl-turbo",
        "stable-diffusion-1.5": "runwayml/stable-diffusion-v1-5",
    }

    def __init__(self, model: Optional[str] = None):
        self.model = model or recommend()["image"] or "sdxl-turbo"
        self._pipe = None

    @property
    def available(self) -> bool:
        try:
            import diffusers  # noqa: F401
            import torch  # noqa: F401
            return detect().has_gpu
        except Exception:
            return False

    def _load(self):
        if self._pipe is not None:
            return self._pipe
        import torch
        from diffusers import AutoPipelineForText2Image

        model_id = self._MODEL_IDS.get(self.model, self.model)
        pipe = AutoPipelineForText2Image.from_pretrained(
            model_id, torch_dtype=torch.float16)
        pipe = pipe.to("cuda" if torch.cuda.is_available() else "cpu")
        self._pipe = pipe
        return pipe

    def generate(self, prompt: str, width: int, height: int, steps: int = 8) -> bytes:
        import io

        pipe = self._load()
        image = pipe(prompt=prompt, width=width, height=height,
                     num_inference_steps=steps).images[0]
        buf = io.BytesIO()
        image.save(buf, format="PNG")
        return buf.getvalue()


def get_image_backend(prefer: str = "auto", host: str = "http://127.0.0.1:7860") -> Optional[ImageBackend]:
    """Return the best available image backend, or None (caller uses SVG)."""
    if prefer in ("automatic1111", "a1111"):
        b = Automatic1111Backend(host)
        return b if b.available else None
    if prefer == "diffusers":
        b = DiffusersBackend()
        return b if b.available else None
    if prefer == "auto":
        a = Automatic1111Backend(host)
        if a.available:
            return a
        d = DiffusersBackend()
        if d.available:
            return d
        return None
    raise ValueError(f"unknown image backend: {prefer}")


def generate_thumbnail(concept: dict, out_path: str, *, backend: Optional[ImageBackend] = None,
                       width: int = 1280, height: int = 720, allow_raster: bool = True,
                       hero: Optional[str] = None) -> dict:
    """Render a concept to the best image this machine can make.

    Order: a real **sourced hero photo** composited + graded (punches above CPU
    diffusion) → a diffusion backend (photorealistic, GPU) → a PIL raster PNG →
    an SVG mockup (always). out_path is a base; the file gets .png or .svg added.
    """
    if hero and _pil_available():
        from .compose import compose_thumbnail
        return compose_thumbnail(hero, concept, out_path, width=width, height=height)
    backend = backend if backend is not None else get_image_backend()
    if backend is not None and backend.available:
        png = backend.generate(thumbnail_prompt(concept), width, height)
        path = out_path + ".png"
        with open(path, "wb") as fh:
            fh.write(png)
        return {"path": path, "backend": backend.name, "photorealistic": True}
    if allow_raster and _pil_available():
        path = out_path + ".png"
        with open(path, "wb") as fh:
            fh.write(render_png(concept, width, height))
        return {"path": path, "backend": "pil-raster", "photorealistic": False}
    path = out_path + ".svg"
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(render_svg(concept, width, height))
    return {"path": path, "backend": "svg", "photorealistic": False}
