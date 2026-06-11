import asyncio
import shutil
import uuid
from pathlib import Path
from typing import Awaitable, Callable, Optional

from app.config import FFMPEG_CANDIDATE_PATHS, TEMP_DIR
from app.models.schemas import RenderConfig
from app.services.ffmpeg_progress import parse_progress_file
from app.services.font_catalog import fonts_dir_for_render


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
        progress_path: Optional[str] = None,
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

        if progress_path:
            command.extend(["-progress", progress_path])

        command.append(output_path)
        return command

    @staticmethod
    def _consume_stderr_chunk(
        chunk: str,
        carry: str,
        stderr_lines: list[str],
    ) -> str:
        """Append a stderr chunk, splitting on newlines and collapsing \\r progress."""
        text = carry + chunk

        while "\n" in text:
            line, text = text.split("\n", 1)
            line = line.split("\r")[-1]
            if line.strip():
                stderr_lines.append(line)
                if len(stderr_lines) > 50:
                    del stderr_lines[:-20]

        if "\r" in text:
            text = text.split("\r")[-1]

        return text

    async def _drain_stderr(self, stderr: asyncio.StreamReader) -> list[str]:
        stderr_lines: list[str] = []
        carry = ""

        while True:
            chunk_bytes = await stderr.read(8192)
            if not chunk_bytes:
                if carry.strip():
                    stderr_lines.append(carry)
                break

            carry = self._consume_stderr_chunk(
                chunk_bytes.decode("utf-8", errors="replace"),
                carry,
                stderr_lines,
            )

        return stderr_lines

    async def _poll_progress_file(
        self,
        progress_path: Path,
        total_seconds: float,
        stop_event: asyncio.Event,
        on_progress: Optional[Callable[[float], Awaitable[None] | None]] = None,
    ) -> None:
        while not stop_event.is_set():
            try:
                if progress_path.is_file():
                    content = progress_path.read_text(encoding="utf-8", errors="replace")
                    progress = parse_progress_file(content, total_seconds)
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

    async def run(
        self,
        ass_path: str,
        config: RenderConfig,
        output_path: str,
        tick_audio_path: Optional[str] = None,
        on_progress: Optional[Callable[[float], Awaitable[None] | None]] = None,
    ) -> str:
        progress_path = TEMP_DIR / f"progress_{uuid.uuid4().hex}.txt"
        command = self.build_command(
            ass_path,
            config,
            output_path,
            tick_audio_path,
            progress_path=str(progress_path),
        )
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        TEMP_DIR.mkdir(parents=True, exist_ok=True)

        self._process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        assert self._process.stderr is not None
        total_seconds = float(config.duration_seconds)
        stop_event = asyncio.Event()
        progress_task = asyncio.create_task(
            self._poll_progress_file(
                progress_path,
                total_seconds,
                stop_event,
                on_progress,
            )
        )
        stderr_task = asyncio.create_task(self._drain_stderr(self._process.stderr))

        try:
            return_code = await self._process.wait()
            stderr_lines = await stderr_task
        finally:
            stop_event.set()
            await progress_task
            progress_path.unlink(missing_ok=True)
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
