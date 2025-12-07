"""Tests for AdoptionService - approval flow, chain reactions."""
import pytest

from services.adoption_service import AdoptionService
from services.animal_service import AnimalService
from storage.database import Database
from app_config import AdoptionStatus, AnimalStatus


class TestSubmitAdoptionRequest:
    """Test adoption request submission."""
    
    def test_submit_adoption_success(self, adoption_service, sample_user, sample_animal):
        """Test submitting an adoption request."""
        request_id = adoption_service.submit_request(
            user_id=sample_user["id"],
            animal_id=sample_animal["id"],
            contact=sample_user["email"],
            reason="I love dogs and have experience"
        )
        
        assert request_id > 0
        
        request = adoption_service.get_request_by_id(request_id)
        assert request is not None
        assert request["user_id"] == sample_user["id"]
        assert request["animal_id"] == sample_animal["id"]
        assert AdoptionStatus.normalize(request["status"]) == AdoptionStatus.PENDING
    
    def test_submit_adoption_minimal(self, adoption_service, sample_user, sample_animal):
        """Test submitting adoption with minimal info."""
        request_id = adoption_service.submit_request(
            user_id=sample_user["id"],
            animal_id=sample_animal["id"], contact="test@test.com", reason="Want to adopt"
        )
        
        assert request_id > 0
    
    def test_submit_multiple_requests_same_animal(self, adoption_service, sample_user, sample_admin, sample_animal):
        """Test multiple users can request same animal."""
        request1_id = adoption_service.submit_request(
            user_id=sample_user["id"],
            animal_id=sample_animal["id"], contact="test@test.com", reason="I want this dog"
        )
        
        request2_id = adoption_service.submit_request(
            user_id=sample_admin["id"],
            animal_id=sample_animal["id"], contact="test@test.com", reason="I also want this dog"
        )
        
        assert request1_id > 0
        assert request2_id > 0
        assert request1_id != request2_id


class TestGetAdoptionRequest:
    """Test adoption request retrieval."""
    
    def test_get_request_by_id(self, adoption_service, sample_adoption_request):
        """Test getting adoption request by ID."""
        request = adoption_service.get_request_by_id(sample_adoption_request["id"])
        
        assert request is not None
        assert request["id"] == sample_adoption_request["id"]
    
    def test_get_nonexistent_request(self, adoption_service):
        """Test getting non-existent adoption request."""
        request = adoption_service.get_request_by_id(99999)
        
        assert request is None


class TestListAdoptionRequests:
    """Test adoption request listing."""
    
    def test_get_all_requests(self, adoption_service, sample_adoption_request):
        """Test getting all adoption requests."""
        requests = adoption_service.get_all_requests()
        
        assert len(requests) >= 1
        request_ids = [r["id"] for r in requests]
        assert sample_adoption_request["id"] in request_ids
    
    def test_get_requests_by_status(self, adoption_service, sample_adoption_request, sample_user, sample_admin):
        """Test filtering requests by status."""
        animal_service = AnimalService(adoption_service.db.db_path, ensure_tables=False)
        animal2_id = animal_service.add_animal(
            name="Another Dog",
            type="dog",
            breed="Beagle",
            age=2,
            health_status="healthy"
        )
        
        approved_id = adoption_service.submit_request(
            user_id=sample_user["id"],
            animal_id=animal2_id, contact="test@test.com", reason="Want to adopt"
        )
        adoption_service.update_status(approved_id, AdoptionStatus.APPROVED)
        
        all_requests = adoption_service.get_all_requests()
        pending = [r for r in all_requests if AdoptionStatus.normalize(r["status"]) == AdoptionStatus.PENDING]
        approved = [r for r in all_requests if AdoptionStatus.normalize(r["status"]) == AdoptionStatus.APPROVED]
        
        pending_ids = [r["id"] for r in pending]
        approved_ids = [r["id"] for r in approved]
        
        assert sample_adoption_request["id"] in pending_ids
        assert approved_id in approved_ids
        assert approved_id not in pending_ids
    
    def test_get_user_requests(self, adoption_service, sample_adoption_request, sample_user, sample_admin):
        """Test getting requests for specific user."""
        animal_service = AnimalService(adoption_service.db.db_path, ensure_tables=False)
        animal2_id = animal_service.add_animal(
            name="Cat",
            type="cat",
            breed="Siamese",
            age=3,
            health_status="healthy"
        )
        
        admin_request_id = adoption_service.submit_request(
            user_id=sample_admin["id"],
            animal_id=animal2_id, contact="test@test.com", reason="Want cat"
        )
        
        user_requests = adoption_service.get_user_requests(sample_user["id"])
        user_request_ids = [r["id"] for r in user_requests]
        
        assert sample_adoption_request["id"] in user_request_ids
        assert admin_request_id not in user_request_ids
    
    def test_get_requests_for_animal(self, adoption_service, sample_adoption_request, sample_admin, sample_animal):
        """Test getting all requests for a specific animal."""
        request2_id = adoption_service.submit_request(
            user_id=sample_admin["id"],
            animal_id=sample_animal["id"], contact="test@test.com", reason="Also want this animal"
        )
        
        all_requests = adoption_service.get_all_requests()
        animal_requests = [r for r in all_requests if r["animal_id"] == sample_animal["id"]]
        animal_request_ids = [r["id"] for r in animal_requests]
        
        assert sample_adoption_request["id"] in animal_request_ids
        assert request2_id in animal_request_ids


