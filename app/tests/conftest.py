"""Pytest fixtures for test database and services."""
from __future__ import annotations

import os
import sys
import tempfile
from typing import Generator

import pytest

# Add the parent directory to path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from storage.database import Database
from services.auth_service import AuthService
from services.animal_service import AnimalService
from services.rescue_service import RescueService
from services.adoption_service import AdoptionService


@pytest.fixture
def temp_db() -> Generator[Database, None, None]:
    """Create a temporary database for testing.
    
    Each test gets a fresh database that is automatically cleaned up
    after the test completes.
    """
    # Create a temporary file for the database
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    
    try:
        db = Database(db_path)
        db.create_tables()
        yield db
    finally:
        # Clean up the temporary database file
        if os.path.exists(db_path):
            os.unlink(db_path)


@pytest.fixture
def auth_service(temp_db: Database) -> AuthService:
    """Create an AuthService with a temporary database."""
    return AuthService(temp_db, ensure_tables=False)


@pytest.fixture
def animal_service(temp_db: Database) -> AnimalService:
    """Create an AnimalService with a temporary database."""
    return AnimalService(temp_db, ensure_tables=False)


@pytest.fixture
def rescue_service(temp_db: Database) -> RescueService:
    """Create a RescueService with a temporary database."""
    return RescueService(temp_db, ensure_tables=False)


@pytest.fixture
def adoption_service(temp_db: Database) -> AdoptionService:
    """Create an AdoptionService with a temporary database."""
    return AdoptionService(temp_db, ensure_tables=False)


@pytest.fixture
def sample_user(auth_service: AuthService) -> dict:
    """Create and return a sample user for testing."""
    user_id = auth_service.register_user(
        name="Test User",
        email="testuser@example.com",
        password="testpass123",
        phone="123-456-7890",
        role="user"
    )
    return {
        "id": user_id,
        "name": "Test User",
        "email": "testuser@example.com",
        "password": "testpass123",
        "phone": "123-456-7890",
        "role": "user"
    }


@pytest.fixture
def sample_animal(animal_service: AnimalService) -> dict:
    """Create and return a sample animal for testing."""
    animal_id = animal_service.add_animal(
        name="Buddy",
        type="Dog",
        age=3,
        health_status="healthy"
    )
    return {
        "id": animal_id,
        "name": "Buddy",
        "type": "Dog",
        "age": 3,
        "health_status": "healthy"
    }
