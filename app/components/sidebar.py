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


def create_admin_sidebar(page: object) -> object:
    """Create an admin sidebar with navigation and profile."""
    if ft is None:
        raise RuntimeError("Flet must be installed to create sidebars")
    
    sidebar_header = create_sidebar_header()
    
    # Create navigation buttons
    nav_buttons = [
        create_nav_button("Admin Dashboard", lambda e: page.go("/admin")),
        create_nav_button("Add Animal", lambda e: page.go("/add_animal")),
        create_nav_button("View Animal List", lambda e: page.go("/animals_list?admin=1")),
        create_nav_button("View Rescue Missions", lambda e: page.go("/rescue_missions?admin=1")),
        create_nav_button("Adoption Requests", lambda e: page.go("/adoption_requests")),
        create_nav_button("View Data Charts", lambda e: page.go("/charts")),
    ]
    
    logout_btn = create_logout_button(lambda e: page.go("/"))
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


def create_user_sidebar(page: object, user_name: str = "User") -> object:
    """Create a user sidebar with navigation and profile."""
    if ft is None:
        raise RuntimeError("Flet must be installed to create sidebars")
    
    sidebar_header = create_sidebar_header()
    
    # Create navigation buttons
    nav_buttons = [
        create_nav_button("User Dashboard", lambda e: page.go("/user")),
        create_nav_button("Apply for Adoption", lambda e: page.go("/available_adoption")),
        create_nav_button("Report Rescue Mission", lambda e: page.go("/rescue_form")),
        create_nav_button("Check Application Status", lambda e: page.go("/check_status")),
        create_nav_button("View Animal List", lambda e: page.go("/animals_list")),
    ]
    
    logout_btn = create_logout_button(lambda e: page.go("/"))
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
