from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


class TranscriptStoreTest(unittest.TestCase):
    def test_store_deduplicates_overlapping_segments(self) -> None:
        from backend.contracts import AudioSource, SttProviderKind, TranscriptSegment
        from backend.services.transcript_store import TranscriptStore

        created_at = datetime.now(UTC)
        store = TranscriptStore(max_segments=10)
        first = TranscriptSegment(
            id="seg-1",
            text="hello everyone thanks for joining",
            start_ms=0,
            end_ms=3000,
            created_at=created_at,
            is_partial=False,
            source=AudioSource.MICROPHONE,
            provider=SttProviderKind.GROQ,
        )
        second = TranscriptSegment(
            id="seg-2",
            text="thanks for joining the meeting today",
            start_ms=2500,
            end_ms=5000,
            created_at=created_at,
            is_partial=False,
            source=AudioSource.MICROPHONE,
            provider=SttProviderKind.GROQ,
        )

        store.add_segment(first)
        store.add_segment(second)

        self.assertEqual(len(store.segments), 2)
        self.assertEqual(
            store.recent_transcript_text(),
            "hello everyone thanks for joining the meeting today",
        )


if __name__ == "__main__":
    unittest.main()
