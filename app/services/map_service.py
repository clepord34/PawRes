"""Map service for geocoding and map generation."""
from __future__ import annotations

from typing import Optional, Tuple, List, Callable
import logging
import time
import app_config
from app_config import RescueStatus

try:
    from geopy.geocoders import Nominatim
    from geopy.exc import GeocoderTimedOut, GeocoderServiceError
    from geopy.extra.rate_limiter import RateLimiter
except ImportError:
    Nominatim = None
    RateLimiter = None

logger = logging.getLogger(__name__)


class MapService:
    """Service for geocoding locations and creating maps."""
    
    # Default center and zoom from centralized config
    DEFAULT_CENTER = app_config.DEFAULT_MAP_CENTER
    DEFAULT_ZOOM = app_config.DEFAULT_MAP_ZOOM
    
    # Class-level timestamp to track last request across instances
    _last_request_time = 0
    _tiles_check_cache: Optional[bool] = None
    _tiles_check_cache_at: float = 0
    _geocode_check_cache: Optional[bool] = None
    _geocode_check_cache_at: float = 0
    
    def __init__(self):
        """Initialize the map service."""
        if Nominatim is None:
            logger.warning("geopy not installed, geocoding will not work")
            self.geocoder = None
            self._geocode = None
            self._reverse = None
        else:
            self.geocoder = Nominatim(user_agent="pawres_rescue_app_v1", timeout=30)
            
            if RateLimiter:
                self._geocode = RateLimiter(self.geocoder.geocode, min_delay_seconds=1.5)
                self._reverse = RateLimiter(self.geocoder.reverse, min_delay_seconds=1.5)
            else:
                self._geocode = self.geocoder.geocode
                self._reverse = self.geocoder.reverse
    
    def _wait_for_rate_limit(self):
        """Ensure we don't exceed rate limits."""
        current_time = time.time()
        time_since_last = current_time - MapService._last_request_time
        if time_since_last < 1.5:
            time.sleep(1.5 - time_since_last)
        MapService._last_request_time = time.time()
    
    def check_geocoding_available(self) -> bool:
        """Check if geocoding service is available (has internet connectivity).
        
        Returns:
            True if geocoding service is reachable, False otherwise
        """
        if not self.geocoder:
            return False
        
        current_time = time.time()
        if current_time - MapService._geocode_check_cache_at < 60 and MapService._geocode_check_cache is not None:
            return MapService._geocode_check_cache

        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            try:
                sock.connect(("nominatim.openstreetmap.org", 443))
                MapService._geocode_check_cache = True
                MapService._geocode_check_cache_at = current_time
                return True
            finally:
                sock.close()
        except (socket.error, socket.timeout, OSError):
            MapService._geocode_check_cache = False
            MapService._geocode_check_cache_at = current_time
            return False
    
    def check_map_tiles_available(self) -> bool:
        """Check if OpenStreetMap tile server is reachable.
        
        Returns:
            True if tile server is reachable, False otherwise
        """
        current_time = time.time()
        if current_time - MapService._tiles_check_cache_at < 60 and MapService._tiles_check_cache is not None:
            return MapService._tiles_check_cache

        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            try:
                sock.connect((app_config.MAP_TILE_HEALTHCHECK_HOST, 443))
                MapService._tiles_check_cache = True
                MapService._tiles_check_cache_at = current_time
                return True
            finally:
                sock.close()
        except (socket.error, socket.timeout, OSError):
            MapService._tiles_check_cache = False
            MapService._tiles_check_cache_at = current_time
            return False
    
    def geocode_location(self, location: str) -> Optional[Tuple[float, float]]:
        """
        Convert a location string to latitude/longitude coordinates.
        
        Args:
            location: Address or location description
            
        Returns:
            Tuple of (latitude, longitude) or None if geocoding fails.
            Returns None for network errors - use check_geocoding_available() 
            to distinguish between "not found" and "offline".
        """
        if not self.geocoder or not location or not location.strip():
            return None
        
        try:
            self._wait_for_rate_limit()
            # Try to geocode the location
            result = self._geocode(location) if self._geocode else None
            if result:
                logger.info(f"Geocoded '{location}' to ({result.latitude}, {result.longitude})")
                return (result.latitude, result.longitude)
            else:
                logger.warning(f"Could not geocode location: '{location}'")
                return None
        except (GeocoderTimedOut, GeocoderServiceError) as e:
            logger.error(f"Geocoding error (network issue) for '{location}': {e}")
            return None
        except Exception as e:
            error_str = str(e).lower()
            if any(x in error_str for x in ['network', 'connection', 'timeout', 'unreachable', 'socket']):
                logger.error(f"Geocoding network error for '{location}': {e}")
            else:
                logger.error(f"Unexpected error geocoding '{location}': {e}")
            return None
    
    def reverse_geocode(self, latitude: float, longitude: float) -> Optional[str]:
        """
        Convert latitude/longitude coordinates to a human-readable address.
        
        Args:
            latitude: The latitude coordinate
            longitude: The longitude coordinate
            
        Returns:
            Address string or None if reverse geocoding fails.
            Falls back gracefully to None when offline - caller should
            use coordinates as fallback display.
        """
        if not self.geocoder:
            return None
        
        try:
            self._wait_for_rate_limit()
            # Try to reverse geocode the coordinates
            result = self._reverse((latitude, longitude), language='en') if self._reverse else None
            if result:
                logger.info(f"Reverse geocoded ({latitude}, {longitude}) to '{result.address}'")
                return result.address
            else:
                logger.warning(f"Could not reverse geocode: ({latitude}, {longitude})")
                return None
        except (GeocoderTimedOut, GeocoderServiceError) as e:
            logger.error(f"Reverse geocoding error (network issue) for ({latitude}, {longitude}): {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error reverse geocoding ({latitude}, {longitude}): {e}")
            return None
    
    def _get_animal_emoji(self, animal_type: str) -> str:
        """Get emoji based on animal type."""
        animal_type_lower = (animal_type or "").lower()
        if "dog" in animal_type_lower:
            return "🐕"
        elif "cat" in animal_type_lower:
            return "🐈"
        else:  # Other
            return "🐾"
    
    def create_map_with_markers(
        self, 
        missions: List[dict], 
        center: Optional[Tuple[float, float]] = None, 
        zoom: Optional[float] = None, 
        is_admin: bool = False,
        locked: bool = True,
        on_unlock_request: Optional[Callable] = None,
    ):
        """
        Create a Flet Map control with markers for rescue missions.
        
        Args:
            missions: List of mission dicts with id, location, latitude, longitude, status, notes
            center: Optional center coordinates (lat, lng)
            zoom: Optional zoom level
            is_admin: If True, show sensitive info (reporter, contact, source) in tooltip
            locked: If True, disable scroll/zoom interactions (prevents accidental scrolling)
            on_unlock_request: Optional callback when user tries to interact with locked map
            
        Returns:
            ft.Map control with marker layers
        """
        try:
            import flet as ft
            from flet_map import (
                Map, MarkerLayer, Marker, MapLatitudeLongitude, TileLayer,
                MapInteractionConfiguration, MapInteractiveFlag
            )
        except ImportError:
            logger.error("flet or flet-map not installed")
            return None
        
        # Note: Archived missions SHOULD appear on map (they're closed but legitimate cases)
        missions_with_coords = [
            m for m in missions 
            if m.get('latitude') is not None 
            and m.get('longitude') is not None
            and not RescueStatus.is_removed(m.get('status') or '')
            and not RescueStatus.is_cancelled(m.get('status') or '')
        ]
        
        # Determine map center
        if center is None:
            if missions_with_coords:
                # Center on average of all mission locations
                avg_lat = sum(m['latitude'] for m in missions_with_coords) / len(missions_with_coords)
                avg_lng = sum(m['longitude'] for m in missions_with_coords) / len(missions_with_coords)
                center = (avg_lat, avg_lng)
            else:
                center = self.DEFAULT_CENTER
        
        markers = []
        for mission in missions_with_coords:
            lat = mission['latitude']
            lng = mission['longitude']
            status = mission.get('status', 'pending')
            location = mission.get('location', 'Unknown location')
            notes = mission.get('notes', '') or ''
            mission_id = mission.get('id', 0)
            
            reporter_name = mission.get('reporter_name') or "Anonymous"
            reporter_phone = mission.get('reporter_phone') or ""
            animal_type = mission.get('animal_type') or "Animal"
            urgency = (mission.get('urgency') or 'medium').capitalize()
            description = notes[:50] + "..." if len(notes) > 50 else notes
            
            # Determine if this is an emergency submission (user_id is None)
            is_emergency = mission.get('user_id') is None
            user_id = mission.get('user_id')
            
            # For legacy data, try to parse from notes if columns are empty
            if not mission.get('urgency'):
                for line in notes.split('\n'):
                    line = line.strip()
                    if line.startswith('[Urgency:'):
                        urgency_match = line.replace('[Urgency:', '').replace(']', '').strip()
                        if 'High' in urgency_match:
                            urgency = 'High'
                        elif 'Low' in urgency_match:
                            urgency = 'Low'
                        else:
                            urgency = 'Medium'
                        break
            
            # Determine marker color based on URGENCY (Red=High, Orange=Medium, Yellow=Low)
            urgency_lower = urgency.lower()
            if urgency_lower == 'high':
                color = ft.Colors.RED_500
                border_color = ft.Colors.RED_700
            elif urgency_lower == 'low':
                color = ft.Colors.YELLOW_700
                border_color = ft.Colors.YELLOW_900
            else:  # Medium (default)
                color = ft.Colors.DEEP_ORANGE_300
                border_color = ft.Colors.DEEP_ORANGE_500
            
            # Determine marker icon based on STATUS
            status_lower = status.lower()
            if status_lower == 'rescued':
                # Rescued - Check icon (unchanged)
                icon = ft.Icons.CHECK_CIRCLE
                # Override color to green for rescued
                color = ft.Colors.GREEN_600
                border_color = ft.Colors.GREEN_800
            elif status_lower == 'pending':
                # Pending - Exclamation Point icon
                icon = ft.Icons.PRIORITY_HIGH
            elif status_lower == 'failed':
                # Failed - Failed/Cancel icon
                icon = ft.Icons.CANCEL
            else:  # On-going or other
                # On-going - Paw icon
                icon = ft.Icons.PETS
            
            status_display = status.replace('_', ' ').title()
            
            animal_emoji = self._get_animal_emoji(animal_type)
            
            breed = mission.get("breed")
            
            tooltip_lines = [
                f"{animal_emoji} {animal_type}",
            ]
            if breed:
                tooltip_lines.append(f"🐕 Breed: {breed}")
            tooltip_lines.extend([
                f"📍 {location[:40]}..." if len(location) > 40 else f"📍 {location}",
                f"⚡ Urgency: {urgency}",
                f"📋 Status: {status_display}",
            ])
            if description:
                tooltip_lines.append(f"📝 {description}")
            
            # Admin-only section with separator
            if is_admin:
                tooltip_lines.append("───────────────────")
                # Source line with user ID if applicable
                if is_emergency:
                    tooltip_lines.append("🚨 Source: Emergency")
                else:
                    tooltip_lines.append(f"👤 Source: User #{user_id}")
                # Reporter and contact
                tooltip_lines.append(f"📢 Reporter: {reporter_name}")
                if reporter_phone:
                    tooltip_lines.append(f"📞 Contact: {reporter_phone}")
            
            tooltip_text = "\n".join(tooltip_lines)
            
            marker = Marker(
                content=ft.Container(
                    content=ft.Icon(
                        icon,
                        color=ft.Colors.WHITE,
                        size=18,
                    ),
                    width=36,
                    height=36,
                    bgcolor=color,
                    border_radius=18,
                    border=ft.border.all(3, border_color),
                    alignment=ft.alignment.center,
                    tooltip=tooltip_text,
                    shadow=ft.BoxShadow(
                        blur_radius=4,
                        spread_radius=1,
                        color=ft.Colors.with_opacity(0.3, ft.Colors.BLACK),
                        offset=(0, 2),
                    ),
                ),
                coordinates=MapLatitudeLongitude(lat, lng),
            )
            markers.append(marker)
        
        marker_layer = MarkerLayer(markers=markers)
        
        tile_layer = TileLayer(
            url_template=app_config.MAP_TILE_URL_TEMPLATE,
            max_zoom=app_config.MAP_TILE_MAX_ZOOM,
        )
        
        # Configure interaction based on locked state
        # When locked: disable scroll wheel zoom to prevent accidental zooming while scrolling page
        # Still allow tap on markers for tooltips
        if locked:
            # Only allow tapping (for marker tooltips), no zoom/drag/scroll
            interaction_flags = MapInteractiveFlag.NONE
        else:
            # Full interactivity when unlocked
            interaction_flags = MapInteractiveFlag.ALL
        
        interaction_config = MapInteractionConfiguration(
            flags=interaction_flags,
        )
        
        map_control = Map(
            initial_center=MapLatitudeLongitude(center[0], center[1]),
            initial_zoom=zoom or self.DEFAULT_ZOOM,
            interaction_configuration=interaction_config,
            layers=[tile_layer, marker_layer],
            expand=True,
        )
        
        return map_control
    
    def create_empty_map_placeholder(self, mission_count: int = 0) -> object:
        """
        Create a placeholder widget when the map cannot be loaded.
        
        Args:
            mission_count: Number of missions to display in the placeholder
            
        Returns:
            Flet Container with placeholder content
        """
        try:
            import flet as ft
        except ImportError:
            return None
        
        message = f"{mission_count} rescue mission(s)" if mission_count > 0 else "No rescue missions"
        
        return ft.Container(
            ft.Column([
                ft.Icon(ft.Icons.MAP_OUTLINED, size=64, color=ft.Colors.GREY_400),
                ft.Text("Map unavailable", size=16, color=ft.Colors.GREY_600, weight="w500"),
                ft.Text(message, size=12, color=ft.Colors.GREY_500),
                ft.Text("Install flet-map and geopy for map features", size=11, color=ft.Colors.GREY_400),
            ], horizontal_alignment="center", alignment="center", spacing=10),
            height=300,
            alignment=ft.alignment.center,
            bgcolor=ft.Colors.GREY_100,
            border_radius=8,
        )
    
    def create_offline_map_fallback(self, missions: List[dict], is_admin: bool = False) -> object:
        """
        Create an offline-friendly fallback widget showing mission locations as a styled list.
        
        Use this when map tiles are unavailable due to no internet connection.
        Shows mission locations with urgency indicators and status badges.
        
        Args:
            missions: List of mission dicts with location, status, urgency, etc.
            is_admin: If True, show admin-only info (user IDs, contacts)
            
        Returns:
            Flet Container with styled mission list
        """
        try:
            import flet as ft
        except ImportError:
            return None
        
        valid_missions = [
            m for m in missions 
            if m.get('latitude') is not None 
            and m.get('longitude') is not None
            and not RescueStatus.is_removed(m.get('status') or '')
            and not RescueStatus.is_cancelled(m.get('status') or '')
        ]
        
        if not valid_missions:
            return ft.Container(
                ft.Column([
                    ft.Icon(ft.Icons.WIFI_OFF, size=48, color=ft.Colors.GREY_400),
                    ft.Text("No Internet Connection", size=16, color=ft.Colors.GREY_600, weight="w600"),
                    ft.Text("Map tiles unavailable offline", size=13, color=ft.Colors.GREY_500),
                    ft.Container(height=8),
                    ft.Text("No rescue locations to display", size=12, color=ft.Colors.GREY_500),
                ], horizontal_alignment="center", alignment="center", spacing=8),
                height=300,
                alignment=ft.alignment.center,
                bgcolor=ft.Colors.GREY_100,
                border_radius=8,
            )
        
        location_cards = []
        for mission in valid_missions[:10]:  # Limit to 10 for performance
            mission_id = mission.get('id', 0)
            location = mission.get('location', 'Unknown location')
            status = mission.get('status', 'pending')
            urgency = (mission.get('urgency') or 'medium').lower()
            animal_type = mission.get('animal_type') or 'Animal'
            
            # Urgency color
            urgency_colors = {
                'high': (ft.Colors.RED_100, ft.Colors.RED_700, ft.Icons.PRIORITY_HIGH),
                'medium': (ft.Colors.ORANGE_100, ft.Colors.ORANGE_700, ft.Icons.PETS),
                'low': (ft.Colors.GREEN_100, ft.Colors.GREEN_700, ft.Icons.CHECK_CIRCLE),
            }
            bg_color, text_color, icon = urgency_colors.get(urgency, urgency_colors['medium'])
            
            # Status color
            status_normalized = RescueStatus.normalize(status)
            if status_normalized == RescueStatus.RESCUED:
                status_color = ft.Colors.GREEN_600
            elif status_normalized == RescueStatus.FAILED:
                status_color = ft.Colors.RED_600
            elif status_normalized == RescueStatus.ONGOING:
                status_color = ft.Colors.TEAL_600
            else:
                status_color = ft.Colors.ORANGE_600
            
            # Truncate location
            location_display = location[:45] + "..." if len(location) > 45 else location
            
            card_content = [
                ft.Row([
                    ft.Container(
                        ft.Icon(icon, color=text_color, size=16),
                        padding=6,
                        bgcolor=bg_color,
                        border_radius=8,
                    ),
                    ft.Column([
                        ft.Text(f"#{mission_id} - {animal_type}", size=12, weight="w600", color=ft.Colors.BLACK87),
                        ft.Text(location_display, size=11, color=ft.Colors.GREY_700,
                               tooltip=location if len(location) > 45 else None),
                    ], spacing=2, expand=True),
                    ft.Container(
                        ft.Text(RescueStatus.get_label(status), size=10, color=ft.Colors.WHITE, weight="w500"),
                        padding=ft.padding.symmetric(horizontal=8, vertical=4),
                        bgcolor=status_color,
                        border_radius=10,
                    ),
                ], spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            ]
            
            if is_admin:
                user_id = mission.get('user_id')
                source_text = "Emergency" if user_id is None else f"User #{user_id}"
                card_content.append(
                    ft.Row([
                        ft.Text(f"Source: {source_text}", size=10, color=ft.Colors.GREY_600),
                        ft.Text(f"Urgency: {urgency.capitalize()}", size=10, color=text_color),
                    ], spacing=15)
                )
            
            location_cards.append(
                ft.Container(
                    ft.Column(card_content, spacing=6),
                    padding=12,
                    bgcolor=ft.Colors.WHITE,
                    border_radius=8,
                    border=ft.border.all(1, ft.Colors.GREY_200),
                )
            )
        
        remaining = len(valid_missions) - 10
        if remaining > 0:
            location_cards.append(
                ft.Container(
                    ft.Text(f"+ {remaining} more location(s)", size=12, color=ft.Colors.GREY_600, 
                           text_align=ft.TextAlign.CENTER),
                    padding=10,
                )
            )
        
        return ft.Container(
            ft.Column([
                # Header
                ft.Row([
                    ft.Icon(ft.Icons.WIFI_OFF, size=20, color=ft.Colors.AMBER_700),
                    ft.Text("Offline Mode - Map Unavailable", size=14, weight="w600", color=ft.Colors.AMBER_800),
                ], spacing=8, alignment=ft.MainAxisAlignment.CENTER),
                ft.Divider(height=1, color=ft.Colors.GREY_300),
                ft.Text(f"{len(valid_missions)} rescue location(s) marked", size=12, color=ft.Colors.GREY_600,
                       text_align=ft.TextAlign.CENTER),
                ft.Container(height=8),
                # Scrollable list of locations
                ft.Container(
                    ft.Column(location_cards, spacing=8, scroll=ft.ScrollMode.AUTO),
                    height=280,
                    expand=True,
                ),
            ], spacing=10, horizontal_alignment="center"),
            padding=15,
            bgcolor=ft.Colors.GREY_100,
            border_radius=8,
            expand=True,
            border=ft.border.all(1, ft.Colors.AMBER_200),
        )