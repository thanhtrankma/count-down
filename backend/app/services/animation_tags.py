import json
import math
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional


class CountdownAnimation(str, Enum):
    NONE = "none"
    FADE = "fade"
    SCALE = "scale"
    SLIDE_UP = "slide_up"
    FLIP = "flip"
    CIRCLE = "circle"


_FLIP_TIMING_PATH = Path(__file__).resolve().parents[3] / "shared" / "animation_timing.json"
_FLIP_TIMING = json.loads(_FLIP_TIMING_PATH.read_text(encoding="utf-8"))["flip"]

# Layout ratios — mirrored in frontend/src/utils/flipLayout.ts
FLIP_PANEL_WIDTH_RATIO = 1.65
FLIP_PANEL_HEIGHT_RATIO = 1.4
FLIP_GAP_RATIO = 0.12
FLIP_COLON_SIZE_RATIO = 0.85
FLIP_COLON_MARGIN_RATIO = 0.04


@dataclass(frozen=True)
class SegmentLayout:
    x: int
    y: int
    panel_width: float
    panel_height: float
    text: str


@dataclass(frozen=True)
class ColonLayout:
    x: int
    y: int


@dataclass(frozen=True)
class FlipLayout:
    segments: tuple[SegmentLayout, ...]
    colons: tuple[ColonLayout, ...]


def clamp_intensity(intensity: float) -> float:
    lo = _FLIP_TIMING["intensity_min"]
    hi = _FLIP_TIMING["intensity_max"]
    return max(lo, min(hi, float(intensity)))


def flip_duration_ms(intensity: float) -> int:
    """Same formula as frontend transitionMs()."""
    base = _FLIP_TIMING["base_duration_ms"]
    minimum = _FLIP_TIMING["min_duration_ms"]
    return max(minimum, round(base / clamp_intensity(intensity)))


def _ms(base: int, intensity: float) -> int:
    """Higher intensity → snappier (shorter) transitions."""
    return max(50, int(base / clamp_intensity(intensity)))


def _scale_pct(base: float, intensity: float) -> float:
    return base * clamp_intensity(intensity)


def countdown_center(width: int, height: int) -> tuple[int, int]:
    return width // 2, height // 2


def _parse_ass_timestamp(ts: str) -> float:
    h_str, rest = ts.split(":", 1)
    m_str, s_cs = rest.split(":", 1)
    s_str, cs_str = s_cs.split(".")
    return (
        int(h_str) * 3600
        + int(m_str) * 60
        + int(s_str)
        + int(cs_str) / 100
    )


def _format_ass_timestamp(seconds: float) -> str:
    total_cs = max(0, int(round(seconds * 100)))
    cs = total_cs % 100
    total_s = total_cs // 100
    s = total_s % 60
    total_m = total_s // 60
    m = total_m % 60
    h = total_m // 60
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def compute_flip_layout(
    width: int,
    height: int,
    font_size: int,
    segments: list[str],
) -> FlipLayout:
    """Center HH | MM | SS panels on canvas; colons sit between panels."""
    panel_width = font_size * FLIP_PANEL_WIDTH_RATIO
    panel_height = font_size * FLIP_PANEL_HEIGHT_RATIO
    gap = font_size * FLIP_GAP_RATIO
    colon_width = font_size * (FLIP_COLON_SIZE_RATIO + 2 * FLIP_COLON_MARGIN_RATIO)

    item_count = len(segments) + max(0, len(segments) - 1)
    total_width = (
        len(segments) * panel_width
        + max(0, len(segments) - 1) * colon_width
        + max(0, item_count - 1) * gap
    )

    cx, cy = countdown_center(width, height)
    cursor = cx - total_width / 2
    segment_layouts: list[SegmentLayout] = []
    colon_layouts: list[ColonLayout] = []

    for index, text in enumerate(segments):
        if index > 0:
            cursor += gap
            colon_layouts.append(ColonLayout(x=int(cursor + colon_width / 2), y=cy))
            cursor += colon_width

        segment_layouts.append(
            SegmentLayout(
                x=int(cursor + panel_width / 2),
                y=cy,
                panel_width=panel_width,
                panel_height=panel_height,
                text=text,
            )
        )
        cursor += panel_width
        if index < len(segments) - 1:
            cursor += gap

    return FlipLayout(segments=tuple(segment_layouts), colons=tuple(colon_layouts))


def _panel_rect_path(panel_width: float, panel_height: float) -> str:
    return (
        f"m 0 0 l {panel_width:.1f} 0 "
        f"l {panel_width:.1f} {panel_height:.1f} l 0 {panel_height:.1f}"
    )


def _panel_bounds(layout: SegmentLayout) -> tuple[int, int, int, int]:
    cx, cy = layout.x, layout.y
    half_w = layout.panel_width / 2
    half_h = layout.panel_height / 2
    return (
        int(cx - half_w),
        int(cy - half_h),
        int(cx + half_w),
        int(cy + half_h),
    )


