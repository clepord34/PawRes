"""Analytics charts page with rescue and adoption statistics."""
from __future__ import annotations

from typing import Optional, Dict, Any, Tuple, List
from datetime import datetime, timedelta

import app_config
from services.animal_service import AnimalService
from services.rescue_service import RescueService
from services.adoption_service import AdoptionService
from services.analytics_service import AnalyticsService
from components import (
    create_admin_sidebar, create_gradient_background,
    create_page_title, create_chart_container, create_stat_card,
    create_line_chart, create_bar_chart, create_pie_chart,
    create_chart_legend, create_empty_chart_message, create_insight_card,
    create_chart_card, create_clickable_stat_card, show_chart_details_dialog,
    CHART_COLORS, PIE_CHART_COLORS, STATUS_COLORS
)


class ChartsPage:
    def __init__(self, db_path: Optional[str] = None) -> None:
        self.animal_service = AnimalService(db_path or app_config.DB_PATH)
        self.rescue_service = RescueService(db_path or app_config.DB_PATH)
        self.adoption_service = AdoptionService(db_path or app_config.DB_PATH)
        self.analytics_service = AnalyticsService(db_path or app_config.DB_PATH)

    def build(self, page) -> None:
        try:
            import flet as ft
        except Exception as exc:
            raise RuntimeError("Flet must be installed to build the UI") from exc

        page.title = "Data Analytics"

        # Sidebar with navigation
        sidebar = create_admin_sidebar(page, current_route=page.route)

        # Fetch data using analytics service
        (months, rescued_counts, adopted_counts), type_dist, status_counts = self.analytics_service.get_chart_data()

        # Calculate statistics
        total_rescued = sum(rescued_counts)
        total_adopted = sum(adopted_counts)
        pending_requests = self.adoption_service.get_all_requests() or []
        total_pending = len([r for r in pending_requests if (r.get("status") or "").lower() == "pending"])
        
        # Get actual percentage changes
        changes = self.analytics_service.get_monthly_changes()
        rescues_change = changes["rescues_change"]
        adoptions_change = changes["adoptions_change"]
        pending_change = changes["pending_change"]

        # Get additional analytics data
        rescue_status_dist = self.analytics_service.get_rescue_status_distribution()
        adoption_status_dist = self.analytics_service.get_adoption_status_distribution()
        urgency_dist = self.analytics_service.get_urgency_distribution()
        species_ranking = self.analytics_service.get_species_adoption_ranking(limit=5)
        insights = self.analytics_service.get_chart_insights()

        # Line chart: rescued vs adopted trend (last 1 month / 30 days)
        has_line_data = any(c > 0 for c in rescued_counts) or any(c > 0 for c in adopted_counts)
        
        if has_line_data:
            # Build data series for line chart
            line_data = [
                {"label": "Rescued", "color": CHART_COLORS["primary"], "values": list(zip(range(len(months)), rescued_counts))},
                {"label": "Adopted", "color": CHART_COLORS["secondary"], "values": list(zip(range(len(months)), adopted_counts))},
            ]
            line_chart = create_line_chart(line_data, width=600, height=220, x_labels=months)
            line_legend = create_chart_legend([
                {"label": "Rescued", "color": CHART_COLORS["primary"], "value": sum(rescued_counts)},
                {"label": "Adopted", "color": CHART_COLORS["secondary"], "value": sum(adopted_counts)},
            ], horizontal=False)
        else:
            line_chart = create_empty_chart_message("No rescue/adoption data available yet", width=600, height=220)
            line_legend = ft.Container()

        # Pie chart: type distribution
        type_pie_refs = {}  # For legend-pie sync
        if type_dist and sum(type_dist.values()) > 0:
            type_sections = []
            total = sum(type_dist.values())
            for idx, (label, value) in enumerate(type_dist.items()):
                pct = (value / total * 100) if total > 0 else 0
                type_sections.append({
                    "value": value,
                    "title": f"{label}\n{pct:.1f}%",
                    "color": PIE_CHART_COLORS[idx % len(PIE_CHART_COLORS)],
                })
            type_pie_chart = create_pie_chart(type_sections, width=180, height=180, legend_refs=type_pie_refs)
            type_legend = create_chart_legend([
                {"label": label, "color": PIE_CHART_COLORS[idx % len(PIE_CHART_COLORS)], "value": value}
                for idx, (label, value) in enumerate(type_dist.items())
            ], horizontal=False, pie_refs=type_pie_refs)
        else:
            type_pie_chart = create_empty_chart_message("No animal type data", width=180, height=180)
            type_legend = ft.Container()

        # Bar chart: health status
        health_bar_refs = {}  # For legend-bar sync
        health_statuses = ["healthy", "recovering", "injured"]
        health_counts = [status_counts.get(s, 0) for s in health_statuses]
        has_health_data = any(c > 0 for c in health_counts)
        
        if has_health_data:
            health_bar_groups = []
            health_colors = [STATUS_COLORS["healthy"], STATUS_COLORS["recovering"], STATUS_COLORS["injured"]]
            for idx, (status, count) in enumerate(zip(health_statuses, health_counts)):
                health_bar_groups.append({
                    "x": idx,
                    "rods": [{"value": count, "color": health_colors[idx], "width": 40}]
                })
            health_bar_chart = create_bar_chart(
                health_bar_groups, 
                bottom_labels={i: s.capitalize() for i, s in enumerate(health_statuses)},
                width=250, height=200,
                legend_refs=health_bar_refs,
            )
            health_legend = create_chart_legend([
                {"label": s.capitalize(), "color": health_colors[i], "value": health_counts[i]}
                for i, s in enumerate(health_statuses)
            ], horizontal=False, bar_refs=health_bar_refs)
        else:
            health_bar_chart = create_empty_chart_message("No health status data", width=280, height=200)
            health_legend = ft.Container()

        # Rescue Status Pie Chart
        rescue_pie_refs = {}  # For legend-pie sync
        if rescue_status_dist and sum(rescue_status_dist.values()) > 0:
            rescue_sections = []
            total = sum(rescue_status_dist.values())
            status_order = ["pending", "on-going", "rescued", "failed"]
            for status in status_order:
                if status in rescue_status_dist:
                    value = rescue_status_dist[status]
                    pct = (value / total * 100) if total > 0 else 0
                    rescue_sections.append({
                        "value": value,
                        "title": f"{status.capitalize()}\n{pct:.1f}%",
                        "color": STATUS_COLORS.get(status, STATUS_COLORS["default"]),
                    })
            rescue_pie_chart = create_pie_chart(rescue_sections, width=180, height=180, legend_refs=rescue_pie_refs)
            rescue_legend = create_chart_legend([
                {"label": s.capitalize(), "color": STATUS_COLORS.get(s, STATUS_COLORS["default"]), "value": rescue_status_dist.get(s, 0)}
                for s in status_order if s in rescue_status_dist
            ], horizontal=False, pie_refs=rescue_pie_refs)
        else:
            rescue_pie_chart = create_empty_chart_message("No rescue mission data", width=180, height=180)
            rescue_legend = ft.Container()

        # Adoption Status Pie Chart
        adoption_pie_refs = {}  # For legend-pie sync
        if adoption_status_dist and sum(adoption_status_dist.values()) > 0:
            adoption_sections = []
            total = sum(adoption_status_dist.values())
            status_order = ["pending", "approved", "denied"]
            for status in status_order:
                if status in adoption_status_dist:
                    value = adoption_status_dist[status]
                    pct = (value / total * 100) if total > 0 else 0
                    adoption_sections.append({
                        "value": value,
                        "title": f"{status.capitalize()}\n{pct:.1f}%",
                        "color": STATUS_COLORS.get(status, STATUS_COLORS["default"]),
                    })
            adoption_pie_chart = create_pie_chart(adoption_sections, width=180, height=180, legend_refs=adoption_pie_refs)
            adoption_legend = create_chart_legend([
                {"label": s.capitalize(), "color": STATUS_COLORS.get(s, STATUS_COLORS["default"]), "value": adoption_status_dist.get(s, 0)}
                for s in status_order if s in adoption_status_dist
            ], horizontal=False, pie_refs=adoption_pie_refs)
        else:
            adoption_pie_chart = create_empty_chart_message("No adoption data", width=180, height=180)
            adoption_legend = ft.Container()

        # Urgency Distribution Bar Chart
        urgency_bar_refs = {}  # For legend-bar sync
        if urgency_dist and sum(urgency_dist.values()) > 0:
            urgency_order = ["low", "medium", "high", "critical"]
            urgency_colors = {
                "low": STATUS_COLORS["healthy"],
                "medium": STATUS_COLORS["pending"],
                "high": STATUS_COLORS["recovering"],
                "critical": STATUS_COLORS["failed"],
            }
            urgency_bar_groups = []
            for idx, level in enumerate(urgency_order):
                if level in urgency_dist:
                    urgency_bar_groups.append({
                        "x": idx,
                        "rods": [{"value": urgency_dist[level], "color": urgency_colors[level], "width": 40}]
                    })
            urgency_bar_chart = create_bar_chart(
                urgency_bar_groups,
                bottom_labels={idx: level.capitalize() for idx, level in enumerate(urgency_order) if level in urgency_dist},
                width=280, height=200,
                legend_refs=urgency_bar_refs,
            )
            urgency_legend = create_chart_legend([
                {"label": level.capitalize(), "color": urgency_colors[level], "value": urgency_dist.get(level, 0)}
                for level in urgency_order if level in urgency_dist
            ], horizontal=False, bar_refs=urgency_bar_refs)
        else:
            urgency_bar_chart = create_empty_chart_message("No urgency data", width=280, height=200)
            urgency_legend = ft.Container()

        # Top Species for Adoption (Horizontal Bar Chart)
        species_bar_refs = {}  # For legend-bar sync
        if species_ranking:
            species_bar_groups = []
            for idx, (species, count) in enumerate(species_ranking):
                species_bar_groups.append({
                    "x": idx,
                    "rods": [{"value": count, "color": PIE_CHART_COLORS[idx % len(PIE_CHART_COLORS)], "width": 40}]
                })
            species_bar_chart = create_bar_chart(
                species_bar_groups,
                bottom_labels={idx: species for idx, (species, _) in enumerate(species_ranking)},
                width=200, height=200,
                legend_refs=species_bar_refs,
            )
            species_legend = create_chart_legend([
                {"label": species, "color": PIE_CHART_COLORS[idx % len(PIE_CHART_COLORS)], "value": count}
                for idx, (species, count) in enumerate(species_ranking)
            ], horizontal=False, bar_refs=species_bar_refs)
        else:
            species_bar_chart = create_empty_chart_message("No species data", width=200, height=200)
            species_legend = ft.Container()

        # Get real rescue mission data for map
        from services.map_service import MapService
        map_service = MapService()
        missions = self.rescue_service.get_all_missions() or []
        map_widget = map_service.create_map_with_markers(missions, is_admin=True)

        # Build clickable stat cards
        stats_row = ft.Row([
            create_clickable_stat_card(
                title="Total Animals Rescued",
                value=str(total_rescued),
                subtitle=rescues_change,
                icon=ft.Icons.PETS,
                icon_color=ft.Colors.GREEN_600,
                on_click=lambda e: page.go("/rescue_missions?admin=1"),
            ),
            create_clickable_stat_card(
                title="Total Adoptions",
                value=f"{total_adopted:,}",
                subtitle=adoptions_change,
                icon=ft.Icons.FAVORITE,
                icon_color=ft.Colors.ORANGE_600,
                on_click=lambda e: page.go("/adoption_requests"),
            ),
            create_clickable_stat_card(
                title="Pending Applications",
                value=str(total_pending),
                subtitle=pending_change,
                icon=ft.Icons.PENDING_ACTIONS,
                icon_color=ft.Colors.BLUE_600,
                on_click=lambda e: page.go("/adoption_requests"),
            ),
        ], spacing=15, expand=True)

        # Chart containers with Flet native charts
        chart1_container = ft.Container(
            ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.SHOW_CHART, size=20, color=ft.Colors.TEAL_600),
                    ft.Text("Rescued vs. Adopted (Last 30 Days)", size=16, weight="w600", color=ft.Colors.BLACK87),
                ], spacing=10),
                ft.Divider(height=12, color=ft.Colors.GREY_200),
                ft.Row([
                    ft.Container(line_chart, padding=ft.padding.only(top=10)),
                    ft.Container(line_legend, padding=ft.padding.only(left=15, top=10)),
                ], alignment=ft.MainAxisAlignment.CENTER, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            ], spacing=8, horizontal_alignment="center"),
            padding=25,
            bgcolor=ft.Colors.WHITE,
            border_radius=12,
            border=ft.border.all(1, ft.Colors.GREY_200),
            shadow=ft.BoxShadow(blur_radius=8, spread_radius=1, color=ft.Colors.BLACK12, offset=(0, 2)),
        )

        # Helper to create consistent chart cards with legend beside (clickable expand icon only)
        def create_chart_card_container(title: str, chart: Any, legend: Any, icon: Any = None, data_for_dialog: List = None) -> Any:
            def show_details(e):
                if data_for_dialog:
                    show_chart_details_dialog(page, f"{title} Details", data_for_dialog, "pie")
            
            return ft.Container(
                ft.Column([
                    ft.Row([
                        ft.Icon(icon or ft.Icons.PIE_CHART, size=18, color=ft.Colors.TEAL_600),
                        ft.Text(title, size=14, weight="w600", color=ft.Colors.BLACK87, expand=True),
                        ft.Container(
                            ft.IconButton(
                                icon=ft.Icons.OPEN_IN_NEW,
                                icon_size=16,
                                icon_color=ft.Colors.TEAL_600,
                                tooltip="View detailed breakdown",
                                on_click=show_details,
                            ),
                            bgcolor=ft.Colors.TEAL_50,
                            border_radius=8,
                            border=ft.border.all(1, ft.Colors.TEAL_200),
                        ) if data_for_dialog else ft.Container(),
                    ], spacing=8),
                    ft.Divider(height=12, color=ft.Colors.GREY_200),
                    ft.Row([
                        ft.Container(chart, alignment=ft.alignment.center),
                        ft.Container(legend, alignment=ft.alignment.center_left, padding=ft.padding.only(left=10)),
                    ], alignment=ft.MainAxisAlignment.CENTER, vertical_alignment=ft.CrossAxisAlignment.CENTER, expand=True),
                ], spacing=5, horizontal_alignment="center", expand=True),
                padding=20,
                height=280,
                bgcolor=ft.Colors.WHITE,
                border_radius=12,
                border=ft.border.all(1, ft.Colors.GREY_200),
                shadow=ft.BoxShadow(blur_radius=8, spread_radius=1, color=ft.Colors.BLACK12, offset=(0, 2)),
                expand=True,
            )
        
        # Build data arrays for click dialogs
        type_data = [{"label": label, "value": value, "color": PIE_CHART_COLORS[idx % len(PIE_CHART_COLORS)]}
                     for idx, (label, value) in enumerate(type_dist.items())] if type_dist else []
        
        rescue_data = [{"label": s.capitalize(), "value": rescue_status_dist.get(s, 0), "color": STATUS_COLORS.get(s, STATUS_COLORS["default"])}
                       for s in ["pending", "on-going", "rescued", "failed"] if s in rescue_status_dist] if rescue_status_dist else []
        
        adoption_data = [{"label": s.capitalize(), "value": adoption_status_dist.get(s, 0), "color": STATUS_COLORS.get(s, STATUS_COLORS["default"])}
                         for s in ["pending", "approved", "denied"] if s in adoption_status_dist] if adoption_status_dist else []

        # Pie charts row
        pie_charts_row = ft.Row([
            create_chart_card_container("Animal Type Distribution", type_pie_chart, type_legend, ft.Icons.CATEGORY, type_data),
            create_chart_card_container("Rescue Mission Status", rescue_pie_chart, rescue_legend, ft.Icons.PETS, rescue_data),
            create_chart_card_container("Adoption Request Status", adoption_pie_chart, adoption_legend, ft.Icons.FAVORITE, adoption_data),
        ], spacing=15, expand=True)

        # Helper for bar chart cards with legend beside (clickable expand icon only)
        def create_bar_chart_card(title: str, chart: Any, legend: Any = None, icon: Any = None, data_for_dialog: List = None) -> Any:
            def show_details(e):
                if data_for_dialog:
                    show_chart_details_dialog(page, f"{title} Details", data_for_dialog, "bar")
            
            if legend:
                chart_content = ft.Row([
                    ft.Container(chart, alignment=ft.alignment.center),
                    ft.Container(legend, alignment=ft.alignment.center_left, padding=ft.padding.only(left=10)),
                ], alignment=ft.MainAxisAlignment.CENTER, vertical_alignment=ft.CrossAxisAlignment.CENTER, expand=True)
            else:
                chart_content = ft.Container(chart, alignment=ft.alignment.center, expand=True)
            
            return ft.Container(
                ft.Column([
                    ft.Row([
                        ft.Icon(icon or ft.Icons.BAR_CHART, size=18, color=ft.Colors.TEAL_600),
                        ft.Text(title, size=14, weight="w600", color=ft.Colors.BLACK87, expand=True),
                        ft.Container(
                            ft.IconButton(
                                icon=ft.Icons.OPEN_IN_NEW,
                                icon_size=16,
                                icon_color=ft.Colors.TEAL_600,
                                tooltip="View detailed breakdown",
                                on_click=show_details,
                            ),
                            bgcolor=ft.Colors.TEAL_50,
                            border_radius=8,
                            border=ft.border.all(1, ft.Colors.TEAL_200),
                        ) if data_for_dialog else ft.Container(),
                    ], spacing=8),
                    ft.Divider(height=12, color=ft.Colors.GREY_200),
                    chart_content,
                ], spacing=5, horizontal_alignment="center", expand=True),
                padding=20,
                height=280,
                bgcolor=ft.Colors.WHITE,
                border_radius=12,
                border=ft.border.all(1, ft.Colors.GREY_200),
                shadow=ft.BoxShadow(blur_radius=8, spread_radius=1, color=ft.Colors.BLACK12, offset=(0, 2)),
                expand=True,
            )
        
        # Build data arrays for bar chart dialogs
        health_data = [{"label": s.capitalize(), "value": status_counts.get(s, 0), "color": STATUS_COLORS.get(s, STATUS_COLORS["default"])}
                       for s in ["healthy", "recovering", "injured"]]
        
        urgency_data = [{"label": level.capitalize(), "value": urgency_dist.get(level, 0), 
                        "color": {"low": STATUS_COLORS["healthy"], "medium": STATUS_COLORS["pending"], 
                                  "high": STATUS_COLORS["recovering"], "critical": STATUS_COLORS["failed"]}.get(level)}
                        for level in ["low", "medium", "high", "critical"] if level in urgency_dist] if urgency_dist else []
        
        species_data = [{"label": species, "value": count, "color": PIE_CHART_COLORS[idx % len(PIE_CHART_COLORS)]}
                        for idx, (species, count) in enumerate(species_ranking)] if species_ranking else []

        # Bar charts row
        bar_charts_row = ft.Row([
            create_bar_chart_card("Health Status Breakdown", health_bar_chart, health_legend, ft.Icons.HEALTH_AND_SAFETY, health_data),
            create_bar_chart_card("Rescue Urgency Distribution", urgency_bar_chart, urgency_legend, ft.Icons.WARNING_AMBER, urgency_data),
            create_bar_chart_card("Top Species for Adoption", species_bar_chart, species_legend, ft.Icons.TRENDING_UP, species_data),
        ], spacing=15, expand=True)

        # Insights row with improved styling
        def create_insight_box(title: str, insight_data: dict, icon: Any, icon_color: str, bg_color: str, border_color: str) -> Any:
            """Create a styled insight box with headline, detail, and action."""
            if isinstance(insight_data, dict):
                headline = insight_data.get("headline", "No data")
                detail = insight_data.get("detail", "")
                action = insight_data.get("action", "")
            else:
                # Fallback for string format
                headline = str(insight_data)
                detail = ""
                action = ""
            
            content_items = [
                ft.Row([
                    ft.Container(
                        ft.Icon(icon, size=20, color=ft.Colors.WHITE),
                        width=36,
                        height=36,
                        bgcolor=icon_color,
                        border_radius=18,
                        alignment=ft.alignment.center,
                    ),
                    ft.Text(title, size=14, weight="bold", color=icon_color),
                ], spacing=10),
                ft.Container(height=12),
                ft.Text(headline, size=15, weight="w600", color=ft.Colors.BLACK87),
            ]
            
            if detail:
                content_items.append(ft.Container(height=6))
                content_items.append(ft.Text(detail, size=12, color=ft.Colors.BLACK54))
            
            if action:
                content_items.append(ft.Container(height=10))
                content_items.append(
                    ft.Container(
                        ft.Text(action, size=11, color=icon_color, weight="w500"),
                        bgcolor=ft.Colors.with_opacity(0.1, icon_color),
                        padding=ft.padding.symmetric(horizontal=10, vertical=6),
                        border_radius=6,
                    )
                )
            
            return ft.Container(
                ft.Column(content_items, spacing=0),
                padding=20,
                bgcolor=bg_color,
                border_radius=12,
                border=ft.border.all(1, border_color),
                expand=True,
            )
        
        # Get structured insight data
        rescue_insight_data = insights.get("rescue_insight", {"headline": "No data", "detail": "", "action": ""})
        adoption_insight_data = insights.get("adoption_insight", {"headline": "No data", "detail": "", "action": ""})
        health_insight_data = insights.get("health_insight", {"headline": "No data", "detail": "", "action": ""})
        
        insights_row = ft.Container(
            ft.Column([
                ft.Row([
                    ft.Container(
                        ft.Icon(ft.Icons.AUTO_AWESOME, size=22, color=ft.Colors.WHITE),
                        width=40,
                        height=40,
                        bgcolor=ft.Colors.TEAL_600,
                        border_radius=20,
                        alignment=ft.alignment.center,
                    ),
                    ft.Column([
                        ft.Text("Key Insights", size=20, weight="bold", color=ft.Colors.BLACK87),
                        ft.Text("Smart analysis of your shelter operations", size=12, color=ft.Colors.BLACK54),
                    ], spacing=2),
                ], spacing=12),
                ft.Divider(height=24, color=ft.Colors.GREY_300),
                ft.Row([
                    create_insight_box(
                        "Rescue Operations",
                        rescue_insight_data,
                        ft.Icons.PETS,
                        ft.Colors.BLUE_600,
                        ft.Colors.BLUE_50,
                        ft.Colors.BLUE_100,
                    ),
                    create_insight_box(
                        "Adoption Progress", 
                        adoption_insight_data,
                        ft.Icons.FAVORITE,
                        ft.Colors.ORANGE_600,
                        ft.Colors.ORANGE_50,
                        ft.Colors.ORANGE_100,
                    ),
                    create_insight_box(
                        "Animal Health",
                        health_insight_data,
                        ft.Icons.HEALTH_AND_SAFETY,
                        ft.Colors.GREEN_600,
                        ft.Colors.GREEN_50,
                        ft.Colors.GREEN_100,
                    ),
                ], spacing=15, expand=True),
            ], spacing=0),
            padding=25,
            bgcolor=ft.Colors.WHITE,
            border_radius=12,
            shadow=ft.BoxShadow(blur_radius=10, spread_radius=2, color=ft.Colors.BLACK12, offset=(0, 3)),
        )

        # Create map container with real map or fallback placeholder
        if map_widget:
            map_content = ft.Container(
                map_widget,
                height=500,
                border_radius=8,
                clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
                border=ft.border.all(1, ft.Colors.GREY_300),
            )
        else:
            map_content = map_service.create_empty_map_placeholder(len(missions))
        
        map_container = ft.Container(
            ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.MAP, size=20, color=ft.Colors.TEAL_600),
                    ft.Text("Realtime Rescue Mission Map", size=16, weight="w600", color=ft.Colors.BLACK87),
                ], spacing=10),
                ft.Divider(height=12, color=ft.Colors.GREY_200),
                map_content,
            ], spacing=8, horizontal_alignment="center"),
            padding=25,
            bgcolor=ft.Colors.WHITE,
            border_radius=12,
            border=ft.border.all(1, ft.Colors.GREY_200),
            shadow=ft.BoxShadow(blur_radius=8, spread_radius=1, color=ft.Colors.BLACK12, offset=(0, 2)),
        )

        # Refresh and Back buttons
        refresh_btn = ft.ElevatedButton(
            "Refresh",
            width=120,
            height=45,
            on_click=lambda e: self.build(page),
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.TEAL_600,
                color=ft.Colors.WHITE,
                shape=ft.RoundedRectangleBorder(radius=8),
                text_style=ft.TextStyle(size=13, weight="w500"),
            )
        )

        back_btn = ft.ElevatedButton(
            "Back",
            width=120,
            height=45,
            on_click=lambda e: page.go("/admin"),
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.WHITE,
                color=ft.Colors.TEAL_600,
                shape=ft.RoundedRectangleBorder(radius=8),
                side=ft.BorderSide(2, ft.Colors.TEAL_600),
                text_style=ft.TextStyle(size=13, weight="w500"),
            )
        )

        # Main content area
        main_content = ft.Container(
            ft.Column([
                ft.Text("Data Analytics", size=28, weight="bold", color=ft.Colors.with_opacity(0.6, ft.Colors.BLACK)),
                ft.Container(height=15),
                stats_row,
                ft.Container(height=20),
                chart1_container,
                ft.Container(height=20),
                pie_charts_row,
                ft.Container(height=20),
                bar_charts_row,
                ft.Container(height=20),
                insights_row,
                ft.Container(height=20),
                map_container,
                ft.Container(height=20),
                ft.Row([refresh_btn, back_btn], alignment="center", spacing=15),
            ], spacing=0, scroll=ft.ScrollMode.AUTO),
            padding=30,
            expand=True,
        )

        # Main layout with sidebar
        main_layout = ft.Row([
            sidebar,
            main_content,
        ], spacing=0, expand=True)

        page.controls.clear()
        page.add(create_gradient_background(main_layout))
        page.update()


__all__ = ["ChartsPage"]


