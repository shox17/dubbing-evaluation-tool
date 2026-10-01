# Architecture

## Flow

```
qa.py → src/cli.py ─────────────┐   (qa.py compare <A> <B> → run_comparison)
app.py (Streamlit)              │
 ├─ setup view: tabs "Check one dub" (one link) / "Compare two dubs" (links A and B), live previews
 │    Evaluate ──► jobs.start_job(run_share_evaluation | run_comparison, params) ──► ?job=<id> in the URL
 ├─ progress view: @st.fragment(run_every=2 s) reads Job (stage, %) ── done ──► results / comparison view
 ├─ results view: build_report(results) → verdict, sections, things to check, details
 └─ comparison view: build_comparison(results A, results B) → recommendation, intervals, reasoning, table
                                │
pipeline.evaluate_share(share_url)                       (one dub; run_share_evaluation adds report files)
 parse_share_url → GET /projects/shared/{seq}                                 stage: fetch
 download original (or --original) + (lipSyncFileUrl | translatedFileUrl)
   into data/cache/<link hash>/, reused on reruns                             stage: download
 evaluate.run_full_evaluation(original, dub, target_lang, source_lang,
   cache=JsonCache(whisper_cache.json))                                       stage: evaluate
 check_translation → (run_share_evaluation) build_report → report.* in --out or runs/<id>/ + results.json

pipeline.run_comparison(url_a, url_b, out_dir)           stages: dub_a, dub_b, compare
 evaluate_share(A), evaluate_share(B) → compare.build_comparison → comparison.* + report_A.* + report_B.*
```

## Modules