def build_flip_panel_background(
    *,
    start_ts: str,
    end_ts: str,
    layout: SegmentLayout,
) -> str:
    """Dark two-tone panel fill + hinge line on layer 0."""
    left = layout.x - layout.panel_width / 2
    top = layout.y - layout.panel_height / 2
    pw = layout.panel_width
    ph = layout.panel_height

    border = "&H505050&"
    border_w = max(2, int(layout.panel_height * 0.02))
    top_h = ph * 0.46

    top_rect = f"m 0 0 l {pw:.1f} 0 l {pw:.1f} {top_h:.1f} l 0 {top_h:.1f}"
    bottom_rect = (
        f"m 0 {top_h:.1f} l {pw:.1f} {top_h:.1f} "
        f"l {pw:.1f} {ph:.1f} l 0 {ph:.1f}"
    )
    outline = _panel_rect_path(pw, ph)
    hinge_h = max(1.0, layout.panel_height * 0.035)
    hinge_top = ph / 2 - hinge_h / 2
    hinge_path = (
        f"m 0 {hinge_top:.1f} l {pw:.1f} {hinge_top:.1f} "
        f"l {pw:.1f} {hinge_top + hinge_h:.1f} l 0 {hinge_top + hinge_h:.1f}"
    )

    tags = (
        f"{{\\p1\\an7\\pos({left:.1f},{top:.1f})"
        f"\\1c&H3A3A3A&\\3c{border}\\bord{border_w}}}"
        f"{outline} "
        f"{{\\1c&H3A3A3A&\\bord0}}{top_rect} "
        f"{{\\1c&H1C1C1C&}}{bottom_rect} "
        f"{{\\1c&H000000&\\bord0}}{hinge_path}{{\\p0}}"
    )
    return f"Dialogue: 0,{start_ts},{end_ts},Countdown,,0,0,0,,{tags}"


def _panel_clips(layout: SegmentLayout) -> tuple[str, str, str]:
    left, top, right, bottom = _panel_bounds(layout)
    cy = layout.y
    clip_full = f"\\clip({left},{top},{right},{bottom})"
    clip_top = f"\\clip({left},{top},{right},{cy})"
    clip_bottom = f"\\clip({left},{cy},{right},{bottom})"
    return clip_full, clip_top, clip_bottom


def build_flip_colon_dialogue(
    *,
    start_ts: str,
    end_ts: str,
    layout: ColonLayout,
    font_size: int,
) -> str:
    colon_fs = int(font_size * FLIP_COLON_SIZE_RATIO)
    tags = f"{{\\an5\\pos({layout.x},{layout.y})\\fs{colon_fs}}}"
    return f"Dialogue: 1,{start_ts},{end_ts},Countdown,,0,0,0,,{tags}:"


def build_flip_segment_dialogues(
    *,
    start_ts: str,
    end_ts: str,
    layout: SegmentLayout,
    label_part: str,
    prev_part: str,
    intensity: float = 1.0,
) -> list[str]:
    """One segment: static when unchanged; split-flap clip + \\frx when changed."""
    cx, cy = layout.x, layout.y
    _, top, _, bottom = _panel_bounds(layout)
    clip_full, clip_top, clip_bottom = _panel_clips(layout)
    pos_center = f"\\an5\\pos({cx},{cy})"
    pos_top = f"\\an8\\pos({cx},{top})"
    pos_bottom = f"\\an2\\pos({cx},{bottom})"

    if label_part == prev_part:
        return [
            (
                f"Dialogue: 1,{start_ts},{end_ts},Countdown,,0,0,0,,"
                f"{{{clip_full}{pos_center}}}{label_part}"
            )
        ]

    flip_ms = flip_duration_ms(intensity)
    flip_end_ts = _format_ass_timestamp(_parse_ass_timestamp(start_ts) + flip_ms / 1000)
    fade_start = max(1, int(flip_ms * 0.82))
    org = f"\\org({cx},{cy})"
    # Bottom = old digit, top = new digit, flap = old top half folding away.
    flap_tags = (
        f"{{{clip_top}{pos_top}{org}"
        f"\\frx0\\t(0,{fade_start},\\frx-90)"
        f"\\t({fade_start},{flip_ms},\\frx-90\\alpha&HFF&)}}"
    )

    return [
        (
            f"Dialogue: 1,{start_ts},{flip_end_ts},Countdown,,0,0,0,,"
            f"{{{clip_bottom}{pos_bottom}}}{prev_part}"
        ),
        (
            f"Dialogue: 2,{start_ts},{flip_end_ts},Countdown,,0,0,0,,"
            f"{{{clip_top}{pos_top}}}{label_part}"
        ),
        (
            f"Dialogue: 3,{start_ts},{flip_end_ts},Countdown,,0,0,0,,"
            f"{flap_tags}{prev_part}"
        ),
        (
            f"Dialogue: 1,{flip_end_ts},{end_ts},Countdown,,0,0,0,,"
            f"{{{clip_full}{pos_center}}}{label_part}"
        ),
    ]


