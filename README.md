# Dubbing QA Studio

A Streamlit app that checks the quality of videos dubbed with **[Perso AI](https://perso.ai)**.

You pick a video, a target language and the script the dub should say. The app sends the video to Perso, **waits until dubbing (and optional lip-sync) is finished**, downloads the result and compares the dub with the original:

| What it checks | How |
|---|---|
| **Timing match**: is the dub as long as the original? | Duration difference, plus a loudness-over-time chart so you can see drift |
| **Matches your script**: how much of *your* script is heard in the dub | Whisper transcribes the dub; CER for Korean, Japanese, Chinese and Thai, WER for other languages |
| **Voice clarity**: how clearly the dub speaks Perso's own translation | Whisper transcript vs the script Perso voiced (live runs only) |
| Loudness, silence, volume steadiness, speaking time | `librosa` on both audio tracks |
| Speech rate | Words or characters per second of speaking time |
| **Lip movement** *(experimental)* | MediaPipe mouth opening vs voice loudness, compared with the original |

Every run also lists **things to check**, such as a big length mismatch, an empty transcript, a script that doesn't fit the video, or a lip-sync that failed.

A **free demo** evaluates a ready-made Korean dub of the sample video, so you can try everything without a Perso account or credits.

---

## How it works

```
 You (browser)                     App (Streamlit)                          Perso AI
 ─────────────                     ───────────────                          ────────
 1. Choose video, language,  ──►  Setup page shows the credit estimate  ◄──  /media/quota
    script, then press Start
                                   A background job starts; its id goes into the URL (?job=…)
 2. Watch the progress page  ◄──  Upload  ─────────────────────────────►  video stored
    (live %, time left)            Dub     ── poll every 5 s ───────────►  dubbing project
                                   Lip-sync (optional, separate project) ►  lip-sync project
                                   Download the dubbed video + Perso's script
                                   Measure: audio, Whisper, MediaPipe (runs locally)
 3. Read the results page    ◄──  Results saved to data/output/results.json
```

- The work runs in a **background thread**, so reloading the page is safe: the job id in the URL reattaches to it.
- **Lip-sync is the slow step** (often 5–30 minutes). If it fails, the plain dub is still evaluated and a warning says so.
- All measuring (Whisper, MediaPipe, audio) happens **on your machine**. Only the video goes to Perso.

More detail: [Architecture](docs/ARCHITECTURE.md) · [Metrics and score bands](docs/METRICS.md) · [Engineering review](docs/ENGINEERING_REVIEW.md)

---

## Get started on a new machine

### 1. What you need
- **Python 3.14** (the pinned package versions were verified on macOS arm64). Check with `python3 --version`.
- **git**
- About **2 GB of free disk space** (Python packages plus the Whisper model).
- A **Perso API key** for real dubbing (optional; the free demo works without it). Get one at https://developers.perso.ai/api-keys. Free Perso plans can't download results, so they can't be evaluated.

`ffmpeg` is **not** needed separately; it comes with the `imageio-ffmpeg` package.

### 2. Install
```bash
python3 -m venv eval_env
source eval_env/bin/activate          # Windows: eval_env\Scripts\activate
pip install -r requirements-dev.txt   # app + test dependencies, takes a few minutes
```

### 3. Connect your Perso account
The API key is **never stored in the repository**. Set it on each machine in one of these ways:

```bash
cp .env.example .env     # then open .env and paste your key after PERSO_API_KEY=
```
or, for the current terminal only:
```bash
export PERSO_API_KEY=your-key-here
```
The app also picks up a key saved by the Perso CLI in `~/.perso/credentials`.

`.env` is listed in `.gitignore`, so it is never committed. Other optional settings are explained in [.env.example](.env.example) (default workspace, Whisper model size, how many runs to keep).

### 4. Check the install and run the app
```bash
pytest -m "not slow"     # about 6 s; all tests should pass
streamlit run app.py     # opens http://localhost:8501
```
The sidebar should show **Connected** with your workspace, plan and credits left. If it shows an error instead, check the key.

### 5. Do one demo run straight away
Choose **Use the sample video**, keep **Korean**, turn on **Free demo**, press **Paste the sample's Korean script**, then **Start demo evaluation**.

The first run downloads the Whisper `small` model (~460 MB) to `~/.cache/whisper`, so it takes a few minutes. Later runs take about 30 seconds. Doing this once right after cloning means the download is out of the way before you need the app.

---

## Using the app
**Interface language:** pick English, 한국어 (Korean), Português or Español at the top of the sidebar. The app starts in your browser's language when it is one of these, otherwise English. This only changes the app's own text; the dub language is chosen separately in step 2. Messages that come straight from Perso or from the measurements (errors, "things to check") stay in English.

1. **Choose a video**: the sample, or upload your own MP4, MOV or WebM (up to 2 GB).
2. **Choose the dubbing options**: target language and lip-sync on or off. The list shows **every language Perso can dub into** (77 today, including English UK, Portuguese Portugal and Spanish Spain), loaded live from Perso's Language API; type to search. The credit estimate from Perso updates as you change them. Lip-sync costs about twice as much.
3. **Paste the target script**: what the dub *should* say, in the target language. It's optional; without it the "Matches your script" score is skipped.
4. **Start.** The progress page shows each stage (Upload → Dub → Lip-sync → Download → Measure) with Perso's live status and time left. **Stop waiting** cancels the job if Perso hasn't started it yet.
5. **Results**: both videos side by side, four headline scores, an original-vs-dubbed table, a loudness chart, and a highlighted script diff (struck red = in your script but not heard, green = heard but not in your script). **Download report** saves everything as JSON.

**Reading the scores** (full detail in [METRICS.md](docs/METRICS.md)):

| Card | Good | Check | Poor |
|---|---|---|---|
| Timing match (length difference) | ≤ 5% | ≤ 15% | above |
| Matches your script / Voice clarity | ≥ 80% | ≥ 50% | below |
| Loudness match | within ±2 dB | within ±4 dB | beyond |
| Lip movement | always *Experimental* | | |

Speech recognition (Whisper) has no model for 4 of Perso's languages: Cebuano, Chichewa, Irish and Kyrgyz. You can still dub into them, but the app warns that the script scores are rough.

The script score is lenient on purpose: a different but correct wording also lowers it. The **lip movement number is not reliable on its own**. Only compare it with the original video's score.

**Credits:** Perso charges about 1 credit per second of video for dubbing, and about 2 with lip-sync. Real dubbing always spends credits; the demo never does. Use the **Refresh balance** button in the sidebar to reload your balance.

---

## Keep building

### Daily workflow
```bash
source eval_env/bin/activate
streamlit run app.py          # reloads automatically when you save a file
pytest -m "not slow"          # run after every change (~6 s)
pytest                        # before committing (~1 min; real Whisper/MediaPipe runs)

git add -A && git status      # check no .env, videos or results are listed
git commit -m "Describe the change"
git push                      # on another machine: git pull
```

### Where things live
```
app.py                   Streamlit UI: setup → progress → results
.streamlit/config.toml   Theme (colors, fonts; light and dark)
src/perso_api.py         Perso REST client: languages, upload, dub, lip-sync, poll, download, script, credits
src/languages.py         Perso target languages: live list parsing, lookup, bundled fallback snapshot
src/i18n.py              Interface text in English, Korean, Portuguese and Spanish
src/jobs.py              Background job runner and progress model (stages, %, ETA, cancel)
src/pipeline.py          Orchestration: dub → wait → download → evaluate → results.json
src/evaluate.py          All metrics (pure functions, no file writes)
src/face_landmarker.task MediaPipe face model used for lip movement
data/ground_truth.txt    Korean script of the sample video
data/input/              sample_original.mp4; your uploads go to data/input/uploads/ (not committed)
data/output/             sample_dubbed_ko.mp4 for the demo; runs/ and results.json (not committed)
tests/                   pytest suite; tests/fake_perso.py fakes the Perso API
docs/                    Architecture, metrics, engineering review
.agents/skills/          Vendored Perso CLI skills (reference only, don't edit)
CLAUDE.md                Rules for AI coding assistants working on this repo
```

### Ground rules
- **Tests never call the real Perso API.** They use the fake in `tests/fake_perso.py`, so they are free and work offline.
- **Never put the API key in code or docs.** Keep it in `.env` or `~/.perso/credentials`.
- Perso API reference: https://developers.perso.ai/llms.txt. Poll no faster than every 5 s.
- `src/evaluate.py` stays pure, and Streamlit code stays in `app.py`.
- If you rename or remove keys in the results, bump `schema_version` in `src/evaluate.py` and `RESULTS_SCHEMA_VERSION` in `app.py`.

### Ideas for next steps
Open items are tracked in [docs/ENGINEERING_REVIEW.md](docs/ENGINEERING_REVIEW.md). The biggest one is replacing the experimental lip-sync measure with a SyncNet-style model.

---

## Troubleshooting

| Problem | What to do |
|---|---|
| `pip install` fails on `mediapipe` or `numpy` | Use Python 3.14 (`python3 --version`). Older Pythons need different package versions. |
| Sidebar shows an error instead of **Connected** | The key is missing or wrong. Check `PERSO_API_KEY` in `.env`, then restart the app. |
| "Free plans can't download dubbed videos" | Upgrade the Perso plan, or use the free demo. |
| First run is very slow | It's downloading the Whisper model (~460 MB). This happens only once. |
| Theme changes don't show | Restart `streamlit run`; `config.toml` is only read at startup. |
| Progress page says the job is no longer tracked | The app was restarted while a job was running. The Perso project keeps going; find it in your Perso workspace. |


