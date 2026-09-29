# AGENTS.md

Guidance for AI coding agents (Codex, Claude Code and others) working in this repository. `CLAUDE.md` imports
this file, so keep everything here.

## What this is
**Dubbing QA Studio**: a Streamlit app and a CLI (`qa.py`) that evaluate a Perso AI dub from its **share link**
and write a quality report.

1. The share link's public endpoint (no key, no account, no credits) gives the original video and the dub.
2. The tool downloads both (the lip-synced dub when there is one), then measures them: length, loudness, silence,
   distortion, speaking pace, dub language, voice clarity (Whisper), speech timing, video file, lip movement
   (experimental, lip-synced dubs only), and script accuracy when a script is passed to the CLI.
3. Gemini (or Claude) checks the translation automatically when a key is set.
4. `src/report.py` turns everything into a report: a verdict (Good / Needs review / Poor), every measure with a
   level, a plain explanation and how it's graded, and timestamped **things to check**. Saved as `report.html`,
   `report.json` and `report.txt`, in English, Korean, Portuguese or Spanish.

Deeper docs: `README.md` (use), `docs/ARCHITECTURE.md` (modules, results schema), `docs/METRICS.md` (how each
measure works and its bands), `docs/ENGINEERING_REVIEW.md` (state, verification, open items).

## Commands
```bash
source eval_env/bin/activate                                   # Windows: eval_env\Scripts\activate
python qa.py "https://perso.ai/en/share/video-translator?seq=…"  # report in the terminal (+ files in data/output/runs/<id>/)
python qa.py "<link>" --lang ko                                # report in Korean (en | ko | pt | es)
python qa.py "<link>" --json                                   # machine-readable report
streamlit run app.py                                           # app at http://localhost:8501
pytest -m "not slow"                                           # ~6 s, offline. Run after every change
pytest                                                         # ~20 s, adds real Whisper runs on tests/data/sample.mp4
```
Other CLI options: `--no-lipsync`, `--no-translation-check`, `--whisper-model small`, `--script "…"` /
`--script-file f.txt`, `--fail-on poor|check` (exit 1), `--verbose` (show MediaPipe logs). Exit codes: 0 done,
1 verdict failed `--fail-on`, 2 couldn't evaluate.

## Setting up a new machine
```bash
python3 -m venv eval_env && source eval_env/bin/activate
pip install -r requirements-dev.txt        # pinned for Python 3.14 (macOS arm64)
printf 'GEMINI_API_KEY=%s\n' "<key>" > .env  # optional: turns on the translation check
pytest -m "not slow"
```
- If `pip install` fails on another Python version, install unpinned:
  `pip install streamlit openai-whisper librosa jiwer mediapipe numpy pandas imageio-ffmpeg python-dotenv requests anthropic pytest`.
- The first evaluation downloads the Whisper `base` model (~145 MB) to `~/.cache/whisper`. Run one evaluation
  before a demo so the download is done.
- `.env` is git-ignored; a fresh clone has none. Without a key everything works except the translation check,
  which the report shows as "not measured" with the reason.
- The real share link, Perso and Gemini need network access. The fast tests are fully offline.

## Project map
```
qa.py                    CLI entry point → src/cli.py
app.py                   Streamlit UI: paste link (live preview) → progress → report. Only rendering; no logic.
src/perso_api.py         Share links: parse_share_url, get_shared_project (public GET), download_media
src/pipeline.py          run_share_evaluation: fetch → download → evaluate → translation check → report files
src/evaluate.py          All measurements (pure). run_full_evaluation returns the results dict (SCHEMA_VERSION)
src/translation_judge.py Translation check: Gemini first (REST, retries + model fallback), else Claude
src/report.py            build_report(results, lang): levels, verdict, things to check; render_text / render_html (pure)
src/report_text.py       Every report sentence in en/ko/pt/es (keys r.*), merged into i18n.TEXT
src/i18n.py              UI text (TEXT), fixed progress/error messages (MESSAGES), t(), translate_message()
src/jobs.py              Background job thread + Progress model (stages fetch/download/evaluate, stop, reattach)
src/cli.py               Argument parsing, quiet native logs, exit codes
src/face_landmarker.task MediaPipe face model (lip movement)
tests/fake_perso.py      Fake share endpoint + media host, with a real response shape
tests/sample_results.py  A realistic results dict (make_results) for report/CLI/UI tests
tests/data/sample.mp4    28.7 s English talking-head clip used as fake share media in slow tests
data/output/             Run folders and results.json, created at run time (git-ignored)
```

## Rules
- **Scope is share-link evaluation.** The tool only uses Perso's public share endpoint
  (`GET https://api.perso.ai/video-translator/api/v1/projects/shared/{seq}`) and the media host
  (`https://portal-media.perso.ai`, paths URL-encoded). Don't add Perso account features (dubbing, credits, API
  keys). Reference: https://developers.perso.ai/llms.txt.
- **Secrets:** never print, log, commit or read the values of `GEMINI_API_KEY` / `ANTHROPIC_API_KEY`; they live
  in the git-ignored `.env`. Send the Gemini key only in the `x-goog-api-key` header, never in a URL.
