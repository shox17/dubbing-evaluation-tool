"""The dubbing pipeline: sends a video to Perso (or uses the demo dub), waits for it, evaluates the result.

Also owns the data folders (sample video, runs/, results.json) and helpers to read and save results.
"""
import os
import json
import time
import uuid
import shutil
import logging
import threading
from typing import Callable, Optional

import cv2
from dotenv import load_dotenv

from src.evaluate import run_full_evaluation, DEFAULT_WHISPER_MODEL
from src.jobs import Progress
from src.languages import resolve_language
from src.perso_api import PersoClient, PersoError, Cancelled, SUPPORTED_UPLOAD_EXTENSIONS

log = logging.getLogger(__name__)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

INPUT_DIR = os.path.join(PROJECT_ROOT, "data", "input")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "data", "output")
RUNS_DIR = os.path.join(OUTPUT_DIR, "runs")
RESULTS_FILE = os.path.join(OUTPUT_DIR, "results.json")
SAMPLE_ORIGINAL = os.path.join(INPUT_DIR, "sample_original.mp4")
SAMPLE_DUBBED_KO = os.path.join(OUTPUT_DIR, "sample_dubbed_ko.mp4")
DEFAULT_GROUND_TRUTH_FILE = os.path.join(PROJECT_ROOT, "data", "ground_truth.txt")
MAX_KEPT_RUNS = int(os.getenv("MAX_KEPT_RUNS", "10"))

# Reference scripts for the bundled sample video (full length, one valid translation each).
# For real evaluations prefer the translated script from Perso itself: any paraphrase counts as error.
DEFAULT_TRANSCRIPTS = {
    "ko": "안녕하세요. 저는 우즈베키스탄에서 온 존입니다. 현재 인하대학교에서 소프트웨어 공학을 공부하고 있습니다. 저의 일상은 보통 수업에 가고, 코딩을 하고, 프로젝트를 진행하는 것입니다. 하지만 컴퓨터 앞에서 벗어날 때면, 새로운 장소, 새로운 맛, 그리고 새로운 경험을 탐험하기 위해 최선을 다합니다. 저에게 삶은 기술에 관한 것뿐만 아니라 화면 밖의 세상을 발견하는 것이기도 합니다. 감사하며, 곧 만나요!",
    "en": "Hi there, I'm John from Uzbekistan. I'm currently studying software engineering at Inha University. My daily life is usually going to classes, coding, and working on projects. But when I step away from my computer, I try my best to explore new places, new flavors, and new experiences. For me, life is not only about technology. It's also about discovering the world outside the screen. Thank you, see you soon!",
    "ja": "こんにちは、ウズベキスタンから来たジョンです。現在、インハ大学でソフトウェア工学を学んでいます。私の日常は、たいてい授業に出て、コーディングをして、プロジェクトに取り組むことです。でも、パソコンから離れるときは、新しい場所、新しい味、新しい経験を探求するために全力を尽くしています。私にとって人生はテクノロジーだけではありません。画面の外の世界を発見することでもあるのです。ありがとうございました、またすぐに会いましょう！",
    "es": "Hola, soy John de Uzbekistán. Actualmente estudio ingeniería de software en la Universidad Inha. Mi día a día suele consistir en ir a clases, programar y trabajar en proyectos. Pero cuando me alejo de la computadora, hago todo lo posible por explorar nuevos lugares, nuevos sabores y nuevas experiencias. Para mí, la vida no se trata solo de tecnología. También se trata de descubrir el mundo más allá de la pantalla. ¡Gracias, nos vemos pronto!",
    "fr": "Bonjour, je suis John et je viens d'Ouzbékistan. J'étudie actuellement le génie logiciel à l'Université Inha. Mon quotidien consiste généralement à aller en cours, coder et travailler sur des projets. Mais quand je m'éloigne de mon ordinateur, je fais de mon mieux pour découvrir de nouveaux lieux, de nouvelles saveurs et de nouvelles expériences. Pour moi, la vie ne se résume pas à la technologie. C'est aussi découvrir le monde au-delà de l'écran. Merci, à bientôt !"
}


