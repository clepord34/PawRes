"""Adoption service for managing adoption requests."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from storage.database import Database
import app_config


class AdoptionService:
    def __init__(self, db: Optional[Database | str] = None, *, ensure_tables: bool = True) -> None:
        if isinstance(db, Database):
            self.db = db
        else:
            self.db = Database(db if isinstance(db, str) else app_config.DB_PATH)

        if ensure_tables:
            self.db.create_tables()

    def submit_request(self, user_id: int, animal_id: int, contact: str, reason: str, status: str = "pending") -> int:
        """Create an adoption request and return its id.

        `contact` should contain contact info (email/phone) and `reason` a short
        explanation. Both are stored in separate columns.
        """
        sql = "INSERT INTO adoption_requests (user_id, animal_id, contact, reason, status) VALUES (?, ?, ?, ?, ?)"
        rid = self.db.execute(sql, (user_id, animal_id, contact, reason, status))
        return rid

    def get_all_requests(self) -> List[Dict[str, Any]]:
        """Return all adoption requests ordered by most recent."""
        sql = """
            SELECT 
                ar.*,
                u.name as user_name,
                u.email as user_email,
                a.name as animal_name,
                a.species as animal_species
            FROM adoption_requests ar
            LEFT JOIN users u ON ar.user_id = u.id
            LEFT JOIN animals a ON ar.animal_id = a.id
            ORDER BY ar.request_date DESC
        """
        return self.db.fetch_all(sql)

    def get_user_requests(self, user_id: int) -> List[Dict[str, Any]]:
        """Return adoption requests submitted by `user_id`."""
        return self.db.fetch_all("SELECT * FROM adoption_requests WHERE user_id = ? ORDER BY request_date DESC", (user_id,))

    def update_status(self, request_id: int, status: str) -> bool:
        """Update the status of an adoption request. Returns True if updated."""
        existing = self.db.fetch_one("SELECT id FROM adoption_requests WHERE id = ?", (request_id,))
        if not existing:
            return False
        self.db.execute("UPDATE adoption_requests SET status = ? WHERE id = ?", (status, request_id))
        return True


__all__ = ["AdoptionService"]
