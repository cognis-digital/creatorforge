"""Asset sourcing — pull real, no-watermark images instead of weak CPU diffusion.

The way to beat a giant cloud image model on a laptop isn't to out-render it —
it's to use *real photography* and design it well. This module finds multiple
related images for any scene from:

  * **your own offline library** — index image folders you already have; search
    them by keyword over filenames, folder names, sidecar captions, and
    (optionally) local `llava` vision captions. Fully offline, your images, zero
    watermarks, zero licensing questions.
  * **free, no-key, no-watermark CC stock** — Openverse and Wikimedia Commons,
    each result carrying its license and attribution so you stay compliant.

Watermarked sources (Getty/Shutterstock previews, etc.) are deliberately never
queried.
"""

from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp", ".tiff", ".heic", ".avif"}
_TOKEN = re.compile(r"[a-z0-9]+")
_STOP = set("the a an and or of to in on for with at by from as is png jpg jpeg img image "
            "photo final copy edited screenshot new untitled".split())


def _tokens(text: str) -> List[str]:
    return [t for t in _TOKEN.findall(text.lower()) if t not in _STOP and len(t) > 1]


@dataclass
class Asset:
    source: str
    ref: str                 # local path or remote URL
    score: float = 0.0
    license: str = "owned"
    attribution: str = ""
    tokens: List[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {"source": self.source, "ref": self.ref, "score": round(self.score, 3),
                "license": self.license, "attribution": self.attribution}


class LocalLibrary:
    """An offline, searchable index of your image folders."""

    def __init__(self):
        self.items: List[dict] = []   # {path, tokens}

    # ---- build ----------------------------------------------------------
    def index(self, roots: List[str], caption: bool = False) -> "LocalLibrary":
        for root in roots:
            base = Path(root)
            if not base.exists():
                continue
            for p in base.rglob("*"):
                if p.is_file() and p.suffix.lower() in IMAGE_EXTS:
                    toks = _tokens(" ".join(p.parts[-3:]))         # filename + 2 parent dirs
                    side = self._sidecar_text(p)
                    if side:
                        toks += _tokens(side)
                    if caption:
                        cap = caption_with_llava(str(p))
                        if cap:
                            toks += _tokens(cap)
                    self.items.append({"path": str(p), "tokens": toks})
        return self

    @staticmethod
    def _sidecar_text(p: Path) -> str:
        for ext in (".txt", ".md", ".caption"):
            s = p.with_suffix(ext)
            if s.exists():
                try:
                    return s.read_text(encoding="utf-8", errors="replace")[:2000]
                except OSError:
                    pass
        return ""

    def save(self, path: str) -> None:
        Path(path).write_text(json.dumps(self.items), encoding="utf-8")

    @classmethod
    def load(cls, path: str) -> "LocalLibrary":
        lib = cls()
        lib.items = json.loads(Path(path).read_text(encoding="utf-8"))
        return lib

    # ---- search ---------------------------------------------------------
    def search(self, query: str, k: int = 6) -> List[Asset]:
        q = Counter(_tokens(query))
        if not q:
            return []
        scored = []
        for it in self.items:
            tc = Counter(it["tokens"])
            overlap = sum(min(q[t], tc[t]) for t in q if t in tc)
            if overlap:
                # normalize a little by query length so short queries don't dominate
                scored.append(Asset("local", it["path"], overlap / sum(q.values()),
                                    license="owned"))
        scored.sort(key=lambda a: a.score, reverse=True)
        return scored[:k]

    def __len__(self) -> int:
        return len(self.items)


def caption_with_llava(image_path: str, host: str = "http://localhost:11434",
                       model: str = "llava") -> str:
    """Caption an image with a local vision model via Ollama (best-effort)."""
    import base64
    import urllib.request
    try:
        data = base64.b64encode(Path(image_path).read_bytes()).decode("ascii")
        body = json.dumps({"model": model, "prompt": "Describe this image in 8 keywords.",
                           "images": [data], "stream": False}).encode("utf-8")
        req = urllib.request.Request(f"{host.rstrip('/')}/api/generate", data=body,
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read()).get("response", "").strip()
    except Exception:
        return ""


# ---- free, no-watermark online stock (optional; needs network, no API key) ----
def openverse_search(query: str, k: int = 6, license_type: str = "cc0,pdm,by") -> List[Asset]:
    """Search Openverse for CC / public-domain images (no key, no watermark)."""
    import urllib.parse
    import urllib.request
    url = ("https://api.openverse.org/v1/images/?" +
           urllib.parse.urlencode({"q": query, "page_size": k, "license_type": license_type}))
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "creatorforge/0.1"})
        with urllib.request.urlopen(req, timeout=15) as r:
            results = json.loads(r.read()).get("results", [])
    except Exception:
        return []
    out = []
    for it in results[:k]:
        out.append(Asset("openverse", it.get("url", ""), 1.0,
                         license=it.get("license", "cc"),
                         attribution=it.get("attribution", "") or
                         f'"{it.get("title","")}" by {it.get("creator","")}'))
    return out


def download(asset: Asset, outdir: str) -> Optional[str]:
    """Download a remote asset locally; local assets are returned as-is."""
    if asset.source == "local":
        return asset.ref
    import urllib.request
    Path(outdir).mkdir(parents=True, exist_ok=True)
    name = re.sub(r"[^a-zA-Z0-9._-]", "_", asset.ref.split("/")[-1] or "asset")[:80] or "asset.jpg"
    dest = Path(outdir) / name
    try:
        req = urllib.request.Request(asset.ref, headers={"User-Agent": "creatorforge/0.1"})
        with urllib.request.urlopen(req, timeout=30) as r, open(dest, "wb") as fh:
            fh.write(r.read())
        return str(dest)
    except Exception:
        return None


def gather(query: str, k: int = 6, *, library: Optional[LocalLibrary] = None,
           online: bool = False) -> List[Asset]:
    """Gather multiple related no-watermark images, offline library first."""
    out: List[Asset] = []
    if library is not None:
        out.extend(library.search(query, k))
    if online and len(out) < k:
        out.extend(openverse_search(query, k - len(out)))
    return out[:k]
