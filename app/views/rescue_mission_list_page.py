"""Rescue missions list with status management and map.

Uses RescueState for state-driven data flow, ensuring consistency
with the application's state management pattern.
"""
from __future__ import annotations

from typing import Optional

from state import get_app_state
from services.map_service import MapService
import app_config
from app_config import RescueStatus
from components import (
    create_admin_sidebar, create_gradient_background,
    create_page_title, create_section_card, show_snackbar, create_archive_dialog, create_remove_dialog, create_scrollable_data_table,
    create_interactive_map,
)


class RescueMissionListPage:
    """Page for viewing and managing rescue missions.
    
    Uses RescueState for reactive data management.
    """
    
    def __init__(self, db_path: Optional[str] = None) -> None:
        self._db_path = db_path or app_config.DB_PATH
        self._app_state = get_app_state(self._db_path)
        self.map_service = MapService()

    def build(self, page, user_role: str = "user") -> None:
        try:
            import flet as ft
        except Exception as exc:
            raise RuntimeError("Flet must be installed to build the UI") from exc

        page.title = "Rescue Missions"

        is_admin = user_role == "admin"

        # Sidebar (for admin only)
        if is_admin:
            sidebar = create_admin_sidebar(page, current_route=page.route)
        else:
            sidebar = None

        # Load missions through state manager (active only for admin, excludes archived/removed)
        if is_admin:
            self._app_state.rescues.load_active_missions()
        else:
            self._app_state.rescues.load_missions()
        missions = self._app_state.rescues.missions

        # Helper to create status badge
        def make_status_badge(status: str, mission_id: int) -> object:
            # Determine color based on status using RescueStatus constants
            normalized = RescueStatus.normalize(status)
            
            # Check if status is cancelled (user cancelled) - show locked grey badge
            if RescueStatus.is_cancelled(status):
                return ft.Container(
                    ft.Row([
                        ft.Icon(ft.Icons.CANCEL, color=ft.Colors.WHITE, size=14),
                        ft.Text("Cancelled", color=ft.Colors.WHITE, size=11, weight="w500"),
                        ft.Icon(ft.Icons.LOCK, color=ft.Colors.WHITE70, size=12),
                    ], spacing=5, alignment=ft.MainAxisAlignment.CENTER),
                    padding=ft.padding.symmetric(horizontal=10, vertical=8),
                    bgcolor=ft.Colors.GREY_600,
                    border_radius=15,
                    tooltip="Cancelled by user - status locked",
                )
            
            if normalized == RescueStatus.RESCUED:
                bg_color = ft.Colors.GREEN_700
                icon = ft.Icons.CHECK_CIRCLE
            elif normalized == RescueStatus.FAILED:
                bg_color = ft.Colors.RED_700
                icon = ft.Icons.CANCEL
            elif normalized == RescueStatus.ONGOING:
                bg_color = ft.Colors.TEAL_600
                icon = ft.Icons.PETS
            else:  # PENDING or default
                bg_color = ft.Colors.ORANGE_700
                icon = ft.Icons.PENDING
            
            if is_admin:
                # Admin can change status with custom dropdown
                def change_status(e, new_status):
                    self._on_status_change(page, mission_id, new_status)
                
                return ft.Container(
                    ft.PopupMenuButton(
                        content=ft.Row([
                            ft.Icon(icon, color=ft.Colors.WHITE, size=14),
                            ft.Text(RescueStatus.get_label(status), color=ft.Colors.WHITE, size=11, weight="w500"),
                            ft.Icon(ft.Icons.ARROW_DROP_DOWN, color=ft.Colors.WHITE, size=14),
                        ], spacing=5, alignment=ft.MainAxisAlignment.CENTER),
                        items=[
                            ft.PopupMenuItem(
                                text=RescueStatus.get_label(RescueStatus.ONGOING),
                                icon=ft.Icons.PETS,
                                on_click=lambda e: change_status(e, RescueStatus.ONGOING),
                            ),
                            ft.PopupMenuItem(
                                text=RescueStatus.get_label(RescueStatus.RESCUED),
                                icon=ft.Icons.CHECK_CIRCLE,
                                on_click=lambda e: change_status(e, RescueStatus.RESCUED),
                            ),
                            ft.PopupMenuItem(
                                text=RescueStatus.get_label(RescueStatus.FAILED),
                                icon=ft.Icons.CANCEL,
                                on_click=lambda e: change_status(e, RescueStatus.FAILED),
                            ),
                        ],
                    ),
                    padding=ft.padding.symmetric(horizontal=10, vertical=8),
                    bgcolor=bg_color,
                    border_radius=15,
                )
            else:
                # User sees static badge
                return ft.Container(
                    ft.Row([
                        ft.Icon(icon, color=ft.Colors.WHITE, size=14),
                        ft.Text(RescueStatus.get_label(status), color=ft.Colors.WHITE, size=12, weight="w500"),
                    ], spacing=5, alignment=ft.MainAxisAlignment.CENTER),
                    padding=ft.padding.symmetric(horizontal=10, vertical=8),
                    bgcolor=bg_color,
                    border_radius=15,
                )

        # Helper to create admin action buttons (Archive/Remove)
        def make_admin_actions(mission_id: int, mission_name: str) -> object:
            # Use default argument to capture value at definition time
            def handle_archive(e, mid=mission_id):
                def on_confirm(note):
                    success = self._app_state.rescues.archive_mission(
                        mid, 
                        self._app_state.auth.user_id, 
                        note
                    )
                    if success:
                        show_snackbar(page, "Mission archived")
                        self.build(page, user_role="admin")
                    else:
                        show_snackbar(page, "Failed to archive mission", error=True)
                
                create_archive_dialog(
                    page,
                    item_type="rescue mission",
                    item_name=f"#{mid}",
                    on_confirm=on_confirm,
                )
            
            def handle_remove(e, mid=mission_id):
                def on_confirm(reason):
                    success = self._app_state.rescues.remove_mission(
                        mid,
                        self._app_state.auth.user_id,
                        reason
                    )
                    if success:
                        show_snackbar(page, "Mission removed")
                        self.build(page, user_role="admin")
                    else:
                        show_snackbar(page, "Failed to remove mission", error=True)
                
                create_remove_dialog(
                    page,
                    item_type="rescue mission",
                    item_name=f"#{mid}",
                    on_confirm=on_confirm,
                )
            
            return ft.Row([
                ft.IconButton(
                    icon=ft.Icons.ARCHIVE_OUTLINED,
                    icon_color=ft.Colors.AMBER_700,
                    icon_size=15,
                    tooltip="Archive",
                    on_click=handle_archive,
                ),
                ft.IconButton(
                    icon=ft.Icons.DELETE_OUTLINE,
                    icon_color=ft.Colors.RED_600,
                    icon_size=15,
                    tooltip="Remove",
                    on_click=handle_remove,
                ),
            ], spacing=0, tight=True)

        # Build table rows for DataTable
        table_rows = []
        if missions:
            for m in missions:
                mid = m.get("id")
                location = str(m.get("location", ""))
                notes = str(m.get("notes", ""))
                status = str(m.get("status", ""))

                # Use new columns instead of notes parsing
                name = m.get("animal_name") or m.get("reporter_name") or "Unknown"
                animal_type = m.get("animal_type") or "Unknown"
                reporter_phone = m.get("reporter_phone") or "N/A"
                details = notes  # Notes now contains only situation description
                
                # Truncate long text for table display
                location_display = location[:30] + "..." if len(location) > 30 else location
                details_display = details[:40] + "..." if len(details) > 40 else details

                # Build row data
                row_data = [
                    ft.Text(f"#{mid}", size=11, color=ft.Colors.TEAL_700, weight="w600"),
                    ft.Text(name, size=11, color=ft.Colors.BLACK87, weight="w500"),
                    ft.Text(animal_type, size=11, color=ft.Colors.BLACK87, weight="w500"),
                    ft.Text(reporter_phone, size=11, color=ft.Colors.BLACK87, weight="w500"),
                    ft.Container(
                        ft.Text(location_display, size=11, color=ft.Colors.BLACK87, weight="w500", tooltip=location if len(location) > 30 else None),
                        tooltip=location if len(location) > 30 else None,
                    ),
                    ft.Container(
                        ft.Text(details_display, size=11, color=ft.Colors.BLACK87, weight="w500"),
                        tooltip=details if len(details) > 40 else None,
                    ),
                ]
                
                # Add Urgency column with color-coded badge
                urgency = (m.get("urgency") or "medium").lower()
                urgency_colors = {
                    "low": (ft.Colors.GREEN_100, ft.Colors.GREEN_700),
                    "medium": (ft.Colors.ORANGE_100, ft.Colors.ORANGE_700),
                    "high": (ft.Colors.RED_100, ft.Colors.RED_700),
                }
                bg_color, text_color = urgency_colors.get(urgency, (ft.Colors.GREY_100, ft.Colors.GREY_700))
                urgency_badge = ft.Container(
                    ft.Text(urgency.capitalize(), size=11, color=text_color, weight="w500"),
                    bgcolor=bg_color,
                    padding=ft.padding.symmetric(horizontal=8, vertical=4),
                    border_radius=10,
                )
                row_data.append(urgency_badge)
                
                # Add Source column (Emergency or User based on user_id)
                is_emergency = m.get('user_id') is None
                user_id = m.get('user_id')
                if is_emergency:
                    source_cell = ft.Row([
                        ft.Icon(ft.Icons.WARNING_AMBER_ROUNDED, color=ft.Colors.RED_600, size=14),
                        ft.Text("Emergency", size=11, color=ft.Colors.RED_600, weight="w500"),
                    ], spacing=4, tight=True)
                else:
                    source_cell = ft.Row([
                        ft.Icon(ft.Icons.ACCOUNT_CIRCLE, color=ft.Colors.BLUE_600, size=14),
                        ft.Text(f"User #{user_id}", size=11, color=ft.Colors.BLUE_600, weight="w500",
                               tooltip=f"User ID: {user_id}"),
                    ], spacing=4, tight=True)
                row_data.append(source_cell)
                
                row_data.append(make_status_badge(status, mid))
                
                # Add admin actions column
                if is_admin:
                    row_data.append(make_admin_actions(mid, name))

                table_rows.append(row_data)
        
        # Define table columns with expand values for proper sizing
        table_columns = [
            {"label": "#", "expand": 0},
            {"label": "Reporter", "expand": 2},
            {"label": "Animal", "expand": 1},
            {"label": "Contact", "expand": 1},
            {"label": "Location", "expand": 2},
            {"label": "Details", "expand": 2},
            {"label": "Urgency", "expand": 1},
            {"label": "Source", "expand": 1},
            {"label": "Status", "expand": 2},
        ]
        
        # Add Actions column for admin
        if is_admin:
            table_columns.append({"label": "Actions", "expand": 1})

        # Create scrollable DataTable
        data_table = create_scrollable_data_table(
            columns=table_columns,
            rows=table_rows,
            height=400,
            empty_message="No rescue missions found",
            column_spacing=13,
            heading_row_height=45,
            data_row_height=50,
        )

        # Map with rescue mission markers (already filtered to active only)
        # Check internet connectivity before creating map
        is_online = self.map_service.check_map_tiles_available()
        
        if is_online:
            # Use the interactive map wrapper with lock/unlock toggle
            map_container = create_interactive_map(
                map_service=self.map_service,
                missions=missions,
                page=page,
                is_admin=is_admin,
                height=500,
                title="Realtime Rescue Mission Map",
                show_legend=True,
                initially_locked=True,
            )
        else:
            # Use offline fallback with mission details when map creation fails
            offline_widget = self.map_service.create_offline_map_fallback(missions, is_admin=is_admin)
            if offline_widget:
                map_container = ft.Container(
                    ft.Column([
                        ft.Text("Realtime Rescue Mission Map", size=16, weight="w600", color=ft.Colors.BLACK87),
                        ft.Container(height=15),
                        ft.Container(
                            offline_widget,
                            height=500,
                            border_radius=8,
                            border=ft.border.all(1, ft.Colors.AMBER_200),
                        ),
                    ], spacing=0),
                    padding=20,
                    bgcolor=ft.Colors.WHITE,
                    border_radius=12,
                    shadow=ft.BoxShadow(blur_radius=8, spread_radius=1, color=ft.Colors.BLACK12, offset=(0, 2)),
                )
            else:
                # Final fallback to simple placeholder
                map_container = ft.Container(
                    ft.Column([
                        ft.Text("Realtime Rescue Mission", size=16, weight="w600", color=ft.Colors.BLACK87),
                        ft.Container(height=15),
                        self.map_service.create_empty_map_placeholder(len(missions)),
                    ], spacing=0),
                    padding=20,
                    bgcolor=ft.Colors.WHITE,
                    border_radius=12,
                    shadow=ft.BoxShadow(blur_radius=8, spread_radius=1, color=ft.Colors.BLACK12, offset=(0, 2)),
                )

        # Build content list
        content_items = [
            create_page_title("Rescue Mission List"),
            ft.Container(height=20),
            # Rescue Mission List Section
            create_section_card(
                title="Rescue Missions",
                content=data_table,
                show_divider=True,
            ),
            ft.Container(height=20),
            # Map Container
            map_container,
            ft.Container(height=30),
        ]

        # Main content area
        main_content = ft.Container(
            ft.Column(content_items, spacing=0, scroll=ft.ScrollMode.AUTO, horizontal_alignment="center"),
            padding=30,
            expand=True,
        )

        # Main layout
        if sidebar:
            main_layout = ft.Row([sidebar, main_content], spacing=0, expand=True)
        else:
            main_layout = main_content

        page.controls.clear()
        page.add(create_gradient_background(main_layout))
        page.update()

    def _on_status_change(self, page, mission_id: int, new_status: str) -> None:
        """Update mission status using state manager."""
        try:
            updated = self._app_state.rescues.update_mission(mission_id, status=new_status)

            if updated:
                show_snackbar(page, "Status updated")
                # refresh
                self.build(page, user_role="admin")
            else:
                show_snackbar(page, "Failed to update status", error=True)
        except Exception as exc:
            show_snackbar(page, f"Error: {exc}", error=True)

