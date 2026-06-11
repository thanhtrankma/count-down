import re
from typing import Optional

OUT_TIME_US_PATTERN = re.compile(r"^out_time_us=(\d+)$", re.MULTILINE)


def parse_progress_file(content: str, total_seconds: float) -> Optional[float]:
    matches = OUT_TIME_US_PATTERN.findall(content)
    if not matches or total_seconds <= 0:
        return None
    elapsed = int(matches[-1]) / 1_000_000
    return min(100.0, (elapsed / total_seconds) * 100.0)
