"""User management service for admin operations.

Provides:
- User CRUD operations (create, read, update, delete)
- User enabling/disabling
- Password reset by admin
- Role management
"""
from __future__ import annotations

import hashlib
import secrets
from typing import Any, Dict, List, Optional

from storage.database import Database
from services.logging_service import get_admin_logger, get_auth_logger
from services.password_policy import (
    get_password_policy,
    PasswordHistoryManager
)
import app_config


class UserServiceError(Exception):
    """Exception raised by UserService operations."""
    pass


class UserService:
    """Service for user management operations.
    
    Provides admin-level user management including creation,
    listing, editing, disabling, and deletion.
    
    Example:
        service = UserService()
        users = service.list_users()
        service.create_user(admin_id=1, name="John", email="john@example.com", password="Pass123!", role="user")
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize the user service.
        
        Args:
            db_path: Path to database file
        """
        self.db = Database(db_path or app_config.DB_PATH)
        self.admin_logger = get_admin_logger()
        self.auth_logger = get_auth_logger()
        self.password_policy = get_password_policy()
        self.password_history = PasswordHistoryManager(db_path or app_config.DB_PATH)
        self._ensure_columns()
    
    def _ensure_columns(self) -> None:
        """Ensure required columns exist in users table."""
        self.db.ensure_columns_exist("users", {
            "is_disabled": "INTEGER DEFAULT 0",
            "last_login": "TIMESTAMP",
            "failed_login_attempts": "INTEGER DEFAULT 0",
            "locked_until": "TIMESTAMP",
        })
    
    # ----- Read Operations -----
    
    def list_users(
        self,
        include_disabled: bool = True,
        role_filter: Optional[str] = None,
        search: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List all users with optional filtering.
        
        Args:
            include_disabled: Whether to include disabled users
            role_filter: Filter by role ('admin' or 'user')
            search: Search term for name or email
            
        Returns:
            List of user dictionaries (without password fields)
        """
        sql = """
        SELECT id, name, email, phone, role, is_disabled, 
               last_login, created_at, updated_at,
               oauth_provider, profile_picture,
               failed_login_attempts, locked_until
        FROM users 
        WHERE 1=1
        """
        params = []
        
        if not include_disabled:
            sql += " AND (is_disabled = 0 OR is_disabled IS NULL)"
        
        if role_filter:
            sql += " AND role = ?"
            params.append(role_filter)
        
        if search:
            sql += " AND (name LIKE ? OR email LIKE ?)"
            search_term = f"%{search}%"
            params.extend([search_term, search_term])
        
        sql += " ORDER BY created_at DESC"
        
        return self.db.fetch_all(sql, params)
    
    def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get a user by ID.
        
        Args:
            user_id: User's ID
            
        Returns:
            User dictionary or None if not found
        """
        return self.db.fetch_one(
            """
            SELECT id, name, email, phone, role, is_disabled,
                   last_login, created_at, updated_at,
                   oauth_provider, profile_picture,
                   failed_login_attempts, locked_until
            FROM users WHERE id = ?
            """,
            (user_id,)
        )
    
    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get a user by email.
        
        Args:
            email: User's email
            
        Returns:
            User dictionary or None if not found
        """
        return self.db.fetch_one(
            """
            SELECT id, name, email, phone, role, is_disabled,
                   last_login, created_at, updated_at,
                   oauth_provider, profile_picture,
                   failed_login_attempts, locked_until
            FROM users WHERE email = ?
            """,
            (email,)
        )
    
    # ----- Create Operations -----
    
    def create_user(
        self,
        admin_id: int,
        name: str,
        email: str,
        password: str,
        role: str = "user",
        phone: Optional[str] = None,
        validate_password: bool = True
    ) -> int:
        """Create a new user (admin operation).
        
        Args:
            admin_id: ID of admin performing the action
            name: User's display name
            email: User's email address
            password: Initial password
            role: User role ('user' or 'admin')
            phone: Optional phone number
            validate_password: Whether to validate against password policy
            
        Returns:
            ID of created user
            
        Raises:
            UserServiceError: If validation fails or email exists
        """
        # Validate inputs
        if not name or len(name) > app_config.MAX_NAME_LENGTH:
            raise UserServiceError(
                f"Name must be 1-{app_config.MAX_NAME_LENGTH} characters"
            )
        
        if not email or len(email) > app_config.MAX_EMAIL_LENGTH:
            raise UserServiceError(
                f"Email must be 1-{app_config.MAX_EMAIL_LENGTH} characters"
            )
        
        if role not in ("user", "admin"):
            raise UserServiceError("Role must be 'user' or 'admin'")
        
        # Check for existing email
        existing = self.db.fetch_one(
            "SELECT id FROM users WHERE email = ?", (email,)
        )
        if existing:
            raise UserServiceError("A user with that email already exists")
        
        # Validate password
        if validate_password:
            is_valid, errors = self.password_policy.validate(password)
            if not is_valid:
                raise UserServiceError("\n".join(errors))
        
        # Hash password
        salt = secrets.token_bytes(app_config.SALT_LENGTH)
        password_hash = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), salt, app_config.PBKDF2_ITERATIONS
        ).hex()
        salt_hex = salt.hex()
        
        # Create user
        user_id = self.db.execute(
            """
            INSERT INTO users (name, email, phone, password_hash, password_salt, role, is_disabled)
            VALUES (?, ?, ?, ?, ?, ?, 0)
            """,
            (name, email, phone, password_hash, salt_hex, role)
        )
        
        # Add to password history
        self.password_history.add_to_history(
            user_id, password_hash, salt_hex, self.password_policy.history_count
        )
        
        # Log the action
        self.admin_logger.log_user_created(admin_id, user_id, email, role)
        
        return user_id
    
    # ----- Update Operations -----
    
    def update_user(
        self,
        admin_id: int,
        user_id: int,
        name: Optional[str] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        role: Optional[str] = None
    ) -> bool:
        """Update user information (admin operation).
        
        Args:
            admin_id: ID of admin performing the action
            user_id: ID of user to update
            name: New name (optional)
            email: New email (optional)
            phone: New phone (optional)
            role: New role (optional)
            
        Returns:
            True if update succeeded
            
        Raises:
            UserServiceError: If validation fails
        """
        user = self.get_user(user_id)
        if not user:
            raise UserServiceError("User not found")
        
        updates = []
        params = []
        
        if name is not None:
            if not name or len(name) > app_config.MAX_NAME_LENGTH:
                raise UserServiceError(
                    f"Name must be 1-{app_config.MAX_NAME_LENGTH} characters"
                )
            updates.append("name = ?")
            params.append(name)
        
        if email is not None:
            if not email or len(email) > app_config.MAX_EMAIL_LENGTH:
                raise UserServiceError(
                    f"Email must be 1-{app_config.MAX_EMAIL_LENGTH} characters"
                )
            # Check for duplicate email
            existing = self.db.fetch_one(
                "SELECT id FROM users WHERE email = ? AND id != ?",
                (email, user_id)
            )
            if existing:
                raise UserServiceError("Email already in use")
            updates.append("email = ?")
            params.append(email)
        
        if phone is not None:
            updates.append("phone = ?")
            params.append(phone)
        
        if role is not None:
            if role not in ("user", "admin"):
                raise UserServiceError("Role must be 'user' or 'admin'")
            old_role = user.get("role")
            if old_role != role:
                updates.append("role = ?")
                params.append(role)
                # Log role change
                self.admin_logger.log_role_changed(
                    admin_id, user_id, user.get("email"), old_role, role
                )
        
        if not updates:
            return True  # Nothing to update
        
        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.append(user_id)
        
        self.db.execute(
            f"UPDATE users SET {', '.join(updates)} WHERE id = ?",
            params
        )
        
        return True
    
    def reset_password(
        self,
        admin_id: int,
        user_id: int,
        new_password: str,
        validate_password: bool = True,
        check_history: bool = False
    ) -> bool:
        """Reset a user's password (admin operation).
        
        Args:
            admin_id: ID of admin performing the action
            user_id: ID of user whose password to reset
            new_password: New password
            validate_password: Whether to validate against policy
            check_history: Whether to check password history
            
        Returns:
            True if reset succeeded
            
        Raises:
            UserServiceError: If validation fails
        """
        user = self.get_user(user_id)
        if not user:
            raise UserServiceError("User not found")
        
        # Validate password
        if validate_password:
            is_valid, errors = self.password_policy.validate(new_password)
            if not is_valid:
                raise UserServiceError("\n".join(errors))
        
        # Check password history
        if check_history:
            allowed, error = self.password_history.check_reuse(
                user_id, new_password, self.password_policy
            )
            if not allowed:
                raise UserServiceError(error)
        
        # Hash new password
        salt = secrets.token_bytes(app_config.SALT_LENGTH)
        password_hash = hashlib.pbkdf2_hmac(
            "sha256", new_password.encode("utf-8"), salt, app_config.PBKDF2_ITERATIONS
        ).hex()
        salt_hex = salt.hex()
        
        # Update password and clear lockout
        self.db.execute(
            """
            UPDATE users SET 
                password_hash = ?, 
                password_salt = ?,
                failed_login_attempts = 0,
                locked_until = NULL,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (password_hash, salt_hex, user_id)
        )
        
        # Add to password history
        self.password_history.add_to_history(
            user_id, password_hash, salt_hex, self.password_policy.history_count
        )
        
        # Log the action
        self.admin_logger.log_password_reset(admin_id, user_id, user.get("email"))
        self.auth_logger.log_password_change(user_id, user.get("email"), admin_id)
        
        return True
    
    # ----- Enable/Disable Operations -----
    
    def disable_user(self, admin_id: int, user_id: int) -> bool:
        """Disable a user account (admin operation).
        
        Args:
            admin_id: ID of admin performing the action
            user_id: ID of user to disable
            
        Returns:
            True if disable succeeded
            
        Raises:
            UserServiceError: If user not found or is admin trying to disable self
        """
        user = self.get_user(user_id)
        if not user:
            raise UserServiceError("User not found")
        
        if admin_id == user_id:
            raise UserServiceError("Cannot disable your own account")
        
        self.db.execute(
            "UPDATE users SET is_disabled = 1, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (user_id,)
        )
        
        self.admin_logger.log_user_disabled(admin_id, user_id, user.get("email"))
        
        return True
    
    def enable_user(self, admin_id: int, user_id: int) -> bool:
        """Enable a disabled user account (admin operation).
        
        Args:
            admin_id: ID of admin performing the action
            user_id: ID of user to enable
            
        Returns:
            True if enable succeeded
            
        Raises:
            UserServiceError: If user not found
        """
        user = self.get_user(user_id)
        if not user:
            raise UserServiceError("User not found")
        
        self.db.execute(
            """
            UPDATE users SET 
                is_disabled = 0, 
                failed_login_attempts = 0,
                locked_until = NULL,
                updated_at = CURRENT_TIMESTAMP 
            WHERE id = ?
            """,
            (user_id,)
        )
        
        self.admin_logger.log_user_enabled(admin_id, user_id, user.get("email"))
        
        return True
    
    # ----- Delete Operations -----
    
    def delete_user(self, admin_id: int, user_id: int) -> bool:
        """Delete a user account (admin operation).
        
        This is a hard delete. Consider using disable_user instead.
        
        Args:
            admin_id: ID of admin performing the action
            user_id: ID of user to delete
            
        Returns:
            True if delete succeeded
            
        Raises:
            UserServiceError: If user not found or admin trying to delete self
        """
        user = self.get_user(user_id)
        if not user:
            raise UserServiceError("User not found")
        
        if admin_id == user_id:
            raise UserServiceError("Cannot delete your own account")
        
        email = user.get("email")
        
        # Delete password history first (foreign key)
        self.password_history.clear_history(user_id)
        
        # Delete user
        self.db.execute("DELETE FROM users WHERE id = ?", (user_id,))
        
        self.admin_logger.log_user_deleted(admin_id, user_id, email)
        
        return True
    
    # ----- Statistics -----
    
    def get_user_stats(self) -> Dict[str, Any]:
        """Get user statistics.
        
        Returns:
            Dictionary with user stats
        """
        total = self.db.fetch_one("SELECT COUNT(*) as count FROM users")
        admins = self.db.fetch_one(
            "SELECT COUNT(*) as count FROM users WHERE role = 'admin'"
        )
        disabled = self.db.fetch_one(
            "SELECT COUNT(*) as count FROM users WHERE is_disabled = 1"
        )
        recent = self.db.fetch_one(
            """
            SELECT COUNT(*) as count FROM users 
            WHERE created_at >= datetime('now', '-7 days')
            """
        )
        
        return {
            "total": total["count"] if total else 0,
            "admins": admins["count"] if admins else 0,
            "users": (total["count"] if total else 0) - (admins["count"] if admins else 0),
            "disabled": disabled["count"] if disabled else 0,
            "recent_signups": recent["count"] if recent else 0,
        }
    
    # ----- Profile Operations (Self-Service) -----
    
    def get_user_profile(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user profile data for self-service profile page.
        
        Args:
            user_id: User's ID
            
        Returns:
            User profile dictionary or None if not found
        """
        return self.db.fetch_one(
            """
            SELECT id, name, email, phone, role, created_at, last_login, 
                   oauth_provider, profile_picture
            FROM users WHERE id = ?
            """,
            (user_id,)
        )
    
    def update_user_profile(
        self,
        user_id: int,
        name: Optional[str] = None,
        phone: Optional[str] = None,
        profile_picture: Optional[str] = None
    ) -> bool:
        """Update user's own profile (self-service).
        
        Args:
            user_id: User's ID
            name: New name (optional)
            phone: New phone (optional)
            profile_picture: New profile picture filename (optional)
            
        Returns:
            True if update succeeded
            
        Raises:
            UserServiceError: If validation fails
        """
        from components.utils import normalize_phone_number
        
        user = self.get_user(user_id)
        if not user:
            raise UserServiceError("User not found")
        
        updates = []
        params = []
        
        if name is not None:
            if not name or len(name) > app_config.MAX_NAME_LENGTH:
                raise UserServiceError(
                    f"Name must be 1-{app_config.MAX_NAME_LENGTH} characters"
                )
            updates.append("name = ?")
            params.append(name)
        
        if phone is not None:
            if phone:
                # Normalize phone number
                normalized = normalize_phone_number(phone)
                if not normalized:
                    raise UserServiceError("Invalid phone number format")
                
                # Check for duplicate phone (excluding current user)
                existing = self.db.fetch_one(
                    "SELECT id FROM users WHERE phone = ? AND id != ?",
                    (normalized, user_id)
                )
                if existing:
                    raise UserServiceError("This phone number is already registered to another account")
                
                updates.append("phone = ?")
                params.append(normalized)
            else:
                updates.append("phone = ?")
                params.append(None)
        
        if profile_picture is not None:
            updates.append("profile_picture = ?")
            params.append(profile_picture)
        
        if not updates:
            return True  # Nothing to update
        
        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.append(user_id)
        
        self.db.execute(
            f"UPDATE users SET {', '.join(updates)} WHERE id = ?",
            params
        )
        
        return True
    
    def change_user_password(
        self,
        user_id: int,
        current_password: str,
        new_password: str
    ) -> Dict[str, Any]:
        """Change user's own password (self-service).
        
        Args:
            user_id: User's ID
            current_password: Current password for verification
            new_password: New password
            
        Returns:
            Dict with 'success' bool and optional 'error' message
        """
        import hmac
        
        # Get user with password fields
        user = self.db.fetch_one(
            "SELECT id, email, password_hash, password_salt, oauth_provider FROM users WHERE id = ?",
            (user_id,)
        )
        
        if not user:
            return {"success": False, "error": "User not found"}
        
        # Check if OAuth user (no password)
        if user.get("oauth_provider"):
            return {"success": False, "error": "Cannot change password for OAuth accounts. Use 'Set Password' instead."}
        
        stored_hash = user.get("password_hash")
        stored_salt = user.get("password_salt")
        
        if not stored_hash or not stored_salt:
            return {"success": False, "error": "Cannot change password for this account"}
        
        # Verify current password
        try:
            salt_bytes = bytes.fromhex(stored_salt)
            current_hash = hashlib.pbkdf2_hmac(
                "sha256", current_password.encode("utf-8"), salt_bytes, app_config.PBKDF2_ITERATIONS
            ).hex()
            
            if not hmac.compare_digest(current_hash, stored_hash):
                return {"success": False, "error": "Current password is incorrect"}
        except Exception:
            return {"success": False, "error": "Error verifying password"}
        
        # Validate new password against policy
        is_valid, errors = self.password_policy.validate(new_password)
        if not is_valid:
            return {"success": False, "error": errors[0]}
        
        # Check password history
        allowed, error = self.password_history.check_reuse(
            user_id, new_password, self.password_policy
        )
        if not allowed:
            return {"success": False, "error": error}
        
        # Hash new password
        new_salt = secrets.token_bytes(app_config.SALT_LENGTH)
        new_hash = hashlib.pbkdf2_hmac(
            "sha256", new_password.encode("utf-8"), new_salt, app_config.PBKDF2_ITERATIONS
        ).hex()
        new_salt_hex = new_salt.hex()
        
        # Update password
        self.db.execute(
            """
            UPDATE users SET 
                password_hash = ?, 
                password_salt = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (new_hash, new_salt_hex, user_id)
        )
        
        # Add to password history
        self.password_history.add_to_history(
            user_id, new_hash, new_salt_hex, self.password_policy.history_count
        )
        
        # Log the change
        self.auth_logger.log_password_change(user_id, user.get("email"))
        
        return {"success": True}
    
    def set_password_for_oauth_user(
        self,
        user_id: int,
        new_password: str
    ) -> Dict[str, Any]:
        """Set password for an OAuth-only user (self-service).
        
        This allows OAuth users to add a password so they can unlink
        their OAuth provider and still log in.
        
        Args:
            user_id: User's ID
            new_password: New password to set
            
        Returns:
            Dict with 'success' bool and optional 'error' message
        """
        # Get user with password fields
        user = self.db.fetch_one(
            "SELECT id, email, password_hash, oauth_provider FROM users WHERE id = ?",
            (user_id,)
        )
        
        if not user:
            return {"success": False, "error": "User not found"}
        
        # This is for OAuth users without a password
        if not user.get("oauth_provider"):
            return {"success": False, "error": "This account is not linked to an OAuth provider"}
        
        if user.get("password_hash"):
            return {"success": False, "error": "Password is already set. Use 'Change Password' instead."}
        
        # Validate new password against policy
        is_valid, errors = self.password_policy.validate(new_password)
        if not is_valid:
            return {"success": False, "error": errors[0]}
        
        # Hash new password
        new_salt = secrets.token_bytes(app_config.SALT_LENGTH)
        new_hash = hashlib.pbkdf2_hmac(
            "sha256", new_password.encode("utf-8"), new_salt, app_config.PBKDF2_ITERATIONS
        ).hex()
        new_salt_hex = new_salt.hex()
        
        # Set password
        self.db.execute(
            """
            UPDATE users SET 
                password_hash = ?, 
                password_salt = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (new_hash, new_salt_hex, user_id)
        )
        
        # Add to password history
        self.password_history.add_to_history(
            user_id, new_hash, new_salt_hex, self.password_policy.history_count
        )
        
        # Log the change
        self.auth_logger.log_password_change(user_id, user.get("email"))
        
        return {"success": True}
    
    def is_oauth_user(self, user_id: int) -> bool:
        """Check if user uses OAuth authentication.
        
        Args:
            user_id: User's ID
            
        Returns:
            True if user uses OAuth
        """
        user = self.db.fetch_one(
            "SELECT oauth_provider FROM users WHERE id = ?",
            (user_id,)
        )
        return bool(user and user.get("oauth_provider"))


__all__ = ["UserService", "UserServiceError"]
