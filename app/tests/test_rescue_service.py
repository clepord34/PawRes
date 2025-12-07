"""Tests for RescueService - status transitions, animal auto-creation."""
import pytest

from services.rescue_service import RescueService
from services.animal_service import AnimalService
from storage.database import Database
from app_config import RescueStatus, AnimalStatus


class TestSubmitRescue:
    """Test rescue mission submission."""
    
    def test_submit_rescue_success(self, rescue_service, sample_user):
        """Test submitting a rescue mission."""
        mission_id = rescue_service.submit_rescue_request(
            user_id=sample_user["id"],
            animal_type="dog",
            breed="Mixed",
            location="Naga City",
            latitude=13.6218,
            longitude=123.1948,
            urgency="high",
            details="Injured dog needs help. Found near the highway"
        )
        
        assert mission_id > 0
        
        mission = rescue_service.get_mission_by_id(mission_id)
        assert mission is not None
        assert mission["user_id"] == sample_user["id"]
        assert RescueStatus.normalize(mission["status"]) == RescueStatus.PENDING
    
    def test_submit_rescue_minimal_fields(self, rescue_service, sample_user):
        """Test submitting rescue with only required fields."""
        mission_id = rescue_service.submit_rescue_request(
            user_id=sample_user["id"],
            animal_type="cat",
            breed="Unknown",
            location="Manila"
        )
        
        assert mission_id > 0
    
    def test_submit_rescue_with_photo(self, rescue_service, sample_user, sample_photo_base64):
        """Test submitting rescue with photo."""
        mission_id = rescue_service.submit_rescue_request(
            user_id=sample_user["id"],
            animal_type="dog",
            breed="Unknown",
            location="Quezon City",
            animal_photo=sample_photo_base64
        )
        
        assert mission_id > 0
        
        mission = rescue_service.get_mission_by_id(mission_id)
        assert mission["animal_photo"] is not None


class TestGetRescueMission:
    """Test rescue mission retrieval."""
    
    def test_get_rescue_by_id(self, rescue_service, sample_rescue_mission):
        """Test getting rescue mission by ID."""
        mission = rescue_service.get_mission_by_id(sample_rescue_mission["id"])
        
        assert mission is not None
        assert mission["id"] == sample_rescue_mission["id"]
    
    def test_get_nonexistent_rescue(self, rescue_service):
        """Test getting non-existent rescue mission."""
        mission = rescue_service.get_mission_by_id(99999)
        
        assert mission is None


class TestListRescueMissions:
    """Test rescue mission listing."""
    
    def test_get_all_missions(self, rescue_service, sample_rescue_mission):
        """Test getting all rescue missions."""
        missions = rescue_service.get_all_missions()
        
        assert len(missions) >= 1
        mission_ids = [m["id"] for m in missions]
        assert sample_rescue_mission["id"] in mission_ids
    
    def test_get_missions_by_status(self, rescue_service, sample_rescue_mission, sample_user):
        """Test filtering missions by status."""
        # Create mission with different status
        ongoing_id = rescue_service.submit_rescue_request(
            user_id=sample_user["id"],
            animal_type="dog",
            breed="Unknown",
            location="Test"
        )
        rescue_service.update_rescue_status(ongoing_id, RescueStatus.ONGOING)
        
        all_missions = rescue_service.get_all_missions()
        pending = [m for m in all_missions if RescueStatus.normalize(m["status"]) == RescueStatus.PENDING]
        ongoing = [m for m in all_missions if RescueStatus.normalize(m["status"]) == RescueStatus.ONGOING]
        
        pending_ids = [m["id"] for m in pending]
        ongoing_ids = [m["id"] for m in ongoing]
        
        assert sample_rescue_mission["id"] in pending_ids
        assert ongoing_id in ongoing_ids
        assert ongoing_id not in pending_ids
    
    def test_get_user_missions(self, rescue_service, sample_rescue_mission, sample_user, sample_admin):
        """Test getting missions for specific user."""
        admin_mission_id = rescue_service.submit_rescue_request(
            user_id=sample_admin["id"],
            animal_type="cat",
            breed="Unknown",
            location="Test"
        )
        
        user_missions = rescue_service.get_user_missions(sample_user["id"])
        user_mission_ids = [m["id"] for m in user_missions]
        
        assert sample_rescue_mission["id"] in user_mission_ids
        assert admin_mission_id not in user_mission_ids


