"""Security logging service for authentication and administrative events.

Provides structured logging with:
- Rotating file handlers (prevents unlimited growth)
- Separate log files for auth, admin, and security events
- Formatted log entries with timestamps and context
- Automatic test mode detection (disables file logging during pytest)
"""
from __future__ import annotations

import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Dict, Optional, List
import json

import app_config


def _is_testing() -> bool:
    """Check if we're running in test mode (pytest).
    
    Returns:
        True if running under pytest, False otherwise
    """
    return (
        "pytest" in sys.modules or
        "unittest" in sys.modules or
        os.environ.get("PYTEST_CURRENT_TEST") is not None or
        os.environ.get("PAWRES_TESTING") == "1"
    )


# Log directory
LOGS_DIR = app_config.STORAGE_DIR / "data" / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Log file paths
AUTH_LOG_FILE = LOGS_DIR / "auth.log"
ADMIN_LOG_FILE = LOGS_DIR / "admin.log"
SECURITY_LOG_FILE = LOGS_DIR / "security.log"

# Log rotation settings
MAX_LOG_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB
BACKUP_COUNT = 5  # Keep 5 backup files


def _create_rotating_handler(
    log_file: Path,
    level: int = logging.INFO
) -> RotatingFileHandler:
    """Create a rotating file handler.
    
    Args:
        log_file: Path to the log file
        level: Logging level
        
    Returns:
        Configured RotatingFileHandler
    """
    handler = RotatingFileHandler(
        str(log_file),
        maxBytes=MAX_LOG_SIZE_BYTES,
        backupCount=BACKUP_COUNT,
        encoding="utf-8"
    )
    handler.setLevel(level)
    
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    handler.setFormatter(formatter)
    
    return handler


def _setup_logger(name: str, log_file: Path) -> logging.Logger:
    """Set up a logger with rotating file handler.
    
    In test mode, uses a NullHandler to prevent file writes.
    
    Args:
        name: Logger name
        log_file: Path to the log file
        
    Returns:
        Configured logger
    """
    logger = logging.getLogger(name)
    
    # Avoid adding handlers multiple times
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        
        # In test mode, use NullHandler to prevent file writes
        if _is_testing():
            logger.addHandler(logging.NullHandler())
        else:
            logger.addHandler(_create_rotating_handler(log_file))
        
        # Prevent propagation to root logger
        logger.propagate = False
    
    return logger


class AuthLogger:
    """Logger for authentication events."""
    
    def __init__(self):
        """Initialize the auth logger."""
        self._logger = _setup_logger("pawres.auth", AUTH_LOG_FILE)
    
    def log_login_success(
        self,
        email: str,
        user_id: int,
        oauth_provider: Optional[str] = None
    ) -> None:
        """Log a successful login.
        
        Args:
            email: User's email
            user_id: User's ID
            oauth_provider: OAuth provider if used (e.g., 'google')
        """
        method = f"oauth:{oauth_provider}" if oauth_provider else "password"
        self._logger.info(
            f"LOGIN_SUCCESS | email={email} | user_id={user_id} | method={method}"
        )
    
    def log_login_failure(
        self,
        email: str,
        reason: str = "invalid_credentials",
        attempt_count: Optional[int] = None
    ) -> None:
        """Log a failed login attempt.
        
        Args:
            email: Email used in attempt
            reason: Reason for failure
            attempt_count: Number of failed attempts if tracking
        """
        extra = f" | attempts={attempt_count}" if attempt_count else ""
        self._logger.warning(
            f"LOGIN_FAILURE | email={email} | reason={reason}{extra}"
        )
    
    def log_logout(self, email: str, user_id: int) -> None:
        """Log a user logout.
        
        Args:
            email: User's email
            user_id: User's ID
        """
        self._logger.info(f"LOGOUT | email={email} | user_id={user_id}")
    
    def log_lockout(self, email: str, duration_minutes: int) -> None:
        """Log an account lockout.
        
        Args:
            email: Email of locked account
            duration_minutes: Lockout duration
        """
        self._logger.warning(
            f"ACCOUNT_LOCKOUT | email={email} | duration_minutes={duration_minutes}"
        )
    
    def log_lockout_expired(self, email: str) -> None:
        """Log a lockout expiration.
        
        Args:
            email: Email of unlocked account
        """
        self._logger.info(f"LOCKOUT_EXPIRED | email={email}")
    
    def log_password_change(
        self,
        user_id: int,
        email: str,
        changed_by: Optional[int] = None
    ) -> None:
        """Log a password change.
        
        Args:
            user_id: ID of user whose password was changed
            email: Email of user
            changed_by: ID of admin who changed it (if not self)
        """
        if changed_by and changed_by != user_id:
            self._logger.info(
                f"PASSWORD_RESET | user_id={user_id} | email={email} | admin_id={changed_by}"
            )
        else:
            self._logger.info(
                f"PASSWORD_CHANGED | user_id={user_id} | email={email}"
            )
    
    def log_session_expired(self, user_id: int, email: str) -> None:
        """Log a session expiration.
        
        Args:
            user_id: User's ID
            email: User's email
        """
        self._logger.info(f"SESSION_EXPIRED | user_id={user_id} | email={email}")


