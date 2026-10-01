"""The pipeline: evaluate the dub behind a Perso share link, or compare the dubs behind two links.

Fetch the shared project, download the original and the dub (cached per link), measure (Whisper results cached
per link too), check the translation, build the report, and save the report files: report.json / .html / .txt
for one dub; comparison.* plus report_A.* and report_B.* for two.
"""
import os
import json
import time
import uuid
import shutil
import hashlib
import logging
import threading
from pathlib import Path
from typing import Callable, Optional

from dotenv import load_dotenv

from src.batch import agreement, render_batch_text, summary_row, to_csv
from src import history
from src.paths import DATA_DIR
from src.compare import LABELS, build_ranking, render_comparison_html, render_comparison_text
from src.evaluate import run_full_evaluation, DEFAULT_WHISPER_MODEL
from src.jobs import Cancelled, Progress
from src.perso_api import PersoError, download_media, get_shared_project, parse_share_url
from src.report import build_report, render_html, render_text
from src.translation_judge import judge_fingerprint, judge_translation, not_measured

log = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

OUTPUT_DIR = DATA_DIR / "output"
RUNS_DIR = OUTPUT_DIR / "runs"
RESULTS_FILE = OUTPUT_DIR / "results.json"
CACHE_DIR = DATA_DIR / "cache"
MAX_KEPT_RUNS = int(os.getenv("MAX_KEPT_RUNS", "10"))
MAX_CACHED_LINKS = int(os.getenv("MAX_CACHED_LINKS", "20"))

NO_ORIGINAL = ("This share link has no original video. Pass the original with --original <file or URL> "
               "(command line), then try again.")


def load_results() -> Optional[dict]:
    """Loads the most recent evaluation, or None if there is none (or it is unreadable)."""
    path = Path(RESULTS_FILE)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        log.warning("Ignoring unreadable %s: %s", path, e)
        return None


def _write_json(path: Path, data) -> None:
    """Writes JSON atomically so a crash never leaves a half-written file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, path)


def save_results(results: dict) -> None:
    """Saves the latest evaluation for the app's "Show last result"."""
    _write_json(Path(RESULTS_FILE), results)


def _prune(folder: Path, keep: int, protect: Optional[Path] = None) -> None:
    """Deletes all but the newest `keep` subfolders of folder."""
    if not folder.is_dir():
        return
    dirs = sorted((d for d in folder.iterdir() if d.is_dir()), key=lambda d: d.stat().st_mtime, reverse=True)
    for old in dirs[keep:]:
        if protect is None or old.resolve() != protect.resolve():
            shutil.rmtree(old, ignore_errors=True)


def prune_old_runs(keep: int = MAX_KEPT_RUNS, protect: Optional[str] = None) -> None:
    """Deletes all but the newest `keep` run directories."""
    _prune(Path(RUNS_DIR), keep, Path(protect) if protect else None)


def new_run_dir() -> tuple[str, str]:
    """A fresh (run_id, run_dir) pair; the directory is not created yet."""
    run_id = f"{time.strftime('%Y%m%d-%H%M%S')}_{uuid.uuid4().hex[:8]}"
    return run_id, str(Path(RUNS_DIR) / run_id)


def _short_hash(text: str) -> str:
    """A short, file-name-safe fingerprint of text."""
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:16]


class JsonCache:
    """A small key -> JSON value store in one file, used to keep Whisper results per share link."""

    def __init__(self, path: Path):
        self.path = path
        try:
            self.data = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
        except (OSError, json.JSONDecodeError):
            self.data = {}

    def get(self, key: str, default=None):
        """The cached value for key, or default."""
        return self.data.get(key, default)

    def __setitem__(self, key: str, value) -> None:
        self.data[key] = value
        _write_json(self.path, self.data)


def _link_cache_dir(token: str) -> Path:
    """This share link's cache folder (videos and Whisper results); marks it as recently used."""
    folder = Path(CACHE_DIR) / _short_hash(token)
    folder.mkdir(parents=True, exist_ok=True)
    os.utime(folder)
    return folder


def _cached_download(remote: str, folder: Path, prefix: str, session, sleep, label: str) -> str:
    """Downloads a media file into the cache folder unless an earlier run already did."""
    target = folder / f"{prefix}_{_short_hash(remote)}.mp4"
    if target.exists() and target.stat().st_size > 0:
        log.info("Using cached %s: %s", label, target.name)
        return str(target)
    return download_media(remote, str(target), session=session, sleep=sleep, label=label)


