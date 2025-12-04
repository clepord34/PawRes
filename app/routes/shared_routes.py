"""Shared routes accessible by both admin and user."""
from __future__ import annotations

from typing import Any, Dict

import app_config
from .utils import clear_page


def render_animals_list(page, params: Dict[str, Any]) -> None:
    """Render the animals list page."""
    from views.animals_list_page import AnimalsListPage
    clear_page(page)
    user_role = "admin" if params.get("admin") == "1" else "user"
    AnimalsListPage(db_path=app_config.DB_PATH).build(page, user_role=user_role)
    page.update()


def render_rescue_missions(page, params: Dict[str, Any]) -> None:
    """Render the rescue missions list page."""
    from views.rescue_mission_list_page import RescueMissionListPage
    clear_page(page)
    user_role = "admin" if params.get("admin") == "1" else "user"
    RescueMissionListPage(db_path=app_config.DB_PATH).build(page, user_role=user_role)
    page.update()


def render_profile(page, params: Dict[str, Any]) -> None:
    """Render the profile page."""
    from views.profile_page import ProfilePage
    clear_page(page)
    ProfilePage(db_path=app_config.DB_PATH).build(page)
    page.update()


# ============================================================================
# SHARED ROUTES - Add routes accessible by both admin and user here
# ============================================================================

ROUTES: Dict[str, Dict[str, Any]] = {
    "/animals_list": {
        "handler": render_animals_list,
        "description": "List of all animals",
        "requires_auth": True,
        "allowed_roles": ["admin", "user"],
    },
    "/rescue_missions": {
        "handler": render_rescue_missions,
        "description": "List of rescue missions",
        "requires_auth": True,
        "allowed_roles": ["admin", "user"],
    },
    "/rescue_missions_list": {
        "handler": render_rescue_missions,
        "description": "Alias for rescue missions list",
        "requires_auth": True,
        "allowed_roles": ["admin", "user"],
    },
    "/profile": {
        "handler": render_profile,
        "description": "User profile management",
        "requires_auth": True,
        "allowed_roles": ["admin", "user"],
    },
}
