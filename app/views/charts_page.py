"""Analytics charts page with rescue and adoption statistics."""
from __future__ import annotations

from typing import Optional, Dict, Any, Tuple, List
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
from services.analytics_service import AnalyticsService
from components import create_admin_sidebar, create_gradient_background


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
        sidebar = create_admin_sidebar(page)

        # try to import matplotlib for drawing charts
        # (already imported at top with Agg backend)

        # fetch data using analytics service
        (months, rescued_counts, adopted_counts), type_dist, status_counts = self.analytics_service.get_chart_data()

        # Calculate statistics
        total_rescued = sum(rescued_counts)
        total_adopted = sum(adopted_counts)
        total_pending = len(self.adoption_service.get_all_requests() or [])  # All requests considered pending

        # helper to render matplotlib figure to base64 png
        def fig_to_base64(fig) -> str:
            buf = BytesIO()
            fig.savefig(buf, format="png", bbox_inches="tight")
            plt.close(fig)
            buf.seek(0)
            b = base64.b64encode(buf.read()).decode("ascii")
            return b

        # Line chart: rescued vs adopted trend
        fig1, ax1 = plt.subplots(figsize=(8, 3.5))
        ax1.plot(months, rescued_counts, label="Rescued", marker="o", color="#2196F3")
        ax1.plot(months, adopted_counts, label="Adopted", marker="o", color="#FF9800")
        ax1.set_title("Rescued vs Adopted (last 12 months)", fontsize=12)
        ax1.set_xticklabels(months, rotation=45, fontsize=8)
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        b1 = fig_to_base64(fig1)

        # Pie chart: type distribution
        fig2, ax2 = plt.subplots(figsize=(3, 2.5))
        labels = list(type_dist.keys()) or ["None"]
        sizes = list(type_dist.values()) or [1]
        colors = ['#2196F3', '#FFA726', '#66BB6A', '#EF5350']
        ax2.pie(sizes, labels=labels, autopct="%1.1f%%", startangle=90, colors=colors[:len(labels)])
        ax2.set_title("Animal Type Distribution", fontsize=10)
        b2 = fig_to_base64(fig2)

        # Bar chart: health status
        fig3, ax3 = plt.subplots(figsize=(8, 3.5))
        statuses = list(status_counts.keys()) or ["unknown"]
        counts = [status_counts.get(s, 0) for s in statuses]
        colors_map = {
            "healthy": "#4CAF50",  # green
            "recovering": "#F44336",  # red
            "injured": "#FFEB3B",  # yellow
        }
        bar_colors = [colors_map.get(s.lower(), "#90A4AE") for s in statuses]
        ax3.bar(statuses, counts, color=bar_colors)
        ax3.set_title("Health Status Breakdown", fontsize=12)
        ax3.set_ylabel("Count")
        b3 = fig_to_base64(fig3)

        # Placeholder map image (static map with pins)
        fig4, ax4 = plt.subplots(figsize=(3, 2.5))
        ax4.text(0.5, 0.5, "Realtime Rescue Mission\n\nMap View", 
                ha='center', va='center', fontsize=10, color='#666')
        ax4.set_xlim(0, 1)
        ax4.set_ylim(0, 1)
        ax4.axis('off')
        # Add some fake map pins
        import numpy as np
        np.random.seed(42)
        for _ in range(5):
            x, y = np.random.rand(2)
            ax4.plot(x, y, 'o', markersize=12, color=np.random.choice(['red', 'green', 'orange']))
        b4 = fig_to_base64(fig4)

        # Build stat cards
        def stat_card(title: str, value: str, change: str, color: str):
            return ft.Container(
                ft.Column([
                    ft.Text(title, size=12, color=ft.Colors.BLACK54),
                    ft.Text(value, size=32, weight="bold", color=color),
                    ft.Text(change, size=11, color=ft.Colors.GREEN_600 if "+" in change else ft.Colors.RED_600),
                ], spacing=5),
                padding=20,
                bgcolor=ft.Colors.WHITE,
                border_radius=12,
                shadow=ft.BoxShadow(blur_radius=8, spread_radius=1, color=ft.Colors.BLACK12, offset=(0, 2)),
                expand=True,
            )

        stats_row = ft.Row([
            stat_card("Total Animals Rescued", str(total_rescued), "▲ 12% this month", ft.Colors.GREEN_600),
            stat_card("Total Adoptions", f"{total_adopted:,}", "▲ 18% this month", ft.Colors.ORANGE_600),
            stat_card("Pending Applications", str(total_pending), "▲ 8% this month", ft.Colors.ORANGE_600),
        ], spacing=15, expand=True)

        # Chart containers
        chart1_container = ft.Container(
            ft.Column([
                ft.Text("Rescued vs. Adopted", size=16, weight="w600", color=ft.Colors.BLACK87),
                ft.Divider(height=10, color=ft.Colors.GREY_300),
                ft.Row([
                    ft.Image(src_base64=b1, fit=ft.ImageFit.CONTAIN),
                ], alignment="center"),
            ], spacing=5, horizontal_alignment="center"),
            padding=20,
            bgcolor=ft.Colors.WHITE,
            border_radius=12,
            shadow=ft.BoxShadow(blur_radius=8, spread_radius=1, color=ft.Colors.BLACK12, offset=(0, 2)),
        )

        # Second row with pie chart and map stacked vertically
        pie_chart_container = ft.Container(
            ft.Column([
                ft.Text("Animal Type Distribution", size=16, weight="w600", color=ft.Colors.BLACK87),
                ft.Divider(height=10, color=ft.Colors.GREY_300),
                ft.Row([
                    ft.Image(src_base64=b2, fit=ft.ImageFit.CONTAIN),
                ], alignment="center"),
            ], spacing=5, horizontal_alignment="center"),
            padding=20,
            bgcolor=ft.Colors.WHITE,
            border_radius=12,
            shadow=ft.BoxShadow(blur_radius=8, spread_radius=1, color=ft.Colors.BLACK12, offset=(0, 2)),
        )

        map_container = ft.Container(
            ft.Column([
                ft.Text("Realtime Rescue Mission", size=16, weight="w600", color=ft.Colors.BLACK87),
                ft.Divider(height=10, color=ft.Colors.GREY_300),
                ft.Row([
                    ft.Image(src_base64=b4, fit=ft.ImageFit.CONTAIN),
                ], alignment="center"),
            ], spacing=5, horizontal_alignment="center"),
            padding=20,
            bgcolor=ft.Colors.WHITE,
            border_radius=12,
            shadow=ft.BoxShadow(blur_radius=8, spread_radius=1, color=ft.Colors.BLACK12, offset=(0, 2)),
        )

        chart2_container = ft.Container(
            ft.Column([
                ft.Text("Health Status", size=16, weight="w600", color=ft.Colors.BLACK87),
                ft.Divider(height=10, color=ft.Colors.GREY_300),
                ft.Row([
                    ft.Image(src_base64=b3, fit=ft.ImageFit.CONTAIN),
                ], alignment="center"),
            ], spacing=5, horizontal_alignment="center"),
            padding=20,
            bgcolor=ft.Colors.WHITE,
            border_radius=12,
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
                pie_chart_container,
                ft.Container(height=20),
                map_container,
                ft.Container(height=20),
                chart2_container,
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


