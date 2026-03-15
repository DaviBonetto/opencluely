from __future__ import annotations

from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


class ProviderStrategyTest(unittest.TestCase):
    def test_stt_auto_prefers_gemini_then_groq_then_no_local_fallback(self) -> None:
        from backend.contracts import SttProviderKind
        from backend.providers.selection import ProviderAvailability, resolve_stt_provider

        self.assertEqual(
            resolve_stt_provider(
                SttProviderKind.AUTO,
                ProviderAvailability(groq_stt=True, gemini_live=True, local_stt=True),
            ),
            SttProviderKind.GEMINI,
        )
        self.assertEqual(
            resolve_stt_provider(
                SttProviderKind.AUTO,
                ProviderAvailability(groq_stt=True, gemini_live=False, local_stt=True),
            ),
            SttProviderKind.GROQ,
        )
        self.assertEqual(
            resolve_stt_provider(
                SttProviderKind.AUTO,
                ProviderAvailability(groq_stt=False, gemini_live=False, local_stt=True),
            ),
            SttProviderKind.AUTO,
        )

    def test_assist_auto_prefers_gemini_then_groq_then_no_local_fallback(self) -> None:
        from backend.contracts import AssistProviderKind
        from backend.providers.selection import ProviderAvailability, resolve_assist_provider

        self.assertEqual(
            resolve_assist_provider(
                AssistProviderKind.AUTO,
                ProviderAvailability(groq_assist=True, gemini_assist=True, local_stt=True),
            ),
            AssistProviderKind.GEMINI,
        )
        self.assertEqual(
            resolve_assist_provider(
                AssistProviderKind.AUTO,
                ProviderAvailability(groq_assist=True, gemini_assist=False, local_stt=True),
            ),
            AssistProviderKind.GROQ,
        )
        self.assertEqual(
            resolve_assist_provider(
                AssistProviderKind.AUTO,
                ProviderAvailability(groq_assist=False, gemini_assist=False, local_stt=True),
            ),
            AssistProviderKind.AUTO,
        )


if __name__ == "__main__":
    unittest.main()
