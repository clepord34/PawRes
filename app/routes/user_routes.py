"""User routes for dashboard and forms."""
from __future__ import annotations

from typing import Any, Dict

import app_config
from .utils import clear_page


def render_user_dashboard(page, params: Dict[str, Any]) -> None:
    """Render the user dashboard."""
    from views.user_dashboard import UserDashboard
    clear_page(page)
    UserDashboard(db_path=app_config.DB_PATH).build(page)
    page.update()


def render_available_adoption(page, params: Dict[str, Any]) -> None:
    """Render the available animals for adoption page."""
    from views.available_adoption_page import AvailableAdoptionPage
    clear_page(page)
    AvailableAdoptionPage(db_path=app_config.DB_PATH).build(page)
    page.update()


def render_adoption_form(page, params: Dict[str, Any]) -> None:
    """Render the adoption form page."""
    from views.adoption_form_page import AdoptionFormPage
    clear_page(page)
    animal_id = None
    if "animal_id" in params:
        try:
            animal_id = int(params["animal_id"])
        except (ValueError, TypeError):
            pass
    AdoptionFormPage(db_path=app_config.DB_PATH).build(page, animal_id=animal_id)
    page.update()


def render_rescue_form(page, params: Dict[str, Any]) -> None:
    """Render the rescue submission form page."""
    from views.rescue_form_page import RescueFormPage
    clear_page(page)
    RescueFormPage(db_path=app_config.DB_PATH).build(page)
    page.update()


def render_check_status(page, params: Dict[str, Any]) -> None:
    """Render the check status page."""
    from views.check_status_page import CheckStatusPage
    clear_page(page)
    user_id = page.session.get("user_id")
    if not user_id:
        print("[WARNING] No user_id in session, redirecting to login")
        page.go("/")
        return
    CheckStatusPage(db_path=app_config.DB_PATH).build(page, user_id=user_id)
    page.update()


# ============================================================================
# USER ROUTES - Add new user routes here
# ============================================================================

ROUTES: Dict[str, Dict[str, Any]] = {
    "/user": {
        "handler": render_user_dashboard,
        "description": "User dashboard",
        "requires_auth": True,
        "allowed_roles": ["user"],
    },
    "/available_adoption": {
        "handler": render_available_adoption,
        "description": "Browse animals available for adoption",
        "requires_auth": True,
        "allowed_roles": ["user"],
    },
    "/adoption_form": {
        "handler": render_adoption_form,
        "description": "Submit an adoption request",
        "requires_auth": True,
        "allowed_roles": ["user"],
    },
    "/rescue_form": {
        "handler": render_rescue_form,
        "description": "Submit a rescue request",
        "requires_auth": True,
        "allowed_roles": ["user"],
    },
    "/check_status": {
        "handler": render_check_status,
        "description": "Check status of user's requests",
        "requires_auth": True,
        "allowed_roles": ["user"],
    },
}
