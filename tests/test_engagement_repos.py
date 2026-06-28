from creatorforge.camera import CAMERA_MOVES, coverage, multicam_plan
from creatorforge.engagement import engagement_plan, retention_move
from creatorforge.growth import GROWTH_PLAYS, launch_strategy
from creatorforge.longform import LongformBrief, build_longform
from creatorforge.repos import parse_readme
from creatorforge.styles import get_style


def test_coverage_has_cameras_and_moves():
    shots = coverage("climax", "the turning point", "AI agents", get_style("epic_doc"), 3)
    assert len(shots) == 3
    assert all(s["cam"] and s["move"] in CAMERA_MOVES for s in shots)
    # climax reaches for a signature/cool move
    assert any(s["move"] in ("dolly_zoom", "drone_reveal", "orbit") for s in shots)


def test_multicam_plan_summarizes():
    plan = build_longform(LongformBrief(topic="x", format="documentary"))
    mc = plan["multicam"]
    assert mc["cameras_needed"] and "A" in mc["cameras_needed"]
    assert mc["signature_shots"] >= 1


def test_engagement_plan_and_per_beat_moves():
    ep = engagement_plan("documentary", "epic_doc")
    assert ep["filmmaker_techniques"] and ep["retention_tactics"] and ep["principles"]
    assert "loop" in retention_move("cold_open").lower()
    assert retention_move("climax")


def test_longform_scenes_carry_coverage_and_retention():
    plan = build_longform(LongformBrief(topic="owning your AI stack", format="documentary"))
    assert "engagement_plan" in plan
    for s in plan["scenes"]:
        assert s["shots"] and "cam" in s["shots"][0]
        assert s["retention_move"]


def test_parse_readme_extracts_title_and_features():
    md = ("# AwesomeTool\n\n"
          "[![CI](badge)](x)\n\n"
          "A tiny tool that does one thing well.\n\n"
          "## Features\n- fast\n- offline\n- no deps\n")
    meta = parse_readme(md)
    assert meta["title"] == "AwesomeTool"
    assert meta["description"].startswith("A tiny tool")
    assert "fast" in meta["features"]


def test_launch_strategy_is_a_calendar():
    strat = launch_strategy("codegraph-mcp", "code knowledge graph for agents", "dev tools")
    assert strat["content_calendar"] and strat["plays"] == GROWTH_PLAYS
    days = [c["day"] for c in strat["content_calendar"]]
    assert days == sorted(days) and days[0] == 1
    assert all(c["title"] for c in strat["content_calendar"])
