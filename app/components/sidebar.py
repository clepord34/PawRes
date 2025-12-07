"""Sidebar components for the application."""
from __future__ import annotations
from typing import Optional

try:
    import flet as ft
except ImportError:
    ft = None

from .header import create_sidebar_header
from .buttons import create_nav_button, create_logout_button
from .profile import create_profile_section


def _get_user_profile_photo(user_id: Optional[int]) -> Optional[str]:
    """Fetch user's profile photo from database.
    
    Args:
        user_id: The user's ID
        
    Returns:
        Base64 encoded photo string or None
    """
    if not user_id:
        return None
    
    try:
        import app_config
        from storage.database import Database
        from services.photo_service import load_photo
        
        db = Database(app_config.DB_PATH)
        user = db.fetch_one(
            "SELECT profile_picture FROM users WHERE id = ?",
            (user_id,)
        )
        
        if user and user.get("profile_picture"):
            return load_photo(user["profile_picture"])
    except Exception as e:
        print(f"[WARN] Could not load profile photo: {e}")
    
    return None


def _handle_logout(page: object) -> None:
    """Handle logout by resetting app state and navigating to login.
    
    This ensures all cached data and subscriptions are properly cleared
    to prevent memory leaks.
    """
    try:
        from state import get_app_state
        app_state = get_app_state()
        app_state.reset()
    except Exception as e:
        print(f"[WARN] Logout: Could not reset AppState: {e}")
    
    page.go("/")


def create_admin_sidebar(page: object, current_route: str = "") -> object:
    """Create an admin sidebar with navigation and profile.
    
    Args:
        page: The Flet page object
        current_route: The current page route for highlighting the active nav button
    """
    if ft is None:
        raise RuntimeError("Flet must be installed to create sidebars")
    
    sidebar_header = create_sidebar_header()
    
    # Normalize current route (remove query params for comparison)
    route_path = current_route.split("?")[0] if current_route else ""
    
    try:
        from state import get_app_state
        app_state = get_app_state()
        user_name = app_state.auth.user_name or "Admin"
        user_id = app_state.auth.user_id
    except Exception:
        user_name = "Admin"
        user_id = None
    
    # Fetch profile photo
    profile_photo = _get_user_profile_photo(user_id)
    
    nav_items = [
        ("Admin Dashboard", "/admin", ["/admin"]),
        ("View Animal List", "/animals_list?admin=1", ["/animals_list", "/edit_animal", "/add_animal"]),
        ("Manage Records", "/manage_records", ["/manage_records", "/rescue_missions", "/adoption_requests", "/hidden_items"]),
        ("View Data Charts", "/charts", ["/charts"]),
        ("User Management", "/user_management", ["/user_management"]),
        ("Audit Logs", "/audit_logs", ["/audit_logs"]),
    ]
    
    nav_buttons = []
    for label, nav_route, match_routes in nav_items:
        is_active = route_path in match_routes
        nav_buttons.append(
            create_nav_button(label, lambda e, r=nav_route: page.go(r), is_active=is_active)
        )
    
    logout_btn = create_logout_button(lambda e: _handle_logout(page))
    
    profile = create_profile_section(
        user_name, 
        is_admin=True,
        profile_photo=profile_photo,
        on_click=lambda e: page.go("/profile")
    )
    
    return ft.Container(
        ft.Column(
            [sidebar_header] + nav_buttons + [
                ft.Container(expand=True),  # Spacer
                profile,
                logout_btn,
                ft.Container(height=20),
            ],
            horizontal_alignment="center",
            spacing=12
        ),
        width=220,
        bgcolor=ft.Colors.with_opacity(0.95, ft.Colors.WHITE),
        padding=15,
        border_radius=ft.border_radius.only(top_right=12, bottom_right=12),
        shadow=ft.BoxShadow(blur_radius=10, spread_radius=2, color=ft.Colors.BLACK12, offset=(2, 0)),
    )


def create_user_sidebar(page: object, user_name: str = "User", current_route: str = "") -> object:
    """Create a user sidebar with navigation and profile.
    
    Args:
        page: The Flet page object
        user_name: Display name for the user profile section
        current_route: The current page route for highlighting the active nav button
    """
    if ft is None:
        raise RuntimeError("Flet must be installed to create sidebars")
    
    sidebar_header = create_sidebar_header()
    
    # Normalize current route (remove query params for comparison)
    route_path = current_route.split("?")[0] if current_route else ""
    
    try:
        from state import get_app_state
        app_state = get_app_state()
        user_id = app_state.auth.user_id
        if user_name == "User":
            user_name = app_state.auth.user_name or "User"
    except Exception:
        user_id = None
    
    # Fetch profile photo
    profile_photo = _get_user_profile_photo(user_id)
    
    nav_items = [
        ("User Dashboard", "/user", ["/user"]),
        ("Apply for Adoption", "/available_adoption", ["/available_adoption", "/adoption_form"]),
        ("Report Rescue Mission", "/rescue_form", ["/rescue_form"]),
        ("Check Application Status", "/check_status", ["/check_status"]),
        ("View Animal List", "/animals_list", ["/animals_list"]),
        ("Your Analytics", "/user_analytics", ["/user_analytics"]),
    ]
    
    nav_buttons = []
    for label, nav_route, match_routes in nav_items:
        is_active = route_path in match_routes
        nav_buttons.append(
            create_nav_button(label, lambda e, r=nav_route: page.go(r), is_active=is_active)
        )
    
    logout_btn = create_logout_button(lambda e: _handle_logout(page))
    
    profile = create_profile_section(
        user_name, 
        is_admin=False,
        profile_photo=profile_photo,
        on_click=lambda e: page.go("/profile")
    )
    
    return ft.Container(
        ft.Column(
            [sidebar_header] + nav_buttons + [
                ft.Container(expand=True),  # Spacer
                profile,
                logout_btn,
                ft.Container(height=20),
            ],
            horizontal_alignment="center",
            spacing=12
        ),
        width=220,
        bgcolor=ft.Colors.with_opacity(0.95, ft.Colors.WHITE),
        padding=15,
        border_radius=ft.border_radius.only(top_right=12, bottom_right=12),
        shadow=ft.BoxShadow(blur_radius=10, spread_radius=2, color=ft.Colors.BLACK12, offset=(2, 0)),
    )
