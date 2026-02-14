"""Page for users to check their application statuses.

Uses state managers for consistent data flow throughout the application.
Uses tabs to switch between Adoption Requests and Rescue Missions.
"""
from __future__ import annotations

import csv
from datetime import datetime
from typing import Optional

import app_config
from app_config import RescueStatus, AdoptionStatus
from services.map_service import MapService
from state import get_app_state
from components import (
    create_user_sidebar, create_gradient_background,
    create_page_title, create_section_card, show_snackbar, create_confirmation_dialog,
    create_scrollable_data_table, create_action_button,
    create_interactive_map,
    show_page_loading, finish_page_loading,
)


class CheckStatusPage:
    """Page for users to check their adoption and rescue mission statuses.
    
    Uses state managers for reactive data management.
    Features tabbed interface with filtering and export capabilities.
    """
    
    def __init__(self, db_path: Optional[str] = None) -> None:
        self._db_path = db_path or app_config.DB_PATH
        self._app_state = get_app_state(self._db_path)
        self.map_service = MapService()
        self._page = None
        self._user_id = None
        
        # Tab state
        self._tab_index = 0
        
        self._adoption_status_filter = "all"
        
        self._rescue_status_filter = "all"
        self._rescue_urgency_filter = "all"

    def build(self, page, user_id: int, tab: int = None) -> None:
        """Build and display the check status page.
        
        Args:
            page: The Flet page instance.
            user_id: The user's ID.
            tab: Initial tab index (0=Rescues, 1=Adoptions). If None, uses current tab state.
        """
        try:
            import flet as ft
        except Exception as exc:
            raise RuntimeError("Flet must be installed to build the UI") from exc

        self._page = page
        self._user_id = user_id
        page.title = "Application Status"
        
        # Only set tab from parameter if explicitly provided (not None)
        if tab is not None and tab in [0, 1]:
            self._tab_index = tab

        user_name = self._app_state.auth.user_name or "User"

        sidebar = create_user_sidebar(page, user_name, current_route=page.route)
        _gradient_ref = show_page_loading(page, sidebar, "Loading statuses...")
        sidebar = create_user_sidebar(page, user_name, current_route=page.route)

        self._app_state.adoptions.load_user_requests(user_id)
        self._app_state.rescues.load_user_missions(user_id)

        # Tab change handler
        def on_tab_change(e):
            self._tab_index = e.control.selected_index
            self.build(page, user_id)

        tabs = ft.Tabs(
            selected_index=self._tab_index,
            animation_duration=300,
            on_change=on_tab_change,
            indicator_color=ft.Colors.TEAL_600,
            label_color=ft.Colors.TEAL_700,
            unselected_label_color=ft.Colors.GREY_600,
            tab_alignment=ft.TabAlignment.START,
            tabs=[
                ft.Tab(
                    text="Rescues",
                    icon=ft.Icons.LOCAL_HOSPITAL_OUTLINED,
                ),
                ft.Tab(
                    text="Adoptions",
                    icon=ft.Icons.VOLUNTEER_ACTIVISM_OUTLINED,
                ),
            ],
        )

        all_adoptions = self._app_state.adoptions.user_requests
        all_rescues = self._app_state.rescues.user_missions

        if self._tab_index == 1:
            # Adoption filters
            filtered_count = len([a for a in all_adoptions
                                 if self._adoption_status_filter == "all" or 
                                 AdoptionStatus.normalize(a.get("status", "")) == self._adoption_status_filter])
            
            filter_controls = ft.Row([
                ft.Dropdown(
                    hint_text="Status",
                    width=140,
                    value=self._adoption_status_filter,
                    options=[
                        ft.dropdown.Option("all", "All Status"),
                        ft.dropdown.Option(AdoptionStatus.PENDING, "Pending"),
                        ft.dropdown.Option(AdoptionStatus.APPROVED, "Approved"),
                        ft.dropdown.Option(AdoptionStatus.DENIED, "Denied"),
                        ft.dropdown.Option(AdoptionStatus.CANCELLED, "Cancelled"),
                    ],
                    border_radius=8,
                    on_change=lambda e: self._on_adoption_filter_change(page, user_id, e.control.value),
                ),
            ], spacing=10)
            
            export_action = lambda e: self._export_adoption_csv(
                [a for a in all_adoptions if self._adoption_status_filter == "all" or 
                 AdoptionStatus.normalize(a.get("status", "")) == self._adoption_status_filter]
            )
            count_text = f"{filtered_count} request(s)"
        else:
            # Rescue filters
            filtered_rescues = all_rescues
            if self._rescue_status_filter != "all":
                filtered_rescues = [r for r in filtered_rescues
                                   if RescueStatus.normalize(r.get("status", "")) == self._rescue_status_filter]
            if self._rescue_urgency_filter != "all":
                filtered_rescues = [r for r in filtered_rescues
                                   if (r.get("urgency") or "medium").lower() == self._rescue_urgency_filter]
            filtered_count = len(filtered_rescues)
            
            filter_controls = ft.Row([
                ft.Dropdown(
                    hint_text="Status",
                    width=140,
                    value=self._rescue_status_filter,
                    options=[
                        ft.dropdown.Option("all", "All Status"),
                        ft.dropdown.Option(RescueStatus.PENDING, "Pending"),
                        ft.dropdown.Option(RescueStatus.ONGOING, "On-going"),
                        ft.dropdown.Option(RescueStatus.RESCUED, "Rescued"),
                        ft.dropdown.Option(RescueStatus.FAILED, "Failed"),
                        ft.dropdown.Option(RescueStatus.CANCELLED, "Cancelled"),
                    ],
                    border_radius=8,
                    on_change=lambda e: self._on_rescue_filter_change(page, user_id, "status", e.control.value),
                ),
                ft.Dropdown(
                    hint_text="Urgency",
                    width=150,
                    value=self._rescue_urgency_filter,
                    options=[
                        ft.dropdown.Option("all", "All Urgency"),
                        ft.dropdown.Option("low", "Low"),
                        ft.dropdown.Option("medium", "Medium"),
                        ft.dropdown.Option("high", "High"),
                    ],
                    border_radius=8,
                    on_change=lambda e: self._on_rescue_filter_change(page, user_id, "urgency", e.control.value),
                ),
            ], spacing=10)
            
            export_action = lambda e: self._export_rescue_csv(filtered_rescues)
            count_text = f"{filtered_count} mission(s)"

        # Unified control bar: Tabs | Filters | Count | Refresh | Export
        control_bar = ft.Container(
            ft.Row([
                # Tabs on the left
                ft.Container(tabs, width=250),
                # Vertical divider
                ft.VerticalDivider(width=1, color=ft.Colors.GREY_300),
                # Spacer
                ft.Container(expand=True),
                filter_controls,
                ft.Text(count_text, size=13, color=ft.Colors.BLACK54),
                # Refresh button
                ft.IconButton(
                    ft.Icons.REFRESH,
                    tooltip="Refresh",
                    icon_color=ft.Colors.TEAL_600,
                    on_click=lambda e: self.build(page, user_id),
                ),
                # Export button
                create_action_button(
                    "Export",
                    on_click=export_action,
                    icon=ft.Icons.DOWNLOAD,
                    width=110,
                ),
            ], spacing=12, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.padding.symmetric(horizontal=5, vertical=5),
            border_radius=10,
        )

        if self._tab_index == 1:
            content = self._build_adoption_requests_content(page, ft, user_id)
        else:
            content = self._build_rescue_missions_content(page, ft, user_id)

        # Main content area
        main_content = ft.Container(
            ft.Column([
                create_page_title("Application Status"),
                ft.Text("Track your adoption requests and rescue mission reports",
                       size=14, color=ft.Colors.BLACK54),
                ft.Container(height=16),
                control_bar,
                ft.Container(height=15),
                content,
            ], spacing=0, scroll=ft.ScrollMode.AUTO, horizontal_alignment="center"),
            padding=30,
            alignment=ft.alignment.top_center,
            expand=True,
        )

        # Main layout
        main_layout = ft.Row([sidebar, main_content], spacing=0, expand=True)

        finish_page_loading(page, _gradient_ref, main_layout)

    def _make_status_badge(self, ft, status: str, admin_message: str = "", is_rescue: bool = False,
                           removal_reason: str = "", archive_note: str = ""):
        """Helper to create status badge with appropriate styling."""
        status_lower = (status or "").lower()
        
        is_cancelled = RescueStatus.is_cancelled(status) if is_rescue else AdoptionStatus.is_cancelled(status)
        
        is_archived = RescueStatus.is_archived(status) if is_rescue else AdoptionStatus.is_archived(status)
        
        is_removed = RescueStatus.is_removed(status) if is_rescue else AdoptionStatus.is_removed(status)
        
        if is_cancelled:
            return ft.Container(
                ft.Row([
                    ft.Icon(ft.Icons.CANCEL, color=ft.Colors.WHITE, size=14),
                    ft.Text("Cancelled", color=ft.Colors.WHITE, size=12, weight="w500"),
                ], spacing=5, alignment=ft.MainAxisAlignment.CENTER),
                padding=ft.padding.symmetric(horizontal=10, vertical=8),
                bgcolor=ft.Colors.GREY_600,
                border_radius=15,
                margin=ft.margin.symmetric(vertical=4),
            )
        elif is_removed:
            reason_text = removal_reason or "Administrative action"
            return ft.Container(
                ft.Row([
                    ft.Icon(ft.Icons.DELETE_OUTLINE, color=ft.Colors.WHITE, size=14),
                    ft.Text("Removed", color=ft.Colors.WHITE, size=12, weight="w500"),
                ], spacing=5, alignment=ft.MainAxisAlignment.CENTER),
                padding=ft.padding.symmetric(horizontal=10, vertical=8),
                bgcolor=ft.Colors.RED_700,
                border_radius=15,
                margin=ft.margin.symmetric(vertical=4),
                tooltip=f"Removed: {reason_text}",
            )
        elif is_archived:
            # For users: DON'T show that it's archived - just show original status normally
            base_status = RescueStatus.get_base_status(status) if is_rescue else AdoptionStatus.get_base_status(status)
            return self._make_status_badge(ft, base_status, admin_message, is_rescue)
        elif is_rescue:
            normalized = RescueStatus.normalize(status)
            if normalized == RescueStatus.RESCUED:
                bg_color = ft.Colors.GREEN_700
                icon = ft.Icons.CHECK_CIRCLE
            elif normalized == RescueStatus.FAILED:
                bg_color = ft.Colors.RED_700
                icon = ft.Icons.CANCEL
            elif normalized == RescueStatus.ONGOING:
                bg_color = ft.Colors.TEAL_600
                icon = ft.Icons.PETS
            elif normalized == RescueStatus.PENDING:
                bg_color = ft.Colors.ORANGE_700
                icon = ft.Icons.PENDING
            else:
                bg_color = ft.Colors.GREY_600
                icon = ft.Icons.HELP_OUTLINE
            
            return ft.Container(
                ft.Row([
                    ft.Icon(icon, color=ft.Colors.WHITE, size=14),
                    ft.Text(RescueStatus.get_label(status), color=ft.Colors.WHITE, size=12, weight="w500"),
                ], spacing=5, alignment=ft.MainAxisAlignment.CENTER),
                padding=ft.padding.symmetric(horizontal=10, vertical=8),
                bgcolor=bg_color,
                border_radius=15,
                margin=ft.margin.symmetric(vertical=4),
            )
        else:
            normalized = AdoptionStatus.normalize(status)
            if normalized == AdoptionStatus.PENDING:
                bg_color = ft.Colors.ORANGE_700
                icon = ft.Icons.PENDING
                text = AdoptionStatus.get_label(AdoptionStatus.PENDING)
            elif normalized == AdoptionStatus.APPROVED:
                bg_color = ft.Colors.GREEN_700
                icon = ft.Icons.CHECK_CIRCLE
                text = AdoptionStatus.get_label(AdoptionStatus.APPROVED)
            elif normalized == AdoptionStatus.DENIED:
                bg_color = ft.Colors.RED_700
                icon = ft.Icons.CANCEL
                text = AdoptionStatus.get_label(AdoptionStatus.DENIED)
            else:
                bg_color = ft.Colors.GREY_600
                icon = ft.Icons.HELP_OUTLINE
                text = status.title()
            
            return ft.Container(
                ft.Row([
                    ft.Icon(icon, color=ft.Colors.WHITE, size=14),
                    ft.Text(text, color=ft.Colors.WHITE, size=12, weight="w500"),
                ], spacing=5, alignment=ft.MainAxisAlignment.CENTER),
                padding=ft.padding.symmetric(horizontal=10, vertical=8),
                bgcolor=bg_color,
                border_radius=15,
                margin=ft.margin.symmetric(vertical=4),
            )

    def _create_urgency_badge(self, ft, urgency: str):
        """Create a color-coded urgency badge."""
        urgency_lower = (urgency or "low").lower()
        colors = {
            "low": ft.Colors.GREEN_700,
            "medium": ft.Colors.ORANGE_700,
            "high": ft.Colors.RED_700,
        }
        return ft.Container(
            content=ft.Text(
                urgency_lower.capitalize(),
                size=11,
                weight=ft.FontWeight.W_500,
                color=ft.Colors.WHITE,
            ),
            bgcolor=colors.get(urgency_lower, ft.Colors.GREY_600),
            padding=ft.padding.symmetric(horizontal=8, vertical=2),
            border_radius=4,
        )

    def _build_adoption_requests_content(self, page, ft, user_id: int):
        """Build the adoption requests tab content."""
        
        all_adoptions = self._app_state.adoptions.user_requests
        
        if self._adoption_status_filter == "all":
            adoptions = all_adoptions
        else:
            adoptions = [a for a in all_adoptions
                        if AdoptionStatus.normalize(a.get("status", "")) == self._adoption_status_filter]

        # Helper function to handle edit button click
        def on_edit_click(request_id: int, animal_id: int):
            def handler(e):
                page.go(f"/adoption_form?animal_id={animal_id}&edit_request_id={request_id}")
            return handler

        # Helper function to handle cancel button click
        def on_cancel_click(request_id: int, animal_name: str, animal_breed: str):
            def handler(e):
                def on_confirm():
                    try:
                        from services.adoption_service import AdoptionService
                        adoption_service = AdoptionService(self._db_path)
                        cancelled = adoption_service.cancel_request(request_id)
                        if cancelled:
                            show_snackbar(page, f"Adoption request for '{animal_name}' has been cancelled")
                            self.build(page, user_id)
                        else:
                            show_snackbar(page, "Failed to cancel request (may not be pending)", error=True)
                    except Exception as exc:
                        show_snackbar(page, f"Error: {exc}", error=True)
                
                animal_label = animal_name
                if animal_breed:
                    animal_label = f"{animal_name} ({animal_breed})"
                create_confirmation_dialog(
                    page,
                    title="Cancel Adoption Request",
                    message=f"Are you sure you want to cancel your adoption request for '{animal_label}'?",
                    on_confirm=on_confirm,
                    confirm_text="Cancel Request",
                    cancel_text="Keep Request",
                )
            return handler

        adoption_rows = []
        for a in adoptions:
            animal_id = a.get("animal_id")
            request_id = a.get("id")
            stored_animal_name = a.get("animal_name")
            stored_animal_species = a.get("animal_species")
            
            animal_was_deleted = False
            animal_breed = (a.get("animal_breed") or "")
            if animal_id and animal_id > 0:
                animal = self._app_state.animals.get_animal_by_id(animal_id)
                if animal:
                    animal_name = animal.get("name", "Unknown")
                    animal_type = animal.get("species", "Unknown")
                    animal_breed = (animal.get("breed") or animal_breed or "").strip()
                else:
                    animal_name = stored_animal_name or "Unknown"
                    animal_type = stored_animal_species or "-"
                    animal_was_deleted = True
            else:
                animal_name = stored_animal_name or "Unknown"
                animal_type = stored_animal_species or "-"
                animal_was_deleted = True
            animal_breed = animal_breed.strip()
            
            status = a.get("status", "pending")
            status_lower = (status or "").lower()
            removal_reason = a.get("removal_reason", "")
            archive_note = a.get("archive_note", "")
            admin_message = a.get("admin_message", "")
            
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
                        on_click=on_cancel_click(request_id, animal_name, animal_breed),
                    ),
                ], spacing=5)
            else:
                actions = ft.Container()
            
            if animal_was_deleted:
                animal_name_display = ft.Text(animal_name, size=12, color=ft.Colors.GREY_500, italic=True)
            else:
                animal_name_display = ft.Text(animal_name, size=12, color=ft.Colors.BLACK87)
            
            if animal_was_deleted:
                status_display = ft.Container(
                    ft.Column([
                        self._make_status_badge(ft, status, admin_message, is_rescue=False,
                                               removal_reason=removal_reason, archive_note=archive_note),
                        ft.Text("(Animal Deleted)", size=10, color=ft.Colors.GREY_500, italic=True),
                    ], spacing=2, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                )
            else:
                status_display = self._make_status_badge(ft, status, admin_message, is_rescue=False,
                                                        removal_reason=removal_reason, archive_note=archive_note)
            
            reason = a.get("reason", "")
            reason_display = reason[:30] + "..." if len(reason) > 30 else reason
            
            breed = animal_breed or "Not Specified"
            breed_display = breed[:15] + "..." if len(breed) > 15 else breed
            
            adoption_rows.append([
                animal_name_display,
                ft.Text(animal_type, size=12, color=ft.Colors.GREY_500 if animal_was_deleted else ft.Colors.BLACK87),
                ft.Container(
                    ft.Text(breed_display, size=12, color=ft.Colors.GREY_500 if animal_was_deleted else ft.Colors.BLACK87),
                    tooltip=breed if len(breed) > 15 else None,
                ),
                ft.Container(
                    ft.Text(reason_display, size=12, color=ft.Colors.BLACK87),
                    tooltip=reason if len(reason) > 30 else None,
                ),
                status_display,
                actions,
            ])

        adoption_columns = [
            {"label": "Animal Name", "expand": 2},
            {"label": "Type", "expand": 1},
            {"label": "Breed", "expand": 2},
            {"label": "Reason", "expand": 3},
            {"label": "Status", "expand": 2},
            {"label": "Actions", "expand": 2},
        ]

        adoption_table = create_scrollable_data_table(
            columns=adoption_columns,
            rows=adoption_rows,
            height=400,
            empty_message="No adoption requests yet",
            column_spacing=20,
            heading_row_height=45,
            data_row_height=55,
        )

        return ft.Column([
            create_section_card(title="Your Adoption Requests", content=adoption_table, show_divider=True),
        ], spacing=0)

    def _build_rescue_missions_content(self, page, ft, user_id: int):
        """Build the rescue missions tab content with map."""
        
        all_rescues = self._app_state.rescues.user_missions
        
        if self._rescue_status_filter == "all":
            rescues = all_rescues
        else:
            rescues = [r for r in all_rescues
                      if RescueStatus.normalize(r.get("status", "")) == self._rescue_status_filter]
        
        if self._rescue_urgency_filter != "all":
            rescues = [r for r in rescues
                      if (r.get("urgency") or "medium").lower() == self._rescue_urgency_filter]

        # Helper for cancel rescue mission click
        def on_cancel_rescue_click(mission_id: int, animal_type: str, location: str):
            def handler(e):
                from services.rescue_service import RescueService
                
                def on_confirm():
                    rescue_service = RescueService(self._db_path)
                    success = rescue_service.cancel_mission(mission_id, user_id)
                    if success:
                        show_snackbar(page, "Rescue mission cancelled successfully")
                        self.build(page, user_id)
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

        rescue_rows = []
        for r in rescues:
            mission_id = r.get("id")
            animal_type = r.get("animal_type") or "Unknown"
            breed = r.get("breed") or "Not Specified"
            breed_display = breed[:15] + "..." if len(breed) > 15 else breed
            location = r.get("location") or "Unknown"
            details = r.get("notes", "")
            details_display = details[:25] + "..." if len(details) > 25 else details
            
            status = r.get("status", "pending")
            admin_message = r.get("admin_message", "")
            removal_reason = r.get("removal_reason", "")
            archive_note = r.get("archive_note", "")
            status_lower = (status or "").lower()
            
            if status_lower == "pending":
                rescue_actions = ft.Row([
                    ft.TextButton(
                        "Cancel",
                        icon=ft.Icons.CANCEL,
                        icon_color=ft.Colors.RED_600,
                        style=ft.ButtonStyle(color=ft.Colors.RED_600),
                        on_click=on_cancel_rescue_click(mission_id, animal_type, location),
                    ),
                ], spacing=5, tight=True)
            else:
                rescue_actions = ft.Container()
            
            rescue_rows.append([
                ft.Text(animal_type, size=12, color=ft.Colors.BLACK87),
                ft.Container(
                    ft.Text(breed_display, size=12, color=ft.Colors.BLACK87),
                    tooltip=breed if len(breed) > 15 else None,
                ),
                ft.Container(
                    ft.Text(location[:20] + "..." if len(location) > 20 else location, size=12, color=ft.Colors.BLACK87),
                    tooltip=location if len(location) > 20 else None,
                ),
                self._create_urgency_badge(ft, r.get("urgency")),
                ft.Container(
                    ft.Text(details_display, size=12, color=ft.Colors.BLACK87),
                    tooltip=details if len(details) > 25 else None,
                ),
                self._make_status_badge(ft, status, admin_message, is_rescue=True,
                                       removal_reason=removal_reason, archive_note=archive_note),
                rescue_actions,
            ])

        rescue_columns = [
            {"label": "Type", "expand": 1},
            {"label": "Breed", "expand": 1},
            {"label": "Location", "expand": 2},
            {"label": "Urgency", "expand": 1},
            {"label": "Details", "expand": 2},
            {"label": "Status", "expand": 2},
            {"label": "Actions", "expand": 2},
        ]

        rescue_table = create_scrollable_data_table(
            columns=rescue_columns,
            rows=rescue_rows,
            height=350,
            empty_message="No rescue missions yet",
            column_spacing=15,
            heading_row_height=45,
            data_row_height=55,
        )

        # Rescue Mission Map
        rescues_for_map = [
            r for r in rescues
            if not RescueStatus.is_cancelled(r.get("status") or "")
            and not RescueStatus.is_removed(r.get("status") or "")
        ]
        is_online = self.map_service.check_map_tiles_available()
        
        if is_online:
            map_container = create_interactive_map(
                map_service=self.map_service,
                missions=rescues_for_map,
                page=self._page,
                is_admin=False,
                height=400,
                title="Your Rescue Mission Locations",
                show_legend=True,
                initially_locked=True,
            )
        else:
            offline_widget = self.map_service.create_offline_map_fallback(rescues_for_map, is_admin=False)
            if offline_widget:
                map_container = ft.Container(
                    ft.Column([
                        ft.Text("Your Rescue Mission Locations", size=16, weight="w600", color=ft.Colors.BLACK87),
                        ft.Container(height=15),
                        ft.Container(
                            offline_widget,
                            height=400,
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
                map_container = ft.Container(
                    ft.Column([
                        ft.Text("Your Rescue Mission Locations", size=16, weight="w600", color=ft.Colors.BLACK87),
                        ft.Container(height=15),
                        self.map_service.create_empty_map_placeholder(len(rescues_for_map)),
                    ], spacing=0),
                    padding=20,
                    bgcolor=ft.Colors.WHITE,
                    border_radius=12,
                    shadow=ft.BoxShadow(blur_radius=8, spread_radius=1, color=ft.Colors.BLACK12, offset=(0, 2)),
                )

        return ft.Column([
            create_section_card(title="Your Rescue Missions", content=rescue_table, show_divider=True),
            ft.Container(height=20),
            map_container,
        ], spacing=0)

    def _on_adoption_filter_change(self, page, user_id: int, value: str) -> None:
        """Handle adoption filter changes."""
        self._adoption_status_filter = value
        self.build(page, user_id)

    def _on_rescue_filter_change(self, page, user_id: int, filter_type: str, value: str) -> None:
        """Handle rescue mission filter changes."""
        if filter_type == "status":
            self._rescue_status_filter = value
        elif filter_type == "urgency":
            self._rescue_urgency_filter = value
        self.build(page, user_id)

    def _export_adoption_csv(self, adoptions: list) -> None:
        """Export user's adoption requests to CSV."""
        if not adoptions:
            show_snackbar(self._page, "No requests to export", error=True)
            return
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"my_adoption_requests_{timestamp}.csv"
            filepath = app_config.STORAGE_DIR / "data" / "exports" / filename
            filepath.parent.mkdir(parents=True, exist_ok=True)
            
            fieldnames = ["request_id", "animal_name", "animal_species", "contact", "reason", 
                          "status", "my_notes", "admin_response", "submitted_date", "last_updated"]
            with open(filepath, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for a in adoptions:
                    animal_id = a.get("animal_id")
                    animal_name = a.get("animal_name") or "Unknown"
                    animal_type = a.get("animal_species") or "Unknown"
                    if animal_id and animal_id > 0:
                        animal = self._app_state.animals.get_animal_by_id(animal_id)
                        if animal:
                            animal_name = animal.get("name", animal_name)
                            animal_type = animal.get("species", animal_type)
                    
                    writer.writerow({
                        "request_id": a.get("id", ""),
                        "animal_name": animal_name,
                        "animal_species": animal_type,
                        "contact": a.get("contact", ""),
                        "reason": a.get("reason", ""),
                        "status": AdoptionStatus.get_label(a.get("status", "")),
                        "my_notes": a.get("notes", ""),
                        "admin_response": a.get("admin_message", ""),
                        "submitted_date": a.get("request_date", ""),
                        "last_updated": a.get("updated_at", ""),
                    })
            
            show_snackbar(self._page, f"Exported {len(adoptions)} request(s) to {filename}")
        except Exception as e:
            show_snackbar(self._page, f"Export failed: {e}", error=True)

    def _export_rescue_csv(self, rescues: list) -> None:
        """Export user's rescue missions to CSV."""
        if not rescues:
            show_snackbar(self._page, "No missions to export", error=True)
            return
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"my_rescue_missions_{timestamp}.csv"
            filepath = app_config.STORAGE_DIR / "data" / "exports" / filename
            filepath.parent.mkdir(parents=True, exist_ok=True)
            
            fieldnames = ["mission_id", "animal_type", "animal_name", "breed", "location", "latitude", "longitude", 
                          "urgency", "status", "my_notes", "reporter_name", "reporter_phone", "admin_response", 
                          "reported_date", "last_updated"]
            with open(filepath, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for r in rescues:
                    writer.writerow({
                        "mission_id": r.get("id", ""),
                        "animal_type": r.get("animal_type", ""),
                        "animal_name": r.get("animal_name", ""),
                        "breed": r.get("breed", ""),
                        "location": r.get("location", ""),
                        "latitude": r.get("latitude", ""),
                        "longitude": r.get("longitude", ""),
                        "urgency": r.get("urgency", ""),
                        "status": RescueStatus.get_label(r.get("status", "")),
                        "my_notes": r.get("notes", ""),
                        "reporter_name": r.get("reporter_name", ""),
                        "reporter_phone": r.get("reporter_phone", ""),
                        "admin_response": r.get("admin_message", ""),
                        "reported_date": r.get("mission_date", ""),
                        "last_updated": r.get("updated_at", ""),
                    })
            
            show_snackbar(self._page, f"Exported {len(rescues)} mission(s) to {filename}")
        except Exception as e:
            show_snackbar(self._page, f"Export failed: {e}", error=True)

    def _refresh_data(self, page, user_id: int) -> None:
        """Refresh the page by rebuilding with latest data."""
        self.build(page, user_id)


__all__ = ["CheckStatusPage"]

