"""Rescue mission state manager."""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from dataclasses import dataclass

from .base import StateManager
import app_config


@dataclass 
class RescueFilter:
    """Filter criteria for rescue missions."""
    status: Optional[str] = None
    user_id: Optional[int] = None
    has_coordinates: bool = False
    
    def matches(self, mission: Dict[str, Any]) -> bool:
        """Check if a mission matches this filter."""
        # Status filter
        if self.status and mission.get("status", "").lower() != self.status.lower():
            return False
        
        # User filter
        if self.user_id is not None and mission.get("user_id") != self.user_id:
            return False
        
        # Coordinates filter
        if self.has_coordinates:
            if mission.get("latitude") is None or mission.get("longitude") is None:
                return False
        
        return True


class RescueState(StateManager[Dict[str, Any]]):
    """Rescue mission state manager."""
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize rescue state.
        
        Args:
            db_path: Path to database file (defaults to app_config.DB_PATH)
        """
        initial_state = {
            "missions": [],
            "filtered_missions": [],
            "user_missions": [],
            "selected_mission": None,
            "filter": RescueFilter(),
            "is_loading": False,
            "error": None,
        }
        super().__init__(initial_state)
        
        self._db_path = db_path or app_config.DB_PATH
        self._service = None
        self._map_service = None
    
    def _get_service(self):
        """Get or create the RescueService instance."""
        if self._service is None:
            from services.rescue_service import RescueService
            self._service = RescueService(self._db_path)
        return self._service
    
    def _get_map_service(self):
        """Get or create the MapService instance."""
        if self._map_service is None:
            from services.map_service import MapService
            self._map_service = MapService()
        return self._map_service
    
    @property
    def missions(self) -> List[Dict[str, Any]]:
        """Get all missions."""
        return self.state.get("missions", [])
    
    @property
    def filtered_missions(self) -> List[Dict[str, Any]]:
        """Get filtered missions based on current filter."""
        return self.state.get("filtered_missions", [])
    
    @property
    def user_missions(self) -> List[Dict[str, Any]]:
        """Get missions for current user."""
        return self.state.get("user_missions", [])
    
    @property
    def selected_mission(self) -> Optional[Dict[str, Any]]:
        """Get currently selected mission."""
        return self.state.get("selected_mission")
    
    @property
    def current_filter(self) -> RescueFilter:
        """Get current filter settings."""
        return self.state.get("filter", RescueFilter())
    
    @property
    def is_loading(self) -> bool:
        """Check if missions are being loaded."""
        return self.state.get("is_loading", False)
    
    @property
    def error(self) -> Optional[str]:
        """Get current error message if any."""
        return self.state.get("error")
    
    @property
    def missions_with_coordinates(self) -> List[Dict[str, Any]]:
        """Get only missions that have geocoded coordinates."""
        return [
            m for m in self.missions 
            if m.get("latitude") is not None and m.get("longitude") is not None
        ]
    
    def load_missions(self) -> None:
        """Load all rescue missions from database."""
        self.patch_state({"is_loading": True, "error": None})
        
        try:
            service = self._get_service()
            missions = service.get_all_missions() or []
            
            # Apply current filter
            filtered = self._apply_filter(missions, self.current_filter)
            
            self.update_state({
                "missions": missions,
                "filtered_missions": filtered,
                "user_missions": self.state.get("user_missions", []),
                "selected_mission": self.state.get("selected_mission"),
                "filter": self.state.get("filter"),
                "is_loading": False,
                "error": None,
            })
            
            print(f"[DEBUG] RescueState: Loaded {len(missions)} missions")
            
        except Exception as e:
            print(f"[ERROR] RescueState: Failed to load missions: {e}")
            self.patch_state({"is_loading": False, "error": str(e)})
    
    def load_user_missions(self, user_id: int) -> None:
        """Load missions for a specific user.
        
        Args:
            user_id: ID of user to load missions for
        """
        self.patch_state({"is_loading": True, "error": None})
        
        try:
            service = self._get_service()
            missions = service.get_user_missions(user_id) or []
            
            self.patch_state({
                "user_missions": missions,
                "is_loading": False,
                "error": None,
            })
            
        except Exception as e:
            print(f"[ERROR] RescueState: Failed to load user missions: {e}")
            self.patch_state({"is_loading": False, "error": str(e)})
    
    def submit_rescue(
        self,
        user_id: int,
        location: str,
        animal_type: str,
        name: str,
        details: str,
        status: str = "pending",
        geocode: bool = True
    ) -> Optional[int]:
        """Submit a new rescue request.
        
        Args:
            user_id: ID of user submitting the request
            location: Location description or address
            animal_type: Type of animal (dog, cat, etc.)
            name: Reporter name
            details: Additional details
            status: Initial status
            geocode: Whether to geocode the location
        
        Returns:
            New mission ID if successful, None otherwise
        """
        try:
            latitude = None
            longitude = None
            
            # Try to geocode the location
            if geocode:
                map_service = self._get_map_service()
                coords = map_service.geocode_location(location)
                if coords:
                    latitude, longitude = coords
                    print(f"[DEBUG] RescueState: Geocoded '{location}' to ({latitude}, {longitude})")
            
            service = self._get_service()
            mission_id = service.submit_rescue_request(
                user_id=user_id,
                location=location,
                animal_type=animal_type,
                name=name,
                details=details,
                status=status,
                latitude=latitude,
                longitude=longitude,
            )
            
            # Reload missions to get fresh data
            self.load_missions()
            
            print(f"[DEBUG] RescueState: Submitted rescue mission ID={mission_id}")
            return mission_id
            
        except Exception as e:
            print(f"[ERROR] RescueState: Failed to submit rescue: {e}")
            self.patch_state({"error": str(e)})
            return None
    
    def update_status(self, mission_id: int, status: str) -> bool:
        """Update a mission's status.
        
        Args:
            mission_id: ID of mission to update
            status: New status value
        
        Returns:
            True if successful
        """
        try:
            service = self._get_service()
            success = service.update_rescue_status(mission_id, status)
            
            if success:
                # Reload missions to get fresh data
                self.load_missions()
                print(f"[DEBUG] RescueState: Updated mission {mission_id} status to '{status}'")
            
            return success
            
        except Exception as e:
            print(f"[ERROR] RescueState: Failed to update mission status: {e}")
            self.patch_state({"error": str(e)})
            return False
    
    def update_mission(self, mission_id: int, **fields) -> bool:
        """Update a mission's fields.
        
        Args:
            mission_id: ID of mission to update
            **fields: Fields to update (e.g., status='rescued')
        
        Returns:
            True if successful
        """
        # Handle status update specially
        if 'status' in fields and len(fields) == 1:
            return self.update_status(mission_id, fields['status'])
        
        try:
            service = self._get_service()
            # For now, we only support status updates
            if 'status' in fields:
                success = service.update_rescue_status(mission_id, fields['status'])
                if success:
                    self.load_missions()
                return success
            return False
            
        except Exception as e:
            print(f"[ERROR] RescueState: Failed to update mission: {e}")
            self.patch_state({"error": str(e)})
            return False
    
    def delete_mission(self, mission_id: int) -> bool:
        """Delete (close) a rescue mission.
        
        Args:
            mission_id: ID of mission to delete
        
        Returns:
            True if successful
        """
        try:
            service = self._get_service()
            success = service.delete_mission(mission_id)
            
            if success:
                # Reload missions to get fresh data
                self.load_missions()
                print(f"[DEBUG] RescueState: Deleted mission {mission_id}")
            
            return success
            
        except Exception as e:
            print(f"[ERROR] RescueState: Failed to delete mission: {e}")
            self.patch_state({"error": str(e)})
            return False
    
    def select_mission(self, mission_id: Optional[int]) -> None:
        """Select a mission by ID.
        
        Args:
            mission_id: ID of mission to select, or None to clear selection
        """
        if mission_id is None:
            self.patch_state({"selected_mission": None})
            return
        
        # Find mission in list
        mission = next(
            (m for m in self.missions if m.get("id") == mission_id),
            None
        )
        self.patch_state({"selected_mission": mission})
    
    def set_filter(self, filter_criteria: RescueFilter) -> None:
        """Apply a filter to missions.
        
        Args:
            filter_criteria: Filter settings
        """
        filtered = self._apply_filter(self.missions, filter_criteria)
        
        self.patch_state({
            "filtered_missions": filtered,
            "filter": filter_criteria,
        })
    
    def filter_by_status(self, status: str) -> None:
        """Filter missions by status.
        
        Args:
            status: Status to filter by
        """
        current = self.current_filter
        new_filter = RescueFilter(
            status=status,
            user_id=current.user_id,
            has_coordinates=current.has_coordinates
        )
        self.set_filter(new_filter)
    
    def filter_by_user(self, user_id: int) -> None:
        """Filter missions by user.
        
        Args:
            user_id: User ID to filter by
        """
        current = self.current_filter
        new_filter = RescueFilter(
            status=current.status,
            user_id=user_id,
            has_coordinates=current.has_coordinates
        )
        self.set_filter(new_filter)
    
    def clear_filter(self) -> None:
        """Clear all filters."""
        self.set_filter(RescueFilter())
    
    def _apply_filter(
        self,
        missions: List[Dict[str, Any]],
        filter_criteria: RescueFilter
    ) -> List[Dict[str, Any]]:
        """Apply filter criteria to mission list.
        
        Args:
            missions: List of missions
            filter_criteria: Filter to apply
        
        Returns:
            Filtered list of missions
        """
        if filter_criteria is None:
            return missions
        
        return [m for m in missions if filter_criteria.matches(m)]
    
    def get_stats(self) -> Dict[str, int]:
        """Get rescue mission statistics.
        
        Returns:
            Dict with counts by status
        """
        missions = self.missions
        
        ongoing_count = len([m for m in missions if (m.get("status") or "").lower() in ("pending", "on-going")])
        rescued_count = len([m for m in missions if (m.get("status") or "").lower() == "rescued"])
        
        return {
            "total": len(missions),
            "ongoing": ongoing_count,
            "rescued": rescued_count,
            "with_coordinates": len(self.missions_with_coordinates),
        }