def _resolve_original(original: str, folder: Path, session, sleep) -> str:
    """The --original video: a local file as is, or a URL downloaded into the cache."""
    text = original.strip()
    if text.lower().startswith(("http://", "https://")):
        return _cached_download(text, folder, "original_override", session, sleep, "original video")
    path = Path(text).expanduser()
    if not path.is_file():
        raise FileNotFoundError(f"The original video file doesn't exist: {path}")
    return str(path.resolve())


def save_report_files(results: dict, out_dir, name: str = "report") -> dict:
    """Writes <name>.json, <name>.html and <name>.txt into out_dir; returns their paths."""
    folder = Path(out_dir)
    folder.mkdir(parents=True, exist_ok=True)
    rep = results["report"]
    p = results.get("pipeline", {})
    files = {"json": folder / f"{name}.json", "html": folder / f"{name}.html", "text": folder / f"{name}.txt"}
    _write_json(files["json"], {"report": rep, "results": {k: v for k, v in results.items() if k != "report"}})
    files["html"].write_text(render_html(rep, results, _video_src(p.get("input_video_path"), folder),
                                         _video_src(p.get("dubbed_video_path"), folder)), encoding="utf-8")
    files["text"].write_text(render_text(rep), encoding="utf-8")
    return {k: str(v) for k, v in files.items()}


def _video_src(path: Optional[str], folder: Path) -> str:
    """How an HTML file in folder refers to a video: a relative path, or a file:// URI on another drive."""
    if not path or not Path(path).exists():
        return ""
    try:
        return Path(os.path.relpath(path, folder)).as_posix()
    except ValueError:                       # Windows: the video is on another drive
        return Path(path).resolve().as_uri()


def share_stages() -> list[str]:
    """The progress stages of a share-link evaluation."""
    return ["fetch", "download", "evaluate"]


def compare_stages(n: int = 2) -> list[str]:
    """The progress stages of a comparison of n share links: one per dub, then the comparison."""
    return [f"dub_{c.lower()}" for c in LABELS[:n]] + ["compare"]


def evaluate_share(
    share_url: str,
    notify: Callable[..., None],
    check_cancel: Callable[[], None],
    ground_truth_text: Optional[str] = None,
    whisper_model_name: str = DEFAULT_WHISPER_MODEL,
    include_lipsync: Optional[bool] = None,
    use_translation_judge: bool = True,
    original: Optional[str] = None,
    use_cache: bool = True,
    session=None,
    sleep: Callable[[float], None] = time.sleep,
) -> dict:
    """Fetches, downloads (cached), measures and checks the translation of one share link; returns the results.

    The lip-synced video is evaluated when the project has one, because that is the version viewers get, and only
    then is lip movement measured (include_lipsync=None); True/False forces it on or off. original is used when
    the share link has no original video (a file path or a URL).
    """
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
    dubbed_remote = project["lipSyncFileUrl"] if use_lipsync else project["translatedFileUrl"]
    if not project.get("originalFileUrl") and not original:
        raise PersoError(NO_ORIGINAL)

    folder = _link_cache_dir(token)
    if not use_cache:
        for f in folder.glob("*"):
            f.unlink()
    notify("download", "Downloading the original video...", 0.1)
    if project.get("originalFileUrl"):
        original_path = _cached_download(project["originalFileUrl"], folder, "original", session, sleep, "original video")
    else:
        original_path = _resolve_original(original, folder, session, sleep)
    check_cancel()
    notify("download", "Downloading the dubbed video...", 0.55)
    dubbed_path = _cached_download(dubbed_remote, folder, f"dubbed_{target_id}", session, sleep, "dubbed video")
    _prune(Path(CACHE_DIR), MAX_CACHED_LINKS, protect=folder)
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
        cache=JsonCache(folder / "whisper_cache.json"),
    )
    check_cancel()
    eval_results["pipeline"] = {
        "run_id": f"{time.strftime('%Y%m%d-%H%M%S')}_{uuid.uuid4().hex[:8]}",
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
            "original_from": "share link" if project.get("originalFileUrl") else "--original",
        },
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "logs": "Read from a Perso share link; videos and speech recognition are cached per link. No credits were spent.",
    }
    check_translation(eval_results, use_translation_judge, notify, cache=JsonCache(folder / "judge_cache.json"))
    return eval_results


