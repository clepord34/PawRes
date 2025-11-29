"""Authentication service for user registration and login.

Provides secure authentication with:
- PBKDF2-HMAC-SHA256 password hashing
- Configurable iterations and salt length
- Automatic admin user creation
- Secure password verification using constant-time comparison
"""
from __future__ import annotations

import hashlib
import hmac
import secrets
from typing import Any, Dict, Optional
from enum import Enum

from storage.database import Database
import app_config


class AuthResult(Enum):
    """Authentication operation results."""
    SUCCESS = "success"
    INVALID_CREDENTIALS = "invalid_credentials"
    USER_NOT_FOUND = "user_not_found"
    EMAIL_EXISTS = "email_exists"
    INVALID_INPUT = "invalid_input"
    DATABASE_ERROR = "database_error"


class AuthServiceError(Exception):
    """Base exception for auth service errors."""
    
    def __init__(self, message: str, result: AuthResult = AuthResult.DATABASE_ERROR):
        super().__init__(message)
        self.result = result


class AuthService:
    """Authentication service backed by SQLite database.
    
    Provides user registration, login, and role management with
    secure password hashing using PBKDF2-HMAC-SHA256.
    
    Attributes:
        db: Database instance for persistence
    
    Example:
        auth = AuthService("app.db")
        user_id = auth.register_user("Alice", "alice@example.com", "secret123")
        user = auth.login("alice@example.com", "secret123")
    """

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
            self.ensure_admin_exists()

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
        email: str, 
        password: str, 
        phone: Optional[str] = None, 
        role: str = "user"
    ) -> int:
        """Create a new user with hashed password.
        
        Args:
            name: User's display name (max 100 chars)
            email: Unique email address (max 255 chars)
            password: Plain-text password (min 6 chars)
            phone: Optional phone number (max 20 chars)
            role: User role ('user' or 'admin')
            
        Returns:
            The new user's ID
            
        Raises:
            ValueError: If email already exists or validation fails
            AuthServiceError: If database operation fails
        """
        # Validate inputs
        if not name or len(name) > app_config.MAX_NAME_LENGTH:
            raise ValueError(f"Name must be 1-{app_config.MAX_NAME_LENGTH} characters")
        if not email or len(email) > app_config.MAX_EMAIL_LENGTH:
            raise ValueError(f"Email must be 1-{app_config.MAX_EMAIL_LENGTH} characters")
        if not password or len(password) < app_config.MIN_PASSWORD_LENGTH:
            raise ValueError(f"Password must be at least {app_config.MIN_PASSWORD_LENGTH} characters")
        if len(password) > app_config.MAX_PASSWORD_LENGTH:
            raise ValueError(f"Password must be at most {app_config.MAX_PASSWORD_LENGTH} characters")
        
        # Check for existing email
        try:
            existing = self.db.fetch_one("SELECT id FROM users WHERE email = ?", (email,))
            if existing is not None:
                raise ValueError("A user with that email already exists")

            salt = self._generate_salt()
            password_hash = self._hash_password(password, salt)
            salt_hex = salt.hex()

            sql = """INSERT INTO users (name, email, phone, password_hash, password_salt, role) VALUES (?, ?, ?, ?, ?, ?)"""
            user_id = self.db.execute(sql, (name, email, phone, password_hash, salt_hex, role))
            return user_id
        except ValueError:
            raise  # Re-raise validation errors
        except Exception as e:
            raise AuthServiceError(f"Failed to register user: {e}", AuthResult.DATABASE_ERROR)

    def login(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """Verify credentials and return user data.
        
        Uses constant-time comparison to prevent timing attacks.
        
        Args:
            email: User's email address
            password: Plain-text password to verify
            
        Returns:
            User dict (without password fields) if valid, None otherwise
        """
        if not email or not password:
            return None
            
        row = self.db.fetch_one("SELECT * FROM users WHERE email = ?", (email,))
        if not row:
            return None

        stored_hash = row.get("password_hash")
        stored_salt = row.get("password_salt")
        if not stored_hash or not stored_salt:
            return None

        try:
            salt = bytes.fromhex(stored_salt)
        except (ValueError, TypeError) as e:
            # Invalid salt format in database
            print(f"[ERROR] Invalid salt format for user {email}: {e}")
            return None

        attempted = self._hash_password(password, salt)
        if hmac.compare_digest(attempted, stored_hash):
            # remove sensitive fields before returning
            safe = dict(row)
            safe.pop("password_hash", None)
            safe.pop("password_salt", None)
            return safe
        return None

    def login_oauth(self, email: str, name: str, oauth_provider: str = "google", 
                    profile_picture: Optional[str] = None) -> Dict[str, Any]:
        """Login or register a user via OAuth provider.
        
        If the user doesn't exist, creates a new account without password.
        If the user exists with OAuth, logs them in.
        If the user exists with password, links the OAuth account.
        
        Args:
            email: User's email from OAuth provider
            name: User's display name from OAuth provider
            oauth_provider: The OAuth provider name (e.g., 'google')
            profile_picture: Optional URL to user's profile picture
            
        Returns:
            User dict with account information
            
        Raises:
            AuthServiceError: If operation fails
        """
        if not email:
            raise AuthServiceError("Email is required for OAuth login", AuthResult.INVALID_INPUT)
        
        try:
            # Check if user already exists
            existing = self.db.fetch_one("SELECT * FROM users WHERE email = ?", (email,))
            
            if existing:
                # User exists - update OAuth info and return
                self.db.execute(
                    """UPDATE users SET oauth_provider = ?, profile_picture = ? 
                       WHERE id = ?""",
                    (oauth_provider, profile_picture, existing["id"])
                )
                safe = dict(existing)
                safe.pop("password_hash", None)
                safe.pop("password_salt", None)
                safe["oauth_provider"] = oauth_provider
                safe["profile_picture"] = profile_picture
                return safe
            
            # Create new OAuth user (no password)
            sql = """INSERT INTO users (name, email, oauth_provider, profile_picture, role) 
                     VALUES (?, ?, ?, ?, ?)"""
            user_id = self.db.execute(sql, (name, email, oauth_provider, profile_picture, "user"))
            
            return {
                "id": user_id,
                "name": name,
                "email": email,
                "oauth_provider": oauth_provider,
                "profile_picture": profile_picture,
                "role": "user",
            }
            
        except Exception as e:
            raise AuthServiceError(f"OAuth login failed: {e}", AuthResult.DATABASE_ERROR)

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
