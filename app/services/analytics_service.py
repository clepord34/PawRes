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
            - (day_labels, rescued_counts, adopted_counts): Daily trend data for last 1 month
            - type_dist: Dictionary of animal type distribution (empty dict if no data)
            - status_counts: Dictionary of health status counts (always includes healthy, recovering, injured)
        """
        # Prepare day labels for last 1 month (30 days)
        now = datetime.utcnow()
        days: List[datetime] = []
        for i in range(29, -1, -1):
            d = now - timedelta(days=i)
            days.append(d)
        day_labels = [d.strftime("%m-%d") for d in days]
        day_dates = [d.strftime("%Y-%m-%d") for d in days]

        # Initialize counts
        rescued_counts = [0 for _ in day_labels]
        adopted_counts = [0 for _ in day_labels]

        # Count rescued missions by day (include closed/deleted for historical data)
        # Only count missions that have "Rescued" in their status (e.g., "Rescued", "Rescued|Closed")
        missions = self.rescue_service.get_all_missions_for_analytics() or []
        for ms in missions:
            dt = ms.get("mission_date")
            status = (ms.get("status") or "").lower()
            # Check if this mission was rescued (including closed ones)
            is_rescued = "rescued" in status
            if not dt or not is_rescued:
                continue
            # Handle both datetime objects and strings
            if isinstance(dt, datetime):
                d = dt
            else:
                try:
                    d = datetime.fromisoformat(str(dt))
                except (ValueError, TypeError):
                    try:
                        d = datetime.strptime(str(dt), "%Y-%m-%d %H:%M:%S")
                    except (ValueError, TypeError):
                        # Unable to parse date, skip this mission
                        continue
            date_str = d.strftime("%Y-%m-%d")
            if date_str in day_dates:
                idx = day_dates.index(date_str)
                rescued_counts[idx] += 1

        # Count adopted animals by day
        requests = self.adoption_service.get_all_requests() or []
        for req in requests:
            dt = req.get("request_date")
            if not dt:
                continue
            # Handle both datetime objects and strings
            if isinstance(dt, datetime):
                d = dt
            else:
                try:
                    d = datetime.fromisoformat(str(dt))
                except (ValueError, TypeError):
                    try:
                        d = datetime.strptime(str(dt), "%Y-%m-%d %H:%M:%S")
                    except (ValueError, TypeError):
                        # Unable to parse date, skip this adoption request
                        continue
            date_str = d.strftime("%Y-%m-%d")
            if date_str in day_dates:
                idx = day_dates.index(date_str)
                # Consider approved/adopted/completed as successful adoptions
                if (req.get("status") or "").lower() in ("approved", "adopted", "completed"):
                    adopted_counts[idx] += 1

        # Calculate type distribution and status counts
        type_dist, status_counts = self.get_animal_statistics()

        return (day_labels, rescued_counts, adopted_counts), type_dist, status_counts

    def get_animal_statistics(self) -> Tuple[Dict[str, int], Dict[str, int]]:
        """Calculate animal type distribution and health status counts.
        
        Returns:
            Tuple of (type_distribution, status_counts) dictionaries.
            - type_distribution: Empty dict if no animals, otherwise counts by species
            - status_counts: Always contains 'healthy', 'recovering', 'injured' keys (with 0 if none)
        """
        animals = self.animal_service.get_all_animals() or []
        type_dist: Dict[str, int] = {}
        # Always include all three health status categories
        status_counts: Dict[str, int] = {
            "healthy": 0,
            "recovering": 0,
            "injured": 0,
        }
        
        for a in animals:
            t = (a.get("species") or "Unknown")
            s = (a.get("status") or "unknown").lower()
            type_dist[t] = type_dist.get(t, 0) + 1
            # Map status to one of the three categories
            if s in status_counts:
                status_counts[s] += 1
            elif s in ("unknown", ""):
                # Don't count unknown statuses in any category
                pass
            else:
                # Any other status goes to 'injured' as fallback
                status_counts["injured"] += 1

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

    def get_monthly_changes(self) -> Dict[str, str]:
        """Calculate percentage changes comparing this month vs last month.
        
        Returns:
            Dictionary with formatted change strings for:
            - animals_change: Change in animals added
            - rescues_change: Change in rescue missions
            - adoptions_change: Change in adoptions
            - pending_change: Change in pending applications
        """
        now = datetime.utcnow()
        
        # Define this month and last month date ranges
        this_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        last_month_end = this_month_start - timedelta(days=1)
        last_month_start = last_month_end.replace(day=1)
        
        def parse_date(dt) -> Optional[datetime]:
            """Parse date from various formats."""
            if dt is None:
                return None
            if isinstance(dt, datetime):
                return dt
            try:
                return datetime.fromisoformat(str(dt))
            except (ValueError, TypeError):
                try:
                    return datetime.strptime(str(dt), "%Y-%m-%d %H:%M:%S")
                except (ValueError, TypeError):
                    return None
        
        def is_in_range(dt, start: datetime, end: datetime) -> bool:
            """Check if datetime is within range."""
            parsed = parse_date(dt)
            if parsed is None:
                return False
            return start <= parsed <= end
        
        # Get all data (use analytics method for missions to include closed ones)
        animals = self.animal_service.get_all_animals() or []
        missions = self.rescue_service.get_all_missions_for_analytics() or []
        requests = self.adoption_service.get_all_requests() or []
        
        # Count animals added this month vs last month
        animals_this_month = len([a for a in animals if is_in_range(a.get("intake_date"), this_month_start, now)])
        animals_last_month = len([a for a in animals if is_in_range(a.get("intake_date"), last_month_start, last_month_end)])
        
        # Count rescued missions this month vs last month (only those with "rescued" in status)
        rescues_this_month = len([m for m in missions 
            if is_in_range(m.get("mission_date"), this_month_start, now)
            and "rescued" in (m.get("status") or "").lower()])
        rescues_last_month = len([m for m in missions 
            if is_in_range(m.get("mission_date"), last_month_start, last_month_end)
            and "rescued" in (m.get("status") or "").lower()])
        
        # Count adoptions (approved/adopted) this month vs last month
        adoptions_this_month = len([r for r in requests 
            if is_in_range(r.get("request_date"), this_month_start, now) 
            and (r.get("status") or "").lower() in ("approved", "adopted", "completed")])
        adoptions_last_month = len([r for r in requests 
            if is_in_range(r.get("request_date"), last_month_start, last_month_end)
            and (r.get("status") or "").lower() in ("approved", "adopted", "completed")])
        
        # Count pending applications this month vs last month
        pending_this_month = len([r for r in requests 
            if is_in_range(r.get("request_date"), this_month_start, now)
            and (r.get("status") or "").lower() == "pending"])
        pending_last_month = len([r for r in requests 
            if is_in_range(r.get("request_date"), last_month_start, last_month_end)
            and (r.get("status") or "").lower() == "pending"])
        
        def calc_change(current: int, previous: int) -> str:
            """Calculate percentage change and format as string."""
            if previous == 0:
                if current == 0:
                    return "No change"
                else:
                    return f"+{current} new this month"
            
            change = ((current - previous) / previous) * 100
            if change > 0:
                return f"+{change:.0f}% this month"
            elif change < 0:
                return f"{change:.0f}% this month"
            else:
                return "No change"
        
        return {
            "animals_change": calc_change(animals_this_month, animals_last_month),
            "rescues_change": calc_change(rescues_this_month, rescues_last_month),
            "adoptions_change": calc_change(adoptions_this_month, adoptions_last_month),
            "pending_change": calc_change(pending_this_month, pending_last_month),
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
        user_rescues = [r for r in all_rescues if r.get("user_id") == user_id]
        
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
