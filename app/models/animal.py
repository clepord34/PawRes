"""Animal model matching the database schema."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, Optional
from datetime import datetime

import app_config


@dataclass
class Animal:
    """Animal model representing an animal in the shelter.
    
    Matches the `animals` table schema exactly.
    """
    id: Optional[int] = None
    name: str = ""
    species: str = ""  # e.g., "Dog", "Cat", "Other"
    age: Optional[int] = None
    status: str = app_config.AnimalStatus.AVAILABLE
    intake_date: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    photo: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Return a dict representation."""
        return asdict(self)
    
    @property
    def is_adoptable(self) -> bool:
        """Check if the animal can be adopted."""
        return app_config.AnimalStatus.is_adoptable(self.status)
    
    @property
    def is_adopted(self) -> bool:
        """Check if the animal has been adopted."""
        return (self.status or "").lower() == app_config.AnimalStatus.ADOPTED
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Animal":
        """Create an Animal instance from a dictionary."""
        return cls(
            id=data.get("id"),
            name=data.get("name", ""),
            species=data.get("species", ""),
            age=data.get("age"),
            status=data.get("status", app_config.AnimalStatus.AVAILABLE),
            intake_date=data.get("intake_date"),
            updated_at=data.get("updated_at"),
            photo=data.get("photo"),
        )


__all__ = ["Animal"]

