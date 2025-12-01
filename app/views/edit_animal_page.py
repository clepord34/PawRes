"""Edit Animal Page for updating existing animal records.

Allows admin to edit animal details: type, name, age, and health status.
"""
from __future__ import annotations

from typing import Optional
from urllib.parse import urlparse, parse_qs

import app_config
from services.animal_service import AnimalService
from services.rescue_service import RescueService
from services.photo_service import load_photo
from storage.file_store import get_file_store
from components import (
    create_page_header, create_action_button, create_gradient_background, 
    PhotoUploadWidget, create_photo_upload_widget,
    create_form_text_field, create_form_dropdown, create_form_label, show_snackbar
)


class EditAnimalPage:
    def __init__(self, db_path: Optional[str] = None) -> None:
        self.service = AnimalService(db_path or app_config.DB_PATH)
        self.rescue_service = RescueService(db_path or app_config.DB_PATH)
        self.file_store = get_file_store()
        self._type_dropdown = None
        self._name_field = None
        self._age_field = None
        self._health_dropdown = None
        self._animal_id = None
        self._photo_display = None
        self._file_picker = None
        self._photo_filename = None  # Store filename for database
        self._photo_base64 = None    # Store base64 for display

    def build(self, page, animal_id: Optional[int] = None) -> None:
        """Build the edit animal form on the provided `flet.Page`."""
        try:
            import flet as ft
        except Exception as exc:
            raise RuntimeError("Flet is required") from exc

        page.title = "Edit Animal"

        # If animal_id not provided, try to get it from query params
        if animal_id is None:
            parsed = urlparse(page.route)
            query_params = parse_qs(parsed.query)
            if "id" in query_params:
                try:
                    animal_id = int(query_params["id"][0])
                except (ValueError, IndexError):
                    pass

        if animal_id is None:
            show_snackbar(page, "Error: No animal ID provided", error=True)
            page.go("/animals_list?admin=1")
            return

        self._animal_id = animal_id

        # Fetch animal data
        animals = self.service.get_all_animals()
        animal = next((a for a in animals if a.get("id") == animal_id), None)

        if not animal:
            show_snackbar(page, "Error: Animal not found", error=True)
            page.go("/animals_list?admin=1")
            return

        # Header with logo - smaller and gray
        header = create_page_header("Edit Animal")

        # Store original photo filename for deletion if replaced
        self._original_photo = animal.get('photo')
        self._pending_image_bytes = None
        self._pending_original_name = None

        # File picker for photo selection - defers saving until submit
        def on_file_picked(e: ft.FilePickerResultEvent):
            if e.files and len(e.files) > 0:
                file_info = e.files[0]
                
                file_path = file_info.path
                original_name = file_info.name
                if not file_path:
                    page.open(ft.SnackBar(ft.Text("Unable to access file. Please try again.")))
                    return
                
                try:
                    import base64
                    import os
                    
                    if not os.path.exists(file_path):
                        raise FileNotFoundError(f"File not found: {file_path}")
                    
                    with open(file_path, "rb") as image_file:
                        image_bytes = image_file.read()
                    
                    # Store pending upload (will save on submit with animal name)
                    self._pending_image_bytes = image_bytes
                    self._pending_original_name = original_name
                    self._photo_filename = None  # Clear - will be set on save
                    
                    # Store base64 for immediate display
                    self._photo_base64 = base64.b64encode(image_bytes).decode()
                    
                    self._photo_display.content = ft.Image(
                        src_base64=self._photo_base64,
                        width=100,
                        height=100,
                        fit=ft.ImageFit.COVER,
                        border_radius=8,
                    )
                    show_snackbar(page, f"Photo selected: {original_name}")
                except Exception as ex:
                    import traceback
                    traceback.print_exc()
                    show_snackbar(page, f"Error loading photo: {str(ex)}", error=True)
            else:
                # No files were selected by the user
                show_snackbar(page, "No file selected.")

        self._file_picker = ft.FilePicker(on_result=on_file_picked)
        page.overlay.append(self._file_picker)

        # Photo upload section - show existing photo if available
        # load_photo handles both filename and legacy base64 formats
        existing_photo_base64 = load_photo(animal.get('photo'))
        if existing_photo_base64:
            self._photo_base64 = existing_photo_base64
            self._photo_display = ft.Container(
                content=ft.Image(
                    src_base64=existing_photo_base64,
                    width=100,
                    height=100,
                    fit=ft.ImageFit.COVER,
                    border_radius=8,
                ),
                width=100,
                height=100,
                border_radius=8,
            )
        else:
            self._photo_display = ft.Container(
                width=100,
                height=100,
                bgcolor=ft.Colors.GREY_300,
                border_radius=8,
                alignment=ft.alignment.center,
            )
        
        # Fetch rescue mission info if this animal came from a rescue
        rescue_mission_id = animal.get("rescue_mission_id")
        rescue_info_btn = None
        if rescue_mission_id:
            mission = self.rescue_service.get_mission_by_id(rescue_mission_id)
            if mission:
                # Format rescue date
                rescue_date = mission.get("created_at", "")
                if rescue_date:
                    try:
                        from datetime import datetime
                        if isinstance(rescue_date, str):
                            dt = datetime.fromisoformat(rescue_date.replace('Z', '+00:00'))
                            rescue_date = dt.strftime("%b %d, %Y")
                    except:
                        pass
                
                info_data = {
                    "location": mission.get("location", "Unknown location"),
                    "date": rescue_date,
                    "reporter": mission.get("reporter_name") or "Anonymous",
                    "urgency": (mission.get("urgency") or "unknown").capitalize(),
                    "description": mission.get("notes", ""),
                    "name": animal.get("name", "Unknown"),
                }
                
                def show_rescue_info(e, data=info_data):
                    content_items = [
                        ft.Row([ft.Icon(ft.Icons.LOCATION_ON, size=18, color=ft.Colors.TEAL_600), 
                               ft.Text("Location:", weight="w600", size=13)], spacing=8),
                        ft.Text(data["location"], size=12, color=ft.Colors.BLACK87),
                        ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                        ft.Row([ft.Icon(ft.Icons.CALENDAR_TODAY, size=18, color=ft.Colors.TEAL_600),
                               ft.Text("Rescue Date:", weight="w600", size=13)], spacing=8),
                        ft.Text(data["date"] or "Not recorded", size=12, color=ft.Colors.BLACK87),
                        ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                        ft.Row([ft.Icon(ft.Icons.PERSON, size=18, color=ft.Colors.TEAL_600),
                               ft.Text("Reported By:", weight="w600", size=13)], spacing=8),
                        ft.Text(data["reporter"] or "Anonymous", size=12, color=ft.Colors.BLACK87),
                        ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                        ft.Row([ft.Icon(ft.Icons.WARNING_AMBER, size=18, color=ft.Colors.ORANGE_600),
                               ft.Text("Urgency Level:", weight="w600", size=13)], spacing=8),
                        ft.Text(data["urgency"], size=12, color=ft.Colors.BLACK87),
                    ]
                    
                    if data["description"]:
                        content_items.extend([
                            ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                            ft.Row([ft.Icon(ft.Icons.DESCRIPTION, size=18, color=ft.Colors.TEAL_600),
                                   ft.Text("Description:", weight="w600", size=13)], spacing=8),
                            ft.Text(data["description"], size=12, color=ft.Colors.BLACK87),
                        ])
                    
                    dlg = ft.AlertDialog(
                        title=ft.Text(f"Rescue Details: {data['name']}", size=16, weight="bold"),
                        content=ft.Container(
                            ft.Column(content_items, spacing=2, tight=True, scroll=ft.ScrollMode.AUTO),
                            width=300,
                            height=280,
                            padding=10,
                        ),
                        actions=[
                            ft.TextButton("Close", on_click=lambda e: page.close(dlg)),
                        ],
                        actions_alignment=ft.MainAxisAlignment.END,
                    )
                    page.open(dlg)
                
                rescue_info_btn = ft.IconButton(
                    icon=ft.Icons.INFO_OUTLINE,
                    icon_color=ft.Colors.ORANGE_600,
                    icon_size=20,
                    tooltip="View rescue mission details",
                    on_click=show_rescue_info,
                )

        # Photo container (info button moved to card top-right)
        photo_container = ft.Container(
            ft.Column([
                self._photo_display,
                ft.ElevatedButton(
                    "+ Add Photo",
                    on_click=lambda e: self._file_picker.pick_files(
                        allowed_extensions=["jpg", "jpeg", "png", "gif"],
                        dialog_title="Select Animal Photo"
                    ),
                    style=ft.ButtonStyle(
                        bgcolor=ft.Colors.WHITE,
                        color=ft.Colors.BLACK54,
                        shape=ft.RoundedRectangleBorder(radius=20),
                        side=ft.BorderSide(1, ft.Colors.GREY_400),
                        padding=ft.padding.symmetric(horizontal=20, vertical=8),
                    )
                ),
            ], horizontal_alignment="center", spacing=10),
            padding=ft.padding.only(bottom=15),
        )

        # Pre-fill form with existing data
        # Capitalize species for display and matching dropdown values
        species_value = (animal.get("species") or "").capitalize()
        self._type_dropdown = create_form_dropdown(
            hint_text="Pick Animal",
            options=["Dog", "Cat", "Other"],
            leading_icon=ft.Icons.PETS,
            value=species_value if species_value in ["Dog", "Cat", "Other"] else ""
        )
        
        self._name_field = create_form_text_field(
            hint_text="Enter animal name...",
            value=animal.get("name", "")
        )
        
        # Handle age - show empty if None or not set
        age_value = animal.get("age")
        age_display = str(age_value) if age_value is not None else ""
        self._age_field = create_form_text_field(
            hint_text="Enter animal Age...",
            keyboard_type=ft.KeyboardType.NUMBER,
            value=age_display
        )
        
        self._health_dropdown = create_form_dropdown(
            hint_text="Health Status",
            options=["healthy", "recovering", "injured"],
            leading_icon=ft.Icons.FAVORITE,
            value=animal.get("status", "")
        )

        # Buttons
        back_btn = ft.ElevatedButton(
            "Back to List",
            width=130,
            height=45,
            on_click=lambda e: page.go("/animals_list?admin=1"),
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.WHITE,
                color=ft.Colors.TEAL_600,
                shape=ft.RoundedRectangleBorder(radius=8),
                side=ft.BorderSide(2, ft.Colors.TEAL_600),
                text_style=ft.TextStyle(size=13, weight="w500"),
            )
        )
        
        submit_btn = ft.ElevatedButton(
            "Submit",
            width=130,
            height=45,
            on_click=lambda e: self._on_submit(page, e),
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.TEAL_600,
                color=ft.Colors.WHITE,
                shape=ft.RoundedRectangleBorder(radius=8),
                text_style=ft.TextStyle(size=13, weight="w500"),
            )
        )

        # Labels for fields
        type_label = create_form_label("Animal Type")
        name_label = create_form_label("Animal Name")
        age_label = create_form_label("Age")
        health_label = create_form_label("Health Status")

        card_content = ft.Container(
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
        
        # Wrap card with info button at top right if from rescue mission
        if rescue_info_btn:
            card = ft.Stack([
                card_content,
                ft.Container(
                    rescue_info_btn,
                    right=10,
                    top=10,
                ),
            ])
        else:
            card = card_content

        # Main layout
        layout = ft.Column([
            header,
            card
        ], horizontal_alignment="center", alignment="center", expand=True, spacing=10)

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

        if not animal_type or not name or not health_status:
            show_snackbar(page, "Animal type, name, and health status are required")
            return

        # Age is optional - set to None if not provided
        age = None
        if age_str:
            try:
                age = int(age_str)
                if age < 0:
                    raise ValueError("Age must be non-negative")
            except ValueError:
                show_snackbar(page, "Age must be a valid non-negative number")
                return

        try:
            # Save new photo with animal name if there's a pending upload
            new_photo_filename = None
            if self._pending_image_bytes:
                new_photo_filename = self.file_store.save_bytes(
                    self._pending_image_bytes,
                    original_name=self._pending_original_name or "photo.jpg",
                    validate=True,
                    custom_name=name  # Use animal name in filename
                )
            
            # Get original animal data to check if name changed
            original_animal = self.service.get_animal_by_id(self._animal_id)
            original_name = original_animal.get('name', '') if original_animal else ''
            
            success = self.service.update_animal(
                self._animal_id,
                type=animal_type,
                name=name,
                age=age,
                health_status=health_status
            )
            
            # If photo was updated with new upload, update it through the service
            # The service will delete the old photo file automatically
            if new_photo_filename and success:
                self.service.update_animal_photo(self._animal_id, new_photo_filename)
            elif success and original_name != name and not self._pending_image_bytes:
                # Name changed but no new photo uploaded - rename existing photo file
                existing_photo = self._original_photo
                if existing_photo and not existing_photo.startswith('data:') and len(existing_photo) < 200:
                    # It's a filename, not base64 - rename it
                    try:
                        renamed_filename = self.file_store.rename_file(existing_photo, name)
                        # Update database with new filename
                        self.service.db.execute(
                            "UPDATE animals SET photo = ? WHERE id = ?",
                            (renamed_filename, self._animal_id)
                        )
                        print(f"[INFO] Renamed photo from '{existing_photo}' to '{renamed_filename}'")
                    except Exception as rename_err:
                        print(f"[WARN] Could not rename photo file: {rename_err}")
            
            if success:
                show_snackbar(page, "Animal updated successfully!")
                page.go("/animals_list?admin=1")
            else:
                show_snackbar(page, "Failed to update animal", error=True)
        except Exception as exc:
            show_snackbar(page, f"Error: {str(exc)}", error=True)


__all__ = ["EditAnimalPage"]