### `src/perso_api.py`
Share links only; no API key, no account (https://developers.perso.ai/llms.txt).
- `parse_share_url` takes the `seq=` token from `https://perso.ai/<lang>/share/video-translator?seq=…` (or a bare token), and raises `ValueError` with a plain message for anything else, before any network call.
- `get_shared_project` calls the public `GET /video-translator/api/v1/projects/shared/{token}`. It returns title, `durationMs`, `sourceLanguage` / `targetLanguage`, and `originalFileUrl`, `translatedFileUrl`, `lipSyncFileUrl`, `isLipSync`. VT4035 becomes "sharing is turned off"; an unknown link or a project without a finished dub also get plain messages. 429 and 5xx are retried with backoff.
- A project without `originalFileUrl` is accepted here; the pipeline then needs `--original` (else a plain error).
- `download_media` streams a relative `/perso-storage/…` path from `https://portal-media.perso.ai` (URL-encoded) with retries and an atomic `.part` rename.

### `src/pipeline.py`
- `evaluate_share` parses the link, reads the project, downloads the original and the dub (the lip-synced video when `isLipSync`) into the link's cache folder `data/cache/<sha1(token)[:16]>/` (files named after a hash of their Perso path, so a re-rendered dub is downloaded again), and evaluates with the project's source and target languages. Whisper results go to `whisper_cache.json` in the same folder. `use_cache=False` (`--no-cache`) empties the folder first. The newest `MAX_CACHED_LINKS` link folders are kept. Lip movement is measured only when the evaluated video is lip-synced (`include_lipsync=None` = automatic; `--no-lipsync` forces it off). `original` (a file or URL) is used when the link has no original. It checks the stop signal between steps, then runs `check_translation` (any failure is a not-measured result).
- `run_share_evaluation` = `evaluate_share` + `build_report` + `save_report_files` (`report.json` = report + results, `report.html`, `report.txt`) into `out_dir` (the CLI's `--out`) or a new `data/output/runs/<run-id>/` (newest `MAX_KEPT_RUNS` kept), then `results.json`.
- `run_comparison` evaluates both links, calls `build_comparison`, and `save_comparison_files` writes `comparison.txt` / `.json` (without the embedded reports) / `.html` and `report_A.*` / `report_B.*`. Progress is mapped onto the stages `dub_a`, `dub_b`, `compare`.
- HTML reports refer to the cached videos by relative path (a `file://` URI when they are on another Windows drive).

### `src/evaluate.py`
Pure: no file writes (only temp audio) and no side effects on import. `run_full_evaluation` reports sub-steps through `on_step`, takes `include_lipsync` (skip the slow experimental step), `source_lang`, and an optional dict-like `cache` for Whisper results (transcripts, language detection, language windows) keyed by model, language and media file; the Whisper model is loaded only on a cache miss. On Windows, OpenCV gets an ASCII path (`_cv2_path`) and MediaPipe gets its model as bytes, because both fail on non-ASCII paths. It returns audio measures, both transcripts with Whisper segments, the dub's detected language, clarity, speech intervals and their alignment, clipping, a technical comparison of both files, and lip movement. See [METRICS.md](METRICS.md).

### `src/translation_judge.py`
One LLM review of both timestamped transcripts: a 1–5 meaning score, a summary, and issues typed `missing / added / mistranslation / name_or_number` with severity, time, exact quotes and `may_be_recognition_error`.
- **Provider:** Gemini when `GEMINI_API_KEY` (or `GOOGLE_API_KEY`) is set, else Claude when `ANTHROPIC_API_KEY` is available (`judge_provider()`).
- **Gemini:** REST `generateContent` with the key in the `x-goog-api-key` header, `responseJsonSchema` for structured output, temperature 0, `thinkingLevel` low. 429/5xx are retried twice with backoff, then the next model in `GEMINI_MODELS` is tried (`gemini-3.5-flash` → `gemini-flash-latest` → `gemini-3.8-flash` → `gemini-3.1-flash-lite`); 404 skips to the next model. Google's "high demand" 503s are frequent and per model, hence the chain.
- **Claude:** `claude-opus-5-5` with structured output and server-side refusal fallback.
- Any failure (no key, rejected key, overload, refusal, unreadable output) returns a not-measured result with the reason; it never fails the run. Tests replace it with a stub (`tests/conftest.py`) and remove all provider keys from the environment.

### `src/report.py` / `src/report_text.py`
Pure. `build_report(results, lang)` builds the whole report in the interface language (`en`, `ko`, `pt`, `es`); every sentence comes from `src/report_text.py` (keys `r.*`), and the judge's summary and explanations are picked from its four-language output. The app rebuilds the report on each render, so switching language switches the report. It returns `{project, overall{level,label,headline,counts}, sections[{id,title,metrics[{id,label,level,value,unit,display,message,thresholds}],note}], things_to_check[{start,end,category,severity,message}], not_measured[], method}`. All thresholds are constants at the top of the file and are printed in every row. `render_text` and `render_html` present the same report; the HTML is self-contained (light/dark) and embeds the videos by relative path when saved in the run folder.

### `src/intervals.py`
Pure. `build_intervals(results, tr, lang)` turns speech-timing mismatches (long silence ≥ 2 s or timing mismatch), clipping locations, loudness jumps (from the loudness envelope), per-window wrong language, unclear speech and translation issues into `{start, end, dub, category, category_label, severity, check, check_label, description, merged}` ranges, merges same-category ranges closer than 0.5 s, clips to the dub's length, rounds to 0.1 s and sorts. Probable recognition errors are returned separately. `total_seconds` is the union length. See [METRICS.md](METRICS.md) §7.

### `src/compare.py`
Pure. `facts(report, results)` → verdict, Poor/Check counts, problem seconds, meaning score, overlap. `decide(a, b)` applies `RULES` in order and returns the winner, the rule, the values at it and the skipped rules (missing values); a full tie → A. `build_comparison(results_a, results_b, lang)` returns `{recommendation{dub, tie, both_poor, ready, headline, warning, fix_first[]}, intervals{A,B}, possible_asr_errors{A,B}, problem_seconds{A,B}, reasoning{rule, rule_label, values{A,B}, deciding_factor, summary[], skipped_rules[], translation_used, translation_note}, facts, decision, table[], links{A,B}, notes[], meta{tool_version, generated, run_seconds}, labels, badges, reports{A,B}}`, every text in the chosen language (keys `c.*` in `report_text.py`). `render_comparison_text` (Korean-aware column widths) and `render_comparison_html` put the three decision sections first.

### `src/cli.py` / `qa.py`
`python qa.py "<share link>" [--out DIR] [--lang ko|en|es|pt] [--original FILE_OR_URL] [--script/--script-file] [--no-lipsync] [--no-translation-check] [--no-cache] [--whisper-model] [--json] [--fail-on never|poor|check] [--verbose]` and `python qa.py compare <A> <B>` with the same options (no script / fail-on). `--out` defaults to `./output` and is created if missing; `--lang` defaults to `ko`. stdout/stderr are switched to UTF-8. Progress on stderr, report on stdout; MediaPipe's native logs are silenced unless `--verbose`. Exit codes: single 0 done / 1 verdict failed `--fail-on`; compare 0 recommended dub Good or Needs review / 1 both Poor; both 2 input or runtime error.

### `src/jobs.py`
- `start_job(runner, params, stages)` runs `runner(report, cancel_event)` in a daemon thread. Jobs live in a process-wide registry, so a page reload (`?job=<id>`) reattaches to them. `Cancelled` marks a stopped job.
- `Job.overall_fraction` weights stages by typical duration (fetch 0.2, download 1, evaluate 6; compare: dub_a 7, dub_b 7, compare 0.2). `stage_state()` drives the done / active / pending / failed checklist.
- **Limitation:** the registry is in memory; restarting the app server loses tracking of a running evaluation.

### `src/i18n.py`
- `TEXT` holds every interface string in `en`, `ko`, `pt` (Brazil) and `es`, plus every report and comparison sentence from `report_text.py` (`r.*`, `c.*`). `app.py` reads it through `t(key, **values)` with the language picked in the sidebar (default: the browser locale).
- `MESSAGES` translates the fixed progress messages from `src/`.
- `tests/test_i18n.py` checks that every key has all four languages with the same `{placeholders}`.

### `app.py`
- The router picks the view: a running job shows progress, a finished job shows results, a failed or stopped job shows an error, otherwise the setup form.
- `shared_project()` (cached 5 min) feeds the live preview under the link box.
- The results page always rebuilds the report from the results, so it reflects the current report rules.

## `results.json` (schema_version 6)
- `metadata`: videos, `target_language`, `detected_source_language`, `whisper_model`.
- `acoustic_metrics`: durations, speaking time, RMS and ratio, volume stability, silence, `original_peak_dbfs`, `dubbed_peak_dbfs`, `dubbed_clipping_pct`, `dubbed_clipping_intervals[[start, end]]`, `loudness_envelope {step_sec, original_db[], dubbed_db[]}`.
- `speech_recognition`: script scores (`wer`, `cer`, `primary_metric`, `error_rate`, `accuracy_pct`; `null` unless the CLI got `--script`), `ground_truth`, both transcripts, both speech rates, `dubbed_language_detected`, `dubbed_language_probability`, `dubbed_language_windows[{start, end, language, probability, expected_probability}]`, `clarity {confident_pct, mean_logprob, segments, unclear_segments[]}`, `original_segments[]`, `dubbed_segments[]`.
- `timing_alignment`: `overlap_pct`, `original_covered_pct`, `dub_in_original_pct`, `start_offset_sec`, `end_offset_sec`, `mismatches[{start, end, kind}]`, `original_speech[]`, `dubbed_speech[]`.
- `video_integrity`: `original` / `dubbed` `{readable, width, height, fps, frames, duration_sec, has_audio}`, `same_resolution`, `same_fps`.
- `lipsync_metrics`: `measured`, `valid`, `reason`, zero-lag and best-lag correlation, face coverage, the original's values, waveforms.
- `translation_judge`: `{measured, reason, model, meaning_score, summary, issues[]}`.
- `report`: the output of `build_report`, including `problem_intervals[]`, `possible_asr_errors[]` and `problem_seconds`.
- `pipeline`: `run_id`, `execution_mode`, local video paths, target language name/code/id, `share {share_url, seq, title, source_language_name, source_language_code, target_language_name, is_lipsync, evaluated_video, duration_ms, created, original_from}`, `timestamp`, `report_files`.

Version 6 turned `warnings` into `{key, params, text}` objects, added `reason_key` / `reason_params` to lip-sync and translation-check results, and made the judge's `summary` and issue `explanation` `{en, ko, pt, es}` objects. Version 5 removed the dubbing-only keys (`perso_translation`, `vs_perso_script`, `perso_translation_vs_target`, `pipeline.perso`, `lip_dubbing_enabled`). When you rename or remove keys, bump `SCHEMA_VERSION` in `evaluate.py` and `RESULTS_SCHEMA_VERSION` in `app.py` (the app asserts they match).

## Configuration
| Variable | Default | Purpose |
|---|---|---|
| `GEMINI_API_KEY` | none | Turns on the translation check with Gemini (preferred) |
| `GEMINI_MODEL` | `gemini-3.5-flash` | First Gemini model tried (`gemini-flash-latest` is the fallback) |
| `GEMINI_THINKING` | `low` | Gemini thinking level: `low` ≈ 3 s per review, `high` ≈ 40 s |
| `ANTHROPIC_API_KEY` | none | Translation check with Claude, when no Gemini key is set |
| `CLAUDE_JUDGE_MODEL` | `claude-opus-5-5` | Claude model for the translation check |
| `WHISPER_MODEL` | `base` | Speech model (145 MB, fast on CPU). The app has no setting for it; the CLI accepts `--whisper-model` |
| `MAX_KEPT_RUNS` | `10` | App run folders kept |
| `MAX_CACHED_LINKS` | `20` | Share links whose downloads and Whisper results stay cached |
| `PERSO_API_BASE` / `PERSO_MEDIA_BASE` | `https://api.perso.ai` / `https://portal-media.perso.ai` | Endpoints |
