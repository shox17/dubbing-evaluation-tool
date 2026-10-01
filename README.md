# Dubbing QA Studio

Automatic quality reports for videos dubbed with **[Perso AI](https://perso.ai)**.

Paste a **Perso share link**, and the tool downloads the original and the dub, measures both, and writes a report: an overall **verdict**, every measure marked **Good / Check / Poor** with a plain-language explanation and the thresholds it used, and a timestamped list of **things to check**. No Perso account, API key or credits are needed.

```bash
python qa.py "https://perso.ai/en/share/video-translator?seq=…"
```

| Section | What it checks | How |
|---|---|---|
| **Timing & audio** | Same length? Same loudness? Unusual gaps? Distortion? Rushed speech? | `librosa` on both tracks: duration, RMS loudness (dB), silence, clipping, chars/words per second |
| **Speech recognition** | Is the dub in the right language? Is the voice clear? | Whisper language detection, and the share of speech Whisper recognises confidently |
| **Timing alignment** | Does the dub speak when the original speaks? | Whisper word timings of both tracks → overlap of speech (IoU) and the places where only one track speaks |
| **Translation** *(automatic when a key is set)* | Same meaning? Anything missing or added? Names and numbers kept? | Gemini (or Claude) compares the two timestamped transcripts (needs `GEMINI_API_KEY` or `ANTHROPIC_API_KEY`) |
| **Video integrity** | Is the picture unchanged, with an audio track? | Resolution, frame rate and audio stream of both files |
| **Lip movement** *(experimental, lip-synced dubs only)* | Does the mouth move with the voice? | MediaPipe mouth opening vs loudness, compared with the original; measured automatically when the dub is lip-synced; never part of the verdict |
| **Script accuracy** *(CLI, when you pass a script)* | Is the script you expected heard in the dub? | Whisper transcript vs your script: CER for Korean, Japanese, Chinese and Thai, WER otherwise |

Every run saves `report.html` (a standalone page to share), `report.json` and `report.txt` in its run folder.

---

## How it works

```
 share link ─► GET /projects/shared/{seq}   (public: no key, no credits)
            ─► download the original + the dub (the lip-synced one when there is one)
            ─► measure on your machine: audio · Whisper (language, clarity, timing) · file check · lip movement
            ─► translation check on both transcripts (Gemini, or Claude), automatic when a key is set
            ─► report: verdict · sections · things to check  →  report.html / report.json / report.txt
```

- **Verdict rule:** any Poor → **Poor**; otherwise any Check → **Needs review**; otherwise **Good**. Informational and not-measured items don't count, and are listed with the reason.
- In the app the work runs in a **background thread**, so reloading the page is safe: the job id in the URL reattaches to it.
- All measuring (Whisper, MediaPipe, audio) happens **on your machine**. Only the translation check sends the two transcripts (text, not audio) to Gemini or Claude.

More detail: [Architecture](docs/ARCHITECTURE.md) · [Metrics and score bands](docs/METRICS.md) · [Engineering review](docs/ENGINEERING_REVIEW.md)

---

## Get started on a new machine

### 1. What you need
- **Python 3.14** (the pinned package versions were verified on macOS arm64). Check with `python3 --version`.
- **git**
- About **2 GB of free disk space** (Python packages plus the Whisper model).
- A **Gemini API key** (`GEMINI_API_KEY`, from Google AI Studio) for the translation check. A Claude key (`ANTHROPIC_API_KEY`) also works. Without a key, everything else still runs and the translation check shows as "not measured".

`ffmpeg` is **not** needed separately; it comes with the `imageio-ffmpeg` package.

### 2. Install
```bash
python3 -m venv eval_env
source eval_env/bin/activate          # Windows: eval_env\Scripts\activate
pip install -r requirements-dev.txt   # app + test dependencies, takes a few minutes
```

### 3. Turn on the translation check
```bash
cp .env.example .env     # then paste your key after GEMINI_API_KEY=
```
`.env` is listed in `.gitignore`, so it is never committed.

### 4. Check the install and run
```bash
pytest -m "not slow"                  # about 6 s; all tests should pass
python qa.py "<your share link>"      # report in the terminal
streamlit run app.py                  # or the app at http://localhost:8501
```

The first run downloads the Whisper `base` speech model (~145 MB) to `~/.cache/whisper`, which takes about a minute. After that, a 30-second video takes about 45 seconds.

---

## Using it

### Get a share link
In Perso, open the dubbed video, choose **Share**, and copy the link. It looks like `https://perso.ai/en/share/video-translator?seq=…`.

### The app
1. Paste the link. The app shows the project: title, languages, length, and whether it is lip-synced. The **lip-synced video is evaluated** when there is one, because that is what viewers get, and then **lip movement is measured automatically**; for a dub without lip-sync it is skipped.
2. The **translation is checked automatically** when `GEMINI_API_KEY` (or `ANTHROPIC_API_KEY`) is set; the preview says which model will be used. There are no options to set. To also score an approved script, use the command line (`--script` / `--script-file`).
3. Press **Evaluate this dub**.
4. The results page shows the **verdict**, both videos side by side, the six report **sections** with a speech timeline chart, and **things to check**; each ▶ button starts both videos at that moment. **Detailed measurements** (table, loudness chart, transcripts) are below. Download **Report (HTML)** or **Data (JSON)**.

**Interface language:** English, 한국어, Português or Español (sidebar). Everything follows it: the report's explanations, verdict and things to check, Gemini's translation comments, error messages, and the downloaded HTML report. The command line takes `--lang ko` (or `pt`, `es`).

### The command line
```bash
python qa.py "<share link>"                        # text report on screen, files saved in the run folder
python qa.py "<share link>" --script-file ko.txt   # also score script accuracy
python qa.py "<share link>" --no-lipsync --no-translation-check   # fastest (skips lip movement even if lip-synced)
python qa.py "<share link>" --json                 # machine-readable
python qa.py "<share link>" --fail-on poor         # exit code 1 on a Poor verdict (automation)
```

### Score bands
Full detail in [METRICS.md](docs/METRICS.md).

| Measure | Good | Check | Poor |
|---|---|---|---|
| Length match | ≤ 5% | ≤ 15% | above |
| Loudness match | within ±2 dB | within ±4 dB | beyond |
| Extra silence in the dub | ≤ 5 pts | ≤ 15 pts | above |
| Speaking pace (Korean) | ≤ 7.5 chars/s | ≤ 9 | above |
| Speaking pace (English) | ≤ 3.2 words/s | ≤ 3.8 | above |
| Speaking pace (Spanish) | ≤ 3.5 words/s | ≤ 4.2 | above |
| Dub language | matches | unsure | different |
| Voice clarity | ≥ 90% | ≥ 70% | below |
| Speech timing overlap | ≥ 75% | ≥ 55% | below |
| Meaning (Gemini/Claude, 1–5) | ≥ 4 | 3 | below |
| Script accuracy | ≥ 80% | ≥ 50% | below |
| Lip movement | always informational | | |

The **lip movement number is not reliable on its own**; only compare it with the original video's score. The translation check works on speech-recognition transcripts, so a misheard word can look like a translation error; the report says when an issue may be one.

---

## Keep building

### Daily workflow
```bash
source eval_env/bin/activate
streamlit run app.py          # reloads when you save a file
pytest -m "not slow"          # run after every change (~6 s)
pytest                        # before committing (~20 s; the 2 slow tests need a local tests/data/sample.mp4)
```

### Where things live
```
qa.py                    Command line: python qa.py "<share link>"
app.py                   Streamlit UI: paste link → progress → report
.streamlit/config.toml   Theme (colors, fonts; light and dark)
src/perso_api.py         Share links: parse the link, read the public project, download the videos
src/pipeline.py          Share link → download → evaluate → translation check → report files
src/evaluate.py          All measurements (pure functions, no file writes)
src/translation_judge.py Translation check with Gemini (or Claude): retries, model fallback, structured JSON
src/report.py            Verdict, levels, messages, things to check; text and HTML renderers (pure)
src/cli.py               The command-line entry point behind qa.py
src/jobs.py              Background job runner and progress model (stages, %, stop)
src/i18n.py              Interface text in English, Korean, Portuguese and Spanish
src/face_landmarker.task MediaPipe face model used for lip movement
tests/                   pytest suite; tests/fake_perso.py fakes the share endpoint. tests/data/sample.mp4 (any ~30 s
                         English talking-head clip) is local test media, not in git; slow tests skip without it
data/output/runs/<id>/   Downloaded videos and report files of each run (not committed)
docs/                    Architecture, metrics, engineering review
AGENTS.md                Guide and rules for AI coding agents (Codex reads it; CLAUDE.md imports it)
CLAUDE.md                Imports AGENTS.md for Claude Code
```

### Ground rules
- **Tests never call Perso, Gemini or Claude**, and never see real keys. They use the fake in `tests/fake_perso.py` and a stubbed translation check, so they are free and work offline.
- **Never put an API key in code or docs.** Keep it in `.env`.
- Perso API reference: https://developers.perso.ai/llms.txt.
- `src/evaluate.py` and `src/report.py` stay pure, and Streamlit code stays in `app.py`.
- If you rename or remove keys in the results, bump `SCHEMA_VERSION` in `src/evaluate.py` and `RESULTS_SCHEMA_VERSION` in `app.py`.

### Ideas for next steps
Open items are tracked in [docs/ENGINEERING_REVIEW.md](docs/ENGINEERING_REVIEW.md). The biggest ones are replacing the experimental lip-sync measure with a SyncNet-style model and calibrating the new bands on more dubs.

---

## Troubleshooting

| Problem | What to do |
|---|---|
| `pip install` fails on `mediapipe` or `numpy` | Use Python 3.14 (`python3 --version`). Older Pythons need different package versions. |
| "This doesn't look like a Perso share link" | Copy the whole link from Perso's **Share** dialog; it contains `/share/` and `?seq=`. |
| "Sharing is turned off for this Perso project" | Ask the owner to turn sharing on for that video in Perso, then try again. |
| "This shared project has no finished dubbed video yet" | Wait until Perso finishes dubbing, then try again. |
| Translation check shows "not measured" | Add `GEMINI_API_KEY` to `.env` and restart. The reason in the report says what went wrong; everything else still works. |
| "Gemini is overloaded right now" | A temporary Google capacity problem (HTTP 503). The tool already retried and tried a second model; run it again in a minute. |
| First run is slow | It's downloading the Whisper speech model (~145 MB). This happens only once. |
| Progress page says the job is no longer tracked | The app was restarted during a run. Paste the share link again. |
