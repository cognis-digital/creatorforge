"""Publish adapters — get finished posts out of creatorforge and into the world.

Full auto-posting to each platform needs that platform's own API credentials, so
creatorforge ships the safe, universal paths: write packaged posts to an
**outbox** folder (ready to upload or hand to a scheduler), and push to a
**webhook** (Discord, Slack, Zapier, or your own poster). Both are local and
need no platform keys.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional


def to_outbox(packages: dict, outdir: str = "outbox") -> list:
    """Write one file per platform package; return the paths written."""
    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    written = []
    for platform, pkg in packages.items():
        p = out / f"{platform}.json"
        p.write_text(json.dumps(pkg, indent=2, ensure_ascii=False), encoding="utf-8")
        written.append(str(p))
    return written


def to_webhook(content: str, url: str, timeout: float = 10.0) -> dict:
    """POST content to a webhook (Discord-compatible `{"content": ...}`)."""
    import urllib.request

    body = json.dumps({"content": content}).encode("utf-8")
    req = urllib.request.Request(url, data=body,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return {"ok": 200 <= r.status < 300, "status": r.status}
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": str(e)}


def publish(packages: dict, *, outbox: Optional[str] = "outbox",
            webhook: Optional[str] = None) -> dict:
    result = {}
    if outbox:
        result["outbox"] = to_outbox(packages, outbox)
    if webhook:
        first = next(iter(packages.values()), {})
        text = first.get("caption") or first.get("title") or ""
        result["webhook"] = to_webhook(text, webhook)
    return result
