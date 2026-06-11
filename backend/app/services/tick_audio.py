import asyncio
import shutil
import uuid
from pathlib import Path
from typing import Awaitable, Callable, Optional

from app.config import FFMPEG_CANDIDATE_PATHS, TEMP_DIR
from app.services.ffmpeg_progress import parse_progress_file


def _ffmpeg_path() -> str:
    for candidate in FFMPEG_CANDIDATE_PATHS:
        if candidate and Path(candidate).is_file():
            return candidate

    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg:
        return ffmpeg

    raise RuntimeError("ffmpeg not found")


async def generate_tick_audio(
    duration_seconds: int,
    output_path: str | None = None,
    on_progress: Optional[Callable[[float], Awaitable[None] | None]] = None,
) -> str:
    """Generate a mono WAV with a short tick at each second boundary."""
    target = output_path or str(TEMP_DIR / f"tick_{duration_seconds}s.wav")
    Path(target).parent.mkdir(parents=True, exist_ok=True)
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    progress_path = TEMP_DIR / f"tick_progress_{uuid.uuid4().hex}.txt"

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
        "-progress",
        str(progress_path),
        target,
    ]

    process = await asyncio.create_subprocess_exec(
        *command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stop_event = asyncio.Event()
    progress_task = asyncio.create_task(
        _poll_tick_progress(
            progress_path,
            duration_seconds,
            stop_event,
            on_progress,
        )
    )

    try:
        _, stderr = await process.communicate()
    finally:
        stop_event.set()
        await progress_task
        progress_path.unlink(missing_ok=True)

    if process.returncode != 0:
        tail = stderr.decode("utf-8", errors="replace")[-500:]
        raise RuntimeError(f"tick audio generation failed: {tail}")

    return target


async def _poll_tick_progress(
    progress_path: Path,
    total_seconds: int,
    stop_event: asyncio.Event,
    on_progress: Optional[Callable[[float], Awaitable[None] | None]] = None,
) -> None:
    while not stop_event.is_set():
        try:
            if progress_path.is_file():
                content = progress_path.read_text(encoding="utf-8", errors="replace")
                progress = parse_progress_file(content, float(total_seconds))
                if progress is not None and on_progress is not None:
                    result = on_progress(progress)
                    if asyncio.iscoroutine(result):
                        await result
        except OSError:
            pass

        try:
            await asyncio.wait_for(stop_event.wait(), timeout=0.5)
        except asyncio.TimeoutError:
            pass
