"""Admin routes for dashboard and management."""
from __future__ import annotations

from typing import Any, Dict

import app_config
from .utils import clear_page


def render_admin_dashboard(page, params: Dict[str, Any]) -> None:
    """Render the admin dashboard."""
    from views.admin_dashboard import AdminDashboard
    clear_page(page)
    AdminDashboard().build(page)
    page.update()


def render_add_animal(page, params: Dict[str, Any]) -> None:
    """Render the add animal page."""
    from views.add_animal_page import AddAnimalPage
    clear_page(page)
    AddAnimalPage(db_path=app_config.DB_PATH).build(page)
    page.update()


def render_edit_animal(page, params: Dict[str, Any]) -> None:
    """Render the edit animal page."""
    from views.edit_animal_page import EditAnimalPage
    clear_page(page)
    EditAnimalPage(db_path=app_config.DB_PATH).build(page)
    page.update()


def render_adoption_requests(page, params: Dict[str, Any]) -> None:
    """Render the adoption requests list page (admin)."""
    from views.adoption_request_list_page import AdoptionRequestListPage
    clear_page(page)
    AdoptionRequestListPage(db_path=app_config.DB_PATH).build(page, user_role="admin")
    page.update()


def render_charts(page, params: Dict[str, Any]) -> None:
    """Render the charts/analytics page."""
    from views.charts_page import ChartsPage
    clear_page(page)
    ChartsPage(db_path=app_config.DB_PATH).build(page)
    page.update()


def render_hidden_items(page, params: Dict[str, Any]) -> None:
    """Render the hidden items management page."""
    from views.hidden_items_page import HiddenItemsPage
    clear_page(page)
    HiddenItemsPage(db_path=app_config.DB_PATH).build(page)
    page.update()


# ============================================================================
# ADMIN ROUTES - Add new admin routes here
# ============================================================================

ROUTES: Dict[str, Dict[str, Any]] = {
    "/admin": {
        "handler": render_admin_dashboard,
        "description": "Admin dashboard",
        "requires_auth": True,
        "allowed_roles": ["admin"],
    },
    "/add_animal": {
        "handler": render_add_animal,
        "description": "Add a new animal to the system",
        "requires_auth": True,
        "allowed_roles": ["admin"],
    },
    "/edit_animal": {
        "handler": render_edit_animal,
        "description": "Edit an existing animal",
        "requires_auth": True,
        "allowed_roles": ["admin"],
    },
    "/adoption_requests": {
        "handler": render_adoption_requests,
        "description": "View and manage adoption requests",
        "requires_auth": True,
        "allowed_roles": ["admin"],
    },
    "/charts": {
        "handler": render_charts,
        "description": "Analytics and charts dashboard",
        "requires_auth": True,
        "allowed_roles": ["admin"],
    },
    "/hidden_items": {
        "handler": render_hidden_items,
        "description": "View and manage archived/removed items",
        "requires_auth": True,
        "allowed_roles": ["admin"],
    },
}
