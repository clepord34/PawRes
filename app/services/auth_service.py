"""Authentication service for user registration and login."""
from __future__ import annotations

import hashlib
import hmac
import secrets
from typing import Any, Dict, Optional

from storage.database import Database
import app_config


class AuthService:
    """Simple authentication service backed by `services.database.Database`.

    Args:
        db: Either a `Database` instance or a string path to sqlite file.
        ensure_tables: if True, calls `create_tables()` on the Database to
            ensure the `users` table exists (safe to call repeatedly).
    """

    def __init__(self, db: Optional[Database | str] = None, *, ensure_tables: bool = True) -> None:
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
    def register_user(self, name: str, email: str, password: str, phone: Optional[str] = None, role: str = "user") -> int:
        """Create a new user and store a hashed password.

        Raises ValueError if the email is already registered.
        Returns the new user's id.
        """
        # check for existing email
        existing = self.db.fetch_one("SELECT id FROM users WHERE email = ?", (email,))
        if existing is not None:
            raise ValueError("A user with that email already exists")

        salt = self._generate_salt()
        password_hash = self._hash_password(password, salt)
        salt_hex = salt.hex()

        sql = """INSERT INTO users (name, email, phone, password_hash, password_salt, role) VALUES (?, ?, ?, ?, ?, ?)"""
        user_id = self.db.execute(sql, (name, email, phone, password_hash, salt_hex, role))
        return user_id

    def login(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """Verify credentials. Returns user dict (without password fields) or None."""
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

    def get_user_role(self, user_id: int) -> Optional[str]:
        """Return the role string for `user_id`, or None if user not found."""
        row = self.db.fetch_one("SELECT role FROM users WHERE id = ?", (user_id,))
        if not row:
            return None
        return row.get("role")

    def ensure_admin_exists(self) -> None:
        """Ensure default admin account exists in database.

        Creates admin account with credentials from app_config (can be overridden via env vars).
        Silently handles the case where admin already exists.
        """
        try:
            existing = self.db.fetch_one("SELECT id FROM users WHERE email = ?", (app_config.DEFAULT_ADMIN_EMAIL,))
            if existing is None:
                self.register_user(
                    name=app_config.DEFAULT_ADMIN_NAME,
                    email=app_config.DEFAULT_ADMIN_EMAIL,
                    password=app_config.DEFAULT_ADMIN_PASSWORD,
                    phone=None,
                    role="admin",
                )
        except ValueError:
            # Admin already exists, which is expected on subsequent runs
            pass
        except Exception as e:
            # Unexpected error during admin creation - log for debugging
            print(f"[ERROR] Unexpected error creating admin user: {e}")


__all__ = ["AuthService"]
