"""Card container components for the application."""
from __future__ import annotations
from typing import List, Optional

try:
    import flet as ft
except ImportError:
    ft = None


def create_form_card(
    controls: List[object],
    width: int = 400,
    padding: int = 35,
    title: Optional[str] = None
) -> object:
    """Create a card container for forms."""
    if ft is None:
        raise RuntimeError("Flet must be installed to create cards")
    
    card_controls = []
    if title:
        card_controls.append(
            ft.Text(title, size=24, weight="w600", color=ft.Colors.BLACK87)
        )
        card_controls.append(ft.Container(height=25))
    
    card_controls.extend(controls)
    
    return ft.Container(
        ft.Column(
            card_controls,
            horizontal_alignment="center",
            spacing=0,
        ),
        padding=padding,
        alignment=ft.alignment.center,
        width=width,
        bgcolor=ft.Colors.WHITE,
        border_radius=16,
        shadow=ft.BoxShadow(
            blur_radius=30, 
            spread_radius=0, 
            color=ft.Colors.with_opacity(0.15, ft.Colors.BLACK), 
            offset=(0, 10)
        ),
    )


def create_content_card(
    controls: List[object],
    width: int = 550,
    padding: int = 25,
    title: Optional[str] = None,
    subtitle: Optional[str] = None
) -> object:
    """Create a card container for content pages."""
    if ft is None:
        raise RuntimeError("Flet must be installed to create cards")
    
    card_controls = []
    if title:
        card_controls.append(
            ft.Text(title, size=22, weight="bold", color=ft.Colors.BLACK87)
        )
    if subtitle:
        card_controls.append(
            ft.Text(subtitle, size=12, color=ft.Colors.BLACK54)
        )
    if title or subtitle:
        card_controls.append(
            ft.Divider(height=12, color=ft.Colors.GREY_300)
        )
    
    card_controls.extend(controls)
    
    return ft.Container(
        ft.Column(card_controls, spacing=10, horizontal_alignment="center"),
        width=width,
        padding=padding,
        bgcolor=ft.Colors.WHITE,
        border_radius=12,
        shadow=ft.BoxShadow(
            blur_radius=20, 
            spread_radius=5, 
            color=ft.Colors.BLACK12, 
            offset=(0, 5)
        ),
    )


def create_dashboard_card(
    title: str,
    value: str,
    subtitle: str = "",
    icon: Optional[object] = None,
    bgcolor: object = None,
    width: int = 250
) -> object:
    """Create a statistics card for dashboards."""
    if ft is None:
        raise RuntimeError("Flet must be installed to create cards")
    
    if bgcolor is None:
        bgcolor = ft.Colors.WHITE
    
    card_content = [
        ft.Text(title, size=14, color=ft.Colors.BLACK54, weight="w500"),
        ft.Text(value, size=32, weight="bold", color=ft.Colors.BLACK87),
    ]
    
    if subtitle:
        card_content.append(
            ft.Text(subtitle, size=12, color=ft.Colors.GREEN_600)
        )
    
    return ft.Container(
        ft.Column(card_content, spacing=5),
        width=width,
        padding=20,
        bgcolor=bgcolor,
        border_radius=12,
        shadow=ft.BoxShadow(
            blur_radius=8, 
            spread_radius=1, 
            color=ft.Colors.BLACK12, 
            offset=(0, 2)
        ),
    )
