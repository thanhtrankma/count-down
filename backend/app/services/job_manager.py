import asyncio
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from app.config import OUTPUT_DIR, TEMP_DIR
from app.exceptions import ConcurrentJobLimitError
from app.models.schemas import JobStatus, RenderConfig, RenderJob
from app.services.ass_generator import ASSGenerator
from app.services.ffmpeg_runner import FFmpegRunner
from app.services.thumbnail_extractor import ThumbnailExtractor
from app.services.tick_audio import generate_tick_audio
from app.utils.counter_label import thumbnail_seek_seconds
from app.utils.structured_log import log_event

logger = logging.getLogger(__name__)

ACTIVE_STATUSES = {JobStatus.PENDING, JobStatus.RUNNING}
TICK_AUDIO_PROGRESS_WEIGHT = 10.0


def estimate_size_mb(duration_seconds: int) -> float:
    return duration_seconds * 4 / 8 / 1024


def estimate_render_minutes(duration_seconds: int) -> float:
    return duration_seconds / 60 * 0.1


@dataclass
class JobEntry:
    job: RenderJob
    runner: FFmpegRunner = field(default_factory=FFmpegRunner)
    task: Optional[asyncio.Task] = None
    ass_path: Optional[str] = None
    tick_audio_path: Optional[str] = None


