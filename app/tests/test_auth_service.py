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
            role="user",
            skip_policy=True
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
            password="pass123",
            skip_policy=True
        )
        
        # Attempt to register with same email should raise
        with pytest.raises(ValueError, match="already exists"):
            auth_service.register_user(
                name="Second User",
                email="duplicate@example.com",
                password="differentpass",
                skip_policy=True
            )

    def test_register_user_with_admin_role(self, auth_service: AuthService):
        """Test that users can be registered with admin role."""
        user_id = auth_service.register_user(
            name="Admin User",
            email="admin@example.com",
            password="adminpass",
            role="admin",
            skip_policy=True
        )
        
        role = auth_service.get_user_role(user_id)
        assert role == "admin"


class TestUserLogin:
    """Tests for user login functionality."""

    def test_login_with_valid_credentials(self, auth_service: AuthService):
        """Test that login succeeds with correct email and password."""
        from services.auth_service import AuthResult
        
        # Register a user first
        auth_service.register_user(
            name="Login Test",
            email="login@example.com",
            password="mypassword",
            skip_policy=True
        )
        
        # Login should succeed
        user, result = auth_service.login("login@example.com", "mypassword")
        
        assert result == AuthResult.SUCCESS
        assert user is not None
        assert user["email"] == "login@example.com"
        assert user["name"] == "Login Test"
        # Password fields should be removed for security
        assert "password_hash" not in user
        assert "password_salt" not in user

    def test_login_with_wrong_password(self, auth_service: AuthService):
        """Test that login fails with incorrect password."""
        from services.auth_service import AuthResult
        
        auth_service.register_user(
            name="Wrong Pass Test",
            email="wrongpass@example.com",
            password="correctpassword",
            skip_policy=True
        )
        
        # Login with wrong password should fail
        user, result = auth_service.login("wrongpass@example.com", "wrongpassword")
        assert user is None
        assert result == AuthResult.INVALID_CREDENTIALS

    def test_login_with_nonexistent_email(self, auth_service: AuthService):
        """Test that login fails for non-existent user."""
        from services.auth_service import AuthResult
        
        user, result = auth_service.login("nonexistent@example.com", "anypassword")
        assert user is None
        assert result == AuthResult.USER_NOT_FOUND


class TestPasswordSecurity:
    """Tests for password hashing and security."""

    def test_password_is_hashed_not_plaintext(self, auth_service: AuthService, temp_db):
        """Test that passwords are stored hashed, not in plaintext."""
        auth_service.register_user(
            name="Hash Test",
            email="hash@example.com",
            password="plaintextpassword",
            skip_policy=True
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
            password="samepassword",
            skip_policy=True
        )
        auth_service.register_user(
            name="User Two",
            email="user2@example.com",
            password="samepassword",
            skip_policy=True
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
            role="user",
            skip_policy=True
        )
        
        role = auth_service.get_user_role(user_id)
        assert role == "user"

    def test_get_user_role_nonexistent_user(self, auth_service: AuthService):
        """Test that get_user_role returns None for non-existent user."""
        role = auth_service.get_user_role(99999)
        assert role is None


class TestOAuthLogin:
    """Tests for OAuth login functionality."""

    def test_login_oauth_creates_new_user(self, auth_service: AuthService):
        """Test that OAuth login creates a new user if they don't exist."""
        user = auth_service.login_oauth(
            email="oauth@example.com",
            name="OAuth User",
            oauth_provider="google",
            # Note: URL will fail to download in tests, so profile_picture will be None
            profile_picture="https://example.com/photo.jpg"
        )
        
        assert user is not None
        assert user["email"] == "oauth@example.com"
        assert user["name"] == "OAuth User"
        assert user["oauth_provider"] == "google"
        # Profile picture is None because the fake URL can't be downloaded
        # In production, real Google URLs are downloaded and saved
        assert user["profile_picture"] is None
        assert user["role"] == "user"

    def test_login_oauth_returns_existing_user(self, auth_service: AuthService):
        """Test that OAuth login returns existing user and updates OAuth info."""
        # First OAuth login creates user
        user1 = auth_service.login_oauth(
            email="returning@example.com",
            name="First Name",
            oauth_provider="google"
        )
        
        # Second OAuth login should return same user
        user2 = auth_service.login_oauth(
            email="returning@example.com",
            name="Updated Name",
            oauth_provider="google",
            # Note: URL will fail to download in tests
            profile_picture="https://new-photo.jpg"
        )
        
        assert user1["id"] == user2["id"]
        # Profile picture remains None because fake URL can't be downloaded
        assert user2["profile_picture"] is None
    
    def test_login_oauth_with_existing_filename(self, auth_service: AuthService):
        """Test that OAuth login preserves existing filename-based profile pictures."""
        # First create user with a fake filename (not URL)
        user1 = auth_service.login_oauth(
            email="filename@example.com",
            name="Filename User",
            oauth_provider="google",
            profile_picture="existing_photo.jpg"  # Already a filename, not URL
        )
        
        assert user1["profile_picture"] == "existing_photo.jpg"
        
        # Second login without picture should keep existing
        user2 = auth_service.login_oauth(
            email="filename@example.com",
            name="Filename User",
            oauth_provider="google"
        )
        
        assert user2["profile_picture"] == "existing_photo.jpg"

    def test_login_oauth_links_to_password_user(self, auth_service: AuthService):
        """Test that OAuth login links to existing password-based user."""
        # Register user with password first
        user_id = auth_service.register_user(
            name="Password User",
            email="hybrid@example.com",
            password="password123",
            skip_policy=True
        )
        
        # OAuth login with same email should link to existing account
        oauth_user = auth_service.login_oauth(
            email="hybrid@example.com",
            name="OAuth Name",
            oauth_provider="google"
        )
        
        assert oauth_user["id"] == user_id
        assert oauth_user["oauth_provider"] == "google"
        
        # User should still be able to login with password
        password_user, result = auth_service.login("hybrid@example.com", "password123")
        assert password_user is not None
        assert password_user["id"] == user_id

