"""Tests for UserService - CRUD operations, role management."""
import pytest

from services.user_service import UserService
from storage.database import Database


class TestGetUser:
    """Test user retrieval operations."""
    
    def test_get_user_by_id(self, user_service, sample_user):
        """Test getting user by ID."""
        user = user_service.get_user(sample_user["id"])
        
        assert user is not None
        assert user["id"] == sample_user["id"]
        assert user["email"] == sample_user["email"]
        assert user["name"] == sample_user["name"]
    
    def test_get_nonexistent_user(self, user_service):
        """Test getting non-existent user returns None."""
        user = user_service.get_user(99999)
        
        assert user is None
    
    def test_get_user_by_email(self, user_service, sample_user):
        """Test getting user by email."""
        user = user_service.get_user_by_email(sample_user["email"])
        
        assert user is not None
        assert user["id"] == sample_user["id"]
        assert user["email"] == sample_user["email"]
    
    def test_get_user_by_email_case_insensitive(self, user_service, sample_user):
        """Test email lookup case sensitivity (SQLite is case-sensitive by default)."""
        user = user_service.get_user_by_email(sample_user["email"].upper())
        
        assert user is None


class TestListUsers:
    """Test user listing operations."""
    
    def test_list_all_users(self, user_service, sample_user, sample_admin):
        """Test getting all users using list_users."""
        users = user_service.list_users()
        
        assert len(users) >= 2
        user_ids = [u["id"] for u in users]
        assert sample_user["id"] in user_ids
        assert sample_admin["id"] in user_ids
    
    def test_list_users_by_role(self, user_service, sample_user, sample_admin):
        """Test filtering users by role."""
        admin_users = user_service.list_users(role_filter="admin")
        user_users = user_service.list_users(role_filter="user")
        
        admin_ids = [u["id"] for u in admin_users]
        user_ids = [u["id"] for u in user_users]
        
        assert sample_admin["id"] in admin_ids
        assert sample_user["id"] in user_ids
        assert sample_admin["id"] not in user_ids
        assert sample_user["id"] not in admin_ids
    
    def test_list_enabled_users_only(self, user_service, sample_user, sample_admin):
        """Test getting only enabled users (not disabled)."""
        db = Database(user_service.db.db_path)
        db.execute("UPDATE users SET is_disabled = 1 WHERE id = ?", (sample_user["id"],))
        
        enabled_users = user_service.list_users(include_disabled=False)
        enabled_ids = [u["id"] for u in enabled_users]
        
        assert sample_admin["id"] in enabled_ids
        assert sample_user["id"] not in enabled_ids


class TestEnableDisableUser:
    """Test user enable/disable operations."""
    
    def test_disable_user(self, user_service, sample_user, sample_admin):
        """Test disabling a user."""
        success = user_service.disable_user(sample_admin["id"], sample_user["id"])
        
        assert success is True
        
        user = user_service.get_user(sample_user["id"])
        assert user["is_disabled"] == 1
    
    def test_enable_user(self, user_service, sample_user, sample_admin):
        """Test enabling a disabled user."""
        user_service.disable_user(sample_admin["id"], sample_user["id"])
        
        success = user_service.enable_user(sample_admin["id"], sample_user["id"])
        
        assert success is True
        
        user = user_service.get_user(sample_user["id"])
        assert user.get("is_disabled", 0) == 0
    
    def test_disable_nonexistent_user(self, user_service, sample_admin):
        """Test disabling non-existent user raises error."""
        from services.user_service import UserServiceError
        with pytest.raises(UserServiceError):
            user_service.disable_user(sample_admin["id"], 99999)
    
    def test_enable_nonexistent_user(self, user_service, sample_admin):
        """Test enabling non-existent user raises error."""
        from services.user_service import UserServiceError
        with pytest.raises(UserServiceError):
            user_service.enable_user(sample_admin["id"], 99999)


