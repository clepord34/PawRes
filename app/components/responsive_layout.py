"""Responsive layout helpers for adaptive UI across screen sizes.

Provides utilities to build layouts that adapt from mobile (360px+)
to tablet (768px+) to desktop (992px+). Uses Flet v0.28.3 ResponsiveRow
with string breakpoint keys ("xs", "sm", "md", "lg", "xl").
"""
from __future__ import annotations
from typing import Optional

try:
    import flet as ft
except ImportError:
    ft = None

import app_config


# ---------------------------------------------------------------------------
# Breakpoint helpers
# ---------------------------------------------------------------------------

def get_breakpoint(page) -> str:
    """Return the current breakpoint name based on page width.

    Returns one of: "xs", "sm", "md", "lg", "xl", "xxl".
    """
    w = page.width or app_config.DEFAULT_WINDOW_WIDTH
    if w >= app_config.BREAKPOINT_XXL:
        return "xxl"
    if w >= app_config.BREAKPOINT_XL:
        return "xl"
    if w >= app_config.BREAKPOINT_LG:
        return "lg"
    if w >= app_config.BREAKPOINT_MD:
        return "md"
    if w >= app_config.BREAKPOINT_SM:
        return "sm"
    return "xs"


def is_mobile(page) -> bool:
    """True when the page width is below the sidebar-collapse threshold."""
    w = page.width or app_config.DEFAULT_WINDOW_WIDTH
    return w < app_config.SIDEBAR_COLLAPSE_WIDTH


def responsive_col(
    xs: int = 12,
    sm: Optional[int] = None,
    md: Optional[int] = None,
    lg: Optional[int] = None,
    xl: Optional[int] = None,
) -> dict:
    """Build a ``col`` dict for ``ft.ResponsiveRow`` children.

    Only includes keys whose value differs from the previous breakpoint so the
    dict stays compact.  Flet inherits the last defined value upward.
    """
    cols: dict = {"xs": xs}
    prev = xs
    for key, val in [("sm", sm), ("md", md), ("lg", lg), ("xl", xl)]:
        if val is not None and val != prev:
            cols[key] = val
            prev = val
    return cols


# ---------------------------------------------------------------------------
# Page-level responsive layout
# ---------------------------------------------------------------------------

def create_responsive_layout(page, sidebar, content, drawer=None, title="PawRes") -> object:
    """Build the top-level page layout that collapses the sidebar on mobile.

    On **desktop** (>= md):  ``ft.Row([sidebar, content])``
    On **mobile** (< md):    just ``content``, sidebar lives in *drawer*

    Args:
        page:    Flet page object.
        sidebar: The desktop sidebar ``ft.Container``.
        content: The main content area (should have ``expand=True``).
        drawer:  An ``ft.NavigationDrawer`` shown on mobile.  If *None* the
                 sidebar is always visible (no collapse).
        title:   AppBar title shown on mobile (default: "PawRes").
    """
    if ft is None:
        raise RuntimeError("Flet is required")

    mobile = is_mobile(page)

    if mobile and drawer is not None:
        # Attach drawer to the page so page.open(drawer) works
        page.drawer = drawer
        page.appbar = create_mobile_appbar(page, title, drawer)
        return content
    else:
        # Desktop — classic sidebar + content row
        try:
            if page.drawer:
                page.close(page.drawer)
        except Exception:
            pass
        page.drawer = None
        page.appbar = None
        return ft.Row([sidebar, content], spacing=0, expand=True)


def create_mobile_appbar(page, title: str = "PawRes", drawer=None) -> object:
    """Return an ``ft.AppBar`` with a hamburger icon for the navigation drawer.

    Only meaningful on mobile; on desktop callers should skip it.

    Args:
        page:   Flet page object.
        title:  AppBar title text.
        drawer: NavigationDrawer to open on hamburger tap.
    """
    if ft is None:
        raise RuntimeError("Flet is required")

    def _open_drawer(e):
        if drawer:
            page.open(drawer)

    return ft.AppBar(
        leading=ft.IconButton(
            ft.Icons.MENU,
            on_click=_open_drawer,
            icon_color=ft.Colors.WHITE,
        ),
        title=ft.Text(title, color=ft.Colors.WHITE, size=18, weight="w600"),
        bgcolor=ft.Colors.TEAL_700,
        center_title=False,
    )


# ---------------------------------------------------------------------------
# Responsive content padding helper
# ---------------------------------------------------------------------------

def responsive_padding(page) -> int:
    """Return content padding appropriate for the current breakpoint."""
    bp = get_breakpoint(page)
    if bp in ("xs", "sm"):
        return 12
    if bp == "md":
        return 20
    return 30  # lg, xl, xxl


__all__ = [
    "get_breakpoint",
    "is_mobile",
    "responsive_col",
    "create_responsive_layout",
    "create_mobile_appbar",
    "responsive_padding",
]
