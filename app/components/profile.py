"""Profile section component for sidebars."""
from __future__ import annotations

try:
    import flet as ft
except ImportError:
    ft = None


def create_profile_section(user_name: str, is_admin: bool = False) -> object:
    """Create a profile section showing user info and online status."""
    if ft is None:
        raise RuntimeError("Flet must be installed to create profile sections")
    
    # Truncate long names with ellipsis for display
    display_name = user_name if len(user_name) <= 18 else user_name[:16] + "..."
    
    return ft.Container(
        ft.Row([
            ft.Container(
                ft.Icon(ft.Icons.PERSON, size=24, color=ft.Colors.GREY_500),
                width=42,
                height=42,
                bgcolor=ft.Colors.GREY_100,
                border_radius=21,
                alignment=ft.alignment.center,
                border=ft.border.all(2, ft.Colors.TEAL_200),
            ),
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
        ], spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        padding=ft.padding.symmetric(horizontal=12, vertical=10),
        bgcolor=ft.Colors.WHITE,
        border_radius=10,
        border=ft.border.all(1, ft.Colors.GREY_200),
        shadow=ft.BoxShadow(blur_radius=4, spread_radius=0, color=ft.Colors.BLACK12, offset=(0, 1)),
    )
