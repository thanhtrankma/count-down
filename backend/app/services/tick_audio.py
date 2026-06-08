import asyncio
import shutil
from pathlib import Path

from app.config import FFMPEG_CANDIDATE_PATHS, TEMP_DIR


def _ffmpeg_path() -> str:
    for candidate in FFMPEG_CANDIDATE_PATHS:
        if candidate and Path(candidate).is_file():
            return candidate

    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg:
        return ffmpeg

    raise RuntimeError("ffmpeg not found")


async def generate_tick_audio(duration_seconds: int, output_path: str | None = None) -> str:
    """Generate a mono WAV with a short tick at each second boundary."""
    target = output_path or str(TEMP_DIR / f"tick_{duration_seconds}s.wav")
    Path(target).parent.mkdir(parents=True, exist_ok=True)

    # Short sine burst at the start of each whole second.
    tick_expr = "0.35*sin(2*PI*1000*t)*between(mod(t,1),0,0.05)"
    command = [
        _ffmpeg_path(),
        "-y",
        "-f",
        "lavfi",
        "-i",
        f"aevalsrc='{tick_expr}':c=mono:s=44100:d={duration_seconds}",
        "-c:a",
        "pcm_s16le",
        target,
    ]

    process = await asyncio.create_subprocess_exec(
        *command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    _, stderr = await process.communicate()

    if process.returncode != 0:
        tail = stderr.decode("utf-8", errors="replace")[-500:]
        raise RuntimeError(f"tick audio generation failed: {tail}")

    return target
