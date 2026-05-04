"""Application settings loaded from environment variables."""

import os

from dotenv import load_dotenv

load_dotenv()


def _read_bool(value: str, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in ("1", "true", "yes", "y", "on")


BASE_URL = os.getenv("BASE_URL", "https://sandbox.moodledemo.net/").strip()
MOODLE_USERNAME = os.getenv("MOODLE_USERNAME", "").strip()
MOODLE_PASSWORD = os.getenv("MOODLE_PASSWORD", "").strip()
HEADLESS = _read_bool(os.getenv("HEADLESS", "false"))
