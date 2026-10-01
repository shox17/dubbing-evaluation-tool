# AGENTS.md

Guidance for AI coding agents (Codex, Claude Code and others) working in this repository. `CLAUDE.md` imports
this file, so keep everything here.

## What this is
**Dubbing QA Studio**: a Streamlit app and a CLI (`qa.py`) that evaluate a Perso AI dub from its **share link**
and write a quality report, or (**compare mode**) evaluate two dubs of the same video and recommend which one to
deliver, with the reason.

1. The share link's public endpoint (no key, no account, no credits) gives the original video and the dub.
2. The tool downloads both (the lip-synced dub when there is one), then measures them: length, loudness, silence,
   distortion, speaking pace, dub language, voice clarity (Whisper), voice quality (DNSMOS), voice similarity (speaker model), speech timing, video file, lip movement
   (experimental, lip-synced dubs only), and script accuracy when a script is passed to the CLI.
3. Gemini (or Claude) checks the translation automatically when a key is set.
4. `src/report.py` turns everything into a report: a verdict (Good / Needs review / Poor), every measure with a
   level, a plain explanation and how it's graded, and every issue as a **problem interval** (`src/intervals.py`).
   Saved as `report.html`, `report.json` and `report.txt`, in English, Korean, Portuguese or Spanish.
5. Compare mode (`src/compare.py`) runs steps 1–4 for 2 to 8 links (A, B, C, ...), ranks them with the decision rule
   (better verdict → fewer Poor → fewer Check → less problem time → higher meaning score → higher speech timing;
   still tied → input order) and writes `comparison.txt/.json/.html` (recommended version, problem intervals,
   reasoning first) plus `report_A.*`, `report_B.*`, ...

Deeper docs: `README.md` (use), `docs/ARCHITECTURE.md` (modules, results schema), `docs/METRICS.md` (how each
measure works and its bands), `docs/ENGINEERING_REVIEW.md` (state, verification, open items).

## Commands
```bash
source eval_env/bin/activate                                   # Windows: eval_env\Scripts\activate
python qa.py "https://perso.ai/en/share/video-translator?seq=…"  # report (Korean by default) + report.* in ./output
python qa.py "<link>" --out ./output --lang en                 # another folder / language (ko | en | es | pt)
python qa.py compare "<link A>" "<link B>" [<C> ...] --out ./output  # rank 2-8 dubs, recommend one
python qa.py batch links.txt --out ./output/batch                # many links → summary.csv (+ agreement with your labels)
python qa.py history --days 30                                    # every past evaluation: totals, pairs, trends
python qa.py feedback                                             # reviewer votes: which checks raise false alarms
python qa.py "<link>" --json                                   # machine-readable report
streamlit run app.py                                           # app at http://localhost:8501
pytest -m "not slow"                                           # ~6 s, offline. Run after every change
pytest                                                         # ~20 s, adds real Whisper runs (need tests/data/sample.mp4)
```
Other CLI options (both modes): `--original <file or URL>` (link without an original), `--no-cache`, `--no-lipsync`,
`--no-translation-check`, `--whisper-model small`, `--verbose` (show MediaPipe logs). Single mode only: `--script "…"`
/ `--script-file f.txt`, `--fail-on poor|check`. Exit codes: 0 done (compare: recommended dub is Good or Needs
review), 1 single: verdict failed `--fail-on` / compare: every dub Poor, 2 input or runtime error (batch: any link
failed; the summary is still written).

## Setting up a new machine
```bash
python3 -m venv eval_env && source eval_env/bin/activate
pip install -r requirements-dev.txt        # pinned for Python 3.14 (macOS arm64)
printf 'GEMINI_API_KEY=%s\n' "<key>" > .env  # optional: turns on the translation check
pytest -m "not slow"
```
- If `pip install` fails on another Python version, install unpinned:
  `pip install streamlit openai-whisper librosa jiwer mediapipe numpy pandas imageio-ffmpeg python-dotenv requests onnxruntime anthropic pytest`.
- The first evaluation downloads the Whisper `base` model (~145 MB) to `~/.cache/whisper`. Run one evaluation
  before a demo so the download is done.
- `.env` is git-ignored; a fresh clone has none. Without a key everything works except the translation check,
  which the report shows as "not measured" with the reason.
- The real share link, Perso and Gemini need network access. The fast tests are fully offline.

