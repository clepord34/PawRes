"""Page for users to check their application statuses.

Uses state managers for consistent data flow throughout the application.
"""
from __future__ import annotations
from typing import Optional, List, Dict

import app_config
from app_config import RescueStatus, AdoptionStatus
from services.map_service import MapService
from state import get_app_state
from components import (
    create_user_sidebar, create_status_badge, create_gradient_background,
    create_page_title, create_section_card, create_map_container,
    create_empty_state, show_snackbar, create_confirmation_dialog
)


class CheckStatusPage:
    """Page for users to check their adoption and rescue mission statuses.
    
    Uses state managers for reactive data management.
    """
    
    def __init__(self, db_path: Optional[str] = None) -> None:
        self._db_path = db_path or app_config.DB_PATH
        self._app_state = get_app_state(self._db_path)
        self.map_service = MapService()

    def build(self, page, user_id: int) -> None:
        try:
            import flet as ft
        except Exception as exc:
            raise RuntimeError("Flet must be installed to build the UI") from exc

        page.title = "Application Status"

        # Get user info from centralized state management
        user_name = self._app_state.auth.user_name or "User"

        # Sidebar with navigation (same as user dashboard)
        sidebar = create_user_sidebar(page, user_name)

        # Load user data through state managers
        self._app_state.adoptions.load_user_requests(user_id)
        self._app_state.rescues.load_user_missions(user_id)
        
        adoptions = self._app_state.adoptions.user_requests
        rescues = self._app_state.rescues.user_missions

        # Helper to show admin message dialog
        def show_admin_message_dialog(message: str):
            def handler(e):
                dialog = ft.AlertDialog(
                    modal=True,
                    title=ft.Text("Admin Message", size=16, weight="w600"),
                    content=ft.Container(
                        ft.Text(message, size=14, color=ft.Colors.BLACK87),
                        padding=10,
                        width=300,
                    ),
                    actions=[
                        ft.TextButton("Close", on_click=lambda e: page.close(dialog)),
                    ],
                    actions_alignment=ft.MainAxisAlignment.END,
                )
                page.open(dialog)
            return handler

        # Helper to create status badge with heart icon for "On-going"
        def make_status_badge(status: str, admin_message: str = "", is_rescue: bool = False, 
                              removal_reason: str = "", archive_note: str = "") -> object:
            status_lower = (status or "").lower()
            
            # Check for cancelled state using status constants
            is_cancelled = RescueStatus.is_cancelled(status) if is_rescue else AdoptionStatus.is_cancelled(status)
            
            # Check for archived state
            is_archived = RescueStatus.is_archived(status) if is_rescue else AdoptionStatus.is_archived(status)
            
            # Check for removed state
            is_removed = RescueStatus.is_removed(status) if is_rescue else AdoptionStatus.is_removed(status)
            
            if is_cancelled:
                # Show user-cancelled status in grey
                return ft.Container(
                    ft.Row([
                        ft.Icon(ft.Icons.CANCEL, color=ft.Colors.WHITE, size=14),
                        ft.Text("Cancelled", color=ft.Colors.WHITE, size=12, weight="w500"),
                    ], spacing=5, alignment=ft.MainAxisAlignment.CENTER),
                    padding=ft.padding.symmetric(horizontal=12, vertical=6),
                    bgcolor=ft.Colors.GREY_600,
                    border_radius=15,
                    alignment=ft.alignment.center,
                )
            elif is_removed:
                # Show removed status with reason
                reason_text = removal_reason or "Administrative action"
                return ft.Container(
                    ft.Column([
                        ft.Row([
                            ft.Icon(ft.Icons.DELETE_OUTLINE, color=ft.Colors.WHITE, size=14),
                            ft.Text("Removed", color=ft.Colors.WHITE, size=12, weight="w500"),
                        ], spacing=5, alignment=ft.MainAxisAlignment.CENTER),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2),
                    padding=ft.padding.symmetric(horizontal=12, vertical=6),
                    bgcolor=ft.Colors.RED_700,
                    border_radius=15,
                    alignment=ft.alignment.center,
                    tooltip=f"Removed: {reason_text}",
                )
            elif is_archived:
                # For users: DON'T show that it's archived - just show original status normally
                # Get the base status without the |archived suffix
                base_status = RescueStatus.get_base_status(status) if is_rescue else AdoptionStatus.get_base_status(status)
                # Recursively call make_status_badge with the base status (not archived)
                # This will show the original status badge (rescued, pending, approved, etc.)
                return make_status_badge(base_status, admin_message, is_rescue)
            elif is_rescue:
                # Use RescueStatus for rescue missions
                normalized = RescueStatus.normalize(status)
                if normalized == RescueStatus.ONGOING:
                    return ft.Container(
                        ft.Row([
                            ft.Icon(ft.Icons.FAVORITE, color=ft.Colors.WHITE, size=14),
                            ft.Text(RescueStatus.get_label(RescueStatus.ONGOING), color=ft.Colors.WHITE, size=12, weight="w500"),
                        ], spacing=5, alignment=ft.MainAxisAlignment.CENTER),
                        padding=ft.padding.symmetric(horizontal=12, vertical=6),
                        bgcolor=ft.Colors.TEAL_400,
                        border_radius=15,
                        alignment=ft.alignment.center,
                    )
                elif normalized == RescueStatus.RESCUED:
                    return ft.Container(
                        ft.Row([
                            ft.Icon(ft.Icons.FAVORITE, color=ft.Colors.WHITE, size=14),
                            ft.Text(RescueStatus.get_label(RescueStatus.RESCUED), color=ft.Colors.WHITE, size=12, weight="w500"),
                        ], spacing=5, alignment=ft.MainAxisAlignment.CENTER),
                        padding=ft.padding.symmetric(horizontal=12, vertical=6),
                        bgcolor=ft.Colors.TEAL_400,
                        border_radius=15,
                        alignment=ft.alignment.center,
                    )
                elif normalized == RescueStatus.FAILED:
                    return ft.Container(
                        ft.Row([
                            ft.Icon(ft.Icons.CANCEL, color=ft.Colors.WHITE, size=14),
                            ft.Text(RescueStatus.get_label(RescueStatus.FAILED), color=ft.Colors.WHITE, size=12, weight="w500"),
                        ], spacing=5, alignment=ft.MainAxisAlignment.CENTER),
                        padding=ft.padding.symmetric(horizontal=12, vertical=6),
                        bgcolor=ft.Colors.RED_600,
                        border_radius=15,
                        alignment=ft.alignment.center,
                    )
                elif normalized == RescueStatus.PENDING:
                    color = ft.Colors.YELLOW_700
                    text = RescueStatus.get_label(RescueStatus.PENDING)
                else:
                    color = ft.Colors.GREY_600
                    text = status.title()
            else:
                # Use AdoptionStatus for adoption requests
                normalized = AdoptionStatus.normalize(status)
                if normalized == AdoptionStatus.PENDING:
                    color = ft.Colors.YELLOW_700
                    text = AdoptionStatus.get_label(AdoptionStatus.PENDING)
                elif normalized == AdoptionStatus.APPROVED:
                    color = ft.Colors.GREEN_600
                    text = AdoptionStatus.get_label(AdoptionStatus.APPROVED)
                elif normalized == AdoptionStatus.DENIED:
                    color = ft.Colors.RED_600
                    text = AdoptionStatus.get_label(AdoptionStatus.DENIED)
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

        # Helper function to handle edit button click
        def on_edit_click(request_id: int, animal_id: int):
            def handler(e):
                page.go(f"/adoption_form?animal_id={animal_id}&edit_request_id={request_id}")
            return handler

        # Helper function to handle cancel button click
        def on_cancel_click(request_id: int, animal_name: str):
            def handler(e):
                def on_confirm():
                    try:
                        # Use cancel_request for soft cancel
                        from services.adoption_service import AdoptionService
                        adoption_service = AdoptionService(self._db_path)
                        cancelled = adoption_service.cancel_request(request_id)
                        if cancelled:
                            show_snackbar(page, f"Adoption request for '{animal_name}' has been cancelled")
                            self._refresh_data(page, user_id)
                        else:
                            show_snackbar(page, "Failed to cancel request (may not be pending)", error=True)
                    except Exception as exc:
                        show_snackbar(page, f"Error: {exc}", error=True)
                
                create_confirmation_dialog(
                    page,
                    title="Cancel Adoption Request",
                    message=f"Are you sure you want to cancel your adoption request for '{animal_name}'?",
                    on_confirm=on_confirm,
                    confirm_text="Cancel Request",
                    cancel_text="Keep Request",
                )
            return handler

        # Build adoption requests table content
        adoption_rows_content = []
        if adoptions:
            for a in adoptions:
                # Fetch animal details using state manager
                animal_id = a.get("animal_id")
                request_id = a.get("id")
                stored_animal_name = a.get("animal_name")  # Column for deleted animals
                stored_animal_species = a.get("animal_species")  # Column for deleted animals
                
                # Handle case where animal was removed (animal_id is NULL)
                animal_was_deleted = False
                if animal_id and animal_id > 0:
                    animal = self._app_state.animals.get_animal_by_id(animal_id)
                    if animal:
                        animal_name = animal.get("name", "Unknown")
                        animal_type = animal.get("species", "Unknown")
                    else:
                        # Animal was deleted but ID still referenced
                        animal_name = stored_animal_name or "Unknown"
                        animal_type = stored_animal_species or "-"
                        animal_was_deleted = True
                else:
                    # animal_id is NULL (deleted marker)
                    animal_name = stored_animal_name or "Unknown"
                    animal_type = stored_animal_species or "-"
                    animal_was_deleted = True
                
                status = a.get("status", "pending")
                status_lower = (status or "").lower()
                removal_reason = a.get("removal_reason", "")
                archive_note = a.get("archive_note", "")
                
                # Create action buttons for pending requests (only if animal still exists)
                if status_lower == "pending" and animal_id and animal_id > 0:
                    actions = ft.Row([
                        ft.TextButton(
                            "Edit",
                            icon=ft.Icons.EDIT,
                            icon_color=ft.Colors.BLUE_600,
                            style=ft.ButtonStyle(color=ft.Colors.BLUE_600),
                            on_click=on_edit_click(request_id, animal_id),
                        ),
                        ft.TextButton(
                            "Cancel",
                            icon=ft.Icons.CANCEL,
                            icon_color=ft.Colors.RED_600,
                            style=ft.ButtonStyle(color=ft.Colors.RED_600),
                            on_click=on_cancel_click(request_id, animal_name),
                        ),
                    ], spacing=5)
                else:
                    actions = ft.Text("-", size=13, color=ft.Colors.BLACK54)
                
                # Get admin message if exists
                admin_message = a.get("admin_message", "")
                
                # Build animal name display - strikethrough if animal deleted
                if animal_was_deleted:
                    animal_name_display = ft.Text(animal_name, size=13, color=ft.Colors.GREY_500, italic=True)
                else:
                    animal_name_display = ft.Text(animal_name, size=13, color=ft.Colors.BLACK87)
                
                # Build status display - combine status with "Animal Deleted" if applicable
                if animal_was_deleted:
                    # Show "[status] - Animal Deleted" in grey
                    status_display = ft.Container(
                        ft.Column([
                            make_status_badge(status, admin_message, is_rescue=False, 
                                            removal_reason=removal_reason, archive_note=archive_note),
                            ft.Text("(Animal Deleted)", size=10, color=ft.Colors.GREY_500, italic=True),
                        ], spacing=2, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    )
                else:
                    status_display = make_status_badge(status, admin_message, is_rescue=False,
                                                      removal_reason=removal_reason, archive_note=archive_note)
                
                adoption_rows_content.append(
                    ft.Column([
                        ft.Row([
                            ft.Container(animal_name_display, expand=2),
                            ft.Text(animal_type, size=13, color=ft.Colors.GREY_500 if animal_was_deleted else ft.Colors.BLACK87, expand=2),
                            ft.Container(status_display, expand=2),
                            ft.Container(actions, expand=2),
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
                        ft.Text("Actions", size=13, weight="w600", color=ft.Colors.BLACK87, expand=2),
                    ], spacing=20),
                    ft.Divider(height=1, color=ft.Colors.GREY_300),
                    ft.Container(height=10),
                ] + (adoption_rows_content if adoption_rows_content else [
                    create_empty_state(
                        message="No adoption requests yet",
                        padding=20
                    )
                ]),
                spacing=0
            ),
            padding=20,
            bgcolor=ft.Colors.WHITE,
            border_radius=8,
        )

        # Helper for cancel rescue mission click
        def on_cancel_rescue_click(mission_id: int, animal_type: str, location: str):
            def handler(e):
                from services.rescue_service import RescueService
                
                def on_confirm():
                    rescue_service = RescueService(self._db_path)
                    success = rescue_service.cancel_mission(mission_id, user_id)
                    if success:
                        show_snackbar(page, "Rescue mission cancelled successfully")
                        self.build(page, user_id)  # Refresh page
                    else:
                        show_snackbar(page, "Failed to cancel rescue mission. It may have already been processed.", error=True)
                
                create_confirmation_dialog(
                    page,
                    title="Cancel Rescue Report",
                    message=f"Are you sure you want to cancel your rescue report for '{animal_type}' at '{location}'?",
                    on_confirm=on_confirm,
                    confirm_text="Cancel Report",
                    cancel_text="Keep Report",
                )
            return handler

        # Build rescue missions table
        rescue_rows_content = []
        if rescues:
            for r in rescues:
                mission_id = r.get("id")
                # Use new database columns directly instead of parsing notes
                animal_type = r.get("animal_type") or "Unknown"
                location = r.get("location") or "Unknown"
                
                # Details from notes (now just contains situation description)
                details = r.get("notes", "")
                details_display = details[:30] + "..." if len(details) > 30 else details
                
                status = r.get("status", "pending")
                admin_message = r.get("admin_message", "")
                removal_reason = r.get("removal_reason", "")
                archive_note = r.get("archive_note", "")
                status_lower = (status or "").lower()
                
                # Create action buttons for pending rescue missions
                if status_lower == "pending":
                    rescue_actions = ft.Row([
                        ft.TextButton(
                            "Cancel",
                            icon=ft.Icons.CANCEL,
                            icon_color=ft.Colors.RED_600,
                            style=ft.ButtonStyle(color=ft.Colors.RED_600),
                            on_click=on_cancel_rescue_click(mission_id, animal_type, location),
                        ),
                    ], spacing=5)
                else:
                    rescue_actions = ft.Text("-", size=13, color=ft.Colors.BLACK54)
                
                rescue_rows_content.append(
                    ft.Column([
                        ft.Row([
                            ft.Text(animal_type, size=13, color=ft.Colors.BLACK87, expand=2),
                            ft.Text(location, size=13, color=ft.Colors.BLACK87, expand=3),
                            ft.Text(details_display, size=13, color=ft.Colors.BLACK87, expand=3),
                            ft.Container(make_status_badge(status, admin_message, is_rescue=True,
                                                          removal_reason=removal_reason, archive_note=archive_note), expand=2),
                            ft.Container(rescue_actions, expand=2),
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
                        ft.Text("Actions", size=13, weight="w600", color=ft.Colors.BLACK87, expand=2),
                    ], spacing=15),
                    ft.Divider(height=1, color=ft.Colors.GREY_300),
                    ft.Container(height=10),
                ] + (rescue_rows_content if rescue_rows_content else [
                    create_empty_state(
                        message="No rescue missions yet",
                        padding=20
                    )
                ]),
                spacing=0
            ),
            padding=20,
            bgcolor=ft.Colors.WHITE,
            border_radius=8,
        )

        # Realtime Rescue Mission map with user's ACTIVE missions only
        # Exclude cancelled, archived, and removed items from the map
        active_rescues_for_map = [
            r for r in rescues 
            if not RescueStatus.is_cancelled(r.get("status") or "")
            and not RescueStatus.is_archived(r.get("status") or "")
            and not RescueStatus.is_removed(r.get("status") or "")
        ]
        map_widget = self.map_service.create_map_with_markers(active_rescues_for_map)
        
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
                    self.map_service.create_empty_map_placeholder(len(active_rescues_for_map)),
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

