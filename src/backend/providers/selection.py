"""Provider selection rules used by the session orchestrator."""

from __future__ import annotations

from dataclasses import dataclass

from ..contracts import AssistProviderKind, SttProviderKind


@dataclass(slots=True)
class ProviderAvailability:
    groq_stt: bool = False
    gemini_live: bool = False
    local_stt: bool = False
    groq_assist: bool = False
    gemini_assist: bool = False
    groq_vision: bool = False
    gemini_vision: bool = False


def resolve_stt_provider(
    desired: SttProviderKind,
    availability: ProviderAvailability,
) -> SttProviderKind:
    if desired == SttProviderKind.AUTO:
        if availability.gemini_live:
            return SttProviderKind.GEMINI
        if availability.groq_stt:
            return SttProviderKind.GROQ
        return SttProviderKind.AUTO

    if desired == SttProviderKind.GROQ and availability.groq_stt:
        return desired
    if desired == SttProviderKind.GEMINI and availability.gemini_live:
        return desired
    if desired == SttProviderKind.LOCAL and availability.local_stt:
        return desired

    return resolve_stt_provider(SttProviderKind.AUTO, availability)


def resolve_assist_provider(
    desired: AssistProviderKind,
    availability: ProviderAvailability,
) -> AssistProviderKind:
    if desired == AssistProviderKind.AUTO:
        if availability.gemini_assist:
            return AssistProviderKind.GEMINI
        if availability.groq_assist:
            return AssistProviderKind.GROQ
        return AssistProviderKind.AUTO

    if desired == AssistProviderKind.GEMINI and availability.gemini_assist:
        return desired
    if desired == AssistProviderKind.GROQ and availability.groq_assist:
        return desired
    if desired == AssistProviderKind.LOCAL and availability.local_stt:
        return desired

    return resolve_assist_provider(AssistProviderKind.AUTO, availability)
