"""Unit tests for models layer (data classes/DTOs)."""
from __future__ import annotations

from datetime import datetime

import pytest

from models.animal import Animal
from models.user import User
from models.rescue_mission import RescueMission
from models.adoption import AdoptionRequest
import app_config


class TestAnimalModel:
    """Tests for Animal model."""

    def test_animal_from_dict(self):
        """Test creating Animal from dictionary."""
        data = {
            "id": 1,
            "name": "Buddy",
            "species": "Dog",
            "age": 3,
            "status": "healthy",
            "photo": "buddy.jpg",
        }
        
        animal = Animal.from_dict(data)
        
        assert animal.id == 1
        assert animal.name == "Buddy"
        assert animal.species == "Dog"
        assert animal.age == 3
        assert animal.status == "healthy"
        assert animal.photo == "buddy.jpg"

    def test_animal_to_dict(self):
        """Test converting Animal to dictionary."""
        animal = Animal(
            id=1,
            name="Whiskers",
            species="Cat",
            age=2,
            status="available"
        )
        
        data = animal.to_dict()
        
        assert data["id"] == 1
        assert data["name"] == "Whiskers"
        assert data["species"] == "Cat"
        assert data["age"] == 2
        assert data["status"] == "available"

    def test_animal_is_adoptable_healthy(self):
        """Test is_adoptable for healthy animals."""
        animal = Animal(status="healthy")
        assert animal.is_adoptable is True

    def test_animal_is_adoptable_available(self):
        """Test is_adoptable for available status."""
        animal = Animal(status="available")
        assert animal.is_adoptable is True

    def test_animal_is_adoptable_injured(self):
        """Test is_adoptable returns False for injured."""
        animal = Animal(status="injured")
        assert animal.is_adoptable is False

    def test_animal_is_adopted(self):
        """Test is_adopted property."""
        adopted_animal = Animal(status="adopted")
        healthy_animal = Animal(status="healthy")
        
        assert adopted_animal.is_adopted is True
        assert healthy_animal.is_adopted is False

    def test_animal_default_values(self):
        """Test Animal default values."""
        animal = Animal()
        
        assert animal.id is None
        assert animal.name == ""
        assert animal.species == ""
        assert animal.age is None
        assert animal.status == app_config.AnimalStatus.AVAILABLE


class TestUserModel:
    """Tests for User model."""

    def test_user_from_dict(self):
        """Test creating User from dictionary."""
        data = {
            "id": 1,
            "name": "John Doe",
            "email": "john@example.com",
            "phone": "123-456-7890",
            "role": "admin",
            "oauth_provider": "google",
        }
        
        user = User.from_dict(data)
        
        assert user.id == 1
        assert user.name == "John Doe"
        assert user.email == "john@example.com"
        assert user.phone == "123-456-7890"
        assert user.role == "admin"
        assert user.oauth_provider == "google"

    def test_user_to_dict_excludes_sensitive_by_default(self):
        """Test to_dict excludes password fields by default."""
        user = User(
            id=1,
            name="Test",
            email="test@test.com",
            password_hash="abc123",
            password_salt="xyz789"
        )
        
        data = user.to_dict(include_sensitive=False)
        
        assert "password_hash" not in data
        assert "password_salt" not in data
        assert data["name"] == "Test"

    def test_user_to_dict_includes_sensitive_when_requested(self):
        """Test to_dict includes password fields when requested."""
        user = User(
            id=1,
            name="Test",
            email="test@test.com",
            password_hash="abc123",
            password_salt="xyz789"
        )
        
        data = user.to_dict(include_sensitive=True)
        
        assert data["password_hash"] == "abc123"
        assert data["password_salt"] == "xyz789"

    def test_user_is_admin(self):
        """Test is_admin property."""
        admin = User(role="admin")
        user = User(role="user")
        
        assert admin.is_admin is True
        assert user.is_admin is False

    def test_user_is_oauth_user(self):
        """Test is_oauth_user property."""
        oauth_user = User(oauth_provider="google")
        password_user = User(oauth_provider=None)
        
        assert oauth_user.is_oauth_user is True
        assert password_user.is_oauth_user is False

    def test_user_default_role(self):
        """Test default role is 'user'."""
        user = User()
        assert user.role == "user"


