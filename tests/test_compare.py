"""Tests for compare mode: the decision rule, the comparison files, the CLI, caching and --original."""
import json
from pathlib import Path

import pytest

from src import cli, pipeline
from src.compare import build_comparison, decide, render_comparison_html, render_comparison_text
from src.perso_api import PersoError
from fake_perso import (SHARE_TOKEN, SHARE_TOKEN_B, SHARE_URL, SHARE_URL_B, SHARED_PROJECT, SHARED_PROJECT_B,
                        FakePerso)
from sample_results import JUDGED, make_results

NO_SLEEP = lambda s: None
GOOD = dict(verdict_rank=0, poor=0, check=0, problem_seconds=0.0, meaning_score=5, overlap_pct=81.0)


def f(**changes) -> dict:
    """Decision facts of a dub: a clean Good dub with the given changes."""
    return {**GOOD, **changes}


# ---------------- decision rule ----------------
@pytest.mark.parametrize("a, b, rule, winner", [
    (f(verdict_rank=1, check=1), f(verdict_rank=2, poor=1), "verdict", "A"),
    (f(verdict_rank=2, poor=2), f(verdict_rank=2, poor=1, check=5), "poor_items", "B"),
    (f(verdict_rank=1, check=1), f(verdict_rank=1, check=3), "check_items", "A"),
    (f(problem_seconds=7.5), f(problem_seconds=2.0), "problem_seconds", "B"),
    (f(meaning_score=4), f(meaning_score=5), "meaning_score", "B"),
    (f(overlap_pct=82.4), f(overlap_pct=79.0), "speech_timing", "A"),
])
def test_first_rule_that_separates_the_dubs_decides(a, b, rule, winner):
    dec = decide(a, b)
    assert (dec["rule"], dec["winner"], dec["tie"]) == (rule, winner, False)
    assert dec["values"] == {"A": a[dict(verdict="verdict_rank", poor_items="poor", check_items="check",
                                          problem_seconds="problem_seconds", meaning_score="meaning_score",
                                          speech_timing="overlap_pct")[rule]],
                             "B": b[dict(verdict="verdict_rank", poor_items="poor", check_items="check",
                                          problem_seconds="problem_seconds", meaning_score="meaning_score",
                                          speech_timing="overlap_pct")[rule]]}


def test_an_earlier_rule_wins_over_a_later_one():
    # B has fewer Poor items, but A has the better verdict: rule 1 decides before rule 2 is looked at.
    dec = decide(f(verdict_rank=1, check=9, problem_seconds=60.0), f(verdict_rank=2, poor=1))
    assert (dec["rule"], dec["winner"]) == ("verdict", "A")


def test_a_full_tie_recommends_a_and_says_so():
    dec = decide(f(), f())
    assert dec["tie"] and dec["winner"] == "A" and dec["rule"] is None


def test_a_missing_value_skips_that_rule():
    dec = decide(f(meaning_score=None, overlap_pct=70.0), f(meaning_score=5, overlap_pct=80.0))
    assert (dec["rule"], dec["winner"]) == ("speech_timing", "B") and dec["skipped"] == ["meaning_score"]


# ---------------- comparison ----------------
def poor_dub(**sections) -> dict:
    """A dub whose length is way off (Poor)."""
    return make_results(acoustic_metrics={"dubbed_duration_sec": 40.0}, translation_judge=JUDGED, **sections)


def as_b(r: dict) -> dict:
    """Marks results as coming from the second share link."""
    r["pipeline"]["share"].update(seq=100002, title="QA sample.mp4 → ko (v2)", share_url=SHARE_URL_B)
    return r


def test_better_verdict_is_recommended_with_values_and_summary():
    comp = build_comparison(poor_dub(), as_b(make_results(translation_judge=JUDGED)), "en")
    rec, why = comp["recommendation"], comp["reasoning"]
    assert rec["dub"] == "B" and rec["headline"] == "Deliver Dub B." and rec["ready"] and not rec["both_poor"]
    assert why["rule"] == "verdict" and why["values"] == {"A": "Poor", "B": "Good"}
    assert 2 <= len(why["summary"]) <= 3 and "Length match" in why["summary"][1]
    assert why["translation_used"] and comp["reasoning"]["rule_label"] == "1. Better overall verdict"


