"""Rolling transcript state with lightweight overlap deduplication."""

from __future__ import annotations

from collections import deque

from ..contracts import TranscriptSegment


class TranscriptStore:
    def __init__(self, max_segments: int = 120):
        self._segments: deque[TranscriptSegment] = deque(maxlen=max_segments)

    @property
    def segments(self) -> list[TranscriptSegment]:
        return list(self._segments)

    def add_segment(self, segment: TranscriptSegment) -> None:
        self._segments.append(segment)

    def recent_segments(self, limit: int = 8) -> list[TranscriptSegment]:
        if limit <= 0:
            return []
        return list(self._segments)[-limit:]

    def recent_transcript_text(self, limit: int = 8) -> str:
        merged = ""
        for segment in self.recent_segments(limit):
            text = segment.text.strip()
            if not text:
                continue
            merged = _merge_with_overlap(merged, text)
        return merged.strip()


def _merge_with_overlap(existing: str, incoming: str) -> str:
    if not existing:
        return incoming

    if incoming in existing:
        return existing

    if existing in incoming:
        return incoming

    existing_words = existing.split()
    incoming_words = incoming.split()
    max_overlap = min(len(existing_words), len(incoming_words))

    for size in range(max_overlap, 0, -1):
        if existing_words[-size:] == incoming_words[:size]:
            merged_words = existing_words + incoming_words[size:]
            return " ".join(merged_words)

    return f"{existing} {incoming}".strip()
