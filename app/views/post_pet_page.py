"""Form page for users to post their own pets for adoption."""
from __future__ import annotations

from typing import Optional

import app_config
from services.animal_service import AnimalService
from services.map_service import MapService
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

# Try to import the flet_geolocator package for GPS auto-detect
try:
    from flet_geolocator import Geolocator, GeolocatorPermissionStatus, GeolocatorPositionAccuracy
    GEOLOCATOR_AVAILABLE = True
except ImportError:
    GEOLOCATOR_AVAILABLE = False


class PostPetPage:
    """Page for users to submit a pet listing for adoption."""

    def __init__(self, db_path: Optional[str] = None) -> None:
        self._db_path = db_path or app_config.DB_PATH
        self.service = AnimalService(self._db_path)
        self._map_service = MapService()
        self._photo_widget: Optional[object] = None
        self._type_dropdown: Optional[object] = None
        self._name_field: Optional[object] = None
        self._breed_field: Optional[object] = None
        self._age_dropdown: Optional[object] = None
        self._contact_field: Optional[object] = None
        self._reason_field: Optional[object] = None
        self._location_field: Optional[object] = None
        self._location_btn: Optional[object] = None
        self._location_status: Optional[object] = None
        self._location_loading: Optional[object] = None
        self._geolocator: Optional[object] = None
        self._current_coords: Optional[tuple] = None
        self._error_text: Optional[object] = None
        self._user_id: Optional[int] = None
        self._page = None
        self._ai_suggestion_container: Optional[object] = None
        self._ai_result = None
        self._ai_loading = False

    def build(self, page) -> None:
        try:
            import flet as ft
        except Exception as exc:
            raise RuntimeError("Flet must be installed to build the UI") from exc

        page.title = "Post Pet for Adoption"
        self._page = page

        app_state = get_app_state(page, self._db_path)
        self._user_id = app_state.auth.user_id or page.session.get("user_id")
        if not self._user_id:
            show_snackbar(page, "Please sign in to post a listing", error=True)
            page.go("/")
            return

        header = create_page_header("Paw Rescue")

        info_banner = ft.Container(
            ft.Row(
                [
                    ft.Icon(ft.Icons.INFO_OUTLINE, color=ft.Colors.TEAL_700, size=18),
                    ft.Text(
                        "Listings are reviewed by admins before going live.",
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

        self._photo_widget = create_photo_upload_widget(
            page,
            show_ai_button=True,
            on_ai_analyze=self._handle_ai_analyze,
            on_photo_changed=self._clear_ai_suggestion,
        )

        self._type_dropdown = create_form_dropdown(
            label="Animal Type",
            options=["Dog", "Cat", "Other"],
        )
        self._name_field = create_form_text_field(
            label="Pet Name",
            hint_text="Enter your pet's name",
        )
        self._breed_field = create_form_text_field(
            label="Breed (Optional)",
            hint_text="Enter breed if known",
        )
        self._age_dropdown = create_form_dropdown(
            label="Age",
            options=self._age_options(),
            menu_height=200,
        )
        self._contact_field = create_form_text_field(
            label="Contact Information",
            hint_text="Email or phone (e.g., email@example.com or 09XXXXXXXXX)",
        )
        self._reason_field = create_form_text_field(
            label="Reason for Posting",
            hint_text="Tell us why you are rehoming your pet",
            multiline=True,
            min_lines=3,
        )
        self._location_field = create_form_text_field(
            label="Owner Location",
            hint_text="Enter your city or address",
            expand=True,
        )

        self._location_status = ft.Container(
            content=ft.Icon(ft.Icons.CHECK_CIRCLE, color=ft.Colors.GREEN_600, size=20),
            visible=False,
            tooltip="Location verified",
        )

        self._location_loading = ft.Container(
            content=ft.ProgressRing(width=20, height=20, stroke_width=2, color=ft.Colors.TEAL_600),
            visible=False,
        )

        if GEOLOCATOR_AVAILABLE:
            self._geolocator = Geolocator(
                on_error=lambda e: self._handle_geolocator_error(page, e),
            )
            page.overlay.append(self._geolocator)
        else:
            self._geolocator = None
            print("[WARN] flet_geolocator not available - GPS button will be disabled")

        self._location_btn = ft.Container(
            content=ft.IconButton(
                icon=ft.Icons.MY_LOCATION,
                icon_color=ft.Colors.WHITE,
                icon_size=20,
                tooltip="Use my current location",
                on_click=lambda e: page.run_task(self._get_current_location, page),
                style=ft.ButtonStyle(
                    shape=ft.RoundedRectangleBorder(radius=8),
                ),
            ),
            bgcolor=ft.Colors.TEAL_600,
            border_radius=8,
            width=42,
            height=42,
        )

        location_row = ft.Row(
            [
                self._location_field,
                self._location_status,
                self._location_loading,
                self._location_btn,
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=8,
        )

        location_helper = ft.Text(
            "Tip: Click the GPS button to auto-detect your location",
            size=11,
            color=ft.Colors.GREY_600,
            italic=True,
        )

        self._ai_suggestion_container = ft.Container(content=None, visible=False)

        if app_state.auth.user_contact:
            self._contact_field.value = app_state.auth.user_contact

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
                    ft.Icon(ft.Icons.SEND, size=18),
                    ft.Text("Submit Listing", size=14, weight="w500"),
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
                    ft.Icon(ft.Icons.PETS, color=ft.Colors.TEAL_700, size=28),
                    ft.Text(
                        "Post a Pet for Adoption",
                        size=22,
                        weight="bold",
                        color=ft.Colors.BLACK87,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Text(
                        "Share your pet with families looking to adopt",
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
                location_row,
                location_helper,
            ],
            spacing=8,
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

    async def _get_current_location(self, page) -> None:
        """Get the user's current location using geolocator."""
        try:
            import flet as ft
        except Exception:
            raise RuntimeError("Flet is required for UI actions")

        if not GEOLOCATOR_AVAILABLE or self._geolocator is None:
            self._show_location_error(page, "GPS functionality not available. Please enter location manually.")
            return

        if self._location_btn:
            self._location_btn.visible = False
        if self._location_loading:
            self._location_loading.visible = True
        if self._location_status:
            self._location_status.visible = False
        if self._error_text:
            self._error_text.value = ""
            self._error_text.visible = False
        page.update()

        try:
            location_enabled = await self._geolocator.is_location_service_enabled_async()
            if not location_enabled:
                self._show_location_error(page, "Location services are disabled. Please enable them.")
                return

            permission = await self._geolocator.request_permission_async(wait_timeout=30)
            if permission in (GeolocatorPermissionStatus.DENIED, GeolocatorPermissionStatus.DENIED_FOREVER):
                self._show_location_error(page, "Location permission denied.")
                return

            position = await self._geolocator.get_current_position_async(
                accuracy=GeolocatorPositionAccuracy.BEST
            )

            if position:
                self._current_coords = (position.latitude, position.longitude)
                address = self._map_service.reverse_geocode(position.latitude, position.longitude)

                if address:
                    self._location_field.value = address
                else:
                    self._location_field.value = f"{position.latitude:.6f}, {position.longitude:.6f}"

                if self._location_status:
                    self._location_status.content = ft.Icon(
                        ft.Icons.CHECK_CIRCLE,
                        color=ft.Colors.GREEN_600,
                        size=20,
                    )
                    self._location_status.tooltip = "Location detected successfully"
                    self._location_status.visible = True

                show_snackbar(page, "Location detected successfully.")
            else:
                self._show_location_error(page, "Could not determine your position.")

        except Exception as exc:
            self._show_location_error(page, f"Location error: {exc}")
        finally:
            if self._location_btn:
                self._location_btn.visible = True
            if self._location_loading:
                self._location_loading.visible = False
            page.update()

    def _show_location_error(self, page, message: str) -> None:
        """Show location error."""
        try:
            import flet as ft
        except Exception:
            return

        if self._location_status:
            self._location_status.content = ft.Icon(
                ft.Icons.WARNING_AMBER,
                color=ft.Colors.ORANGE_700,
                size=20,
            )
            self._location_status.tooltip = message
            self._location_status.visible = True

        if self._location_btn:
            self._location_btn.visible = True
        if self._location_loading:
            self._location_loading.visible = False
        show_snackbar(page, message, error=True)
        page.update()

    def _handle_geolocator_error(self, page, error) -> None:
        """Handle geolocator errors."""
        self._show_location_error(page, f"Location error: {error.data}")

    def _on_submit(self, page) -> None:
        if not self._user_id:
            show_snackbar(page, "Please sign in to post a listing", error=True)
            page.go("/")
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

        photo_filename = None
        if self._photo_widget:
            photo_filename = self._photo_widget.save_with_name(name)

        try:
            listing_id = self.service.create_user_listing(
                user_id=self._user_id,
                name=name,
                type=animal_type,
                age=age_value,
                contact=contact,
                reason=reason,
                location=location,
                photo=photo_filename,
                breed=breed or None,
            )
            show_snackbar(page, f"Listing submitted for review (ID: {listing_id})")
            page.go("/my_listings")
        except Exception as exc:
            self._show_error(page, f"Error: {exc}")

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


__all__ = ["PostPetPage"]
