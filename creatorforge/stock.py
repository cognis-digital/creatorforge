"""Real stock photos — legally, without API keys.

Pulls topical, real photographs from **Openverse** (which aggregates CC0 /
public-domain / Creative-Commons images from Flickr, museums, and more) and,
as a second source, **Wikimedia Commons**. Both are keyless and return images
that are free to use commercially. Pexels/Unsplash are supported too *if* the
user has set PEXELS_API_KEY / UNSPLASH_ACCESS_KEY — otherwise we skip them
rather than scrape (their terms require the API).

Every photo carries its license + creator so callers can credit BY / BY-SA
images. We prefer CC0 / public-domain (no attribution needed) where possible.
"""

from __future__ import annotations

import json
import os
import urllib.request
from typing import Dict, List, Optional

UA = {"User-Agent": "creatorforge/1.0 (chris@greenwayenergycapital.com)"}
NO_ATTR = ("cc0", "pdm")          # licenses that need no credit


def _get(url: str, timeout: int = 25) -> bytes:
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout).read()


def search_openverse(query: str, n: int = 6) -> List[Dict]:
    u = (f"https://api.openverse.org/v1/images/?q={urllib.request.quote(query)}"
         f"&license_type=commercial&page_size={n}&mature=false")
    try:
        d = json.loads(_get(u))
    except Exception:
        return []
    out = []
    for r in d.get("results", []):
        url = r.get("url")
        if not url:
            continue
        out.append({"url": url, "license": (r.get("license") or "").lower(),
                    "creator": r.get("creator") or "", "source": r.get("source") or "openverse",
                    "title": r.get("title") or query})
    return out


def search_commons(query: str, n: int = 6) -> List[Dict]:
    u = ("https://commons.wikimedia.org/w/api.php?action=query&format=json&generator=search"
         f"&gsrsearch=filetype:bitmap%20{urllib.request.quote(query)}&gsrlimit={n}"
         "&gsrnamespace=6&prop=imageinfo&iiprop=url|extmetadata&iiurlwidth=1280")
    try:
        d = json.loads(_get(u))
    except Exception:
        return []
    out = []
    for p in d.get("query", {}).get("pages", {}).values():
        ii = (p.get("imageinfo") or [{}])[0]
        url = ii.get("thumburl") or ii.get("url")
        if not url:
            continue
        em = ii.get("extmetadata", {})
        out.append({"url": url,
                    "license": (em.get("LicenseShortName", {}).get("value", "") or "").lower(),
                    "creator": em.get("Artist", {}).get("value", "") or "",
                    "source": "Wikimedia Commons", "title": p.get("title", query)})
    return out


def _valid_image(path: str) -> bool:
    try:
        from PIL import Image
        with Image.open(path) as im:
            im.verify()
        return os.path.getsize(path) > 8000
    except Exception:
        return False


def fetch_photos(queries: List[str], outdir: str, per_query: int = 3,
                 limit: int = 12) -> List[Dict]:
    """Download real photos for the given topical queries.

    Returns records: {path, license, creator, source, title}. Prefers
    no-attribution licenses but keeps BY/BY-SA (with creator) as well.
    """
    os.makedirs(outdir, exist_ok=True)
    cands: List[Dict] = []
    for q in queries:
        cands += search_openverse(q, per_query + 2)
        if len(cands) < per_query * len(queries):
            cands += search_commons(q, per_query)
    # prefer CC0/PDM first, then the rest
    cands.sort(key=lambda c: 0 if any(k in c["license"] for k in NO_ATTR) else 1)

    got: List[Dict] = []
    i = 0
    for c in cands:
        if len(got) >= limit:
            break
        p = os.path.join(outdir, f"photo_{i:03d}.jpg")
        i += 1
        try:
            data = _get(c["url"], timeout=30)
            with open(p, "wb") as f:
                f.write(data)
            if _valid_image(p):
                c2 = dict(c)
                c2["path"] = p
                got.append(c2)
            else:
                os.remove(p)
        except Exception:
            try:
                os.remove(p)
            except OSError:
                pass
    return got


def attribution_lines(photos: List[Dict]) -> List[str]:
    """Human-readable credit lines for BY / BY-SA images (skip CC0/PDM)."""
    lines = []
    for ph in photos:
        if any(k in ph["license"] for k in NO_ATTR):
            continue
        cr = ph.get("creator") or "unknown"
        lines.append(f'\"{ph.get("title","")}\" by {cr} ({ph["license"].upper()}) via {ph["source"]}')
    return lines


# Topical photo queries per repo — chosen to give a realistic, attention-grabbing
# visual that still relates to what the tool actually does.
REPO_QUERIES: Dict[str, List[str]] = {
    "codegraph-mcp": ["source code screen", "data network", "server room", "programmer working"],
    "agentledger": ["security padlock", "audit documents", "data center", "fingerprint identity"],
    "sentinel-policy": ["security control room", "shield protection", "command center", "cyber security"],
    "repo-warden": ["code review developer", "software engineer", "guard tower", "open source"],
    "cyclework": ["industrial gears", "automation machine", "factory robotics", "workflow"],
    "creatorforge": ["video production studio", "film camera", "content creator", "broadcast studio"],
    "accountable-ai-suite": ["artificial intelligence", "data governance", "neural network", "audit compliance"],
}


def photos_for(repo: str, outdir: str, limit: int = 10) -> List[Dict]:
    return fetch_photos(REPO_QUERIES.get(repo, [repo, "technology", "software"]),
                        outdir, per_query=3, limit=limit)
