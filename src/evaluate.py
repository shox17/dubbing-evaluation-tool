"""All quality measurements for a dub: audio, speech recognition (Whisper) and lip movement (MediaPipe).

Pure functions: they take files or waveforms and return dicts. Nothing here writes files or talks to Perso.
"""
import os
import re
import logging
import subprocess
import tempfile
import threading
import unicodedata
from typing import Callable, Optional

import numpy as np
import librosa
import whisper
import jiwer
import cv2
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision
import imageio_ffmpeg

log = logging.getLogger(__name__)

SRC_DIR = os.path.dirname(os.path.abspath(__file__))
FACE_MODEL_PATH = os.path.join(SRC_DIR, "face_landmarker.task")
FFMPEG_EXE = imageio_ffmpeg.get_ffmpeg_exe()
SAMPLE_RATE = 16000

DEFAULT_WHISPER_MODEL = os.getenv("WHISPER_MODEL", "small")

# Scripts written without spaces between words (or with coarse spacing units) are scored by CER.
CER_LANGS = {"ja", "zh", "ko", "th"}

# Perso language codes that Whisper spells differently.
WHISPER_CODE_ALIASES = {"fil": "tl", "jv": "jw"}

# Lip-sync analysis settings
LIPSYNC_SAMPLE_FPS = 15.0          # frames analysed per second of video
LIPSYNC_MAX_SECONDS = 60.0         # analysis window from the start of the clip
LIPSYNC_MAX_LAG_MS = 200           # diagnostic lag search range (+/-); never used for the headline score
LIPSYNC_MIN_FACE_COVERAGE = 0.5    # below this the result is reported as invalid
LIPSYNC_MIN_FRAMES = 20

_whisper_models: dict = {}
_whisper_lock = threading.Lock()


def get_whisper_model(model_name: str = DEFAULT_WHISPER_MODEL):
    """Loads and caches Whisper models in memory, keyed by model name."""
    with _whisper_lock:
        if model_name not in _whisper_models:
            log.info("Loading Whisper model %r", model_name)
            _whisper_models[model_name] = whisper.load_model(model_name)
        return _whisper_models[model_name]


def extract_audio(video_path: str, output_audio_path: str, sample_rate: int = SAMPLE_RATE) -> str:
    """Extracts 16kHz mono PCM WAV audio using the bundled ffmpeg binary."""
    os.makedirs(os.path.dirname(os.path.abspath(output_audio_path)), exist_ok=True)
    command = [
        FFMPEG_EXE, "-nostdin", "-y",
        "-i", video_path,
        "-vn",
        "-acodec", "pcm_s16le",
        "-ar", str(sample_rate),
        "-ac", "1",
        output_audio_path
    ]
    proc = subprocess.run(command, capture_output=True)
    if proc.returncode != 0:
        tail = proc.stderr.decode(errors="replace").strip().splitlines()[-3:]
        raise RuntimeError(f"ffmpeg could not extract audio from {video_path}: {' | '.join(tail)}")
    return output_audio_path


def load_audio(audio_path: str) -> np.ndarray:
    """Loads a mono float32 waveform at SAMPLE_RATE."""
    y, _ = librosa.load(audio_path, sr=SAMPLE_RATE, mono=True)
    return y.astype(np.float32)


def analyze_acoustics(y: np.ndarray, sr: int = SAMPLE_RATE) -> dict:
    """Computes acoustic features: duration, mean RMS energy, volume stability, and silence ratio."""
    duration = float(len(y) / sr) if sr else 0.0

    rms_frames = librosa.feature.rms(y=y, frame_length=2048, hop_length=512)[0] if len(y) else np.array([])
    mean_rms = float(np.mean(rms_frames)) if len(rms_frames) > 0 else 0.0
    std_rms = float(np.std(rms_frames)) if len(rms_frames) > 0 else 0.0

    stability = max(0.0, min(100.0, (1.0 - (std_rms / mean_rms)) * 100.0)) if mean_rms > 1e-6 else 0.0

    if len(y) and np.max(np.abs(y)) > 0:
        non_silent_intervals = librosa.effects.split(y, top_db=20)
        non_silent_duration = sum((end - start) / sr for start, end in non_silent_intervals)
    else:
        non_silent_duration = 0.0
    silence_ratio = float((duration - non_silent_duration) / duration) if duration > 0 else 0.0

    return {
        "duration_sec": round(duration, 2),
        "mean_rms_energy": round(mean_rms, 4),
        "rms_std": round(std_rms, 4),
        "volume_stability_pct": round(stability, 1),
        "silence_ratio_pct": round(silence_ratio * 100, 2)
    }