class JobManager:
    def __init__(self) -> None:
        self._jobs: dict[str, JobEntry] = {}

    def has_active_job(self) -> bool:
        return any(entry.job.status in ACTIVE_STATUSES for entry in self._jobs.values())

    def get_active_job_id(self) -> Optional[str]:
        for job_id, entry in self._jobs.items():
            if entry.job.status in ACTIVE_STATUSES:
                return job_id
        return None

    def list_active_jobs(self) -> list[RenderJob]:
        return [
            entry.job
            for entry in self._jobs.values()
            if entry.job.status in ACTIVE_STATUSES
        ]

    async def create_job(self, config: RenderConfig) -> tuple[str, float, float]:
        if self.has_active_job():
            active_id = self.get_active_job_id()
            log_event(
                logger,
                logging.WARNING,
                "render.rejected.concurrent_limit",
                active_job_id=active_id,
                duration_seconds=config.duration_seconds,
            )
            raise ConcurrentJobLimitError(
                f"Only one render job can run at a time (active: {active_id})"
            )

        job = RenderJob(config=config)
        entry = JobEntry(job=job)
        self._jobs[job.id] = entry

        log_event(
            logger,
            logging.INFO,
            "render.job.created",
            job_id=job.id,
            duration_seconds=config.duration_seconds,
            resolution=config.resolution,
            audio_tick=config.audio_tick,
        )

        entry.task = asyncio.create_task(self._run_job(job.id))
        return (
            job.id,
            estimate_size_mb(config.duration_seconds),
            estimate_render_minutes(config.duration_seconds),
        )

    def get_job(self, job_id: str) -> Optional[RenderJob]:
        entry = self._jobs.get(job_id)
        return entry.job if entry else None

    async def cancel_job(self, job_id: str) -> bool:
        entry = self._jobs.get(job_id)
        if entry is None:
            return False

        job = entry.job
        if job.status in (JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED):
            return False

        log_event(logger, logging.INFO, "render.job.cancelling", job_id=job_id)

        job.status = JobStatus.CANCELLED
        await entry.runner.cancel()
        if entry.task and not entry.task.done():
            entry.task.cancel()
        self._cleanup_temp_files(entry)
        return True

    async def _run_job(self, job_id: str) -> None:
        entry = self._jobs.get(job_id)
        if entry is None:
            return

        job = entry.job
        config = job.config
        output_path = str(OUTPUT_DIR / f"{job_id}.mp4")
        thumb_path = str(OUTPUT_DIR / f"{job_id}.jpg")
        job.output_path = output_path

        try:
            job.status = JobStatus.RUNNING
            log_event(
                logger,
                logging.INFO,
                "render.job.started",
                job_id=job_id,
                duration_seconds=config.duration_seconds,
            )

            ass_path = ASSGenerator().generate(config)
            entry.ass_path = ass_path

            tick_audio_path: Optional[str] = None
            if config.audio_tick:

                async def on_tick_progress(progress: float) -> None:
                    if job.status == JobStatus.CANCELLED:
                        return
                    job.progress = progress * TICK_AUDIO_PROGRESS_WEIGHT / 100.0
                    await asyncio.sleep(0)

                tick_audio_path = await generate_tick_audio(
                    config.duration_seconds,
                    on_progress=on_tick_progress,
                )
                entry.tick_audio_path = tick_audio_path
                log_event(
                    logger,
                    logging.INFO,
                    "render.tick_audio.generated",
                    job_id=job_id,
                    tick_audio_path=tick_audio_path,
                )

            encode_base = TICK_AUDIO_PROGRESS_WEIGHT if config.audio_tick else 0.0
            encode_scale = 100.0 - encode_base

            async def on_progress(progress: float) -> None:
                if job.status == JobStatus.CANCELLED:
                    return
                job.progress = encode_base + progress * encode_scale / 100.0
                await asyncio.sleep(0)

            await entry.runner.run(
                ass_path,
                config,
                output_path,
                tick_audio_path=tick_audio_path,
                on_progress=on_progress,
            )

            if job.status == JobStatus.CANCELLED:
                self._remove_output(output_path)
                log_event(logger, logging.INFO, "render.job.cancelled", job_id=job_id)
                return

            try:
                thumbnail_path = await ThumbnailExtractor().extract(
                    output_path,
                    thumb_path,
                    seek_seconds=thumbnail_seek_seconds(
                        config.counter_mode.value, config.duration_seconds
                    ),
                )
                job.thumbnail_path = thumbnail_path
                log_event(
                    logger,
                    logging.INFO,
                    "render.thumbnail.generated",
                    job_id=job_id,
                    thumbnail_path=thumbnail_path,
                )
            except Exception as exc:
                log_event(
                    logger,
                    logging.WARNING,
                    "render.thumbnail.failed",
                    job_id=job_id,
                    error=str(exc),
                )
                job.thumbnail_path = None
                thumb_file = Path(thumb_path)
                if thumb_file.exists():
                    thumb_file.unlink()

            job.progress = 100.0
            job.status = JobStatus.COMPLETED
            log_event(
                logger,
                logging.INFO,
                "render.job.completed",
                job_id=job_id,
                output_path=output_path,
                thumbnail_path=job.thumbnail_path,
            )
        except asyncio.CancelledError:
            job.status = JobStatus.CANCELLED
            self._remove_output(output_path)
            log_event(logger, logging.INFO, "render.job.cancelled", job_id=job_id)
        except Exception as exc:
            log_event(
                logger,
                logging.ERROR,
                "render.job.failed",
                job_id=job_id,
                error=str(exc),
                exc_info=True,
            )
            if job.status != JobStatus.CANCELLED:
                job.status = JobStatus.FAILED
                job.error = str(exc)
            self._remove_output(output_path)
        finally:
            self._cleanup_temp_files(entry)

    @staticmethod
    def _cleanup_temp_files(entry: JobEntry) -> None:
        if entry.ass_path:
            ass_file = Path(entry.ass_path)
            if ass_file.exists():
                ass_file.unlink()
            entry.ass_path = None

        if entry.tick_audio_path:
            tick_file = Path(entry.tick_audio_path)
            if tick_file.exists():
                tick_file.unlink()
            entry.tick_audio_path = None

    @staticmethod
    def _remove_output(output_path: str) -> None:
        output_file = Path(output_path)
        if output_file.exists():
            output_file.unlink()
        thumb_file = output_file.with_suffix(".jpg")
        if thumb_file.exists():
            thumb_file.unlink()


job_manager = JobManager()
