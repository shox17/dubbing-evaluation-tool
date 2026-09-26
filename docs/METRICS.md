# Evaluation Metrics

This page explains how each score is produced (`src/evaluate.py`), how to read it, and where it breaks down.
Reference numbers come from the demo pair: `sample_original.mp4` (English) → `sample_dubbed_ko.mp4` (Korean), Whisper `small`.

## 1. Acoustics (`analyze_acoustics`)

Audio is decoded to 16 kHz mono with the bundled ffmpeg.

| Field | Definition | Read as | Demo |
|---|---|---|---|
| `duration_diff_sec` | dubbed − original | ≈ 0 for a time-aligned dub. Beyond ±20%, a warning is raised because the pair probably doesn't match | 0.00 |
| `rms_ratio` | mean RMS dub ÷ original | ≈ 1.0 means matched loudness. `null` if the original is silent | 1.00 |
| `*_volume_stability_pct` | `(1 − std/mean RMS)·100` | Higher is steadier. Useful as a comparison, not as an absolute | 60 → 63 |
| `*_silence_ratio` | 1 − non-silent time ÷ duration (`top_db=20`, relative to the clip's peak) | Music beds hide silence | 0.1% → 1.0% |

## 2. Speech accuracy (`score_transcript`)

1. Whisper transcribes the dub with `language=target` (`whisper_language` maps Perso's `fil` → `tl` and `jv` → `jw`). For Cebuano, Chichewa, Irish and Kyrgyz Whisper has no model, so it auto-detects and the run warns that the script scores are rough. The original is transcribed with language auto-detection (`detected_source_language`).
2. Both reference and hypothesis are normalized: NFKC, lowercase, punctuation and symbols removed, whitespace collapsed.
3. `wer` is word-level. `cer` is character-level with spaces removed, so spacing differences are not errors.
4. **Primary metric:** `cer` for `ko`, `ja`, `zh`, `th`, and `wer` otherwise. `error_rate` and `accuracy_pct = max(0, 1 − error_rate)·100` come from it.
5. An empty ground truth gives `null` scores. An empty transcript gives error 1.0.

**Why CER for Korean and Japanese:** Japanese has no spaces, so WER treats a whole sentence as a single "word". Korean spacing units are coarse and ASR spacing is inconsistent. For example, `소프트웨어 공학을` vs `소프트웨어공학을` is a 100% word error but a 0% character error.

**Demo:** CER 0.395, WER 0.519. This is **not** a 40% dubbing failure. The number mixes three things:
- **Paraphrase:** Perso's translation is valid but worded differently from `data/ground_truth.txt` (for example, `공부하고` vs `전공하고`).
- **ASR error:** Whisper mishears proper nouns (`인하대학교` → `이나데아크`).
- **Real dubbing errors.**

For a dubbing-quality score, use Perso's own translated script as the ground truth. Then only ASR and pronunciation errors remain. Whisper `small` is noticeably better than `base` on Korean. Use `medium` for reporting (`WHISPER_MODEL=medium`).

### Voice clarity (live runs)
After dubbing, the app downloads the script Perso actually voiced (`GET …/script`, `translatedText`) and scores the Whisper transcript against it (`vs_perso_script`). Wording differences with your script drop out, so this isolates **how intelligible the synthetic voice is**, plus ASR error. `perso_translation_vs_target` compares Perso's translation with your script directly. It measures wording differences only and doesn't involve audio.

### Speech rate
Words per second (chars/s for ko/ja/zh/th) over *speaking time*, where speaking time is duration × (1 − silence ratio). Units differ between languages, so compare the dub against other dubs in the same language, not against the original.

### Loudness over time
The dBFS of each 0.25 s window, for both tracks. Peaks and gaps should line up. A shifted or stretched pattern shows timing drift that the single duration number hides.

## Score bands in the app
| Card | ✓ Good | ! Check | ✗ Poor |
|---|---|---|---|
| Timing match: \|Δduration\| / original | ≤ 5% | ≤ 15% | above that |
| Matches your script / Voice clarity: accuracy | ≥ 80% | ≥ 50% | below |
| Loudness match: dub vs original | within ±2 dB | within ±4 dB | beyond |
| Lip movement | always shown as *Experimental* ||| 

The script bands are lenient on purpose. On the demo, a correct Korean dub scores **60%** against `data/ground_truth.txt`, mostly because of wording differences and Whisper mishearing names. The highlighted diff under **What was said** shows which is which.

## 3. Lip-sync (`analyze_lipsync`), experimental

1. Frames are sampled at about 15 fps (sequential decode) over the first 60 s. MediaPipe runs in VIDEO mode.
2. Per frame, the Mouth Aspect Ratio is `|lm13 − lm14| / |lm61 − lm291|`. Frames without a face are excluded rather than filled in.
3. Speech RMS is computed on a 10 ms grid and interpolated at each frame's timestamp, so it doesn't drift.
4. **Score:** the Pearson r at zero lag (`pearson_correlation`).
5. Diagnostic: the best r within ±200 ms (`best_lag_correlation`, `best_lag_ms`). Taking a maximum over 21 lags turns pure noise into r ≈ +0.1, so this is **never** used as the score.
6. The result is `valid: false` with a `reason` if there are fewer than 20 frames, faces appear in fewer than 50% of frames, or the mouth never moves.

`sync_quality` bands: `strong` ≥ 0.4 · `moderate` ≥ 0.2 · `weak` ≥ 0.05 · `none` below that.

### Known limitation: this heuristic does not work on the demo video
| Video | r (zero lag) | Face coverage |
|---|---|---|
| Original, which is in sync by definition | **−0.20** | 56% |
| Korean dub | −0.05 | 56% |

The original should score clearly positive, and it doesn't. The causes, found by investigation:
- **Voice-over B-roll.** The speaker is on screen but not talking (typing, walking) while narration plays. Those frames anti-correlate mouth opening with loudness.
- **Weak signal even on the talking-head part.** On the first 5.5 s (99% face coverage), every variant tried gave |r| < 0.2 and random best lags: inner vs. outer lips, face-height normalization, speech-band (300–3400 Hz) energy, and smoothing.

**Treat the lip-sync card as informational.** Compare it only against `original_pearson` on the same video, never as an absolute. The proper replacement is a SyncNet-style audio-visual model (the LSE-C / LSE-D metrics), which is tracked in ENGINEERING_REVIEW.md.

## Sanity warnings (`warnings` in results)
Raised automatically when:
- the duration differs by more than 20% (probably not a matching pair),
- the dub transcript is empty,
- the primary error rate is above 0.8 (probably the wrong script or language),
- lip-sync is invalid on the dub (the reason is included),
- the worker reports that lip-sync failed and it saved the plain dub instead.
