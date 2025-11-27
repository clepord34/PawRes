"""Rescue missions list with status management and map."""
from __future__ import annotations

from typing import Optional

from services.rescue_service import RescueService
from services.map_service import MapService
import app_config
from components import create_admin_sidebar, create_mission_status_badge, create_gradient_background


class RescueMissionListPage:
    def __init__(self, db_path: Optional[str] = None) -> None:
        self.rescue_service = RescueService(db_path or app_config.DB_PATH)
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

        missions = self.rescue_service.get_all_missions()

        # Helper to create status badge
        def make_status_badge(status: str, mission_id: int) -> object:
            # Determine color based on status
            if status == "Rescued":
                bg_color = ft.Colors.GREEN_700
                icon = ft.Icons.CHECK_CIRCLE
            else:  # On-going or default
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
                # User sees static badge
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

        # Build table rows content
        table_rows_content = []
        if missions:
            for m in missions:
                mid = m.get("id")
                location = str(m.get("location", ""))
                notes = str(m.get("notes", ""))
                status = str(m.get("status", ""))

                # Parse notes to extract name and type
                name = ""
                animal_type = ""
                details = ""
                if notes:
                    lines = notes.split("\n")
                    for line in lines:
                        if line.startswith("name:"):
                            name = line.replace("name:", "").strip()
                        elif line.startswith("type:"):
                            animal_type = line.replace("type:", "").strip()
                        else:
                            if line.strip() and not line.startswith("name:") and not line.startswith("type:"):
                                details = line.strip()

                table_rows_content.append(
                    ft.Column([
                        ft.Row([
                            ft.Text(name or "Unknown", size=13, color=ft.Colors.BLACK87, expand=2),
                            ft.Text(animal_type or "Unknown", size=13, color=ft.Colors.BLACK87, expand=2),
                            ft.Text(location, size=13, color=ft.Colors.BLACK87, expand=3),
                            ft.Text(details[:30] + "..." if len(details) > 30 else details, size=13, color=ft.Colors.BLACK87, expand=3),
                            ft.Container(make_status_badge(status, mid), expand=2),
                        ], spacing=15),
                        ft.Divider(height=1, color=ft.Colors.GREY_200),
                        ft.Container(height=8),
                    ], spacing=0)
                )
        
        # Table container
        table_container = ft.Container(
            ft.Column(
                [
                    ft.Row([
                        ft.Text("Name", size=13, weight="w600", color=ft.Colors.BLACK87, expand=2),
                        ft.Text("Type", size=13, weight="w600", color=ft.Colors.BLACK87, expand=2),
                        ft.Text("Location", size=13, weight="w600", color=ft.Colors.BLACK87, expand=3),
                        ft.Text("Details", size=13, weight="w600", color=ft.Colors.BLACK87, expand=3),
                        ft.Text("Status", size=13, weight="w600", color=ft.Colors.BLACK87, expand=2),
                    ], spacing=15),
                    ft.Divider(height=1, color=ft.Colors.GREY_300),
                    ft.Container(height=10),
                ] + (table_rows_content if table_rows_content else [
                    ft.Container(
                        ft.Text("No rescue missions found", size=13, color=ft.Colors.BLACK54),
                        padding=20,
                        alignment=ft.alignment.center,
                    )
                ]),
                spacing=0
            ),
            padding=20,
            bgcolor=ft.Colors.WHITE,
            border_radius=8,
        )

        # Map with rescue mission markers
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

        # Main content area
        main_content = ft.Container(
            ft.Column([
                ft.Text("Rescue Mission List", size=28, weight="bold", color=ft.Colors.with_opacity(0.6, ft.Colors.BLACK), text_align=ft.TextAlign.CENTER),
                ft.Container(height=20),
                # Rescue Mission List Section
                ft.Container(
                    ft.Column([
                        ft.Text("Rescue Mission List", size=18, weight="w600", color=ft.Colors.BLACK87),
                        ft.Container(height=10),
                        table_container,
                    ], spacing=0),
                    padding=20,
                    bgcolor=ft.Colors.WHITE,
                    border_radius=12,
                    shadow=ft.BoxShadow(blur_radius=8, spread_radius=1, color=ft.Colors.BLACK12, offset=(0, 2)),
                ),
                ft.Container(height=20),
                # Map Container
                map_container,
                ft.Container(height=30),
            ], spacing=0, scroll=ft.ScrollMode.AUTO, horizontal_alignment="center"),
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
        try:
            updated = self.rescue_service.update_rescue_status(mission_id, new_status)
            import flet as ft

            if updated:
                page.snack_bar = ft.SnackBar(ft.Text("Status updated"))
                page.snack_bar.open = True
                page.update()
                # refresh
                self.build(page, user_role="admin")
            else:
                page.snack_bar = ft.SnackBar(ft.Text("Failed to update status"))
                page.snack_bar.open = True
                page.update()
        except Exception as exc:
            import flet as ft

            page.snack_bar = ft.SnackBar(ft.Text(f"Error: {exc}"))
            page.snack_bar.open = True
            page.update()

