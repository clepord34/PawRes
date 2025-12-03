"""Sidebar components for the application."""
from __future__ import annotations
from typing import Callable

try:
    import flet as ft
except ImportError:
    ft = None

from .header import create_sidebar_header
from .buttons import create_nav_button, create_logout_button
from .profile import create_profile_section


def _handle_logout(page: object) -> None:
    """Handle logout by resetting app state and navigating to login.
    
    This ensures all cached data and subscriptions are properly cleared
    to prevent memory leaks.
    """
    try:
        from state import get_app_state
        app_state = get_app_state()
        app_state.reset()
        print("[DEBUG] Logout: AppState reset completed")
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
    
    # Define nav items with their routes for matching
    nav_items = [
        ("Admin Dashboard", "/admin", ["/admin"]),
        ("Add Animal", "/add_animal", ["/add_animal"]),
        ("View Animal List", "/animals_list?admin=1", ["/animals_list", "/edit_animal"]),
        ("View Rescue Missions", "/rescue_missions?admin=1", ["/rescue_missions"]),
        ("Adoption Requests", "/adoption_requests", ["/adoption_requests"]),
        ("View Data Charts", "/charts", ["/charts"]),
        ("Hidden Items", "/hidden_items", ["/hidden_items"]),
    ]
    
    # Create navigation buttons with active state
    nav_buttons = []
    for label, nav_route, match_routes in nav_items:
        is_active = route_path in match_routes
        nav_buttons.append(
            create_nav_button(label, lambda e, r=nav_route: page.go(r), is_active=is_active)
        )
    
    logout_btn = create_logout_button(lambda e: _handle_logout(page))
    profile = create_profile_section("Admin", is_admin=True)
    
    return ft.Container(
        ft.Column(
            [sidebar_header] + nav_buttons + [
                ft.Container(expand=True),  # Spacer
                logout_btn,
                profile,
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
    
    # Define nav items with their routes for matching
    nav_items = [
        ("User Dashboard", "/user", ["/user"]),
        ("Apply for Adoption", "/available_adoption", ["/available_adoption", "/adoption_form"]),
        ("Report Rescue Mission", "/rescue_form", ["/rescue_form"]),
        ("Check Application Status", "/check_status", ["/check_status"]),
        ("View Animal List", "/animals_list", ["/animals_list"]),
        ("Your Analytics", "/user_analytics", ["/user_analytics"]),
    ]
    
    # Create navigation buttons with active state
    nav_buttons = []
    for label, nav_route, match_routes in nav_items:
        is_active = route_path in match_routes
        nav_buttons.append(
            create_nav_button(label, lambda e, r=nav_route: page.go(r), is_active=is_active)
        )
    
    logout_btn = create_logout_button(lambda e: _handle_logout(page))
    profile = create_profile_section(user_name, is_admin=False)
    
    return ft.Container(
        ft.Column(
            [sidebar_header] + nav_buttons + [
                ft.Container(expand=True),  # Spacer
                logout_btn,
                profile,
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
