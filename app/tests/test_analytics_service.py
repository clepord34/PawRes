"""Unit tests for AnalyticsService."""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List

import pytest

from services.analytics_service import AnalyticsService
from services.animal_service import AnimalService
from services.rescue_service import RescueService
from services.adoption_service import AdoptionService
from storage.database import Database
import app_config


@pytest.fixture
def db(tmp_path):
    """Create a temporary database for testing."""
    db_path = str(tmp_path / "test_analytics.db")
    database = Database(db_path)
    database.create_tables()
    return database


@pytest.fixture
def analytics_service(db):
    """Create AnalyticsService with test database."""
    return AnalyticsService(db)


@pytest.fixture
def animal_service(db):
    """Create AnimalService with test database."""
    return AnimalService(db)


@pytest.fixture
def rescue_service(db):
    """Create RescueService with test database."""
    return RescueService(db)


@pytest.fixture
def adoption_service(db):
    """Create AdoptionService with test database."""
    return AdoptionService(db)


class TestAnalyticsServiceBasic:
    """Basic tests for AnalyticsService initialization."""

    def test_create_with_database_instance(self, db):
        """Test creating service with Database instance."""
        service = AnalyticsService(db)
        assert service.db is db

    def test_create_with_db_path(self, tmp_path):
        """Test creating service with database path string."""
        db_path = str(tmp_path / "test.db")
        service = AnalyticsService(db_path)
        assert service.db is not None

    def test_has_dependent_services(self, analytics_service):
        """Test that service has all dependent services initialized."""
        assert analytics_service.animal_service is not None
        assert analytics_service.rescue_service is not None
        assert analytics_service.adoption_service is not None


class TestAnimalStatistics:
    """Tests for animal statistics methods."""

    def test_empty_animal_statistics(self, analytics_service):
        """Test statistics with no animals."""
        type_dist, status_counts = analytics_service.get_animal_statistics()
        
        assert type_dist == {}
        assert status_counts == {"healthy": 0, "recovering": 0, "injured": 0}

    def test_animal_type_distribution(self, analytics_service, animal_service):
        """Test type distribution calculation."""
        # Add animals
        animal_service.add_animal("Dog1", "Dog", 2, "healthy")
        animal_service.add_animal("Dog2", "Dog", 3, "healthy")
        animal_service.add_animal("Cat1", "Cat", 1, "healthy")
        
        type_dist, _ = analytics_service.get_animal_statistics()
        
        assert type_dist["Dog"] == 2
        assert type_dist["Cat"] == 1

    def test_animal_status_counts(self, analytics_service, animal_service):
        """Test health status counting."""
        animal_service.add_animal("Healthy1", "Dog", 2, "healthy")
        animal_service.add_animal("Healthy2", "Cat", 3, "healthy")
        animal_service.add_animal("Injured1", "Dog", 4, "injured")
        animal_service.add_animal("Recovering1", "Cat", 2, "recovering")
        
        _, status_counts = analytics_service.get_animal_statistics()
        
        assert status_counts["healthy"] == 2
        assert status_counts["injured"] == 1
        assert status_counts["recovering"] == 1

    def test_animal_status_excludes_adopted(self, analytics_service, animal_service):
        """Test that adopted animals are not in health status counts."""
        animal_service.add_animal("Healthy", "Dog", 2, "healthy")
        animal_service.add_animal("Adopted", "Cat", 3, "adopted")
        
        _, status_counts = analytics_service.get_animal_statistics()
        
        # Total should be 1 (only healthy, not adopted)
        assert status_counts["healthy"] == 1
        assert status_counts["injured"] == 0
        assert status_counts["recovering"] == 0


