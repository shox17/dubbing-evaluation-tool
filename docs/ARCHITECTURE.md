# Architecture

## Flow

```
qa.py → src/cli.py ─────────────┐
app.py (Streamlit)              │
 ├─ setup view: paste link, live project preview, options
 │    Evaluate ──► jobs.start_job(run_share_evaluation, params) ──► ?job=<id> in the URL
 ├─ progress view: @st.fragment(run_every=2 s) reads Job (stage, %) ── done ──► results view
 └─ results view: build_report(results) → verdict, sections, things to check, details
                                │
pipeline.run_share_evaluation(share_url)
 parse_share_url → GET /projects/shared/{seq}                                 stage: fetch
 download original + (lipSyncFileUrl | translatedFileUrl) into runs/<id>/     stage: download
 evaluate.run_full_evaluation(original, dub, target_lang, source_lang)        stage: evaluate
 finish_run: translation_judge → report.build_report → save_report_files + results.json
```

## Modules

### `src/perso_api.py`
Share links only; no API key, no account (https://developers.perso.ai/llms.txt).
- `parse_share_url` takes the `seq=` token from `https://perso.ai/<lang>/share/video-translator?seq=…` (or a bare token), and raises `ValueError` with a plain message for anything else, before any network call.
- `get_shared_project` calls the public `GET /video-translator/api/v1/projects/shared/{token}`. It returns title, `durationMs`, `sourceLanguage` / `targetLanguage`, and `originalFileUrl`, `translatedFileUrl`, `lipSyncFileUrl`, `isLipSync`. VT4035 becomes "sharing is turned off"; an unknown link or a project without a finished dub also get plain messages. 429 and 5xx are retried with backoff.
- `download_media` streams a relative `/perso-storage/…` path from `https://portal-media.perso.ai` (URL-encoded) with retries and an atomic `.part` rename.

### `src/pipeline.py`
- `run_share_evaluation` parses the link, reads the project, downloads the original and the dub into `data/output/runs/<run-id>/` (the lip-synced video when `isLipSync`), and evaluates with the project's source and target languages. Lip movement is measured only when the evaluated video is lip-synced (`include_lipsync=None` = automatic; the CLI's `--no-lipsync` forces it off). It checks the stop signal between steps.
- `finish_run`: the optional translation check, `build_report`, `save_report_files` (`report.json` = report + results, `report.html`, `report.txt`), then `results.json`. The newest `MAX_KEPT_RUNS` run folders are kept.

### `src/evaluate.py`
Pure: no file writes (only temp audio) and no side effects on import. `run_full_evaluation` reports sub-steps through `on_step`, takes `include_lipsync` (skip the slow experimental step) and `source_lang`. It returns audio measures, both transcripts with Whisper segments, the dub's detected language, clarity, speech intervals and their alignment, clipping, a technical comparison of both files, and lip movement. See [METRICS.md](METRICS.md).

### `src/translation_judge.py`
One LLM review of both timestamped transcripts: a 1–5 meaning score, a summary, and issues typed `missing / added / mistranslation / name_or_number` with severity, time, exact quotes and `may_be_recognition_error`.
- **Provider:** Gemini when `GEMINI_API_KEY` (or `GOOGLE_API_KEY`) is set, else Claude when `ANTHROPIC_API_KEY` is available (`judge_provider()`).
- **Gemini:** REST `generateContent` with the key in the `x-goog-api-key` header, `responseJsonSchema` for structured output, temperature 0, `thinkingLevel` low. 429/5xx are retried twice with backoff, then the next model in `GEMINI_MODELS` is tried (`gemini-3.5-flash` → `gemini-flash-latest` → `gemini-3.8-flash` → `gemini-3.1-flash-lite`); 404 skips to the next model. Google's "high demand" 503s are frequent and per model, hence the chain.
- **Claude:** `claude-opus-5-5` with structured output and server-side refusal fallback.
- Any failure (no key, rejected key, overload, refusal, unreadable output) returns a not-measured result with the reason; it never fails the run. Tests replace it with a stub (`tests/conftest.py`) and remove all provider keys from the environment.