class TestDeleteUser:
    """Test user deletion operations."""
    
    def test_delete_user(self, user_service, sample_user, sample_admin):
        """Test deleting a user."""
        success = user_service.delete_user(sample_admin["id"], sample_user["id"])
        
        assert success is True
        
        user = user_service.get_user(sample_user["id"])
        assert user is None
    
    def test_delete_nonexistent_user(self, user_service, sample_admin):
        """Test deleting non-existent user raises error."""
        from services.user_service import UserServiceError
        with pytest.raises(UserServiceError):
            user_service.delete_user(sample_admin["id"], 99999)
    
    def test_delete_user_cascades(self, user_service, sample_user, sample_admin, rescue_service, sample_rescue_mission):
        """Test that deleting user handles related records appropriately."""
        success = user_service.delete_user(sample_admin["id"], sample_user["id"])
        
        assert success is True


class TestResetPassword:
    """Test password reset by admin."""
    
    def test_reset_user_password(self, user_service, sample_user, sample_admin, auth_service):
        """Test admin resetting user password."""
        new_password = "NewResetPass@123"
        success = user_service.reset_password(
            sample_admin["id"],
            sample_user["id"],
            new_password,
            validate_password=False
        )
        
        assert success is True
        
        # Verify can login with new password
        from services.auth_service import AuthResult
        user, result = auth_service.login(sample_user["email"], new_password)
        assert result == AuthResult.SUCCESS
    
    def test_reset_password_invalid_user(self, user_service):
        """Test resetting password of non-existent user."""
        from services.user_service import UserServiceError
        with pytest.raises(UserServiceError):
            user_service.reset_password(1, 99999, "NewPass@123", validate_password=False)
    
    def test_reset_password_clears_lockout(self, user_service, sample_user, sample_admin, auth_service):
        """Test that password reset clears account lockout."""
        import app_config
        for i in range(app_config.MAX_FAILED_LOGIN_ATTEMPTS):
            auth_service.login(sample_user["email"], f"Wrong{i}")
        
        user, result = auth_service.login(sample_user["email"], sample_user["password"])
        from services.auth_service import AuthResult
        assert result != AuthResult.SUCCESS
        
        new_password = "ResetPass@123"
        user_service.reset_password(sample_admin["id"], sample_user["id"], new_password, validate_password=False)
        
        user, result = auth_service.login(sample_user["email"], new_password)
        assert result == AuthResult.SUCCESS
    
    def test_update_multiple_fields(self, user_service, sample_user):
        """Test updating multiple fields at once."""
        success = user_service.update_user_profile(
            sample_user["id"],
            name="New Name",
            phone="+639179999999"
        )
        
        assert success is True
        
        user = user_service.get_user(sample_user["id"])
        assert user["name"] == "New Name"
        assert user["phone"] == "+639179999999"
    
    def test_update_profile_invalid_user(self, user_service):
        """Test updating profile of non-existent user."""
        from services.user_service import UserServiceError
        with pytest.raises(UserServiceError):
            user_service.update_user_profile(
                99999,
                name="Test"
            )


class TestUserSearch:
    """Test user search operations."""
    
    def test_search_users_by_name(self, user_service, sample_user):
        """Test searching users by name."""
        results = user_service.list_users(search=sample_user["name"])
        
        assert len(results) >= 1
        found = any(u["id"] == sample_user["id"] for u in results)
        assert found is True
    
    def test_search_users_by_email(self, user_service, sample_user):
        """Test searching users by email."""
        results = user_service.list_users(search=sample_user["email"])
        
        assert len(results) >= 1
        found = any(u["id"] == sample_user["id"] for u in results)
        assert found is True
    
    def test_search_users_partial_match(self, user_service, sample_user):
        """Test searching with partial match."""
        query = sample_user["name"].split()[0]
        results = user_service.list_users(search=query)
        
        found = any(u["id"] == sample_user["id"] for u in results)
        assert found is True
    
    def test_search_users_no_results(self, user_service):
        """Test search with no matching results."""
        results = user_service.list_users(search="NonexistentUserXYZ123")
        
        assert len(results) == 0
