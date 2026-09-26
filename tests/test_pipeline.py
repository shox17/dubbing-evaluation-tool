"""Tests for the pipeline: input validation, demo mode, results files and full runs against the fake API."""
import os
import threading

import pytest

from src import pipeline
from src.perso_api import Cancelled
from conftest import SAMPLE_ORIGINAL
from fake_perso import FakePerso, CopyingFakePerso


def test_demo_mode_rejects_other_videos(isolated_output, tmp_path):
    other = tmp_path / "other.mp4"
    other.write_bytes(b"x")
    with pytest.raises(ValueError, match="Demo mode only works"):
        pipeline.run_pipeline(str(other), "Korean", use_demo_mode=True)


def test_demo_mode_rejects_other_languages(isolated_output):
    with pytest.raises(ValueError, match="Demo mode only works"):
        pipeline.run_pipeline(SAMPLE_ORIGINAL, "Japanese", use_demo_mode=True)


def test_unknown_language_is_rejected_before_upload(isolated_output):
    fake = FakePerso()
    with pytest.raises(ValueError, match="Unsupported target language"):
        pipeline.run_pipeline(SAMPLE_ORIGINAL, "Klingon", client=fake.client())
    assert [p for _, p, _ in fake.calls] == ["/video-translator/api/v1/languages"]


def test_missing_input_is_rejected(isolated_output):
    with pytest.raises(FileNotFoundError):
        pipeline.run_pipeline("does/not/exist.mp4", "Korean")


def test_unsupported_extension_is_rejected_before_upload(isolated_output, tmp_path):
    avi = tmp_path / "clip.avi"
    avi.write_bytes(b"x")
    fake = FakePerso()
    with pytest.raises(ValueError, match="Perso accepts"):
        pipeline.run_pipeline(str(avi), "Korean", client=fake.client())
    assert fake.calls == []


def test_probe_video_reads_sample():
    info = pipeline.probe_video(SAMPLE_ORIGINAL)
    assert info["width"] == 1920 and info["height"] == 1080 and 28_000 < info["duration_ms"] < 29_500


def test_stages_depend_on_options():
    assert pipeline.pipeline_stages(True, True) == ["evaluate"]
    assert pipeline.pipeline_stages(False, False) == ["upload", "dubbing", "download", "evaluate"]
    assert "lipsync" in pipeline.pipeline_stages(False, True)


def test_results_roundtrip_and_corrupt_file(isolated_output):
    assert pipeline.load_results() is None
    pipeline.save_results({"schema_version": 3, "x": "한국어"})
    assert pipeline.load_results() == {"schema_version": 3, "x": "한국어"}
    (isolated_output / "results.json").write_text("{not json")
    assert pipeline.load_results() is None


def test_prune_keeps_newest_runs(isolated_output):
    runs = isolated_output / "runs"
    for i in range(5):
        d = runs / f"run{i}"
        d.mkdir(parents=True)
        os.utime(d, (i, i))
    pipeline.prune_old_runs(keep=2)
    assert sorted(os.listdir(runs)) == ["run3", "run4"]


def test_sample_script_available_for_demo():
    assert "우즈베키스탄" in pipeline.get_default_ground_truth("ko")


def test_cancel_before_evaluation(isolated_output, monkeypatch):
    fake = CopyingFakePerso(SAMPLE_ORIGINAL)
    ev = threading.Event()
    ev.set()
    with pytest.raises(Cancelled):
        pipeline.run_pipeline(SAMPLE_ORIGINAL, "Korean", lip_dubbing=False, client=fake.client(), cancel_event=ev)


@pytest.mark.slow
def test_demo_pipeline_end_to_end(isolated_output):
    stages = []
    r = pipeline.run_pipeline(SAMPLE_ORIGINAL, "Korean", use_demo_mode=True, whisper_model_name="base",
                              ground_truth_text=pipeline.get_default_ground_truth("ko"),
                              report=lambda p: stages.append(p.stage))
    assert set(stages) == {"evaluate"}
    assert r["schema_version"] == 3
    assert r["acoustic_metrics"]["duration_diff_sec"] == 0.0
    assert len(r["acoustic_metrics"]["loudness_envelope"]["original_db"]) > 100
    assert r["speech_recognition"]["primary_metric"] == "cer"
    assert r["speech_recognition"]["error_rate"] < 0.6
    assert r["speech_recognition"]["dubbed_speech_rate"]["unit"] == "chars/s"
    assert r["speech_recognition"]["original_speech_rate"]["unit"] == "words/s"
    assert r["metadata"]["detected_source_language"] == "en"
    assert (isolated_output / "results.json").exists()


@pytest.mark.slow
def test_demo_without_script_is_not_scored(isolated_output):
    r = pipeline.run_pipeline(SAMPLE_ORIGINAL, "Korean", use_demo_mode=True, whisper_model_name="tiny")
    assert r["speech_recognition"]["accuracy_pct"] is None
    assert any("No target script" in w for w in r["warnings"])


@pytest.mark.slow
def test_live_run_with_lipsync_waits_and_evaluates(isolated_output):
    """Full live flow against the fake API: upload -> dub -> lip-sync -> download -> evaluate."""
    fake = CopyingFakePerso(SAMPLE_ORIGINAL)
    progress = []
    r = pipeline.run_pipeline(SAMPLE_ORIGINAL, "English", lip_dubbing=True, client=fake.client(),
                              ground_truth_text=pipeline.DEFAULT_TRANSCRIPTS["en"], whisper_model_name="base",
                              report=progress.append)
    assert [s for s in dict.fromkeys(p.stage for p in progress)] == ["upload", "dubbing", "lipsync", "download", "evaluate"]
    assert "Applying Lip Sync" in {p.message for p in progress if p.stage == "lipsync"} or \
        "Re-rendering lips to match the new audio" in {p.message for p in progress}
    assert r["pipeline"]["execution_mode"] == "Perso AI + lip-sync"
    assert r["pipeline"]["perso"] == {"space_seq": 7, "media_seq": 555, "dubbing_project": 100, "lipsync_project": 101}
    targets = [c[2]["target"] for c in fake.calls if c[1].endswith("/download")]
    assert targets == ["lipSyncVideo"]
    assert r["speech_recognition"]["perso_translation"] == "안녕하세요. 저는 존입니다."
    assert r["speech_recognition"]["vs_perso_script"] is not None
    # The 'dub' is the English original here, so it should match the English script well.
    assert r["speech_recognition"]["primary_metric"] == "wer" and r["speech_recognition"]["error_rate"] < 0.5


@pytest.mark.slow
def test_lipsync_failure_falls_back_to_dub(isolated_output):
    fake = CopyingFakePerso(SAMPLE_ORIGINAL, fail_lipsync=True)
    r = pipeline.run_pipeline(SAMPLE_ORIGINAL, "English", lip_dubbing=True, client=fake.client(),
                              whisper_model_name="tiny")
    assert r["pipeline"]["execution_mode"] == "Perso AI"
    assert any("Lip-sync failed" in w for w in r["warnings"])
    assert [c[2]["target"] for c in fake.calls if c[1].endswith("/download")] == ["dubbingVideo"]
