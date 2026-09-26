"""Tests for the audio measurements: duration, silence, loudness and volume steadiness."""
import numpy as np

from src.evaluate import analyze_acoustics, SAMPLE_RATE


def tone(seconds: float, amp: float = 0.5) -> np.ndarray:
    """A 220 Hz sine wave of the given length, used as fake speech."""
    t = np.arange(int(seconds * SAMPLE_RATE)) / SAMPLE_RATE
    return (amp * np.sin(2 * np.pi * 220 * t)).astype(np.float32)


def test_duration_and_silence_ratio():
    y = np.concatenate([tone(1.0), np.zeros(SAMPLE_RATE, dtype=np.float32)])
    a = analyze_acoustics(y)
    assert a["duration_sec"] == 2.0
    assert 40.0 <= a["silence_ratio_pct"] <= 60.0


def test_steady_tone_is_stable_and_not_silent():
    a = analyze_acoustics(tone(2.0))
    assert a["silence_ratio_pct"] < 5.0
    assert a["volume_stability_pct"] > 90.0
    assert abs(a["mean_rms_energy"] - 0.5 / np.sqrt(2)) < 0.01


def test_pure_silence_does_not_crash():
    a = analyze_acoustics(np.zeros(SAMPLE_RATE, dtype=np.float32))
    assert a["mean_rms_energy"] == 0.0
    assert a["volume_stability_pct"] == 0.0
    assert a["silence_ratio_pct"] == 100.0
