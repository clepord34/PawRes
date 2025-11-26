"""Admin dashboard with navigation and analytics overview."""
from __future__ import annotations

from typing import Optional, Dict, Any, Tuple, List
from datetime import datetime, timedelta
from io import BytesIO
import base64

# Set matplotlib backend to Agg before importing pyplot
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from services.animal_service import AnimalService
from services.rescue_service import RescueService
from services.adoption_service import AdoptionService
from services.analytics_service import AnalyticsService
from services.map_service import MapService
from state import get_app_state
import app_config
from components import create_admin_sidebar, create_dashboard_card, create_gradient_background


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
        
        # Calculate percentage changes (mock data for now - you can enhance with historical data)
        animals_change = "+15% this month"
        adoptions_change = "+15% this month"
        pending_change = "+15% this month"

        # Fetch chart data using analytics service
        (month_labels, rescued_counts, adopted_counts), type_dist, status_counts = self.analytics_service.get_chart_data()

        # Fetch missions for map display
        missions = self.rescue_service.get_all_missions() or []

        # Sidebar with navigation
        sidebar = create_admin_sidebar(page)

        # Try to create charts with matplotlib
        chart_images = {}
        try:
            def fig_to_base64(fig) -> str:
                buf = BytesIO()
                fig.savefig(buf, format="png", bbox_inches="tight", dpi=100)
                plt.close(fig)
                buf.seek(0)
                b = base64.b64encode(buf.read()).decode("ascii")
                return b

            # Line chart: rescued vs adopted trend
            fig1, ax1 = plt.subplots(figsize=(5, 2.5))
            ax1.plot(month_labels, rescued_counts, label="Rescued", marker="o", color="#26A69A")
            ax1.plot(month_labels, adopted_counts, label="Adopted", marker="o", color="#FFA726")
            ax1.set_title("Rescued vs Adopted (last 12 months)", fontsize=10)
            ax1.set_xticklabels(month_labels, rotation=45, fontsize=7)
            ax1.tick_params(axis='y', labelsize=8)
            ax1.legend(fontsize=8)
            ax1.grid(True, alpha=0.3)
            chart_images['rescued_vs_adopted'] = fig_to_base64(fig1)

            # Pie chart: type distribution
            fig2, ax2 = plt.subplots(figsize=(3, 2.5))
            labels = list(type_dist.keys()) or ["None"]
            sizes = list(type_dist.values()) or [1]
            colors = ['#2196F3', '#FFA726', '#66BB6A', '#EF5350']
            ax2.pie(sizes, labels=labels, autopct="%1.1f%%", startangle=90, colors=colors[:len(labels)])
            ax2.set_title("Animal Type Distribution", fontsize=10)
            chart_images['type_dist'] = fig_to_base64(fig2)

            # Bar chart: health status
            fig3, ax3 = plt.subplots(figsize=(3.5, 2.5))
            statuses = list(status_counts.keys()) or ["unknown"]
            counts = [status_counts.get(s, 0) for s in statuses]
            colors_map = {
                "healthy": "#4CAF50",
                "recovering": "#FFEB3B",
                "injured": "#F44336",
            }
            bar_colors = [colors_map.get(s.lower(), "#90A4AE") for s in statuses]
            ax3.bar(statuses, counts, color=bar_colors)
            ax3.set_title("Health Status Breakdown", fontsize=10)
            ax3.tick_params(axis='both', labelsize=8)
            ax3.grid(True, alpha=0.3, axis='y')
            chart_images['health_status'] = fig_to_base64(fig3)

        except Exception as e:
            print(f"[WARNING] Could not generate charts: {e}")
            chart_images = None

        # Stats cards
        stat_cards = ft.Row([
            create_dashboard_card("Total Animals Rescued", str(total_animals), animals_change, width=200),
            create_dashboard_card("Total Adoptions", str(total_adoptions), adoptions_change, width=200),
            create_dashboard_card("Pending Applications", str(pending_applications), pending_change, width=200),
        ], spacing=20, alignment=ft.MainAxisAlignment.CENTER)

        # Create chart containers
        if chart_images:
            rescued_chart = ft.Container(
                ft.Column([
                    ft.Text("Rescued vs. Adopted", size=15, weight="w600", color=ft.Colors.BLACK87),
                    ft.Image(src_base64=chart_images['rescued_vs_adopted'], width=380, height=200, fit=ft.ImageFit.CONTAIN),
                ], horizontal_alignment="center", spacing=8),
                width=400,
                padding=12,
                bgcolor=ft.Colors.WHITE,
                border_radius=12,
                shadow=ft.BoxShadow(blur_radius=8, spread_radius=1, color=ft.Colors.BLACK12, offset=(0, 2)),
            )
            
            type_chart = ft.Container(
                ft.Column([
                    ft.Text("Type Distribution", size=15, weight="w600", color=ft.Colors.BLACK87),
                    ft.Image(src_base64=chart_images['type_dist'], width=250, height=200, fit=ft.ImageFit.CONTAIN),
                ], horizontal_alignment="center", spacing=8),
                width=280,
                padding=12,
                bgcolor=ft.Colors.WHITE,
                border_radius=12,
                shadow=ft.BoxShadow(blur_radius=8, spread_radius=1, color=ft.Colors.BLACK12, offset=(0, 2)),
            )
            
            health_chart = ft.Container(
                ft.Column([
                    ft.Text("Health Status", size=15, weight="w600", color=ft.Colors.BLACK87),
                    ft.Image(src_base64=chart_images['health_status'], width=280, height=200, fit=ft.ImageFit.CONTAIN),
                ], horizontal_alignment="center", spacing=8),
                width=310,
                padding=12,
                bgcolor=ft.Colors.WHITE,
                border_radius=12,
                shadow=ft.BoxShadow(blur_radius=8, spread_radius=1, color=ft.Colors.BLACK12, offset=(0, 2)),
            )
        else:
            # Fallback if matplotlib is not available
            rescued_chart = ft.Container(
                ft.Column([
                    ft.Text("Rescued vs. Adopted", size=15, weight="w600", color=ft.Colors.BLACK87),
                    ft.Container(
                        ft.Text("Install matplotlib to view charts\npip install matplotlib", 
                               size=12, 
                               color=ft.Colors.BLACK54,
                               text_align="center"),
                        height=160,
                        alignment=ft.alignment.center,
                    ),
                ], horizontal_alignment="center", spacing=8),
                width=400,
                padding=12,
                bgcolor=ft.Colors.WHITE,
                border_radius=12,
                shadow=ft.BoxShadow(blur_radius=8, spread_radius=1, color=ft.Colors.BLACK12, offset=(0, 2)),
            )
            type_chart = ft.Container(
                ft.Column([
                    ft.Text("Type Distribution", size=15, weight="w600", color=ft.Colors.BLACK87),
                    ft.Container(
                        ft.Text(f"Types: {', '.join(type_dist.keys()) if type_dist else 'No data'}", 
                               size=12, 
                               color=ft.Colors.BLACK54,
                               text_align="center"),
                        height=160,
                        alignment=ft.alignment.center,
                    ),
                ], horizontal_alignment="center", spacing=8),
                width=280,
                padding=12,
                bgcolor=ft.Colors.WHITE,
                border_radius=12,
                shadow=ft.BoxShadow(blur_radius=8, spread_radius=1, color=ft.Colors.BLACK12, offset=(0, 2)),
            )
            health_chart = ft.Container(
                ft.Column([
                    ft.Text("Health Status", size=15, weight="w600", color=ft.Colors.BLACK87),
                    ft.Container(
                        ft.Text(f"Status: {', '.join(status_counts.keys()) if status_counts else 'No data'}", 
                               size=12, 
                               color=ft.Colors.BLACK54,
                               text_align="center"),
                        height=160,
                        alignment=ft.alignment.center,
                ),
            ], horizontal_alignment="center", spacing=8),
                width=310,
                padding=12,
                bgcolor=ft.Colors.WHITE,
                border_radius=12,
                shadow=ft.BoxShadow(blur_radius=8, spread_radius=1, color=ft.Colors.BLACK12, offset=(0, 2)),
            )

        # Realtime map with rescue mission markers
        map_widget = self.map_service.create_map_with_markers(missions)
        
        if map_widget:
            map_container = ft.Container(
                ft.Column([
                    ft.Text("Realtime Rescue Mission Map", size=15, weight="w600", color=ft.Colors.BLACK87),
                    ft.Container(
                        map_widget,
                        height=200,
                        border_radius=8,
                        clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
                    ),
                ], horizontal_alignment="center", spacing=8),
                width=370,
                padding=12,
                bgcolor=ft.Colors.WHITE,
                border_radius=12,
                shadow=ft.BoxShadow(blur_radius=8, spread_radius=1, color=ft.Colors.BLACK12, offset=(0, 2)),
            )
        else:
            # Fallback to placeholder if map creation fails
            map_container = ft.Container(
                ft.Column([
                    ft.Text("Realtime Rescue Mission", size=15, weight="w600", color=ft.Colors.BLACK87),
                    self.map_service.create_empty_map_placeholder(len(missions)),
                ], horizontal_alignment="center", spacing=8),
                width=370,
                padding=12,
                bgcolor=ft.Colors.WHITE,
                border_radius=12,
                shadow=ft.BoxShadow(blur_radius=8, spread_radius=1, color=ft.Colors.BLACK12, offset=(0, 2)),
            )        # Main content area
        main_content = ft.Container(
            ft.Column([
                # Page title - centered
                ft.Container(
                    ft.Text("Admin Dashboard Overview", size=22, weight="bold", color=ft.Colors.BLACK87),
                    padding=ft.padding.only(bottom=15),
                    alignment=ft.alignment.center,
                ),
                # Stats row - evenly spaced and centered
                ft.Container(
                    stat_cards,
                    alignment=ft.alignment.center,
                ),
                ft.Container(height=15),
                # Charts row - centered and tighter spacing
                ft.Container(
                    ft.Row([
                        rescued_chart,
                        type_chart,
                    ], spacing=12, alignment=ft.MainAxisAlignment.CENTER),
                    alignment=ft.alignment.center,
                ),
                ft.Container(height=12),
                # Bottom row - centered and tighter spacing
                ft.Container(
                    ft.Row([
                        health_chart,
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

