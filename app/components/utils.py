"""Utility functions for components."""
from __future__ import annotations
from io import BytesIO
import base64

try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    plt = None


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
]
