"""UI state manager."""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

from .base import StateManager


class NotificationType(Enum):
    """Types of UI notifications."""
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"


@dataclass
class Notification:
    """A UI notification/snackbar message."""
    message: str
    type: NotificationType = NotificationType.INFO
    duration: int = 3000
    timestamp: datetime = field(default_factory=datetime.utcnow)
    id: str = field(default_factory=lambda: str(datetime.utcnow().timestamp()))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "message": self.message,
            "type": self.type.value,
            "duration": self.duration,
            "timestamp": self.timestamp.isoformat(),
            "id": self.id,
        }


@dataclass
class NavigationState:
    """Current navigation state.
    
    Attributes:
        current_route: Current page route
        previous_route: Previous page route (for back navigation)
        route_params: Parameters from URL query string
        history: Navigation history stack
    """
    current_route: str = "/"
    previous_route: Optional[str] = None
    route_params: Dict[str, Any] = field(default_factory=dict)
    history: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "current_route": self.current_route,
            "previous_route": self.previous_route,
            "route_params": self.route_params,
            "history": self.history,
        }


class UIState(StateManager[Dict[str, Any]]):
    """UI state manager.
    
    Provides centralized management of UI-related state with:
    - Global loading indicators
    - Notification queue
    - Navigation tracking
    - Modal/dialog state
    
    Usage:
        ui_state = UIState()
        
        # Subscribe to UI state changes
        ui_state.subscribe(lambda data: update_ui(data))
        
        # Show loading
        ui_state.set_loading(True, "Loading animals...")
        
        # Show notification
        ui_state.show_success("Animal added successfully!")
        
        # Track navigation
        ui_state.navigate("/animals_list")
    """
    
    def __init__(self):
        """Initialize UI state."""
        initial_state = {
            "is_loading": False,
            "loading_message": "",
            "notifications": [],
            "navigation": NavigationState().to_dict(),
            "active_modal": None,
            "sidebar_collapsed": False,
            "theme": "light",
        }
        super().__init__(initial_state)
        
        self._page = None
        self._max_notifications = 5
    
    def set_page(self, page: object) -> None:
        """Set the Flet page reference.
        
        Args:
            page: Flet page object
        """
        self._page = page
    
    # ===== Loading State =====
    
    @property
    def is_loading(self) -> bool:
        """Check if app is in loading state."""
        return self.state.get("is_loading", False)
    
    @property
    def loading_message(self) -> str:
        """Get current loading message."""
        return self.state.get("loading_message", "")
    
    def set_loading(self, loading: bool, message: str = "") -> None:
        """Set loading state.
        
        Args:
            loading: Whether to show loading indicator
            message: Optional loading message
        """
        self.patch_state({
            "is_loading": loading,
            "loading_message": message if loading else "",
        })
    
    def start_loading(self, message: str = "Loading...") -> None:
        """Start loading with a message."""
        self.set_loading(True, message)
    
    def stop_loading(self) -> None:
        """Stop loading."""
        self.set_loading(False)
    
    # ===== Notifications =====
    
    @property
    def notifications(self) -> List[Dict[str, Any]]:
        """Get current notification queue."""
        return self.state.get("notifications", [])
    
    def show_notification(
        self,
        message: str,
        notification_type: NotificationType = NotificationType.INFO,
        duration: int = 3000
    ) -> str:
        """Show a notification.
        
        Args:
            message: Notification text
            notification_type: Type of notification
            duration: Display duration in ms
        
        Returns:
            Notification ID
        """
        notification = Notification(
            message=message,
            type=notification_type,
            duration=duration
        )
        
        # Add to queue
        current = list(self.notifications)
        current.append(notification.to_dict())
        
        # Trim to max
        if len(current) > self._max_notifications:
            current = current[-self._max_notifications:]
        
        self.patch_state({"notifications": current})
        
        # Also show via Flet's snackbar if page is available
        self._show_flet_snackbar(message, notification_type)
        
        return notification.id
    
    def show_info(self, message: str, duration: int = 3000) -> str:
        """Show an info notification."""
        return self.show_notification(message, NotificationType.INFO, duration)
    
    def show_success(self, message: str, duration: int = 3000) -> str:
        """Show a success notification."""
        return self.show_notification(message, NotificationType.SUCCESS, duration)
    
    def show_warning(self, message: str, duration: int = 4000) -> str:
        """Show a warning notification."""
        return self.show_notification(message, NotificationType.WARNING, duration)
    
    def show_error(self, message: str, duration: int = 5000) -> str:
        """Show an error notification."""
        return self.show_notification(message, NotificationType.ERROR, duration)
    
    def dismiss_notification(self, notification_id: str) -> None:
        """Dismiss a notification by ID.
        
        Args:
            notification_id: ID of notification to dismiss
        """
        current = [
            n for n in self.notifications 
            if n.get("id") != notification_id
        ]
        self.patch_state({"notifications": current})
    
    def clear_notifications(self) -> None:
        """Clear all notifications."""
        self.patch_state({"notifications": []})
    
    def _show_flet_snackbar(self, message: str, notification_type: NotificationType) -> None:
        """Show notification using Flet's snackbar.
        
        Args:
            message: Message text
            notification_type: Type for color selection
        """
        if self._page is None:
            return
        
        try:
            import flet as ft
            
            # Color based on type
            colors = {
                NotificationType.INFO: ft.Colors.BLUE_700,
                NotificationType.SUCCESS: ft.Colors.GREEN_700,
                NotificationType.WARNING: ft.Colors.ORANGE_700,
                NotificationType.ERROR: ft.Colors.RED_700,
            }
            bgcolor = colors.get(notification_type, ft.Colors.GREY_700)
            
            self._page.open(ft.SnackBar(
                ft.Text(message, color=ft.Colors.WHITE),
                bgcolor=bgcolor
            ))
            
        except Exception as e:
            print(f"[ERROR] UIState: Failed to show snackbar: {e}")
    
    # ===== Navigation State =====
    
    @property
    def current_route(self) -> str:
        """Get current route."""
        nav = self.state.get("navigation", {})
        return nav.get("current_route", "/")
    
    @property
    def previous_route(self) -> Optional[str]:
        """Get previous route."""
        nav = self.state.get("navigation", {})
        return nav.get("previous_route")
    
    @property
    def route_params(self) -> Dict[str, Any]:
        """Get current route parameters."""
        nav = self.state.get("navigation", {})
        return nav.get("route_params", {})
    
    @property
    def navigation_history(self) -> List[str]:
        """Get navigation history."""
        nav = self.state.get("navigation", {})
        return nav.get("history", [])
    
    def navigate(self, route: str, params: Optional[Dict[str, Any]] = None) -> None:
        """Navigate to a route.
        
        Args:
            route: Target route path
            params: Optional route parameters
        """
        current_nav = self.state.get("navigation", {})
        current_route = current_nav.get("current_route", "/")
        history = list(current_nav.get("history", []))
        
        # Add current to history (max 20 entries)
        if current_route and current_route != route:
            history.append(current_route)
            if len(history) > 20:
                history = history[-20:]
        
        new_nav = {
            "current_route": route,
            "previous_route": current_route,
            "route_params": params or {},
            "history": history,
        }
        
        self.patch_state({"navigation": new_nav})
        
        # Navigate via Flet page
        if self._page:
            try:
                self._page.go(route)
            except Exception as e:
                print(f"[ERROR] UIState: Navigation failed: {e}")
    
    def go_back(self) -> bool:
        """Go back to previous route.
        
        Returns:
            True if navigation occurred
        """
        history = self.navigation_history
        if not history:
            return False
        
        prev = history[-1]
        self.navigate(prev)
        
        # Remove the entry we just navigated to
        current_nav = dict(self.state.get("navigation", {}))
        current_nav["history"] = history[:-1]
        self.patch_state({"navigation": current_nav})
        
        return True
    
    # ===== Modal State =====
    
    @property
    def active_modal(self) -> Optional[str]:
        """Get currently active modal ID."""
        return self.state.get("active_modal")
    
    def open_modal(self, modal_id: str) -> None:
        """Open a modal by ID.
        
        Args:
            modal_id: Identifier for the modal
        """
        self.patch_state({"active_modal": modal_id})
    
    def close_modal(self) -> None:
        """Close the current modal."""
        self.patch_state({"active_modal": None})
    
    def is_modal_open(self, modal_id: str) -> bool:
        """Check if a specific modal is open.
        
        Args:
            modal_id: Modal identifier
        
        Returns:
            True if the specified modal is open
        """
        return self.active_modal == modal_id
    
    # ===== Theme State =====
    
    @property
    def theme(self) -> str:
        """Get current theme (light/dark)."""
        return self.state.get("theme", "light")
    
    @property
    def is_dark_theme(self) -> bool:
        """Check if dark theme is active."""
        return self.theme == "dark"
    
    def set_theme(self, theme: str) -> None:
        """Set the UI theme.
        
        Args:
            theme: Theme name (light/dark)
        """
        self.patch_state({"theme": theme})
    
    def toggle_theme(self) -> None:
        """Toggle between light and dark theme."""
        new_theme = "dark" if self.theme == "light" else "light"
        self.set_theme(new_theme)
    
    # ===== Sidebar State =====
    
    @property
    def is_sidebar_collapsed(self) -> bool:
        """Check if sidebar is collapsed."""
        return self.state.get("sidebar_collapsed", False)
    
    def toggle_sidebar(self) -> None:
        """Toggle sidebar collapsed state."""
        self.patch_state({"sidebar_collapsed": not self.is_sidebar_collapsed})
    
    def collapse_sidebar(self) -> None:
        """Collapse the sidebar."""
        self.patch_state({"sidebar_collapsed": True})
    
    def expand_sidebar(self) -> None:
        """Expand the sidebar."""
        self.patch_state({"sidebar_collapsed": False})