class TestDashboardStats:
    """Tests for dashboard statistics."""

    def test_empty_dashboard_stats(self, analytics_service):
        """Test dashboard stats with no data."""
        stats = analytics_service.get_dashboard_stats()
        
        assert stats["total_animals"] == 0
        assert stats["total_adoptions"] == 0
        assert stats["pending_applications"] == 0

    def test_dashboard_stats_with_data(self, db, analytics_service):
        """Test dashboard stats with data."""
        # Use the analytics_service's internal animal_service to ensure same db
        analytics_service.animal_service.add_animal("Dog1", "Dog", 2, "healthy")
        analytics_service.animal_service.add_animal("Cat1", "Cat", 1, "healthy")
        
        # Clear cache to get fresh data
        analytics_service.invalidate_cache()
        
        stats = analytics_service.get_dashboard_stats()
        
        assert stats["total_animals"] == 2


class TestRescueStatusDistribution:
    """Tests for rescue status distribution."""

    def test_empty_rescue_distribution(self, analytics_service):
        """Test rescue distribution with no missions."""
        dist = analytics_service.get_rescue_status_distribution()
        
        assert dist["pending"] == 0
        assert dist["on-going"] == 0
        assert dist["rescued"] == 0
        assert dist["failed"] == 0

    def test_rescue_distribution_counts(self, db, analytics_service):
        """Test rescue distribution counting."""
        rescue_service = RescueService(db)
        
        # Create test user
        db.execute(
            "INSERT INTO users (name, email, password_hash, password_salt, role) VALUES (?, ?, ?, ?, ?)",
            ("Test", "test@test.com", "hash", "salt", "user")
        )
        
        # Add missions with different statuses using submit_rescue_request
        rescue_service.submit_rescue_request(
            user_id=1,
            location="Location 1",
            animal_type="Dog",
            name="Dog1",
            details="Notes",
            reporter_name="Reporter",
            reporter_phone="123",
            urgency="medium"
        )
        rescue_service.submit_rescue_request(
            user_id=1,
            location="Location 2",
            animal_type="Cat",
            name="Cat1",
            details="Notes",
            reporter_name="Reporter",
            reporter_phone="123",
            urgency="high"
        )
        
        dist = analytics_service.get_rescue_status_distribution()
        
        # Both should be pending by default
        assert dist["pending"] == 2


class TestAdoptionStatusDistribution:
    """Tests for adoption status distribution."""

    def test_empty_adoption_distribution(self, analytics_service):
        """Test adoption distribution with no requests."""
        dist = analytics_service.get_adoption_status_distribution()
        
        assert dist["pending"] == 0
        assert dist["approved"] == 0
        assert dist["denied"] == 0


class TestUrgencyDistribution:
    """Tests for urgency distribution."""

    def test_empty_urgency_distribution(self, analytics_service):
        """Test urgency distribution with no missions."""
        dist = analytics_service.get_urgency_distribution()
        
        assert dist["low"] == 0
        assert dist["medium"] == 0
        assert dist["high"] == 0

    def test_urgency_distribution_counts(self, db, analytics_service):
        """Test urgency distribution counting."""
        rescue_service = RescueService(db)
        
        # Create test user
        db.execute(
            "INSERT INTO users (name, email, password_hash, password_salt, role) VALUES (?, ?, ?, ?, ?)",
            ("Test", "test@test.com", "hash", "salt", "user")
        )
        
        # Add missions with different urgencies using submit_rescue_request
        rescue_service.submit_rescue_request(
            user_id=1, location="Loc1", animal_type="Dog", name="D1",
            details="", reporter_name="R", reporter_phone="123", urgency="low"
        )
        rescue_service.submit_rescue_request(
            user_id=1, location="Loc2", animal_type="Cat", name="C1",
            details="", reporter_name="R", reporter_phone="123", urgency="high"
        )
        rescue_service.submit_rescue_request(
            user_id=1, location="Loc3", animal_type="Dog", name="D2",
            details="", reporter_name="R", reporter_phone="123", urgency="high"
        )
        
        dist = analytics_service.get_urgency_distribution()
        
        assert dist["low"] == 1
        assert dist["medium"] == 0
        assert dist["high"] == 2