def build_flip_second_dialogues(
    *,
    start_ts: str,
    end_ts: str,
    label: str,
    prev_label: str,
    width: int,
    height: int,
    font_size: int,
    intensity: float = 1.0,
) -> list[str]:
    """Per-second flip: 3 panels, static colons, segment-diff split-flap."""
    segments = label.split(":")
    prev_segments = prev_label.split(":")
    flip_layout = compute_flip_layout(width, height, font_size, segments)

    lines: list[str] = []
    for panel in flip_layout.segments:
        lines.append(
            build_flip_panel_background(
                start_ts=start_ts,
                end_ts=end_ts,
                layout=panel,
            )
        )

    for colon in flip_layout.colons:
        lines.append(
            build_flip_colon_dialogue(
                start_ts=start_ts,
                end_ts=end_ts,
                layout=colon,
                font_size=font_size,
            )
        )

    for index, panel in enumerate(flip_layout.segments):
        lines.extend(
            build_flip_segment_dialogues(
                start_ts=start_ts,
                end_ts=end_ts,
                layout=panel,
                label_part=segments[index],
                prev_part=prev_segments[index],
                intensity=intensity,
            )
        )

    return lines


def circle_progress(
    start_seconds: int,
    second_index: int,
    total_seconds: int,
    counter_mode: str = "countdown",
) -> float:
    if total_seconds <= 0:
        return 0.0
    if counter_mode == "countup":
        if total_seconds <= 1:
            return 0.0
        return max(0.0, min(1.0, second_index / (total_seconds - 1)))
    remaining = max(0, start_seconds - second_index)
    return max(0.0, min(1.0, remaining / total_seconds))


def get_countdown_override_tags(
    animation: str | CountdownAnimation,
    width: int,
    height: int,
    font_size: int,
    second_index: int,
    total_seconds: int,
    intensity: float = 1.0,
) -> str:
    anim = CountdownAnimation(animation) if isinstance(animation, str) else animation
    if anim == CountdownAnimation.NONE:
        return ""

    if anim == CountdownAnimation.CIRCLE:
        fade_in = _ms(200, intensity)
        fade_out = _ms(200, intensity)
        return f"{{\\fad({fade_in},{fade_out})}}"

    intensity = clamp_intensity(intensity)
    cx, cy = countdown_center(width, height)

    if anim == CountdownAnimation.FADE:
        fade_in = _ms(200, intensity)
        fade_out = _ms(200, intensity)
        return f"{{\\fad({fade_in},{fade_out})}}"

    if anim == CountdownAnimation.SCALE:
        peak = int(_scale_pct(120, intensity))
        peak_ms = _ms(250, intensity)
        settle_ms = _ms(750, intensity)
        return (
            f"{{\\t(0,{peak_ms},\\fscx{peak}\\fscy{peak})"
            f"\\t({peak_ms},{settle_ms},\\fscx100\\fscy100)}}"
        )

    if anim == CountdownAnimation.SLIDE_UP:
        offset = int(_scale_pct(80, intensity))
        move_ms = _ms(350, intensity)
        return f"{{\\move({cx},{cy + offset},{cx},{cy},0,{move_ms})}}"

    if anim == CountdownAnimation.FLIP:
        return ""

    return ""


def build_circle_dialogue(
    *,
    start_ts: str,
    end_ts: str,
    width: int,
    height: int,
    font_size: int,
    ass_color: str,
    start_seconds: int,
    second_index: int,
    total_seconds: int,
    counter_mode: str = "countdown",
    intensity: float = 1.0,
) -> str:
    """Vector arc on layer 0; sweep reflects elapsed or remaining time fraction."""
    cx, cy = countdown_center(width, height)
    progress = circle_progress(
        start_seconds, second_index, total_seconds, counter_mode
    )
    sweep = progress * 360.0
    if sweep <= 0.5:
        return ""

    radius = int(font_size * 1.35 * clamp_intensity(intensity))
    stroke = max(3, int(font_size * 0.04 * clamp_intensity(intensity)))

    path = _arc_path(0, 0, radius, -90.0, -90.0 + sweep)
    tags = (
        f"{{\\p1\\an5\\bord{stroke}\\1c{ass_color}\\3c{ass_color}"
        f"\\pos({cx},{cy})}}{path}{{\\p0}}"
    )
    return f"Dialogue: 0,{start_ts},{end_ts},Countdown,,0,0,0,,{tags}"


def _arc_path(cx: float, cy: float, radius: float, start_deg: float, end_deg: float) -> str:
    steps = max(12, int(abs(end_deg - start_deg) / 8))
    points: list[tuple[float, float]] = []
    for step in range(steps + 1):
        t = step / steps
        angle = math.radians(start_deg + (end_deg - start_deg) * t)
        points.append((cx + radius * math.cos(angle), cy + radius * math.sin(angle)))

    path = f"m {points[0][0]:.1f} {points[0][1]:.1f}"
    for x, y in points[1:]:
        path += f" l {x:.1f} {y:.1f}"
    return path
