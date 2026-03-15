from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


class NotesEngineTest(unittest.TestCase):
    def test_local_notes_extracts_actions_and_decisions(self) -> None:
        from backend.contracts import AudioSource, SttProviderKind, TranscriptSegment
        from backend.services.notes_engine import LocalNotesEngine

        segments = [
            TranscriptSegment(
                id="1",
                text="We decided to send the updated proposal tomorrow morning.",
                start_ms=0,
                end_ms=1000,
                created_at=datetime.now(UTC),
                is_partial=False,
                source=AudioSource.MICROPHONE,
                provider=SttProviderKind.GROQ,
            ),
            TranscriptSegment(
                id="2",
                text="Please follow up with finance and confirm the discount.",
                start_ms=1100,
                end_ms=2200,
                created_at=datetime.now(UTC),
                is_partial=False,
                source=AudioSource.MICROPHONE,
                provider=SttProviderKind.GROQ,
            ),
        ]

        notes = LocalNotesEngine().build_snapshot(segments)

        self.assertIn("Decisions", notes.body)
        self.assertIn("Action items", notes.body)
        self.assertIn("updated proposal", notes.body)
        self.assertIn("follow up with finance", notes.body.lower())


if __name__ == "__main__":
    unittest.main()