class TestUserActivityStats:
    """Tests for user activity statistics."""

    def test_user_activity_no_activity(self, db, analytics_service):
        """Test user activity with no activity."""
        # Create test user
        db.execute(
            "INSERT INTO users (name, email, password_hash, password_salt, role) VALUES (?, ?, ?, ?, ?)",
            ("Test", "test@test.com", "hash", "salt", "user")
        )
        
        stats = analytics_service.get_user_activity_stats(user_id=1)
        
        assert stats["total_adoptions"] == 0
        assert stats["rescue_reports_filed"] == 0
        assert stats["pending_adoption_requests"] == 0
        assert stats["ongoing_rescue_missions"] == 0

    def test_user_activity_with_rescues(self, db, analytics_service):
        """Test user activity with rescue missions."""
        # Create test user
        db.execute(
            "INSERT INTO users (name, email, password_hash, password_salt, role) VALUES (?, ?, ?, ?, ?)",
            ("Test", "test@test.com", "hash", "salt", "user")
        )
        
        rescue_service = RescueService(db)
        rescue_service.submit_rescue_request(
            user_id=1, location="Loc1", animal_type="Dog", name="D1",
            details="", reporter_name="R", reporter_phone="123", urgency="medium"
        )
        rescue_service.submit_rescue_request(
            user_id=1, location="Loc2", animal_type="Cat", name="C1",
            details="", reporter_name="R", reporter_phone="123", urgency="high"
        )
        
        stats = analytics_service.get_user_activity_stats(user_id=1)
        
        assert stats["rescue_reports_filed"] == 2


class TestChartData:
    """Tests for chart data generation."""

    def test_chart_data_empty(self, analytics_service):
        """Test chart data with no data."""
        (day_labels, rescued, adopted), type_dist, status_counts = analytics_service.get_chart_data()
        
        assert len(day_labels) == 30
        assert all(c == 0 for c in rescued)
        assert all(c == 0 for c in adopted)
        assert type_dist == {}

    def test_chart_data_14_days_empty(self, analytics_service):
        """Test 14-day chart data with no data."""
        day_labels, rescued, adopted = analytics_service.get_chart_data_14_days()
        
        assert len(day_labels) == 14
        assert all(c == 0 for c in rescued)
        assert all(c == 0 for c in adopted)


class TestUserChartData:
    """Tests for user-specific chart data."""

    def test_user_chart_data_empty(self, db, analytics_service):
        """Test user chart data with no activity."""
        db.execute(
            "INSERT INTO users (name, email, password_hash, password_salt, role) VALUES (?, ?, ?, ?, ?)",
            ("Test", "test@test.com", "hash", "salt", "user")
        )
        
        day_labels, rescues, adoptions = analytics_service.get_user_chart_data(user_id=1)
        
        assert len(day_labels) == 30
        assert all(c == 0 for c in rescues)
        assert all(c == 0 for c in adoptions)


class TestMonthlyChanges:
    """Tests for monthly change calculations."""

    def test_monthly_changes_no_data(self, analytics_service):
        """Test monthly changes with no data."""
        changes = analytics_service.get_monthly_changes()
        
        assert "animals_change" in changes
        assert "rescues_change" in changes
        assert "adoptions_change" in changes
        assert "pending_change" in changes

    def test_monthly_changes_format(self, analytics_service):
        """Test monthly changes return formatted strings."""
        changes = analytics_service.get_monthly_changes()
        
        for key in ["animals_change", "rescues_change", "adoptions_change", "pending_change"]:
            assert isinstance(changes[key], str)


class TestUserInsights:
    """Tests for user insights generation."""

    def test_user_insights_no_activity(self, db, analytics_service):
        """Test insights for user with no activity."""
        db.execute(
            "INSERT INTO users (name, email, password_hash, password_salt, role) VALUES (?, ?, ?, ?, ?)",
            ("Test", "test@test.com", "hash", "salt", "user")
        )
        
        insights = analytics_service.get_user_insights(user_id=1)
        
        assert "rescue_insight" in insights
        assert "adoption_insight" in insights
        assert "activity_insight" in insights
        
        # Check insight structure
        assert "headline" in insights["rescue_insight"]
        assert "detail" in insights["rescue_insight"]
        assert "action" in insights["rescue_insight"]


