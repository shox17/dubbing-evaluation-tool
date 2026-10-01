"""Tests for batch mode: the input file, summary rows, agreement with a person's verdicts, files and the CLI."""
import csv
import io
import json

import pytest

from src import cli, pipeline
from src.batch import agreement, parse_batch_file, render_batch_text, summary_row, to_csv
from src.report import build_report
from fake_perso import SHARE_TOKEN, SHARE_TOKEN_B, SHARE_URL, SHARE_URL_B, SHARED_PROJECT, SHARED_PROJECT_B, FakePerso
from sample_results import make_results

NO_SLEEP = lambda s: None


def test_batch_file_takes_links_labels_comments_and_a_header():
    text = "﻿url,label\n# my test set\n\nhttps://perso.ai/a?seq=x1, Good\nhttps://perso.ai/b?seq=x2;needs review\n" \
           "https://perso.ai/c?seq=x3\t poor\n\"https://perso.ai/d?seq=x4\"\n"
    entries = parse_batch_file(text)
    assert [(e["link"], e["label"]) for e in entries] == [
        ("https://perso.ai/a?seq=x1", "good"), ("https://perso.ai/b?seq=x2", "check"),
        ("https://perso.ai/c?seq=x3", "poor"), ("https://perso.ai/d?seq=x4", None)]


@pytest.mark.parametrize("text, msg", [("https://perso.ai/a?seq=x1,excellent", "unknown verdict"), ("# nothing\n\n", "no links")])
def test_bad_batch_files_get_plain_errors(text, msg):
    with pytest.raises(ValueError, match=msg):
        parse_batch_file(text)


def row(verdict: str, label: str) -> dict:
    """A summary row with the tool's verdict and a person's label."""
    return {"human_label": label, "verdict": verdict, "error": ""}


def test_agreement_counts_matches_and_which_way_the_tool_errs():
    agr = agreement([row("good", "good"), row("poor", "check"), row("check", "poor"), row("poor", "good"),
                     row("check", "")])
    assert (agr["labelled"], agr["agree"], agr["agree_pct"]) == (4, 1, 25.0)
    assert (agr["too_strict"], agr["too_lenient"]) == (2, 1)
    assert agr["table"]["good"]["poor"] == 1
    assert agreement([row("good", "")]) is None


def test_summary_row_flattens_every_measure_and_keeps_errors():
    r = make_results()
    r["report"] = build_report(r)
    full = summary_row(1, {"link": "L", "label": "good"}, r)
    assert full["verdict"] == "good" and full["agrees"] is True and full["speech_overlap_value"] == 81.0
    assert full["length_match_level"] == "good" and full["title"] == "QA sample.mp4 → ko"
    failed = summary_row(2, {"link": "bad", "label": None}, error="Sharing is turned off")
    assert failed["error"] == "Sharing is turned off" and failed["verdict"] == ""
    table = list(csv.DictReader(io.StringIO(to_csv([full, failed]))))
    assert table[0]["speech_overlap_level"] == "good" and table[1]["error"] == "Sharing is turned off"


@pytest.fixture
def batch_env(monkeypatch, isolated_output):
    """A fake Perso with two links and a fake measurement: the first link Poor, the second Good."""
    fake = FakePerso(projects={SHARE_TOKEN: dict(SHARED_PROJECT), SHARE_TOKEN_B: dict(SHARED_PROJECT_B)})
    plan = iter([make_results(acoustic_metrics={"dubbed_duration_sec": 40.0}), make_results()])
    monkeypatch.setattr(pipeline, "run_full_evaluation",
                        lambda **kw: {k: v for k, v in next(plan).items() if k not in ("pipeline", "translation_judge")})
    real = pipeline.run_batch
    monkeypatch.setattr(pipeline, "run_batch", lambda *a, **kw: real(*a, **{**kw, "session": fake, "sleep": NO_SLEEP}))
    return fake


def test_batch_cli_writes_summary_and_goes_on_after_a_broken_link(batch_env, tmp_path, capsys):
    links = tmp_path / "links.txt"
    links.write_text(f"{SHARE_URL},poor\nhttps://example.com/nope,good\n{SHARE_URL_B},poor\n", encoding="utf-8")
    out = tmp_path / "out"
    assert cli.main(["batch", str(links), "--out", str(out), "--lang", "en", "--no-translation-check"]) == 2
    text = (out / "summary.txt").read_text(encoding="utf-8")
    assert "3 links: 1 Good · 0 Needs review · 1 Poor · 1 failed" in text
    assert "Agreement with your verdicts: 1 of 2 (50%). Stricter than you: 0. More lenient: 1." in text
    rows = list(csv.DictReader(io.StringIO((out / "summary.csv").read_text(encoding="utf-8-sig"))))
    assert [r["verdict"] for r in rows] == ["poor", "", "good"] and "share link" in rows[1]["error"]
    assert (out / "001" / "report.html").is_file() and (out / "003" / "report.json").is_file()
    assert json.loads((out / "summary.json").read_text(encoding="utf-8"))["agreement"]["labelled"] == 2
    assert "1 failed" in capsys.readouterr().out


def test_batch_cli_exit_0_when_every_link_works_and_2_for_a_bad_file(batch_env, tmp_path):
    links = tmp_path / "links.txt"
    links.write_text(f"{SHARE_URL}\n{SHARE_URL_B}\n", encoding="utf-8")
    assert cli.main(["batch", str(links), "--out", str(tmp_path / "o"), "--no-translation-check"]) == 0
    assert "일괄 평가 요약" in (tmp_path / "o" / "summary.txt").read_text(encoding="utf-8")
    assert cli.main(["batch", str(tmp_path / "missing.txt")]) == 2
    (tmp_path / "bad.txt").write_text("https://perso.ai/a?seq=x1,amazing\n", encoding="utf-8")
    assert cli.main(["batch", str(tmp_path / "bad.txt")]) == 2


def test_batch_text_lists_every_link_in_korean():
    r = make_results()
    r["report"] = build_report(r, "ko")
    text = render_batch_text([summary_row(1, {"link": "L", "label": None}, r)], "ko")
    assert "좋음 · QA sample.mp4 → ko" in text and "도구가 얼마나 사람과 일치하는지" in text