### `src/report.py` / `src/report_text.py`
Pure. `build_report(results, lang)` builds the whole report in the interface language (`en`, `ko`, `pt`, `es`); every sentence comes from `src/report_text.py` (keys `r.*`), and the judge's summary and explanations are picked from its four-language output. The app rebuilds the report on each render, so switching language switches the report. It returns `{project, overall{level,label,headline,counts}, sections[{id,title,metrics[{id,label,level,value,unit,display,message,thresholds}],note}], things_to_check[{start,end,category,severity,message}], not_measured[], method}`. All thresholds are constants at the top of the file and are printed in every row. `render_text` and `render_html` present the same report; the HTML is self-contained (light/dark) and embeds the videos by relative path when saved in the run folder.

### `src/cli.py` / `qa.py`
`python qa.py "<share link>" [--script/--script-file] [--no-lipsync] [--no-translation-check] [--whisper-model] [--json] [--fail-on never|poor|check] [--verbose]`. Progress on stderr, report on stdout; MediaPipe's native logs are silenced unless `--verbose`. Exit 0 done, 1 verdict failed `--fail-on`, 2 could not evaluate.

### `src/jobs.py`
- `start_job(runner, params, stages)` runs `runner(report, cancel_event)` in a daemon thread. Jobs live in a process-wide registry, so a page reload (`?job=<id>`) reattaches to them. `Cancelled` marks a stopped job.
- `Job.overall_fraction` weights stages by typical duration (fetch 0.2, download 1, evaluate 6). `stage_state()` drives the done / active / pending / failed checklist.
- **Limitation:** the registry is in memory; restarting the app server loses tracking of a running evaluation.

### `src/i18n.py`
- `TEXT` holds every interface string in `en`, `ko`, `pt` (Brazil) and `es`. `app.py` reads it through `t(key, **values)` with the language picked in the sidebar (default: the browser locale). Report section titles and metric labels are translated (`rsec.*`, `rmetric.*`); report messages stay in English.
- `MESSAGES` translates the fixed progress messages from `src/`.
- `tests/test_i18n.py` checks that every key has all four languages with the same `{placeholders}`.

### `app.py`
- The router picks the view: a running job shows progress, a finished job shows results, a failed or stopped job shows an error, otherwise the setup form.
- `shared_project()` (cached 5 min) feeds the live preview under the link box.
- The results page always rebuilds the report from the results, so it reflects the current report rules.

## `results.json` (schema_version 6)
- `metadata`: videos, `target_language`, `detected_source_language`, `whisper_model`.
- `acoustic_metrics`: durations, speaking time, RMS and ratio, volume stability, silence, `original_peak_dbfs`, `dubbed_peak_dbfs`, `dubbed_clipping_pct`, `loudness_envelope {step_sec, original_db[], dubbed_db[]}`.
- `speech_recognition`: script scores (`wer`, `cer`, `primary_metric`, `error_rate`, `accuracy_pct`; `null` unless the CLI got `--script`), `ground_truth`, both transcripts, both speech rates, `dubbed_language_detected`, `dubbed_language_probability`, `clarity {confident_pct, mean_logprob, segments, unclear_segments[]}`, `original_segments[]`, `dubbed_segments[]`.
- `timing_alignment`: `overlap_pct`, `original_covered_pct`, `dub_in_original_pct`, `start_offset_sec`, `end_offset_sec`, `mismatches[{start, end, kind}]`, `original_speech[]`, `dubbed_speech[]`.
- `video_integrity`: `original` / `dubbed` `{readable, width, height, fps, frames, duration_sec, has_audio}`, `same_resolution`, `same_fps`.
- `lipsync_metrics`: `measured`, `valid`, `reason`, zero-lag and best-lag correlation, face coverage, the original's values, waveforms.
- `translation_judge`: `{measured, reason, model, meaning_score, summary, issues[]}`.
- `report`: the output of `build_report`.
- `pipeline`: `run_id`, `execution_mode`, local video paths, target language name/code/id, `share {share_url, seq, title, source_language_name, source_language_code, target_language_name, is_lipsync, evaluated_video, duration_ms, created}`, `timestamp`, `report_files`.

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
| `MAX_KEPT_RUNS` | `10` | Run folders kept |
| `PERSO_API_BASE` / `PERSO_MEDIA_BASE` | `https://api.perso.ai` / `https://portal-media.perso.ai` | Endpoints |
