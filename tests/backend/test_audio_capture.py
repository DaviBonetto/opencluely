from __future__ import annotations

from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


class AudioCaptureSelectionTest(unittest.TestCase):
    def test_auto_prefers_mixed_when_microphone_and_loopback_exist(self) -> None:
        from backend.audio_capture.capture import AudioCapture
        from backend.contracts import AudioSource

        capture = AudioCapture(source=AudioSource.AUTO)
        capture._mic_info = {"name": "Mic"}
        capture._sys_info = {"name": "Loopback"}

        self.assertEqual(capture._resolve_selected_source(), AudioSource.MIXED)

    def test_runtime_auto_prefers_mixed_when_both_streams_are_open(self) -> None:
        from backend.audio_capture.capture import AudioCapture
        from backend.contracts import AudioSource

        capture = AudioCapture(source=AudioSource.AUTO)
        capture._mic_stream = object()
        capture._sys_stream = object()

        self.assertEqual(capture._resolve_runtime_source(), AudioSource.MIXED)
