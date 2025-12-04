"""User analytics page with personal statistics and charts."""
from __future__ import annotations

from typing import Optional, Dict, Any, List

import app_config
from services.analytics_service import AnalyticsService
from services.rescue_service import RescueService
from services.adoption_service import AdoptionService
from services.map_service import MapService
from state import get_app_state
from components import (
    create_user_sidebar, create_gradient_background,
    create_page_title, create_clickable_stat_card,
    create_line_chart, create_pie_chart,
    create_chart_legend, create_empty_chart_message,
    create_insight_box, show_chart_details_dialog,
    CHART_COLORS, PIE_CHART_COLORS, STATUS_COLORS
)


class UserAnalyticsPage:
    """User analytics page displaying personal statistics and charts.
    
    Mirrors the admin charts page but with user-specific data.
    """
    
    def __init__(self, db_path: Optional[str] = None) -> None:
        self.db_path = db_path or app_config.DB_PATH
        self.analytics_service = AnalyticsService(self.db_path)
        self.rescue_service = RescueService(self.db_path)
        self.adoption_service = AdoptionService(self.db_path)
        self.map_service = MapService()

    def build(self, page) -> None:
        try:
            import flet as ft
        except Exception as exc:
            raise RuntimeError("Flet must be installed to build the UI") from exc

        page.title = "Your Analytics"

        # Get user info from centralized state management
        app_state = get_app_state()
        user_name = app_state.auth.user_name or "User"
        user_id = app_state.auth.user_id

        if not user_id:
            page.go("/")
            return

        # Sidebar with navigation
        sidebar = create_user_sidebar(page, user_name, current_route=page.route)

        # Fetch user-specific data
        user_activity_stats = self.analytics_service.get_user_activity_stats(user_id)
        user_rescue_status_dist = self.analytics_service.get_user_rescue_status_distribution(user_id)
        user_adoption_status_dist = self.analytics_service.get_user_adoption_status_distribution(user_id)
        user_insights = self.analytics_service.get_user_insights(user_id)
        
        # Get user's chart data (30-day trend)
        day_labels, rescues_reported, adoptions_approved = self.analytics_service.get_user_chart_data(user_id)
        
        # Get user's rescue missions for map
        app_state.rescues.load_user_missions(user_id)
        user_missions = app_state.rescues.user_missions or []

        # Calculate stats
        total_rescues = user_activity_stats.get("rescue_reports_filed", 0)
        rescued_successfully = user_rescue_status_dist.get("rescued", 0)
        total_adoptions = user_activity_stats.get("total_adoptions", 0)
        pending_adoptions = user_activity_stats.get("pending_adoption_requests", 0)
        
        # Calculate success rate
        if total_rescues > 0:
            success_rate = f"{(rescued_successfully / total_rescues * 100):.0f}% success"
        else:
            success_rate = "No data"

        # Stats cards row
        stats_row = ft.Row([
            create_clickable_stat_card(
                title="Rescues Reported",
                value=str(total_rescues),
                subtitle=f"{rescued_successfully} rescued",
                icon=ft.Icons.PETS,
                icon_color=ft.Colors.ORANGE_600,
                on_click=lambda e: page.go("/check_status"),
            ),
            create_clickable_stat_card(
                title="Successfully Rescued",
                value=str(rescued_successfully),
                subtitle=success_rate,
                icon=ft.Icons.CHECK_CIRCLE,
                icon_color=ft.Colors.GREEN_600,
                on_click=lambda e: page.go("/check_status"),
            ),
            create_clickable_stat_card(
                title="Animals Adopted",
                value=str(total_adoptions),
                subtitle="Forever homes given",
                icon=ft.Icons.FAVORITE,
                icon_color=ft.Colors.TEAL_600,
                on_click=lambda e: page.go("/check_status"),
            ),
            create_clickable_stat_card(
                title="Pending Requests",
                value=str(pending_adoptions),
                subtitle="Awaiting review",
                icon=ft.Icons.PENDING_ACTIONS,
                icon_color=ft.Colors.BLUE_600,
                on_click=lambda e: page.go("/check_status"),
            ),
        ], spacing=15, alignment=ft.MainAxisAlignment.CENTER)

        # ========================================
        # Chart 1: Your Activity Line Chart (30 Days)
        # ========================================
        has_line_data = any(c > 0 for c in rescues_reported) or any(c > 0 for c in adoptions_approved)
        
        if has_line_data:
            formatted_labels = [f"Date: {label}" for label in day_labels]
            line_chart = create_line_chart(
                data_series=[
                    {"label": "Rescues Reported", "values": list(zip(range(len(day_labels)), rescues_reported)), "color": CHART_COLORS["secondary"]},
                    {"label": "Adoptions Approved", "values": list(zip(range(len(day_labels)), adoptions_approved)), "color": CHART_COLORS["primary"]},
                ],
                height=180,
                x_labels=formatted_labels,
            )
            line_legend = create_chart_legend([
                {"label": "Rescues Reported", "color": CHART_COLORS["secondary"], "value": sum(rescues_reported)},
                {"label": "Adoptions Approved", "color": CHART_COLORS["primary"], "value": sum(adoptions_approved)},
            ], horizontal=False)
        else:
            line_chart = create_empty_chart_message("No activity in the last 30 days", width=600, height=180)
            line_legend = ft.Container()

        activity_chart_container = ft.Container(
            ft.Column([
                ft.Text("Your Activity (Last 30 Days)", size=14, weight=ft.FontWeight.W_600, color=ft.Colors.BLACK87),
                ft.Divider(height=8, color=ft.Colors.GREY_300),
                ft.Row([
                    line_chart,
                    ft.Container(line_legend, padding=ft.padding.only(left=15, right=10)),
                ], alignment=ft.MainAxisAlignment.CENTER, vertical_alignment=ft.CrossAxisAlignment.CENTER, expand=True),
            ], spacing=5, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            width=700,
            height=268,
            padding=ft.padding.only(left=15, top=15, bottom=15, right=25),
            bgcolor=ft.Colors.WHITE,
            border_radius=12,
            shadow=ft.BoxShadow(blur_radius=8, spread_radius=1, color=ft.Colors.BLACK12, offset=ft.Offset(0, 2)),
        )

        # ========================================
        # Chart 2: Your Rescue Status Pie Chart
        # ========================================
        rescue_pie_refs = {}
        if user_rescue_status_dist and sum(user_rescue_status_dist.values()) > 0:
            rescue_sections = []
            total = sum(user_rescue_status_dist.values())
            status_order = ["pending", "on-going", "rescued", "failed"]
            for status in status_order:
                if status in user_rescue_status_dist and user_rescue_status_dist[status] > 0:
                    value = user_rescue_status_dist[status]
                    pct = (value / total * 100) if total > 0 else 0
                    rescue_sections.append({
                        "value": value,
                        "title": f"{pct:.0f}%",
                        "color": STATUS_COLORS.get(status, STATUS_COLORS["default"]),
                    })
            rescue_pie_chart = create_pie_chart(rescue_sections, height=150, section_radius=60, center_space_radius=20, legend_refs=rescue_pie_refs)
            rescue_legend = create_chart_legend([
                {"label": s.capitalize(), "color": STATUS_COLORS.get(s, STATUS_COLORS["default"]), "value": user_rescue_status_dist.get(s, 0)}
                for s in status_order if user_rescue_status_dist.get(s, 0) > 0
            ], horizontal=False, pie_refs=rescue_pie_refs)
            rescue_data_for_dialog = [
                {"label": s.capitalize(), "value": user_rescue_status_dist.get(s, 0), "color": STATUS_COLORS.get(s, STATUS_COLORS["default"])}
                for s in status_order if user_rescue_status_dist.get(s, 0) > 0
            ]
        else:
            rescue_pie_chart = create_empty_chart_message("No rescue data", width=150, height=150)
            rescue_legend = ft.Container()
            rescue_data_for_dialog = []

        def show_rescue_details(e):
            if rescue_data_for_dialog:
                show_chart_details_dialog(page, "Your Rescue Status Details", rescue_data_for_dialog, "pie")

        rescue_chart_container = ft.Container(
            ft.Column([
                ft.Row([
                    ft.Text("Your Rescue Status", size=14, weight=ft.FontWeight.W_600, color=ft.Colors.BLACK87),
                    ft.Container(
                        ft.IconButton(
                            icon=ft.Icons.OPEN_IN_NEW,
                            icon_size=16,
                            icon_color=ft.Colors.TEAL_600,
                            tooltip="View detailed breakdown",
                            on_click=show_rescue_details,
                        ),
                        bgcolor=ft.Colors.TEAL_50,
                        border_radius=8,
                        border=ft.border.all(1, ft.Colors.TEAL_200),
                    ) if rescue_data_for_dialog else ft.Container(),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Divider(height=8, color=ft.Colors.GREY_300),
                ft.Row([
                    rescue_pie_chart,
                    rescue_legend,
                ], alignment=ft.MainAxisAlignment.CENTER, spacing=10, expand=True),
            ], spacing=5, horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True),
            width=340,
            height=268,
            padding=15,
            bgcolor=ft.Colors.WHITE,
            border_radius=12,
            shadow=ft.BoxShadow(blur_radius=8, spread_radius=1, color=ft.Colors.BLACK12, offset=ft.Offset(0, 2)),
        )

        # ========================================
        # Chart 3: Your Adoption Status Pie Chart
        # ========================================
        adoption_pie_refs = {}
        if user_adoption_status_dist and sum(user_adoption_status_dist.values()) > 0:
            adoption_sections = []
            total = sum(user_adoption_status_dist.values())
            status_order = ["pending", "approved", "denied"]
            for status in status_order:
                if status in user_adoption_status_dist and user_adoption_status_dist[status] > 0:
                    value = user_adoption_status_dist[status]
                    pct = (value / total * 100) if total > 0 else 0
                    adoption_sections.append({
                        "value": value,
                        "title": f"{pct:.0f}%",
                        "color": STATUS_COLORS.get(status, STATUS_COLORS["default"]),
                    })
            adoption_pie_chart = create_pie_chart(adoption_sections, height=150, section_radius=60, center_space_radius=20, legend_refs=adoption_pie_refs)
            adoption_legend = create_chart_legend([
                {"label": s.capitalize(), "color": STATUS_COLORS.get(s, STATUS_COLORS["default"]), "value": user_adoption_status_dist.get(s, 0)}
                for s in status_order if user_adoption_status_dist.get(s, 0) > 0
            ], horizontal=False, pie_refs=adoption_pie_refs)
            adoption_data_for_dialog = [
                {"label": s.capitalize(), "value": user_adoption_status_dist.get(s, 0), "color": STATUS_COLORS.get(s, STATUS_COLORS["default"])}
                for s in status_order if user_adoption_status_dist.get(s, 0) > 0
            ]
        else:
            adoption_pie_chart = create_empty_chart_message("No adoption data", width=150, height=150)
            adoption_legend = ft.Container()
            adoption_data_for_dialog = []

        def show_adoption_details(e):
            if adoption_data_for_dialog:
                show_chart_details_dialog(page, "Your Adoption Status Details", adoption_data_for_dialog, "pie")

        adoption_chart_container = ft.Container(
            ft.Column([
                ft.Row([
                    ft.Text("Your Adoption Status", size=14, weight=ft.FontWeight.W_600, color=ft.Colors.BLACK87),
                    ft.Container(
                        ft.IconButton(
                            icon=ft.Icons.OPEN_IN_NEW,
                            icon_size=16,
                            icon_color=ft.Colors.TEAL_600,
                            tooltip="View detailed breakdown",
                            on_click=show_adoption_details,
                        ),
                        bgcolor=ft.Colors.TEAL_50,
                        border_radius=8,
                        border=ft.border.all(1, ft.Colors.TEAL_200),
                    ) if adoption_data_for_dialog else ft.Container(),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Divider(height=8, color=ft.Colors.GREY_300),
                ft.Row([
                    adoption_pie_chart,
                    adoption_legend,
                ], alignment=ft.MainAxisAlignment.CENTER, spacing=10, expand=True),
            ], spacing=5, horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True),
            width=340,
            height=268,
            padding=15,
            bgcolor=ft.Colors.WHITE,
            border_radius=12,
            shadow=ft.BoxShadow(blur_radius=8, spread_radius=1, color=ft.Colors.BLACK12, offset=ft.Offset(0, 2)),
        )

        # Pie charts row
        pie_charts_row = ft.Row([
            rescue_chart_container,
            adoption_chart_container,
        ], spacing=15, alignment=ft.MainAxisAlignment.CENTER)

        # ========================================
        # Map: Your Rescue Mission Locations
        # ========================================
        # Filter out cancelled/removed missions
        from app_config import RescueStatus
        missions_for_map = [
            m for m in user_missions
            if not RescueStatus.is_cancelled(m.get("status") or "")
            and not RescueStatus.is_removed(m.get("status") or "")
        ]
        
        map_widget = self.map_service.create_map_with_markers(missions_for_map, is_admin=False)

        if map_widget:
            map_container = ft.Container(
                ft.Column([
                    ft.Text("Your Rescue Mission Locations", size=14, weight=ft.FontWeight.W_600, color=ft.Colors.BLACK87),
                    ft.Divider(height=8, color=ft.Colors.GREY_300),
                    ft.Container(
                        map_widget,
                        height=500,
                        border_radius=8,
                        clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
                    ),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=5, expand=True),
                margin=ft.margin.symmetric(horizontal=20),
                padding=15,
                bgcolor=ft.Colors.WHITE,
                border_radius=12,
                shadow=ft.BoxShadow(blur_radius=8, spread_radius=1, color=ft.Colors.BLACK12, offset=ft.Offset(0, 2)),
            )
        else:
            map_container = ft.Container(
                ft.Column([
                    ft.Text("Your Rescue Mission Locations", size=14, weight=ft.FontWeight.W_600, color=ft.Colors.BLACK87),
                    ft.Divider(height=8, color=ft.Colors.GREY_300),
                    self.map_service.create_empty_map_placeholder(len(missions_for_map)),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=5, expand=True),
                padding=15,
                margin=ft.margin.symmetric(horizontal=20),
                bgcolor=ft.Colors.WHITE,
                border_radius=12,
                shadow=ft.BoxShadow(blur_radius=8, spread_radius=1, color=ft.Colors.BLACK12, offset=ft.Offset(0, 2)),
            )

        # ========================================
        # Insights Section
        # ========================================
        rescue_insight_data = user_insights.get("rescue_insight", {"headline": "No data", "detail": "", "action": ""})
        adoption_insight_data = user_insights.get("adoption_insight", {"headline": "No data", "detail": "", "action": ""})
        activity_insight_data = user_insights.get("activity_insight", {"headline": "No data", "detail": "", "action": ""})
        
        insights_container = ft.Container(
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
                        ft.Text("Your Insights", size=20, weight="bold", color=ft.Colors.BLACK87),
                        ft.Text("Personalized summary of your contributions", size=12, color=ft.Colors.BLACK54),
                    ], spacing=2),
                ], spacing=12),
                ft.Divider(height=24, color=ft.Colors.GREY_300),
                ft.Row([
                    create_insight_box(
                        "Rescue Reports",
                        rescue_insight_data,
                        ft.Icons.PETS,
                        ft.Colors.ORANGE_600,
                        ft.Colors.ORANGE_50,
                        ft.Colors.ORANGE_100,
                    ),
                    create_insight_box(
                        "Adoptions",
                        adoption_insight_data,
                        ft.Icons.FAVORITE,
                        ft.Colors.TEAL_600,
                        ft.Colors.TEAL_50,
                        ft.Colors.TEAL_100,
                    ),
                    create_insight_box(
                        "Overall Activity",
                        activity_insight_data,
                        ft.Icons.STAR,
                        ft.Colors.AMBER_600,
                        ft.Colors.AMBER_50,
                        ft.Colors.AMBER_100,
                    ),
                ], spacing=15, expand=True),
            ], spacing=0),
            padding=25,
            bgcolor=ft.Colors.WHITE,
            border_radius=12,
            shadow=ft.BoxShadow(blur_radius=10, spread_radius=2, color=ft.Colors.BLACK12, offset=(0, 3)),
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
            on_click=lambda e: page.go("/user"),
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
                ft.Text("Your Analytics", size=28, weight="bold", color=ft.Colors.with_opacity(0.6, ft.Colors.BLACK)),
                ft.Container(height=15),
                stats_row,
                ft.Container(height=20),
                activity_chart_container,
                ft.Container(height=20),
                pie_charts_row,
                ft.Container(height=20),
                map_container,
                ft.Container(height=20),
                insights_container,
                ft.Container(height=20),
                ft.Row([refresh_btn, back_btn], alignment="center", spacing=15),
                ft.Container(height=30),
            ], spacing=0, scroll=ft.ScrollMode.AUTO, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
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


__all__ = ["UserAnalyticsPage"]
