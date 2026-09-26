"""UI tests: run app.py headlessly with AppTest against the fake Perso account (never the real API)."""
import os
import time

import pytest
import streamlit as st
from streamlit.testing.v1 import AppTest

from src import jobs, perso_api
from conftest import PROJECT_ROOT
from fake_perso import FakePerso

APP = os.path.join(PROJECT_ROOT, "app.py")


@pytest.fixture(autouse=True)
def fake_account(monkeypatch, isolated_output):
    """The UI talks to a fake Perso account, never the real API."""
    fake = FakePerso(credits=300)
    monkeypatch.setattr(perso_api, "PersoClient", lambda *a, **k: fake.client())
    st.cache_data.clear()
    return fake


def app():
    """Runs the Streamlit app headlessly and returns the AppTest handle."""
    return AppTest.from_file(APP, default_timeout=120).run()


def all_text(at) -> str:
    """All visible text on the page (markdown, captions and alerts) joined into one string."""
    parts = [e.value for e in at.markdown] + [e.value for e in at.caption] + [e.value for e in at.info] + \
            [e.value for e in at.success] + [e.value for e in at.warning] + [e.value for e in at.error]
    return "\n".join(str(p) for p in parts)


def test_setup_page_guides_the_user_and_script_is_empty():
    at = app()
    assert not at.exception
    text = all_text(at)
    subheaders = [s.value for s in at.subheader]
    for step in ("① Choose a video", "② Choose the dubbing options", "③ Paste the target script"):
        assert step in subheaders
    assert at.text_area(key="target_script").value == ""
    assert "Connected" in text and "QA" in text
    assert "Estimated cost: **56 credits**" in text           # 28 s sample, lip-sync on
    assert at.button(key="start").label.startswith("Start dubbing (56 credits)")


def test_cost_updates_when_lipsync_is_turned_off():
    at = app()
    at.toggle(key="lip_dubbing").set_value(False).run()
    assert "Estimated cost: **28 credits**" in all_text(at)


def test_not_enough_credits_blocks_start(fake_account):
    fake_account.credits = 10
    at = app()
    assert "Not enough credits" in all_text(at)
    assert at.button(key="start").disabled


def test_demo_only_offered_for_korean():
    at = app()
    assert any(t.key == "use_demo" for t in at.toggle)
    at.selectbox(key="target_language").set_value("ja").run()
    assert not any(t.key == "use_demo" for t in at.toggle)
    assert "in Japanese" in all_text(at)


def test_language_list_comes_from_perso():
    at = app()
    box = at.selectbox(key="target_language")
    assert box.value == "ko" and "English (UK)" in box.options and "Cebuano" in box.options
    at.selectbox(key="target_language").set_value("ceb").run()
    assert "Speech recognition doesn't support Cebuano" in all_text(at)


@pytest.mark.parametrize("lang, title, cost", [
    ("ko", "더빙 영상 품질 확인", "예상 비용: **56 크레딧**"),
    ("pt", "Verifique a qualidade de um vídeo dublado", "Custo estimado: **56 créditos**"),
    ("es", "Revisa la calidad de un video doblado", "Costo estimado: **56 créditos**"),
])
def test_interface_language_can_be_switched(lang, title, cost):
    at = app()
    at.selectbox(key="ui_lang").set_value(lang).run()
    assert not at.exception
    assert at.title[0].value == title
    assert cost in all_text(at)
    assert at.selectbox(key="target_language").value == "ko"      # the dub language is unaffected


def test_sample_script_button_fills_script():
    at = app()
    at.toggle(key="use_demo").set_value(True).run()
    next(b for b in at.button if "sample's Korean script" in b.label).click().run()
    assert "우즈베키스탄" in at.text_area(key="target_script").value
    assert at.button(key="start").label == "Start demo evaluation"


@pytest.mark.slow
def test_demo_run_shows_progress_then_results():
    at = app()
    at.toggle(key="use_demo").set_value(True).run()
    at.text_area(key="target_script").set_value("안녕하세요 저는 우즈베키스탄에서 온 존입니다").run()
    at.button(key="start").click().run()
    job = jobs.get_job(at.query_params["job"][0] if isinstance(at.query_params["job"], list) else at.query_params["job"])
    assert job is not None
    assert "Dubbing in progress" in [t.value for t in at.title][0] or job.status != "running"
    end = time.time() + 240
    while job.status == "running" and time.time() < end:
        time.sleep(0.5)
    assert job.status == "done", job.error
    at.run()
    at.run()
    assert not at.exception
    assert at.title[0].value == "Results"
    text = all_text(at)
    assert "Timing match" in text and "Matches your script" in text and "Original vs dubbed" in [s.value for s in at.subheader]
    assert len(at.dataframe) == 1 and list(at.dataframe[0].value["Measure"])[0] == "Duration"


def test_progress_view_shows_stage_checklist_and_eta():
    """A live job paused in the lip-sync stage renders the waiting screen, and reattaches after a reload."""
    import threading
    from src.jobs import Progress, start_job
    release = threading.Event()

    def runner(report, cancel):
        """Fake pipeline that stops in the lip-sync stage until the test releases it."""
        report(Progress("upload", "Uploading", 1.0))
        report(Progress("dubbing", "Generating the dubbed voice", 1.0))
        report(Progress("lipsync", "Re-rendering lips to match the new audio", 0.4, eta_minutes=12))
        release.wait(10)
        raise RuntimeError("stopped by test")

    params = {"input_video_path": "x/sample.mp4", "target_language": "Korean", "lip_dubbing": True, "use_demo_mode": False}
    job = start_job(runner, params, ["upload", "dubbing", "lipsync", "download", "evaluate"])
    time.sleep(0.2)
    at = AppTest.from_file(APP, default_timeout=60)
    at.query_params["job"] = job.id           # same as reloading the page with ?job=<id>
    at.run()
    try:
        assert at.title[0].value == "Dubbing in progress"
        text = all_text(at)
        assert ":material/check_circle:] Upload video to Perso" in text and ":material/check_circle:] Dub the voice" in text
        assert ":material/progress_activity:] **Lip-sync the video**" in text and "40%" in text and "about 12 min left" in text
        assert ":material/radio_button_unchecked:] :gray[Measure quality]" in text
        assert "slowest step" in text
        assert any(b.label == "Stop waiting" for b in at.button)
    finally:
        release.set()
    while job.status == "running":
        time.sleep(0.05)
    at.run()
    assert at.title[0].value == "Something went wrong" and "stopped by test" in all_text(at)
