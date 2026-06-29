"""Smoke-test the demo scenarios — each must run fully offline and produce output.

The demos double as smoke tests for the public API; this guards them in CI so a
breaking API change is caught here too. No network, GPU, or model download.
"""
import importlib
import os
import sys

import pytest

DEMOS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "demos")
sys.path.insert(0, DEMOS_DIR)

SCENARIOS = [
    "01_creator_voice_to_post",
    "02_agency_full_pipeline",
    "03_devrel_repo_launch",
    "04_multiplatform_repurpose",
    "05_longform_studio",
]


@pytest.mark.parametrize("name", SCENARIOS)
def test_demo_runs_and_prints(name, capsys):
    mod = importlib.import_module(name)
    mod.main()                       # must not raise
    out = capsys.readouterr().out
    assert len(out) > 200            # produced real narrated output
    assert "=" * 10 in out           # printed its section rule


def test_run_all_imports():
    run_all = importlib.import_module("run_all")
    assert run_all.SCENARIOS == SCENARIOS


def test_sample_voice_is_deterministic():
    from _common import sample_voice
    v1, v2 = sample_voice(), sample_voice()
    assert v1.to_dict() == v2.to_dict()
    assert v1.samples == 5 and v1.energetic and v1.emoji_heavy
