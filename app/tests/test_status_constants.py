"""Tests for status constants - RescueStatus, AdoptionStatus, AnimalStatus."""
import pytest

from app_config import RescueStatus, AdoptionStatus, AnimalStatus, Urgency


class TestRescueStatusNormalization:
    """Test RescueStatus normalization."""
    
    def test_normalize_pending(self):
        """Test normalizing pending variants."""
        assert RescueStatus.normalize("pending") == RescueStatus.PENDING
        assert RescueStatus.normalize("PENDING") == RescueStatus.PENDING
        assert RescueStatus.normalize("  pending  ") == RescueStatus.PENDING
        assert RescueStatus.normalize("") == RescueStatus.PENDING
    
    def test_normalize_ongoing(self):
        """Test normalizing on-going variants."""
        assert RescueStatus.normalize("on-going") == RescueStatus.ONGOING
        assert RescueStatus.normalize("ongoing") == RescueStatus.ONGOING
        assert RescueStatus.normalize("in_progress") == RescueStatus.ONGOING
        assert RescueStatus.normalize("in progress") == RescueStatus.ONGOING
    
    def test_normalize_rescued(self):
        """Test normalizing rescued variants."""
        assert RescueStatus.normalize("rescued") == RescueStatus.RESCUED
        assert RescueStatus.normalize("completed") == RescueStatus.RESCUED
    
    def test_normalize_failed(self):
        """Test normalizing failed."""
        assert RescueStatus.normalize("failed") == RescueStatus.FAILED
    
    def test_normalize_cancelled(self):
        """Test normalizing cancelled variants."""
        assert RescueStatus.normalize("cancelled") == RescueStatus.CANCELLED
        assert RescueStatus.normalize("canceled") == RescueStatus.CANCELLED
    
    def test_normalize_removed(self):
        """Test normalizing removed."""
        assert RescueStatus.normalize("removed") == RescueStatus.REMOVED


class TestRescueStatusArchived:
    """Test RescueStatus archived functionality."""
    
    def test_is_archived(self):
        """Test detecting archived status."""
        assert RescueStatus.is_archived("rescued|archived") is True
        assert RescueStatus.is_archived("failed|archived") is True
        assert RescueStatus.is_archived("rescued") is False
        assert RescueStatus.is_archived("pending") is False
    
    def test_get_base_status(self):
        """Test extracting base status from archived."""
        assert RescueStatus.get_base_status("rescued|archived") == "rescued"
        assert RescueStatus.get_base_status("failed|archived") == "failed"
        assert RescueStatus.get_base_status("rescued") == "rescued"
    
    def test_make_archived(self):
        """Test adding archived suffix."""
        assert RescueStatus.make_archived("rescued") == "rescued|archived"
        assert RescueStatus.make_archived("failed") == "failed|archived"
        assert RescueStatus.make_archived("rescued|archived") == "rescued|archived"
    
    def test_normalize_archived_status(self):
        """Test normalizing archived statuses."""
        assert RescueStatus.normalize("rescued|archived") == RescueStatus.RESCUED
        assert RescueStatus.normalize("failed|archived") == RescueStatus.FAILED


