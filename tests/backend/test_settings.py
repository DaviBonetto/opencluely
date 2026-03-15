from __future__ import annotations

import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


class BackendSettingsTest(unittest.TestCase):
    def test_defaults_prioritize_free_tier_first_behavior(self) -> None:
        from backend.settings import (
            AppBackendSettings,
            AssistProviderKind,
            AudioSource,
            SttProviderKind,
        )

        with patch.dict(os.environ, {}, clear=True):
            settings = AppBackendSettings.from_env()

        self.assertEqual(settings.stt_provider, SttProviderKind.AUTO)
        self.assertEqual(settings.assist_provider, AssistProviderKind.AUTO)
        self.assertEqual(settings.audio_source, AudioSource.AUTO)
        self.assertEqual(settings.groq_audio_model, "whisper-large-v3-turbo")
        self.assertEqual(settings.gemini_assist_model, "gemini-3.1-flash-lite-preview")
        self.assertTrue(settings.persist_session_data)
        self.assertFalse(settings.incognito)

    def test_key_detection_ignores_placeholder_values(self) -> None:
        from backend.settings import AppBackendSettings

        env = {
            "GROQ_API_KEY": "gsk_...",
            "GEMINI_API_KEY": "replace-me",
            "GEMINI_ASSIST_API_KEY": "your-key-here",
        }
        with patch.dict(os.environ, env, clear=True):
            settings = AppBackendSettings.from_env()

        self.assertFalse(settings.has_groq_key)
        self.assertFalse(settings.has_gemini_key)
        self.assertFalse(settings.has_gemini_assist_key)


if __name__ == "__main__":
    unittest.main()
