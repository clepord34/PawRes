"""Utility functions for components."""
from __future__ import annotations
from io import BytesIO
from datetime import datetime, date
from typing import Optional, Union, Tuple
import base64
import re

try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    plt = None

try:
    import phonenumbers
    from phonenumbers import NumberParseException
    PHONENUMBERS_AVAILABLE = True
except ImportError:
    PHONENUMBERS_AVAILABLE = False
    phonenumbers = None
    NumberParseException = Exception


# Regular expressions for contact validation
# Email pattern: standard email format
EMAIL_PATTERN = re.compile(
    r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
)

# Default region for phone number parsing (Philippines)
DEFAULT_PHONE_REGION = "PH"


def normalize_phone_number(phone: str, region: str = DEFAULT_PHONE_REGION) -> Optional[str]:
    """Normalize a phone number to E.164 international format.
    
    Uses the phonenumbers library for international support.
    All valid phone numbers are stored in E.164 format (e.g., +639171234567)
    to ensure uniqueness regardless of input format.
    
    Args:
        phone: The phone number string to normalize
        region: Default region code (ISO 3166-1 alpha-2) for numbers without country code
        
    Returns:
        Normalized phone number in E.164 format (e.g., "+639171234567") or None if invalid
        
    Examples:
        >>> normalize_phone_number("09171234567")
        '+639171234567'
        >>> normalize_phone_number("+639171234567")
        '+639171234567'
        >>> normalize_phone_number("639171234567")
        '+639171234567'
        >>> normalize_phone_number("(555) 123-4567", "US")
        '+15551234567'
    """
    if not phone:
        return None
    
    if not PHONENUMBERS_AVAILABLE:
        # Fallback: basic normalization for PH numbers only
        cleaned = re.sub(r'[-.\s()\+]', '', phone.strip())
        if cleaned.startswith('63') and len(cleaned) == 12:
            return f"+{cleaned}"
        elif cleaned.startswith('09') and len(cleaned) == 11:
            return f"+63{cleaned[1:]}"
        elif cleaned.startswith('9') and len(cleaned) == 10:
            return f"+63{cleaned}"
        return None
    
    try:
        # Parse the phone number
        parsed = phonenumbers.parse(phone.strip(), region)
        
        # Validate the number
        if not phonenumbers.is_valid_number(parsed):
            return None
        
        # Format to E.164 (international format with +)
        return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
    except NumberParseException:
        return None
    except Exception:
        return None


def format_phone_for_display(phone: str, region: str = DEFAULT_PHONE_REGION) -> str:
    """Format a phone number for human-readable display.
    
    Args:
        phone: The phone number (can be E.164 or local format)
        region: Default region for formatting
        
    Returns:
        Formatted phone number for display (e.g., "+63 917 123 4567") or original if can't format
    """
    if not phone:
        return ""
    
    if not PHONENUMBERS_AVAILABLE:
        return phone
    
    try:
        parsed = phonenumbers.parse(phone.strip(), region)
        if phonenumbers.is_valid_number(parsed):
            return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
        return phone
    except Exception:
        return phone


def is_valid_email(value: str) -> bool:
    """Check if the value is a valid email address.
    
    Args:
        value: The string to validate
        
    Returns:
        True if valid email format
    """
    if not value:
        return False
    return bool(EMAIL_PATTERN.match(value.strip()))


def is_valid_phone(value: str, region: str = DEFAULT_PHONE_REGION) -> bool:
    """Check if the value is a valid phone number.
    
    Uses the phonenumbers library for comprehensive international validation.
    Supports all countries and various input formats.
    
    Args:
        value: The string to validate
        region: Default region code for numbers without country code
        
    Returns:
        True if valid phone format
    """
    if not value:
        return False
    
    # Try to normalize - if successful, it's valid
    normalized = normalize_phone_number(value.strip(), region)
    return normalized is not None


def is_valid_contact(value: str) -> bool:
    """Check if the value is a valid email OR phone number.
    
    Args:
        value: The string to validate
        
    Returns:
        True if valid email or phone format
    """
    return is_valid_email(value) or is_valid_phone(value)


def validate_contact(value: str) -> Tuple[bool, str]:
    """Validate contact information and return result with message.
    
    Args:
        value: The contact string to validate
        
    Returns:
        Tuple of (is_valid, error_message). Error message is empty if valid.
    """
    if not value or not value.strip():
        return False, "Contact information is required."
    
    value = value.strip()
    
    if is_valid_email(value):
        return True, ""
    
    if is_valid_phone(value):
        return True, ""
    
    return False, "Please enter a valid email address or phone number (e.g., email@example.com or 09XXXXXXXXX)."


def get_contact_type(value: str) -> Optional[str]:
    """Determine if contact is email or phone.
    
    Args:
        value: The contact string
        
    Returns:
        'email', 'phone', or None if invalid
    """
    if not value:
        return None
    value = value.strip()
    if is_valid_email(value):
        return 'email'
    if is_valid_phone(value):
        return 'phone'
    return None


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


# ============================================================================
# Location/Coordinates Utilities
# ============================================================================

# Pattern to detect if a string looks like coordinates
COORDS_PATTERN = re.compile(
    r'^[-+]?\d{1,3}\.?\d*\s*[,\s]\s*[-+]?\d{1,3}\.?\d*$'
)


