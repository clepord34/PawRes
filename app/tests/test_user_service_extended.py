"""Extended tests for UserService - comprehensive coverage of all methods."""
import pytest

from services.user_service import UserService, UserServiceError


class TestCreateUser:
    """Test user creation by admin."""
    
    def test_create_user_success(self, user_service, sample_admin):
        """Test creating a new user."""
        user_id = user_service.create_user(
            admin_id=sample_admin["id"],
            name="New User",
            email="newuser@example.com",
            password="NewPass@123",
            role="user"
        )
        
        assert user_id > 0
        
        # Verify user was created
        user = user_service.get_user(user_id)
        assert user is not None
        assert user["name"] == "New User"
        assert user["email"] == "newuser@example.com"
        assert user["role"] == "user"
    
    def test_create_user_with_phone(self, user_service, sample_admin):
        """Test creating user with phone number."""
        user_id = user_service.create_user(
            admin_id=sample_admin["id"],
            name="User With Phone",
            email="withphone@example.com",
            password="Pass@123",
            phone="09123456789"
        )
        
        assert user_id > 0
        user = user_service.get_user(user_id)
        assert user["phone"] == "09123456789"
    
    def test_create_user_duplicate_email_fails(self, user_service, sample_admin, sample_user):
        """Test creating user with existing email fails."""
        with pytest.raises(UserServiceError, match="already exists"):
            user_service.create_user(
                admin_id=sample_admin["id"],
                name="Duplicate",
                email=sample_user["email"],
                password="Pass@123"
            )
    
    def test_create_user_invalid_name_fails(self, user_service, sample_admin):
        """Test creating user with empty name fails."""
        with pytest.raises(UserServiceError, match="Name must be"):
            user_service.create_user(
                admin_id=sample_admin["id"],
                name="",
                email="test@example.com",
                password="Pass@123"
            )
    
    def test_create_user_invalid_role_fails(self, user_service, sample_admin):
        """Test creating user with invalid role fails."""
        with pytest.raises(UserServiceError, match="Role must be"):
            user_service.create_user(
                admin_id=sample_admin["id"],
                name="Test",
                email="test@example.com",
                password="Pass@123",
                role="superadmin"
            )
    
    def test_create_user_weak_password_fails(self, user_service, sample_admin):
        """Test creating user with weak password fails."""
        with pytest.raises(UserServiceError):
            user_service.create_user(
                admin_id=sample_admin["id"],
                name="Test",
                email="test@example.com",
                password="weak",
                validate_password=True
            )
    
    def test_create_user_admin_role(self, user_service, sample_admin):
        """Test creating admin user."""
        user_id = user_service.create_user(
            admin_id=sample_admin["id"],
            name="New Admin",
            email="newadmin@example.com",
            password="Admin@123",
            role="admin"
        )
        
        user = user_service.get_user(user_id)
        assert user["role"] == "admin"


class TestUpdateUser:
    """Test user update operations."""
    
    def test_update_user_name(self, user_service, sample_admin, sample_user):
        """Test updating user name."""
        success = user_service.update_user(
            admin_id=sample_admin["id"],
            user_id=sample_user["id"],
            name="Updated Name"
        )
        
        assert success is True
        user = user_service.get_user(sample_user["id"])
        assert user["name"] == "Updated Name"
    
    def test_update_user_email(self, user_service, sample_admin, sample_user):
        """Test updating user email."""
        success = user_service.update_user(
            admin_id=sample_admin["id"],
            user_id=sample_user["id"],
            email="newemail@example.com"
        )
        
        assert success is True
        user = user_service.get_user(sample_user["id"])
        assert user["email"] == "newemail@example.com"
    
    def test_update_user_phone(self, user_service, sample_admin, sample_user):
        """Test updating user phone."""
        success = user_service.update_user(
            admin_id=sample_admin["id"],
            user_id=sample_user["id"],
            phone="09987654321"
        )
        
        assert success is True
        user = user_service.get_user(sample_user["id"])
        assert user["phone"] == "09987654321"
    
    def test_update_user_role(self, user_service, sample_admin, sample_user):
        """Test updating user role."""
        success = user_service.update_user(
            admin_id=sample_admin["id"],
            user_id=sample_user["id"],
            role="admin"
        )
        
        assert success is True
        user = user_service.get_user(sample_user["id"])
        assert user["role"] == "admin"
    
    def test_update_user_multiple_fields(self, user_service, sample_admin, sample_user):
        """Test updating multiple fields at once."""
        success = user_service.update_user(
            admin_id=sample_admin["id"],
            user_id=sample_user["id"],
            name="Multi Update",
            email="multi@example.com",
            phone="09111111111",
            role="admin"
        )
        
        assert success is True
        user = user_service.get_user(sample_user["id"])
        assert user["name"] == "Multi Update"
        assert user["email"] == "multi@example.com"
        assert user["phone"] == "09111111111"
        assert user["role"] == "admin"


