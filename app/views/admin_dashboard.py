"""Admin dashboard with navigation and analytics overview."""
from __future__ import annotations

from typing import Optional, Dict, Any, Tuple, List

from services.animal_service import AnimalService
from services.rescue_service import RescueService
from services.adoption_service import AdoptionService
from services.analytics_service import AnalyticsService
from services.map_service import MapService
from state import get_app_state
import app_config
from components import (
    create_admin_sidebar, create_dashboard_card, create_gradient_background,
    create_line_chart, create_bar_chart, create_pie_chart,
    create_chart_legend, create_clickable_stat_card, show_chart_details_dialog,
    STATUS_COLORS, PIE_CHART_COLORS,
)


class AdminDashboard:
    """Admin dashboard UI for managing animals, missions and requests.

    Call `AdminDashboard().build(page)` from your Flet app.
    """

    def __init__(self, db_path: Optional[str] = None) -> None:
        self.animal_service = AnimalService(db_path or app_config.DB_PATH)
        self.rescue_service = RescueService(db_path or app_config.DB_PATH)
        self.adoption_service = AdoptionService(db_path or app_config.DB_PATH)
        self.analytics_service = AnalyticsService(db_path or app_config.DB_PATH)
        self.map_service = MapService()

    def build(self, page) -> None:
        """Build the admin dashboard on a `flet.Page` instance."""
        try:
            import flet as ft
        except Exception as exc:  # pragma: no cover - flet may be missing during tests
            raise RuntimeError("Flet is required to build the AdminDashboard") from exc

        page.title = "Admin Dashboard"

        # Fetch data using analytics service
        stats = self.analytics_service.get_dashboard_stats()
        total_animals = stats["total_animals"]
        total_adoptions = stats["total_adoptions"]
        pending_applications = stats["pending_applications"]
        
        # Get pending rescue missions count
        pending_rescues = self.analytics_service.get_pending_rescue_missions()
        
        # Calculate actual percentage changes
        changes = self.analytics_service.get_monthly_changes()
        animals_change = changes["animals_change"]
        adoptions_change = changes["adoptions_change"]
        pending_change = changes["pending_change"]
        rescues_change = changes["rescues_change"]

        # Fetch chart data using analytics service
        # Use 14-day data for admin dashboard (less crowded)
        (month_labels, rescued_counts, adopted_counts) = self.analytics_service.get_chart_data_14_days()
        # Get type distribution and status counts from full chart data
        _, type_dist, status_counts = self.analytics_service.get_chart_data()

        # Fetch missions for map display
        missions = self.rescue_service.get_all_missions() or []

        # Sidebar with navigation
        sidebar = create_admin_sidebar(page, current_route=page.route)

        # Stats cards - now with 4 clickable cards including Pending Rescue Missions
        stat_cards = ft.Row([
            create_clickable_stat_card(
                title="Total Animals",
                value=str(total_animals),
                subtitle=animals_change,
                icon=ft.Icons.PETS,
                icon_color=ft.Colors.TEAL_600,
                on_click=lambda e: page.go("/animals_list?admin=1"),
            ),
            create_clickable_stat_card(
                title="Total Adoptions",
                value=str(total_adoptions),
                subtitle=adoptions_change,
                icon=ft.Icons.FAVORITE,
                icon_color=ft.Colors.ORANGE_600,
                on_click=lambda e: page.go("/adoption_requests"),
            ),
            create_clickable_stat_card(
                title="Pending Applications",
                value=str(pending_applications),
                subtitle=pending_change,
                icon=ft.Icons.PENDING_ACTIONS,
                icon_color=ft.Colors.BLUE_600,
                on_click=lambda e: page.go("/adoption_requests"),
            ),
            create_clickable_stat_card(
                title="Pending Rescues",
                value=str(pending_rescues),
                subtitle=rescues_change,
                icon=ft.Icons.EMERGENCY,
                icon_color=ft.Colors.RED_600,
                on_click=lambda e: page.go("/rescue_missions?admin=1"),
            ),
        ], spacing=15, alignment=ft.MainAxisAlignment.CENTER)

        # ========================================
        # Chart 1: Rescued vs Adopted Line Chart (14 Days)
        # ========================================
        # Format labels with "Date: " prefix for tooltips
        formatted_labels = [f"Date: {label}" for label in month_labels]
        
        line_chart = create_line_chart(
            data_series=[
                {"label": "Rescued", "values": list(zip(range(len(month_labels)), rescued_counts)), "color": "#26A69A"},
                {"label": "Adopted", "values": list(zip(range(len(month_labels)), adopted_counts)), "color": "#FFA726"},
            ],
            height=180,
            x_labels=formatted_labels,  # Pass formatted date labels for tooltips
        )
        
        line_legend = create_chart_legend([
            {"label": "Rescued", "color": "#26A69A", "value": sum(rescued_counts)},
            {"label": "Adopted", "color": "#FFA726", "value": sum(adopted_counts)},
        ], horizontal=False)
        
        rescued_chart_container = ft.Container(
            ft.Column([
                ft.Text("Rescued vs. Adopted (14 Days)", size=14, weight=ft.FontWeight.W_600, color=ft.Colors.BLACK87),
                ft.Divider(height=8, color=ft.Colors.GREY_300),
                ft.Row([
                    line_chart,
                    ft.Container(line_legend, padding=ft.padding.only(left=15, right=10)),
                ], alignment=ft.MainAxisAlignment.CENTER, vertical_alignment=ft.CrossAxisAlignment.CENTER, expand=True),
            ], spacing=5, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            width=420,
            height=268,
            padding=ft.padding.only(left=15, top=15, bottom=15, right=25),
            bgcolor=ft.Colors.WHITE,
            border_radius=12,
            shadow=ft.BoxShadow(blur_radius=8, spread_radius=1, color=ft.Colors.BLACK12, offset=ft.Offset(0, 2)),
        )

        # ========================================
        # Chart 2: Animal Type Distribution Pie (Clickable)
        # ========================================
        type_labels = list(type_dist.keys()) if type_dist else []
        type_values = list(type_dist.values()) if type_dist else []
        total_types = sum(type_values) if type_values else 0
        
        type_sections = []
        type_data_for_dialog = []  # For click dialog
        for i, (label, value) in enumerate(zip(type_labels, type_values)):
            pct = (value / total_types * 100) if total_types > 0 else 0
            color = PIE_CHART_COLORS[i % len(PIE_CHART_COLORS)]
            type_sections.append({
                "value": value,
                "title": f"{pct:.0f}%",
                "color": color,
            })
            type_data_for_dialog.append({
                "label": label,
                "value": value,
                "color": color,
            })
        
        # Create refs dict for legend-pie sync
        type_pie_refs = {}
        type_pie_chart = create_pie_chart(
            sections=type_sections,
            height=150,
            section_radius=60,
            center_space_radius=20,
            legend_refs=type_pie_refs,
        )
        
        type_legend = create_chart_legend([
            {"label": label, "color": PIE_CHART_COLORS[i % len(PIE_CHART_COLORS)], "value": value}
            for i, (label, value) in enumerate(zip(type_labels, type_values))
        ], horizontal=False, pie_refs=type_pie_refs)
        
        # Make the chart container clickable for details
        def show_type_details(e):
            show_chart_details_dialog(page, "Animal Types Breakdown", type_data_for_dialog, "pie")
        
        type_chart_container = ft.Container(
            ft.Column([
                ft.Row([
                    ft.Text("Animal Types", size=14, weight=ft.FontWeight.W_600, color=ft.Colors.BLACK87),
                    ft.Container(
                        ft.IconButton(
                            icon=ft.Icons.OPEN_IN_NEW,
                            icon_size=16,
                            icon_color=ft.Colors.TEAL_600,
                            tooltip="View detailed breakdown",
                            on_click=show_type_details,
                        ),
                        bgcolor=ft.Colors.TEAL_50,
                        border_radius=8,
                        border=ft.border.all(1, ft.Colors.TEAL_200),
                    ),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Divider(height=8, color=ft.Colors.GREY_300),
                ft.Row([
                    type_pie_chart,
                    type_legend,
                ], alignment=ft.MainAxisAlignment.CENTER, spacing=10, expand=True),
            ], spacing=5, horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True),
            width=280,
            height=268,
            padding=15,
            bgcolor=ft.Colors.WHITE,
            border_radius=12,
            shadow=ft.BoxShadow(blur_radius=8, spread_radius=1, color=ft.Colors.BLACK12, offset=ft.Offset(0, 2)),
        )

        # ========================================
        # Chart 3: Health Status Bar Chart (Clickable)
        # ========================================
        health_labels = ["Healthy", "Recovering", "Injured"]
        health_values = [status_counts.get("healthy", 0), status_counts.get("recovering", 0), status_counts.get("injured", 0)]
        health_colors = [STATUS_COLORS["healthy"], STATUS_COLORS["recovering"], STATUS_COLORS["injured"]]
        
        health_data_for_dialog = []  # For click dialog
        health_bar_groups = []
        for i, (label, value, color) in enumerate(zip(health_labels, health_values, health_colors)):
            health_bar_groups.append({
                "x": i,
                "rods": [{"value": value, "color": color, "width": 40}]
            })
            health_data_for_dialog.append({
                "label": label,
                "value": value,
                "color": color,
            })
        
        health_bar_chart = create_bar_chart(
            bar_groups=health_bar_groups,
            bottom_labels={i: label for i, label in enumerate(health_labels)},
            height=180,
        )
        
        def show_health_details(e):
            show_chart_details_dialog(page, "Health Status Breakdown", health_data_for_dialog, "bar")
        
        health_chart_container = ft.Container(
            ft.Column([
                ft.Row([
                    ft.Text("Health Status", size=14, weight=ft.FontWeight.W_600, color=ft.Colors.BLACK87),
                    ft.Container(
                        ft.IconButton(
                            icon=ft.Icons.OPEN_IN_NEW,
                            icon_size=16,
                            icon_color=ft.Colors.TEAL_600,
                            tooltip="View detailed breakdown",
                            on_click=show_health_details,
                        ),
                        bgcolor=ft.Colors.TEAL_50,
                        border_radius=8,
                        border=ft.border.all(1, ft.Colors.TEAL_200),
                    ),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Divider(height=8, color=ft.Colors.GREY_300),
                health_bar_chart,
            ], spacing=5, horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True),
            width=280,
            height=298,
            padding=15,
            bgcolor=ft.Colors.WHITE,
            border_radius=12,
            shadow=ft.BoxShadow(blur_radius=8, spread_radius=1, color=ft.Colors.BLACK12, offset=ft.Offset(0, 2)),
        )

        # ========================================
        # Map: Realtime Rescue Mission Map
        # ========================================
        map_widget = self.map_service.create_map_with_markers(missions, is_admin=True)
        
        if map_widget:
            map_container = ft.Container(
                ft.Column([
                    ft.Text("Rescue Mission Map", size=14, weight=ft.FontWeight.W_600, color=ft.Colors.BLACK87),
                    ft.Divider(height=8, color=ft.Colors.GREY_300),
                    ft.Container(
                        map_widget,
                        expand=True,
                        border_radius=8,
                        clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
                    ),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=5, expand=True),
                width=420,
                height=298,
                padding=15,
                bgcolor=ft.Colors.WHITE,
                border_radius=12,
                shadow=ft.BoxShadow(blur_radius=8, spread_radius=1, color=ft.Colors.BLACK12, offset=ft.Offset(0, 2)),
            )
        else:
            # Fallback to placeholder if map creation fails
            map_container = ft.Container(
                ft.Column([
                    ft.Text("Rescue Mission Map", size=14, weight=ft.FontWeight.W_600, color=ft.Colors.BLACK87),
                    ft.Divider(height=8, color=ft.Colors.GREY_300),
                    self.map_service.create_empty_map_placeholder(len(missions)),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=5, expand=True),
                width=420,
                height=298,
                padding=15,
                bgcolor=ft.Colors.WHITE,
                border_radius=12,
                shadow=ft.BoxShadow(blur_radius=8, spread_radius=1, color=ft.Colors.BLACK12, offset=ft.Offset(0, 2)),
            )

        # Main content area with improved layout
        main_content = ft.Container(
            ft.Column([
                # Page title - centered
                ft.Container(
                    ft.Text("Admin Dashboard Overview", size=22, weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK87),
                    padding=ft.padding.only(bottom=15),
                    alignment=ft.alignment.center,
                ),
                # Stats row - 4 cards
                ft.Container(
                    stat_cards,
                    alignment=ft.alignment.center,
                ),
                ft.Container(height=15),
                # Row 1: Line chart + Type distribution
                ft.Container(
                    ft.Row([
                        rescued_chart_container,
                        type_chart_container,
                    ], spacing=12, alignment=ft.MainAxisAlignment.CENTER),
                    alignment=ft.alignment.center,
                ),
                ft.Container(height=12),
                # Row 2: Health status + Map (side by side)
                ft.Container(
                    ft.Row([
                        health_chart_container,
                        map_container,
                    ], spacing=12, alignment=ft.MainAxisAlignment.CENTER),
                    alignment=ft.alignment.center,
                ),
            ], spacing=0, scroll=ft.ScrollMode.AUTO, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            expand=True,
            padding=25,
        )

        # Main layout with sidebar and content
        layout = ft.Row([
            sidebar,
            main_content,
        ], spacing=0, expand=True, vertical_alignment=ft.CrossAxisAlignment.START)

        page.controls.clear()
        page.add(create_gradient_background(layout))
        page.update()


__all__ = ["AdminDashboard"]

