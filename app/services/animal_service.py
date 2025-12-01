"""Animal service for CRUD operations on animals."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from storage.database import Database
from storage.file_store import get_file_store, FileStoreError
from services.photo_service import get_photo_service
import app_config
from app_config import AnimalStatus, AdoptionStatus


class AnimalService:
    def __init__(self, db: Optional[Database | str] = None, *, ensure_tables: bool = True) -> None:
        """Create service with a Database instance or path.

        Args:
            db: Database instance or path to sqlite file. If None, defaults
                to DB_PATH from app_config.
            ensure_tables: if True the service will call `create_tables()` on
                the Database to ensure the `animals` table exists.
        """
        if isinstance(db, Database):
            self.db = db
        else:
            self.db = Database(db if isinstance(db, str) else app_config.DB_PATH)

        if ensure_tables:
            self.db.create_tables()
        
        self.file_store = get_file_store()
        self.photo_service = get_photo_service()

    def add_animal(
        self,
        name: str,
        type: str,
        age: Optional[int] = None,
        health_status: str = "unknown",
        breed: Optional[str] = None,
        description: Optional[str] = None,
        photo: Optional[str] = None,
    ) -> int:
        """Insert a new animal and return its id.

        Note: `type` maps to the `species` column in the DB; `health_status`
        maps to `status`. `photo` should be base64-encoded image data.
        """
        sql = (
            "INSERT INTO animals (name, species, breed, age, status, description, photo) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)"
        )
        last_id = self.db.execute(sql, (name, type, breed, age, health_status, description, photo))
        return last_id

    def get_all_animals(self) -> List[Dict[str, Any]]:
        """Return all animals as list of dicts (DB column names).

        The returned dicts use the DB column names (e.g., `species`). If you
        prefer model objects, convert using the `Animal` dataclass.
        """
        rows = self.db.fetch_all("SELECT * FROM animals ORDER BY id")
        return rows

    def get_all_animals_for_analytics(self) -> List[Dict[str, Any]]:
        """Return animals that count in analytics and charts.
        
        Excludes "removed" status items. Includes archived items (they preserve
        their original status in the compound format like "adopted|archived").
        
        Used for dashboard stats and animal distribution charts.
        """
        rows = self.db.fetch_all(
            "SELECT * FROM animals WHERE status != 'removed' ORDER BY id"
        )
        return rows

    def get_animal_by_id(self, animal_id: int) -> Optional[Dict[str, Any]]:
        """Return a single animal by id, or None if not found.

        The returned dict uses the DB column names (e.g., `species`).
        """
        return self.db.fetch_one("SELECT * FROM animals WHERE id = ?", (animal_id,))

    def update_animal(self, animal_id: int, **fields: Any) -> bool:
        """Update allowed fields for an animal. Returns True if updated.

        Allowed fields: `name`, `type` (mapped to `species`), `breed`,
        `age`, `health_status` (mapped to `status`), `description`, `photo`.
        """
        if not fields:
            return False

        # map input field names to DB column names
        mapping = {
            "type": "species",
            "health_status": "status",
            "name": "name",
            "breed": "breed",
            "age": "age",
            "description": "description",
            "photo": "photo",
        }

        set_clauses = []
        params: List[Any] = []
        for key, value in fields.items():
            col = mapping.get(key)
            if not col:
                # ignore unknown fields
                continue
            set_clauses.append(f"{col} = ?")
            params.append(value)

        if not set_clauses:
            return False

        params.append(animal_id)
        sql = f"UPDATE animals SET {', '.join(set_clauses)} WHERE id = ?"
        self.db.execute(sql, params)
        return True

    def get_adoptable_animals(self) -> List[Dict[str, Any]]:
        """Return animals considered adoptable.

        Uses ADOPTABLE_STATUSES from app_config to determine which
        animals are available for adoption.
        """
        adoptable_states = app_config.ADOPTABLE_STATUSES
        placeholders = ",".join(["?" for _ in adoptable_states])
        sql = f"SELECT * FROM animals WHERE status IN ({placeholders}) ORDER BY id"
        rows = self.db.fetch_all(sql, adoptable_states)
        return rows

    def update_animal_photo(self, animal_id: int, new_photo: str) -> bool:
        """Update an animal's photo, deleting the old photo file if it exists.
        
        Args:
            animal_id: The ID of the animal to update
            new_photo: New photo filename (from FileStore)
            
        Returns:
            True if the photo was updated successfully
        """
        if not new_photo:
            return False
        
        # Get existing animal to check for old photo
        existing = self.db.fetch_one("SELECT id, photo FROM animals WHERE id = ?", (animal_id,))
        if not existing:
            return False
        
        # Delete old photo file if it exists and is a filename (not base64)
        old_photo = existing.get('photo')
        if old_photo and not self.photo_service.is_base64(old_photo):
            try:
                self.file_store.delete_file(old_photo)
                print(f"[INFO] Deleted old photo file: {old_photo}")
            except FileStoreError as e:
                print(f"[WARN] Could not delete old photo file: {e}")
        
        sql = "UPDATE animals SET photo = ? WHERE id = ?"
        self.db.execute(sql, (new_photo, animal_id))
        return True

    def get_adoption_request_count(self, animal_id: int) -> int:
        """Get the count of adoption requests for an animal.
        
        Args:
            animal_id: The ID of the animal to check
            
        Returns:
            Number of adoption requests for this animal
        """
        result = self.db.fetch_one(
            "SELECT COUNT(*) as count FROM adoption_requests WHERE animal_id = ?",
            (animal_id,)
        )
        return result.get('count', 0) if result else 0

    def get_adoption_requests_summary(self, animal_id: int) -> Dict[str, Any]:
        """Get summary of adoption requests for an animal.
        
        Args:
            animal_id: The ID of the animal to check
            
        Returns:
            Dict with 'total', 'pending', 'approved', 'denied' counts
        """
        requests = self.db.fetch_all(
            "SELECT status FROM adoption_requests WHERE animal_id = ?",
            (animal_id,)
        )
        summary = {'total': 0, 'pending': 0, 'approved': 0, 'denied': 0, 'other': 0}
        for r in requests:
            status = (r.get('status') or '').lower()
            summary['total'] += 1
            if status == 'pending':
                summary['pending'] += 1
            elif status in ('approved', 'adopted', 'completed'):
                summary['approved'] += 1
            elif status in ('denied', 'rejected'):
                summary['denied'] += 1
            else:
                summary['other'] += 1
        return summary

    # -------------------------------------------------------------------------
    # Archive / Remove / Restore / Permanent Delete Methods
    # -------------------------------------------------------------------------

    def archive_animal(self, animal_id: int, admin_id: int, note: Optional[str] = None) -> bool:
        """Archive an animal (soft-hide, still counts in analytics).
        
        Status becomes "original_status|archived" to preserve original for analytics.
        Returns True if archived successfully.
        """
        existing = self.db.fetch_one(
            "SELECT id, status FROM animals WHERE id = ?",
            (animal_id,)
        )
        if not existing:
            return False
        
        current_status = existing.get("status", "")
        
        # Don't archive if already archived or removed
        if AnimalStatus.is_archived(current_status) or AnimalStatus.is_removed(current_status):
            return False
        
        # Create archived status (e.g., "adopted|archived")
        archived_status = AnimalStatus.make_archived(current_status)
        
        self.db.execute(
            """UPDATE animals
               SET status = ?, previous_status = ?, 
                   archived_at = ?, archived_by = ?, archive_note = ?,
                   updated_at = ?
               WHERE id = ?""",
            (archived_status, current_status, datetime.now(), admin_id, note,
             datetime.now(), animal_id)
        )
        return True

    def remove_animal(self, animal_id: int, admin_id: int, reason: str, 
                      cascade_adoptions: bool = True) -> Dict[str, Any]:
        """Remove an animal (soft-delete, excluded from analytics).
        
        Status becomes "removed". Use for spam, duplicates, test data, etc.
        
        Args:
            animal_id: ID of animal to remove
            admin_id: ID of admin performing the action
            reason: Reason for removal
            cascade_adoptions: If True, auto-denies pending adoption requests for this animal
        
        Returns:
            Dict with 'success' bool and 'adoptions_affected' count
        """
        existing = self.db.fetch_one(
            "SELECT id, status FROM animals WHERE id = ?",
            (animal_id,)
        )
        if not existing:
            return {"success": False, "adoptions_affected": 0}
        
        current_status = existing.get("status", "")
        
        # Don't remove if already removed
        if AnimalStatus.is_removed(current_status):
            return {"success": False, "adoptions_affected": 0}
        
        # Get base status (in case it's archived)
        base_status = AnimalStatus.get_base_status(current_status)
        
        # Handle cascade: auto-deny pending adoption requests for this animal
        adoptions_affected = 0
        if cascade_adoptions:
            # Count pending requests
            pending_result = self.db.fetch_one(
                f"""SELECT COUNT(*) as count FROM adoption_requests 
                    WHERE animal_id = ? AND LOWER(status) = '{AdoptionStatus.PENDING}'""",
                (animal_id,)
            )
            adoptions_affected = pending_result.get('count', 0) if pending_result else 0
            
            # Auto-deny pending requests
            if adoptions_affected > 0:
                self.db.execute(
                    f"""UPDATE adoption_requests 
                        SET status = '{AdoptionStatus.DENIED}', 
                            denial_reason = 'Animal has been removed from system',
                            updated_at = ?
                        WHERE animal_id = ? 
                        AND LOWER(status) = '{AdoptionStatus.PENDING}'""",
                    (datetime.now(), animal_id)
                )
        
        # Remove the animal
        self.db.execute(
            """UPDATE animals
               SET status = ?, previous_status = ?,
                   removed_at = ?, removed_by = ?, removal_reason = ?,
                   archived_at = NULL, archived_by = NULL, archive_note = NULL,
                   updated_at = ?
               WHERE id = ?""",
            (AnimalStatus.REMOVED, base_status, datetime.now(), admin_id, reason,
             datetime.now(), animal_id)
        )
        return {"success": True, "adoptions_affected": adoptions_affected}

    def restore_animal(self, animal_id: int) -> bool:
        """Restore an archived or removed animal to its previous status.
        
        Returns True if restored successfully.
        """
        existing = self.db.fetch_one(
            "SELECT id, status, previous_status FROM animals WHERE id = ?",
            (animal_id,)
        )
        if not existing:
            return False
        
        current_status = existing.get("status", "")
        
        # Only restore if hidden (archived or removed)
        if not AnimalStatus.is_hidden(current_status):
            return False
        
        # Restore to previous_status if available, otherwise extract from archived status
        previous = existing.get("previous_status")
        if not previous:
            previous = AnimalStatus.get_base_status(current_status)
        if not previous or previous == AnimalStatus.REMOVED:
            previous = AnimalStatus.HEALTHY  # Default fallback
        
        self.db.execute(
            """UPDATE animals
               SET status = ?, previous_status = NULL,
                   archived_at = NULL, archived_by = NULL, archive_note = NULL,
                   removed_at = NULL, removed_by = NULL, removal_reason = NULL,
                   updated_at = ?
               WHERE id = ?""",
            (previous, datetime.now(), animal_id)
        )
        return True

    def permanently_delete_animal(self, animal_id: int) -> Dict[str, Any]:
        """Permanently delete a REMOVED animal from the database.
        
        Only works on removed animals (not archived or active).
        Also deletes associated photo file if it exists.
        This cannot be undone.
        
        Returns:
            Dict with 'success' bool and 'photo_deleted' bool
        """
        existing = self.db.fetch_one(
            "SELECT id, status, photo FROM animals WHERE id = ?",
            (animal_id,)
        )
        if not existing:
            return {"success": False, "photo_deleted": False}
        
        # Only allow permanent deletion of removed items
        if not AnimalStatus.is_removed(existing.get("status", "")):
            return {"success": False, "photo_deleted": False}
        
        # Delete photo file if exists
        photo_deleted = False
        photo = existing.get('photo')
        if photo and not self.photo_service.is_base64(photo):
            try:
                self.file_store.delete_file(photo)
                photo_deleted = True
                print(f"[INFO] Deleted photo file during permanent delete: {photo}")
            except FileStoreError as e:
                print(f"[WARN] Could not delete photo file: {e}")
        
        self.db.execute("DELETE FROM animals WHERE id = ?", (animal_id,))
        return {"success": True, "photo_deleted": photo_deleted}

    def get_active_animals(self) -> List[Dict[str, Any]]:
        """Return all NON-hidden animals (excludes archived/removed).
        
        Admin sees all active statuses (healthy, adopted, under_treatment, etc.)
        """
        sql = """
            SELECT * FROM animals 
            WHERE status NOT LIKE '%|archived'
              AND status != 'removed'
            ORDER BY id
        """
        return self.db.fetch_all(sql)

    def get_hidden_animals(self) -> List[Dict[str, Any]]:
        """Return all hidden animals (archived and removed).
        
        For admin's Hidden Items page.
        """
        sql = """
            SELECT * FROM animals 
            WHERE status LIKE '%|archived'
               OR status = 'removed'
            ORDER BY 
                CASE WHEN status = 'removed' THEN removed_at ELSE archived_at END DESC
        """
        return self.db.fetch_all(sql)


__all__ = ["AnimalService"]
