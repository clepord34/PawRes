"""Password policy enforcement for security compliance.

Provides:
- Password complexity validation
- Password history tracking (reuse prevention)
- Configurable policy rules
"""
from __future__ import annotations

import re
import hashlib
from typing import List, Optional, Tuple

import app_config
from storage.database import Database


class PasswordPolicy:
    """Validates passwords against security policy rules.
    
    Default requirements:
    - Minimum 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special character
    
    Example:
        policy = PasswordPolicy()
        is_valid, errors = policy.validate("MyP@ss123")
        if not is_valid:
            print("\\n".join(errors))
    """
    
    def __init__(
        self,
        min_length: int = None,
        require_uppercase: bool = None,
        require_lowercase: bool = None,
        require_digit: bool = None,
        require_special: bool = None,
        history_count: int = None
    ):
        """Initialize password policy with configurable rules.
        
        Args:
            min_length: Minimum password length
            require_uppercase: Require at least one uppercase letter
            require_lowercase: Require at least one lowercase letter
            require_digit: Require at least one digit
            require_special: Require at least one special character
            history_count: Number of previous passwords to check for reuse
        """
        self.min_length = min_length or getattr(
            app_config, 'PASSWORD_MIN_LENGTH', 8
        )
        self.require_uppercase = require_uppercase if require_uppercase is not None else getattr(
            app_config, 'PASSWORD_REQUIRE_UPPERCASE', True
        )
        self.require_lowercase = require_lowercase if require_lowercase is not None else getattr(
            app_config, 'PASSWORD_REQUIRE_LOWERCASE', True
        )
        self.require_digit = require_digit if require_digit is not None else getattr(
            app_config, 'PASSWORD_REQUIRE_DIGIT', True
        )
        self.require_special = require_special if require_special is not None else getattr(
            app_config, 'PASSWORD_REQUIRE_SPECIAL', True
        )
        self.history_count = history_count or getattr(
            app_config, 'PASSWORD_HISTORY_COUNT', 5
        )
        
        # Special characters pattern
        self.special_chars = r'[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\\/`~]'
    
    def validate(self, password: str) -> Tuple[bool, List[str]]:
        """Validate a password against policy rules.
        
        Args:
            password: The password to validate
            
        Returns:
            Tuple of (is_valid, list_of_error_messages)
        """
        errors = []
        
        if not password:
            return False, ["Password is required"]
        
        # Length check
        if len(password) < self.min_length:
            errors.append(f"Password must be at least {self.min_length} characters")
        
        # Uppercase check
        if self.require_uppercase and not re.search(r'[A-Z]', password):
            errors.append("Password must contain at least one uppercase letter")
        
        # Lowercase check
        if self.require_lowercase and not re.search(r'[a-z]', password):
            errors.append("Password must contain at least one lowercase letter")
        
        # Digit check
        if self.require_digit and not re.search(r'\d', password):
            errors.append("Password must contain at least one digit")
        
        # Special character check
        if self.require_special and not re.search(self.special_chars, password):
            errors.append("Password must contain at least one special character (!@#$%^&*...)")
        
        return len(errors) == 0, errors
    
    def get_requirements_text(self) -> str:
        """Get human-readable password requirements.
        
        Returns:
            Formatted string describing requirements
        """
        reqs = [f"• At least {self.min_length} characters"]
        
        if self.require_uppercase:
            reqs.append("• At least one uppercase letter (A-Z)")
        if self.require_lowercase:
            reqs.append("• At least one lowercase letter (a-z)")
        if self.require_digit:
            reqs.append("• At least one digit (0-9)")
        if self.require_special:
            reqs.append("• At least one special character (!@#$%^&*...)")
        
        return "\n".join(reqs)
    
    def hash_for_history(self, password: str, salt: bytes) -> str:
        """Create a hash suitable for password history comparison.
        
        Uses the same hashing as auth_service but returns consistent format.
        
        Args:
            password: The password to hash
            salt: Salt bytes to use
            
        Returns:
            Hex-encoded hash string
        """
        dk = hashlib.pbkdf2_hmac(
            "sha256", 
            password.encode("utf-8"), 
            salt, 
            app_config.PBKDF2_ITERATIONS
        )
        return dk.hex()