class TestRescueStatusHelpers:
    """Test RescueStatus helper methods."""
    
    def test_is_active(self):
        """Test checking active status."""
        assert RescueStatus.is_active("pending") is True
        assert RescueStatus.is_active("on-going") is True
        assert RescueStatus.is_active("rescued") is False
        assert RescueStatus.is_active("failed") is False
        assert RescueStatus.is_active("cancelled") is False
    
    def test_is_final(self):
        """Test checking final status."""
        assert RescueStatus.is_final("rescued") is True
        assert RescueStatus.is_final("failed") is True
        assert RescueStatus.is_final("cancelled") is True
        assert RescueStatus.is_final("pending") is False
        assert RescueStatus.is_final("on-going") is False
    
    def test_is_cancelled(self):
        """Test checking cancelled status."""
        assert RescueStatus.is_cancelled("cancelled") is True
        assert RescueStatus.is_cancelled("pending") is False
    
    def test_is_removed(self):
        """Test checking removed status."""
        assert RescueStatus.is_removed("removed") is True
        assert RescueStatus.is_removed("pending") is False
    
    def test_is_hidden(self):
        """Test checking hidden status (archived or removed)."""
        assert RescueStatus.is_hidden("rescued|archived") is True
        assert RescueStatus.is_hidden("removed") is True
        assert RescueStatus.is_hidden("pending") is False
        assert RescueStatus.is_hidden("rescued") is False
    
    def test_has_outcome(self):
        """Test checking if status has real outcome."""
        assert RescueStatus.has_outcome("rescued") is True
        assert RescueStatus.has_outcome("failed") is True
        assert RescueStatus.has_outcome("rescued|archived") is True
        assert RescueStatus.has_outcome("cancelled") is False
        assert RescueStatus.has_outcome("removed") is False
    
    def test_counts_in_analytics(self):
        """Test checking if status counts in analytics."""
        assert RescueStatus.counts_in_analytics("rescued") is True
        assert RescueStatus.counts_in_analytics("failed") is True
        assert RescueStatus.counts_in_analytics("cancelled") is True
        assert RescueStatus.counts_in_analytics("removed") is False


class TestRescueStatusLabels:
    """Test RescueStatus display labels."""
    
    def test_get_label(self):
        """Test getting display labels."""
        assert RescueStatus.get_label("pending") == "Pending"
        assert RescueStatus.get_label("on-going") == "On-going"
        assert RescueStatus.get_label("rescued") == "Rescued"
        assert RescueStatus.get_label("failed") == "Failed"
        assert RescueStatus.get_label("cancelled") == "Cancelled"
    
    def test_get_label_archived(self):
        """Test getting labels for archived statuses."""
        # Archived statuses show original status label
        assert RescueStatus.get_label("rescued|archived") == "Rescued"
        assert RescueStatus.get_label("failed|archived") == "Failed"


class TestAdoptionStatusNormalization:
    """Test AdoptionStatus normalization."""
    
    def test_normalize_pending(self):
        """Test normalizing pending."""
        assert AdoptionStatus.normalize("pending") == AdoptionStatus.PENDING
        assert AdoptionStatus.normalize("") == AdoptionStatus.PENDING
    
    def test_normalize_approved(self):
        """Test normalizing approved variants."""
        assert AdoptionStatus.normalize("approved") == AdoptionStatus.APPROVED
        assert AdoptionStatus.normalize("adopted") == AdoptionStatus.APPROVED
        assert AdoptionStatus.normalize("completed") == AdoptionStatus.APPROVED
    
    def test_normalize_denied(self):
        """Test normalizing denied variants."""
        assert AdoptionStatus.normalize("denied") == AdoptionStatus.DENIED
        assert AdoptionStatus.normalize("rejected") == AdoptionStatus.DENIED
    
    def test_normalize_cancelled(self):
        """Test normalizing cancelled variants."""
        assert AdoptionStatus.normalize("cancelled") == AdoptionStatus.CANCELLED
        assert AdoptionStatus.normalize("canceled") == AdoptionStatus.CANCELLED
        assert AdoptionStatus.normalize("revoked") == AdoptionStatus.CANCELLED
    
    def test_normalize_removed(self):
        """Test normalizing removed."""
        assert AdoptionStatus.normalize("removed") == AdoptionStatus.REMOVED


class TestAdoptionStatusArchived:
    """Test AdoptionStatus archived functionality."""
    
    def test_is_archived(self):
        """Test detecting archived status."""
        assert AdoptionStatus.is_archived("approved|archived") is True
        assert AdoptionStatus.is_archived("denied|archived") is True
        assert AdoptionStatus.is_archived("approved") is False
    
    def test_get_base_status(self):
        """Test extracting base status."""
        assert AdoptionStatus.get_base_status("approved|archived") == "approved"
        assert AdoptionStatus.get_base_status("denied|archived") == "denied"
    
    def test_make_archived(self):
        """Test adding archived suffix."""
        assert AdoptionStatus.make_archived("approved") == "approved|archived"
        assert AdoptionStatus.make_archived("denied") == "denied|archived"


