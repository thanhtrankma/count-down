import math
from enum import Enum
from typing import Optional


class CountdownAnimation(str, Enum):
    NONE = "none"
    FADE = "fade"
    SCALE = "scale"
    SLIDE_UP = "slide_up"
    FLIP = "flip"
    CIRCLE = "circle"


def clamp_intensity(intensity: float) -> float:
    return max(0.5, min(1.5, float(intensity)))


def _ms(base: int, intensity: float) -> int:
    """Higher intensity → snappier (shorter) transitions."""
    return max(50, int(base / clamp_intensity(intensity)))


def _scale_pct(base: float, intensity: float) -> float:
    return base * clamp_intensity(intensity)


def countdown_center(width: int, height: int) -> tuple[int, int]:
    return width // 2, height // 2


def circle_progress(
    start_seconds: int,
    second_index: int,
    total_seconds: int,
) -> float:
    remaining = max(0, start_seconds - second_index)
    if total_seconds <= 0:
        return 0.0
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
        # Number layer uses a subtle fade; arc is a separate dialogue.
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
        # Split-flap handled by build_flip_dialogues(); no inline tags on number line.
        return ""

    return ""


def build_flip_dialogues(
    *,
    start_ts: str,
    end_ts: str,
    label: str,
    prev_label: str,
    width: int,
    height: int,
    intensity: float = 1.0,
) -> list[str]:
    """Split-flap clock: bottom static, top static (new), top flap (old) folding down."""
    cx, cy = countdown_center(width, height)
    mid_ms = _ms(400, intensity)
    end_ms = _ms(1000, intensity)

    clip_top = f"\\clip(0,0,{width},{cy})"
    clip_bottom = f"\\clip(0,{cy},{width},{height})"
    pos = f"\\an5\\pos({cx},{cy})"

    bottom = (
        f"Dialogue: 0,{start_ts},{end_ts},Countdown,,0,0,0,,"
        f"{{{clip_bottom}{pos}}}{label}"
    )
    top_new = (
        f"Dialogue: 1,{start_ts},{end_ts},Countdown,,0,0,0,,"
        f"{{{clip_top}{pos}}}{label}"
    )
    top_flap = (
        f"Dialogue: 2,{start_ts},{end_ts},Countdown,,0,0,0,,"
        f"{{{clip_top}{pos}\\frx0\\t(0,{mid_ms},\\frx90)\\t({mid_ms},{end_ms},\\frx90)}}{prev_label}"
    )
    return [bottom, top_new, top_flap]


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
    intensity: float = 1.0,
) -> str:
    """Vector arc on layer 0; sweep reflects remaining time fraction."""
    cx, cy = countdown_center(width, height)
    progress = circle_progress(start_seconds, second_index, total_seconds)
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
