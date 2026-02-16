"""Combined admin page for managing Rescue Missions, Adoption Requests, and Hidden Items.

Uses tabs to switch between different record types.
"""
from __future__ import annotations

import csv
from datetime import datetime
from typing import Optional

import app_config
from app_config import RescueStatus, AdoptionStatus, AnimalStatus
from state import get_app_state
from services.map_service import MapService


class ManageRecordsPage:
    """Admin page with tabs for managing rescue missions, adoption requests, and hidden items."""
    
    def __init__(self, db_path: Optional[str] = None) -> None:
        self._db_path = db_path or app_config.DB_PATH
        self._app_state = get_app_state(self._db_path)
        self.map_service = MapService()
        self._page = None
        
        # Tab state
        self._tab_index = 0
        self._hidden_tab_index = 0  # Sub-tab for hidden items
        
        self._rescue_status_filter = "all"
        self._rescue_urgency_filter = "all"
        
        self._adoption_status_filter = "all"
    
    def build(self, page, tab: int = None) -> None:
        """Build and display the manage records page.
        
        Args:
            page: The Flet page instance.
            tab: Initial tab index (0=Rescues, 1=Adoptions, 2=Hidden). If None, uses current tab state.
        """
        try:
            import flet as ft
        except Exception as exc:
            raise RuntimeError("Flet must be installed to build the UI") from exc
        
        from components import (
            create_admin_sidebar, create_gradient_background,
            create_page_title, create_section_card, show_snackbar,
            create_archive_dialog, create_remove_dialog,
            create_scrollable_data_table, create_empty_state,
            create_restore_dialog, create_permanent_delete_dialog,
            create_interactive_map,
            show_page_loading, finish_page_loading,
            is_mobile, create_responsive_layout, responsive_padding,
            create_admin_drawer,
        )
        
        self._page = page
        page.title = "Manage Records - PawRes Admin"
        
        # Only set tab from parameter if explicitly provided (not None)
        if tab is not None and tab in [0, 1, 2]:
            self._tab_index = tab
        
        # Auth check
        if not self._app_state.auth.is_authenticated or self._app_state.auth.user_role != "admin":
            page.go("/login")
            return
        
        _mobile = is_mobile(page)
        sidebar = create_admin_sidebar(page, current_route=page.route)
        drawer = create_admin_drawer(page, current_route=page.route) if _mobile else None
        _gradient_ref = show_page_loading(page, None if _mobile else sidebar, "Loading records...")
        sidebar = create_admin_sidebar(page, current_route=page.route)
        
        # Tab change handler
        def on_tab_change(e):
            self._tab_index = e.control.selected_index
            self.build(page)
        
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
                ft.Tab(
                    text="Hidden",
                    icon=ft.Icons.VISIBILITY_OFF_OUTLINED,
                ),
            ],
        )
        
        # Import create_action_button for export
        from components import create_action_button
        
        if self._tab_index == 0:
            # Rescue Missions tab
            self._app_state.rescues.load_active_missions()
            all_missions = self._app_state.rescues.missions
            
            filtered_missions = all_missions
            if self._rescue_status_filter != "all":
                filtered_missions = [m for m in filtered_missions 
                                    if RescueStatus.normalize(m.get("status", "")) == self._rescue_status_filter]
            if self._rescue_urgency_filter != "all":
                filtered_missions = [m for m in filtered_missions 
                                    if (m.get("urgency") or "medium").lower() == self._rescue_urgency_filter]
            
            filter_controls = ft.Row([
                ft.Dropdown(
                    hint_text="Status",
                    width=130 if _mobile else 140,
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
                    on_change=lambda e: self._on_rescue_filter_change(page, "status", e.control.value),
                ),
                ft.Dropdown(
                    hint_text="Urgency",
                    width=140 if _mobile else 160,
                    value=self._rescue_urgency_filter,
                    options=[
                        ft.dropdown.Option("all", "All Urgency"),
                        ft.dropdown.Option("low", "Low"),
                        ft.dropdown.Option("medium", "Medium"),
                        ft.dropdown.Option("high", "High"),
                    ],
                    border_radius=8,
                    on_change=lambda e: self._on_rescue_filter_change(page, "urgency", e.control.value),
                ),
            ], spacing=10, wrap=_mobile, run_spacing=8)
            
            count_text = f"{len(filtered_missions)} mission(s)"
            export_action = lambda e: self._export_rescue_csv(filtered_missions)
            show_export = True
            
        elif self._tab_index == 1:
            # Adoption Requests tab
            self._app_state.adoptions.load_active_requests()
            all_requests = self._app_state.adoptions.requests
            
            if self._adoption_status_filter == "all":
                filtered_requests = all_requests
            else:
                filtered_requests = [r for r in all_requests 
                                    if AdoptionStatus.normalize(r.get("status", "")) == self._adoption_status_filter]
            
            filter_controls = ft.Row([
                ft.Dropdown(
                    hint_text="Status",
                    width=130 if _mobile else 140,
                    value=self._adoption_status_filter,
                    options=[
                        ft.dropdown.Option("all", "All Status"),
                        ft.dropdown.Option(AdoptionStatus.PENDING, "Pending"),
                        ft.dropdown.Option(AdoptionStatus.APPROVED, "Approved"),
                        ft.dropdown.Option(AdoptionStatus.DENIED, "Denied"),
                        ft.dropdown.Option(AdoptionStatus.CANCELLED, "Cancelled"),
                    ],
                    border_radius=8,
                    on_change=lambda e: self._on_adoption_filter_change(page, e.control.value),
                ),
            ], spacing=10, wrap=_mobile, run_spacing=8)
            
            count_text = f"{len(filtered_requests)} request(s)"
            export_action = lambda e: self._export_adoption_csv(filtered_requests)
            show_export = True
            
        else:
            # Hidden Items tab - no filters needed
            filter_controls = ft.Container()
            count_text = ""
            export_action = None
            show_export = False
        
        right_controls = []

        if count_text:
            right_controls.append(ft.Text(count_text, size=13, color=ft.Colors.BLACK54))
        right_controls.append(
            ft.IconButton(
                ft.Icons.REFRESH,
                tooltip="Refresh",
                icon_color=ft.Colors.TEAL_600,
                on_click=lambda e: self.build(page),
            )
        )
        if show_export:
            right_controls.append(
                create_action_button(
                    "Export",
                    on_click=export_action,
                    icon=ft.Icons.DOWNLOAD,
                    width=110,
                )
            )
        
        # Unified control bar: Tabs | Filters | Count | Refresh | Export
        control_bar = ft.Container(
            ft.Column([
                ft.Container(tabs, width=None if _mobile else 280),
                ft.Row([
                    filter_controls,
                    *right_controls,
                ],
                    spacing=12,
                    wrap=True,
                    run_spacing=8,
                    alignment=ft.MainAxisAlignment.END if _mobile else ft.MainAxisAlignment.START,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            ], spacing=8),
            padding=ft.padding.symmetric(horizontal=5, vertical=5),
            border_radius=10,
        )
        
        if self._tab_index == 0:
            content = self._build_rescue_missions_content(page, ft, show_snackbar, create_section_card, 
                                                          create_scrollable_data_table, create_archive_dialog, 
                                                          create_remove_dialog, create_interactive_map)
        elif self._tab_index == 1:
            content = self._build_adoption_requests_content(page, ft, show_snackbar, create_section_card,
                                                            create_scrollable_data_table, create_archive_dialog,
                                                            create_remove_dialog)
        else:
            content = self._build_hidden_items_content(page, ft, show_snackbar, create_empty_state,
                                                        create_restore_dialog, create_permanent_delete_dialog)
        
        # Main content area
        main_content = ft.Container(
            ft.Column([
                create_page_title("Manage Records"),
                ft.Text("View and manage rescue missions, adoption requests, and hidden items", 
                       size=14, color=ft.Colors.BLACK54),
                ft.Container(height=16),
                control_bar,
                ft.Container(height=15),
                content,
            ], spacing=0, scroll=ft.ScrollMode.AUTO, horizontal_alignment="center"),
            padding=responsive_padding(page),
            alignment=ft.alignment.top_center,
            expand=True,
        )
        
        # Main layout
        main_layout = create_responsive_layout(page, sidebar, main_content, drawer, title="Manage Records")
        
        finish_page_loading(page, _gradient_ref, main_layout)
    
    def _switch_to_tab(self, page, tab_index: int) -> None:
        """Switch to a specific tab and rebuild the page."""
        self._tab_index = tab_index
        self.build(page)
    
    def _build_rescue_missions_content(self, page, ft, show_snackbar, create_section_card,
                                        create_scrollable_data_table, create_archive_dialog,
                                        create_remove_dialog, create_interactive_map):
        """Build the rescue missions tab content."""
        
        all_missions = self._app_state.rescues.missions
        
        if self._rescue_status_filter == "all":
            missions = all_missions
        else:
            missions = [m for m in all_missions 
                       if RescueStatus.normalize(m.get("status", "")) == self._rescue_status_filter]
        
        if self._rescue_urgency_filter != "all":
            missions = [m for m in missions 
                       if (m.get("urgency") or "medium").lower() == self._rescue_urgency_filter]
        
        # Helper to create status badge
        def make_status_badge(status: str, mission_id: int):
            normalized = RescueStatus.normalize(status)
            
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
            else:
                bg_color = ft.Colors.ORANGE_700
                icon = ft.Icons.PENDING
            
            def change_status(e, new_status):
                self._on_rescue_status_change(page, mission_id, new_status, show_snackbar)
            
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
        
        # Helper to create admin action buttons
        def make_admin_actions(mission_id: int, mission_name: str):
            def handle_archive(e, mid=mission_id):
                def on_confirm(note):
                    success = self._app_state.rescues.archive_mission(
                        mid, self._app_state.auth.user_id, note)
                    if success:
                        show_snackbar(page, "Mission archived")
                        self.build(page)
                    else:
                        show_snackbar(page, "Failed to archive mission", error=True)
                create_archive_dialog(page, item_type="rescue mission", item_name=f"#{mid}", on_confirm=on_confirm)
            
            def handle_remove(e, mid=mission_id):
                def on_confirm(reason):
                    success = self._app_state.rescues.remove_mission(mid, self._app_state.auth.user_id, reason)
                    if success:
                        show_snackbar(page, "Mission removed")
                        self.build(page)
                    else:
                        show_snackbar(page, "Failed to remove mission", error=True)
                create_remove_dialog(page, item_type="rescue mission", item_name=f"#{mid}", on_confirm=on_confirm)
            
            return ft.Row([
                ft.IconButton(icon=ft.Icons.ARCHIVE_OUTLINED, icon_color=ft.Colors.AMBER_700,
                             icon_size=15, tooltip="Archive", on_click=handle_archive),
                ft.IconButton(icon=ft.Icons.DELETE_OUTLINE, icon_color=ft.Colors.RED_600,
                             icon_size=15, tooltip="Remove", on_click=handle_remove),
            ], spacing=0, tight=True)
        
        table_rows = []
        for m in missions:
            mid = m.get("id")
            location = str(m.get("location", ""))
            notes = str(m.get("notes", ""))
            status = str(m.get("status", ""))
            name = m.get("animal_name") or m.get("reporter_name") or "Unknown"
            animal_type = m.get("animal_type") or "Unknown"
            reporter_phone = m.get("reporter_phone") or "N/A"
            details = notes
            
            location_display = location[:30] + "..." if len(location) > 30 else location
            details_display = details[:40] + "..." if len(details) > 40 else details
            
            breed = m.get('breed') or ''
            breed_display = (breed[:15] + "...") if len(breed) > 15 else (breed if breed else 'Not Specified')
            
            urgency = (m.get("urgency") or "medium").lower()
            urgency_colors = {
                "low": (ft.Colors.GREEN_100, ft.Colors.GREEN_700),
                "medium": (ft.Colors.ORANGE_100, ft.Colors.ORANGE_700),
                "high": (ft.Colors.RED_100, ft.Colors.RED_700),
            }
            bg_color, text_color = urgency_colors.get(urgency, (ft.Colors.GREY_100, ft.Colors.GREY_700))
            urgency_badge = ft.Container(
                ft.Text(urgency.capitalize(), size=11, color=text_color, weight="w500"),
                bgcolor=bg_color, padding=ft.padding.symmetric(horizontal=8, vertical=4), border_radius=10)
            
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
            
            row_data = [
                ft.Text(f"#{mid}", size=11, color=ft.Colors.TEAL_700, weight="w600"),
                ft.Text(name, size=11, color=ft.Colors.BLACK87, weight="w500"),
                ft.Text(animal_type, size=11, color=ft.Colors.BLACK87, weight="w500"),
                ft.Container(ft.Text(breed_display, size=11, color=ft.Colors.BLACK87, weight="w500"),
                            tooltip=breed if breed and len(breed) > 15 else None),
                ft.Text(reporter_phone, size=11, color=ft.Colors.BLACK87, weight="w500"),
                ft.Container(ft.Text(location_display, size=11, color=ft.Colors.BLACK87, weight="w500"),
                            tooltip=location if len(location) > 30 else None),
                ft.Container(ft.Text(details_display, size=11, color=ft.Colors.BLACK87, weight="w500"),
                            tooltip=details if len(details) > 40 else None),
                urgency_badge,
                source_cell,
                make_status_badge(status, mid),
                make_admin_actions(mid, name),
            ]
            table_rows.append(row_data)
        
        table_columns = [
            {"label": "#", "expand": 0},
            {"label": "Reporter", "expand": 2},
            {"label": "Animal", "expand": 1},
            {"label": "Breed", "expand": 2},
            {"label": "Contact", "expand": 1},
            {"label": "Location", "expand": 2},
            {"label": "Details", "expand": 2},
            {"label": "Urgency", "expand": 1},
            {"label": "Source", "expand": 1},
            {"label": "Status", "expand": 2},
            {"label": "Actions", "expand": 1},
        ]
        
        data_table = create_scrollable_data_table(
            columns=table_columns, rows=table_rows, height=400,
            empty_message="No rescue missions found", column_spacing=13,
            heading_row_height=45, data_row_height=50)
        
        # Map with rescue mission markers
        is_online = self.map_service.check_map_tiles_available()
        
        if is_online:
            map_container = create_interactive_map(
                map_service=self.map_service,
                missions=missions,
                page=self._page,
                is_admin=True,
                height=500,
                title="Realtime Rescue Mission Map",
                show_legend=True,
                initially_locked=True,
            )
        else:
            offline_widget = self.map_service.create_offline_map_fallback(missions, is_admin=True)
            if offline_widget:
                map_container = ft.Container(
                    ft.Column([
                        ft.Text("Realtime Rescue Mission Map", size=16, weight="w600", color=ft.Colors.BLACK87),
                        ft.Container(height=15),
                        ft.Container(offline_widget, height=500, border_radius=8,
                                    border=ft.border.all(1, ft.Colors.AMBER_200)),
                    ], spacing=0),
                    padding=20, bgcolor=ft.Colors.WHITE, border_radius=12,
                    shadow=ft.BoxShadow(blur_radius=8, spread_radius=1, color=ft.Colors.BLACK12, offset=(0, 2)))
            else:
                # Final fallback to simple placeholder
                map_container = ft.Container(
                    ft.Column([
                        ft.Text("Realtime Rescue Mission Map", size=16, weight="w600", color=ft.Colors.BLACK87),
                        ft.Container(height=15),
                        self.map_service.create_empty_map_placeholder(len(missions)),
                    ], spacing=0),
                    padding=20, bgcolor=ft.Colors.WHITE, border_radius=12,
                    shadow=ft.BoxShadow(blur_radius=8, spread_radius=1, color=ft.Colors.BLACK12, offset=(0, 2)))
        
        return ft.Column([
            create_section_card(title="Rescue Missions", content=data_table, show_divider=True),
            ft.Container(height=20),
            map_container,
        ], spacing=0)
    
    def _on_rescue_filter_change(self, page, filter_type: str, value: str) -> None:
        """Handle rescue mission filter changes."""
        if filter_type == "status":
            self._rescue_status_filter = value
        elif filter_type == "urgency":
            self._rescue_urgency_filter = value
        self.build(page)
    
    def _export_rescue_csv(self, missions: list) -> None:
        """Export rescue missions to CSV."""
        from components import show_snackbar
        
        if not missions:
            show_snackbar(self._page, "No missions to export", error=True)
            return
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"rescue_missions_{timestamp}.csv"
            filepath = app_config.STORAGE_DIR / "data" / "exports" / filename
            filepath.parent.mkdir(parents=True, exist_ok=True)
            
            fieldnames = ["id", "user_id", "animal_id", "reporter_name", "reporter_phone", "animal_type", 
                          "animal_name", "breed", "location", "latitude", "longitude", "urgency", "status", 
                          "notes", "admin_message", "is_closed", "mission_date", "updated_at", "animal_photo"]
            with open(filepath, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for m in missions:
                    writer.writerow({
                        "id": m.get("id", ""),
                        "user_id": m.get("user_id", ""),
                        "animal_id": m.get("animal_id", ""),
                        "reporter_name": m.get("reporter_name", ""),
                        "reporter_phone": m.get("reporter_phone", ""),
                        "animal_type": m.get("animal_type", ""),
                        "animal_name": m.get("animal_name", ""),
                        "breed": m.get("breed", ""),
                        "location": m.get("location", ""),
                        "latitude": m.get("latitude", ""),
                        "longitude": m.get("longitude", ""),
                        "urgency": m.get("urgency", ""),
                        "status": m.get("status", ""),
                        "notes": m.get("notes", ""),
                        "admin_message": m.get("admin_message", ""),
                        "is_closed": m.get("is_closed", ""),
                        "mission_date": m.get("mission_date", ""),
                        "updated_at": m.get("updated_at", ""),
                        "animal_photo": m.get("animal_photo", ""),
                    })
            
            show_snackbar(self._page, f"Exported {len(missions)} missions to {filename}")
        except Exception as e:
            show_snackbar(self._page, f"Export failed: {e}", error=True)
    
    def _build_adoption_requests_content(self, page, ft, show_snackbar, create_section_card,
                                          create_scrollable_data_table, create_archive_dialog,
                                          create_remove_dialog):
        """Build the adoption requests tab content."""
        
        all_requests = self._app_state.adoptions.requests
        
        if self._adoption_status_filter == "all":
            requests = all_requests
        else:
            requests = [r for r in all_requests 
                       if AdoptionStatus.normalize(r.get("status", "")) == self._adoption_status_filter]
        
        # Helper to create status badge
        def make_status_badge(status: str, request_id: int, is_frozen: bool = False):
            normalized = AdoptionStatus.normalize(status)
            
            if normalized == AdoptionStatus.APPROVED:
                bg_color = ft.Colors.GREEN_700
                icon = ft.Icons.CHECK_CIRCLE
            elif normalized == AdoptionStatus.DENIED:
                bg_color = ft.Colors.RED_700
                icon = ft.Icons.CANCEL
            elif normalized == AdoptionStatus.CANCELLED:
                bg_color = ft.Colors.GREY_600
                icon = ft.Icons.CANCEL
            else:
                bg_color = ft.Colors.ORANGE_700
                icon = ft.Icons.PENDING
            
            if is_frozen:
                tooltip_text = "Status locked - cancelled by user" if normalized == AdoptionStatus.CANCELLED else "Status locked - animal was removed from system"
                return ft.Container(
                    ft.Row([
                        ft.Icon(icon, color=ft.Colors.WHITE, size=14),
                        ft.Text(AdoptionStatus.get_label(status), color=ft.Colors.WHITE, size=12, weight="w500"),
                        ft.Icon(ft.Icons.LOCK, color=ft.Colors.WHITE70, size=12),
                    ], spacing=5, alignment=ft.MainAxisAlignment.CENTER),
                    padding=ft.padding.symmetric(horizontal=10, vertical=8),
                    bgcolor=bg_color, border_radius=15,
                    tooltip=tooltip_text)
            
            def change_status(e, new_status):
                self._on_adoption_status_change(page, request_id, new_status, show_snackbar)
            
            return ft.Container(
                ft.PopupMenuButton(
                    content=ft.Row([
                        ft.Icon(icon, color=ft.Colors.WHITE, size=14),
                        ft.Text(AdoptionStatus.get_label(status), color=ft.Colors.WHITE, size=12, weight="w500"),
                        ft.Icon(ft.Icons.ARROW_DROP_DOWN, color=ft.Colors.WHITE, size=16),
                    ], spacing=5, alignment=ft.MainAxisAlignment.CENTER),
                    items=[
                        ft.PopupMenuItem(text=AdoptionStatus.get_label(AdoptionStatus.PENDING),
                                        icon=ft.Icons.PENDING,
                                        on_click=lambda e: change_status(e, AdoptionStatus.PENDING)),
                        ft.PopupMenuItem(text=AdoptionStatus.get_label(AdoptionStatus.APPROVED),
                                        icon=ft.Icons.CHECK_CIRCLE,
                                        on_click=lambda e: change_status(e, AdoptionStatus.APPROVED)),
                        ft.PopupMenuItem(text=AdoptionStatus.get_label(AdoptionStatus.DENIED),
                                        icon=ft.Icons.CANCEL,
                                        on_click=lambda e: change_status(e, AdoptionStatus.DENIED)),
                    ],
                ),
                padding=ft.padding.symmetric(horizontal=10, vertical=8),
                bgcolor=bg_color, border_radius=15)
        
        # Helper to create admin action buttons
        def make_admin_actions(request_id: int, req_name: str):
            def handle_archive(e, rid=request_id):
                def on_confirm(note):
                    success = self._app_state.adoptions.archive_request(
                        rid, self._app_state.auth.user_id, note)
                    if success:
                        show_snackbar(page, "Request archived")
                        self.build(page)
                    else:
                        show_snackbar(page, "Failed to archive request", error=True)
                create_archive_dialog(page, item_type="adoption request", item_name=f"#{rid}", on_confirm=on_confirm)
            
            def handle_remove(e, rid=request_id):
                def on_confirm(reason):
                    success = self._app_state.adoptions.remove_request(rid, self._app_state.auth.user_id, reason)
                    if success:
                        show_snackbar(page, "Request removed")
                        self.build(page)
                    else:
                        show_snackbar(page, "Failed to remove request", error=True)
                create_remove_dialog(page, item_type="adoption request", item_name=f"#{rid}", on_confirm=on_confirm)
            
            return ft.Row([
                ft.IconButton(icon=ft.Icons.ARCHIVE_OUTLINED, icon_color=ft.Colors.AMBER_700,
                             icon_size=20, tooltip="Archive", on_click=handle_archive),
                ft.IconButton(icon=ft.Icons.DELETE_OUTLINE, icon_color=ft.Colors.RED_600,
                             icon_size=20, tooltip="Remove", on_click=handle_remove),
            ], spacing=0, tight=True)
        
        table_rows = []
        for req in requests:
            request_id = req.get("id")
            user_name = req.get("user_name", "N/A")
            contact = req.get("contact", "N/A")
            reason = req.get("reason", "N/A")
            status = req.get("status") or "pending"
            
            breed = req.get('animal_breed') or ''
            breed_display = (breed[:15] + "...") if len(breed) > 15 else (breed if breed else 'Not Specified')
            
            animal_id = req.get("animal_id")
            animal_name = req.get("animal_name")
            animal_was_deleted = False
            
            if animal_id is None or (animal_id and not req.get("animal_species")):
                animal_name = animal_name or "Unknown Animal"
                animal_was_deleted = True
            elif not animal_name:
                animal_name = "N/A"
            
            animal_was_removed = animal_id is None or (animal_id and not req.get("animal_species"))
            is_cancelled = AdoptionStatus.is_cancelled(status)
            is_frozen = animal_was_removed or is_cancelled
            
            status_widget = make_status_badge(status, request_id, is_frozen)
            
            if animal_was_deleted:
                final_status_widget = ft.Column([
                    status_widget,
                    ft.Text("(Animal Deleted)", size=10, color=ft.Colors.GREY_500, italic=True),
                ], spacing=2, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
                animal_name_widget = ft.Text(animal_name, size=12, color=ft.Colors.GREY_500, italic=True)
            else:
                final_status_widget = status_widget
                animal_name_widget = ft.Text(animal_name, size=12, color=ft.Colors.BLACK87)
            
            reason_display = reason[:40] + "..." if len(reason) > 40 else reason
            
            row_data = [
                ft.Text(user_name, size=12, color=ft.Colors.BLACK87),
                animal_name_widget,
                ft.Container(ft.Text(breed_display, size=12, color=ft.Colors.BLACK87),
                            tooltip=breed if breed and len(breed) > 15 else None),
                ft.Text(contact, size=12, color=ft.Colors.BLACK87),
                ft.Container(ft.Text(reason_display, size=12, color=ft.Colors.BLACK87),
                            tooltip=reason if len(reason) > 40 else None),
                final_status_widget,
                make_admin_actions(request_id, user_name),
            ]
            table_rows.append(row_data)
        
        table_columns = [
            {"label": "User Name", "expand": 2},
            {"label": "Animal", "expand": 2},
            {"label": "Breed", "expand": 2},
            {"label": "Contact", "expand": 2},
            {"label": "Reason", "expand": 3},
            {"label": "Status", "expand": 2},
            {"label": "Actions", "expand": 1},
        ]
        
        data_table = create_scrollable_data_table(
            columns=table_columns, rows=table_rows, height=400,
            empty_message="No adoption requests found", column_spacing=20,
            heading_row_height=45, data_row_height=55)
        
        return ft.Column([
            create_section_card(title="Adoption Requests", content=data_table, show_divider=True),
        ], spacing=0)
    
    def _on_adoption_filter_change(self, page, value: str) -> None:
        """Handle adoption filter changes."""
        self._adoption_status_filter = value
        self.build(page)
    
    def _export_adoption_csv(self, requests: list) -> None:
        """Export adoption requests to CSV."""
        from components import show_snackbar
        
        if not requests:
            show_snackbar(self._page, "No requests to export", error=True)
            return
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"adoption_requests_{timestamp}.csv"
            filepath = app_config.STORAGE_DIR / "data" / "exports" / filename
            filepath.parent.mkdir(parents=True, exist_ok=True)
            
            fieldnames = ["id", "user_id", "user_name", "animal_id", "animal_name", "animal_species", 
                          "animal_breed", "contact", "reason", "status", "notes", "admin_message", "was_approved", 
                          "request_date", "updated_at"]
            with open(filepath, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for r in requests:
                    writer.writerow({
                        "id": r.get("id", ""),
                        "user_id": r.get("user_id", ""),
                        "user_name": r.get("user_name", ""),
                        "animal_id": r.get("animal_id", ""),
                        "animal_name": r.get("animal_name", ""),
                        "animal_species": r.get("animal_species", ""),
                        "animal_breed": r.get("animal_breed", ""),
                        "contact": r.get("contact", ""),
                        "reason": r.get("reason", ""),
                        "status": r.get("status", ""),
                        "notes": r.get("notes", ""),
                        "admin_message": r.get("admin_message", ""),
                        "was_approved": r.get("was_approved", ""),
                        "request_date": r.get("request_date", ""),
                        "updated_at": r.get("updated_at", ""),
                    })
            
            show_snackbar(self._page, f"Exported {len(requests)} requests to {filename}")
        except Exception as e:
            show_snackbar(self._page, f"Export failed: {e}", error=True)
    
    def _build_hidden_items_content(self, page, ft, show_snackbar, create_empty_state,
                                     create_restore_dialog, create_permanent_delete_dialog):
        """Build the hidden items tab content with sub-tabs."""
        
        # Sub-tab change handler
        def on_hidden_tab_change(e):
            self._hidden_tab_index = e.control.selected_index
            self.build(page)
        
        hidden_tabs = ft.Tabs(
            selected_index=self._hidden_tab_index,
            animation_duration=300,
            on_change=on_hidden_tab_change,
            indicator_color=ft.Colors.AMBER_700,
            label_color=ft.Colors.AMBER_800,
            unselected_label_color=ft.Colors.GREY_600,
            tab_alignment=ft.TabAlignment.START,
            tabs=[
                ft.Tab(text="Rescue Missions"),
                ft.Tab(text="Adoption Requests"),
                ft.Tab(text="Animals"),
            ],
        )
        
        if self._hidden_tab_index == 0:
            sub_content = self._build_hidden_rescues(page, ft, show_snackbar, create_empty_state,
                                                      create_restore_dialog, create_permanent_delete_dialog)
        elif self._hidden_tab_index == 1:
            sub_content = self._build_hidden_adoptions(page, ft, show_snackbar, create_empty_state,
                                                        create_restore_dialog, create_permanent_delete_dialog)
        else:
            sub_content = self._build_hidden_animals(page, ft, show_snackbar, create_empty_state,
                                                      create_restore_dialog, create_permanent_delete_dialog)
        
        return ft.Container(
            ft.Column([
                ft.Container(
                    content=hidden_tabs,
                    bgcolor=ft.Colors.with_opacity(0.3, ft.Colors.AMBER_100),
                    border_radius=8,
                    padding=ft.padding.only(left=8, right=8),
                ),
                ft.Container(height=12),
                sub_content,
            ], spacing=0),
            padding=16,
            bgcolor=ft.Colors.with_opacity(0.8, ft.Colors.WHITE),
            border_radius=12,
            shadow=ft.BoxShadow(blur_radius=8, spread_radius=1, color=ft.Colors.BLACK12, offset=(0, 2)),
        )
    
    def _build_hidden_rescues(self, page, ft, show_snackbar, create_empty_state,
                               create_restore_dialog, create_permanent_delete_dialog):
        """Build hidden rescue missions list."""
        hidden_missions = self._app_state.rescues.load_hidden_missions()
        
        if not hidden_missions:
            from components import create_empty_state_with_action
            return create_empty_state_with_action(
                icon=ft.Icons.INBOX_OUTLINED,
                message="No hidden rescue missions",
                button_text="View Rescue Missions",
                button_icon=ft.Icons.LOCAL_HOSPITAL,
                on_click=lambda e: self._switch_to_tab(page, 0),
            )
        
        archived = [m for m in hidden_missions if RescueStatus.is_archived(m.get("status", ""))]
        removed = [m for m in hidden_missions if RescueStatus.is_removed(m.get("status", ""))]
        
        sections = []
        
        if archived:
            from components import create_section_header
            sections.append(create_section_header("Archived Missions", len(archived), ft.Colors.AMBER_700))
            for mission in archived:
                sections.append(self._build_rescue_card(page, ft, mission, False, show_snackbar,
                                                        create_restore_dialog, create_permanent_delete_dialog))
        
        if removed:
            if archived:
                sections.append(ft.Container(height=24))
            from components import create_section_header
            sections.append(create_section_header("Removed Missions", len(removed), ft.Colors.RED_700))
            for mission in removed:
                sections.append(self._build_rescue_card(page, ft, mission, True, show_snackbar,
                                                        create_restore_dialog, create_permanent_delete_dialog))
        
        return ft.Column(sections, spacing=12)
    
    def _build_hidden_adoptions(self, page, ft, show_snackbar, create_empty_state,
                                 create_restore_dialog, create_permanent_delete_dialog):
        """Build hidden adoption requests list."""
        hidden_requests = self._app_state.adoptions.load_hidden_requests()
        
        if not hidden_requests:
            from components import create_empty_state_with_action
            return create_empty_state_with_action(
                icon=ft.Icons.INBOX_OUTLINED,
                message="No hidden adoption requests",
                button_text="View Adoption Requests",
                button_icon=ft.Icons.VOLUNTEER_ACTIVISM,
                on_click=lambda e: self._switch_to_tab(page, 1),
            )
        
        archived = [r for r in hidden_requests if AdoptionStatus.is_archived(r.get("status", ""))]
        removed = [r for r in hidden_requests if AdoptionStatus.is_removed(r.get("status", ""))]
        
        sections = []
        
        if archived:
            from components import create_section_header
            sections.append(create_section_header("Archived Requests", len(archived), ft.Colors.AMBER_700))
            for request in archived:
                sections.append(self._build_adoption_card(page, ft, request, False, show_snackbar,
                                                          create_restore_dialog, create_permanent_delete_dialog))
        
        if removed:
            if archived:
                sections.append(ft.Container(height=24))
            from components import create_section_header
            sections.append(create_section_header("Removed Requests", len(removed), ft.Colors.RED_700))
            for request in removed:
                sections.append(self._build_adoption_card(page, ft, request, True, show_snackbar,
                                                          create_restore_dialog, create_permanent_delete_dialog))
        
        return ft.Column(sections, spacing=12)
    
    def _build_hidden_animals(self, page, ft, show_snackbar, create_empty_state,
                               create_restore_dialog, create_permanent_delete_dialog):
        """Build hidden animals list."""
        hidden_animals = self._app_state.animals.load_hidden_animals()
        
        if not hidden_animals:
            from components import create_empty_state_with_action
            return create_empty_state_with_action(
                icon=ft.Icons.INBOX_OUTLINED,
                message="No hidden animals",
                button_text="View Animals List",
                button_icon=ft.Icons.PETS,
                on_click=lambda e: page.go("/animals_list?admin=1"),
            )
        
        archived = [a for a in hidden_animals if AnimalStatus.is_archived(a.get("status", ""))]
        removed = [a for a in hidden_animals if AnimalStatus.is_removed(a.get("status", ""))]
        
        sections = []
        
        if archived:
            from components import create_section_header
            sections.append(create_section_header("Archived Animals", len(archived), ft.Colors.AMBER_700))
            for animal in archived:
                sections.append(self._build_animal_card(page, ft, animal, False, show_snackbar,
                                                        create_restore_dialog, create_permanent_delete_dialog))
        
        if removed:
            if archived:
                sections.append(ft.Container(height=24))
            from components import create_section_header
            sections.append(create_section_header("Removed Animals", len(removed), ft.Colors.RED_700))
            for animal in removed:
                sections.append(self._build_animal_card(page, ft, animal, True, show_snackbar,
                                                        create_restore_dialog, create_permanent_delete_dialog))
        
        return ft.Column(sections, spacing=12)
    
    def _build_rescue_card(self, page, ft, mission, is_removed, show_snackbar,
                           create_restore_dialog, create_permanent_delete_dialog):
        """Build a card for a hidden rescue mission."""
        mission_id = mission.get("id")
        status = mission.get("status", "")
        base_status = RescueStatus.get_base_status(status)
        previous_status = mission.get("previous_status") or base_status
        
        if is_removed:
            hidden_reason = mission.get("removal_reason", "")
            badge_color = ft.Colors.RED_100
            badge_text_color = ft.Colors.RED_700
            badge_text = f"Removed: {hidden_reason}"
        else:
            hidden_reason = mission.get("archive_note", "")
            badge_color = ft.Colors.AMBER_100
            badge_text_color = ft.Colors.AMBER_700
            badge_text = f"Archived (was: {RescueStatus.get_label(previous_status)})"
            if hidden_reason:
                badge_text += f" - {hidden_reason}"
        
        def handle_restore(e):
            def on_confirm():
                success = self._app_state.rescues.restore_mission(mission_id)
                if success:
                    show_snackbar(page, "Mission restored successfully!")
                    self.build(page)
                else:
                    show_snackbar(page, "Failed to restore mission", error=True)
            create_restore_dialog(page, item_type="rescue mission", item_name=f"#{mission_id}",
                                 previous_status=RescueStatus.get_label(previous_status), on_confirm=on_confirm)
        
        def handle_permanent_delete(e):
            def on_confirm():
                success = self._app_state.rescues.permanently_delete_mission(mission_id)
                if success:
                    show_snackbar(page, "Mission permanently deleted!")
                    self.build(page)
                else:
                    show_snackbar(page, "Failed to delete mission", error=True)
            create_permanent_delete_dialog(page, item_type="rescue mission", item_name=f"#{mission_id}",
                                          on_confirm=on_confirm)
        
        actions = [ft.IconButton(icon=ft.Icons.RESTORE, icon_color=ft.Colors.TEAL_600,
                                tooltip="Restore", on_click=handle_restore)]
        if is_removed:
            actions.append(ft.IconButton(icon=ft.Icons.DELETE_FOREVER, icon_color=ft.Colors.RED_600,
                                        tooltip="Delete Forever", on_click=handle_permanent_delete))
        
        breed = mission.get('breed') or ''
        breed_display = breed if breed else 'Not Specified'
        
        return ft.Container(
            content=ft.Row([
                ft.Column([
                    ft.Text(f"Mission #{mission_id}", weight=ft.FontWeight.BOLD),
                    ft.Text(f"Location: {mission.get('location', 'N/A')}", size=13, color=ft.Colors.GREY_700),
                    ft.Text(f"Animal: {mission.get('animal_type', 'N/A')}", size=13, color=ft.Colors.GREY_700),
                    ft.Text(f"Breed: {breed_display}", size=13, color=ft.Colors.GREY_700),
                    ft.Container(
                        content=ft.Text(badge_text, size=12, color=badge_text_color),
                        bgcolor=badge_color, border_radius=4,
                        padding=ft.padding.symmetric(horizontal=8, vertical=2)),
                ], spacing=4, expand=True),
                ft.Row(actions, spacing=0),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=16, bgcolor=ft.Colors.GREY_50, border_radius=8,
            border=ft.border.all(1, ft.Colors.GREY_300))
    
    def _build_adoption_card(self, page, ft, request, is_removed, show_snackbar,
                             create_restore_dialog, create_permanent_delete_dialog):
        """Build a card for a hidden adoption request."""
        request_id = request.get("id")
        status = request.get("status", "")
        base_status = AdoptionStatus.get_base_status(status)
        previous_status = request.get("previous_status") or base_status
        
        animal_name = request.get("animal_name", "Unknown Animal")
        user_name = request.get("user_name", "Unknown User")
        
        if is_removed:
            hidden_reason = request.get("removal_reason", "")
            badge_color = ft.Colors.RED_100
            badge_text_color = ft.Colors.RED_700
            badge_text = f"Removed: {hidden_reason}"
        else:
            hidden_reason = request.get("archive_note", "")
            badge_color = ft.Colors.AMBER_100
            badge_text_color = ft.Colors.AMBER_700
            badge_text = f"Archived (was: {AdoptionStatus.get_label(previous_status)})"
            if hidden_reason:
                badge_text += f" - {hidden_reason}"
        
        def handle_restore(e):
            def on_confirm():
                success = self._app_state.adoptions.restore_request(request_id)
                if success:
                    show_snackbar(page, "Request restored successfully!")
                    self.build(page)
                else:
                    show_snackbar(page, "Failed to restore request", error=True)
            create_restore_dialog(page, item_type="adoption request", item_name=f"#{request_id}",
                                 previous_status=AdoptionStatus.get_label(previous_status), on_confirm=on_confirm)
        
        def handle_permanent_delete(e):
            def on_confirm():
                success = self._app_state.adoptions.permanently_delete_request(request_id)
                if success:
                    show_snackbar(page, "Request permanently deleted!")
                    self.build(page)
                else:
                    show_snackbar(page, "Failed to delete request", error=True)
            create_permanent_delete_dialog(page, item_type="adoption request", item_name=f"#{request_id}",
                                          on_confirm=on_confirm)
        
        actions = [ft.IconButton(icon=ft.Icons.RESTORE, icon_color=ft.Colors.TEAL_600,
                                tooltip="Restore", on_click=handle_restore)]
        if is_removed:
            actions.append(ft.IconButton(icon=ft.Icons.DELETE_FOREVER, icon_color=ft.Colors.RED_600,
                                        tooltip="Delete Forever", on_click=handle_permanent_delete))
        
        breed = request.get('animal_breed') or ''
        breed_display = breed if breed else 'Not Specified'
        
        return ft.Container(
            content=ft.Row([
                ft.Column([
                    ft.Text(f"Request #{request_id}", weight=ft.FontWeight.BOLD),
                    ft.Text(f"Animal: {animal_name}", size=13, color=ft.Colors.GREY_700),
                    ft.Text(f"Breed: {breed_display}", size=13, color=ft.Colors.GREY_700),
                    ft.Text(f"Applicant: {user_name}", size=13, color=ft.Colors.GREY_700),
                    ft.Container(
                        content=ft.Text(badge_text, size=12, color=badge_text_color),
                        bgcolor=badge_color, border_radius=4,
                        padding=ft.padding.symmetric(horizontal=8, vertical=2)),
                ], spacing=4, expand=True),
                ft.Row(actions, spacing=0),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=16, bgcolor=ft.Colors.GREY_50, border_radius=8,
            border=ft.border.all(1, ft.Colors.GREY_300))
    
    def _build_animal_card(self, page, ft, animal, is_removed, show_snackbar,
                           create_restore_dialog, create_permanent_delete_dialog):
        """Build a card for a hidden animal."""
        from services.photo_service import load_photo
        
        animal_id = animal.get("id")
        name = animal.get("name", "Unknown")
        species = animal.get("species", "Unknown")
        status = animal.get("status", "")
        base_status = AnimalStatus.get_base_status(status)
        previous_status = animal.get("previous_status") or base_status
        
        photo_b64 = load_photo(animal.get("photo"))
        
        if is_removed:
            hidden_reason = animal.get("removal_reason", "")
            badge_color = ft.Colors.RED_100
            badge_text_color = ft.Colors.RED_700
            badge_text = f"Removed: {hidden_reason}"
        else:
            hidden_reason = animal.get("archive_note", "")
            badge_color = ft.Colors.AMBER_100
            badge_text_color = ft.Colors.AMBER_700
            badge_text = f"Archived (was: {AnimalStatus.get_label(previous_status)})"
            if hidden_reason:
                badge_text += f" - {hidden_reason}"
        
        def handle_restore(e):
            def on_confirm():
                success = self._app_state.animals.restore_animal(animal_id)
                if success:
                    show_snackbar(page, "Animal restored successfully!")
                    self.build(page)
                else:
                    show_snackbar(page, "Failed to restore animal", error=True)
            create_restore_dialog(page, item_type="animal", item_name=name,
                                 previous_status=AnimalStatus.get_label(previous_status), on_confirm=on_confirm)
        
        def handle_permanent_delete(e):
            def on_confirm():
                result = self._app_state.animals.permanently_delete_animal(animal_id)
                if result.get("success"):
                    show_snackbar(page, "Animal permanently deleted!")
                    self.build(page)
                else:
                    show_snackbar(page, "Failed to delete animal", error=True)
            create_permanent_delete_dialog(page, item_type="animal", item_name=name, on_confirm=on_confirm)
        
        if photo_b64:
            photo_element = ft.Image(src_base64=photo_b64, width=60, height=60,
                                     fit=ft.ImageFit.COVER, border_radius=8)
        else:
            photo_element = ft.Container(
                content=ft.Icon(ft.Icons.PETS, color=ft.Colors.GREY_400, size=30),
                width=60, height=60, bgcolor=ft.Colors.GREY_200,
                border_radius=8, alignment=ft.alignment.center)
        
        actions = [ft.IconButton(icon=ft.Icons.RESTORE, icon_color=ft.Colors.TEAL_600,
                                tooltip="Restore", on_click=handle_restore)]
        if is_removed:
            actions.append(ft.IconButton(icon=ft.Icons.DELETE_FOREVER, icon_color=ft.Colors.RED_600,
                                        tooltip="Delete Forever", on_click=handle_permanent_delete))
        
        breed = animal.get('breed') or ''
        breed_display = breed if breed else 'Not Specified'
        
        return ft.Container(
            content=ft.Row([
                photo_element,
                ft.Container(width=12),
                ft.Column([
                    ft.Text(name, weight=ft.FontWeight.BOLD),
                    ft.Text(f"Species: {species}", size=13, color=ft.Colors.GREY_700),
                    ft.Text(f"Breed: {breed_display}", size=13, color=ft.Colors.GREY_700),
                    ft.Container(
                        content=ft.Text(badge_text, size=12, color=badge_text_color),
                        bgcolor=badge_color, border_radius=4,
                        padding=ft.padding.symmetric(horizontal=8, vertical=2)),
                ], spacing=4, expand=True),
                ft.Row(actions, spacing=0),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=16, bgcolor=ft.Colors.GREY_50, border_radius=8,
            border=ft.border.all(1, ft.Colors.GREY_300))
    
    def _on_rescue_status_change(self, page, mission_id: int, new_status: str, show_snackbar) -> None:
        """Update mission status."""
        try:
            updated = self._app_state.rescues.update_mission(mission_id, status=new_status)
            if updated:
                show_snackbar(page, "Status updated")
                self.build(page)
            else:
                show_snackbar(page, "Failed to update status", error=True)
        except Exception as exc:
            show_snackbar(page, f"Error: {exc}", error=True)
    
    def _on_adoption_status_change(self, page, request_id: int, new_status: str, show_snackbar) -> None:
        """Update adoption request status."""
        try:
            updated = self._app_state.adoptions.update_request_status(request_id, new_status)
            if updated:
                show_snackbar(page, f"Status updated to {new_status}")
                self.build(page)
            else:
                show_snackbar(page, "Failed to update status", error=True)
        except Exception as exc:
            show_snackbar(page, f"Error: {exc}", error=True)


__all__ = ["ManageRecordsPage"]
