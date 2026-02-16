"""User dashboard with activity overview and featured animals."""
from __future__ import annotations
from typing import Optional
import threading
import random

import app_config
from services.animal_service import AnimalService
from services.rescue_service import RescueService
from services.adoption_service import AdoptionService
from services.analytics_service import AnalyticsService
from services.map_service import MapService
from services.photo_service import load_photo
from state import get_app_state
from components import (
    create_user_sidebar, create_gradient_background,
    create_pie_chart, create_chart_legend, create_bar_chart,
    create_empty_chart_message,
    create_scrollable_chart_content,
    show_chart_details_dialog,
    create_impact_insight_widgets,
    STATUS_COLORS, PIE_CHART_COLORS,
    create_interactive_map,
    create_ai_download_dialog,
    create_animal_card,
    create_ai_download_button,
    show_page_loading, finish_page_loading,
    is_mobile, create_responsive_layout,
    responsive_padding, create_user_drawer,
)


class UserDashboard:
    def __init__(self, db_path: Optional[str] = None) -> None:
        self.db_path = db_path or app_config.DB_PATH
        self.animal_service = AnimalService(self.db_path)
        self.rescue_service = RescueService(self.db_path)
        self.adoption_service = AdoptionService(self.db_path)
        self.analytics_service = AnalyticsService(self.db_path)
        self.map_service = MapService()

    def _sync_pending_addresses_background(self) -> None:
        """Sync pending addresses in a background thread.
        
        This updates location text for missions that were submitted offline
        and only have GPS coordinates stored.
        """
        def sync_task():
            try:
                updated = self.rescue_service.sync_pending_addresses(self.map_service)
                if updated > 0:
                    print(f"[INFO] Background sync: Updated {updated} mission address(es)")
            except Exception as e:
                print(f"[WARN] Background address sync failed: {e}")
        
        sync_thread = threading.Thread(target=sync_task, daemon=True)
        sync_thread.start()

    def build(self, page) -> None:
        """Build the user dashboard on the provided flet.Page instance."""
        try:
            import flet as ft
        except Exception as exc:
            raise RuntimeError("Flet must be installed to build the UI") from exc

        page.title = "User Dashboard"

        app_state = get_app_state()
        user_name = app_state.auth.user_name or "User"
        user_id = app_state.auth.user_id

        _mobile = is_mobile(page)
        sidebar = create_user_sidebar(page, user_name, current_route=page.route)
        drawer = create_user_drawer(page, current_route=page.route) if _mobile else None
        _gradient_ref = show_page_loading(page, None if _mobile else sidebar, "Loading dashboard...")

        self._sync_pending_addresses_background()

        all_adoptions = self.adoption_service.get_all_requests() or []
        all_rescues = self.rescue_service.get_all_missions() or []
        
        if user_id:
            user_rescues = self.rescue_service.get_user_missions(user_id)
            user_rescues = [r for r in user_rescues if (r.get("status") or "").lower() != "cancelled"]
        else:
            user_rescues = []
        
        if user_id:
            user_adoptions = [a for a in all_adoptions if a.get("user_id") == user_id]
            user_adoptions = [a for a in user_adoptions if (a.get("status") or "").lower() != "cancelled"]
        else:
            user_adoptions = []
        
        total_adoptions = len(user_adoptions)
        total_rescues = len(user_rescues)

        user_rescue_status_dist = self.analytics_service.get_user_rescue_status_distribution(user_id) if user_id else {}
        user_adoption_status_dist = self.analytics_service.get_user_adoption_status_distribution(user_id) if user_id else {}

        adoptable_animals = self.animal_service.get_adoptable_animals() or []
        if adoptable_animals:
            random.shuffle(adoptable_animals)

        sidebar = create_user_sidebar(page, user_name, current_route=page.route)
        if _mobile:
            drawer = create_user_drawer(page, current_route=page.route)

        user_activity_stats = self.analytics_service.get_user_activity_stats(user_id) if user_id else {}
        rescued_successfully = user_rescue_status_dist.get("rescued", 0) if user_rescue_status_dist else 0
        
        impact_insight_data = self.analytics_service.get_user_impact_insights(user_id) if user_id else []
        
        # Render insights using frontend component
        insight_widgets = create_impact_insight_widgets(impact_insight_data)
        
        def create_impact_stat(icon, value, label, color):
            return ft.Container(
                ft.Column([
                    ft.Container(
                        ft.Icon(icon, size=24, color=ft.Colors.WHITE),
                        width=48,
                        height=48,
                        bgcolor=color,
                        border_radius=24,
                        alignment=ft.alignment.center,
                    ),
                    ft.Container(height=8),
                    ft.Text(str(value), size=24, weight="bold", color=ft.Colors.BLACK87),
                    ft.Text(label, size=11, color=ft.Colors.BLACK54, text_align=ft.TextAlign.CENTER),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0),
                width=120,
                padding=ft.padding.symmetric(vertical=15),
            )
        
        impact_section = ft.Container(
            ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.AUTO_AWESOME, size=22, color=ft.Colors.AMBER_600),
                    ft.Text("Your Impact", size=16, weight="w600", color=ft.Colors.BLACK87),
                ], spacing=8),
                ft.Divider(height=10, color=ft.Colors.GREY_200, thickness=2),
                ft.ResponsiveRow([
                    ft.Container(create_impact_stat(ft.Icons.PETS, total_rescues, "Rescues\nReported", ft.Colors.ORANGE_600), col={"xs": 6, "sm": 3}),
                    ft.Container(create_impact_stat(ft.Icons.CHECK_CIRCLE, rescued_successfully, "Successfully\nRescued", ft.Colors.GREEN_600), col={"xs": 6, "sm": 3}),
                    ft.Container(create_impact_stat(ft.Icons.FAVORITE, user_activity_stats.get("total_adoptions", 0), "Animals\nAdopted", ft.Colors.TEAL_600), col={"xs": 6, "sm": 3}),
                    ft.Container(create_impact_stat(ft.Icons.PENDING, user_activity_stats.get("pending_adoption_requests", 0), "Pending\nRequests", ft.Colors.BLUE_600), col={"xs": 6, "sm": 3}),
                ], spacing=0, run_spacing=0),
                ft.Container(height=7),
                ft.Row(insight_widgets, spacing=10, alignment=ft.MainAxisAlignment.CENTER, wrap=True),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0),
            padding=20,
            bgcolor=ft.Colors.WHITE,
            border_radius=12,
            border=ft.border.all(1, ft.Colors.GREY_200),
            shadow=ft.BoxShadow(blur_radius=8, spread_radius=1, color=ft.Colors.BLACK12, offset=(0, 2)),
        )

        def create_quick_action_btn(icon, text, color, route):
            return ft.ElevatedButton(
                content=ft.Row([
                    ft.Icon(icon, size=18, color=ft.Colors.WHITE),
                    ft.Text(text, size=13, weight="w500", color=ft.Colors.WHITE),
                ], spacing=8, alignment=ft.MainAxisAlignment.CENTER),
                height=40,
                style=ft.ButtonStyle(
                    bgcolor=color,
                    shape=ft.RoundedRectangleBorder(radius=20),
                    padding=ft.padding.symmetric(horizontal=20),
                ),
                on_click=lambda e: page.go(route),
            )
        
        _quick_actions = ft.Row([
                    create_quick_action_btn(ft.Icons.PETS, "Report Rescue", ft.Colors.ORANGE_600, "/rescue_form"),
                    create_quick_action_btn(ft.Icons.FAVORITE, "Apply to Adopt", ft.Colors.TEAL_500, "/available_adoption"),
                    create_ai_download_button(
                        on_click=lambda e: create_ai_download_dialog(page),
                        icon_size=14,
                        border_radius=20,
                        padding=ft.padding.symmetric(horizontal=16),
                    ),
                ], spacing=12, wrap=True)

        if _mobile:
            welcome_section = ft.Container(
                ft.Column([
                    ft.Row([
                        ft.Icon(ft.Icons.WAVING_HAND, size=28, color=ft.Colors.ORANGE_400),
                        ft.Column([
                            ft.Text(f"Welcome back, {user_name}!", size=22, weight="w600", color=ft.Colors.BLACK87),
                            ft.Text("Here's your activity overview", size=13, color=ft.Colors.BLACK54),
                        ], spacing=2, expand=True),
                    ], spacing=12, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    ft.Container(height=8),
                    _quick_actions,
                ], spacing=0),
                padding=ft.padding.symmetric(horizontal=15, vertical=14),
                bgcolor=ft.Colors.WHITE,
                border_radius=12,
                border=ft.border.all(1, ft.Colors.GREY_200),
                shadow=ft.BoxShadow(blur_radius=8, spread_radius=1, color=ft.Colors.BLACK12, offset=(0, 2)),
            )
        else:
            welcome_section = ft.Container(
                ft.Row([
                    ft.Icon(ft.Icons.WAVING_HAND, size=28, color=ft.Colors.ORANGE_400),
                    ft.Column([
                        ft.Text(f"Welcome back, {user_name}!", size=22, weight="w600", color=ft.Colors.BLACK87),
                        ft.Text("Here's your activity overview", size=13, color=ft.Colors.BLACK54),
                    ], spacing=2),
                    ft.Container(expand=True),
                    _quick_actions,
                ], spacing=12, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                padding=ft.padding.symmetric(horizontal=25, vertical=18),
                bgcolor=ft.Colors.WHITE,
                border_radius=12,
                border=ft.border.all(1, ft.Colors.GREY_200),
                shadow=ft.BoxShadow(blur_radius=8, spread_radius=1, color=ft.Colors.BLACK12, offset=(0, 2)),
            )

        adoption_pie_refs = {}  # For legend-pie sync
        if user_adoption_status_dist and sum(user_adoption_status_dist.values()) > 0:
            adoption_sections = []
            total = sum(user_adoption_status_dist.values())
            status_order = ["pending", "approved", "denied"]
            for status in status_order:
                if status in user_adoption_status_dist:
                    value = user_adoption_status_dist[status]
                    pct = (value / total * 100) if total > 0 else 0
                    adoption_sections.append({
                        "value": value,
                        "title": f"{pct:.0f}%",
                        "color": STATUS_COLORS.get(status, STATUS_COLORS["default"]),
                    })
            adoption_pie = create_pie_chart(adoption_sections, width=140, height=140, section_radius=54, legend_refs=adoption_pie_refs)
            
            adoption_legend_items = [
                {"label": status.capitalize(), "value": user_adoption_status_dist.get(status, 0), "color": STATUS_COLORS.get(status, STATUS_COLORS["default"])}
                for status in status_order
            ]
            adoption_legend = create_chart_legend(adoption_legend_items, horizontal=False, pie_refs=adoption_pie_refs)
            adoption_data_for_dialog = [{"label": status.capitalize(), "value": user_adoption_status_dist.get(status, 0), "color": STATUS_COLORS.get(status, STATUS_COLORS["default"])} for status in status_order if status in user_adoption_status_dist]
        else:
            adoption_pie = ft.Container(
                ft.Column([
                    ft.Icon(ft.Icons.PIE_CHART, size=48, color=ft.Colors.GREY_400),
                    ft.Text("No data", size=12, color=ft.Colors.GREY_500),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=4),
                width=150, height=150, alignment=ft.alignment.center,
            )
            adoption_legend = ft.Text("No applications yet", size=13, color=ft.Colors.BLACK54)
            adoption_data_for_dialog = []
        
        def show_adoption_details(e):
            if adoption_data_for_dialog:
                show_chart_details_dialog(page, "My Adoption Status Details", adoption_data_for_dialog, "pie")

        adoptions_card = ft.Container(
            ft.Column([
                # Header
                ft.Row([
                    ft.Icon(ft.Icons.FAVORITE, size=22, color=ft.Colors.TEAL_600),
                    ft.Text("My Adoptions", size=16, weight="w600", color=ft.Colors.BLACK87),
                    ft.Container(expand=True),
                    ft.Container(
                        ft.Text(str(total_adoptions), size=22, weight="bold", color=ft.Colors.TEAL_600),
                    ),
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
                ], spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                ft.Divider(height=5),
                # Content: Chart + Legend side by side
                create_scrollable_chart_content(
                    adoption_pie,
                    adoption_legend,
                    chart_width=160,
                    legend_width=170,
                    legend_height=150,
                ),
                
            ], spacing=0),
            padding=20,
            bgcolor=ft.Colors.WHITE,
            border_radius=12,
            border=ft.border.all(1, ft.Colors.GREY_200),
            shadow=ft.BoxShadow(blur_radius=8, spread_radius=1, color=ft.Colors.BLACK12, offset=(0, 2)),
        )

        rescue_pie_refs = {}  # For legend-pie sync
        if user_rescue_status_dist and sum(user_rescue_status_dist.values()) > 0:
            rescue_sections = []
            total = sum(user_rescue_status_dist.values())
            status_order = ["pending", "on-going", "rescued", "failed"]
            for status in status_order:
                if status in user_rescue_status_dist:
                    value = user_rescue_status_dist[status]
                    pct = (value / total * 100) if total > 0 else 0
                    rescue_sections.append({
                        "value": value,
                        "title": f"{pct:.0f}%",
                        "color": STATUS_COLORS.get(status, STATUS_COLORS["default"]),
                    })
            rescue_pie = create_pie_chart(rescue_sections, width=140, height=140, section_radius=54, legend_refs=rescue_pie_refs)
            
            rescue_legend_items = [
                {"label": status.capitalize(), "value": user_rescue_status_dist.get(status, 0), "color": STATUS_COLORS.get(status, STATUS_COLORS["default"])}
                for status in status_order
            ]
            rescue_legend = create_chart_legend(rescue_legend_items, horizontal=False, pie_refs=rescue_pie_refs)
            rescue_data_for_dialog = [{"label": status.capitalize(), "value": user_rescue_status_dist.get(status, 0), "color": STATUS_COLORS.get(status, STATUS_COLORS["default"])} for status in status_order if status in user_rescue_status_dist]
        else:
            rescue_pie = create_empty_chart_message("No reports yet", width=160, height=150)
            rescue_legend = ft.Container()
            rescue_data_for_dialog = []
        
        def show_rescue_details(e):
            if rescue_data_for_dialog:
                show_chart_details_dialog(page, "My Rescue Status Details", rescue_data_for_dialog, "pie")

        rescues_card = ft.Container(
            ft.Column([
                # Header
                ft.Row([
                    ft.Icon(ft.Icons.PETS, size=22, color=ft.Colors.ORANGE_600),
                    ft.Text("My Rescues", size=16, weight="w600", color=ft.Colors.BLACK87),
                    ft.Container(expand=True),
                    ft.Container(
                        ft.Text(str(total_rescues), size=22, weight="bold", color=ft.Colors.ORANGE_600),
                    ),
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
                ], spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                ft.Divider(height=5),
                # Content: Chart + Legend side by side
                create_scrollable_chart_content(
                    rescue_pie,
                    rescue_legend,
                    chart_width=160,
                    legend_width=170,
                    legend_height=150,
                ),
            ], spacing=0),
            padding=20,
            bgcolor=ft.Colors.WHITE,
            border_radius=12,
            border=ft.border.all(1, ft.Colors.GREY_200),
            shadow=ft.BoxShadow(blur_radius=8, spread_radius=1, color=ft.Colors.BLACK12, offset=(0, 2)),
        )

        popular_breeds_data = self.analytics_service.get_adoptable_breed_distribution(limit=3)
        
        if popular_breeds_data and len(popular_breeds_data) > 0:
            breed_labels = [breed for breed, _ in popular_breeds_data]
            breed_values = [count for _, count in popular_breeds_data]
            breed_colors = [PIE_CHART_COLORS[i % len(PIE_CHART_COLORS)] for i in range(len(breed_labels))]
            
            breed_data_for_dialog = []
            breed_bar_groups = []
            breed_bar_refs = {}  # For legend-bar sync
            
            for i, (label, value, color) in enumerate(zip(breed_labels, breed_values, breed_colors)):
                breed_bar_groups.append({
                    "x": i,
                    "rods": [{"value": value, "color": color, "width": 28}]
                })
                breed_data_for_dialog.append({
                    "label": label,
                    "value": value,
                    "color": color,
                })
            
            popular_breeds_bar_chart = create_bar_chart(
                bar_groups=breed_bar_groups,
                bottom_labels=None,
                height=140,
                legend_refs=breed_bar_refs,
            )
            
            breed_legend_items = [
                {"label": label, "value": value, "color": color}
                for label, value, color in zip(breed_labels, breed_values, breed_colors)
            ]
            breed_legend = create_chart_legend(breed_legend_items, horizontal=False, bar_refs=breed_bar_refs, text_size=10)
            
            def show_popular_breeds_details(e):
                show_chart_details_dialog(page, "Popular Breeds Breakdown", breed_data_for_dialog, "bar")
            
            popular_breeds_card = ft.Container(
                ft.Column([
                    ft.Row([
                        ft.Icon(ft.Icons.EMOJI_EVENTS, size=22, color=ft.Colors.PURPLE_600),
                        ft.Text("Popular Breeds", size=16, weight="w600", color=ft.Colors.BLACK87),
                        ft.Container(expand=True),
                        ft.Container(
                            ft.IconButton(
                                icon=ft.Icons.OPEN_IN_NEW,
                                icon_size=16,
                                icon_color=ft.Colors.TEAL_600,
                                tooltip="View detailed breakdown",
                                on_click=show_popular_breeds_details,
                            ),
                            bgcolor=ft.Colors.TEAL_50,
                            border_radius=8,
                            border=ft.border.all(1, ft.Colors.TEAL_200),
                        ),
                    ], spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    ft.Divider(height=5),
                    create_scrollable_chart_content(
                        popular_breeds_bar_chart,
                        breed_legend,
                        chart_width=180,
                        legend_width=170,
                        legend_height=150,
                    ),
                ], spacing=0),
                padding=20,
                bgcolor=ft.Colors.WHITE,
                border_radius=12,
                border=ft.border.all(1, ft.Colors.GREY_200),
                shadow=ft.BoxShadow(blur_radius=8, spread_radius=1, color=ft.Colors.BLACK12, offset=(0, 2)),
            )
        else:
            popular_breeds_card = ft.Container(
                ft.Column([
                    ft.Row([
                        ft.Icon(ft.Icons.EMOJI_EVENTS, size=22, color=ft.Colors.PURPLE_600),
                        ft.Text("Popular Breeds", size=16, weight="w600", color=ft.Colors.BLACK87),
                    ], spacing=10),
                    ft.Divider(height=5),
                    ft.Container(
                        ft.Column([
                            ft.Icon(ft.Icons.PETS, size=48, color=ft.Colors.GREY_400),
                            ft.Text("No adoptable animals yet", size=13, color=ft.Colors.BLACK54),
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8),
                        expand=True,
                        alignment=ft.alignment.center,
                    ),
                ], spacing=0),
                padding=20,
                bgcolor=ft.Colors.WHITE,
                border_radius=12,
                border=ft.border.all(1, ft.Colors.GREY_200),
                shadow=ft.BoxShadow(blur_radius=8, spread_radius=1, color=ft.Colors.BLACK12, offset=(0, 2)),
            )

        adoptable_breeds_data = self.analytics_service.get_adoptable_breed_distribution(limit=10)
        
        breed_pie_refs = {}  # For legend-pie sync
        if adoptable_breeds_data and len(adoptable_breeds_data) > 0:
            breed_sections = []
            total_breeds = sum(count for _, count in adoptable_breeds_data)
            breed_data_for_dialog = []
            
            for i, (breed, count) in enumerate(adoptable_breeds_data):
                pct = (count / total_breeds * 100) if total_breeds > 0 else 0
                color = PIE_CHART_COLORS[i % len(PIE_CHART_COLORS)]
                breed_sections.append({
                    "value": count,
                    "title": f"{pct:.0f}%",
                    "color": color,
                })
                breed_data_for_dialog.append({
                    "label": breed,
                    "value": count,
                    "color": color,
                })
            
            breed_pie = create_pie_chart(breed_sections, width=140, height=140, section_radius=54, legend_refs=breed_pie_refs)
            
            breed_legend_items = [
                {"label": breed, "value": count, "color": PIE_CHART_COLORS[i % len(PIE_CHART_COLORS)]}
                for i, (breed, count) in enumerate(adoptable_breeds_data)
            ]
            breed_legend = create_chart_legend(breed_legend_items, horizontal=False, pie_refs=breed_pie_refs, text_size=10)
        else:
            breed_pie = create_empty_chart_message("No animals available", width=160, height=150)
            breed_legend = ft.Container()
            breed_data_for_dialog = []
        
        def show_adoptable_breeds_details(e):
            if breed_data_for_dialog:
                show_chart_details_dialog(page, "Adoptable Breeds Details", breed_data_for_dialog, "pie")

        adoptable_breeds_card = ft.Container(
            ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.CATEGORY, size=22, color=ft.Colors.BLUE_600),
                    ft.Text("Adoptable Breeds", size=16, weight="w600", color=ft.Colors.BLACK87),
                    ft.Container(expand=True),
                    ft.Container(
                        ft.IconButton(
                            icon=ft.Icons.OPEN_IN_NEW,
                            icon_size=16,
                            icon_color=ft.Colors.TEAL_600,
                            tooltip="View detailed breakdown",
                            on_click=show_adoptable_breeds_details,
                        ),
                        bgcolor=ft.Colors.TEAL_50,
                        border_radius=8,
                        border=ft.border.all(1, ft.Colors.TEAL_200),
                    ) if breed_data_for_dialog else ft.Container(),
                ], spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                ft.Divider(height=5),
                create_scrollable_chart_content(
                    breed_pie,
                    breed_legend,
                    chart_width=160,
                    legend_width=170,
                    legend_height=150,
                ),
            ], spacing=0),
            padding=20,
            bgcolor=ft.Colors.WHITE,
            border_radius=12,
            border=ft.border.all(1, ft.Colors.GREY_200),
            shadow=ft.BoxShadow(blur_radius=8, spread_radius=1, color=ft.Colors.BLACK12, offset=(0, 2)),
        )

        if adoptable_animals:
            current_index = [0]
            is_hovered = [False]
            auto_scroll_timer = [None]
            
            carousel_animals = adoptable_animals[:5]
            num_animals = len(carousel_animals)
            has_multiple_animals = num_animals > 1
            
            def create_featured_animal_card(animal: dict, index: int) -> ft.Control:
                """Create a featured animal card using the standardized component."""
                animal_id = animal.get("id")
                animal_name = animal.get("name", "Unknown")
                animal_age = animal.get("age", "N/A")
                animal_species = animal.get("species", "Unknown")
                animal_breed = animal.get("breed")
                animal_health = animal.get("status", "Unknown")
                animal_photo = load_photo(animal.get("photo"))
                
                return create_animal_card(
                    animal_id=animal_id,
                    name=animal_name,
                    species=animal_species,
                    age=animal_age if isinstance(animal_age, int) else 0,
                    status=animal_health,
                    photo_base64=animal_photo,
                    on_adopt=lambda e, aid=animal_id: page.go(f"/adoption_form?animal_id={aid}"),
                    is_admin=False,
                    show_adopt_button=True,
                    breed=animal_breed,
                )

            # Dot indicators
            dot_containers = []
            if has_multiple_animals:
                for i in range(num_animals):
                    dot = ft.Container(
                        width=10,
                        height=10,
                        bgcolor=ft.Colors.TEAL_500 if i == 0 else ft.Colors.GREY_300,
                        border_radius=5,
                        animate=ft.Animation(300, ft.AnimationCurve.EASE_IN_OUT),
                    )
                    dot_containers.append(dot)

            carousel_content = ft.Container(
                create_featured_animal_card(carousel_animals[0], 0),
                alignment=ft.alignment.center,
                animate_opacity=ft.Animation(300, ft.AnimationCurve.EASE_IN_OUT),
                opacity=1.0,
            )

            def update_carousel(new_index: int):
                if new_index < 0:
                    new_index = num_animals - 1
                elif new_index >= num_animals:
                    new_index = 0
                
                current_index[0] = new_index
                
                for i, dot in enumerate(dot_containers):
                    dot.bgcolor = ft.Colors.TEAL_500 if i == new_index else ft.Colors.GREY_300
                
                carousel_content.opacity = 0.0
                page.update()
                
                def update_content():
                    carousel_content.content = create_featured_animal_card(carousel_animals[new_index], new_index)
                    carousel_content.opacity = 1.0
                    page.update()
                
                threading.Timer(0.15, update_content).start()

            def on_prev_click(e):
                update_carousel(current_index[0] - 1)

            def on_next_click(e):
                update_carousel(current_index[0] + 1)

            def on_dot_click(index: int):
                def handler(e):
                    update_carousel(index)
                return handler

            for i, dot in enumerate(dot_containers):
                dot.on_click = on_dot_click(i)

            def start_auto_scroll():
                if not has_multiple_animals:
                    return
                
                def auto_scroll():
                    if not is_hovered[0]:
                        update_carousel(current_index[0] + 1)
                    if not is_hovered[0]:
                        auto_scroll_timer[0] = threading.Timer(4.0, auto_scroll)
                        auto_scroll_timer[0].start()
                
                auto_scroll_timer[0] = threading.Timer(4.0, auto_scroll)
                auto_scroll_timer[0].start()

            def on_hover(e):
                is_hovered[0] = e.data == "true"
                if is_hovered[0]:
                    if auto_scroll_timer[0]:
                        auto_scroll_timer[0].cancel()
                else:
                    if has_multiple_animals:
                        start_auto_scroll()

            if has_multiple_animals:
                start_auto_scroll()

            # Navigation arrows
            nav_row = ft.Row([
                ft.IconButton(
                    icon=ft.Icons.CHEVRON_LEFT,
                    icon_color=ft.Colors.TEAL_600,
                    icon_size=24,
                    on_click=on_prev_click,
                    tooltip="Previous",
                ) if has_multiple_animals else ft.Container(width=40),
                ft.Row(dot_containers, spacing=6, alignment=ft.MainAxisAlignment.CENTER),
                ft.IconButton(
                    icon=ft.Icons.CHEVRON_RIGHT,
                    icon_color=ft.Colors.TEAL_600,
                    icon_size=24,
                    on_click=on_next_click,
                    tooltip="Next",
                ) if has_multiple_animals else ft.Container(width=40),
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=10)

            featured_card = ft.Container(
                ft.Column([
                    ft.Row([
                        ft.Icon(ft.Icons.STAR, size=22, color=ft.Colors.AMBER_600),
                        ft.Text("Featured Adoptables", size=16, weight="w600", color=ft.Colors.BLACK87),
                    ], spacing=8, alignment=ft.MainAxisAlignment.CENTER,),
                    ft.Divider(height=10, thickness=2, color=ft.Colors.GREY_500),
                    ft.Container(
                        ft.Container(
                            carousel_content,
                        ),
                        alignment=ft.alignment.center,
                        expand=True,
                    ),
                    ft.Container(height=1),
                    nav_row,
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0),
                padding=ft.padding.symmetric(vertical=10, horizontal=30),
                bgcolor=ft.Colors.WHITE,
                border_radius=12,
                border=ft.border.all(1, ft.Colors.GREY_200),
                shadow=ft.BoxShadow(blur_radius=8, spread_radius=1, color=ft.Colors.BLACK12, offset=(0, 2)),
                on_hover=on_hover,
            )
        else:
            featured_card = ft.Container(
                ft.Column([
                    ft.Row([
                        ft.Icon(ft.Icons.STAR, size=22, color=ft.Colors.AMBER_600),
                        ft.Text("Featured Adoptables", size=16, weight="w600", color=ft.Colors.BLACK87),
                    ], spacing=8, alignment=ft.MainAxisAlignment.CENTER),
                    ft.Container(height=8),
                    ft.Container(
                        ft.Column([
                            ft.Icon(ft.Icons.PETS, size=80, color=ft.Colors.GREY_400),
                            ft.Text("No animals available", size=14, color=ft.Colors.BLACK54),
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
                        expand=True,
                        alignment=ft.alignment.center,
                    ),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0),
                padding=ft.padding.symmetric(vertical=30, horizontal=30),
                bgcolor=ft.Colors.WHITE,
                border_radius=12,
                border=ft.border.all(1, ft.Colors.GREY_200),
                shadow=ft.BoxShadow(blur_radius=8, spread_radius=1, color=ft.Colors.BLACK12, offset=(0, 2)),
            )

        is_online = self.map_service.check_map_tiles_available()
        
        if is_online:
            map_card = ft.Container(
                create_interactive_map(
                    map_service=self.map_service,
                    missions=all_rescues,
                    page=page,
                    zoom=11,
                    is_admin=False,
                    height=500,
                    title="Realtime Rescue Mission Map",
                    show_legend=True,
                    initially_locked=True,
                ),
            )
        else:
            offline_widget = self.map_service.create_offline_map_fallback(all_rescues, is_admin=False)
            if offline_widget:
                map_card = ft.Container(
                    ft.Column([
                        ft.Row([
                            ft.Icon(ft.Icons.MAP, size=20, color=ft.Colors.TEAL_600),
                            ft.Text("Realtime Rescue Mission Map", size=16, weight="w600", color=ft.Colors.BLACK87),
                        ], spacing=8),
                        ft.Divider(height=15, color=ft.Colors.GREY_200),
                        ft.Container(
                            offline_widget,
                            height=500,
                            border_radius=8,
                            border=ft.border.all(1, ft.Colors.AMBER_200),
                        ),
                    ], spacing=0),
                    padding=20,
                    bgcolor=ft.Colors.WHITE,
                    border_radius=12,
                    border=ft.border.all(1, ft.Colors.GREY_200),
                    shadow=ft.BoxShadow(blur_radius=8, spread_radius=1, color=ft.Colors.BLACK12, offset=(0, 2)),
                )
            else:
                map_card = ft.Container(
                    ft.Column([
                        ft.Row([
                            ft.Icon(ft.Icons.MAP, size=20, color=ft.Colors.TEAL_600),
                            ft.Text("Realtime Rescue Mission Map", size=16, weight="w600", color=ft.Colors.BLACK87),
                        ], spacing=8),
                        ft.Divider(height=15, color=ft.Colors.GREY_200),
                        self.map_service.create_empty_map_placeholder(len(all_rescues)),
                    ], spacing=0),
                    padding=20,
                    bgcolor=ft.Colors.WHITE,
                    border_radius=12,
                    border=ft.border.all(1, ft.Colors.GREY_200),
                    shadow=ft.BoxShadow(blur_radius=8, spread_radius=1, color=ft.Colors.BLACK12, offset=(0, 2)),
                )

        # Activity section: responsive 3 columns on desktop, stacked on mobile
        _card_col = {"xs": 12, "md": 6, "lg": 4}
        activity_section = ft.ResponsiveRow([
            # Left: My Adoptions and My Rescues stacked vertically
            ft.Container(
                ft.Column([
                    adoptions_card,
                    rescues_card,
                ], spacing=15),
                col=_card_col,
            ),
            # Middle: Breed charts stacked vertically
            ft.Container(
                ft.Column([
                    popular_breeds_card,
                    adoptable_breeds_card,
                ], spacing=15),
                col=_card_col,
            ),
            # Right: Featured Adoptables
            ft.Container(
                featured_card,
                col=_card_col,
            ),
        ], spacing=15, run_spacing=15)
        
        _content_padding = responsive_padding(page)

        main_content = ft.Container(
            ft.Column([
                # Welcome section
                welcome_section,
                ft.Container(height=20),
                # Your Impact section
                impact_section,
                ft.Container(height=20),
                # Activity section
                activity_section,
                ft.Container(height=20),
                # Map
                map_card,
                ft.Container(height=30),
            ], spacing=0, scroll=ft.ScrollMode.AUTO, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=_content_padding,
            expand=True,
        )

        main_layout = create_responsive_layout(page, sidebar, main_content, drawer, title="Dashboard")

        finish_page_loading(page, _gradient_ref, main_layout)


__all__ = ["UserDashboard"]


