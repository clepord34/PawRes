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
STORAGE_DIR = APP_ROOT / "storage"
STORAGE_DIR.mkdir(exist_ok=True)

# Database
DB_PATH = os.getenv("PAWRES_DB_PATH", str(STORAGE_DIR / "data/app.db"))

# Default admin credentials
DEFAULT_ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@gmail.com")
DEFAULT_ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "123")
DEFAULT_ADMIN_NAME = os.getenv("ADMIN_NAME", "Admin User")

# Password hashing
PBKDF2_ITERATIONS = 100000
SALT_LENGTH = 16

# Map defaults
DEFAULT_MAP_CENTER = (13.5250, 123.3486)  # Camarines Sur, Philippines
DEFAULT_MAP_ZOOM = 9

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
MAX_REASON_LENGTH = 500
MAX_LOCATION_LENGTH = 500
MIN_PASSWORD_LENGTH = 6
MAX_PASSWORD_LENGTH = 128

# Status values
ANIMAL_STATUS_VALUES = ("available", "adoptable", "healthy", "recovering", "injured", "adopted", "unknown")
RESCUE_STATUS_VALUES = ("pending", "in_progress", "completed", "cancelled")
ADOPTION_STATUS_VALUES = ("pending", "approved", "rejected", "completed")

# Adoptable status values (animals that can be adopted)
ADOPTABLE_STATUSES = ("available", "adoptable", "healthy", "ready")

# Healthy status values for filtering
HEALTHY_STATUSES = ("healthy", "available", "adoptable", "ready")

# Approved adoption statuses
APPROVED_ADOPTION_STATUSES = ("approved", "adopted", "completed")

# File upload
MAX_PHOTO_SIZE_MB = 5
ALLOWED_PHOTO_EXTENSIONS = (".jpg", ".jpeg", ".png", ".gif", ".webp")
ALLOWED_MIME_TYPES = (
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/webp",
)

# Upload paths
UPLOADS_DIR = STORAGE_DIR / "uploads"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
TEMP_DIR = STORAGE_DIR / "temp"
TEMP_DIR.mkdir(parents=True, exist_ok=True)


def get_upload_path(filename: str) -> Path:
    """Get absolute path for an uploaded file.
    
    Args:
        filename: The filename (not full path)
        
    Returns:
        Absolute Path to the file in uploads directory
    """
    return UPLOADS_DIR / filename


def is_valid_status(status: str, status_type: str = "animal") -> bool:
    """Check if a status value is valid.
    
    Args:
        status: The status string to validate
        status_type: One of 'animal', 'rescue', or 'adoption'
        
    Returns:
        True if status is valid for the given type
    """
    status_lower = status.lower()
    if status_type == "animal":
        return status_lower in ANIMAL_STATUS_VALUES
    elif status_type == "rescue":
        return status_lower in RESCUE_STATUS_VALUES
    elif status_type == "adoption":
        return status_lower in ADOPTION_STATUS_VALUES
    return False


def is_adoptable_status(status: str) -> bool:
    """Check if an animal status means it's adoptable.
    
    Args:
        status: The animal's status
        
    Returns:
        True if the animal can be adopted
    """
    return status.lower() in ADOPTABLE_STATUSES


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
    "MAX_REASON_LENGTH",
    "MAX_LOCATION_LENGTH",
    "MIN_PASSWORD_LENGTH",
    "MAX_PASSWORD_LENGTH",
    "ANIMAL_STATUS_VALUES",
    "RESCUE_STATUS_VALUES",
    "ADOPTION_STATUS_VALUES",
    "ADOPTABLE_STATUSES",
    "HEALTHY_STATUSES",
    "APPROVED_ADOPTION_STATUSES",
    "MAX_PHOTO_SIZE_MB",
    "ALLOWED_PHOTO_EXTENSIONS",
    "ALLOWED_MIME_TYPES",
    "UPLOADS_DIR",
    "TEMP_DIR",
    "get_upload_path",
    "is_valid_status",
    "is_adoptable_status",
]
