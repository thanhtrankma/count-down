import sys
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from app.services.animation_tags import (
    CountdownAnimation,
    build_circle_dialogue,
    circle_progress,
    get_countdown_override_tags,
)


def test_none_returns_empty_tags():
    assert get_countdown_override_tags("none", 1920, 1080, 120, 0, 60) == ""


def test_fade_contains_fad():
    tags = get_countdown_override_tags("fade", 1920, 1080, 120, 0, 60, 1.0)
    assert "\\fad(" in tags


def test_scale_contains_fscx():
    tags = get_countdown_override_tags("scale", 1920, 1080, 120, 0, 60, 1.0)
    assert "\\fscx" in tags
    assert "\\t(" in tags


def test_slide_up_contains_move():
    tags = get_countdown_override_tags("slide_up", 1920, 1080, 120, 0, 60, 1.0)
    assert "\\move(" in tags
    assert "540" in tags  # cy + offset for 1080 height


def test_flip_uses_split_flap_dialogues():
    from app.services.animation_tags import build_flip_dialogues

    lines = build_flip_dialogues(
        start_ts="0:00:01.00",
        end_ts="0:00:02.00",
        label="00:00:59",
        prev_label="00:01:00",
        width=1920,
        height=1080,
        intensity=1.0,
    )
    assert len(lines) == 3
    assert all("\\clip(" in line for line in lines)
    assert any("\\frx" in line for line in lines)


def test_flip_override_tags_empty():
    tags = get_countdown_override_tags("flip", 1920, 1080, 120, 1, 60, 1.0)
    assert tags == ""


def test_intensity_scales_fade_duration():
    subtle = get_countdown_override_tags("fade", 1920, 1080, 120, 0, 60, 0.5)
    strong = get_countdown_override_tags("fade", 1920, 1080, 120, 0, 60, 1.5)
    assert subtle != strong


def test_circle_progress_clamped():
    assert circle_progress(60, 0, 60) == pytest.approx(1.0)
    assert circle_progress(60, 30, 60) == pytest.approx(0.5)
    assert circle_progress(60, 60, 60) == pytest.approx(0.0)


def test_build_circle_dialogue_contains_vector_path():
    line = build_circle_dialogue(
        start_ts="0:00:00.00",
        end_ts="0:00:01.00",
        width=1920,
        height=1080,
        font_size=120,
        ass_color="&HFFFFFF&",
        start_seconds=60,
        second_index=0,
        total_seconds=60,
        intensity=1.0,
    )
    assert line.startswith("Dialogue:")
    assert "\\p1" in line
    assert "m 0.0" in line


def test_build_circle_dialogue_empty_when_no_progress():
    line = build_circle_dialogue(
        start_ts="0:00:59.00",
        end_ts="0:01:00.00",
        width=1920,
        height=1080,
        font_size=120,
        ass_color="&HFFFFFF&",
        start_seconds=60,
        second_index=60,
        total_seconds=60,
        intensity=1.0,
    )
    assert line == ""
