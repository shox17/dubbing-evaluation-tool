# Engineering Review

_Initial review 2026-09-25. Updated the same day after the UI and Perso API rework._

## Current state
- **Perso integration:** a native Python client implemented from the official API docs (https://developers.perso.ai/llms.txt). It covers upload, dubbing, lip-sync as a separate project, 5 s polling of `progressReason`/progress/ETA, download, the translated script, credits, and cost estimates. The Node worker it replaced was an opaque subprocess with no progress data.
- **Waiting:** jobs run in a background thread. The UI shows a live stage checklist with percentage and ETA, polls every 2 s, reattaches after a reload (`?job=<id>`), and can stop a job. Results appear automatically.
- **Results:** a side-by-side video comparison, four headline scores with Good/Check/Poor badges, an original-vs-dubbed table (8 measures), a loudness-over-time chart, a highlighted script diff, Perso's translation, and a JSON report download.
- **UI copy:** a guided 3-step form in plain language. The target script starts **empty** and is entered by the user; a one-click sample script is available in demo mode. The cost estimate comes from Perso, and the Start button stays disabled with a stated reason when something is missing.

## Fixed (cumulative)
| Area | Fix |
|---|---|
| Security | The hardcoded live API key was removed, and process-wide TLS bypass was removed. ⚠️ **Rotate the old key**, because it sat in plaintext. |
| Perso API | Wrong endpoint and 1.2 MB compression replaced by the documented flow. Friendly error mapping. Retries with backoff. |
| Correctness | Stale and mismatched results deleted. Demo mode restricted to sample + Korean. CER for CJK. Text normalization. Lip-sync `valid` flag. Full-length sample scripts. Zero-lag lip-sync score (the lag-maximised version inflated noise). |
| Robustness | Temp dirs, uuid run dirs, atomic results, pruning, logging, sanitised uploads, anchored paths, no import side effects. |
| Quality | Pinned deps, `.gitignore`, `.env.example`, 50 tests (fake Perso API, jobs, pipeline, Streamlit `AppTest` for setup, progress and results). |

## Verification performed
- `pytest`: all pass. This includes a full live flow against the fake API (upload → dub → lip-sync → download → evaluate), lip-sync failure fallback, cancellation, error codes, and UI views including the progress checklist with ETA and reload reattachment.
- **Read-only calls against the real Perso API** returned the workspace, plan (Starter), credits (300), and cost estimates for the sample: 28 credits without lip-sync, 56 with it.
- A real browser run through headless Chrome covered setup → Start (demo) → progress → results.
- **Not yet verified:** a real paid dubbing + lip-sync run. It spends credits (56 for the sample) and needs your go-ahead.

## Open items
1. **Replace the lip-sync heuristic** with SyncNet (LSE-C/LSE-D). On the demo, the in-sync original scores r = −0.20. See METRICS.md §3.
2. **Persist jobs across server restarts.** Save `{job params, perso project seqs}` to `data/output/runs/<id>/job.json` and resume polling on start. Today a restart loses tracking; the Perso project itself continues.
3. **Surface Perso's per-sentence `matchingRate`** (from `/script`) as a timing-fit measure, which is useful for spotting rushed sentences.
4. **Multi-speaker videos:** `numberOfSpeakers` is fixed at 1.
5. **Whisper `medium`** for reporting-grade transcripts, and GPU/MPS support.
6. **Initialise git.** `.gitignore` is ready. Use LFS for the sample media and the face model.
