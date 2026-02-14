"""Authentication routes for login and signup."""
from __future__ import annotations

from typing import Any, Dict

import app_config
from .utils import clear_page


def render_login(page, params: Dict[str, Any]) -> None:
    """Render the login page."""
    from views.login_page import LoginPage
    LoginPage(db_path=app_config.DB_PATH).build(page)


def render_signup(page, params: Dict[str, Any]) -> None:
    """Render the signup page."""
    from views.signup_page import SignupPage
    SignupPage(db_path=app_config.DB_PATH).build(page)


def render_emergency_rescue(page, params: Dict[str, Any]) -> None:
    """Render the emergency rescue page (no login required)."""
    from views.emergency_rescue_page import EmergencyRescuePage
    EmergencyRescuePage(db_path=app_config.DB_PATH).build(page)


# ============================================================================
# AUTH ROUTES - Add new authentication routes here
# ============================================================================

ROUTES: Dict[str, Dict[str, Any]] = {
    "/": {
        "handler": render_login,
        "description": "Login page",
        "requires_auth": False,
        "allowed_roles": None,
    },
    "/signup": {
        "handler": render_signup,
        "description": "User registration page",
        "requires_auth": False,
        "allowed_roles": None,
    },
    "/emergency_rescue": {
        "handler": render_emergency_rescue,
        "description": "Emergency rescue report (no login required)",
        "requires_auth": False,
        "allowed_roles": None,
    },
}
