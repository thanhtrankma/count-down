import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = BASE_DIR.parent

OUTPUT_DIR = BASE_DIR / "output"
TEMP_DIR = BASE_DIR / "temp"
MAX_DURATION_SECONDS = 28800  # 8 hours

_default_fonts_dir = REPO_ROOT / "frontend" / "font"
FONTS_DIR = Path(os.environ.get("FONTS_DIR", str(_default_fonts_dir))).resolve()
FONTS_MANIFEST_PATH = FONTS_DIR / "fonts.json"

FFMPEG_CANDIDATE_PATHS = [
    os.environ.get("FFMPEG_PATH", ""),
    "/opt/homebrew/opt/ffmpeg-full/bin/ffmpeg",
    "/usr/local/opt/ffmpeg-full/bin/ffmpeg",
]
