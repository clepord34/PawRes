"""Route utilities for all route handlers."""
from __future__ import annotations


def clear_page(page) -> None:
    """Clear all controls from the page.
    
    Args:
        page: The Flet page object
    """
    page.controls.clear()
    page.update()
