"""Command line: evaluate the dub behind a Perso share link, or compare two dubs and recommend one.

    python qa.py "<share link>" --out ./output --lang ko
    python qa.py compare "<link A>" "<link B>" --out ./output --lang ko
    python qa.py batch links.txt --out ./output/batch       (one link per line, optionally ",good|check|poor")
    python qa.py history --days 30                          (every past evaluation: totals, language pairs, trends)
    python qa.py feedback                                   (reviewers' votes: which checks raise false alarms)
    python qa.py serve [--host 127.0.0.1] [--port 8000]     (REST API; docs at /docs)

Progress goes to stderr, the report to stdout. Single mode saves report.json / .html / .txt in --out; compare
mode saves comparison.* plus report_A.* and report_B.*.
"""
import os
import sys
import json
import logging
import argparse
import contextlib
from pathlib import Path

from src.evaluate import DEFAULT_WHISPER_MODEL
from src.jobs import Cancelled, Progress
from src.perso_api import PersoError
from src.pipeline import run_comparison, run_share_evaluation
from src.compare import render_comparison_text
from src.report import render_text

log = logging.getLogger(__name__)
FAIL_LEVELS = {"never": (), "poor": ("poor",), "check": ("check", "poor")}
LANGS = ["ko", "en", "es", "pt"]
DEFAULT_OUT = os.getenv("DUBBING_QA_OUT") or "output"      # the Docker image sets /data/output (on the volume)


def _common(ap: argparse.ArgumentParser) -> None:
    """Options shared by single and compare mode."""
    ap.add_argument("--out", default=DEFAULT_OUT, help="Folder for the report files (created if missing; default ./output)")
    ap.add_argument("--lang", choices=LANGS, default="ko", help="Report language (default ko)")
    ap.add_argument("--original", help="The original video (file or URL), used when a share link has none")
    ap.add_argument("--whisper-model", default=DEFAULT_WHISPER_MODEL, help=f"Speech model (default {DEFAULT_WHISPER_MODEL})")
    ap.add_argument("--no-lipsync", action="store_true", help="Skip lip movement even for a lip-synced dub (faster). By default it is measured "
                         "automatically when the dub is lip-synced")
    ap.add_argument("--no-translation-check", action="store_true", help="Skip the translation check (by default it runs automatically when GEMINI_API_KEY or ANTHROPIC_API_KEY is set)")
    ap.add_argument("--no-cache", action="store_true", help="Download the videos and run speech recognition again instead of reusing earlier results")
    ap.add_argument("--json", action="store_true", help="Print the report as JSON instead of text")
    ap.add_argument("--verbose", action="store_true", help="Show library logs (MediaPipe, TensorFlow) while running")


def parse_args(argv: list[str]) -> argparse.Namespace:
    """Command-line options for single mode."""
    ap = argparse.ArgumentParser(prog="qa.py", description="Evaluate the quality of a Perso AI dub from its share link. "
                                 "To compare two dubs: qa.py compare <link A> <link B>.")
    ap.add_argument("share_url", help="Perso share link (https://perso.ai/.../share/video-translator?seq=...)")
    script = ap.add_mutually_exclusive_group()
    script.add_argument("--script", help="What the dub should say, to also score script accuracy")
    script.add_argument("--script-file", help="File with what the dub should say (UTF-8)")
    _common(ap)
    ap.add_argument("--fail-on", choices=list(FAIL_LEVELS), default="never",
                    help="Exit with code 1 when the verdict is this bad (for automation)")
    args = ap.parse_args(argv)
    args.mode = "single"
    return args


def parse_compare_args(argv: list[str]) -> argparse.Namespace:
    """Command-line options for compare mode."""
    ap = argparse.ArgumentParser(prog="qa.py compare", description="Evaluate two Perso dubs of the same video, "
                                 "recommend which one to deliver, and explain why.")
    ap.add_argument("url_a", help="Share link of dub A")
    ap.add_argument("url_b", help="Share link of dub B")
    ap.add_argument("more", nargs="*", metavar="url_c", help="More share links (dubs C, D, ...; up to 8 in all)")
    _common(ap)
    args = ap.parse_args(argv)
    args.mode = "compare"
    return args


def parse_batch_args(argv: list[str]) -> argparse.Namespace:
    """Command-line options for batch mode."""
    ap = argparse.ArgumentParser(prog="qa.py batch", description="Evaluate every share link in a file and write one "
                                 "summary (summary.csv / .txt / .json). Add your own verdict after a link "
                                 "(link,good / check / poor) to see how often the tool agrees with you.")
    ap.add_argument("file", help="Text or CSV file: one share link per line, optionally followed by ,good / ,check / ,poor")
    _common(ap)
    args = ap.parse_args(argv)
    args.mode = "batch"
    return args