def normalize_text(text: str) -> str:
    """Unicode-normalizes, lowercases, strips punctuation/symbols and collapses whitespace."""
    text = unicodedata.normalize("NFKC", text or "").lower()
    text = "".join(" " if unicodedata.category(ch)[0] in ("P", "S") else ch for ch in text)
    return re.sub(r"\s+", " ", text).strip()


def score_transcript(ground_truth: str, hypothesis: str, lang: str) -> dict:
    """Scores a transcript against ground truth with WER and CER; picks the primary metric by language."""
    ref = normalize_text(ground_truth)
    hyp = normalize_text(hypothesis)
    if not ref:
        return {"wer": None, "cer": None, "primary_metric": None, "error_rate": None, "accuracy_pct": None}

    wer = float(jiwer.wer(ref, hyp)) if hyp else 1.0
    # CER ignores word boundaries, so spacing differences don't count as errors.
    cer = float(jiwer.cer(ref.replace(" ", ""), hyp.replace(" ", ""))) if hyp else 1.0
    primary = "cer" if lang in CER_LANGS else "wer"
    error_rate = cer if primary == "cer" else wer
    return {
        "wer": round(wer, 3),
        "cer": round(cer, 3),
        "primary_metric": primary,
        "error_rate": round(error_rate, 3),
        "accuracy_pct": round(max(0.0, 1.0 - error_rate) * 100.0, 1)
    }


def whisper_language(code: str) -> Optional[str]:
    """Whisper's code for a Perso language code, or None when Whisper has no model for it."""
    code = WHISPER_CODE_ALIASES.get(code, code)
    return code if code in whisper.tokenizer.LANGUAGES else None


def transcribe(y: np.ndarray, whisper_model, language: Optional[str] = None) -> dict:
    """Transcribes a 16kHz waveform with Whisper. language=None lets Whisper detect it."""
    result = whisper_model.transcribe(y, language=language, fp16=False)
    return {"text": result.get("text", "").strip(), "language": result.get("language", language)}


def _mouth_aspect_ratio(lm) -> float:
    """How open the mouth is: lip gap divided by mouth width, from MediaPipe face landmarks."""
    v_dist = ((lm[13].x - lm[14].x) ** 2 + (lm[13].y - lm[14].y) ** 2) ** 0.5
    h_dist = ((lm[61].x - lm[291].x) ** 2 + (lm[61].y - lm[291].y) ** 2) ** 0.5
    return float(v_dist / (h_dist + 1e-6))


def _pearson(a: np.ndarray, b: np.ndarray) -> float:
    """Pearson correlation of two series; 0.0 when either is too short or flat to correlate."""
    if len(a) < 3 or np.std(a) < 1e-9 or np.std(b) < 1e-9:
        return 0.0
    r = float(np.corrcoef(a, b)[0, 1])
    return 0.0 if np.isnan(r) else r


def _sync_quality(r: float) -> str:
    """Turns a lip-sync correlation into a label: strong, moderate, weak or none."""
    if r >= 0.4:
        return "strong"
    if r >= 0.2:
        return "moderate"
    if r >= 0.05:
        return "weak"
    return "none"


