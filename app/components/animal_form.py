"""Shared animal form component for Add and Edit Animal pages."""
from __future__ import annotations

import threading
from typing import Optional, Callable, Dict, Any

try:
    import flet as ft
except ImportError:
    ft = None # type: ignore

from components.form_fields import create_form_text_field, create_form_dropdown
from components.photo_upload import create_photo_upload_widget
from services.photo_service import load_photo


class AnimalFormWidget:
    """Reusable animal form widget for both Add and Edit pages.
    
    This widget provides a consistent form layout with:
    - Photo upload section
    - Animal type dropdown
    - Name field
    - Age field (optional)
    - Health status dropdown
    - Action buttons
    """
    
    def __init__(
        self,
        page,
        mode: str = "add",  # "add" or "edit"
        animal_data: Optional[Dict[str, Any]] = None,
        on_submit: Optional[Callable[[Dict[str, Any]], None]] = None,
        on_cancel: Optional[Callable[[], None]] = None,
        rescue_info: Optional[Dict[str, Any]] = None,
        on_bulk_import: Optional[Callable[[], None]] = None,
    ):
        """Initialize the animal form widget.
        
        Args:
            page: Flet page instance
            mode: "add" for new animals, "edit" for existing animals
            animal_data: Existing animal data (for edit mode)
            on_submit: Callback when form is submitted with form data dict
            on_cancel: Callback when cancel/back is clicked
            rescue_info: Optional rescue mission info for rescued animals
            on_bulk_import: Optional callback for bulk import button (add mode only)
        """
        if ft is None:
            raise RuntimeError("Flet must be installed")
        
        self.page = page
        self.mode = mode
        self.animal_data = animal_data or {}
        self.on_submit_callback = on_submit
        self.on_cancel_callback = on_cancel
        self.on_bulk_import_callback = on_bulk_import
        self.rescue_info = rescue_info
        
        # Form fields
        self._type_dropdown = None
        self._name_field = None
        self._breed_field = None
        self._age_dropdown = None
        self._health_dropdown = None
        self._photo_widget = None
        self._error_text = None
        self._submit_btn = None
        
        # AI classification
        self._ai_suggestion_container = None
        self._ai_result = None
        self._ai_loading = False
        self._accepted_breed = None  # Store accepted breed from AI suggestion
        
        # For edit mode photo handling
        self._existing_photo_base64 = None
        self._file_picker = None
        self._photo_display = None
        self._pending_image_bytes = None
        self._pending_original_name = None
        self._current_photo_base64 = None
        self._ai_button = None
    
    def build(self) -> object:
        """Build and return the form container."""
        is_edit = self.mode == "edit"
        
        # Title section with icon
        if is_edit:
            title_icon = ft.Icons.EDIT
            title_text = "Edit Animal"
            subtitle_text = "Update animal information"
        else:
            title_icon = ft.Icons.PETS
            title_text = "Add New Animal"
            subtitle_text = "Register a new animal in the system"
        
        title_section = ft.Container(
            ft.Column([
                ft.Icon(title_icon, color=ft.Colors.TEAL_700, size=28),
                ft.Text(title_text, size=22, weight="bold", color=ft.Colors.BLACK87, text_align=ft.TextAlign.CENTER),
                ft.Text(subtitle_text, size=13, color=ft.Colors.GREY_600, text_align=ft.TextAlign.CENTER),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=6),
            padding=ft.padding.only(bottom=10),
        )
        
        # Photo section
        photo_section = self._build_photo_section()
        
        # AI suggestion container (initially empty)
        self._ai_suggestion_container = ft.Container(content=None, visible=False)
        
        # Animal details section
        details_section = self._build_details_section()
        
        # Error text (hidden until there is a validation error)
        self._error_text = ft.Text("", color=ft.Colors.RED_600, size=12, text_align=ft.TextAlign.CENTER, visible=False)
        
        # Action buttons
        buttons_section = self._build_buttons_section()
        
        card_content = ft.Column([
            title_section,
            ft.Divider(height=1, color=ft.Colors.GREY_300),
            ft.Container(height=12),
            photo_section,
            ft.Container(height=8),
            self._ai_suggestion_container,
            details_section,
            self._error_text,
            ft.Container(height=4),
            buttons_section,
        ], spacing=8, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        
        # Card container
        card = ft.Container(
            card_content,
            padding=ft.padding.symmetric(horizontal=24, vertical=28),
            bgcolor=ft.Colors.WHITE,
            border_radius=16,
            shadow=ft.BoxShadow(
                blur_radius=25,
                spread_radius=2,
                color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK),
                offset=(0, 8)
            ),
            width=480,  # acts as max_width in centered layout
        )
        
        if self.rescue_info:
            rescue_info_btn = self._create_rescue_info_button()
            return ft.Stack([
                card,
                ft.Container(
                    rescue_info_btn,
                    right=10,
                    top=10,
                ),
            ])
        
        return card
    
    def _build_photo_section(self):
        """Build the photo upload section."""
        if self.mode == "edit":
            # For edit mode, handle existing photo
            existing_photo = self.animal_data.get("photo")
            self._existing_photo_base64 = load_photo(existing_photo) if existing_photo else None
            
            if self._existing_photo_base64:
                self._photo_display = ft.Container(
                    content=ft.Image(
                        src_base64=self._existing_photo_base64,
                        width=120,
                        height=120,
                        fit=ft.ImageFit.COVER,
                        border_radius=8,
                    ),
                    width=120,
                    height=120,
                    border_radius=8,
                )
            else:
                self._photo_display = ft.Container(
                    ft.Icon(ft.Icons.ADD_A_PHOTO, size=40, color=ft.Colors.GREY_400),
                    width=120,
                    height=120,
                    bgcolor=ft.Colors.GREY_200,
                    border_radius=8,
                    alignment=ft.alignment.center,
                )
            
            # File picker for edit mode
            def on_file_picked(e):
                if e.files and len(e.files) > 0:
                    file_info = e.files[0]
                    file_path = file_info.path
                    original_name = file_info.name
                    
                    if not file_path:
                        return
                    
                    try:
                        import base64
                        import os
                        
                        if not os.path.exists(file_path):
                            return
                        
                        with open(file_path, "rb") as image_file:
                            image_bytes = image_file.read()
                        
                        self._pending_image_bytes = image_bytes
                        self._pending_original_name = original_name
                        
                        photo_b64 = base64.b64encode(image_bytes).decode()
                        self._current_photo_base64 = photo_b64
                        self._photo_display.content = ft.Image(
                            src_base64=photo_b64,
                            width=120,
                            height=120,
                            fit=ft.ImageFit.COVER,
                            border_radius=8,
                        )
                        
                        # Clear AI suggestion when new photo is selected
                        self._clear_ai_suggestion()
                        
                        # Enable AI button now that we have a photo
                        if self._ai_button:
                            self._ai_button.disabled = False
                            self._ai_button.bgcolor = ft.Colors.TEAL_600
                            self._ai_button.color = ft.Colors.WHITE
                        
                        self.page.update()
                    except Exception:
                        pass
            
            self._file_picker = ft.FilePicker(on_result=on_file_picked)
            self.page.overlay.append(self._file_picker)
            
            photo_button = ft.ElevatedButton(
                "Change Photo",
                icon=ft.Icons.CAMERA_ALT,
                on_click=lambda e: self._file_picker.pick_files(
                    allowed_extensions=["jpg", "jpeg", "png", "gif"],
                    dialog_title="Select Animal Photo"
                ),
                style=ft.ButtonStyle(
                    bgcolor=ft.Colors.WHITE,
                    color=ft.Colors.TEAL_700,
                    shape=ft.RoundedRectangleBorder(radius=8),
                    side=ft.BorderSide(1, ft.Colors.TEAL_400),
                )
            )
            
            self._current_photo_base64 = self._existing_photo_base64
            
            # AI analyze button for edit mode
            from components.ai_suggestion_card import create_ai_analyze_button
            self._ai_button = create_ai_analyze_button(
                on_click=lambda: self._handle_ai_analyze(self._current_photo_base64) if self._current_photo_base64 else None,
                disabled=not self._current_photo_base64,
            )
            ai_button = self._ai_button
            
            photo_container = ft.Column([
                self._photo_display,
                ft.Container(height=8),
                ft.Row([photo_button, ai_button], spacing=8, alignment=ft.MainAxisAlignment.CENTER),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0)
        else:
            # For add mode, use photo upload widget with AI callback
            self._photo_widget = create_photo_upload_widget(
                self.page,
                on_ai_analyze=self._handle_ai_analyze,
                show_ai_button=True,
                on_photo_changed=self._clear_ai_suggestion,
            )
            photo_container = self._photo_widget.build()
        
        return ft.Column([
            ft.Row([
                ft.Icon(ft.Icons.PHOTO_CAMERA, color=ft.Colors.TEAL_700, size=20),
                ft.Text("Animal Photo", size=14, weight="w600", color=ft.Colors.TEAL_700),
            ], spacing=8),
            ft.Container(height=8),
            ft.Container(photo_container, alignment=ft.alignment.center),
        ], spacing=0)
    
    def _handle_ai_analyze(self, photo_base64: str):
        """Handle AI analyze button click - runs classification in background thread with progress."""
        if self._ai_loading:
            return
        
        from services.ai_classification_service import get_ai_classification_service
        service = get_ai_classification_service()
        download_status = service.get_download_status()
        
        # If models not downloaded, show download dialog
        if not all(download_status.values()):
            from components.ai_download_dialog import create_ai_download_dialog
            
            def on_download_complete(success: bool):
                """Called after download completes."""
                if success:
                    # Start classification after successful download
                    self._handle_ai_analyze(photo_base64)
            
            create_ai_download_dialog(self.page, on_complete=on_download_complete)
            return
        
        self._ai_loading = True
        
        from components.ai_suggestion_card import create_ai_loading_card
        self._ai_suggestion_container.content = create_ai_loading_card()
        self._ai_suggestion_container.visible = True
        self.page.update()
        
        def classify():
            try:
                result = service.classify_image(photo_base64)
                
                self.page.run_thread(lambda: self._on_ai_result(result))
            except Exception as e:
                print(f"[AI] Classification error: {e}")
                from models.classification_result import ClassificationResult
                error_result = ClassificationResult.from_error(str(e))
                self.page.run_thread(lambda: self._on_ai_result(error_result))
        
        thread = threading.Thread(target=classify, daemon=True)
        thread.start()
    
    def _on_ai_result(self, result):
        """Handle AI classification result - called on main thread."""
        self._ai_loading = False
        self._ai_result = result
        
        from components.ai_suggestion_card import create_ai_suggestion_card
        
        self._ai_suggestion_container.content = create_ai_suggestion_card(
            result=result,
            on_accept=self._accept_ai_suggestion,
            on_dismiss=self._dismiss_ai_suggestion,
        )
        self._ai_suggestion_container.visible = True
        self.page.update()
    
    def _accept_ai_suggestion(self, species: str, breed: str):
        """Accept the AI suggestion and fill in the form fields."""
        # Map species to dropdown value
        species_map = {"Dog": "Dog", "Cat": "Cat", "Other": "Other"}
        dropdown_value = species_map.get(species, "Other")
        
        if self._type_dropdown:
            self._type_dropdown.value = dropdown_value
        
        self._accepted_breed = breed
        if self._breed_field and breed and breed != "Not Applicable":
            self._breed_field.value = breed
        
        # If breed is a specific name (not mixed breed placeholder), suggest it for the name
        # Only suggest name if it's empty and breed is specific
        if self._name_field and not self._name_field.value:
            # Don't auto-fill name for mixed breeds (Aspin/Puspin)
            if breed and "Mixed Breed" not in breed and breed != "Not Applicable":
                # Just leave name empty - user should name their pet
                pass
        
        # Hide the suggestion card
        self._ai_suggestion_container.visible = False
        self._ai_suggestion_container.content = None
        
        from components.dialogs import show_snackbar
        breed_text = f" - {breed}" if breed and breed != "Not Applicable" else ""
        show_snackbar(self.page, f"✅ Set species to {species}{breed_text}")
        
        self.page.update()
    
    def _dismiss_ai_suggestion(self):
        """Dismiss the AI suggestion and allow manual entry."""
        self._ai_suggestion_container.visible = False
        self._ai_suggestion_container.content = None
        self._ai_result = None
        self.page.update()
    
    def _clear_ai_suggestion(self):
        """Clear AI suggestion when new photo is selected."""
        self._ai_suggestion_container.visible = False
        self._ai_suggestion_container.content = None
        self._ai_result = None
        self._ai_loading = False
        self._accepted_breed = None  # Clear breed when new photo selected
        # Don't call page.update() here - caller will update
    
    def _build_details_section(self):
        """Build the animal details section."""
        # Pre-fill values for edit mode
        species_value = ""
        name_value = ""
        age_value = ""
        status_value = ""
        
        if self.mode == "edit":
            species_value = (self.animal_data.get("species") or "").capitalize()
            if species_value not in ["Dog", "Cat", "Other"]:
                species_value = ""
            name_value = self.animal_data.get("name", "")
            age = self.animal_data.get("age")
            # Convert numeric age to dropdown value
            if age is not None:
                if age == 0:
                    age_value = "Under 1 year"
                else:
                    age_value = f"{age} year{'s' if age != 1 else ''}"
            status_value = self.animal_data.get("status", "")
        
        # Animal type dropdown
        self._type_dropdown = create_form_dropdown(
            label="Animal Type",
            options=["Dog", "Cat", "Other"],
            value=species_value,
        )
        
        # Name field
        self._name_field = create_form_text_field(
            label="Animal Name",
            hint_text="Enter the animal's name",
            value=name_value,
        )
        
        # Breed field (optional - can be set manually or by AI)
        breed_value = self.animal_data.get("breed", "") if self.mode == "edit" else ""
        self._breed_field = create_form_text_field(
            label="Breed (Optional)",
            hint_text="Enter breed or use AI to detect",
            value=breed_value,
        )
        
        # Age dropdown - covers typical lifespan for dogs (10-13 avg, up to 20) and cats (15-20 avg, up to 25+)
        age_options = ["Under 1 year"] + [f"{i} year{'s' if i != 1 else ''}" for i in range(1, 21)] + ["Above 20 years"]
        age_label = "Age" if self.mode == "add" else "Age (Optional)"
        self._age_dropdown = create_form_dropdown(
            label=age_label,
            options=age_options,
            value=age_value,
            menu_height=200,  # Limit dropdown height to show ~5 items
        )
        
        # Health status dropdown
        self._health_dropdown = create_form_dropdown(
            label="Health Status",
            options=["Healthy", "Recovering", "Injured"],
            value=status_value,
        )
        
        return ft.Column([
            ft.Row([
                ft.Icon(ft.Icons.PETS, color=ft.Colors.TEAL_700, size=20),
                ft.Text("Animal Details", size=14, weight="w600", color=ft.Colors.TEAL_700),
            ], spacing=8),
            ft.Container(height=8),
            self._type_dropdown,
            self._name_field,
            self._breed_field,
            self._age_dropdown,
            self._health_dropdown,
        ], spacing=12)
    
    def _build_buttons_section(self):
        """Build the action buttons section."""
        is_edit = self.mode == "edit"
        
        # Submit button with icon
        submit_text = "Save Changes" if is_edit else "Add Animal"
        submit_icon = ft.Icons.SAVE if is_edit else ft.Icons.ADD
        
        self._submit_btn = ft.ElevatedButton(
            content=ft.Row(
                [ft.Icon(submit_icon, size=18), ft.Text(submit_text, size=14, weight="w500")],
                spacing=8,
                alignment=ft.MainAxisAlignment.CENTER,
                tight=True,
            ),
            expand=True,
            height=48,
            on_click=lambda e: self._handle_submit(),
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.TEAL_600,
                color=ft.Colors.WHITE,
                shape=ft.RoundedRectangleBorder(radius=10),
                elevation=2,
            )
        )
        
        # Cancel button
        cancel_text = "Back" if is_edit else "Cancel"
        cancel_btn = ft.OutlinedButton(
            content=ft.Text(cancel_text, size=14, weight="w500"),
            expand=True,
            height=48,
            on_click=lambda e: self._handle_cancel(),
            style=ft.ButtonStyle(
                color=ft.Colors.GREY_700,
                shape=ft.RoundedRectangleBorder(radius=10),
                side=ft.BorderSide(1.5, ft.Colors.GREY_400),
            )
        )
        
        buttons_row = ft.Row(
            [self._submit_btn, cancel_btn],
            spacing=12,
            alignment=ft.MainAxisAlignment.CENTER,
        )
        
        if not is_edit and self.on_bulk_import_callback:
            bulk_import_btn = ft.OutlinedButton(
                content=ft.Row(
                    [ft.Icon(ft.Icons.UPLOAD_FILE, size=16), ft.Text("Bulk Import from File", size=13)],
                    spacing=6,
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                height=38,
                on_click=lambda e: self.on_bulk_import_callback(),
                style=ft.ButtonStyle(
                    color=ft.Colors.TEAL_700,
                    shape=ft.RoundedRectangleBorder(radius=8),
                    side=ft.BorderSide(1, ft.Colors.TEAL_400),
                )
            )
            
            return ft.Column([
                buttons_row,
                ft.Container(height=12),
                ft.Divider(height=1, color=ft.Colors.GREY_300),
                ft.Container(height=12),
                bulk_import_btn,
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0)
        
        return buttons_row
    
    def _create_rescue_info_button(self):
        """Create the rescue info button for rescued animals."""
        info = self.rescue_info
        
        def show_rescue_info(e):
            # Determine source color
            source = info.get("source", "Unknown")
            source_color = ft.Colors.BLUE_600 if source == "User" else ft.Colors.RED_600
            
            content_items = [
                ft.Row([ft.Icon(ft.Icons.LOCATION_ON, size=18, color=ft.Colors.TEAL_600),
                       ft.Text("Location:", weight="w600", size=13)], spacing=8),
                ft.Text(info.get("location", "Unknown"), size=12, color=ft.Colors.BLACK87),
                ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                ft.Row([ft.Icon(ft.Icons.CALENDAR_TODAY, size=18, color=ft.Colors.TEAL_600),
                       ft.Text("Rescue Date:", weight="w600", size=13)], spacing=8),
                ft.Text(info.get("date", "Not recorded"), size=12, color=ft.Colors.BLACK87),
                ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                ft.Row([ft.Icon(ft.Icons.PERSON, size=18, color=ft.Colors.TEAL_600),
                       ft.Text("Reported By:", weight="w600", size=13)], spacing=8),
                ft.Text(info.get("reporter", "Anonymous"), size=12, color=ft.Colors.BLACK87),
                ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                ft.Row([ft.Icon(ft.Icons.PHONE, size=18, color=ft.Colors.TEAL_600),
                       ft.Text("Contact:", weight="w600", size=13)], spacing=8),
                ft.Text(info.get("contact") or "Not provided", size=12, color=ft.Colors.BLACK87),
                ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                ft.Row([ft.Icon(ft.Icons.SOURCE, size=18, color=source_color),
                       ft.Text("Source:", weight="w600", size=13)], spacing=8),
                ft.Text(source, size=12, color=source_color),
                ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                ft.Row([ft.Icon(ft.Icons.WARNING_AMBER, size=18, color=ft.Colors.ORANGE_600),
                       ft.Text("Urgency Level:", weight="w600", size=13)], spacing=8),
                ft.Text(info.get("urgency", "Unknown"), size=12, color=ft.Colors.BLACK87),
            ]
            
            if info.get("description"):
                content_items.extend([
                    ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                    ft.Row([ft.Icon(ft.Icons.DESCRIPTION, size=18, color=ft.Colors.TEAL_600),
                           ft.Text("Description:", weight="w600", size=13)], spacing=8),
                    ft.Text(info["description"], size=12, color=ft.Colors.BLACK87),
                ])
            
            dlg = ft.AlertDialog(
                title=ft.Text(f"Rescue Details: {info.get('name', 'Unknown')}", size=16, weight="bold"),
                content=ft.Container(
                    ft.Column(content_items, spacing=2, tight=True, scroll=ft.ScrollMode.AUTO),
                    width=320,
                    height=380,
                    padding=10,
                ),
                actions=[
                    ft.TextButton("Close", on_click=lambda e: self.page.close(dlg)),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )
            self.page.open(dlg)
        
        return ft.IconButton(
            icon=ft.Icons.INFO_OUTLINE,
            icon_color=ft.Colors.ORANGE_600,
            icon_size=22,
            tooltip="View rescue mission details",
            on_click=show_rescue_info,
        )
    
    def _validate_form(self) -> tuple[bool, str]:
        """Validate form fields. Returns (is_valid, error_message)."""
        animal_type = (self._type_dropdown.value or "").strip()
        name = (self._name_field.value or "").strip()
        age_selection = (self._age_dropdown.value or "").strip()
        health_status = (self._health_dropdown.value or "").strip()
        
        if not animal_type:
            return False, "Please select an animal type."
        if not name:
            return False, "Please enter the animal's name."
        if not health_status:
            return False, "Please select a health status."
        
        # Age validation - required for add mode, optional for edit
        if self.mode == "add" and not age_selection:
            return False, "Please select the animal's age."
        
        return True, ""
    
    def _parse_age_value(self, age_selection: str) -> Optional[int]:
        """Parse age dropdown selection to integer value."""
        if not age_selection:
            return None
        if age_selection == "Under 1 year":
            return 0
        try:
            return int(age_selection.split()[0])
        except (ValueError, IndexError):
            return None
    
    def _handle_submit(self) -> None:
        """Handle form submission."""
        is_valid, error_msg = self._validate_form()
        
        if not is_valid:
            self._error_text.value = error_msg
            self._error_text.visible = True
            self.page.update()
            return
        
        self._error_text.value = ""
        self._error_text.visible = False
        
        # Collect form data
        age_selection = (self._age_dropdown.value or "").strip()
        age = self._parse_age_value(age_selection)
        
        form_data = {
            "type": (self._type_dropdown.value or "").strip(),
            "name": (self._name_field.value or "").strip(),
            "age": age,
            "health_status": (self._health_dropdown.value or "").strip(),
            "breed": (self._breed_field.value or "").strip() or self._accepted_breed,
        }
        
        if self.mode == "add" and self._photo_widget:
            form_data["photo_widget"] = self._photo_widget
        elif self.mode == "edit":
            form_data["pending_image_bytes"] = self._pending_image_bytes
            form_data["pending_original_name"] = self._pending_original_name
        
        if self.on_submit_callback:
            self.on_submit_callback(form_data)
    
    def _handle_cancel(self) -> None:
        """Handle cancel button click."""
        if self.on_cancel_callback:
            self.on_cancel_callback()


def create_animal_form(
    page,
    mode: str = "add",
    animal_data: Optional[Dict[str, Any]] = None,
    on_submit: Optional[Callable[[Dict[str, Any]], None]] = None,
    on_cancel: Optional[Callable[[], None]] = None,
    rescue_info: Optional[Dict[str, Any]] = None,
    on_bulk_import: Optional[Callable[[], None]] = None,
) -> AnimalFormWidget:
    """Create an animal form widget.
    
    Args:
        page: Flet page instance
        mode: "add" or "edit"
        animal_data: Existing animal data for edit mode
        on_submit: Callback with form data dict
        on_cancel: Callback for cancel action
        rescue_info: Optional rescue mission info
        on_bulk_import: Optional callback for bulk import (add mode only)
    
    Returns:
        AnimalFormWidget instance
    """
    return AnimalFormWidget(
        page=page,
        mode=mode,
        animal_data=animal_data,
        on_submit=on_submit,
        on_cancel=on_cancel,
        rescue_info=rescue_info,
        on_bulk_import=on_bulk_import,
    )


__all__ = ["AnimalFormWidget", "create_animal_form"]
