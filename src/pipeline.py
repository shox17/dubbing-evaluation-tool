"""The pipeline: evaluate the dub behind a Perso share link.

Fetch the shared project, download the original and the dub, measure, check the translation, build the report,
and save results.json plus report.json / report.html / report.txt in the run folder.
"""
import os
import json
import time
import uuid
import shutil
import logging
import threading
from typing import Callable, Optional

from dotenv import load_dotenv

from src.evaluate import run_full_evaluation, DEFAULT_WHISPER_MODEL
from src.jobs import Cancelled, Progress
from src.perso_api import PersoError, download_media, get_shared_project, parse_share_url
from src.report import build_report, render_html, render_text
from src.translation_judge import judge_translation, not_measured

log = logging.getLogger(__name__)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

OUTPUT_DIR = os.path.join(PROJECT_ROOT, "data", "output")
RUNS_DIR = os.path.join(OUTPUT_DIR, "runs")
RESULTS_FILE = os.path.join(OUTPUT_DIR, "results.json")
MAX_KEPT_RUNS = int(os.getenv("MAX_KEPT_RUNS", "10"))


def load_results() -> Optional[dict]:
    """Loads the most recent evaluation, or None if there is none (or it is unreadable)."""
    if not os.path.exists(RESULTS_FILE):
        return None
    try:
        with open(RESULTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        log.warning("Ignoring unreadable %s: %s", RESULTS_FILE, e)
        return None


def save_results(results: dict) -> None:
    """Writes results atomically so a crash never leaves a half-written file."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    tmp = RESULTS_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    os.replace(tmp, RESULTS_FILE)


def prune_old_runs(keep: int = MAX_KEPT_RUNS, protect: Optional[str] = None) -> None:
    """Deletes all but the newest `keep` run directories."""
    if not os.path.isdir(RUNS_DIR):
        return
    runs = sorted((os.path.join(RUNS_DIR, d) for d in os.listdir(RUNS_DIR)), key=os.path.getmtime, reverse=True)
    for old in runs[keep:]:
        if protect and os.path.abspath(old) == os.path.abspath(protect):
            continue
        shutil.rmtree(old, ignore_errors=True)


def new_run_dir() -> tuple[str, str]:
    """A fresh (run_id, run_dir) pair; the directory is not created yet."""
    run_id = f"{time.strftime('%Y%m%d-%H%M%S')}_{uuid.uuid4().hex[:8]}"
    return run_id, os.path.join(RUNS_DIR, run_id)


def save_report_files(results: dict, run_dir: str) -> dict:
    """Writes report.json, report.html and report.txt next to the videos; returns their paths."""
    os.makedirs(run_dir, exist_ok=True)
    rep = results["report"]
    p = results.get("pipeline", {})
    rel = lambda path: os.path.relpath(path, run_dir) if path and os.path.exists(path) else ""
    files = {"json": os.path.join(run_dir, "report.json"), "html": os.path.join(run_dir, "report.html"),
             "text": os.path.join(run_dir, "report.txt")}
    with open(files["json"], "w", encoding="utf-8") as f:
        json.dump({"report": rep, "results": {k: v for k, v in results.items() if k != "report"}},
                  f, ensure_ascii=False, indent=2)
    with open(files["html"], "w", encoding="utf-8") as f:
        f.write(render_html(rep, results, rel(p.get("input_video_path")), rel(p.get("dubbed_video_path"))))
    with open(files["text"], "w", encoding="utf-8") as f:
        f.write(render_text(rep))
    return files


def finish_run(eval_results: dict, run_dir: str, use_translation_judge: bool,
               notify: Callable[..., None], report_lang: str = "en") -> dict:
    """Checks the translation, builds the report, and saves results.json plus the report files."""
    if use_translation_judge:
        notify("evaluate", "Checking the translation...", 0.96)
        sr = eval_results["speech_recognition"]
        eval_results["translation_judge"] = judge_translation(
            sr.get("original_segments") or [], sr.get("dubbed_segments") or [],
            eval_results["metadata"].get("detected_source_language") or "unknown",
            eval_results["metadata"].get("target_language") or "unknown")
    else:
        eval_results["translation_judge"] = not_measured("r.judge.off")
    notify("evaluate", "Writing the report...", 0.99)
    eval_results["report"] = build_report(eval_results, report_lang)
    eval_results["pipeline"]["report_files"] = save_report_files(eval_results, run_dir)
    save_results(eval_results)
    return eval_results


def share_stages() -> list[str]:
    """The progress stages of a share-link evaluation."""
    return ["fetch", "download", "evaluate"]


def run_share_evaluation(
    share_url: str,
    ground_truth_text: Optional[str] = None,
    report: Optional[Callable[[Progress], None]] = None,
    cancel_event: Optional[threading.Event] = None,
    whisper_model_name: str = DEFAULT_WHISPER_MODEL,
    include_lipsync: Optional[bool] = None,
    use_translation_judge: bool = True,
    report_lang: str = "en",
    session=None,
    sleep: Callable[[float], None] = time.sleep,
) -> dict:
    """Evaluates the dub behind a Perso share link: fetch the project, download both videos, measure, report.

    Needs no Perso API key and spends no credits. The lip-synced video is evaluated when the project has one,
    because that is the version viewers get, and only then is lip movement measured (include_lipsync=None);
    True/False forces it on or off.
    """
    def notify(stage: str, message: str, fraction: float = 0.0, **kw):
        """Sends a progress update to the UI, if anyone is listening."""
        if report:
            report(Progress(stage=stage, message=message, stage_fraction=fraction, **kw))

    def check_cancel():
        """Stops the run if the user pressed Stop waiting."""
        if cancel_event is not None and cancel_event.is_set():
            raise Cancelled("Stopped by user.")

    token = parse_share_url(share_url)
    notify("fetch", "Reading the shared Perso project...", 0.3)
    project = get_shared_project(token, session=session, sleep=sleep)
    check_cancel()

    target, source = project.get("targetLanguage") or {}, project.get("sourceLanguage") or {}
    tag = target.get("languageTag")
    target_id = tag if tag and tag != "default" else target.get("code", "")
    if not target.get("code"):
        raise PersoError("The shared project doesn't say which language it was dubbed into.")
    use_lipsync = bool(project.get("isLipSync") and project.get("lipSyncFileUrl"))
    measure_lips = use_lipsync if include_lipsync is None else include_lipsync
    dubbed_path_remote = project["lipSyncFileUrl"] if use_lipsync else project["translatedFileUrl"]

    run_id, run_dir = new_run_dir()
    os.makedirs(run_dir, exist_ok=True)
    notify("download", "Downloading the original video...", 0.1)
    original_path = download_media(project["originalFileUrl"], os.path.join(run_dir, "original.mp4"),
                                   session=session, sleep=sleep, label="original video")
    check_cancel()
    notify("download", "Downloading the dubbed video...", 0.55)
    dubbed_path = download_media(dubbed_path_remote, os.path.join(run_dir, f"dubbed_{target_id}.mp4"),
                                 session=session, sleep=sleep, label="dubbed video")
    prune_old_runs(protect=run_dir)
    check_cancel()

    source_code = source.get("code") if source.get("code") not in (None, "", "auto") else None
    eval_results = run_full_evaluation(
        original_video_path=original_path,
        dubbed_video_path=dubbed_path,
        ground_truth_text=(ground_truth_text or "").strip(),
        target_lang=target["code"],
        whisper_model_name=whisper_model_name,
        on_step=lambda msg, frac: notify("evaluate", msg, frac * 0.95),
        include_lipsync=measure_lips,
        source_lang=source_code,
    )
    check_cancel()
    eval_results["pipeline"] = {
        "run_id": run_id,
        "execution_mode": "Perso share link" + (" (lip-synced video)" if use_lipsync else ""),
        "input_video_path": original_path,
        "dubbed_video_path": dubbed_path,
        "target_language_name": target.get("name") or target_id,
        "target_language_code": target["code"],
        "target_language_id": target_id,
        "share": {
            "share_url": share_url.strip(),
            "seq": project.get("seq"),
            "title": project.get("title"),
            "source_language_name": source.get("name"),
            "source_language_code": source.get("code"),
            "target_language_name": target.get("name"),
            "is_lipsync": bool(project.get("isLipSync")),
            "evaluated_video": "lip-synced" if use_lipsync else "dubbed",
            "duration_ms": project.get("durationMs"),
            "created": project.get("createDate"),
        },
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "logs": f"Downloaded from Perso share link to {os.path.relpath(run_dir, PROJECT_ROOT)}. No credits were spent.",
    }
    return finish_run(eval_results, run_dir, use_translation_judge, notify, report_lang)
