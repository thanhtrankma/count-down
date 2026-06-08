import asyncio
import os
import shutil
import sys
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from app.config import OUTPUT_DIR
from app.models.schemas import JobStatus, RenderConfig, RenderStyle
from app.services.job_manager import JobManager


def _ffmpeg_available() -> bool:
    return shutil.which("ffmpeg") is not None


@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.asyncio
async def test_render_3600s_integration():
    if not _ffmpeg_available():
        pytest.skip("FFmpeg not available")

    manager = JobManager()
    config = RenderConfig(
        start_time="01:00:00",
        duration_seconds=3600,
        resolution="640x360",
        style=RenderStyle(font_size=48),
        audio_tick=False,
    )

    job_id, _, _ = await manager.create_job(config)
    entry = manager._jobs[job_id]

    timeout_seconds = int(os.environ.get("INTEGRATION_RENDER_TIMEOUT", "900"))
    try:
        await asyncio.wait_for(entry.task, timeout=timeout_seconds)
    except asyncio.TimeoutError:
        await manager.cancel_job(job_id)
        pytest.fail(f"3600s render did not complete within {timeout_seconds}s")

    job = manager.get_job(job_id)
    assert job is not None
    assert job.status == JobStatus.COMPLETED, job.error
    assert job.progress == 100.0

    output_path = Path(job.output_path or "")
    assert output_path.is_file()
    assert output_path.stat().st_size > 100_000

    if job_id:
        stale = OUTPUT_DIR / f"{job_id}.mp4"
        if stale.exists():
            stale.unlink()
