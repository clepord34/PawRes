"""Adoption request state manager."""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from dataclasses import dataclass

from .base import StateManager
import app_config


@dataclass
class AdoptionFilter:
    """Filter criteria for adoption requests."""
    status: Optional[str] = None
    user_id: Optional[int] = None
    animal_id: Optional[int] = None
    
    def matches(self, request: Dict[str, Any]) -> bool:
        """Check if a request matches this filter."""
        # Status filter
        if self.status and request.get("status", "").lower() != self.status.lower():
            return False
        
        # User filter
        if self.user_id is not None and request.get("user_id") != self.user_id:
            return False
        
        # Animal filter
        if self.animal_id is not None and request.get("animal_id") != self.animal_id:
            return False
        
        return True


class AdoptionState(StateManager[Dict[str, Any]]):
    """Adoption request state manager."""
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize adoption state.
        
        Args:
            db_path: Path to database file (defaults to app_config.DB_PATH)
        """
        initial_state = {
            "requests": [],
            "filtered_requests": [],
            "user_requests": [],
            "selected_request": None,
            "filter": AdoptionFilter(),
            "is_loading": False,
            "error": None,
        }
        super().__init__(initial_state)
        
        self._db_path = db_path or app_config.DB_PATH
        self._service = None
    
    def _get_service(self):
        """Get or create the AdoptionService instance."""
        if self._service is None:
            from services.adoption_service import AdoptionService
            self._service = AdoptionService(self._db_path)
        return self._service
    
    @property
    def requests(self) -> List[Dict[str, Any]]:
        """Get all adoption requests."""
        return self.state.get("requests", [])
    
    @property
    def filtered_requests(self) -> List[Dict[str, Any]]:
        """Get filtered requests based on current filter."""
        return self.state.get("filtered_requests", [])
    
    @property
    def user_requests(self) -> List[Dict[str, Any]]:
        """Get requests for current user."""
        return self.state.get("user_requests", [])
    
    @property
    def selected_request(self) -> Optional[Dict[str, Any]]:
        """Get currently selected request."""
        return self.state.get("selected_request")
    
    @property
    def current_filter(self) -> AdoptionFilter:
        """Get current filter settings."""
        return self.state.get("filter", AdoptionFilter())
    
    @property
    def is_loading(self) -> bool:
        """Check if requests are being loaded."""
        return self.state.get("is_loading", False)
    
    @property
    def error(self) -> Optional[str]:
        """Get current error message if any."""
        return self.state.get("error")
    
    @property
    def pending_requests(self) -> List[Dict[str, Any]]:
        """Get only pending requests."""
        return [
            r for r in self.requests 
            if (r.get("status") or "").lower() == "pending"
        ]
    
    @property
    def approved_requests(self) -> List[Dict[str, Any]]:
        """Get only approved requests."""
        return [
            r for r in self.requests 
            if (r.get("status") or "").lower() in ("approved", "adopted", "completed")
        ]
    
    def load_requests(self) -> None:
        """Load all adoption requests from database."""
        self.patch_state({"is_loading": True, "error": None})
        
        try:
            service = self._get_service()
            requests = service.get_all_requests() or []
            
            # Apply current filter
            filtered = self._apply_filter(requests, self.current_filter)
            
            self.update_state({
                "requests": requests,
                "filtered_requests": filtered,
                "user_requests": self.state.get("user_requests", []),
                "selected_request": self.state.get("selected_request"),
                "filter": self.state.get("filter"),
                "is_loading": False,
                "error": None,
            })
            
            print(f"[DEBUG] AdoptionState: Loaded {len(requests)} adoption requests")
            
        except Exception as e:
            print(f"[ERROR] AdoptionState: Failed to load requests: {e}")
            self.patch_state({"is_loading": False, "error": str(e)})
    
    def load_user_requests(self, user_id: int) -> None:
        """Load requests for a specific user.
        
        Args:
            user_id: ID of user to load requests for
        """
        self.patch_state({"is_loading": True, "error": None})
        
        try:
            service = self._get_service()
            requests = service.get_user_requests(user_id) or []
            
            self.patch_state({
                "user_requests": requests,
                "is_loading": False,
                "error": None,
            })
            
        except Exception as e:
            print(f"[ERROR] AdoptionState: Failed to load user requests: {e}")
            self.patch_state({"is_loading": False, "error": str(e)})
    
    def submit_request(
        self,
        user_id: int,
        animal_id: int,
        contact: str,
        reason: str,
        status: str = "pending"
    ) -> Optional[int]:
        """Submit a new adoption request.
        
        Args:
            user_id: ID of user submitting the request
            animal_id: ID of animal to adopt
            contact: Contact information
            reason: Reason for adoption
            status: Initial status
        
        Returns:
            New request ID if successful, None otherwise
        """
        try:
            service = self._get_service()
            request_id = service.submit_request(
                user_id=user_id,
                animal_id=animal_id,
                contact=contact,
                reason=reason,
                status=status,
            )
            
            # Reload requests to get fresh data
            self.load_requests()
            
            return request_id
            
        except Exception as e:
            print(f"[ERROR] AdoptionState: Failed to submit request: {e}")
            self.patch_state({"error": str(e)})
            return None
    
    def update_status(self, request_id: int, status: str) -> bool:
        """Update a request's status.
        
        Args:
            request_id: ID of request to update
            status: New status value (approved, denied, pending)
        
        Returns:
            True if successful
        """
        try:
            service = self._get_service()
            success = service.update_status(request_id, status)
            
            if success:
                # Reload requests to get fresh data
                self.load_requests()
            
            return success
            
        except Exception as e:
            print(f"[ERROR] AdoptionState: Failed to update request status: {e}")
            self.patch_state({"error": str(e)})
            return False
    
    def select_request(self, request_id: Optional[int]) -> None:
        """Select a request by ID.
        
        Args:
            request_id: ID of request to select, or None to clear selection
        """
        if request_id is None:
            self.patch_state({"selected_request": None})
            return
        
        # Find request in list
        request = next(
            (r for r in self.requests if r.get("id") == request_id),
            None
        )
        self.patch_state({"selected_request": request})
    
    def set_filter(self, filter_criteria: AdoptionFilter) -> None:
        """Apply a filter to requests.
        
        Args:
            filter_criteria: Filter settings
        """
        filtered = self._apply_filter(self.requests, filter_criteria)
        
        self.patch_state({
            "filtered_requests": filtered,
            "filter": filter_criteria,
        })
    
    def filter_by_status(self, status: str) -> None:
        """Filter requests by status.
        
        Args:
            status: Status to filter by
        """
        current = self.current_filter
        new_filter = AdoptionFilter(
            status=status,
            user_id=current.user_id,
            animal_id=current.animal_id
        )
        self.set_filter(new_filter)
    
    def filter_by_user(self, user_id: int) -> None:
        """Filter requests by user.
        
        Args:
            user_id: User ID to filter by
        """
        current = self.current_filter
        new_filter = AdoptionFilter(
            status=current.status,
            user_id=user_id,
            animal_id=current.animal_id
        )
        self.set_filter(new_filter)
    
    def clear_filter(self) -> None:
        """Clear all filters."""
        self.set_filter(AdoptionFilter())
    
    def _apply_filter(
        self,
        requests: List[Dict[str, Any]],
        filter_criteria: AdoptionFilter
    ) -> List[Dict[str, Any]]:
        """Apply filter criteria to request list.
        
        Args:
            requests: List of requests
            filter_criteria: Filter to apply
        
        Returns:
            Filtered list of requests
        """
        if filter_criteria is None:
            return requests
        
        return [r for r in requests if filter_criteria.matches(r)]
    
    def get_stats(self) -> Dict[str, int]:
        """Get adoption request statistics.
        
        Returns:
            Dict with counts by status
        """
        requests = self.requests
        
        pending_count = len([r for r in requests if (r.get("status") or "").lower() == "pending"])
        approved_count = len([r for r in requests if (r.get("status") or "").lower() in ("approved", "adopted", "completed")])
        denied_count = len([r for r in requests if (r.get("status") or "").lower() == "denied"])
        
        return {
            "total": len(requests),
            "pending": pending_count,
            "approved": approved_count,
            "denied": denied_count,
        }
