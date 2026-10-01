"""UI tests: run app.py headlessly with AppTest; the share preview reads a fake project (never the real API)."""
import os
import time

import pytest
import streamlit as st
from streamlit.testing.v1 import AppTest

from src import jobs, perso_api
from conftest import PROJECT_ROOT, needs_sample_video
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
    assert "**Length:** 28.7 s" in text and "**Lip-sync:** Yes" in text and "**Perso project:** #100001" in text
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
@needs_sample_video
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


# ---------------- compare mode ----------------
def compare_run(a=None, b=None) -> dict:
    """What run_comparison returns, for two sample dubs (A Poor, B Good by default)."""
    from src.compare import build_comparison
    a = a or make_results(acoustic_metrics={"dubbed_duration_sec": 40.0})
    b = b or make_results()
    b["pipeline"]["share"].update(seq=100002, title="QA sample.mp4 → ko (v2)")
    return {"comparison": build_comparison(a, b, "en", run_seconds=12.0), "results": {"A": a, "B": b}, "files": {}}


def test_compare_tab_needs_two_valid_links(shared):
    from fake_perso import SHARE_URL_B
    at = app()
    assert at.tabs[1].label.endswith("Compare two dubs")
    assert at.button(key="start_compare").disabled and "Paste two valid Perso share links first." in all_text(at)
    at.text_input(key="share_url_a").set_value(SHARE_URL).run()
    assert at.button(key="start_compare").disabled
    at.text_input(key="share_url_b").set_value(SHARE_URL_B).run()
    assert not at.exception and not at.button(key="start_compare").disabled
    assert "same Perso project" in all_text(at)          # the fake answers both links with the same project


def test_compare_job_runs_and_opens_the_comparison(shared, monkeypatch):
    from fake_perso import SHARE_URL_B
    from src import pipeline
    seen = {}

    def fake_compare(url_a, url_b, out_dir, report=None, cancel_event=None, **kw):
        seen.update(url_a=url_a, url_b=url_b, out_dir=out_dir, **kw)
        return compare_run()
    monkeypatch.setattr(pipeline, "run_comparison", fake_compare)
    at = app()
    at.text_input(key="share_url_a").set_value(SHARE_URL).run()
    at.text_input(key="share_url_b").set_value(SHARE_URL_B).run()
    at.button(key="start_compare").click().run()
    job = list(jobs._jobs.values())[-1]
    while job.status == "running":
        time.sleep(0.05)
    assert job.status == "done" and job.stages == ["dub_a", "dub_b", "compare"]
    assert (seen["url_a"], seen["url_b"], seen["report_lang"]) == (SHARE_URL, SHARE_URL_B, "en")
    for _ in range(3):                        # the page follows the job: progress → done → comparison
        if at.title and at.title[0].value == "Dub comparison":
            break
        at.run()
    assert not at.exception and at.title[0].value == "Dub comparison"


def test_comparison_page_shows_recommendation_intervals_and_reasoning_in_order():
    at = app(view="compare", compare_run=compare_run())
    assert not at.exception
    text = all_text(at)
    assert "### :green[:material/verified:] Deliver Dub B." in text
    order = [text.index(x) for x in ("**1. Recommended version**", "**2. Problem intervals**", "**3. Reasoning**")]
    assert order == sorted(order)
    assert "**Deciding rule:** 1. Better overall verdict" in text and "Length match (Poor)" in text
    seek = at.button(key="seek_B_0")
    assert seek.label == "19.4s"
    seek.click().run()
    assert at.session_state["seek_B"] == 19 and at.session_state["seek_A"] == 0


def test_comparison_page_follows_the_interface_language_and_warns_when_both_are_poor():
    poor = make_results(acoustic_metrics={"dubbed_duration_sec": 40.0})
    at = app(ui_lang="ko", view="compare", compare_run=compare_run(b=poor))
    text = all_text(at)
    assert at.title[0].value == "더빙 비교" and "**1. 추천 버전**" in text
    assert "두 더빙 모두 납품할 준비가 되지 않았습니다" in text and "**먼저 고칠 것**" in text


def test_compare_tab_can_add_and_remove_dubs(shared):
    from fake_perso import SHARE_URL_B
    at = app()
    assert at.button(key="remove_dub").disabled
    at.button(key="add_dub").click().run()
    assert not at.exception and at.session_state["compare_n"] == 3
    at.text_input(key="share_url_a").set_value(SHARE_URL).run()
    at.text_input(key="share_url_b").set_value(SHARE_URL_B).run()
    assert at.button(key="start_compare").disabled                  # dub C still empty
    at.button(key="remove_dub").click().run()
    assert at.session_state["compare_n"] == 2 and not at.button(key="start_compare").disabled


def test_comparison_page_with_three_dubs_shows_the_ranking():
    from src.compare import build_ranking
    a, b, c = make_results(acoustic_metrics={"dubbed_duration_sec": 40.0}), make_results(), make_results()
    for r, seq in ((b, 100002), (c, 100003)):
        r["pipeline"]["share"].update(seq=seq)
    run = {"comparison": build_ranking([a, b, c], "en", run_seconds=5.0), "results": {"A": a, "B": b, "C": c},
           "files": {}}
    at = app(view="compare", compare_run=run)
    assert not at.exception
    text = all_text(at)
    assert "Deliver Dub B." in text and "**Ranking:** 1. Dub B" in text and "3. Dub A" in text
    assert at.button(key="seek_C_0").label == "19.4s"


def test_history_page_shows_totals_pairs_and_recent_runs():
    from src import history
    from src.report import build_report
    for sections in ({}, {"acoustic_metrics": {"dubbed_duration_sec": 40.0}}):
        r = make_results(**sections)
        r["report"] = build_report(r)
        history.record(r, "single")
    at = app()
    at.button(key="open_history").click().run()
    assert not at.exception and at.title[0].value == "Evaluation history"
    assert "2 runs on 1 dubs" in all_text(at)                         # same link twice: counts once
    assert len(at.dataframe) == 3                                       # pairs, problems, recent
    at.selectbox(key="history_days").set_value(7).run()
    assert not at.exception


def test_history_page_without_records_says_so():
    at = app(view="history")
    assert "No evaluations recorded yet" in all_text(at)
