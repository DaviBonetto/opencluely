"""Screenshot capture and optional temporary persistence."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
import uuid

from runtime.paths import get_screens_dir


try:
    from PIL import ImageGrab

    PIL_CAPTURE_AVAILABLE = True
except ImportError:
    PIL_CAPTURE_AVAILABLE = False
    ImageGrab = None


class ScreenCaptureService:
    def __init__(self):
        self._temporary_files: list[Path] = []

    @property
    def is_available(self) -> bool:
        return PIL_CAPTURE_AVAILABLE

    def capture(self, persist: bool) -> tuple[object, str | None]:
        if not PIL_CAPTURE_AVAILABLE:
            raise RuntimeError("Pillow ImageGrab is unavailable.")

        image = ImageGrab.grab()
        if not persist:
            return image, None

        screens_dir = get_screens_dir()
        filename = f"screen_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}.png"
        output = screens_dir / filename
        image.save(output)
        return image, str(output)

    def clear_temporary_files(self) -> None:
        for path in self._temporary_files:
            try:
                path.unlink(missing_ok=True)
            except Exception:
                pass
        self._temporary_files.clear()
