import asyncio
import re
import shutil
from pathlib import Path
from typing import Awaitable, Callable, Optional

from app.config import FFMPEG_CANDIDATE_PATHS
from app.models.schemas import RenderConfig
from app.services.font_catalog import fonts_dir_for_render

TIME_PROGRESS_PATTERN = re.compile(r"time=(\d{2}):(\d{2}):(\d{2}\.\d{2})")


class FFmpegRunner:
    def __init__(self) -> None:
        self._process: Optional[asyncio.subprocess.Process] = None

    @staticmethod
    def _ffmpeg_path() -> str:
        for candidate in FFMPEG_CANDIDATE_PATHS:
            if candidate and Path(candidate).is_file():
                return candidate

        ffmpeg = shutil.which("ffmpeg")
        if ffmpeg:
            return ffmpeg

        raise RuntimeError(
            "ffmpeg not found. Install ffmpeg with libass support, e.g. "
            "'brew install ffmpeg-full' then add "
            "'export PATH=\"/opt/homebrew/opt/ffmpeg-full/bin:$PATH\"' to ~/.zshrc"
        )

    @staticmethod
    def _escape_filter_path(path: str) -> str:
        return path.replace("\\", "/").replace(":", "\\:")

    @staticmethod
    def build_ass_filter(ass_path: str, fonts_dir: Optional[str] = None) -> str:
        escaped_ass = FFmpegRunner._escape_filter_path(ass_path)
        if fonts_dir:
            escaped_fonts = FFmpegRunner._escape_filter_path(fonts_dir)
            return f"ass={escaped_ass}:fontsdir={escaped_fonts}"
        return f"ass={escaped_ass}"

    def build_command(
        self,
        ass_path: str,
        config: RenderConfig,
        output_path: str,
        tick_audio_path: Optional[str] = None,
    ) -> list[str]:
        width = config.width
        height = config.height
        duration = config.duration_seconds
        bg = config.background_color.lstrip("#")
        fonts_dir = fonts_dir_for_render()
        filter_graph = self.build_ass_filter(
            ass_path,
            str(fonts_dir) if fonts_dir else None,
        )

        command = [
            self._ffmpeg_path(),
            "-y",
            "-f",
            "lavfi",
            "-i",
            f"color=c=#{bg}:s={width}x{height}:d={duration}",
        ]

        if tick_audio_path:
            command.extend(["-i", tick_audio_path])

        command.extend(
            [
                "-vf",
                filter_graph,
                "-c:v",
                "libx264",
                "-preset",
                "veryfast",
                "-crf",
                "23",
                "-pix_fmt",
                "yuv420p",
            ]
        )

        if tick_audio_path:
            command.extend(
                [
                    "-c:a",
                    "aac",
                    "-b:a",
                    "128k",
                    "-shortest",
                ]
            )

        command.append(output_path)
        return command

    @staticmethod
    def _parse_progress(stderr_line: str, total_seconds: float) -> Optional[float]:
        match = TIME_PROGRESS_PATTERN.search(stderr_line)
        if not match:
            return None
        hours, minutes, seconds = match.groups()
        elapsed = int(hours) * 3600 + int(minutes) * 60 + float(seconds)
        if total_seconds <= 0:
            return 0.0
        return min(100.0, (elapsed / total_seconds) * 100.0)

    async def run(
        self,
        ass_path: str,
        config: RenderConfig,
        output_path: str,
        tick_audio_path: Optional[str] = None,
        on_progress: Optional[Callable[[float], Awaitable[None] | None]] = None,
    ) -> str:
        command = self.build_command(ass_path, config, output_path, tick_audio_path)
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        self._process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        assert self._process.stderr is not None
        total_seconds = float(config.duration_seconds)
        stderr_lines: list[str] = []

        while True:
            line_bytes = await self._process.stderr.readline()
            if not line_bytes:
                break
            line = line_bytes.decode("utf-8", errors="replace")
            stderr_lines.append(line)
            progress = self._parse_progress(line, total_seconds)
            if progress is not None and on_progress is not None:
                result = on_progress(progress)
                if asyncio.iscoroutine(result):
                    await result

        return_code = await self._process.wait()
        self._process = None

        if return_code != 0:
            tail = "".join(stderr_lines[-20:]).strip()
            raise RuntimeError(
                f"ffmpeg exited with code {return_code}"
                + (f"\n{tail}" if tail else "")
            )

        return output_path

    async def cancel(self) -> None:
        if self._process is None or self._process.returncode is not None:
            return
        self._process.terminate()
        try:
            await asyncio.wait_for(self._process.wait(), timeout=5)
        except asyncio.TimeoutError:
            self._process.kill()
            await self._process.wait()
        self._process = None
