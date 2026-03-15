"""Typed backend settings and compatibility exports for optional providers."""

from __future__ import annotations

from dataclasses import dataclass
import logging
import os

from .contracts import AssistProviderKind, AudioSource, SttProviderKind


logger = logging.getLogger("backend.settings")


_PLACEHOLDER_PREFIXES = (
    "hf_...",
    "gsk_...",
    "your-",
    "replace-",
    "MY_",
)


def _get_env(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


def _get_bool_env(name: str, default: bool) -> bool:
    value = _get_env(name)
    if not value:
        return default
    return value.lower() in {"1", "true", "yes", "on"}


def _get_float_env(name: str, default: float) -> float:
    value = _get_env(name)
    if not value:
        return default
    return float(value)


def _get_int_env(name: str, default: int) -> int:
    value = _get_env(name)
    if not value:
        return default
    return int(value)


def _is_placeholder(value: str) -> bool:
    return not value or value.startswith(_PLACEHOLDER_PREFIXES)


@dataclass(slots=True)
class AppBackendSettings:
    stt_provider: SttProviderKind
    assist_provider: AssistProviderKind
    audio_source: AudioSource
    groq_api_key: str
    gemini_api_key: str
    gemini_assist_api_key: str
    groq_audio_model: str
    groq_assist_model: str
    groq_vision_model: str
    gemini_live_model: str
    gemini_assist_model: str
    gemini_vision_model: str
    request_timeout_seconds: float
    assist_temperature: float
    assist_max_tokens: int
    rate_limit_per_minute: int
    persist_session_data: bool
    persist_transcripts: bool
    persist_notes: bool
    persist_screenshots: bool
    incognito: bool
    screen_context_enabled: bool
    local_whisper_model_size: str

    @classmethod
    def from_env(cls) -> "AppBackendSettings":
        return cls(
            stt_provider=SttProviderKind(_get_env("OPENCLUELY_STT_PROVIDER", "auto").lower()),
            assist_provider=AssistProviderKind(
                _get_env("OPENCLUELY_ASSIST_PROVIDER", "auto").lower()
            ),
            audio_source=AudioSource(_get_env("OPENCLUELY_AUDIO_SOURCE", "auto").lower()),
            groq_api_key=_get_env("GROQ_API_KEY"),
            gemini_api_key=_get_env("GEMINI_API_KEY"),
            gemini_assist_api_key=_get_env("GEMINI_ASSIST_API_KEY", _get_env("GEMINI_API_KEY")),
            groq_audio_model=_get_env("GROQ_AUDIO_MODEL", "whisper-large-v3-turbo"),
            groq_assist_model=_get_env("GROQ_ASSIST_MODEL", "llama-3.3-70b-versatile"),
            groq_vision_model=_get_env(
                "GROQ_VISION_MODEL",
                "meta-llama/llama-4-scout-17b-16e-instruct",
            ),
            gemini_live_model=_get_env(
                "GEMINI_LIVE_MODEL",
                "gemini-2.5-flash-native-audio-preview-12-2025",
            ),
            gemini_assist_model=_get_env(
                "GEMINI_ASSIST_MODEL",
                "gemini-3.1-flash-lite-preview",
            ),
            gemini_vision_model=_get_env("GEMINI_VISION_MODEL", "gemini-2.0-flash"),
            request_timeout_seconds=_get_float_env("OPENCLUELY_REQUEST_TIMEOUT_SECONDS", 30.0),
            assist_temperature=_get_float_env("OPENCLUELY_ASSIST_TEMPERATURE", 0.3),
            assist_max_tokens=_get_int_env("OPENCLUELY_ASSIST_MAX_TOKENS", 400),
            rate_limit_per_minute=_get_int_env("OPENCLUELY_RATE_LIMIT_PER_MINUTE", 30),
            persist_session_data=_get_bool_env("OPENCLUELY_PERSIST_SESSION_DATA", True),
            persist_transcripts=_get_bool_env("OPENCLUELY_PERSIST_TRANSCRIPTS", True),
            persist_notes=_get_bool_env("OPENCLUELY_PERSIST_NOTES", True),
            persist_screenshots=_get_bool_env("OPENCLUELY_PERSIST_SCREENSHOTS", False),
            incognito=_get_bool_env("OPENCLUELY_INCOGNITO", False),
            screen_context_enabled=_get_bool_env("OPENCLUELY_SCREEN_CONTEXT_ENABLED", True),
            local_whisper_model_size=_get_env("OPENCLUELY_LOCAL_WHISPER_MODEL", "tiny"),
        )

    @property
    def has_groq_key(self) -> bool:
        return not _is_placeholder(self.groq_api_key)

    @property
    def has_gemini_live_key(self) -> bool:
        return not _is_placeholder(self.gemini_api_key)

    @property
    def has_gemini_assist_key(self) -> bool:
        return not _is_placeholder(self.gemini_assist_api_key)

    @property
    def has_gemini_key(self) -> bool:
        return self.has_gemini_live_key


SETTINGS = AppBackendSettings.from_env()


def reload_settings() -> AppBackendSettings:
    global SETTINGS
    SETTINGS = AppBackendSettings.from_env()
    return SETTINGS


def has_groq_api_key() -> bool:
    return SETTINGS.has_groq_key


def has_gemini_api_key() -> bool:
    return SETTINGS.has_gemini_key


GROQ_API_KEY = SETTINGS.groq_api_key
GEMINI_API_KEY = SETTINGS.gemini_api_key
GEMINI_ASSIST_API_KEY = SETTINGS.gemini_assist_api_key

GROQ_AUDIO_MODEL = SETTINGS.groq_audio_model
GROQ_ASSIST_MODEL = SETTINGS.groq_assist_model
GROQ_VISION_MODEL = SETTINGS.groq_vision_model

GEMINI_LIVE_MODEL = SETTINGS.gemini_live_model
GEMINI_ASSIST_MODEL = SETTINGS.gemini_assist_model
GEMINI_VISION_MODEL = SETTINGS.gemini_vision_model

GROQ_REQUEST_TIMEOUT = SETTINGS.request_timeout_seconds
GROQ_ASSIST_MAX_TOKENS = SETTINGS.assist_max_tokens
GROQ_ASSIST_TEMPERATURE = SETTINGS.assist_temperature
GROQ_RATE_LIMIT_PER_MINUTE = SETTINGS.rate_limit_per_minute

OPENCLUELY_STT_PROVIDER = SETTINGS.stt_provider
OPENCLUELY_ASSIST_PROVIDER = SETTINGS.assist_provider
OPENCLUELY_AUDIO_SOURCE = SETTINGS.audio_source
OPENCLUELY_PERSIST_SESSION_DATA = SETTINGS.persist_session_data
OPENCLUELY_PERSIST_TRANSCRIPTS = SETTINGS.persist_transcripts
OPENCLUELY_PERSIST_NOTES = SETTINGS.persist_notes
OPENCLUELY_PERSIST_SCREENSHOTS = SETTINGS.persist_screenshots
OPENCLUELY_INCOGNITO = SETTINGS.incognito
OPENCLUELY_SCREEN_CONTEXT_ENABLED = SETTINGS.screen_context_enabled
LOCAL_WHISPER_MODEL_SIZE = SETTINGS.local_whisper_model_size


if not SETTINGS.has_groq_key:
    logger.warning("GROQ_API_KEY is not configured")

if not SETTINGS.has_gemini_live_key:
    logger.warning("GEMINI_API_KEY is not configured")

if not SETTINGS.has_gemini_assist_key:
    logger.warning("GEMINI_ASSIST_API_KEY is not configured")