def parse_history_args(argv: list[str]) -> argparse.Namespace:
    """Command-line options for the history view."""
    ap = argparse.ArgumentParser(prog="qa.py history", description="Summarize every past evaluation: totals, verdicts "
                                 "per language pair, the most frequent problems and a weekly trend.")
    ap.add_argument("--days", type=int, help="Only the last N days")
    ap.add_argument("--lang", choices=LANGS, default="ko", help="Language (default ko)")
    ap.add_argument("--json", action="store_true", help="Print the summary as JSON")
    ap.add_argument("--csv", help="Also write every recorded evaluation to this CSV file")
    args = ap.parse_args(argv)
    args.mode, args.verbose = "history", True
    return args


def parse_feedback_args(argv: list[str]) -> argparse.Namespace:
    """Command-line options for the reviewer-feedback summary."""
    ap = argparse.ArgumentParser(prog="qa.py feedback", description="Summarize reviewers' votes on problem intervals: "
                                 "per check, how many flags were real problems and how many false alarms.")
    ap.add_argument("--lang", choices=LANGS, default="ko", help="Language (default ko)")
    ap.add_argument("--json", action="store_true", help="Print the summary as JSON")
    args = ap.parse_args(argv)
    args.mode, args.verbose = "feedback", True
    return args


@contextlib.contextmanager
def quiet_native_stderr(enabled: bool):
    """Sends C++ library logs (MediaPipe writes straight to fd 2) to the null device; yields a stream for our messages."""
    if not enabled:
        yield sys.stderr
        return
    sys.stderr.flush()
    saved = os.dup(2)
    devnull = os.open(os.devnull, os.O_WRONLY)
    os.dup2(devnull, 2)
    ours = os.fdopen(os.dup(saved), "w", buffering=1, encoding="utf-8", errors="replace")
    try:
        yield ours
    finally:
        ours.flush()
        os.dup2(saved, 2)
        for fd in (saved, devnull):
            os.close(fd)
        ours.close()


def use_utf8_console() -> None:
    """Prints Korean and other non-ASCII text correctly on every console (Windows defaults to a legacy code page)."""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError, OSError):
            pass                                  # replaced streams (tests, pipes in some IDEs) keep their encoding


def main(argv: list[str] | None = None) -> int:
    """Runs one evaluation or a comparison. Exit codes: 0 done, 1 see below, 2 input or runtime error.

    Single mode: 1 when the verdict fails --fail-on. Compare mode: 1 when every dub is Poor. Batch mode: 0 when every
    link was evaluated, 2 when any link failed (the summary is written either way).
    """
    use_utf8_console()
    argv = sys.argv[1:] if argv is None else argv
    if argv[:1] == ["serve"]:
        return _serve(argv[1:])
    parsers = {"compare": parse_compare_args, "batch": parse_batch_args, "history": parse_history_args,
               "feedback": parse_feedback_args}
    args = parsers[argv[0]](argv[1:]) if argv[:1] and argv[0] in parsers else parse_args(argv)
    with quiet_native_stderr(not args.verbose and _has_real_stderr()) as err:
        logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(name)s: %(message)s", stream=err, force=True)
        return _run(args, err)


def _serve(argv: list[str]) -> int:
    """Runs the REST API (src/api.py)."""
    ap = argparse.ArgumentParser(prog="qa.py serve", description="Run the REST API (interactive docs at /docs). "
                                 "Listening beyond this machine requires DUBBING_QA_API_TOKEN.")
    ap.add_argument("--host", default="127.0.0.1", help="Address to listen on (default 127.0.0.1: this machine only)")
    ap.add_argument("--port", type=int, default=8000, help="Port (default 8000)")
    args = ap.parse_args(argv)
    from src.api import serve
    serve(args.host, args.port)
    return 0


def _has_real_stderr() -> bool:
    """False under test capture, where fd 2 isn't the process's stderr."""
    try:
        return sys.stderr.fileno() == 2
    except (AttributeError, OSError, ValueError):
        return False


def _progress(err):
    """A progress callback that prints each new message once."""
    last = {"msg": None}

    def progress(p: Progress):
        """Prints a progress line when the message changes."""
        if p.message != last["msg"]:
            last["msg"] = p.message
            print(f"  [{p.stage}] {p.message}", file=err, flush=True)
    return progress