def analyze_lipsync(video_path: str, y: np.ndarray, sr: int = SAMPLE_RATE,
                    model_path: str = FACE_MODEL_PATH, max_seconds: float = LIPSYNC_MAX_SECONDS) -> dict:
    """Correlates mouth opening (MediaPipe MAR) with speech loudness (RMS).

    Experimental: the headline score is the zero-lag Pearson r. The best r over a +/-200 ms lag window is
    reported only as a diagnostic, because maximising over lags inflates pure noise to r ~ +0.1.
    """
    invalid = {
        "valid": False, "reason": "", "pearson_correlation": None, "best_lag_correlation": None,
        "best_lag_ms": None, "sync_quality": "n/a", "face_coverage_pct": 0.0, "frames_analyzed": 0,
        "timestamps": [], "mar_waveform": [], "rms_waveform": []
    }

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return {**invalid, "reason": "video could not be opened"}
    fps = cap.get(cv2.CAP_PROP_FPS)
    if not fps or fps <= 0 or np.isnan(fps):
        fps = 25.0
    stride = max(1, int(round(fps / LIPSYNC_SAMPLE_FPS)))
    max_frame = int(max_seconds * fps)

    options = vision.FaceLandmarkerOptions(
        base_options=mp_python.BaseOptions(model_asset_path=model_path),
        running_mode=vision.RunningMode.VIDEO,
        num_faces=1
    )
    timestamps, mar_values = [], []
    try:
        with vision.FaceLandmarker.create_from_options(options) as detector:
            idx = 0
            while idx < max_frame:
                # grab() skips decoding of frames we don't analyse; retrieve() decodes only sampled ones.
                if not cap.grab():
                    break
                if idx % stride == 0:
                    ok, frame = cap.retrieve()
                    if not ok:
                        break
                    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    t = idx / fps
                    res = detector.detect_for_video(mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb), int(t * 1000))
                    timestamps.append(t)
                    mar_values.append(_mouth_aspect_ratio(res.face_landmarks[0]) if res.face_landmarks else np.nan)
                idx += 1
    finally:
        cap.release()

    n = len(mar_values)
    mar = np.array(mar_values, dtype=np.float64)
    ts = np.array(timestamps, dtype=np.float64)
    face_mask = ~np.isnan(mar)
    coverage = float(face_mask.mean()) if n else 0.0
    base = {**invalid, "face_coverage_pct": round(coverage * 100, 1), "frames_analyzed": n}

    if n < LIPSYNC_MIN_FRAMES:
        return {**base, "reason": f"only {n} frames analysed"}
    if coverage < LIPSYNC_MIN_FACE_COVERAGE:
        return {**base, "reason": f"face detected in only {coverage * 100:.0f}% of frames"}

    # Audio RMS on a fine 10 ms grid, then sampled at (lag-shifted) frame times.
    hop = sr // 100
    rms = librosa.feature.rms(y=y, frame_length=hop * 4, hop_length=hop)[0]
    rms_t = librosa.frames_to_time(np.arange(len(rms)), sr=sr, hop_length=hop)

    ts_face, mar_face = ts[face_mask], mar[face_mask]
    if np.std(mar_face) < 1e-6:
        return {**base, "reason": "mouth shape does not change"}
    mar_z = (mar_face - mar_face.mean()) / mar_face.std()

    def corr_at(lag_s: float) -> float:
        """Correlation between mouth opening and loudness with the audio shifted by lag_s seconds."""
        audio = np.interp(ts_face + lag_s, rms_t, rms, left=0.0, right=0.0)
        return _pearson(mar_z, audio)

    lags_ms = range(-LIPSYNC_MAX_LAG_MS, LIPSYNC_MAX_LAG_MS + 1, 20)
    best_r, best_lag = max((corr_at(l / 1000.0), l) for l in lags_ms)
    zero_r = corr_at(0.0)

    audio = np.interp(ts_face, rms_t, rms, left=0.0, right=0.0)
    audio_z = (audio - audio.mean()) / (audio.std() + 1e-9)

    return {
        "valid": True,
        "reason": "",
        "pearson_correlation": round(zero_r, 4),
        "best_lag_correlation": round(best_r, 4),
        "best_lag_ms": int(best_lag),
        "sync_quality": _sync_quality(zero_r),
        "face_coverage_pct": round(coverage * 100, 1),
        "frames_analyzed": n,
        "timestamps": [round(float(t), 3) for t in ts_face],
        "mar_waveform": [round(float(v), 3) for v in mar_z],
        "rms_waveform": [round(float(v), 3) for v in audio_z]
    }


