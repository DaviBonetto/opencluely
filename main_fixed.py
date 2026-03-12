#!/usr/bin/env python3

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from brand import APP_LOG_PREFIX, APP_NAME
from storage_paths import build_log_file


LOG_FILE = build_log_file(APP_LOG_PREFIX)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)

logger = logging.getLogger("main_fixed")


def check_environment() -> bool:
    """Validate the minimal environment used by the alternate launcher."""
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
        logger.warning("GROQ_API_KEY is missing; AI features will be limited")

    return True


def main() -> int:
    print()
    print("=" * 50)
    print(f"  {APP_NAME} - Alternate Launcher")
    print("=" * 50)
    print()

    logger.info("=== %s alternate launcher starting ===", APP_NAME)
    logger.info("Log file: %s", LOG_FILE)

    try:
        if not check_environment():
            print("\nEnvironment check failed. Review the log file for details.")
            return 1

        from PyQt5.QtCore import Qt
        from PyQt5.QtWidgets import QApplication
        from ui.horizontal_overlay import HorizontalOverlay
        from ui.session_setup import SessionSetupWindow

        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

        app = QApplication(sys.argv)
        app.setApplicationName(APP_NAME)
        app.setApplicationVersion("0.1.0")
        app.setStyle("Fusion")
        app.setQuitOnLastWindowClosed(False)

        def on_session_started(session_context: dict) -> None:
            active_brief = session_context.get("brief_name") or session_context.get("template_name")
            logger.info("Session started with brief: %s", active_brief)
            overlay = HorizontalOverlay()
            if hasattr(overlay, "set_session_data"):
                overlay.set_session_data(session_context)
            overlay.show()
            app.overlay = overlay

        session_setup = SessionSetupWindow()
        session_setup.session_started.connect(on_session_started)
        session_setup.show()

        return app.exec_()

    except Exception as exc:
        logger.error("Fatal startup error", exc_info=True)
        print(f"\nFatal error: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
