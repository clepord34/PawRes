"""User routes for dashboard and forms."""
from __future__ import annotations

from typing import Any, Dict

import app_config
from .utils import clear_page


def render_user_dashboard(page, params: Dict[str, Any]) -> None:
    """Render the user dashboard."""
    from views.user_dashboard import UserDashboard
    UserDashboard(db_path=app_config.DB_PATH).build(page)


def render_available_adoption(page, params: Dict[str, Any]) -> None:
    """Render the available animals for adoption page."""
    from views.available_adoption_page import AvailableAdoptionPage
    AvailableAdoptionPage(db_path=app_config.DB_PATH).build(page)


def render_adoption_form(page, params: Dict[str, Any]) -> None:
    """Render the adoption form page."""
    from views.adoption_form_page import AdoptionFormPage
    animal_id = None
    edit_request_id = None
    if "animal_id" in params:
        try:
            animal_id = int(params["animal_id"])
        except (ValueError, TypeError):
            pass
    if "edit_request_id" in params:
        try:
            edit_request_id = int(params["edit_request_id"])
        except (ValueError, TypeError):
            pass
    AdoptionFormPage(db_path=app_config.DB_PATH).build(page, animal_id=animal_id, edit_request_id=edit_request_id)


def render_rescue_form(page, params: Dict[str, Any]) -> None:
    """Render the rescue submission form page."""
    from views.rescue_form_page import RescueFormPage
    RescueFormPage(db_path=app_config.DB_PATH).build(page)


def render_check_status(page, params: Dict[str, Any]) -> None:
    """Render the check status page."""
    from views.check_status_page import CheckStatusPage
    user_id = page.session.get("user_id")
    if not user_id:
        print("[WARNING] No user_id in session, redirecting to login")
        page.go("/")
        return
    # Parse tab parameter (0=Rescues, 1=Adoptions)
    tab = 0
    if "tab" in params:
        try:
            tab = int(params["tab"])
        except (ValueError, TypeError):
            pass
    CheckStatusPage(db_path=app_config.DB_PATH).build(page, user_id=user_id, tab=tab)


def render_user_analytics(page, params: Dict[str, Any]) -> None:
    """Render the user analytics page."""
    from views.user_analytics_page import UserAnalyticsPage
    user_id = page.session.get("user_id")
    if not user_id:
        print("[WARNING] No user_id in session, redirecting to login")
        page.go("/")
        return
    UserAnalyticsPage(db_path=app_config.DB_PATH).build(page)


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
    "/user_analytics": {
        "handler": render_user_analytics,
        "description": "View personal analytics and statistics",
        "requires_auth": True,
        "allowed_roles": ["user"],
    },
}
