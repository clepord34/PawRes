"""Button components for the application."""
from __future__ import annotations
from typing import Callable, Optional

try:
    import flet as ft
except ImportError:
    ft = None


def create_nav_button(
    text: str,
    on_click: Callable,
    width: int = 160,
    icon: Optional[object] = None
) -> object:
    """Create a navigation button for sidebars."""
    if ft is None:
        raise RuntimeError("Flet must be installed to create buttons")
    
    content = [
        ft.Text(text, size=11 if width <= 160 else 13, weight="w500", 
                color=ft.Colors.BLACK87, text_align=ft.TextAlign.CENTER),
    ]
    
    return ft.Container(
        ft.TextButton(
            content=ft.Row(content, spacing=10, alignment=ft.MainAxisAlignment.CENTER),
            on_click=on_click,
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.WHITE,
                overlay_color=ft.Colors.TEAL_50,
                shape=ft.RoundedRectangleBorder(radius=8),
                padding=15,
            ),
        ),
        width=width,
        border=ft.border.all(2, ft.Colors.TEAL_400),
        border_radius=8,
    )


def create_action_button(
    text: str,
    on_click: Callable,
    width: int = 130,
    height: int = 45,
    bgcolor: object = None,
    color: object = None,
    outlined: bool = False,
    border_color: object = None
) -> object:
    """Create an action button (submit, cancel, etc.)."""
    if ft is None:
        raise RuntimeError("Flet must be installed to create buttons")
    
    if bgcolor is None:
        bgcolor = ft.Colors.TEAL_600
    if color is None:
        color = ft.Colors.WHITE
    
    if outlined:
        if border_color is None:
            border_color = bgcolor
        return ft.ElevatedButton(
            text,
            width=width,
            height=height,
            on_click=on_click,
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.WHITE,
                color=border_color,
                shape=ft.RoundedRectangleBorder(radius=8),
                side=ft.BorderSide(2, border_color),
                text_style=ft.TextStyle(size=14, weight="w500"),
            )
        )
    else:
        return ft.ElevatedButton(
            text,
            width=width,
            height=height,
            on_click=on_click,
            style=ft.ButtonStyle(
                bgcolor=bgcolor,
                color=color,
                shape=ft.RoundedRectangleBorder(radius=8),
                text_style=ft.TextStyle(size=14, weight="w500"),
            )
        )


def create_logout_button(on_click: Callable, width: int = 160) -> object:
    """Create a logout button for sidebars."""
    if ft is None:
        raise RuntimeError("Flet must be installed to create buttons")
    
    return ft.Container(
        ft.ElevatedButton(
            "Logout",
            width=width,
            height=45,
            on_click=on_click,
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.RED_400,
                color=ft.Colors.WHITE,
                shape=ft.RoundedRectangleBorder(radius=8),
            )
        ),
        padding=ft.padding.only(bottom=20),
    )


def create_table_action_button(
    text: str,
    on_click: Callable,
    bgcolor: object = None,
    icon: Optional[object] = None
) -> object:
    """Create a small action button for use in tables."""
    if ft is None:
        raise RuntimeError("Flet must be installed to create buttons")
    
    if bgcolor is None:
        bgcolor = ft.Colors.TEAL_400
    
    return ft.ElevatedButton(
        text,
        height=35,
        on_click=on_click,
        style=ft.ButtonStyle(
            bgcolor=bgcolor,
            color=ft.Colors.WHITE,
            shape=ft.RoundedRectangleBorder(radius=6),
        )
    )
