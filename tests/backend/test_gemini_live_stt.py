from __future__ import annotations

from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


class GeminiLiveTranscriberTest(unittest.TestCase):
    def test_merge_transcription_text_handles_fragmented_words(self) -> None:
        from backend.providers.gemini_live_stt import _merge_transcription_text

        merged = ""
        for fragment in ("Tra", "ns", "krip", "tion", "test Hello World."):
            merged = _merge_transcription_text(merged, fragment)

        self.assertEqual(merged, "Transkription test Hello World.")

    def test_buffered_turn_is_emitted_once_turn_complete_is_seen(self) -> None:
        from backend.contracts import AudioSource, SttProviderKind
        from backend.providers.gemini_live_stt import GeminiLiveTranscriber, _AudioFrame

        transcriber = GeminiLiveTranscriber(api_key="test-key")
        segments = []
        partials = []
        transcriber.segment_ready.connect(segments.append)
        transcriber.partial_text.connect(partials.append)

        transcriber._latest_frame = _AudioFrame(
            source=AudioSource.MICROPHONE,
            start_ms=120,
            end_ms=1820,
        )
        transcriber._buffered_input_text = "Opencluely transcription test"
        transcriber._turn_complete_seen = True

        transcriber._emit_buffered_segment_if_ready()

        self.assertEqual(len(segments), 1)
        self.assertEqual(segments[0].text, "Opencluely transcription test")
        self.assertEqual(segments[0].source, AudioSource.MICROPHONE)
        self.assertEqual(segments[0].provider, SttProviderKind.GEMINI)
        self.assertIn("", partials)

    def test_silent_frame_triggers_idle_flush_after_recent_speech(self) -> None:
        from backend.contracts import AudioSource
        from backend.providers.gemini_live_stt import GeminiLiveTranscriber

        transcriber = GeminiLiveTranscriber(api_key="test-key")
        transcriber._last_voiced_end_ms = 1000

        silent_frame = (b"\x00\x00" * 1600)
        transcriber.submit_frame(silent_frame, 1000, 2000, AudioSource.MICROPHONE)

        queued = transcriber._queue.get_nowait()
        self.assertTrue(queued.audio_stream_end)


if __name__ == "__main__":
    unittest.main()
