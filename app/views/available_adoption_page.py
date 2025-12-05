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
    create_page_title, create_animal_card, create_empty_state
)


class AvailableAdoptionPage:
    """Page for browsing and selecting animals available for adoption.
    
    Uses AnimalState for reactive data management.
    """
    
    def __init__(self, db_path: Optional[str] = None) -> None:
        self._db_path = db_path or app_config.DB_PATH
        self._app_state = get_app_state(self._db_path)

    def build(self, page) -> None:
        try:
            import flet as ft
        except Exception as exc:
            raise RuntimeError("Flet must be installed to build the UI") from exc

        page.title = "Available for Adoption"

        # Get user info from session
        user_name = page.session.get("user_name") or "User"

        # Create sidebar
        sidebar = create_user_sidebar(page, user_name, current_route=page.route)

        # Load adoptable animals through state manager
        self._app_state.animals.load_adoptable_animals()
        animals = self._app_state.animals.animals

        # Create animal cards
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
            )

        # Create grid of animal cards
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

        # Main content area
        main_content = ft.Container(
            ft.Column([
                # Page title
                create_page_title("Available for Adoption"),
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

        # Layout with sidebar
        layout = ft.Row([
            sidebar,
            main_content,
        ], spacing=0, expand=True, vertical_alignment=ft.CrossAxisAlignment.START)

        page.controls.clear()
        page.add(create_gradient_background(layout))
        page.update()

    def _on_apply(self, page, animal_id: int) -> None:
        # navigate to adoption form with query param
        page.go(f"/adoption_form?animal_id={animal_id}")


__all__ = ["AvailableAdoptionPage"]

