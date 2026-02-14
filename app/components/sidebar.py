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
from .responsive_layout import is_mobile


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


def create_admin_drawer(page: object, current_route: str = "") -> object:
    """Create a NavigationDrawer for admin on mobile screens.

    Args:
        page: The Flet page object
        current_route: The current page route for highlighting
    """
    return _build_drawer(page, current_route, is_admin=True)


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


def create_user_drawer(page: object, current_route: str = "") -> object:
    """Create a NavigationDrawer for regular users on mobile screens.

    Args:
        page: The Flet page object
        current_route: The current page route for highlighting
    """
    return _build_drawer(page, current_route, is_admin=False)


# ---------------------------------------------------------------------------
# Shared drawer builder
# ---------------------------------------------------------------------------

_ADMIN_NAV_ITEMS = [
    ("Admin Dashboard", ft.Icons.DASHBOARD if ft else None, "/admin", ["/admin"]),
    ("View Animal List", ft.Icons.PETS if ft else None, "/animals_list?admin=1", ["/animals_list", "/edit_animal", "/add_animal"]),
    ("Manage Records", ft.Icons.FOLDER_OPEN if ft else None, "/manage_records", ["/manage_records", "/rescue_missions", "/adoption_requests", "/hidden_items"]),
    ("View Data Charts", ft.Icons.BAR_CHART if ft else None, "/charts", ["/charts"]),
    ("User Management", ft.Icons.PEOPLE if ft else None, "/user_management", ["/user_management"]),
    ("Audit Logs", ft.Icons.HISTORY if ft else None, "/audit_logs", ["/audit_logs"]),
]

_USER_NAV_ITEMS = [
    ("User Dashboard", ft.Icons.DASHBOARD if ft else None, "/user", ["/user"]),
    ("Apply for Adoption", ft.Icons.FAVORITE if ft else None, "/available_adoption", ["/available_adoption", "/adoption_form"]),
    ("Report Rescue", ft.Icons.REPORT if ft else None, "/rescue_form", ["/rescue_form"]),
    ("Check Status", ft.Icons.CHECKLIST if ft else None, "/check_status", ["/check_status"]),
    ("View Animals", ft.Icons.PETS if ft else None, "/animals_list", ["/animals_list"]),
    ("Your Analytics", ft.Icons.ANALYTICS if ft else None, "/user_analytics", ["/user_analytics"]),
]


def _build_drawer(page, current_route: str, is_admin: bool) -> object:
    """Internal helper to build a NavigationDrawer for mobile."""
    if ft is None:
        raise RuntimeError("Flet must be installed")

    route_path = current_route.split("?")[0] if current_route else ""
    items = _ADMIN_NAV_ITEMS if is_admin else _USER_NAV_ITEMS

    destinations = []
    selected_idx = 0
    for idx, (label, icon, nav_route, match_routes) in enumerate(items):
        if route_path in match_routes:
            selected_idx = idx
        destinations.append(
            ft.NavigationDrawerDestination(
                label=label,
                icon=icon,
                selected_icon=icon,
            )
        )

    # Build route list for on_change mapping
    route_list = [item[2] for item in items]

    def _on_drawer_change(e):
        idx = e.control.selected_index
        if idx is not None and 0 <= idx < len(route_list):
            page.close(drawer)
            page.go(route_list[idx])

    # Header inside drawer
    drawer_header = ft.Container(
        ft.Column([
            create_sidebar_header(),
        ], horizontal_alignment="center"),
        padding=ft.padding.only(top=20, bottom=10),
    )

    # Logout button at bottom
    logout_tile = ft.ListTile(
        leading=ft.Icon(ft.Icons.LOGOUT, color=ft.Colors.RED_400),
        title=ft.Text("Logout", color=ft.Colors.RED_400, weight="w500"),
        on_click=lambda e: _handle_logout(page),
    )

    drawer = ft.NavigationDrawer(
        controls=[
            drawer_header,
            ft.Divider(thickness=1),
        ] + destinations + [
            ft.Divider(thickness=1),
            logout_tile,
        ],
        selected_index=selected_idx,
        on_change=_on_drawer_change,
    )
    return drawer