def get_default_ground_truth(lang_code: str = "ko") -> str:
    """Retrieves target script baseline for selected target language."""
    if lang_code == "ko" and os.path.exists(DEFAULT_GROUND_TRUTH_FILE):
        with open(DEFAULT_GROUND_TRUTH_FILE, "r", encoding="utf-8") as f:
            content = f.read().strip()
        if content:
            return content
    return DEFAULT_TRANSCRIPTS.get(lang_code, DEFAULT_TRANSCRIPTS["ko"])


def is_sample_input(path: str) -> bool:
    """True when path is the bundled sample video that the demo dub was made from."""
    return os.path.exists(path) and os.path.exists(SAMPLE_ORIGINAL) and os.path.samefile(path, SAMPLE_ORIGINAL)


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


def probe_video(path: str) -> dict:
    """Duration, resolution and size of a local video (needed for Perso validation and cost estimates)."""
    cap = cv2.VideoCapture(path)
    try:
        if not cap.isOpened():
            raise ValueError(f"This file can't be read as a video: {os.path.basename(path)}")
        fps = cap.get(cv2.CAP_PROP_FPS) or 0
        frames = cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0
        return {
            "duration_ms": int(frames / fps * 1000) if fps > 0 else 0,
            "width": int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            "height": int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            "size": os.path.getsize(path),
        }
    finally:
        cap.release()


def pipeline_stages(use_demo_mode: bool, lip_dubbing: bool) -> list[str]:
    """The progress stages a run goes through, in order: demo runs only evaluate."""
    if use_demo_mode:
        return ["evaluate"]
    return ["upload", "dubbing"] + (["lipsync"] if lip_dubbing else []) + ["download", "evaluate"]


