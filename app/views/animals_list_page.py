"""Animals list page with role-based actions."""
from __future__ import annotations

from typing import Any, List, Optional

import app_config
from services.animal_service import AnimalService
from services.photo_service import load_photo
from components import create_admin_sidebar, create_user_sidebar, create_gradient_background


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

        # Create animal cards
        def create_animal_card(animal):
            aid = animal.get("id")
            name = animal.get("name", "Unknown")
            species = animal.get("species", "")
            age = animal.get("age", 0)
            status = animal.get("status", "Unknown")
            
            # Status color mapping
            status_colors = {
                "healthy": ft.Colors.GREEN_600,
                "recovering": ft.Colors.ORANGE_600,
                "injured": ft.Colors.RED_600,
            }
            status_color = status_colors.get(status.lower(), ft.Colors.GREY_600)

            # Animal image - use photo if available, otherwise placeholder
            # load_photo handles both filename and legacy base64 formats
            photo_base64 = load_photo(animal.get('photo'))
            if photo_base64:
                animal_image = ft.Container(
                    content=ft.Image(
                        src_base64=photo_base64,
                        width=130,
                        height=130,
                        fit=ft.ImageFit.COVER,
                        border_radius=8,
                    ),
                    width=130,
                    height=130,
                    border_radius=8,
                )
            else:
                animal_image = ft.Container(
                    width=130,
                    height=130,
                    bgcolor=ft.Colors.GREY_300,
                    border_radius=8,
                    alignment=ft.alignment.center,
                )

            return ft.Container(
                ft.Column([
                    # Image
                    animal_image,
                    ft.Container(height=10),
                    # Animal info
                    ft.Text(f"{name}, {age}yrs old", size=14, weight="bold", color=ft.Colors.BLACK87),
                    ft.Text(species.capitalize(), size=12, color=ft.Colors.BLACK54),
                    ft.Text(status.capitalize(), size=12, color=status_color, weight="w500"),
                    ft.Container(height=8),
                    # Action buttons (only for admin)
                    ft.Row([
                        ft.ElevatedButton(
                            "Adopt",
                            width=120,
                            height=35,
                            on_click=lambda e, id=aid: page.go(f"/adoption_form?animal_id={id}"),
                            style=ft.ButtonStyle(
                                bgcolor=ft.Colors.TEAL_400,
                                color=ft.Colors.WHITE,
                                shape=ft.RoundedRectangleBorder(radius=20),
                                text_style=ft.TextStyle(size=12),
                            )
                        ),
                    ], spacing=8, alignment=ft.MainAxisAlignment.CENTER) if not is_admin else ft.Row([
                        ft.ElevatedButton(
                            "Edit",
                            width=60,
                            height=35,
                            on_click=lambda e, id=aid: self._on_edit(page, id),
                            style=ft.ButtonStyle(
                                bgcolor=ft.Colors.TEAL_600,
                                color=ft.Colors.WHITE,
                                shape=ft.RoundedRectangleBorder(radius=6),
                                text_style=ft.TextStyle(size=12),
                            )
                        ),
                        ft.ElevatedButton(
                            "Delete",
                            width=60,
                            height=35,
                            on_click=lambda e, id=aid: self.delete_animal(id),
                            style=ft.ButtonStyle(
                                bgcolor=ft.Colors.RED_400,
                                color=ft.Colors.WHITE,
                                shape=ft.RoundedRectangleBorder(radius=6),
                                text_style=ft.TextStyle(size=12),
                            )
                        ),
                    ], spacing=8, alignment=ft.MainAxisAlignment.CENTER),
                ], horizontal_alignment="center", spacing=0),
                width=180,
                padding=15,
                bgcolor=ft.Colors.WHITE,
                border_radius=12,
                border=ft.border.all(1, ft.Colors.GREY_300),
                shadow=ft.BoxShadow(blur_radius=8, spread_radius=1, color=ft.Colors.BLACK12, offset=(0, 2)),
            )

        # Create grid of animal cards
        animal_cards = []
        if animals:
            for animal in animals:
                animal_cards.append(create_animal_card(animal))
        else:
            animal_cards.append(ft.Text("No animals found", size=16, color=ft.Colors.BLACK54))

        # Main content area
        main_content = ft.Container(
            ft.Column([
                # Page title
                ft.Container(
                    ft.Text("Animal List", size=28, weight="bold", color=ft.Colors.with_opacity(0.6, ft.Colors.BLACK)),
                    padding=ft.padding.only(bottom=20),
                    alignment=ft.alignment.center,
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
                self.page.snack_bar = ft.SnackBar(
                    ft.Text("✓ Animal deleted!", color=ft.Colors.WHITE),
                    bgcolor=ft.Colors.GREEN_700
                )
                self.page.snack_bar.open = True
                
                # Rebuild the entire page to show updated list
                print("Rebuilding page...")
                self.build(self.page, user_role=self.user_role)
                print("Delete complete!\n")
            else:
                self.page.snack_bar = ft.SnackBar(
                    ft.Text("Failed to delete", color=ft.Colors.WHITE),
                    bgcolor=ft.Colors.RED_700
                )
                self.page.snack_bar.open = True
                self.page.update()
                
        except Exception as ex:
            print(f"ERROR: {ex}")
            import traceback
            traceback.print_exc()
            self.page.snack_bar = ft.SnackBar(
                ft.Text(f"Error: {str(ex)}", color=ft.Colors.WHITE),
                bgcolor=ft.Colors.RED_700
            )
            self.page.snack_bar.open = True
            self.page.update()


__all__ = ["AnimalsListPage"]

