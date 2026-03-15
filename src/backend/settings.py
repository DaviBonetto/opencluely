"""Environment-driven backend settings for optional services."""

from __future__ import annotations

import logging
import os


logger = logging.getLogger("backend.settings")


def _get_env(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


def _is_placeholder(value: str) -> bool:
    return value.startswith(("hf_...", "gsk_...", "your-", "replace-"))


GROQ_API_KEY = _get_env("GROQ_API_KEY")
HUGGINGFACE_API_KEY = _get_env("HUGGINGFACE_API_KEY")

GROQ_AUDIO_MODEL = _get_env("GROQ_AUDIO_MODEL", "whisper-large-v3")
GROQ_ASSIST_MODEL = _get_env("GROQ_ASSIST_MODEL", "llama-3.3-70b-versatile")
GROQ_VISION_MODEL = _get_env(
    "GROQ_VISION_MODEL", "meta-llama/llama-4-scout-17b-16e-instruct"
)

GROQ_REQUEST_TIMEOUT = float(_get_env("GROQ_REQUEST_TIMEOUT_SECONDS", "30"))
GROQ_ASSIST_MAX_TOKENS = int(_get_env("GROQ_ASSIST_MAX_TOKENS", "500"))
GROQ_ASSIST_TEMPERATURE = float(_get_env("GROQ_ASSIST_TEMPERATURE", "0.7"))
GROQ_RATE_LIMIT_PER_MINUTE = int(_get_env("GROQ_RATE_LIMIT_PER_MINUTE", "30"))

HUGGINGFACE_VISION_MODEL = _get_env("HUGGINGFACE_VISION_MODEL", "Qwen/Qwen2-VL-7B-Instruct")
HUGGINGFACE_ENDPOINT = f"https://api-inference.huggingface.co/models/{HUGGINGFACE_VISION_MODEL}"
VISION_TIMEOUT = int(_get_env("VISION_TIMEOUT_SECONDS", "30"))


def has_groq_api_key() -> bool:
    return bool(GROQ_API_KEY) and not _is_placeholder(GROQ_API_KEY)


def has_huggingface_api_key() -> bool:
    return bool(HUGGINGFACE_API_KEY) and not _is_placeholder(HUGGINGFACE_API_KEY)


if not has_huggingface_api_key():
    logger.warning("HUGGINGFACE_API_KEY is not configured")

if not has_groq_api_key():
    logger.warning("GROQ_API_KEY is not configured")
