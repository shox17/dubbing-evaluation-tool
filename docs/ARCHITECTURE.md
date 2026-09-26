# Architecture

## Flow

```
app.py (Streamlit)
 ├─ setup view ── Start ──► jobs.start_job(run_pipeline, params) ──► ?job=<id> in the URL
 ├─ progress view: @st.fragment(run_every=2 s) reads Job (stage, %, ETA) ── done ──► results view
 └─ results view: reads the results dict (also saved to data/output/results.json)

jobs.Job (background thread)
 └─ pipeline.run_pipeline(report=job.report, cancel_event=job.cancel_event)
     ├─ demo: data/output/sample_dubbed_ko.mp4                                    stage: evaluate
     └─ live (perso_api.PersoClient):
         validate media → SAS upload → register (mediaSeq)                       stage: upload
         PUT queue → POST translate → poll /progress every 5 s                    stage: dubbing
         POST lip-sync (separate project) → poll /progress                        stage: lipsync
           └ on failure: keep the dub and add a warning (same policy as Perso's CLI)
         download-info → download (lipSyncVideo | dubbingVideo) → GET /script     stage: download
     evaluate.run_full_evaluation(..., perso_translation, on_step)               stage: evaluate
     save_results (atomic)
```

## Modules

### `src/perso_api.py`
Implements the documented REST flow (https://developers.perso.ai/llms.txt).
- **Auth:** the `XP-API-KEY` header. The key comes from `PERSO_API_KEY`, then `XP_API_KEY`, then `~/.perso/credentials` (written by the Perso CLI).
- **Account:** `list_spaces` (filtered to `serviceType == video_translator`), `default_space` (with `PERSO_SPACE_SEQ` pin, else the owned default), `plan_status`, `remaining_credits`, `estimate_credits` (`/media/quota`).
- **Media:** `validate_media` checks limits before uploading. `upload_video` gets a SAS token, PUTs to the blob, then registers with the query string stripped.
- **Languages:** `list_languages` reads `GET /languages` and returns target entries (see `src/languages.py`).
- **Projects:** `request_dubbing` (initialises the queue once per space, uses `targetLanguages` with `AUDIO_ENGINE_V3` plus `languageTag` for regional variants such as `en-GB`, `withLipSync: false`), `request_lipsync`, `get_status` (normalises `progressReason`, progress, ETA, and failure message), `wait_for` (5 s polling with cancel and timeout), `cancel`, `get_script`, `download_video` (checks `download-info`, URL-encodes the media path, retries).
- **Errors:** `PersoError` messages are safe to show users. Known codes (VT4021 credits, VT4044 unknown language, VT5034 queue full, F400x media limits, 401/403/429) map to plain-language hints. 429 and 5xx responses are retried with backoff.

### `src/jobs.py`
- `start_job(runner, params, stages)` runs `runner(report, cancel_event)` in a daemon thread. Jobs live in a process-wide registry, so a page reload (`?job=<id>`) reattaches to them.
- `Job.overall_fraction` weights stages by typical duration (upload 1, dubbing 4, lip-sync 6, download 1, evaluate 2). `stage_state()` drives the done / active / pending / failed checklist on the progress page.
- **Limitation:** the registry is in memory. If the app server restarts, tracking is lost, but the Perso project keeps running and stays in the workspace.

### `src/pipeline.py`
- `run_pipeline` validates the input, extension (`.mp4/.mov/.webm`) and demo pairing, then runs the flow above. The target language (an id like `ko` or `en-GB`, a code, or a name) is resolved against Perso's live list on live runs, after the extension check, so a bad file makes no API calls.

### `src/i18n.py`
- `TEXT` holds every interface string in `en`, `ko`, `pt` (Brazil) and `es`, keyed by a short id. `app.py` reads it through `t(key, **values)`, which uses the language picked in the sidebar (`st.session_state.ui_lang`, defaulting to the browser locale).
- `MESSAGES` translates the fixed English progress messages from `src/` (Perso steps, pipeline and evaluation steps) by their text. Dynamic messages, errors and result warnings stay in English.
- `tests/test_i18n.py` checks that every key has all four languages with the same `{placeholders}`.

### `src/languages.py`
- One entry per selectable language: `{id, code, tag, name, experimental}`. `id` is the regional tag (`en-GB`, `pt-PT`, `es-ES`) or, for a code's default row, the code itself.
- `FALLBACK_LANGUAGES` is a snapshot of the Language API (77 targets, 2026-09-26). The app uses it when Perso can't be reached (demo, no key, tests). Regenerate it if Perso adds languages.
- `resolve_language` matches by id, name, code or name without region ("English" → English (US)).
- `probe_video` returns duration, size and resolution for validation and cost estimates.
- `pipeline_stages(demo, lipsync)` gives the stages the UI shows.
- Paths are anchored at the project root. Live dubs go to `data/output/runs/<run-id>/`, and the newest `MAX_KEPT_RUNS` are kept.

### `src/evaluate.py`
This module is pure: it writes no files and has no side effects on import. `run_full_evaluation` reports sub-steps through `on_step`. See [METRICS.md](METRICS.md).

### `app.py`
- The router picks the view: a running job shows progress, a finished job shows results, a failed or cancelled job shows an error, and otherwise the setup form appears.
- `perso_account()` (cached 60 s) and `credit_estimate()` (cached 5 min) feed the sidebar and the cost line.
- Form widget values are re-assigned to session state on every run, so they survive while the form is hidden.

## `results.json` (schema_version 3)
The fields match version 2, plus:
- `acoustic_metrics`: `original_speaking_sec`, `dubbed_speaking_sec`, and `loudness_envelope {step_sec, original_db[], dubbed_db[]}`.
- `speech_recognition`: `perso_translation`, `vs_perso_script` (score object), `perso_translation_vs_target` (score object), and `original_speech_rate` / `dubbed_speech_rate` (`{value, unit}`). Scores are `null` when no script was entered.
- `lipsync_metrics`: `original_face_coverage_pct`.
- `pipeline.perso`: `{space_seq, media_seq, dubbing_project, lipsync_project}`.

When you rename or remove keys, bump `schema_version` in `evaluate.py` and `RESULTS_SCHEMA_VERSION` in `app.py`.

## Configuration
| Variable | Default | Purpose |
|---|---|---|
| `PERSO_API_KEY` | CLI key file | API key |
| `PERSO_SPACE_SEQ` | owned default | Default workspace |
| `PERSO_API_BASE` / `PERSO_MEDIA_BASE` | `https://api.perso.ai` / `https://portal-media.perso.ai` | Endpoints |
| `WHISPER_MODEL` | `small` | Default speech model (can be changed in the sidebar) |
| `MAX_KEPT_RUNS` | `10` | Downloaded runs kept |
