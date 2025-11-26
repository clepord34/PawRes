"""Admin page for managing adoption requests."""
from __future__ import annotations
from typing import Optional

import app_config
from services.adoption_service import AdoptionService
from components import create_admin_sidebar, create_adoption_status_dropdown, create_status_badge, create_gradient_background


class AdoptionRequestListPage:
    def __init__(self, db_path: Optional[str] = None) -> None:
        self.adoption_service = AdoptionService(db_path or app_config.DB_PATH)

    def build(self, page, user_role: str = "admin") -> None:
        try:
            import flet as ft
        except Exception as exc:
            raise RuntimeError("Flet must be installed to build the UI") from exc

        page.title = "Adoption Requests"

        is_admin = user_role == "admin"

        # Sidebar (for admin only)
        if is_admin:
            sidebar = create_admin_sidebar(page)
        else:
            sidebar = None

        # Fetch all adoption requests
        requests = self.adoption_service.get_all_requests() or []

        # Build table rows
        table_rows = []
        for req in requests:
            request_id = req.get("id")
            user_name = req.get("user_name", "N/A")
            animal_name = req.get("animal_name", "N/A")
            contact = req.get("contact", "N/A")
            reason = req.get("reason", "N/A")
            status = (req.get("status") or "pending").capitalize()

            # Status dropdown for admin
            if is_admin:
                # Determine status color: Approved=green, Denied=red, Pending=orange
                if status.lower() == "approved":
                    dropdown_color = ft.Colors.GREEN_600
                elif status.lower() == "denied":
                    dropdown_color = ft.Colors.RED_600
                else:
                    dropdown_color = ft.Colors.ORANGE_600
                
                status_dropdown = ft.Dropdown(
                    value=status,
                    options=[
                        ft.dropdown.Option("Approved"),
                        ft.dropdown.Option("Denied")
                    ],
                    on_change=lambda e, rid=request_id: self._on_status_change(page, rid, e.control.value),
                    width=140,
                    bgcolor=dropdown_color,
                    border_color=dropdown_color,
                    text_style=ft.TextStyle(color=ft.Colors.WHITE, size=12, weight="w500"),
                    color=ft.Colors.WHITE,
                    filled=True,
                    content_padding=10,
                )
                status_widget = status_dropdown
            else:
                # For non-admin, show static chip
                if status.lower() == "approved":
                    status_widget = ft.Container(
                        ft.Row([
                            ft.Icon(ft.Icons.CHECK_CIRCLE, size=16, color=ft.Colors.WHITE),
                            ft.Text(status, size=12, color=ft.Colors.WHITE, weight="w500"),
                        ], spacing=5, alignment="center"),
                        bgcolor=ft.Colors.GREEN_600,
                        padding=ft.padding.symmetric(horizontal=15, vertical=8),
                        border_radius=20,
                    )
                elif status.lower() == "denied":
                    status_widget = ft.Container(
                        ft.Row([
                            ft.Icon(ft.Icons.CANCEL, size=16, color=ft.Colors.WHITE),
                            ft.Text(status, size=12, color=ft.Colors.WHITE, weight="w500"),
                        ], spacing=5, alignment="center"),
                        bgcolor=ft.Colors.RED_600,
                        padding=ft.padding.symmetric(horizontal=15, vertical=8),
                        border_radius=20,
                    )
                else:
                    status_widget = ft.Container(
                        ft.Row([
                            ft.Icon(ft.Icons.PENDING, size=16, color=ft.Colors.WHITE),
                            ft.Text(status, size=12, color=ft.Colors.WHITE, weight="w500"),
                        ], spacing=5, alignment="center"),
                        bgcolor=ft.Colors.ORANGE_600,
                        padding=ft.padding.symmetric(horizontal=15, vertical=8),
                        border_radius=20,
                    )

            # Table row
            row = ft.Container(
                ft.Row([
                    ft.Container(ft.Text(user_name, size=14, color=ft.Colors.BLACK87), width=120),
                    ft.Container(ft.Text(animal_name, size=14, color=ft.Colors.BLACK87), width=120),
                    ft.Container(ft.Text(contact, size=14, color=ft.Colors.BLACK87), width=200),
                    ft.Container(ft.Text(reason, size=14, color=ft.Colors.BLACK87), width=220),
                    ft.Container(status_widget, width=150, alignment=ft.alignment.center),
                ], spacing=20),
                padding=15,
                border=ft.border.only(bottom=ft.BorderSide(1, ft.Colors.GREY_200)),
            )
            table_rows.append(row)

        # Table header
        table_header = ft.Container(
            ft.Row([
                ft.Container(ft.Text("User Name", size=14, weight="bold", color=ft.Colors.BLACK87), width=120),
                ft.Container(ft.Text("Animal Name", size=14, weight="bold", color=ft.Colors.BLACK87), width=120),
                ft.Container(ft.Text("Contact Info", size=14, weight="bold", color=ft.Colors.BLACK87), width=200),
                ft.Container(ft.Text("Reason", size=14, weight="bold", color=ft.Colors.BLACK87), width=220),
                ft.Container(ft.Text("Status", size=14, weight="bold", color=ft.Colors.BLACK87), width=150, alignment=ft.alignment.center),
            ], spacing=20),
            padding=15,
            bgcolor=ft.Colors.GREY_100,
            border=ft.border.only(bottom=ft.BorderSide(2, ft.Colors.GREY_300)),
        )

        # Table container
        table_container = ft.Container(
            ft.Column([
                ft.Text("Rescue Mission List", size=18, weight="w600", color=ft.Colors.BLACK87),
                ft.Divider(height=15, color=ft.Colors.GREY_300),
                table_header,
                ft.Column(table_rows if table_rows else [
                    ft.Container(
                        ft.Text("No adoption requests found", size=16, color=ft.Colors.BLACK54),
                        padding=40,
                        alignment=ft.alignment.center,
                    )
                ], spacing=0, scroll=ft.ScrollMode.AUTO),
            ], spacing=10),
            padding=20,
            bgcolor=ft.Colors.WHITE,
            border_radius=12,
            shadow=ft.BoxShadow(blur_radius=8, spread_radius=1, color=ft.Colors.BLACK12, offset=(0, 2)),
        )

        # Main content area
        main_content = ft.Container(
            ft.Column([
                ft.Text("Adoption Requests List", size=28, weight="bold", color=ft.Colors.with_opacity(0.6, ft.Colors.BLACK)),
                ft.Container(height=15),
                table_container,
            ], spacing=0, scroll=ft.ScrollMode.AUTO),
            padding=30,
            expand=True,
        )

        # Main layout
        if sidebar:
            main_layout = ft.Row([sidebar, main_content], spacing=0, expand=True)
        else:
            main_layout = main_content

        page.controls.clear()
        page.add(create_gradient_background(main_layout))
        page.update()

    def _on_status_change(self, page, request_id: int, new_status: str) -> None:
        try:
            updated = self.adoption_service.update_status(request_id, new_status)
            import flet as ft

            if updated:
                page.snack_bar = ft.SnackBar(ft.Text(f"Status updated to {new_status}"))
                page.snack_bar.open = True
                page.update()
                # Refresh page
                self.build(page, user_role="admin")
            else:
                page.snack_bar = ft.SnackBar(ft.Text("Failed to update status"))
                page.snack_bar.open = True
                page.update()
        except Exception as exc:
            import flet as ft

            page.snack_bar = ft.SnackBar(ft.Text(f"Error: {exc}"))
            page.snack_bar.open = True
            page.update()

