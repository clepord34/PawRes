"""Authentication service with PBKDF2-HMAC-SHA256 hashing and login lockout."""
from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Tuple
from enum import Enum

from storage.database import Database
from components.utils import normalize_phone_number
import app_config


class AuthResult(Enum):
    """Authentication operation results."""
    SUCCESS = "success"
    INVALID_CREDENTIALS = "invalid_credentials"
    USER_NOT_FOUND = "user_not_found"
    EMAIL_EXISTS = "email_exists"
    PHONE_EXISTS = "phone_exists"
    CONTACT_EXISTS = "contact_exists"
    INVALID_INPUT = "invalid_input"
    DATABASE_ERROR = "database_error"
    ACCOUNT_LOCKED = "account_locked"
    ACCOUNT_DISABLED = "account_disabled"
    OAUTH_CONFLICT = "oauth_conflict"  # User exists with password, OAuth would overwrite


class AuthServiceError(Exception):
    """Base exception for auth service errors."""
    
    def __init__(self, message: str, result: AuthResult = AuthResult.DATABASE_ERROR):
        super().__init__(message)
        self.result = result


def _download_and_save_profile_picture(picture_url: str, user_email: str) -> Optional[str]:
    """Download a profile picture from URL and save it using FileStore.
    
    Args:
        picture_url: URL of the profile picture (e.g., Google profile pic)
        user_email: User's email (used for generating filename)
        
    Returns:
        The saved filename, or None if download failed
    """
    if not picture_url:
        return None
    
    try:
        import urllib.request
        from storage.file_store import FileStore
        
        # Download the image
        req = urllib.request.Request(
            picture_url,
            headers={"User-Agent": "PawRes/1.0"}
        )
        
        with urllib.request.urlopen(req, timeout=10) as response:
            image_data = response.read()
            
            # Determine content type and extension
            content_type = response.headers.get("Content-Type", "image/jpeg")
            if "png" in content_type:
                ext = "png"
            elif "gif" in content_type:
                ext = "gif"
            elif "webp" in content_type:
                ext = "webp"
            else:
                ext = "jpg"
        
        # Save using FileStore with user identifier
        file_store = FileStore()
        # Use email prefix as custom name for the profile picture
        username = user_email.split("@")[0] if user_email else "user"
        filename = file_store.save_bytes(
            data=image_data,
            original_name=f"profile.{ext}",
            validate=False,  # Skip validation for external images
            custom_name=f"profile_{username}"
        )
        
        return filename
        
    except Exception as e:
        print(f"[WARN] Could not download profile picture: {e}")
        return None