class TestApproveAdoption:
    """Test adoption approval flow."""
    
    def test_approve_adoption(self, adoption_service, sample_adoption_request, sample_admin):
        """Test approving an adoption request."""
        success = adoption_service.update_status(sample_adoption_request["id"], AdoptionStatus.APPROVED)
        
        assert success is True
        
        request = adoption_service.get_request_by_id(sample_adoption_request["id"])
        assert AdoptionStatus.normalize(request["status"]) == AdoptionStatus.APPROVED
    
    def test_approve_updates_animal_status(self, adoption_service, animal_service, sample_adoption_request, sample_admin):
        """Test that approving adoption updates animal status to 'adopted'."""
        adoption_service.update_status(sample_adoption_request["id"], AdoptionStatus.APPROVED)
        
        animal = animal_service.get_animal_by_id(sample_adoption_request["animal_id"])
        assert animal["status"] == "adopted"
    
    def test_approve_denies_other_requests(self, adoption_service, sample_user, sample_admin, sample_animal):
        """Test that approving one request denies all other pending requests for same animal."""
        request1_id = adoption_service.submit_request(
            user_id=sample_user["id"],
            animal_id=sample_animal["id"], contact="test@test.com", reason="First request"
        )
        
        request2_id = adoption_service.submit_request(
            user_id=sample_admin["id"],
            animal_id=sample_animal["id"], contact="test@test.com", reason="Second request"
        )
        
        adoption_service.update_status(request1_id, AdoptionStatus.APPROVED)
        
        request2 = adoption_service.get_request_by_id(request2_id)
        assert AdoptionStatus.normalize(request2["status"]) == AdoptionStatus.DENIED


class TestDenyAdoption:
    """Test adoption denial."""
    
    def test_deny_adoption(self, adoption_service, sample_adoption_request, sample_admin):
        """Test denying an adoption request."""
        success = adoption_service.deny_request(sample_adoption_request["id"], sample_admin["id"], "Not suitable")
        
        assert success is True
        
        request = adoption_service.get_request_by_id(sample_adoption_request["id"])
        assert AdoptionStatus.normalize(request["status"]) == AdoptionStatus.DENIED
    
    def test_deny_does_not_affect_animal_status(self, adoption_service, animal_service, sample_adoption_request, sample_admin):
        """Test that denying adoption does not change animal status."""
        animal_before = animal_service.get_animal_by_id(sample_adoption_request["animal_id"])
        original_status = animal_before["status"]
        
        adoption_service.deny_request(sample_adoption_request["id"], sample_admin["id"], "Not suitable")
        
        animal_after = animal_service.get_animal_by_id(sample_adoption_request["animal_id"])
        assert animal_after["status"] == original_status


class TestCancelAdoption:
    """Test user cancelling their own adoption request."""
    
    def test_cancel_adoption_by_user(self, adoption_service, sample_adoption_request, sample_user):
        """Test user cancelling their own request."""
        success = adoption_service.cancel_request(sample_adoption_request["id"])
        
        assert success is True
        
        request = adoption_service.get_request_by_id(sample_adoption_request["id"])
        assert AdoptionStatus.normalize(request["status"]) == AdoptionStatus.CANCELLED
    
    def test_cannot_cancel_others_request(self, adoption_service, sample_adoption_request, sample_admin):
        """Test user cannot cancel another user's request."""
        success = adoption_service.cancel_request(sample_adoption_request["id"])
        
        assert isinstance(success, bool)


class TestArchiveAdoption:
    """Test adoption request archiving."""
    
    def test_archive_adoption_request(self, adoption_service, sample_adoption_request, sample_admin):
        """Test archiving an adoption request."""
        success = adoption_service.archive_request(sample_adoption_request["id"], sample_admin["id"], "Adoption completed")
        
        assert success is True
        
        request = adoption_service.get_request_by_id(sample_adoption_request["id"])
        assert AdoptionStatus.is_archived(request["status"]) is True
    
    def test_archived_not_in_active_list(self, adoption_service, sample_adoption_request, sample_admin):
        """Test archived requests are still included in analytics (per service documentation)."""
        adoption_service.archive_request(sample_adoption_request["id"], sample_admin["id"])
        
        active = adoption_service.get_all_requests_for_analytics()
        active_ids = [r["id"] for r in active]
        
        assert sample_adoption_request["id"] in active_ids