## Project map
```
qa.py                    CLI entry point → src/cli.py
app.py                   Streamlit UI: tabs "Check one dub" / "Compare two dubs" → progress → report or comparison.
                         Only rendering; no logic.
src/perso_api.py         Share links: parse_share_url, get_shared_project (public GET), download_media
src/pipeline.py          evaluate_share (fetch → cached download → evaluate → translation check), run_share_evaluation
                         (+ report files), run_comparison (two links → comparison files); per-link cache in data/cache/
src/evaluate.py          All measurements (pure). run_full_evaluation returns the results dict (SCHEMA_VERSION)
src/translation_judge.py Translation check: Gemini first (REST, retries + model fallback), else Claude
src/report.py            build_report(results, lang): levels, verdict, intervals, things to check; renderers (pure)
src/intervals.py         Problem intervals: collect from every check, merge (< 0.5 s), clip, round 0.1 s, sort (pure)
src/compare.py           Compare mode: facts, decide (the rule), build_comparison, text/HTML renderers (pure)
src/batch.py             Batch mode: parse links file (+ person's verdicts), summary rows, agreement, CSV/text (pure)
src/voice_quality.py     Voice quality: DNSMOS P.835 on both tracks at the same moments, where both speak (ONNX)
src/speaker.py           Voice similarity: WeSpeaker ONNX (downloaded once, SHA-256 pinned), numpy Kaldi fbank
src/feedback.py          Reviewer votes (real problem / false alarm) per interval; per-check summary
src/history.py           Records every evaluation to data/history.jsonl; summarize() and the history text view
src/version.py           TOOL_VERSION, printed in comparison footers
src/report_text.py       Every report sentence in en/ko/pt/es (keys r.*), merged into i18n.TEXT
src/i18n.py              UI text (TEXT), fixed progress/error messages (MESSAGES), t(), translate_message()
src/jobs.py              Background job thread + Progress model (stages fetch/download/evaluate, stop, reattach)
src/cli.py               Argument parsing, quiet native logs, exit codes
src/models/              Bundled models with their licenses (README.md there): MediaPipe face landmarker (lip
                         movement), DNSMOS P.835 ONNX (voice quality)
tests/fake_perso.py      Fake share endpoint + media host, with a real response shape
tests/sample_results.py  A realistic results dict (make_results) for report/CLI/UI tests
tests/data/sample.mp4    Local only (git-ignored): any ~30 s English talking-head MP4; the 2 slow tests skip without it
data/output/             App run folders and results.json, created at run time (git-ignored)
data/cache/              Per share link: downloaded videos + whisper_cache.json (git-ignored)
output/                  The CLI's default --out folder (git-ignored)
data/history.jsonl       Evaluation history, one JSON line per evaluated dub (git-ignored)
data/feedback.jsonl      Reviewer votes on problem intervals (git-ignored)
```

## Rules
- **Scope is share-link evaluation.** The tool only uses Perso's public share endpoint
  (`GET https://api.perso.ai/video-translator/api/v1/projects/shared/{seq}`) and the media host
  (`https://portal-media.perso.ai`, paths URL-encoded). Don't add Perso account features (dubbing, credits, API
  keys). Reference: https://developers.perso.ai/llms.txt.
- **Secrets:** never print, log, commit or read the values of `GEMINI_API_KEY` / `ANTHROPIC_API_KEY`; they live
  in the git-ignored `.env`. Send the Gemini key only in the `x-goog-api-key` header, never in a URL.
- **History recording never fails a run** (errors are logged); tests write history and votes to temp files
  (`tests/conftest.py`).
- **Calibrate with evidence:** reviewer votes (`qa.py feedback`) and batch labels (`qa.py batch`) are how thresholds
  should change; a check marked "flags too much" is the first candidate.
- **Tests never call real services.** Perso: `tests/fake_perso.py`. Gemini/Claude: `tests/conftest.py` removes
  provider keys from the environment and stubs the pipeline's translation check; judge tests use fake sessions
  and clients. Keep it that way.
- **Never fail a run because of the translation check:** any problem becomes a not-measured result whose reason
  is a text key (`not_measured("r.judge.…")`).
- `src/evaluate.py` and `src/report.py` stay pure (no file writes except temp audio, no network, no import side
  effects). Streamlit stays out of `src/`.
- **Levels, thresholds and messages live only in `src/report.py`** (thresholds are constants at its top), interval
  thresholds in `src/intervals.py`, and the compare decision rule only in `src/compare.py` (`RULES`). The UI and
  CLI render reports and comparisons; they never re-derive levels or decisions. Every Good/Check/Poor row states
  how it's graded.
- **The decision rule is deterministic and printed:** rule order, "skip a rule when any dub lacks its value", ties
  keep input order, the reasoning compares #1 with #2, and the all-Poor warning are part of the spec; change them only together with `c.rule.*` / `c.why.*` texts,
  `c.rules_order`, `tests/test_compare.py`, README and this file.
