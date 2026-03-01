"""Emergency rescue form page for unregistered users."""
from __future__ import annotations
from typing import Optional
import asyncio
import concurrent.futures

import app_config
from app_config import Urgency, RescueStatus
from services.rescue_service import RescueService
from services.map_service import MapService
from components import (
    create_page_header, create_gradient_background,
    create_form_text_field, create_form_dropdown, show_snackbar, validate_contact,
    create_ai_suggestion_card, create_ai_loading_card, create_ai_analyze_button,
)
from components.photo_upload import create_photo_upload_widget

# Try to import the new flet_geolocator package
try:
    from flet_geolocator import Geolocator, GeolocatorPermissionStatus, GeolocatorPositionAccuracy
    GEOLOCATOR_AVAILABLE = True
except ImportError:
    GEOLOCATOR_AVAILABLE = False


class EmergencyRescuePage:
    """Emergency rescue form that doesn't require login."""
    
    def __init__(self, db_path: Optional[str] = None) -> None:
        self.rescue_service = RescueService(db_path or app_config.DB_PATH)
        self.map_service = MapService()
        self._type_dropdown: Optional[object] = None
        self._urgency_dropdown: Optional[object] = None
        self._breed_field: Optional[object] = None
        self._name_field: Optional[object] = None
        self._contact_field: Optional[object] = None
        self._location_field: Optional[object] = None
        self._details_field: Optional[object] = None
        self._error_text: Optional[object] = None
        self._submit_btn: Optional[object] = None
        self._location_btn: Optional[object] = None
        self._location_status: Optional[object] = None
        self._location_loading: Optional[object] = None
        self._geolocator: Optional[object] = None
        self._current_coords: Optional[tuple] = None
        
        # Photo and AI classification
        self._photo_widget: Optional[object] = None
        self._ai_suggestion_container: Optional[object] = None
        self._ai_loading: bool = False
        self._ai_result: Optional[object] = None
        self._page: Optional[object] = None

    def build(self, page) -> None:
        try:
            import flet as ft
        except Exception as exc:
            raise RuntimeError("Flet must be installed to build the UI") from exc

        page.title = "Emergency Rescue Report"

        self._page = page

        # Header with logo
        header = create_page_header("Paw Rescue")
        
        # Photo upload with AI classification
        self._photo_widget = create_photo_upload_widget(
            page,
            on_ai_analyze=self._handle_ai_analyze,
            show_ai_button=True,
            width=120,
            height=120,
        )
        
        # AI suggestion container (initially hidden)
        self._ai_suggestion_container = ft.Container(content=None, visible=False)
        
        # Animal type dropdown
        self._type_dropdown = create_form_dropdown(
            label="Animal Type",
            options=["Dog", "Cat", "Other"],
        )
        
        # Urgency level dropdown - default to High for emergency
        self._urgency_dropdown = create_form_dropdown(
            label="Urgency Level",
            options=["Low - Appears safe", "Medium - Needs attention", "High - Immediate help"],
            value="High - Immediate help",
        )
        
        # Breed field (optional - can help with rescue)
        self._breed_field = create_form_text_field(
            label="Breed (Optional)",
            hint_text="Enter breed if known",
        )

        # Reporter name field
        self._name_field = create_form_text_field(
            label="Your Name", 
            hint_text="Enter your full name",
        )
        
        # Contact field - required for emergency reports
        self._contact_field = create_form_text_field(
            label="Contact Number/Email",
            hint_text="Email or phone (e.g., email@example.com or 09XXXXXXXXX)",
        )
        
        # Location field
        self._location_field = create_form_text_field(
            label="Location",
            hint_text="Enter address or use GPS button →",
            expand=True,
        )
        
        # Location status indicator
        self._location_status = ft.Container(
            content=ft.Icon(ft.Icons.CHECK_CIRCLE, color=ft.Colors.GREEN_600, size=20),
            visible=False,
            tooltip="Location verified",
        )
        
        self._location_loading = ft.Container(
            content=ft.ProgressRing(width=20, height=20, stroke_width=2, color=ft.Colors.RED_600),
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
        
        # GPS Button
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
            bgcolor=ft.Colors.RED_600,
            border_radius=8,
            width=42,
            height=42,
        )
        
        # Location row
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
        
        # Helper text for location
        location_helper = ft.Text(
            "Tip: Click the GPS button to auto-detect your location",
            size=11,
            color=ft.Colors.GREY_600,
            italic=True,
        )
        
        # Details field
        self._details_field = create_form_text_field(
            label="Situation Description",
            hint_text="Describe the animal's condition and surroundings...",
            multiline=True,
            min_lines=4,
        )

        # Error display
        self._error_text = ft.Text("", color=ft.Colors.RED_600, size=12, text_align=ft.TextAlign.CENTER)

        # Submit and back buttons
        self._submit_btn = ft.ElevatedButton(
            content=ft.Row(
                [ft.Icon(ft.Icons.EMERGENCY, size=16), ft.Text("Submit", size=14, weight="w600")],
                spacing=6,
                alignment=ft.MainAxisAlignment.CENTER,
                tight=True,
            ),
            height=48,
            expand=True,
            on_click=lambda e: self._on_submit(page),
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.RED_600,
                color=ft.Colors.WHITE,
                shape=ft.RoundedRectangleBorder(radius=10),
                elevation=3,
            )
        )
        
        back_btn = ft.OutlinedButton(
            content=ft.Text("Back to Login", size=13, weight="w500"),
            expand=True,
            height=48,
            on_click=lambda e: page.go("/"),
            style=ft.ButtonStyle(
                color=ft.Colors.GREY_700,
                shape=ft.RoundedRectangleBorder(radius=10),
                side=ft.BorderSide(1.5, ft.Colors.GREY_400),
            )
        )
        
        # Form sections
        # Photo section with AI
        photo_section = ft.Column([
            ft.Row([
                ft.Icon(ft.Icons.PHOTO_CAMERA, color=ft.Colors.RED_700, size=20),
                ft.Text("Animal Photo (Optional)", size=14, weight="w600", color=ft.Colors.RED_700),
            ], spacing=8),
            ft.Container(height=8),
            ft.Container(self._photo_widget.build(), alignment=ft.alignment.center),
            ft.Container(height=8),
            self._ai_suggestion_container,
        ], spacing=8)
        
        animal_section = ft.Column([
            ft.Row([
                ft.Icon(ft.Icons.PETS, color=ft.Colors.RED_700, size=20),
                ft.Text("Animal Information", size=14, weight="w600", color=ft.Colors.RED_700),
            ], spacing=8),
            self._type_dropdown,
            self._breed_field,
            self._urgency_dropdown,
        ], spacing=12)
        
        reporter_section = ft.Column([
            ft.Row([
                ft.Icon(ft.Icons.PERSON, color=ft.Colors.RED_700, size=20),
                ft.Text("Your Details", size=14, weight="w600", color=ft.Colors.RED_700),
            ], spacing=8),
            self._name_field,
            self._contact_field,
        ], spacing=12)
        
        location_section = ft.Column([
            ft.Row([
                ft.Icon(ft.Icons.LOCATION_ON, color=ft.Colors.RED_700, size=20),
                ft.Text("Location", size=14, weight="w600", color=ft.Colors.RED_700),
            ], spacing=8),
            location_row,
            location_helper,
        ], spacing=8)
        
        details_section = ft.Column([
            ft.Row([
                ft.Icon(ft.Icons.DESCRIPTION, color=ft.Colors.RED_700, size=20),
                ft.Text("Additional Details", size=14, weight="w600", color=ft.Colors.RED_700),
            ], spacing=8),
            self._details_field,
        ], spacing=12)
        
        # Card container with emergency styling
        card = ft.Container(
            ft.Column([
                # Title section with emergency styling
                ft.Container(
                    ft.Column([
                        ft.Icon(ft.Icons.EMERGENCY, color=ft.Colors.RED_700, size=28),
                        ft.Text("Emergency Rescue Report", size=22, weight="bold", color=ft.Colors.RED_700, text_align=ft.TextAlign.CENTER),
                        ft.Text("Report an animal in immediate danger - No login required", size=13, color=ft.Colors.GREY_600, text_align=ft.TextAlign.CENTER),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=6),
                    padding=ft.padding.only(bottom=10),
                ),
                ft.Container(
                    height=3,
                    bgcolor=ft.Colors.RED_600,
                    border_radius=2,
                ),
                ft.Container(height=15),
                
                # Form sections
                photo_section,
                ft.Container(height=8),
                animal_section,
                ft.Container(height=8),
                reporter_section,
                ft.Container(height=8),
                location_section,
                ft.Container(height=8),
                details_section,
                
                ft.Container(height=15),
                
                # Error text
                self._error_text,
                
                # Action buttons
                ft.Row(
                    [self._submit_btn, back_btn], 
                    spacing=12, 
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
            ], spacing=8, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            width=480,  # acts as max-width in centered layout
            padding=ft.padding.symmetric(horizontal=24, vertical=28),
            bgcolor=ft.Colors.WHITE,
            border_radius=16,
            border=ft.border.all(2, ft.Colors.RED_200),
            shadow=ft.BoxShadow(
                blur_radius=25, 
                spread_radius=2, 
                color=ft.Colors.with_opacity(0.15, ft.Colors.RED), 
                offset=(0, 8)
            ),
        )

        # Main layout - margin wrapper so card doesn't touch screen edges
        card_with_margin = ft.Container(card, margin=ft.margin.symmetric(horizontal=16))

        layout = ft.Column([
            header,
            card_with_margin,
            ft.Container(height=20),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, alignment=ft.MainAxisAlignment.START, expand=True, spacing=15, scroll=ft.ScrollMode.AUTO)

        page.controls.clear()
        page.add(create_gradient_background(layout))
        page.update()

    def _validate_form(self) -> tuple[bool, str]:
        """Validate form fields."""
        animal_type = (self._type_dropdown.value or "").strip()
        urgency = (self._urgency_dropdown.value or "").strip()
        name = (self._name_field.value or "").strip()
        contact = (self._contact_field.value or "").strip()
        location = (self._location_field.value or "").strip()
        details = (self._details_field.value or "").strip()

        if not animal_type:
            return False, "Please select an animal type."
        if not urgency:
            return False, "Please select an urgency level."
        if not name:
            return False, "Please enter your name."
        if not contact:
            return False, "Please enter contact information so we can reach you."
        
        is_valid, error_msg = validate_contact(contact)
        if not is_valid:
            return False, error_msg
        
        if not location:
            return False, "Please enter or detect the location."
        if not details:
            return False, "Please describe the situation."

        return True, ""

    async def _get_current_location(self, page) -> None:
        """Get the user's current location using geolocator."""
        try:
            import flet as ft
        except Exception:
            raise RuntimeError("Flet is required for UI actions")
        
        if not GEOLOCATOR_AVAILABLE or self._geolocator is None:
            self._show_location_error(page, "GPS functionality not available. Please enter location manually.")
            return
        
        self._location_btn.visible = False
        self._location_loading.visible = True
        self._location_status.visible = False
        self._error_text.value = ""
        page.update()
        
        try:
            location_enabled = await self._geolocator.is_location_service_enabled_async()
            if not location_enabled:
                self._show_location_error(page, "Location services are disabled. Please enable them.")
                return
            
            permission = await self._geolocator.request_permission_async(wait_timeout=30)
            if permission in (GeolocatorPermissionStatus.DENIED, 
                             GeolocatorPermissionStatus.DENIED_FOREVER):
                self._show_location_error(page, "Location permission denied.")
                return
            
            position = await self._geolocator.get_current_position_async(
                accuracy=GeolocatorPositionAccuracy.BEST
            )
            
            if position:
                self._current_coords = (position.latitude, position.longitude)
                address = self.map_service.reverse_geocode(position.latitude, position.longitude)
                
                if address:
                    self._location_field.value = address
                else:
                    self._location_field.value = f"{position.latitude:.6f}, {position.longitude:.6f}"
                
                self._location_status.content = ft.Icon(ft.Icons.CHECK_CIRCLE, color=ft.Colors.GREEN_600, size=20)
                self._location_status.tooltip = "Location detected successfully"
                self._location_status.visible = True
                
                show_snackbar(page, "📍 Location detected successfully!")
            else:
                self._show_location_error(page, "Could not determine your position.")
        
        except Exception as exc:
            self._show_location_error(page, f"Location error: {str(exc)}")
        finally:
            self._location_btn.visible = True
            self._location_loading.visible = False
            page.update()
    
    def _show_location_error(self, page, message: str) -> None:
        """Show location error."""
        try:
            import flet as ft
        except Exception:
            return
        
        self._location_status.content = ft.Icon(ft.Icons.WARNING_AMBER, color=ft.Colors.ORANGE_700, size=20)
        self._location_status.tooltip = message
        self._location_status.visible = True
        self._location_btn.visible = True
        self._location_loading.visible = False
        show_snackbar(page, message, error=True)
        page.update()
    
    def _handle_geolocator_error(self, page, error) -> None:
        """Handle geolocator errors."""
        self._show_location_error(page, f"Location error: {error.data}")

    def _on_submit(self, page) -> None:
        """Validate form and show confirmation dialog before submitting."""
        try:
            import flet as ft
        except Exception:
            raise RuntimeError("Flet is required for UI actions")

        is_valid, error_msg = self._validate_form()
        if not is_valid:
            self._error_text.value = error_msg
            page.update()
            return
        
        animal_type = (self._type_dropdown.value or "").strip()
        breed = (self._breed_field.value or "").strip() or "Not specified"
        urgency_label = (self._urgency_dropdown.value or "").strip()
        reporter_name = (self._name_field.value or "").strip()
        contact = (self._contact_field.value or "").strip()
        location = (self._location_field.value or "").strip()
        details = (self._details_field.value or "").strip()
        
        def close_dialog(e):
            page.close(dialog)
        
        def confirm_submit(e):
            page.close(dialog)
            page.run_task(self._on_submit_async, page)
        
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Icon(ft.Icons.WARNING_AMBER, color=ft.Colors.RED_700, size=24),
                ft.Text("Confirm Emergency Report", weight="bold", size=18),
            ], spacing=8),
            content=ft.Container(
                ft.Column([
                    ft.Text(
                        "Please verify your emergency report details. Once submitted, you cannot edit or cancel this report.",
                        size=13,
                        color=ft.Colors.RED_700,
                        weight="w500",
                    ),
                    ft.Container(height=10),
                    ft.Divider(height=1, color=ft.Colors.GREY_300),
                    ft.Container(height=10),
                    # Summary of inputs
                    ft.Row([ft.Text("Animal Type:", weight="w600", size=12, width=100), ft.Text(animal_type, size=12)]),
                    ft.Row([ft.Text("Breed:", weight="w600", size=12, width=100), ft.Text(breed, size=12)]),
                    ft.Row([ft.Text("Urgency:", weight="w600", size=12, width=100), ft.Text(urgency_label, size=12)]),
                    ft.Row([ft.Text("Your Name:", weight="w600", size=12, width=100), ft.Text(reporter_name, size=12)]),
                    ft.Row([ft.Text("Contact:", weight="w600", size=12, width=100), ft.Text(contact, size=12)]),
                    ft.Row([ft.Text("Location:", weight="w600", size=12, width=100), ft.Text(location[:50] + "..." if len(location) > 50 else location, size=12)], vertical_alignment=ft.CrossAxisAlignment.START),
                    ft.Row([ft.Text("Details:", weight="w600", size=12, width=100), ft.Text(details[:80] + "..." if len(details) > 80 else details, size=12)], vertical_alignment=ft.CrossAxisAlignment.START),
                    ft.Container(height=10),
                    ft.Text(
                        "Is the information above correct?",
                        size=13,
                        italic=True,
                    ),
                ], spacing=4, tight=True),
                width=400,
                padding=10,
            ),
            actions=[
                ft.TextButton("Go Back & Edit", on_click=close_dialog),
                ft.ElevatedButton(
                    "Confirm & Submit",
                    on_click=confirm_submit,
                    style=ft.ButtonStyle(
                        bgcolor=ft.Colors.RED_600,
                        color=ft.Colors.WHITE,
                    ),
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        page.open(dialog)
    
    async def _on_submit_async(self, page) -> None:
        """Async version of submit."""
        try:
            import flet as ft
        except Exception:
            raise RuntimeError("Flet is required for UI actions")

        # Disable submit button
        self._submit_btn.disabled = True
        self._submit_btn.content = ft.Row(
            [ft.ProgressRing(width=18, height=18, stroke_width=2, color=ft.Colors.WHITE), 
             ft.Text("Submitting...", size=14, weight="w600")],
            spacing=8,
            alignment=ft.MainAxisAlignment.CENTER,
        )
        self._error_text.value = ""
        page.update()

        is_valid, error_msg = self._validate_form()
        if not is_valid:
            self._error_text.value = error_msg
            self._reset_submit_button(page)
            return

        try:
            animal_type = (self._type_dropdown.value or "").strip()
            breed = (self._breed_field.value or "").strip() or None
            urgency_label = (self._urgency_dropdown.value or "").strip()
            reporter_name = (self._name_field.value or "").strip()
            contact = (self._contact_field.value or "").strip()
            location = (self._location_field.value or "").strip()
            details = (self._details_field.value or "").strip()
            
            # Convert urgency label to code
            urgency = Urgency.from_label(urgency_label)

            animal_photo = None
            if self._photo_widget and self._photo_widget.has_photo():
                from datetime import datetime
                photo_name = f"{animal_type.lower()}_emergency_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                animal_photo = self._photo_widget.save_with_name(photo_name)
                if animal_photo:
                    print(f"[INFO] Saved emergency rescue photo: {animal_photo}")



            if self._current_coords:
                latitude, longitude = self._current_coords
            else:
                loop = asyncio.get_event_loop()
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    coords = await loop.run_in_executor(
                        pool, 
                        self.map_service.geocode_location, 
                        location
                    )
                
                if coords:
                    latitude = coords[0]
                    longitude = coords[1]
                else:
                    # Location could not be geocoded - show error and don't save
                    self._error_text.value = "Location not found. Please enter a valid address or use the GPS button to detect your location."
                    show_snackbar(page, "❌ Could not find location. Please enter a valid address.", error=True)
                    self._reset_submit_button(page)
                    return

            # Submit rescue request with proper columns (user_id=None for anonymous)
            mission_id = self.rescue_service.submit_rescue_request(
                user_id=None,  # Anonymous report
                location=location,
                animal_type=animal_type,
                breed=breed,
                name=None,  # Animal name assigned by admin later
                details=details,  # Just the description
                status=RescueStatus.PENDING,  # All new reports start as Pending (admin hasn't reviewed yet)
                latitude=latitude,
                longitude=longitude,
                reporter_name=reporter_name,
                reporter_phone=contact,
                urgency=urgency,
                animal_photo=animal_photo,
            )


            self._current_coords = None

            def close_dialog(e):
                page.close(success_dialog)
                page.go("/")

            success_dialog = ft.AlertDialog(
                modal=True,
                title=ft.Row([
                    ft.Icon(ft.Icons.CHECK_CIRCLE, color=ft.Colors.GREEN_600, size=28),
                    ft.Text("Report Submitted!", weight="w600"),
                ], spacing=10),
                content=ft.Column([
                    ft.Text(
                        f"Your emergency report has been submitted successfully!",
                        size=14,
                    ),
                    ft.Container(height=10),
                    ft.Text(
                        f"Reference ID: #{mission_id}",
                        size=16,
                        weight="w600",
                        color=ft.Colors.TEAL_700,
                    ),
                    ft.Container(height=10),
                    ft.Text(
                        "We will contact you at the provided contact information.",
                        size=12,
                        color=ft.Colors.GREY_600,
                    ),
                ], tight=True, spacing=5),
                actions=[
                    ft.TextButton("OK", on_click=close_dialog),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )
            page.open(success_dialog)

        except Exception as exc:
            self._error_text.value = f"Error: {str(exc)}"
            self._reset_submit_button(page)
    
    def _reset_submit_button(self, page) -> None:
        """Reset the submit button."""
        try:
            import flet as ft
        except Exception:
            return
        
        self._submit_btn.disabled = False
        self._submit_btn.content = ft.Row(
            [ft.Icon(ft.Icons.EMERGENCY, size=15), ft.Text("Submit Emergency Report", size=12, weight="w600")],
            spacing=8,
            alignment=ft.MainAxisAlignment.CENTER,
        )
        page.update()
    
    def _handle_ai_analyze(self, photo_base64: str) -> None:
        """Handle AI analyze button click - runs classification in background thread with progress."""
        import threading
        if self._ai_loading:
            return
        
        from services.ai_classification_service import get_ai_classification_service
        service = get_ai_classification_service()
        status = service.get_download_status()
        
        all_downloaded = all(status.values())
        if not all_downloaded:
            # Models not downloaded, show download dialog
            from components.ai_download_dialog import create_ai_download_dialog
            def on_download_complete(success: bool):
                if success:
                    # Proceed with classification after download
                    self._start_classification(photo_base64)
            
            create_ai_download_dialog(self._page, on_complete=on_download_complete)
            return
        
        # Models already downloaded, proceed with classification
        self._start_classification(photo_base64)
    
    def _start_classification(self, photo_base64: str) -> None:
        """Start the classification process after models are confirmed downloaded."""
        import threading
        if self._ai_loading:
            return
        
        self._ai_loading = True
        
        self._ai_suggestion_container.content = create_ai_loading_card()
        self._ai_suggestion_container.visible = True
        self._page.update()
        
        def classify():
            try:
                from services.ai_classification_service import get_ai_classification_service
                service = get_ai_classification_service()
                result = service.classify_image(photo_base64)
                
                self._page.run_thread(lambda: self._on_ai_result(result))
            except Exception as e:
                print(f"[AI] Classification error: {e}")
                from models.classification_result import ClassificationResult
                error_result = ClassificationResult.from_error(str(e))
                self._page.run_thread(lambda: self._on_ai_result(error_result))
        
        thread = threading.Thread(target=classify, daemon=True)
        thread.start()
    
    def _on_ai_result(self, result) -> None:
        """Handle AI classification result - called on main thread."""
        self._ai_loading = False
        self._ai_result = result
        
        self._ai_suggestion_container.content = create_ai_suggestion_card(
            result=result,
            on_accept=self._accept_ai_suggestion,
            on_dismiss=self._dismiss_ai_suggestion,
        )
        self._ai_suggestion_container.visible = True
        self._page.update()
    
    def _accept_ai_suggestion(self, species: str, breed: str) -> None:
        """Accept the AI suggestion and fill in the form fields."""
        import flet as ft
        
        # Map species to dropdown value
        species_map = {"Dog": "Dog", "Cat": "Cat", "Other": "Other"}
        dropdown_value = species_map.get(species, "Other")
        
        if self._type_dropdown:
            self._type_dropdown.value = dropdown_value
        
        if self._breed_field and breed and breed != "Not Applicable":
            self._breed_field.value = breed
        
        # Hide the suggestion card
        self._ai_suggestion_container.visible = False
        self._ai_suggestion_container.content = None
        
        breed_text = f" - {breed}" if breed and breed != "Not Applicable" else ""
        show_snackbar(self._page, f"✅ Set animal type to {species}{breed_text}")
        
        self._page.update()
    
    def _dismiss_ai_suggestion(self) -> None:
        """Dismiss the AI suggestion and allow manual entry."""
        self._ai_suggestion_container.visible = False
        self._ai_suggestion_container.content = None
        self._ai_result = None
        self._page.update()


__all__ = ["EmergencyRescuePage"]
