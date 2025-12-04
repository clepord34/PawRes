"""Unit tests for AnimalService."""
from __future__ import annotations

import pytest

from services.animal_service import AnimalService


class TestAddAnimal:
    """Tests for adding animals to the system."""

    def test_add_animal_basic(self, animal_service: AnimalService):
        """Test adding an animal with basic required fields."""
        animal_id = animal_service.add_animal(
            name="Max",
            type="Dog",
            age=2,
            health_status="healthy"
        )
        
        assert animal_id is not None
        assert isinstance(animal_id, int)
        assert animal_id > 0

    def test_add_animal_with_all_fields(self, animal_service: AnimalService):
        """Test adding an animal with all optional fields."""
        animal_id = animal_service.add_animal(
            name="Whiskers",
            type="Cat",
            age=5,
            health_status="healthy"
        )
        
        # Verify the animal was created with all fields
        animal = animal_service.get_animal_by_id(animal_id)
        assert animal is not None
        assert animal["name"] == "Whiskers"
        assert animal["species"] == "Cat"  # Note: 'type' maps to 'species' in DB
        assert animal["age"] == 5
        assert animal["status"] == "healthy"  # Note: 'health_status' maps to 'status'

    def test_add_multiple_animals(self, animal_service: AnimalService):
        """Test adding multiple animals."""
        id1 = animal_service.add_animal(name="Dog1", type="Dog", health_status="healthy")
        id2 = animal_service.add_animal(name="Cat1", type="Cat", health_status="healthy")
        id3 = animal_service.add_animal(name="Dog2", type="Dog", health_status="injured")
        
        # All should have unique IDs
        assert id1 != id2 != id3
        
        # Should be able to retrieve all
        animals = animal_service.get_all_animals()
        assert len(animals) == 3


class TestGetAnimals:
    """Tests for retrieving animals."""

    def test_get_all_animals_empty(self, animal_service: AnimalService):
        """Test getting animals when database is empty."""
        animals = animal_service.get_all_animals()
        assert animals == []

    def test_get_all_animals_returns_list(self, animal_service: AnimalService):
        """Test that get_all_animals returns a list of dicts."""
        animal_service.add_animal(name="Test", type="Dog", health_status="healthy")
        
        animals = animal_service.get_all_animals()
        assert isinstance(animals, list)
        assert len(animals) == 1
        assert isinstance(animals[0], dict)

    def test_get_animal_by_id_found(self, animal_service: AnimalService):
        """Test retrieving a specific animal by ID."""
        animal_id = animal_service.add_animal(
            name="FindMe",
            type="Bird",
            age=1,
            health_status="healthy"
        )
        
        animal = animal_service.get_animal_by_id(animal_id)
        assert animal is not None
        assert animal["name"] == "FindMe"
        assert animal["id"] == animal_id

    def test_get_animal_by_id_not_found(self, animal_service: AnimalService):
        """Test retrieving a non-existent animal returns None."""
        animal = animal_service.get_animal_by_id(99999)
        assert animal is None


class TestUpdateAnimal:
    """Tests for updating animal information."""

    def test_update_animal_single_field(self, animal_service: AnimalService):
        """Test updating a single field of an animal."""
        animal_id = animal_service.add_animal(
            name="Original",
            type="Dog",
            health_status="healthy"
        )
        
        result = animal_service.update_animal(animal_id, name="Updated")
        assert result is True
        
        animal = animal_service.get_animal_by_id(animal_id)
        assert animal["name"] == "Updated"

    def test_update_animal_multiple_fields(self, animal_service: AnimalService):
        """Test updating multiple fields at once."""
        animal_id = animal_service.add_animal(
            name="Multi",
            type="Dog",
            age=1,
            health_status="healthy"
        )
        
        result = animal_service.update_animal(
            animal_id,
            name="MultiUpdated",
            age=2,
            health_status="recovering"
        )
        assert result is True
        
        animal = animal_service.get_animal_by_id(animal_id)
        assert animal["name"] == "MultiUpdated"
        assert animal["age"] == 2
        assert animal["status"] == "recovering"

    def test_update_animal_no_fields(self, animal_service: AnimalService):
        """Test that updating with no fields returns False."""
        animal_id = animal_service.add_animal(name="NoUpdate", type="Cat", health_status="healthy")
        
        result = animal_service.update_animal(animal_id)
        assert result is False


class TestAdoptableAnimals:
    """Tests for filtering adoptable animals."""

    def test_get_adoptable_animals_filters_correctly(self, animal_service: AnimalService):
        """Test that only adoptable status animals are returned."""
        # Add animals with various statuses
        animal_service.add_animal(name="Healthy", type="Dog", health_status="healthy")
        animal_service.add_animal(name="Available", type="Cat", health_status="available")
        animal_service.add_animal(name="Injured", type="Dog", health_status="injured")
        animal_service.add_animal(name="Adoptable", type="Bird", health_status="adoptable")
        
        adoptable = animal_service.get_adoptable_animals()
        
        # Should only return healthy, available, adoptable (not injured)
        assert len(adoptable) == 3
        names = [a["name"] for a in adoptable]
        assert "Healthy" in names
        assert "Available" in names
        assert "Adoptable" in names
        assert "Injured" not in names

    def test_get_adoptable_animals_empty(self, animal_service: AnimalService):
        """Test adoptable returns empty when no animals match."""
        animal_service.add_animal(name="Sick", type="Dog", health_status="injured")
        animal_service.add_animal(name="Recovering", type="Cat", health_status="recovering")
        
        adoptable = animal_service.get_adoptable_animals()
        assert adoptable == []
