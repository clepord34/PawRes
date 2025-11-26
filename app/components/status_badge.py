"""Status badge components for the application."""
from __future__ import annotations
from typing import Optional, Callable

try:
    import flet as ft
except ImportError:
    ft = None


def create_status_badge(
    status: str,
    for_adoption: bool = True,
    with_icon: bool = True
) -> object:
    """Create a status badge for adoption requests."""
    if ft is None:
        raise RuntimeError("Flet must be installed to create status badges")
    
    status_lower = (status or "").lower()
    
    # Determine color and icon based on status
    if status_lower in ("approved", "adopted", "completed", "rescued"):
        bgcolor = ft.Colors.GREEN_600
        icon = ft.Icons.CHECK_CIRCLE
        text = status.capitalize()
    elif status_lower == "denied":
        bgcolor = ft.Colors.RED_600
        icon = ft.Icons.CANCEL
        text = "Denied"
    elif status_lower == "pending":
        bgcolor = ft.Colors.ORANGE_600
        icon = ft.Icons.PENDING
        text = "Pending"
    elif status_lower == "on-going":
        bgcolor = ft.Colors.TEAL_400
        icon = ft.Icons.FAVORITE
        text = "On-going"
    else:
        bgcolor = ft.Colors.GREY_600
        icon = ft.Icons.INFO
        text = status.capitalize()
    
    if with_icon:
        content = ft.Row([
            ft.Icon(icon, size=16, color=ft.Colors.WHITE),
            ft.Text(text, size=12, color=ft.Colors.WHITE, weight="w500"),
        ], spacing=5, alignment="center")
    else:
        content = ft.Text(text, size=12, color=ft.Colors.WHITE, weight="w500")
    
    return ft.Container(
        content,
        bgcolor=bgcolor,
        padding=ft.padding.symmetric(horizontal=15, vertical=8),
        border_radius=20,
    )


def create_mission_status_badge(
    status: str,
    mission_id: int,
    is_admin: bool = False,
    on_status_change: Optional[Callable] = None
) -> object:
    """Create a status badge for rescue missions with optional admin controls."""
    if ft is None:
        raise RuntimeError("Flet must be installed to create status badges")
    
    # Determine color and icon based on status
    if status == "Rescued":
        bg_color = ft.Colors.GREEN_700
        icon = ft.Icons.CHECK_CIRCLE
    else:  # On-going or default
        bg_color = ft.Colors.ORANGE_700
        icon = ft.Icons.PETS
    
    if is_admin and on_status_change:
        # Admin can change status with popup menu
        def change_status(e, new_status):
            on_status_change(mission_id, new_status)
        
        return ft.Container(
            ft.PopupMenuButton(
                content=ft.Row([
                    ft.Icon(icon, color=ft.Colors.WHITE, size=14),
                    ft.Text(status, color=ft.Colors.WHITE, size=12, weight="w500"),
                    ft.Icon(ft.Icons.ARROW_DROP_DOWN, color=ft.Colors.WHITE, size=16),
                ], spacing=5, alignment=ft.MainAxisAlignment.CENTER),
                items=[
                    ft.PopupMenuItem(
                        text="On-going",
                        icon=ft.Icons.PETS,
                        on_click=lambda e: change_status(e, "On-going"),
                    ),
                    ft.PopupMenuItem(
                        text="Rescued",
                        icon=ft.Icons.CHECK_CIRCLE,
                        on_click=lambda e: change_status(e, "Rescued"),
                    ),
                ],
            ),
            padding=ft.padding.symmetric(horizontal=12, vertical=6),
            bgcolor=bg_color,
            border_radius=15,
            alignment=ft.alignment.center,
        )
    else:
        # Static badge for regular users
        return ft.Container(
            ft.Row([
                ft.Icon(icon, color=ft.Colors.WHITE, size=14),
                ft.Text(status, color=ft.Colors.WHITE, size=12, weight="w500"),
            ], spacing=5, alignment=ft.MainAxisAlignment.CENTER),
            padding=ft.padding.symmetric(horizontal=12, vertical=6),
            bgcolor=bg_color,
            border_radius=15,
            alignment=ft.alignment.center,
        )


def create_adoption_status_dropdown(
    current_status: str,
    request_id: int,
    on_change: Callable
) -> object:
    """Create a dropdown for admins to change adoption request status."""
    if ft is None:
        raise RuntimeError("Flet must be installed to create dropdowns")
    
    # Determine dropdown color
    status_lower = current_status.lower()
    if status_lower == "approved":
        dropdown_color = ft.Colors.GREEN_600
    elif status_lower == "denied":
        dropdown_color = ft.Colors.RED_600
    else:
        dropdown_color = ft.Colors.ORANGE_600
    
    return ft.Dropdown(
        value=current_status.capitalize(),
        options=[
            ft.dropdown.Option("Approved"),
            ft.dropdown.Option("Denied")
        ],
        on_change=lambda e: on_change(request_id, e.control.value),
        width=140,
        bgcolor=dropdown_color,
        border_color=dropdown_color,
        text_style=ft.TextStyle(color=ft.Colors.WHITE, size=12, weight="w500"),
        color=ft.Colors.WHITE,
        filled=True,
        content_padding=10,
    )
