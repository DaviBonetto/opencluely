"""Typed contracts for session orchestration and provider state."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class SessionMode(str, Enum):
    IDLE = "idle"
    LISTENING = "listening"
    PAUSED = "paused"
    TRANSCRIBING = "transcribing"
    ANALYZING = "analyzing"
    GENERATING = "generating"
    ERROR = "error"
    STOPPED = "stopped"


class SttProviderKind(str, Enum):
    AUTO = "auto"
    GROQ = "groq"
    GEMINI = "gemini"
    LOCAL = "local"


class AssistProviderKind(str, Enum):
    AUTO = "auto"
    GEMINI = "gemini"
    GROQ = "groq"
    LOCAL = "local"


class AudioSource(str, Enum):
    AUTO = "auto"
    MICROPHONE = "microphone"
    LOOPBACK = "loopback"
    MIXED = "mixed"


@dataclass(slots=True)
class TranscriptSegment:
    id: str
    text: str
    start_ms: int
    end_ms: int
    created_at: datetime
    is_partial: bool
    source: AudioSource
    provider: SttProviderKind


@dataclass(slots=True)
class ChatTurn:
    id: str
    role: str
    text: str
    created_at: datetime
    provider: str | None = None


@dataclass(slots=True)
class NoteSnapshot:
    body: str
    created_at: datetime
    source_summary: str = ""


@dataclass(slots=True)
class ScreenContext:
    summary: str
    captured_at: datetime
    provider: str
    is_active: bool
    image_path: str | None = None


@dataclass(slots=True)
class ProviderHealth:
    name: str
    available: bool
    configured: bool
    detail: str = ""


@dataclass(slots=True)
class SessionState:
    mode: SessionMode
    stt_provider: SttProviderKind
    audio_source: AudioSource
    started_at: datetime
    transcript_segments: list[TranscriptSegment] = field(default_factory=list)
    chat_history: list[ChatTurn] = field(default_factory=list)
    notes: list[NoteSnapshot] = field(default_factory=list)
    screen_context: ScreenContext | None = None
    provider_health: dict[str, ProviderHealth] = field(default_factory=dict)
    error_message: str = ""
    is_incognito: bool = False
