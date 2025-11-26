"""Analytics service for data aggregation and reporting."""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta

from storage.database import Database
from .animal_service import AnimalService
from .rescue_service import RescueService
from .adoption_service import AdoptionService
import app_config


class AnalyticsService:
    """Service for generating analytics and aggregated statistics."""

    def __init__(self, db: Optional[Database | str] = None) -> None:
        """Initialize with database connection.
        
        Args:
            db: Database instance or path to sqlite file.
        """
        if isinstance(db, Database):
            self.db = db
        else:
            self.db = Database(db if isinstance(db, str) else app_config.DB_PATH)
        
        # Initialize other services for data access
        self.animal_service = AnimalService(self.db)
        self.rescue_service = RescueService(self.db)
        self.adoption_service = AdoptionService(self.db)

    def get_chart_data(self) -> Tuple[Tuple[List[str], List[int], List[int]], Dict[str, int], Dict[str, int]]:
        """Return aggregated data for charts.
        
        Returns:
            Tuple containing:
            - (month_labels, rescued_counts, adopted_counts): Monthly trend data
            - type_dist: Dictionary of animal type distribution
            - status_counts: Dictionary of health status counts
        """
        # Prepare months labels for last 12 months
        now = datetime.utcnow()
        months: List[datetime] = []
        for i in range(11, -1, -1):
            m = (now.replace(day=15) - timedelta(days=30 * i))
            months.append(m)
        month_labels = [m.strftime("%Y-%m") for m in months]

        # Initialize counts
        rescued_counts = [0 for _ in month_labels]
        adopted_counts = [0 for _ in month_labels]

        # Count rescued missions by month
        missions = self.rescue_service.get_all_missions() or []
        for ms in missions:
            dt = ms.get("mission_date")
            if not dt:
                continue
            try:
                d = datetime.fromisoformat(dt)
            except (ValueError, TypeError):
                try:
                    d = datetime.strptime(dt, "%Y-%m-%d %H:%M:%S")
                except (ValueError, TypeError):
                    # Unable to parse date, skip this mission
                    continue
            label = d.strftime("%Y-%m")
            if label in month_labels:
                idx = month_labels.index(label)
                rescued_counts[idx] += 1

        # Count adopted animals by month
        requests = self.adoption_service.get_all_requests() or []
        for req in requests:
            dt = req.get("request_date")
            if not dt:
                continue
            try:
                d = datetime.fromisoformat(dt)
            except (ValueError, TypeError):
                try:
                    d = datetime.strptime(dt, "%Y-%m-%d %H:%M:%S")
                except (ValueError, TypeError):
                    # Unable to parse date, skip this adoption request
                    continue
            label = d.strftime("%Y-%m")
            if label in month_labels:
                idx = month_labels.index(label)
                # Consider approved/adopted/completed as successful adoptions
                if (req.get("status") or "").lower() in ("approved", "adopted", "completed"):
                    adopted_counts[idx] += 1

        # Calculate type distribution and status counts
        type_dist, status_counts = self.get_animal_statistics()

        return (month_labels, rescued_counts, adopted_counts), type_dist, status_counts

    def get_animal_statistics(self) -> Tuple[Dict[str, int], Dict[str, int]]:
        """Calculate animal type distribution and health status counts.
        
        Returns:
            Tuple of (type_distribution, status_counts) dictionaries
        """
        animals = self.animal_service.get_all_animals() or []
        type_dist: Dict[str, int] = {}
        status_counts: Dict[str, int] = {}
        
        for a in animals:
            t = (a.get("species") or "Unknown")
            s = (a.get("status") or "unknown")
            type_dist[t] = type_dist.get(t, 0) + 1
            status_counts[s] = status_counts.get(s, 0) + 1

        return type_dist, status_counts

    def get_dashboard_stats(self) -> Dict[str, Any]:
        """Get summary statistics for dashboard display.
        
        Returns:
            Dictionary with total animals, adoptions, and pending requests
        """
        animals = self.animal_service.get_all_animals() or []
        all_requests = self.adoption_service.get_all_requests() or []
        
        total_animals = len(animals)
        total_adoptions = len([r for r in all_requests if (r.get("status") or "").lower() in ("approved", "adopted")])
        pending_applications = len([r for r in all_requests if (r.get("status") or "").lower() == "pending"])
        
        return {
            "total_animals": total_animals,
            "total_adoptions": total_adoptions,
            "pending_applications": pending_applications,
        }

    def get_user_activity_stats(self, user_id: int) -> Dict[str, Any]:
        """Get activity statistics for a specific user.
        
        Args:
            user_id: The user's ID
            
        Returns:
            Dictionary with user's adoption and rescue statistics
        """
        all_adoptions = self.adoption_service.get_all_requests() or []
        all_rescues = self.rescue_service.get_all_missions() or []
        
        user_adoptions = [a for a in all_adoptions if a.get("user_id") == user_id]
        user_rescues = [r for r in all_rescues if r.get("reporter_id") == user_id or r.get("user_id") == user_id]
        
        total_adoptions = len(user_adoptions)
        rescue_reports_filed = len(user_rescues)
        pending_adoption_requests = len([a for a in user_adoptions if (a.get("status") or "").lower() == "pending"])
        ongoing_rescue_missions = len([r for r in user_rescues if (r.get("status") or "").lower() == "on-going"])
        
        return {
            "total_adoptions": total_adoptions,
            "rescue_reports_filed": rescue_reports_filed,
            "pending_adoption_requests": pending_adoption_requests,
            "ongoing_rescue_missions": ongoing_rescue_missions,
        }


__all__ = ["AnalyticsService"]
