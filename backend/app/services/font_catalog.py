import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from app.config import FONTS_DIR, FONTS_MANIFEST_PATH
from app.models.schemas import RenderConfig, RenderStyle

logger = logging.getLogger(__name__)

FONT_EXTENSIONS = {".ttf", ".otf", ".woff2"}


@dataclass(frozen=True)
class FontEntry:
    id: str
    file: str
    family: str
    label: str

    @property
    def path(self) -> Path:
        return FONTS_DIR / self.file

    @property
    def available(self) -> bool:
        return self.path.is_file()


def load_manifest() -> list[FontEntry]:
    if not FONTS_MANIFEST_PATH.is_file():
        return []

    try:
        raw = json.loads(FONTS_MANIFEST_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("Failed to read fonts manifest: %s", exc)
        return []

    if not isinstance(raw, list):
        return []

    entries: list[FontEntry] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        try:
            entries.append(
                FontEntry(
                    id=str(item["id"]),
                    file=str(item["file"]),
                    family=str(item["family"]),
                    label=str(item.get("label", item["family"])),
                )
            )
        except KeyError:
            continue
    return entries


def get_font_by_id(font_id: str) -> Optional[FontEntry]:
    return next((entry for entry in load_manifest() if entry.id == font_id), None)


def list_fonts() -> list[dict]:
    return [
        {
            "id": entry.id,
            "file": entry.file,
            "family": entry.family,
            "label": entry.label,
            "available": entry.available,
        }
        for entry in load_manifest()
    ]


def normalize_render_config(config: RenderConfig) -> tuple[RenderConfig, list[str]]:
    """Resolve custom font; fall back to Arial when missing."""
    warnings: list[str] = []
    style = config.style
    font_id = style.font_id

    if not font_id:
        return config, warnings

    entry = get_font_by_id(font_id)
    if entry is None:
        warnings.append(f"Unknown font_id '{font_id}'; falling back to Arial")
        return config.model_copy(
            update={
                "style": style.model_copy(update={"font_id": None, "font_name": "Arial"}),
            }
        ), warnings

    if not entry.available:
        warnings.append(
            f"Font file '{entry.file}' for '{font_id}' not found; falling back to Arial"
        )
        return config.model_copy(
            update={
                "style": style.model_copy(update={"font_id": None, "font_name": "Arial"}),
            }
        ), warnings

    if style.font_name != entry.family:
        warnings.append(
            f"font_name '{style.font_name}' does not match manifest family "
            f"'{entry.family}'; using manifest family for render"
        )

    return config.model_copy(
        update={
            "style": style.model_copy(
                update={"font_id": entry.id, "font_name": entry.family},
            ),
        }
    ), warnings


def fonts_dir_for_render() -> Optional[Path]:
    if not FONTS_DIR.is_dir():
        return None
    if any(path.suffix.lower() in FONT_EXTENSIONS for path in FONTS_DIR.iterdir()):
        return FONTS_DIR
    return None
