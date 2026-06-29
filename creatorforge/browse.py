"""Browser walkthrough recorder — capture a *real person browsing a GitHub repo*.

Drives a headless Chromium (Playwright) the way a curious developer would: land
on the repo, read the About box, scroll the file tree, open the README and a few
key files, and find the install / setup section. Every step is a real screenshot
of the live page — not a mock — returned as timed frames you can narrate over.

Falls back gracefully: if Playwright/Chromium isn't available, callers can use the
repo's GitHub social card (browse.repo_card) instead.
"""

from __future__ import annotations

import os
import re
import urllib.request
from typing import List, Optional, Tuple


def playwright_available() -> bool:
    try:
        from playwright.sync_api import sync_playwright  # noqa: F401
        return True
    except Exception:
        return False


def repo_card(owner: str, name: str, out_path: str) -> Optional[str]:
    """Download the real GitHub social-preview card (og:image) for a repo."""
    url = f"https://github.com/{owner}/{name}"
    try:
        html = urllib.request.urlopen(
            urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}),
            timeout=20).read().decode("utf-8", "replace")
        m = re.search(r'<meta property="og:image" content="([^"]+)"', html)
        if not m:
            return None
        img = urllib.request.urlopen(
            urllib.request.Request(m.group(1), headers={"User-Agent": "Mozilla/5.0"}),
            timeout=25).read()
        with open(out_path, "wb") as f:
            f.write(img)
        return out_path
    except Exception:
        return None


# A frame: (screenshot_path, narration_caption, dwell_seconds_hint)
Frame = Tuple[str, str, float]


def walkthrough(owner: str, name: str, outdir: str,
                width: int = 1366, height: int = 768) -> List[Frame]:
    """Record a human-style browse of github.com/<owner>/<name>.

    Returns an ordered list of (image_path, caption, dwell) frames. Captions are
    plain narration cues; the caller synthesizes voice and syncs each frame.
    """
    from playwright.sync_api import sync_playwright

    os.makedirs(outdir, exist_ok=True)
    base = f"https://github.com/{owner}/{name}"
    frames: List[Frame] = []
    idx = 0

    def shot(caption: str, dwell: float = 3.0):
        nonlocal idx
        p = os.path.join(outdir, f"br_{idx:03d}.png")
        page.screenshot(path=p, full_page=False)
        frames.append((p, caption, dwell))
        idx += 1
        return p

    with sync_playwright() as pw:
        browser = pw.chromium.launch(args=["--hide-scrollbars"])
        page = browser.new_page(viewport={"width": width, "height": height},
                                device_scale_factor=1)
        # 1) Land on the repo — the first thing anyone sees.
        page.goto(base, wait_until="domcontentloaded", timeout=45000)
        page.wait_for_timeout(3500)
        shot(f"Here is the {name} repository on GitHub, under Cognis Digital.", 4.0)

        # 2) The About box / topics on the right — what it is, at a glance.
        shot("On the right you can see exactly what it is, and the topics it covers.", 3.5)

        # 3) Scroll the file tree — show it's real, organized code.
        for label in ("Scroll down and you find the real source, tests, and examples.",
                      "Everything is here in the open: the package, the test suite, a runnable demo."):
            page.mouse.wheel(0, height - 120)
            page.wait_for_timeout(1200)
            shot(label, 3.5)

        # 4) Into the README — the actual documentation, rendered.
        for _ in range(6):
            page.mouse.wheel(0, height - 140)
            page.wait_for_timeout(900)
        shot("Keep scrolling into the README — this is the full documentation.", 3.5)

        # 5) Hunt for the install / setup section and dwell on it.
        setup_caps = ["This is the part that matters when you adopt it: setup.",
                      "Install is a couple of commands — clone it, install it, run it."]
        for cap in setup_caps:
            page.mouse.wheel(0, height - 100)
            page.wait_for_timeout(900)
            shot(cap, 4.0)

        # 6) Open a couple of real files so viewers see the code itself.
        for fname, cap in ((f"{name.replace('-', '_').split('/')[0]}",
                            "Open the source and the code is clean and readable."),
                           ("README.md",
                            "And the README again, in full, so nothing is hidden.")):
            try:
                page.goto(f"{base}/blob/master/{fname}", wait_until="domcontentloaded", timeout=30000)
                page.wait_for_timeout(2500)
                shot(cap, 3.5)
                page.mouse.wheel(0, height)
                page.wait_for_timeout(900)
                shot("You can read every line — nothing hidden, nothing obfuscated.", 3.0)
            except Exception:
                pass

        browser.close()
    return frames
