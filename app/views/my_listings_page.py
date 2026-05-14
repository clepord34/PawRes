"""Page for users to manage their pet listings."""
from __future__ import annotations
from typing import Optional

import app_config
from app_config import AnimalStatus
from services.animal_service import AnimalService
from services.photo_service import load_photo
from state import get_app_state
from components import (
    create_user_sidebar,
    create_user_drawer,
    create_gradient_background,
    create_page_control_bar,
    create_form_text_field,
    create_animal_card,
    create_empty_state_with_action,
    create_confirmation_dialog,
    show_snackbar,
    show_page_loading,
    finish_page_loading,
    is_mobile,
    create_responsive_layout,
    responsive_padding,
)


class MyListingsPage:
    """Page displaying a user's posted pets for adoption."""

    def __init__(self, db_path: Optional[str] = None) -> None:
        self._db_path = db_path or app_config.DB_PATH
        self._service = AnimalService(self._db_path)
        self._app_state = None
        self.current_search = ""
        self._status_filter = "all"

    def build(self, page) -> None:
        try:
            import flet as ft
        except Exception as exc:
            raise RuntimeError("Flet must be installed to build the UI") from exc

        page.title = "My Listings"
        self._app_state = get_app_state(page, self._db_path)
        user_id = self._app_state.auth.user_id or page.session.get("user_id")
        if not user_id:
            show_snackbar(page, "Please sign in to view your listings", error=True)
            page.go("/")
            return

        user_name = self._app_state.auth.user_name or "User"

        _mobile = is_mobile(page)
        sidebar = create_user_sidebar(page, user_name, current_route=page.route)
        drawer = create_user_drawer(page, current_route=page.route) if _mobile else None
        _gradient_ref = show_page_loading(page, None if _mobile else sidebar, "Loading listings...")
        sidebar = create_user_sidebar(page, user_name, current_route=page.route)

        listings = self._service.get_user_listings(user_id) or []

        if self._status_filter != "all":
            listings = [
                l for l in listings
                if AnimalStatus.normalize(l.get("status", "")) == self._status_filter
            ]

        search_query = self.current_search.lower().strip()
        if search_query:
            listings = [
                l for l in listings
                if search_query in (l.get("name", "").lower() or "")
                or search_query in (l.get("breed", "").lower() or "")
            ]

        def handle_remove(animal_id: int, pet_name: str):
            def on_confirm():
                result = self._service.remove_user_listing(animal_id, user_id)
                if result.get("success"):
                    msg = "Listing removed"
                    if result.get("adoptions_affected", 0) > 0:
                        msg += f" ({result['adoptions_affected']} pending adoptions auto-denied)"
                    show_snackbar(page, msg)
                    self.build(page)
                else:
                    show_snackbar(page, "Failed to remove listing", error=True)

            create_confirmation_dialog(
                page,
                title="Remove Listing",
                message=f"Remove \"{pet_name}\" from your listings?",
                on_confirm=on_confirm,
                confirm_text="Remove",
                cancel_text="Cancel",
            )

        def create_card(listing: dict) -> object:
            status = listing.get("status", "")
            normalized_status = AnimalStatus.normalize(status)
            can_edit = normalized_status not in (AnimalStatus.ADOPTED, AnimalStatus.REMOVED)
            can_remove = normalized_status not in (AnimalStatus.ADOPTED, AnimalStatus.REMOVED)

            photo_base64 = load_photo(listing.get("photo"))
            return create_animal_card(
                animal_id=listing.get("id"),
                name=listing.get("name", "Unknown"),
                species=listing.get("species", "Unknown"),
                age=listing.get("age"),
                status=status,
                photo_base64=photo_base64,
                on_edit=(lambda e, aid=listing.get("id"): page.go(f"/edit_listing?animal_id={aid}"))
                if can_edit else None,
                on_remove=(lambda _id, aid=listing.get("id"), pname=listing.get("name", "Listing"): handle_remove(aid, pname))
                if can_remove else None,
                is_admin=can_edit or can_remove,
                show_adopt_button=False,
                breed=listing.get("breed"),
                status_context="listing",
            )

        if listings:
            card_controls = [
                ft.Container(create_card(l), col={"xs": 6, "sm": 6, "md": 4, "lg": 3})
                for l in listings
            ]
        else:
            card_controls = [
                ft.Container(
                    create_empty_state_with_action(
                        message="You have no pet listings yet",
                        icon=ft.Icons.PETS,
                        button_text="Post a Pet",
                        button_icon=ft.Icons.POST_ADD,
                        on_click=lambda e: page.go("/post_pet"),
                        padding=30,
                    ),
                    col={"xs": 12, "sm": 12, "md": 12, "lg": 12},
                    alignment=ft.alignment.center,
                )
            ]

        cards_container = ft.ResponsiveRow(
            card_controls,
            spacing=16,
            run_spacing=16,
        )

        status_filter = ft.Dropdown(
            hint_text="Status",
            value=self._status_filter,
            options=[
                ft.dropdown.Option("all", text="All"),
                ft.dropdown.Option(AnimalStatus.PROCESSING, text="Pending"),
                ft.dropdown.Option(AnimalStatus.HEALTHY, text="Approved"),
                ft.dropdown.Option(AnimalStatus.DECLINED, text="Declined"),
                ft.dropdown.Option(AnimalStatus.RECOVERING, text="Recovering"),
                ft.dropdown.Option(AnimalStatus.INJURED, text="Injured"),
                ft.dropdown.Option(AnimalStatus.ADOPTED, text="Adopted"),
                ft.dropdown.Option(AnimalStatus.REMOVED, text="Deleted"),
            ],
            on_change=lambda e: self._on_filter(page, e.control.value),
            border_radius=8,
        )

        search_field = create_form_text_field(
            hint_text="Search by name or breed...",
            prefix_icon=ft.Icons.SEARCH,
            value=self.current_search,
            on_change=lambda e: self._on_search(page, e.control.value),
        )

        control_bar = create_page_control_bar(
            title="My Listings",
            search_field=search_field,
            filters=[status_filter],
            is_mobile=_mobile,
            page=page,
        )

        main_content = ft.Container(
            ft.Column(
                [
                    ft.Container(
                        ft.Column([
                            control_bar,
                            cards_container,
                        ], spacing=0, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        padding=responsive_padding(page),
                    )
                ],
                scroll=ft.ScrollMode.AUTO,
                expand=True,
            ),
            expand=True,
        )

        layout = create_responsive_layout(page, sidebar, main_content, drawer, title="My Listings")

        finish_page_loading(page, _gradient_ref, layout)

    def _on_filter(self, page, status_value: str) -> None:
        self._status_filter = status_value
        self.build(page)

    def _on_search(self, page, search_query: str) -> None:
        self.current_search = search_query
        self.build(page)


__all__ = ["MyListingsPage"]
