import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from app.models.schemas import RenderConfig, RenderStyle
from app.services.font_catalog import get_font_by_id, list_fonts, normalize_render_config


@pytest.fixture
def fonts_dir(tmp_path: Path) -> Path:
    manifest = [
        {
            "id": "demo-font",
            "file": "Demo-Regular.ttf",
            "family": "Demo Font",
            "label": "Demo Font",
        }
    ]
    (tmp_path / "fonts.json").write_text(json.dumps(manifest), encoding="utf-8")
    (tmp_path / "Demo-Regular.ttf").write_bytes(b"fake-font")
    return tmp_path


def test_get_font_by_id(fonts_dir: Path):
    with patch("app.services.font_catalog.FONTS_DIR", fonts_dir):
        with patch("app.services.font_catalog.FONTS_MANIFEST_PATH", fonts_dir / "fonts.json"):
            entry = get_font_by_id("demo-font")
            assert entry is not None
            assert entry.family == "Demo Font"
            assert entry.available is True


def test_normalize_unknown_font_id_falls_back_to_arial():
    config = RenderConfig(
        start_time="00:01:00",
        duration_seconds=60,
        style=RenderStyle(font_id="missing", font_name="Missing"),
    )

    normalized, warnings = normalize_render_config(config)

    assert normalized.style.font_id is None
    assert normalized.style.font_name == "Arial"
    assert any("Unknown font_id" in warning for warning in warnings)


def test_normalize_missing_font_file_falls_back(fonts_dir: Path):
    manifest = [
        {
            "id": "ghost",
            "file": "Ghost.ttf",
            "family": "Ghost",
            "label": "Ghost",
        }
    ]
    (fonts_dir / "fonts.json").write_text(json.dumps(manifest), encoding="utf-8")

    config = RenderConfig(
        start_time="00:01:00",
        duration_seconds=60,
        style=RenderStyle(font_id="ghost", font_name="Ghost"),
    )

    with patch("app.services.font_catalog.FONTS_DIR", fonts_dir):
        with patch("app.services.font_catalog.FONTS_MANIFEST_PATH", fonts_dir / "fonts.json"):
            normalized, warnings = normalize_render_config(config)

    assert normalized.style.font_name == "Arial"
    assert any("not found" in warning for warning in warnings)


def test_normalize_uses_manifest_family(fonts_dir: Path):
    config = RenderConfig(
        start_time="00:01:00",
        duration_seconds=60,
        style=RenderStyle(font_id="demo-font", font_name="Wrong Name"),
    )

    with patch("app.services.font_catalog.FONTS_DIR", fonts_dir):
        with patch("app.services.font_catalog.FONTS_MANIFEST_PATH", fonts_dir / "fonts.json"):
            normalized, warnings = normalize_render_config(config)

    assert normalized.style.font_name == "Demo Font"
    assert normalized.style.font_id == "demo-font"
    assert any("does not match" in warning for warning in warnings)


def test_list_fonts_reports_availability(fonts_dir: Path):
    with patch("app.services.font_catalog.FONTS_DIR", fonts_dir):
        with patch("app.services.font_catalog.FONTS_MANIFEST_PATH", fonts_dir / "fonts.json"):
            fonts = list_fonts()

    assert len(fonts) == 1
    assert fonts[0]["id"] == "demo-font"
    assert fonts[0]["available"] is True
