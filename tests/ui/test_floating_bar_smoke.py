from __future__ import annotations

import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from PySide6.QtWidgets import QApplication

from ui.floating_bar import FloatingBar
from ui.live_bar import LiveBar


class FloatingBarSmokeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_floating_bar_bootstraps_headless_without_autostart(self):
        bar = FloatingBar({"language": "pt-BR"}, autostart=False)
        try:
            self.assertFalse(bar._card.isHidden())
            self.assertEqual(bar._response_mode, "smart")
            self.assertEqual(bar._orchestrator.state.mode.value, "idle")
        finally:
            bar.close()

    def test_options_menu_exposes_provider_and_audio_sections(self):
        bar = FloatingBar({"language": "pt-BR"}, autostart=False)
        try:
            menu = bar._build_menu()
            labels = [action.text() for action in menu.actions()]
            self.assertIn("Transcription provider", labels)
            self.assertIn("Assistant provider", labels)
            self.assertIn("Gemini chat model", labels)
            self.assertIn("Audio source", labels)
            self.assertIn("Capture screen now", labels)
        finally:
            bar.close()

    def test_options_menu_hides_local_provider_from_transcription_choices(self):
        bar = FloatingBar({"language": "pt-BR"}, autostart=False)
        try:
            menu = bar._build_menu()
            stt_action = next(action for action in menu.actions() if action.text() == "Transcription provider")
            stt_menu = stt_action.menu()
            labels = [action.text() for action in stt_menu.actions()]
            self.assertNotIn("Local faster-whisper", labels)
            self.assertNotIn("Local", labels)
        finally:
            bar.close()

    def test_live_bar_still_forwards_session_context_to_floating_bar(self):
        with patch("ui.live_bar.FloatingBar.__init__", return_value=None) as floating_bar_init:
            bar = LiveBar({"language": "pt-BR"})

        floating_bar_init.assert_called_once_with(session_context={"language": "pt-BR"})
        self.assertEqual(bar.session_context["language"], "pt-BR")


if __name__ == "__main__":
    unittest.main()
