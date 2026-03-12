"""Shared project paths for logs, runtime data, and committed seed files."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOGS_DIR = PROJECT_ROOT / "logs"
DATA_DIR = PROJECT_ROOT / "data"
CONFIG_DIR = PROJECT_ROOT / "config"


def _ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_logs_dir() -> Path:
    return _ensure_dir(LOGS_DIR)


def get_data_dir() -> Path:
    return _ensure_dir(DATA_DIR)


def get_runtime_file(filename: str) -> Path:
    return get_data_dir() / filename


def get_seed_file(filename: str) -> Path:
    return CONFIG_DIR / filename


def build_log_file(prefix: str = "opencluely") -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return get_logs_dir() / f"{prefix}_{timestamp}.log"
