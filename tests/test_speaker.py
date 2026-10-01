"""Tests for voice similarity: filterbank features, the pinned model download, line selection, grading, intervals."""
import hashlib

import numpy as np
import pytest

from src import speaker
from src.i18n import t
from src.intervals import build_intervals
from src.report import build_report
from sample_results import make_results

SR = speaker.SAMPLE_RATE


def metric(rep: dict, mid: str) -> dict:
    """The report row with this id."""
    return next(m for s in rep["sections"] for m in s["metrics"] if m["id"] == mid)


# ---------------- features ----------------
def test_mel_banks_cover_the_spectrum_like_kaldi():
    banks = speaker.mel_banks(80, 512, SR)
    assert banks.shape == (80, 257) and banks[:, -1].sum() == 0          # Nyquist bin unused
    assert banks.max() <= 1.0 and (banks.sum(axis=1) > 0).all()
    assert np.argmax(banks[0]) < np.argmax(banks[40]) < np.argmax(banks[79])


def test_fbank_frames_and_a_tone_lands_in_the_right_band():
    t_ = np.arange(SR) / SR
    feats = speaker.fbank((0.5 * np.sin(2 * np.pi * 1000 * t_)).astype(np.float32))
    assert feats.shape == (98, 80) and feats.dtype == np.float32           # 1 s: (16000 - 400) // 160 + 1
    peak_band = int(np.argmax(feats.mean(axis=0)))
    banks = speaker.mel_banks(80, 512, SR)
    assert abs(np.argmax(banks[peak_band]) * SR / 512 - 1000) < 100
    assert speaker.fbank(np.zeros(100, dtype=np.float32)).shape == (0, 80)


# ---------------- model download ----------------
def test_model_is_downloaded_once_and_checked(tmp_path, monkeypatch):
    payload = b"fake-onnx-bytes"
    monkeypatch.setattr(speaker, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(speaker, "MODEL_SHA256", hashlib.sha256(payload).hexdigest())
    calls = []

    def download(url, out):
        calls.append(url)
        out.write_bytes(payload)
    assert speaker.model_path(download).read_bytes() == payload
    assert speaker.model_path(download) and len(calls) == 1                # second call uses the verified file
    assert "f0c48c298fd835726c27956a5d617bad7115627e" in calls[0]         # pinned to a commit


def test_a_bad_or_failed_download_is_refused(tmp_path, monkeypatch):
    monkeypatch.setattr(speaker, "CACHE_DIR", tmp_path)
    with pytest.raises(speaker.ModelUnavailable, match="checksum"):
        speaker.model_path(lambda url, out: out.write_bytes(b"tampered"))
    assert not list(tmp_path.iterdir())
    with pytest.raises(speaker.ModelUnavailable, match="download"):
        speaker.model_path(lambda url, out: (_ for _ in ()).throw(OSError("offline")))


# ---------------- comparison ----------------
class FakeSession:
    """Fingerprints from the audio's main frequency: same pitch → same voice."""
    def run(self, _outputs, feeds):
        band = int(np.argmax(feeds["feats"][0].std(axis=0)))
        e = np.zeros((1, 256), dtype=np.float32)
        e[0, band] = 1.0
        e[0, 255] = 0.3
        return [e]


def tone(freq: float, seconds: float) -> np.ndarray:
    """A buzzy tone (rich harmonics) standing in for a voice of this pitch."""
    t_ = np.arange(int(seconds * SR)) / SR
    return (0.3 * np.sign(np.sin(2 * np.pi * freq * t_)) * (1 + 0.5 * np.sin(2 * np.pi * 3 * t_))).astype(np.float32)


def lines(*spans):
    """Original transcript lines."""
    return [{"start": s, "end": e, "text": "x"} for s, e in spans]


def test_lines_are_compared_at_the_same_moment_and_noisy_ones_skipped():
    orig = np.concatenate([tone(150, 3), tone(250, 3), tone(150, 3)])
    dub = np.concatenate([tone(150, 3), tone(400, 3), tone(150, 3)])
    quiet_bg = lambda audio: 4.0
    r = speaker.voice_similarity(orig, dub, lines((0, 3), (3, 6), (6, 9), (8.5, 9.0)), quiet_bg, FakeSession())
    assert r["measured"] and [l["start"] for l in r["lines"]] == [0, 3, 6]          # the 0.5 s line is skipped
    assert r["lines"][0]["similarity"] > 0.99 and r["lines"][1]["similarity"] < 0.2
    loud_bg = lambda audio: 2.0
    noisy = speaker.voice_similarity(orig, dub, lines((0, 3), (3, 6)), loud_bg, FakeSession())
    assert not noisy["measured"] and noisy["reason_key"] == "r.vs.noisy" and noisy["skipped_noisy"] == 2
    few = speaker.voice_similarity(orig, dub, lines((0, 3)), quiet_bg, FakeSession())
    assert few["reason_key"] == "r.vs.few_lines"


# ---------------- grading and intervals ----------------
def vs_result(*sims) -> dict:
    """A measured voice-similarity result with these per-line similarities."""
    ls = [{"start": i * 5.0, "end": i * 5.0 + 3.0, "similarity": s} for i, s in enumerate(sims)]
    return {"measured": True, "reason_key": None, "median": float(np.median(sims)), "lines": ls, "skipped_noisy": 0}


@pytest.mark.parametrize("sims, level", [((0.8, 0.85, 0.82), "good"), ((0.5, 0.52, 0.49), "good"),
                                         ((0.15, 0.2, 0.3), "check")])
def test_similarity_is_good_or_check_never_poor(sims, level):
    row = metric(build_report(make_results(voice_similarity=vs_result(*sims))), "voice_similarity")
    assert row["level"] == level and row["thresholds"] and "lines" in row["display"]


def test_not_measured_reasons_are_explained():
    row = metric(build_report(make_results(voice_similarity=speaker.not_measured("r.vs.noisy"))), "voice_similarity")
    assert row["level"] == "not_measured" and "too loud" in row["message"]
    row = metric(build_report(make_results(voice_similarity=speaker.not_measured("r.vs.no_model"))), "voice_similarity")
    assert "couldn't be downloaded" in row["message"]


@pytest.mark.parametrize("sims, flagged", [
    ((0.8, 0.86, 0.87, 0.81), []),            # a good clone: nothing stands out
    ((0.8, 0.86, 0.55, 0.81), [10.0]),        # a similar but different voice on one line
    ((0.8, 0.2, 0.87, 0.81), [5.0]),          # the other character's voice on one line
    ((0.08, 0.22, 0.08, 0.3), []),            # a stock voice throughout: low overall, no single odd line
])
def test_a_line_with_another_voice_becomes_an_interval(sims, flagged):
    r = make_results(timing_alignment={"mismatches": []}, acoustic_metrics={"dubbed_duration_sec": 30.0},
                     voice_similarity=vs_result(*sims))
    out = build_intervals(r, lambda key, **p: t(key, "en", **p), "en")["intervals"]
    assert [i["start"] for i in out if i["category"] == "voice_change"] == flagged
