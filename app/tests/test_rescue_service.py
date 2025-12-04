"""Unit tests for RescueService."""
from __future__ import annotations

import pytest

from services.rescue_service import RescueService
from services.auth_service import AuthService


@pytest.fixture
def test_user(auth_service: AuthService) -> int:
    """Create a test user and return their ID for foreign key constraints."""
    user_id = auth_service.register_user(
        name="Rescue Test User",
        email="rescue_test@example.com",
        password="testpass"
    )
    return user_id


class TestSubmitRescueRequest:
    """Tests for submitting rescue requests."""

    def test_submit_rescue_request_basic(self, rescue_service: RescueService, test_user: int):
        """Test submitting a basic rescue request."""
        mission_id = rescue_service.submit_rescue_request(
            user_id=test_user,
            location="123 Main Street"
        )
        
        assert mission_id is not None
        assert isinstance(mission_id, int)
        assert mission_id > 0

    def test_submit_rescue_request_with_all_fields(self, rescue_service: RescueService, test_user: int):
        """Test submitting a rescue request with all optional fields."""
        mission_id = rescue_service.submit_rescue_request(
            user_id=test_user,
            location="456 Oak Avenue",
            animal_type="Dog",
            name="Stray dog near park",
            details="Medium-sized brown dog, looks scared",
            latitude=14.5995,
            longitude=120.9842
        )
        
        assert mission_id is not None
        
        # Verify mission was created
        missions = rescue_service.get_all_missions()
        assert len(missions) == 1
        mission = missions[0]
        assert mission["location"] == "456 Oak Avenue"
        assert mission["latitude"] == 14.5995
        assert mission["longitude"] == 120.9842

    def test_submit_rescue_request_default_status_is_pending(self, rescue_service: RescueService, test_user: int):
        """Test that new rescue requests default to 'pending' status."""
        mission_id = rescue_service.submit_rescue_request(
            user_id=test_user,
            location="Test Location"
        )
        
        missions = rescue_service.get_all_missions()
        assert missions[0]["status"] == "pending"

    def test_submit_rescue_request_with_custom_status(self, rescue_service: RescueService, test_user: int):
        """Test submitting a rescue request with custom status."""
        mission_id = rescue_service.submit_rescue_request(
            user_id=test_user,
            location="Urgent Location",
            status="in_progress"
        )
        
        missions = rescue_service.get_all_missions()
        assert missions[0]["status"] == "in_progress"

    def test_submit_rescue_request_with_null_user(self, rescue_service: RescueService):
        """Test submitting a rescue request with null user_id (anonymous report)."""
        mission_id = rescue_service.submit_rescue_request(
            user_id=None,
            location="Anonymous report location"
        )
        
        assert mission_id is not None
        missions = rescue_service.get_all_missions()
        assert missions[0]["user_id"] is None


class TestUpdateRescueStatus:
    """Tests for updating rescue mission status."""

    def test_update_rescue_status_success(self, rescue_service: RescueService, test_user: int):
        """Test successfully updating a mission's status."""
        mission_id = rescue_service.submit_rescue_request(
            user_id=test_user,
            location="Test"
        )
        
        result = rescue_service.update_rescue_status(mission_id, "completed")
        assert result is True
        
        missions = rescue_service.get_all_missions()
        assert missions[0]["status"] == "completed"

    def test_update_rescue_status_nonexistent_mission(self, rescue_service: RescueService):
        """Test updating status of non-existent mission returns False."""
        result = rescue_service.update_rescue_status(99999, "completed")
        assert result is False

    def test_update_rescue_status_multiple_times(self, rescue_service: RescueService, test_user: int):
        """Test that status can be updated multiple times."""
        mission_id = rescue_service.submit_rescue_request(
            user_id=test_user,
            location="Test"
        )
        
        # Update to in_progress
        rescue_service.update_rescue_status(mission_id, "in_progress")
        missions = rescue_service.get_all_missions()
        assert missions[0]["status"] == "in_progress"
        
        # Update to completed
        rescue_service.update_rescue_status(mission_id, "completed")
        missions = rescue_service.get_all_missions()
        assert missions[0]["status"] == "completed"


class TestGetMissions:
    """Tests for retrieving rescue missions."""

    def test_get_all_missions_empty(self, rescue_service: RescueService):
        """Test getting missions when none exist."""
        missions = rescue_service.get_all_missions()
        assert missions == []

    def test_get_all_missions_returns_all(self, rescue_service: RescueService, auth_service: AuthService):
        """Test that all missions are returned."""
        # Create multiple users for different missions
        user1 = auth_service.register_user(name="User1", email="u1@test.com", password="password1")
        user2 = auth_service.register_user(name="User2", email="u2@test.com", password="password2")
        
        rescue_service.submit_rescue_request(user_id=user1, location="Location 1")
        rescue_service.submit_rescue_request(user_id=user2, location="Location 2")
        rescue_service.submit_rescue_request(user_id=user1, location="Location 3")
        
        missions = rescue_service.get_all_missions()
        assert len(missions) == 3

    def test_get_user_missions_filters_by_user(self, rescue_service: RescueService, auth_service: AuthService):
        """Test that user missions only returns missions for that user."""
        user1 = auth_service.register_user(name="User1", email="filter1@test.com", password="password1")
        user2 = auth_service.register_user(name="User2", email="filter2@test.com", password="password2")
        
        rescue_service.submit_rescue_request(user_id=user1, location="User 1 - Mission 1")
        rescue_service.submit_rescue_request(user_id=user2, location="User 2 - Mission 1")
        rescue_service.submit_rescue_request(user_id=user1, location="User 1 - Mission 2")
        
        user1_missions = rescue_service.get_user_missions(user1)
        user2_missions = rescue_service.get_user_missions(user2)
        
        assert len(user1_missions) == 2
        assert len(user2_missions) == 1
        
        # Verify correct missions
        for mission in user1_missions:
            assert mission["user_id"] == user1

    def test_get_user_missions_nonexistent_user(self, rescue_service: RescueService, test_user: int):
        """Test getting missions for user with no missions."""
        rescue_service.submit_rescue_request(user_id=test_user, location="Test")
        
        missions = rescue_service.get_user_missions(999)
        assert missions == []


class TestMissionNotes:
    """Tests for mission notes field composition."""

    def test_notes_contain_animal_info(self, rescue_service: RescueService, test_user: int):
        """Test that animal type and name are stored in dedicated columns."""
        rescue_service.submit_rescue_request(
            user_id=test_user,
            location="Test",
            animal_type="Cat",
            name="Orange tabby",
            details="Found near dumpster"
        )
        
        missions = rescue_service.get_all_missions()
        mission = missions[0]
        
        # Animal info is now stored in dedicated columns, not notes
        assert mission["animal_name"] == "Orange tabby"
        assert mission["animal_type"] == "Cat"
        assert mission["notes"] == "Found near dumpster"
