"""Animals list page with role-based actions.

Uses AnimalState for state-driven data flow, ensuring consistency
with the application's state management pattern.
"""
from __future__ import annotations

import csv
from datetime import datetime
from typing import Callable, Optional

import app_config
from state import get_app_state
from services.photo_service import load_photo
from services.rescue_service import RescueService
from components import (
    create_admin_sidebar, create_user_sidebar, create_gradient_background,
    create_page_title, create_animal_card, create_empty_state, show_snackbar,
    create_archive_dialog, create_remove_dialog, create_action_button
)


class AnimalsListPage:
    """Page displaying list of animals with filtering and role-based actions.
    
    Uses AnimalState for reactive data management, subscribing to state
    changes for automatic UI updates.
    """
    
    def __init__(self, db_path: Optional[str] = None) -> None:
        self._db_path = db_path or app_config.DB_PATH
        self._app_state = get_app_state(self._db_path)
        self._rescue_service = RescueService(self._db_path)
        self.page = None  # Store page reference
        self.user_role = "user"  # Store user role
        self.current_filter = "all"  # Current filter state
        self._unsubscribe: Optional[Callable] = None

    def build(self, page, user_role: str = "user", filter_status: str = "all") -> None:
        try:
            import flet as ft
        except Exception as exc:
            raise RuntimeError("Flet must be installed to build the UI") from exc

        # Store references
        self.page = page
        self.user_role = user_role
        self.current_filter = filter_status
        page.title = "Animals List"

        is_admin = user_role == "admin"
        
        # Get user info from session
        user_name = page.session.get("user_name") or "User"

        # Create sidebar based on user role using components
        if is_admin:
            sidebar = create_admin_sidebar(page, current_route=page.route)
        else:
            sidebar = create_user_sidebar(page, user_name, current_route=page.route)

        # Load animals through state manager (ensures data is fresh)
        # Admin sees active (non-hidden) animals only in main list
        if is_admin:
            self._app_state.animals.load_active_animals()
        else:
            self._app_state.animals.load_animals()
        
        # Get animals from state
        all_animals = self._app_state.animals.animals
        
        # Filter out 'processing' animals for non-admin users
        # These are newly rescued animals awaiting admin setup
        if not is_admin:
            all_animals = [a for a in all_animals 
                         if (a.get("status") or "").lower() != app_config.AnimalStatus.PROCESSING]

        # Apply filter
        if filter_status == "all":
            animals = all_animals
        elif filter_status == "healthy":
            animals = [a for a in all_animals if (a.get("status") or "").lower() in app_config.HEALTHY_STATUSES]
        elif filter_status == "recovering":
            animals = [a for a in all_animals if (a.get("status") or "").lower() == "recovering"]
        elif filter_status == "injured":
            animals = [a for a in all_animals if (a.get("status") or "").lower() == "injured"]
        elif filter_status == "adopted":
            animals = [a for a in all_animals if (a.get("status") or "").lower() == "adopted"]
        elif filter_status == "rescued":
            animals = [a for a in all_animals if a.get("rescue_mission_id") is not None]
        elif filter_status == "processing":
            animals = [a for a in all_animals if (a.get("status") or "").lower() == app_config.AnimalStatus.PROCESSING]
        else:
            animals = all_animals

        # Create filter dropdown - admin gets extra "Needs Setup" option
        def on_filter_change(e):
            new_filter = e.control.value
            self.build(page, user_role=user_role, filter_status=new_filter)

        filter_options = [
            ft.dropdown.Option("all", text="All Animals"),
            ft.dropdown.Option("healthy", text="Healthy"),
            ft.dropdown.Option("recovering", text="Recovering"),
            ft.dropdown.Option("injured", text="Injured"),
            ft.dropdown.Option("adopted", text="Adopted"),
            ft.dropdown.Option("rescued", text="🧡 Recently Rescued"),
        ]
        
        # Add "Needs Setup" filter for admin only
        if is_admin:
            filter_options.append(ft.dropdown.Option("processing", text="⏳ Needs Setup"))
        
        filter_dropdown = ft.Dropdown(
            hint_text="Filter by Status",
            width=180,
            value=filter_status,
            options=filter_options,
            on_change=on_filter_change,
            border_radius=8,
        )
        
        # Species filter dropdown
        species_list = list(set(a.get("species", "Unknown") for a in all_animals if a.get("species")))
        species_list.sort()
        species_options = [ft.dropdown.Option("all", text="All Species")] + [
            ft.dropdown.Option(s, text=s) for s in species_list
        ]
        
        species_filter = ft.Dropdown(
            hint_text="Filter by Species",
            width=160,
            value="all",
            options=species_options,
            on_change=lambda e: self._on_species_filter(page, user_role, filter_status, e.control.value),
            border_radius=8,
        )
        
        # Store species filter value for export
        self._species_filter = getattr(self, '_species_filter_value', 'all')
        
        # Refresh button
        refresh_btn = ft.IconButton(
            ft.Icons.REFRESH,
            tooltip="Refresh list",
            icon_color=ft.Colors.TEAL_600,
            on_click=lambda e: self.build(page, user_role=user_role, filter_status=filter_status),
        )
        
        # Export button (admin only)
        export_btn = create_action_button(
            "Export",
            on_click=lambda e: self._export_csv(animals),
            icon=ft.Icons.DOWNLOAD,
            width=110,
        ) if is_admin else ft.Container()
        
        # Add Animal button (admin only) - improved styling
        add_animal_btn = ft.Container(
            ft.Row([
                ft.Icon(ft.Icons.ADD, size=18, color=ft.Colors.WHITE),
                ft.Text("Add Animal", size=14, weight="w600", color=ft.Colors.WHITE),
            ], spacing=6),
            padding=ft.padding.symmetric(horizontal=16, vertical=10),
            bgcolor=ft.Colors.TEAL_600,
            border_radius=8,
            on_click=lambda e: page.go("/add_animal"),
            on_hover=lambda e: self._on_btn_hover(e),
            ink=True,
            tooltip="Add a new animal",
        ) if is_admin else ft.Container()

        # Create animal cards using component
        def create_card_for_animal(animal):
            aid = animal.get("id")
            aname = animal.get("name", "Unknown")
            # Load photo (handles both filename and legacy base64)
            photo_base64 = load_photo(animal.get("photo"))
            # Check if animal came from a rescue mission and get details
            rescue_mission_id = animal.get("rescue_mission_id")
            rescue_info = None
            if rescue_mission_id:
                mission = self._rescue_service.get_mission_by_id(rescue_mission_id)
                if mission:
                    rescue_info = {
                        "mission_id": rescue_mission_id,
                        "location": mission.get("location", "Unknown"),
                        "date": mission.get("mission_date", ""),
                        "reporter": mission.get("reporter_name", ""),
                        "contact": mission.get("reporter_phone", ""),
                        "urgency": mission.get("urgency", ""),
                        "description": mission.get("notes", ""),
                        "source": "Emergency" if mission.get("user_id") is None else "User",
                    }
            is_rescued = rescue_mission_id is not None
            
            # Archive/Remove handlers for admin
            def handle_archive(animal_id):
                def on_confirm(note):
                    success = self._app_state.animals.archive_animal(
                        animal_id,
                        self._app_state.auth.user_id,
                        note
                    )
                    if success:
                        show_snackbar(page, "Animal archived")
                        self.build(page, user_role=user_role, filter_status=self.current_filter)
                    else:
                        show_snackbar(page, "Failed to archive animal", error=True)
                
                create_archive_dialog(
                    page,
                    item_type="animal",
                    item_name=aname,
                    on_confirm=on_confirm,
                )
            
            def handle_remove(animal_id):
                def on_confirm(reason):
                    result = self._app_state.animals.remove_animal(
                        animal_id,
                        self._app_state.auth.user_id,
                        reason
                    )
                    if result.get("success"):
                        msg = "Animal removed"
                        if result.get("adoptions_affected", 0) > 0:
                            msg += f" ({result['adoptions_affected']} pending adoptions auto-denied)"
                        show_snackbar(page, msg)
                        self.build(page, user_role=user_role, filter_status=self.current_filter)
                    else:
                        show_snackbar(page, "Failed to remove animal", error=True)
                
                create_remove_dialog(
                    page,
                    item_type="animal",
                    item_name=aname,
                    on_confirm=on_confirm,
                )
            
            return create_animal_card(
                animal_id=aid,
                name=aname,
                species=animal.get("species", "Unknown"),
                age=animal.get("age", 0),
                status=animal.get("status", "unknown"),
                photo_base64=photo_base64,
                on_adopt=lambda e, id=aid: page.go(f"/adoption_form?animal_id={id}"),
                on_edit=lambda e, id=aid: self._on_edit(page, id) if is_admin else None,
                on_archive=handle_archive if is_admin else None,
                on_remove=handle_remove if is_admin else None,
                is_admin=is_admin,
                show_adopt_button=not is_admin,  # Only show adopt button for users
                is_rescued=is_rescued,
                rescue_info=rescue_info,
            )

        # Create grid of animal cards
        animal_cards = []
        if animals:
            for animal in animals:
                animal_cards.append(create_card_for_animal(animal))
        else:
            animal_cards.append(create_empty_state(
                message="No animals found",
                icon=ft.Icons.PETS,
                padding=40
            ))

        # Main content area
        main_content = ft.Container(
            ft.Column([
                # Page title row with Add Animal button
                ft.Row([
                    create_page_title("Animal List"),
                    ft.Container(expand=True),
                    add_animal_btn,
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                
                # Filter and action row
                ft.Container(
                    ft.Row([
                        filter_dropdown,
                        species_filter,
                        ft.Container(expand=True),
                        ft.Text(f"Showing {len(animals)} animal(s)", size=13, color=ft.Colors.BLACK54),
                        refresh_btn,
                        export_btn,
                    ], alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.CENTER, spacing=12),
                    padding=ft.padding.only(bottom=15, top=5),
                ),
                
                # Animal cards grid
                ft.Container(
                    ft.Row(
                        animal_cards,
                        wrap=True,
                        spacing=15,
                        run_spacing=15,
                        alignment=ft.MainAxisAlignment.START,
                    ),
                    padding=20,
                    bgcolor=ft.Colors.WHITE,
                    border_radius=12,
                    shadow=ft.BoxShadow(blur_radius=15, spread_radius=2, color=ft.Colors.BLACK12, offset=(0, 3)),
                ),
            ], spacing=0, scroll=ft.ScrollMode.AUTO, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            expand=True,
            padding=30,
        )

        # Layout with or without sidebar
        if sidebar:
            layout = ft.Row([
                sidebar,
                main_content,
            ], spacing=0, expand=True, vertical_alignment=ft.CrossAxisAlignment.START)
        else:
            layout = main_content

        page.controls.clear()
        page.add(create_gradient_background(layout))
        page.update()

    # ---- actions ----
    def _on_edit(self, page, animal_id: int) -> None:
        # navigate to edit page with query param
        page.go(f"/edit_animal?id={animal_id}")
    
    def _on_species_filter(self, page, user_role: str, status_filter: str, species: str) -> None:
        """Handle species filter change - rebuild with species filter applied."""
        self._species_filter_value = species
        self.build(page, user_role=user_role, filter_status=status_filter)
    
    def _on_btn_hover(self, e) -> None:
        """Handle button hover effect."""
        import flet as ft
        if e.data == "true":
            e.control.bgcolor = ft.Colors.TEAL_700
        else:
            e.control.bgcolor = ft.Colors.TEAL_600
        e.control.update()
    
    def _export_csv(self, animals: list) -> None:
        """Export current animal list to CSV."""
        if not animals:
            show_snackbar(self.page, "No animals to export", error=True)
            return
        
        try:
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"animals_export_{timestamp}.csv"
            filepath = app_config.STORAGE_DIR / "data" / "exports" / filename
            
            # Ensure exports directory exists
            filepath.parent.mkdir(parents=True, exist_ok=True)
            
            # Write CSV
            fieldnames = ["id", "name", "species", "breed", "age", "status", "description", "created_at"]
            with open(filepath, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for animal in animals:
                    writer.writerow({
                        "id": animal.get("id", ""),
                        "name": animal.get("name", ""),
                        "species": animal.get("species", ""),
                        "breed": animal.get("breed", ""),
                        "age": animal.get("age", ""),
                        "status": animal.get("status", ""),
                        "description": animal.get("description", ""),
                        "created_at": animal.get("created_at", ""),
                    })
            
            show_snackbar(self.page, f"Exported {len(animals)} animals to {filename}")
            
        except Exception as e:
            show_snackbar(self.page, f"Export failed: {e}", error=True)


__all__ = ["AnimalsListPage"]

