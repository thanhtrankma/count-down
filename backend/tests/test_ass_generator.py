import re
import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from app.models.schemas import CountdownAnimation, RenderConfig, RenderStyle
from app.services.ass_generator import ASSGenerator
from app.utils.time_format import format_ass_timestamp, format_time, parse_time

DIALOGUE_PATTERN = re.compile(r"^Dialogue:", re.MULTILINE)


def test_format_time():
    assert format_time(0) == "00:00:00"
    assert format_time(59) == "00:00:59"
    assert format_time(60) == "00:01:00"
    assert format_time(3661) == "01:01:01"


def test_parse_time():
    assert parse_time("00:00:00") == 0
    assert parse_time("00:01:00") == 60
    assert parse_time("03:00:00") == 10800


def test_format_ass_timestamp():
    assert format_ass_timestamp(0) == "0:00:00.00"
    assert format_ass_timestamp(1) == "0:00:01.00"
    assert format_ass_timestamp(61.5) == "0:01:01.50"


def test_dialogue_event_count_matches_duration():
    config = RenderConfig(
        start_time="00:01:00",
        duration_seconds=60,
        style=RenderStyle(),
    )
    generator = ASSGenerator()
    ass_path = generator.generate(config, output_dir=Path("/tmp/countdown-test-ass"))
    content = Path(ass_path).read_text(encoding="utf-8-sig")

    countdown_dialogues = [
        line for line in content.splitlines()
        if line.startswith("Dialogue:") and ",Countdown," in line
    ]
    assert len(countdown_dialogues) == config.duration_seconds


def test_dialogue_event_count_with_title():
    config = RenderConfig(
        start_time="00:01:00",
        duration_seconds=60,
        title="Event Title",
        style=RenderStyle(),
    )
    generator = ASSGenerator()
    ass_path = generator.generate(config, output_dir=Path("/tmp/countdown-test-ass-title"))
    content = Path(ass_path).read_text(encoding="utf-8-sig")

    countdown_dialogues = [
        line for line in content.splitlines()
        if line.startswith("Dialogue:") and ",Countdown," in line
    ]
    assert len(countdown_dialogues) == config.duration_seconds


@pytest.mark.parametrize(
    "animation,needle",
    [
        (CountdownAnimation.FADE, "\\fad("),
        (CountdownAnimation.SCALE, "\\fscx"),
        (CountdownAnimation.SLIDE_UP, "\\move("),
        (CountdownAnimation.FLIP, "\\clip("),
    ],
)
def test_countdown_animation_tags_in_dialogue(animation, needle):
    config = RenderConfig(
        start_time="00:01:00",
        duration_seconds=3,
        style=RenderStyle(animation=animation, animation_intensity=1.0),
    )
    generator = ASSGenerator()
    ass_path = generator.generate(config, output_dir=Path("/tmp/countdown-test-anim"))
    content = Path(ass_path).read_text(encoding="utf-8-sig")
    assert needle in content


def test_circle_animation_adds_vector_and_layered_dialogues():
    config = RenderConfig(
        start_time="00:01:00",
        duration_seconds=3,
        style=RenderStyle(animation=CountdownAnimation.CIRCLE),
    )
    generator = ASSGenerator()
    ass_path = generator.generate(config, output_dir=Path("/tmp/countdown-test-circle"))
    content = Path(ass_path).read_text(encoding="utf-8-sig")

    assert "\\p1" in content
    circle_dialogues = [line for line in content.splitlines() if line.startswith("Dialogue: 0,")]
    number_dialogues = [line for line in content.splitlines() if line.startswith("Dialogue: 1,")]
    assert len(circle_dialogues) == 3
    assert len(number_dialogues) == 3


def test_custom_font_name_in_style_line():
    config = RenderConfig(
        start_time="00:01:00",
        duration_seconds=3,
        style=RenderStyle(font_name="Bebas Neue", font_id="bebas-neue"),
    )
    generator = ASSGenerator()
    ass_path = generator.generate(config, output_dir=Path("/tmp/countdown-test-font"))
    content = Path(ass_path).read_text(encoding="utf-8-sig")

    assert "Style: Countdown,Bebas Neue," in content


def test_countdown_labels():
    config = RenderConfig(
        start_time="00:01:00",
        duration_seconds=3,
        style=RenderStyle(),
    )
    generator = ASSGenerator()
    ass_path = generator.generate(config, output_dir=Path("/tmp/countdown-test-labels"))
    content = Path(ass_path).read_text(encoding="utf-8-sig")

    assert "00:01:00" in content
    assert "00:00:59" in content
    assert "00:00:58" in content


@pytest.mark.parametrize(
    "start_time,duration_seconds",
    [
        ("00:00:00", 0),
        ("00:01:00", 28801),
        ("00:60:00", 60),
        ("00:00:60", 60),
        ("1:00:00", 60),
    ],
)
def test_render_config_validation(start_time: str, duration_seconds: int):
    with pytest.raises(ValidationError):
        RenderConfig(start_time=start_time, duration_seconds=duration_seconds)
