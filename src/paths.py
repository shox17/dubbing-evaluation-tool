"""Where the tool keeps its data: run outputs, the per-link cache, history, votes and jobs.

Everything lives under DATA_DIR: the project's data/ folder by default, or DUBBING_QA_DATA (the Docker image uses
/data, a volume, so results survive container restarts).
"""
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.getenv("DUBBING_QA_DATA") or PROJECT_ROOT / "data")
