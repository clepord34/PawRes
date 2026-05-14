"""User preferences model matching the database schema."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Dict, Optional


@dataclass
class UserPreferences:
    """User preferences model matching the `user_preferences` table schema."""
    id: Optional[int] = None
    user_id: int = 0
    preferred_species: Optional[str] = None
    preferred_breeds: Optional[str] = None
    preferred_age_min: Optional[int] = None
    preferred_age_max: Optional[int] = None
    living_situation: Optional[str] = None
    activity_level: Optional[str] = None
    experience_level: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Return a dict representation."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UserPreferences":
        """Create a UserPreferences instance from a dictionary."""
        return cls(
            id=data.get("id"),
            user_id=data.get("user_id", 0),
            preferred_species=data.get("preferred_species"),
            preferred_breeds=data.get("preferred_breeds"),
            preferred_age_min=data.get("preferred_age_min"),
            preferred_age_max=data.get("preferred_age_max"),
            living_situation=data.get("living_situation"),
            activity_level=data.get("activity_level"),
            experience_level=data.get("experience_level"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )


__all__ = ["UserPreferences"]
