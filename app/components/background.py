"""Background components for the application."""
from __future__ import annotations
from typing import Optional

try:
    import flet as ft
except ImportError:
    ft = None


def create_gradient_background(
    content: object,
    start_color: Optional[object] = None,
    end_color: Optional[object] = None
) -> object:
    """Create a gradient background container."""
    if ft is None:
        raise RuntimeError("Flet must be installed to create backgrounds")
    
    if start_color is None:
        start_color = ft.Colors.LIGHT_BLUE_50
    if end_color is None:
        end_color = ft.Colors.AMBER_50
    
    return ft.Container(
        content,
        expand=True,
        width=float('inf'),
        height=float('inf'),
        gradient=ft.LinearGradient(
            begin=ft.alignment.top_center,
            end=ft.alignment.bottom_center,
            colors=[start_color, end_color]
        )
    )


def create_centered_layout(
    content: object,
    with_gradient: bool = True,
    scrollable: bool = False
) -> object:
    """Create a centered layout with optional gradient background."""
    if ft is None:
        raise RuntimeError("Flet must be installed to create layouts")
    
    scroll_mode = ft.ScrollMode.AUTO if scrollable else None
    
    layout = ft.Column(
        [content],
        alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        expand=True,
        scroll=scroll_mode,
        spacing=10
    )
    
    if with_gradient:
        return create_gradient_background(layout)
    else:
        return ft.Container(
            layout,
            expand=True,
            width=float('inf'),
            height=float('inf'),
        )