class TestAdoptionStatusHelpers:
    """Test AdoptionStatus helper methods."""
    
    def test_is_final(self):
        """Test checking final status."""
        assert AdoptionStatus.is_final("approved") is True
        assert AdoptionStatus.is_final("denied") is True
        assert AdoptionStatus.is_final("cancelled") is True
        assert AdoptionStatus.is_final("pending") is False
    
    def test_is_cancelled(self):
        """Test checking cancelled status."""
        assert AdoptionStatus.is_cancelled("cancelled") is True
        assert AdoptionStatus.is_cancelled("pending") is False
    
    def test_is_removed(self):
        """Test checking removed status."""
        assert AdoptionStatus.is_removed("removed") is True
        assert AdoptionStatus.is_removed("pending") is False
    
    def test_is_hidden(self):
        """Test checking hidden status."""
        assert AdoptionStatus.is_hidden("approved|archived") is True
        assert AdoptionStatus.is_hidden("removed") is True
        assert AdoptionStatus.is_hidden("pending") is False
    
    def test_has_outcome(self):
        """Test checking if status has outcome."""
        assert AdoptionStatus.has_outcome("approved") is True
        assert AdoptionStatus.has_outcome("denied") is True
        assert AdoptionStatus.has_outcome("cancelled") is False
        assert AdoptionStatus.has_outcome("removed") is False
    
    def test_counts_in_analytics(self):
        """Test checking if counts in analytics."""
        assert AdoptionStatus.counts_in_analytics("approved") is True
        assert AdoptionStatus.counts_in_analytics("denied") is True
        assert AdoptionStatus.counts_in_analytics("removed") is False


class TestAdoptionStatusLabels:
    """Test AdoptionStatus display labels."""
    
    def test_get_label(self):
        """Test getting display labels."""
        assert AdoptionStatus.get_label("pending") == "Pending"
        assert AdoptionStatus.get_label("approved") == "Approved"
        assert AdoptionStatus.get_label("denied") == "Denied"
        assert AdoptionStatus.get_label("cancelled") == "Cancelled"


class TestAnimalStatusNormalization:
    """Test AnimalStatus normalization."""
    
    def test_normalize_healthy(self):
        """Test normalizing healthy."""
        assert AnimalStatus.normalize("healthy") == AnimalStatus.HEALTHY
    
    def test_normalize_recovering(self):
        """Test normalizing recovering."""
        assert AnimalStatus.normalize("recovering") == AnimalStatus.RECOVERING
    
    def test_normalize_injured(self):
        """Test normalizing injured."""
        assert AnimalStatus.normalize("injured") == AnimalStatus.INJURED
    
    def test_normalize_adopted(self):
        """Test normalizing adopted."""
        assert AnimalStatus.normalize("adopted") == AnimalStatus.ADOPTED
    
    def test_normalize_processing(self):
        """Test normalizing processing."""
        assert AnimalStatus.normalize("processing") == AnimalStatus.PROCESSING
    
    def test_normalize_removed(self):
        """Test normalizing removed."""
        assert AnimalStatus.normalize("removed") == AnimalStatus.REMOVED


class TestAnimalStatusArchived:
    """Test AnimalStatus archived functionality."""
    
    def test_is_archived(self):
        """Test detecting archived status."""
        assert AnimalStatus.is_archived("adopted|archived") is True
        assert AnimalStatus.is_archived("healthy|archived") is True
        assert AnimalStatus.is_archived("healthy") is False
    
    def test_get_base_status(self):
        """Test extracting base status."""
        assert AnimalStatus.get_base_status("adopted|archived") == "adopted"
        assert AnimalStatus.get_base_status("healthy") == "healthy"
    
    def test_make_archived(self):
        """Test adding archived suffix."""
        assert AnimalStatus.make_archived("adopted") == "adopted|archived"


