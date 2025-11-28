"""User dashboard with activity overview and featured animals."""
from __future__ import annotations
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, timedelta
from io import BytesIO
import base64

# Set matplotlib backend to Agg before importing pyplot
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

import app_config
from services.animal_service import AnimalService
from services.rescue_service import RescueService
from services.adoption_service import AdoptionService
from services.map_service import MapService
from services.photo_service import load_photo
from state import get_app_state
from components import (
    create_user_sidebar, create_gradient_background,
    create_section_card, create_chart_container, fig_to_base64
)


class UserDashboard:
    def __init__(self, db_path: Optional[str] = None) -> None:
        self.db_path = db_path or app_config.DB_PATH
        self.animal_service = AnimalService(self.db_path)
        self.rescue_service = RescueService(self.db_path)
        self.adoption_service = AdoptionService(self.db_path)
        self.map_service = MapService()

    def build(self, page) -> None:
        """Build the user dashboard on the provided flet.Page instance."""
        try:
            import flet as ft
        except Exception as exc:
            raise RuntimeError("Flet must be installed to build the UI") from exc

        page.title = "User Dashboard"

        # Get user info from centralized state management
        app_state = get_app_state()
        user_name = app_state.auth.user_name or "User"
        user_id = app_state.auth.user_id

        # Fetch data for charts
        all_adoptions = self.adoption_service.get_all_requests() or []
        all_rescues = self.rescue_service.get_all_missions() or []
        
        # Get user-specific data if user_id exists
        if user_id:
            user_adoptions = [a for a in all_adoptions if a.get("user_id") == user_id]
            user_rescues = [r for r in all_rescues if r.get("user_id") == user_id]
        else:
            user_adoptions = []
            user_rescues = []
        
        # Count totals and pending
        total_adoptions = len(user_adoptions)
        rescue_reports_filed = len(user_rescues)
        pending_adoption_requests = len([a for a in user_adoptions if (a.get("status") or "").lower() == "pending"])
        ongoing_rescue_missions = len([r for r in user_rescues if (r.get("status") or "").lower() == "on-going"])

        # Create chart data
        # Bar chart for user activity
        try:
            fig, ax = plt.subplots(figsize=(4.5, 2.5))
            categories = ['Total Adoptions', 'Rescue Reports']
            values = [total_adoptions, rescue_reports_filed]
            colors = ['#2196F3', '#FFA726']
            ax.bar(categories, values, color=colors, width=0.6)
            ax.set_ylabel('Count', fontsize=9)
            ax.set_title('User Management', fontsize=10, pad=10)
            ax.tick_params(axis='both', labelsize=8)
            ax.set_ylim(0, max(values) + 2 if max(values) > 0 else 5)
            plt.tight_layout()
            chart_b64 = fig_to_base64(fig)
        except Exception:
            chart_b64 = None

        # Get featured adoptable animal
        adoptable_animals = self.animal_service.get_adoptable_animals() or []
        featured_animal = adoptable_animals[0] if adoptable_animals else None

        # Sidebar with navigation
        sidebar = create_user_sidebar(page, user_name)

        # My Activity card with chart
        activity_chart = None
        if chart_b64:
            activity_chart = ft.Image(src_base64=chart_b64, width=380, height=220, fit=ft.ImageFit.CONTAIN)
        else:
            activity_chart = ft.Container(
                ft.Text("Chart unavailable", color=ft.Colors.BLACK54),
                width=380,
                height=220,
                alignment=ft.alignment.center,
            )

        activity_card = ft.Container(
            ft.Column([
                ft.Text("My Activity", size=16, weight="w600", color=ft.Colors.BLACK87),
                ft.Container(height=10),
                activity_chart,
                ft.Container(height=15),
                ft.Column([
                    ft.Row([
                        ft.Container(
                            width=12,
                            height=12,
                            bgcolor=ft.Colors.BLUE_500,
                            border_radius=2,
                        ),
                        ft.Text(f"Total Adoptions ({total_adoptions})", size=12, color=ft.Colors.BLACK87),
                    ], spacing=8),
                    ft.Container(height=5),
                    ft.Row([
                        ft.Container(
                            width=12,
                            height=12,
                            bgcolor=ft.Colors.ORANGE_600,
                            border_radius=2,
                        ),
                        ft.Text(f"Rescue Reports Filed ({rescue_reports_filed})", size=12, color=ft.Colors.BLACK87),
                    ], spacing=8),
                ], spacing=2),
                ft.Container(height=15),
                ft.Text("Current Applications:", size=13, weight="w600", color=ft.Colors.BLACK87),
                ft.Container(height=8),
                ft.Row([
                    ft.Container(
                        width=8,
                        height=8,
                        bgcolor=ft.Colors.BLUE_500,
                        border_radius=4,
                    ),
                    ft.Text(f"Adoption Requests (Pending: {pending_adoption_requests})", size=12, color=ft.Colors.BLACK87),
                ], spacing=8),
                ft.Container(height=5),
                ft.Row([
                    ft.Container(
                        width=8,
                        height=8,
                        bgcolor=ft.Colors.ORANGE_600,
                        border_radius=4,
                    ),
                    ft.Text(f"Rescue Mission (On-going: {ongoing_rescue_missions})", size=12, color=ft.Colors.BLACK87),
                ], spacing=8),
            ], spacing=0, horizontal_alignment="start"),
            width=450,
            padding=20,
            bgcolor=ft.Colors.WHITE,
            border_radius=12,
            shadow=ft.BoxShadow(blur_radius=8, spread_radius=1, color=ft.Colors.BLACK12, offset=(0, 2)),
        )

        # Featured Adoptables card
        if featured_animal:
            animal_name = featured_animal.get("name", "Unknown")
            animal_age = featured_animal.get("age", "N/A")
            animal_species = featured_animal.get("species", "Unknown")
            animal_health = featured_animal.get("health_status", "Unknown")
            # load_photo handles both filename and legacy base64 formats
            animal_photo = load_photo(featured_animal.get("photo"))

            if animal_photo:
                animal_image = ft.Image(
                    src_base64=animal_photo,
                    width=200,
                    height=200,
                    fit=ft.ImageFit.COVER,
                    border_radius=8,
                )
            else:
                animal_image = ft.Container(
                    ft.Icon(ft.Icons.PETS, size=80, color=ft.Colors.GREY_400),
                    width=200,
                    height=200,
                    bgcolor=ft.Colors.GREY_200,
                    border_radius=8,
                    alignment=ft.alignment.center,
                )

            featured_card = ft.Container(
                ft.Column([
                    ft.Text("Featured Adoptables", size=16, weight="w600", color=ft.Colors.BLACK87),
                    ft.Container(height=15),
                    animal_image,
                    ft.Container(height=10),
                    ft.Text(f"{animal_name}, {animal_age}yrs old", size=14, weight="bold", color=ft.Colors.BLACK87),
                    ft.Row([
                        ft.Text(animal_species, size=11, color=ft.Colors.ORANGE_600, weight="w500"),
                        ft.Text(animal_health, size=11, color=ft.Colors.GREEN_600, weight="w500"),
                    ], spacing=20, alignment="center"),
                    ft.Container(height=10),
                    ft.ElevatedButton(
                        "Adopt",
                        width=120,
                        on_click=lambda e: page.go("/available_adoption"),
                        style=ft.ButtonStyle(
                            bgcolor=ft.Colors.TEAL_400,
                            color=ft.Colors.WHITE,
                            shape=ft.RoundedRectangleBorder(radius=20),
                        )
                    ),
                    ft.Container(height=20),
                    ft.Row([
                        ft.Container(width=10, height=10, bgcolor=ft.Colors.ORANGE_400, border_radius=5),
                        ft.Container(width=10, height=10, bgcolor=ft.Colors.GREY_300, border_radius=5),
                        ft.Container(width=10, height=10, bgcolor=ft.Colors.GREY_300, border_radius=5),
                    ], spacing=5, alignment="center"),
                ], horizontal_alignment="center", spacing=0),
                width=280,
                padding=20,
                bgcolor=ft.Colors.WHITE,
                border_radius=12,
                shadow=ft.BoxShadow(blur_radius=8, spread_radius=1, color=ft.Colors.BLACK12, offset=(0, 2)),
            )
        else:
            featured_card = ft.Container(
                ft.Column([
                    ft.Text("Featured Adoptables", size=16, weight="w600", color=ft.Colors.BLACK87),
                    ft.Container(height=15),
                    ft.Container(
                        ft.Text("No animals available", size=12, color=ft.Colors.BLACK54),
                        width=200,
                        height=200,
                        alignment=ft.alignment.center,
                    ),
                ], horizontal_alignment="center"),
                width=280,
                padding=20,
                bgcolor=ft.Colors.WHITE,
                border_radius=12,
                shadow=ft.BoxShadow(blur_radius=8, spread_radius=1, color=ft.Colors.BLACK12, offset=(0, 2)),
            )

        # Realtime Rescue Mission map with markers
        map_widget = self.map_service.create_map_with_markers(all_rescues, zoom=11)
        
        if map_widget:
            map_card = ft.Container(
                ft.Column([
                    ft.Text("Realtime Rescue Mission Map", size=16, weight="w600", color=ft.Colors.BLACK87),
                    ft.Container(height=15),
                    ft.Container(
                        map_widget,
                        width=750,
                        height=300,
                        border_radius=8,
                        clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
                    ),
                ], spacing=0, horizontal_alignment="start"),
                width=790,
                padding=20,
                bgcolor=ft.Colors.WHITE,
                border_radius=12,
                shadow=ft.BoxShadow(blur_radius=8, spread_radius=1, color=ft.Colors.BLACK12, offset=(0, 2)),
            )
        else:
            # Fallback to placeholder
            map_card = ft.Container(
                ft.Column([
                    ft.Text("Realtime Rescue Mission", size=16, weight="w600", color=ft.Colors.BLACK87),
                    ft.Container(height=15),
                    self.map_service.create_empty_map_placeholder(len(all_rescues)),
                ], spacing=0, horizontal_alignment="start"),
                width=790,
                padding=20,
            bgcolor=ft.Colors.WHITE,
            border_radius=12,
            shadow=ft.BoxShadow(blur_radius=8, spread_radius=1, color=ft.Colors.BLACK12, offset=(0, 2)),
        )

        # Main content area
        main_content = ft.Container(
            ft.Column([
                ft.Text("User Dashboard Overview", size=28, weight="bold", color=ft.Colors.with_opacity(0.6, ft.Colors.BLACK), text_align=ft.TextAlign.CENTER),
                ft.Container(height=20),
                ft.Row([
                    activity_card,
                    ft.Container(width=20),
                    featured_card,
                ], alignment="center"),
                ft.Container(height=20),
                ft.Container(
                    map_card,
                    alignment=ft.alignment.center,
                ),
            ], spacing=0, scroll=ft.ScrollMode.AUTO, horizontal_alignment="center"),
            padding=30,
            expand=True,
        )        # Main layout
        main_layout = ft.Row([sidebar, main_content], spacing=0, expand=True)

        page.controls.clear()
        page.add(create_gradient_background(main_layout))
        page.update()


__all__ = ["UserDashboard"]


