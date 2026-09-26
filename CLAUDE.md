# CLAUDE.md

Guidance for AI coding agents working in this repository.

## What this is
A Streamlit app that dubs a video with the Perso AI REST API, waits for dubbing and lip-sync to finish in a background job, then compares the dub with the original: timing, loudness, silence, speech rate, Whisper CER/WER against the user's script and Perso's script, and experimental lip-sync. Read `README.md`, then `docs/ARCHITECTURE.md`, `docs/METRICS.md`, and `docs/ENGINEERING_REVIEW.md`.

## Commands
```bash
source eval_env/bin/activate
streamlit run app.py
pytest -m "not slow"     # ~6 s. Run after every change
pytest                   # ~1 min, includes real Whisper/MediaPipe runs
```

## Rules
- **Perso API reference:** https://developers.perso.ai/llms.txt. Poll no faster than every 5 s. Lip-sync is a separate project, created after dubbing completes. Media paths resolve against `https://portal-media.perso.ai` and must be URL-encoded.
- **Never start a real Perso dubbing job without the user's explicit OK.** It spends credits. Read-only calls (spaces, plan/status, media/quota) are fine. Tests must use `tests/fake_perso.py` and never the real API.
- **Never print, log, or read the API key.** It comes from `PERSO_API_KEY` or `~/.perso/credentials`.
- `src/evaluate.py` stays pure (no file writes, no import side effects). Streamlit stays out of `src/`.
- The pipeline reports progress only through `Progress` objects (`src/jobs.py`). The background thread must never call `st.*`.
- Demo mode is valid only for `sample_original.mp4` + Korean. The guard lives in both `app.py` and `pipeline.py`.
- The target script box starts empty. Don't prefill it; the demo's "Paste the sample's Korean script" button is the only shortcut.
- If you rename or remove result keys, bump `schema_version` (`evaluate.py`) and `RESULTS_SCHEMA_VERSION` (`app.py`).
- Don't present the lip-sync number as reliable (METRICS.md §3). `.agents/` is vendored, so don't edit it.

## Conventions
- Plain functions returning dicts. Type hints, one-line docstrings. Use `logging`, never `print`.
- User-facing failures raise `PersoError`, `ValueError`, or `FileNotFoundError` with an actionable, plain-language message.
- UI copy is short, plain language, and second person ("Paste the script the dub should say"). Explain every number in a caption.
- All UI text lives in `src/i18n.py` in English, Korean, Portuguese and Spanish; add every new string in all four (`tests/test_i18n.py` enforces it). Never hard-code UI text in `app.py`.
- `None` means "not measured". Never use sentinel numbers.