class AdminLogger:
    """Logger for administrative actions."""
    
    def __init__(self):
        """Initialize the admin logger."""
        self._logger = _setup_logger("pawres.admin", ADMIN_LOG_FILE)
    
    def log_user_created(
        self,
        admin_id: int,
        new_user_id: int,
        new_user_email: str,
        new_user_role: str
    ) -> None:
        """Log user creation by admin.
        
        Args:
            admin_id: ID of admin who created the user
            new_user_id: ID of created user
            new_user_email: Email of created user
            new_user_role: Role assigned to created user
        """
        self._logger.info(
            f"USER_CREATED | admin_id={admin_id} | new_user_id={new_user_id} | "
            f"email={new_user_email} | role={new_user_role}"
        )
    
    def log_user_disabled(
        self,
        admin_id: int,
        user_id: int,
        user_email: str
    ) -> None:
        """Log user disabling by admin.
        
        Args:
            admin_id: ID of admin who disabled the user
            user_id: ID of disabled user
            user_email: Email of disabled user
        """
        self._logger.info(
            f"USER_DISABLED | admin_id={admin_id} | user_id={user_id} | email={user_email}"
        )
    
    def log_user_enabled(
        self,
        admin_id: int,
        user_id: int,
        user_email: str
    ) -> None:
        """Log user re-enabling by admin.
        
        Args:
            admin_id: ID of admin who enabled the user
            user_id: ID of enabled user
            user_email: Email of enabled user
        """
        self._logger.info(
            f"USER_ENABLED | admin_id={admin_id} | user_id={user_id} | email={user_email}"
        )
    
    def log_user_deleted(
        self,
        admin_id: int,
        user_id: int,
        user_email: str
    ) -> None:
        """Log user deletion by admin.
        
        Args:
            admin_id: ID of admin who deleted the user
            user_id: ID of deleted user
            user_email: Email of deleted user
        """
        self._logger.warning(
            f"USER_DELETED | admin_id={admin_id} | user_id={user_id} | email={user_email}"
        )
    
    def log_role_changed(
        self,
        admin_id: int,
        user_id: int,
        user_email: str,
        old_role: str,
        new_role: str
    ) -> None:
        """Log role change by admin.
        
        Args:
            admin_id: ID of admin who changed the role
            user_id: ID of user whose role was changed
            user_email: Email of user
            old_role: Previous role
            new_role: New role
        """
        self._logger.info(
            f"ROLE_CHANGED | admin_id={admin_id} | user_id={user_id} | "
            f"email={user_email} | old_role={old_role} | new_role={new_role}"
        )
    
    def log_password_reset(
        self,
        admin_id: int,
        user_id: int,
        user_email: str
    ) -> None:
        """Log password reset by admin.
        
        Args:
            admin_id: ID of admin who reset the password
            user_id: ID of user whose password was reset
            user_email: Email of user
        """
        self._logger.info(
            f"PASSWORD_RESET | admin_id={admin_id} | user_id={user_id} | email={user_email}"
        )


