"""Adoption service for managing adoption requests."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from storage.database import Database
import app_config
from app_config import AdoptionStatus, AnimalStatus


class AdoptionService:
    def __init__(self, db: Optional[Database | str] = None, *, ensure_tables: bool = True) -> None:
        if isinstance(db, Database):
            self.db = db
        else:
            self.db = Database(db if isinstance(db, str) else app_config.DB_PATH)

        if ensure_tables:
            self.db.create_tables()

    def submit_request(
        self,
        user_id: int,
        animal_id: int,
        contact: str,
        reason: str,
        status: str = AdoptionStatus.PENDING
    ) -> int:
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
                ar.id,
                ar.user_id,
                ar.animal_id,
                ar.contact,
                ar.reason,
                ar.status,
                ar.request_date,
                ar.notes,
                ar.was_approved,
                u.name as user_name,
                u.email as user_email,
                COALESCE(a.name, ar.animal_name) as animal_name,
                COALESCE(a.species, ar.animal_species) as animal_species,
                a.breed as animal_breed
            FROM adoption_requests ar
            LEFT JOIN users u ON ar.user_id = u.id
            LEFT JOIN animals a ON ar.animal_id = a.id
            ORDER BY ar.request_date DESC
        """
        return self.db.fetch_all(sql)

    def get_all_requests_for_analytics(self) -> List[Dict[str, Any]]:
        """Return adoption requests that count in analytics and charts.
        
        Excludes "removed" and "cancelled" status items. Includes archived items 
        (they preserve their original status in the compound format like "approved|archived").
        
        Used for dashboard stats and adoption trend charts.
        """
        sql = """
            SELECT 
                ar.id,
                ar.user_id,
                ar.animal_id,
                ar.contact,
                ar.reason,
                ar.status,
                ar.request_date,
                ar.notes,
                ar.was_approved,
                u.name as user_name,
                u.email as user_email,
                COALESCE(a.name, ar.animal_name) as animal_name,
                COALESCE(a.species, ar.animal_species) as animal_species,
                a.breed as animal_breed
            FROM adoption_requests ar
            LEFT JOIN users u ON ar.user_id = u.id
            LEFT JOIN animals a ON ar.animal_id = a.id
            WHERE ar.status NOT IN ('removed', 'cancelled')
            ORDER BY ar.request_date DESC
        """
        return self.db.fetch_all(sql)

    def get_user_requests(self, user_id: int) -> List[Dict[str, Any]]:
        """Return adoption requests submitted by `user_id`."""
        return self.db.fetch_all(
            "SELECT * FROM adoption_requests WHERE user_id = ? ORDER BY request_date DESC",
            (user_id,)
        )

    def update_status(self, request_id: int, status: str) -> bool:
        """Update the status of an adoption request. Returns True if updated.
        
        If the status is 'approved':
        - Updates the animal's status to 'adopted'
        - Auto-denies all other pending requests for the same animal
        
        If the status is 'denied' and animal was adopted by this request:
        - Reverts animal status to 'healthy' (if no other approved adoptions)
        """
        existing = self.db.fetch_one(
            "SELECT id, animal_id, status as old_status FROM adoption_requests WHERE id = ?", 
            (request_id,)
        )
        if not existing:
            return False
        
        old_status = (existing.get("old_status") or "").lower()
        new_status_lower = status.lower()
        animal_id = existing.get("animal_id")
        
        # If approving, also set was_approved flag and approved_at for historical tracking
        now = datetime.now()
        if new_status_lower == "approved" and old_status != "approved":
            self.db.execute(
                "UPDATE adoption_requests SET status = ?, updated_at = ?, was_approved = 1, approved_at = ? WHERE id = ?",
                (status, now, now, request_id)
            )
        elif new_status_lower == "approved":
            self.db.execute(
                "UPDATE adoption_requests SET status = ?, updated_at = ?, was_approved = 1 WHERE id = ?",
                (status, now, request_id)
            )
        else:
            self.db.execute(
                "UPDATE adoption_requests SET status = ?, updated_at = ? WHERE id = ?",
                (status, now, request_id)
            )
        
        if new_status_lower == "approved":
            if animal_id:
                self.db.execute(
                    f"UPDATE animals SET status = '{AnimalStatus.ADOPTED}', updated_at = ? WHERE id = ?",
                    (datetime.now(), animal_id)
                )
                
                # Auto-deny all OTHER pending requests for this same animal
                self.db.execute(
                    f"""UPDATE adoption_requests 
                        SET status = '{AdoptionStatus.DENIED}', 
                            notes = 'Animal was adopted by another applicant',
                            updated_at = ?
                        WHERE animal_id = ? 
                        AND id != ? 
                        AND LOWER(status) = '{AdoptionStatus.PENDING}'""",
                    (datetime.now(), animal_id, request_id)
                )
        
        elif new_status_lower == "denied" and old_status == "approved":
            # Changing FROM approved TO denied - may need to revert animal status
            if animal_id:
                other_approved = self.db.fetch_one(
                    f"""SELECT id FROM adoption_requests 
                        WHERE animal_id = ? 
                        AND LOWER(status) = '{AdoptionStatus.APPROVED}' 
                        AND id != ?""",
                    (animal_id, request_id)
                )
                if not other_approved:
                    # No other approved adoption, revert animal to healthy
                    self.db.execute(
                        f"UPDATE animals SET status = '{AnimalStatus.HEALTHY}', updated_at = ? WHERE id = ?",
                        (datetime.now(), animal_id)
                    )
        
        return True

    def update_request(self, request_id: int, contact: str, reason: str) -> bool:
        """Update the contact and reason of an adoption request. Returns True if updated."""
        existing = self.db.fetch_one("SELECT id FROM adoption_requests WHERE id = ?", (request_id,))
        if not existing:
            return False
        try:
            self.db.execute(
                "UPDATE adoption_requests SET contact = ?, reason = ?, updated_at = ? WHERE id = ?",
                (contact, reason, datetime.now(), request_id)
            )
        except Exception:
            self.db.execute(
                "UPDATE adoption_requests SET contact = ?, reason = ? WHERE id = ?",
                (contact, reason, request_id)
            )
        return True

    def cancel_request(self, request_id: int) -> bool:
        """User cancels their own adoption request.
        
        Sets status to 'cancelled' so user can still see it in their history.
        Returns True if cancelled.
        """
        existing = self.db.fetch_one("SELECT id, status FROM adoption_requests WHERE id = ?", (request_id,))
        if not existing:
            return False
        
        # Only allow cancelling pending requests
        if AdoptionStatus.normalize(existing.get('status', '')) != AdoptionStatus.PENDING:
            return False
        
        try:
            self.db.execute(
                f"UPDATE adoption_requests SET status = '{AdoptionStatus.CANCELLED}', updated_at = ? WHERE id = ?",
                (datetime.now(), request_id)
            )
        except Exception:
            self.db.execute(
                f"UPDATE adoption_requests SET status = '{AdoptionStatus.CANCELLED}' WHERE id = ?",
                (request_id,)
            )
        return True

    def get_request_by_id(self, request_id: int) -> Optional[Dict[str, Any]]:
        """Get a single adoption request by ID."""
        return self.db.fetch_one("SELECT * FROM adoption_requests WHERE id = ?", (request_id,))

    def deny_request(self, request_id: int, admin_id: int, reason: str) -> bool:
        """Deny an adoption request with a reason.
        
        This sets status to 'denied' and stores the denial reason.
        Only works on pending requests.
        Returns True if denied.
        """
        existing = self.db.fetch_one(
            "SELECT id, animal_id, status FROM adoption_requests WHERE id = ?", 
            (request_id,)
        )
        if not existing:
            return False
        
        current_status = AdoptionStatus.normalize(existing.get('status', ''))
        if current_status != AdoptionStatus.PENDING:
            return False
        
        self.db.execute(
            """UPDATE adoption_requests 
               SET status = ?, denial_reason = ?, updated_at = ?
               WHERE id = ?""",
            (AdoptionStatus.DENIED, reason, datetime.now(), request_id)
        )
        return True

    # -------------------------------------------------------------------------
    # Archive / Remove / Restore / Permanent Delete Methods
    # -------------------------------------------------------------------------

    def archive_request(self, request_id: int, admin_id: int, note: Optional[str] = None) -> bool:
        """Archive an adoption request (soft-hide, still counts in analytics).
        
        Status becomes "original_status|archived" to preserve original for analytics.
        Returns True if archived successfully.
        """
        existing = self.db.fetch_one(
            "SELECT id, status FROM adoption_requests WHERE id = ?",
            (request_id,)
        )
        if not existing:
            return False
        
        current_status = existing.get("status", "")
        
        # Don't archive if already archived or removed
        if AdoptionStatus.is_archived(current_status) or AdoptionStatus.is_removed(current_status):
            return False
        
        archived_status = AdoptionStatus.make_archived(current_status)
        
        self.db.execute(
            """UPDATE adoption_requests
               SET status = ?, previous_status = ?, 
                   archived_at = ?, archived_by = ?, archive_note = ?,
                   updated_at = ?
               WHERE id = ?""",
            (archived_status, current_status, datetime.now(), admin_id, note,
             datetime.now(), request_id)
        )
        return True

    def remove_request(self, request_id: int, admin_id: int, reason: str) -> bool:
        """Remove an adoption request (soft-delete, excluded from analytics).
        
        Status becomes "removed". Use for spam, duplicates, test data, etc.
        Returns True if removed successfully.
        """
        existing = self.db.fetch_one(
            "SELECT id, status FROM adoption_requests WHERE id = ?",
            (request_id,)
        )
        if not existing:
            return False
        
        current_status = existing.get("status", "")
        
        # Don't remove if already removed
        if AdoptionStatus.is_removed(current_status):
            return False
        
        base_status = AdoptionStatus.get_base_status(current_status)
        
        self.db.execute(
            """UPDATE adoption_requests
               SET status = ?, previous_status = ?,
                   removed_at = ?, removed_by = ?, removal_reason = ?,
                   archived_at = NULL, archived_by = NULL, archive_note = NULL,
                   updated_at = ?
               WHERE id = ?""",
            (AdoptionStatus.REMOVED, base_status, datetime.now(), admin_id, reason,
             datetime.now(), request_id)
        )
        return True

    def restore_request(self, request_id: int) -> bool:
        """Restore an archived or removed adoption request to its previous status.
        
        Returns True if restored successfully.
        """
        existing = self.db.fetch_one(
            "SELECT id, status, previous_status FROM adoption_requests WHERE id = ?",
            (request_id,)
        )
        if not existing:
            return False
        
        current_status = existing.get("status", "")
        
        # Only restore if hidden (archived or removed)
        if not AdoptionStatus.is_hidden(current_status):
            return False
        
        previous = existing.get("previous_status")
        if not previous:
            previous = AdoptionStatus.get_base_status(current_status)
        if not previous or previous == AdoptionStatus.REMOVED:
            previous = AdoptionStatus.PENDING  # Default fallback
        
        self.db.execute(
            """UPDATE adoption_requests
               SET status = ?, previous_status = NULL,
                   archived_at = NULL, archived_by = NULL, archive_note = NULL,
                   removed_at = NULL, removed_by = NULL, removal_reason = NULL,
                   updated_at = ?
               WHERE id = ?""",
            (previous, datetime.now(), request_id)
        )
        return True

    def permanently_delete_request(self, request_id: int) -> bool:
        """Permanently delete a REMOVED adoption request from the database.
        
        Only works on removed requests (not archived or active).
        This cannot be undone. Returns True if deleted.
        """
        existing = self.db.fetch_one(
            "SELECT id, status FROM adoption_requests WHERE id = ?",
            (request_id,)
        )
        if not existing:
            return False
        
        # Only allow permanent deletion of removed items
        if not AdoptionStatus.is_removed(existing.get("status", "")):
            return False
        
        self.db.execute("DELETE FROM adoption_requests WHERE id = ?", (request_id,))
        return True

    def get_active_requests(self) -> List[Dict[str, Any]]:
        """Return all NON-hidden adoption requests (excludes archived/removed).
        
        Admin sees: pending, approved, denied, cancelled
        """
        sql = """
            SELECT 
                ar.id,
                ar.user_id,
                ar.animal_id,
                ar.contact,
                ar.reason,
                ar.status,
                ar.request_date,
                ar.notes,
                ar.was_approved,
                ar.denial_reason,
                u.name as user_name,
                u.email as user_email,
                COALESCE(a.name, ar.animal_name) as animal_name,
                COALESCE(a.species, ar.animal_species) as animal_species,
                a.breed as animal_breed
            FROM adoption_requests ar
            LEFT JOIN users u ON ar.user_id = u.id
            LEFT JOIN animals a ON ar.animal_id = a.id
            WHERE ar.status NOT LIKE '%|archived'
              AND ar.status != 'removed'
            ORDER BY ar.request_date DESC
        """
        return self.db.fetch_all(sql)

    def get_hidden_requests(self) -> List[Dict[str, Any]]:
        """Return all hidden adoption requests (archived and removed).
        
        For admin's Hidden Items page.
        """
        sql = """
            SELECT 
                ar.id,
                ar.user_id,
                ar.animal_id,
                ar.contact,
                ar.reason,
                ar.status,
                ar.request_date,
                ar.notes,
                ar.was_approved,
                ar.denial_reason,
                ar.previous_status,
                ar.archived_at,
                ar.archived_by,
                ar.archive_note,
                ar.removed_at,
                ar.removed_by,
                ar.removal_reason,
                u.name as user_name,
                u.email as user_email,
                COALESCE(a.name, ar.animal_name) as animal_name,
                COALESCE(a.species, ar.animal_species) as animal_species,
                a.breed as animal_breed
            FROM adoption_requests ar
            LEFT JOIN users u ON ar.user_id = u.id
            LEFT JOIN animals a ON ar.animal_id = a.id
            WHERE ar.status LIKE '%|archived'
               OR ar.status = 'removed'
            ORDER BY 
                CASE WHEN ar.status = 'removed' THEN ar.removed_at ELSE ar.archived_at END DESC
        """
        return self.db.fetch_all(sql)

    def archive_adoption(self, request_id: int, archived_by: int, reason: Optional[str] = None) -> bool:
        """Alias for archive_request() for backward compatibility.
        
        Args:
            request_id: ID of adoption request to archive
            archived_by: ID of admin performing the action
            reason: Optional note explaining why it was archived
            
        Returns True if archived successfully.
        """
        return self.archive_request(request_id, archived_by, reason)


__all__ = ["AdoptionService"]