def test_both_poor_names_the_better_one_but_says_neither_is_ready():
    worse = poor_dub(video_integrity={**make_results()["video_integrity"],
                                      "dubbed": {**make_results()["video_integrity"]["dubbed"], "has_audio": False}})
    comp = build_comparison(worse, as_b(poor_dub()), "en")
    rec = comp["recommendation"]
    assert rec["dub"] == "B" and rec["both_poor"] and not rec["ready"]
    assert "Neither dub is ready to deliver" in rec["warning"]
    assert rec["fix_first"] and rec["fix_first"][0].startswith("Length match:")
    assert comp["reasoning"]["rule"] == "poor_items" and comp["reasoning"]["values"] == {"A": "2", "B": "1"}


def test_without_translation_the_decision_says_so_and_skips_that_rule():
    a = make_results(translation_judge=JUDGED, timing_alignment={"overlap_pct": 76.0})      # both Good: rule 6 decides
    b = as_b(make_results(timing_alignment={"overlap_pct": 80.0}))          # judge off for B
    comp = build_comparison(a, b, "en")
    why = comp["reasoning"]
    assert not why["translation_used"] and "without translation" in why["translation_note"]
    assert any("without translation" in n for n in comp["notes"])
    assert "5. Higher translation meaning score" in why["skipped_rules"]
    assert why["rule"] == "speech_timing" and comp["recommendation"]["dub"] == "B"


def test_problem_seconds_break_a_tie_on_counts():
    gap = {"mismatches": [{"start": 2.0, "end": 3.0, "kind": "dub_only"}]}
    a = make_results(translation_judge=JUDGED, timing_alignment=gap)
    b = as_b(make_results(translation_judge=JUDGED, timing_alignment={"mismatches": []}))
    comp = build_comparison(a, b, "en")
    assert comp["reasoning"]["rule"] == "problem_seconds" and comp["recommendation"]["dub"] == "B"
    assert comp["reasoning"]["values"] == {"A": "1.0 s", "B": "0.0 s"}


def test_identical_dubs_tie_and_a_is_recommended():
    comp = build_comparison(make_results(translation_judge=JUDGED), as_b(make_results(translation_judge=JUDGED)), "en")
    assert comp["recommendation"]["dub"] == "A" and comp["recommendation"]["tie"]
    assert "tied" in comp["recommendation"]["headline"] and comp["reasoning"]["rule"] == "tie"


@pytest.mark.parametrize("lang, titles", [
    ("en", ["1. RECOMMENDED VERSION", "2. PROBLEM INTERVALS", "3. REASONING", "EVERY CHECK, SIDE BY SIDE",
            "THE TWO LINKS", "MEASUREMENT NOTES"]),
    ("ko", ["1. 추천 버전", "2. 문제 구간", "3. 판단 근거", "전체 항목 나란히 보기", "두 링크 정보", "측정 참고 사항"]),
])
def test_comparison_text_starts_with_the_three_sections_in_order(lang, titles):
    comp = build_comparison(poor_dub(), as_b(make_results(translation_judge=JUDGED)), lang)
    text = render_comparison_text(comp)
    positions = [text.index(title) for title in titles]
    assert positions == sorted(positions)
    assert text.splitlines()[3].strip() == titles[0]          # right after the title bar
    assert "19.4s-20.1s | " in text and ("Dub B" if lang == "en" else "더빙 B") in text
    assert "Dubbing QA Studio 1." in text                     # tool version in the footer


def test_comparison_html_has_the_decision_sections_first():
    comp = build_comparison(poor_dub(), as_b(make_results(translation_judge=JUDGED)), "en")
    page = render_comparison_html(comp)
    order = [page.index(x) for x in ("1. Recommended version", "2. Problem intervals", "3. Reasoning",
                                     "Every check, side by side")]
    assert order == sorted(order) and "report_A.html" in page and page.startswith("<!doctype html>")


def test_interval_lines_carry_every_field():
    comp = build_comparison(make_results(translation_judge=JUDGED), as_b(make_results(translation_judge=JUDGED)), "en")
    text = render_comparison_text(comp, width=300)
    line = next(x for x in text.splitlines() if x.strip().startswith("19.4s-20.1s | Dub A"))
    assert line.strip().split(" | ")[:5] == ["19.4s-20.1s", "Dub A", "timing", "Check", "Speech timing"]


