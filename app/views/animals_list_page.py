"""Animals list page with role-based actions."""
from __future__ import annotations

from typing import Any, List, Optional

import app_config
from services.animal_service import AnimalService
from services.photo_service import load_photo
from components import (
    create_admin_sidebar, create_user_sidebar, create_gradient_background,
    create_page_title, create_animal_card, show_snackbar
)


class AnimalsListPage:
    def __init__(self, db_path: Optional[str] = None) -> None:
        # AnimalService expects 'db' parameter, not 'db_path'
        self.animal_service = AnimalService(db=db_path or app_config.DB_PATH)
        self.page = None  # Store page reference
        self.user_role = "user"  # Store user role

    def build(self, page, user_role: str = "user") -> None:
        try:
            import flet as ft
        except Exception as exc:
            raise RuntimeError("Flet must be installed to build the UI") from exc

        # Store references
        self.page = page
        self.user_role = user_role
        page.title = "Animals List"

        is_admin = user_role == "admin"
        
        # Get user info from session
        user_name = page.session.get("user_name") or "User"

        # Create sidebar based on user role using components
        if is_admin:
            sidebar = create_admin_sidebar(page)
        else:
            sidebar = create_user_sidebar(page, user_name)

        # Get animals from database
        animals = self.animal_service.get_all_animals()

        # Create animal cards using component
        def create_card_for_animal(animal):
            aid = animal.get("id")
            # Load photo (handles both filename and legacy base64)
            photo_base64 = load_photo(animal.get("photo"))
            return create_animal_card(
                animal_id=aid,
                name=animal.get("name", "Unknown"),
                species=animal.get("species", "Unknown"),
                age=animal.get("age", 0),
                status=animal.get("status", "unknown"),
                photo_base64=photo_base64,
                on_adopt=lambda e, id=aid: page.go(f"/adoption_form?animal_id={id}"),
                on_edit=lambda e, id=aid: self._on_edit(page, id) if is_admin else None,
                on_delete=lambda e, id=aid: self.delete_animal(id) if is_admin else None,
                is_admin=is_admin,
            )

        # Create grid of animal cards
        animal_cards = []
        if animals:
            for animal in animals:
                animal_cards.append(create_card_for_animal(animal))
        else:
            animal_cards.append(ft.Text("No animals found", size=16, color=ft.Colors.BLACK54))

        # Main content area
        main_content = ft.Container(
            ft.Column([
                # Page title
                create_page_title("Animal List"),
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
        page.add(ft.Container(
            layout,
            expand=True,
            width=float('inf'),
            height=float('inf'),
            gradient=ft.LinearGradient(
                begin=ft.alignment.top_center,
                end=ft.alignment.bottom_center,
                colors=[ft.Colors.LIGHT_BLUE_50, ft.Colors.AMBER_50]
            )
        ))
        page.update()

    # ---- actions ----
    def _on_edit(self, page, animal_id: int) -> None:
        # navigate to edit page with query param
        page.go(f"/edit_animal?id={animal_id}")

    def delete_animal(self, animal_id: int) -> None:
        """Delete an animal directly (like todo app clear_clicked)."""
        import flet as ft
        
        print(f"\n{'='*60}")
        print(f"DELETING Animal ID: {animal_id}")
        print(f"Database: {self.animal_service.db.db_path}")
        print(f"{'='*60}")
        
        try:
            # Perform the delete
            success = self.animal_service.delete_animal(animal_id)
            print(f"Delete result: {success}")
            
            if success:
                # Show success message
                show_snackbar(self.page, "✓ Animal deleted!")
                
                # Rebuild the entire page to show updated list
                print("Rebuilding page...")
                self.build(self.page, user_role=self.user_role)
                print("Delete complete!\n")
            else:
                show_snackbar(self.page, "Failed to delete", error=True)
                
        except Exception as ex:
            print(f"ERROR: {ex}")
            import traceback
            traceback.print_exc()
            show_snackbar(self.page, f"Error: {str(ex)}", error=True)


__all__ = ["AnimalsListPage"]

