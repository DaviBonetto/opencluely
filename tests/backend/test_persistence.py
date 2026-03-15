from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


class PersistenceTest(unittest.TestCase):
    def test_incognito_redacts_sensitive_payloads(self) -> None:
        from backend.contracts import (
            AudioSource,
            ChatTurn,
            NoteSnapshot,
            SessionMode,
            SessionState,
            SttProviderKind,
            TranscriptSegment,
        )
        from backend.session.persistence import SessionPersistence

        state = SessionState(
            mode=SessionMode.STOPPED,
            stt_provider=SttProviderKind.GROQ,
            audio_source=AudioSource.MICROPHONE,
            started_at=datetime.now(UTC),
            transcript_segments=[
                TranscriptSegment(
                    id="1",
                    text="secret meeting content",
                    start_ms=0,
                    end_ms=1000,
                    created_at=datetime.now(UTC),
                    is_partial=False,
                    source=AudioSource.MICROPHONE,
                    provider=SttProviderKind.GROQ,
                )
            ],
            chat_history=[
                ChatTurn(
                    id="turn-1",
                    role="assistant",
                    text="confidential answer",
                    created_at=datetime.now(UTC),
                )
            ],
            notes=[NoteSnapshot(body="- confidential notes", created_at=datetime.now(UTC))],
            is_incognito=True,
        )

        with tempfile.TemporaryDirectory() as tmp:
            persistence = SessionPersistence(base_dir=Path(tmp))
            output = persistence.save_state(state)
            payload = output.read_text(encoding="utf-8")

        self.assertIn('"is_incognito": true', payload)
        self.assertNotIn("secret meeting content", payload)
        self.assertNotIn("confidential answer", payload)
        self.assertNotIn("confidential notes", payload)


if __name__ == "__main__":
    unittest.main()
