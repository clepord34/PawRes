"""Centralized application configuration."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional


# Determine project root (parent of app/ directory)
APP_ROOT = Path(__file__).parent
PROJECT_ROOT = APP_ROOT.parent

# Load .env file from project root if python-dotenv is available
try:
	from dotenv import load_dotenv
	# Look for .env in project root first, then current directory
	env_file = PROJECT_ROOT / ".env"
	if env_file.exists():
		load_dotenv(env_file)
	else:
		load_dotenv()  # Fallback to default behavior
except ImportError:
	pass


def get_env(key: str, default: Optional[str] = None, required: bool = False) -> Optional[str]:
	"""Read an environment variable."""
	value = os.getenv(key, default)
	if required and (value is None or value == ""):
		raise RuntimeError(f"Required environment variable '{key}' is not set")
	return value


# Application paths (APP_ROOT already defined above)
STORAGE_DIR = APP_ROOT / "storage"
STORAGE_DIR.mkdir(exist_ok=True)

# Assets directory
ASSETS_DIR = APP_ROOT / "assets"

# Database
DB_PATH = os.getenv("PAWRES_DB_PATH", str(STORAGE_DIR / "data/app.db"))

# Default admin credentials
DEFAULT_ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@gmail.com")
DEFAULT_ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "Admin@123")  # Stronger default
DEFAULT_ADMIN_NAME = os.getenv("ADMIN_NAME", "Admin User")

# Password hashing
PBKDF2_ITERATIONS = 100000
SALT_LENGTH = 16

# =============================================================================
# SECURITY SETTINGS
# =============================================================================

# Login lockout settings
MAX_FAILED_LOGIN_ATTEMPTS = int(os.getenv("MAX_FAILED_LOGIN_ATTEMPTS", "5"))
LOCKOUT_DURATION_MINUTES = int(os.getenv("LOCKOUT_DURATION_MINUTES", "15"))

# Session timeout settings
SESSION_TIMEOUT_MINUTES = int(os.getenv("SESSION_TIMEOUT_MINUTES", "30"))

# Password policy settings
PASSWORD_MIN_LENGTH = int(os.getenv("PASSWORD_MIN_LENGTH", "8"))
PASSWORD_REQUIRE_UPPERCASE = os.getenv("PASSWORD_REQUIRE_UPPERCASE", "true").lower() == "true"
PASSWORD_REQUIRE_LOWERCASE = os.getenv("PASSWORD_REQUIRE_LOWERCASE", "true").lower() == "true"
PASSWORD_REQUIRE_DIGIT = os.getenv("PASSWORD_REQUIRE_DIGIT", "true").lower() == "true"
PASSWORD_REQUIRE_SPECIAL = os.getenv("PASSWORD_REQUIRE_SPECIAL", "true").lower() == "true"
PASSWORD_HISTORY_COUNT = int(os.getenv("PASSWORD_HISTORY_COUNT", "5"))

# Map defaults
DEFAULT_MAP_CENTER = (13.5250, 123.3486)  # Camarines Sur, Philippines
DEFAULT_MAP_ZOOM = 9
MAP_TILE_URL_TEMPLATE = os.getenv(
    "MAP_TILE_URL_TEMPLATE",
    "https://a.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png",
)
MAP_TILE_MAX_ZOOM = int(os.getenv("MAP_TILE_MAX_ZOOM", "19"))
MAP_TILE_HEALTHCHECK_HOST = os.getenv("MAP_TILE_HEALTHCHECK_HOST", "a.basemaps.cartocdn.com")

# UI defaults
DEFAULT_WINDOW_WIDTH = 1200
DEFAULT_WINDOW_HEIGHT = 800
DEFAULT_WINDOW_MIN_WIDTH = 360
DEFAULT_WINDOW_MIN_HEIGHT = 500

# Responsive breakpoints (matches Bootstrap/Flet defaults)
BREAKPOINT_XS = 0       # Extra small: < 576px (phones)
BREAKPOINT_SM = 576     # Small: >= 576px (large phones)
BREAKPOINT_MD = 768     # Medium: >= 768px (tablets)
BREAKPOINT_LG = 992     # Large: >= 992px (desktops)
BREAKPOINT_XL = 1200    # Extra large: >= 1200px (large desktops)
BREAKPOINT_XXL = 1400   # Extra extra large: >= 1400px

# Sidebar collapse threshold — below this, sidebar becomes a drawer
SIDEBAR_COLLAPSE_WIDTH = BREAKPOINT_MD  # 768px

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
ANIMAL_STATUS_VALUES = ("healthy", "recovering", "injured", "adopted", "unknown")
RESCUE_STATUS_VALUES = ("pending", "in_progress", "completed", "cancelled")
ADOPTION_STATUS_VALUES = ("pending", "approved", "rejected", "completed")

# Adoptable status values (animals that can be adopted)
ADOPTABLE_STATUSES = ("healthy",)

# Healthy status values for filtering
HEALTHY_STATUSES = ("healthy",)

# Approved adoption statuses
APPROVED_ADOPTION_STATUSES = ("approved", "adopted", "completed")


# =============================================================================
# STATUS CONSTANTS - Use these instead of magic strings throughout the app
# =============================================================================

class RescueStatus:
    """Standardized rescue mission status values."""
    PENDING = "pending"
    ONGOING = "on-going"
    RESCUED = "rescued"
    FAILED = "failed"
    CANCELLED = "cancelled"  # User cancelled their own report
    REMOVED = "removed"  # Admin removed as invalid/spam/duplicate
    
    # Archived status is stored as "original_status|archived" (e.g., "rescued|archived")
    ARCHIVED_SUFFIX = "|archived"
    
    @classmethod
    def normalize(cls, status: str) -> str:
        """Normalize a status string to match constant values."""
        s = (status or "").lower().strip()
        # Handle archived suffix
        if cls.ARCHIVED_SUFFIX in s:
            s = s.replace(cls.ARCHIVED_SUFFIX, "")
        if s in ("pending", ""): return cls.PENDING
        if s in ("on-going", "ongoing", "in_progress", "in progress"): return cls.ONGOING
        if s in ("rescued", "completed"): return cls.RESCUED
        if s in ("failed",): return cls.FAILED
        if s in ("cancelled", "canceled"): return cls.CANCELLED
        if s in ("removed",): return cls.REMOVED
        return s
    
    @classmethod
    def get_label(cls, status: str) -> str:
        """Get human-readable label for a status (strips archived suffix for display)."""
        # For archived items, show original status to users
        base_status = cls.get_base_status(status)
        normalized = cls.normalize(base_status)
        labels = {
            cls.PENDING: "Pending",
            cls.ONGOING: "On-going",
            cls.RESCUED: "Rescued",
            cls.FAILED: "Failed",
            cls.CANCELLED: "Cancelled",
            cls.REMOVED: "Removed",
        }
        return labels.get(normalized, status.title())
    
    @classmethod
    def is_cancelled(cls, status: str) -> bool:
        """Check if a status indicates user cancellation."""
        return cls.normalize(status) == cls.CANCELLED
    
    @classmethod
    def is_final(cls, status: str) -> bool:
        """Check if a status is final (rescued/failed/cancelled)."""
        normalized = cls.normalize(status)
        return normalized in (cls.RESCUED, cls.FAILED, cls.CANCELLED)
    
    @classmethod
    def is_active(cls, status: str) -> bool:
        """Check if a status indicates an active (non-final) mission."""
        normalized = cls.normalize(status)
        return normalized in (cls.PENDING, cls.ONGOING)
    
    @classmethod
    def is_archived(cls, status: str) -> bool:
        """Check if a status indicates archived."""
        return cls.ARCHIVED_SUFFIX in (status or "").lower()
    
    @classmethod
    def is_removed(cls, status: str) -> bool:
        """Check if a status indicates removed (invalid/spam/duplicate)."""
        return cls.normalize(status) == cls.REMOVED
    
    @classmethod
    def is_hidden(cls, status: str) -> bool:
        """Check if a status is hidden from active admin list (archived or removed)."""
        return cls.is_archived(status) or cls.is_removed(status)
    
    @classmethod
    def get_base_status(cls, status: str) -> str:
        """Get the base status without archived suffix."""
        s = (status or "").lower().strip()
        if cls.ARCHIVED_SUFFIX in s:
            return s.replace(cls.ARCHIVED_SUFFIX, "")
        return s
    
    @classmethod
    def make_archived(cls, status: str) -> str:
        """Add archived suffix to a status."""
        base = cls.get_base_status(status)
        return f"{base}{cls.ARCHIVED_SUFFIX}"
    
    @classmethod
    def has_outcome(cls, status: str) -> bool:
        """Check if this status represents a real outcome (for analytics)."""
        base = cls.get_base_status(status)
        normalized = cls.normalize(base)
        return normalized in (cls.RESCUED, cls.FAILED)
    
    @classmethod
    def counts_in_analytics(cls, status: str) -> bool:
        """Check if this status should be counted in analytics (not removed)."""
        return not cls.is_removed(status)
    
    @classmethod
    def all_statuses(cls) -> tuple:
        """Return all status values (excluding archived variants)."""
        return (cls.PENDING, cls.ONGOING, cls.RESCUED, cls.FAILED, cls.CANCELLED, cls.REMOVED)


class AdoptionStatus:
    """Standardized adoption request status values."""
    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"
    CANCELLED = "cancelled"  # User cancelled their own request
    REMOVED = "removed"  # Admin removed as invalid/spam/duplicate
    
    # Archived status is stored as "original_status|archived" (e.g., "approved|archived")
    ARCHIVED_SUFFIX = "|archived"
    
    @classmethod
    def normalize(cls, status: str) -> str:
        """Normalize a status string to match constant values."""
        s = (status or "").lower().strip()
        # Handle archived suffix
        if cls.ARCHIVED_SUFFIX in s:
            s = s.replace(cls.ARCHIVED_SUFFIX, "")
        if s in ("pending", ""): return cls.PENDING
        if s in ("approved", "adopted", "completed"): return cls.APPROVED
        if s in ("denied", "rejected"): return cls.DENIED
        if s in ("cancelled", "canceled", "revoked"): return cls.CANCELLED
        if s in ("removed",): return cls.REMOVED
        return s
    
    @classmethod
    def get_label(cls, status: str) -> str:
        """Get human-readable label for a status (strips archived suffix for display)."""
        # For archived items, show original status to users
        base_status = cls.get_base_status(status)
        normalized = cls.normalize(base_status)
        labels = {
            cls.PENDING: "Pending",
            cls.APPROVED: "Approved",
            cls.DENIED: "Denied",
            cls.CANCELLED: "Cancelled",
            cls.REMOVED: "Removed",
        }
        return labels.get(normalized, status.title())
    
    @classmethod
    def is_cancelled(cls, status: str) -> bool:
        """Check if a status indicates user cancellation."""
        return cls.normalize(status) == cls.CANCELLED
    
    @classmethod
    def is_final(cls, status: str) -> bool:
        """Check if a status is final (approved/denied/cancelled)."""
        normalized = cls.normalize(status)
        return normalized in (cls.APPROVED, cls.DENIED, cls.CANCELLED)
    
    @classmethod
    def is_archived(cls, status: str) -> bool:
        """Check if a status indicates archived."""
        return cls.ARCHIVED_SUFFIX in (status or "").lower()
    
    @classmethod
    def is_removed(cls, status: str) -> bool:
        """Check if a status indicates removed (invalid/spam/duplicate)."""
        return cls.normalize(status) == cls.REMOVED
    
    @classmethod
    def is_hidden(cls, status: str) -> bool:
        """Check if a status is hidden from active admin list (archived or removed)."""
        return cls.is_archived(status) or cls.is_removed(status)
    
    @classmethod
    def get_base_status(cls, status: str) -> str:
        """Get the base status without archived suffix."""
        s = (status or "").lower().strip()
        if cls.ARCHIVED_SUFFIX in s:
            return s.replace(cls.ARCHIVED_SUFFIX, "")
        return s
    
    @classmethod
    def make_archived(cls, status: str) -> str:
        """Add archived suffix to a status."""
        base = cls.get_base_status(status)
        return f"{base}{cls.ARCHIVED_SUFFIX}"
    
    @classmethod
    def has_outcome(cls, status: str) -> bool:
        """Check if this status represents a real outcome (for analytics)."""
        base = cls.get_base_status(status)
        normalized = cls.normalize(base)
        return normalized in (cls.APPROVED, cls.DENIED)
    
    @classmethod
    def counts_in_analytics(cls, status: str) -> bool:
        """Check if this status should be counted in analytics (not removed)."""
        return not cls.is_removed(status)
    
    @classmethod
    def all_statuses(cls) -> tuple:
        """Return all status values (excluding archived variants)."""
        return (cls.PENDING, cls.APPROVED, cls.DENIED, cls.CANCELLED, cls.REMOVED)


class AnimalStatus:
    """Standardized animal status values."""
    HEALTHY = "healthy"
    RECOVERING = "recovering"
    INJURED = "injured"
    ADOPTED = "adopted"
    PROCESSING = "processing"  # Newly rescued, awaiting admin setup
    REMOVED = "removed"  # Admin removed as invalid/duplicate
    
    # Archived status is stored as "original_status|archived" (e.g., "adopted|archived")
    ARCHIVED_SUFFIX = "|archived"
    
    @classmethod
    def normalize(cls, status: str) -> str:
        """Normalize a status string to match constant values."""
        s = (status or "").lower().strip()
        # Handle archived suffix
        if cls.ARCHIVED_SUFFIX in s:
            s = s.replace(cls.ARCHIVED_SUFFIX, "")
        if s in ("healthy",): return cls.HEALTHY
        if s in ("recovering",): return cls.RECOVERING
        if s in ("injured",): return cls.INJURED
        if s in ("adopted",): return cls.ADOPTED
        if s in ("processing",): return cls.PROCESSING
        if s in ("removed",): return cls.REMOVED
        return s
    
    @classmethod
    def is_adoptable(cls, status: str) -> bool:
        """Check if an animal can be adopted."""
        base = cls.get_base_status(status)
        return base.lower() == cls.HEALTHY
    
    @classmethod
    def needs_setup(cls, status: str) -> bool:
        """Check if animal needs admin setup before being visible to users."""
        return cls.normalize(status) == cls.PROCESSING
    
    @classmethod
    def is_archived(cls, status: str) -> bool:
        """Check if a status indicates archived."""
        return cls.ARCHIVED_SUFFIX in (status or "").lower()
    
    @classmethod
    def is_removed(cls, status: str) -> bool:
        """Check if a status indicates removed (invalid/duplicate)."""
        return cls.normalize(status) == cls.REMOVED
    
    @classmethod
    def is_hidden(cls, status: str) -> bool:
        """Check if a status is hidden from active lists (archived or removed)."""
        return cls.is_archived(status) or cls.is_removed(status)
    
    @classmethod
    def get_base_status(cls, status: str) -> str:
        """Get the base status without archived suffix."""
        s = (status or "").lower().strip()
        if cls.ARCHIVED_SUFFIX in s:
            return s.replace(cls.ARCHIVED_SUFFIX, "")
        return s
    
    @classmethod
    def make_archived(cls, status: str) -> str:
        """Add archived suffix to a status."""
        base = cls.get_base_status(status)
        return f"{base}{cls.ARCHIVED_SUFFIX}"
    
    @classmethod
    def get_label(cls, status: str) -> str:
        """Get human-readable label for a status."""
        base = cls.get_base_status(status)
        normalized = cls.normalize(base)
        labels = {
            cls.HEALTHY: "Healthy",
            cls.RECOVERING: "Recovering",
            cls.INJURED: "Injured",
            cls.ADOPTED: "Adopted",
            cls.PROCESSING: "Processing",
            cls.REMOVED: "Removed",
        }
        return labels.get(normalized, status.title())
    
    @classmethod
    def counts_in_analytics(cls, status: str) -> bool:
        """Check if this status should be counted in analytics (not removed)."""
        return not cls.is_removed(status)


class Urgency:
    """Standardized urgency levels for rescue missions."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    
    # Display labels
    LOW_LABEL = "Low - Animal appears safe"
    MEDIUM_LABEL = "Medium - Needs attention soon"
    HIGH_LABEL = "High - Immediate help needed"
    
    @classmethod
    def get_label(cls, urgency: str) -> str:
        """Get display label for an urgency level."""
        labels = {
            cls.LOW: cls.LOW_LABEL,
            cls.MEDIUM: cls.MEDIUM_LABEL,
            cls.HIGH: cls.HIGH_LABEL,
        }
        return labels.get((urgency or "").lower(), cls.MEDIUM_LABEL)
    
    @classmethod
    def from_label(cls, label: str) -> str:
        """Extract urgency level from full label."""
        if not label:
            return cls.MEDIUM
        label_lower = label.lower()
        if "high" in label_lower:
            return cls.HIGH
        elif "low" in label_lower:
            return cls.LOW
        return cls.MEDIUM

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
    "MAP_TILE_URL_TEMPLATE",
    "MAP_TILE_MAX_ZOOM",
    "MAP_TILE_HEALTHCHECK_HOST",
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
    "RescueStatus",
    "AdoptionStatus",
    "AnimalStatus",
    "Urgency",
    "MAX_PHOTO_SIZE_MB",
    "ALLOWED_PHOTO_EXTENSIONS",
    "ALLOWED_MIME_TYPES",
    "UPLOADS_DIR",
    "TEMP_DIR",
    "get_upload_path",
    "is_valid_status",
    "is_adoptable_status",
]