def run_pipeline(
    input_video_path: str,
    target_language: str = "ko",
    lip_dubbing: bool = True,
    use_demo_mode: bool = False,
    ground_truth_text: Optional[str] = None,
    report: Optional[Callable[[Progress], None]] = None,
    cancel_event: Optional[threading.Event] = None,
    space_seq: Optional[int] = None,
    client: Optional[PersoClient] = None,
    whisper_model_name: str = DEFAULT_WHISPER_MODEL
) -> dict:
    """Dubs the video with Perso (or uses the demo dub), waits for it to finish, then evaluates it."""
    def notify(stage: str, message: str, fraction: float = 0.0, **kw):
        """Sends a progress update to the UI, if anyone is listening."""
        if report:
            report(Progress(stage=stage, message=message, stage_fraction=fraction, **kw))

    def check_cancel():
        """Stops the run if the user pressed Stop waiting."""
        if cancel_event is not None and cancel_event.is_set():
            raise Cancelled("Stopped by user.")

    if not os.path.exists(input_video_path):
        raise FileNotFoundError(f"Input video not found: {input_video_path}")
    ground_truth_text = (ground_truth_text or "").strip()

    run_id = f"{time.strftime('%Y%m%d-%H%M%S')}_{uuid.uuid4().hex[:8]}"
    run_dir = os.path.join(RUNS_DIR, run_id)
    warnings: list[str] = []
    perso_info: dict = {}
    perso_translation: Optional[str] = None

    if use_demo_mode:
        lang = resolve_language(target_language)
        # The pre-processed dub is a Korean dub of the sample video only; any other pairing is meaningless.
        if not is_sample_input(input_video_path) or lang["id"] != "ko":
            raise ValueError("Demo mode only works with the bundled sample video and Korean as the target "
                             "language. Remove the uploaded video / select Korean, or turn demo mode off.")
        if not os.path.exists(SAMPLE_DUBBED_KO):
            raise FileNotFoundError(f"Demo dub not found: {SAMPLE_DUBBED_KO}")
        dubbed_output_path = SAMPLE_DUBBED_KO
        mode_desc = "Demo (pre-processed sample dub)"
        logs = "Used the bundled Korean dub of the sample video. No credits were spent."
    else:
        ext = os.path.splitext(input_video_path)[1].lower()
        if ext not in SUPPORTED_UPLOAD_EXTENSIONS:
            raise ValueError(f"Perso accepts {', '.join(SUPPORTED_UPLOAD_EXTENSIONS)} videos; this file is {ext}.")
        client = client or PersoClient()
        lang = resolve_language(target_language, client.list_languages())
        space_seq = space_seq or client.default_space()["spaceSeq"]
        meta = probe_video(input_video_path)

        notify("upload", "Checking the video against your Perso plan...", 0.1)
        client.validate_media(space_seq, os.path.basename(input_video_path), meta["size"],
                              meta["duration_ms"], meta["width"], meta["height"])
        check_cancel()
        notify("upload", f"Uploading {meta['size'] / 1e6:.1f} MB to Perso...", 0.3)
        media_seq = client.upload_video(space_seq, input_video_path)
        check_cancel()

        notify("dubbing", "Sending the dubbing request...", 0.0)
        dub_project = client.request_dubbing(space_seq, media_seq, lang["code"], language_tag=lang["tag"],
                                             title=f"QA {os.path.basename(input_video_path)} → {lang['id']}")
        perso_info = {"space_seq": space_seq, "media_seq": media_seq, "dubbing_project": dub_project}
        client.wait_for(dub_project, space_seq, cancel_event=cancel_event, on_update=lambda st: notify(
            "dubbing", st.label, st.progress / 100, eta_minutes=st.eta_minutes, perso_project=dub_project))

        final_project, use_lipsync_video = dub_project, False
        if lip_dubbing:
            notify("lipsync", "Requesting lip-sync...", 0.0)
            try:
                ls_project = client.request_lipsync(dub_project, space_seq)
                perso_info["lipsync_project"] = ls_project
                client.wait_for(ls_project, space_seq, cancel_event=cancel_event, on_update=lambda st: notify(
                    "lipsync", st.label, st.progress / 100, eta_minutes=st.eta_minutes, perso_project=ls_project))
                final_project, use_lipsync_video = ls_project, True
            except PersoError as e:
                # Same policy as Perso's own CLI: keep the (already paid) dub and say so.
                warnings.append(f"Lip-sync failed, so the plain dubbed video was evaluated instead ({e}).")

        notify("download", "Downloading the dubbed video...", 0.2)
        os.makedirs(run_dir, exist_ok=True)
        dubbed_output_path = client.download_video(
            final_project, space_seq, os.path.join(run_dir, f"dubbed_{lang['id']}.mp4"), lipsync=use_lipsync_video)
        notify("download", "Fetching Perso's translated script...", 0.8)
        try:
            sentences = client.get_script(dub_project, space_seq)
            perso_translation = " ".join(s.get("translatedText", "").strip() for s in sentences).strip() or None
        except PersoError as e:
            log.warning("Could not fetch Perso script: %s", e)
        mode_desc = "Perso AI" + (" + lip-sync" if use_lipsync_video else "")
        logs = f"Dubbed video saved to {os.path.relpath(dubbed_output_path, PROJECT_ROOT)}"
        prune_old_runs(protect=run_dir)

    check_cancel()
    eval_results = run_full_evaluation(
        original_video_path=input_video_path,
        dubbed_video_path=dubbed_output_path,
        ground_truth_text=ground_truth_text,
        target_lang=lang["code"],
        whisper_model_name=whisper_model_name,
        perso_translation=perso_translation,
        on_step=lambda msg, frac: notify("evaluate", msg, frac)
    )
    if not ground_truth_text:
        warnings.append("No target script was entered, so speech accuracy against your script was not scored.")
    eval_results["warnings"] = warnings + eval_results.get("warnings", [])

    eval_results["pipeline"] = {
        "run_id": run_id,
        "execution_mode": mode_desc,
        "input_video_path": input_video_path,
        "dubbed_video_path": dubbed_output_path,
        "target_language_name": lang["name"],
        "target_language_code": lang["code"],
        "target_language_id": lang["id"],
        "lip_dubbing_enabled": lip_dubbing and not use_demo_mode,
        "perso": perso_info,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "logs": logs
    }

    save_results(eval_results)
    return eval_results