def check_translation(results: dict, enabled: bool, notify: Callable[..., None], cache=None) -> None:
    """Adds the translation check to results; any failure becomes a not-measured result, never an error.

    A successful review is cached (when cache is given) under a fingerprint of both transcripts, the languages,
    the prompt and the models, so a rerun of the same link gets the same answer without another API call.
    Failures are never cached: the next run tries again.
    """
    if not enabled:
        results["translation_judge"] = not_measured("r.judge.off")
        return
    notify("evaluate", "Checking the translation...", 0.96)
    sr, meta, share = results["speech_recognition"], results["metadata"], results["pipeline"]["share"]
    name = lambda label, code: f"{label} ({code})" if label and code else (label or code or "unknown")
    args = (sr.get("original_segments") or [], sr.get("dubbed_segments") or [],
            name(share.get("source_language_name"), meta.get("detected_source_language")),
            name(share.get("target_language_name"), meta.get("target_language")))
    key = _short_hash(json.dumps([args, judge_fingerprint()], ensure_ascii=False, sort_keys=True))
    cached = cache.get(key) if cache is not None else None
    if cached:
        results["translation_judge"] = {**cached, "cached": True}
        return
    results["translation_judge"] = judge_translation(*args)
    if cache is not None and results["translation_judge"].get("measured"):
        cache[key] = results["translation_judge"]


def _notifier(report: Optional[Callable[[Progress], None]]):
    """A notify(stage, message, fraction) function that forwards to report, if anyone is listening."""
    def notify(stage: str, message: str, fraction: float = 0.0):
        """Sends a progress update to the UI."""
        if report:
            report(Progress(stage=stage, message=message, stage_fraction=fraction))
    return notify


def _canceller(cancel_event: Optional[threading.Event]):
    """A check_cancel() function that stops the run once the user pressed Stop waiting."""
    def check_cancel():
        """Raises Cancelled if the user stopped the job."""
        if cancel_event is not None and cancel_event.is_set():
            raise Cancelled("Stopped by user.")
    return check_cancel


def run_share_evaluation(
    share_url: str,
    ground_truth_text: Optional[str] = None,
    report: Optional[Callable[[Progress], None]] = None,
    cancel_event: Optional[threading.Event] = None,
    whisper_model_name: str = DEFAULT_WHISPER_MODEL,
    include_lipsync: Optional[bool] = None,
    use_translation_judge: bool = True,
    report_lang: str = "en",
    out_dir: Optional[str] = None,
    original: Optional[str] = None,
    use_cache: bool = True,
    history_mode: str = "single",
    session=None,
    sleep: Callable[[float], None] = time.sleep,
) -> dict:
    """Evaluates the dub behind a Perso share link and saves report.json / .html / .txt.

    Needs no Perso API key and spends no credits. The files go to out_dir when given (the CLI's --out),
    otherwise to a new run folder under data/output/runs/. results.json keeps the latest run for the app.
    """
    notify = _notifier(report)
    results = evaluate_share(share_url, notify, _canceller(cancel_event), ground_truth_text=ground_truth_text,
                             whisper_model_name=whisper_model_name, include_lipsync=include_lipsync,
                             use_translation_judge=use_translation_judge, original=original, use_cache=use_cache,
                             session=session, sleep=sleep)
    notify("evaluate", "Writing the report...", 0.99)
    results["report"] = build_report(results, report_lang)
    if out_dir is None:
        run_id, folder = new_run_dir()
        results["pipeline"]["run_id"] = run_id
        prune_old_runs(protect=folder)
    else:
        folder = out_dir
    results["pipeline"]["report_files"] = save_report_files(results, folder)
    save_results(results)
    history.record(results, history_mode)
    return results


def save_comparison_files(comp: dict, results: dict, out_dir) -> dict:
    """Writes comparison.txt / .json / .html and report_A.*, report_B.*, ... into out_dir; returns their paths."""
    folder = Path(out_dir)
    folder.mkdir(parents=True, exist_ok=True)
    files = {"text": folder / "comparison.txt", "json": folder / "comparison.json", "html": folder / "comparison.html"}
    files["text"].write_text(render_comparison_text(comp), encoding="utf-8")
    _write_json(files["json"], {k: v for k, v in comp.items() if k != "reports"})
    files["html"].write_text(render_comparison_html(comp), encoding="utf-8")
    out = {k: str(v) for k, v in files.items()}
    for dub in comp["dubs"]:
        for kind, path in save_report_files(results[dub], folder, f"report_{dub}").items():
            out[f"{kind}_{dub}"] = path
    return out


