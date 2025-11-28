"""Page displaying animals available for adoption."""
from __future__ import annotations
from typing import Optional, List, Dict

import app_config
from services.animal_service import AnimalService
from services.photo_service import load_photo
from components import (
    create_user_sidebar, create_gradient_background,
    create_page_title, create_animal_card
)


class AvailableAdoptionPage:
    def __init__(self, db_path: Optional[str] = None) -> None:
        self.animal_service = AnimalService(db_path or app_config.DB_PATH)
        self._all_animals: List[Dict] = []

    def build(self, page) -> None:
        try:
            import flet as ft
        except Exception as exc:
            raise RuntimeError("Flet must be installed to build the UI") from exc

        page.title = "Available for Adoption"

        # Get user info from session
        user_name = page.session.get("user_name") or "User"

        # Create sidebar
        sidebar = create_user_sidebar(page, user_name)

        # Fetch adoptable animals (only healthy/ready animals)
        self._all_animals = self.animal_service.get_adoptable_animals() or []

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
        if self._all_animals:
            for animal in self._all_animals:
                animal_cards.append(create_card_for_animal(animal))
        else:
            animal_cards.append(
                ft.Container(
                    ft.Column([
                        ft.Icon(ft.Icons.PETS, size=64, color=ft.Colors.GREY_400),
                        ft.Text("No animals available for adoption", size=16, color=ft.Colors.BLACK54),
                    ], horizontal_alignment="center", spacing=10),
                    padding=40,
                    alignment=ft.alignment.center,
                )
            )

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

