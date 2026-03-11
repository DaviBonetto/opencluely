"""Provider configuration loaded from environment variables."""

import logging
import os

logger = logging.getLogger("config")


HUGGINGFACE_API_KEY = os.environ.get("HUGGINGFACE_API_KEY", "").strip()
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "").strip()

VISION_MODEL = os.environ.get("HUGGINGFACE_VISION_MODEL", "Qwen/Qwen2-VL-7B-Instruct")
HUGGINGFACE_ENDPOINT = f"https://api-inference.huggingface.co/models/{VISION_MODEL}"
VISION_TIMEOUT = int(os.environ.get("VISION_TIMEOUT_SECONDS", "30"))


def _is_placeholder(value: str) -> bool:
    return value.startswith(("hf_...", "gsk_...", "your-", "replace-"))


if not HUGGINGFACE_API_KEY or _is_placeholder(HUGGINGFACE_API_KEY):
    logger.warning("HUGGINGFACE_API_KEY is not configured")

if not GROQ_API_KEY or _is_placeholder(GROQ_API_KEY):
    logger.warning("GROQ_API_KEY is not configured")
