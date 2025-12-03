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
    create_empty_state, show_snackbar, create_archive_dialog, create_remove_dialog,
    create_scrollable_data_table
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
            sidebar = create_admin_sidebar(page, current_route=page.route)
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

        # Helper to create status badge with popup menu for admin
        def make_status_badge(status: str, request_id: int, is_frozen: bool = False) -> object:
            # Determine color based on status using AdoptionStatus constants
            normalized = AdoptionStatus.normalize(status)
            
            if normalized == AdoptionStatus.APPROVED:
                bg_color = ft.Colors.GREEN_700
                icon = ft.Icons.CHECK_CIRCLE
            elif normalized == AdoptionStatus.DENIED:
                bg_color = ft.Colors.RED_700
                icon = ft.Icons.CANCEL
            else:  # PENDING or default
                bg_color = ft.Colors.ORANGE_700
                icon = ft.Icons.PENDING
            
            if is_frozen:
                # Show locked static badge (animal was removed)
                return ft.Container(
                    ft.Row([
                        ft.Icon(icon, color=ft.Colors.WHITE, size=14),
                        ft.Text(AdoptionStatus.get_label(status), color=ft.Colors.WHITE, size=12, weight="w500"),
                        ft.Icon(ft.Icons.LOCK, color=ft.Colors.WHITE70, size=12),
                    ], spacing=5, alignment=ft.MainAxisAlignment.CENTER),
                    padding=ft.padding.symmetric(horizontal=10, vertical=8),
                    bgcolor=bg_color,
                    border_radius=15,
                    tooltip="Status locked - animal was removed from system",
                )
            
            if is_admin:
                # Admin can change status with custom popup menu
                def change_status(e, new_status):
                    self._on_status_change(page, request_id, new_status)
                
                return ft.Container(
                    ft.PopupMenuButton(
                        content=ft.Row([
                            ft.Icon(icon, color=ft.Colors.WHITE, size=14),
                            ft.Text(AdoptionStatus.get_label(status), color=ft.Colors.WHITE, size=12, weight="w500"),
                            ft.Icon(ft.Icons.ARROW_DROP_DOWN, color=ft.Colors.WHITE, size=16),
                        ], spacing=5, alignment=ft.MainAxisAlignment.CENTER),
                        items=[
                            ft.PopupMenuItem(
                                text=AdoptionStatus.get_label(AdoptionStatus.PENDING),
                                icon=ft.Icons.PENDING,
                                on_click=lambda e: change_status(e, AdoptionStatus.PENDING),
                            ),
                            ft.PopupMenuItem(
                                text=AdoptionStatus.get_label(AdoptionStatus.APPROVED),
                                icon=ft.Icons.CHECK_CIRCLE,
                                on_click=lambda e: change_status(e, AdoptionStatus.APPROVED),
                            ),
                            ft.PopupMenuItem(
                                text=AdoptionStatus.get_label(AdoptionStatus.DENIED),
                                icon=ft.Icons.CANCEL,
                                on_click=lambda e: change_status(e, AdoptionStatus.DENIED),
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
                        ft.Text(AdoptionStatus.get_label(status), color=ft.Colors.WHITE, size=12, weight="w500"),
                    ], spacing=5, alignment=ft.MainAxisAlignment.CENTER),
                    padding=ft.padding.symmetric(horizontal=10, vertical=8),
                    bgcolor=bg_color,
                    border_radius=15,
                )

        # Helper to create admin action buttons (Archive/Remove)
        def make_admin_actions(request_id: int, req_name: str) -> object:
            def handle_archive(e, rid=request_id):
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
            
            def handle_remove(e, rid=request_id):
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
            ], spacing=0, tight=True)

        # Build table rows for DataTable
        table_rows = []
        for req in requests:
            request_id = req.get("id")
            user_name = req.get("user_name", "N/A")
            contact = req.get("contact", "N/A")
            reason = req.get("reason", "N/A")
            status = req.get("status") or "pending"
            
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

            # Check if status changes should be disabled:
            # Only lock if animal was removed (animal_id is NULL or no species from join)
            animal_was_removed = animal_id is None or (animal_id and not req.get("animal_species"))
            is_frozen = animal_was_removed
            
            # Create status badge
            status_widget = make_status_badge(status, request_id, is_frozen)
            
            # Wrap status widget with "Animal Deleted" indicator if needed
            if animal_was_deleted:
                final_status_widget = ft.Column([
                    status_widget,
                    ft.Text("(Animal Deleted)", size=10, color=ft.Colors.GREY_500, italic=True),
                ], spacing=2, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
            else:
                final_status_widget = status_widget

            # Animal name display - grey and italic if deleted
            if animal_was_deleted:
                animal_name_widget = ft.Text(animal_name, size=12, color=ft.Colors.GREY_500, italic=True)
            else:
                animal_name_widget = ft.Text(animal_name, size=12, color=ft.Colors.BLACK87)
            
            # Truncate long reason text for table display
            reason_display = reason[:40] + "..." if len(reason) > 40 else reason

            # Build row data
            row_data = [
                ft.Text(user_name, size=12, color=ft.Colors.BLACK87),
                animal_name_widget,
                ft.Text(contact, size=12, color=ft.Colors.BLACK87),
                ft.Container(
                    ft.Text(reason_display, size=12, color=ft.Colors.BLACK87),
                    tooltip=reason if len(reason) > 40 else None,
                ),
                final_status_widget,
            ]
            
            # Add admin actions column
            if is_admin:
                row_data.append(make_admin_actions(request_id, user_name))

            table_rows.append(row_data)

        # Define table columns with expand values for proper sizing
        table_columns = [
            {"label": "User Name", "expand": 2},
            {"label": "Animal", "expand": 2},
            {"label": "Contact", "expand": 2},
            {"label": "Reason", "expand": 3},
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
            empty_message="No adoption requests found",
            column_spacing=20,
            heading_row_height=45,
            data_row_height=55,
        )

        # Build content items (matching rescue mission list structure)
        content_items = [
            create_page_title("Adoption Requests List"),
            ft.Container(height=20),
            # Adoption Requests Section using create_section_card
            create_section_card(
                title="Adoption Requests",
                content=data_table,
                show_divider=True,
            ),
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

