"""Interactive map wrapper component with lock/unlock functionality.

This component wraps the map control and provides a toggle to lock/unlock
map interactions, preventing accidental scrolling/zooming when users just
want to scroll the page.
"""
from __future__ import annotations

from typing import Optional, List, Tuple
import logging

logger = logging.getLogger(__name__)


def create_interactive_map(
    map_service,
    missions: List[dict],
    page,
    *,
    center: Optional[Tuple[float, float]] = None,
    zoom: Optional[float] = None,
    is_admin: bool = False,
    height: int = 350,
    title: str = "Rescue Missions Map",
    show_legend: bool = True,
    initially_locked: bool = True,
) -> object:
    """Create an interactive map with lock/unlock toggle.
    
    This wrapper provides a user-friendly map experience:
    - Map starts LOCKED by default to prevent accidental scroll-zoom
    - User can click "Unlock" button to enable full map interaction
    - Visual overlay indicates locked state clearly
    - Legend explains marker colors
    
    Args:
        map_service: MapService instance for creating the map
        missions: List of rescue mission dicts with coordinates
        page: Flet page for updates
        center: Optional center coordinates (lat, lng)
        zoom: Optional zoom level
        is_admin: If True, show admin-only info in tooltips
        height: Height of the map container in pixels
        title: Title text for the map section
        show_legend: If True, show the marker legend
        initially_locked: If True, start with map locked (recommended)
        
    Returns:
        Flet Container with the interactive map and controls
    """
    try:
        import flet as ft
    except ImportError:
        logger.error("Flet is required for map wrapper")
        return None
    
    # State for lock toggle
    is_locked = [initially_locked]  # Use list to allow mutation in nested function
    
    # Container references for updating
    map_container_ref = ft.Ref[ft.Container]()  # Reference to the map container
    map_stack_ref = ft.Ref[ft.Stack]()
    overlay_ref = ft.Ref[ft.Container]()
    lock_button_ref = ft.Ref[ft.Container]()
    status_badge_ref = ft.Ref[ft.Container]()
    
    def create_map_widget(locked: bool):
        """Create the map widget with current lock state."""
        map_widget = map_service.create_map_with_markers(
            missions=missions,
            center=center,
            zoom=zoom,
            is_admin=is_admin,
            locked=locked,
        )
        
        if map_widget is None:
            # Fallback if map can't be created
            return map_service.create_empty_map_placeholder(len(missions))
        
        return map_widget
    
    def toggle_lock(e):
        """Toggle the map lock state."""
        is_locked[0] = not is_locked[0]
        
        # IMPORTANT: Recreate the map with new lock state
        # The map control needs to be recreated because flet-map doesn't support
        # dynamic interaction flag changes
        new_map = create_map_widget(is_locked[0])
        if map_container_ref.current:
            map_container_ref.current.content = new_map
        
        # Update overlay visibility AND disabled state
        # When unlocked, overlay must be both invisible AND disabled to not block events
        if overlay_ref.current:
            overlay_ref.current.visible = is_locked[0]
            overlay_ref.current.disabled = not is_locked[0]
        
        # Update header button appearance
        if lock_button_ref.current:
            update_lock_button()
        
        # Update status badge
        if status_badge_ref.current:
            update_status_badge()
        
        page.update()
    
    def update_lock_button():
        """Update the header lock button appearance based on state."""
        if not lock_button_ref.current:
            return
        
        btn = lock_button_ref.current
        if is_locked[0]:
            btn.content = ft.Row([
                ft.Icon(ft.Icons.LOCK_OPEN_OUTLINED, size=14, color=ft.Colors.TEAL_700),
                ft.Text("Unlock", size=11, weight="w600", color=ft.Colors.TEAL_700),
            ], spacing=4, tight=True)
            btn.bgcolor = ft.Colors.TEAL_50
            btn.border = ft.border.all(1.5, ft.Colors.TEAL_400)
        else:
            btn.content = ft.Row([
                ft.Icon(ft.Icons.LOCK_OUTLINED, size=14, color=ft.Colors.WHITE),
                ft.Text("Lock", size=11, weight="w600", color=ft.Colors.WHITE),
            ], spacing=4, tight=True)
            btn.bgcolor = ft.Colors.TEAL_600
            btn.border = ft.border.all(1.5, ft.Colors.TEAL_700)
    
    def update_status_badge():
        """Update the status badge in corner."""
        if not status_badge_ref.current:
            return
        
        badge = status_badge_ref.current
        if is_locked[0]:
            badge.content = ft.Row([
                ft.Icon(ft.Icons.LOCK, size=12, color=ft.Colors.GREY_600),
                ft.Text("Locked", size=10, weight="w500", color=ft.Colors.GREY_600),
            ], spacing=3, tight=True)
            badge.bgcolor = ft.Colors.with_opacity(0.9, ft.Colors.WHITE)
        else:
            badge.content = ft.Row([
                ft.Icon(ft.Icons.OPEN_WITH, size=12, color=ft.Colors.TEAL_700),
                ft.Text("Interactive", size=10, weight="w500", color=ft.Colors.TEAL_700),
            ], spacing=3, tight=True)
            badge.bgcolor = ft.Colors.with_opacity(0.95, ft.Colors.TEAL_50)
    
    # Create the initial map
    initial_map = create_map_widget(is_locked[0])
    
    # Semi-transparent overlay when locked (clickable to unlock)
    lock_overlay = ft.Container(
        ref=overlay_ref,
        content=ft.Stack([
            # Dark background with centered content
            ft.Container(
                content=ft.Column(
                    [
                        ft.Icon(ft.Icons.TOUCH_APP, size=44, color=ft.Colors.WHITE),
                        ft.Text("Click to interact", size=16, weight="w600", color=ft.Colors.WHITE),
                        ft.Text("with the map", size=13, color=ft.Colors.with_opacity(0.85, ft.Colors.WHITE)),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=6,
                ),
                bgcolor=ft.Colors.with_opacity(0.65, ft.Colors.BLACK),
                expand=True,
                alignment=ft.alignment.center,
            ),
            # Bottom hint - stacked on top, positioned at bottom
            ft.Container(
                content=ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.INFO_OUTLINE, size=12, color=ft.Colors.GREY_700),
                        ft.Text("Scroll protection enabled", size=10, color=ft.Colors.GREY_700),
                    ], spacing=4, tight=True),
                    padding=ft.padding.symmetric(horizontal=10, vertical=5),
                    border_radius=4,
                    bgcolor=ft.Colors.with_opacity(0.92, ft.Colors.WHITE),
                ),
                bottom=12,
                left=0,
                right=0,
                alignment=ft.alignment.bottom_center,
            ),
        ]),
        expand=True,
        visible=is_locked[0],
        disabled=not is_locked[0],
        on_click=toggle_lock,
    )
    
    # Status badge (top-left corner of map) - doesn't block interaction
    status_badge = ft.Container(
        ref=status_badge_ref,
        content=ft.Row([
            ft.Icon(ft.Icons.LOCK, size=12, color=ft.Colors.GREY_600),
            ft.Text("Locked", size=10, weight="w500", color=ft.Colors.GREY_600),
        ], spacing=3, tight=True),
        padding=ft.padding.symmetric(horizontal=8, vertical=4),
        border_radius=4,
        bgcolor=ft.Colors.with_opacity(0.9, ft.Colors.WHITE),
        shadow=ft.BoxShadow(
            blur_radius=4,
            color=ft.Colors.with_opacity(0.15, ft.Colors.BLACK),
        ),
        top=8,
        left=8,
    )
    
    # Map with overlay stack
    # IMPORTANT: Use positioned children instead of expanding containers
    # to avoid blocking map interactions when unlocked
    map_with_overlay = ft.Stack([
        # Base map - fills the entire stack
        ft.Container(
            ref=map_container_ref,
            content=initial_map,
            expand=True,
        ),
        # Lock overlay (on top) - only visible when locked
        lock_overlay,
        # Status badge (positioned, doesn't expand)
        status_badge,
    ])
    
    # Header lock/unlock button
    lock_button = ft.Container(
        ref=lock_button_ref,
        content=ft.Row([
            ft.Icon(ft.Icons.LOCK_OPEN_OUTLINED, size=14, color=ft.Colors.TEAL_700),
            ft.Text("Unlock", size=11, weight="w600", color=ft.Colors.TEAL_700),
        ], spacing=4, tight=True),
        padding=ft.padding.symmetric(horizontal=12, vertical=6),
        border_radius=20,
        bgcolor=ft.Colors.TEAL_50,
        border=ft.border.all(1.5, ft.Colors.TEAL_400),
        on_click=toggle_lock,
        tooltip="Toggle map interactions (prevents accidental scrolling)",
        ink=True,
    )
    
    # Mission count badge
    mission_count = len([m for m in missions if m.get('latitude') and m.get('longitude')])
    count_badge = ft.Container(
        content=ft.Text(
            f"{mission_count} location{'s' if mission_count != 1 else ''}",
            size=10,
            color=ft.Colors.GREY_600,
            weight="w500",
        ),
        padding=ft.padding.symmetric(horizontal=8, vertical=3),
        border_radius=10,
        bgcolor=ft.Colors.GREY_100,
    )
    
    # Header row with title and controls
    header_row = ft.Container(
        content=ft.Row([
            ft.Row([
                ft.Container(
                    content=ft.Icon(ft.Icons.MAP_OUTLINED, size=18, color=ft.Colors.WHITE),
                    width=32,
                    height=32,
                    border_radius=8,
                    bgcolor=ft.Colors.TEAL_600,
                    alignment=ft.alignment.center,
                ),
                ft.Column([
                    ft.Text(title, size=14, weight="w600", color=ft.Colors.GREY_900),
                    ft.Text(
                        "Click map to enable pan & zoom" if is_locked[0] else "Drag to pan, scroll to zoom",
                        size=10,
                        color=ft.Colors.GREY_500,
                    ),
                ], spacing=0),
            ], spacing=10),
            ft.Row([
                count_badge,
                lock_button,
            ], spacing=8),
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        padding=ft.padding.only(bottom=10),
    )
    
    # Legend for marker colors (by urgency) - more compact design
    legend_items = []
    if show_legend and mission_count > 0:
        legend_items = [
            _create_legend_item(ft, ft.Colors.RED_500, "High"),
            _create_legend_item(ft, ft.Colors.DEEP_ORANGE_400, "Med"),
            _create_legend_item(ft, ft.Colors.AMBER_600, "Low"),
            ft.Container(width=1, height=14, bgcolor=ft.Colors.GREY_300),
            _create_legend_item(ft, ft.Colors.GREEN_600, "Done"),
        ]
    
    legend_row = ft.Container(
        content=ft.Row(
            legend_items,
            spacing=10,
            alignment=ft.MainAxisAlignment.CENTER,
        ),
        padding=ft.padding.only(top=8),
    ) if legend_items else ft.Container()
    
    # Map container with overlay
    map_wrapper = ft.Container(
        ref=map_stack_ref,
        content=map_with_overlay,
        height=height,
        border_radius=10,
        border=ft.border.all(1, ft.Colors.GREY_300),
        clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
        shadow=ft.BoxShadow(
            blur_radius=4,
            color=ft.Colors.with_opacity(0.08, ft.Colors.BLACK),
            offset=(0, 1),
        ),
    )
    
    # Complete wrapper with modern card style
    return ft.Container(
        ft.Column([
            header_row,
            map_wrapper,
            legend_row,
        ], spacing=0),
        padding=16,
        bgcolor=ft.Colors.WHITE,
        border_radius=14,
        border=ft.border.all(1, ft.Colors.GREY_200),
        shadow=ft.BoxShadow(
            blur_radius=12,
            spread_radius=1,
            color=ft.Colors.with_opacity(0.06, ft.Colors.BLACK),
            offset=(0, 3),
        ),
    )


def _create_legend_item(ft, color, label: str):
    """Helper to create a compact legend item."""
    return ft.Row([
        ft.Container(
            width=10,
            height=10,
            bgcolor=color,
            border_radius=5,
            border=ft.border.all(1, ft.Colors.with_opacity(0.3, ft.Colors.BLACK)),
        ),
        ft.Text(label, size=9, color=ft.Colors.GREY_600, weight="w500"),
    ], spacing=3, tight=True)


def create_simple_locked_map(
    map_service,
    missions: List[dict],
    *,
    center: Optional[Tuple[float, float]] = None,
    zoom: Optional[float] = None,
    is_admin: bool = False,
    height: int = 300,
    show_lock_badge: bool = True,
) -> object:
    """Create a simple locked map without the toggle UI.
    
    Useful for compact views where you just want a static map display.
    The map is always locked (no scroll/zoom) but markers are still visible.
    
    Args:
        map_service: MapService instance
        missions: List of rescue missions
        center: Optional center coordinates
        zoom: Optional zoom level
        is_admin: Show admin info in tooltips
        height: Map height in pixels
        show_lock_badge: Show a small "View Only" badge
        
    Returns:
        Flet Container with the locked map
    """
    try:
        import flet as ft
    except ImportError:
        return None
    
    map_widget = map_service.create_map_with_markers(
        missions=missions,
        center=center,
        zoom=zoom,
        is_admin=is_admin,
        locked=True,
    )
    
    if map_widget is None:
        return map_service.create_empty_map_placeholder(len(missions))
    
    # Badge to indicate view-only mode
    view_badge = ft.Container(
        content=ft.Row([
            ft.Icon(ft.Icons.VISIBILITY, size=11, color=ft.Colors.GREY_600),
            ft.Text("View Only", size=9, color=ft.Colors.GREY_600, weight="w500"),
        ], spacing=3, tight=True),
        padding=ft.padding.symmetric(horizontal=6, vertical=3),
        border_radius=4,
        bgcolor=ft.Colors.with_opacity(0.9, ft.Colors.WHITE),
        shadow=ft.BoxShadow(
            blur_radius=3,
            color=ft.Colors.with_opacity(0.12, ft.Colors.BLACK),
        ),
    ) if show_lock_badge else None
    
    # Stack map with optional badge
    if show_lock_badge:
        content = ft.Stack([
            ft.Container(content=map_widget, expand=True),
            ft.Container(
                content=view_badge,
                alignment=ft.alignment.top_left,
                padding=6,
                expand=True,
            ),
        ])
    else:
        content = map_widget
    
    return ft.Container(
        content=content,
        height=height,
        border_radius=10,
        border=ft.border.all(1, ft.Colors.GREY_300),
        clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
        shadow=ft.BoxShadow(
            blur_radius=4,
            color=ft.Colors.with_opacity(0.06, ft.Colors.BLACK),
            offset=(0, 1),
        ),
    )


__all__ = [
    "create_interactive_map",
    "create_simple_locked_map",
]
