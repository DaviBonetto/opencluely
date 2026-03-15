"""Pure backend services shared by providers and the UI bridge."""

from .notes_engine import LocalNotesEngine
from .transcript_store import TranscriptStore

__all__ = ["LocalNotesEngine", "TranscriptStore"]
