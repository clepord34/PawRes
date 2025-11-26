"""Form page for adding new animals to the system."""
from __future__ import annotations

from typing import Optional

from services.animal_service import AnimalService
import app_config
from components import create_header, create_photo_upload_widget, create_action_button, create_gradient_background


class AddAnimalPage:
    def __init__(self, db_path: Optional[str] = None) -> None:
        self.service = AnimalService(db_path or app_config.DB_PATH)
        self._type_dropdown = None
        self._name_field = None
        self._age_field = None
        self._health_dropdown = None
        self._photo_widget = None  # Store the photo widget instance
        self._photo_base64 = None  # Store the base64 data directly

    def build(self, page) -> None:
        """Build the add animal form on the provided `flet.Page`."""
        try:
            import flet as ft
        except Exception as exc:
            raise RuntimeError("Flet is required") from exc

        page.title = "Add Animal"

        # Header with logo - smaller and gray
        header = create_header(title="Add Animal", icon_size=50, title_size=28, subtitle="", padding=ft.padding.only(bottom=20))

        # Photo upload section using component
        self._photo_widget = create_photo_upload_widget(page)
        photo_container = self._photo_widget.build()

        # Dropdown and fields with updated styling
        self._type_dropdown = ft.Dropdown(
            hint_text="Pick Animal",
            options=[ft.dropdown.Option("dog"), ft.dropdown.Option("cat")],
            width=280,
            bgcolor=ft.Colors.WHITE,
            border_color=ft.Colors.GREY_300,
            focused_border_color=ft.Colors.TEAL_400,
            prefix_icon=ft.Icons.PETS,
        )
        
        self._name_field = ft.TextField(
            hint_text="Enter animal name...",
            width=280,
            height=50,
            color=ft.Colors.BLACK,
            bgcolor=ft.Colors.WHITE,
            border_color=ft.Colors.GREY_300,
            focused_border_color=ft.Colors.TEAL_400,
            text_size=14,
            content_padding=ft.padding.all(12),
        )
        
        self._age_field = ft.TextField(
            hint_text="Enter animal Age...",
            keyboard_type=ft.KeyboardType.NUMBER,
            width=280,
            height=50,
            color=ft.Colors.BLACK,
            bgcolor=ft.Colors.WHITE,
            border_color=ft.Colors.GREY_300,
            focused_border_color=ft.Colors.TEAL_400,
            text_size=14,
            content_padding=ft.padding.all(12),
        )
        
        self._health_dropdown = ft.Dropdown(
            hint_text="Health Status",
            options=[
                ft.dropdown.Option("healthy"),
                ft.dropdown.Option("recovering"),
                ft.dropdown.Option("injured"),
            ],
            width=280,
            bgcolor=ft.Colors.WHITE,
            border_color=ft.Colors.GREY_300,
            focused_border_color=ft.Colors.TEAL_400,
            prefix_icon=ft.Icons.FAVORITE,
        )

        # Buttons
        back_btn = create_action_button(
            "Back to Dashboard",
            on_click=lambda e: page.go("/admin"),
            width=130,
            height=45,
            outlined=True,
            bgcolor=ft.Colors.TEAL_600
        )
        
        submit_btn = create_action_button(
            "Submit",
            on_click=lambda e: self._on_submit(page, e),
            width=130,
            height=45
        )

        # Labels for fields
        type_label = ft.Text("Choose what type", size=13, color=ft.Colors.BLACK54)
        name_label = ft.Text("Animal Name", size=13, color=ft.Colors.BLACK54)
        age_label = ft.Text("Age", size=13, color=ft.Colors.BLACK54)
        health_label = ft.Text("Health Status", size=13, color=ft.Colors.BLACK54)

        # Card with form
        card = ft.Container(
            ft.Column([
                photo_container,
                ft.Container(type_label, width=280, alignment=ft.alignment.center_left),
                ft.Container(height=5),
                self._type_dropdown,
                ft.Container(height=10),
                ft.Container(name_label, width=280, alignment=ft.alignment.center_left),
                ft.Container(height=5),
                self._name_field,
                ft.Container(height=10),
                ft.Container(age_label, width=280, alignment=ft.alignment.center_left),
                ft.Container(height=5),
                self._age_field,
                ft.Container(height=10),
                ft.Container(health_label, width=280, alignment=ft.alignment.center_left),
                ft.Container(height=5),
                self._health_dropdown,
                ft.Container(height=20),
                ft.Row([back_btn, submit_btn], alignment="center", spacing=15),
            ], horizontal_alignment="center", spacing=0),
            padding=35,
            alignment=ft.alignment.center,
            width=400,
            bgcolor=ft.Colors.WHITE,
            border_radius=16,
            shadow=ft.BoxShadow(
                blur_radius=30, 
                spread_radius=0, 
                color=ft.Colors.with_opacity(0.15, ft.Colors.BLACK), 
                offset=(0, 10)
            ),
        )

        # Main layout
        layout = ft.Column([header, card], alignment="center", horizontal_alignment="center", expand=True, scroll=ft.ScrollMode.AUTO)

        page.controls.clear()
        page.add(create_gradient_background(layout))
        page.update()

    def _on_submit(self, page, e) -> None:
        try:
            import flet as ft
        except Exception:
            return

        animal_type = (self._type_dropdown.value or "").strip()
        name = (self._name_field.value or "").strip()
        age_str = (self._age_field.value or "").strip()
        health_status = (self._health_dropdown.value or "").strip()

        if not animal_type or not name or not age_str or not health_status:
            page.snack_bar = ft.SnackBar(ft.Text("All fields are required"))
            page.snack_bar.open = True
            page.update()
            return

        try:
            age = int(age_str)
            if age < 0:
                raise ValueError("Age must be non-negative")
        except ValueError:
            page.snack_bar = ft.SnackBar(ft.Text("Age must be a valid non-negative number"))
            page.snack_bar.open = True
            page.update()
            return

        try:
            # Save photo with animal name (deferred save)
            photo_filename = None
            if self._photo_widget:
                photo_filename = self._photo_widget.save_with_name(name)

            # Insert into DB via AnimalService
            animal_id = self.service.add_animal(
                name=name,
                type=animal_type,
                age=age,
                health_status=health_status,
                photo=photo_filename,  # Stores filename like 'pipay_20251125_abc1.jpg'
            )

            page.snack_bar = ft.SnackBar(ft.Text(f"Animal added successfully (ID: {animal_id})"))
            page.snack_bar.open = True
            page.update()
            page.go("/admin")
        except Exception as exc:
            import traceback
            traceback.print_exc()
            page.snack_bar = ft.SnackBar(ft.Text(f"Error: {str(exc)}"))
            page.snack_bar.open = True
            page.update()


__all__ = ["AddAnimalPage"]

