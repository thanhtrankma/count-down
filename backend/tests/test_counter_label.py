import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from app.models.schemas import CounterMode, RenderConfig, RenderStyle
from app.utils.counter_label import (
    display_seconds_at,
    prev_display_seconds_at,
    thumbnail_seek_seconds,
    validate_countup_range,
)


def test_countdown_display_seconds():
    assert display_seconds_at("countdown", 3600, 0) == 3600
    assert display_seconds_at("countdown", 3600, 60) == 3540  # 00:59:00


def test_countup_display_seconds():
    assert display_seconds_at("countup", 0, 0) == 0
    assert display_seconds_at("countup", 0, 59) == 59
    assert display_seconds_at("countup", 1800, 120) == 1920


def test_prev_display_seconds_countdown():
    assert prev_display_seconds_at("countdown", 3600, 0) == 3600
    assert prev_display_seconds_at("countdown", 3600, 60) == 3541


def test_prev_display_seconds_countup():
    assert prev_display_seconds_at("countup", 10, 0) == 10
    assert prev_display_seconds_at("countup", 10, 1) == 10


def test_validate_countup_range_ok():
    validate_countup_range(0, 60)
    validate_countup_range(359940, 60)


def test_thumbnail_seek_seconds():
    assert thumbnail_seek_seconds("countdown", 60) == 0.0
    assert thumbnail_seek_seconds("countup", 60) == 59.0
    assert thumbnail_seek_seconds("countup", 1) == 0.0


def test_validate_countup_range_overflow():
    with pytest.raises(ValueError, match="99:59:59"):
        validate_countup_range(359940, 120)


def test_render_config_countup_overflow_validation():
    with pytest.raises(ValidationError):
        RenderConfig(
            start_time="99:59:00",
            counter_mode=CounterMode.COUNTUP,
            duration_seconds=120,
            style=RenderStyle(),
        )
