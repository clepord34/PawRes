"""RescueMission model matching the database schema."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, Optional
from datetime import datetime

import app_config


@dataclass
class RescueMission:
    """Rescue mission model representing a rescue request.
    
    Matches the `rescue_missions` table schema exactly.
    """
    id: Optional[int] = None
    user_id: Optional[int] = None  # Can be None for anonymous emergency reports
    animal_id: Optional[int] = None
    location: str = ""
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    mission_date: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    notes: Optional[str] = None  # Additional details/description
    status: str = app_config.RescueStatus.PENDING
    is_closed: bool = False  # Deprecated - kept for backwards compatibility
    admin_message: Optional[str] = None
    # Structured fields (previously embedded in notes)
    animal_type: str = ""  # e.g., "Dog", "Cat", "Other"
    animal_name: Optional[str] = None
    reporter_name: Optional[str] = None
    reporter_phone: Optional[str] = None
    urgency: str = app_config.Urgency.MEDIUM

    def to_dict(self) -> Dict[str, Any]:
        """Return a dict representation."""
        return asdict(self)
    
    @property
    def is_active(self) -> bool:
        """Check if the mission is active (pending or on-going)."""
        return app_config.RescueStatus.is_active(self.status)
    
    @property
    def has_coordinates(self) -> bool:
        """Check if the mission has geocoded coordinates."""
        return self.latitude is not None and self.longitude is not None
    
    @property
    def is_emergency(self) -> bool:
        """Check if this is a high-urgency emergency."""
        return self.urgency == app_config.Urgency.HIGH
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RescueMission":
        """Create a RescueMission instance from a dictionary."""
        return cls(
            id=data.get("id"),
            user_id=data.get("user_id"),
            animal_id=data.get("animal_id"),
            location=data.get("location", ""),
            latitude=data.get("latitude"),
            longitude=data.get("longitude"),
            mission_date=data.get("mission_date"),
            updated_at=data.get("updated_at"),
            notes=data.get("notes"),
            status=data.get("status", app_config.RescueStatus.PENDING),
            is_closed=bool(data.get("is_closed", 0)),
            admin_message=data.get("admin_message"),
            animal_type=data.get("animal_type", ""),
            animal_name=data.get("animal_name"),
            reporter_name=data.get("reporter_name"),
            reporter_phone=data.get("reporter_phone"),
            urgency=data.get("urgency", app_config.Urgency.MEDIUM),
        )


__all__ = ["RescueMission"]