class TestRescueMissionModel:
    """Tests for RescueMission model."""

    def test_rescue_mission_from_dict(self):
        """Test creating RescueMission from dictionary."""
        data = {
            "id": 1,
            "user_id": 10,
            "location": "123 Main St",
            "latitude": 14.5,
            "longitude": 120.9,
            "status": "pending",
            "animal_type": "Dog",
            "animal_name": "Stray Dog",
            "urgency": "high",
        }
        
        mission = RescueMission.from_dict(data)
        
        assert mission.id == 1
        assert mission.user_id == 10
        assert mission.location == "123 Main St"
        assert mission.latitude == 14.5
        assert mission.longitude == 120.9
        assert mission.status == "pending"
        assert mission.animal_type == "Dog"
        assert mission.animal_name == "Stray Dog"
        assert mission.urgency == "high"

    def test_rescue_mission_to_dict(self):
        """Test converting RescueMission to dictionary."""
        mission = RescueMission(
            id=1,
            location="Test Location",
            status="on-going",
            urgency="medium"
        )
        
        data = mission.to_dict()
        
        assert data["id"] == 1
        assert data["location"] == "Test Location"
        assert data["status"] == "on-going"
        assert data["urgency"] == "medium"

    def test_rescue_mission_is_active_pending(self):
        """Test is_active for pending missions."""
        mission = RescueMission(status="pending")
        assert mission.is_active is True

    def test_rescue_mission_is_active_ongoing(self):
        """Test is_active for on-going missions."""
        mission = RescueMission(status="on-going")
        assert mission.is_active is True

    def test_rescue_mission_is_active_rescued(self):
        """Test is_active returns False for rescued missions."""
        mission = RescueMission(status="rescued")
        assert mission.is_active is False

    def test_rescue_mission_has_coordinates(self):
        """Test has_coordinates property."""
        with_coords = RescueMission(latitude=14.5, longitude=120.9)
        without_coords = RescueMission(latitude=None, longitude=None)
        partial_coords = RescueMission(latitude=14.5, longitude=None)
        
        assert with_coords.has_coordinates is True
        assert without_coords.has_coordinates is False
        assert partial_coords.has_coordinates is False

    def test_rescue_mission_is_emergency(self):
        """Test is_emergency property."""
        high_urgency = RescueMission(urgency="high")
        medium_urgency = RescueMission(urgency="medium")
        low_urgency = RescueMission(urgency="low")
        
        assert high_urgency.is_emergency is True
        assert medium_urgency.is_emergency is False
        assert low_urgency.is_emergency is False

    def test_rescue_mission_default_status(self):
        """Test default status is pending."""
        mission = RescueMission()
        assert mission.status == app_config.RescueStatus.PENDING

    def test_rescue_mission_default_urgency(self):
        """Test default urgency is medium."""
        mission = RescueMission()
        assert mission.urgency == app_config.Urgency.MEDIUM


class TestAdoptionRequestModel:
    """Tests for AdoptionRequest model."""

    def test_adoption_request_from_dict(self):
        """Test creating AdoptionRequest from dictionary."""
        data = {
            "id": 1,
            "user_id": 5,
            "animal_id": 10,
            "contact": "555-1234",
            "reason": "I love dogs",
            "status": "pending",
            "animal_name": "Buddy",
            "animal_species": "Dog",
        }
        
        request = AdoptionRequest.from_dict(data)
        
        assert request.id == 1
        assert request.user_id == 5
        assert request.animal_id == 10
        assert request.contact == "555-1234"
        assert request.reason == "I love dogs"
        assert request.status == "pending"
        assert request.animal_name == "Buddy"
        assert request.animal_species == "Dog"

    def test_adoption_request_to_dict(self):
        """Test converting AdoptionRequest to dictionary."""
        request = AdoptionRequest(
            id=1,
            user_id=5,
            animal_id=10,
            contact="test@test.com",
            reason="Testing",
            status="approved"
        )
        
        data = request.to_dict()
        
        assert data["id"] == 1
        assert data["user_id"] == 5
        assert data["animal_id"] == 10
        assert data["status"] == "approved"

    def test_adoption_request_is_pending(self):
        """Test is_pending property."""
        pending = AdoptionRequest(status="pending")
        approved = AdoptionRequest(status="approved")
        
        assert pending.is_pending is True
        assert approved.is_pending is False

    def test_adoption_request_is_approved(self):
        """Test is_approved property."""
        approved = AdoptionRequest(status="approved")
        denied = AdoptionRequest(status="denied")
        
        assert approved.is_approved is True
        assert denied.is_approved is False

    def test_adoption_request_is_denied(self):
        """Test is_denied property."""
        denied = AdoptionRequest(status="denied")
        pending = AdoptionRequest(status="pending")
        
        assert denied.is_denied is True
        assert pending.is_denied is False

    def test_adoption_request_animal_was_removed(self):
        """Test animal_was_removed property."""
        with_animal = AdoptionRequest(animal_id=10)
        without_animal = AdoptionRequest(animal_id=None)
        
        assert with_animal.animal_was_removed is False
        assert without_animal.animal_was_removed is True

    def test_adoption_request_default_status(self):
        """Test default status is pending."""
        request = AdoptionRequest()
        assert request.status == app_config.AdoptionStatus.PENDING


