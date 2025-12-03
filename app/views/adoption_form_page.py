"""Form page for submitting adoption applications."""
from __future__ import annotations
from typing import Optional

import app_config
from services.adoption_service import AdoptionService
from services.animal_service import AnimalService
from services.photo_service import load_photo
from state import get_app_state
from components import (
    create_page_header, create_gradient_background,
    create_form_text_field, show_snackbar
)


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
        self._edit_request_id: Optional[int] = None
        self._animal_photo_container: Optional[object] = None

    def build(self, page, animal_id: Optional[int] = None, edit_request_id: Optional[int] = None) -> None:
        try:
            import flet as ft
        except Exception as exc:
            raise RuntimeError("Flet must be installed to build the UI") from exc

        page.title = "Adoption Application"
        self._edit_request_id = edit_request_id

        # If editing, load existing request data
        existing_request = None
        if edit_request_id:
            existing_request = self.adoption_service.get_request_by_id(edit_request_id)
            if existing_request:
                animal_id = existing_request.get("animal_id")

        # Header with logo
        header = create_page_header("Paw Rescue")

        # fetch adoptable animals
        animals = self.animal_service.get_adoptable_animals() or []
        
        # Create a dict for quick animal lookup
        animals_dict = {a.get("id"): a for a in animals}

        # animal dropdown - needs to be ft.Dropdown for option text support
        animal_options = [ft.dropdown.Option(str(a.get("id")), text=a.get("name", "Unknown")) for a in animals]
        
        # If editing, also add the current animal if not in adoptable list
        if animal_id and animal_id not in animals_dict:
            current_animal = self.animal_service.get_animal_by_id(animal_id)
            if current_animal:
                animals_dict[animal_id] = current_animal
                animal_options.insert(0, ft.dropdown.Option(str(animal_id), text=current_animal.get("name", "Unknown")))

        # Function to update animal photo display
        def update_animal_photo(selected_animal_id: Optional[int]):
            if selected_animal_id and selected_animal_id in animals_dict:
                animal = animals_dict[selected_animal_id]
                photo_data = load_photo(animal.get("photo"))
                if photo_data:
                    self._animal_photo_container.content = ft.Image(
                        src_base64=photo_data,
                        width=120,
                        height=120,
                        fit=ft.ImageFit.COVER,
                        border_radius=8,
                    )
                else:
                    self._animal_photo_container.content = ft.Container(
                        ft.Icon(ft.Icons.PETS, size=50, color=ft.Colors.GREY_400),
                        width=120,
                        height=120,
                        bgcolor=ft.Colors.GREY_200,
                        border_radius=8,
                        alignment=ft.alignment.center,
                    )
                # Show animal info
                animal_name = animal.get("name", "Unknown")
                animal_species = animal.get("species", "Unknown")
                animal_age = animal.get("age", "N/A")
                self._animal_info_text.value = f"{animal_name} • {animal_species} • {animal_age}yrs old"
                self._animal_info_text.visible = True
            else:
                self._animal_photo_container.content = ft.Container(
                    ft.Column([
                        ft.Icon(ft.Icons.PETS, size=40, color=ft.Colors.GREY_400),
                        ft.Text("Select an animal", size=11, color=ft.Colors.GREY_500),
                    ], horizontal_alignment="center", alignment="center", spacing=5),
                    width=120,
                    height=120,
                    bgcolor=ft.Colors.GREY_100,
                    border_radius=8,
                    alignment=ft.alignment.center,
                )
                self._animal_info_text.value = ""
                self._animal_info_text.visible = False
            page.update()

        def on_animal_change(e):
            try:
                selected_id = int(e.control.value) if e.control.value else None
                update_animal_photo(selected_id)
            except (ValueError, TypeError):
                update_animal_photo(None)

        self._animal_dropdown = ft.Dropdown(
            label="Select Animal to Adopt",
            width=400,
            options=animal_options,
            hint_text="Choose an animal",
            bgcolor=ft.Colors.WHITE,
            border_color=ft.Colors.GREY_300,
            focused_border_color=ft.Colors.TEAL_400,
            color=ft.Colors.BLACK87,
            on_change=on_animal_change,
            disabled=edit_request_id is not None,  # Disable dropdown when editing
        )

        # Animal photo container
        self._animal_photo_container = ft.Container(
            ft.Container(
                ft.Column([
                    ft.Icon(ft.Icons.PETS, size=40, color=ft.Colors.GREY_400),
                    ft.Text("Select an animal", size=11, color=ft.Colors.GREY_500),
                ], horizontal_alignment="center", alignment="center", spacing=5),
                width=120,
                height=120,
                bgcolor=ft.Colors.GREY_100,
                border_radius=8,
                alignment=ft.alignment.center,
            ),
            alignment=ft.alignment.center,
        )
        
        # Animal info text
        self._animal_info_text = ft.Text("", size=12, color=ft.Colors.BLACK87, weight="w500", visible=False)

        # set dropdown to animal_id if provided
        if animal_id is not None:
            self._animal_dropdown.value = str(animal_id)

        # Form fields with improved styling
        self._name_field = create_form_text_field(
            label="Your Full Name", 
            hint_text="Enter your full name",
            width=400,
        )
        self._contact_field = create_form_text_field(
            label="Contact Information", 
            hint_text="Phone number or email address",
            width=400,
        )
        self._reason_field = create_form_text_field(
            label="Why do you want to adopt? (Optional)",
            hint_text="Tell us about your home, experience with pets, etc.",
            multiline=True,
            min_lines=3,
            width=400,
        )

        # Pre-fill user name from state for logged-in users
        app_state = get_app_state()
        if app_state.auth.user_name:
            self._name_field.value = app_state.auth.user_name
        
        # Pre-fill form if editing
        if existing_request:
            self._contact_field.value = existing_request.get("contact", "")
            self._reason_field.value = existing_request.get("reason", "")

        # Error display
        self._error_text = ft.Text("", color=ft.Colors.RED_600, size=12, text_align=ft.TextAlign.CENTER)

        # Submit and cancel buttons with improved styling
        submit_text = "Update Application" if edit_request_id else "Submit Application"
        submit_icon = ft.Icons.EDIT if edit_request_id else ft.Icons.SEND
        
        self._submit_btn = ft.ElevatedButton(
            content=ft.Row(
                [ft.Icon(submit_icon, size=18), ft.Text(submit_text, size=14, weight="w500")],
                spacing=8,
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            width=180,
            height=48,
            on_click=lambda e: self._on_submit(page),
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.TEAL_600,
                color=ft.Colors.WHITE,
                shape=ft.RoundedRectangleBorder(radius=10),
                elevation=2,
            )
        )
        
        cancel_btn = ft.OutlinedButton(
            content=ft.Text("Cancel", size=14, weight="w500"),
            width=120,
            height=48,
            on_click=lambda e: page.go("/check_status") if edit_request_id else page.go("/available_adoption"),
            style=ft.ButtonStyle(
                color=ft.Colors.GREY_700,
                shape=ft.RoundedRectangleBorder(radius=10),
                side=ft.BorderSide(1.5, ft.Colors.GREY_400),
            )
        )

        # Title section
        title_text = "Edit Adoption Application" if edit_request_id else "Adoption Application"
        subtitle_text = "Update your application details" if edit_request_id else "Give a loving home to an animal in need"
        title_icon = ft.Icons.EDIT if edit_request_id else ft.Icons.FAVORITE
        
        title_section = ft.Container(
            ft.Column([
                ft.Row([
                    ft.Icon(title_icon, color=ft.Colors.TEAL_700, size=28),
                    ft.Text(title_text, size=24, weight="bold", color=ft.Colors.BLACK87),
                ], alignment=ft.MainAxisAlignment.CENTER, spacing=10),
                ft.Text(subtitle_text, size=13, color=ft.Colors.GREY_600),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=4),
            padding=ft.padding.only(bottom=10),
        )
        
        # Animal selection section
        animal_section = ft.Column([
            ft.Row([
                ft.Icon(ft.Icons.PETS, color=ft.Colors.TEAL_700, size=20),
                ft.Text("Animal Selection", size=14, weight="w600", color=ft.Colors.TEAL_700),
            ], spacing=8),
            ft.Container(height=8),
            ft.Container(self._animal_photo_container, alignment=ft.alignment.center),
            self._animal_info_text,
            ft.Container(height=5),
            self._animal_dropdown,
        ], spacing=8, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        
        # Adopter information section
        adopter_section = ft.Column([
            ft.Row([
                ft.Icon(ft.Icons.PERSON, color=ft.Colors.TEAL_700, size=20),
                ft.Text("Your Information", size=14, weight="w600", color=ft.Colors.TEAL_700),
            ], spacing=8),
            self._name_field,
            self._contact_field,
        ], spacing=12)
        
        # Additional details section
        details_section = ft.Column([
            ft.Row([
                ft.Icon(ft.Icons.DESCRIPTION, color=ft.Colors.TEAL_700, size=20),
                ft.Text("Additional Details", size=14, weight="w600", color=ft.Colors.TEAL_700),
            ], spacing=8),
            self._reason_field,
        ], spacing=12)

        # Card container with improved layout
        card = ft.Container(
            ft.Column([
                title_section,
                ft.Divider(height=1, color=ft.Colors.GREY_300),
                ft.Container(height=15),
                
                # Form sections
                animal_section,
                ft.Container(height=15),
                adopter_section,
                ft.Container(height=8),
                details_section,
                
                ft.Container(height=15),
                
                # Error text
                self._error_text,
                
                # Action buttons
                ft.Row(
                    [self._submit_btn, cancel_btn],
                    spacing=16,
                    alignment=ft.MainAxisAlignment.CENTER
                ),
            ], spacing=8, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            width=480,
            padding=30,
            bgcolor=ft.Colors.WHITE,
            border_radius=16,
            shadow=ft.BoxShadow(
                blur_radius=25,
                spread_radius=2,
                color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK),
                offset=(0, 8)
            ),
        )

        # Main layout
        layout = ft.Column([
            header,
            card,
            ft.Container(height=20),  # Bottom padding
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15, scroll=ft.ScrollMode.AUTO)

        page.controls.clear()
        page.add(create_gradient_background(layout))
        page.update()

        # Update photo display for initial animal_id
        if animal_id:
            update_animal_photo(animal_id)

    def _validate_form(self) -> tuple[bool, str]:
        """Validate form fields. Return (is_valid, error_message)."""
        animal_id = (self._animal_dropdown.value or "").strip()
        name = (self._name_field.value or "").strip()
        contact = (self._contact_field.value or "").strip()

        if not animal_id:
            return False, "Please select an animal."
        if not name:
            return False, "Please enter your name."
        if not contact:
            return False, "Please enter contact information."

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

            # Validate animal is still adoptable (for new requests)
            if not self._edit_request_id:
                animal = next((a for a in self.animal_service.get_all_animals() if a.get("id") == animal_id), None)
                if not animal:
                    self._error_text.value = "Animal no longer exists in the system."
                    self._submit_btn.disabled = False
                    page.update()
                    return
                
                animal_status = (animal.get("status") or "").lower()
                if animal_status == "adopted":
                    self._error_text.value = "This animal has already been adopted."
                    self._submit_btn.disabled = False
                    page.update()
                    return
                if animal_status == "processing":
                    self._error_text.value = "This animal is not yet available for adoption."
                    self._submit_btn.disabled = False
                    page.update()
                    return
                if animal_status not in ("healthy", "available", "adoptable", "ready", "recovering"):
                    self._error_text.value = f"This animal is currently '{animal_status}' and cannot be adopted."
                    self._submit_btn.disabled = False
                    page.update()
                    return

            # Get user_id from centralized state management
            app_state = get_app_state()
            user_id = app_state.auth.user_id
            if not user_id:
                self._error_text.value = "Session expired. Please log in again."
                self._submit_btn.disabled = False
                page.update()
                return

            if self._edit_request_id:
                # Update existing request
                updated = self.adoption_service.update_request(
                    request_id=self._edit_request_id,
                    contact=contact,
                    reason=reason,
                )
                if updated:
                    show_snackbar(page, "Application updated successfully!")
                    page.go("/check_status")
                else:
                    self._error_text.value = "Failed to update application."
                    self._submit_btn.disabled = False
                    page.update()
            else:
                # Submit new adoption request
                request_id = self.adoption_service.submit_request(
                    user_id=user_id,
                    animal_id=animal_id,
                    contact=contact,
                    reason=reason,
                    status="pending",
                )

                # show success
                show_snackbar(page, "Application submitted successfully!")

                # navigate to check status
                page.go(f"/check_status?request_id={request_id}")

        except Exception as exc:
            self._error_text.value = f"Error: {str(exc)}"
            self._submit_btn.disabled = False
            page.update()


__all__ = ["AdoptionFormPage"]

