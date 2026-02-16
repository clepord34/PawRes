"""Analytics charts page with rescue and adoption statistics."""
from __future__ import annotations

from typing import Optional, Any, List

import app_config
from services.animal_service import AnimalService
from services.rescue_service import RescueService
from services.adoption_service import AdoptionService
from services.analytics_service import AnalyticsService
from components import (
    create_admin_sidebar, create_gradient_background,
    create_line_chart, create_bar_chart, create_pie_chart,
    create_scrollable_chart_content,
    create_chart_legend, create_empty_chart_message, create_insight_box, create_clickable_stat_card, 
    show_chart_details_dialog, CHART_COLORS, PIE_CHART_COLORS, STATUS_COLORS,
    create_interactive_map,
    show_page_loading, finish_page_loading,
    is_mobile, create_responsive_layout, responsive_padding,
    create_admin_drawer,
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

        _mobile = is_mobile(page)
        sidebar = create_admin_sidebar(page, current_route=page.route)
        drawer = create_admin_drawer(page, current_route=page.route) if _mobile else None
        _gradient_ref = show_page_loading(page, None if _mobile else sidebar, "Loading charts...")
        sidebar = create_admin_sidebar(page, current_route=page.route)

        line_chart_width = 300 if _mobile else None
        line_chart_height = 220 if _mobile else 270
        trend_chart_width = 300 if _mobile else None
        trend_chart_height = 200 if _mobile else 220

        def _build_horizontal_panel(chart: Any, legend: Any = None) -> Any:
            return create_scrollable_chart_content(
                chart,
                legend,
                chart_width=300 if _mobile else 340,
                legend_width=170 if _mobile else 180,
                legend_height=220 if _mobile else 240,
            )

        (months, rescued_counts, adopted_counts), type_dist, status_counts = self.analytics_service.get_chart_data()

        total_rescued = sum(rescued_counts)
        total_adopted = sum(adopted_counts)
        pending_requests = self.adoption_service.get_all_requests() or []
        total_pending = len([r for r in pending_requests if (r.get("status") or "").lower() == "pending"])
        total_requests = len([r for r in pending_requests if (r.get("status") or "").lower() in ["pending", "approved", "denied"]])
        
        pending_rescues = self.analytics_service.get_pending_rescue_missions()
        
        changes = self.analytics_service.get_monthly_changes()
        rescues_change = changes["rescues_change"]
        adoptions_change = changes["adoptions_change"]
        pending_change = changes["pending_change"]
        pending_rescues_change = changes["rescues_change"]  # Use rescues change for pending rescues

        rescue_status_dist = self.analytics_service.get_rescue_status_distribution()
        adoption_status_dist = self.analytics_service.get_adoption_status_distribution()
        urgency_dist = self.analytics_service.get_urgency_distribution()
        species_ranking = self.analytics_service.get_species_adoption_ranking(limit=5)
        insights = self.analytics_service.get_chart_insights()
        
        breed_distribution = self.analytics_service.get_breed_distribution()  # All animals, no limit

        # Line chart: rescued vs adopted trend (last 1 month / 30 days)
        has_line_data = any(c > 0 for c in rescued_counts) or any(c > 0 for c in adopted_counts)
        
        line_refs = {}  # For legend-line sync
        if has_line_data:
            line_data = [
                {"label": "Rescued", "color": CHART_COLORS["primary"], "values": list(zip(range(len(months)), rescued_counts))},
                {"label": "Adopted", "color": CHART_COLORS["secondary"], "values": list(zip(range(len(months)), adopted_counts))},
            ]
            line_chart = create_line_chart(line_data, width=line_chart_width, height=line_chart_height, x_labels=months, legend_refs=line_refs)
            line_legend = create_chart_legend([
                {"label": "Rescued", "color": CHART_COLORS["primary"], "value": sum(rescued_counts)},
                {"label": "Adopted", "color": CHART_COLORS["secondary"], "value": sum(adopted_counts)},
            ], horizontal=False, line_refs=line_refs)
        else:
            line_chart = create_empty_chart_message("No rescue/adoption data available yet", width=line_chart_width, height=line_chart_height,
                button_text="View Manage Records", button_icon=ft.Icons.FOLDER_OPEN,
                on_click=lambda e: page.go("/manage_records"))
            line_legend = ft.Container()

        chart1_body = _build_horizontal_panel(line_chart, line_legend)

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
            type_pie_chart = create_empty_chart_message("No animal type data", width=260, height=180,
                button_text="Add Animal", button_icon=ft.Icons.ADD,
                on_click=lambda e: page.go("/add_animal"))
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
            health_bar_chart = create_empty_chart_message("No health status data", width=280, height=200,
                button_text="Add Animal", button_icon=ft.Icons.ADD,
                on_click=lambda e: page.go("/add_animal"))
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
            rescue_pie_chart = create_empty_chart_message("No rescue mission data", width=260, height=180,
                button_text="View Rescues", button_icon=ft.Icons.LOCAL_HOSPITAL,
                on_click=lambda e: page.go("/rescue_missions?admin=1"))
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
            adoption_pie_chart = create_empty_chart_message("No adoption data", width=260, height=180,
                button_text="View Adoptions", button_icon=ft.Icons.VOLUNTEER_ACTIVISM,
                on_click=lambda e: page.go("/adoption_requests"))
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
            urgency_bar_chart = create_empty_chart_message("No urgency data", width=280, height=200,
                button_text="View Rescues", button_icon=ft.Icons.LOCAL_HOSPITAL,
                on_click=lambda e: page.go("/rescue_missions?admin=1"))
            urgency_legend = ft.Container()

        from services.map_service import MapService
        map_service = MapService()
        missions = self.rescue_service.get_all_missions() or []
        
        is_online = map_service.check_map_tiles_available()

        stats_row = ft.ResponsiveRow([
            ft.Container(
                create_clickable_stat_card(
                    title="Animals Rescued",
                    value=str(total_rescued),
                    subtitle=rescues_change,
                    icon=ft.Icons.PETS,
                    icon_color=ft.Colors.GREEN_600,
                    on_click=lambda e: page.go("/manage_records?tab=0"),
                ),
                col={"xs": 6, "md": 3},
            ),
            ft.Container(
                create_clickable_stat_card(
                    title="Adoption Requests",
                    value=f"{total_requests:,}",
                    subtitle=f"{total_adopted} approved",
                    icon=ft.Icons.FAVORITE,
                    icon_color=ft.Colors.ORANGE_600,
                    on_click=lambda e: page.go("/manage_records?tab=1"),
                ),
                col={"xs": 6, "md": 3},
            ),
            ft.Container(
                create_clickable_stat_card(
                    title="Pending Adoptions",
                    value=str(total_pending),
                    subtitle=pending_change,
                    icon=ft.Icons.PENDING_ACTIONS,
                    icon_color=ft.Colors.BLUE_600,
                    on_click=lambda e: page.go("/manage_records?tab=1"),
                ),
                col={"xs": 6, "md": 3},
            ),
            ft.Container(
                create_clickable_stat_card(
                    title="Pending Rescues",
                    value=str(pending_rescues),
                    subtitle=pending_rescues_change,
                    icon=ft.Icons.EMERGENCY,
                    icon_color=ft.Colors.RED_600,
                    on_click=lambda e: page.go("/manage_records?tab=0"),
                ),
                col={"xs": 6, "md": 3},
            ),
        ], spacing=15, run_spacing=15)

        # Chart containers with Flet native charts
        chart1_container = ft.Container(
            ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.SHOW_CHART, size=20, color=ft.Colors.TEAL_600),
                    ft.Text("Rescued vs. Adopted (Last 30 Days)", size=16, weight="w600", color=ft.Colors.BLACK87, expand=True, max_lines=2),
                ], spacing=10),
                ft.Divider(height=12, color=ft.Colors.GREY_200),
                chart1_body,
            ], spacing=8, horizontal_alignment="center"),
            padding=ft.padding.only(top=20 if _mobile else 25, bottom=20 if _mobile else 50, left=16 if _mobile else 25, right=16 if _mobile else 25),
            bgcolor=ft.Colors.WHITE,
            border_radius=12,
            border=ft.border.all(1, ft.Colors.GREY_200),
            shadow=ft.BoxShadow(blur_radius=8, spread_radius=1, color=ft.Colors.BLACK12, offset=(0, 2)),
            expand=True,
        )
        
        # Breed trend chart with toggle (adoption vs rescue)
        breed_trend_mode = ft.Ref[ft.Tabs]()
        breed_chart_content = ft.Ref[ft.Container]()
        
        def build_breed_trend_chart(mode: str) -> tuple:
            """Build breed trend chart for given mode (adoption or rescue)."""
            day_labels, breed_series = self.analytics_service.get_breed_trends(mode=mode)
            
            if mode == "adoption":
                breed_colors = ["#9C27B0", "#E91E63", "#26C6DA"]  # Purple, Pink, Cyan
            else:
                breed_colors = [CHART_COLORS["primary"], CHART_COLORS["secondary"], "#AB47BC"]  # Teal, Orange, Purple
            line_data = []
            legend_data = []
            
            # Always build legend for top 3 breeds, even if no data in 30-day window
            if not breed_series:
                # If no breed data at all, show empty state with no legend
                return create_empty_chart_message(f"No {mode} breed data available yet", width=600, height=220,
                    button_text="Add Animal", button_icon=ft.Icons.ADD,
                    on_click=lambda e: page.go("/add_animal")), ft.Container()
            
            for idx, (breed_name, counts) in enumerate(breed_series[:3]):
                color = breed_colors[idx] if idx < len(breed_colors) else PIE_CHART_COLORS[idx % len(PIE_CHART_COLORS)]
                line_data.append({
                    "label": breed_name,
                    "color": color,
                    "values": list(zip(range(len(day_labels)), counts))
                })
                legend_data.append({
                    "label": breed_name,
                    "color": color,
                    "value": sum(counts)
                })
            
            breed_line_refs = {}  # For legend-line sync
            if line_data:
                chart = create_line_chart(line_data, width=trend_chart_width, height=trend_chart_height, x_labels=day_labels, legend_refs=breed_line_refs)
                legend = create_chart_legend(legend_data, horizontal=False, line_refs=breed_line_refs) if legend_data else ft.Container()
            else:
                chart = create_empty_chart_message(f"No {mode} breed data available yet", width=trend_chart_width, height=trend_chart_height,
                    button_text="Add Animal", button_icon=ft.Icons.ADD,
                    on_click=lambda e: page.go("/add_animal"))
                legend = ft.Container()
            return chart, legend
        
        def on_breed_tab_change(e):
            """Handle tab change for breed trends."""
            mode = "adoption" if breed_trend_mode.current.selected_index == 0 else "rescue"
            chart, legend = build_breed_trend_chart(mode)
            breed_chart_content.current.content = _build_horizontal_panel(chart, legend)
            page.update()
        
        # Initial breed trend chart (adoption mode)
        initial_breed_chart, initial_breed_legend = build_breed_trend_chart("adoption")
        
        breed_trend_container = ft.Container(
            ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.TRENDING_UP, size=20, color=ft.Colors.TEAL_600),
                    ft.Text("Top 3 Breed Trends (Last 30 Days)", size=16, weight="w600", color=ft.Colors.BLACK87, expand=True, max_lines=2),
                ], spacing=10),
                ft.Divider(height=8, color=ft.Colors.GREY_200),
                ft.Tabs(
                    ref=breed_trend_mode,
                    selected_index=0,
                    animation_duration=300,
                    on_change=on_breed_tab_change,
                    tabs=[
                        ft.Tab(text="Adoption Trends", icon=ft.Icons.FAVORITE),
                        ft.Tab(text="Rescue Trends", icon=ft.Icons.PETS),
                    ],
                    indicator_color=ft.Colors.TEAL_600,
                    label_color=ft.Colors.TEAL_600,
                    unselected_label_color=ft.Colors.GREY_600,
                ),
                ft.Container(
                    ref=breed_chart_content,
                    content=_build_horizontal_panel(initial_breed_chart, initial_breed_legend),
                ),
            ], spacing=8, horizontal_alignment="center"),
            padding=16 if _mobile else 25,
            bgcolor=ft.Colors.WHITE,
            border_radius=12,
            border=ft.border.all(1, ft.Colors.GREY_200),
            shadow=ft.BoxShadow(blur_radius=8, spread_radius=1, color=ft.Colors.BLACK12, offset=(0, 2)),
            expand=True,
        )
        
        # Combined chart row (rescued vs adopted + breed trends)
        charts_row_1 = ft.ResponsiveRow([
            ft.Container(chart1_container, col={"xs": 12, "xl": 6}),
            ft.Container(breed_trend_container, col={"xs": 12, "xl": 6}),
        ], spacing=15, run_spacing=15)

        def _build_horizontal_chart_content(chart: Any, legend: Any = None) -> Any:
            return create_scrollable_chart_content(
                chart,
                legend,
                chart_width=300 if _mobile else 320,
                legend_width=170 if _mobile else 180,
                legend_height=220 if _mobile else 240,
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
                    ft.Container(
                        _build_horizontal_chart_content(chart, legend),
                        expand=True,
                    ),
                ], spacing=5, horizontal_alignment="center"),
                padding=16 if _mobile else 20,
                height=None,
                bgcolor=ft.Colors.WHITE,
                border_radius=12,
                border=ft.border.all(1, ft.Colors.GREY_200),
                shadow=ft.BoxShadow(blur_radius=8, spread_radius=1, color=ft.Colors.BLACK12, offset=(0, 2)),
                expand=True,
            )
        
        type_data = [{"label": label, "value": value, "color": PIE_CHART_COLORS[idx % len(PIE_CHART_COLORS)]}
                     for idx, (label, value) in enumerate(type_dist.items())] if type_dist else []
        
        rescue_data = [{"label": s.capitalize(), "value": rescue_status_dist.get(s, 0), "color": STATUS_COLORS.get(s, STATUS_COLORS["default"])}
                       for s in ["pending", "on-going", "rescued", "failed"] if s in rescue_status_dist] if rescue_status_dist else []
        
        adoption_data = [{"label": s.capitalize(), "value": adoption_status_dist.get(s, 0), "color": STATUS_COLORS.get(s, STATUS_COLORS["default"])}
                         for s in ["pending", "approved", "denied"] if s in adoption_status_dist] if adoption_status_dist else []

        # Pie charts row
        pie_charts_row = ft.ResponsiveRow([
            ft.Container(create_chart_card_container("Animal Type Distribution", type_pie_chart, type_legend, ft.Icons.CATEGORY, type_data), col={"xs": 12, "md": 6, "lg": 4}),
            ft.Container(create_chart_card_container("Rescue Mission Status", rescue_pie_chart, rescue_legend, ft.Icons.PETS, rescue_data), col={"xs": 12, "md": 6, "lg": 4}),
            ft.Container(create_chart_card_container("Adoption Request Status", adoption_pie_chart, adoption_legend, ft.Icons.FAVORITE, adoption_data), col={"xs": 12, "md": 6, "lg": 4}),
        ], spacing=15, run_spacing=15)

        # Helper for bar chart cards with legend beside (clickable expand icon only)
        def create_bar_chart_card(title: str, chart: Any, legend: Any = None, icon: Any = None, data_for_dialog: List = None) -> Any:
            def show_details(e):
                if data_for_dialog:
                    show_chart_details_dialog(page, f"{title} Details", data_for_dialog, "bar")
            chart_content = _build_horizontal_chart_content(chart, legend)
            
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
                ], spacing=5, horizontal_alignment="center"),
                padding=16 if _mobile else 20,
                height=None,
                bgcolor=ft.Colors.WHITE,
                border_radius=12,
                border=ft.border.all(1, ft.Colors.GREY_200),
                shadow=ft.BoxShadow(blur_radius=8, spread_radius=1, color=ft.Colors.BLACK12, offset=(0, 2)),
                expand=True,
            )
        
        health_data = [{"label": s.capitalize(), "value": status_counts.get(s, 0), "color": STATUS_COLORS.get(s, STATUS_COLORS["default"])}
                       for s in ["healthy", "recovering", "injured"]]
        
        urgency_data = [{"label": level.capitalize(), "value": urgency_dist.get(level, 0), 
                        "color": {"low": STATUS_COLORS["healthy"], "medium": STATUS_COLORS["pending"], 
                                  "high": STATUS_COLORS["recovering"], "critical": STATUS_COLORS["failed"]}.get(level)}
                        for level in ["low", "medium", "high", "critical"] if level in urgency_dist] if urgency_dist else []
        
        # Breed Distribution Pie Chart (replacing Top Species for Adoption)
        breed_pie_refs = {}  # For legend-pie sync
        if breed_distribution and sum(count for _, count in breed_distribution) > 0:
            breed_sections = []
            total = sum(count for _, count in breed_distribution)
            for idx, (breed, count) in enumerate(breed_distribution):
                pct = (count / total * 100) if total > 0 else 0
                breed_sections.append({
                    "value": count,
                    "title": f"{pct:.0f}%",  # Only show percentage (no decimals), no breed name
                    "color": PIE_CHART_COLORS[idx % len(PIE_CHART_COLORS)],
                })
            breed_pie_chart = create_pie_chart(breed_sections, width=200, height=200, legend_refs=breed_pie_refs, title_font_size=9)
            breed_legend = create_chart_legend([
                {"label": breed, "color": PIE_CHART_COLORS[idx % len(PIE_CHART_COLORS)], "value": count}
                for idx, (breed, count) in enumerate(breed_distribution)
            ], horizontal=False, pie_refs=breed_pie_refs)
        else:
            breed_pie_chart = create_empty_chart_message("No breed data", width=200, height=200,
                button_text="Add Animal", button_icon=ft.Icons.ADD,
                on_click=lambda e: page.go("/add_animal"))
            breed_legend = ft.Container()
        
        breed_data = [{"label": breed, "value": count, "color": PIE_CHART_COLORS[idx % len(PIE_CHART_COLORS)]}
                      for idx, (breed, count) in enumerate(breed_distribution)] if breed_distribution else []

        # Bar charts row (replaced "Top Species for Adoption" with "Breed Distribution")
        bar_charts_row = ft.ResponsiveRow([
            ft.Container(create_bar_chart_card("Health Status Breakdown", health_bar_chart, health_legend, ft.Icons.HEALTH_AND_SAFETY, health_data), col={"xs": 12, "md": 6, "lg": 4}),
            ft.Container(create_bar_chart_card("Rescue Urgency Distribution", urgency_bar_chart, urgency_legend, ft.Icons.WARNING_AMBER, urgency_data), col={"xs": 12, "md": 6, "lg": 4}),
            ft.Container(create_chart_card_container("Breed Distribution", breed_pie_chart, breed_legend, ft.Icons.PETS, breed_data), col={"xs": 12, "md": 6, "lg": 4}),
        ], spacing=15, run_spacing=15)

        rescue_insight_data = insights.get("rescue_insight", {"headline": "No data", "detail": "", "action": ""})
        adoption_insight_data = insights.get("adoption_insight", {"headline": "No data", "detail": "", "action": ""})
        health_insight_data = insights.get("health_insight", {"headline": "No data", "detail": "", "action": ""})
        breed_insight_data = insights.get("breed_insight", {"headline": "No data", "detail": "", "action": ""})
        
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
                ft.ResponsiveRow([
                    ft.Container(create_insight_box(
                        "Rescue Operations",
                        rescue_insight_data,
                        ft.Icons.PETS,
                        ft.Colors.BLUE_600,
                        ft.Colors.BLUE_50,
                        ft.Colors.BLUE_100,
                    ), col={"xs": 12, "md": 6, "lg": 3}),
                    ft.Container(create_insight_box(
                        "Adoption Progress", 
                        adoption_insight_data,
                        ft.Icons.FAVORITE,
                        ft.Colors.ORANGE_600,
                        ft.Colors.ORANGE_50,
                        ft.Colors.ORANGE_100,
                    ), col={"xs": 12, "md": 6, "lg": 3}),
                    ft.Container(create_insight_box(
                        "Animal Health",
                        health_insight_data,
                        ft.Icons.HEALTH_AND_SAFETY,
                        ft.Colors.GREEN_600,
                        ft.Colors.GREEN_50,
                        ft.Colors.GREEN_100,
                    ), col={"xs": 12, "md": 6, "lg": 3}),
                    ft.Container(create_insight_box(
                        "Breed Popularity",
                        breed_insight_data,
                        ft.Icons.PETS,
                        ft.Colors.PURPLE_600,
                        ft.Colors.PURPLE_50,
                        ft.Colors.PURPLE_100,
                    ), col={"xs": 12, "md": 6, "lg": 3}),
                ], spacing=15, run_spacing=15),
            ], spacing=0),
            padding=25,
            bgcolor=ft.Colors.WHITE,
            border_radius=12,
            shadow=ft.BoxShadow(blur_radius=10, spread_radius=2, color=ft.Colors.BLACK12, offset=(0, 3)),
        )

        if is_online:
            map_container = create_interactive_map(
                map_service=map_service,
                missions=missions,
                page=page,
                is_admin=True,
                height=500,
                title="Realtime Rescue Mission Map",
                show_legend=True,
                initially_locked=True,
            )
        else:
            offline_widget = map_service.create_offline_map_fallback(missions, is_admin=True)
            if offline_widget:
                map_container = ft.Container(
                    ft.Column([
                        ft.Row([
                            ft.Icon(ft.Icons.MAP, size=20, color=ft.Colors.TEAL_600),
                            ft.Text("Realtime Rescue Mission Map", size=16, weight="w600", color=ft.Colors.BLACK87),
                        ], spacing=10),
                        ft.Divider(height=12, color=ft.Colors.GREY_200),
                        ft.Container(
                            offline_widget,
                            height=500,
                            border_radius=8,
                            border=ft.border.all(1, ft.Colors.AMBER_200),
                        ),
                    ], spacing=8, horizontal_alignment="center"),
                    padding=25,
                    bgcolor=ft.Colors.WHITE,
                    border_radius=12,
                    border=ft.border.all(1, ft.Colors.GREY_200),
                    shadow=ft.BoxShadow(blur_radius=8, spread_radius=1, color=ft.Colors.BLACK12, offset=(0, 2)),
                )
            else:
                map_container = ft.Container(
                    ft.Column([
                        ft.Row([
                            ft.Icon(ft.Icons.MAP, size=20, color=ft.Colors.TEAL_600),
                            ft.Text("Realtime Rescue Mission Map", size=16, weight="w600", color=ft.Colors.BLACK87),
                        ], spacing=10),
                        ft.Divider(height=12, color=ft.Colors.GREY_200),
                        map_service.create_empty_map_placeholder(len(missions)),
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
                charts_row_1,  # Rescued vs Adopted + Breed Trends
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
            padding=responsive_padding(page),
            expand=True,
        )

        # Main layout with sidebar
        main_layout = create_responsive_layout(page, sidebar, main_content, drawer, title="Analytics")

        finish_page_loading(page, _gradient_ref, main_layout)


__all__ = ["ChartsPage"]


