"""Animal state manager."""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

from .base import StateManager
import app_config


@dataclass
class AnimalFilter:
    """Filter criteria for animals."""
    species: Optional[str] = None
    status: Optional[str] = None
    search_query: str = ""
    only_adoptable: bool = False
    
    def matches(self, animal: Dict[str, Any]) -> bool:
        """Check if an animal matches this filter."""
        # Species filter
        if self.species and animal.get("species", "").lower() != self.species.lower():
            return False
        
        # Status filter
        if self.status and animal.get("status", "").lower() != self.status.lower():
            return False
        
        # Search query
        if self.search_query:
            name = animal.get("name", "").lower()
            if self.search_query.lower() not in name:
                return False
        
        # Adoptable filter
        if self.only_adoptable:
            if animal.get("status", "").lower() not in app_config.ADOPTABLE_STATUSES:
                return False
        
        return True


class AnimalState(StateManager[Dict[str, Any]]):
    """Animal data state manager.
    
    Provides centralized management of animal data with:
    - Observable state changes for reactive UI
    - Filtering and search support
    - Integration with AnimalService for persistence
    
    Usage:
        animal_state = AnimalState()
        
        # Subscribe to animal list changes
        animal_state.subscribe(lambda data: rebuild_animal_grid(data))
        
        # Load animals
        animal_state.load_animals()
        
        # Add animal
        animal_state.add_animal({"name": "Buddy", "species": "dog", ...})
        
        # Filter animals
        animal_state.set_filter(AnimalFilter(species="dog"))
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize animal state.
        
        Args:
            db_path: Path to database file (defaults to app_config.DB_PATH)
        """
        initial_state = {
            "animals": [],
            "filtered_animals": [],
            "selected_animal": None,
            "filter": AnimalFilter(),
            "is_loading": False,
            "error": None,
        }
        super().__init__(initial_state)
        
        self._db_path = db_path or app_config.DB_PATH
        self._service = None  # Lazy load to avoid circular imports
    
    def _get_service(self):
        """Get or create the AnimalService instance."""
        if self._service is None:
            from services.animal_service import AnimalService
            self._service = AnimalService(self._db_path)
        return self._service
    
    @property
    def animals(self) -> List[Dict[str, Any]]:
        """Get all animals."""
        return self.state.get("animals", [])
    
    @property
    def filtered_animals(self) -> List[Dict[str, Any]]:
        """Get filtered animals based on current filter."""
        return self.state.get("filtered_animals", [])
    
    @property
    def selected_animal(self) -> Optional[Dict[str, Any]]:
        """Get currently selected animal."""
        return self.state.get("selected_animal")
    
    @property
    def current_filter(self) -> AnimalFilter:
        """Get current filter settings."""
        return self.state.get("filter", AnimalFilter())
    
    @property
    def is_loading(self) -> bool:
        """Check if animals are being loaded."""
        return self.state.get("is_loading", False)
    
    @property
    def error(self) -> Optional[str]:
        """Get current error message if any."""
        return self.state.get("error")
    
    def load_animals(self) -> None:
        """Load all animals from database."""
        self.patch_state({"is_loading": True, "error": None})
        
        try:
            service = self._get_service()
            animals = service.get_all_animals() or []
            
            # Apply current filter
            filtered = self._apply_filter(animals, self.current_filter)
            
            self.update_state({
                "animals": animals,
                "filtered_animals": filtered,
                "selected_animal": self.state.get("selected_animal"),
                "filter": self.state.get("filter"),
                "is_loading": False,
                "error": None,
            })
            
            
        except Exception as e:
            print(f"[ERROR] AnimalState: Failed to load animals: {e}")
            self.patch_state({"is_loading": False, "error": str(e)})
    
    def load_adoptable_animals(self) -> None:
        """Load only adoptable animals from database."""
        self.patch_state({"is_loading": True, "error": None})
        
        try:
            service = self._get_service()
            animals = service.get_adoptable_animals() or []
            
            self.update_state({
                "animals": animals,
                "filtered_animals": animals,
                "selected_animal": self.state.get("selected_animal"),
                "filter": AnimalFilter(only_adoptable=True),
                "is_loading": False,
                "error": None,
            })
            
        except Exception as e:
            print(f"[ERROR] AnimalState: Failed to load adoptable animals: {e}")
            self.patch_state({"is_loading": False, "error": str(e)})
    
    def add_animal(
        self,
        name: str,
        animal_type: str,
        age: Optional[int] = None,
        health_status: str = "unknown",
        photo: Optional[str] = None,
        **kwargs
    ) -> Optional[int]:
        """Add a new animal.
        
        Args:
            name: Animal name
            animal_type: Species (dog, cat, etc.)
            age: Age in years
            health_status: Health status string
            photo: Base64 encoded photo
            **kwargs: Additional fields (breed, description, etc.)
        
        Returns:
            New animal ID if successful, None otherwise
        """
        try:
            service = self._get_service()
            animal_id = service.add_animal(
                name=name,
                type=animal_type,
                age=age,
                health_status=health_status,
                photo=photo,
                **kwargs
            )
            
            # Reload animals to get fresh data
            self.load_animals()
            
            return animal_id
            
        except Exception as e:
            print(f"[ERROR] AnimalState: Failed to add animal: {e}")
            self.patch_state({"error": str(e)})
            return None
    
    def update_animal(self, animal_id: int, **fields) -> bool:
        """Update an existing animal.
        
        Args:
            animal_id: ID of animal to update
            **fields: Fields to update
        
        Returns:
            True if successful
        """
        try:
            service = self._get_service()
            success = service.update_animal(animal_id, **fields)
            
            if success:
                # Reload animals to get fresh data
                self.load_animals()
            
            return success
            
        except Exception as e:
            print(f"[ERROR] AnimalState: Failed to update animal: {e}")
            self.patch_state({"error": str(e)})
            return False
    
    def select_animal(self, animal_id: Optional[int]) -> None:
        """Select an animal by ID.
        
        Args:
            animal_id: ID of animal to select, or None to clear selection
        """
        if animal_id is None:
            self.patch_state({"selected_animal": None})
            return
        
        # Find animal in list
        animal = next(
            (a for a in self.animals if a.get("id") == animal_id),
            None
        )
        self.patch_state({"selected_animal": animal})
    
    def get_animal_by_id(self, animal_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific animal by ID.
        
        Args:
            animal_id: Animal ID
        
        Returns:
            Animal dict or None
        """
        # Try local cache first
        animal = next(
            (a for a in self.animals if a.get("id") == animal_id),
            None
        )
        
        if animal is None:
            # Fetch from database
            service = self._get_service()
            animal = service.get_animal_by_id(animal_id)
        
        return animal
    
    def set_filter(self, filter_criteria: AnimalFilter) -> None:
        """Apply a filter to animals.
        
        Args:
            filter_criteria: Filter settings
        """
        filtered = self._apply_filter(self.animals, filter_criteria)
        
        self.update_state({
            "animals": self.animals,
            "filtered_animals": filtered,
            "selected_animal": self.state.get("selected_animal"),
            "filter": filter_criteria,
            "is_loading": False,
            "error": None,
        })
    
    def clear_filter(self) -> None:
        """Clear all filters."""
        self.set_filter(AnimalFilter())
    
    def search(self, query: str) -> None:
        """Search animals by name.
        
        Args:
            query: Search string
        """
        current = self.current_filter
        new_filter = AnimalFilter(
            species=current.species,
            status=current.status,
            search_query=query,
            only_adoptable=current.only_adoptable
        )
        self.set_filter(new_filter)
    
    def _apply_filter(
        self,
        animals: List[Dict[str, Any]],
        filter_criteria: AnimalFilter
    ) -> List[Dict[str, Any]]:
        """Apply filter criteria to animal list.
        
        Args:
            animals: List of animals
            filter_criteria: Filter to apply
        
        Returns:
            Filtered list of animals
        """
        if filter_criteria is None:
            return animals
        
        return [a for a in animals if filter_criteria.matches(a)]

    # -------------------------------------------------------------------------
    # Archive / Remove / Restore / Permanent Delete Methods
    # -------------------------------------------------------------------------

    def archive_animal(self, animal_id: int, admin_id: int, note: Optional[str] = None) -> bool:
        """Archive an animal (soft-hide, still counts in analytics).
        
        Args:
            animal_id: ID of animal to archive
            admin_id: ID of admin performing the action
            note: Optional note explaining why
        
        Returns:
            True if successful
        """
        try:
            service = self._get_service()
            success = service.archive_animal(animal_id, admin_id, note)
            
            if success:
                self.load_animals()
            
            return success
            
        except Exception as e:
            print(f"[ERROR] AnimalState: Failed to archive animal: {e}")
            self.patch_state({"error": str(e)})
            return False

    def remove_animal(self, animal_id: int, admin_id: int, reason: str, 
                      cascade_adoptions: bool = True) -> Dict[str, Any]:
        """Remove an animal (soft-delete, excluded from analytics).
        
        If cascade_adoptions is True, also auto-denies pending adoption requests.
        
        Args:
            animal_id: ID of animal to remove
            admin_id: ID of admin performing the action
            reason: Reason for removal (spam, duplicate, test, etc.)
            cascade_adoptions: If True, auto-denies pending adoption requests
        
        Returns:
            Dict with 'success' bool and 'adoptions_affected' count
        """
        try:
            service = self._get_service()
            result = service.remove_animal(animal_id, admin_id, reason, cascade_adoptions)
            
            if result.get("success"):
                self.load_animals()
            
            return result
            
        except Exception as e:
            print(f"[ERROR] AnimalState: Failed to remove animal: {e}")
            self.patch_state({"error": str(e)})
            return {"success": False, "adoptions_affected": 0}

    def restore_animal(self, animal_id: int) -> bool:
        """Restore an archived or removed animal to its previous status.
        
        Args:
            animal_id: ID of animal to restore
        
        Returns:
            True if successful
        """
        try:
            service = self._get_service()
            success = service.restore_animal(animal_id)
            
            if success:
                self.load_animals()
            
            return success
            
        except Exception as e:
            print(f"[ERROR] AnimalState: Failed to restore animal: {e}")
            self.patch_state({"error": str(e)})
            return False

    def permanently_delete_animal(self, animal_id: int) -> Dict[str, Any]:
        """Permanently delete a REMOVED animal from the database.
        
        Only works on removed animals. Also deletes photo file.
        This cannot be undone.
        
        Args:
            animal_id: ID of animal to delete
        
        Returns:
            Dict with 'success' bool and 'photo_deleted' bool
        """
        try:
            service = self._get_service()
            result = service.permanently_delete_animal(animal_id)
            
            if result.get("success"):
                self.load_animals()
            
            return result
            
        except Exception as e:
            print(f"[ERROR] AnimalState: Failed to permanently delete animal: {e}")
            self.patch_state({"error": str(e)})
            return {"success": False, "photo_deleted": False}

    def load_active_animals(self) -> None:
        """Load only active (non-hidden) animals.
        
        Excludes archived and removed animals.
        """
        self.patch_state({"is_loading": True, "error": None})
        
        try:
            service = self._get_service()
            animals = service.get_active_animals() or []
            
            # Apply current filter
            filtered = self._apply_filter(animals, self.current_filter)
            
            self.update_state({
                "animals": animals,
                "filtered_animals": filtered,
                "selected_animal": self.state.get("selected_animal"),
                "filter": self.state.get("filter"),
                "is_loading": False,
                "error": None,
            })
            
            
        except Exception as e:
            print(f"[ERROR] AnimalState: Failed to load active animals: {e}")
            self.patch_state({"is_loading": False, "error": str(e)})

    def load_hidden_animals(self) -> List[Dict[str, Any]]:
        """Load hidden (archived/removed) animals.
        
        Returns:
            List of hidden animals
        """
        try:
            service = self._get_service()
            return service.get_hidden_animals() or []
            
        except Exception as e:
            print(f"[ERROR] AnimalState: Failed to load hidden animals: {e}")
            self.patch_state({"error": str(e)})
            return []