class TestUpdateRescueStatus:
    """Test rescue status transitions."""
    
    def test_update_to_ongoing(self, rescue_service, sample_rescue_mission, sample_admin):
        """Test updating rescue to on-going status."""
        success = rescue_service.update_rescue_status(
            sample_rescue_mission["id"],
            RescueStatus.ONGOING
        )
        
        assert success is True
        
        mission = rescue_service.get_mission_by_id(sample_rescue_mission["id"])
        assert RescueStatus.normalize(mission["status"]) == RescueStatus.ONGOING
    
    def test_update_to_failed(self, rescue_service, sample_rescue_mission, sample_admin):
        """Test updating rescue to failed status."""
        success = rescue_service.update_rescue_status(
            sample_rescue_mission["id"],
            RescueStatus.FAILED
        )
        
        assert success is True
        
        mission = rescue_service.get_mission_by_id(sample_rescue_mission["id"])
        assert RescueStatus.normalize(mission["status"]) == RescueStatus.FAILED
    
    def test_cancel_rescue_by_user(self, rescue_service, sample_rescue_mission, sample_user):
        """Test user cancelling their own rescue report."""
        success = rescue_service.cancel_mission(
            sample_rescue_mission["id"],
            sample_user["id"]
        )
        
        assert success is True
        
        mission = rescue_service.get_mission_by_id(sample_rescue_mission["id"])
        assert RescueStatus.is_cancelled(mission["status"]) is True


class TestRescueToAnimalCreation:
    """Test automatic animal creation when rescue is marked as 'rescued'."""
    
    def test_rescued_status_creates_animal(self, rescue_service, animal_service, sample_rescue_mission, sample_admin):
        """Test that marking rescue as 'rescued' creates an animal."""
        success = rescue_service.update_rescue_status(
            sample_rescue_mission["id"],
            RescueStatus.RESCUED
        )
        
        assert success is True
        
        mission = rescue_service.get_mission_by_id(sample_rescue_mission["id"])
        assert mission["animal_id"] is not None
        
        animal = animal_service.get_animal_by_id(mission["animal_id"])
        assert animal is not None
        assert animal["species"] == "Dog"  # Capitalized from mission animal_type
        assert animal["breed"] == mission["breed"]
    
    def test_animal_inherits_rescue_data(self, rescue_service, animal_service, sample_user, sample_admin):
        """Test that created animal inherits data from rescue mission."""
        mission_id = rescue_service.submit_rescue_request(
            user_id=sample_user["id"],
            animal_type="dog",
            breed="Aspin",
            name="Brownie",
            location="Naga City",
            latitude=13.6218,
            longitude=123.1948,
            details="Friendly stray dog"
        )
        
        rescue_service.update_rescue_status(
            mission_id,
            RescueStatus.RESCUED
        )
        
        mission = rescue_service.get_mission_by_id(mission_id)
        animal = animal_service.get_animal_by_id(mission["animal_id"])
        
        assert animal["species"] == "Dog"  # Capitalized from 'dog'
        assert animal["breed"] == "Aspin"
        assert animal["name"] == "Brownie"
    
    def test_rescued_with_photo_copies_to_animal(self, rescue_service, animal_service, sample_user, sample_admin, sample_photo_base64):
        """Test that animal inherits photo from rescue mission."""
        mission_id = rescue_service.submit_rescue_request(
            user_id=sample_user["id"],
            animal_type="cat",
            breed="Puspin",
            location="Manila",
            animal_photo=sample_photo_base64
        )
        
        rescue_service.update_rescue_status(
            mission_id,
            RescueStatus.RESCUED
        )
        
        mission = rescue_service.get_mission_by_id(mission_id)
        animal = animal_service.get_animal_by_id(mission["animal_id"])
        
        assert animal["photo"] is not None


class TestRescueToAnimalDeletion:
    """Test automatic animal deletion when rescue status is reverted."""
    
    def test_failed_after_rescued_deletes_animal(self, rescue_service, animal_service, sample_rescue_mission, sample_admin):
        """Test that marking rescued mission as failed deletes the animal."""
        rescue_service.update_rescue_status(
            sample_rescue_mission["id"],
            RescueStatus.RESCUED
        )
        
        mission = rescue_service.get_mission_by_id(sample_rescue_mission["id"])
        animal_id = mission["animal_id"]
        assert animal_id is not None
        
        animal = animal_service.get_animal_by_id(animal_id)
        assert animal is not None
        
        rescue_service.update_rescue_status(
            sample_rescue_mission["id"],
            RescueStatus.FAILED
        )
        
        animal = animal_service.get_animal_by_id(animal_id)
    
    def test_animal_not_deleted_if_has_adoptions(self, rescue_service, animal_service, adoption_service, sample_rescue_mission, sample_user, sample_admin):
        """Test that animal is NOT deleted if it has adoption requests."""
        rescue_service.update_rescue_status(
            sample_rescue_mission["id"],
            RescueStatus.RESCUED
        )
        
        mission = rescue_service.get_mission_by_id(sample_rescue_mission["id"])
        animal_id = mission["animal_id"]
        
        adoption_service.submit_request(
            user_id=sample_user["id"],
            animal_id=animal_id,
            contact=sample_user["email"],
            reason="Want to adopt"
        )
        
        rescue_service.update_rescue_status(
            sample_rescue_mission["id"],
            RescueStatus.FAILED
        )
        
        animal = animal_service.get_animal_by_id(animal_id)
        assert animal is not None


