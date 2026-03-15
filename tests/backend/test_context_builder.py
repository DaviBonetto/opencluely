from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


class ContextBuilderTest(unittest.TestCase):
    def test_context_builder_uses_recent_transcript_notes_and_screen(self) -> None:
        from backend.contracts import AudioSource, NoteSnapshot, ScreenContext, SttProviderKind, TranscriptSegment
        from backend.session.context_builder import build_assist_prompt

        segments = [
            TranscriptSegment(
                id="1",
                text="The client is pushing back on pricing.",
                start_ms=0,
                end_ms=1000,
                created_at=datetime.now(UTC),
                is_partial=False,
                source=AudioSource.MICROPHONE,
                provider=SttProviderKind.GROQ,
            )
        ]
        notes = [
            NoteSnapshot(
                body="- Decision: hold firm on annual contract pricing.",
                created_at=datetime.now(UTC),
            )
        ]
        screen = ScreenContext(
            summary="Pricing slide with annual and monthly options.",
            captured_at=datetime.now(UTC),
            provider="gemini",
            is_active=True,
        )

        prompt = build_assist_prompt(
            user_prompt="What should I answer?",
            transcript_segments=segments,
            notes=notes,
            screen_context=screen,
            language="pt-BR",
        )

        self.assertIn("What should I answer?", prompt)
        self.assertIn("pricing", prompt.lower())
        self.assertIn("annual contract pricing", prompt.lower())
        self.assertIn("Pricing slide", prompt)


if __name__ == "__main__":
    unittest.main()
