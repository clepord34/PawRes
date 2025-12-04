"""User model matching the database schema."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, Optional
from datetime import datetime


@dataclass
class User:
    """User model matching the `users` table schema."""
    id: Optional[int] = None
    name: str = ""
    email: str = ""
    phone: Optional[str] = None
    password_hash: Optional[str] = None
    password_salt: Optional[str] = None
    oauth_provider: Optional[str] = None
    profile_picture: Optional[str] = None
    role: str = "user"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def to_dict(self, include_sensitive: bool = False) -> Dict[str, Any]:
        """Return dict representation (excludes password fields by default)."""
        data = asdict(self)
        if not include_sensitive:
            data.pop("password_hash", None)
            data.pop("password_salt", None)
        return data
    
    @property
    def is_admin(self) -> bool:
        """Check if user has admin role."""
        return self.role == "admin"
    
    @property
    def is_oauth_user(self) -> bool:
        """Check if user logged in via OAuth."""
        return self.oauth_provider is not None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "User":
        """Create a User instance from a dictionary."""
        return cls(
            id=data.get("id"),
            name=data.get("name", ""),
            email=data.get("email", ""),
            phone=data.get("phone"),
            password_hash=data.get("password_hash"),
            password_salt=data.get("password_salt"),
            oauth_provider=data.get("oauth_provider"),
            profile_picture=data.get("profile_picture"),
            role=data.get("role", "user"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )


__all__ = ["User"]

