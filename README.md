# Dubbing QA Studio

Automatic quality reports for videos dubbed with **[Perso AI](https://perso.ai)**.

Paste a **Perso share link**, and the tool downloads the original and the dub, measures both, and writes a report: an overall **verdict**, every measure marked **Good / Check / Poor** with a plain-language explanation and the thresholds it used, and every problem as a **time range** to check. No Perso account, API key or credits are needed.

**Compare mode** takes 2 to 8 share links (dubs of the same video), evaluates all of them the same way, **ranks them and recommends which one to deliver** with a fixed decision rule, and explains why.

```bash
python qa.py "https://perso.ai/en/share/video-translator?seq=…" --out ./output --lang ko
python qa.py compare "<link A>" "<link B>" --out ./output --lang ko
```

Works with any language pair, with or without lip-sync, on Windows, macOS and Linux.

| Section | What it checks | How |
|---|---|---|
| **Timing & audio** | Same length? Same loudness? Unusual gaps? Distortion? Rushed speech? | `librosa` on both tracks: duration, RMS loudness (dB), silence, clipping, chars/words per second |
| **Speech recognition** | Is the dub in the right language? Is the voice clear? Does it sound clean, not robotic or distorted? | Whisper language detection, the share of speech Whisper recognises confidently, a voice-quality model (DNSMOS P.835) comparing the dub with the original at the same moments, and a speaker-recognition model checking the dub voice still sounds like each original speaker (lines with a quiet background only) |
| **Timing alignment** | Does the dub speak when the original speaks? | Whisper word timings of both tracks → overlap of speech (IoU) and the places where only one track speaks |
| **Translation** *(automatic when a key is set)* | Same meaning? Anything missing or added? Names and numbers kept? | Gemini (or Claude) compares the two timestamped transcripts (needs `GEMINI_API_KEY` or `ANTHROPIC_API_KEY`) |
| **Video integrity** | Is the picture unchanged, with an audio track? | Resolution, frame rate and audio stream of both files |
| **Lip movement** *(experimental, lip-synced dubs only)* | Does the mouth move with the voice? | MediaPipe mouth opening vs loudness, compared with the original; measured automatically when the dub is lip-synced; never part of the verdict |
| **Script accuracy** *(CLI, when you pass a script)* | Is the script you expected heard in the dub? | Whisper transcript vs your script: CER for Korean, Japanese, Chinese and Thai, WER otherwise |

Every run saves `report.html` (a standalone page to share), `report.json` and `report.txt` in the `--out` folder (default `./output`). Compare mode saves `comparison.txt` / `.json` / `.html` plus `report_A.*` and `report_B.*`.

---

## How it works

```
 share link ─► GET /projects/shared/{seq}   (public: no key, no credits)
            ─► download the original + the dub (the lip-synced one when there is one)
            ─► measure on your machine: audio · Whisper (language, clarity, timing) · file check · lip movement
            ─► translation check on both transcripts (Gemini, or Claude), automatic when a key is set
            ─► report: verdict · sections · problem intervals  →  report.html / report.json / report.txt

 compare: link A + link B ─► the pipeline above for each ─► decision rule ─► comparison.txt / .json / .html
```

- **Verdict rule:** any Poor → **Poor**; otherwise any Check → **Needs review**; otherwise **Good**. Informational and not-measured items don't count, and are listed with the reason.
- **Downloads, speech recognition and the translation review are cached per share link** (`data/cache/`), so a rerun of the same link takes seconds and costs no API call. `--no-cache` redoes the downloads and speech recognition; a failed translation review is never cached.
- In the app the work runs in a **background thread**, so reloading the page is safe: the job id in the URL reattaches to it.
- All measuring (Whisper, MediaPipe, audio) happens **on your machine**. Only the translation check sends the two transcripts (text, not audio) to Gemini or Claude.

More detail: [Architecture](docs/ARCHITECTURE.md) · [Metrics and score bands](docs/METRICS.md) · [Engineering review](docs/ENGINEERING_REVIEW.md)

---

## Get started on a new machine

### 1. What you need
- **Python 3.14** (the pinned package versions were verified on macOS arm64; on Windows or Linux, if a pinned version doesn't install, use the unpinned command in [AGENTS.md](AGENTS.md#setting-up-a-new-machine)). Check with `python3 --version` (`py --version` on Windows).
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

The first run downloads the Whisper `base` speech model (~145 MB) to `~/.cache/whisper` and the speaker model (26 MB) to `~/.cache/dubbing-qa`, which takes about a minute. After that, a 30-second video takes about 45 seconds.

---

## Using it

### Get a share link
In Perso, open the dubbed video, choose **Share**, and copy the link. It looks like `https://perso.ai/en/share/video-translator?seq=…`. Links from Perso's gallery pages work too (`https://perso.ai/video-translator/en-es/<category>?seq=…`): any perso.ai link with a `seq=` token.

### The app
1. Paste the link. The app shows the project: title, languages, length, and whether it is lip-synced. The **lip-synced video is evaluated** when there is one, because that is what viewers get, and then **lip movement is measured automatically**; for a dub without lip-sync it is skipped.
2. The **translation is checked automatically** when `GEMINI_API_KEY` (or `ANTHROPIC_API_KEY`) is set; the preview says which model will be used. There are no options to set. To also score an approved script, use the command line (`--script` / `--script-file`).
3. Press **Evaluate this dub**.
4. The results page shows the **verdict**, both videos side by side, the six report **sections** with a speech timeline chart, and **things to check**; each ▶ button starts both videos at that moment. **Detailed measurements** (table, loudness chart, transcripts) are below. Download **Report (HTML)** or **Data (JSON)**.

**Interface language:** English, 한국어, Português or Español (sidebar). Everything follows it: the report's explanations, verdict and things to check, Gemini's translation comments, error messages, and the downloaded HTML report. The command line takes `--lang ko` (the default), `en`, `es` or `pt`.

### Compare two dubs
**In the app:** open the **Compare two dubs** tab, paste link A and link B (each shows a preview; **Add another dub** goes up to 8), and press **Evaluate and compare**. The comparison page shows the recommended version, the problem intervals of each dub next to its video (▶ jumps there), the reasoning, and every check side by side. Download it as HTML or JSON.

**On the command line:**
```bash
python qa.py compare "<link A>" "<link B>" --out ./output --lang ko
python qa.py compare "<link A>" "<link B>" "<link C>" "<link D>"     # up to 8 dubs: a full ranking
```
Every dub goes through the full pipeline. **Decision rule**, stopping at the first rule that separates them:
1. better overall verdict (Good > Needs review > Poor)
2. fewer Poor items
3. fewer Check items
4. less total time in problem intervals (seconds)
5. higher translation meaning score (1–5)
6. higher speech-timing alignment (%)

Still tied → the earlier dub (A before B), and the comparison says it's a tie. With 3+ dubs the same rule sorts all of them into a ranking, and the reasoning explains #1 against #2. A rule is skipped when any dub has no value for it (for example, no translation check), and the comparison then says the decision was made without translation. If **every dub is Poor**, the best one is still named, with a clear "neither is ready to deliver" warning and what to fix first.

`comparison.txt` and the top of `comparison.html` start with **1. Recommended version**, **2. Problem intervals** (per dub, e.g. `12.4s-15.1s | Dub B | missing speech | Poor | Translation check | The line about … is not spoken`) and **3. Reasoning** (the rule, the values for A and B, a short summary), followed by every check side by side, each link's details, measurement notes, the tool version and the run time. Probable speech-recognition errors are listed separately and never count.

**Exit codes:** `0` the recommended dub is Good or Needs review · `1` every dub is Poor · `2` input or runtime error (invalid link, sharing turned off, …).

### Batch mode: many links, one summary
```bash
python qa.py batch links.txt --out ./output/batch --lang en
```
`links.txt` has one share link per line (`#` comments and a `url,label` header are fine). Each link gets its own report folder (`001/`, `002/`, …), and the batch writes `summary.csv` (every measure's level and value per link; opens in Excel with Korean intact), `summary.txt` and `summary.json`. A broken link is recorded with its error and the batch goes on (exit code 2 if any failed, else 0).

**Calibrate the tool against your ears:** after each link, add your own verdict, `good`, `check` (or `needs review`) or `poor`:
```
https://perso.ai/…?seq=…,good
https://perso.ai/…?seq=…,poor
```
The summary then shows how often the tool agrees with you, whether it is stricter or more lenient, and a person × tool table. Use the CSV to see which measure drove each disagreement before you change a threshold.

### History and trends
Every evaluation (app, command line, compare and batch) is added to `data/history.jsonl` on your machine. See it with **History** in the app's sidebar (period filter, weekly verdict chart, language pairs, most frequent problems, latest runs), or:
```bash
python qa.py history --days 30 --lang en          # summary in the terminal
python qa.py history --csv history.csv            # every recorded evaluation as a spreadsheet
```
Reruns of the same link count once in the totals (the latest run wins).

### The command line
```bash
python qa.py "<share link>"                        # text report on screen (Korean by default), files in ./output
python qa.py "<share link>" --script-file ko.txt   # also score script accuracy
python qa.py "<share link>" --no-lipsync --no-translation-check   # fastest (skips lip movement even if lip-synced)
python qa.py "<share link>" --json                 # machine-readable
python qa.py "<share link>" --fail-on poor         # exit code 1 on a Poor verdict (automation)
python qa.py "<share link>" --out reports --lang en   # another folder (created if missing), English report
python qa.py "<share link>" --original original.mp4   # when the share link has no original (file or URL)
python qa.py "<share link>" --no-cache             # download and transcribe again
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
| Voice similarity to the original speaker (lines with a quiet background) | ≥ 50% | below (never Poor) | |
| Voice quality (vs the original, per ~9 s stretch) | voice < 0.6 and whole sound < 0.5 below | below that | voice ≥ 1.0 or whole sound ≥ 0.9 below |
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
src/pipeline.py          Share link → download (cached) → evaluate → translation check → report files; compare mode
src/compare.py           Compare mode: decision rule, comparison model, text and HTML renderers (pure)
src/intervals.py         Problem intervals: collect, merge, clip, round, sort (pure)
src/history.py           Evaluation history: record every run, summaries and trends
src/batch.py             Batch mode: input file, summary rows, agreement with your verdicts (pure)
src/version.py           Tool version printed in comparisons
src/evaluate.py          All measurements (pure functions, no file writes)
src/translation_judge.py Translation check with Gemini (or Claude): retries, model fallback, structured JSON
src/report.py            Verdict, levels, messages, things to check; text and HTML renderers (pure)
src/cli.py               The command-line entry point behind qa.py
src/jobs.py              Background job runner and progress model (stages, %, stop)
src/i18n.py              Interface text in English, Korean, Portuguese and Spanish
src/voice_quality.py     Voice quality with the DNSMOS model (ONNX, CPU)
src/speaker.py           Voice similarity with a speaker-recognition model (ONNX, downloaded once, 26 MB)
src/models/              Bundled models (face landmarks, DNSMOS) and their licenses
tests/                   pytest suite; tests/fake_perso.py fakes the share endpoint. tests/data/sample.mp4 (any ~30 s
                         English talking-head clip) is local test media, not in git; slow tests skip without it
data/cache/<link>/       Downloaded videos and Whisper results per share link (not committed)
data/output/runs/<id>/   Report files of each app run (not committed)
data/history.jsonl       Every evaluation, one line each (not committed)
output/                  The command line's default --out folder (not committed)
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
| "This doesn't look like a Perso share link" | Copy the whole link from Perso (Share dialog or gallery page); it must be on perso.ai and contain `?seq=`. |
| "Sharing is turned off for this Perso project" | Ask the owner to turn sharing on for that video in Perso, then try again. |
| "This shared project has no finished dubbed video yet" | Wait until Perso finishes dubbing, then try again. |
| "This share link has no original video" | Pass the original with `--original <file or URL>`. |
| Korean text shows as `???` in a Windows console | The CLI switches its output to UTF-8; use Windows Terminal, or open `comparison.txt` / `report.txt`, which are always UTF-8. |
| Translation check shows "not measured" | Add `GEMINI_API_KEY` to `.env` and restart. The reason in the report says what went wrong; everything else still works. |
| "Gemini is overloaded right now" | A temporary Google capacity problem (HTTP 503). The tool already retried and tried a second model; run it again in a minute. |
| First run is slow | It's downloading the Whisper speech model (~145 MB). This happens only once. |
| Progress page says the job is no longer tracked | The app was restarted during a run. Paste the share link again. |
