"""Authentication routes for login and signup."""
from __future__ import annotations

from typing import Any, Dict

import app_config
from .utils import clear_page


def render_login(page, params: Dict[str, Any]) -> None:
    """Render the login page."""
    from views.login_page import LoginPage
    clear_page(page)
    LoginPage(db_path=app_config.DB_PATH).build(page)
    page.update()


def render_signup(page, params: Dict[str, Any]) -> None:
    """Render the signup page."""
    from views.signup_page import SignupPage
    clear_page(page)
    SignupPage(db_path=app_config.DB_PATH).build(page)
    page.update()


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
}