- **Any language pair:** the dub language comes from the share metadata (base code: `es-MX` → `es`). A language
  without a pace rule (`SPEECH_RATE`) or without a Whisper model is "not measured" with the reason, never graded
  silently and never a crash.
- **Cross-platform (Windows, macOS, Linux):** pathlib for paths, `encoding="utf-8"` on every text file, no shell
  commands (ffmpeg comes from `imageio-ffmpeg` and runs as an argument list), OpenCV paths through `_cv2_path`.
- Verdict rule: any Poor → Poor; otherwise any Check → Needs review; otherwise Good. Info and not-measured rows
  never count. Issues the judge flags `may_be_recognition_error` are listed but never lower a level.
- The pipeline reports progress only through `Progress` objects; the background thread must never call `st.*`.
- **Voice quality compares the dub with the original at the same moments**, never in absolute terms: DNSMOS scores
  fall with background music, which both tracks share. It was chosen after UTMOS failed on real dubs (every real
  recording scored ~1.2-1.5, even after voice separation); don't swap in a studio-speech model without testing it on
  real Perso dubs. Window bands are in `src/intervals.py` (`VOICE_SIG_DROP`, `VOICE_OVRL_DROP`).
- **Voice similarity is only measured on lines with a clean original background** (DNSMOS background ≥ 3.0):
  music blurs voice fingerprints (on a real film even one actor's own lines scored < 0.45). It's Good or Check, never
  Poor (a new voice can be deliberate). Line-level "different voice" intervals are relative to the dub's own median.
  The model downloads on first use to `~/.cache/dubbing-qa/` (`DUBBING_QA_MODELS` overrides); tests never download
  (`tests/conftest.py`).
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
- **Calibrate thresholds:** run `qa.py batch` on labelled links (`link,good|check|poor`), read the agreement and
  `summary.csv` (every measure's level and value), change the constant, rerun (cached: seconds, no API calls).
- **Change a threshold:** edit the constant at the top of `src/report.py` (or `src/intervals.py` for intervals);
  the grading sentences read it. Update the bands in `docs/METRICS.md` and `README.md`.
- **Add a pace rule for a language:** add `"<code>": (good, check)` to `SPEECH_RATE` in `src/report.py` (chars/s for
  ko/ja/zh/th, words/s otherwise), a test in `tests/test_report.py`, and the band in README/METRICS.
- **Add an interval category:** add the id → `r.cat.*` label to `CATEGORIES` in `src/intervals.py`, a collector that
  returns `_item(...)` ranges, its texts in `src/report_text.py` (4 languages), a test in `tests/test_intervals.py`,
  and a row in METRICS.md §7.
- **Things to check** are built from the problem intervals (+ untimed warnings) in `_things_to_check`
  (`src/report.py`); add new timed issues as interval categories instead.
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
4. `git status` shows no `.env`, videos, `data/`, `output/` or `tests/data/` files. Never commit videos: git keeps them in
   history forever and every clone downloads them.
5. Commit only when the user asks.

## Known limits
- Lip movement is a heuristic (the in-sync original of the sample scores −0.20); a SyncNet-style model would
  replace it.
- The translation check reads Whisper transcripts, not audio, so misheard words can look like translation errors
  (they're flagged as probable recognition errors).
- Speech-timing and pace bands are calibrated on one real Perso EN→KO dub (81–82% overlap, 5.8 chars/s).
- Google's Gemini API often returns 503 "high demand"; the judge retries and falls back across four Flash models,
  then reports "busy, try again in a minute".
- Whisper is seeded inside `transcribe` so results are repeatable; keep it that way (bump `CACHE_VERSION` in
  `src/evaluate.py` when cached Whisper results would change).
- The job registry is in memory; restarting the app during a run loses tracking.
- Voice similarity is not measured on music-heavy videos (by design); its bands come from synthetic voices (same voice
  0.80-0.87 across languages, different voices median 0.13, max 0.57) and need real cloned dubs to confirm.
- Voice quality misses a muffled (low-passed) voice, and its bands were set from damage simulated on two real dubs
  (clean dubs: at most 0.25 below the original; robotic/distorted stretches: 0.4-2.3 below).
- Interval thresholds (long silence 2/4 s, loudness jump 10/16 dB, wrong language: original's 50/80%, other 80/95%) are first guesses checked on
  the sample only. The per-window language check needs ~3 s of speech per 10 s window.
- Compare mode was verified with fake share links (real Whisper), in the browser, and on two real EN→ES Perso dubs of
  one video; not yet on a real Windows machine.
