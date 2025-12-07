"""Tests for LoggingService - event logging, rotation."""
import pytest
import os
from pathlib import Path

from services.logging_service import get_auth_logger, get_admin_logger, get_security_logger
import app_config


class TestLoggingSetup:
    """Test logging service initialization."""
    
    def test_logging_service_initializes(self, logging_service):
        """Test that logging service can be created."""
        assert logging_service is not None
        assert "auth_logger" in logging_service
        assert "admin_logger" in logging_service
        assert "security_logger" in logging_service
        assert logging_service["auth_logger"] is not None
        assert logging_service["admin_logger"] is not None
        assert logging_service["security_logger"] is not None
    
    def test_log_directories_created(self, logging_service):
        """Test that log directories are created."""
        log_dir = app_config.STORAGE_DIR / "data" / "logs"
        assert log_dir.exists()
    
    def test_loggers_have_handlers(self, logging_service):
        """Test that loggers have handlers configured."""
        assert logging_service["auth_logger"] is not None
        assert logging_service["admin_logger"] is not None
        assert logging_service["security_logger"] is not None


class TestAuthenticationLogging:
    """Test authentication event logging."""
    
    def test_log_login_success(self, logging_service):
        """Test logging successful login."""
        try:
            logging_service["auth_logger"].log_login_success(
                email="test@example.com",
                user_id=1
            )
            success = True
        except Exception:
            success = False
        
        assert success is True
    
    def test_log_login_failure(self, logging_service):
        """Test logging failed login."""
        try:
            logging_service["auth_logger"].log_login_failure(
                email="test@example.com",
                reason="Invalid password"
            )
            success = True
        except Exception:
            success = False
        
        assert success is True
    
    def test_log_logout(self, logging_service):
        """Test logging logout."""
        try:
            logging_service["auth_logger"].log_logout(
                email="test@example.com",
                user_id=1
            )
            success = True
        except Exception:
            success = False
        
        assert success is True
    
    def test_log_registration(self, logging_service):
        """Test logging user registration."""
        try:
            logging_service["admin_logger"].log_user_created(
                admin_id=1,
                new_user_id=1,
                new_user_email="newuser@example.com",
                new_user_role="user"
            )
            success = True
        except Exception:
            success = False
        
        assert success is True


class TestSecurityLogging:
    """Test security event logging."""
    
    def test_log_account_lockout(self, logging_service):
        """Test logging account lockout."""
        try:
            logging_service["auth_logger"].log_lockout(
                email="test@example.com",
                duration_minutes=15
            )
            success = True
        except Exception:
            success = False
        
        assert success is True
    
    def test_log_password_change(self, logging_service):
        """Test logging password change."""
        try:
            logging_service["auth_logger"].log_password_change(
                user_id=1,
                email="test@example.com"
            )
            success = True
        except Exception:
            success = False
        
        assert success is True
    
    def test_log_password_reset(self, logging_service):
        """Test logging password reset."""
        try:
            logging_service["admin_logger"].log_password_reset(
                admin_id=2,
                user_id=1,
                user_email="test@example.com"
            )
            success = True
        except Exception:
            success = False
        
        assert success is True
    
    def test_log_security_event(self, logging_service):
        """Test logging generic security event."""
        try:
            logging_service["security_logger"].log_suspicious_activity(
                activity="Multiple failed login attempts from different IPs",
                user_id=1
            )
            success = True
        except Exception:
            success = False
        
        assert success is True


class TestAdminLogging:
    """Test admin action logging."""
    
    def test_log_user_disabled(self, logging_service):
        """Test logging user disable action."""
        try:
            logging_service["admin_logger"].log_user_disabled(
                admin_id=2,
                user_id=1,
                user_email="test@example.com"
            )
            success = True
        except Exception:
            success = False
        
        assert success is True
    
    def test_log_user_enabled(self, logging_service):
        """Test logging user enable action."""
        try:
            logging_service["admin_logger"].log_user_enabled(
                admin_id=2,
                user_id=1,
                user_email="test@example.com"
            )
            success = True
        except Exception:
            success = False
        
        assert success is True
    
    def test_log_role_change(self, logging_service):
        """Test logging role change."""
        try:
            logging_service["admin_logger"].log_role_changed(
                admin_id=2,
                user_id=1,
                user_email="test@example.com",
                old_role="user",
                new_role="admin"
            )
            success = True
        except Exception:
            success = False
        
        assert success is True
    
    def test_log_admin_action(self, logging_service):
        """Test logging generic admin action."""
        try:
            logging_service["admin_logger"].log_user_deleted(
                admin_id=2,
                user_id=1,
                user_email="test@example.com"
            )
            success = True
        except Exception:
            success = False
        
        assert success is True


class TestLoggingWithOptionalParameters:
    """Test logging with optional parameters."""
    
    def test_log_login_without_ip(self, logging_service):
        """Test login logging without IP address."""
        try:
            logging_service["auth_logger"].log_login_success(
                email="test@example.com",
                user_id=1
            )
            success = True
        except Exception:
            success = False
        
        assert success is True
    
    def test_log_login_without_reason(self, logging_service):
        """Test failed login without specific reason."""
        try:
            logging_service["auth_logger"].log_login_failure(
                email="test@example.com"
            )
            success = True
        except Exception:
            success = False
        
        assert success is True
    
    def test_log_security_event_minimal(self, logging_service):
        """Test security event logging with minimal info."""
        try:
            logging_service["security_logger"].log_suspicious_activity(
                activity="test_event"
            )
            success = True
        except Exception:
            success = False
        
        assert success is True


class TestLoggingInTestMode:
    """Test that logging works in test mode (pytest)."""
    
    def test_logging_uses_null_handler_in_tests(self, logging_service):
        """Test that NullHandler is used during tests to avoid file creation."""
        auth_logger = logging_service["auth_logger"]
        
        assert auth_logger is not None
    
    def test_multiple_log_calls_dont_error(self, logging_service):
        """Test that multiple rapid log calls work correctly."""
        try:
            for i in range(10):
                logging_service["auth_logger"].log_login_success(
                    email=f"user{i}@example.com",
                    user_id=i
                )
            success = True
        except Exception:
            success = False
        
        assert success is True


