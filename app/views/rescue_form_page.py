"""Form page for submitting rescue mission requests."""
from __future__ import annotations
from typing import Optional

import app_config
from services.rescue_service import RescueService
from services.map_service import MapService
from state import get_app_state
from components import create_page_header, create_content_card, create_action_button, create_gradient_background


class RescueFormPage:
    def __init__(self, db_path: Optional[str] = None) -> None:
        self.rescue_service = RescueService(db_path or app_config.DB_PATH)
        self.map_service = MapService()
        self._type_dropdown: Optional[object] = None
        self._name_field: Optional[object] = None
        self._location_field: Optional[object] = None
        self._details_field: Optional[object] = None
        self._error_text: Optional[object] = None
        self._submit_btn: Optional[object] = None

    def build(self, page) -> None:
        try:
            import flet as ft
        except Exception as exc:
            raise RuntimeError("Flet must be installed to build the UI") from exc

        page.title = "Report Rescue Mission"

        # Header with logo
        header = create_page_header("Paw Rescue")        # animal type dropdown
        self._type_dropdown = ft.Dropdown(
            label="Animal Type",
            width=350,
            options=[ft.dropdown.Option("Dog"), ft.dropdown.Option("Cat"), ft.dropdown.Option("Other")],
            bgcolor=ft.Colors.WHITE,
            border_color=ft.Colors.TEAL_300,
            color=ft.Colors.BLACK87,
        )

        # form fields
        self._name_field = ft.TextField(
            label="Reporter Name", 
            width=350,
            bgcolor=ft.Colors.WHITE,
            border_color=ft.Colors.TEAL_300,
            color=ft.Colors.BLACK87,
        )
        self._location_field = ft.TextField(
            label="Location", 
            width=350, 
            hint_text="Address or coordinates",
            bgcolor=ft.Colors.WHITE,
            border_color=ft.Colors.TEAL_300,
            color=ft.Colors.BLACK87,
        )
        self._details_field = ft.TextField(
            label="Other Details", 
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
            "Submit Request",
            on_click=lambda e: self._on_submit(page)
        )
        cancel_btn = create_action_button(
            "Cancel",
            on_click=lambda e: page.go("/user"),
            outlined=True,
            bgcolor=ft.Colors.TEAL_400
        )        # Card container
        card = ft.Container(
            ft.Column([
                ft.Text("Report Rescue Mission", size=22, weight="bold", color=ft.Colors.BLACK87),
                ft.Text("Fill in the rescue details", size=12, color=ft.Colors.BLACK54),
                ft.Divider(height=12, color=ft.Colors.GREY_300),
                self._type_dropdown,
                self._name_field,
                self._location_field,
                self._details_field,
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
        animal_type = (self._type_dropdown.value or "").strip()
        name = (self._name_field.value or "").strip()
        location = (self._location_field.value or "").strip()
        details = (self._details_field.value or "").strip()

        if not animal_type:
            return False, "Please select an animal type."
        if not name:
            return False, "Please enter reporter name."
        if not location:
            return False, "Please enter location."
        if not details:
            return False, "Please enter additional details."

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
            animal_type = (self._type_dropdown.value or "").strip()
            name = (self._name_field.value or "").strip()
            location = (self._location_field.value or "").strip()
            details = (self._details_field.value or "").strip()

            # Get user_id from centralized state management
            app_state = get_app_state()
            user_id = app_state.auth.user_id
            if not user_id:
                self._error_text.value = "Session expired. Please log in again."
                self._submit_btn.disabled = False
                page.update()
                return

            print(f"[DEBUG] Submitting rescue request for user_id={user_id}, animal_type={animal_type}")

            # Try to geocode the location
            coords = self.map_service.geocode_location(location)
            latitude = coords[0] if coords else None
            longitude = coords[1] if coords else None
            
            if coords:
                print(f"[DEBUG] Geocoded location to lat={latitude}, lng={longitude}")
            else:
                print(f"[DEBUG] Could not geocode location, storing without coordinates")

            # submit rescue request
            mission_id = self.rescue_service.submit_rescue_request(
                user_id=user_id,
                location=location,
                animal_type=animal_type,
                name=name,
                details=details,
                status="pending",
                latitude=latitude,
                longitude=longitude,
            )

            print(f"[DEBUG] Rescue mission created with ID={mission_id}")

            # show success
            page.snack_bar = ft.SnackBar(ft.Text("Rescue mission submitted successfully!"))
            page.snack_bar.open = True
            page.update()

            # navigate to check status
            page.go(f"/check_status?mission_id={mission_id}")

        except Exception as exc:
            self._error_text.value = f"Error: {str(exc)}"
            self._submit_btn.disabled = False
            page.update()


__all__ = ["RescueFormPage"]

