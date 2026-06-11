import asyncio
from pathlib import Path

from app.services.ffmpeg_runner import FFmpegRunner


class ThumbnailExtractor:
    async def extract(
        self,
        video_path: str,
        output_path: str,
        *,
        seek_seconds: float = 0,
    ) -> str:
        command = [
            FFmpegRunner._ffmpeg_path(),
            "-y",
            "-i",
            video_path,
            "-ss",
            str(seek_seconds),
            "-frames:v",
            "1",
            "-q:v",
            "2",
            output_path,
        ]
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await process.communicate()

        if process.returncode != 0:
            tail = stderr.decode("utf-8", errors="replace")[-500:].strip()
            raise RuntimeError(
                f"ffmpeg thumbnail extract exited with code {process.returncode}"
                + (f"\n{tail}" if tail else "")
            )

        output_file = Path(output_path)
        if not output_file.is_file() or output_file.stat().st_size == 0:
            raise RuntimeError("thumbnail file was not created")

        return output_path
