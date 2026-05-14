"""Form page for users to edit their pet listings."""
from __future__ import annotations

from typing import Optional
from urllib.parse import urlparse, parse_qs

import app_config
from services.animal_service import AnimalService
from app_config import AnimalStatus
from state import get_app_state
from components import (
    create_page_header,
    create_gradient_background,
    create_form_text_field,
    create_form_dropdown,
    create_photo_upload_widget,
    create_ai_suggestion_card,
    create_ai_loading_card,
    create_ai_download_dialog,
    show_snackbar,
    validate_contact,
)


class EditListingPage:
    """Page for users to update their existing listings."""

    def __init__(self, db_path: Optional[str] = None) -> None:
        self._db_path = db_path or app_config.DB_PATH
        self.service = AnimalService(self._db_path)
        self._photo_widget: Optional[object] = None
        self._type_dropdown: Optional[object] = None
        self._name_field: Optional[object] = None
        self._breed_field: Optional[object] = None
        self._age_dropdown: Optional[object] = None
        self._contact_field: Optional[object] = None
        self._reason_field: Optional[object] = None
        self._location_field: Optional[object] = None
        self._error_text: Optional[object] = None
        self._user_id: Optional[int] = None
        self._animal_id: Optional[int] = None
        self._existing_photo: Optional[str] = None
        self._photo_changed = False
        self._page = None
        self._ai_suggestion_container: Optional[object] = None
        self._ai_result = None
        self._ai_loading = False

    def build(self, page, animal_id: Optional[int] = None) -> None:
        try:
            import flet as ft
        except Exception as exc:
            raise RuntimeError("Flet must be installed to build the UI") from exc

        page.title = "Edit Listing"
        self._page = page

        app_state = get_app_state(page, self._db_path)
        self._user_id = app_state.auth.user_id or page.session.get("user_id")
        if not self._user_id:
            show_snackbar(page, "Please sign in to edit listings", error=True)
            page.go("/")
            return

        if animal_id is None:
            parsed = urlparse(page.route)
            query_params = parse_qs(parsed.query)
            if "animal_id" in query_params:
                try:
                    animal_id = int(query_params["animal_id"][0])
                except (ValueError, IndexError):
                    animal_id = None

        if animal_id is None:
            show_snackbar(page, "No listing selected", error=True)
            page.go("/my_listings")
            return

        self._animal_id = animal_id
        listing = self.service.get_user_listing_by_id(animal_id, self._user_id)
        if not listing:
            show_snackbar(page, "Listing not found", error=True)
            page.go("/my_listings")
            return

        if AnimalStatus.normalize(listing.get("status", "")) == AnimalStatus.ADOPTED:
            show_snackbar(page, "Adopted listings cannot be edited", error=True)
            page.go("/my_listings")
            return

        header = create_page_header("Paw Rescue")

        info_banner = ft.Container(
            ft.Row(
                [
                    ft.Icon(ft.Icons.INFO_OUTLINE, color=ft.Colors.TEAL_700, size=18),
                    ft.Text(
                        "Edits will resubmit your listing for admin review.",
                        size=12,
                        color=ft.Colors.TEAL_700,
                    ),
                ],
                spacing=8,
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            padding=ft.padding.symmetric(horizontal=14, vertical=10),
            bgcolor=ft.Colors.TEAL_50,
            border_radius=10,
            border=ft.border.all(1, ft.Colors.TEAL_200),
        )

        self._existing_photo = listing.get("photo")
        self._photo_widget = create_photo_upload_widget(
            page,
            initial_photo=self._existing_photo,
            show_ai_button=True,
            on_ai_analyze=self._handle_ai_analyze,
            on_photo_changed=self._mark_photo_changed,
        )

        species_value = (listing.get("species") or "").capitalize()
        if species_value not in ["Dog", "Cat", "Other"]:
            species_value = ""

        age_value = self._age_label(listing.get("age"))

        self._type_dropdown = create_form_dropdown(
            label="Animal Type",
            options=["Dog", "Cat", "Other"],
            value=species_value,
        )
        self._name_field = create_form_text_field(
            label="Pet Name",
            hint_text="Enter your pet's name",
            value=listing.get("name", ""),
        )
        self._breed_field = create_form_text_field(
            label="Breed (Optional)",
            hint_text="Enter breed if known",
            value=listing.get("breed") or "",
        )
        self._age_dropdown = create_form_dropdown(
            label="Age",
            options=self._age_options(),
            value=age_value,
            menu_height=200,
        )
        self._contact_field = create_form_text_field(
            label="Contact Information",
            hint_text="Email or phone (e.g., email@example.com or 09XXXXXXXXX)",
            value=listing.get("listed_contact", "") or app_state.auth.user_contact,
        )
        self._reason_field = create_form_text_field(
            label="Reason for Posting",
            hint_text="Tell us why you are rehoming your pet",
            multiline=True,
            min_lines=3,
            value=listing.get("listed_reason", ""),
        )
        self._location_field = create_form_text_field(
            label="Owner Location",
            hint_text="Enter your city or address",
            value=listing.get("listed_location", ""),
        )

        self._ai_suggestion_container = ft.Container(content=None, visible=False)

        self._error_text = ft.Text(
            "",
            color=ft.Colors.RED_600,
            size=12,
            text_align=ft.TextAlign.CENTER,
            visible=False,
        )

        submit_btn = ft.ElevatedButton(
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.SAVE, size=18),
                    ft.Text("Save Changes", size=14, weight="w500"),
                ],
                spacing=8,
                alignment=ft.MainAxisAlignment.CENTER,
                tight=True,
            ),
            expand=True,
            height=48,
            on_click=lambda e: self._on_submit(page),
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.TEAL_600,
                color=ft.Colors.WHITE,
                shape=ft.RoundedRectangleBorder(radius=10),
                elevation=2,
            ),
        )

        cancel_btn = ft.OutlinedButton(
            content=ft.Text("Cancel", size=14, weight="w500"),
            expand=True,
            height=48,
            on_click=lambda e: page.go("/my_listings"),
            style=ft.ButtonStyle(
                color=ft.Colors.GREY_700,
                shape=ft.RoundedRectangleBorder(radius=10),
                side=ft.BorderSide(1.5, ft.Colors.GREY_400),
            ),
        )

        title_section = ft.Container(
            ft.Column(
                [
                    ft.Icon(ft.Icons.EDIT, color=ft.Colors.TEAL_700, size=28),
                    ft.Text(
                        "Edit Listing",
                        size=22,
                        weight="bold",
                        color=ft.Colors.BLACK87,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Text(
                        "Update your pet details before it goes live",
                        size=13,
                        color=ft.Colors.GREY_600,
                        text_align=ft.TextAlign.CENTER,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=6,
            ),
            padding=ft.padding.only(bottom=10),
        )

        details_section = ft.Column(
            [
                ft.Row(
                    [
                        ft.Icon(ft.Icons.PETS, color=ft.Colors.TEAL_700, size=20),
                        ft.Text("Pet Details", size=14, weight="w600", color=ft.Colors.TEAL_700),
                    ],
                    spacing=8,
                ),
                self._type_dropdown,
                self._name_field,
                self._breed_field,
                self._age_dropdown,
            ],
            spacing=12,
        )

        contact_section = ft.Column(
            [
                ft.Row(
                    [
                        ft.Icon(ft.Icons.CONTACT_PHONE, color=ft.Colors.TEAL_700, size=20),
                        ft.Text("Contact", size=14, weight="w600", color=ft.Colors.TEAL_700),
                    ],
                    spacing=8,
                ),
                self._contact_field,
            ],
            spacing=12,
        )

        reason_section = ft.Column(
            [
                ft.Row(
                    [
                        ft.Icon(ft.Icons.DESCRIPTION, color=ft.Colors.TEAL_700, size=20),
                        ft.Text("Reason", size=14, weight="w600", color=ft.Colors.TEAL_700),
                    ],
                    spacing=8,
                ),
                self._reason_field,
            ],
            spacing=12,
        )

        location_section = ft.Column(
            [
                ft.Row(
                    [
                        ft.Icon(ft.Icons.LOCATION_ON, color=ft.Colors.TEAL_700, size=20),
                        ft.Text("Owner Location", size=14, weight="w600", color=ft.Colors.TEAL_700),
                    ],
                    spacing=8,
                ),
                self._location_field,
            ],
            spacing=12,
        )

        card_content = ft.Column(
            [
                title_section,
                info_banner,
                ft.Divider(height=1, color=ft.Colors.GREY_300),
                ft.Container(height=8),
                self._photo_widget.build(),
                self._ai_suggestion_container,
                details_section,
                contact_section,
                reason_section,
                location_section,
                self._error_text,
                ft.Container(height=4),
                ft.Row([submit_btn, cancel_btn], spacing=12),
            ],
            spacing=12,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

        card = ft.Container(
            card_content,
            padding=ft.padding.symmetric(horizontal=24, vertical=28),
            bgcolor=ft.Colors.WHITE,
            border_radius=16,
            shadow=ft.BoxShadow(
                blur_radius=25,
                spread_radius=2,
                color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK),
                offset=(0, 8),
            ),
            width=480,
        )

        layout = ft.Column(
            [
                header,
                ft.Container(card, margin=ft.margin.symmetric(horizontal=16)),
                ft.Container(height=20),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=10,
            scroll=ft.ScrollMode.AUTO,
        )

        page.controls.clear()
        page.add(create_gradient_background(layout))
        page.update()

    def _age_options(self) -> list[str]:
        return [
            "Under 1 year",
            *[f"{i} year{'s' if i != 1 else ''}" for i in range(1, 21)],
            "Above 20 years",
        ]

    def _age_label(self, age: Optional[int]) -> str:
        if age is None:
            return ""
        if age == 0:
            return "Under 1 year"
        if age > 20:
            return "Above 20 years"
        return f"{age} year{'s' if age != 1 else ''}"

    def _parse_age_value(self, selection: str) -> Optional[int]:
        if not selection:
            return None
        if selection == "Under 1 year":
            return 0
        if selection == "Above 20 years":
            return 21
        try:
            return int(selection.split()[0])
        except (ValueError, IndexError):
            return None

    def _mark_photo_changed(self) -> None:
        self._photo_changed = True
        self._clear_ai_suggestion()

    def _on_submit(self, page) -> None:
        if not self._user_id or not self._animal_id:
            show_snackbar(page, "Missing listing data", error=True)
            page.go("/my_listings")
            return

        animal_type = (self._type_dropdown.value or "").strip() if self._type_dropdown else ""
        name = (self._name_field.value or "").strip() if self._name_field else ""
        breed = (self._breed_field.value or "").strip() if self._breed_field else ""
        age_selection = (self._age_dropdown.value or "").strip() if self._age_dropdown else ""
        contact = (self._contact_field.value or "").strip() if self._contact_field else ""
        reason = (self._reason_field.value or "").strip() if self._reason_field else ""
        location = (self._location_field.value or "").strip() if self._location_field else ""

        if not animal_type:
            return self._show_error(page, "Please select an animal type.")
        if not name:
            return self._show_error(page, "Please enter your pet's name.")
        if not age_selection:
            return self._show_error(page, "Please select your pet's age.")

        age_value = self._parse_age_value(age_selection)
        if age_value is None:
            return self._show_error(page, "Please select a valid age.")

        contact_ok, contact_error = validate_contact(contact)
        if not contact_ok:
            return self._show_error(page, contact_error)

        if not reason:
            return self._show_error(page, "Please provide a reason for posting.")

        if not location:
            return self._show_error(page, "Please provide your location.")

        success = self.service.update_user_listing(
            animal_id=self._animal_id,
            user_id=self._user_id,
            name=name,
            type=animal_type,
            age=age_value,
            contact=contact,
            reason=reason,
            location=location,
            breed=breed or None,
            reset_status=True,
        )

        if not success:
            return self._show_error(page, "Unable to update listing. Please try again.")

        if self._photo_widget and self._photo_changed:
            new_photo = self._photo_widget.save_with_name(name)
            if new_photo and new_photo != self._existing_photo:
                self.service.update_animal_photo(self._animal_id, new_photo)

        show_snackbar(page, "Listing updated and submitted for review")
        page.go("/my_listings")

    def _handle_ai_analyze(self, photo_base64: str) -> None:
        if self._ai_loading or not self._page:
            return

        from services.ai_classification_service import get_ai_classification_service

        service = get_ai_classification_service()
        download_status = service.get_download_status()

        if not all(download_status.values()):
            def on_download_complete(success: bool):
                if success:
                    self._handle_ai_analyze(photo_base64)

            create_ai_download_dialog(self._page, on_complete=on_download_complete)
            return

        self._ai_loading = True

        if self._ai_suggestion_container:
            self._ai_suggestion_container.content = create_ai_loading_card()
            self._ai_suggestion_container.visible = True
            self._page.update()

        def classify():
            try:
                result = service.classify_image(photo_base64)
                self._page.run_thread(lambda: self._on_ai_result(result))
            except Exception as exc:
                from models.classification_result import ClassificationResult
                error_result = ClassificationResult.from_error(str(exc))
                self._page.run_thread(lambda: self._on_ai_result(error_result))

        import threading
        thread = threading.Thread(target=classify, daemon=True)
        thread.start()

    def _on_ai_result(self, result) -> None:
        self._ai_loading = False
        self._ai_result = result

        if not self._ai_suggestion_container:
            return

        self._ai_suggestion_container.content = create_ai_suggestion_card(
            result=result,
            on_accept=self._accept_ai_suggestion,
            on_dismiss=self._dismiss_ai_suggestion,
        )
        self._ai_suggestion_container.visible = True
        if self._page:
            self._page.update()

    def _accept_ai_suggestion(self, species: str, breed: str) -> None:
        species_map = {"Dog": "Dog", "Cat": "Cat", "Other": "Other"}
        if self._type_dropdown:
            self._type_dropdown.value = species_map.get(species, "Other")

        if self._breed_field and breed and breed != "Not Applicable":
            self._breed_field.value = breed

        if self._ai_suggestion_container:
            self._ai_suggestion_container.visible = False
            self._ai_suggestion_container.content = None

        if self._page:
            breed_text = f" - {breed}" if breed and breed != "Not Applicable" else ""
            show_snackbar(self._page, f"Set species to {species}{breed_text}")
            self._page.update()

    def _dismiss_ai_suggestion(self) -> None:
        if self._ai_suggestion_container:
            self._ai_suggestion_container.visible = False
            self._ai_suggestion_container.content = None
        self._ai_result = None
        if self._page:
            self._page.update()

    def _clear_ai_suggestion(self) -> None:
        if self._ai_suggestion_container:
            self._ai_suggestion_container.visible = False
            self._ai_suggestion_container.content = None
        self._ai_result = None
        self._ai_loading = False

    def _show_error(self, page, message: str) -> None:
        if self._error_text:
            self._error_text.value = message
            self._error_text.visible = True
            page.update()
        else:
            show_snackbar(page, message, error=True)


__all__ = ["EditListingPage"]
