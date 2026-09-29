"""Command line: evaluate the dub behind a Perso share link and print the report.

    python qa.py "https://perso.ai/en/share/video-translator?seq=..."

Progress goes to stderr, the report to stdout; report.json / report.html / report.txt are saved in the run folder.
"""
import os
import sys
import json
import logging
import argparse
import contextlib

from src.evaluate import DEFAULT_WHISPER_MODEL
from src.jobs import Cancelled, Progress
from src.perso_api import PersoError
from src.pipeline import run_share_evaluation
from src.report import render_text

log = logging.getLogger(__name__)
FAIL_LEVELS = {"never": (), "poor": ("poor",), "check": ("check", "poor")}


def parse_args(argv: list[str]) -> argparse.Namespace:
    """Command-line options."""
    ap = argparse.ArgumentParser(prog="qa.py", description="Evaluate the quality of a Perso AI dub from its share link.")
    ap.add_argument("share_url", help="Perso share link (https://perso.ai/.../share/video-translator?seq=...)")
    script = ap.add_mutually_exclusive_group()
    script.add_argument("--script", help="What the dub should say, to also score script accuracy")
    script.add_argument("--script-file", help="File with what the dub should say (UTF-8)")
    ap.add_argument("--whisper-model", default=DEFAULT_WHISPER_MODEL, help=f"Speech model (default {DEFAULT_WHISPER_MODEL})")
    ap.add_argument("--no-lipsync", action="store_true", help="Skip lip movement even for a lip-synced dub (faster). By default it is measured "
                         "automatically when the dub is lip-synced")
    ap.add_argument("--no-translation-check", action="store_true", help="Skip the translation check (by default it runs automatically when GEMINI_API_KEY or ANTHROPIC_API_KEY is set)")
    ap.add_argument("--json", action="store_true", help="Print the report as JSON instead of text")
    ap.add_argument("--lang", choices=["en", "ko", "pt", "es"], default="en", help="Report language (default en)")
    ap.add_argument("--verbose", action="store_true", help="Show library logs (MediaPipe, TensorFlow) while running")
    ap.add_argument("--fail-on", choices=list(FAIL_LEVELS), default="never",
                    help="Exit with code 1 when the verdict is this bad (for automation)")
    return ap.parse_args(argv)


@contextlib.contextmanager
def quiet_native_stderr(enabled: bool):
    """Sends C++ library logs (MediaPipe writes straight to fd 2) to /dev/null; yields a stream for our messages."""
    if not enabled:
        yield sys.stderr
        return
    sys.stderr.flush()
    saved = os.dup(2)
    devnull = os.open(os.devnull, os.O_WRONLY)
    os.dup2(devnull, 2)
    ours = os.fdopen(os.dup(saved), "w", buffering=1)
    try:
        yield ours
    finally:
        ours.flush()
        os.dup2(saved, 2)
        for fd in (saved, devnull):
            os.close(fd)
        ours.close()


def main(argv: list[str] | None = None) -> int:
    """Runs one evaluation. Exit codes: 0 done, 1 verdict failed --fail-on, 2 could not evaluate."""
    args = parse_args(sys.argv[1:] if argv is None else argv)
    with quiet_native_stderr(not args.verbose and _has_real_stderr()) as err:
        logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(name)s: %(message)s", stream=err, force=True)
        return _run(args, err)


def _has_real_stderr() -> bool:
    """False under test capture, where fd 2 isn't the process's stderr."""
    try:
        return sys.stderr.fileno() == 2
    except (AttributeError, OSError, ValueError):
        return False


def _run(args: argparse.Namespace, err) -> int:
    """The evaluation itself, printing progress and errors to err."""
    script = args.script
    if args.script_file:
        try:
            with open(args.script_file, encoding="utf-8") as f:
                script = f.read()
        except OSError as e:
            print(f"Can't read the script file: {e}", file=err)
            return 2

    last = {"msg": None}

    def progress(p: Progress):
        """Prints each new progress message once."""
        if p.message != last["msg"]:
            last["msg"] = p.message
            print(f"  [{p.stage}] {p.message}", file=err, flush=True)

    try:
        results = run_share_evaluation(
            args.share_url, ground_truth_text=script, report=progress, whisper_model_name=args.whisper_model,
            # None = automatic: lip movement is measured only when the dub is lip-synced.
            include_lipsync=False if args.no_lipsync else None,
            use_translation_judge=not args.no_translation_check, report_lang=args.lang)
    except (ValueError, FileNotFoundError, PersoError) as e:
        print(f"\nCould not evaluate: {e}", file=err)
        return 2
    except (Cancelled, KeyboardInterrupt):
        print("\nStopped.", file=err)
        return 2

    rep = results["report"]
    print(json.dumps(rep, ensure_ascii=False, indent=2) if args.json else render_text(rep))
    files = results["pipeline"].get("report_files", {})
    if files:
        print(f"\nSaved: {files['html']}\n       {files['json']}", file=err)
    return 1 if rep["overall"]["level"] in FAIL_LEVELS[args.fail_on] else 0


if __name__ == "__main__":
    sys.exit(main())
