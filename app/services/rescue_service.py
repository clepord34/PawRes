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
        """Return all active missions ordered newest first (excludes closed/deleted)."""
        rows = self.db.fetch_all("SELECT * FROM rescue_missions WHERE status NOT LIKE '%|Closed' AND status != 'Deleted' ORDER BY mission_date DESC")
        return rows

    def get_all_missions_for_analytics(self) -> List[Dict[str, Any]]:
        """Return ALL missions including closed/deleted for analytics and charts.
        
        This is used for historical data in charts like 'Rescued vs Adopted'.
        """
        rows = self.db.fetch_all("SELECT * FROM rescue_missions ORDER BY mission_date DESC")
        return rows

    def get_user_missions(self, user_id: int) -> List[Dict[str, Any]]:
        """Return missions submitted by a specific user, newest first."""
        rows = self.db.fetch_all("SELECT * FROM rescue_missions WHERE user_id = ? ORDER BY mission_date DESC", (user_id,))
        return rows

    def delete_mission(self, mission_id: int) -> bool:
        """Soft-delete a rescue mission by preserving original status with Closed suffix.
        
        This preserves the record for the user who reported it while hiding it
        from admin views. The user can still see their report history.
        Status is stored as 'OriginalStatus|Closed' (e.g., 'Rescued|Closed').
        
        Returns True if updated successfully.
        """
        existing = self.db.fetch_one("SELECT id, status FROM rescue_missions WHERE id = ?", (mission_id,))
        if not existing:
            return False
        # Store original status with |Closed suffix for display as "Status (Case Closed)"
        original_status = existing.get('status', 'On-going')
        # Don't double-close
        if '|Closed' in original_status:
            return True
        closed_status = f"{original_status}|Closed"
        self.db.execute("UPDATE rescue_missions SET status = ? WHERE id = ?", (closed_status, mission_id))
        return True

    def hard_delete_mission(self, mission_id: int) -> bool:
        """Permanently delete a rescue mission. Use with caution.
        
        Returns True if deleted successfully.
        """
        existing = self.db.fetch_one("SELECT id FROM rescue_missions WHERE id = ?", (mission_id,))
        if not existing:
            return False
        self.db.execute("DELETE FROM rescue_missions WHERE id = ?", (mission_id,))
        return True


__all__ = ["RescueService"]
