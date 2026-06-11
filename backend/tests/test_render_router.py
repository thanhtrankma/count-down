import sys
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi import HTTPException
from fastapi.responses import FileResponse

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from app.models.schemas import JobStatus, RenderConfig, RenderJob, RenderStyle
from app.routers.render import download_thumbnail, list_active_jobs


def _completed_job(job_id: str, thumbnail_path: str | None = None) -> RenderJob:
    return RenderJob(
        id=job_id,
        status=JobStatus.COMPLETED,
        progress=100.0,
        config=RenderConfig(
            start_time="00:01:00",
            duration_seconds=60,
            style=RenderStyle(),
        ),
        output_path=f"/tmp/{job_id}.mp4",
        thumbnail_path=thumbnail_path,
    )


def test_list_active_jobs_empty():
    with patch("app.routers.render.job_manager.list_active_jobs", return_value=[]):
        response = list_active_jobs()

    assert response.jobs == []


def test_list_active_jobs_returns_running_jobs():
    job_id = "active-job-1"
    running_job = RenderJob(
        id=job_id,
        status=JobStatus.RUNNING,
        progress=55.0,
        config=RenderConfig(
            start_time="00:01:00",
            duration_seconds=60,
            style=RenderStyle(),
        ),
    )

    with patch(
        "app.routers.render.job_manager.list_active_jobs",
        return_value=[running_job],
    ):
        response = list_active_jobs()

    assert len(response.jobs) == 1
    assert response.jobs[0].id == job_id
    assert response.jobs[0].status == JobStatus.RUNNING


def test_get_thumbnail_completed_job_returns_jpeg(tmp_path: Path):
    job_id = "test-job-thumb"
    thumb_file = tmp_path / f"{job_id}.jpg"
    thumb_file.write_bytes(b"\xff\xd8\xff\xd9")

    job = _completed_job(job_id, thumbnail_path=str(thumb_file))

    with patch("app.routers.render.job_manager.get_job", return_value=job):
        response = download_thumbnail(job_id)

    assert isinstance(response, FileResponse)
    assert response.media_type == "image/jpeg"
    assert response.path == str(thumb_file)


def test_get_thumbnail_running_job_returns_409():
    job_id = "running-job"
    job = RenderJob(
        id=job_id,
        status=JobStatus.RUNNING,
        progress=42.0,
        config=RenderConfig(
            start_time="00:01:00",
            duration_seconds=60,
            style=RenderStyle(),
        ),
    )

    with patch("app.routers.render.job_manager.get_job", return_value=job):
        with pytest.raises(HTTPException) as exc_info:
            download_thumbnail(job_id)

    assert exc_info.value.status_code == 409


def test_get_thumbnail_missing_file_returns_404():
    job_id = "missing-thumb"
    job = _completed_job(job_id, thumbnail_path="/tmp/does-not-exist.jpg")

    with patch("app.routers.render.job_manager.get_job", return_value=job):
        with pytest.raises(HTTPException) as exc_info:
            download_thumbnail(job_id)

    assert exc_info.value.status_code == 404


def test_get_thumbnail_job_not_found_returns_404():
    with patch("app.routers.render.job_manager.get_job", return_value=None):
        with pytest.raises(HTTPException) as exc_info:
            download_thumbnail("unknown")

    assert exc_info.value.status_code == 404
