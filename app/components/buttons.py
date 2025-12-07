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
    icon: Optional[object] = None,
    is_active: bool = False
) -> object:
    """Create a navigation button for sidebars.
    
    Args:
        text: Button label text
        on_click: Click handler callback
        width: Button width in pixels
        icon: Optional icon to display
        is_active: Whether this button represents the current page (for highlighting)
    """
    if ft is None:
        raise RuntimeError("Flet must be installed to create buttons")
    
    if is_active:
        bg_color = ft.Colors.TEAL_600
        text_color = ft.Colors.WHITE
        border_color = ft.Colors.TEAL_700
        overlay_color = ft.Colors.TEAL_700
    else:
        bg_color = ft.Colors.WHITE
        text_color = ft.Colors.BLACK87
        border_color = ft.Colors.TEAL_400
        overlay_color = ft.Colors.TEAL_50
    
    content = [
        ft.Text(text, size=11 if width <= 160 else 13, weight="w600" if is_active else "w500", 
                color=text_color, text_align=ft.TextAlign.CENTER),
    ]
    
    return ft.Container(
        ft.TextButton(
            content=ft.Row(content, spacing=10, alignment=ft.MainAxisAlignment.CENTER),
            on_click=on_click,
            style=ft.ButtonStyle(
                bgcolor=bg_color,
                overlay_color=overlay_color,
                shape=ft.RoundedRectangleBorder(radius=8),
                padding=15,
            ),
        ),
        width=width,
        border=ft.border.all(2, border_color),
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
    border_color: object = None,
    icon: object = None
) -> object:
    """Create an action button (submit, cancel, etc.).
    
    Args:
        text: Button text
        on_click: Click handler
        width: Button width
        height: Button height
        bgcolor: Background color
        color: Text color
        outlined: If True, creates outlined button
        border_color: Border color for outlined buttons
        icon: Optional icon to display
    """
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
            icon=icon,
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
            icon=icon,
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
            height=42,
            on_click=on_click,
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.RED_400,
                color=ft.Colors.WHITE,
                shape=ft.RoundedRectangleBorder(radius=8),
            )
        ),
        padding=ft.padding.only(bottom=10),
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


def create_ai_download_button(
    on_click: Callable,
    icon_size: int = 16,
    text_size: int = 12,
    height: int = 40,
    border_radius: int = 8,
    padding: Optional[object] = None
) -> object:
    """Create a Download AI Models button.
    
    This button is used to trigger the AI models download dialog.
    
    Args:
        on_click: Click handler callback
        icon_size: Size of the icon (default: 16)
        text_size: Size of the text (default: 12)
        height: Button height (default: 40)
        border_radius: Border radius for the button (default: 8)
        padding: Custom padding (default: symmetric horizontal=16, vertical=10)
        
    Returns:
        ElevatedButton configured for AI model downloads
    """
    if ft is None:
        raise RuntimeError("Flet must be installed to create buttons")
    
    if padding is None:
        padding = ft.padding.symmetric(horizontal=16, vertical=10)
    
    return ft.ElevatedButton(
        content=ft.Row([
            ft.Icon(ft.Icons.SMART_TOY, size=icon_size, color=ft.Colors.WHITE),
            ft.Text("Download AI Models", size=text_size, weight="w500", color=ft.Colors.WHITE),
        ], spacing=6),
        style=ft.ButtonStyle(
            bgcolor=ft.Colors.PURPLE_600,
            shape=ft.RoundedRectangleBorder(radius=border_radius),
            padding=padding,
        ),
        on_click=on_click,
        tooltip="Download AI models for breed classification",
        height=height,
    )
