import os

import pytest

from creatorforge.hardware import ffmpeg_exe
from creatorforge.record import Capture, capture, render_terminal


def test_capture_runs_a_real_command():
    c = capture('python -c "print(\'hello from a real run\')"')
    assert c.returncode == 0
    assert "hello from a real run" in c.output
    assert c.seconds >= 0
    assert c.lines()[0].startswith("$ ")


def test_capture_records_nonzero_exit():
    c = capture('python -c "import sys; sys.exit(3)"')
    assert c.returncode == 3


def test_render_terminal_when_ffmpeg_present(tmp_path):
    if not ffmpeg_exe():
        pytest.skip("ffmpeg not available")
    cap = capture('python -c "print(1); print(2); print(3)"')
    res = render_terminal([cap], str(tmp_path / "t"), fps=6, lines_per_sec=6)
    assert res["backend"] == "terminal-cast"
    assert os.path.exists(res["path"]) and res["frames"] > 0
