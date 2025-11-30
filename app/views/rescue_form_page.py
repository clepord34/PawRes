"""Form page for submitting rescue mission requests."""
from __future__ import annotations
from typing import Optional
import asyncio
import concurrent.futures

import app_config
from services.rescue_service import RescueService
from services.map_service import MapService
from state import get_app_state
from components import (
    create_page_header, create_content_card, create_action_button, create_gradient_background,
    create_form_text_field, create_form_dropdown, show_snackbar
)


class RescueFormPage:
    def __init__(self, db_path: Optional[str] = None) -> None:
        self.rescue_service = RescueService(db_path or app_config.DB_PATH)
        self.map_service = MapService()
        self._type_dropdown: Optional[object] = None
        self._urgency_dropdown: Optional[object] = None
        self._name_field: Optional[object] = None
        self._location_field: Optional[object] = None
        self._details_field: Optional[object] = None
        self._error_text: Optional[object] = None
        self._submit_btn: Optional[object] = None
        self._location_btn: Optional[object] = None
        self._location_status: Optional[object] = None
        self._location_loading: Optional[object] = None
        self._geolocator: Optional[object] = None
        self._current_coords: Optional[tuple] = None  # Store (lat, lng) for submission

    def build(self, page) -> None:
        try:
            import flet as ft
        except Exception as exc:
            raise RuntimeError("Flet must be installed to build the UI") from exc

        page.title = "Report Rescue Mission"

        # Header with logo
        header = create_page_header("Paw Rescue")
        
        # Animal type dropdown
        self._type_dropdown = create_form_dropdown(
            label="Animal Type",
            options=["Dog", "Cat", "Bird", "Other"],
            width=400,
        )
        
        # Urgency level dropdown
        self._urgency_dropdown = create_form_dropdown(
            label="Urgency Level",
            options=["Low - Animal appears safe", "Medium - Needs attention soon", "High - Immediate help needed"],
            width=400,
        )

        # Reporter name field
        self._name_field = create_form_text_field(
            label="Your Name", 
            hint_text="Enter your full name",
            width=400,
        )
        
        # Location field with improved styling
        self._location_field = create_form_text_field(
            label="Location",
            hint_text="Enter address or use GPS button →",
            width=330,
        )
        
        # Location status indicator (checkmark or warning)
        self._location_status = ft.Container(
            content=ft.Icon(ft.Icons.CHECK_CIRCLE, color=ft.Colors.GREEN_600, size=20),
            visible=False,
            tooltip="Location verified",
        )
        
        # Loading indicator for location
        self._location_loading = ft.Container(
            content=ft.ProgressRing(width=20, height=20, stroke_width=2, color=ft.Colors.TEAL_600),
            visible=False,
        )
        
        # Create geolocator control for getting current location
        self._geolocator = ft.Geolocator(
            on_error=lambda e: self._handle_geolocator_error(page, e),
        )
        page.overlay.append(self._geolocator)
        
        # GPS Button to get current location
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
        
        # Location row with field, status, and GPS button
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
            width=400,
        )

        # Error display (only for actual errors, not loading states)
        self._error_text = ft.Text("", color=ft.Colors.RED_600, size=12, text_align=ft.TextAlign.CENTER)

        # Submit and cancel buttons
        self._submit_btn = ft.ElevatedButton(
            content=ft.Row(
                [ft.Icon(ft.Icons.SEND, size=18), ft.Text("Submit Report", size=14, weight="w500")],
                spacing=8,
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            width=160,
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
            on_click=lambda e: page.go("/user"),
            style=ft.ButtonStyle(
                color=ft.Colors.GREY_700,
                shape=ft.RoundedRectangleBorder(radius=10),
                side=ft.BorderSide(1.5, ft.Colors.GREY_400),
            )
        )
        
        # Form sections for better organization
        animal_section = ft.Column([
            ft.Row([
                ft.Icon(ft.Icons.PETS, color=ft.Colors.TEAL_700, size=20),
                ft.Text("Animal Information", size=14, weight="w600", color=ft.Colors.TEAL_700),
            ], spacing=8),
            self._type_dropdown,
            self._urgency_dropdown,
        ], spacing=12)
        
        reporter_section = ft.Column([
            ft.Row([
                ft.Icon(ft.Icons.PERSON, color=ft.Colors.TEAL_700, size=20),
                ft.Text("Reporter Details", size=14, weight="w600", color=ft.Colors.TEAL_700),
            ], spacing=8),
            self._name_field,
        ], spacing=12)
        
        location_section = ft.Column([
            ft.Row([
                ft.Icon(ft.Icons.LOCATION_ON, color=ft.Colors.TEAL_700, size=20),
                ft.Text("Location", size=14, weight="w600", color=ft.Colors.TEAL_700),
            ], spacing=8),
            location_row,
            location_helper,
        ], spacing=8)
        
        details_section = ft.Column([
            ft.Row([
                ft.Icon(ft.Icons.DESCRIPTION, color=ft.Colors.TEAL_700, size=20),
                ft.Text("Additional Details", size=14, weight="w600", color=ft.Colors.TEAL_700),
            ], spacing=8),
            self._details_field,
        ], spacing=12)
        
        # Card container with improved layout
        card = ft.Container(
            ft.Column([
                # Title section
                ft.Container(
                    ft.Column([
                        ft.Row([
                            ft.Icon(ft.Icons.EMERGENCY, color=ft.Colors.ORANGE_700, size=28),
                            ft.Text("Report Rescue Mission", size=24, weight="bold", color=ft.Colors.BLACK87),
                        ], alignment=ft.MainAxisAlignment.CENTER, spacing=10),
                        ft.Text("Help us locate and rescue animals in need", size=13, color=ft.Colors.GREY_600),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=4),
                    padding=ft.padding.only(bottom=10),
                ),
                ft.Divider(height=1, color=ft.Colors.GREY_300),
                ft.Container(height=10),  # Spacer
                
                # Form sections
                animal_section,
                ft.Container(height=8),
                reporter_section,
                ft.Container(height=8),
                location_section,
                ft.Container(height=8),
                details_section,
                
                ft.Container(height=15),  # Spacer before buttons
                
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
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, alignment=ft.MainAxisAlignment.START, expand=True, spacing=15, scroll=ft.ScrollMode.AUTO)

        page.controls.clear()
        page.add(create_gradient_background(layout))
        page.update()

    def _validate_form(self) -> tuple[bool, str]:
        """Validate form fields. Return (is_valid, error_message)."""
        animal_type = (self._type_dropdown.value or "").strip()
        urgency = (self._urgency_dropdown.value or "").strip()
        name = (self._name_field.value or "").strip()
        location = (self._location_field.value or "").strip()
        details = (self._details_field.value or "").strip()

        if not animal_type:
            return False, "Please select an animal type."
        if not urgency:
            return False, "Please select an urgency level."
        if not name:
            return False, "Please enter your name."
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
        
        # Show loading state
        self._location_btn.visible = False
        self._location_loading.visible = True
        self._location_status.visible = False
        self._error_text.value = ""
        page.update()
        
        try:
            # Check if location service is enabled
            location_enabled = await self._geolocator.is_location_service_enabled_async()
            if not location_enabled:
                self._show_location_error(page, "Location services are disabled. Please enable them in your device settings.")
                return
            
            # Request permission
            permission = await self._geolocator.request_permission_async(wait_timeout=30)
            if permission in (ft.GeolocatorPermissionStatus.DENIED, 
                             ft.GeolocatorPermissionStatus.DENIED_FOREVER):
                self._show_location_error(page, "Location permission denied. Please grant access in settings.")
                return
            
            # Get current position
            position = await self._geolocator.get_current_position_async(
                accuracy=ft.GeolocatorPositionAccuracy.BEST
            )
            
            if position:
                # Store coordinates for submission
                self._current_coords = (position.latitude, position.longitude)
                
                # Try to reverse geocode to get address
                address = self.map_service.reverse_geocode(position.latitude, position.longitude)
                
                if address:
                    self._location_field.value = address
                else:
                    # Fallback to coordinates if reverse geocoding fails
                    self._location_field.value = f"{position.latitude:.6f}, {position.longitude:.6f}"
                
                # Show success indicator
                self._location_status.content = ft.Icon(ft.Icons.CHECK_CIRCLE, color=ft.Colors.GREEN_600, size=20)
                self._location_status.tooltip = "Location detected successfully"
                self._location_status.visible = True
                
                show_snackbar(page, "📍 Location detected successfully!")
            else:
                self._show_location_error(page, "Could not determine your position. Please try again or enter manually.")
        
        except Exception as exc:
            self._show_location_error(page, f"Location error: {str(exc)}")
        finally:
            # Restore button state
            self._location_btn.visible = True
            self._location_loading.visible = False
            page.update()
    
    def _show_location_error(self, page, message: str) -> None:
        """Show location error with warning indicator."""
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
        """Validate and submit the form."""
        # Run the async submit in a task
        page.run_task(self._on_submit_async, page)
    
    async def _on_submit_async(self, page) -> None:
        """Async version of submit to prevent UI blocking during geocoding."""
        try:
            import flet as ft
        except Exception:
            raise RuntimeError("Flet is required for UI actions")

        # Disable submit button and show loading state
        self._submit_btn.disabled = True
        self._submit_btn.content = ft.Row(
            [ft.ProgressRing(width=18, height=18, stroke_width=2, color=ft.Colors.WHITE), 
             ft.Text("Submitting...", size=14, weight="w500")],
            spacing=8,
            alignment=ft.MainAxisAlignment.CENTER,
        )
        self._error_text.value = ""
        page.update()

        # Validate form
        is_valid, error_msg = self._validate_form()
        if not is_valid:
            self._error_text.value = error_msg
            self._submit_btn.disabled = False
            self._submit_btn.content = ft.Row(
                [ft.Icon(ft.Icons.SEND, size=18), ft.Text("Submit Report", size=14, weight="w500")],
                spacing=8,
                alignment=ft.MainAxisAlignment.CENTER,
            )
            page.update()
            return

        try:
            # Extract form data
            animal_type = (self._type_dropdown.value or "").strip()
            urgency = (self._urgency_dropdown.value or "").strip()
            name = (self._name_field.value or "").strip()
            location = (self._location_field.value or "").strip()
            details = (self._details_field.value or "").strip()
            
            # Add urgency to details
            full_details = f"[Urgency: {urgency}]\n\n{details}"

            # Get user_id from centralized state management
            app_state = get_app_state()
            user_id = app_state.auth.user_id
            if not user_id:
                self._error_text.value = "Session expired. Please log in again."
                self._reset_submit_button(page)
                return

            print(f"[DEBUG] Submitting rescue request for user_id={user_id}, animal_type={animal_type}")

            # Use stored coordinates from geolocator if available, otherwise try to geocode
            if self._current_coords:
                latitude, longitude = self._current_coords
                print(f"[DEBUG] Using geolocator coordinates: lat={latitude}, lng={longitude}")
            else:
                # Try to geocode the location in a thread pool to not block UI
                loop = asyncio.get_event_loop()
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    coords = await loop.run_in_executor(
                        pool, 
                        self.map_service.geocode_location, 
                        location
                    )
                latitude = coords[0] if coords else None
                longitude = coords[1] if coords else None
                
                if coords:
                    print(f"[DEBUG] Geocoded location to lat={latitude}, lng={longitude}")
                else:
                    print(f"[DEBUG] Could not geocode location, storing without coordinates")

            # Submit rescue request
            mission_id = self.rescue_service.submit_rescue_request(
                user_id=user_id,
                location=location,
                animal_type=animal_type,
                name=name,
                details=full_details,
                status="pending",
                latitude=latitude,
                longitude=longitude,
            )

            print(f"[DEBUG] Rescue mission created with ID={mission_id}")

            # Reset stored coordinates after successful submission
            self._current_coords = None

            # Show success
            show_snackbar(page, "✅ Rescue mission submitted successfully!")

            # Navigate to check status
            page.go(f"/check_status?mission_id={mission_id}")

        except Exception as exc:
            self._error_text.value = f"Error: {str(exc)}"
            self._reset_submit_button(page)
    
    def _reset_submit_button(self, page) -> None:
        """Reset the submit button to its original state."""
        try:
            import flet as ft
        except Exception:
            return
        
        self._submit_btn.disabled = False
        self._submit_btn.content = ft.Row(
            [ft.Icon(ft.Icons.SEND, size=18), ft.Text("Submit Report", size=14, weight="w500")],
            spacing=8,
            alignment=ft.MainAxisAlignment.CENTER,
        )
        page.update()


__all__ = ["RescueFormPage"]

