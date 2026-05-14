"""Page for users to set pet adoption preferences."""
from __future__ import annotations

from typing import Optional

import app_config
from services.animal_service import AnimalService
from services.recommendation_service import RecommendationService
from state import get_app_state
from components import (
    create_user_sidebar,
    create_user_drawer,
    create_form_text_field,
    create_form_dropdown,
    create_section_card,
    create_action_button,
    show_snackbar,
    show_page_loading,
    finish_page_loading,
    is_mobile,
    create_responsive_layout,
    responsive_padding,
)


class PetPreferencesPage:
    """Form page for managing adoption preferences."""

    def __init__(self, db_path: Optional[str] = None) -> None:
        self._db_path = db_path or app_config.DB_PATH
        self._service = RecommendationService(self._db_path)
        self._animal_service = AnimalService(self._db_path)
        self._species_selected: set[str] = set()
        self._species_chip_controls: dict[str, object] = {}
        self._breed_field: Optional[object] = None
        self._age_min_dropdown: Optional[object] = None
        self._age_max_dropdown: Optional[object] = None
        self._living_group: Optional[object] = None
        self._activity_group: Optional[object] = None
        self._experience_group: Optional[object] = None
        self._user_id: Optional[int] = None

    def build(self, page) -> None:
        try:
            import flet as ft
        except Exception as exc:
            raise RuntimeError("Flet must be installed to build the UI") from exc

        page.title = "Pet Preferences"

        app_state = get_app_state(page, self._db_path)
        self._user_id = app_state.auth.user_id or page.session.get("user_id")
        if not self._user_id:
            show_snackbar(page, "Please sign in to set preferences", error=True)
            page.go("/")
            return

        _mobile = is_mobile(page)
        sidebar = create_user_sidebar(page, app_state.auth.user_name or "User", current_route=page.route)
        drawer = create_user_drawer(page, current_route=page.route) if _mobile else None
        _gradient_ref = show_page_loading(page, None if _mobile else sidebar, "Loading preferences...")
        sidebar = create_user_sidebar(page, app_state.auth.user_name or "User", current_route=page.route)

        prefs = self._service.get_preferences(self._user_id) or {}
        self._species_selected = set(self._parse_list(prefs.get("preferred_species")))

        def build_species_chip(label: str) -> object:
            is_selected = label in self._species_selected
            chip = ft.Container(
                ft.Row([
                    ft.Icon(ft.Icons.PETS, size=12, color=ft.Colors.WHITE if is_selected else ft.Colors.TEAL_700),
                    ft.Text(
                        label,
                        size=11,
                        weight="w600",
                        color=ft.Colors.WHITE if is_selected else ft.Colors.TEAL_700,
                    ),
                ], spacing=6, alignment=ft.MainAxisAlignment.CENTER),
                bgcolor=ft.Colors.TEAL_600 if is_selected else ft.Colors.TEAL_50,
                border=ft.border.all(1, ft.Colors.TEAL_600 if is_selected else ft.Colors.TEAL_200),
                border_radius=20,
                padding=ft.padding.symmetric(horizontal=12, vertical=6),
                on_click=lambda e, s=label: self._toggle_species(page, s),
            )
            self._species_chip_controls[label] = chip
            return chip

        self._breed_field = create_form_text_field(
            label="Preferred Breeds",
            hint_text="e.g., Labrador, Poodle, Shih Tzu",
        )
        if prefs.get("preferred_breeds"):
            self._breed_field.value = prefs.get("preferred_breeds")

        age_options = ["Any"] + [str(i) for i in range(0, 21)]
        self._age_min_dropdown = create_form_dropdown(
            label="Preferred Min Age",
            options=age_options,
            value=str(prefs.get("preferred_age_min")) if prefs.get("preferred_age_min") is not None else "Any",
        )
        self._age_max_dropdown = create_form_dropdown(
            label="Preferred Max Age",
            options=age_options,
            value=str(prefs.get("preferred_age_max")) if prefs.get("preferred_age_max") is not None else "Any",
        )

        self._living_group = ft.RadioGroup(
            value=prefs.get("living_situation") or "apartment",
            content=ft.Column([
                ft.Radio(value="apartment", label="Apartment"),
                ft.Radio(value="house_small_yard", label="House with small yard"),
                ft.Radio(value="house_large_yard", label="House with large yard"),
            ], spacing=6),
        )

        self._activity_group = ft.RadioGroup(
            value=prefs.get("activity_level") or "moderate",
            content=ft.Column([
                ft.Radio(value="low", label="Low activity"),
                ft.Radio(value="moderate", label="Moderate activity"),
                ft.Radio(value="high", label="High activity"),
            ], spacing=6),
        )

        self._experience_group = ft.RadioGroup(
            value=prefs.get("experience_level") or "some_experience",
            content=ft.Column([
                ft.Radio(value="first_time", label="First-time owner"),
                ft.Radio(value="some_experience", label="Some experience"),
                ft.Radio(value="experienced", label="Experienced"),
            ], spacing=6),
        )

        species_row = ft.Row(
            [build_species_chip(label) for label in ["Dog", "Cat", "Other"]],
            spacing=10,
            wrap=True,
        )

        breed_suggestions = self._get_breed_suggestions()
        suggestion_chips = []
        if breed_suggestions:
            for breed in breed_suggestions:
                suggestion_chips.append(
                    ft.Container(
                        ft.Row([
                            ft.Icon(ft.Icons.ADD, size=12, color=ft.Colors.TEAL_700),
                            ft.Text(breed, size=11, color=ft.Colors.TEAL_700),
                        ], spacing=4),
                        bgcolor=ft.Colors.TEAL_50,
                        border=ft.border.all(1, ft.Colors.TEAL_200),
                        border_radius=16,
                        padding=ft.padding.symmetric(horizontal=10, vertical=4),
                        on_click=lambda e, b=breed: self._add_breed_suggestion(b),
                    )
                )

        suggestion_row = ft.Row(suggestion_chips, spacing=6, wrap=True) if suggestion_chips else ft.Container()

        save_button = create_action_button(
            text="Save Preferences",
            on_click=lambda e: self._on_save(page),
            width=200,
            height=44,
        )

        preferences_form = ft.Column([
            ft.Text("Tell us what kind of pet fits your lifestyle.", size=13, color=ft.Colors.BLACK54),
            ft.Container(height=10),
            ft.Text("Preferred Species", size=12, weight="w600", color=ft.Colors.BLACK87),
            species_row,
            ft.Container(height=12),
            self._breed_field,
            suggestion_row,
            ft.Container(height=12),
            ft.Row([
                ft.Container(self._age_min_dropdown, expand=True),
                ft.Container(self._age_max_dropdown, expand=True),
            ], spacing=12),
            ft.Container(height=12),
            ft.Text("Living Situation", size=12, weight="w600", color=ft.Colors.BLACK87),
            self._living_group,
            ft.Container(height=12),
            ft.Text("Activity Level", size=12, weight="w600", color=ft.Colors.BLACK87),
            self._activity_group,
            ft.Container(height=12),
            ft.Text("Pet Ownership Experience", size=12, weight="w600", color=ft.Colors.BLACK87),
            self._experience_group,
            ft.Container(height=16),
            ft.Container(save_button, alignment=ft.alignment.center),
        ], spacing=8)

        preferences_card = create_section_card(
            title="Adoption Preferences",
            subtitle="Update these anytime from your dashboard",
            content=preferences_form,
            show_divider=False,
        )

        content = ft.Container(
            ft.ListView(
                controls=[
                    ft.Row(
                        [ft.Container(preferences_card, width=720)],
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                ],
                spacing=0,
                expand=True,
            ),
            padding=responsive_padding(page),
            expand=True,
        )

        layout = create_responsive_layout(page, sidebar, content, drawer, title="Preferences")
        finish_page_loading(page, _gradient_ref, layout)

    def _toggle_species(self, page, label: str) -> None:
        if label in self._species_selected:
            self._species_selected.remove(label)
        else:
            self._species_selected.add(label)

        chip = self._species_chip_controls.get(label)
        if chip:
            import flet as ft
            is_selected = label in self._species_selected
            chip.bgcolor = ft.Colors.TEAL_600 if is_selected else ft.Colors.TEAL_50
            chip.border = ft.border.all(1, ft.Colors.TEAL_600 if is_selected else ft.Colors.TEAL_200)
            if isinstance(chip.content, ft.Row):
                for control in chip.content.controls:
                    if isinstance(control, ft.Text):
                        control.color = ft.Colors.WHITE if is_selected else ft.Colors.TEAL_700
                    if isinstance(control, ft.Icon):
                        control.color = ft.Colors.WHITE if is_selected else ft.Colors.TEAL_700
            chip.update()
        else:
            page.update()

    def _add_breed_suggestion(self, breed: str) -> None:
        if not self._breed_field:
            return
        current = self._breed_field.value or ""
        parts = [p.strip() for p in current.split(",") if p.strip()]
        if breed not in parts:
            parts.append(breed)
        self._breed_field.value = ", ".join(parts)
        self._breed_field.update()

    def _on_save(self, page) -> None:
        if not self._user_id:
            return

        min_age = self._parse_age_value(self._age_min_dropdown.value if self._age_min_dropdown else None)
        max_age = self._parse_age_value(self._age_max_dropdown.value if self._age_max_dropdown else None)
        if min_age is not None and max_age is not None and min_age > max_age:
            show_snackbar(page, "Minimum age cannot be greater than maximum age", error=True)
            return

        prefs = {
            "preferred_species": sorted(self._species_selected),
            "preferred_breeds": self._breed_field.value if self._breed_field else None,
            "preferred_age_min": min_age,
            "preferred_age_max": max_age,
            "living_situation": self._living_group.value if self._living_group else None,
            "activity_level": self._activity_group.value if self._activity_group else None,
            "experience_level": self._experience_group.value if self._experience_group else None,
        }

        self._service.save_preferences(self._user_id, prefs)
        show_snackbar(page, "Preferences saved successfully")

    def _get_breed_suggestions(self) -> list[str]:
        animals = self._animal_service.get_all_animals() or []
        breeds = sorted({(a.get("breed") or "").strip() for a in animals if (a.get("breed") or "").strip()})
        return breeds[:8]

    @staticmethod
    def _parse_list(value: object) -> list[str]:
        if not value:
            return []
        if isinstance(value, str):
            return [part.strip() for part in value.split(",") if part.strip()]
        if isinstance(value, (list, tuple, set)):
            return [str(part).strip() for part in value if str(part).strip()]
        return [str(value).strip()]

    @staticmethod
    def _parse_age_value(value: Optional[str]) -> Optional[int]:
        if not value or value == "Any":
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return None


__all__ = ["PetPreferencesPage"]