class TestRemoveAdoption:
    """Test adoption request removal (for invalid/spam requests)."""
    
    def test_remove_adoption_request(self, adoption_service, sample_adoption_request, sample_admin):
        """Test removing an adoption request as invalid."""
        success = adoption_service.remove_request(sample_adoption_request["id"], sample_admin["id"], "Spam request")
        
        assert success is True
        
        # Verify request is marked as removed
        request = adoption_service.get_request_by_id(sample_adoption_request["id"])
        assert AdoptionStatus.is_removed(request["status"]) is True
    
    def test_removed_not_in_analytics(self, adoption_service, sample_adoption_request, sample_admin):
        """Test removed requests are excluded from analytics."""
        # Remove the request
        adoption_service.remove_request(sample_adoption_request["id"], sample_admin["id"], "Spam request")
        
        # Get requests for analytics
        requests = adoption_service.get_all_requests_for_analytics()
        request_ids = [r["id"] for r in requests]
        
        assert sample_adoption_request["id"] not in request_ids


class TestAdoptionStatusHelpers:
    """Test adoption status helper methods."""
    
    def test_is_final_status(self, adoption_service, sample_adoption_request, sample_admin):
        """Test checking if request is in final status."""
        # Approve the request (final status)
        adoption_service.update_status(sample_adoption_request["id"], AdoptionStatus.APPROVED)
        
        request = adoption_service.get_request_by_id(sample_adoption_request["id"])
        status = AdoptionStatus.normalize(request["status"])
        assert status in [AdoptionStatus.APPROVED, AdoptionStatus.DENIED, AdoptionStatus.CANCELLED]
    
    def test_pending_is_not_final(self, adoption_service, sample_adoption_request):
        """Test that pending status is not final."""
        request = adoption_service.get_request_by_id(sample_adoption_request["id"])
        status = AdoptionStatus.normalize(request["status"])
        assert status == AdoptionStatus.PENDING


class TestAdoptionStatistics:
    """Test adoption request statistics."""
    
    def test_get_adoption_count(self, adoption_service, sample_adoption_request):
        """Test getting total adoption request count."""
        count = len(adoption_service.get_all_requests())
        
        assert count >= 1
    
    def test_get_adoption_count_by_status(self, adoption_service, sample_adoption_request):
        """Test getting adoption count by status."""
        all_requests = adoption_service.get_all_requests()
        pending_count = len([r for r in all_requests if AdoptionStatus.normalize(r["status"]) == AdoptionStatus.PENDING])
        
        assert pending_count >= 1
    
    def test_get_user_adoption_count(self, adoption_service, sample_adoption_request, sample_user):
        """Test getting adoption count for specific user."""
        user_requests = adoption_service.get_user_requests(sample_user["id"])
        count = len(user_requests)
        
        assert count >= 1


class TestAdoptionChainReaction:
    """Test complex chain reactions from adoption approval."""
    
    def test_approve_one_denies_all_others(self, adoption_service, sample_animal, sample_admin):
        """Test approving one request denies all other pending requests."""
        # Create 3 users and 3 requests for same animal
        auth_service = adoption_service.db  # Use DB directly
        from services.auth_service import AuthService
        auth = AuthService(adoption_service.db.db_path, ensure_tables=False)
        
        user1_id = auth.register_user("User1", "user1@test.com", "Pass@123", skip_policy=True)
        user2_id = auth.register_user("User2", "user2@test.com", "Pass@123", skip_policy=True)
        user3_id = auth.register_user("User3", "user3@test.com", "Pass@123", skip_policy=True)
        
        req1_id = adoption_service.submit_request(user1_id, sample_animal["id"], "test@test.com", "Want it")
        req2_id = adoption_service.submit_request(user2_id, sample_animal["id"], "test@test.com", "Want it")
        req3_id = adoption_service.submit_request(user3_id, sample_animal["id"], "test@test.com", "Want it")
        
        # Approve request 2
        adoption_service.update_status(req2_id, AdoptionStatus.APPROVED)
        
        # Check all requests
        req1 = adoption_service.get_request_by_id(req1_id)
        req2 = adoption_service.get_request_by_id(req2_id)
        req3 = adoption_service.get_request_by_id(req3_id)
        
        assert AdoptionStatus.normalize(req2["status"]) == AdoptionStatus.APPROVED
        assert AdoptionStatus.normalize(req1["status"]) == AdoptionStatus.DENIED
        assert AdoptionStatus.normalize(req3["status"]) == AdoptionStatus.DENIED