class SecurityLogger:
    """Logger for security-related events."""
    
    def __init__(self):
        """Initialize the security logger."""
        self._logger = _setup_logger("pawres.security", SECURITY_LOG_FILE)
    
    def log_unauthorized_access(
        self,
        route: str,
        reason: str,
        user_id: Optional[int] = None,
        user_role: Optional[str] = None,
        required_roles: Optional[List[str]] = None
    ) -> None:
        """Log an unauthorized access attempt.
        
        Args:
            route: Route that was accessed
            reason: Reason for denial
            user_id: User ID if authenticated
            user_role: User's role if authenticated
            required_roles: Roles that were required
        """
        user_info = f"user_id={user_id} | role={user_role}" if user_id else "user_id=None"
        roles_info = f" | required_roles={required_roles}" if required_roles else ""
        
        self._logger.warning(
            f"UNAUTHORIZED_ACCESS | route={route} | reason={reason} | {user_info}{roles_info}"
        )
    
    def log_brute_force_attempt(
        self,
        email: str,
        attempt_count: int
    ) -> None:
        """Log a potential brute force attempt.
        
        Args:
            email: Email being targeted
            attempt_count: Number of failed attempts
        """
        self._logger.warning(
            f"BRUTE_FORCE_ATTEMPT | email={email} | attempts={attempt_count}"
        )
    
    def log_suspicious_activity(
        self,
        activity: str,
        user_id: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log suspicious activity.
        
        Args:
            activity: Description of the activity
            user_id: User ID if known
            details: Additional details
        """
        user_info = f"user_id={user_id}" if user_id else "user_id=None"
        details_str = f" | details={json.dumps(details)}" if details else ""
        
        self._logger.warning(
            f"SUSPICIOUS_ACTIVITY | activity={activity} | {user_info}{details_str}"
        )


# Singleton instances
_auth_logger: Optional[AuthLogger] = None
_admin_logger: Optional[AdminLogger] = None
_security_logger: Optional[SecurityLogger] = None


def get_auth_logger() -> AuthLogger:
    """Get the authentication logger singleton.
    
    Returns:
        AuthLogger instance
    """
    global _auth_logger
    if _auth_logger is None:
        _auth_logger = AuthLogger()
    return _auth_logger


def get_admin_logger() -> AdminLogger:
    """Get the admin logger singleton.
    
    Returns:
        AdminLogger instance
    """
    global _admin_logger
    if _admin_logger is None:
        _admin_logger = AdminLogger()
    return _admin_logger


def get_security_logger() -> SecurityLogger:
    """Get the security logger singleton.
    
    Returns:
        SecurityLogger instance
    """
    global _security_logger
    if _security_logger is None:
        _security_logger = SecurityLogger()
    return _security_logger


def read_log_entries(
    log_type: str = "security",
    limit: int = 100,
    level: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Read log entries from a log file.
    
    Args:
        log_type: Type of log ('auth', 'admin', 'security')
        limit: Maximum number of entries to return
        level: Filter by log level ('INFO', 'WARNING', 'ERROR')
        
    Returns:
        List of parsed log entries
    """
    log_files = {
        "auth": AUTH_LOG_FILE,
        "admin": ADMIN_LOG_FILE,
        "security": SECURITY_LOG_FILE,
    }
    
    log_file = log_files.get(log_type, SECURITY_LOG_FILE)
    
    if not log_file.exists():
        return []
    
    entries = []
    try:
        with open(log_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        # Read from end to get most recent first
        for line in reversed(lines):
            if len(entries) >= limit:
                break
            
            line = line.strip()
            if not line:
                continue
            
            try:
                # Parse log line: "2024-12-04 10:30:00 | INFO | MESSAGE"
                parts = line.split(" | ", 2)
                if len(parts) >= 3:
                    timestamp_str, log_level, message = parts
                    
                    if level and log_level != level:
                        continue
                    
                    entries.append({
                        "timestamp": timestamp_str,
                        "level": log_level,
                        "message": message,
                        "raw": line,
                    })
            except Exception:
                continue
                
    except Exception as e:
        print(f"[ERROR] Failed to read log file {log_file}: {e}")
    
    return entries


__all__ = [
    "AuthLogger",
    "AdminLogger",
    "SecurityLogger",
    "get_auth_logger",
    "get_admin_logger",
    "get_security_logger",
    "read_log_entries",
    "LOGS_DIR",
]