class TestAnimalStatusHelpers:
    """Test AnimalStatus helper methods."""
    
    def test_is_adoptable(self):
        """Test checking if animal is adoptable."""
        assert AnimalStatus.is_adoptable("healthy") is True
        assert AnimalStatus.is_adoptable("recovering") is False
        assert AnimalStatus.is_adoptable("injured") is False
        assert AnimalStatus.is_adoptable("adopted") is False
        assert AnimalStatus.is_adoptable("processing") is False
    
    def test_needs_setup(self):
        """Test checking if animal needs setup."""
        assert AnimalStatus.needs_setup("processing") is True
        assert AnimalStatus.needs_setup("healthy") is False
    
    def test_is_removed(self):
        """Test checking removed status."""
        assert AnimalStatus.is_removed("removed") is True
        assert AnimalStatus.is_removed("healthy") is False
    
    def test_is_hidden(self):
        """Test checking hidden status."""
        assert AnimalStatus.is_hidden("adopted|archived") is True
        assert AnimalStatus.is_hidden("removed") is True
        assert AnimalStatus.is_hidden("healthy") is False
    
    def test_counts_in_analytics(self):
        """Test checking if counts in analytics."""
        assert AnimalStatus.counts_in_analytics("healthy") is True
        assert AnimalStatus.counts_in_analytics("adopted") is True
        assert AnimalStatus.counts_in_analytics("removed") is False


class TestAnimalStatusLabels:
    """Test AnimalStatus display labels."""
    
    def test_get_label(self):
        """Test getting display labels."""
        assert AnimalStatus.get_label("healthy") == "Healthy"
        assert AnimalStatus.get_label("recovering") == "Recovering"
        assert AnimalStatus.get_label("injured") == "Injured"
        assert AnimalStatus.get_label("adopted") == "Adopted"
        assert AnimalStatus.get_label("processing") == "Processing"


class TestUrgency:
    """Test Urgency constants."""
    
    def test_urgency_levels(self):
        """Test urgency level constants."""
        assert Urgency.LOW == "low"
        assert Urgency.MEDIUM == "medium"
        assert Urgency.HIGH == "high"
    
    def test_get_label(self):
        """Test getting urgency labels."""
        assert "Low" in Urgency.get_label("low")
        assert "Medium" in Urgency.get_label("medium")
        assert "High" in Urgency.get_label("high")
    
    def test_from_label(self):
        """Test extracting urgency from label."""
        assert Urgency.from_label(Urgency.LOW_LABEL) == Urgency.LOW
        assert Urgency.from_label(Urgency.MEDIUM_LABEL) == Urgency.MEDIUM
        assert Urgency.from_label(Urgency.HIGH_LABEL) == Urgency.HIGH
    
    def test_from_label_defaults_to_medium(self):
        """Test from_label defaults to medium."""
        assert Urgency.from_label("unknown") == Urgency.MEDIUM
        assert Urgency.from_label("") == Urgency.MEDIUM
        assert Urgency.from_label(None) == Urgency.MEDIUM


class TestStatusConstantsAllStatuses:
    """Test all_statuses methods."""
    
    def test_rescue_all_statuses(self):
        """Test RescueStatus.all_statuses()."""
        statuses = RescueStatus.all_statuses()
        
        assert RescueStatus.PENDING in statuses
        assert RescueStatus.ONGOING in statuses
        assert RescueStatus.RESCUED in statuses
        assert RescueStatus.FAILED in statuses
        assert RescueStatus.CANCELLED in statuses
        assert RescueStatus.REMOVED in statuses
        
        # Should not include archived variants
        assert "pending|archived" not in statuses
    
    def test_adoption_all_statuses(self):
        """Test AdoptionStatus.all_statuses()."""
        statuses = AdoptionStatus.all_statuses()
        
        assert AdoptionStatus.PENDING in statuses
        assert AdoptionStatus.APPROVED in statuses
        assert AdoptionStatus.DENIED in statuses
        assert AdoptionStatus.CANCELLED in statuses
        assert AdoptionStatus.REMOVED in statuses
