"""API key and configuration management."""

import os
from pathlib import Path


# Default configuration values
DEFAULT_CONFIG = {
    "openai_model": "gpt-4o-mini",
    "max_tokens": 2000,
    "temperature": 0.0,
    "ocr_language": "eng",
    "min_chars_per_page": 20,
    "rent_min": 100.0,
    "rent_max": 50000.0,
    "deposit_max_multiplier": 3.0,
}


def get_openai_api_key():
    """Return OpenAI API key from environment variable."""
    key = os.environ.get("OPENAI_API_KEY", "")
    return key if key else None


def get_config(key, default=None):
    """Return config value by key."""
    return DEFAULT_CONFIG.get(key, default)


def is_llm_available():
    """Return True if OpenAI API key is configured."""
    return get_openai_api_key() is not None


def get_tesseract_path():
    """Return custom Tesseract path if set."""
    return os.environ.get("TESSERACT_PATH", None)
