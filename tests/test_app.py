"""UI tests: run app.py headlessly with AppTest; the share preview reads a fake project (never the real API)."""
import os
import time

import pytest
import streamlit as st
from streamlit.testing.v1 import AppTest

from src import jobs, perso_api
from conftest import PROJECT_ROOT
from fake_perso import SHARE_URL, SHARED_PROJECT
from sample_results import make_results

APP = os.path.join(PROJECT_ROOT, "app.py")


@pytest.fixture(autouse=True)
def shared(monkeypatch, isolated_output):
    """The share preview reads a fake project instead of calling Perso; records the tokens it was asked for."""
    calls = []

    def fake_get(token, **kw):
        calls.append(token)
        return dict(SHARED_PROJECT)
    monkeypatch.setattr(perso_api, "get_shared_project", fake_get)
    st.cache_data.clear()
    return calls


def app(**state):
    """Runs the Streamlit app headlessly with the given session state and returns the AppTest handle."""
    at = AppTest.from_file(APP, default_timeout=120)
    for k, v in state.items():
        at.session_state[k] = v
    return at.run()


def all_text(at) -> str:
    """All visible text on the page (markdown, captions and alerts) joined into one string."""
    parts = [e.value for e in at.markdown] + [e.value for e in at.caption] + [e.value for e in at.info] + \
            [e.value for e in at.success] + [e.value for e in at.warning] + [e.value for e in at.error]
    return "\n".join(str(p) for p in parts)


def test_setup_asks_for_a_share_link_and_start_is_disabled(shared):
    at = app()
    assert not at.exception
    assert at.title[0].value == "Check the quality of a dubbed video"
    assert "① Paste a Perso share link" in [s.value for s in at.subheader]
    assert at.button(key="start").disabled and "Paste a Perso share link first" in all_text(at)
    assert not at.text_area                      # no script box: scripts are a CLI option (--script)
    assert shared == []


def test_share_link_shows_project_preview_and_enables_start(shared):
    at = app()
    at.text_input(key="share_url").set_value(SHARE_URL).run()
    assert not at.exception
    text = all_text(at)
    assert "QA sample.mp4 → ko" in text and "**Languages:** English (US) → Korean" in text
    assert "**Length:** 28.7 s" in text and "**Lip-sync:** Yes" in text and "**Perso project:** #420891" in text
    assert "**Videos in the link:** original, dubbed, lip-synced" in text
    for removed in ("spends no Perso credits", "Lip movement is measured automatically", "checked automatically with"):
        assert removed not in text
    assert not at.toggle                         # lip movement and translation check are automatic
    assert "No API key found for the translation check" in text
    assert not at.button(key="start").disabled


def test_preview_hides_key_warning_when_a_key_is_set(shared, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    at = app()
    at.text_input(key="share_url").set_value(SHARE_URL).run()
    assert "No API key found" not in all_text(at)


def test_bad_share_link_explains_the_problem(shared):
    at = app()
    at.text_input(key="share_url").set_value("https://youtube.com/watch?v=1").run()
    assert "doesn't look like a Perso share link" in all_text(at)
    assert at.button(key="start").disabled and shared == []


@pytest.mark.parametrize("lang, title", [("ko", "더빙 영상 품질 확인"), ("pt", "Verifique a qualidade de um vídeo dublado"),
                                         ("es", "Revisa la calidad de un video doblado")])
def test_interface_language_can_be_switched(lang, title):
    at = app()
    at.selectbox(key="ui_lang").set_value(lang).run()
    assert not at.exception and at.title[0].value == title


def test_progress_view_shows_stage_checklist_and_reattaches():
    """A running job renders the checklist, reattaches after a reload (?job=<id>), and shows failures."""
    import threading
    from src.jobs import Progress, start_job
    release = threading.Event()

    def runner(report, cancel):
        """Fake pipeline that stops while measuring until the test releases it."""
        report(Progress("fetch", "Reading the shared Perso project...", 1.0))
        report(Progress("download", "Downloading the dubbed video...", 1.0))
        report(Progress("evaluate", "Transcribing the dubbed speech...", 0.4))
        release.wait(10)
        raise RuntimeError("stopped by test")

    job = start_job(runner, {"share_url": SHARE_URL, "title": "QA sample.mp4 → ko"}, ["fetch", "download", "evaluate"])
    time.sleep(0.2)
    at = AppTest.from_file(APP, default_timeout=60)
    at.query_params["job"] = job.id           # same as reloading the page with ?job=<id>
    at.run()
    try:
        assert at.title[0].value == "Evaluating the dub"
        text = all_text(at)
        assert ":material/check_circle:] Read the share link" in text and ":material/check_circle:] Download both videos" in text
        assert ":material/progress_activity:] **Measure quality**" in text and "Transcribing the dubbed speech" in text
        assert any(b.label == "Stop" or "Stop" in b.label for b in at.button)
    finally:
        release.set()
    while job.status == "running":
        time.sleep(0.05)
    at.run()
    assert at.title[0].value == "Something went wrong" and "stopped by test" in all_text(at)


def test_results_page_shows_verdict_report_and_seekable_things_to_check():
    at = app(view="results", results=make_results())
    assert not at.exception
    text = all_text(at)
    assert "### :green[:material/verified:] Good" in text and "The dub passed every automatic check." in text
    assert "**3. Timing alignment**" in text and "81% lined up" in text
    seek = next(b for b in at.button if b.key == "seek_0")
    assert seek.label == "00:19.4"
    seek.click().run()
    assert at.session_state["seek"] == 19


def test_results_page_in_korean_translates_labels():
    at = app(ui_lang="ko", view="results", results=make_results())
    text = all_text(at)
    assert "좋음" in text and "**3. 발화 타이밍**" in text and "**길이 일치**" in text


@pytest.mark.slow
def test_share_run_end_to_end_in_the_app(monkeypatch, isolated_output):
    """Start from the UI with a fake share link serving the sample video; the report appears when done."""
    from conftest import SAMPLE_VIDEO
    from fake_perso import CopyingFakePerso
    from src import pipeline
    english = {**SHARED_PROJECT, "targetLanguage": {"code": "en", "name": "English (US)", "languageTag": "default"}}
    fake = CopyingFakePerso(SAMPLE_VIDEO, shared_project=english)
    real = pipeline.run_share_evaluation      # app.py re-imports it from src.pipeline on every script run
    monkeypatch.setattr(pipeline, "run_share_evaluation",
                        lambda **kw: real(**{**kw, "session": fake, "sleep": lambda s: None}))
    at = app()
    at.text_input(key="share_url").set_value(SHARE_URL).run()
    at.button(key="start").click().run()
    job_id = at.query_params["job"]
    job = jobs.get_job(job_id[0] if isinstance(job_id, list) else job_id)
    end = time.time() + 240
    while job.status == "running" and time.time() < end:
        time.sleep(0.5)
    assert job.status == "done", job.error
    at.run()
    at.run()
    assert not at.exception and at.title[0].value == "Results"
    assert "Length match" in all_text(at) and "Detailed measurements" in [s.value for s in at.subheader]
