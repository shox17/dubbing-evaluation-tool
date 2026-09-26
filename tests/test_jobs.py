"""Tests for background jobs: results, errors, cancellation, progress weighting and the stage checklist."""
import time

from src.jobs import Progress, get_job, start_job
from src.perso_api import Cancelled


def wait(job, timeout=5):
    """Blocks until the job leaves the running state or the timeout passes."""
    end = time.time() + timeout
    while job.status == "running" and time.time() < end:
        time.sleep(0.01)
    return job


def test_job_runs_in_background_and_stores_result():
    def runner(report, cancel):
        report(Progress("upload", "Uploading", 0.5))
        report(Progress("dubbing", "Generating Voice", 0.5, eta_minutes=3, perso_project=11))
        return {"ok": True}
    job = wait(start_job(runner, {}, ["upload", "dubbing", "evaluate"]))
    assert job.status == "done" and job.result == {"ok": True}
    assert job.perso_projects == [11]
    assert get_job(job.id) is job
    assert job.overall_fraction == 1.0


def test_overall_progress_and_stage_states():
    def runner(report, cancel):
        report(Progress("lipsync", "Applying Lip Sync", 0.5))
        cancel.wait(5)
        raise Cancelled()
    job = start_job(runner, {}, ["upload", "dubbing", "lipsync", "download", "evaluate"])
    time.sleep(0.05)
    # weights: upload 1, dubbing 4, lipsync 6 (half done), download 1, evaluate 2 -> (1+4+3)/14
    assert abs(job.overall_fraction - 8 / 14) < 1e-6
    assert [job.stage_state(s) for s in job.stages] == ["done", "done", "active", "pending", "pending"]
    job.cancel_event.set()
    wait(job)
    assert job.status == "cancelled" and job.stage_state("lipsync") == "failed"


def test_failure_is_captured():
    def runner(report, cancel):
        raise ValueError("bad input")
    job = wait(start_job(runner, {}, ["evaluate"]))
    assert job.status == "failed" and job.error == "bad input"