def is_coordinate_string(location: str) -> bool:
    """Check if a location string appears to be raw coordinates.
    
    Args:
        location: The location string to check
        
    Returns:
        True if the string looks like "lat, lng" coordinates
        
    Examples:
        >>> is_coordinate_string("14.5995, 120.9842")
        True
        >>> is_coordinate_string("123 Main St, Naga City")
        False
        >>> is_coordinate_string("14.5995°N, 120.9842°E")
        True
    """
    if not location:
        return False
    
    # Remove degree symbols and direction letters for checking
    cleaned = re.sub(r'[°NSEW]', '', location.strip())
    return bool(COORDS_PATTERN.match(cleaned))


def parse_coordinates_from_string(location: str) -> Optional[Tuple[float, float]]:
    """Extract latitude and longitude from a coordinate string.
    
    Args:
        location: A string like "14.5995, 120.9842" or "14.5995°N, 120.9842°E"
        
    Returns:
        Tuple of (latitude, longitude) or None if parsing fails
    """
    if not location:
        return None
    
    try:
        # Remove degree symbols and direction letters
        cleaned = re.sub(r'[°NSEW]', '', location.strip())
        
        # Split by comma or whitespace
        parts = re.split(r'[,\s]+', cleaned)
        if len(parts) >= 2:
            lat = float(parts[0].strip())
            lng = float(parts[1].strip())
            
            # Validate ranges
            if -90 <= lat <= 90 and -180 <= lng <= 180:
                return (lat, lng)
    except (ValueError, IndexError):
        pass
    
    return None


def format_coordinates_display(lat: float, lng: float, short: bool = False) -> str:
    """Format coordinates for human-readable display.
    
    Args:
        lat: Latitude value
        lng: Longitude value
        short: If True, use shorter format
        
    Returns:
        Formatted string like "14.60°N, 120.98°E"
        
    Examples:
        >>> format_coordinates_display(14.5995, 120.9842)
        '14.60°N, 120.98°E'
        >>> format_coordinates_display(-33.8688, 151.2093)
        '33.87°S, 151.21°E'
        >>> format_coordinates_display(14.5995, 120.9842, short=True)
        '14.60°N, 120.98°E'
    """
    lat_dir = "N" if lat >= 0 else "S"
    lng_dir = "E" if lng >= 0 else "W"
    
    if short:
        return f"{abs(lat):.2f}°{lat_dir}, {abs(lng):.2f}°{lng_dir}"
    else:
        return f"{abs(lat):.2f}°{lat_dir}, {abs(lng):.2f}°{lng_dir}"


def format_location_for_display(
    location: Optional[str], 
    latitude: Optional[float] = None, 
    longitude: Optional[float] = None,
    max_length: int = 50
) -> Tuple[str, Optional[str]]:
    """Format a location for display, handling both addresses and coordinates.
    
    This function provides a user-friendly display of location data:
    - If location is a readable address, returns it (truncated if needed)
    - If location looks like coordinates, formats them nicely
    - Returns coordinates as tooltip if available
    
    Args:
        location: The location string (address or coordinates)
        latitude: Optional latitude value
        longitude: Optional longitude value
        max_length: Maximum length before truncation
        
    Returns:
        Tuple of (display_text, tooltip_text)
        - display_text: The formatted location for display
        - tooltip_text: Additional info for tooltip (coords or full address)
        
    Examples:
        >>> format_location_for_display("123 Main St, Naga City", 14.5995, 120.9842)
        ('123 Main St, Naga City', 'Coordinates: 14.60°N, 120.98°E')
        
        >>> format_location_for_display("14.5995, 120.9842", 14.5995, 120.9842)
        ('📍 14.60°N, 120.98°E', None)
        
        >>> format_location_for_display("A very long address that exceeds the maximum length limit...")
        ('A very long address that exceeds the max...', 'Full: A very long address...')
    """
    if not location and latitude is None and longitude is None:
        return ("Unknown location", None)
    
    # If we have coordinates but no/coordinate-like location
    if latitude is not None and longitude is not None:
        coords_display = format_coordinates_display(latitude, longitude)
        
        if not location or is_coordinate_string(location):
            # Location is empty or just coordinates - show formatted coords
            return (f"📍 {coords_display}", None)
        else:
            # Location is a readable address
            if len(location) > max_length:
                truncated = location[:max_length-3] + "..."
                return (truncated, f"Full address: {location}\nCoordinates: {coords_display}")
            else:
                return (location, f"Coordinates: {coords_display}")
    
    # No coordinates, just location string
    if location:
        if is_coordinate_string(location):
            # Parse and format the coordinates
            coords = parse_coordinates_from_string(location)
            if coords:
                return (f"📍 {format_coordinates_display(coords[0], coords[1])}", None)
        
        # Regular address
        if len(location) > max_length:
            return (location[:max_length-3] + "...", f"Full address: {location}")
        return (location, None)
    
    return ("Unknown location", None)


__all__ = [
    "fig_to_base64",
    "is_matplotlib_available",
    "parse_date",
    "parse_datetime",
    "is_valid_email",
    "is_valid_phone",
    "is_valid_contact",
    "validate_contact",
    "get_contact_type",
    "normalize_phone_number",
    "format_phone_for_display",
    "DEFAULT_PHONE_REGION",
    # Location utilities
    "is_coordinate_string",
    "parse_coordinates_from_string",
    "format_coordinates_display",
    "format_location_for_display",
]
