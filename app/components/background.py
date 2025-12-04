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
