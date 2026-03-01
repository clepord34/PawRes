"""Edit Animal Page for updating existing animal records.

Allows admin to edit animal details: type, name, age, and health status.
"""
from __future__ import annotations

from typing import Optional
from urllib.parse import urlparse, parse_qs

import app_config
from services.animal_service import AnimalService
from services.rescue_service import RescueService
from storage.file_store import get_file_store
from components import (
    create_page_header, create_gradient_background, create_animal_form, show_snackbar
)


class EditAnimalPage:
    def __init__(self, db_path: Optional[str] = None) -> None:
        self.service = AnimalService(db_path or app_config.DB_PATH)
        self.rescue_service = RescueService(db_path or app_config.DB_PATH)
        self.file_store = get_file_store()
        self._animal_id = None
        self._original_photo = None

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

        animal = self.service.get_animal_by_id(animal_id)

        if not animal:
            show_snackbar(page, "Error: Animal not found", error=True)
            page.go("/animals_list?admin=1")
            return

        self._original_photo = animal.get('photo')

        # Header with logo
        header = create_page_header("Paw Rescue")

        rescue_info = None
        rescue_mission_id = animal.get("rescue_mission_id")
        if rescue_mission_id:
            mission = self.rescue_service.get_mission_by_id(rescue_mission_id)
            if mission:
                rescue_date = mission.get("created_at", "")
                if rescue_date:
                    try:
                        from datetime import datetime
                        if isinstance(rescue_date, str):
                            dt = datetime.fromisoformat(rescue_date.replace('Z', '+00:00'))
                            rescue_date = dt.strftime("%b %d, %Y")
                    except:
                        pass
                
                rescue_info = {
                    "location": mission.get("location", "Unknown location"),
                    "date": rescue_date,
                    "reporter": mission.get("reporter_name") or "Anonymous",
                    "contact": mission.get("reporter_phone", ""),
                    "urgency": (mission.get("urgency") or "unknown").capitalize(),
                    "description": mission.get("notes", ""),
                    "source": "Emergency" if mission.get("user_id") is None else "User",
                    "name": animal.get("name", "Unknown"),
                }

        def handle_submit(form_data):
            """Handle form submission."""
            try:
                new_photo_filename = None
                if form_data.get("pending_image_bytes"):
                    new_photo_filename = self.file_store.save_bytes(
                        form_data["pending_image_bytes"],
                        original_name=form_data.get("pending_original_name") or "photo.jpg",
                        validate=True,
                        custom_name=form_data["name"]
                    )
                
                original_animal = self.service.get_animal_by_id(self._animal_id)
                original_name = original_animal.get('name', '') if original_animal else ''
                
                success = self.service.update_animal(
                    self._animal_id,
                    type=form_data["type"],
                    name=form_data["name"],
                    breed=form_data.get("breed") or None,
                    age=form_data["age"],
                    health_status=form_data["health_status"]
                )
                
                if new_photo_filename and success:
                    self.service.update_animal_photo(self._animal_id, new_photo_filename)
                elif success and original_name != form_data["name"] and not form_data.get("pending_image_bytes"):
                    # Name changed but no new photo - rename existing photo file
                    existing_photo = self._original_photo
                    if existing_photo and not existing_photo.startswith('data:') and len(existing_photo) < 200:
                        try:
                            renamed_filename = self.file_store.rename_file(existing_photo, form_data["name"])
                            self.service.db.execute(
                                "UPDATE animals SET photo = ? WHERE id = ?",
                                (renamed_filename, self._animal_id)
                            )
                        except Exception:
                            pass
                
                if success:
                    show_snackbar(page, "Animal updated successfully!")
                    page.go("/animals_list?admin=1")
                else:
                    show_snackbar(page, "Failed to update animal", error=True)
            except Exception as exc:
                show_snackbar(page, f"Error: {str(exc)}", error=True)

        def handle_cancel():
            """Handle cancel button click."""
            page.go("/animals_list?admin=1")

        animal_form = create_animal_form(
            page=page,
            mode="edit",
            animal_data=animal,
            on_submit=handle_submit,
            on_cancel=handle_cancel,
            rescue_info=rescue_info,
        )

        card = animal_form.build()

        # Main layout - margin wrapper so card doesn't touch screen edges
        card_with_margin = ft.Container(card, margin=ft.margin.symmetric(horizontal=16))

        layout = ft.Column([
            header,
            card_with_margin,
            ft.Container(height=20),  # Bottom padding for scroll
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15, scroll=ft.ScrollMode.AUTO)

        page.controls.clear()
        page.add(create_gradient_background(layout))
        page.update()


__all__ = ["EditAnimalPage"]

