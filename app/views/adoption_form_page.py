"""Form page for submitting adoption applications."""
from __future__ import annotations
from typing import Optional

import app_config
from services.adoption_service import AdoptionService
from services.animal_service import AnimalService
from state import get_app_state
from components import create_page_header, create_content_card, create_action_button, create_gradient_background


class AdoptionFormPage:
    def __init__(self, db_path: Optional[str] = None) -> None:
        self.adoption_service = AdoptionService(db_path or app_config.DB_PATH)
        self.animal_service = AnimalService(db_path or app_config.DB_PATH)
        self._animal_dropdown: Optional[object] = None
        self._name_field: Optional[object] = None
        self._contact_field: Optional[object] = None
        self._reason_field: Optional[object] = None
        self._error_text: Optional[object] = None
        self._submit_btn: Optional[object] = None

    def build(self, page, animal_id: Optional[int] = None) -> None:
        try:
            import flet as ft
        except Exception as exc:
            raise RuntimeError("Flet must be installed to build the UI") from exc

        page.title = "Adoption Application"

        # Header with logo
        header = create_page_header("Paw Rescue")

        # fetch adoptable animals
        animals = self.animal_service.get_adoptable_animals() or []

        # animal dropdown
        animal_options = [ft.dropdown.Option(str(a.get("id")), text=a.get("name", "Unknown")) for a in animals]
        self._animal_dropdown = ft.Dropdown(
            label="Select Animal",
            width=350,
            options=animal_options,
            hint_text="Choose animal to adopt",
            bgcolor=ft.Colors.WHITE,
            border_color=ft.Colors.TEAL_300,
            color=ft.Colors.BLACK87,
        )

        # set dropdown to animal_id if provided
        if animal_id is not None:
            self._animal_dropdown.value = str(animal_id)

        # form fields
        self._name_field = ft.TextField(
            label="Your Name", 
            width=350,
            bgcolor=ft.Colors.WHITE,
            border_color=ft.Colors.TEAL_300,
            color=ft.Colors.BLACK87,
        )
        self._contact_field = ft.TextField(
            label="Contact Info (Phone/Email)", 
            width=350,
            bgcolor=ft.Colors.WHITE,
            border_color=ft.Colors.TEAL_300,
            color=ft.Colors.BLACK87,
        )
        self._reason_field = ft.TextField(
            label="Reason for Adoption", 
            multiline=True, 
            min_lines=3, 
            width=350,
            bgcolor=ft.Colors.WHITE,
            border_color=ft.Colors.TEAL_300,
            color=ft.Colors.BLACK87,
        )

        # error display
        self._error_text = ft.Text("", color=ft.Colors.RED, size=12)

        # submit and cancel buttons
        self._submit_btn = create_action_button(
            "Submit Application",
            on_click=lambda e: self._on_submit(page)
        )
        cancel_btn = create_action_button(
            "Cancel",
            on_click=lambda e: page.go("/available_adoption"),
            outlined=True,
            bgcolor=ft.Colors.TEAL_400
        )

        # Card container
        card = ft.Container(
            ft.Column([
                ft.Text("Adoption Application", size=22, weight="bold", color=ft.Colors.BLACK87),
                ft.Text("Fill in your details to adopt", size=12, color=ft.Colors.BLACK54),
                ft.Divider(height=12, color=ft.Colors.GREY_300),
                self._animal_dropdown,
                self._name_field,
                self._contact_field,
                self._reason_field,
                ft.Row([self._submit_btn, cancel_btn], spacing=12, alignment="center"),
                self._error_text,
            ], spacing=10, horizontal_alignment="center"),
            width=550,
            padding=25,
            bgcolor=ft.Colors.WHITE,
            border_radius=12,
            shadow=ft.BoxShadow(blur_radius=20, spread_radius=5, color=ft.Colors.BLACK12, offset=(0, 5)),
        )

        # Main layout
        layout = ft.Column([
            header,
            card
        ], horizontal_alignment="center", alignment="center", expand=True, spacing=10, scroll=ft.ScrollMode.AUTO)

        page.controls.clear()
        page.add(create_gradient_background(layout))
        page.update()

    def _validate_form(self) -> tuple[bool, str]:
        """Validate form fields. Return (is_valid, error_message)."""
        animal_id = (self._animal_dropdown.value or "").strip()
        name = (self._name_field.value or "").strip()
        contact = (self._contact_field.value or "").strip()
        reason = (self._reason_field.value or "").strip()

        if not animal_id:
            return False, "Please select an animal."
        if not name:
            return False, "Please enter your name."
        if not contact:
            return False, "Please enter contact information."
        if not reason:
            return False, "Please enter a reason for adoption."
        if len(reason) < 50:
            return False, "Reason must be at least 50 characters."

        return True, ""

    def _on_submit(self, page) -> None:
        """Validate and submit the form."""
        try:
            import flet as ft
        except Exception:
            raise RuntimeError("Flet is required for UI actions")

        # disable submit button while processing
        self._submit_btn.disabled = True
        page.update()

        # validate
        is_valid, error_msg = self._validate_form()
        if not is_valid:
            self._error_text.value = error_msg
            self._submit_btn.disabled = False
            page.update()
            return

        # clear error
        self._error_text.value = ""

        try:
            # extract form data
            animal_id = int(self._animal_dropdown.value)
            name = (self._name_field.value or "").strip()
            contact = (self._contact_field.value or "").strip()
            reason = (self._reason_field.value or "").strip()

            # Get user_id from centralized state management
            app_state = get_app_state()
            user_id = app_state.auth.user_id
            if not user_id:
                self._error_text.value = "Session expired. Please log in again."
                self._submit_btn.disabled = False
                page.update()
                return

            # submit adoption request
            request_id = self.adoption_service.submit_request(
                user_id=user_id,
                animal_id=animal_id,
                contact=contact,
                reason=reason,
                status="pending",
            )

            # show success
            page.snack_bar = ft.SnackBar(ft.Text("Application submitted successfully!"))
            page.snack_bar.open = True
            page.update()

            # navigate to check status
            page.go(f"/check_status?request_id={request_id}")

        except Exception as exc:
            self._error_text.value = f"Error: {str(exc)}"
            self._submit_btn.disabled = False
            page.update()


__all__ = ["AdoptionFormPage"]

