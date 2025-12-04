"""Authorization middleware for route protection.

Provides:
- Authentication checking for protected routes
- Role-based access control (RBAC) enforcement
- Session timeout detection
- Logging of unauthorized access attempts
"""
from __future__ import annotations

from typing import Any, Callable, Dict, Optional, TYPE_CHECKING
from datetime import datetime, timedelta

import app_config

if TYPE_CHECKING:
    import flet as ft


class AuthorizationMiddleware:
    """Middleware that enforces authentication and authorization rules.
    
    This middleware checks:
    1. If the user is authenticated for protected routes
    2. If the user's role is allowed for the requested route
    3. If the session has timed out
    
    Example usage in route handler:
        def my_route_handler(page, params):
            middleware = AuthorizationMiddleware()
            if not middleware.check_access(page, route_config):
                return  # Middleware handles redirect
            # ... proceed with route handling
    """
    
    def __init__(self):
        """Initialize the authorization middleware."""
        self._logging_service = None
    
    @property
    def logging_service(self):
        """Lazy load the logging service to avoid circular imports."""
        if self._logging_service is None:
            try:
                from services.logging_service import get_security_logger
                self._logging_service = get_security_logger()
            except ImportError:
                self._logging_service = None
        return self._logging_service
    
    def check_access(
        self,
        page,
        route_config: Dict[str, Any],
        route_path: str
    ) -> bool:
        """Check if the current user can access a route.
        
        Args:
            page: Flet page object with session
            route_config: Route configuration dict with requires_auth and allowed_roles
            route_path: The route path being accessed
            
        Returns:
            True if access is allowed, False otherwise.
            When False, the middleware handles the redirect.
        """
        from state import get_app_state
        
        app_state = get_app_state()
        
        # Check if route requires authentication
        requires_auth = route_config.get("requires_auth", False)
        
        if not requires_auth:
            return True
        
        # Check if user is authenticated
        if not app_state.auth.is_authenticated:
            self._log_unauthorized_access(
                route_path, 
                reason="not_authenticated",
                user_id=None
            )
            self._redirect_to_login(page, "Please log in to access this page")
            return False
        
        # Check session timeout
        if self._is_session_expired(app_state):
            user_id = app_state.auth.user_id
            self._log_unauthorized_access(
                route_path,
                reason="session_expired",
                user_id=user_id
            )
            app_state.reset()
            self._redirect_to_login(page, "Session expired. Please log in again.")
            return False
        
        # Update last activity timestamp
        self._update_last_activity(app_state)
        
        # Check role-based access
        allowed_roles = route_config.get("allowed_roles")
        if allowed_roles is not None:
            user_role = app_state.auth.user_role
            if user_role not in allowed_roles:
                user_id = app_state.auth.user_id
                self._log_unauthorized_access(
                    route_path,
                    reason="insufficient_role",
                    user_id=user_id,
                    user_role=user_role,
                    required_roles=allowed_roles
                )
                self._redirect_to_dashboard(page, app_state, "You don't have permission to access this page")
                return False
        
        return True
    
    def _is_session_expired(self, app_state) -> bool:
        """Check if the current session has expired.
        
        Args:
            app_state: The application state
            
        Returns:
            True if session has expired, False otherwise
        """
        last_activity = app_state.auth.state.get("last_activity")
        
        if last_activity is None:
            return False
        
        try:
            if isinstance(last_activity, str):
                last_activity = datetime.fromisoformat(last_activity)
            
            timeout_minutes = getattr(app_config, 'SESSION_TIMEOUT_MINUTES', 30)
            timeout_delta = timedelta(minutes=timeout_minutes)
            
            return datetime.utcnow() - last_activity > timeout_delta
        except (ValueError, TypeError) as e:
            print(f"[WARN] Could not check session expiry: {e}")
            return False
    
    def _update_last_activity(self, app_state) -> None:
        """Update the last activity timestamp in the auth state.
        
        Args:
            app_state: The application state
        """
        app_state.auth.update_last_activity()
    
    def _log_unauthorized_access(
        self,
        route_path: str,
        reason: str,
        user_id: Optional[int] = None,
        user_role: Optional[str] = None,
        required_roles: Optional[list] = None
    ) -> None:
        """Log an unauthorized access attempt.
        
        Args:
            route_path: The route that was accessed
            reason: Why access was denied
            user_id: User ID if authenticated
            user_role: User's role if authenticated
            required_roles: Roles that were required for access
        """
        if self.logging_service:
            self.logging_service.log_unauthorized_access(
                route=route_path,
                reason=reason,
                user_id=user_id,
                user_role=user_role,
                required_roles=required_roles
            )
        else:
            # Fallback to print logging
            print(f"[SECURITY] Unauthorized access to {route_path}: {reason} "
                  f"(user_id={user_id}, role={user_role})")
    
    def _redirect_to_login(self, page, message: str) -> None:
        """Redirect user to login page with a message.
        
        Args:
            page: Flet page object
            message: Message to show on login page
        """
        try:
            from components import show_snackbar
            show_snackbar(page, message, color="error")
        except Exception:
            pass
        
        page.go("/")
    
    def _redirect_to_dashboard(self, page, app_state, message: str) -> None:
        """Redirect user to their appropriate dashboard with a message.
        
        Args:
            page: Flet page object
            app_state: Application state
            message: Message to show
        """
        try:
            from components import show_snackbar
            show_snackbar(page, message, color="warning")
        except Exception:
            pass
        
        redirect_route = app_state.auth.get_redirect_route()
        page.go(redirect_route)


# Singleton instance
_middleware_instance: Optional[AuthorizationMiddleware] = None


def get_middleware() -> AuthorizationMiddleware:
    """Get the singleton middleware instance.
    
    Returns:
        The AuthorizationMiddleware singleton
    """
    global _middleware_instance
    if _middleware_instance is None:
        _middleware_instance = AuthorizationMiddleware()
    return _middleware_instance


def check_route_access(page, route_config: Dict[str, Any], route_path: str) -> bool:
    """Convenience function to check route access.
    
    Args:
        page: Flet page object
        route_config: Route configuration dict
        route_path: The route being accessed
        
    Returns:
        True if access is allowed
    """
    return get_middleware().check_access(page, route_config, route_path)


__all__ = [
    "AuthorizationMiddleware",
    "get_middleware",
    "check_route_access",
]
