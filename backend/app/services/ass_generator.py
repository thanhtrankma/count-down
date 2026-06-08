import re
from pathlib import Path

from app.config import TEMP_DIR
from app.models.schemas import RenderConfig
from app.services.animation_tags import (
    CountdownAnimation,
    build_circle_dialogue,
    build_flip_dialogues,
    get_countdown_override_tags,
)
from app.utils.time_format import format_ass_timestamp, format_time, parse_time

HEX_COLOR_PATTERN = re.compile(r"^#([0-9A-Fa-f]{6})$")


def hex_to_ass_color(hex_color: str) -> str:
    match = HEX_COLOR_PATTERN.match(hex_color)
    if not match:
        raise ValueError(f"Invalid hex color: {hex_color}")
    r = int(hex_color[1:3], 16)
    g = int(hex_color[3:5], 16)
    b = int(hex_color[5:7], 16)
    return f"&H{b:02X}{g:02X}{r:02X}"


def escape_ass_text(text: str) -> str:
    return text.replace("\\", "\\\\").replace("{", "\\{").replace("}", "\\}")


class ASSGenerator:
    def generate(self, config: RenderConfig, output_dir: Path | None = None) -> str:
        output_dir = output_dir or TEMP_DIR
        output_dir.mkdir(parents=True, exist_ok=True)

        ass_path = output_dir / f"countdown_{config.duration_seconds}s.ass"
        ass_path.write_text(self._build_ass(config), encoding="utf-8-sig")
        return str(ass_path)

    def _build_ass(self, config: RenderConfig) -> str:
        style = config.style
        primary_color = hex_to_ass_color(style.color)
        start_seconds = parse_time(config.start_time)
        width = config.width
        height = config.height
        animation = style.animation
        intensity = style.animation_intensity

        lines = [
            "[Script Info]",
            "ScriptType: v4.00+",
            f"PlayResX: {width}",
            f"PlayResY: {height}",
            "WrapStyle: 0",
            "ScaledBorderAndShadow: yes",
            "",
            "[V4+ Styles]",
            "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
            (
                f"Style: Countdown,{style.font_name},{style.font_size},{primary_color},"
                f"&H000000FF,&H00000000,&H80000000,0,0,0,0,100,100,0,0,1,2,0,5,20,20,20,1"
            ),
        ]

        if config.title:
            lines.append(
                f"Style: Title,{style.font_name},{style.title_font_size},{primary_color},"
                f"&H000000FF,&H00000000,&H80000000,0,0,0,0,100,100,0,0,1,2,0,8,20,20,80,1"
            )

        lines.extend(["", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"])

        if config.title:
            end_ts = format_ass_timestamp(config.duration_seconds)
            lines.append(
                f"Dialogue: 0,0:00:00.00,{end_ts},Title,,0,0,0,,{escape_ass_text(config.title)}"
            )

        use_circle = animation == CountdownAnimation.CIRCLE
        use_flip = animation == CountdownAnimation.FLIP

        for second in range(config.duration_seconds):
            remaining = start_seconds - second
            label = format_time(remaining)
            prev_label = format_time(remaining + 1) if second > 0 else label
            start_ts = format_ass_timestamp(second)
            end_ts = format_ass_timestamp(second + 1)

            if use_circle:
                circle_line = build_circle_dialogue(
                    start_ts=start_ts,
                    end_ts=end_ts,
                    width=width,
                    height=height,
                    font_size=style.font_size,
                    ass_color=primary_color,
                    start_seconds=start_seconds,
                    second_index=second,
                    total_seconds=config.duration_seconds,
                    intensity=intensity,
                )
                if circle_line:
                    lines.append(circle_line)

            if use_flip and second > 0:
                lines.extend(
                    build_flip_dialogues(
                        start_ts=start_ts,
                        end_ts=end_ts,
                        label=label,
                        prev_label=prev_label,
                        width=width,
                        height=height,
                        intensity=intensity,
                    )
                )
            else:
                tags = get_countdown_override_tags(
                    animation=animation,
                    width=width,
                    height=height,
                    font_size=style.font_size,
                    second_index=second,
                    total_seconds=config.duration_seconds,
                    intensity=intensity,
                )
                layer = 1 if use_circle else 0
                lines.append(
                    f"Dialogue: {layer},{start_ts},{end_ts},Countdown,,0,0,0,,{tags}{label}"
                )

        return "\n".join(lines) + "\n"

    def count_dialogue_events(self, config: RenderConfig) -> int:
        events = config.duration_seconds + (1 if config.title else 0)
        if config.style.animation == CountdownAnimation.CIRCLE:
            events += config.duration_seconds
        if config.style.animation == CountdownAnimation.FLIP:
            # Three layers per second after the first (no flip on second 0).
            events += max(0, config.duration_seconds - 1) * 2
        return events
