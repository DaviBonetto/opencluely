"""Shared runtime paths for logs and local application data."""

from __future__ import annotations

import os
import sys
from datetime import datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
APP_NAME = "Opencluely"
APP_HOME_ENV = "OPENCLUELY_HOME"


def _resolve_app_home() -> Path:
    env_home = os.environ.get(APP_HOME_ENV)
    if env_home:
        return Path(env_home).expanduser()

    if sys.platform == "win32":
        base_dir = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    elif sys.platform == "darwin":
        base_dir = Path.home() / "Library" / "Application Support"
    else:
        base_dir = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))

    return base_dir / APP_NAME


APP_HOME = _resolve_app_home()
LOGS_DIR = APP_HOME / "logs"
DATA_DIR = APP_HOME / "data"
SESSIONS_DIR = DATA_DIR / "sessions"
SCREENS_DIR = DATA_DIR / "screens"


def _ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_app_home() -> Path:
    return _ensure_dir(APP_HOME)


def get_logs_dir() -> Path:
    return _ensure_dir(LOGS_DIR)


def get_data_dir() -> Path:
    return _ensure_dir(DATA_DIR)


def get_sessions_dir() -> Path:
    return _ensure_dir(SESSIONS_DIR)


def get_screens_dir() -> Path:
    return _ensure_dir(SCREENS_DIR)


def get_runtime_file(filename: str) -> Path:
    return get_data_dir() / filename


def build_log_file(prefix: str = "opencluely") -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return get_logs_dir() / f"{prefix}_{timestamp}.log"
