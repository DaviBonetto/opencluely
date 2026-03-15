"""Prompt composition helpers for contextual chat replies."""

from __future__ import annotations

from ..contracts import NoteSnapshot, ScreenContext, TranscriptSegment


def build_assist_prompt(
    user_prompt: str,
    transcript_segments: list[TranscriptSegment],
    notes: list[NoteSnapshot],
    screen_context: ScreenContext | None,
    language: str,
) -> str:
    transcript_text = "\n".join(
        f"- [{segment.start_ms}ms-{segment.end_ms}ms] {segment.text}"
        for segment in transcript_segments[-8:]
        if segment.text.strip()
    )
    notes_text = notes[-1].body if notes else "No notes yet."
    screen_text = screen_context.summary if screen_context else "No screen context."

    return (
        f"Language: {language}\n"
        f"User request: {user_prompt}\n\n"
        f"Recent transcript:\n{transcript_text or '- No transcript yet.'}\n\n"
        f"Current notes:\n{notes_text}\n\n"
        f"Screen context:\n{screen_text}\n\n"
        "Answer clearly and helpfully. "
        "Be concise by default, but if the user asks for explanation, explain well. "
        "When the meeting context matters, make the reply practical and easy to say out loud."
    ).strip()