# ---------------- pipeline, files and CLI (fake Perso, no real network) ----------------
@pytest.fixture
def two_links(monkeypatch, isolated_output):
    """A fake Perso serving two share links, and a fake measurement: A is Poor, B is Good."""
    fake = FakePerso(original_bytes=b"orig", video_bytes=b"dub",
                     projects={SHARE_TOKEN: dict(SHARED_PROJECT), SHARE_TOKEN_B: dict(SHARED_PROJECT_B)})
    plan = {"A": make_results(acoustic_metrics={"dubbed_duration_sec": 40.0}), "B": make_results()}
    calls = []

    def fake_eval(**kw):
        calls.append(kw)
        r = plan["A" if len(calls) % 2 == 1 else "B"]          # dubs are evaluated in order: A, then B
        return {k: v for k, v in r.items() if k not in ("pipeline", "translation_judge")}
    monkeypatch.setattr(pipeline, "run_full_evaluation", fake_eval)
    real = pipeline.run_comparison
    monkeypatch.setattr(cli, "run_comparison", lambda *a, **kw: real(*a, **{**kw, "session": fake, "sleep": NO_SLEEP}))
    return {"fake": fake, "plan": plan, "calls": calls}


def test_compare_cli_writes_every_file_and_recommends_b(two_links, tmp_path, capsys):
    out = tmp_path / "out" / "nested"
    code = cli.main(["compare", SHARE_URL, SHARE_URL_B, "--out", str(out), "--lang", "en", "--no-translation-check"])
    assert code == 0
    for name in ("comparison.txt", "comparison.json", "comparison.html", "report_A.html", "report_A.json",
                 "report_A.txt", "report_B.html", "report_B.json", "report_B.txt"):
        assert (out / name).is_file(), name
    text = (out / "comparison.txt").read_text(encoding="utf-8")
    assert "Deliver Dub B." in text and "without translation" in text
    saved = json.loads((out / "comparison.json").read_text(encoding="utf-8"))
    assert saved["recommendation"]["dub"] == "B" and "reports" not in saved
    assert "Deliver Dub B." in capsys.readouterr().out


def test_compare_exit_code_1_when_both_dubs_are_poor(two_links, tmp_path):
    two_links["plan"]["B"] = make_results(acoustic_metrics={"dubbed_duration_sec": 40.0})
    assert cli.main(["compare", SHARE_URL, SHARE_URL_B, "--out", str(tmp_path), "--no-translation-check"]) == 1
    assert "두 더빙 모두 납품할 준비가 되지 않았습니다" in (tmp_path / "comparison.txt").read_text(encoding="utf-8")


def test_compare_exit_code_2_for_a_bad_link_or_sharing_off(two_links, tmp_path, capsys):
    assert cli.main(["compare", SHARE_URL, "https://example.com/x", "--out", str(tmp_path)]) == 2
    assert "doesn't look like a Perso share link" in capsys.readouterr().err
    two_links["fake"].share_error = (403, "VT4035")
    assert cli.main(["compare", SHARE_URL, SHARE_URL_B, "--out", str(tmp_path)]) == 2
    assert "Sharing is turned off" in capsys.readouterr().err


def test_compare_progress_goes_through_both_dubs(two_links, tmp_path):
    stages = []
    pipeline.run_comparison(SHARE_URL, SHARE_URL_B, str(tmp_path), report=lambda p: stages.append(p.stage),
                            use_translation_judge=False, session=two_links["fake"], sleep=NO_SLEEP)
    assert stages[0] == "dub_a" and "dub_b" in stages and stages[-1] == "compare"


def test_single_mode_writes_report_files_into_out(isolated_output, monkeypatch, tmp_path):
    monkeypatch.setattr(pipeline, "run_full_evaluation",
                        lambda **kw: {k: v for k, v in make_results().items() if k not in ("pipeline", "translation_judge")})
    r = pipeline.run_share_evaluation(SHARE_URL, out_dir=str(tmp_path / "o"), use_translation_judge=False,
                                      session=FakePerso(), sleep=NO_SLEEP)
    assert sorted(p.name for p in (tmp_path / "o").iterdir()) == ["report.html", "report.json", "report.txt"]
    assert r["pipeline"]["report_files"]["html"].endswith("report.html")