def _quality_warnings(orig_ac: dict, dub_ac: dict, stt: dict, dub_ls: dict, dub_text: str) -> list[str]:
    """Plain-language warnings for results that look wrong (mismatched videos, empty transcript, ...)."""
    warnings = []
    od, dd = orig_ac["duration_sec"], dub_ac["duration_sec"]
    if od > 0 and abs(dd - od) / od > 0.2:
        warnings.append(
            f"Dubbed duration ({dd}s) differs from the original ({od}s) by more than 20% — "
            "the videos may not be a matching pair."
        )
    if not dub_text:
        warnings.append("Whisper produced no transcript for the dubbed audio.")
    if stt.get("error_rate") is not None and stt["error_rate"] > 0.8:
        warnings.append(
            f"{stt['primary_metric'].upper()} is {stt['error_rate']:.2f} — check that the ground-truth script "
            "matches this video and target language."
        )
    if not dub_ls["valid"]:
        warnings.append(f"Lip-sync could not be measured on the dubbed video: {dub_ls['reason']}.")
    return warnings


def loudness_envelope(y: np.ndarray, sr: int = SAMPLE_RATE, step_sec: float = 0.25) -> list[float]:
    """Loudness in dBFS per step_sec window, for plotting original vs dub over time."""
    hop = int(sr * step_sec)
    if len(y) < hop:
        return []
    rms = librosa.feature.rms(y=y, frame_length=hop, hop_length=hop, center=False)[0]
    return [round(float(v), 1) for v in 20 * np.log10(np.maximum(rms, 1e-5))]


def speech_rate(text: str, speaking_sec: float, lang: str) -> Optional[dict]:
    """Characters/s for CER languages, words/s otherwise, over non-silent time."""
    norm = normalize_text(text)
    if not norm or speaking_sec <= 0:
        return None
    if lang in CER_LANGS:
        count, unit = len(norm.replace(" ", "")), "chars/s"
    else:
        count, unit = len(norm.split()), "words/s"
    return {"value": round(count / speaking_sec, 2), "unit": unit}