def _run_history(args: argparse.Namespace, err) -> int:
    """Prints the history summary (and writes the CSV when asked)."""
    import csv
    from src import history
    records = history.load()
    summary = history.summarize(records, days=args.days)
    print(json.dumps(summary, ensure_ascii=False, indent=2) if args.json else history.render_history_text(summary, args.lang))
    if args.csv:
        fields = ["time", "mode", "title", "languages", "language_pair", "lipsync", "verdict", "poor", "check",
                  "problem_seconds", "meaning_score", "overlap_pct", "link", "seq", "tool_version", "report"]
        with open(args.csv, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(records)
        print(f"\nSaved: {args.csv}", file=err)
    return 0


def _run(args: argparse.Namespace, err) -> int:
    """The evaluation or comparison itself, printing progress and errors to err."""
    if args.mode == "history":
        return _run_history(args, err)
    if args.mode == "feedback":
        from src import feedback
        summary = feedback.summarize(feedback.load())
        print(json.dumps(summary, ensure_ascii=False, indent=2) if args.json
              else feedback.render_feedback_text(summary, args.lang))
        return 0
    script = getattr(args, "script", None)
    if getattr(args, "script_file", None):
        try:
            script = Path(args.script_file).read_text(encoding="utf-8")
        except OSError as e:
            print(f"Can't read the script file: {e}", file=err)
            return 2
    options = dict(report=_progress(err), whisper_model_name=args.whisper_model,
                   # None = automatic: lip movement is measured only when the dub is lip-synced.
                   include_lipsync=False if args.no_lipsync else None,
                   use_translation_judge=not args.no_translation_check, report_lang=args.lang,
                   original=args.original, use_cache=not args.no_cache)
    if args.mode == "batch":
        return _run_batch(args, options, err)
    try:
        if args.mode == "compare":
            run = run_comparison(args.url_a, args.url_b, out_dir=args.out, more_urls=tuple(args.more), **options)
        else:
            results = run_share_evaluation(args.share_url, ground_truth_text=script, out_dir=args.out, **options)
    except (ValueError, FileNotFoundError, PersoError) as e:
        print(f"\nCould not evaluate: {e}", file=err)
        return 2
    except (Cancelled, KeyboardInterrupt):
        print("\nStopped.", file=err)
        return 2
    except Exception as e:  # anything unexpected (ffmpeg, a broken video) is a runtime error, exit code 2
        log.debug("Evaluation failed", exc_info=True)
        print(f"\nCould not evaluate: {e.__class__.__name__}: {e}", file=err)
        return 2

    if args.mode == "compare":
        comp = run["comparison"]
        print(json.dumps({k: v for k, v in comp.items() if k != "reports"}, ensure_ascii=False, indent=2)
              if args.json else render_comparison_text(comp))
        print("\nSaved: " + "\n       ".join(run["files"][k] for k in ("text", "html", "json")), file=err)
        return 1 if comp["recommendation"]["all_poor"] else 0

    rep = results["report"]
    print(json.dumps(rep, ensure_ascii=False, indent=2) if args.json else render_text(rep))
    files = results["pipeline"].get("report_files", {})
    if files:
        print(f"\nSaved: {files['html']}\n       {files['json']}", file=err)
    return 1 if rep["overall"]["level"] in FAIL_LEVELS[args.fail_on] else 0


def _run_batch(args: argparse.Namespace, options: dict, err) -> int:
    """Batch mode: evaluate every link in the file, print the summary, write summary files."""
    from src.batch import parse_batch_file, render_batch_text
    from src.pipeline import run_batch
    try:
        entries = parse_batch_file(Path(args.file).read_text(encoding="utf-8-sig"))
    except OSError as e:
        print(f"Can't read the batch file: {e}", file=err)
        return 2
    except ValueError as e:
        print(f"Could not read the batch file: {e}", file=err)
        return 2
    try:
        batch = run_batch(entries, args.out, **options)
    except (Cancelled, KeyboardInterrupt):
        print("\nStopped.", file=err)
        return 2
    print(json.dumps({"rows": batch["rows"], "agreement": batch["agreement"]}, ensure_ascii=False, indent=2)
          if args.json else render_batch_text(batch["rows"], args.lang))
    print("\nSaved: " + "\n       ".join(batch["files"][k] for k in ("csv", "text", "json")), file=err)
    return 2 if any(r["error"] for r in batch["rows"]) else 0


if __name__ == "__main__":
    sys.exit(main())
