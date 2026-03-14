"""Desktop entrypoint for Opencluely."""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from storage_paths import build_log_file


LOG_FILE = build_log_file("opencluely")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)

logger = logging.getLogger("main")


def load_brand_fonts(app) -> None:
    """Load bundled brand fonts so the wordmark stays stable across machines."""
    try:
        from PyQt5.QtGui import QFont, QFontDatabase
    except ImportError:
        logger.warning("PyQt5 font helpers are unavailable; skipping bundled font loading")
        return

    fonts_dir = PROJECT_ROOT / "assets" / "fonts"
    font_path = fonts_dir / "InterVariable.ttf"
    font_family = "Inter"

    if font_path.exists():
        font_id = QFontDatabase.addApplicationFont(str(font_path))
        if font_id != -1:
            families = QFontDatabase.applicationFontFamilies(font_id)
            if families:
                font_family = families[0]
                logger.info("Loaded bundled font family: %s", font_family)
        else:
            logger.warning("Failed to register bundled font: %s", font_path)
    else:
        logger.warning("Bundled Inter font not found at %s", font_path)

    app.setProperty("opencluely_wordmark_family", font_family)
    app.setProperty("opencluely_ui_family", font_family)
    app.setFont(QFont(font_family, 10))


def check_environment() -> bool:
    """Validate a minimal runtime environment before booting the UI."""
    logger.info("Checking runtime environment")
    logger.info("Python: %s", sys.version)

    try:
        from PyQt5.QtCore import QT_VERSION_STR

        logger.info("PyQt5: %s", QT_VERSION_STR)
    except ImportError:
        logger.error("PyQt5 is not installed. Run: pip install -r requirements.txt")
        return False

    api_key = os.environ.get("GROQ_API_KEY", "")
    if api_key.startswith("gsk_"):
        logger.info("GROQ_API_KEY is configured")
    else:
        logger.warning(
            "GROQ_API_KEY is missing; transcription, Assist, and Screen Analysis will be disabled"
        )

    try:
        import pytesseract

        pytesseract.get_tesseract_version()
        logger.info("Tesseract is available")
    except Exception:
        logger.warning("Tesseract is not available; screen OCR will be disabled")

    return True


def main() -> int:
    """Create the Qt app and launch the Live Bar immediately."""
    print()
    print("=" * 50)
    print("  Opencluely")
    print("=" * 50)
    print()

    logger.info("=== Opencluely starting ===")
    logger.info("Log file: %s", LOG_FILE)

    try:
        if not check_environment():
            print("\nEnvironment check failed. Review the log file for details.")
            return 1

        from PyQt5.QtCore import Qt
        from PyQt5.QtWidgets import QApplication
        from ui.live_bar import LiveBar

        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

        app = QApplication(sys.argv)
        app.setApplicationName("Opencluely")
        app.setApplicationVersion("1.0.0")
        app.setQuitOnLastWindowClosed(True)
        load_brand_fonts(app)
        session_context = {
            "profile_name": "Before Meeting",
            "brief_name": "General",
            "system_instructions": "",
            "user_context": "",
            "language": "pt-BR",
        }

        overlay = LiveBar(session_context)
        overlay.show()
        app.overlay = overlay

        logger.info("Entering Qt event loop")
        return app.exec_()

    except ImportError as exc:
        logger.critical("Import error during bootstrap", exc_info=True)
        print(f"\nMissing module: {exc}")
        print("Run: pip install -r requirements.txt")
        return 1
    except Exception as exc:
        logger.critical("Fatal startup error", exc_info=True)
        print(f"\nFatal error: {exc}")
        print(f"Review the log for details: {LOG_FILE}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
