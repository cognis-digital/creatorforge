import pytest

from creatorforge.audiogen import generate_music
from creatorforge.formats import FORMATS, allocate, get_format
from creatorforge.longform import LongformBrief, build_longform
from creatorforge.playbook import production_notes
from creatorforge.styles import STYLES, get_style
from creatorforge.voice import VoiceProfile


def test_formats_allocate_sums_to_runtime():
    fmt = get_format("documentary")
    alloc = allocate(fmt["beats"], 600)
    assert abs(sum(sec for _n, _p, sec in alloc) - 600) < 1.0   # distributes the runtime
    assert all(sec > 0 for _n, _p, sec in alloc)


def test_unknown_format_and_style_raise():
    with pytest.raises(ValueError):
        get_format("tiktok-dance")
    with pytest.raises(ValueError):
        get_style("nope")


def test_production_notes_are_actionable():
    n = production_notes("youtube_long", "documentary")
    assert n["hook_must_land_by_s"] <= 30
    assert n["re_hook_every_s"] > 0
    assert n["use_chapters"] is True
    assert n["retention_tactics"] and n["algorithm_optimizes_for"]


def test_build_longform_structure():
    brief = LongformBrief(topic="why founders should own their AI stack",
                          format="documentary", target_minutes=10)
    plan = build_longform(brief)
    # runtime is close to the requested 10 minutes
    assert abs(plan["runtime_seconds"] - 600) < 30
    # one chapter per beat, scenes have shots + narration + cues
    assert len(plan["chapters"]) == len(FORMATS["documentary"]["beats"])
    assert all(s["shots"] and s["narration"] and s["music_cue"] for s in plan["scenes"])
    assert plan["sound_cue_sheet"] and plan["pattern_interrupts_s"]
    assert plan["title_options"] and plan["thumbnail_concepts"]
    assert plan["narration_word_count"] > 300        # a real 10-min narration is long


def test_style_drives_pacing():
    fast = build_longform(LongformBrief(topic="x", format="devlog", style="kinetic_vlog"))
    slow = build_longform(LongformBrief(topic="x", format="devlog", style="arthouse_slowburn"))
    # faster style -> shorter scenes -> more shots for the same runtime
    fast_shots = sum(len(s["shots"]) for s in fast["scenes"])
    slow_shots = sum(len(s["shots"]) for s in slow["scenes"])
    assert fast_shots >= slow_shots


def test_all_formats_build():
    for name in FORMATS:
        plan = build_longform(LongformBrief(topic="a topic", format=name))
        assert plan["scenes"] and plan["runtime_seconds"] > 0


def test_generate_music_fallback(tmp_path):
    res = generate_music("sweeping orchestral, slow build", 2.0, str(tmp_path / "m"))
    assert res["backend"] in ("wave-bed", "music-small", "music-medium")
    import os
    assert os.path.exists(res["path"])
