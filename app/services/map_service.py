"""Map service for geocoding and map generation."""
from __future__ import annotations

from typing import Optional, Tuple, List
import logging
import app_config

try:
    from geopy.geocoders import Nominatim
    from geopy.exc import GeocoderTimedOut, GeocoderServiceError
except ImportError:
    Nominatim = None

logger = logging.getLogger(__name__)


class MapService:
    """Service for geocoding locations and creating maps."""
    
    # Default center and zoom from centralized config
    DEFAULT_CENTER = app_config.DEFAULT_MAP_CENTER
    DEFAULT_ZOOM = app_config.DEFAULT_MAP_ZOOM
    
    def __init__(self):
        """Initialize the map service."""
        if Nominatim is None:
            logger.warning("geopy not installed, geocoding will not work")
            self.geocoder = None
        else:
            # Initialize geocoder with a user agent
            self.geocoder = Nominatim(user_agent="pawres_app", timeout=10)
    
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
            # Try to geocode the location
            result = self.geocoder.geocode(location)
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
            # Try to reverse geocode the coordinates
            result = self.geocoder.reverse((latitude, longitude), language='en')
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
    
    def create_map_with_markers(self, missions: List[dict], center: Optional[Tuple[float, float]] = None, zoom: Optional[float] = None):
        """
        Create a Flet Map control with markers for rescue missions.
        
        Args:
            missions: List of mission dicts with id, location, latitude, longitude, status, notes
            center: Optional center coordinates (lat, lng)
            zoom: Optional zoom level
            
        Returns:
            ft.Map control with marker layers
        """
        try:
            import flet as ft
            from flet_map import Map, MarkerLayer, Marker, MapLatitudeLongitude, TileLayer
        except ImportError:
            logger.error("flet or flet-map not installed")
            return None
        
        # Filter missions that have coordinates AND are not deleted/closed
        missions_with_coords = [
            m for m in missions 
            if m.get('latitude') is not None 
            and m.get('longitude') is not None
            and (m.get('status') or '').lower() != 'deleted'
            and '|closed' not in (m.get('status') or '').lower()
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
            
            # Parse notes to extract name, type, urgency, and details
            reporter_name = "Anonymous"
            animal_type = "Animal"
            urgency = "Medium"
            description = ""
            
            for line in notes.split('\n'):
                line = line.strip()
                if line.startswith('name:'):
                    reporter_name = line.replace('name:', '').strip()
                elif line.startswith('type:'):
                    animal_type = line.replace('type:', '').strip()
                elif line.startswith('[Urgency:'):
                    # Extract urgency from "[Urgency: High - Immediate help needed]"
                    urgency_match = line.replace('[Urgency:', '').replace(']', '').strip()
                    if 'High' in urgency_match:
                        urgency = 'High'
                    elif 'Low' in urgency_match:
                        urgency = 'Low'
                    else:
                        urgency = 'Medium'
                elif line and not line.startswith('['):
                    description = line[:50] + "..." if len(line) > 50 else line
            
            # Determine marker color and icon based on status and urgency
            if status.lower() == 'rescued':
                # Rescued - Green with checkmark
                color = ft.Colors.GREEN_600
                icon = ft.Icons.CHECK_CIRCLE
                border_color = ft.Colors.GREEN_800
            elif status.lower() == 'pending':
                # Pending - Color based on urgency
                if urgency == 'High':
                    color = ft.Colors.RED_600
                    icon = ft.Icons.PRIORITY_HIGH
                    border_color = ft.Colors.RED_800
                elif urgency == 'Low':
                    color = ft.Colors.BLUE_500
                    icon = ft.Icons.PETS
                    border_color = ft.Colors.BLUE_700
                else:  # Medium
                    color = ft.Colors.ORANGE_600
                    icon = ft.Icons.PETS
                    border_color = ft.Colors.ORANGE_800
            else:  # On-going or other
                if urgency == 'High':
                    color = ft.Colors.RED_500
                    icon = ft.Icons.WARNING
                    border_color = ft.Colors.RED_700
                elif urgency == 'Low':
                    color = ft.Colors.TEAL_500
                    icon = ft.Icons.PETS
                    border_color = ft.Colors.TEAL_700
                else:  # Medium
                    color = ft.Colors.ORANGE_500
                    icon = ft.Icons.PETS
                    border_color = ft.Colors.ORANGE_700
            
            # Format status for display
            status_display = status.replace('_', ' ').title()
            
            # Build tooltip with all relevant info
            tooltip_lines = [
                f"🐾 {animal_type}",
                f"📍 {location[:40]}..." if len(location) > 40 else f"📍 {location}",
                f"⚡ Urgency: {urgency}",
                f"📋 Status: {status_display}",
                f"👤 Reporter: {reporter_name}",
            ]
            if description:
                tooltip_lines.append(f"📝 {description}")
            
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
        
        # Create the map with both tile layer and marker layer
        map_control = Map(
            initial_center=MapLatitudeLongitude(center[0], center[1]),
            initial_zoom=zoom or self.DEFAULT_ZOOM,
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