def run_full_evaluation(original_video_path: str, dubbed_video_path: str, ground_truth_text: str,
                        target_lang: str = "ko", whisper_model_name: str = DEFAULT_WHISPER_MODEL,
                        perso_translation: Optional[str] = None,
                        on_step: Optional[Callable[[str, float], None]] = None) -> dict:
    """Runs the acoustic, speech-recognition and lip-sync evaluation. Returns results; does not write files.

    perso_translation: the script Perso translated and voiced (live runs). When given, the dub is also scored
    against it, which isolates voice clarity from wording differences with the user's target script.
    """
    def step(msg: str, frac: float):
        """Reports evaluation progress, if a callback was given."""
        if on_step:
            on_step(msg, frac)

    step("Loading the speech recognition model...", 0.02)
    model = get_whisper_model(whisper_model_name)

    step("Extracting audio from both videos...", 0.10)
    with tempfile.TemporaryDirectory(prefix="dubeval_") as tmp:
        y_orig = load_audio(extract_audio(original_video_path, os.path.join(tmp, "orig.wav")))
        y_dub = load_audio(extract_audio(dubbed_video_path, os.path.join(tmp, "dubbed.wav")))

    step("Measuring loudness and silence...", 0.15)
    orig_ac = analyze_acoustics(y_orig)
    dub_ac = analyze_acoustics(y_dub)

    step("Transcribing the original speech...", 0.20)
    orig_stt = transcribe(y_orig, model, language=None)
    step("Transcribing the dubbed speech...", 0.45)
    stt_lang = whisper_language(target_lang)
    dub_stt = transcribe(y_dub, model, language=stt_lang)
    scores = score_transcript(ground_truth_text, dub_stt["text"], target_lang)

    vs_perso = score_transcript(perso_translation, dub_stt["text"], target_lang) if perso_translation else None
    translation_vs_target = (score_transcript(ground_truth_text, perso_translation, target_lang)
                             if perso_translation and (ground_truth_text or "").strip() else None)

    step("Analyzing lip movement in the dubbed video...", 0.70)
    dub_ls = analyze_lipsync(dubbed_video_path, y_dub)
    step("Analyzing lip movement in the original video...", 0.85)
    orig_ls = analyze_lipsync(original_video_path, y_orig)

    orig_speaking = orig_ac["duration_sec"] * (1 - orig_ac["silence_ratio_pct"] / 100)
    dub_speaking = dub_ac["duration_sec"] * (1 - dub_ac["silence_ratio_pct"] / 100)
    source_lang = orig_stt["language"] or "en"
    step("Done", 1.0)

    return {
        "schema_version": 3,
        "metadata": {
            "original_video": original_video_path,
            "dubbed_video": dubbed_video_path,
            "target_language": target_lang,
            "detected_source_language": source_lang,
            "whisper_model": whisper_model_name
        },
        "acoustic_metrics": {
            "original_duration_sec": orig_ac["duration_sec"],
            "dubbed_duration_sec": dub_ac["duration_sec"],
            "duration_diff_sec": round(dub_ac["duration_sec"] - orig_ac["duration_sec"], 2),
            "original_speaking_sec": round(orig_speaking, 2),
            "dubbed_speaking_sec": round(dub_speaking, 2),
            "original_rms": orig_ac["mean_rms_energy"],
            "dubbed_rms": dub_ac["mean_rms_energy"],
            "rms_ratio": round(dub_ac["mean_rms_energy"] / orig_ac["mean_rms_energy"], 4) if orig_ac["mean_rms_energy"] > 1e-6 else None,
            "original_volume_stability_pct": orig_ac["volume_stability_pct"],
            "dubbed_volume_stability_pct": dub_ac["volume_stability_pct"],
            "original_silence_ratio": round(orig_ac["silence_ratio_pct"] / 100.0, 4),
            "dubbed_silence_ratio": round(dub_ac["silence_ratio_pct"] / 100.0, 4),
            "silence_diff": round((dub_ac["silence_ratio_pct"] - orig_ac["silence_ratio_pct"]) / 100.0, 4),
            "loudness_envelope": {
                "step_sec": 0.25,
                "original_db": loudness_envelope(y_orig),
                "dubbed_db": loudness_envelope(y_dub)
            }
        },
        "speech_recognition": {
            **scores,
            "ground_truth": (ground_truth_text or "").strip(),
            "dubbed_transcript": dub_stt["text"],
            "original_transcript": orig_stt["text"],
            "perso_translation": perso_translation,
            "vs_perso_script": vs_perso,
            "perso_translation_vs_target": translation_vs_target,
            "original_speech_rate": speech_rate(orig_stt["text"], orig_speaking, source_lang),
            "dubbed_speech_rate": speech_rate(dub_stt["text"], dub_speaking, target_lang)
        },
        "lipsync_metrics": {
            "valid": dub_ls["valid"],
            "reason": dub_ls["reason"],
            "pearson_correlation": dub_ls["pearson_correlation"],
            "best_lag_correlation": dub_ls["best_lag_correlation"],
            "best_lag_ms": dub_ls["best_lag_ms"],
            "sync_quality": dub_ls["sync_quality"],
            "face_coverage_pct": dub_ls["face_coverage_pct"],
            "original_valid": orig_ls["valid"],
            "original_pearson": orig_ls["pearson_correlation"],
            "original_sync_quality": orig_ls["sync_quality"],
            "original_face_coverage_pct": orig_ls["face_coverage_pct"],
            "waveform_data": {
                "timestamps": dub_ls["timestamps"],
                "mar_norm": dub_ls["mar_waveform"],
                "rms_norm": dub_ls["rms_waveform"]
            }
        },
        "warnings": ([] if stt_lang else [
            f"Speech recognition (Whisper) doesn't support the target language ({target_lang}), so it guessed "
            "the language. Treat the script scores as rough."]) + _quality_warnings(orig_ac, dub_ac, scores, dub_ls, dub_stt["text"])
    }