class TestStatusConstants:
    """Tests for status constant classes."""

    def test_rescue_status_normalize(self):
        """Test RescueStatus.normalize()."""
        assert app_config.RescueStatus.normalize("pending") == "pending"
        assert app_config.RescueStatus.normalize("on-going") == "on-going"
        assert app_config.RescueStatus.normalize("ongoing") == "on-going"
        assert app_config.RescueStatus.normalize("in_progress") == "on-going"
        assert app_config.RescueStatus.normalize("rescued") == "rescued"
        assert app_config.RescueStatus.normalize("completed") == "rescued"
        assert app_config.RescueStatus.normalize("PENDING") == "pending"

    def test_rescue_status_is_final(self):
        """Test RescueStatus.is_final()."""
        assert app_config.RescueStatus.is_final("rescued") is True
        assert app_config.RescueStatus.is_final("failed") is True
        assert app_config.RescueStatus.is_final("cancelled") is True
        assert app_config.RescueStatus.is_final("pending") is False
        assert app_config.RescueStatus.is_final("on-going") is False

    def test_rescue_status_is_archived(self):
        """Test RescueStatus.is_archived()."""
        assert app_config.RescueStatus.is_archived("rescued|archived") is True
        assert app_config.RescueStatus.is_archived("pending|archived") is True
        assert app_config.RescueStatus.is_archived("rescued") is False
        assert app_config.RescueStatus.is_archived("pending") is False

    def test_rescue_status_make_archived(self):
        """Test RescueStatus.make_archived()."""
        assert app_config.RescueStatus.make_archived("rescued") == "rescued|archived"
        assert app_config.RescueStatus.make_archived("pending") == "pending|archived"

    def test_rescue_status_get_base_status(self):
        """Test RescueStatus.get_base_status()."""
        assert app_config.RescueStatus.get_base_status("rescued|archived") == "rescued"
        assert app_config.RescueStatus.get_base_status("pending") == "pending"

    def test_adoption_status_normalize(self):
        """Test AdoptionStatus.normalize()."""
        assert app_config.AdoptionStatus.normalize("pending") == "pending"
        assert app_config.AdoptionStatus.normalize("approved") == "approved"
        assert app_config.AdoptionStatus.normalize("adopted") == "approved"
        assert app_config.AdoptionStatus.normalize("denied") == "denied"
        assert app_config.AdoptionStatus.normalize("rejected") == "denied"

    def test_animal_status_is_adoptable(self):
        """Test AnimalStatus.is_adoptable()."""
        assert app_config.AnimalStatus.is_adoptable("healthy") is True
        assert app_config.AnimalStatus.is_adoptable("available") is True
        assert app_config.AnimalStatus.is_adoptable("injured") is False
        assert app_config.AnimalStatus.is_adoptable("adopted") is False

    def test_urgency_get_label(self):
        """Test Urgency.get_label()."""
        assert "Immediate help" in app_config.Urgency.get_label("high")
        assert "attention soon" in app_config.Urgency.get_label("medium")
        assert "safe" in app_config.Urgency.get_label("low")

    def test_urgency_from_label(self):
        """Test Urgency.from_label()."""
        assert app_config.Urgency.from_label("High - Immediate help needed") == "high"
        assert app_config.Urgency.from_label("Medium - Needs attention") == "medium"
        assert app_config.Urgency.from_label("Low - Animal appears safe") == "low"
        assert app_config.Urgency.from_label("") == "medium"  # Default
