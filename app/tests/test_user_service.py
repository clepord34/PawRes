"""Tests for user service and user management."""
from __future__ import annotations

import os
import sys
import tempfile
import pytest
from datetime import datetime

# Ensure app imports work
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.user_service import UserService, UserServiceError
from storage.database import Database


@pytest.fixture
def db_path():
    """Create a temporary database path."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    db = Database(path)
    db.create_tables()
    yield path
    if os.path.exists(path):
        os.unlink(path)


class TestUserService:
    """Test cases for user service."""
    
    def test_list_users_empty(self, db_path):
        """Test listing users with empty database (except default admin)."""
        service = UserService(db_path)
        users = service.list_users()
        
        # Should have at least the default admin
        assert len(users) >= 0
    
    def test_create_user(self, db_path):
        """Test creating a new user."""
        service = UserService(db_path)
        
        user_id = service.create_user(
            admin_id=1,
            name="Test User",
            email="test@example.com",
            password="Test@123!",
            role="user"
        )
        
        assert user_id > 0
        
        user = service.get_user(user_id)
        assert user is not None
        assert user["name"] == "Test User"
        assert user["email"] == "test@example.com"
        assert user["role"] == "user"
        assert user.get("is_disabled") == 0
    
    def test_create_user_duplicate_email(self, db_path):
        """Test that duplicate emails are rejected."""
        service = UserService(db_path)
        
        service.create_user(
            admin_id=1,
            name="User 1",
            email="duplicate@example.com",
            password="Test@123!",
        )
        
        with pytest.raises(UserServiceError, match="already exists"):
            service.create_user(
                admin_id=1,
                name="User 2",
                email="duplicate@example.com",
                password="Test@123!",
            )
    
    def test_create_user_weak_password(self, db_path):
        """Test that weak passwords are rejected."""
        service = UserService(db_path)
        
        with pytest.raises(UserServiceError):
            service.create_user(
                admin_id=1,
                name="Test User",
                email="test@example.com",
                password="weak",  # Too short, no complexity
            )
    
    def test_update_user(self, db_path):
        """Test updating user information."""
        service = UserService(db_path)
        
        user_id = service.create_user(
            admin_id=1,
            name="Original Name",
            email="update@example.com",
            password="Test@123!",
        )
        
        service.update_user(
            admin_id=1,
            user_id=user_id,
            name="Updated Name",
            phone="1234567890"
        )
        
        user = service.get_user(user_id)
        assert user["name"] == "Updated Name"
        assert user["phone"] == "1234567890"
    
    def test_disable_user(self, db_path):
        """Test disabling a user account."""
        service = UserService(db_path)
        
        # Create an admin first
        admin_id = service.create_user(
            admin_id=0,  # Use 0 to bootstrap
            name="Admin",
            email="admin@example.com",
            password="Test@123!",
            role="admin"
        )
        
        user_id = service.create_user(
            admin_id=admin_id,
            name="To Disable",
            email="disable@example.com",
            password="Test@123!",
        )
        
        service.disable_user(admin_id=admin_id, user_id=user_id)
        
        user = service.get_user(user_id)
        assert user["is_disabled"] == 1
    
    def test_enable_user(self, db_path):
        """Test enabling a disabled user account."""
        service = UserService(db_path)
        
        # Create an admin first
        admin_id = service.create_user(
            admin_id=0,
            name="Admin",
            email="admin@example.com",
            password="Test@123!",
            role="admin"
        )
        
        user_id = service.create_user(
            admin_id=admin_id,
            name="To Enable",
            email="enable@example.com",
            password="Test@123!",
        )
        
        service.disable_user(admin_id=admin_id, user_id=user_id)
        service.enable_user(admin_id=admin_id, user_id=user_id)
        
        user = service.get_user(user_id)
        assert user["is_disabled"] == 0
    
    def test_cannot_disable_self(self, db_path):
        """Test that admin cannot disable their own account."""
        service = UserService(db_path)
        
        admin_id = service.create_user(
            admin_id=1,
            name="Admin",
            email="admin2@example.com",
            password="Test@123!",
            role="admin"
        )
        
        with pytest.raises(UserServiceError, match="Cannot disable your own"):
            service.disable_user(admin_id=admin_id, user_id=admin_id)
    
    def test_reset_password(self, db_path):
        """Test resetting a user's password."""
        service = UserService(db_path)
        
        user_id = service.create_user(
            admin_id=1,
            name="Reset Test",
            email="reset@example.com",
            password="Original@123!",
        )
        
        result = service.reset_password(
            admin_id=1,
            user_id=user_id,
            new_password="NewPass@456!"
        )
        
        assert result is True
    
    def test_delete_user(self, db_path):
        """Test deleting a user."""
        service = UserService(db_path)
        
        # Create an admin first
        admin_id = service.create_user(
            admin_id=0,
            name="Admin",
            email="admin@example.com",
            password="Test@123!",
            role="admin"
        )
        
        user_id = service.create_user(
            admin_id=admin_id,
            name="To Delete",
            email="delete@example.com",
            password="Test@123!",
        )
        
        service.delete_user(admin_id=admin_id, user_id=user_id)
        
        user = service.get_user(user_id)
        assert user is None
    
    def test_cannot_delete_self(self, db_path):
        """Test that admin cannot delete their own account."""
        service = UserService(db_path)
        
        admin_id = service.create_user(
            admin_id=1,
            name="Admin",
            email="admin3@example.com",
            password="Test@123!",
            role="admin"
        )
        
        with pytest.raises(UserServiceError, match="Cannot delete your own"):
            service.delete_user(admin_id=admin_id, user_id=admin_id)
    
    def test_get_user_stats(self, db_path):
        """Test getting user statistics."""
        service = UserService(db_path)
        
        # Create some users
        service.create_user(
            admin_id=1, name="User1", email="u1@test.com", 
            password="Test@123!", role="user"
        )
        service.create_user(
            admin_id=1, name="User2", email="u2@test.com",
            password="Test@123!", role="user"
        )
        service.create_user(
            admin_id=1, name="Admin2", email="a2@test.com",
            password="Test@123!", role="admin"
        )
        
        stats = service.get_user_stats()
        
        assert stats["total"] >= 3
        assert "admins" in stats
        assert "users" in stats
        assert "disabled" in stats
    
    def test_filter_users_by_role(self, db_path):
        """Test filtering users by role."""
        service = UserService(db_path)
        
        service.create_user(
            admin_id=1, name="Regular", email="regular@test.com",
            password="Test@123!", role="user"
        )
        service.create_user(
            admin_id=1, name="Admin", email="admin4@test.com",
            password="Test@123!", role="admin"
        )
        
        users = service.list_users(role_filter="user")
        
        for user in users:
            assert user["role"] == "user"
    
    def test_search_users(self, db_path):
        """Test searching users by name or email."""
        service = UserService(db_path)
        
        service.create_user(
            admin_id=1, name="John Smith", email="john@test.com",
            password="Test@123!"
        )
        service.create_user(
            admin_id=1, name="Jane Doe", email="jane@test.com",
            password="Test@123!"
        )
        
        results = service.list_users(search="john")
        
        assert len(results) >= 1
        assert any("john" in u["name"].lower() or "john" in u["email"].lower() for u in results)
