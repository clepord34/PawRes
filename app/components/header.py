"""Header components for the application."""
from __future__ import annotations
from typing import Optional

try:
    import flet as ft
except ImportError:
    ft = None


def create_header(
    title: str = "Paw Rescue",
    subtitle: str = "Management System",
    icon_size: int = 60,
    title_size: int = 32,
    subtitle_size: int = 14,
    padding: Optional[object] = None
) -> object:
    """Create a standard header with logo, title, and subtitle."""
    if ft is None:
        raise RuntimeError("Flet must be installed to create headers")
    
    if padding is None:
        padding = ft.padding.only(bottom=30)
    
    return ft.Container(
        ft.Column([
            ft.Icon(ft.Icons.PETS, size=icon_size, color=ft.Colors.TEAL_700),
            ft.Text(title, size=title_size, weight="bold", color=ft.Colors.with_opacity(0.6, ft.Colors.BLACK)),
            ft.Text(subtitle, size=subtitle_size, color=ft.Colors.with_opacity(0.5, ft.Colors.BLACK)),
        ], horizontal_alignment="center", spacing=8),
        padding=padding,
    )


def create_page_header(
    title: str,
    icon_size: int = 50,
    title_size: int = 20,
    subtitle: str = "Management System",
    subtitle_size: int = 12,
    padding: int = 20
) -> object:
    """Create a smaller page header for internal pages."""
    if ft is None:
        raise RuntimeError("Flet must be installed to create headers")
    
    return ft.Container(
        ft.Column([
            ft.Icon(ft.Icons.PETS, size=icon_size, color=ft.Colors.TEAL_700),
            ft.Text(title, size=title_size, weight="bold", color=ft.Colors.TEAL_900),
            ft.Text(subtitle, size=subtitle_size, color=ft.Colors.TEAL_700),
        ], horizontal_alignment="center", spacing=5),
        padding=padding,
    )


def create_sidebar_header() -> object:
    """Create a compact header for use in sidebars."""
    if ft is None:
        raise RuntimeError("Flet must be installed to create headers")
    
    return ft.Container(
        ft.Column([
            ft.Icon(ft.Icons.PETS, size=40, color=ft.Colors.TEAL_700),
            ft.Text("Paw Rescue", size=18, weight="bold", color=ft.Colors.BLACK87),
            ft.Text("Management System", size=10, color=ft.Colors.BLACK54),
        ], horizontal_alignment="center", spacing=3),
        padding=ft.padding.only(top=20, bottom=30),
    )
