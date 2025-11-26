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
    
    return ft.Container(
        ft.Row([
            ft.Container(
                ft.Icon(ft.Icons.PERSON, size=30, color=ft.Colors.GREY_400),
                width=50,
                height=50,
                bgcolor=ft.Colors.GREY_200,
                border_radius=25,
                alignment=ft.alignment.center,
            ),
            ft.Column([
                ft.Text(user_name, size=14, weight="bold", color=ft.Colors.BLACK87),
                ft.Row([
                    ft.Container(
                        width=8,
                        height=8,
                        bgcolor=ft.Colors.GREEN_400,
                        border_radius=4,
                    ),
                    ft.Text("Online", size=11, color=ft.Colors.GREEN_600),
                ], spacing=5),
            ], spacing=2),
        ], spacing=10),
        padding=15,
        bgcolor=ft.Colors.WHITE,
        border_radius=10,
        border=ft.border.all(1, ft.Colors.GREY_300),
    )