# ---------------- cache ----------------
def test_rerun_reuses_downloads_and_hands_evaluation_a_cache(isolated_output, monkeypatch):
    seen = []
    monkeypatch.setattr(pipeline, "run_full_evaluation", lambda **kw: seen.append(kw) or
                        {k: v for k, v in make_results().items() if k not in ("pipeline", "translation_judge")})
    fake = FakePerso()
    for _ in range(2):
        pipeline.run_share_evaluation(SHARE_URL, use_translation_judge=False, session=fake, sleep=NO_SLEEP)
    assert len([c for c in fake.calls if c[0] == "GET-MEDIA"]) == 2           # only the first run downloaded
    assert seen[0]["dubbed_video_path"] == seen[1]["dubbed_video_path"]
    cache = seen[1]["cache"]
    cache["stt|base|ko|x"] = {"text": "안녕"}
    assert pipeline.JsonCache(cache.path).get("stt|base|ko|x") == {"text": "안녕"}


def test_no_cache_downloads_again(isolated_output, monkeypatch):
    monkeypatch.setattr(pipeline, "run_full_evaluation",
                        lambda **kw: {k: v for k, v in make_results().items() if k not in ("pipeline", "translation_judge")})
    fake = FakePerso()
    pipeline.run_share_evaluation(SHARE_URL, use_translation_judge=False, session=fake, sleep=NO_SLEEP)
    pipeline.run_share_evaluation(SHARE_URL, use_translation_judge=False, use_cache=False, session=fake, sleep=NO_SLEEP)
    assert len([c for c in fake.calls if c[0] == "GET-MEDIA"]) == 4


# ---------------- --original ----------------
def test_missing_original_needs_the_original_option(isolated_output, monkeypatch, tmp_path):
    seen = {}
    monkeypatch.setattr(pipeline, "run_full_evaluation", lambda **kw: seen.update(kw) or
                        {k: v for k, v in make_results().items() if k not in ("pipeline", "translation_judge")})
    fake = FakePerso(shared_project={**SHARED_PROJECT, "originalFileUrl": None})
    with pytest.raises(PersoError, match="--original"):
        pipeline.run_share_evaluation(SHARE_URL, use_translation_judge=False, session=fake, sleep=NO_SLEEP)
    with pytest.raises(FileNotFoundError):
        pipeline.run_share_evaluation(SHARE_URL, original=str(tmp_path / "nope.mp4"), use_translation_judge=False,
                                      session=fake, sleep=NO_SLEEP)
    local = tmp_path / "원본 video.mp4"
    local.write_bytes(b"orig")
    r = pipeline.run_share_evaluation(SHARE_URL, original=str(local), use_translation_judge=False,
                                      session=fake, sleep=NO_SLEEP)
    assert seen["original_video_path"] == str(local.resolve()) and r["pipeline"]["share"]["original_from"] == "--original"
    pipeline.run_share_evaluation(SHARE_URL, original="https://portal-media.perso.ai/perso-storage/x/original/o.mp4",
                                  use_translation_judge=False, session=fake, sleep=NO_SLEEP)
    assert Path(seen["original_video_path"]).read_bytes() == fake.original_bytes            # downloaded via the URL


# ---------------- translation-check cache ----------------
def test_translation_check_is_cached_per_link_but_failures_are_retried(isolated_output, monkeypatch):
    from src.translation_judge import not_measured
    monkeypatch.setattr(pipeline, "run_full_evaluation",
                        lambda **kw: {k: v for k, v in make_results().items() if k not in ("pipeline", "translation_judge")})
    answers = iter([not_measured("r.judge.busy", model="Gemini"), JUDGED])
    calls = []
    monkeypatch.setattr(pipeline, "judge_translation", lambda *a, **k: calls.append(a) or next(answers))
    fake = FakePerso()
    runs = [pipeline.run_share_evaluation(SHARE_URL, session=fake, sleep=NO_SLEEP) for _ in range(3)]
    assert len(calls) == 2                                    # busy → asked again; success → cached
    assert runs[0]["translation_judge"]["measured"] is False
    assert runs[1]["translation_judge"]["meaning_score"] == 5 and not runs[1]["translation_judge"].get("cached")
    assert runs[2]["translation_judge"]["meaning_score"] == 5 and runs[2]["translation_judge"]["cached"]
