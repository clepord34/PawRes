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
from components import (
    create_admin_sidebar, create_gradient_background,
    create_page_title, create_chart_container, create_stat_card, fig_to_base64
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
        sidebar = create_admin_sidebar(page)

        # try to import matplotlib for drawing charts
        # (already imported at top with Agg backend)

        # fetch data using analytics service
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

        # Line chart: rescued vs adopted trend (last 1 month / 30 days)
        fig1, ax1 = plt.subplots(figsize=(8, 3.5))
        ax1.plot(months, rescued_counts, label="Rescued", marker="o", color="#2196F3")
        ax1.plot(months, adopted_counts, label="Adopted", marker="o", color="#FF9800")
        ax1.set_title("Rescued vs Adopted (last 1 month)", fontsize=12)
        # Show only every 5th label to avoid crowding
        ax1.set_xticks(range(0, len(months), 5))
        ax1.set_xticklabels([months[i] for i in range(0, len(months), 5)], rotation=45, fontsize=8)
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        b1 = fig_to_base64(fig1)

        # Pie chart: type distribution
        fig2, ax2 = plt.subplots(figsize=(3, 2.5))
        if type_dist:
            labels = list(type_dist.keys())
            sizes = list(type_dist.values())
            colors = ['#2196F3', '#FFA726', '#66BB6A', '#EF5350']
            ax2.pie(sizes, labels=labels, autopct="%1.1f%%", startangle=90, colors=colors[:len(labels)])
        else:
            # No data - show empty pie with "No Data" message
            ax2.pie([1], labels=[""], colors=["#E0E0E0"])
            ax2.text(0, 0, "No Data", ha='center', va='center', fontsize=12, color='#757575')
        ax2.set_title("Animal Type Distribution", fontsize=10)
        b2 = fig_to_base64(fig2)

        # Bar chart: health status - always show all three categories
        fig3, ax3 = plt.subplots(figsize=(8, 3.5))
        statuses = ["healthy", "recovering", "injured"]
        counts = [status_counts.get(s, 0) for s in statuses]
        colors_map = {
            "healthy": "#4CAF50",  # green
            "recovering": "#FFEB3B",  # yellow
            "injured": "#F44336",  # red
        }
        bar_colors = [colors_map[s] for s in statuses]
        bars = ax3.bar(statuses, counts, color=bar_colors)
        # Add value labels on top of bars
        for bar, count in zip(bars, counts):
            ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
                    str(count), ha='center', va='bottom', fontsize=10)
        ax3.set_title("Health Status Breakdown", fontsize=12)
        ax3.set_ylabel("Count")
        # Ensure y-axis starts at 0 and has some headroom for labels
        ax3.set_ylim(0, max(counts) + 1 if max(counts) > 0 else 1)
        b3 = fig_to_base64(fig3)

        # Get real rescue mission data for map
        from services.map_service import MapService
        map_service = MapService()
        missions = self.rescue_service.get_all_missions() or []
        map_widget = map_service.create_map_with_markers(missions)

        # Build stat cards
        def stat_card(title: str, value: str, change: str, color: str):
            # Determine change text color based on content
            if "+" in change:
                change_color = ft.Colors.GREEN_600
            elif "-" in change or "%" in change:
                change_color = ft.Colors.RED_600
            else:
                change_color = ft.Colors.GREY_600  # For "No change" or neutral text
            
            return ft.Container(
                ft.Column([
                    ft.Text(title, size=12, color=ft.Colors.BLACK54),
                    ft.Text(value, size=32, weight="bold", color=color),
                    ft.Text(change, size=11, color=change_color),
                ], spacing=5),
                padding=20,
                bgcolor=ft.Colors.WHITE,
                border_radius=12,
                shadow=ft.BoxShadow(blur_radius=8, spread_radius=1, color=ft.Colors.BLACK12, offset=(0, 2)),
                expand=True,
            )

        stats_row = ft.Row([
            stat_card("Total Animals Rescued", str(total_rescued), rescues_change, ft.Colors.GREEN_600),
            stat_card("Total Adoptions", f"{total_adopted:,}", adoptions_change, ft.Colors.ORANGE_600),
            stat_card("Pending Applications", str(total_pending), pending_change, ft.Colors.ORANGE_600),
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

        # Create map container with real map or fallback placeholder
        if map_widget:
            map_content = ft.Container(
                map_widget,
                height=500,
                border_radius=8,
                clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            )
        else:
            map_content = map_service.create_empty_map_placeholder(len(missions))
        
        map_container = ft.Container(
            ft.Column([
                ft.Text("Realtime Rescue Mission", size=16, weight="w600", color=ft.Colors.BLACK87),
                ft.Divider(height=10, color=ft.Colors.GREY_300),
                map_content,
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


