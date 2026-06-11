import asyncio
import shutil
import sys
from pathlib import Path
import pytest

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from app.services.thumbnail_extractor import ThumbnailExtractor


def _ffmpeg_available() -> bool:
    return shutil.which("ffmpeg") is not None


@pytest.mark.asyncio
async def test_extract_raises_when_ffmpeg_fails(tmp_path: Path):
    if not _ffmpeg_available():
        pytest.skip("FFmpeg not available")

    video_path = tmp_path / "input.mp4"
    video_path.write_bytes(b"not-a-video")
    output_path = tmp_path / "thumb.jpg"

    with pytest.raises(RuntimeError, match="ffmpeg thumbnail extract"):
        await ThumbnailExtractor().extract(str(video_path), str(output_path))

    assert not output_path.exists()


@pytest.mark.asyncio
async def test_extract_creates_jpeg_from_video(tmp_path: Path):
    if not _ffmpeg_available():
        pytest.skip("FFmpeg not available")

    from app.services.ffmpeg_runner import FFmpegRunner

    video_path = tmp_path / "sample.mp4"
    output_path = tmp_path / "thumb.jpg"
    ffmpeg = FFmpegRunner._ffmpeg_path()

    render_cmd = [
        ffmpeg,
        "-y",
        "-f",
        "lavfi",
        "-i",
        "color=c=#112233:s=640x360:d=5",
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        str(video_path),
    ]
    process = await asyncio.create_subprocess_exec(*render_cmd)
    return_code = await process.wait()
    assert return_code == 0
    assert video_path.is_file()

    result = await ThumbnailExtractor().extract(str(video_path), str(output_path))

    assert result == str(output_path)


@pytest.mark.asyncio
async def test_extract_last_frame_with_seek_seconds(tmp_path: Path):
    if not _ffmpeg_available():
        pytest.skip("FFmpeg not available")

    from app.services.ffmpeg_runner import FFmpegRunner

    video_path = tmp_path / "sample.mp4"
    first_thumb = tmp_path / "first.jpg"
    last_thumb = tmp_path / "last.jpg"
    ffmpeg = FFmpegRunner._ffmpeg_path()

    render_cmd = [
        ffmpeg,
        "-y",
        "-f",
        "lavfi",
        "-i",
        "color=c=#112233:s=640x360:d=5",
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        str(video_path),
    ]
    process = await asyncio.create_subprocess_exec(*render_cmd)
    return_code = await process.wait()
    assert return_code == 0

    await ThumbnailExtractor().extract(str(video_path), str(first_thumb), seek_seconds=0)
    await ThumbnailExtractor().extract(str(video_path), str(last_thumb), seek_seconds=4)

    assert first_thumb.is_file()
    assert last_thumb.is_file()
    assert first_thumb.stat().st_size > 0
    assert last_thumb.stat().st_size > 0
