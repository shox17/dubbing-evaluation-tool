"""Background jobs: a share-link evaluation (or a comparison of two) runs in a thread so the UI can show live progress, survive page
reloads (the job id is kept in the URL) and let the user stop it."""
import time
import uuid
import logging
import threading
from dataclasses import dataclass, field
from typing import Callable, Optional

log = logging.getLogger(__name__)

# Ordered stages shown in the UI checklist.
STAGES = [
    ("fetch", "Read the Perso share link"),
    ("download", "Download both videos"),
    ("evaluate", "Measure quality"),
    ("dub_a", "Evaluate dub A"),
    ("dub_b", "Evaluate dub B"),
    ("dub_c", "Evaluate dub C"),
    ("dub_d", "Evaluate dub D"),
    ("dub_e", "Evaluate dub E"),
    ("dub_f", "Evaluate dub F"),
    ("dub_g", "Evaluate dub G"),
    ("dub_h", "Evaluate dub H"),
    ("compare", "Compare and recommend"),
    ("batch", "Evaluate every link"),
]
STAGE_KEYS = [k for k, _ in STAGES]


class Cancelled(RuntimeError):
    """The user stopped a job."""


@dataclass
class Progress:
    """One progress report from the pipeline."""
    stage: str                       # one of STAGE_KEYS
    message: str                     # what is happening, in plain words
    stage_fraction: float = 0.0      # 0..1 within the stage


@dataclass
class Job:
    """One background evaluation: its status, current stage, progress and, when finished, result or error."""
    id: str
    params: dict
    stages: list[str]                               # the stages this job goes through
    status: str = "running"                         # running | done | failed | cancelled
    stage: str = ""
    message: str = "Starting..."
    stage_fraction: float = 0.0
    started_at: float = field(default_factory=time.time)
    stage_started_at: float = field(default_factory=time.time)
    finished_at: Optional[float] = None
    result: Optional[dict] = None
    error: Optional[str] = None
    cancel_event: threading.Event = field(default_factory=threading.Event)
    _lock: threading.Lock = field(default_factory=threading.Lock)

    def report(self, p: Progress) -> None:
        """Records a progress update from the pipeline (called from the worker thread)."""
        with self._lock:
            if p.stage != self.stage:
                self.stage_started_at = time.time()
            self.stage, self.message = p.stage, p.message
            self.stage_fraction = max(0.0, min(1.0, p.stage_fraction))

    @property
    def overall_fraction(self) -> float:
        """Progress across all stages, weighted by their typical share of the run time."""
        weights = {"fetch": 0.2, "download": 1, "evaluate": 6, "compare": 0.2, "batch": 1,
                   **{f"dub_{c}": 7 for c in "abcdefgh"}}
        total = sum(weights[s] for s in self.stages)
        if self.status == "done":
            return 1.0
        done = 0.0
        for s in self.stages:
            if s == self.stage:
                done += weights[s] * self.stage_fraction
                break
            done += weights[s]
        return min(0.99, done / total) if total else 0.0

    @property
    def elapsed_sec(self) -> float:
        """Seconds since the job started, frozen once it finishes."""
        return (self.finished_at or time.time()) - self.started_at

    def stage_state(self, stage: str) -> str:
        """pending | active | done | failed for the UI checklist."""
        if self.status == "done":
            return "done"
        order = self.stages
        if stage not in order or self.stage not in order:
            return "pending"
        i, cur = order.index(stage), order.index(self.stage)
        if i < cur:
            return "done"
        if i == cur:
            return "failed" if self.status in ("failed", "cancelled") else "active"
        return "pending"


_jobs: dict[str, Job] = {}
_registry_lock = threading.Lock()


def start_job(runner: Callable[[Callable[[Progress], None], threading.Event], dict],
              params: dict, stages: list[str]) -> Job:
    """Runs runner(report, cancel_event) in a daemon thread and returns the Job immediately."""
    job = Job(id=uuid.uuid4().hex[:12], params=params, stages=stages, stage=stages[0])
    with _registry_lock:
        _jobs[job.id] = job

    def target():
        """Thread body: runs the pipeline and stores the result, error or cancellation on the job."""
        try:
            job.result = runner(job.report, job.cancel_event)
            job.status = "done"
            job.message = "Finished"
        except Exception as e:  # reported to the UI; the traceback goes to the log
            if isinstance(e, Cancelled):
                job.status, job.error = "cancelled", "You stopped this job."
            else:
                log.exception("Job %s failed", job.id)
                job.status, job.error = "failed", str(e)
        finally:
            job.finished_at = time.time()

    threading.Thread(target=target, name=f"job-{job.id}", daemon=True).start()
    return job


def get_job(job_id: Optional[str]) -> Optional[Job]:
    """Looks up a running or finished job by id; None if unknown (for example after an app restart)."""
    if not job_id:
        return None
    with _registry_lock:
        return _jobs.get(job_id)
