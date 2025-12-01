"""AdoptionRequest model matching the database schema."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, Optional
from datetime import datetime

import app_config


@dataclass
class AdoptionRequest:
    """Adoption request model representing an adoption application.
    
    Matches the `adoption_requests` table schema exactly.
    """
    id: Optional[int] = None
    user_id: int = 0
    animal_id: Optional[int] = None  # Can be None if animal was deleted
    contact: str = ""
    reason: str = ""
    status: str = app_config.AdoptionStatus.PENDING
    request_date: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    notes: Optional[str] = None
    # Backup fields for when animal is deleted
    animal_name: Optional[str] = None
    animal_species: Optional[str] = None
    admin_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Return a dict representation."""
        return asdict(self)
    
    @property
    def is_pending(self) -> bool:
        """Check if the request is pending."""
        return (self.status or "").lower() == "pending"
    
    @property
    def is_approved(self) -> bool:
        """Check if the request was approved."""
        return (self.status or "").lower() == "approved"
    
    @property
    def is_denied(self) -> bool:
        """Check if the request was denied."""
        return (self.status or "").lower() == "denied"
    
    @property
    def animal_was_removed(self) -> bool:
        """Check if the associated animal was removed from system."""
        return self.animal_id is None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AdoptionRequest":
        """Create an AdoptionRequest instance from a dictionary."""
        return cls(
            id=data.get("id"),
            user_id=data.get("user_id", 0),
            animal_id=data.get("animal_id"),
            contact=data.get("contact", ""),
            reason=data.get("reason", ""),
            status=data.get("status", app_config.AdoptionStatus.PENDING),
            request_date=data.get("request_date"),
            updated_at=data.get("updated_at"),
            notes=data.get("notes"),
            animal_name=data.get("animal_name"),
            animal_species=data.get("animal_species"),
            admin_message=data.get("admin_message"),
        )


__all__ = ["AdoptionRequest"]

