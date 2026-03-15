"""Incremental local notes synthesis used when remote summarization is unavailable."""

from __future__ import annotations

from datetime import UTC, datetime

from ..contracts import NoteSnapshot, TranscriptSegment


class LocalNotesEngine:
    def build_snapshot(self, segments: list[TranscriptSegment]) -> NoteSnapshot:
        decisions: list[str] = []
        actions: list[str] = []
        highlights: list[str] = []

        for segment in segments[-12:]:
            text = segment.text.strip()
            lower = text.lower()
            if not text:
                continue
            if any(token in lower for token in ("decided", "decision", "vamos", "we will")):
                decisions.append(text)
            elif any(
                token in lower
                for token in (
                    "please",
                    "follow up",
                    "action item",
                    "next step",
                    "preciso",
                    "vamos enviar",
                )
            ):
                actions.append(text)
            else:
                highlights.append(text)

        body = _render_notes(decisions, actions, highlights)
        return NoteSnapshot(
            body=body,
            created_at=datetime.now(UTC),
            source_summary=f"{len(segments)} transcript segments",
        )


def _render_notes(decisions: list[str], actions: list[str], highlights: list[str]) -> str:
    lines = ["Decisions"]
    lines.extend(_as_bullets(decisions) or ["- No explicit decisions yet."])
    lines.append("")
    lines.append("Action items")
    lines.extend(_as_bullets(actions) or ["- No action items yet."])
    if highlights:
        lines.append("")
        lines.append("Highlights")
        lines.extend(_as_bullets(highlights[:3]))
    return "\n".join(lines).strip()


def _as_bullets(items: list[str]) -> list[str]:
    return [f"- {item}" for item in items]
