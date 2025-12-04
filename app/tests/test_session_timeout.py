"""Tests for session timeout functionality."""
from __future__ import annotations

import os
import sys
import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock

# Ensure app imports work
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from routes.middleware import AuthorizationMiddleware
from state.auth_state import AuthState, UserSession
import app_config


class TestSessionTimeout:
    """Test cases for session timeout functionality."""
    
    def test_active_session_not_expired(self):
        """Test that recently active sessions are not expired."""
        middleware = AuthorizationMiddleware()
        auth_state = AuthState()
        
        # Login with recent activity
        auth_state.login({
            "id": 1, "email": "test@test.com", "role": "user", "name": "Test"
        })
        auth_state.update_last_activity()
        
        # Check if session is expired by checking the state
        last_activity = auth_state.state.get("last_activity")
        assert last_activity is not None
        
        # Recent activity should not be expired
        if isinstance(last_activity, str):
            last_activity = datetime.fromisoformat(last_activity)
        timeout = timedelta(minutes=app_config.SESSION_TIMEOUT_MINUTES)
        is_expired = datetime.utcnow() - last_activity > timeout
        
        assert is_expired is False
    
    def test_session_activity_updates_on_navigation(self):
        """Test that session activity is updated when user navigates."""
        auth_state = AuthState()
        
        # Login
        auth_state.login({
            "id": 1, "email": "test@test.com", "role": "user", "name": "Test"
        })
        
        initial_activity = auth_state.state.get("last_activity")
        
        # Simulate some time passing
        import time
        time.sleep(0.1)
        
        # Update activity
        auth_state.update_last_activity()
        
        new_activity = auth_state.state.get("last_activity")
        
        assert new_activity >= initial_activity
    
    def test_no_session_not_authenticated(self):
        """Test that no session means not authenticated."""
        auth_state = AuthState()
        
        # Don't login - no session
        assert auth_state.is_authenticated is False
    
    def test_login_creates_session_with_activity(self):
        """Test that login creates a session with initial activity timestamp."""
        auth_state = AuthState()
        
        auth_state.login({
            "id": 1, "email": "test@test.com", "role": "user", "name": "Test"
        })
        
        assert auth_state.is_authenticated is True
        assert auth_state.state.get("last_activity") is not None
        
        # Activity should be recent
        last_activity = auth_state.state.get("last_activity")
        if isinstance(last_activity, str):
            last_activity = datetime.fromisoformat(last_activity)
        
        age = datetime.utcnow() - last_activity
        assert age.total_seconds() < 5
    
    def test_logout_clears_session(self):
        """Test that logout clears the session."""
        auth_state = AuthState()
        
        auth_state.login({
            "id": 1, "email": "test@test.com", "role": "user", "name": "Test"
        })
        auth_state.logout()
        
        assert auth_state.is_authenticated is False
    
    def test_multiple_activity_updates(self):
        """Test that activity can be updated multiple times."""
        auth_state = AuthState()
        
        auth_state.login({
            "id": 1, "email": "test@test.com", "role": "user", "name": "Test"
        })
        
        timestamps = []
        for _ in range(3):
            auth_state.update_last_activity()
            timestamps.append(auth_state.state.get("last_activity"))
            import time
            time.sleep(0.05)
        
        # Each update should be equal or later than previous
        for i in range(1, len(timestamps)):
            assert timestamps[i] >= timestamps[i-1]


class TestMiddlewareSessionCheck:
    """Test the middleware session checking logic."""
    
    def test_middleware_allows_public_routes(self):
        """Test that middleware allows public routes."""
        middleware = AuthorizationMiddleware()
        
        # Route config for public route
        route_config = {
            "requires_auth": False,
            "allowed_roles": None
        }
        
        # Create mock page
        mock_page = MagicMock()
        
        # Should allow access
        result = middleware.check_access(mock_page, route_config, "/login")
        assert result is True
    
    def test_user_session_properties(self):
        """Test UserSession dataclass properties."""
        session = UserSession(
            user_id=1,
            email="test@test.com",
            name="Test User",
            role="admin",
            is_authenticated=True,
            last_activity=datetime.utcnow().isoformat()
        )
        
        data = session.to_dict()
        assert data["user_id"] == 1
        assert data["email"] == "test@test.com"
        assert data["role"] == "admin"
        assert data["is_authenticated"] is True
        
        # Test from_dict
        restored = UserSession.from_dict(data)
        assert restored.user_id == session.user_id
        assert restored.email == session.email
