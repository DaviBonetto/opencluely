"""Opencluely context notes manager."""

from __future__ import annotations

import json
import logging
import os
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import List, Optional

try:
    from storage_paths import get_runtime_file
except ImportError:
    from src.storage_paths import get_runtime_file


logger = logging.getLogger("context_notes_manager")

CONTEXT_NOTES_FILE = str(get_runtime_file("context_notes.json"))
LEGACY_NOTES_FILE = str(get_runtime_file("notes.json"))


@dataclass
class ContextNote:
    """Represents a saved context note."""

    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    title: str = "New Context Note"
    content: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(data: dict) -> "ContextNote":
        return ContextNote(
            id=data.get("id", str(uuid.uuid4())[:8]),
            title=data.get("title", "Untitled"),
            content=data.get("content", ""),
            created_at=data.get("created_at", datetime.now().isoformat()),
            updated_at=data.get("updated_at", datetime.now().isoformat()),
        )


class ContextNotesManager:
    """Handles local context notes with light legacy migration."""

    def __init__(self, filepath: str = CONTEXT_NOTES_FILE):
        self.filepath = filepath
        self.notes: List[ContextNote] = []
        self.load()
        logger.info("[ContextNotesManager] Loaded %s notes", len(self.notes))

    def load(self) -> None:
        """Load notes from runtime storage or a legacy notes file."""
        if self._load_payload_from_path(self.filepath):
            return

        if self._load_payload_from_path(LEGACY_NOTES_FILE, migrate=True):
            logger.info("[ContextNotesManager] Migrated legacy notes")
            return

        self.notes = []
        self.add("Session Notes", "Capture key points, proof points, and follow-ups here.")

    def _load_payload_from_path(self, path: str, migrate: bool = False) -> bool:
        if not path or not os.path.exists(path):
            return False

        try:
            with open(path, "r", encoding="utf-8") as handle:
                data = json.load(handle)
        except Exception as exc:
            logger.error("[ContextNotesManager] Failed to read %s: %s", path, exc)
            return False

        self.notes = [ContextNote.from_dict(note) for note in data.get("notes", [])]

        if migrate or path != self.filepath:
            self.save()

        return True

    def save(self) -> None:
        """Persist notes to runtime storage."""
        try:
            os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
            data = {
                "version": "1.0",
                "notes": [note.to_dict() for note in self.notes],
            }
            with open(self.filepath, "w", encoding="utf-8") as handle:
                json.dump(data, handle, ensure_ascii=False, indent=2)
            logger.info("[ContextNotesManager] Saved %s notes", len(self.notes))
        except Exception as exc:
            logger.error("[ContextNotesManager] Failed to save notes: %s", exc)

    def add(self, title: str = "New Context Note", content: str = "") -> ContextNote:
        note = ContextNote(title=title, content=content)
        self.notes.append(note)
        self.save()
        logger.info("[ContextNotesManager] Added note: %s", note.title)
        return note

    def update(self, note_id: str, title: str = None, content: str = None) -> Optional[ContextNote]:
        for note in self.notes:
            if note.id != note_id:
                continue
            if title is not None:
                note.title = title
            if content is not None:
                note.content = content
            note.updated_at = datetime.now().isoformat()
            self.save()
            logger.info("[ContextNotesManager] Updated note: %s", note.title)
            return note
        return None

    def delete(self, note_id: str) -> bool:
        for index, note in enumerate(self.notes):
            if note.id != note_id:
                continue
            deleted = self.notes.pop(index)
            self.save()
            logger.info("[ContextNotesManager] Deleted note: %s", deleted.title)
            return True
        return False

    def get_by_id(self, note_id: str) -> Optional[ContextNote]:
        for note in self.notes:
            if note.id == note_id:
                return note
        return None

    def get_all(self) -> List[ContextNote]:
        return self.notes

    def get_titles(self) -> List[tuple]:
        return [(note.id, note.title) for note in self.notes]
