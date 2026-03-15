"""Session persistence outside the repository runtime tree."""

from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path

from runtime.paths import get_data_dir

from ..contracts import SessionState


class SessionPersistence:
    def __init__(self, base_dir: Path | None = None):
        self._base_dir = base_dir or (get_data_dir() / "sessions")
        self._base_dir.mkdir(parents=True, exist_ok=True)

    def save_state(self, state: SessionState) -> Path:
        output = self._base_dir / "last_session.json"
        payload = asdict(state)
        if state.is_incognito:
            payload["transcript_segments"] = []
            payload["chat_history"] = []
            payload["notes"] = []
            if payload.get("screen_context"):
                payload["screen_context"]["summary"] = ""
                payload["screen_context"]["image_path"] = None
        output.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
        return output
