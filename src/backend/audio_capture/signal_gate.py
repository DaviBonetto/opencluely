"""Small PCM16 helpers used to suppress silence-driven hallucinations."""

from __future__ import annotations


def pcm16_signal_stats(audio_bytes: bytes) -> tuple[int, float, float]:
    samples = memoryview(audio_bytes).cast("h")
    if not samples:
        return 0, 0.0, 0.0

    peak = 0
    total = 0
    active = 0
    for sample in samples:
        value = abs(int(sample))
        total += value
        if value > peak:
            peak = value
        if value >= 400:
            active += 1

    length = len(samples)
    mean_abs = total / length
    activity_ratio = active / length
    return peak, mean_abs, activity_ratio


def has_spoken_audio(
    audio_bytes: bytes,
    *,
    peak_threshold: int = 900,
    mean_abs_threshold: float = 75.0,
    activity_ratio_threshold: float = 0.015,
) -> bool:
    peak, mean_abs, activity_ratio = pcm16_signal_stats(audio_bytes)
    return peak >= peak_threshold and (
        mean_abs >= mean_abs_threshold or activity_ratio >= activity_ratio_threshold
    )


def looks_like_silence(audio_bytes: bytes) -> bool:
    return not has_spoken_audio(audio_bytes)
