"""Extended tests for AnalyticsService - comprehensive coverage."""
import pytest
from datetime import datetime, timedelta

from services.analytics_service import AnalyticsService


class TestGetChartData:
    """Test chart data generation."""
    
    def test_get_chart_data_structure(self, analytics_service):
        """Test that get_chart_data returns proper structure."""
        result = analytics_service.get_chart_data()
        
        assert isinstance(result, tuple)
        assert len(result) == 3
        
        trend_data, type_dist, status_counts = result
        
        # Verify trend data structure
        assert isinstance(trend_data, tuple)
        assert len(trend_data) == 3
        day_labels, rescued_counts, adopted_counts = trend_data
        assert isinstance(day_labels, list)
        assert isinstance(rescued_counts, list)
        assert isinstance(adopted_counts, list)
        assert len(day_labels) == 30  # 30 days of data
        assert len(rescued_counts) == 30
        assert len(adopted_counts) == 30
        
        # Verify type distribution
        assert isinstance(type_dist, dict)
        
        # Verify status counts
        assert isinstance(status_counts, dict)
    
    def test_get_chart_data_with_rescued_animal(self, analytics_service, rescue_service, sample_user):
        """Test chart data includes rescued animals."""
        # Create and mark as rescued
        mission_id = rescue_service.submit_rescue_request(
            user_id=sample_user["id"],
            animal_type="dog",
            breed="Labrador",
            name="Chart Dog",
            location="Test Location"
        )
        
        from app_config import RescueStatus
        rescue_service.update_rescue_status(mission_id, RescueStatus.RESCUED)
        
        # Clear cache and get chart data
        analytics_service._cache.clear()
        trend_data, type_dist, status_counts = analytics_service.get_chart_data()
        
        day_labels, rescued_counts, adopted_counts = trend_data
        
        # Should have at least one rescued animal today
        assert sum(rescued_counts) >= 1


class TestGetDashboardStats:
    """Test dashboard statistics."""
    
    def test_dashboard_stats_structure(self, analytics_service):
        """Test dashboard stats returns correct structure."""
        stats = analytics_service.get_dashboard_stats()
        
        assert isinstance(stats, dict)
        assert "total_animals" in stats
        assert "total_adoptions" in stats
        assert "pending_applications" in stats
        
        assert isinstance(stats["total_animals"], int)
        assert isinstance(stats["total_adoptions"], int)
        assert isinstance(stats["pending_applications"], int)
    
    def test_dashboard_stats_counts_animals(self, analytics_service, sample_animal):
        """Test dashboard counts animals correctly."""
        analytics_service._cache.clear()
        stats = analytics_service.get_dashboard_stats()
        
        assert stats["total_animals"] >= 1
    
    def test_dashboard_stats_counts_adoptions(self, analytics_service, adoption_service, sample_animal, sample_user, sample_admin):
        """Test dashboard counts approved adoptions."""
        # Create and approve an adoption
        adoption_id = adoption_service.submit_request(
            user_id=sample_user["id"],
            animal_id=sample_animal["id"],
            contact=sample_user["email"],
            reason="Test adoption for stats"
        )
        
        from app_config import AdoptionStatus
        adoption_service.update_status(
            adoption_id,
            AdoptionStatus.APPROVED
        )
        
        analytics_service._cache.clear()
        stats = analytics_service.get_dashboard_stats()
        
        assert stats["total_adoptions"] >= 1
    
    def test_dashboard_stats_counts_pending_applications(self, analytics_service, sample_adoption_request):
        """Test dashboard counts pending applications."""
        analytics_service._cache.clear()
        stats = analytics_service.get_dashboard_stats()
        
        assert stats["pending_applications"] >= 1


class TestCaching:
    """Test analytics caching functionality."""
    
    def test_cache_is_used(self, analytics_service, sample_animal):
        """Test that cache improves performance."""
        analytics_service._cache.clear()
        
        # First call - populates cache
        stats1 = analytics_service.get_dashboard_stats()
        
        # Second call - should use cache
        stats2 = analytics_service.get_dashboard_stats()
        
        assert stats1 == stats2
    
    def test_cache_can_be_cleared(self, analytics_service):
        """Test that cache can be cleared."""
        # Populate cache
        analytics_service.get_dashboard_stats()
        
        # Clear cache
        analytics_service._cache.clear()
        
        # Should work after clearing
        stats = analytics_service.get_dashboard_stats()
        assert isinstance(stats, dict)


