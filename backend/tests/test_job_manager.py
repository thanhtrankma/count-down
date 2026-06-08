import asyncio
import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from app.exceptions import ConcurrentJobLimitError
from app.models.schemas import JobStatus, RenderConfig, RenderStyle
from app.services.job_manager import JobManager


@pytest.fixture
def manager() -> JobManager:
    return JobManager()


def test_has_active_job_false_when_empty(manager: JobManager):
    assert manager.has_active_job() is False


@pytest.mark.asyncio
async def test_rejects_second_concurrent_job(manager: JobManager):
    config = RenderConfig(
        start_time="00:01:00",
        duration_seconds=60,
        style=RenderStyle(),
    )

    with patch.object(manager, "_run_job", new_callable=AsyncMock) as mock_run:
        mock_run.return_value = None
        job_id, _, _ = await manager.create_job(config)

        entry = manager._jobs[job_id]
        entry.job.status = JobStatus.RUNNING

        with pytest.raises(ConcurrentJobLimitError):
            await manager.create_job(config)


def test_ffmpeg_command_includes_audio_when_tick_enabled():
    from app.services.ffmpeg_runner import FFmpegRunner

    config = RenderConfig(
        start_time="00:01:00",
        duration_seconds=10,
        audio_tick=True,
        style=RenderStyle(),
    )

    with patch.object(FFmpegRunner, "_ffmpeg_path", return_value="ffmpeg"):
        command = FFmpegRunner().build_command(
            "/tmp/test.ass",
            config,
            "/tmp/out.mp4",
            tick_audio_path="/tmp/tick.wav",
        )

    assert "-i" in command
    assert "/tmp/tick.wav" in command
    assert "-c:a" in command
    assert "aac" in command


def test_ffmpeg_command_includes_fontsdir_when_fonts_dir_set():
    from app.services.ffmpeg_runner import FFmpegRunner

    config = RenderConfig(
        start_time="00:01:00",
        duration_seconds=10,
        style=RenderStyle(),
    )

    with patch.object(FFmpegRunner, "_ffmpeg_path", return_value="ffmpeg"):
        with patch(
            "app.services.ffmpeg_runner.fonts_dir_for_render",
            return_value=Path("/tmp/custom-fonts"),
        ):
            command = FFmpegRunner().build_command(
                "/tmp/test.ass",
                config,
                "/tmp/out.mp4",
            )

    filter_arg_index = command.index("-vf") + 1
    assert "fontsdir=/tmp/custom-fonts" in command[filter_arg_index]


def test_ffmpeg_command_video_only_without_tick():
    from app.services.ffmpeg_runner import FFmpegRunner

    config = RenderConfig(
        start_time="00:01:00",
        duration_seconds=10,
        style=RenderStyle(),
    )

    with patch.object(FFmpegRunner, "_ffmpeg_path", return_value="ffmpeg"):
        command = FFmpegRunner().build_command(
            "/tmp/test.ass",
            config,
            "/tmp/out.mp4",
        )

    assert command.count("-i") == 1
    assert "-c:a" not in command
