"""Utility functions for components."""
from __future__ import annotations
from io import BytesIO
from datetime import datetime, date
from typing import Optional, Union
import base64

try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    plt = None


def parse_date(date_str: Optional[str], default: Optional[date] = None) -> Optional[date]:
    """Parse a date string safely, handling multiple formats.
    
    Handles ISO format strings from database (with or without time component).
    
    Args:
        date_str: Date string to parse (ISO format expected)
        default: Default value if parsing fails
        
    Returns:
        Parsed date object or default value
        
    Example:
        >>> parse_date("2024-01-15")
        datetime.date(2024, 1, 15)
        >>> parse_date("2024-01-15T10:30:00")
        datetime.date(2024, 1, 15)
        >>> parse_date(None)
        None
    """
    if not date_str:
        return default
    try:
        # Handle both date-only and datetime strings
        dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return dt.date()
    except (ValueError, AttributeError):
        return default


def parse_datetime(
    dt: Optional[Union[datetime, str]], 
    default: Optional[datetime] = None
) -> Optional[datetime]:
    """Parse a datetime value from various formats (datetime, string).
    
    Handles datetime objects, ISO format strings, and fallback formats.
    
    Args:
        dt: A datetime object, string, or None
        default: Default value if parsing fails
        
    Returns:
        Parsed datetime object or default value
        
    Example:
        >>> parse_datetime("2024-01-15T10:30:00")
        datetime.datetime(2024, 1, 15, 10, 30, 0)
        >>> parse_datetime(datetime.now())  # Returns as-is
        datetime.datetime(...)
    """
    if dt is None:
        return default
    if isinstance(dt, datetime):
        return dt
    try:
        return datetime.fromisoformat(str(dt).replace('Z', '+00:00'))
    except (ValueError, TypeError, AttributeError):
        try:
            return datetime.strptime(str(dt), "%Y-%m-%d %H:%M:%S")
        except (ValueError, TypeError):
            return default


def fig_to_base64(fig) -> str:
    """Convert a matplotlib figure to base64 string.
    
    Args:
        fig: Matplotlib figure object
    
    Returns:
        Base64 encoded PNG string
    """
    if not MATPLOTLIB_AVAILABLE:
        raise RuntimeError("matplotlib must be installed to convert figures")
    
    buf = BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=100)
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("ascii")


def is_matplotlib_available() -> bool:
    """Check if matplotlib is available."""
    return MATPLOTLIB_AVAILABLE


__all__ = [
    "fig_to_base64",
    "is_matplotlib_available",
    "parse_date",
    "parse_datetime",
]