class PasswordHistoryManager:
    """Manages password history to prevent reuse.
    
    Stores hashed versions of previous passwords and checks
    new passwords against them.
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize the password history manager.
        
        Args:
            db_path: Path to database file
        """
        self.db = Database(db_path or app_config.DB_PATH)
        self._ensure_table()
    
    def _ensure_table(self) -> None:
        """Ensure password_history table exists."""
        sql = """
        CREATE TABLE IF NOT EXISTS password_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            password_hash TEXT NOT NULL,
            password_salt TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        """
        self.db.execute(sql)
        
        # Create index for faster lookups
        self.db.execute(
            "CREATE INDEX IF NOT EXISTS idx_password_history_user "
            "ON password_history(user_id)"
        )
    
    def add_to_history(
        self,
        user_id: int,
        password_hash: str,
        password_salt: str,
        max_history: int = 5
    ) -> None:
        """Add a password hash to the user's history.
        
        Args:
            user_id: User's ID
            password_hash: Hashed password
            password_salt: Salt used for hashing
            max_history: Maximum history entries to keep
        """
        # Add new entry
        self.db.execute(
            "INSERT INTO password_history (user_id, password_hash, password_salt) "
            "VALUES (?, ?, ?)",
            (user_id, password_hash, password_salt)
        )
        
        # Clean up old entries (keep only max_history most recent)
        self.db.execute(
            """
            DELETE FROM password_history 
            WHERE user_id = ? AND id NOT IN (
                SELECT id FROM password_history 
                WHERE user_id = ? 
                ORDER BY created_at DESC 
                LIMIT ?
            )
            """,
            (user_id, user_id, max_history)
        )
    
    def check_reuse(
        self,
        user_id: int,
        password: str,
        policy: PasswordPolicy
    ) -> Tuple[bool, Optional[str]]:
        """Check if a password was recently used.
        
        Args:
            user_id: User's ID
            password: New password to check
            policy: Password policy with history_count
            
        Returns:
            Tuple of (is_allowed, error_message)
            is_allowed is True if password is NOT in history
        """
        history = self.db.fetch_all(
            """
            SELECT password_hash, password_salt FROM password_history 
            WHERE user_id = ? 
            ORDER BY created_at DESC 
            LIMIT ?
            """,
            (user_id, policy.history_count)
        )
        
        for entry in history:
            stored_hash = entry["password_hash"]
            stored_salt = bytes.fromhex(entry["password_salt"])
            
            # Hash the new password with stored salt and compare
            test_hash = policy.hash_for_history(password, stored_salt)
            
            if test_hash == stored_hash:
                return False, f"Cannot reuse any of your last {policy.history_count} passwords"
        
        return True, None
    
    def clear_history(self, user_id: int) -> None:
        """Clear password history for a user (for testing or admin reset).
        
        Args:
            user_id: User's ID
        """
        self.db.execute(
            "DELETE FROM password_history WHERE user_id = ?",
            (user_id,)
        )


# Default policy instance
_default_policy: Optional[PasswordPolicy] = None


def get_password_policy() -> PasswordPolicy:
    """Get the default password policy instance.
    
    Returns:
        PasswordPolicy instance
    """
    global _default_policy
    if _default_policy is None:
        _default_policy = PasswordPolicy()
    return _default_policy


def validate_password(password: str) -> Tuple[bool, List[str]]:
    """Convenience function to validate a password.
    
    Args:
        password: Password to validate
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    return get_password_policy().validate(password)


__all__ = [
    "PasswordPolicy",
    "PasswordHistoryManager",
    "get_password_policy",
    "validate_password",
]
