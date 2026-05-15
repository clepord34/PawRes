"""Page showing personalized pet recommendations for users."""
from __future__ import annotations

from typing import Optional

import app_config
from services.recommendation_service import RecommendationService
from services.photo_service import load_photo
from state import get_app_state
from components import (
    create_user_sidebar,
    create_user_drawer,
    create_animal_card,
    create_empty_state_with_action,
    create_form_dropdown,
    create_form_text_field,
    create_page_control_bar,
    show_snackbar,
    show_page_loading,
    finish_page_loading,
    is_mobile,
    create_responsive_layout,
    responsive_padding,
)


class PetRecommendationsPage:
    """Page that lists personalized pet recommendations."""

    def __init__(self, db_path: Optional[str] = None) -> None:
        self._db_path = db_path or app_config.DB_PATH
        self._service = RecommendationService(self._db_path)
        self._current_search = ""
        self._species_filter = "All Species"
        self._recommendations: list[dict] = []
        self._cards_container: Optional[object] = None
        self._has_preferences = False

    def build(self, page) -> None:
        try:
            import flet as ft
        except Exception as exc:
            raise RuntimeError("Flet must be installed to build the UI") from exc

        page.title = "Pet Recommendations"

        app_state = get_app_state(page, self._db_path)
        user_id = app_state.auth.user_id or page.session.get("user_id")
        if not user_id:
            show_snackbar(page, "Please sign in to view recommendations", error=True)
            page.go("/")
            return

        _mobile = is_mobile(page)
        sidebar = create_user_sidebar(page, app_state.auth.user_name or "User", current_route=page.route)
        drawer = create_user_drawer(page, current_route=page.route) if _mobile else None
        _gradient_ref = show_page_loading(page, None if _mobile else sidebar, "Loading recommendations...")
        sidebar = create_user_sidebar(page, app_state.auth.user_name or "User", current_route=page.route)

        preferences = self._service.get_preferences(user_id)
        self._has_preferences = bool(preferences)
        if self._has_preferences:
            self._recommendations = self._service.get_recommendations(user_id, limit=40)
        else:
            self._recommendations = self._service.get_recommendations_without_preferences(user_id, limit=40)

        species_options = sorted({
            (rec.get("animal") or {}).get("species", "Unknown")
            for rec in self._recommendations
            if (rec.get("animal") or {}).get("species")
        })

        species_dropdown = create_form_dropdown(
            hint_text="Filter by Species",
            options=["All Species"] + species_options,
            value=self._species_filter,
            on_change=lambda e: self._on_species_filter(page, e.control.value),
        )

        search_field = create_form_text_field(
            hint_text="Search by name or breed...",
            prefix_icon=ft.Icons.SEARCH,
            expand=True,
            value=self._current_search,
            on_change=lambda e: self._on_search(page, e.control.value),
        )

        control_bar = create_page_control_bar(
            title="Pet Recommendations",
            search_field=search_field,
            filters=[species_dropdown],
            is_mobile=_mobile,
            page=page,
        )

        header_actions = []
        if self._has_preferences:
            header_actions.append(
                ft.TextButton(
                    "Edit Preferences",
                    on_click=lambda e: page.go("/pet_preferences"),
                )
            )
        else:
            header_actions.append(
                ft.TextButton(
                    "Set Preferences",
                    on_click=lambda e: page.go("/pet_preferences"),
                )
            )

        header_row = ft.Row([
            ft.Column([
                ft.Text("Recommended For You", size=20, weight="w600", color=ft.Colors.BLACK87),
                ft.Text(
                    "Update your preferences to improve recommendations",
                    size=12,
                    color=ft.Colors.BLACK54,
                ),
            ], spacing=2),
            ft.Container(expand=True),
            *header_actions,
        ], alignment=ft.MainAxisAlignment.CENTER)

        recommendations_view = self._build_recommendations_view(page)

        content = ft.Container(
            ft.Column([
                ft.Container(
                    ft.Column([
                        header_row,
                        ft.Container(height=8),
                        control_bar,
                        recommendations_view,
                    ], spacing=0),
                    padding=responsive_padding(page),
                ),
            ], scroll=ft.ScrollMode.AUTO, expand=True),
            expand=True,
        )

        layout = create_responsive_layout(page, sidebar, content, drawer, title="Recommendations")
        finish_page_loading(page, _gradient_ref, layout)

    def _build_recommendations_view(self, page) -> object:
        import flet as ft

        filtered = self._filter_recommendations()
        if not filtered:
            action_text = "Set Preferences" if not self._has_preferences else "Browse Animals"
            action_route = "/pet_preferences" if not self._has_preferences else "/available_adoption"
            empty_state = create_empty_state_with_action(
                message="No recommendations yet",
                subtitle="Try widening your preferences or check back later.",
                icon=ft.Icons.PETS,
                button_text=action_text,
                button_icon=ft.Icons.TUNE,
                on_click=lambda e: page.go(action_route),
                padding=40,
            )
            self._cards_container = ft.ResponsiveRow([
                ft.Container(empty_state, col={"xs": 12, "sm": 12, "md": 12, "lg": 12})
            ])
            return self._cards_container

        card_controls = []
        for rec in filtered:
            card_controls.append(
                ft.Container(
                    self._create_recommendation_card(page, rec),
                    col={"xs": 6, "sm": 6, "md": 4, "lg": 3},
                )
            )

        self._cards_container = ft.ResponsiveRow(
            card_controls,
            spacing=16,
            run_spacing=16,
        )
        return self._cards_container

    def _create_recommendation_card(self, page, rec: dict) -> object:
        import flet as ft

        animal = rec.get("animal") or {}
        animal_id = animal.get("id")
        score = int(rec.get("score", 0))
        reasons = self._filter_match_reasons(rec.get("match_reasons") or [])

        def open_match_insights(e):
            if not reasons:
                return

            badges = [self._create_reason_badge(ft, reason) for reason in reasons]
            dlg = ft.AlertDialog(
                title=ft.Text("Why this pet is recommended", size=16, weight="w600"),
                content=ft.Container(
                    ft.Column(badges, spacing=8, tight=True, scroll=ft.ScrollMode.AUTO),
                    width=320,
                    height=220,
                    padding=8,
                ),
                actions=[
                    ft.TextButton("Close", on_click=lambda evt: page.close(dlg)),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )
            page.open(dlg)

        score_badge = ft.Container(
            ft.Row([
                ft.Icon(ft.Icons.STAR, size=12, color=ft.Colors.WHITE),
                ft.Text(f"Score {score}", size=11, color=ft.Colors.WHITE, weight="w600"),
                ft.Icon(ft.Icons.INFO_OUTLINE, size=12, color=ft.Colors.WHITE) if reasons else ft.Container(),
            ], spacing=5, alignment=ft.MainAxisAlignment.CENTER),
            padding=ft.padding.symmetric(horizontal=10, vertical=8),
            bgcolor=ft.Colors.TEAL_600,
            border_radius=15,
            shadow=ft.BoxShadow(blur_radius=4, spread_radius=0, color=ft.Colors.BLACK26, offset=(0, 2)),
            on_click=open_match_insights if reasons else None,
            tooltip="Tap for match insights" if reasons else None,
        )

        photo_base64 = load_photo(animal.get("photo"))
        base_card = create_animal_card(
            animal_id=animal_id,
            name=animal.get("name", "Unknown"),
            species=animal.get("species", "Unknown"),
            age=animal.get("age", 0),
            status=animal.get("status", "unknown"),
            photo_base64=photo_base64,
            on_adopt=lambda e, aid=animal_id: page.go(f"/adoption_form?animal_id={aid}"),
            is_admin=False,
            show_adopt_button=True,
            breed=animal.get("breed"),
            custom_badge=score_badge,
        )

        return ft.Column([base_card], spacing=0)

    def _create_reason_badge(self, ft, reason: str) -> object:
        style_map = {
            "Matches preferred species": (ft.Colors.TEAL_600, ft.Icons.PETS),
            "Matches preferred breed": (ft.Colors.GREEN_700, ft.Icons.CHECK_CIRCLE),
            "Similar breed preference": (ft.Colors.GREEN_600, ft.Icons.VERIFIED),
            "Fits your age range": (ft.Colors.BLUE_600, ft.Icons.CAKE),
            "Based on your past adoptions": (ft.Colors.PURPLE_600, ft.Icons.HISTORY),
        }
        bg_color, icon = style_map.get(reason, (ft.Colors.GREY_600, ft.Icons.INFO))

        return ft.Container(
            ft.Row([
                ft.Icon(icon, color=ft.Colors.WHITE, size=12),
                ft.Text(reason, color=ft.Colors.WHITE, size=11, weight="w500"),
            ], spacing=5, alignment=ft.MainAxisAlignment.CENTER),
            padding=ft.padding.symmetric(horizontal=10, vertical=8),
            bgcolor=bg_color,
            border_radius=15,
        )

    def _filter_match_reasons(self, reasons: list[str]) -> list[str]:
        allowed = {
            "Matches preferred species",
            "Matches preferred breed",
            "Similar breed preference",
            "Fits your age range",
            "Based on your past adoptions",
        }
        return [reason for reason in reasons if reason in allowed]

    def _filter_recommendations(self) -> list[dict]:
        filtered = self._recommendations

        if self._species_filter and self._species_filter != "All Species":
            filtered = [
                r for r in filtered
                if (r.get("animal") or {}).get("species", "").lower() == self._species_filter.lower()
            ]

        search = self._current_search.lower().strip()
        if search:
            filtered = [
                r for r in filtered
                if search in (r.get("animal") or {}).get("name", "").lower()
                or search in ((r.get("animal") or {}).get("breed") or "").lower()
            ]

        return filtered

    def _on_search(self, page, value: str) -> None:
        self._current_search = value
        if self._cards_container:
            self._cards_container.controls = self._build_recommendation_controls(page)
            self._cards_container.update()

    def _on_species_filter(self, page, value: str) -> None:
        self._species_filter = value
        if self._cards_container:
            self._cards_container.controls = self._build_recommendation_controls(page)
            self._cards_container.update()

    def _build_recommendation_controls(self, page) -> list:
        import flet as ft

        filtered = self._filter_recommendations()
        if not filtered:
            action_text = "Set Preferences" if not self._has_preferences else "Browse Animals"
            action_route = "/pet_preferences" if not self._has_preferences else "/available_adoption"
            empty_state = create_empty_state_with_action(
                message="No recommendations yet",
                subtitle="Try widening your preferences or check back later.",
                icon=ft.Icons.PETS,
                button_text=action_text,
                button_icon=ft.Icons.TUNE,
                on_click=lambda e: page.go(action_route),
                padding=40,
            )
            return [ft.Container(empty_state, col={"xs": 12, "sm": 12, "md": 12, "lg": 12})]

        controls = []
        for rec in filtered:
            controls.append(
                ft.Container(
                    self._create_recommendation_card(page, rec),
                    col={"xs": 6, "sm": 6, "md": 4, "lg": 3},
                )
            )
        return controls


__all__ = ["PetRecommendationsPage"]