class TestSearchUsers:
    """Test user search functionality."""
    
    def test_search_users_by_name(self, user_service, sample_user):
        """Test searching users by name."""
        results = user_service.list_users(search=sample_user["name"][:5])
        
        assert len(results) > 0
        user_ids = [u["id"] for u in results]
        assert sample_user["id"] in user_ids
    
    def test_search_users_by_email(self, user_service, sample_user):
        """Test searching users by email."""
        results = user_service.list_users(search=sample_user["email"][:5])
        
        assert len(results) > 0
        user_ids = [u["id"] for u in results]
        assert sample_user["id"] in user_ids
    
    def test_search_users_partial_match(self, user_service, sample_user):
        """Test partial search matches."""
        # Search for part of the name
        results = user_service.list_users(search="User")
        
        # Should find at least the sample_user
        assert len(results) > 0
    
    def test_search_users_no_results(self, user_service):
        """Test search with no matches."""
        results = user_service.list_users(search="ZZZZNONEXISTENT")
        
        assert len(results) == 0


class TestGetUserByEmail:
    """Test getting user by email."""
    
    def test_get_user_by_email_exists(self, user_service, sample_user):
        """Test getting existing user by email."""
        user = user_service.get_user_by_email(sample_user["email"])
        
        assert user is not None
        assert user["id"] == sample_user["id"]
    
    def test_get_user_by_email_not_exists(self, user_service):
        """Test getting non-existent user by email."""
        user = user_service.get_user_by_email("nonexistent@example.com")
        
        assert user is None


class TestDeleteUserWithPassword:
    """Test deleting user with password verification."""
    
    def test_delete_user_nonexistent(self, user_service, sample_admin):
        """Test deleting non-existent user raises error."""
        with pytest.raises(UserServiceError, match="not found"):
            user_service.delete_user(sample_admin["id"], 99999)


class TestAdminActions:
    """Test admin-specific actions."""
    
    def test_disable_nonexistent_user(self, user_service, sample_admin):
        """Test disabling non-existent user raises error."""
        with pytest.raises(UserServiceError, match="not found"):
            user_service.disable_user(sample_admin["id"], 99999)
    
    def test_enable_nonexistent_user(self, user_service, sample_admin):
        """Test enabling non-existent user raises error."""
        with pytest.raises(UserServiceError, match="not found"):
            user_service.enable_user(sample_admin["id"], 99999)


class TestPasswordReset:
    """Test password reset functionality."""
    
    def test_reset_password_clears_lockout(self, user_service, sample_admin, sample_user):
        """Test resetting password clears lockout status."""
        from storage.database import Database
        
        # Lock the user
        db = Database(user_service.db.db_path)
        db.execute(
            "UPDATE users SET failed_login_attempts = 5, locked_until = datetime('now', '+15 minutes') WHERE id = ?",
            (sample_user["id"],)
        )
        
        # Reset password
        success = user_service.reset_password(
            admin_id=sample_admin["id"],
            user_id=sample_user["id"],
            new_password="NewPass@123",
            validate_password=False
        )
        
        assert success is True
        
        # Verify lockout was cleared
        user = user_service.get_user(sample_user["id"])
        assert user["failed_login_attempts"] == 0
        assert user["locked_until"] is None
    
    def test_reset_password_invalid_user(self, user_service, sample_admin):
        """Test resetting password for non-existent user raises error."""
        with pytest.raises(UserServiceError):
            user_service.reset_password(
                admin_id=sample_admin["id"],
                user_id=99999,
                new_password="NewPass@123"
            )


class TestUpdateUserInvalidCases:
    """Test update_user error cases."""
    
    def test_update_user_nonexistent(self, user_service, sample_admin):
        """Test updating non-existent user raises error."""
        with pytest.raises(UserServiceError):
            user_service.update_user(
                admin_id=sample_admin["id"],
                user_id=99999,
                name="Test"
            )
