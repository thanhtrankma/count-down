MAX_DISPLAY_SECONDS = 99 * 3600 + 59 * 60 + 59


def display_seconds_at(
    counter_mode: str,
    start_seconds: int,
    second_index: int,
) -> int:
    if counter_mode == "countup":
        return start_seconds + second_index
    return max(0, start_seconds - second_index)


def prev_display_seconds_at(
    counter_mode: str,
    start_seconds: int,
    second_index: int,
) -> int:
    if second_index <= 0:
        return display_seconds_at(counter_mode, start_seconds, second_index)
    return display_seconds_at(counter_mode, start_seconds, second_index - 1)


def validate_countup_range(start_seconds: int, duration_seconds: int) -> None:
    if start_seconds + (duration_seconds - 1) > MAX_DISPLAY_SECONDS:
        raise ValueError("Count up would exceed 99:59:59")


def thumbnail_seek_seconds(counter_mode: str, duration_seconds: int) -> float:
    """Thumbnail frame: t=0 for countdown, last labeled second for count-up."""
    if counter_mode == "countup":
        return float(max(0, duration_seconds - 1))
    return 0.0
