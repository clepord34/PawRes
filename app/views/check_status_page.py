"""Page for users to check their application statuses."""
from __future__ import annotations
from typing import Optional, List, Dict

import app_config
from services.adoption_service import AdoptionService
from services.rescue_service import RescueService
from services.animal_service import AnimalService
from services.map_service import MapService
from state import get_app_state
from components import (
    create_user_sidebar, create_status_badge, create_gradient_background,
    create_page_title, create_section_card, create_map_container
)


class CheckStatusPage:
    def __init__(self, db_path: Optional[str] = None) -> None:
        self.db_path = db_path or app_config.DB_PATH
        self.adoption_service = AdoptionService(self.db_path)
        self.rescue_service = RescueService(self.db_path)
        self.animal_service = AnimalService(self.db_path)
        self.map_service = MapService()

    def build(self, page, user_id: int) -> None:
        try:
            import flet as ft
        except Exception as exc:
            raise RuntimeError("Flet must be installed to build the UI") from exc

        page.title = "Application Status"

        # Get user info from centralized state management
        app_state = get_app_state()
        user_name = app_state.auth.user_name or "User"

        # Sidebar with navigation (same as user dashboard)
        sidebar = create_user_sidebar(page, user_name)

        # Fetch user data
        adoptions = self.adoption_service.get_user_requests(user_id) or []
        rescues = self.rescue_service.get_user_missions(user_id) or []

        # Helper to create status badge with heart icon for "On-going"
        def make_status_badge(status: str) -> object:
            status_lower = (status or "").lower()
            
            if status_lower == "on-going":
                return ft.Container(
                    ft.Row([
                        ft.Icon(ft.Icons.FAVORITE, color=ft.Colors.WHITE, size=14),
                        ft.Text("On-going", color=ft.Colors.WHITE, size=12, weight="w500"),
                    ], spacing=5, alignment=ft.MainAxisAlignment.CENTER),
                    padding=ft.padding.symmetric(horizontal=12, vertical=6),
                    bgcolor=ft.Colors.TEAL_400,
                    border_radius=15,
                    alignment=ft.alignment.center,
                )
            elif status_lower == "rescued":
                return ft.Container(
                    ft.Row([
                        ft.Icon(ft.Icons.FAVORITE, color=ft.Colors.WHITE, size=14),
                        ft.Text("Rescued", color=ft.Colors.WHITE, size=12, weight="w500"),
                    ], spacing=5, alignment=ft.MainAxisAlignment.CENTER),
                    padding=ft.padding.symmetric(horizontal=12, vertical=6),
                    bgcolor=ft.Colors.TEAL_400,
                    border_radius=15,
                    alignment=ft.alignment.center,
                )
            elif status_lower == "pending":
                color = ft.Colors.YELLOW_700
                text = "Pending"
            elif status_lower in ("approved", "adopted", "completed"):
                color = ft.Colors.GREEN_600
                text = status.title()
            elif status_lower == "denied":
                color = ft.Colors.RED_600
                text = "Denied"
            else:
                color = ft.Colors.GREY_600
                text = status.title()
            
            return ft.Container(
                ft.Text(text, color=ft.Colors.WHITE, size=12, weight="w500"),
                padding=ft.padding.symmetric(horizontal=12, vertical=6),
                bgcolor=color,
                border_radius=15,
                alignment=ft.alignment.center,
            )

        # Build adoption requests table content
        adoption_rows_content = []
        if adoptions:
            for a in adoptions:
                # Fetch animal details
                animal_id = a.get("animal_id")
                animal = self.animal_service.get_animal_by_id(animal_id) if animal_id else None
                animal_name = animal.get("name", "Unknown") if animal else "Unknown"
                animal_type = animal.get("species", "Unknown") if animal else "Unknown"
                status = a.get("status", "pending")
                
                adoption_rows_content.append(
                    ft.Column([
                        ft.Row([
                            ft.Text(animal_name, size=13, color=ft.Colors.BLACK87, expand=2),
                            ft.Text(animal_type, size=13, color=ft.Colors.BLACK87, expand=2),
                            ft.Container(make_status_badge(status), expand=2),
                        ], spacing=20),
                        ft.Divider(height=1, color=ft.Colors.GREY_200),
                        ft.Container(height=8),
                    ], spacing=0)
                )

        adoption_table = ft.Container(
            ft.Column(
                [
                    ft.Row([
                        ft.Text("Animal Name", size=13, weight="w600", color=ft.Colors.BLACK87, expand=2),
                        ft.Text("Type", size=13, weight="w600", color=ft.Colors.BLACK87, expand=2),
                        ft.Text("Status", size=13, weight="w600", color=ft.Colors.BLACK87, expand=2),
                    ], spacing=20),
                    ft.Divider(height=1, color=ft.Colors.GREY_300),
                    ft.Container(height=10),
                ] + (adoption_rows_content if adoption_rows_content else [
                    ft.Container(
                        ft.Text("No adoption requests yet", size=13, color=ft.Colors.BLACK54),
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

        # Build rescue missions table
        rescue_rows_content = []
        if rescues:
            for r in rescues:
                # Parse animal type from notes
                notes = r.get("notes", "")
                animal_type = "Unknown"
                if "type:" in notes:
                    type_part = notes.split("type:")[1].split("\n")[0].strip()
                    animal_type = type_part if type_part else "Unknown"
                
                location = r.get("location", "Unknown")
                
                # Extract details (everything after type line)
                details = notes
                if "\n" in notes and "type:" in notes:
                    lines = notes.split("\n")
                    detail_lines = [l for l in lines if not l.startswith("name:") and not l.startswith("type:")]
                    details = " ".join(detail_lines).strip()
                details_display = details[:30] + "..." if len(details) > 30 else details
                
                status = r.get("status", "pending")
                
                rescue_rows_content.append(
                    ft.Column([
                        ft.Row([
                            ft.Text(animal_type, size=13, color=ft.Colors.BLACK87, expand=2),
                            ft.Text(location, size=13, color=ft.Colors.BLACK87, expand=3),
                            ft.Text(details_display, size=13, color=ft.Colors.BLACK87, expand=3),
                            ft.Container(make_status_badge(status), expand=2),
                        ], spacing=15),
                        ft.Divider(height=1, color=ft.Colors.GREY_200),
                        ft.Container(height=8),
                    ], spacing=0)
                )

        rescue_table = ft.Container(
            ft.Column(
                [
                    ft.Row([
                        ft.Text("Type", size=13, weight="w600", color=ft.Colors.BLACK87, expand=2),
                        ft.Text("Location", size=13, weight="w600", color=ft.Colors.BLACK87, expand=3),
                        ft.Text("Details", size=13, weight="w600", color=ft.Colors.BLACK87, expand=3),
                        ft.Text("Status", size=13, weight="w600", color=ft.Colors.BLACK87, expand=2),
                    ], spacing=15),
                    ft.Divider(height=1, color=ft.Colors.GREY_300),
                    ft.Container(height=10),
                ] + (rescue_rows_content if rescue_rows_content else [
                    ft.Container(
                        ft.Text("No rescue missions yet", size=13, color=ft.Colors.BLACK54),
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

        # Realtime Rescue Mission map with user's missions
        map_widget = self.map_service.create_map_with_markers(rescues)
        
        if map_widget:
            map_container = ft.Container(
                ft.Column([
                    ft.Text("Your Rescue Mission Locations", size=16, weight="w600", color=ft.Colors.BLACK87),
                    ft.Container(height=15),
                    ft.Container(
                        map_widget,
                        height=350,
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
                    ft.Text("Your Rescue Mission Locations", size=16, weight="w600", color=ft.Colors.BLACK87),
                    ft.Container(height=15),
                    self.map_service.create_empty_map_placeholder(len(rescues)),
                ], spacing=0),
                padding=20,
                bgcolor=ft.Colors.WHITE,
                border_radius=12,
                shadow=ft.BoxShadow(blur_radius=8, spread_radius=1, color=ft.Colors.BLACK12, offset=(0, 2)),
            )

        # Main content area
        main_content = ft.Container(
            ft.Column([
                create_page_title("Application Status"),
                ft.Container(height=20),
                # Adoption Requests Section
                create_section_card(
                    title="Adoption Requests",
                    content=adoption_table,
                ),
                ft.Container(height=20),
                # Rescue Missions Section
                create_section_card(
                    title="Reported Rescue Missions",
                    content=rescue_table,
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
        main_layout = ft.Row([sidebar, main_content], spacing=0, expand=True)

        page.controls.clear()
        page.add(create_gradient_background(main_layout))
        page.update()

    def _refresh_data(self, page, user_id: int) -> None:
        """Refresh the page by rebuilding with latest data."""
        self.build(page, user_id)


__all__ = ["CheckStatusPage"]

