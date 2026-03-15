"""Compatibility wrapper for the new floating bar UI."""

from __future__ import annotations

from .floating_bar import FloatingBar


class LiveBar(FloatingBar):
    """Expose the new floating bar through the existing ui.live_bar path."""

    def __init__(self, session_context: dict | None = None):
        super().__init__()
        self.session_context = session_context or {}
