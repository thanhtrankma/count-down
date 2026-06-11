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


def test_list_active_jobs_empty(manager: JobManager):
    assert manager.list_active_jobs() == []


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


@pytest.mark.asyncio
async def test_completed_job_countup_thumbnail_seeks_last_frame(
    manager: JobManager, tmp_path: Path
):
    from app.models.schemas import CounterMode

    config = RenderConfig(
        start_time="00:00:00",
        counter_mode=CounterMode.COUNTUP,
        duration_seconds=30,
        resolution="640x360",
        style=RenderStyle(),
    )

    with patch("app.services.job_manager.OUTPUT_DIR", tmp_path):
        with patch(
            "app.services.job_manager.ASSGenerator.generate",
            return_value=str(tmp_path / "test.ass"),
        ):
            with patch(
                "app.services.job_manager.FFmpegRunner.run",
                new_callable=AsyncMock,
            ):
                with patch(
                    "app.services.job_manager.ThumbnailExtractor.extract",
                    new_callable=AsyncMock,
                    return_value=str(tmp_path / "thumb.jpg"),
                ) as mock_extract:
                    job_id, _, _ = await manager.create_job(config)
                    entry = manager._jobs[job_id]
                    await entry.task

    mock_extract.assert_awaited_once()
    assert mock_extract.await_args.kwargs["seek_seconds"] == 29.0


@pytest.mark.asyncio
async def test_completed_job_sets_thumbnail_path(manager: JobManager, tmp_path: Path):
    config = RenderConfig(
        start_time="00:01:00",
        duration_seconds=5,
        resolution="640x360",
        style=RenderStyle(),
    )

    with patch("app.services.job_manager.OUTPUT_DIR", tmp_path):
        with patch(
            "app.services.job_manager.ASSGenerator.generate",
            return_value=str(tmp_path / "test.ass"),
        ):
            with patch(
                "app.services.job_manager.FFmpegRunner.run",
                new_callable=AsyncMock,
            ):
                thumb_path = str(tmp_path / "thumb.jpg")
                with patch(
                    "app.services.job_manager.ThumbnailExtractor.extract",
                    new_callable=AsyncMock,
                    return_value=thumb_path,
                ) as mock_extract:
                    job_id, _, _ = await manager.create_job(config)
                    entry = manager._jobs[job_id]
                    await entry.task

    mock_extract.assert_awaited_once()
    assert mock_extract.await_args.kwargs["seek_seconds"] == 0.0
    job = manager.get_job(job_id)
    assert job is not None
    assert job.status == JobStatus.COMPLETED
    assert job.thumbnail_path == thumb_path


@pytest.mark.asyncio
async def test_completed_job_without_thumbnail_when_extract_fails(
    manager: JobManager, tmp_path: Path
):
    config = RenderConfig(
        start_time="00:01:00",
        duration_seconds=5,
        resolution="640x360",
        style=RenderStyle(),
    )

    with patch("app.services.job_manager.OUTPUT_DIR", tmp_path):
        with patch(
            "app.services.job_manager.ASSGenerator.generate",
            return_value=str(tmp_path / "test.ass"),
        ):
            with patch(
                "app.services.job_manager.FFmpegRunner.run",
                new_callable=AsyncMock,
            ) as mock_run:
                mock_run.return_value = str(tmp_path / "job.mp4")
                Path(tmp_path / "job.mp4").write_bytes(b"mp4")

                with patch(
                    "app.services.job_manager.ThumbnailExtractor.extract",
                    new_callable=AsyncMock,
                    side_effect=RuntimeError("extract failed"),
                ):
                    job_id, _, _ = await manager.create_job(config)
                    entry = manager._jobs[job_id]
                    await entry.task

    job = manager.get_job(job_id)
    assert job is not None
    assert job.status == JobStatus.COMPLETED
    assert job.thumbnail_path is None


@pytest.mark.asyncio
async def test_failed_job_has_no_thumbnail(manager: JobManager, tmp_path: Path):
    config = RenderConfig(
        start_time="00:01:00",
        duration_seconds=5,
        resolution="640x360",
        style=RenderStyle(),
    )

    with patch("app.services.job_manager.OUTPUT_DIR", tmp_path):
        with patch(
            "app.services.job_manager.ASSGenerator.generate",
            return_value=str(tmp_path / "test.ass"),
        ):
            with patch(
                "app.services.job_manager.FFmpegRunner.run",
                new_callable=AsyncMock,
                side_effect=RuntimeError("render failed"),
            ):
                job_id, _, _ = await manager.create_job(config)
                entry = manager._jobs[job_id]
                await entry.task

    job = manager.get_job(job_id)
    assert job is not None
    assert job.status == JobStatus.FAILED
    assert job.thumbnail_path is None


def test_remove_output_deletes_mp4_and_jpg(tmp_path: Path):
    mp4 = tmp_path / "job-id.mp4"
    jpg = tmp_path / "job-id.jpg"
    mp4.write_bytes(b"video")
    jpg.write_bytes(b"image")

    JobManager._remove_output(str(mp4))

    assert not mp4.exists()
    assert not jpg.exists()
