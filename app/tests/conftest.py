"""Test fixtures and configuration for pytest."""
import os
import tempfile
import shutil
from pathlib import Path
import pytest
from datetime import datetime, timedelta

# Add app directory to path so we can import modules
import sys
app_dir = Path(__file__).parent.parent
sys.path.insert(0, str(app_dir))

from storage.database import Database
from services.auth_service import AuthService
from services.animal_service import AnimalService
from services.rescue_service import RescueService
from services.adoption_service import AdoptionService
from services.analytics_service import AnalyticsService
from services.import_service import ImportService
from services.logging_service import get_auth_logger, get_admin_logger, get_security_logger
from services.user_service import UserService
from services.password_policy import PasswordPolicy
import app_config


# =============================================================================
# DATABASE FIXTURES
# =============================================================================

@pytest.fixture
def temp_db():
    """Create a temporary database for testing.
    
    Yields:
        Database: A Database instance with a temporary file
    """
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    
    db = Database(db_path)
    db.create_tables()
    
    yield db
    
    # Cleanup
    try:
        os.unlink(db_path)
    except Exception:
        pass


@pytest.fixture
def temp_db_path():
    """Create a temporary database path (for services that accept path strings).
    
    Yields:
        str: Path to temporary database file
    """
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    
    db = Database(db_path)
    db.create_tables()
    
    yield db_path
    
    # Cleanup
    try:
        os.unlink(db_path)
    except Exception:
        pass


# =============================================================================
# SERVICE FIXTURES
# =============================================================================

@pytest.fixture
def auth_service(temp_db_path):
    """Auth service with temporary database."""
    return AuthService(temp_db_path)


@pytest.fixture
def animal_service(temp_db_path):
    """Animal service with temporary database."""
    return AnimalService(temp_db_path)


@pytest.fixture
def rescue_service(temp_db_path):
    """Rescue service with temporary database."""
    return RescueService(temp_db_path)


@pytest.fixture
def adoption_service(temp_db_path):
    """Adoption service with temporary database."""
    return AdoptionService(temp_db_path)


@pytest.fixture
def analytics_service(temp_db_path):
    """Analytics service with temporary database."""
    return AnalyticsService(temp_db_path)


@pytest.fixture
def import_service(temp_db_path):
    """Import service with temporary database."""
    return ImportService(temp_db_path)


@pytest.fixture
def logging_service():
    """Logging service (no database needed) - returns a dict of loggers."""
    return {
        "auth_logger": get_auth_logger(),
        "admin_logger": get_admin_logger(),
        "security_logger": get_security_logger()
    }


@pytest.fixture
def user_service(temp_db_path):
    """User service with temporary database."""
    return UserService(temp_db_path)


@pytest.fixture
def password_policy(temp_db_path):
    """Password policy with temporary database."""
    return PasswordPolicy()


# =============================================================================
# SAMPLE DATA FIXTURES
# =============================================================================

@pytest.fixture
def sample_user(auth_service):
    """Create a test user.
    
    Returns:
        dict: User data with id, email, password, name, role
    """
    user_id = auth_service.register_user(
        name="Test User",
        email="testuser@test.com",
        password="TestPass@123",
        role="user",
        skip_policy=True
    )
    return {
        "id": user_id,
        "email": "testuser@test.com",
        "password": "TestPass@123",
        "name": "Test User",
        "role": "user"
    }


@pytest.fixture
def sample_admin(auth_service):
    """Create a test admin.
    
    Returns:
        dict: Admin data with id, email, password, name, role
    """
    admin_id = auth_service.register_user(
        name="Test Admin",
        email="testadmin@test.com",
        password="AdminPass@123",
        role="admin",
        skip_policy=True
    )
    return {
        "id": admin_id,
        "email": "testadmin@test.com",
        "password": "AdminPass@123",
        "name": "Test Admin",
        "role": "admin"
    }


