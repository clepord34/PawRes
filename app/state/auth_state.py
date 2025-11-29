"""Authentication state manager."""
from __future__ import annotations

from typing import Any, Dict, Optional
from dataclasses import dataclass, asdict

from .base import StateManager


@dataclass
class UserSession:
    """User session data structure."""
    user_id: Optional[int] = None
    email: str = ""
    name: str = ""
    role: str = "user"
    is_authenticated: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UserSession":
        """Create from dictionary."""
        return cls(
            user_id=data.get("user_id"),
            email=data.get("email", ""),
            name=data.get("name", ""),
            role=data.get("role", "user"),
            is_authenticated=data.get("is_authenticated", False)
        )


class AuthState(StateManager[Dict[str, Any]]):
    """Authentication state manager."""
    
    def __init__(self):
        """Initialize auth state with empty session."""
        initial_state = UserSession().to_dict()
        super().__init__(initial_state)
        self._page = None  # Flet page reference for session sync
    
    def set_page(self, page: object) -> None:
        """Set the Flet page reference for session synchronization.
        
        Args:
            page: Flet page object with session support
        """
        self._page = page
        # Load existing session if available
        self._load_from_page_session()
    
    def _load_from_page_session(self) -> None:
        """Load auth state from Flet's page.session."""
        if self._page is None:
            return
        
        try:
            user_id = self._page.session.get("user_id")
            if user_id is not None:
                session = UserSession(
                    user_id=user_id,
                    email=self._page.session.get("user_email", ""),
                    name=self._page.session.get("user_name", ""),
                    role=self._page.session.get("user_role", "user"),
                    is_authenticated=True
                )
                self.update_state(session.to_dict(), notify=True)
        except Exception as e:
            print(f"[ERROR] Failed to load session: {e}")
    
    def _sync_to_page_session(self) -> None:
        """Sync auth state to Flet's page.session."""
        if self._page is None:
            return
        
        try:
            state = self.state
            if state.get("is_authenticated"):
                self._page.session.set("user_id", state.get("user_id"))
                self._page.session.set("user_email", state.get("email"))
                self._page.session.set("user_name", state.get("name"))
                self._page.session.set("user_role", state.get("role"))
            else:
                # Clear session on logout
                self._page.session.clear()
        except Exception as e:
            print(f"[ERROR] Failed to sync session: {e}")
    
    @property
    def current_user(self) -> Optional[UserSession]:
        """Get current user session or None if not authenticated."""
        state = self.state
        if state.get("is_authenticated"):
            return UserSession.from_dict(state)
        return None
    
    @property
    def is_authenticated(self) -> bool:
        """Check if user is currently authenticated."""
        return self.state.get("is_authenticated", False)
    
    @property
    def user_id(self) -> Optional[int]:
        """Get current user ID or None."""
        return self.state.get("user_id")
    
    @property
    def user_name(self) -> str:
        """Get current user name."""
        return self.state.get("name", "")
    
    @property
    def user_email(self) -> str:
        """Get current user email."""
        return self.state.get("email", "")
    
    @property
    def user_role(self) -> str:
        """Get current user role."""
        return self.state.get("role", "user")
    
    @property
    def is_admin(self) -> bool:
        """Check if current user is an admin."""
        return self.user_role == "admin"
    
    def login(self, user_data: Dict[str, Any]) -> None:
        """Process successful login.
        
        Args:
            user_data: User data from AuthService.login()
                       Expected keys: id, email, name, role
        """
        session = UserSession(
            user_id=user_data.get("id"),
            email=user_data.get("email", ""),
            name=user_data.get("name", ""),
            role=user_data.get("role", "user"),
            is_authenticated=True
        )
        
        self.update_state(session.to_dict())
        self._sync_to_page_session()
    
    def logout(self) -> None:
        """Process logout, clearing all session data.
        
        This clears the auth state and syncs to page session.
        Note: Call AppState.reset() for full logout including all domain states.
        """
        self.clear_observers()  # Clear any lingering subscriptions
        self.reset(UserSession().to_dict())
        self._sync_to_page_session()
    
    def update_user_info(self, **kwargs) -> None:
        """Update specific user info fields.
        
        Args:
            **kwargs: Fields to update (name, email, etc.)
        """
        allowed_fields = {"name", "email", "role"}
        updates = {k: v for k, v in kwargs.items() if k in allowed_fields}
        
        if updates:
            self.patch_state(updates)
            self._sync_to_page_session()
    
    def get_redirect_route(self) -> str:
        """Get the appropriate redirect route based on user role.
        
        Returns:
            Route path string ("/admin" for admin, "/user" for others)
        """
        if not self.is_authenticated:
            return "/"
        
        if self.user_role == "admin":
            return "/admin"
        else:
            return "/user"
