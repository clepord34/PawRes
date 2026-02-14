"""Page displaying animals available for adoption.

Uses AnimalState for state-driven data flow, ensuring consistency
with the application's state management pattern.
"""
from __future__ import annotations
from typing import Optional

import app_config
from state import get_app_state
from services.photo_service import load_photo
from components import (
    create_user_sidebar, create_gradient_background,
    create_page_title, create_animal_card, create_empty_state,
    show_page_loading, finish_page_loading,
    is_mobile, create_responsive_layout, responsive_padding,
    create_user_drawer,
)


class AvailableAdoptionPage:
    """Page for browsing and selecting animals available for adoption.
    
    Uses AnimalState for reactive data management.
    """
    
    def __init__(self, db_path: Optional[str] = None) -> None:
        self._db_path = db_path or app_config.DB_PATH
        self._app_state = get_app_state(self._db_path)
        self.current_search = ""  # Track search query for filtering
        self._species_filter = "all"  # Track species filter
        self._animal_cards_container = None  # Store reference to cards container

    def build(self, page) -> None:
        try:
            import flet as ft
        except Exception as exc:
            raise RuntimeError("Flet must be installed to build the UI") from exc

        page.title = "Available for Adoption"

        user_name = page.session.get("user_name") or "User"

        _mobile = is_mobile(page)
        sidebar = create_user_sidebar(page, user_name, current_route=page.route)
        drawer = create_user_drawer(page, current_route=page.route) if _mobile else None
        _gradient_ref = show_page_loading(page, None if _mobile else sidebar, "Loading animals...")
        sidebar = create_user_sidebar(page, user_name, current_route=page.route)

        self._app_state.animals.load_adoptable_animals()
        animals = self._app_state.animals.animals

        if self._species_filter != "all":
            animals = [a for a in animals if (a.get("species", "Unknown") or "Unknown") == self._species_filter]

        search_query = self.current_search.lower().strip()
        if search_query:
            animals = [a for a in animals
                      if search_query in (a.get("name", "Unknown").lower() or "")
                      or search_query in (a.get("breed", "") or "").lower()]

        def create_card_for_animal(animal):
            aid = animal.get("id")
            photo_base64 = load_photo(animal.get("photo"))
            return create_animal_card(
                animal_id=aid,
                name=animal.get("name", "Unknown"),
                species=animal.get("species", "Unknown"),
                age=animal.get("age", 0),
                status=animal.get("status", "unknown"),
                photo_base64=photo_base64,
                on_adopt=lambda e, id=aid: self._on_apply(page, id),
                is_admin=False,
                show_adopt_button=True,
                breed=animal.get("breed"),
            )

        animal_cards = []
        if animals:
            for animal in animals:
                animal_cards.append(create_card_for_animal(animal))
        else:
            animal_cards.append(create_empty_state(
                message="No animals available for adoption",
                icon=ft.Icons.PETS,
                padding=40
            ))
        
        self._animal_cards_container = ft.ResponsiveRow(
            [ft.Container(c, col={"xs": 12, "sm": 6, "md": 4, "lg": 3}) for c in animal_cards],
            spacing=15,
            run_spacing=15,
        )

        # Main content area
        main_content = ft.Container(
            ft.Column([
                # Page title
                create_page_title("Available for Adoption"),
                ft.Container(
                    ft.Row([
                        # Species filter dropdown
                        ft.Dropdown(
                            hint_text="Filter by Species",
                            width=180,
                            value=self._species_filter,
                            options=[
                                ft.dropdown.Option("all", text="All Species")
                            ] + [ft.dropdown.Option(s, text=s) for s in sorted(set(a.get("species", "Unknown") for a in self._app_state.animals.animals))],
                            on_change=lambda e: self._on_species_filter(page, e.control.value),
                            border_radius=8,
                        ),
                        # Search field
                        ft.TextField(
                            hint_text="Search by animal name or breed...",
                            prefix_icon=ft.Icons.SEARCH,
                            width=300,
                            value=self.current_search,
                            on_change=lambda e: self._on_search(page, e.control.value),
                        ),
                    ], spacing=10),
                    padding=ft.padding.symmetric(horizontal=20, vertical=10),
                    border_radius=12,
                ),
                # Animal cards grid
                ft.Container(
                    self._animal_cards_container,
                    padding=20,
                    bgcolor=ft.Colors.WHITE,
                    border_radius=12,
                    shadow=ft.BoxShadow(blur_radius=15, spread_radius=2, color=ft.Colors.BLACK12, offset=(0, 3)),
                ),
            ], spacing=0, scroll=ft.ScrollMode.AUTO, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            expand=True,
            padding=responsive_padding(page),
        )

        # Layout with sidebar
        layout = create_responsive_layout(page, sidebar, main_content, drawer, title="Available Adoption")

        finish_page_loading(page, _gradient_ref, layout)

    def _on_apply(self, page, animal_id: int) -> None:
        # navigate to adoption form with query param
        page.go(f"/adoption_form?animal_id={animal_id}")

    def _on_species_filter(self, page, species: str) -> None:
        """Handle species filter change - rebuild page with filter applied."""
        self._species_filter = species
        self.build(page)

    def _on_search(self, page, search_query: str) -> None:
        """Handle search query change - update cards without full rebuild."""
        import flet as ft
        self.current_search = search_query
        
        # Re-filter animals
        self._app_state.animals.load_adoptable_animals()
        animals = self._app_state.animals.animals
        
        if self._species_filter != "all":
            animals = [a for a in animals if (a.get("species", "Unknown") or "Unknown") == self._species_filter]
        
        search_lower = search_query.lower().strip()
        if search_lower:
            animals = [a for a in animals
                      if search_lower in (a.get("name", "Unknown").lower() or "")
                      or search_lower in (a.get("breed", "") or "").lower()]
        
        # Rebuild animal cards
        animal_cards = []
        if animals:
            for animal in animals:
                aid = animal.get("id")
                photo_base64 = load_photo(animal.get("photo"))
                animal_cards.append(create_animal_card(
                    animal_id=aid,
                    name=animal.get("name", "Unknown"),
                    species=animal.get("species", "Unknown"),
                    age=animal.get("age", 0),
                    status=animal.get("status", "unknown"),
                    photo_base64=photo_base64,
                    on_adopt=lambda e, id=aid: self._on_apply(page, id),
                    is_admin=False,
                    show_adopt_button=True,
                    breed=animal.get("breed"),
                ))
        else:
            animal_cards.append(create_empty_state(
                message="No animals found",
                icon=ft.Icons.PETS,
                padding=40
            ))
        
        if self._animal_cards_container:
            self._animal_cards_container.controls = animal_cards
            self._animal_cards_container.update()


__all__ = ["AvailableAdoptionPage"]

