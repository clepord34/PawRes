"""Map service for geocoding and map generation."""
from __future__ import annotations

from typing import Optional, Tuple, List
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
    
    def __init__(self):
        """Initialize the map service."""
        if Nominatim is None:
            logger.warning("geopy not installed, geocoding will not work")
            self.geocoder = None
            self._geocode = None
            self._reverse = None
        else:
            # Initialize geocoder with a user agent and longer timeout
            self.geocoder = Nominatim(user_agent="pawres_rescue_app_v1", timeout=30)
            
            # Use rate limiter to respect Nominatim's 1 request/second policy
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
    
    def geocode_location(self, location: str) -> Optional[Tuple[float, float]]:
        """
        Convert a location string to latitude/longitude coordinates.
        
        Args:
            location: Address or location description
            
        Returns:
            Tuple of (latitude, longitude) or None if geocoding fails
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
            logger.error(f"Geocoding error for '{location}': {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error geocoding '{location}': {e}")
            return None
    
    def reverse_geocode(self, latitude: float, longitude: float) -> Optional[str]:
        """
        Convert latitude/longitude coordinates to a human-readable address.
        
        Args:
            latitude: The latitude coordinate
            longitude: The longitude coordinate
            
        Returns:
            Address string or None if reverse geocoding fails
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
            logger.error(f"Reverse geocoding error for ({latitude}, {longitude}): {e}")
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
    
    def create_map_with_markers(self, missions: List[dict], center: Optional[Tuple[float, float]] = None, zoom: Optional[float] = None, is_admin: bool = False):
        """
        Create a Flet Map control with markers for rescue missions.
        
        Args:
            missions: List of mission dicts with id, location, latitude, longitude, status, notes
            center: Optional center coordinates (lat, lng)
            zoom: Optional zoom level
            is_admin: If True, show sensitive info (reporter, contact, source) in tooltip
            
        Returns:
            ft.Map control with marker layers
        """
        try:
            import flet as ft
            from flet_map import Map, MarkerLayer, Marker, MapLatitudeLongitude, TileLayer, MapInteractionConfiguration, MapInteractiveFlag
        except ImportError:
            logger.error("flet or flet-map not installed")
            return None
        
        # Filter missions that have coordinates AND are not removed (spam/invalid) or cancelled
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
                # Use default center
                center = self.DEFAULT_CENTER
        
        # Create markers for each mission
        markers = []
        for mission in missions_with_coords:
            lat = mission['latitude']
            lng = mission['longitude']
            status = mission.get('status', 'pending')
            location = mission.get('location', 'Unknown location')
            notes = mission.get('notes', '') or ''
            mission_id = mission.get('id', 0)
            
            # Use new structured columns (fallback to parsing notes for legacy data)
            reporter_name = mission.get('reporter_name') or "Anonymous"
            reporter_phone = mission.get('reporter_phone') or ""
            animal_type = mission.get('animal_type') or "Animal"
            urgency = (mission.get('urgency') or 'medium').capitalize()
            description = notes[:50] + "..." if len(notes) > 50 else notes
            
            # Determine if this is an emergency submission (user_id is None)
            is_emergency = mission.get('user_id') is None
            
            # For legacy data, try to parse from notes if columns are empty
            if not mission.get('urgency'):
                for line in notes.split('\n'):
                    line = line.strip()
                    if line.startswith('[Urgency:'):
                        # Extract urgency from "[Urgency: High - Immediate help needed]"
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
            
            # Format status for display
            status_display = status.replace('_', ' ').title()
            
            # Get animal emoji based on type
            animal_emoji = self._get_animal_emoji(animal_type)
            
            # Build tooltip with all relevant info
            tooltip_lines = [
                f"{animal_emoji} {animal_type}",
                f"📍 {location[:40]}..." if len(location) > 40 else f"📍 {location}",
                f"⚡ Urgency: {urgency}",
                f"📋 Status: {status_display}",
            ]
            if description:
                tooltip_lines.append(f"📝 {description}")
            
            # Admin-only section with separator
            if is_admin:
                tooltip_lines.append("───────────────────")
                # Source line
                if is_emergency:
                    tooltip_lines.append("🚨 Source: Emergency")
                else:
                    tooltip_lines.append("👨 Source: User")
                # Reporter and contact
                tooltip_lines.append(f"👤 Reporter: {reporter_name}")
                if reporter_phone:
                    tooltip_lines.append(f"📞 Contact: {reporter_phone}")
            
            tooltip_text = "\n".join(tooltip_lines)
            
            # Create marker with styled container
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
        
        # Create marker layer
        marker_layer = MarkerLayer(markers=markers)
        
        # Create tile layer (base map from OpenStreetMap)
        tile_layer = TileLayer(
            url_template="https://tile.openstreetmap.org/{z}/{x}/{y}.png",
            max_zoom=19,
        )
        
        # Create a reference to update the map's interaction configuration on click
        map_ref = ft.Ref[Map]()
        
        def on_map_tap(e):
            """Enable map interactions when user clicks on the map."""
            if map_ref.current:
                map_ref.current.interaction_configuration = MapInteractionConfiguration(
                    flags=MapInteractiveFlag.ALL
                )
                map_ref.current.update()
        
        # Create the map with both tile layer and marker layer
        # Initially disable interactions - user must click to enable drag/zoom
        map_control = Map(
            ref=map_ref,
            initial_center=MapLatitudeLongitude(center[0], center[1]),
            initial_zoom=zoom or self.DEFAULT_ZOOM,
            interaction_configuration=MapInteractionConfiguration(
                flags=MapInteractiveFlag.NONE  # Disabled until user clicks
            ),
            on_tap=on_map_tap,  # Enable interactions on click
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