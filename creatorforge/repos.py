"""Repo → content — point creatorforge at a repository and get videos and posts for it.

Reads a repo's README (a local checkout, or `owner/name` via the `gh` CLI),
derives what it is and who it's for, and runs the pipeline / long-form engine to
produce launch content. Batch it over an owner's whole catalog to give every
project its own promo, devlog, or documentary.
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import List, Optional

from .longform import LongformBrief, build_longform
from .pipeline import ContentBrief, run_pipeline

_HEADING = re.compile(r"^#\s+(.+)$", re.M)
_BULLET = re.compile(r"^\s*[-*]\s+(.+)$", re.M)
_BADGE = re.compile(r"^\s*(\[!\[|!\[|>|<)")


def parse_readme(text: str) -> dict:
    title = ""
    m = _HEADING.search(text)
    if m:
        title = re.sub(r"[`*_]", "", m.group(1)).strip()
    # first real paragraph (skip headings, badges, blockquotes, blanks)
    description = ""
    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith("#") or _BADGE.match(s):
            continue
        description = re.sub(r"[`*_]", "", s).strip()
        break
    # real feature bullets, not the yes-ladder hook questions some READMEs open with
    features = [re.sub(r"[`*_]", "", b).strip()[:140]
                for b in _BULLET.findall(text) if not b.strip().endswith("?")][:8]
    return {"title": title, "description": description, "features": features}


def _read_local_readme(path: Path) -> str:
    for name in ("README.md", "README.MD", "Readme.md", "readme.md", "README"):
        p = path / name
        if p.exists():
            return p.read_text(encoding="utf-8", errors="replace")
    return ""


def _gh_readme(spec: str) -> str:
    try:
        out = subprocess.run(["gh", "api", f"repos/{spec}/readme", "-q", ".content"],
                             capture_output=True, text=True, timeout=20, check=True).stdout.strip()
        import base64
        return base64.b64decode(out).decode("utf-8", "replace")
    except Exception:
        return ""


def repo_meta(spec: str) -> dict:
    """Resolve {name, title, description, features} from a path or owner/name."""
    p = Path(spec)
    if p.is_dir():
        name = p.resolve().name
        readme = _read_local_readme(p)
    else:
        name = spec.split("/")[-1]
        readme = _gh_readme(spec)
    meta = parse_readme(readme) if readme else {"title": name, "description": "", "features": []}
    meta["name"] = name
    return meta


def _seed(meta: dict) -> dict:
    topic = meta.get("title") or f"How {meta['name']} works"
    desc = meta.get("description", "")
    niche = desc[:60] if desc else meta["name"]
    return {"topic": topic, "niche": niche, "summary": desc, "features": meta.get("features", [])}


def content_for_repo(spec: str, fmt: str = "promotional", longform: bool = False,
                     platforms: Optional[List[str]] = None, voice=None, provider=None) -> dict:
    """Generate content for one repo. longform=True -> a cinematic production plan."""
    meta = repo_meta(spec)
    seed = _seed(meta)
    if longform:
        brief = LongformBrief(topic=seed["topic"], format=fmt, niche=seed["niche"])
        plan = build_longform(brief, voice, provider)
    else:
        brief = ContentBrief(topic=seed["topic"], niche=seed["niche"],
                             platforms=platforms or ["youtube", "x", "linkedin"])
        plan = run_pipeline(brief, voice, provider)
    plan["repo"] = {"name": meta["name"], "features": seed["features"]}
    return plan


def list_repos(owner: str, limit: int = 30) -> List[dict]:
    """List an owner's repos via the gh CLI (name + description)."""
    try:
        out = subprocess.run(
            ["gh", "repo", "list", owner, "--limit", str(limit), "--json", "name,description"],
            capture_output=True, text=True, timeout=30, check=True).stdout
        return json.loads(out)
    except Exception:
        return []
