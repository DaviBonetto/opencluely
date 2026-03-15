from __future__ import annotations

from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


class SignalGateTest(unittest.TestCase):
    def test_zeroed_pcm_is_silence(self) -> None:
        from backend.audio_capture.signal_gate import looks_like_silence

        self.assertTrue(looks_like_silence(b"\x00\x00" * 1600))

    def test_generated_speech_like_pcm_is_not_silence(self) -> None:
        from backend.audio_capture.signal_gate import has_spoken_audio

        path = ROOT / "tmp" / "opencluely_smoke_16k.wav"
        if not path.exists():
            self.skipTest("synthetic smoke wav is unavailable")

        import wave

        with wave.open(str(path), "rb") as wav_file:
            audio_bytes = wav_file.readframes(wav_file.getnframes())

        self.assertTrue(has_spoken_audio(audio_bytes))