class AuthService:
    """Authentication service backed by SQLite database."""

    def __init__(self, db: Optional[Database | str] = None, *, ensure_tables: bool = True) -> None:
        """Create service with a Database instance or path.
        
        Args:
            db: Database instance or path to sqlite file. If None, defaults
                to DB_PATH from app_config.
            ensure_tables: If True, creates tables on init (safe to call repeatedly).
        """
        if isinstance(db, Database):
            self.db = db
        else:
            self.db = Database(db if isinstance(db, str) else app_config.DB_PATH)

        if ensure_tables:
            self.db.create_tables()
            self._ensure_security_columns()
            self.ensure_admin_exists()
        
        # Lazy-load loggers to avoid circular imports
        self._auth_logger = None
        self._security_logger = None
    
    @property
    def auth_logger(self):
        """Lazy load auth logger."""
        if self._auth_logger is None:
            try:
                from services.logging_service import get_auth_logger
                self._auth_logger = get_auth_logger()
            except ImportError:
                self._auth_logger = None
        return self._auth_logger
    
    @property
    def security_logger(self):
        """Lazy load security logger."""
        if self._security_logger is None:
            try:
                from services.logging_service import get_security_logger
                self._security_logger = get_security_logger()
            except ImportError:
                self._security_logger = None
        return self._security_logger
    
    def _ensure_security_columns(self) -> None:
        """Ensure security-related columns exist in users table."""
        self.db.ensure_columns_exist("users", {
            "is_disabled": "INTEGER DEFAULT 0",
            "last_login": "TIMESTAMP",
            "failed_login_attempts": "INTEGER DEFAULT 0",
            "locked_until": "TIMESTAMP",
        })

    # ----- contact availability -----
    def check_contact_availability(
        self, 
        email: Optional[str] = None, 
        phone: Optional[str] = None,
        exclude_user_id: Optional[int] = None
    ) -> Tuple[bool, Optional[str]]:
        """Check if email and/or phone are available for registration.
        
        Args:
            email: Email to check (optional)
            phone: Phone number to check - will be normalized (optional)
            exclude_user_id: User ID to exclude from check (for profile updates)
            
        Returns:
            Tuple of (is_available, error_message)
            - (True, None) if both are available
            - (False, error_message) if either is taken
        """
        if email:
            if exclude_user_id:
                existing = self.db.fetch_one(
                    "SELECT id FROM users WHERE email = ? AND id != ?", 
                    (email, exclude_user_id)
                )
            else:
                existing = self.db.fetch_one(
                    "SELECT id FROM users WHERE email = ?", 
                    (email,)
                )
            if existing:
                return False, "This email is already registered"
        
        if phone:
            # Normalize phone before checking
            normalized_phone = normalize_phone_number(phone)
            if not normalized_phone:
                return False, "Invalid phone number format"
            
            if exclude_user_id:
                existing = self.db.fetch_one(
                    "SELECT id FROM users WHERE phone = ? AND id != ?", 
                    (normalized_phone, exclude_user_id)
                )
            else:
                existing = self.db.fetch_one(
                    "SELECT id FROM users WHERE phone = ?", 
                    (normalized_phone,)
                )
            if existing:
                return False, "This phone number is already registered"
        
        return True, None

    # ----- password helpers -----
    def _generate_salt(self) -> bytes:
        return secrets.token_bytes(app_config.SALT_LENGTH)

    def _hash_password(self, password: str, salt: bytes) -> str:
        # Use PBKDF2-HMAC-SHA256 with configurable iterations
        dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, app_config.PBKDF2_ITERATIONS)
        return dk.hex()

    # ----- public API -----
    def register_user(
        self, 
        name: str, 
        email: Optional[str] = None, 
        password: str = "", 
        phone: Optional[str] = None, 
        role: str = "user",
        skip_policy: bool = False,
        profile_picture: Optional[str] = None
    ) -> int:
        """Create a new user with hashed password.
        
        Args:
            name: User's display name (max 100 chars)
            email: Unique email address (max 255 chars) - optional if phone provided
            password: Plain-text password meeting policy requirements
            phone: Optional phone number (will be normalized to E.164 format)
            role: User role ('user' or 'admin')
            skip_policy: Skip password policy validation (for testing only)
            profile_picture: Optional filename of uploaded profile picture
            
        Returns:
            The new user's ID
            
        Raises:
            ValueError: If email/phone already exists or validation fails
            AuthServiceError: If database operation fails
        """
        # Validate inputs
        if not name or len(name) > app_config.MAX_NAME_LENGTH:
            raise ValueError(f"Name must be 1-{app_config.MAX_NAME_LENGTH} characters")
        
        # Must have at least email or phone
        if not email and not phone:
            raise ValueError("Email or phone number is required")
        
        if email and len(email) > app_config.MAX_EMAIL_LENGTH:
            raise ValueError(f"Email must be at most {app_config.MAX_EMAIL_LENGTH} characters")
        
        # Normalize phone number if provided
        normalized_phone = None
        if phone:
            normalized_phone = normalize_phone_number(phone)
            if not normalized_phone:
                raise ValueError("Invalid phone number format")
        
        # Validate password against policy (unless explicitly skipped for testing)
        if not skip_policy:
            from services.password_policy import validate_password
            is_valid, errors = validate_password(password)
            if not is_valid:
                raise ValueError(errors[0])  # Return first error
        else:
            # Basic length check for testing
            if not password or len(password) < app_config.MIN_PASSWORD_LENGTH:
                raise ValueError(f"Password must be at least {app_config.MIN_PASSWORD_LENGTH} characters")
        
        if len(password) > app_config.MAX_PASSWORD_LENGTH:
            raise ValueError(f"Password must be at most {app_config.MAX_PASSWORD_LENGTH} characters")
        
        # Check for existing email/phone using the new method
        try:
            is_available, error_msg = self.check_contact_availability(email, normalized_phone)
            if not is_available:
                raise ValueError(error_msg)

            salt = self._generate_salt()
            password_hash = self._hash_password(password, salt)
            salt_hex = salt.hex()

            sql = """INSERT INTO users (name, email, phone, password_hash, password_salt, role, profile_picture) VALUES (?, ?, ?, ?, ?, ?, ?)"""
            user_id = self.db.execute(sql, (name, email, normalized_phone, password_hash, salt_hex, role, profile_picture))
            return user_id
        except ValueError:
            raise  # Re-raise validation errors
        except Exception as e:
            raise AuthServiceError(f"Failed to register user: {e}", AuthResult.DATABASE_ERROR)

    def login(self, email_or_phone: str, password: str) -> Tuple[Optional[Dict[str, Any]], AuthResult]:
        """Verify credentials and return user data with result status.
        
        Uses constant-time comparison to prevent timing attacks.
        Implements lockout after failed attempts.
        
        Args:
            email_or_phone: User's email address or phone number
            password: Plain-text password to verify
            
        Returns:
            Tuple of (user_dict or None, AuthResult enum)
        """
        if not email_or_phone or not password:
            return None, AuthResult.INVALID_INPUT
        
        # Try to find user by email first
        row = self.db.fetch_one("SELECT * FROM users WHERE email = ?", (email_or_phone,))
        if not row:
            # Try finding by phone number - normalize input first
            normalized_phone = normalize_phone_number(email_or_phone)
            if normalized_phone:
                row = self.db.fetch_one("SELECT * FROM users WHERE phone = ?", (normalized_phone,))
            
            # If still not found, try the raw input as fallback (for legacy data)
            if not row:
                row = self.db.fetch_one("SELECT * FROM users WHERE phone = ?", (email_or_phone,))
        
        if not row:
            # Log failed attempt for unknown email/phone
            if self.auth_logger:
                self.auth_logger.log_login_failure(email_or_phone, "user_not_found")
            return None, AuthResult.USER_NOT_FOUND
        
        email = row.get("email")  # Get the actual email for logging
        
        # Check if account is disabled
        if row.get("is_disabled"):
            if self.auth_logger:
                self.auth_logger.log_login_failure(email, "account_disabled")
            return None, AuthResult.ACCOUNT_DISABLED
        
        # Check if account is locked
        locked_until = row.get("locked_until")
        if locked_until:
            try:
                if isinstance(locked_until, str):
                    locked_until = datetime.fromisoformat(locked_until)
                
                if datetime.utcnow() < locked_until:
                    # Still locked
                    remaining = (locked_until - datetime.utcnow()).seconds // 60 + 1
                    if self.auth_logger:
                        self.auth_logger.log_login_failure(
                            email, "account_locked", 
                            row.get("failed_login_attempts")
                        )
                    return None, AuthResult.ACCOUNT_LOCKED
                else:
                    # Lock expired, clear it
                    self._clear_lockout(row["id"])
                    if self.auth_logger:
                        self.auth_logger.log_lockout_expired(email)
            except (ValueError, TypeError):
                pass

        stored_hash = row.get("password_hash")
        stored_salt = row.get("password_salt")
        if not stored_hash or not stored_salt:
            return None, AuthResult.INVALID_CREDENTIALS

        try:
            salt = bytes.fromhex(stored_salt)
        except (ValueError, TypeError) as e:
            print(f"[ERROR] Invalid salt format for user {email}: {e}")
            return None, AuthResult.DATABASE_ERROR

        attempted = self._hash_password(password, salt)
        if hmac.compare_digest(attempted, stored_hash):
            # Successful login - clear failed attempts and update last_login
            self._record_successful_login(row["id"])
            
            if self.auth_logger:
                self.auth_logger.log_login_success(email, row["id"])
            
            # remove sensitive fields before returning
            safe = dict(row)
            safe.pop("password_hash", None)
            safe.pop("password_salt", None)
            return safe, AuthResult.SUCCESS
        
        # Failed login - increment attempts
        result = self._record_failed_login(row["id"], email)
        return None, result
    
    def login_simple(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """Simplified login that returns user dict or None.
        
        This is for backward compatibility with existing code.
        
        Args:
            email: User's email address
            password: Plain-text password to verify
            
        Returns:
            User dict (without password fields) if valid, None otherwise
        """
        user, result = self.login(email, password)
        return user
    
    def _record_successful_login(self, user_id: int) -> None:
        """Record a successful login.
        
        Args:
            user_id: User's ID
        """
        local_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.db.execute(
            """
            UPDATE users SET 
                failed_login_attempts = 0,
                locked_until = NULL,
                last_login = ?
            WHERE id = ?
            """,
            (local_now, user_id)
        )
    
    def _record_failed_login(self, user_id: int, email: str) -> AuthResult:
        """Record a failed login attempt.
        
        Args:
            user_id: User's ID
            email: User's email for logging
            
        Returns:
            AuthResult indicating the outcome
        """
        # Get current attempt count
        user = self.db.fetch_one(
            "SELECT failed_login_attempts FROM users WHERE id = ?",
            (user_id,)
        )
        
        current_attempts = (user.get("failed_login_attempts") or 0) + 1
        max_attempts = getattr(app_config, 'MAX_FAILED_LOGIN_ATTEMPTS', 5)
        lockout_minutes = getattr(app_config, 'LOCKOUT_DURATION_MINUTES', 15)
        
        if current_attempts >= max_attempts:
            # Lock the account
            locked_until = datetime.utcnow() + timedelta(minutes=lockout_minutes)
            self.db.execute(
                """
                UPDATE users SET 
                    failed_login_attempts = ?,
                    locked_until = ?
                WHERE id = ?
                """,
                (current_attempts, locked_until.isoformat(), user_id)
            )
            
            if self.auth_logger:
                self.auth_logger.log_lockout(email, lockout_minutes)
            if self.security_logger:
                self.security_logger.log_brute_force_attempt(email, current_attempts)
            
            return AuthResult.ACCOUNT_LOCKED
        else:
            # Just increment the counter
            self.db.execute(
                "UPDATE users SET failed_login_attempts = ? WHERE id = ?",
                (current_attempts, user_id)
            )
            
            if self.auth_logger:
                self.auth_logger.log_login_failure(
                    email, "invalid_credentials", current_attempts
                )
            
            return AuthResult.INVALID_CREDENTIALS
    
    def _clear_lockout(self, user_id: int) -> None:
        """Clear lockout status for a user.
        
        Args:
            user_id: User's ID
        """
        self.db.execute(
            """
            UPDATE users SET 
                failed_login_attempts = 0,
                locked_until = NULL
            WHERE id = ?
            """,
            (user_id,)
        )
    
    def get_lockout_status(self, email_or_phone: str) -> Tuple[bool, Optional[int]]:
        """Check if an account is locked and get remaining time.
        
        Args:
            email_or_phone: User's email or phone number
            
        Returns:
            Tuple of (is_locked, remaining_minutes)
        """
        row = self.db.fetch_one(
            "SELECT locked_until, failed_login_attempts FROM users WHERE email = ?",
            (email_or_phone,)
        )
        if not row:
            row = self.db.fetch_one(
                "SELECT locked_until, failed_login_attempts FROM users WHERE phone = ?",
                (email_or_phone,)
            )
        
        if not row or not row.get("locked_until"):
            return False, None
        
        try:
            locked_until_str = row["locked_until"]
            if locked_until_str:
                # Parse ISO format timestamp
                locked_until = datetime.fromisoformat(locked_until_str)
                
                now = datetime.utcnow()
                if now < locked_until:
                    remaining = int((locked_until - now).total_seconds() / 60) + 1
                    return True, remaining
        except (ValueError, TypeError) as e:
            print(f"[WARN] Could not parse lockout time: {e}")
        
        return False, None
    
    def get_failed_login_attempts(self, email_or_phone: str) -> Optional[int]:
        """Get the current failed login attempt count for an email or phone.
        
        Args:
            email_or_phone: User's email or phone number
            
        Returns:
            Number of failed attempts or None if user not found
        """
        row = self.db.fetch_one(
            "SELECT failed_login_attempts FROM users WHERE email = ?",
            (email_or_phone,)
        )
        if not row:
            row = self.db.fetch_one(
                "SELECT failed_login_attempts FROM users WHERE phone = ?",
                (email_or_phone,)
            )
        
        if not row:
            return None
        
        return row.get("failed_login_attempts", 0) or 0

    def login_oauth(self, email: str, name: str, oauth_provider: str = "google", 
                    profile_picture: Optional[str] = None) -> Tuple[Dict[str, Any], AuthResult]:
        """Login or register a user via OAuth provider.
        
        If the user doesn't exist, creates a new account without password.
        If the user exists with OAuth already linked, logs them in.
        If the user exists with password but no OAuth, returns OAUTH_CONFLICT.
        
        Args:
            email: User's email from OAuth provider
            name: User's display name from OAuth provider
            oauth_provider: The OAuth provider name (e.g., 'google')
            profile_picture: Optional URL to user's profile picture (will be downloaded and saved)
            
        Returns:
            Tuple of (user_dict, AuthResult)
            - On success: (user_dict, AuthResult.SUCCESS)
            - On conflict: (existing_user_dict, AuthResult.OAUTH_CONFLICT)
            
        Raises:
            AuthServiceError: If operation fails
        """
        if not email:
            raise AuthServiceError("Email is required for OAuth login", AuthResult.INVALID_INPUT)
        
        try:
            # Download and save the profile picture if provided as URL
            saved_picture = None
            if profile_picture and profile_picture.startswith(("http://", "https://")):
                saved_picture = _download_and_save_profile_picture(profile_picture, email)
            elif profile_picture:
                # Already a filename, keep it
                saved_picture = profile_picture
            
            # Check if user already exists
            existing = self.db.fetch_one("SELECT * FROM users WHERE email = ?", (email,))
            
            if existing:
                # User exists - check if they already have this OAuth provider linked
                existing_oauth = existing.get("oauth_provider")
                has_password = bool(existing.get("password_hash"))
                
                if existing_oauth == oauth_provider:
                    # Same OAuth provider - just update and log in
                    update_picture = saved_picture or existing.get("profile_picture")
                    local_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    self.db.execute(
                        """UPDATE users SET profile_picture = ?, last_login = ? 
                           WHERE id = ?""",
                        (update_picture, local_now, existing["id"])
                    )
                    
                    if self.auth_logger:
                        self.auth_logger.log_login_success(email, existing["id"], oauth_provider=oauth_provider)
                    
                    safe = dict(existing)
                    safe.pop("password_hash", None)
                    safe.pop("password_salt", None)
                    safe["profile_picture"] = update_picture
                    return safe, AuthResult.SUCCESS
                
                elif has_password and not existing_oauth:
                    # User has password account but no OAuth linked
                    # Return conflict - let UI handle whether to link
                    safe = dict(existing)
                    safe.pop("password_hash", None)
                    safe.pop("password_salt", None)
                    return safe, AuthResult.OAUTH_CONFLICT
                
                else:
                    # User has different OAuth provider or OAuth already set
                    # Update to new OAuth provider and log in
                    update_picture = saved_picture or existing.get("profile_picture")
                    local_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    self.db.execute(
                        """UPDATE users SET oauth_provider = ?, profile_picture = ?, last_login = ? 
                           WHERE id = ?""",
                        (oauth_provider, update_picture, local_now, existing["id"])
                    )
                    
                    if self.auth_logger:
                        self.auth_logger.log_login_success(email, existing["id"], oauth_provider=oauth_provider)
                    
                    safe = dict(existing)
                    safe.pop("password_hash", None)
                    safe.pop("password_salt", None)
                    safe["oauth_provider"] = oauth_provider
                    safe["profile_picture"] = update_picture
                    return safe, AuthResult.SUCCESS
            
            # Create new OAuth user (no password) with last_login set
            local_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            sql = """INSERT INTO users (name, email, oauth_provider, profile_picture, role, last_login) 
                     VALUES (?, ?, ?, ?, ?, ?)"""
            user_id = self.db.execute(sql, (name, email, oauth_provider, saved_picture, "user", local_now))
            
            # Log successful OAuth registration/login
            if self.auth_logger:
                self.auth_logger.log_login_success(email, user_id, oauth_provider=oauth_provider)
            
            return {
                "id": user_id,
                "name": name,
                "email": email,
                "oauth_provider": oauth_provider,
                "profile_picture": saved_picture,
                "role": "user",
            }, AuthResult.SUCCESS
            
        except Exception as e:
            raise AuthServiceError(f"OAuth login failed: {e}", AuthResult.DATABASE_ERROR)
    
    def link_google_account(self, user_id: int, oauth_provider: str = "google") -> Tuple[bool, str]:
        """Link a Google account to an existing password-based account.
        
        Args:
            user_id: The user's ID
            oauth_provider: OAuth provider name (default: 'google')
            
        Returns:
            Tuple of (success, message)
        """
        try:
            user = self.db.fetch_one("SELECT * FROM users WHERE id = ?", (user_id,))
            if not user:
                return False, "User not found"
            
            if user.get("oauth_provider"):
                return False, f"Account is already linked to {user.get('oauth_provider')}"
            
            self.db.execute(
                "UPDATE users SET oauth_provider = ? WHERE id = ?",
                (oauth_provider, user_id)
            )
            
            # Log if logger supports it
            if self.auth_logger and hasattr(self.auth_logger, 'log_oauth_linked'):
                self.auth_logger.log_oauth_linked(user.get("email"), oauth_provider)
            
            return True, f"Successfully linked {oauth_provider} account"
            
        except Exception as e:
            return False, f"Failed to link account: {e}"
    
    def unlink_google_account(self, user_id: int) -> Tuple[bool, str]:
        """Unlink a Google account from a password-based account.
        
        Requires the user to have a password set (can't leave them with no login method).
        
        Args:
            user_id: The user's ID
            
        Returns:
            Tuple of (success, message)
        """
        try:
            user = self.db.fetch_one("SELECT * FROM users WHERE id = ?", (user_id,))
            if not user:
                return False, "User not found"
            
            if not user.get("oauth_provider"):
                return False, "No Google account is linked"
            
            # Check if user has a password - if not, they can't unlink
            if not user.get("password_hash"):
                return False, "Cannot unlink Google account - no password set. Please set a password first."
            
            old_provider = user.get("oauth_provider")
            self.db.execute(
                "UPDATE users SET oauth_provider = NULL WHERE id = ?",
                (user_id,)
            )
            
            # Log if logger supports it
            if self.auth_logger and hasattr(self.auth_logger, 'log_oauth_unlinked'):
                self.auth_logger.log_oauth_unlinked(user.get("email"), old_provider)
            
            return True, "Successfully unlinked Google account"
            
        except Exception as e:
            return False, f"Failed to unlink account: {e}"

    def get_user_role(self, user_id: int) -> Optional[str]:
        """Get the role for a user by ID.
        
        Args:
            user_id: The user's database ID
            
        Returns:
            Role string ('user' or 'admin') or None if not found
        """
        row = self.db.fetch_one("SELECT role FROM users WHERE id = ?", (user_id,))
        if not row:
            return None
        return row.get("role")

    def ensure_admin_exists(self) -> None:
        """Ensure default admin account exists in database.

        Creates admin account with credentials from app_config (can be overridden via env vars).
        Also removes any old admin accounts that don't match the current configured email.
        This ensures that changing ADMIN_EMAIL in .env takes effect properly.
        """
        try:
            # First, check if the configured admin email already exists
            existing = self.db.fetch_one("SELECT id FROM users WHERE email = ?", (app_config.DEFAULT_ADMIN_EMAIL,))
            
            if existing is None:
                # Create the new admin account
                self.register_user(
                    name=app_config.DEFAULT_ADMIN_NAME,
                    email=app_config.DEFAULT_ADMIN_EMAIL,
                    password=app_config.DEFAULT_ADMIN_PASSWORD,
                    phone=None,
                    role="admin",
                )
            
            # Remove any other admin accounts that don't match the configured email
            # This ensures old admin emails no longer work after changing .env
            self.db.execute(
                "DELETE FROM users WHERE role = 'admin' AND email != ?",
                (app_config.DEFAULT_ADMIN_EMAIL,)
            )
        except ValueError:
            # Admin already exists, which is expected on subsequent runs
            pass
        except Exception as e:
            # Unexpected error during admin creation - log for debugging
            print(f"[ERROR] Unexpected error creating admin user: {e}")


__all__ = ["AuthService", "AuthServiceError", "AuthResult"]
