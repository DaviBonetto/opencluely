from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


class SessionOrchestratorTest(unittest.TestCase):
    def _make_settings(self):
        from backend.settings import AppBackendSettings

        settings = AppBackendSettings.from_env()
        settings.persist_session_data = False
        settings.persist_screenshots = False
        return settings

    def test_preferred_provider_and_audio_source_can_be_changed_without_starting_capture(self):
        from backend.contracts import AudioSource, SttProviderKind
        from backend.session.orchestrator import SessionOrchestrator

        orchestrator = SessionOrchestrator(settings=self._make_settings())
        try:
            orchestrator.set_stt_provider(SttProviderKind.GEMINI)
            orchestrator.set_audio_source(AudioSource.MICROPHONE)

            self.assertEqual(orchestrator.desired_stt_provider, SttProviderKind.GEMINI)
            self.assertEqual(orchestrator.requested_audio_source, AudioSource.MICROPHONE)
            self.assertEqual(orchestrator.state.audio_source, AudioSource.MICROPHONE)
        finally:
            orchestrator.close_session()

    def test_gemini_chat_model_can_be_changed_without_starting_capture(self):
        from backend.session.orchestrator import SessionOrchestrator

        orchestrator = SessionOrchestrator(settings=self._make_settings())
        try:
            orchestrator.set_gemini_assist_model("gemini-2.5-flash")

            self.assertEqual(orchestrator.current_gemini_assist_model, "gemini-2.5-flash")
            self.assertEqual(orchestrator._gemini_assist._model, "gemini-2.5-flash")
        finally:
            orchestrator.close_session()

    def test_clear_session_resets_transcript_chat_notes_and_screen_context(self):
        from backend.contracts import (
            AudioSource,
            ChatTurn,
            NoteSnapshot,
            ScreenContext,
            SttProviderKind,
            TranscriptSegment,
        )
        from backend.session.orchestrator import SessionOrchestrator

        orchestrator = SessionOrchestrator(settings=self._make_settings())
        now = datetime.now(UTC)
        segment = TranscriptSegment(
            id="seg-1",
            text="Testing the rolling transcript.",
            start_ms=0,
            end_ms=1200,
            created_at=now,
            is_partial=False,
            source=AudioSource.MICROPHONE,
            provider=SttProviderKind.LOCAL,
        )
        try:
            orchestrator._transcript_store.add_segment(segment)
            orchestrator.state.transcript_segments = orchestrator._transcript_store.segments
            orchestrator.state.chat_history.append(
                ChatTurn(id="chat-1", role="user", text="Hello", created_at=now)
            )
            orchestrator.state.notes.append(
                NoteSnapshot(body="- Action item", created_at=now)
            )
            orchestrator.state.screen_context = ScreenContext(
                summary="A CRM dashboard with open deals.",
                captured_at=now,
                provider="gemini",
                is_active=True,
            )

            orchestrator.clear_session()

            self.assertEqual(orchestrator.state.transcript_segments, [])
            self.assertEqual(orchestrator.state.chat_history, [])
            self.assertEqual(orchestrator.state.notes, [])
            self.assertIsNone(orchestrator.state.screen_context)
            self.assertEqual(orchestrator._transcript_store.segments, [])
        finally:
            orchestrator.close_session()

    def test_start_session_without_cloud_provider_surfaces_explicit_error(self):
        from backend.contracts import SessionMode
        from backend.session.orchestrator import SessionOrchestrator

        settings = self._make_settings()
        settings.groq_api_key = ""
        settings.gemini_api_key = ""
        orchestrator = SessionOrchestrator(settings=settings)
        errors = []
        orchestrator.error_occurred.connect(errors.append)
        try:
            orchestrator.start_session()

            self.assertEqual(orchestrator.state.mode, SessionMode.ERROR)
            self.assertTrue(errors)
            self.assertIn("No cloud transcription provider is available", errors[-1])
        finally:
            orchestrator.close_session()


if __name__ == "__main__":
    unittest.main()
