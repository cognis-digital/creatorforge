import pytest

from creatorforge.calendar import build_calendar
from creatorforge.ideas import generate_ideas
from creatorforge.platforms import package, platform_spec
from creatorforge.voice import VoiceProfile


def test_x_package_within_limit():
    core = {"topic": "AI agents", "hook": "The truth about AI agents nobody tells you",
            "summary": "Here is the one thing that matters.", "niche": "ai agents"}
    pkg = package(core, "x", VoiceProfile())
    assert len(pkg["caption"]) <= 280
    assert len(pkg["hashtags"]) <= platform_spec("x")["hashtags"]


def test_youtube_title_clipped():
    long_hook = "How to " + "really " * 40 + "win"
    core = {"topic": "x", "hook": long_hook, "summary": "", "niche": "x"}
    pkg = package(core, "youtube", VoiceProfile())
    assert len(pkg["title"]) <= 100


def test_unknown_platform_raises():
    with pytest.raises(ValueError):
        platform_spec("myspace")


def test_calendar_slot_count_and_order():
    ideas = generate_ideas("fitness", VoiceProfile(), 12)
    cal = build_calendar(ideas, "2026-07-06", per_week=3, weeks=4)  # 2026-07-06 is a Monday
    assert len(cal) == 12
    dates = [c["date"] for c in cal]
    assert dates == sorted(dates)                 # chronological
    assert {c["platform"] for c in cal}           # platforms assigned


def test_calendar_empty_ideas():
    assert build_calendar([], "2026-07-06") == []
