"""Page displaying animals available for adoption."""
from __future__ import annotations
from typing import Optional, List, Dict

import app_config
from services.animal_service import AnimalService
from components import (
    create_page_header, create_action_button, create_table_action_button, create_gradient_background,
    create_section_card
)


class AvailableAdoptionPage:
    def __init__(self, db_path: Optional[str] = None) -> None:
        self.animal_service = AnimalService(db_path or app_config.DB_PATH)
        self._all_animals: List[Dict] = []

    def build(self, page) -> None:
        try:
            import flet as ft
        except Exception as exc:
            raise RuntimeError("Flet must be installed to build the UI") from exc

        page.title = "Available for Adoption"

        # Header with logo/title
        header = create_page_header("Paw Rescue")

        # Title
        title = ft.Container(
            ft.Text("Available For Adoption", size=18, weight="w600", color=ft.Colors.BLACK87),
            padding=ft.padding.only(bottom=15, top=10),
            alignment=ft.alignment.center,
        )

        # fetch adoptable animals
        self._all_animals = self.animal_service.get_adoptable_animals() or []

        # Build table rows
        rows = []
        for a in self._all_animals:
            name = (a.get("name") or "Unknown")
            species = (a.get("species") or "Unknown")
            age = f"{a.get('age')}yrs Old" if a.get('age') else "Unknown"
            status = (a.get("status") or "unknown").capitalize()
            animal_id = a.get("id")

            adopt_btn = create_table_action_button(
                "Adopt",
                on_click=lambda e, aid=animal_id: self._on_apply(page, aid)
            )

            rows.append(ft.DataRow(cells=[
                ft.DataCell(ft.Text(name, size=14, color=ft.Colors.BLACK87)),
                ft.DataCell(ft.Text(species, size=14, color=ft.Colors.BLACK87)),
                ft.DataCell(ft.Text(age, size=14, color=ft.Colors.BLACK87)),
                ft.DataCell(ft.Text(status, size=14, color=ft.Colors.BLACK87)),
                ft.DataCell(adopt_btn),
            ]))

        # Table
        table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Name", weight="bold", size=14, color=ft.Colors.BLACK87)),
                ft.DataColumn(ft.Text("Type", weight="bold", size=14, color=ft.Colors.BLACK87)),
                ft.DataColumn(ft.Text("Age", weight="bold", size=14, color=ft.Colors.BLACK87)),
                ft.DataColumn(ft.Text("Health Status", weight="bold", size=14, color=ft.Colors.BLACK87)),
                ft.DataColumn(ft.Text("", weight="bold", size=14)),
            ],
            rows=rows,
            heading_row_color=ft.Colors.WHITE,
            data_row_min_height=60,
            border=ft.border.all(1, ft.Colors.GREY_300),
            border_radius=8,
        )

        # Card container
        card = ft.Container(
            ft.Column([
                title, 
                ft.Container(table, bgcolor=ft.Colors.WHITE, padding=10),
                ft.Divider(height=8, color=ft.Colors.TRANSPARENT),
                create_action_button(
                    "Back to Dashboard",
                    on_click=lambda e: page.go("/user"),
                    outlined=True,
                    bgcolor=ft.Colors.TEAL_400
                ),
            ], horizontal_alignment="center", spacing=10),
            width=700,
            padding=20,
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

    def _on_apply(self, page, animal_id: int) -> None:
        # navigate to adoption form with query param
        page.go(f"/adoption_form?animal_id={animal_id}")


__all__ = ["AvailableAdoptionPage"]

