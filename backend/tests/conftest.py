import os
import shutil

import pytest


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "integration: full render pipeline tests (require FFmpeg)",
    )
    config.addinivalue_line(
        "markers",
        "slow: long-running tests",
    )


def pytest_collection_modifyitems(config, items):
    if os.environ.get("RUN_INTEGRATION_RENDER") == "1":
        return

    skip_integration = pytest.mark.skip(
        reason="Set RUN_INTEGRATION_RENDER=1 to run integration render tests",
    )
    for item in items:
        if "integration" in item.keywords:
            item.add_marker(skip_integration)


@pytest.fixture
def ffmpeg_available() -> bool:
    return shutil.which("ffmpeg") is not None
