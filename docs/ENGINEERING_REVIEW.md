# Engineering Review

_Initial review 2026-09-25. Updated 2026-09-29: the tool evaluates a dub from its Perso share link. Updated 2026-10-01: compare mode._

## Current state
- **Input:** a Perso share link, pasted in the app or passed to `python qa.py "<link>"`. The public shared-project endpoint gives the original and the dub (the lip-synced one when present). No Perso account, API key or credits.
- **Measures:** length, loudness, silence, clipping, speaking pace, dub language, voice clarity (Whisper confidence), speech timing alignment (word-timing overlap and mismatch spots), video integrity, experimental lip movement, and script accuracy when a script is passed to the CLI.
- **Translation check (automatic):** Gemini (or Claude) compares both timestamped transcripts for meaning, missing or added content, names and numbers, and mistranslations. Issues the model flags as probable speech-recognition errors are listed but don't change levels. Without a key it's reported as not measured; it never fails the run.
- **Report:** a verdict (Good / Needs review / Poor) with a one-line summary, six sections where every measure has a level, a plain explanation and the thresholds used, timestamped things to check (▶ jumps both videos there in the app), and a not-measured list with reasons. Saved as `report.html` (standalone, shareable), `report.json` and `report.txt` in every run folder.

## Compare mode (2026-10-01)
- `python qa.py compare <A> <B>` and a **Compare two dubs** tab evaluate two dubs with the full pipeline and recommend one with a deterministic, printed rule (verdict → Poor items → Check items → problem seconds → meaning score → speech timing; tie → A). Both Poor → the better one, a "not ready" warning and what to fix first. A missing translation check skips its rule and the comparison says so.
- **Problem intervals** (`src/intervals.py`): every issue as a merged, clipped, rounded time range with category, severity, the check that found it and a description; probable recognition errors kept apart. New measurements: clipping locations and a per-window language check of the dub (catches the original voice left in).
- **Language-agnostic pace:** Korean, English and Spanish rules (plus Japanese/Chinese); other languages are not measured, with the reason.
- **Robustness:** downloads and Whisper results cached per link (rerun of a 30 s pair: 9.4 s → 0.5 s), `--out` (default `./output`), `--original`, `--no-cache`, pathlib + UTF-8 everywhere, UTF-8 console, Windows-safe video paths for OpenCV/MediaPipe, exit codes 0/1/2.
- **Verified:** two real EN→ES Perso dubs of one 60 s clip (gallery links) compared end to end in 53 s with Gemini: Dub B recommended (Needs review) over Dub A (Poor: 49% speech timing, a mistranslated countdown). That run led to accepting gallery links, a stricter rule for non-source languages (noise was guessed as Nynorsk) and better line matching for translation issues. Also: fast suite offline; real Whisper end to end through fake share links (identical dubs tie → A with no intervals; an English "dub" labelled Korean is flagged as the original voice left in); the app's compare flow in a browser in English and Korean against a local fake Perso. **Not verified:** a real Windows machine (covered by design and a unit test of the path fallback).

## Simplified (2026-09-29)
The dubbing path was removed: the Perso account client (upload, dubbing, lip-sync requests, polling, credits, languages), demo mode, the sidebar account panel, `src/languages.py`, the vendored Perso CLI skills (`.agents/`), the demo dub and its script. `src/perso_api.py` went from ~450 to ~130 lines. The sample clip moved to `tests/data/sample.mp4` as test media. Results schema 5 drops the dubbing-only keys.

## Fixed (cumulative)
| Area | Fix |
|---|---|
| Security | The hardcoded live API key was removed, and process-wide TLS bypass was removed. ⚠️ **Rotate the old Perso key**, because it sat in plaintext. The tool no longer needs any Perso key. |
| Correctness | CER for CJK, text normalization, lip-sync `valid` flag and zero-lag score, wrong-language detection, Whisper "silence" segments dropped before timing and clarity. |
| Reporting | Verdict and thresholds live in `src/report.py`, not in the UI, so the saved output explains itself. `None` means not measured and is shown with a reason. |
| Robustness | Link parsed before any network call; retries with backoff; atomic downloads (`.part`) and results; uuid run folders with pruning; HTML output escaped; native library logs kept out of the CLI output. |
| Quality | Pinned deps, `.env.example`, ~220 tests: fake share endpoint, report rules, timing math, translation check with a fake client, CLI exit codes, Streamlit `AppTest` for setup, preview, progress and results, plus slow end-to-end runs with real Whisper. Tests never call Perso or Claude. |

## Verification performed
- `pytest`: all pass.
- **Real share link, end to end** (read-only, no credits): a Perso EN→KO lip-sync project (28.7 s). CLI and app both produced the report in ~45 s: Good, 81% speech overlap with two short dub-only spots, Korean detected at 99%, 100% clarity, identical length and loudness, 1920×1080 @ 60 fps preserved.
- **Gemini translation check, live** on the same project: `gemini-3.5-flash` scored the dub 4/5 in ≈ 3 s and flagged "이나데아크" and "고맙나요" as probable recognition errors. Gemini returned 503 ("high demand") on one early attempt, which is why the judge retries and falls back to a second model.
- **Not verified live:** the Claude path (no Anthropic key on the development machine); covered by tests with a fake client.

## Open items
1. **Replace the lip-sync heuristic** with SyncNet (LSE-C/LSE-D). On the sample, the in-sync original scores r = −0.20. See METRICS.md §3.
2. **Calibrate the new bands on more dubs.** Speech-timing (75/55%) and speaking-pace bands come from one real sample plus rules of thumb.
3. **Naturalness and voice similarity:** a MOS predictor (e.g. UTMOS) and speaker-embedding similarity (e.g. ECAPA) between the original voice and the cloned dub voice.
4. **Background preservation:** separate vocals from music/effects (e.g. Demucs) and compare the backgrounds.
5. **Compare the lip-synced and plain dubs** of one project automatically (compare mode compares two links today; the share response includes both files).
8. **Calibrate interval thresholds** (long silence 2/4 s, loudness jump 10/16 dB, wrong-language: original's 50/80%, other 80/95%) on more dubs, and run the compare suite on a real Windows machine.
6. **Multi-speaker videos:** diarization so the report can check each speaker.
7. **Whisper `medium`** for reporting-grade transcripts, and GPU/MPS support.
