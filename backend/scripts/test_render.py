#!/usr/bin/env python3
import asyncio
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from app.config import TEMP_DIR
from app.models.schemas import RenderConfig, RenderStyle
from app.services.ass_generator import ASSGenerator
from app.services.ffmpeg_runner import FFmpegRunner


async def main() -> None:
    config = RenderConfig(
        start_time="00:01:00",
        duration_seconds=60,
        resolution="1920x1080",
        background_color="#000000",
        style=RenderStyle(
            font_name="Arial",
            font_size=120,
            color="#FFFFFF",
        ),
        title="Countdown Test",
    )

    ass_path = ASSGenerator().generate(config)
    output_path = str(TEMP_DIR / "test_60s.mp4")

    runner = FFmpegRunner()

    def on_progress(progress: float) -> None:
        print(f"\rProgress: {progress:5.1f}%", end="", flush=True)

    print(f"ASS file: {ass_path}")
    print(f"Rendering to: {output_path}")

    result = await runner.run(ass_path, config, output_path, on_progress=on_progress)
    print(f"\nDone: {result}")


if __name__ == "__main__":
    asyncio.run(main())