@pytest.fixture
def sample_animal(animal_service, sample_admin):
    """Create a test animal.
    
    Returns:
        dict: Animal data with id
    """
    animal_id = animal_service.add_animal(
        name="Test Dog",
        type="dog",
        breed="Labrador",
        age=3,
        health_status="healthy",
        photo=None
    )
    return {
        "id": animal_id,
        "name": "Test Dog",
        "type": "dog",
        "breed": "Labrador",
        "age": 3,
        "gender": "male",
        "health_status": "healthy"
    }


@pytest.fixture
def sample_rescue_mission(rescue_service, sample_user):
    """Create a test rescue mission.
    
    Returns:
        dict: Rescue mission data with id
    """
    mission_id = rescue_service.submit_rescue_request(
        user_id=sample_user["id"],
        animal_type="dog",
        breed="Unknown",
        location="Test Location",
        latitude=13.5,
        longitude=123.3,
        urgency="medium",
        details="Dog needs help. Found near park"
    )
    return {
        "id": mission_id,
        "reporter_id": sample_user["id"],
        "animal_type": "dog",
        "status": "pending"
    }


@pytest.fixture
def sample_adoption_request(adoption_service, sample_user, sample_animal):
    """Create a test adoption request.
    
    Returns:
        dict: Adoption request data with id
    """
    request_id = adoption_service.submit_request(
        user_id=sample_user["id"],
        animal_id=sample_animal["id"],
        contact=sample_user["email"],
        reason="I love dogs"
    )
    return {
        "id": request_id,
        "user_id": sample_user["id"],
        "animal_id": sample_animal["id"],
        "status": "pending"
    }


# =============================================================================
# TEMP PHOTO DIRECTORY FIXTURES
# =============================================================================

@pytest.fixture
def temp_photo_dir():
    """Create a temporary directory for test photos (uses storage/temp/).
    
    Yields:
        Path: Temporary directory path
    """
    # Use app's temp directory instead of uploads
    temp_dir = app_config.TEMP_DIR / f"test_photos_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    yield temp_dir
    
    # Cleanup
    try:
        shutil.rmtree(temp_dir)
    except Exception:
        pass


@pytest.fixture
def sample_photo_base64():
    """Return a small base64-encoded test image (1x1 PNG).
    
    Returns:
        str: Base64-encoded PNG image data
    """
    # 1x1 red pixel PNG (67 bytes)
    return (
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8DwHwAFBQIAX8jx"
        "0gAAAABJRU5ErkJggg=="
    )


# =============================================================================
# TIME MANIPULATION FIXTURES (for session timeout testing)
# =============================================================================

@pytest.fixture
def mock_datetime(monkeypatch):
    """Mock datetime.now() for testing time-based features.
    
    Returns:
        function: A function to set the current time
    """
    frozen_time = [datetime.now()]
    
    class MockDateTime:
        @staticmethod
        def now(tz=None):
            return frozen_time[0]
        
        @staticmethod
        def utcnow():
            return frozen_time[0]
    
    def set_time(dt):
        frozen_time[0] = dt
    
    monkeypatch.setattr("datetime.datetime", MockDateTime)
    
    return set_time


# =============================================================================
# DATABASE HELPERS
# =============================================================================

def get_user_by_email(db: Database, email: str) -> dict:
    """Helper to fetch user by email."""
    return db.fetch_one(
        "SELECT * FROM users WHERE email = ?",
        (email,)
    )


def get_animal_by_id(db: Database, animal_id: int) -> dict:
    """Helper to fetch animal by ID."""
    return db.fetch_one(
        "SELECT * FROM animals WHERE id = ?",
        (animal_id,)
    )


def get_rescue_by_id(db: Database, rescue_id: int) -> dict:
    """Helper to fetch rescue mission by ID."""
    return db.fetch_one(
        "SELECT * FROM rescue_missions WHERE id = ?",
        (rescue_id,)
    )


def get_adoption_by_id(db: Database, adoption_id: int) -> dict:
    """Helper to fetch adoption request by ID."""
    return db.fetch_one(
        "SELECT * FROM adoption_requests WHERE id = ?",
        (adoption_id,)
    )
