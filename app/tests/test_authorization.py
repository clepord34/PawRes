"""Tests for authorization middleware and route protection."""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta

from routes.middleware import AuthorizationMiddleware, check_route_access


class TestAuthorizationMiddleware:
    """Test cases for authorization middleware."""
    
    def test_allows_public_routes(self):
        """Test that public routes (requires_auth=False) are allowed without auth."""
        middleware = AuthorizationMiddleware()
        
        page = MagicMock()
        route_config = {
            "requires_auth": False,
            "handler": lambda p, params: None,
        }
        
        result = middleware.check_access(page, route_config, "/public")
        
        assert result is True
    
    def test_blocks_unauthenticated_access(self):
        """Test that protected routes block unauthenticated users."""
        middleware = AuthorizationMiddleware()
        
        page = MagicMock()
        route_config = {
            "requires_auth": True,
            "allowed_roles": ["user", "admin"],
        }
        
        with patch("state.get_app_state") as mock_state:
            mock_auth = MagicMock()
            mock_auth.is_authenticated = False
            mock_state.return_value.auth = mock_auth
            
            result = middleware.check_access(page, route_config, "/protected")
        
        assert result is False
        page.go.assert_called_once_with("/")
    
    def test_allows_authenticated_user_with_correct_role(self):
        """Test that authenticated users with correct role can access routes."""
        middleware = AuthorizationMiddleware()
        
        page = MagicMock()
        route_config = {
            "requires_auth": True,
            "allowed_roles": ["user", "admin"],
        }
        
        with patch("state.get_app_state") as mock_state:
            mock_auth = MagicMock()
            mock_auth.is_authenticated = True
            mock_auth.user_role = "user"
            mock_auth.user_id = 1
            mock_auth.state = {"last_activity": None}
            mock_state.return_value.auth = mock_auth
            
            result = middleware.check_access(page, route_config, "/protected")
        
        assert result is True
    
    def test_blocks_user_with_wrong_role(self):
        """Test that users without the required role are blocked."""
        middleware = AuthorizationMiddleware()
        
        page = MagicMock()
        route_config = {
            "requires_auth": True,
            "allowed_roles": ["admin"],  # Admin only
        }
        
        with patch("state.get_app_state") as mock_state:
            mock_auth = MagicMock()
            mock_auth.is_authenticated = True
            mock_auth.user_role = "user"  # User trying to access admin route
            mock_auth.user_id = 1
            mock_auth.state = {"last_activity": None}
            mock_auth.get_redirect_route.return_value = "/user"
            mock_state.return_value.auth = mock_auth
            
            result = middleware.check_access(page, route_config, "/admin")
        
        assert result is False
        page.go.assert_called_once_with("/user")
    
    def test_blocks_expired_session(self):
        """Test that expired sessions are blocked."""
        middleware = AuthorizationMiddleware()
        
        page = MagicMock()
        route_config = {
            "requires_auth": True,
            "allowed_roles": ["user"],
        }
        
        # Set last activity to 60 minutes ago (default timeout is 30 min)
        old_time = (datetime.utcnow() - timedelta(minutes=60)).isoformat()
        
        with patch("state.get_app_state") as mock_state:
            mock_auth = MagicMock()
            mock_auth.is_authenticated = True
            mock_auth.user_role = "user"
            mock_auth.user_id = 1
            mock_auth.state = {"last_activity": old_time}
            mock_state.return_value.auth = mock_auth
            mock_state.return_value.reset = MagicMock()
            
            result = middleware.check_access(page, route_config, "/protected")
        
        assert result is False
        mock_state.return_value.reset.assert_called_once()
        page.go.assert_called_once_with("/")
    
    def test_allows_fresh_session(self):
        """Test that recently active sessions are allowed."""
        middleware = AuthorizationMiddleware()
        
        page = MagicMock()
        route_config = {
            "requires_auth": True,
            "allowed_roles": ["user"],
        }
        
        # Set last activity to 5 minutes ago (well within 30 min timeout)
        recent_time = (datetime.utcnow() - timedelta(minutes=5)).isoformat()
        
        with patch("state.get_app_state") as mock_state:
            mock_auth = MagicMock()
            mock_auth.is_authenticated = True
            mock_auth.user_role = "user"
            mock_auth.user_id = 1
            mock_auth.state = {"last_activity": recent_time}
            mock_state.return_value.auth = mock_auth
            
            result = middleware.check_access(page, route_config, "/protected")
        
        assert result is True


class TestCheckRouteAccess:
    """Test cases for the check_route_access function."""
    
    def test_function_delegates_to_middleware(self):
        """Test that check_route_access uses the middleware singleton."""
        page = MagicMock()
        route_config = {"requires_auth": False}
        
        result = check_route_access(page, route_config, "/public")
        
        assert result is True
