"""Shared pytest setup: puts the project on the import path and provides the isolated_output fixture."""
import os
import sys

import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

# A short English talking-head clip served by the fake share link in the slow tests. It isn't in git (it would
# make every clone ~30 MB bigger); put any ~30 s MP4 with clear English speech here to run those tests.
SAMPLE_VIDEO = os.path.join(PROJECT_ROOT, "tests", "data", "sample.mp4")
needs_sample_video = pytest.mark.skipif(not os.path.exists(SAMPLE_VIDEO),
                                        reason="tests/data/sample.mp4 is missing (not in git; see tests/conftest.py)")


def pytest_configure(config):
    """Registers the `slow` marker so `pytest -m "not slow"` can skip the heavy tests."""
    config.addinivalue_line("markers", "slow: runs Whisper/MediaPipe on tests/data/sample.mp4")


@pytest.fixture
def isolated_output(tmp_path, monkeypatch):
    """Redirects pipeline output (results.json, runs/) into a temp dir."""
    from src import pipeline
    monkeypatch.setattr(pipeline, "OUTPUT_DIR", str(tmp_path))
    monkeypatch.setattr(pipeline, "RUNS_DIR", str(tmp_path / "runs"))
    monkeypatch.setattr(pipeline, "RESULTS_FILE", str(tmp_path / "results.json"))
    return tmp_path


@pytest.fixture(autouse=True)
def isolated_cache(tmp_path, monkeypatch):
    """Downloads and Whisper results are cached per share link; each test gets its own empty cache."""
    from src import history, pipeline
    monkeypatch.setattr(pipeline, "CACHE_DIR", tmp_path / "cache")
    monkeypatch.setattr(history, "HISTORY_FILE", tmp_path / "history.jsonl")    # never the real history
    return tmp_path / "cache"


@pytest.fixture(autouse=True)
def no_model_downloads(monkeypatch):
    """Tests never download models: the speaker model is used only if it's already on disk."""
    from src import speaker

    def refuse(url, out):
        raise RuntimeError("tests never download models")
    monkeypatch.setattr(speaker, "_download", refuse)


@pytest.fixture(autouse=True)
def no_real_api_keys(monkeypatch):
    """Tests never see real keys (the app loads .env): every provider key is removed from the environment."""
    for var in ("GEMINI_API_KEY", "GOOGLE_API_KEY", "ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN"):
        monkeypatch.delenv(var, raising=False)


@pytest.fixture(autouse=True)
def no_real_translation_judge(monkeypatch):
    """Tests never call Gemini or Claude: the pipeline's translation check reports itself as off."""
    from src import pipeline
    from src.translation_judge import not_measured
    monkeypatch.setattr(pipeline, "judge_translation", lambda *a, **k: not_measured("r.judge.off"))
