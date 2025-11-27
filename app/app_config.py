"""Centralized application configuration."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional


# Load .env file if python-dotenv is available
try:
	from dotenv import load_dotenv
	load_dotenv()
except ImportError:
	pass


def get_env(key: str, default: Optional[str] = None, required: bool = False) -> Optional[str]:
	"""Read an environment variable."""
	value = os.getenv(key, default)
	if required and (value is None or value == ""):
		raise RuntimeError(f"Required environment variable '{key}' is not set")
	return value


# Application paths
APP_ROOT = Path(__file__).parent
STORAGE_DIR = APP_ROOT / "storage/data"
STORAGE_DIR.mkdir(exist_ok=True)

# Database
DB_PATH = os.getenv("PAWRES_DB_PATH", str(STORAGE_DIR / "app.db"))

# Default admin credentials
DEFAULT_ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@gmail.com")
DEFAULT_ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "123")
DEFAULT_ADMIN_NAME = os.getenv("ADMIN_NAME", "Admin User")

# Password hashing
PBKDF2_ITERATIONS = 100000
SALT_LENGTH = 16

# Map defaults
DEFAULT_MAP_CENTER = (14.5995, 120.9842)  # Manila, Philippines
DEFAULT_MAP_ZOOM = 12

# UI defaults
DEFAULT_WINDOW_WIDTH = 1200
DEFAULT_WINDOW_HEIGHT = 800
DEFAULT_WINDOW_MIN_WIDTH = 1000
DEFAULT_WINDOW_MIN_HEIGHT = 700

# Validation limits
MAX_NAME_LENGTH = 100
MAX_EMAIL_LENGTH = 255
MAX_PHONE_LENGTH = 20
MAX_DESCRIPTION_LENGTH = 1000
MAX_NOTES_LENGTH = 2000

# Status values
ANIMAL_STATUS_VALUES = ("available", "adoptable", "healthy", "recovering", "injured", "adopted", "unknown")
RESCUE_STATUS_VALUES = ("pending", "in_progress", "completed", "cancelled")
ADOPTION_STATUS_VALUES = ("pending", "approved", "rejected", "completed")

# File upload
MAX_PHOTO_SIZE_MB = 5
ALLOWED_PHOTO_EXTENSIONS = (".jpg", ".jpeg", ".png", ".gif")


__all__ = [
    "get_env",
    "APP_ROOT",
    "STORAGE_DIR",
    "DB_PATH",
    "DEFAULT_ADMIN_EMAIL",
    "DEFAULT_ADMIN_PASSWORD",
    "DEFAULT_ADMIN_NAME",
    "PBKDF2_ITERATIONS",
    "SALT_LENGTH",
    "DEFAULT_MAP_CENTER",
    "DEFAULT_MAP_ZOOM",
    "DEFAULT_WINDOW_WIDTH",
    "DEFAULT_WINDOW_HEIGHT",
    "DEFAULT_WINDOW_MIN_WIDTH",
    "DEFAULT_WINDOW_MIN_HEIGHT",
    "MAX_NAME_LENGTH",
    "MAX_EMAIL_LENGTH",
    "MAX_PHONE_LENGTH",
    "MAX_DESCRIPTION_LENGTH",
    "MAX_NOTES_LENGTH",
    "ANIMAL_STATUS_VALUES",
    "RESCUE_STATUS_VALUES",
    "ADOPTION_STATUS_VALUES",
    "MAX_PHOTO_SIZE_MB",
    "ALLOWED_PHOTO_EXTENSIONS",
]
