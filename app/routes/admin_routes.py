"""Admin routes for dashboard and management."""
from __future__ import annotations

from typing import Any, Dict

import app_config
from .utils import clear_page


def render_admin_dashboard(page, params: Dict[str, Any]) -> None:
    """Render the admin dashboard."""
    from views.admin_dashboard import AdminDashboard
    AdminDashboard().build(page)


def render_add_animal(page, params: Dict[str, Any]) -> None:
    """Render the add animal page."""
    from views.add_animal_page import AddAnimalPage
    AddAnimalPage(db_path=app_config.DB_PATH).build(page)


def render_edit_animal(page, params: Dict[str, Any]) -> None:
    """Render the edit animal page."""
    from views.edit_animal_page import EditAnimalPage
    EditAnimalPage(db_path=app_config.DB_PATH).build(page)


def render_adoption_requests(page, params: Dict[str, Any]) -> None:
    """Render the adoption requests list page (admin)."""
    from views.adoption_request_list_page import AdoptionRequestListPage
    AdoptionRequestListPage(db_path=app_config.DB_PATH).build(page, user_role="admin")


def render_charts(page, params: Dict[str, Any]) -> None:
    """Render the charts/analytics page."""
    from views.charts_page import ChartsPage
    ChartsPage(db_path=app_config.DB_PATH).build(page)


def render_hidden_items(page, params: Dict[str, Any]) -> None:
    """Render the hidden items management page."""
    from views.hidden_items_page import HiddenItemsPage
    HiddenItemsPage(db_path=app_config.DB_PATH).build(page)


def render_manage_records(page, params: Dict[str, Any]) -> None:
    """Render the combined manage records page (rescue missions, adoptions, hidden items)."""
    from views.manage_records_page import ManageRecordsPage
    # Parse tab parameter (0=Rescues, 1=Adoptions, 2=Hidden)
    tab = 0
    if "tab" in params:
        try:
            tab = int(params["tab"])
        except (ValueError, TypeError):
            pass
    ManageRecordsPage(db_path=app_config.DB_PATH).build(page, tab=tab)


def render_user_management(page, params: Dict[str, Any]) -> None:
    """Render the user management page."""
    from views.user_management_page import UserManagementPage
    UserManagementPage(db_path=app_config.DB_PATH).build(page)


def render_audit_logs(page, params: Dict[str, Any]) -> None:
    """Render the audit log viewer page."""
    from views.audit_log_page import AuditLogPage
    AuditLogPage(db_path=app_config.DB_PATH).build(page)


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
    "/manage_records": {
        "handler": render_manage_records,
        "description": "Manage rescue missions, adoption requests, and hidden items",
        "requires_auth": True,
        "allowed_roles": ["admin"],
    },
    "/user_management": {
        "handler": render_user_management,
        "description": "Manage user accounts",
        "requires_auth": True,
        "allowed_roles": ["admin"],
    },
    "/audit_logs": {
        "handler": render_audit_logs,
        "description": "View security audit logs",
        "requires_auth": True,
        "allowed_roles": ["admin"],
    },
}
