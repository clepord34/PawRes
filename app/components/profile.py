"""Profile section component for sidebars."""
from __future__ import annotations
from typing import Optional, Callable

try:
    import flet as ft
except ImportError:
    ft = None


def create_profile_section(
    user_name: str, 
    is_admin: bool = False,
    profile_photo: Optional[str] = None,
    on_click: Optional[Callable] = None
) -> object:
    """Create a profile section showing user info and online status.
    
    Args:
        user_name: Display name for the user
        is_admin: Whether the user is an admin
        profile_photo: Base64 encoded photo or None for default icon
        on_click: Optional callback when profile is clicked
    """
    if ft is None:
        raise RuntimeError("Flet must be installed to create profile sections")
    
    # Truncate long names with ellipsis for display
    display_name = user_name if len(user_name) <= 18 else user_name[:16] + "..."
    
    # Create profile avatar - either photo or default icon
    if profile_photo:
        avatar_content = ft.Image(
            src_base64=profile_photo,
            width=38,
            height=38,
            fit=ft.ImageFit.COVER,
            border_radius=19,
        )
    else:
        avatar_content = ft.Icon(ft.Icons.PERSON, size=24, color=ft.Colors.GREY_500)
    
    avatar_container = ft.Container(
        avatar_content,
        width=42,
        height=42,
        bgcolor=ft.Colors.GREY_100,
        border_radius=21,
        alignment=ft.alignment.center,
        border=ft.border.all(2, ft.Colors.TEAL_200),
        clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
    )
    
    return ft.Container(
        ft.Row([
            avatar_container,
            ft.Column([
                ft.Text(
                    display_name, 
                    size=13, 
                    weight="w600", 
                    color=ft.Colors.BLACK87,
                    max_lines=1,
                    overflow=ft.TextOverflow.ELLIPSIS,
                    tooltip=user_name,  # Show full name on hover
                ),
                ft.Row([
                    ft.Container(
                        width=7,
                        height=7,
                        bgcolor=ft.Colors.GREEN_500,
                        border_radius=4,
                    ),
                    ft.Text("Online", size=10, color=ft.Colors.GREEN_600, weight="w500"),
                ], spacing=4),
            ], spacing=3, expand=True),
            # Add a subtle arrow indicator to show it's clickable
            ft.Icon(ft.Icons.CHEVRON_RIGHT, size=16, color=ft.Colors.GREY_400) if on_click else ft.Container(),
        ], spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        padding=ft.padding.symmetric(horizontal=12, vertical=10),
        bgcolor=ft.Colors.WHITE,
        border_radius=10,
        border=ft.border.all(1, ft.Colors.GREY_200),
        shadow=ft.BoxShadow(blur_radius=4, spread_radius=0, color=ft.Colors.BLACK12, offset=(0, 1)),
        on_click=on_click,
        on_hover=lambda e: _handle_hover(e) if on_click else None,
        ink=True if on_click else False,
        tooltip="View Profile" if on_click else None,
    )


def _handle_hover(e):
    """Handle hover effect on profile container."""
    if e.data == "true":
        e.control.border = ft.border.all(1, ft.Colors.TEAL_300)
    else:
        e.control.border = ft.border.all(1, ft.Colors.GREY_200)
    e.control.update()
