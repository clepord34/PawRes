"""Central application state controller (singleton)."""
from __future__ import annotations

from typing import Any, Dict, Optional
import threading

from .base import Observable
from .auth_state import AuthState
from .animal_state import AnimalState
from .rescue_state import RescueState
from .adoption_state import AdoptionState
from .ui_state import UIState
import app_config


class AppState(Observable):
    """Singleton that coordinates all state managers."""
    
    _instance: Optional["AppState"] = None
    _lock = threading.Lock()
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, db_path: Optional[str] = None):
        if hasattr(self, "_initialized") and self._initialized:
            return
        
        super().__init__()
        
        self._db_path = db_path or app_config.DB_PATH
        self._page = None
        self._initialized = False
        
        self._auth = AuthState()
        self._animals = AnimalState(self._db_path)
        self._rescues = RescueState(self._db_path)
        self._adoptions = AdoptionState(self._db_path)
        self._ui = UIState()
        
        self._setup_state_subscriptions()
        self._initialized = True
    
    @classmethod
    def get_instance(cls, db_path: Optional[str] = None) -> "AppState":
        """Get the singleton AppState instance."""
        if cls._instance is None:
            cls._instance = cls(db_path)
        return cls._instance
    
    @classmethod
    def reset_instance(cls) -> None:
        """Reset the singleton instance (for testing)."""
        with cls._lock:
            if cls._instance is not None:
                cls._instance._initialized = False
            cls._instance = None
    
    def _setup_state_subscriptions(self) -> None:
        self._auth.subscribe(self._on_auth_changed)
        self._animals.subscribe(lambda d: self._propagate_change("animals", d))
        self._rescues.subscribe(lambda d: self._propagate_change("rescues", d))
        self._adoptions.subscribe(lambda d: self._propagate_change("adoptions", d))
        self._ui.subscribe(lambda d: self._propagate_change("ui", d))
    
    def _on_auth_changed(self, data: Dict[str, Any]) -> None:
        self._propagate_change("auth", data)
        if not self._auth.is_authenticated:
            self._animals.reset()
            self._rescues.reset()
            self._adoptions.reset()
    
    def _propagate_change(self, domain: str, data: Dict[str, Any]) -> None:
        """Propagate state changes to observers."""
        self.notify_observers({
            "domain": domain,
            "data": data,
        })
    
    # ===== State Manager Properties =====
    
    @property
    def auth(self) -> AuthState:
        """Get the authentication state manager."""
        return self._auth
    
    @property
    def animals(self) -> AnimalState:
        """Get the animal state manager."""
        return self._animals
    
    @property
    def rescues(self) -> RescueState:
        """Get the rescue mission state manager."""
        return self._rescues
    
    @property
    def adoptions(self) -> AdoptionState:
        """Get the adoption request state manager."""
        return self._adoptions
    
    @property
    def ui(self) -> UIState:
        """Get the UI state manager."""
        return self._ui
    
    @property
    def page(self) -> Optional[object]:
        """Get the Flet page reference."""
        return self._page
    
    # ===== Initialization =====
    
    def initialize(self, page: object) -> None:
        """Initialize state with Flet page reference.
        
        Call this from main.py after creating the Flet page.
        Sets up page references for session sync and UI updates.
        
        Args:
            page: Flet Page object
        """
        self._page = page
        
        # Set page reference on state managers that need it
        self._auth.set_page(page)
        self._ui.set_page(page)
    
    # ===== Convenience Methods =====
    
    def load_initial_data(self) -> None:
        """Load initial data after authentication.
        
        Call after successful login to preload commonly needed data.
        """
        if not self._auth.is_authenticated:
            print("[WARNING] AppState: Cannot load data - not authenticated")
            return
        
        self._ui.start_loading("Loading data...")
        
        try:
            # Load data based on user role
            self._animals.load_animals()
            
            if self._auth.is_admin:
                self._rescues.load_missions()
                self._adoptions.load_requests()
            else:
                # For regular users, load only their data
                user_id = self._auth.user_id
                if user_id:
                    self._rescues.load_user_missions(user_id)
                    self._adoptions.load_user_requests(user_id)
            
        except Exception as e:
            print(f"[ERROR] AppState: Failed to load initial data: {e}")
            self._ui.show_error(f"Failed to load data: {e}")
        finally:
            self._ui.stop_loading()
    
    def refresh_all(self) -> None:
        """Refresh all data from database."""
        self._ui.start_loading("Refreshing...")
        
        try:
            self._animals.load_animals()
            self._rescues.load_missions()
            self._adoptions.load_requests()
            
            self._ui.show_success("Data refreshed")
            
        except Exception as e:
            print(f"[ERROR] AppState: Failed to refresh data: {e}")
            self._ui.show_error(f"Failed to refresh: {e}")
        finally:
            self._ui.stop_loading()
    
    def reset(self) -> None:
        """Reset all state to initial values.
        
        Call this on logout to clear all cached data and prevent memory leaks.
        This method:
        - Clears all observer subscriptions
        - Resets all domain states to initial values
        - Clears UI notifications
        """
        # Clear observers from all state managers to prevent memory leaks
        self._auth.clear_observers()
        self._animals.clear_observers()
        self._rescues.clear_observers()
        self._adoptions.clear_observers()
        self._ui.clear_observers()
        
        # Reset individual states
        self._auth.reset()
        self._animals.reset()
        self._rescues.reset()
        self._adoptions.reset()
        self._ui.clear_notifications()
        
        # Re-setup subscriptions for future use
        self._setup_state_subscriptions()
        
    
    def get_dashboard_stats(self) -> Dict[str, Any]:
        """Get aggregated statistics for dashboard display.
        
        Returns:
            Dict with stats from all domains
        """
        return {
            "animals": {
                "total": len(self._animals.animals),
                "adoptable": len([
                    a for a in self._animals.animals 
                    if a.get("status", "").lower() in ("healthy", "available", "adoptable")
                ]),
            },
            "rescues": self._rescues.get_stats(),
            "adoptions": self._adoptions.get_stats(),
            "user": {
                "is_authenticated": self._auth.is_authenticated,
                "is_admin": self._auth.is_admin,
                "name": self._auth.user_name,
            },
        }
    
    # ===== Utility Methods =====
    
    def is_ready(self) -> bool:
        """Check if state is fully initialized.
        
        Returns:
            True if initialized and page is set
        """
        return self._initialized and self._page is not None
    
    def get_state_snapshot(self) -> Dict[str, Any]:
        """Get a snapshot of all state (for debugging/logging).
        
        Returns:
            Dict with all state data
        """
        return {
            "auth": self._auth.state,
            "animals": {
                "count": len(self._animals.animals),
                "is_loading": self._animals.is_loading,
            },
            "rescues": {
                "count": len(self._rescues.missions),
                "is_loading": self._rescues.is_loading,
            },
            "adoptions": {
                "count": len(self._adoptions.requests),
                "is_loading": self._adoptions.is_loading,
            },
            "ui": {
                "is_loading": self._ui.is_loading,
                "current_route": self._ui.current_route,
                "theme": self._ui.theme,
            },
        }


# Convenience function to get the app state
def get_app_state(db_path: Optional[str] = None) -> AppState:
    """Get the global AppState instance.
    
    Args:
        db_path: Optional database path (only used on first call)
    
    Returns:
        The AppState singleton
    """
    return AppState.get_instance(db_path)
