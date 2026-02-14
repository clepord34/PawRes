"""Admin dashboard with navigation and analytics overview."""
from __future__ import annotations

from typing import Optional

from services.animal_service import AnimalService
from services.rescue_service import RescueService
from services.adoption_service import AdoptionService
from services.analytics_service import AnalyticsService
from services.map_service import MapService
import app_config
from components import (
    create_admin_sidebar, create_gradient_background, create_page_title,
    create_line_chart, create_bar_chart, create_pie_chart,
    create_chart_legend, create_clickable_stat_card, show_chart_details_dialog,
    STATUS_COLORS, PIE_CHART_COLORS, create_interactive_map,
    create_ai_download_dialog, create_ai_download_button,
    show_page_loading, finish_page_loading, create_empty_chart_message,
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

        sidebar = create_admin_sidebar(page, current_route=page.route)
        _gradient_ref = show_page_loading(page, sidebar, "Loading dashboard...")

        stats = self.analytics_service.get_dashboard_stats()
        total_animals = stats["total_animals"]
        total_adoptions = stats["total_adoptions"]  # Actual approved count
        pending_applications = stats["pending_applications"]
        
        all_requests = self.adoption_service.get_all_requests() or []
        total_requests = len([r for r in all_requests if (r.get("status") or "").lower() in ["pending", "approved", "denied"]])
        
        pending_rescues = self.analytics_service.get_pending_rescue_missions()
        
        changes = self.analytics_service.get_monthly_changes()
        animals_change = changes["animals_change"]
        adoptions_change = changes["adoptions_change"]
        pending_change = changes["pending_change"]
        rescues_change = changes["rescues_change"]

        (month_labels, rescued_counts, adopted_counts) = self.analytics_service.get_chart_data_14_days()
        _, type_dist, status_counts = self.analytics_service.get_chart_data()
        
        breed_distribution = self.analytics_service.get_breed_distribution()

        missions = self.rescue_service.get_all_missions() or []

        sidebar = create_admin_sidebar(page, current_route=page.route)

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
                title="Adoption Requests",
                value=str(total_requests),
                subtitle=f"{total_adoptions} approved",
                icon=ft.Icons.FAVORITE,
                icon_color=ft.Colors.ORANGE_600,
                on_click=lambda e: page.go("/manage_records?tab=1"),
            ),
            create_clickable_stat_card(
                title="Pending Adoptions",
                value=str(pending_applications),
                subtitle=pending_change,
                icon=ft.Icons.PENDING_ACTIONS,
                icon_color=ft.Colors.BLUE_600,
                on_click=lambda e: page.go("/manage_records?tab=1"),
            ),
            create_clickable_stat_card(
                title="Pending Rescues",
                value=str(pending_rescues),
                subtitle=rescues_change,
                icon=ft.Icons.EMERGENCY,
                icon_color=ft.Colors.RED_600,
                on_click=lambda e: page.go("/manage_records?tab=0"),
            ),
        ], spacing=15, alignment=ft.MainAxisAlignment.CENTER)

        has_line_data = any(v > 0 for v in rescued_counts + adopted_counts)

        if has_line_data:
            formatted_labels = [f"Date: {label}" for label in month_labels]
            
            dashboard_line_refs = {}  # For legend-line sync
            line_chart = create_line_chart(
                data_series=[
                    {"label": "Rescued", "values": list(zip(range(len(month_labels)), rescued_counts)), "color": "#26A69A"},
                    {"label": "Adopted", "values": list(zip(range(len(month_labels)), adopted_counts)), "color": "#FFA726"},
                ],
                height=180,
                x_labels=formatted_labels,  # Pass formatted date labels for tooltips
                legend_refs=dashboard_line_refs,
            )
            
            line_legend = create_chart_legend([
                {"label": "Rescued", "color": "#26A69A", "value": sum(rescued_counts)},
                {"label": "Adopted", "color": "#FFA726", "value": sum(adopted_counts)},
            ], horizontal=False, line_refs=dashboard_line_refs)
            
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
                height=270,
                padding=ft.padding.only(left=15, top=15, bottom=15, right=25),
                bgcolor=ft.Colors.WHITE,
                border_radius=12,
                shadow=ft.BoxShadow(blur_radius=8, spread_radius=1, color=ft.Colors.BLACK12, offset=ft.Offset(0, 2)),
            )
        else:
            rescued_chart_container = ft.Container(
                ft.Column([
                    ft.Text("Rescued vs. Adopted (14 Days)", size=14, weight=ft.FontWeight.W_600, color=ft.Colors.BLACK87),
                    ft.Divider(height=8, color=ft.Colors.GREY_300),
                    create_empty_chart_message(
                        "No rescue or adoption activity in the last 14 days",
                        height=180,
                        button_text="View Manage Records",
                        button_icon=ft.Icons.FOLDER_OPEN,
                        on_click=lambda e: page.go("/manage_records"),
                    ),
                ], spacing=5, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                width=420,
                height=270,
                padding=ft.padding.only(left=15, top=15, bottom=15, right=25),
                bgcolor=ft.Colors.WHITE,
                border_radius=12,
                shadow=ft.BoxShadow(blur_radius=8, spread_radius=1, color=ft.Colors.BLACK12, offset=ft.Offset(0, 2)),
            )

        has_breed_data = bool(breed_distribution)

        if has_breed_data:
            breed_labels = [breed for breed, _ in breed_distribution] if breed_distribution else []
            breed_values = [count for _, count in breed_distribution] if breed_distribution else []
            total_breeds = sum(breed_values) if breed_values else 0
            
            breed_sections = []
            breed_data_for_dialog = []  # For click dialog
            for i, (label, value) in enumerate(zip(breed_labels, breed_values)):
                pct = (value / total_breeds * 100) if total_breeds > 0 else 0
                color = PIE_CHART_COLORS[i % len(PIE_CHART_COLORS)]
                breed_sections.append({
                    "value": value,
                    "title": f"{pct:.0f}%",
                    "color": color,
                })
                breed_data_for_dialog.append({
                    "label": label,
                    "value": value,
                    "color": color,
                })
            
            breed_pie_refs = {}
            breed_pie_chart = create_pie_chart(
                sections=breed_sections,
                height=150,
                section_radius=60,
                center_space_radius=20,
                legend_refs=breed_pie_refs,
            )
            
            breed_legend = create_chart_legend([
                {"label": label, "color": PIE_CHART_COLORS[i % len(PIE_CHART_COLORS)], "value": value}
                for i, (label, value) in enumerate(zip(breed_labels, breed_values))
            ], horizontal=False, pie_refs=breed_pie_refs)
            
            def show_breed_details(e):
                show_chart_details_dialog(page, "Breed Distribution Breakdown", breed_data_for_dialog, "pie")
            
            breed_chart_container = ft.Container(
                ft.Column([
                    ft.Row([
                        ft.Text("Breed Distribution", size=14, weight=ft.FontWeight.W_600, color=ft.Colors.BLACK87),
                        ft.Container(
                            ft.IconButton(
                                icon=ft.Icons.OPEN_IN_NEW,
                                icon_size=16,
                                icon_color=ft.Colors.TEAL_600,
                                tooltip="View detailed breakdown",
                                on_click=show_breed_details,
                            ),
                            bgcolor=ft.Colors.TEAL_50,
                            border_radius=8,
                            border=ft.border.all(1, ft.Colors.TEAL_200),
                        ),
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Divider(height=8, color=ft.Colors.GREY_300),
                    ft.Row([
                        breed_pie_chart,
                        breed_legend,
                    ], alignment=ft.MainAxisAlignment.CENTER, spacing=10, expand=True),
                ], spacing=5, horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True),
                width=380,
                height=270,
                padding=15,
                bgcolor=ft.Colors.WHITE,
                border_radius=12,
                shadow=ft.BoxShadow(blur_radius=8, spread_radius=1, color=ft.Colors.BLACK12, offset=ft.Offset(0, 2)),
            )
        else:
            breed_chart_container = ft.Container(
                ft.Column([
                    ft.Text("Breed Distribution", size=14, weight=ft.FontWeight.W_600, color=ft.Colors.BLACK87),
                    ft.Divider(height=8, color=ft.Colors.GREY_300),
                    create_empty_chart_message(
                        "No breed data available yet",
                        height=180,
                        button_text="Add Animal",
                        button_icon=ft.Icons.ADD,
                        on_click=lambda e: page.go("/add_animal"),
                    ),
                ], spacing=5, horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True),
                width=380,
                height=270,
                padding=15,
                bgcolor=ft.Colors.WHITE,
                border_radius=12,
                shadow=ft.BoxShadow(blur_radius=8, spread_radius=1, color=ft.Colors.BLACK12, offset=ft.Offset(0, 2)),
            )

        # Chart 3: Health Status Bar Chart (Clickable)
        health_labels = ["Healthy", "Recovering", "Injured"]
        health_values = [status_counts.get("healthy", 0), status_counts.get("recovering", 0), status_counts.get("injured", 0)]
        health_colors = [STATUS_COLORS["healthy"], STATUS_COLORS["recovering"], STATUS_COLORS["injured"]]
        has_health_data = any(v > 0 for v in health_values)

        if has_health_data:
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
                width=320,
                height=298,
                padding=15,
                bgcolor=ft.Colors.WHITE,
                border_radius=12,
                shadow=ft.BoxShadow(blur_radius=8, spread_radius=1, color=ft.Colors.BLACK12, offset=ft.Offset(0, 2)),
            )
        else:
            health_chart_container = ft.Container(
                ft.Column([
                    ft.Text("Health Status", size=14, weight=ft.FontWeight.W_600, color=ft.Colors.BLACK87),
                    ft.Divider(height=8, color=ft.Colors.GREY_300),
                    create_empty_chart_message(
                        "No health status data available",
                        height=220,
                        button_text="Add Animal",
                        button_icon=ft.Icons.ADD,
                        on_click=lambda e: page.go("/add_animal"),
                    ),
                ], spacing=5, horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True),
                width=320,
                height=298,
                padding=15,
                bgcolor=ft.Colors.WHITE,
                border_radius=12,
                shadow=ft.BoxShadow(blur_radius=8, spread_radius=1, color=ft.Colors.BLACK12, offset=ft.Offset(0, 2)),
            )

        # Map: Realtime Rescue Mission Map
        is_online = self.map_service.check_map_tiles_available()
        
        if is_online:
            map_container = create_interactive_map(
                map_service=self.map_service,
                missions=missions,
                page=page,
                is_admin=True,
                height=250,
                title="Rescue Mission Map",
                show_legend=True,
                initially_locked=True,
            )
            # Wrap in fixed-size container for dashboard layout
            map_container = ft.Container(
                content=map_container,
                width=420,
            )
        else:
            offline_widget = self.map_service.create_offline_map_fallback(missions, is_admin=True)
            if offline_widget:
                map_container = ft.Container(
                    ft.Container(
                        ft.Column([
                            ft.Text("Rescue Mission Map", size=14, weight=ft.FontWeight.W_600, color=ft.Colors.BLACK87),
                            ft.Divider(height=8, color=ft.Colors.GREY_300),
                            offline_widget,
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=5,  expand=True),
                    margin=ft.margin.all(5),),
                    width=420,
                    height=298,
                    padding=15,
                    bgcolor=ft.Colors.WHITE,
                    border_radius=12,
                    shadow=ft.BoxShadow(blur_radius=8, spread_radius=1, color=ft.Colors.BLACK12, offset=ft.Offset(0, 2)),
                )
            else:
                # Final fallback to simple placeholder
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

        main_content = ft.Container(
            ft.Column([
                ft.Container(
                    ft.Row([
                        create_page_title("Admin Dashboard Overview"),
                        create_ai_download_button(
                            on_click=lambda e: create_ai_download_dialog(page),
                        ),
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    padding=ft.padding.only(bottom=15),
                ),
                ft.Container(
                    stat_cards,
                    alignment=ft.alignment.center,
                ),
                ft.Container(height=15),
                ft.Container(
                    ft.Row([
                        rescued_chart_container,
                        breed_chart_container,
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

        layout = ft.Row([
            sidebar,
            main_content,
        ], spacing=0, expand=True, vertical_alignment=ft.CrossAxisAlignment.START)

        finish_page_loading(page, _gradient_ref, layout)


__all__ = ["AdminDashboard"]

