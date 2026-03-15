from __future__ import annotations

import unittest
from datetime import UTC, datetime
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


class BackendContractsTest(unittest.TestCase):
    def test_session_models_capture_expected_defaults(self) -> None:
        from backend.contracts import (
            AudioSource,
            ChatTurn,
            ProviderHealth,
            ScreenContext,
            SessionMode,
            SessionState,
            SttProviderKind,
            TranscriptSegment,
        )

        started_at = datetime.now(UTC)
        segment = TranscriptSegment(
            id="seg-1",
            text="hello world",
            start_ms=1000,
            end_ms=2100,
            created_at=started_at,
            is_partial=False,
            source=AudioSource.MICROPHONE,
            provider=SttProviderKind.GROQ,
        )
        turn = ChatTurn(
            id="turn-1",
            role="user",
            text="What should I say?",
            created_at=started_at,
        )
        screen = ScreenContext(
            summary="Dashboard with a failed payment banner.",
            captured_at=started_at,
            provider="gemini",
            is_active=True,
        )
        health = ProviderHealth(
            name="groq",
            available=True,
            configured=True,
            detail="ready",
        )
        state = SessionState(
            mode=SessionMode.IDLE,
            stt_provider=SttProviderKind.AUTO,
            audio_source=AudioSource.AUTO,
            started_at=started_at,
            transcript_segments=[segment],
            chat_history=[turn],
            screen_context=screen,
            provider_health={"groq": health},
        )

        self.assertEqual(state.mode, SessionMode.IDLE)
        self.assertEqual(state.stt_provider, SttProviderKind.AUTO)
        self.assertEqual(state.audio_source, AudioSource.AUTO)
        self.assertEqual(state.transcript_segments[0].text, "hello world")
        self.assertEqual(state.chat_history[0].text, "What should I say?")
        self.assertTrue(state.screen_context.is_active)
        self.assertTrue(state.provider_health["groq"].available)


if __name__ == "__main__":
    unittest.main()