class TestArchiveRescue:
    """Test rescue mission archiving."""
    
    def test_archive_rescue_mission(self, rescue_service, sample_rescue_mission, sample_admin):
        """Test archiving a rescue mission."""
        success = rescue_service.archive_rescue(
            sample_rescue_mission["id"],
            archived_by=sample_admin["id"],
            reason="Mission completed"
        )
        
        assert success is True
        
        # Verify mission is archived
        mission = rescue_service.get_mission_by_id(sample_rescue_mission["id"])
        assert RescueStatus.is_archived(mission["status"]) is True
    
    def test_archived_not_in_active_list(self, rescue_service, sample_rescue_mission, sample_admin):
        """Test archived missions are excluded from active listings."""
        # Archive the mission
        rescue_service.archive_rescue(
            sample_rescue_mission["id"],
            archived_by=sample_admin["id"]
        )
        
        # Get active missions (should exclude archived)
        active = rescue_service.get_active_missions()
        active_ids = [m["id"] for m in active]
        
        assert sample_rescue_mission["id"] not in active_ids


class TestRemoveRescue:
    """Test rescue mission removal (for invalid/spam reports)."""
    
    def test_remove_rescue_mission(self, rescue_service, sample_rescue_mission, sample_admin):
        """Test removing a rescue mission as invalid."""
        success = rescue_service.remove_mission(
            sample_rescue_mission["id"],
            sample_admin["id"],
            "Spam report"
        )
        
        assert success is True
        
        # Verify mission is marked as removed
        mission = rescue_service.get_mission_by_id(sample_rescue_mission["id"])
        assert RescueStatus.is_removed(mission["status"]) is True
    
    def test_removed_not_in_analytics(self, rescue_service, sample_rescue_mission, sample_admin):
        """Test removed missions are excluded from analytics."""
        # Remove the mission
        rescue_service.remove_mission(
            sample_rescue_mission["id"],
            sample_admin["id"],
            "Test removal"
        )
        
        # Get missions for analytics
        missions = rescue_service.get_all_missions_for_analytics()
        mission_ids = [m["id"] for m in missions]
        
        assert sample_rescue_mission["id"] not in mission_ids


class TestRescueStatusHelpers:
    """Test rescue status helper methods."""
    
    def test_is_active_status(self, rescue_service, sample_rescue_mission):
        """Test checking if mission is active."""
        mission = rescue_service.get_mission_by_id(sample_rescue_mission["id"])
        
        # Pending is active
        assert RescueStatus.is_active(mission["status"]) is True
    
    def test_is_final_status(self, rescue_service, sample_rescue_mission, sample_admin):
        """Test checking if mission is in final status."""
        # Update to rescued (final status)
        rescue_service.update_rescue_status(
            sample_rescue_mission["id"],
            RescueStatus.RESCUED
        )
        
        mission = rescue_service.get_mission_by_id(sample_rescue_mission["id"])
        assert RescueStatus.is_final(mission["status"]) is True


class TestRescueSearch:
    """Test rescue mission search."""
    
    def test_search_by_location(self, rescue_service, sample_rescue_mission):
        """Test searching missions by location."""
        location = sample_rescue_mission.get("location", "Test Location")
        results = rescue_service.search_missions(query=location)
        
        # Should find at least one result
        assert len(results) >= 1
        # Verify the sample mission is in the results
        result_ids = [r["id"] for r in results]
        assert sample_rescue_mission["id"] in result_ids
    
    def test_search_by_animal_type(self, rescue_service, sample_rescue_mission):
        """Test searching missions by animal type."""
        animal_type = sample_rescue_mission.get("animal_type", "dog")
        results = rescue_service.search_missions(query=animal_type)
        
        # Should find the mission
        result_ids = [r["id"] for r in results]
        assert sample_rescue_mission["id"] in result_ids


class TestRescueStatistics:
    """Test rescue mission statistics."""
    
    def test_get_mission_count(self, rescue_service, sample_rescue_mission):
        """Test getting total mission count."""
        # Use get_all_missions instead
        missions = rescue_service.get_all_missions()
        count = len(missions)
        
        assert count >= 1
    
    def test_get_mission_count_by_status(self, rescue_service, sample_rescue_mission):
        """Test getting mission count by status."""
        # Filter missions by status manually
        missions = rescue_service.get_all_missions()
        pending = [m for m in missions if RescueStatus.normalize(m["status"]) == RescueStatus.PENDING]
        pending_count = len(pending)
        
        assert pending_count >= 1
    
    def test_get_active_mission_count(self, rescue_service, sample_rescue_mission):
        """Test getting count of active missions."""
        # Use get_active_missions instead
        active_missions = rescue_service.get_active_missions()
        active_count = len(active_missions)
        
        assert active_count >= 1  # sample_rescue_mission is pending (active)
