"""Route registry package for the Paw Rescue application."""
from __future__ import annotations

from typing import Any, Callable, Dict, Optional, TYPE_CHECKING
from urllib.parse import urlparse, parse_qs

if TYPE_CHECKING:
    import flet as ft

# Type alias for route handler functions
RouteHandler = Callable[["ft.Page", Dict[str, Any]], None]


# ===========================================================================
# SHARED UTILITIES - Used by all route sub-modules
# These MUST be defined before importing the sub-modules to avoid circular imports
# ===========================================================================

def _clear(page) -> None:
    """Clear all controls from the page."""
    page.controls.clear()
    page.update()


def _extract_query_params(route: str) -> Dict[str, str]:
    """Extract query parameters from a route string.
    
    Args:
        route: The full route string (e.g., "/animals_list?admin=1")
    
    Returns:
        Dictionary of query parameter key-value pairs
    """
    parsed = urlparse(route)
    query_params = parse_qs(parsed.query)
    # Convert lists to single values for convenience
    return {k: v[0] if v else "" for k, v in query_params.items()}


# ===========================================================================
# IMPORT ROUTES FROM SUB-MODULES
# Each sub-module defines a ROUTES dictionary that gets merged here
# ===========================================================================

from .auth_routes import ROUTES as AUTH_ROUTES
from .admin_routes import ROUTES as ADMIN_ROUTES
from .user_routes import ROUTES as USER_ROUTES
from .shared_routes import ROUTES as SHARED_ROUTES


# Combine all route registries
ROUTE_REGISTRY: Dict[str, Dict[str, Any]] = {}
ROUTE_REGISTRY.update(AUTH_ROUTES)
ROUTE_REGISTRY.update(ADMIN_ROUTES)
ROUTE_REGISTRY.update(USER_ROUTES)
ROUTE_REGISTRY.update(SHARED_ROUTES)


def get_route_handler(route_path: str) -> Optional[Dict[str, Any]]:
    """Get the route configuration for a given path.
    
    Args:
        route_path: The route path without query parameters
    
    Returns:
        Route configuration dict or None if not found
    """
    return ROUTE_REGISTRY.get(route_path)


def get_all_routes() -> Dict[str, Dict[str, Any]]:
    """Get all registered routes.
    
    Returns:
        Copy of the route registry
    """
    return ROUTE_REGISTRY.copy()


def list_routes_by_role(role: str) -> list[str]:
    """List all routes accessible by a given role.
    
    Args:
        role: The user role ('admin' or 'user')
    
    Returns:
        List of route paths accessible by the role
    """
    routes = []
    for path, config in ROUTE_REGISTRY.items():
        allowed = config.get("allowed_roles")
        if allowed is None or role in allowed:
            routes.append(path)
    return routes


__all__ = [
    "_clear",
    "_extract_query_params",
    "get_route_handler",
    "get_all_routes",
    "list_routes_by_role",
    "ROUTE_REGISTRY",
]
