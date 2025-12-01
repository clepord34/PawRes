"""Rescue mission service for submitting and managing rescue requests."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from storage.database import Database
import app_config
from app_config import RescueStatus, Urgency


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
        status: str = RescueStatus.PENDING,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        reporter_name: Optional[str] = None,
        reporter_phone: Optional[str] = None,
        urgency: str = Urgency.MEDIUM,
    ) -> int:
        """Create a rescue mission record and return its id.

        Uses structured columns for animal_type, reporter info, and urgency.
        The `details` parameter is stored in the `notes` field.
        The `name` parameter is the animal's name (if known).
        """
        # Extract urgency level from full label if provided
        urgency_level = Urgency.from_label(urgency)
        
        sql = """
            INSERT INTO rescue_missions 
            (user_id, animal_id, location, latitude, longitude, notes, status, 
             animal_type, animal_name, reporter_name, reporter_phone, urgency, is_closed)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
        """
        mid = self.db.execute(sql, (
            user_id, animal_id, location, latitude, longitude, details, status,
            animal_type, name, reporter_name, reporter_phone, urgency_level
        ))
        return mid

    def update_rescue_status(self, mission_id: int, status: str) -> bool:
        """Update the status for a mission. Returns True when updated.
        
        If status is 'rescued', automatically creates an animal entry from the
        mission details and links it to the mission.
        
        If status changes FROM 'rescued' to something else (failed/on-going),
        deletes the auto-created animal since the rescue didn't succeed.
        """
        existing = self.db.fetch_one(
            "SELECT id, animal_id, animal_type, animal_name, location, status FROM rescue_missions WHERE id = ?", 
            (mission_id,)
        )
        if not existing:
            return False
        
        old_status = RescueStatus.normalize(existing.get('status', ''))
        new_status = RescueStatus.normalize(status)
        
        # Update the status
        self.db.execute(
            "UPDATE rescue_missions SET status = ?, updated_at = ? WHERE id = ?",
            (status, datetime.now(), mission_id)
        )
        
        # Handle status transitions
        if new_status == RescueStatus.RESCUED and old_status != RescueStatus.RESCUED:
            # Changed TO rescued - create animal if not exists
            if not existing.get('animal_id'):
                animal_id = self._create_animal_from_mission(existing)
                if animal_id:
                    # Link the animal to this mission
                    self.db.execute(
                        "UPDATE rescue_missions SET animal_id = ? WHERE id = ?",
                        (animal_id, mission_id)
                    )
                    print(f"[INFO] Created animal ID={animal_id} from rescue mission ID={mission_id}")
        
        elif old_status == RescueStatus.RESCUED and new_status != RescueStatus.RESCUED:
            # Changed FROM rescued to something else - delete the auto-created animal
            animal_id = existing.get('animal_id')
            if animal_id:
                # Check for adoption requests before deleting
                adoption_count = self.db.fetch_one(
                    "SELECT COUNT(*) as count FROM adoption_requests WHERE animal_id = ?",
                    (animal_id,)
                )
                has_adoptions = adoption_count and adoption_count.get('count', 0) > 0
                
                if has_adoptions:
                    # Don't delete animal - has adoption requests linked
                    # Just unlink from mission
                    self.db.execute(
                        "UPDATE rescue_missions SET animal_id = NULL WHERE id = ?",
                        (mission_id,)
                    )
                    print(f"[WARN] Mission ID={mission_id} changed from rescued but animal ID={animal_id} has adoption requests - keeping animal, unlinking from mission")
                else:
                    # No adoption requests - check if animal is still in 'processing' status
                    animal = self.db.fetch_one(
                        "SELECT id, status FROM animals WHERE id = ?", (animal_id,)
                    )
                    if animal:
                        animal_status = (animal.get('status') or '').lower()
                        if animal_status == 'processing':
                            # Safe to delete - animal hasn't been set up yet
                            self.db.execute("DELETE FROM animals WHERE id = ?", (animal_id,))
                            self.db.execute(
                                "UPDATE rescue_missions SET animal_id = NULL WHERE id = ?",
                                (mission_id,)
                            )
                            print(f"[INFO] Deleted processing animal ID={animal_id} - mission ID={mission_id} changed from rescued to {new_status}")
                        else:
                            # Animal was already set up by admin, just unlink but don't delete
                            self.db.execute(
                                "UPDATE rescue_missions SET animal_id = NULL WHERE id = ?",
                                (mission_id,)
                            )
                            print(f"[WARN] Mission ID={mission_id} changed from rescued but animal ID={animal_id} has status '{animal_status}' - keeping animal record")
        
        return True
    
    def _create_animal_from_mission(self, mission: Dict[str, Any]) -> Optional[int]:
        """Create an animal entry from rescue mission data.
        
        Returns the new animal ID, or None if creation failed.
        Animals are created with 'processing' status - only visible to admin
        until they update the details and change the status.
        """
        animal_type = mission.get('animal_type') or 'Other'
        animal_name = mission.get('animal_name') or f"Rescued {animal_type}"
        location = mission.get('location') or ''
        
        # Map common animal types to species (capitalized for consistency)
        species = animal_type.lower()
        if species in ('dog', 'dogs'):
            species = 'Dog'
        elif species in ('cat', 'cats'):
            species = 'Cat'
        elif species in ('other', 'others', 'unknown'):
            species = 'Other'
        else:
            species = animal_type.capitalize()
        
        # Create animal with 'processing' status - admin must set up details first
        # Import here to avoid circular imports
        from app_config import AnimalStatus
        sql = """
            INSERT INTO animals (name, species, status, description, rescue_mission_id)
            VALUES (?, ?, ?, ?, ?)
        """
        try:
            animal_id = self.db.execute(sql, (
                animal_name,
                species,
                AnimalStatus.PROCESSING,
                f"Rescued from: {location}. Awaiting admin setup.",
                mission.get('id')
            ))
            return animal_id
        except Exception as e:
            print(f"[ERROR] Failed to create animal from mission: {e}")
            return None

    def get_all_missions(self) -> List[Dict[str, Any]]:
        """Return all missions ordered newest first."""
        rows = self.db.fetch_all(
            "SELECT * FROM rescue_missions ORDER BY mission_date DESC"
        )
        return rows

    def get_all_missions_for_analytics(self) -> List[Dict[str, Any]]:
        """Return missions that count in analytics and charts.
        
        Excludes "removed" status items. Includes archived items (they preserve
        their original status in the compound format like "rescued|archived").
        
        Used for historical data in charts like 'Rescued vs Adopted'.
        """
        rows = self.db.fetch_all(
            "SELECT * FROM rescue_missions WHERE status != 'removed' ORDER BY mission_date DESC"
        )
        return rows

    def get_user_missions(self, user_id: int) -> List[Dict[str, Any]]:
        """Return missions submitted by a specific user, newest first."""
        rows = self.db.fetch_all(
            "SELECT * FROM rescue_missions WHERE user_id = ? ORDER BY mission_date DESC",
            (user_id,)
        )
        return rows
    
    def get_mission_by_id(self, mission_id: int) -> Optional[Dict[str, Any]]:
        """Get a single mission by ID."""
        return self.db.fetch_one(
            "SELECT * FROM rescue_missions WHERE id = ?",
            (mission_id,)
        )

    def cancel_mission(self, mission_id: int, user_id: int) -> bool:
        """User cancels their own pending rescue mission.
        
        Only allows cancelling if:
        - Mission belongs to the user
        - Mission is still pending (not on-going, rescued, etc.)
        
        Args:
            mission_id: ID of mission to cancel
            user_id: ID of user attempting to cancel (must be owner)
        
        Returns True if cancelled successfully.
        """
        existing = self.db.fetch_one(
            "SELECT id, user_id, status FROM rescue_missions WHERE id = ?", 
            (mission_id,)
        )
        if not existing:
            return False
        
        # Verify ownership
        if existing.get('user_id') != user_id:
            print(f"[WARN] User {user_id} tried to cancel mission {mission_id} owned by {existing.get('user_id')}")
            return False
        
        # Only allow cancelling pending missions
        current_status = RescueStatus.normalize(existing.get('status', ''))
        if current_status != RescueStatus.PENDING:
            print(f"[WARN] Cannot cancel mission {mission_id} - status is {current_status}, not pending")
            return False
        
        # Set status to indicate user cancelled
        self.db.execute(
            "UPDATE rescue_missions SET status = 'cancelled', updated_at = ? WHERE id = ?",
            (datetime.now(), mission_id)
        )
        return True

    # =========================================================================
    # Archive/Remove/Restore/Delete methods
    # =========================================================================

    def archive_mission(self, mission_id: int, admin_id: int, note: Optional[str] = None) -> bool:
        """Archive a mission (hide from active list, keep in analytics).
        
        The status becomes "original_status|archived" to preserve the original
        status for analytics while marking it as archived.
        
        Args:
            mission_id: ID of mission to archive
            admin_id: ID of admin performing the action
            note: Optional note explaining why it was archived
            
        Returns True if archived successfully.
        """
        existing = self.db.fetch_one(
            "SELECT id, status FROM rescue_missions WHERE id = ?",
            (mission_id,)
        )
        if not existing:
            return False
        
        current_status = existing.get('status', '')
        
        # Don't archive if already archived or removed
        if RescueStatus.is_archived(current_status) or RescueStatus.is_removed(current_status):
            print(f"[WARN] Mission {mission_id} is already archived or removed")
            return False
        
        # Create archived status (e.g., "rescued|archived")
        archived_status = RescueStatus.make_archived(current_status)
        
        self.db.execute(
            """UPDATE rescue_missions 
               SET status = ?, previous_status = ?, archived_at = ?, archived_by = ?, archive_note = ?, updated_at = ?
               WHERE id = ?""",
            (archived_status, current_status, datetime.now(), admin_id, note, datetime.now(), mission_id)
        )
        print(f"[INFO] Archived mission {mission_id}: {current_status} -> {archived_status}")
        return True

    def remove_mission(self, mission_id: int, admin_id: int, reason: str) -> bool:
        """Remove a mission (mark as invalid/spam - excluded from analytics).
        
        Args:
            mission_id: ID of mission to remove
            admin_id: ID of admin performing the action
            reason: Reason for removal (shown to user)
            
        Returns True if removed successfully.
        """
        existing = self.db.fetch_one(
            "SELECT id, status FROM rescue_missions WHERE id = ?",
            (mission_id,)
        )
        if not existing:
            return False
        
        current_status = existing.get('status', '')
        
        # Don't remove if already removed
        if RescueStatus.is_removed(current_status):
            print(f"[WARN] Mission {mission_id} is already removed")
            return False
        
        # Store previous status for potential restore
        previous_status = RescueStatus.get_base_status(current_status)
        
        self.db.execute(
            """UPDATE rescue_missions 
               SET status = ?, previous_status = ?, removed_at = ?, removed_by = ?, removal_reason = ?, updated_at = ?
               WHERE id = ?""",
            (RescueStatus.REMOVED, previous_status, datetime.now(), admin_id, reason, datetime.now(), mission_id)
        )
        print(f"[INFO] Removed mission {mission_id}: {current_status} -> removed (reason: {reason})")
        return True

    def restore_mission(self, mission_id: int) -> bool:
        """Restore an archived or removed mission to its previous status.
        
        Returns True if restored successfully.
        """
        existing = self.db.fetch_one(
            "SELECT id, status, previous_status FROM rescue_missions WHERE id = ?",
            (mission_id,)
        )
        if not existing:
            return False
        
        current_status = existing.get('status', '')
        
        # Only restore if archived or removed
        if not RescueStatus.is_hidden(current_status):
            print(f"[WARN] Mission {mission_id} is not archived or removed")
            return False
        
        # Restore to previous status, or pending if no previous status
        previous_status = existing.get('previous_status') or RescueStatus.PENDING
        
        self.db.execute(
            """UPDATE rescue_missions 
               SET status = ?, archived_at = NULL, archived_by = NULL, archive_note = NULL,
                   removed_at = NULL, removed_by = NULL, removal_reason = NULL, updated_at = ?
               WHERE id = ?""",
            (previous_status, datetime.now(), mission_id)
        )
        print(f"[INFO] Restored mission {mission_id}: {current_status} -> {previous_status}")
        return True

    def permanently_delete_mission(self, mission_id: int) -> tuple[bool, str]:
        """Permanently delete a removed mission from the database.
        
        Only allowed for missions with 'removed' status.
        
        Returns (success, message) tuple.
        """
        existing = self.db.fetch_one(
            "SELECT id, status FROM rescue_missions WHERE id = ?",
            (mission_id,)
        )
        if not existing:
            return False, "Mission not found"
        
        current_status = existing.get('status', '')
        
        # Only allow permanent deletion of removed items
        if not RescueStatus.is_removed(current_status):
            return False, "Only removed missions can be permanently deleted"
        
        self.db.execute("DELETE FROM rescue_missions WHERE id = ?", (mission_id,))
        print(f"[INFO] Permanently deleted mission {mission_id}")
        return True, "Mission permanently deleted"

    def get_active_missions(self) -> List[Dict[str, Any]]:
        """Return all active missions (not archived or removed) for admin list."""
        rows = self.db.fetch_all(
            """SELECT * FROM rescue_missions 
               WHERE status NOT LIKE '%|archived' AND status != 'removed'
               ORDER BY mission_date DESC"""
        )
        return rows

    def get_hidden_missions(self) -> List[Dict[str, Any]]:
        """Return all archived and removed missions for admin's hidden items page."""
        rows = self.db.fetch_all(
            """SELECT * FROM rescue_missions 
               WHERE status LIKE '%|archived' OR status = 'removed'
               ORDER BY 
                   CASE WHEN status = 'removed' THEN removed_at ELSE archived_at END DESC"""
        )
        return rows


__all__ = ["RescueService"]
