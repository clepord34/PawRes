"""Rescue mission service for submitting and managing rescue requests."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from storage.database import Database
import app_config


class RescueService:
    def __init__(self, db: Optional[Database | str] = None, *, ensure_tables: bool = True) -> None:
        if isinstance(db, Database):
            self.db = db
        else:
            self.db = Database(db if isinstance(db, str) else app_config.DB_PATH)

        if ensure_tables:
            self.db.create_tables()

    def submit_rescue_request(
        self,
        user_id: Optional[int],
        location: str,
        animal_id: Optional[int] = None,
        animal_type: Optional[str] = None,
        name: Optional[str] = None,
        details: Optional[str] = None,
        status: str = "pending",
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
    ) -> int:
        """Create a rescue mission record and return its id.

        If `animal_id` is not provided, `animal_type` and `name` are recorded
        inside the `notes` field along with `details`.
        """
        note_parts: List[str] = []
        if name:
            note_parts.append(f"name: {name}")
        if animal_type:
            note_parts.append(f"type: {animal_type}")
        if details:
            note_parts.append(details)
        notes = "\n".join(note_parts) if note_parts else None

        sql = "INSERT INTO rescue_missions (user_id, animal_id, location, latitude, longitude, notes, status) VALUES (?, ?, ?, ?, ?, ?, ?)"
        mid = self.db.execute(sql, (user_id, animal_id, location, latitude, longitude, notes, status))
        return mid

    def update_rescue_status(self, mission_id: int, status: str) -> bool:
        """Update the status for a mission. Returns True when updated."""
        existing = self.db.fetch_one("SELECT id FROM rescue_missions WHERE id = ?", (mission_id,))
        if not existing:
            return False
        self.db.execute("UPDATE rescue_missions SET status = ? WHERE id = ?", (status, mission_id))
        return True

    def get_all_missions(self) -> List[Dict[str, Any]]:
        """Return all missions ordered newest first."""
        rows = self.db.fetch_all("SELECT * FROM rescue_missions ORDER BY mission_date DESC")
        return rows

    def get_user_missions(self, user_id: int) -> List[Dict[str, Any]]:
        """Return missions submitted by a specific user, newest first."""
        rows = self.db.fetch_all("SELECT * FROM rescue_missions WHERE user_id = ? ORDER BY mission_date DESC", (user_id,))
        return rows


__all__ = ["RescueService"]