- **Tests never call real services.** Perso: `tests/fake_perso.py`. Gemini/Claude: `tests/conftest.py` removes
  provider keys from the environment and stubs the pipeline's translation check; judge tests use fake sessions
  and clients. Keep it that way.
- **Never fail a run because of the translation check:** any problem becomes a not-measured result whose reason
  is a text key (`not_measured("r.judge.…")`).
- `src/evaluate.py` and `src/report.py` stay pure (no file writes except temp audio, no network, no import side
  effects). Streamlit stays out of `src/`.
- **Levels, thresholds and messages live only in `src/report.py`** (thresholds are constants at its top). The UI
  and CLI render the report; they never re-derive levels. Every Good/Check/Poor row states how it's graded.
- Verdict rule: any Poor → Poor; otherwise any Check → Needs review; otherwise Good. Info and not-measured rows
  never count. Issues the judge flags `may_be_recognition_error` are listed but never lower a level.
- The pipeline reports progress only through `Progress` objects; the background thread must never call `st.*`.
- Lip movement is measured automatically only when the dub is lip-synced, is always informational and never
  changes the verdict. Don't present its number as reliable (METRICS.md §3).
- The app has no options or settings: lip movement and the translation check are automatic, the Whisper model
  is fixed (`base`, overridable by `WHISPER_MODEL` or the CLI), script accuracy is CLI-only.
- If you rename or remove result keys, bump `SCHEMA_VERSION` (`src/evaluate.py`) and `RESULTS_SCHEMA_VERSION`
  (`app.py`); the app asserts they match.

## Conventions
- Plain functions returning dicts. Type hints, one-line docstrings, comments only where the why isn't obvious.
  Use `logging`, never `print` (except the CLI's own output). Match the surrounding style.
- User-facing failures raise `PersoError`, `ValueError` or `FileNotFoundError` with an actionable, plain-language
  message; add the exact English text to `i18n.MESSAGES` so the UI can translate it.
- `None` means "not measured". Never use sentinel numbers.
- **Everything a person reads follows the interface language.** UI text → `src/i18n.py` `TEXT`; report sentences
  → `src/report_text.py`; fixed progress/error messages → `i18n.MESSAGES`. Every string needs `en`, `ko`, `pt`,
  `es` with identical `{placeholders}` (`tests/test_i18n.py` enforces it). Counted texts use `_one` / `_many`
  keys. Never hard-code UI text in `app.py` or sentences in `report.py`.
- In Korean, don't put a particle (이/가/을/를/은/는) right after a `{placeholder}`; rephrase instead.
- Explanations say what was measured, what it means for a viewer, and what to do. No file references
  (METRICS.md) and no jargon (IoU, r, CER, dBFS) in anything the user reads.
- UI copy is short, plain, second person ("Paste a Perso share link").

## How to do common tasks
- **Add a measure:** compute it in `src/evaluate.py` (pure) and add it to the `run_full_evaluation` result →
  grade it in the right section function of `src/report.py` with `_metric(tr, "<id>", level, message, value,
  display, graded)` → add `r.m.<id>`, its messages and its `r.g.<id>` grading sentence to `src/report_text.py`
  in all four languages → add a test in `tests/test_report.py` (use `make_results(...)`) → update
  `docs/METRICS.md`. New result keys need no schema bump; renames/removals do.
- **Change a threshold:** edit the constant at the top of `src/report.py`; the grading sentences read it. Update
  the bands in `docs/METRICS.md` and `README.md`.
- **Add a thing to check:** append an item `{start, end, category, severity, message}` in `_things_to_check`
  (`src/report.py`), with its text in `src/report_text.py`.
- **Change the translation check:** prompt and JSON schema are `SYSTEM_PROMPT` / `RESULT_SCHEMA` in
  `src/translation_judge.py`. Summary and explanations must stay four-language objects. Gemini models are tried
  in `GEMINI_MODELS` order; `GEMINI_MODEL` / `GEMINI_THINKING` env vars override the first model and thinking.
- **Add UI text:** add the key to `TEXT` in `src/i18n.py` in all four languages and use `t("key")` in `app.py`.
- **Inspect a share link by hand:**
  `curl -s "https://api.perso.ai/video-translator/api/v1/projects/shared/<seq>" | python3 -m json.tool`
  (public; returns title, languages, `originalFileUrl`, `translatedFileUrl`, `lipSyncFileUrl`, `isLipSync`).

## Definition of done
1. `pytest -m "not slow"` passes (and `pytest` before committing).
2. New user-facing text exists in en/ko/pt/es.
3. Docs match the change (`README.md`, `docs/*.md`, this file).
4. `git status` shows no `.env`, videos or `data/` files.
5. Commit only when the user asks.

## Known limits
- Lip movement is a heuristic (the in-sync original of the sample scores −0.20); a SyncNet-style model would
  replace it.
- The translation check reads Whisper transcripts, not audio, so misheard words can look like translation errors
  (they're flagged as probable recognition errors).
- Speech-timing and pace bands are calibrated on one real Perso EN→KO dub (81–82% overlap, 5.8 chars/s).
- Google's Gemini API often returns 503 "high demand"; the judge retries and falls back across four Flash models,
  then reports "busy, try again in a minute".
- The job registry is in memory; restarting the app during a run loses tracking.
