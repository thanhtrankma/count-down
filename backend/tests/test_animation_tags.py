import sys
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from app.services.animation_tags import (
    CountdownAnimation,
    build_circle_dialogue,
    build_flip_second_dialogues,
    build_flip_segment_dialogues,
    circle_progress,
    compute_flip_layout,
    flip_duration_ms,
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


def test_flip_duration_matches_shared_timing():
    assert flip_duration_ms(1.0) == 350
    assert flip_duration_ms(0.5) == 700
    assert flip_duration_ms(1.5) == 233


def test_flip_bottom_half_shows_prev_during_animation():
    layout = compute_flip_layout(1920, 1080, 120, ["00", "04", "59"]).segments[1]
    lines = build_flip_segment_dialogues(
        start_ts="0:00:01.00",
        end_ts="0:00:02.00",
        layout=layout,
        label_part="04",
        prev_part="05",
        intensity=1.0,
    )
    bottom = next(line for line in lines if line.startswith("Dialogue: 1,"))
    bottom_text = bottom.split(",,0,0,0,,", 1)[1]
    assert bottom_text.endswith("05")
    assert not bottom_text.endswith("04")


def test_flip_segment_diff_only_changed_segment_flips():
    lines = build_flip_second_dialogues(
        start_ts="0:00:01.00",
        end_ts="0:00:02.00",
        label="00:01:09",
        prev_label="00:01:10",
        width=1920,
        height=1080,
        font_size=120,
        intensity=1.0,
    )
    frx_lines = [line for line in lines if "\\frx" in line]
    assert len(frx_lines) == 1
    frx_text = frx_lines[0].split(",,0,0,0,,", 1)[1]
    assert frx_text.endswith("10")
    assert "00:01:10" not in frx_text


def test_flip_uses_panel_rect_clips_not_full_screen():
    width = 1920
    height = 1080
    font_size = 120
    lines = build_flip_second_dialogues(
        start_ts="0:00:01.00",
        end_ts="0:00:02.00",
        label="00:00:59",
        prev_label="00:01:00",
        width=width,
        height=height,
        font_size=font_size,
        intensity=1.0,
    )
    layout = compute_flip_layout(width, height, font_size, ["00", "00", "59"])
    panel = layout.segments[2]
    clip_lines = [line for line in lines if "\\clip(" in line]
    assert clip_lines
    assert not any(f"\\clip(0,0,{width}," in line for line in clip_lines)

    left = int(panel.x - panel.panel_width / 2)
    right = int(panel.x + panel.panel_width / 2)
    assert any(f"\\clip({left}," in line for line in clip_lines)
    assert any(f",{right}," in line or f",{right})" in line for line in clip_lines)


def test_flip_duration_in_ass_tags():
    lines = build_flip_second_dialogues(
        start_ts="0:00:01.00",
        end_ts="0:00:02.00",
        label="00:00:59",
        prev_label="00:01:00",
        width=1920,
        height=1080,
        font_size=120,
        intensity=1.0,
    )
    frx_line = next(line for line in lines if "\\frx" in line)
    assert "\\t(0," in frx_line
    assert ",350," in frx_line or ",350\\" in frx_line
    assert "\\alpha&HFF&" in frx_line


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


def test_circle_progress_countup_increases():
    assert circle_progress(0, 0, 60, "countup") == pytest.approx(0.0)
    assert circle_progress(0, 30, 60, "countup") == pytest.approx(30 / 59)
    assert circle_progress(0, 59, 60, "countup") == pytest.approx(1.0)


def test_circle_progress_countup_single_second():
    assert circle_progress(0, 0, 1, "countup") == pytest.approx(0.0)


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