class TestChartInsights:
    """Tests for chart insights generation."""

    def test_chart_insights_empty_data(self, analytics_service):
        """Test chart insights with no data."""
        insights = analytics_service.get_chart_insights()
        
        assert "rescue_insight" in insights
        assert "adoption_insight" in insights
        assert "health_insight" in insights
        
        # Each insight should have headline, detail, action
        for key in ["rescue_insight", "adoption_insight", "health_insight"]:
            assert "headline" in insights[key]
            assert "detail" in insights[key]
            assert "action" in insights[key]

    def test_chart_insights_with_animals(self, db, analytics_service):
        """Test chart insights with animal data."""
        animal_service = AnimalService(db)
        animal_service.add_animal("Dog1", "Dog", 2, "healthy")
        animal_service.add_animal("Cat1", "Cat", 1, "injured")
        
        insights = analytics_service.get_chart_insights()
        
        assert "total_animals" in insights or "health_insight" in insights


class TestSpeciesRanking:
    """Tests for species adoption ranking."""

    def test_empty_species_ranking(self, analytics_service):
        """Test species ranking with no adoptions."""
        ranking = analytics_service.get_species_adoption_ranking()
        
        assert ranking == []

    def test_species_ranking_limit(self, analytics_service):
        """Test species ranking respects limit."""
        ranking = analytics_service.get_species_adoption_ranking(limit=3)
        
        assert len(ranking) <= 3


class TestCacheInvalidation:
    """Tests for cache invalidation."""

    def test_invalidate_cache(self, analytics_service):
        """Test cache invalidation doesn't raise error."""
        # Should not raise
        analytics_service.invalidate_cache()


class TestPendingRescueMissions:
    """Tests for pending rescue missions count."""

    def test_no_pending_missions(self, analytics_service):
        """Test pending count with no missions."""
        count = analytics_service.get_pending_rescue_missions()
        assert count == 0

    def test_pending_missions_count(self, db, analytics_service):
        """Test pending missions counting."""
        db.execute(
            "INSERT INTO users (name, email, password_hash, password_salt, role) VALUES (?, ?, ?, ?, ?)",
            ("Test", "test@test.com", "hash", "salt", "user")
        )
        
        rescue_service = RescueService(db)
        rescue_service.submit_rescue_request(
            user_id=1, location="Loc1", animal_type="Dog", name="D1",
            details="", reporter_name="R", reporter_phone="123", urgency="medium"
        )
        rescue_service.submit_rescue_request(
            user_id=1, location="Loc2", animal_type="Cat", name="C1",
            details="", reporter_name="R", reporter_phone="123", urgency="high"
        )
        
        count = analytics_service.get_pending_rescue_missions()
        assert count == 2


class TestUserStatusDistributions:
    """Tests for user-specific status distributions."""

    def test_user_rescue_distribution_empty(self, db, analytics_service):
        """Test user rescue distribution with no missions."""
        db.execute(
            "INSERT INTO users (name, email, password_hash, password_salt, role) VALUES (?, ?, ?, ?, ?)",
            ("Test", "test@test.com", "hash", "salt", "user")
        )
        
        dist = analytics_service.get_user_rescue_status_distribution(user_id=1)
        
        assert dist["pending"] == 0
        assert dist["on-going"] == 0
        assert dist["rescued"] == 0
        assert dist["failed"] == 0

    def test_user_adoption_distribution_empty(self, db, analytics_service):
        """Test user adoption distribution with no requests."""
        db.execute(
            "INSERT INTO users (name, email, password_hash, password_salt, role) VALUES (?, ?, ?, ?, ?)",
            ("Test", "test@test.com", "hash", "salt", "user")
        )
        
        dist = analytics_service.get_user_adoption_status_distribution(user_id=1)
        
        assert dist["pending"] == 0
        assert dist["approved"] == 0
        assert dist["denied"] == 0
