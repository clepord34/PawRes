"""Unit tests for AuthService."""
from __future__ import annotations

import pytest

from services.auth_service import AuthService


class TestUserRegistration:
    """Tests for user registration functionality."""

    def test_register_user_success(self, auth_service: AuthService):
        """Test that a new user can be registered successfully."""
        user_id = auth_service.register_user(
            name="Alice Smith",
            email="alice@example.com",
            password="securepass123",
            phone="555-1234",
            role="user"
        )
        
        # Should return a valid user ID
        assert user_id is not None
        assert isinstance(user_id, int)
        assert user_id > 0

    def test_register_user_duplicate_email_raises_error(self, auth_service: AuthService):
        """Test that registering with an existing email raises ValueError."""
        # Register first user
        auth_service.register_user(
            name="First User",
            email="duplicate@example.com",
            password="pass123"
        )
        
        # Attempt to register with same email should raise
        with pytest.raises(ValueError, match="already exists"):
            auth_service.register_user(
                name="Second User",
                email="duplicate@example.com",
                password="differentpass"
            )

    def test_register_user_with_admin_role(self, auth_service: AuthService):
        """Test that users can be registered with admin role."""
        user_id = auth_service.register_user(
            name="Admin User",
            email="admin@example.com",
            password="adminpass",
            role="admin"
        )
        
        role = auth_service.get_user_role(user_id)
        assert role == "admin"


class TestUserLogin:
    """Tests for user login functionality."""

    def test_login_with_valid_credentials(self, auth_service: AuthService):
        """Test that login succeeds with correct email and password."""
        # Register a user first
        auth_service.register_user(
            name="Login Test",
            email="login@example.com",
            password="mypassword"
        )
        
        # Login should succeed
        user = auth_service.login("login@example.com", "mypassword")
        
        assert user is not None
        assert user["email"] == "login@example.com"
        assert user["name"] == "Login Test"
        # Password fields should be removed for security
        assert "password_hash" not in user
        assert "password_salt" not in user

    def test_login_with_wrong_password(self, auth_service: AuthService):
        """Test that login fails with incorrect password."""
        auth_service.register_user(
            name="Wrong Pass Test",
            email="wrongpass@example.com",
            password="correctpassword"
        )
        
        # Login with wrong password should fail
        user = auth_service.login("wrongpass@example.com", "wrongpassword")
        assert user is None

    def test_login_with_nonexistent_email(self, auth_service: AuthService):
        """Test that login fails for non-existent user."""
        user = auth_service.login("nonexistent@example.com", "anypassword")
        assert user is None


class TestPasswordSecurity:
    """Tests for password hashing and security."""

    def test_password_is_hashed_not_plaintext(self, auth_service: AuthService, temp_db):
        """Test that passwords are stored hashed, not in plaintext."""
        auth_service.register_user(
            name="Hash Test",
            email="hash@example.com",
            password="plaintextpassword"
        )
        
        # Query database directly to check stored password
        row = temp_db.fetch_one("SELECT password_hash, password_salt FROM users WHERE email = ?", 
                                ("hash@example.com",))
        
        assert row is not None
        # Password hash should not be the plaintext
        assert row["password_hash"] != "plaintextpassword"
        # Should have a salt
        assert row["password_salt"] is not None
        assert len(row["password_salt"]) > 0

    def test_same_password_different_hash(self, auth_service: AuthService, temp_db):
        """Test that same password produces different hashes (due to unique salt)."""
        auth_service.register_user(
            name="User One",
            email="user1@example.com",
            password="samepassword"
        )
        auth_service.register_user(
            name="User Two",
            email="user2@example.com",
            password="samepassword"
        )
        
        row1 = temp_db.fetch_one("SELECT password_hash FROM users WHERE email = ?", 
                                 ("user1@example.com",))
        row2 = temp_db.fetch_one("SELECT password_hash FROM users WHERE email = ?", 
                                 ("user2@example.com",))
        
        # Same password should have different hashes due to unique salts
        assert row1["password_hash"] != row2["password_hash"]


class TestGetUserRole:
    """Tests for role retrieval functionality."""

    def test_get_user_role_returns_correct_role(self, auth_service: AuthService):
        """Test that get_user_role returns the correct role."""
        user_id = auth_service.register_user(
            name="Role Test",
            email="role@example.com",
            password="pass123",
            role="user"
        )
        
        role = auth_service.get_user_role(user_id)
        assert role == "user"

    def test_get_user_role_nonexistent_user(self, auth_service: AuthService):
        """Test that get_user_role returns None for non-existent user."""
        role = auth_service.get_user_role(99999)
        assert role is None
