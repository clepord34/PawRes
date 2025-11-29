"""Integration tests for adoption workflow."""
from __future__ import annotations

import pytest

from services.auth_service import AuthService
from services.animal_service import AnimalService
from services.adoption_service import AdoptionService


class TestCompleteAdoptionWorkflow:
    """Integration tests for the full adoption workflow."""

    def test_full_adoption_flow(
        self,
        auth_service: AuthService,
        animal_service: AnimalService,
        adoption_service: AdoptionService
    ):
        """Test complete adoption workflow from registration to approval."""
        # Step 1: Register a user
        user_id = auth_service.register_user(
            name="John Adopter",
            email="john@example.com",
            password="adopt123",
            phone="555-ADOPT"
        )
        assert user_id is not None
        
        # Step 2: User logs in
        user = auth_service.login("john@example.com", "adopt123")
        assert user is not None
        assert user["name"] == "John Adopter"
        
        # Step 3: Admin adds an animal (simulated)
        animal_id = animal_service.add_animal(
            name="Fluffy",
            type="Cat",
            age=2,
            health_status="healthy",
            breed="Siamese",
            description="Gentle and loves cuddles"
        )
        assert animal_id is not None
        
        # Step 4: User browses adoptable animals
        adoptable = animal_service.get_adoptable_animals()
        assert len(adoptable) == 1
        assert adoptable[0]["name"] == "Fluffy"
        
        # Step 5: User submits adoption request
        request_id = adoption_service.submit_request(
            user_id=user_id,
            animal_id=animal_id,
            contact="555-ADOPT",
            reason="I love cats and have experience with Siamese cats"
        )
        assert request_id is not None
        
        # Step 6: Verify request is pending
        requests = adoption_service.get_user_requests(user_id)
        assert len(requests) == 1
        assert requests[0]["status"] == "pending"
        
        # Step 7: Admin approves the request
        result = adoption_service.update_status(request_id, "approved")
        assert result is True
        
        # Step 8: Verify status updated
        requests = adoption_service.get_user_requests(user_id)
        assert requests[0]["status"] == "approved"

    def test_multiple_users_multiple_animals(
        self,
        auth_service: AuthService,
        animal_service: AnimalService,
        adoption_service: AdoptionService
    ):
        """Test workflow with multiple users requesting different animals."""
        # Create two users
        user1_id = auth_service.register_user(
            name="User One", email="user1@test.com", password="password1"
        )
        user2_id = auth_service.register_user(
            name="User Two", email="user2@test.com", password="password2"
        )
        
        # Create multiple animals
        dog_id = animal_service.add_animal(
            name="Rex", type="Dog", health_status="healthy"
        )
        cat_id = animal_service.add_animal(
            name="Mittens", type="Cat", health_status="available"
        )
        
        # User 1 requests the dog
        req1_id = adoption_service.submit_request(
            user_id=user1_id,
            animal_id=dog_id,
            contact="user1@test.com",
            reason="Want a dog companion"
        )
        
        # User 2 requests the cat
        req2_id = adoption_service.submit_request(
            user_id=user2_id,
            animal_id=cat_id,
            contact="user2@test.com",
            reason="Cat lover"
        )
        
        # Verify each user sees only their requests
        user1_requests = adoption_service.get_user_requests(user1_id)
        user2_requests = adoption_service.get_user_requests(user2_id)
        
        assert len(user1_requests) == 1
        assert len(user2_requests) == 1
        assert user1_requests[0]["animal_id"] == dog_id
        assert user2_requests[0]["animal_id"] == cat_id
        
        # Admin sees all requests
        all_requests = adoption_service.get_all_requests()
        assert len(all_requests) == 2


class TestAdoptionRequestManagement:
    """Integration tests for adoption request management."""

    def test_admin_can_approve_and_reject(
        self,
        auth_service: AuthService,
        animal_service: AnimalService,
        adoption_service: AdoptionService
    ):
        """Test that admin can approve some requests and reject others."""
        # Setup: Create user and multiple animals
        user_id = auth_service.register_user(
            name="Multi Adopter", email="multi@test.com", password="password123"
        )
        
        animal1_id = animal_service.add_animal(
            name="Animal1", type="Dog", health_status="healthy"
        )
        animal2_id = animal_service.add_animal(
            name="Animal2", type="Cat", health_status="healthy"
        )
        
        # User requests both animals
        req1_id = adoption_service.submit_request(
            user_id=user_id,
            animal_id=animal1_id,
            contact="test",
            reason="Want dog"
        )
        req2_id = adoption_service.submit_request(
            user_id=user_id,
            animal_id=animal2_id,
            contact="test",
            reason="Want cat"
        )
        
        # Admin approves first, rejects second
        adoption_service.update_status(req1_id, "approved")
        adoption_service.update_status(req2_id, "rejected")
        
        # Verify statuses
        all_requests = adoption_service.get_all_requests()
        statuses = {r["animal_id"]: r["status"] for r in all_requests}
        
        assert statuses[animal1_id] == "approved"
        assert statuses[animal2_id] == "rejected"

    def test_request_persists_user_and_animal_info(
        self,
        auth_service: AuthService,
        animal_service: AnimalService,
        adoption_service: AdoptionService
    ):
        """Test that adoption requests maintain relationship to user and animal."""
        # Create user and animal
        user_id = auth_service.register_user(
            name="Persistence Test",
            email="persist@test.com",
            password="password123"
        )
        animal_id = animal_service.add_animal(
            name="TestAnimal",
            type="Bird",
            health_status="healthy"
        )
        
        # Submit request
        adoption_service.submit_request(
            user_id=user_id,
            animal_id=animal_id,
            contact="persist@test.com",
            reason="Testing persistence"
        )
        
        # Get all requests (includes joined user/animal info)
        requests = adoption_service.get_all_requests()
        assert len(requests) == 1
        
        request = requests[0]
        # These fields come from JOINs in get_all_requests
        assert request["user_id"] == user_id
        assert request["animal_id"] == animal_id
        assert request["user_name"] == "Persistence Test"
        assert request["animal_name"] == "TestAnimal"
