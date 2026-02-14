"""Card container components for the application."""
from __future__ import annotations
from typing import List, Optional

try:
    import flet as ft
except ImportError:
    ft = None


def create_form_card(
    controls: List[object],
    width: Optional[int] = None,
    padding: int = 35,
    title: Optional[str] = None,
    max_width: int = 480,
) -> object:
    """Create a card container for forms.
    
    Args:
        controls: List of controls to place inside the card.
        width: Explicit width (None = responsive, constrained by max_width).
        padding: Inner padding.
        title: Optional title text.
        max_width: Maximum width when responsive (width=None).
    """
    if ft is None:
        raise RuntimeError("Flet must be installed to create cards")
    
    card_controls = []
    if title:
        card_controls.append(
            ft.Text(title, size=24, weight="w600", color=ft.Colors.BLACK87)
        )
        card_controls.append(ft.Container(height=25))
    
    card_controls.extend(controls)
    
    container_kwargs = {
        "padding": padding,
        "alignment": ft.alignment.center,
        "bgcolor": ft.Colors.WHITE,
        "border_radius": 16,
        "shadow": ft.BoxShadow(
            blur_radius=30, 
            spread_radius=0, 
            color=ft.Colors.with_opacity(0.15, ft.Colors.BLACK), 
            offset=(0, 10)
        ),
    }
    
    if width is not None:
        container_kwargs["width"] = width
    else:
        container_kwargs["expand"] = True
        if max_width:
            container_kwargs["width"] = max_width
    
    return ft.Container(
        ft.Column(
            card_controls,
            horizontal_alignment="center",
            spacing=0,
        ),
        **container_kwargs,
    )


def create_content_card(
    controls: List[object],
    width: Optional[int] = None,
    padding: int = 25,
    title: Optional[str] = None,
    subtitle: Optional[str] = None,
    max_width: int = 600,
) -> object:
    """Create a card container for content pages.
    
    Args:
        controls: List of controls to place inside the card.
        width: Explicit width (None = responsive, constrained by max_width).
        padding: Inner padding.
        title: Optional title text.
        subtitle: Optional subtitle text.
        max_width: Maximum width when responsive (width=None).
    """
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
    
    container_kwargs = {
        "padding": padding,
        "bgcolor": ft.Colors.WHITE,
        "border_radius": 12,
        "shadow": ft.BoxShadow(
            blur_radius=20, 
            spread_radius=5, 
            color=ft.Colors.BLACK12, 
            offset=(0, 5)
        ),
    }
    
    if width is not None:
        container_kwargs["width"] = width
    else:
        container_kwargs["expand"] = True
        if max_width:
            container_kwargs["width"] = max_width
    
    return ft.Container(
        ft.Column(card_controls, spacing=10, horizontal_alignment="center"),
        **container_kwargs,
    )
