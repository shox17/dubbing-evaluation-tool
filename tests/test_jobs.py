"""Tests for background jobs: results, errors, cancellation, progress weighting and the stage checklist."""
import time

from src.jobs import Cancelled, Progress, get_job, start_job


def wait(job, timeout=5):
    """Blocks until the job leaves the running state or the timeout passes."""
    end = time.time() + timeout
    while job.status == "running" and time.time() < end:
        time.sleep(0.01)
    return job


def test_job_runs_in_background_and_stores_result():
    def runner(report, cancel):
        report(Progress("fetch", "Reading the shared Perso project...", 1.0))
        report(Progress("download", "Downloading the dubbed video...", 0.5))
        return {"ok": True}
    job = wait(start_job(runner, {}, ["fetch", "download", "evaluate"]))
    assert job.status == "done" and job.result == {"ok": True}
    assert get_job(job.id) is job
    assert job.overall_fraction == 1.0


def test_overall_progress_and_stage_states():
    def runner(report, cancel):
        report(Progress("evaluate", "Transcribing the dubbed speech...", 0.5))
        cancel.wait(5)
        raise Cancelled()
    job = start_job(runner, {}, ["fetch", "download", "evaluate"])
    time.sleep(0.05)
    # weights: fetch 0.2, download 1, evaluate 6 (half done) -> (0.2 + 1 + 3) / 7.2
    assert abs(job.overall_fraction - 4.2 / 7.2) < 1e-6
    assert [job.stage_state(s) for s in job.stages] == ["done", "done", "active"]
    job.cancel_event.set()
    wait(job)
    assert job.status == "cancelled" and job.stage_state("evaluate") == "failed"


def test_failure_is_captured():
    def runner(report, cancel):
        raise ValueError("bad input")
    job = wait(start_job(runner, {}, ["evaluate"]))
    assert job.status == "failed" and job.error == "bad input"