def run_comparison(
    url_a: str,
    url_b: str,
    out_dir: str,
    report_lang: str = "ko",
    original: Optional[str] = None,
    report: Optional[Callable[[Progress], None]] = None,
    cancel_event: Optional[threading.Event] = None,
    whisper_model_name: str = DEFAULT_WHISPER_MODEL,
    include_lipsync: Optional[bool] = None,
    use_translation_judge: bool = True,
    use_cache: bool = True,
    more_urls: tuple = (),
    session=None,
    sleep: Callable[[float], None] = time.sleep,
) -> dict:
    """Evaluates dubs of the same video with the full pipeline, ranks them, recommends one, and saves every file.

    url_a and url_b are dubs A and B; more_urls adds C, D, ... (up to 8 in all). Returns {"comparison", "results":
    {"A", "B", ...}, "files"}. The decision rule lives in src/compare.py.
    """
    urls = [url_a, url_b, *more_urls]
    if len(urls) > len(LABELS):
        raise ValueError(f"Compare at most {len(LABELS)} dubs at a time.")
    started = time.time()
    outer = _notifier(report)
    check_cancel = _canceller(cancel_event)
    results = {}
    for dub, url in zip(LABELS, urls):
        span = {"fetch": (0.0, 0.03), "download": (0.03, 0.15), "evaluate": (0.15, 1.0)}

        def notify(stage, message, fraction=0.0, _dub=dub):
            """Maps one dub's fetch/download/evaluate progress onto its dub_a / dub_b stage."""
            lo, hi = span.get(stage, (0.0, 1.0))
            outer(f"dub_{_dub.lower()}", message, lo + (hi - lo) * fraction)
        results[dub] = evaluate_share(url, notify, check_cancel, whisper_model_name=whisper_model_name,
                                      include_lipsync=include_lipsync, use_translation_judge=use_translation_judge,
                                      original=original, use_cache=use_cache, session=session, sleep=sleep)
    outer("compare", "Comparing the dubs...", 0.5)
    comp = build_ranking(list(results.values()), report_lang, run_seconds=time.time() - started)
    for dub in comp["dubs"]:
        results[dub]["report"] = comp["reports"][dub]
    files = save_comparison_files(comp, results, out_dir)
    for dub in comp["dubs"]:
        history.record(results[dub], "compare")
    outer("compare", "Comparing the dubs...", 1.0)
    return {"comparison": comp, "results": results, "files": files}


def run_batch(entries: list[dict], out_dir: str, report_lang: str = "ko",
              report: Optional[Callable[[Progress], None]] = None, cancel_event: Optional[threading.Event] = None,
              session=None, sleep: Callable[[float], None] = time.sleep, **options) -> dict:
    """Evaluates every link of a batch (see src/batch.py) and writes summary.csv / .txt / .json plus one report
    folder per link. A link that fails is recorded with its error; the batch goes on. Returns {"rows", "files"}."""
    folder = Path(out_dir)
    folder.mkdir(parents=True, exist_ok=True)
    outer, check_cancel = _notifier(report), _canceller(cancel_event)
    rows = []
    for n, entry in enumerate(entries, 1):
        check_cancel()
        outer("batch", f"{n}/{len(entries)} {entry['link']}", (n - 1) / len(entries))
        inner = lambda p, _n=n: outer("batch", f"{_n}/{len(entries)} · {p.message}", (_n - 1) / len(entries))
        try:
            results = run_share_evaluation(entry["link"], report_lang=report_lang, out_dir=str(folder / f"{n:03d}"),
                                           report=inner, cancel_event=cancel_event, session=session, sleep=sleep,
                                           history_mode="batch", **options)
            rows.append(summary_row(n, entry, results))
        except Cancelled:
            raise
        except Exception as e:  # one broken link must not stop the batch
            log.warning("Batch link %d failed: %s", n, e)
            rows.append(summary_row(n, entry, error=str(e) or e.__class__.__name__))
    files = {"csv": folder / "summary.csv", "text": folder / "summary.txt", "json": folder / "summary.json"}
    files["csv"].write_text(to_csv(rows), encoding="utf-8-sig")       # BOM: Excel opens Korean text correctly
    files["text"].write_text(render_batch_text(rows, report_lang), encoding="utf-8")
    _write_json(files["json"], {"rows": rows, "agreement": agreement(rows)})
    outer("batch", "Done", 1.0)
    return {"rows": rows, "agreement": agreement(rows), "files": {k: str(v) for k, v in files.items()}}
