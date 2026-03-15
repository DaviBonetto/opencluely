"""Desktop entrypoint for Opencluely."""

from __future__ import annotations

import logging
import sys
from pathlib import Path


sys.dont_write_bytecode = True

PROJECT_ROOT = Path(__file__).resolve().parent
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from runtime.paths import build_log_file, get_app_home


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
    """Load bundled brand fonts so the floating bar uses Inter when available."""
    try:
        from PySide6.QtGui import QFont, QFontDatabase
    except ImportError:
        logger.warning("PySide6 font helpers are unavailable; skipping bundled font loading")
        return

    font_path = PROJECT_ROOT / "assets" / "fonts" / "InterVariable.ttf"
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
    """Validate the minimal runtime required for the floating bar."""
    logger.info("Checking runtime environment")
    logger.info("Python: %s", sys.version)

    try:
        from PySide6 import __version__ as pyside_version
        from PySide6.QtCore import qVersion

        logger.info("PySide6: %s", pyside_version)
        logger.info("Qt: %s", qVersion())
    except ImportError:
        logger.error("PySide6 is not installed. Run: pip install -r requirements.txt")
        return False

    return True


def main() -> int:
    """Create the Qt app and launch the floating bar."""
    print()
    print("=" * 50)
    print("  Opencluely")
    print("=" * 50)
    print()

    logger.info("=== Opencluely starting ===")
    logger.info("Runtime home: %s", get_app_home())
    logger.info("Log file: %s", LOG_FILE)

    try:
        if not check_environment():
            print("\nEnvironment check failed. Review the log file for details.")
            return 1

        from PySide6.QtCore import Qt
        from PySide6.QtWidgets import QApplication
        from ui.live_bar import LiveBar

        if hasattr(Qt.ApplicationAttribute, "AA_UseHighDpiPixmaps"):
            QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)

        app = QApplication(sys.argv)
        app.setStyle("Fusion")
        app.setApplicationName("Opencluely")
        app.setApplicationVersion("1.0.0")
        app.setQuitOnLastWindowClosed(True)
        load_brand_fonts(app)

        overlay = LiveBar(
            {
                "profile_name": "Before Meeting",
                "brief_name": "General",
                "system_instructions": "",
                "user_context": "",
                "language": "pt-BR",
            }
        )
        screen = app.primaryScreen().availableGeometry()
        overlay.move(
            screen.x() + (screen.width() - overlay.width()) // 2,
            screen.y() + 80,
        )
        overlay.show()
        app.overlay = overlay

        logger.info("Entering Qt event loop")
        return app.exec()

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
