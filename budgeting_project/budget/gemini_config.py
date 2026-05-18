"""Read Gemini API settings from environment (Railway vars or .env)."""

from __future__ import annotations

import os
from pathlib import Path

_PLACEHOLDERS = frozenset({
    '',
    'your_gemini_api_key_here',
    'your-api-key',
    'changeme',
})


def _project_base() -> Path:
    try:
        from django.conf import settings
        return Path(settings.BASE_DIR)
    except Exception:
        return Path(__file__).resolve().parent.parent


def _load_dotenv_if_present() -> None:
    env_path = _project_base() / '.env'
    if not env_path.is_file():
        return
    try:
        from dotenv import load_dotenv
        load_dotenv(env_path, override=False)
    except ImportError:
        pass


def get_gemini_api_key() -> str:
    """Current API key from os.environ (after optional .env load)."""
    _load_dotenv_if_present()
    key = (os.environ.get('GEMINI_API_KEY') or '').strip().strip('"').strip("'")
    if key.lower() in _PLACEHOLDERS:
        return ''
    return key


def get_gemini_model() -> str:
    _load_dotenv_if_present()
    model = (os.environ.get('GEMINI_MODEL') or '').strip()
    return model or 'gemini-2.5-flash'


def is_gemini_configured() -> bool:
    return bool(get_gemini_api_key())
