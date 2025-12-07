"""Hidden Items Page - Admin view for archived and removed items."""
from __future__ import annotations

from typing import Any, Dict, Optional

import app_config
from app_config import RescueStatus, AdoptionStatus, AnimalStatus


class HiddenItemsPage:
    """Admin page for managing archived and removed items.
    
    Shows all hidden items across:
    - Rescue Missions (archived/removed)
    - Adoption Requests (archived/removed)
    - Animals (archived/removed)
    
    Provides actions to:
    - Restore items to their previous status
    - Permanently delete removed items
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize the page.
        
        Args:
            db_path: Path to database file (defaults to app_config.DB_PATH)
        """
        self._db_path = db_path or app_config.DB_PATH
        self._page = None
        self._tab_index = 0
        
        # UI references
        self._tabs = None
        self._content_area = None
        
        # State managers
        self._rescue_state = None
        self._adoption_state = None
        self._animal_state = None
    
    def _get_states(self):
        """Lazy-load state managers."""
        if self._rescue_state is None:
            from state import get_app_state
            app_state = get_app_state()
            self._rescue_state = app_state.rescues
            self._adoption_state = app_state.adoptions
            self._animal_state = app_state.animals
    
    def build(self, page) -> None:
        """Build and display the hidden items page.
        
        Args:
            page: The Flet page instance
        """
        import flet as ft
        from components import (
            create_admin_sidebar,
            create_page_title,
            create_section_card,
            create_empty_state,
            show_snackbar,
            create_restore_dialog,
            create_permanent_delete_dialog,
        )
        from state import get_app_state
        
        self._page = page
        self._get_states()
        
        # Auth check
        app_state = get_app_state()
        if not app_state.auth.is_authenticated or app_state.auth.user_role != "admin":
            page.go("/login")
            return
        
        page.title = "Hidden Items - PawRes Admin"
        page.bgcolor = ft.Colors.GREY_100
        
        # Tab change handler
        def on_tab_change(e):
            self._tab_index = e.control.selected_index
            self._refresh_content()
        
        self._tabs = ft.Tabs(
            selected_index=self._tab_index,
            animation_duration=300,
            on_change=on_tab_change,
            tabs=[
                ft.Tab(
                    text="Rescue Missions",
                    icon=ft.Icons.LOCAL_HOSPITAL_OUTLINED,
                ),
                ft.Tab(
                    text="Adoption Requests",
                    icon=ft.Icons.VOLUNTEER_ACTIVISM_OUTLINED,
                ),
                ft.Tab(
                    text="Animals",
                    icon=ft.Icons.PETS_OUTLINED,
                ),
            ],
        )
        
        # Content area
        self._content_area = ft.Container(
            expand=True,
            padding=20,
        )
        
        self._refresh_content()
        
        sidebar = create_admin_sidebar(page, current_route=page.route)
        
        # Main layout
        main_content = ft.Container(
            content=ft.Column([
                create_page_title("Hidden Items"),
                ft.Text("Manage archived and removed items", size=14, color=ft.Colors.BLACK54),
                ft.Container(height=16),
                ft.Container(
                    content=self._tabs,
                    bgcolor=ft.Colors.WHITE,
                    border_radius=12,
                    padding=ft.padding.only(left=16, right=16, top=8),
                ),
                self._content_area,
            ], scroll=ft.ScrollMode.AUTO),
            expand=True,
            padding=24,
        )
        
        # Page layout
        page.controls.clear()
        page.add(
            ft.Row([
                sidebar,
                main_content,
            ], expand=True, spacing=0)
        )
        page.update()
    
    def _refresh_content(self):
        """Refresh the content area based on selected tab."""
        import flet as ft
        
        if self._tab_index == 0:
            content = self._build_rescue_missions_content()
        elif self._tab_index == 1:
            content = self._build_adoption_requests_content()
        else:
            content = self._build_animals_content()
        
        self._content_area.content = content
        if self._page:
            self._page.update()
    
    def _build_rescue_missions_content(self):
        """Build the rescue missions hidden items list."""
        import flet as ft
        from components import create_empty_state, create_section_card
        
        hidden_missions = self._rescue_state.load_hidden_missions()
        
        if not hidden_missions:
            return create_empty_state(
                icon=ft.Icons.INBOX_OUTLINED,
                message="No hidden rescue missions. There are no archived or removed missions."
            )
        
        # Separate archived and removed
        archived = [m for m in hidden_missions if RescueStatus.is_archived(m.get("status", ""))]
        removed = [m for m in hidden_missions if RescueStatus.is_removed(m.get("status", ""))]
        
        sections = []
        
        if archived:
            from components import create_section_header
            sections.append(create_section_header("Archived Missions", len(archived), ft.Colors.AMBER_700))
            for mission in archived:
                sections.append(self._build_rescue_mission_card(mission, is_removed=False))
        
        if removed:
            if archived:
                sections.append(ft.Container(height=24))
            from components import create_section_header
            sections.append(create_section_header("Removed Missions", len(removed), ft.Colors.RED_700))
            for mission in removed:
                sections.append(self._build_rescue_mission_card(mission, is_removed=True))
        
        return ft.Column(sections, spacing=12)
    
    def _build_adoption_requests_content(self):
        """Build the adoption requests hidden items list."""
        import flet as ft
        from components import create_empty_state
        
        hidden_requests = self._adoption_state.load_hidden_requests()
        
        if not hidden_requests:
            return create_empty_state(
                icon=ft.Icons.INBOX_OUTLINED,
                message="No hidden adoption requests. There are no archived or removed requests."
            )
        
        # Separate archived and removed
        archived = [r for r in hidden_requests if AdoptionStatus.is_archived(r.get("status", ""))]
        removed = [r for r in hidden_requests if AdoptionStatus.is_removed(r.get("status", ""))]
        
        sections = []
        
        if archived:
            from components import create_section_header
            sections.append(create_section_header("Archived Requests", len(archived), ft.Colors.AMBER_700))
            for request in archived:
                sections.append(self._build_adoption_request_card(request, is_removed=False))
        
        if removed:
            if archived:
                sections.append(ft.Container(height=24))
            from components import create_section_header
            sections.append(create_section_header("Removed Requests", len(removed), ft.Colors.RED_700))
            for request in removed:
                sections.append(self._build_adoption_request_card(request, is_removed=True))
        
        return ft.Column(sections, spacing=12)
    
    def _build_animals_content(self):
        """Build the animals hidden items list."""
        import flet as ft
        from components import create_empty_state
        
        hidden_animals = self._animal_state.load_hidden_animals()
        
        if not hidden_animals:
            return create_empty_state(
                icon=ft.Icons.INBOX_OUTLINED,
                message="No hidden animals. There are no archived or removed animals."
            )
        
        # Separate archived and removed
        archived = [a for a in hidden_animals if AnimalStatus.is_archived(a.get("status", ""))]
        removed = [a for a in hidden_animals if AnimalStatus.is_removed(a.get("status", ""))]
        
        sections = []
        
        if archived:
            from components import create_section_header
            sections.append(create_section_header("Archived Animals", len(archived), ft.Colors.AMBER_700))
            for animal in archived:
                sections.append(self._build_animal_card(animal, is_removed=False))
        
        if removed:
            if archived:
                sections.append(ft.Container(height=24))
            from components import create_section_header
            sections.append(create_section_header("Removed Animals", len(removed), ft.Colors.RED_700))
            for animal in removed:
                sections.append(self._build_animal_card(animal, is_removed=True))
        
        return ft.Column(sections, spacing=12)
    
    def _build_rescue_mission_card(self, mission: Dict[str, Any], is_removed: bool):
        """Build a card for a hidden rescue mission."""
        import flet as ft
        from components import show_snackbar, create_restore_dialog, create_permanent_delete_dialog
        from state import get_app_state
        
        mission_id = mission.get("id")
        status = mission.get("status", "")
        base_status = RescueStatus.get_base_status(status)
        previous_status = mission.get("previous_status") or base_status
        
        if is_removed:
            hidden_date = mission.get("removed_at", "")
            hidden_reason = mission.get("removal_reason", "")
            badge_color = ft.Colors.RED_100
            badge_text_color = ft.Colors.RED_700
            badge_text = f"Removed: {hidden_reason}"
        else:
            hidden_date = mission.get("archived_at", "")
            hidden_reason = mission.get("archive_note", "")
            badge_color = ft.Colors.AMBER_100
            badge_text_color = ft.Colors.AMBER_700
            badge_text = f"Archived (was: {RescueStatus.get_label(previous_status)})"
            if hidden_reason:
                badge_text += f" - {hidden_reason}"
        
        def handle_restore(e):
            def on_confirm():
                app_state = get_app_state()
                success = self._rescue_state.restore_mission(mission_id)
                if success:
                    show_snackbar(self._page, "Mission restored successfully!")
                    self._refresh_content()
                else:
                    show_snackbar(self._page, "Failed to restore mission", error=True)
            
            create_restore_dialog(
                self._page,
                item_type="rescue mission",
                item_name=f"#{mission_id}",
                previous_status=RescueStatus.get_label(previous_status),
                on_confirm=on_confirm,
            )
        
        def handle_permanent_delete(e):
            def on_confirm():
                success = self._rescue_state.permanently_delete_mission(mission_id)
                if success:
                    show_snackbar(self._page, "Mission permanently deleted!")
                    self._refresh_content()
                else:
                    show_snackbar(self._page, "Failed to delete mission", error=True)
            
            create_permanent_delete_dialog(
                self._page,
                item_type="rescue mission",
                item_name=f"#{mission_id}",
                on_confirm=on_confirm,
            )
        
        # Action buttons
        actions = [
            ft.IconButton(
                icon=ft.Icons.RESTORE,
                icon_color=ft.Colors.TEAL_600,
                tooltip="Restore",
                on_click=handle_restore,
            ),
        ]
        
        if is_removed:
            actions.append(
                ft.IconButton(
                    icon=ft.Icons.DELETE_FOREVER,
                    icon_color=ft.Colors.RED_600,
                    tooltip="Delete Forever",
                    on_click=handle_permanent_delete,
                ),
            )
        
        breed = mission.get('breed', '')
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
                        bgcolor=badge_color,
                        border_radius=4,
                        padding=ft.padding.symmetric(horizontal=8, vertical=2),
                    ),
                ], spacing=4, expand=True),
                ft.Row(actions, spacing=0),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=16,
            bgcolor=ft.Colors.WHITE,
            border_radius=8,
            border=ft.border.all(1, ft.Colors.GREY_300),
        )
    
    def _build_adoption_request_card(self, request: Dict[str, Any], is_removed: bool):
        """Build a card for a hidden adoption request."""
        import flet as ft
        from components import show_snackbar, create_restore_dialog, create_permanent_delete_dialog
        
        request_id = request.get("id")
        status = request.get("status", "")
        base_status = AdoptionStatus.get_base_status(status)
        previous_status = request.get("previous_status") or base_status
        
        animal_name = request.get("animal_name", "Unknown Animal")
        user_name = request.get("user_name", "Unknown User")
        
        if is_removed:
            hidden_date = request.get("removed_at", "")
            hidden_reason = request.get("removal_reason", "")
            badge_color = ft.Colors.RED_100
            badge_text_color = ft.Colors.RED_700
            badge_text = f"Removed: {hidden_reason}"
        else:
            hidden_date = request.get("archived_at", "")
            hidden_reason = request.get("archive_note", "")
            badge_color = ft.Colors.AMBER_100
            badge_text_color = ft.Colors.AMBER_700
            badge_text = f"Archived (was: {AdoptionStatus.get_label(previous_status)})"
            if hidden_reason:
                badge_text += f" - {hidden_reason}"
        
        def handle_restore(e):
            def on_confirm():
                success = self._adoption_state.restore_request(request_id)
                if success:
                    show_snackbar(self._page, "Request restored successfully!")
                    self._refresh_content()
                else:
                    show_snackbar(self._page, "Failed to restore request", error=True)
            
            create_restore_dialog(
                self._page,
                item_type="adoption request",
                item_name=f"#{request_id}",
                previous_status=AdoptionStatus.get_label(previous_status),
                on_confirm=on_confirm,
            )
        
        def handle_permanent_delete(e):
            def on_confirm():
                success = self._adoption_state.permanently_delete_request(request_id)
                if success:
                    show_snackbar(self._page, "Request permanently deleted!")
                    self._refresh_content()
                else:
                    show_snackbar(self._page, "Failed to delete request", error=True)
            
            create_permanent_delete_dialog(
                self._page,
                item_type="adoption request",
                item_name=f"#{request_id}",
                on_confirm=on_confirm,
            )
        
        # Action buttons
        actions = [
            ft.IconButton(
                icon=ft.Icons.RESTORE,
                icon_color=ft.Colors.TEAL_600,
                tooltip="Restore",
                on_click=handle_restore,
            ),
        ]
        
        if is_removed:
            actions.append(
                ft.IconButton(
                    icon=ft.Icons.DELETE_FOREVER,
                    icon_color=ft.Colors.RED_600,
                    tooltip="Delete Forever",
                    on_click=handle_permanent_delete,
                ),
            )
        
        breed = request.get('animal_breed', '')
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
                        bgcolor=badge_color,
                        border_radius=4,
                        padding=ft.padding.symmetric(horizontal=8, vertical=2),
                    ),
                ], spacing=4, expand=True),
                ft.Row(actions, spacing=0),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=16,
            bgcolor=ft.Colors.WHITE,
            border_radius=8,
            border=ft.border.all(1, ft.Colors.GREY_300),
        )
    
    def _build_animal_card(self, animal: Dict[str, Any], is_removed: bool):
        """Build a card for a hidden animal."""
        import flet as ft
        from components import show_snackbar, create_restore_dialog, create_permanent_delete_dialog
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
                success = self._animal_state.restore_animal(animal_id)
                if success:
                    show_snackbar(self._page, "Animal restored successfully!")
                    self._refresh_content()
                else:
                    show_snackbar(self._page, "Failed to restore animal", error=True)
            
            create_restore_dialog(
                self._page,
                item_type="animal",
                item_name=name,
                previous_status=AnimalStatus.get_label(previous_status),
                on_confirm=on_confirm,
            )
        
        def handle_permanent_delete(e):
            def on_confirm():
                result = self._animal_state.permanently_delete_animal(animal_id)
                if result.get("success"):
                    show_snackbar(self._page, "Animal permanently deleted!")
                    self._refresh_content()
                else:
                    show_snackbar(self._page, "Failed to delete animal", error=True)
            
            create_permanent_delete_dialog(
                self._page,
                item_type="animal",
                item_name=name,
                on_confirm=on_confirm,
            )
        
        # Photo element
        if photo_b64:
            photo_element = ft.Image(
                src_base64=photo_b64,
                width=60,
                height=60,
                fit=ft.ImageFit.COVER,
                border_radius=8,
            )
        else:
            photo_element = ft.Container(
                content=ft.Icon(ft.Icons.PETS, color=ft.Colors.GREY_400, size=30),
                width=60,
                height=60,
                bgcolor=ft.Colors.GREY_200,
                border_radius=8,
                alignment=ft.alignment.center,
            )
        
        # Action buttons
        actions = [
            ft.IconButton(
                icon=ft.Icons.RESTORE,
                icon_color=ft.Colors.TEAL_600,
                tooltip="Restore",
                on_click=handle_restore,
            ),
        ]
        
        if is_removed:
            actions.append(
                ft.IconButton(
                    icon=ft.Icons.DELETE_FOREVER,
                    icon_color=ft.Colors.RED_600,
                    tooltip="Delete Forever",
                    on_click=handle_permanent_delete,
                ),
            )
        
        breed = animal.get('breed', '')
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
                        bgcolor=badge_color,
                        border_radius=4,
                        padding=ft.padding.symmetric(horizontal=8, vertical=2),
                    ),
                ], spacing=4, expand=True),
                ft.Row(actions, spacing=0),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=16,
            bgcolor=ft.Colors.WHITE,
            border_radius=8,
            border=ft.border.all(1, ft.Colors.GREY_300),
        )


__all__ = ["HiddenItemsPage"]
