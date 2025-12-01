"""Admin page for managing adoption requests.

Uses AdoptionState for state-driven data flow, ensuring consistency
with the application's state management pattern.
"""
from __future__ import annotations
from typing import Optional

import app_config
from app_config import AdoptionStatus
from state import get_app_state
from services.adoption_service import AdoptionService
from components import (
    create_admin_sidebar, create_adoption_status_dropdown, create_status_badge, 
    create_gradient_background, create_page_title, create_section_card, 
    create_empty_state, show_snackbar, create_archive_dialog, create_remove_dialog
)


class AdoptionRequestListPage:
    """Admin page for viewing and managing adoption requests.
    
    Uses AdoptionState for reactive data management.
    """
    
    def __init__(self, db_path: Optional[str] = None) -> None:
        self._db_path = db_path or app_config.DB_PATH
        self._app_state = get_app_state(self._db_path)

    def build(self, page, user_role: str = "admin") -> None:
        try:
            import flet as ft
        except Exception as exc:
            raise RuntimeError("Flet must be installed to build the UI") from exc

        page.title = "Adoption Requests"

        is_admin = user_role == "admin"

        # Sidebar (for admin only)
        if is_admin:
            sidebar = create_admin_sidebar(page)
        else:
            sidebar = None

        # Load adoption requests through state manager (active only for admin)
        if is_admin:
            self._app_state.adoptions.load_active_requests()
        else:
            self._app_state.adoptions.load_requests()
        requests = self._app_state.adoptions.requests
        
        # Filter out user-cancelled requests from admin view (already excluded archived/removed)
        if is_admin:
            requests = [r for r in requests 
                       if not AdoptionStatus.is_cancelled(r.get("status") or "")]

        # Build table rows
        table_rows = []
        for req in requests:
            request_id = req.get("id")
            user_name = req.get("user_name", "N/A")
            contact = req.get("contact", "N/A")
            reason = req.get("reason", "N/A")
            status = (req.get("status") or "pending").capitalize()
            
            # Handle animal name - the query uses COALESCE to prefer joined name, fallback to stored name
            animal_id = req.get("animal_id")
            animal_name = req.get("animal_name")
            animal_was_deleted = False
            
            # Check if animal was deleted (animal_id is NULL or no species from join)
            if animal_id is None or (animal_id and not req.get("animal_species")):
                animal_name = animal_name or "Unknown Animal"
                animal_was_deleted = True
            elif not animal_name:
                animal_name = "N/A"

            # Status dropdown for admin
            if is_admin:
                # Determine status color using AdoptionStatus constants
                normalized = AdoptionStatus.normalize(status)
                if normalized == AdoptionStatus.APPROVED:
                    dropdown_color = ft.Colors.GREEN_600
                elif normalized == AdoptionStatus.DENIED:
                    dropdown_color = ft.Colors.RED_600
                else:
                    dropdown_color = ft.Colors.ORANGE_600
                
                # Check if status changes should be disabled:
                # Only lock if animal was removed (animal_id is NULL or no species from join)
                # Approved status is NOT locked - admin can still change it
                animal_was_removed = animal_id is None or (animal_id and not req.get("animal_species"))
                is_frozen = animal_was_removed
                
                if is_frozen:
                    # Show static badge instead of dropdown (status locked because animal removed)
                    status_widget = ft.Container(
                        ft.Row([
                            ft.Icon(
                                ft.Icons.CHECK_CIRCLE if status.lower() == "approved" else 
                                ft.Icons.CANCEL if status.lower() == "denied" else ft.Icons.PENDING,
                                size=14, color=ft.Colors.WHITE
                            ),
                            ft.Text(status, size=12, color=ft.Colors.WHITE, weight="w500"),
                            ft.Icon(ft.Icons.LOCK, size=12, color=ft.Colors.WHITE70),
                        ], spacing=5, alignment="center", tight=True),
                        bgcolor=dropdown_color,
                        padding=ft.padding.symmetric(horizontal=12, vertical=8),
                        border_radius=20,
                        tooltip="Status locked - animal was removed from system",
                    )
                else:
                    status_dropdown = ft.Dropdown(
                        value=status,
                        options=[
                            ft.dropdown.Option(AdoptionStatus.get_label(AdoptionStatus.PENDING)),
                            ft.dropdown.Option(AdoptionStatus.get_label(AdoptionStatus.APPROVED)),
                            ft.dropdown.Option(AdoptionStatus.get_label(AdoptionStatus.DENIED))
                        ],
                        on_change=lambda e, rid=request_id: self._on_status_change(page, rid, e.control.value),
                        width=140,
                        bgcolor=dropdown_color,
                        border_color=dropdown_color,
                        text_style=ft.TextStyle(color=ft.Colors.WHITE, size=12, weight="w500"),
                        color=ft.Colors.WHITE,
                        filled=True,
                        content_padding=10,
                    )
                    status_widget = status_dropdown
            else:
                # For non-admin, show static chip
                normalized = AdoptionStatus.normalize(status)
                if normalized == AdoptionStatus.APPROVED:
                    status_widget = ft.Container(
                        ft.Row([
                            ft.Icon(ft.Icons.CHECK_CIRCLE, size=16, color=ft.Colors.WHITE),
                            ft.Text(status, size=12, color=ft.Colors.WHITE, weight="w500"),
                        ], spacing=5, alignment="center"),
                        bgcolor=ft.Colors.GREEN_600,
                        padding=ft.padding.symmetric(horizontal=15, vertical=8),
                        border_radius=20,
                    )
                elif normalized == AdoptionStatus.DENIED:
                    status_widget = ft.Container(
                        ft.Row([
                            ft.Icon(ft.Icons.CANCEL, size=16, color=ft.Colors.WHITE),
                            ft.Text(AdoptionStatus.get_label(AdoptionStatus.DENIED), size=12, color=ft.Colors.WHITE, weight="w500"),
                        ], spacing=5, alignment="center"),
                        bgcolor=ft.Colors.RED_600,
                        padding=ft.padding.symmetric(horizontal=15, vertical=8),
                        border_radius=20,
                    )
                else:
                    status_widget = ft.Container(
                        ft.Row([
                            ft.Icon(ft.Icons.PENDING, size=16, color=ft.Colors.WHITE),
                            ft.Text(AdoptionStatus.get_label(AdoptionStatus.PENDING), size=12, color=ft.Colors.WHITE, weight="w500"),
                        ], spacing=5, alignment="center"),
                        bgcolor=ft.Colors.ORANGE_600,
                        padding=ft.padding.symmetric(horizontal=15, vertical=8),
                        border_radius=20,
                    )

            # Build row controls
            # Animal name display - grey and italic if deleted
            if animal_was_deleted:
                animal_name_widget = ft.Text(animal_name, size=14, color=ft.Colors.GREY_500, italic=True)
            else:
                animal_name_widget = ft.Text(animal_name, size=14, color=ft.Colors.BLACK87)
            
            # Wrap status widget with "Animal Deleted" indicator if needed
            if animal_was_deleted:
                final_status_widget = ft.Column([
                    status_widget,
                    ft.Text("(Animal Deleted)", size=10, color=ft.Colors.GREY_500, italic=True),
                ], spacing=2, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
            else:
                final_status_widget = status_widget
            
            row_controls = [
                ft.Container(ft.Text(user_name, size=14, color=ft.Colors.BLACK87), width=120),
                ft.Container(animal_name_widget, width=120),
                ft.Container(ft.Text(contact, size=14, color=ft.Colors.BLACK87), width=180),
                ft.Container(ft.Text(reason, size=14, color=ft.Colors.BLACK87), width=200),
                ft.Container(final_status_widget, width=150, alignment=ft.alignment.center),
            ]
            
            # Add admin action buttons (Archive/Remove)
            if is_admin:
                def make_admin_actions(rid, req_name):
                    def handle_archive(e):
                        def on_confirm(note):
                            success = self._app_state.adoptions.archive_request(
                                rid,
                                self._app_state.auth.user_id,
                                note
                            )
                            if success:
                                show_snackbar(page, "Request archived")
                                self.build(page, user_role="admin")
                            else:
                                show_snackbar(page, "Failed to archive request", error=True)
                        
                        create_archive_dialog(
                            page,
                            item_type="adoption request",
                            item_name=f"#{rid}",
                            on_confirm=on_confirm,
                        )
                    
                    def handle_remove(e):
                        def on_confirm(reason):
                            success = self._app_state.adoptions.remove_request(
                                rid,
                                self._app_state.auth.user_id,
                                reason
                            )
                            if success:
                                show_snackbar(page, "Request removed")
                                self.build(page, user_role="admin")
                            else:
                                show_snackbar(page, "Failed to remove request", error=True)
                        
                        create_remove_dialog(
                            page,
                            item_type="adoption request",
                            item_name=f"#{rid}",
                            on_confirm=on_confirm,
                        )
                    
                    return ft.Row([
                        ft.IconButton(
                            icon=ft.Icons.ARCHIVE_OUTLINED,
                            icon_color=ft.Colors.AMBER_700,
                            icon_size=18,
                            tooltip="Archive",
                            on_click=handle_archive,
                        ),
                        ft.IconButton(
                            icon=ft.Icons.DELETE_OUTLINE,
                            icon_color=ft.Colors.RED_600,
                            icon_size=18,
                            tooltip="Remove",
                            on_click=handle_remove,
                        ),
                    ], spacing=0, tight=True)
                
                row_controls.append(ft.Container(make_admin_actions(request_id, user_name), width=90, alignment=ft.alignment.center))

            # Table row
            row = ft.Container(
                ft.Row(row_controls, spacing=20),
                padding=15,
                border=ft.border.only(bottom=ft.BorderSide(1, ft.Colors.GREY_200)),
            )
            table_rows.append(row)

        # Table header
        header_controls = [
            ft.Container(ft.Text("User Name", size=14, weight="bold", color=ft.Colors.BLACK87), width=120),
            ft.Container(ft.Text("Animal Name", size=14, weight="bold", color=ft.Colors.BLACK87), width=120),
            ft.Container(ft.Text("Contact Info", size=14, weight="bold", color=ft.Colors.BLACK87), width=180),
            ft.Container(ft.Text("Reason", size=14, weight="bold", color=ft.Colors.BLACK87), width=200),
            ft.Container(ft.Text("Status", size=14, weight="bold", color=ft.Colors.BLACK87), width=150, alignment=ft.alignment.center),
        ]
        
        # Add Actions header for admin
        if is_admin:
            header_controls.append(ft.Container(ft.Text("Actions", size=14, weight="bold", color=ft.Colors.BLACK87), width=90, alignment=ft.alignment.center))

        table_header = ft.Container(
            ft.Row(header_controls, spacing=20),
            padding=15,
            bgcolor=ft.Colors.GREY_100,
            border=ft.border.only(bottom=ft.BorderSide(2, ft.Colors.GREY_300)),
        )

        # Table container
        table_container = ft.Container(
            ft.Column([
                ft.Text("Adoption Request List", size=18, weight="w600", color=ft.Colors.BLACK87),
                ft.Divider(height=15, color=ft.Colors.GREY_300),
                table_header,
                ft.Column(table_rows if table_rows else [
                    create_empty_state(
                        message="No adoption requests found",
                        padding=40
                    )
                ], spacing=0, scroll=ft.ScrollMode.AUTO),
            ], spacing=10),
            padding=20,
            bgcolor=ft.Colors.WHITE,
            border_radius=12,
            shadow=ft.BoxShadow(blur_radius=8, spread_radius=1, color=ft.Colors.BLACK12, offset=(0, 2)),
        )

        # Main content area
        main_content = ft.Container(
            ft.Column([
                create_page_title("Adoption Requests List"),
                ft.Container(height=15),
                table_container,
            ], spacing=0, scroll=ft.ScrollMode.AUTO),
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

    def _on_status_change(self, page, request_id: int, new_status: str) -> None:
        """Update adoption request status using state manager."""
        try:
            updated = self._app_state.adoptions.update_request_status(request_id, new_status)

            if updated:
                show_snackbar(page, f"Status updated to {new_status}")
                # Refresh page
                self.build(page, user_role="admin")
            else:
                show_snackbar(page, "Failed to update status", error=True)
        except Exception as exc:
            show_snackbar(page, f"Error: {exc}", error=True)

