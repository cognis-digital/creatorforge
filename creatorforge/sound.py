"""Sound engineering — a proper mix, not just a voice track.

Takes a finished video that already carries the narration and lays a royalty-free
(CC0 / public-domain) music bed underneath it: the music is volume-ducked far
below the voice, looped to length, and faded in and out. The voice is loudness-
normalized so it sits consistently on top. Music is sourced from the Internet
Archive's public-domain collections — never copyrighted songs or covers.
"""

from __future__ import annotations

import glob
import json
import os
import urllib.request
from typing import List, Optional

from .hardware import ffmpeg_exe


def _get(url: str, timeout: int = 300) -> bytes:
    return urllib.request.urlopen(
        urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}),
        timeout=timeout).read()


def find_cc0_tracks(query: str = "ambient instrumental", rows: int = 8) -> List[dict]:
    """Search the Internet Archive for genuinely public-domain (CC0) audio."""
    q = (f"https://archive.org/advancedsearch.php?q="
         f"({urllib.request.quote(query)})+AND+mediatype:(audio)+AND+"
         f"licenseurl:(*publicdomain*+OR+*zero*)"
         f"&fl[]=identifier&fl[]=title&rows={rows}&output=json")
    try:
        d = json.loads(_get(q, timeout=30))
        return d["response"]["docs"]
    except Exception:
        return []


def download_track(identifier: str, dest_dir: str) -> Optional[str]:
    """Download the smallest audio file for an IA item; verify it is CC0/PD."""
    os.makedirs(dest_dir, exist_ok=True)
    try:
        meta = json.loads(_get(f"https://archive.org/metadata/{identifier}", timeout=30))
        lic = meta.get("metadata", {}).get("licenseurl", "")
        if not any(k in lic for k in ("publicdomain", "zero")):
            return None
        audio = [(f["name"], int(f.get("size", "0") or 0))
                 for f in meta.get("files", [])
                 if f["name"].lower().endswith((".mp3", ".ogg"))]
        if not audio:
            return None
        audio.sort(key=lambda x: x[1] or 1 << 62)   # smallest real file first
        name = audio[0][0]
        out = os.path.join(dest_dir, "bed_" + "".join(c for c in name if c.isalnum() or c in "._-"))
        if not os.path.exists(out):
            url = f"https://archive.org/download/{identifier}/" + urllib.request.quote(name)
            with open(out, "wb") as f:
                f.write(_get(url))
        return out
    except Exception:
        return None


def ensure_bed(music_dir: str = r"C:\Users\user\_music") -> Optional[str]:
    """Return a cached CC0 music bed, downloading one if the cache is empty."""
    hits = sorted(glob.glob(os.path.join(music_dir, "*.mp3")) +
                  glob.glob(os.path.join(music_dir, "*.ogg")))
    if hits:
        return hits[0]
    for doc in find_cc0_tracks():
        p = download_track(doc["identifier"], music_dir)
        if p:
            return p
    return None


def mix_music(video_in: str, video_out: str, music_path: str,
              music_db: float = -20.0) -> dict:
    """Mix a CC0 music bed under a video's existing voice track.

    music_db: how far below unity the bed sits (negative dB). -20 keeps the
    narration clearly dominant. The bed loops to length and fades in/out.
    """
    import subprocess

    ff = ffmpeg_exe()
    gain = 10 ** (music_db / 20.0)
    # voice = input 0 audio (normalized); music = input 1 (looped, gained, faded)
    filt = (
        f"[0:a]loudnorm=I=-16:TP=-1.5:LRA=11[voice];"
        f"[1:a]volume={gain:.4f},afade=t=in:st=0:d=2,"
        f"aloop=loop=-1:size=2e9[music];"
        f"[voice][music]amix=inputs=2:duration=first:dropout_transition=3,"
        f"afade=t=out:st=0:d=0[mix]"
    )
    cmd = [ff, "-y", "-i", video_in, "-stream_loop", "-1", "-i", music_path,
           "-filter_complex", filt, "-map", "0:v", "-map", "[mix]",
           "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", video_out]
    proc = subprocess.run(cmd, capture_output=True)
    if proc.returncode != 0:
        raise RuntimeError("ffmpeg mix failed: " +
                           proc.stderr.decode("utf-8", "replace")[-400:])
    return {"path": video_out, "music": os.path.basename(music_path), "music_db": music_db}
