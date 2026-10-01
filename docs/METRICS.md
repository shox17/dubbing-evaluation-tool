# Evaluation Metrics

This page explains how each score is produced (`src/evaluate.py`), how to read it, and where it breaks down.
Reference numbers ("Sample") come from a real Perso EN→KO lip-sync dub of a 28.7 s talking-head clip, Whisper `small`. The default model is now `base`, which gave the same verdict and scores on this sample (82% vs 81% speech overlap, 4/5 meaning) with a 3× smaller download.

## 1. Acoustics (`analyze_acoustics`)

Audio is decoded to 16 kHz mono with the bundled ffmpeg.

| Field | Definition | Read as | Sample |
|---|---|---|---|
| `duration_diff_sec` | dubbed − original | ≈ 0 for a time-aligned dub. Beyond ±20%, a warning is raised because the pair probably doesn't match | 0.00 |
| `rms_ratio` | mean RMS dub ÷ original | ≈ 1.0 means matched loudness. `null` if the original is silent | 1.00 |
| `*_volume_stability_pct` | `(1 − std/mean RMS)·100` | Higher is steadier. Useful as a comparison, not as an absolute | 60 → 63 |
| `*_silence_ratio` | 1 − non-silent time ÷ duration (`top_db=20`, relative to the clip's peak) | Music beds hide silence | 0.1% → 0.6% |

## 2. Script accuracy (`score_transcript`, only when you give a script)

Share links don't include a script, so this is scored only when you pass one on the command line (`--script` / `--script-file`). It isn't listed as "not measured" otherwise: it's an optional extra, not a gap.

1. Whisper transcribes the dub with `language=target` (`whisper_language` maps Perso's `fil` → `tl` and `jv` → `jw`). For Cebuano, Chichewa, Irish and Kyrgyz Whisper has no model, so it auto-detects and the run warns that the script scores are rough. The original is transcribed in the share project's source language, or with auto-detection when that is unknown (`detected_source_language`).
2. Both reference and hypothesis are normalized: NFKC, lowercase, punctuation and symbols removed, whitespace collapsed.
3. `wer` is word-level. `cer` is character-level with spaces removed, so spacing differences are not errors.
4. **Primary metric:** `cer` for `ko`, `ja`, `zh`, `th`, and `wer` otherwise. `error_rate` and `accuracy_pct = max(0, 1 − error_rate)·100` come from it.
5. An empty ground truth gives `null` scores. An empty transcript gives error 1.0.

**Why CER for Korean and Japanese:** Japanese has no spaces, so WER treats a whole sentence as a single "word". Korean spacing units are coarse and ASR spacing is inconsistent. For example, `소프트웨어 공학을` vs `소프트웨어공학을` is a 100% word error but a 0% character error.

**Reading it:** on a Korean dub of the sample, a correct dub scored about 60% (CER ≈ 0.4) against an independently written Korean script. That is **not** a 40% dubbing failure. The number mixes three things:
- **Paraphrase:** the dub's translation is valid but worded differently from your script (for example, `공부하고` vs `전공하고`).
- **ASR error:** Whisper mishears proper nouns (`인하대학교` → `이나데아크`).
- **Real dubbing errors.**

The highlighted diff under **What was said** shows which is which. For meaning rather than wording, use the translation check (§5). The default speech model is `base` (fast, 145 MB). It mishears a few more words than `small`, which mostly shows up as extra "possible recognition error" items; for reporting-grade transcripts set `WHISPER_MODEL=small` or `medium`.

### Speech rate
Words per second (chars/s for ko/ja/zh/th) over *speaking time*, where speaking time is duration × (1 − silence ratio). Units differ between languages, so compare the dub against other dubs in the same language, not against the original.

### Loudness over time
The dBFS of each 0.25 s window, for both tracks. Peaks and gaps should line up. A shifted or stretched pattern shows timing drift that the single duration number hides.

## Score bands (audio and script)
| Measure | ✓ Good | ! Check | ✗ Poor |
|---|---|---|---|
| Length match: \|Δduration\| / original | ≤ 5% | ≤ 15% | above that |
| Matches your script: accuracy | ≥ 80% | ≥ 50% | below |
| Loudness match: dub vs original | within ±2 dB | within ±4 dB | beyond |
| Extra silence in the dub | ≤ 5 pts | ≤ 15 pts | above |
| Lip movement | always informational ||| 

The script-free measures and their bands are in §4 and §5. The script bands are lenient on purpose, because paraphrases count as errors (§2).

## 3. Lip-sync (`analyze_lipsync`), experimental

Measured automatically when the shared dub is lip-synced (`isLipSync`); skipped otherwise, and the report says why.

1. Frames are sampled at about 15 fps (sequential decode) over the first 60 s. MediaPipe runs in VIDEO mode.
2. Per frame, the Mouth Aspect Ratio is `|lm13 − lm14| / |lm61 − lm291|`. Frames without a face are excluded rather than filled in.
3. Speech RMS is computed on a 10 ms grid and interpolated at each frame's timestamp, so it doesn't drift.
4. **Score:** the Pearson r at zero lag (`pearson_correlation`).
5. Diagnostic: the best r within ±200 ms (`best_lag_correlation`, `best_lag_ms`). Taking a maximum over 21 lags turns pure noise into r ≈ +0.1, so this is **never** used as the score.
6. The result is `valid: false` with a `reason` if there are fewer than 20 frames, faces appear in fewer than 50% of frames, or the mouth never moves.

`sync_quality` bands: `strong` ≥ 0.4 · `moderate` ≥ 0.2 · `weak` ≥ 0.05 · `none` below that.

### Known limitation: this heuristic does not work on the sample video
| Video | r (zero lag) | Face coverage |
|---|---|---|
| Original, which is in sync by definition | **−0.20** | 56% |
| Perso Korean lip-sync dub | −0.03 | 56% |

The original should score clearly positive, and it doesn't. The causes, found by investigation:
- **Voice-over B-roll.** The speaker is on screen but not talking (typing, walking) while narration plays. Those frames anti-correlate mouth opening with loudness.
- **Weak signal even on the talking-head part.** On the first 5.5 s (99% face coverage), every variant tried gave |r| < 0.2 and random best lags: inner vs. outer lips, face-height normalization, speech-band (300–3400 Hz) energy, and smoothing.

**Treat the lip movement row as informational.** Compare it only against `original_pearson` on the same video, never as an absolute. The proper replacement is a SyncNet-style audio-visual model (the LSE-C / LSE-D metrics), which is tracked in ENGINEERING_REVIEW.md.

## 4. Script-free measures
Share links carry no script, so these measure the dub against the original directly.

### Dub language (`detect_language`)
Whisper's language identification on the first 30 s of the dub. **Good** when it matches the target and Whisper is ≥ 50% sure, **Check** when it matches but Whisper is unsure, **Poor** when it's a different language. Catches the worst failure (wrong language, or the original voice left in).

### Voice clarity (`speech_clarity`)
Share of speech time in Whisper segments with `avg_logprob ≥ −1.0` (Whisper's own threshold for trusting a decode). Segments Whisper itself treats as silence (`no_speech_prob > 0.6` and `avg_logprob < −1.0`) are ignored. Good ≥ 90%, Check ≥ 70%. The unclear segments are listed with timestamps under *Things to check*. It's an intelligibility proxy that needs no script; ASR weaknesses on names and accents also lower it.

### Speech timing (`speech_intervals`, `timing_alignment`)
1. Speech stretches come from Whisper word timings, merging gaps shorter than 0.3 s and dropping segments Whisper treats as silence. Word timings follow speech, not the music bed, which defeats energy-based voice detection on this kind of video.
2. Both tracks go on a 50 ms grid. `overlap_pct` is intersection over union of speaking time. Stretches of ≥ 0.5 s where only one track speaks become `mismatches` (`dub_only` / `original_only`, the 8 longest).
3. Bands: Good ≥ 75%, Check ≥ 55%. **Calibration:** the real Perso EN→KO lip-sync dub of the sample scores **81%**, with two short dub-only spots. Languages differ in rhythm, so 100% isn't expected; these bands are a starting point from one sample and should be tuned on more dubs.
4. It depends on correct transcription: a dub in the wrong language gets distorted word timings (the language check flags that case separately).

### Distortion (`clipping_pct`)
Share of dub samples at |x| ≥ 0.999. Good ≤ 0.01%, Check ≤ 0.1%.

### Speaking pace bands
The dub language comes from the share link's metadata (base code, so `es-MX` uses the `es` rule). Chars/s for Korean (Good ≤ 7.5, Check ≤ 9), Japanese (≤ 8.5, ≤ 10.5), Chinese (≤ 6, ≤ 7.5); words/s for English (≤ 3.2, ≤ 3.8) and Spanish (≤ 3.5, ≤ 4.2). Any other language has no rule: the row is **not measured**, with the reason and the measured pace, and never counts toward the verdict. Rules of thumb for "the translation is too long for the time slot"; the sample dub runs at 5.8 chars/s.

### Video integrity (`video_integrity`)
Resolution, frame rate, frame count and audio stream of both files (OpenCV + ffmpeg stream list). Poor if the dub can't be read or has no audio, Check if resolution or frame rate changed.

## 5. Translation check (`translation_judge.py`, automatic when a key is set)
Gemini (`gemini-3.5-flash`, low thinking, ≈ 3 s) or Claude reads both timestamped transcripts and returns a meaning score (1–5), a summary, and issues typed missing / added / mistranslation / name-or-number, each with severity, time, exact quotes and a `may_be_recognition_error` flag. Bands: meaning Good ≥ 4, Check = 3; completeness, names/numbers and mistranslations are Good with no issues, Check with minor ones only, Poor with any major one.

It sees transcripts, not audio, so a Whisper mishearing can look like a translation error. The model flags those, and **flagged issues don't change a level**: they are shown as "(+N?)" and listed under *Things to check* to confirm by ear. On the sample, Gemini scored the dub 4/5 and correctly flagged "이나데아크" (for 인하대) and "고맙나요" (for 또 만나요) as probable recognition errors. Without a key it's reported as not measured, with the reason.

## 6. The report and the verdict (`report.py`)
Every measure gets a level (good / check / poor / info / not measured), a one-sentence explanation and the thresholds used. **Verdict:** any Poor → Poor; otherwise any Check → Needs review; otherwise Good. Info (lip movement, speech offsets) and not-measured items never change it, and the report lists why each unmeasured item wasn't measured. There's deliberately no single 0–100 score: weights between these measures would be arbitrary and hard to defend.

## 7. Problem intervals (`intervals.py`)
Every issue becomes a time range `{start, end, dub, category, severity (poor/check), check, description}`, in `report.problem_intervals`. Things to check are built from the same list.

| Category | Found by | Severity |
|---|---|---|
| `long_silence` | speech timing: original speaks, dub silent for ≥ 2 s | Poor from 4 s, else Check |
| `timing_mismatch` | speech timing: shorter one-track-only stretches (≥ 0.5 s) | Check |
| `missing_speech` / `added_speech` | translation check | Poor if major, else Check |
| `mistranslation`, `names_numbers` | translation check | Poor if major, else Check |
| `distortion` | clipped samples (`dubbed_clipping_intervals`, merged within 0.5 s) | Poor if the clipping row is Poor, else Check |
| `loudness_jump` | loudness envelope: dub vs original level, after removing their overall offset, differs by ≥ 10 dB for ≥ 1 s where both tracks have sound | Poor from 16 dB, else Check |
| `wrong_language` | Whisper language detection per 10 s window of the dub (`dubbed_language_windows`; windows widen so at most 60 are checked): another language at ≥ 50% while the expected one is < 20%. If it is the original's language, the description says the original voice may have been left in | Poor from 80%, else Check |
| `unclear_speech` | voice clarity: segments Whisper recognised with low confidence | Check |

Rules: ranges of the same category that overlap or are less than 0.5 s apart merge (worst severity kept, `merged` counts them); ranges are clipped to the dub's length, rounded to 0.1 s and sorted by start. A translation issue lasts until the end of the original transcript line containing it (2 s if none). Issues the judge flags as probable speech-recognition errors go to `report.possible_asr_errors` and never count. `report.problem_seconds` is the time covered by at least one interval (overlaps count once). Intervals don't change the verdict, which comes from the measure levels; compare mode uses `problem_seconds` as a tie-breaker.

## Sanity warnings (`warnings` in results)
Raised automatically when:
- the duration differs by more than 20% (probably not a matching pair),
- the dub transcript is empty,
- the primary error rate is above 0.8 (probably the wrong script or language),
- lip movement couldn't be measured on the dub (the reason is included).

Each warning also appears under *Things to check* in the report.
