"""Rescue missions list with status management and map.

Uses RescueState for state-driven data flow, ensuring consistency
with the application's state management pattern.
"""
from __future__ import annotations

from typing import Optional

from state import get_app_state
from services.map_service import MapService
from services.rescue_service import RescueService
import app_config
from app_config import RescueStatus
from components import (
    create_admin_sidebar, create_mission_status_badge, create_gradient_background,
    create_page_title, create_section_card, create_map_container, create_empty_state,
    show_snackbar, create_archive_dialog, create_remove_dialog
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
            sidebar = create_admin_sidebar(page)
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
                        ft.Text("Cancelled", color=ft.Colors.WHITE, size=12, weight="w500"),
                        ft.Icon(ft.Icons.LOCK, color=ft.Colors.WHITE70, size=12),
                    ], spacing=5, alignment=ft.MainAxisAlignment.CENTER),
                    padding=ft.padding.symmetric(horizontal=12, vertical=6),
                    bgcolor=ft.Colors.GREY_600,
                    border_radius=15,
                    alignment=ft.alignment.center,
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
                icon = ft.Icons.PETS
            
            if is_admin:
                # Admin can change status with custom dropdown
                def change_status(e, new_status):
                    self._on_status_change(page, mission_id, new_status)
                
                return ft.Container(
                    ft.PopupMenuButton(
                        content=ft.Row([
                            ft.Icon(icon, color=ft.Colors.WHITE, size=14),
                            ft.Text(RescueStatus.get_label(status), color=ft.Colors.WHITE, size=12, weight="w500"),
                            ft.Icon(ft.Icons.ARROW_DROP_DOWN, color=ft.Colors.WHITE, size=16),
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
                    padding=ft.padding.symmetric(horizontal=12, vertical=6),
                    bgcolor=bg_color,
                    border_radius=15,
                    alignment=ft.alignment.center,
                )
            else:
                # User sees static badge
                return ft.Container(
                    ft.Row([
                        ft.Icon(icon, color=ft.Colors.WHITE, size=14),
                        ft.Text(RescueStatus.get_label(status), color=ft.Colors.WHITE, size=12, weight="w500"),
                    ], spacing=5, alignment=ft.MainAxisAlignment.CENTER),
                    padding=ft.padding.symmetric(horizontal=12, vertical=6),
                    bgcolor=bg_color,
                    border_radius=15,
                    alignment=ft.alignment.center,
                )

        # Helper to create admin action buttons (Archive/Remove)
        def make_admin_actions(mission_id: int, mission_name: str) -> object:
            # Use default argument to capture value at definition time
            def handle_archive(e, mid=mission_id):
                print(f"[DEBUG] Archive clicked for mission {mid}")
                def on_confirm(note):
                    print(f"[DEBUG] Archive confirmed with note: {note}")
                    success = self._app_state.rescues.archive_mission(
                        mid, 
                        self._app_state.auth.user_id, 
                        note
                    )
                    print(f"[DEBUG] Archive result: {success}")
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
                print(f"[DEBUG] Remove clicked for mission {mid}")
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
                    icon_size=20,
                    tooltip="Archive",
                    on_click=handle_archive,
                ),
                ft.IconButton(
                    icon=ft.Icons.DELETE_OUTLINE,
                    icon_color=ft.Colors.RED_600,
                    icon_size=20,
                    tooltip="Remove",
                    on_click=handle_remove,
                ),
            ], spacing=4)

        # Build table rows content
        table_rows_content = []
        if missions:
            for m in missions:
                mid = m.get("id")
                location = str(m.get("location", ""))
                notes = str(m.get("notes", ""))
                status = str(m.get("status", ""))

                # Use new columns instead of notes parsing
                name = m.get("animal_name") or m.get("reporter_name") or ""
                animal_type = m.get("animal_type") or ""
                details = notes  # Notes now contains only situation description

                # Create row
                row_controls = [
                    ft.Text(name or "Unknown", size=13, color=ft.Colors.BLACK87, expand=2),
                    ft.Text(animal_type or "Unknown", size=13, color=ft.Colors.BLACK87, expand=2),
                    ft.Text(location, size=13, color=ft.Colors.BLACK87, expand=3),
                    ft.Text(details[:30] + "..." if len(details) > 30 else details, size=13, color=ft.Colors.BLACK87, expand=2),
                    ft.Container(make_status_badge(status, mid), expand=2),
                ]
                
                # Add admin actions column
                if is_admin:
                    row_controls.append(ft.Container(make_admin_actions(mid, name), expand=1))

                table_rows_content.append(
                    ft.Column([
                        ft.Row(row_controls, spacing=15),
                        ft.Divider(height=1, color=ft.Colors.GREY_200),
                        ft.Container(height=8),
                    ], spacing=0)
                )
        
        # Table container
        header_controls = [
            ft.Text("Name", size=13, weight="w600", color=ft.Colors.BLACK87, expand=2),
            ft.Text("Type", size=13, weight="w600", color=ft.Colors.BLACK87, expand=2),
            ft.Text("Location", size=13, weight="w600", color=ft.Colors.BLACK87, expand=3),
            ft.Text("Details", size=13, weight="w600", color=ft.Colors.BLACK87, expand=2),
            ft.Text("Status", size=13, weight="w600", color=ft.Colors.BLACK87, expand=2),
        ]
        
        # Add Actions header for admin
        if is_admin:
            header_controls.append(ft.Text("Actions", size=13, weight="w600", color=ft.Colors.BLACK87, expand=1))

        table_container = ft.Container(
            ft.Column(
                [
                    ft.Row(header_controls, spacing=15),
                    ft.Divider(height=1, color=ft.Colors.GREY_300),
                    ft.Container(height=10),
                ] + (table_rows_content if table_rows_content else [
                    create_empty_state(
                        message="No rescue missions found",
                        padding=20
                    )
                ]),
                spacing=0
            ),
            padding=20,
            bgcolor=ft.Colors.WHITE,
            border_radius=8,
        )

        # Map with rescue mission markers (already filtered to active only)
        map_widget = self.map_service.create_map_with_markers(missions)
        
        if map_widget:
            map_container = ft.Container(
                ft.Column([
                    ft.Text("Realtime Rescue Mission Map", size=16, weight="w600", color=ft.Colors.BLACK87),
                    ft.Container(height=15),
                    ft.Container(
                        map_widget,
                        height=500,
                        border_radius=8,
                        clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
                        border=ft.border.all(1, ft.Colors.GREY_300),
                    ),
                ], spacing=0),
                padding=20,
                bgcolor=ft.Colors.WHITE,
                border_radius=12,
                shadow=ft.BoxShadow(blur_radius=8, spread_radius=1, color=ft.Colors.BLACK12, offset=(0, 2)),
            )
        else:
            # Fallback to placeholder
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
                content=table_container,
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