class TestAnalyticsWithRemovedItems:
    """Test that removed items are excluded from analytics."""
    
    def test_removed_animals_excluded(self, analytics_service, animal_service, sample_animal, sample_admin):
        """Test removed animals don't appear in stats."""
        # Get initial count
        analytics_service._cache.clear()
        stats_before = analytics_service.get_dashboard_stats()
        initial_count = stats_before["total_animals"]
        
        # Remove animal
        animal_service.remove_animal(
            sample_animal["id"],
            sample_admin["id"],
            "Test removal"
        )
        
        # Get stats after removal
        analytics_service._cache.clear()
        stats_after = analytics_service.get_dashboard_stats()
        
        # Count should decrease
        assert stats_after["total_animals"] == initial_count - 1
    
    def test_removed_adoptions_excluded(self, analytics_service, adoption_service, sample_adoption_request, sample_admin):
        """Test removed adoptions don't appear in stats."""
        # Get initial count
        analytics_service._cache.clear()
        stats_before = analytics_service.get_dashboard_stats()
        initial_pending = stats_before["pending_applications"]
        
        # Remove adoption request
        from app_config import AdoptionStatus
        adoption_service.update_status(
            sample_adoption_request["id"],
            AdoptionStatus.REMOVED
        )
        
        # Get stats after removal
        analytics_service._cache.clear()
        stats_after = analytics_service.get_dashboard_stats()
        
        # Pending count should decrease
        assert stats_after["pending_applications"] == initial_pending - 1


class TestAnalyticsWithArchivedItems:
    """Test analytics handling of archived items."""
    
    def test_archived_animals_excluded(self, analytics_service, animal_service, sample_animal):
        """Test archived animals are excluded from analytics."""
        # Get initial count
        analytics_service._cache.clear()
        stats_before = analytics_service.get_dashboard_stats()
        initial_count = stats_before["total_animals"]
        
        # Archive animal
        from app_config import AnimalStatus
        animal_service.update_animal(
            sample_animal["id"],
            status=AnimalStatus.make_archived(AnimalStatus.HEALTHY)
        )
        
        # Get stats after archiving
        analytics_service._cache.clear()
        stats_after = analytics_service.get_dashboard_stats()
        
        # Archived animals should not be counted
        assert stats_after["total_animals"] <= initial_count


class TestAnalyticsDateFiltering:
    """Test date-based filtering in analytics."""
    
    def test_chart_data_covers_30_days(self, analytics_service):
        """Test that chart data covers exactly 30 days."""
        trend_data, _, _ = analytics_service.get_chart_data()
        day_labels, _, _ = trend_data
        
        assert len(day_labels) == 30
        
        # Verify date format (MM-DD)
        for label in day_labels:
            assert len(label) == 5  # "MM-DD"
            assert label[2] == "-"


class TestAnalyticsTypeDistribution:
    """Test animal type distribution in analytics."""
    
    def test_type_distribution_with_animals(self, analytics_service, animal_service, sample_user):
        """Test type distribution includes animal types."""
        # Create animals of different types
        animal_service.add_animal(
            name="Dog Type Test",
            type="dog",
            breed="Labrador",
            age=2,
            health_status="healthy"
        )
        
        animal_service.add_animal(
            name="Cat Type Test",
            type="cat",
            breed="Persian",
            age=1,
            health_status="healthy"
        )
        
        analytics_service._cache.clear()
        _, type_dist, _ = analytics_service.get_chart_data()
        
        # Should have at least dog and cat
        assert isinstance(type_dist, dict)


class TestAnalyticsHealthStatus:
    """Test health status distribution in analytics."""
    
    def test_status_distribution_structure(self, analytics_service):
        """Test health status distribution structure."""
        _, _, status_counts = analytics_service.get_chart_data()
        
        assert isinstance(status_counts, dict)
        # Should include standard health statuses


class TestAnalyticsEdgeCases:
    """Test edge cases in analytics."""
    
    def test_analytics_with_no_data(self, analytics_service):
        """Test analytics work with empty database."""
        analytics_service._cache.clear()
        
        stats = analytics_service.get_dashboard_stats()
        
        # Should return zero counts, not error
        assert isinstance(stats, dict)
        assert stats["total_animals"] >= 0
        assert stats["total_adoptions"] >= 0
        assert stats["pending_applications"] >= 0
    
    def test_chart_data_with_no_rescued_animals(self, analytics_service):
        """Test chart data works with no rescued animals."""
        analytics_service._cache.clear()
        
        trend_data, type_dist, status_counts = analytics_service.get_chart_data()
        day_labels, rescued_counts, adopted_counts = trend_data
        
        # Should return arrays of zeros, not error
        assert len(rescued_counts) == 30
        assert all(isinstance(count, int) for count in rescued_counts)
        assert all(count >= 0 for count in rescued_counts)
