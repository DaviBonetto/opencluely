"""Qt-safe session orchestrator that wires audio, transcript, notes, screen, and chat."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
import logging
import uuid

from PySide6.QtCore import QObject, Signal

from backend.audio_capture.capture import AudioCapture
from backend.providers.gemini_assist import GeminiAssistService
from backend.providers.gemini_live_stt import GeminiLiveTranscriber
from backend.providers.gemini_screen import GeminiScreenAnalyzer
from backend.providers.groq_assist import GroqAssistService
from backend.providers.groq_screen import GroqScreenAnalyzer
from backend.providers.groq_stt import GroqChunkTranscriber
from backend.providers.local_stt import LocalChunkTranscriber
from backend.providers.selection import ProviderAvailability, resolve_assist_provider, resolve_stt_provider
from backend.services.notes_engine import LocalNotesEngine
from backend.services.screen_capture import ScreenCaptureService
from backend.services.transcript_store import TranscriptStore

from ..contracts import (
    AssistProviderKind,
    AudioSource,
    ChatTurn,
    ProviderHealth,
    ScreenContext,
    SessionMode,
    SessionState,
    SttProviderKind,
)
from ..settings import AppBackendSettings, SETTINGS
from .context_builder import build_assist_prompt
from .persistence import SessionPersistence


logger = logging.getLogger("backend.session.orchestrator")


class SessionOrchestrator(QObject):
    state_changed = Signal(object)
    transcript_changed = Signal(object)
    partial_transcript_changed = Signal(str)
    notes_changed = Signal(str)
    chat_turn_added = Signal(object)
    screen_context_changed = Signal(object)
    provider_health_changed = Signal(object)
    status_message = Signal(str)
    error_occurred = Signal(str)

    def __init__(
        self,
        session_context: dict | None = None,
        settings: AppBackendSettings | None = None,
        parent: QObject | None = None,
    ):
        super().__init__(parent)
        self._settings = settings or SETTINGS
        self._session_context = session_context or {}
        self._transcript_store = TranscriptStore()
        self._notes_engine = LocalNotesEngine()
        self._screen_capture = ScreenCaptureService()
        self._persistence = SessionPersistence()
        self._screen_awareness_enabled = False
        self._latest_screen_path: str | None = None
        self._last_screen_capture_at: datetime | None = None
        self._latest_partial = ""

        self._audio_capture = AudioCapture(source=self._settings.audio_source)
        self._groq_stt = GroqChunkTranscriber(api_key=self._settings.groq_api_key)
        self._gemini_stt = GeminiLiveTranscriber(
            api_key=self._settings.gemini_api_key,
            model=self._settings.gemini_live_model,
        )
        self._local_stt = LocalChunkTranscriber()
        self._gemini_assist = GeminiAssistService(
            api_key=self._settings.gemini_assist_api_key,
            model=self._settings.gemini_assist_model,
        )
        self._groq_assist = GroqAssistService(api_key=self._settings.groq_api_key)
        self._gemini_screen = GeminiScreenAnalyzer(api_key=self._settings.gemini_api_key)
        self._groq_screen = GroqScreenAnalyzer(api_key=self._settings.groq_api_key)

        self._state = SessionState(
            mode=SessionMode.IDLE,
            stt_provider=self._settings.stt_provider,
            audio_source=self._settings.audio_source,
            started_at=datetime.now(UTC),
            is_incognito=self._settings.incognito,
        )

        self._connect_audio()
        self._connect_stt()
        self._connect_assist()
        self._connect_screen()
        self._refresh_provider_health()

    @property
    def state(self) -> SessionState:
        return self._state

    @property
    def desired_stt_provider(self) -> SttProviderKind:
        return self._settings.stt_provider

    @property
    def desired_assist_provider(self) -> AssistProviderKind:
        return self._settings.assist_provider

    @property
    def requested_audio_source(self) -> AudioSource:
        return self._settings.audio_source

    @property
    def screen_awareness_enabled(self) -> bool:
        return self._screen_awareness_enabled

    @property
    def current_groq_audio_model(self) -> str:
        return self._settings.groq_audio_model

    @property
    def current_gemini_live_model(self) -> str:
        return self._settings.gemini_live_model

    @property
    def current_gemini_assist_model(self) -> str:
        return self._settings.gemini_assist_model

    @property
    def current_assist_provider(self) -> AssistProviderKind:
        return self._current_assist_provider()

    def start_session(self) -> None:
        if self._state.mode == SessionMode.PAUSED:
            self._audio_capture.resume_recording()
            if self._current_stt_provider() == SttProviderKind.GEMINI:
                self._gemini_stt.start()
            self._set_mode(SessionMode.LISTENING)
            return

        if not self._ensure_transcriber_started():
            return
        if not self._audio_capture.isRunning():
            self._audio_capture.set_audio_source(self._settings.audio_source)
            self._audio_capture.start()
        self._state.started_at = datetime.now(UTC)
        self._set_mode(SessionMode.LISTENING)

    def pause_session(self) -> None:
        self._audio_capture.pause_recording()
        if self._current_stt_provider() == SttProviderKind.GEMINI:
            self._gemini_stt.flush_stream()
        self._set_mode(SessionMode.PAUSED)

    def stop_session(self) -> None:
        self._audio_capture.stop_recording()
        self._gemini_stt.stop()
        self._groq_stt.stop()
        self._local_stt.stop()
        self._persist_if_allowed()
        self._set_mode(SessionMode.STOPPED)

    def close_session(self) -> None:
        self.stop_session()
        self._screen_capture.clear_temporary_files()

    def toggle_incognito(self) -> bool:
        self._state.is_incognito = not self._state.is_incognito
        if self._state.is_incognito:
            self._screen_capture.clear_temporary_files()
        self.state_changed.emit(self._state)
        return self._state.is_incognito

    def toggle_screen_awareness(self) -> bool:
        self._screen_awareness_enabled = not self._screen_awareness_enabled
        if self._screen_awareness_enabled:
            self.capture_screen_context()
        else:
            self._latest_screen_path = None
            self._state.screen_context = None
            self.screen_context_changed.emit(None)
            self.state_changed.emit(self._state)
        return self._screen_awareness_enabled

    def capture_screen_context(self) -> None:
        if not self._screen_capture.is_available:
            self.error_occurred.emit("Screen capture is unavailable.")
            return

        persist = (
            self._settings.persist_screenshots
            and self._settings.persist_session_data
            and not self._state.is_incognito
        )
        image, image_path = self._screen_capture.capture(persist=persist)
        self._latest_screen_path = image_path
        self._last_screen_capture_at = datetime.now(UTC)
        prompt = (
            "Summarize this screen for a meeting copilot. "
            "Focus on what the user likely needs to answer or understand next."
        )

        if self._gemini_screen.is_available:
            self._set_mode(SessionMode.ANALYZING)
            self._gemini_screen.analyze_image(image, prompt)
            return

        if self._groq_screen.is_available:
            self._set_mode(SessionMode.ANALYZING)
            self._groq_screen.analyze_image(image, prompt)
            return

        self.error_occurred.emit("No multimodal provider is available for screen analysis.")

    def submit_prompt(self, text: str) -> None:
        prompt = text.strip()
        if not prompt:
            return

        user_turn = ChatTurn(
            id=f"user-{uuid.uuid4().hex[:10]}",
            role="user",
            text=prompt,
            created_at=datetime.now(UTC),
        )
        self._state.chat_history.append(user_turn)
        self.chat_turn_added.emit(user_turn)

        if self._screen_awareness_enabled and self._screen_context_is_stale():
            self.capture_screen_context()

        assist_prompt = build_assist_prompt(
            user_prompt=prompt,
            transcript_segments=self._transcript_store.recent_segments(8),
            notes=self._state.notes,
            screen_context=self._state.screen_context,
            language=self._session_context.get("language", "pt-BR"),
        )
        system_instruction = self._build_system_instruction()

        assist_provider = self._current_assist_provider()
        self._set_mode(SessionMode.GENERATING)
        if assist_provider == AssistProviderKind.GEMINI:
            self._gemini_assist.generate_answer(assist_prompt, system_instruction)
            return
        if assist_provider == AssistProviderKind.GROQ:
            self._groq_assist.generate_answer(assist_prompt, system_instruction)
            return

        self._on_error("No cloud assistant provider is available. Configure Groq or Gemini.")

    def set_stt_provider(self, provider: SttProviderKind) -> None:
        self._stop_transcribers()
        self._latest_partial = ""
        self.partial_transcript_changed.emit("")
        self._state.stt_provider = provider
        self._settings.stt_provider = provider
        if self._audio_capture.isRunning():
            self._ensure_transcriber_started()
        self._refresh_provider_health()

    def set_assist_provider(self, provider: AssistProviderKind) -> None:
        self._settings.assist_provider = provider
        self.state_changed.emit(self._state)

    def set_audio_source(self, source: AudioSource) -> None:
        self._state.audio_source = source
        self._settings.audio_source = source
        was_running = self._audio_capture.isRunning()
        if was_running:
            self._audio_capture.stop_recording()
            self._audio_capture.wait(2000)
        self._audio_capture.set_audio_source(source)
        if was_running:
            self.start_session()
        self.state_changed.emit(self._state)

    def set_groq_audio_model(self, model: str) -> None:
        self._settings.groq_audio_model = model.strip()
        self._groq_stt.set_model(self._settings.groq_audio_model)
        if self._audio_capture.isRunning() and self._current_stt_provider() == SttProviderKind.GROQ:
            self._groq_stt.stop()
            self._groq_stt.start()
        self._refresh_provider_health()

    def set_gemini_live_model(self, model: str) -> None:
        self._settings.gemini_live_model = model.strip()
        self._gemini_stt.set_model(self._settings.gemini_live_model)
        if self._audio_capture.isRunning() and self._current_stt_provider() == SttProviderKind.GEMINI:
            self._gemini_stt.stop()
            self._gemini_stt.start()
        self._refresh_provider_health()

    def set_gemini_assist_model(self, model: str) -> None:
        self._settings.gemini_assist_model = model.strip()
        self._gemini_assist.set_model(self._settings.gemini_assist_model)
        self._refresh_provider_health()

    def clear_session(self) -> None:
        self._transcript_store = TranscriptStore()
        self._state.transcript_segments = []
        self._state.chat_history = []
        self._state.notes = []
        self._state.screen_context = None
        self._state.error_message = ""
        self._latest_partial = ""
        self._latest_screen_path = None
        self._last_screen_capture_at = None
        self._screen_capture.clear_temporary_files()
        self.transcript_changed.emit([])
        self.partial_transcript_changed.emit("")
        self.notes_changed.emit("")
        self.screen_context_changed.emit(None)
        self._restore_live_mode()
        self.state_changed.emit(self._state)

    def _connect_audio(self) -> None:
        self._audio_capture.audio_frame_ready.connect(self._on_audio_frame)
        self._audio_capture.audio_chunk_ready_detailed.connect(self._on_audio_chunk)
        self._audio_capture.error_occurred.connect(self._on_error)
        self._audio_capture.recording_started.connect(lambda: self.status_message.emit("Listening"))
        self._audio_capture.recording_paused.connect(lambda: self.status_message.emit("Paused"))
        self._audio_capture.recording_resumed.connect(lambda: self.status_message.emit("Listening"))
        self._audio_capture.devices_ready.connect(self._on_devices_ready)

    def _connect_stt(self) -> None:
        for provider in (self._groq_stt, self._gemini_stt, self._local_stt):
            provider.segment_ready.connect(self._on_segment_ready)
            provider.error_occurred.connect(self._on_error)
            provider.status_changed.connect(self.status_message.emit)
        self._gemini_stt.partial_text.connect(self._on_partial_text)

    def _connect_assist(self) -> None:
        for service in (self._gemini_assist, self._groq_assist):
            service.answer_ready.connect(self._append_assistant_answer)
            service.error_occurred.connect(self._on_error)

    def _connect_screen(self) -> None:
        self._gemini_screen.analysis_ready.connect(
            lambda summary: self._on_screen_summary_ready(summary, "gemini")
        )
        self._groq_screen.analysis_ready.connect(
            lambda summary: self._on_screen_summary_ready(summary, "groq")
        )
        self._gemini_screen.error_occurred.connect(self._on_error)
        self._groq_screen.error_occurred.connect(self._on_error)

    def _refresh_provider_health(self) -> None:
        availability = self._availability()
        self._state.provider_health = {
            "groq_stt": ProviderHealth(
                name="groq_stt",
                available=availability.groq_stt,
                configured=self._settings.has_groq_key,
                detail=self._settings.groq_audio_model,
            ),
            "gemini_stt": ProviderHealth(
                name="gemini_stt",
                available=availability.gemini_live,
                configured=self._settings.has_gemini_live_key,
                detail=self._settings.gemini_live_model,
            ),
            "groq_assist": ProviderHealth(
                name="groq_assist",
                available=availability.groq_assist,
                configured=self._settings.has_groq_key,
                detail=self._settings.groq_assist_model,
            ),
            "gemini_assist": ProviderHealth(
                name="gemini_assist",
                available=availability.gemini_assist,
                configured=self._settings.has_gemini_assist_key,
                detail=self._settings.gemini_assist_model,
            ),
            "local_stt": ProviderHealth(
                name="local_stt",
                available=availability.local_stt,
                configured=availability.local_stt,
                detail=self._settings.local_whisper_model_size,
            ),
        }
        self.provider_health_changed.emit(self._state.provider_health)
        self.state_changed.emit(self._state)

    def _availability(self) -> ProviderAvailability:
        return ProviderAvailability(
            groq_stt=self._groq_stt.is_available,
            gemini_live=self._gemini_stt.is_available,
            local_stt=self._local_stt.is_available,
            groq_assist=self._groq_assist.is_available,
            gemini_assist=self._gemini_assist.is_available,
            groq_vision=self._groq_screen.is_available,
            gemini_vision=self._gemini_screen.is_available,
        )

    def _current_stt_provider(self) -> SttProviderKind:
        return resolve_stt_provider(self._state.stt_provider, self._availability())

    def _current_assist_provider(self) -> AssistProviderKind:
        return resolve_assist_provider(self._settings.assist_provider, self._availability())

    def _ensure_transcriber_started(self) -> bool:
        provider = self._current_stt_provider()
        if provider == SttProviderKind.GROQ:
            started = self._groq_stt.start()
        elif provider == SttProviderKind.GEMINI:
            started = self._gemini_stt.start()
        elif provider == SttProviderKind.LOCAL and self._settings.stt_provider == SttProviderKind.LOCAL:
            started = self._local_stt.start()
        else:
            self._state.stt_provider = provider
            self._on_error("No cloud transcription provider is available. Configure Groq or Gemini.")
            return False
        if not started:
            return False
        self._state.stt_provider = provider
        self._state.error_message = ""
        self.state_changed.emit(self._state)
        return True

    def _stop_transcribers(self) -> None:
        self._gemini_stt.stop()
        self._groq_stt.stop()
        self._local_stt.stop()

    def _on_audio_frame(self, audio_bytes: bytes, source_name: str, start_ms: int, end_ms: int) -> None:
        if self._current_stt_provider() != SttProviderKind.GEMINI:
            return
        self._gemini_stt.submit_frame(audio_bytes, start_ms, end_ms, AudioSource(source_name))

    def _on_audio_chunk(self, audio_bytes: bytes, source_name: str, start_ms: int, end_ms: int) -> None:
        source = AudioSource(source_name)
        provider = self._current_stt_provider()
        if provider == SttProviderKind.GROQ:
            self._groq_stt.submit_chunk(audio_bytes, start_ms, end_ms, source)
        elif provider == SttProviderKind.LOCAL:
            self._local_stt.submit_chunk(audio_bytes, start_ms, end_ms, source)

    def _on_segment_ready(self, segment) -> None:
        if not segment.text:
            return
        self._latest_partial = ""
        self.partial_transcript_changed.emit("")
        self._transcript_store.add_segment(segment)
        self._state.transcript_segments = self._transcript_store.segments
        self.transcript_changed.emit(self._state.transcript_segments)
        self._refresh_notes()
        self._persist_if_allowed()
        self._restore_live_mode()
        self.state_changed.emit(self._state)

    def _refresh_notes(self) -> None:
        snapshot = self._notes_engine.build_snapshot(self._state.transcript_segments)
        self._state.notes = [snapshot]
        self.notes_changed.emit(snapshot.body)

    def _on_partial_text(self, text: str) -> None:
        self._latest_partial = text
        self.partial_transcript_changed.emit(text)
        self._set_mode(SessionMode.TRANSCRIBING, emit_state=False)

    def _append_assistant_answer(self, answer: str, provider: str | None = None) -> None:
        if not answer:
            self._restore_live_mode()
            return
        turn = ChatTurn(
            id=f"assistant-{uuid.uuid4().hex[:10]}",
            role="assistant",
            text=answer,
            created_at=datetime.now(UTC),
            provider=provider,
        )
        self._state.chat_history.append(turn)
        self.chat_turn_added.emit(turn)
        self._persist_if_allowed()
        self._restore_live_mode()

    def _on_screen_summary_ready(self, summary: str, provider: str) -> None:
        context = ScreenContext(
            summary=summary,
            captured_at=datetime.now(UTC),
            provider=provider,
            is_active=self._screen_awareness_enabled,
            image_path=self._latest_screen_path,
        )
        self._state.screen_context = context
        self.screen_context_changed.emit(context)
        self._persist_if_allowed()
        self._restore_live_mode()

    def _on_devices_ready(self, details: dict) -> None:
        self._state.audio_source = AudioSource(details["selected_source"])
        self.status_message.emit(
            f"Audio source: {details['selected_source']} | "
            f"Mic: {'yes' if details['microphone_available'] else 'no'} | "
            f"Loopback: {'yes' if details['loopback_available'] else 'no'}"
        )
        self.state_changed.emit(self._state)

    def _on_error(self, message: str) -> None:
        self._state.error_message = message
        self._set_mode(SessionMode.ERROR)
        self.error_occurred.emit(message)

    def _persist_if_allowed(self) -> None:
        if self._settings.persist_session_data:
            self._persistence.save_state(self._state)

    def _screen_context_is_stale(self) -> bool:
        if self._last_screen_capture_at is None:
            return True
        return datetime.now(UTC) - self._last_screen_capture_at >= timedelta(seconds=30)

    def _build_system_instruction(self) -> str:
        language = self._session_context.get("language", "pt-BR")
        return (
            "You are Opencluely, an AI meeting assistant. "
            "You help with meeting questions, live meeting support, and any other question the user asks. "
            "If the user asks who you are, explain that you are Opencluely, an AI-powered meeting assistant. "
            f"Reply in {language}. "
            "Be practical, clear, and helpful. "
            "Use the transcript, notes, and screen summary when they are relevant, but answer normally when the question is broader than the meeting."
        )

    def _build_local_answer(self, user_prompt: str) -> str:
        transcript = self._transcript_store.recent_transcript_text()
        notes = self._state.notes[-1].body if self._state.notes else "No notes yet."
        screen = self._state.screen_context.summary if self._state.screen_context else "No screen context."
        return (
            f"Offline mode.\n"
            f"Prompt: {user_prompt}\n"
            f"Recent transcript: {transcript or 'No transcript yet.'}\n"
            f"Notes: {notes}\n"
            f"Screen: {screen}"
        )

    def _restore_live_mode(self) -> None:
        self._state.error_message = ""
        if self._audio_capture.is_recording():
            self._set_mode(SessionMode.LISTENING, emit_state=False)
            return
        if self._state.mode != SessionMode.STOPPED:
            self._set_mode(SessionMode.IDLE, emit_state=False)
        self.state_changed.emit(self._state)

    def _set_mode(self, mode: SessionMode, emit_state: bool = True) -> None:
        self._state.mode = mode
        if emit_state:
            self.state_changed.emit(self._state)
