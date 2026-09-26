"""Shared pytest setup: puts the project on the import path and provides the isolated_output fixture."""
import os
import sys

import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

SAMPLE_ORIGINAL = os.path.join(PROJECT_ROOT, "data", "input", "sample_original.mp4")


def pytest_configure(config):
    """Registers the `slow` marker so `pytest -m "not slow"` can skip the heavy tests."""
    config.addinivalue_line("markers", "slow: runs Whisper/MediaPipe on the bundled sample video")


@pytest.fixture
def isolated_output(tmp_path, monkeypatch):
    """Redirects pipeline output (results.json, runs/) into a temp dir."""
    from src import pipeline
    monkeypatch.setattr(pipeline, "OUTPUT_DIR", str(tmp_path))
    monkeypatch.setattr(pipeline, "RUNS_DIR", str(tmp_path / "runs"))
    monkeypatch.setattr(pipeline, "RESULTS_FILE", str(tmp_path / "results.json"))
    return tmp_path
