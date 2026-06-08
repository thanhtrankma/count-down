import logging
import shutil
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, ConfigDict, Field

from app.exceptions import ConcurrentJobLimitError
from app.models.schemas import JobStatus, RenderConfig, RenderJob
from app.services.font_catalog import list_fonts, normalize_render_config
from app.services.job_manager import job_manager
from app.utils.structured_log import log_event

logger = logging.getLogger(__name__)

router = APIRouter()


class CreateJobResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    job_id: str = Field(alias="jobId")
    estimated_size_mb: float = Field(alias="estimatedSizeMb")
    estimated_render_minutes: float = Field(alias="estimatedRenderMinutes")
    warnings: list[str] = Field(default_factory=list)


@router.get("/api/fonts")
def get_fonts() -> dict:
    return {"fonts": list_fonts()}


@router.post("/api/render", response_model=CreateJobResponse)
async def create_render_job(config: RenderConfig) -> CreateJobResponse:
    config, warnings = normalize_render_config(config)
    for warning in warnings:
        log_event(logger, logging.WARNING, "render.font.fallback", message=warning)

    try:
        job_id, size_mb, render_minutes = await job_manager.create_job(config)
    except ConcurrentJobLimitError as exc:
        raise HTTPException(status_code=429, detail=str(exc)) from exc

    return CreateJobResponse(
        jobId=job_id,
        estimatedSizeMb=size_mb,
        estimatedRenderMinutes=render_minutes,
        warnings=warnings,
    )


@router.get("/api/jobs/{job_id}", response_model=RenderJob)
def get_job(job_id: str) -> RenderJob:
    job = job_manager.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.get("/api/jobs/{job_id}/download")
def download_job(job_id: str) -> FileResponse:
    job = job_manager.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status != JobStatus.COMPLETED:
        raise HTTPException(
            status_code=409,
            detail=f"Job is not completed (status: {job.status.value})",
        )
    if not job.output_path or not Path(job.output_path).is_file():
        raise HTTPException(status_code=404, detail="Output file not found")

    return FileResponse(
        job.output_path,
        media_type="video/mp4",
        filename=f"countdown_{job_id}.mp4",
    )


@router.delete("/api/jobs/{job_id}")
async def cancel_job(job_id: str) -> dict:
    job = job_manager.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    cancelled = await job_manager.cancel_job(job_id)
    if not cancelled:
        raise HTTPException(
            status_code=409,
            detail=f"Job cannot be cancelled (status: {job.status.value})",
        )
    return {"status": "cancelled", "job_id": job_id}


@router.get("/api/health")
def health_check() -> dict:
    ffmpeg_path = shutil.which("ffmpeg")
    return {
        "status": "ok" if ffmpeg_path else "error",
        "ffmpeg": ffmpeg_path is not None,
        "ffmpeg_path": ffmpeg_path,
    }
