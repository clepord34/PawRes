"""Form page for adding new animals to the system."""
from __future__ import annotations

from typing import Optional

from services.animal_service import AnimalService
import app_config
from components import (
    create_header, create_photo_upload_widget, create_action_button, create_gradient_background,
    create_form_text_field, create_form_dropdown, create_form_label, show_snackbar
)


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
        self._type_dropdown = create_form_dropdown(
            hint_text="Pick Animal",
            options=["dog", "cat"],
            leading_icon=ft.Icons.PETS,
        )
        
        self._name_field = create_form_text_field(hint_text="Enter animal name...")
        
        self._age_field = create_form_text_field(
            hint_text="Enter animal Age...",
            keyboard_type=ft.KeyboardType.NUMBER,
        )
        
        self._health_dropdown = create_form_dropdown(
            hint_text="Health Status",
            options=["healthy", "recovering", "injured"],
            leading_icon=ft.Icons.FAVORITE,
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
        type_label = create_form_label("Choose what type")
        name_label = create_form_label("Animal Name")
        age_label = create_form_label("Age")
        health_label = create_form_label("Health Status")

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
            show_snackbar(page, "All fields are required")
            return

        try:
            age = int(age_str)
            if age < 0:
                raise ValueError("Age must be non-negative")
        except ValueError:
            show_snackbar(page, "Age must be a valid non-negative number")
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

            show_snackbar(page, f"Animal added successfully (ID: {animal_id})")
            page.go("/admin")
        except Exception as exc:
            import traceback
            traceback.print_exc()
            show_snackbar(page, f"Error: {str(exc)}", error=True)


__all__ = ["AddAnimalPage"]

