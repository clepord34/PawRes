"""Analytics service for data aggregation and reporting."""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple, Union
from datetime import datetime, timedelta

from storage.database import Database
from storage.cache import get_query_cache, QueryCache
from .animal_service import AnimalService
from .rescue_service import RescueService
from .adoption_service import AdoptionService
from components.utils import parse_datetime
import app_config
from app_config import RescueStatus, AdoptionStatus, AnimalStatus


class AnalyticsService:
    """Service for generating analytics and aggregated statistics.
    
    Provides cached access to analytics data including:
    - Chart data for rescued/adopted trends
    - Animal type distribution
    - Health status counts
    - Dashboard statistics
    - Monthly comparison changes
    
    Uses QueryCache for performance optimization on expensive queries.
    """

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
        
        # Use query cache for expensive analytics queries
        self._cache: QueryCache = get_query_cache()
        
        # Cache TTL in seconds (2 minutes for analytics)
        self._cache_ttl = 120

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

        # Count rescued missions by day (include archived for historical data)
        # Only count missions that have "Rescued" in their status (e.g., "Rescued", "rescued|archived")
        # Excludes "removed" status items via get_all_missions_for_analytics()
        missions = self.rescue_service.get_all_missions_for_analytics() or []
        for ms in missions:
            dt = ms.get("mission_date")
            status = (ms.get("status") or "").lower()
            # Check if this mission was rescued (including archived ones)
            # Get base status to check for "rescued" 
            base_status = RescueStatus.get_base_status(status)
            is_rescued = base_status == RescueStatus.RESCUED
            if not dt or not is_rescued:
                continue
            # Parse date using shared helper
            d = parse_datetime(dt)
            if d is None:
                continue
            date_str = d.strftime("%Y-%m-%d")
            if date_str in day_dates:
                idx = day_dates.index(date_str)
                rescued_counts[idx] += 1

        # Count adopted animals by day
        # Excludes "removed" status items via get_all_requests_for_analytics()
        requests = self.adoption_service.get_all_requests_for_analytics() or []
        for req in requests:
            dt = req.get("request_date")
            if not dt:
                continue
            # Parse date using shared helper
            d = parse_datetime(dt)
            if d is None:
                continue
            date_str = d.strftime("%Y-%m-%d")
            if date_str in day_dates:
                idx = day_dates.index(date_str)
                # Consider approved/adopted/completed OR was_approved as successful adoptions
                # Get base status to check (handles "approved|archived" format)
                status_lower = (req.get("status") or "").lower()
                base_status = AdoptionStatus.get_base_status(status_lower)
                if base_status in app_config.APPROVED_ADOPTION_STATUSES or req.get("was_approved") == 1:
                    adopted_counts[idx] += 1

        # Calculate type distribution and status counts
        type_dist, status_counts = self.get_animal_statistics()

        return (day_labels, rescued_counts, adopted_counts), type_dist, status_counts

    def get_chart_data_14_days(self) -> Tuple[List[str], List[int], List[int]]:
        """Return 14-day trend data for rescued vs adopted chart (admin dashboard).
        
        Returns:
            Tuple containing (day_labels, rescued_counts, adopted_counts)
        """
        # Prepare day labels for last 14 days
        now = datetime.utcnow()
        days: List[datetime] = []
        for i in range(13, -1, -1):
            d = now - timedelta(days=i)
            days.append(d)
        day_labels = [d.strftime("%m-%d") for d in days]
        day_dates = [d.strftime("%Y-%m-%d") for d in days]

        # Initialize counts
        rescued_counts = [0 for _ in day_labels]
        adopted_counts = [0 for _ in day_labels]

        # Count rescued missions by day
        missions = self.rescue_service.get_all_missions_for_analytics() or []
        for ms in missions:
            dt = ms.get("mission_date")
            status = (ms.get("status") or "").lower()
            base_status = RescueStatus.get_base_status(status)
            is_rescued = base_status == RescueStatus.RESCUED
            if not dt or not is_rescued:
                continue
            d = parse_datetime(dt)
            if d is None:
                continue
            date_str = d.strftime("%Y-%m-%d")
            if date_str in day_dates:
                idx = day_dates.index(date_str)
                rescued_counts[idx] += 1

        # Count adopted animals by day
        requests = self.adoption_service.get_all_requests_for_analytics() or []
        for req in requests:
            dt = req.get("request_date")
            if not dt:
                continue
            d = parse_datetime(dt)
            if d is None:
                continue
            date_str = d.strftime("%Y-%m-%d")
            if date_str in day_dates:
                idx = day_dates.index(date_str)
                status_lower = (req.get("status") or "").lower()
                base_status = AdoptionStatus.get_base_status(status_lower)
                if base_status in app_config.APPROVED_ADOPTION_STATUSES or req.get("was_approved") == 1:
                    adopted_counts[idx] += 1

        return (day_labels, rescued_counts, adopted_counts)

    def get_animal_statistics(self) -> Tuple[Dict[str, int], Dict[str, int]]:
        """Calculate animal type distribution and health status counts.
        
        Excludes "removed" animals from counts.
        
        Returns:
            Tuple of (type_distribution, status_counts) dictionaries.
            - type_distribution: Empty dict if no animals, otherwise counts by species
            - status_counts: Always contains 'healthy', 'recovering', 'injured' keys (with 0 if none)
        """
        animals = self.animal_service.get_all_animals_for_analytics() or []
        type_dist: Dict[str, int] = {}
        # Always include all three health status categories
        status_counts: Dict[str, int] = {
            "healthy": 0,
            "recovering": 0,
            "injured": 0,
        }
        
        for a in animals:
            # Normalize species name to Title Case for consistent grouping
            t = (a.get("species") or "Unknown").strip().capitalize()
            s = (a.get("status") or "unknown").lower()
            # Get base status (handles "healthy|archived" format)
            base_s = AnimalStatus.get_base_status(s)
            type_dist[t] = type_dist.get(t, 0) + 1
            # Map status to one of the three health categories
            # Skip adopted and processing - they're not health statuses
            if base_s in status_counts:
                status_counts[base_s] += 1
            elif base_s in ("adopted", "processing", "unknown", ""):
                # Don't count these in health status chart
                pass
            else:
                # Any other status goes to 'injured' as fallback
                status_counts["injured"] += 1

        return type_dist, status_counts

    def get_dashboard_stats(self) -> Dict[str, Any]:
        """Get summary statistics for dashboard display.
        
        Excludes "removed" items from all counts.
        Returns cached results for performance.
        
        Returns:
            Dictionary with total animals, adoptions, and pending requests
        """
        def _fetch_stats():
            animals = self.animal_service.get_all_animals_for_analytics() or []
            all_requests = self.adoption_service.get_all_requests_for_analytics() or []
            
            total_animals = len(animals)
            # Count approved OR was_approved (preserves count even after archiving)
            # Get base status to handle "approved|archived" format
            total_adoptions = len([r for r in all_requests 
                if AdoptionStatus.get_base_status((r.get("status") or "").lower()) in app_config.APPROVED_ADOPTION_STATUSES
                or r.get("was_approved") == 1])
            pending_applications = len([r for r in all_requests 
                if AdoptionStatus.get_base_status((r.get("status") or "").lower()) == "pending"])
            
            return {
                "total_animals": total_animals,
                "total_adoptions": total_adoptions,
                "pending_applications": pending_applications,
            }
        
        return self._cache.get_or_fetch(
            "dashboard_stats",
            None,
            _fetch_stats,
            ttl_seconds=self._cache_ttl
        )

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
        
        def is_in_range(dt, start: datetime, end: datetime) -> bool:
            """Check if datetime is within range."""
            parsed = parse_datetime(dt)
            if parsed is None:
                return False
            return start <= parsed <= end
        
        # Get all data (use analytics methods to exclude "removed" items)
        animals = self.animal_service.get_all_animals_for_analytics() or []
        missions = self.rescue_service.get_all_missions_for_analytics() or []
        requests = self.adoption_service.get_all_requests_for_analytics() or []
        
        # Count animals added this month vs last month
        animals_this_month = len([a for a in animals if is_in_range(a.get("intake_date"), this_month_start, now)])
        animals_last_month = len([a for a in animals if is_in_range(a.get("intake_date"), last_month_start, last_month_end)])
        
        # Count rescued missions this month vs last month (only those with "rescued" in status)
        # Use get_base_status to handle "rescued|archived" format
        rescues_this_month = len([m for m in missions 
            if is_in_range(m.get("mission_date"), this_month_start, now)
            and RescueStatus.get_base_status((m.get("status") or "").lower()) == RescueStatus.RESCUED])
        rescues_last_month = len([m for m in missions 
            if is_in_range(m.get("mission_date"), last_month_start, last_month_end)
            and RescueStatus.get_base_status((m.get("status") or "").lower()) == RescueStatus.RESCUED])
        
        # Count adoptions (approved/adopted OR was_approved) this month vs last month
        # Use get_base_status to handle "approved|archived" format
        adoptions_this_month = len([r for r in requests 
            if is_in_range(r.get("request_date"), this_month_start, now) 
            and (AdoptionStatus.get_base_status((r.get("status") or "").lower()) in app_config.APPROVED_ADOPTION_STATUSES
                 or r.get("was_approved") == 1)])
        adoptions_last_month = len([r for r in requests 
            if is_in_range(r.get("request_date"), last_month_start, last_month_end)
            and (AdoptionStatus.get_base_status((r.get("status") or "").lower()) in app_config.APPROVED_ADOPTION_STATUSES
                 or r.get("was_approved") == 1)])
        
        # Count pending applications this month vs last month
        pending_this_month = len([r for r in requests 
            if is_in_range(r.get("request_date"), this_month_start, now)
            and AdoptionStatus.get_base_status((r.get("status") or "").lower()) == "pending"])
        pending_last_month = len([r for r in requests 
            if is_in_range(r.get("request_date"), last_month_start, last_month_end)
            and AdoptionStatus.get_base_status((r.get("status") or "").lower()) == "pending"])
        
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
        
        Excludes "removed" items from counts.
        
        Args:
            user_id: The user's ID
            
        Returns:
            Dictionary with user's adoption and rescue statistics
        """
        all_adoptions = self.adoption_service.get_all_requests_for_analytics() or []
        all_rescues = self.rescue_service.get_all_missions_for_analytics() or []
        
        user_adoptions = [a for a in all_adoptions if a.get("user_id") == user_id]
        user_rescues = [r for r in all_rescues if r.get("user_id") == user_id]
        
        # Count approved OR was_approved (preserves count even after archiving)
        # Use get_base_status to handle "approved|archived" format
        total_adoptions = len([a for a in user_adoptions 
                              if AdoptionStatus.get_base_status((a.get("status") or "").lower()) == "approved"
                              or a.get("was_approved") == 1])
        rescue_reports_filed = len(user_rescues)
        pending_adoption_requests = len([a for a in user_adoptions 
                                        if AdoptionStatus.get_base_status((a.get("status") or "").lower()) == "pending"])
        ongoing_rescue_missions = len([r for r in user_rescues 
                                       if RescueStatus.get_base_status((r.get("status") or "").lower()) == "on-going"])
        
        return {
            "total_adoptions": total_adoptions,
            "rescue_reports_filed": rescue_reports_filed,
            "pending_adoption_requests": pending_adoption_requests,
            "ongoing_rescue_missions": ongoing_rescue_missions,
        }

    def get_rescue_status_distribution(self) -> Dict[str, int]:
        """Get rescue mission status distribution.
        
        Returns:
            Dictionary with counts for each status: pending, on-going, rescued, failed
        """
        missions = self.rescue_service.get_all_missions_for_analytics() or []
        
        status_counts = {
            "pending": 0,
            "on-going": 0,
            "rescued": 0,
            "failed": 0,
        }
        
        for mission in missions:
            status = RescueStatus.get_base_status((mission.get("status") or "").lower())
            if status in status_counts:
                status_counts[status] += 1
        
        return status_counts

    def get_adoption_status_distribution(self) -> Dict[str, int]:
        """Get adoption request status distribution.
        
        Returns:
            Dictionary with counts for each status: pending, approved, denied
        """
        requests = self.adoption_service.get_all_requests_for_analytics() or []
        
        status_counts = {
            "pending": 0,
            "approved": 0,
            "denied": 0,
        }
        
        for req in requests:
            status = AdoptionStatus.get_base_status((req.get("status") or "").lower())
            # Use current status - was_approved is only for historical tracking when archived
            if status == "approved":
                status_counts["approved"] += 1
            elif status == "denied":
                status_counts["denied"] += 1
            elif status == "pending":
                status_counts["pending"] += 1
        
        return status_counts

    def get_urgency_distribution(self) -> Dict[str, int]:
        """Get rescue mission urgency level distribution.
        
        Returns:
            Dictionary with counts for each urgency: low, medium, high
        """
        missions = self.rescue_service.get_all_missions_for_analytics() or []
        
        urgency_counts = {
            "low": 0,
            "medium": 0,
            "high": 0,
        }
        
        for mission in missions:
            urgency = (mission.get("urgency") or "medium").lower()
            if urgency in urgency_counts:
                urgency_counts[urgency] += 1
            else:
                urgency_counts["medium"] += 1  # Default fallback
        
        return urgency_counts

    def get_pending_rescue_missions(self) -> int:
        """Get count of pending rescue missions.
        
        Returns:
            Number of pending rescue missions
        """
        missions = self.rescue_service.get_all_missions_for_analytics() or []
        pending = [m for m in missions 
                   if RescueStatus.get_base_status((m.get("status") or "").lower()) == "pending"]
        return len(pending)

    def get_species_adoption_ranking(self, limit: int = 5) -> List[Tuple[str, int]]:
        """Get top adopted species ranking.
        
        Args:
            limit: Maximum number of species to return
            
        Returns:
            List of (species, count) tuples sorted by count descending
        """
        requests = self.adoption_service.get_all_requests_for_analytics() or []
        
        species_counts: Dict[str, int] = {}
        
        for req in requests:
            status = AdoptionStatus.get_base_status((req.get("status") or "").lower())
            if status == "approved" or req.get("was_approved") == 1:
                species = (req.get("animal_species") or "Unknown").strip().capitalize()
                species_counts[species] = species_counts.get(species, 0) + 1
        
        # Sort by count descending
        sorted_species = sorted(species_counts.items(), key=lambda x: x[1], reverse=True)
        return sorted_species[:limit]

    def get_user_rescue_status_distribution(self, user_id: int) -> Dict[str, int]:
        """Get rescue mission status distribution for a specific user.
        
        Args:
            user_id: The user's ID
            
        Returns:
            Dictionary with counts for each status
        """
        missions = self.rescue_service.get_all_missions_for_analytics() or []
        user_missions = [m for m in missions if m.get("user_id") == user_id]
        
        status_counts = {
            "pending": 0,
            "on-going": 0,
            "rescued": 0,
            "failed": 0,
        }
        
        for mission in user_missions:
            status = RescueStatus.get_base_status((mission.get("status") or "").lower())
            if status in status_counts:
                status_counts[status] += 1
        
        return status_counts

    def get_user_adoption_status_distribution(self, user_id: int) -> Dict[str, int]:
        """Get adoption request status distribution for a specific user.
        
        Args:
            user_id: The user's ID
            
        Returns:
            Dictionary with counts for each status
        """
        requests = self.adoption_service.get_all_requests_for_analytics() or []
        user_requests = [r for r in requests if r.get("user_id") == user_id]
        
        status_counts = {
            "pending": 0,
            "approved": 0,
            "denied": 0,
        }
        
        for req in user_requests:
            status = AdoptionStatus.get_base_status((req.get("status") or "").lower())
            # Use current status - was_approved is only for historical tracking when archived
            if status == "approved":
                status_counts["approved"] += 1
            elif status == "denied":
                status_counts["denied"] += 1
            elif status == "pending":
                status_counts["pending"] += 1
        
        return status_counts

    def get_user_chart_data(self, user_id: int) -> Tuple[List[str], List[int], List[int]]:
        """Get 30-day trend data for a specific user's rescues reported and adoptions approved.
        
        Args:
            user_id: The user's ID
            
        Returns:
            Tuple containing (day_labels, rescues_reported_counts, adoptions_approved_counts)
        """
        # Prepare day labels for last 30 days
        now = datetime.utcnow()
        days: List[datetime] = []
        for i in range(29, -1, -1):
            d = now - timedelta(days=i)
            days.append(d)
        day_labels = [d.strftime("%m-%d") for d in days]
        day_dates = [d.strftime("%Y-%m-%d") for d in days]

        # Initialize counts
        rescues_reported = [0 for _ in day_labels]
        adoptions_approved = [0 for _ in day_labels]

        # Get user's rescue missions
        missions = self.rescue_service.get_all_missions_for_analytics() or []
        user_missions = [m for m in missions if m.get("user_id") == user_id]
        
        for ms in missions:
            # Only count this user's reported rescues
            if ms.get("user_id") != user_id:
                continue
            dt = ms.get("mission_date")
            if not dt:
                continue
            d = parse_datetime(dt)
            if d is None:
                continue
            date_str = d.strftime("%Y-%m-%d")
            if date_str in day_dates:
                idx = day_dates.index(date_str)
                rescues_reported[idx] += 1

        # Get user's adoption requests
        requests = self.adoption_service.get_all_requests_for_analytics() or []
        user_requests = [r for r in requests if r.get("user_id") == user_id]
        
        for req in user_requests:
            dt = req.get("request_date")
            if not dt:
                continue
            d = parse_datetime(dt)
            if d is None:
                continue
            date_str = d.strftime("%Y-%m-%d")
            if date_str in day_dates:
                idx = day_dates.index(date_str)
                # Count approved adoptions
                status_lower = (req.get("status") or "").lower()
                base_status = AdoptionStatus.get_base_status(status_lower)
                if base_status in app_config.APPROVED_ADOPTION_STATUSES or req.get("was_approved") == 1:
                    adoptions_approved[idx] += 1

        return (day_labels, rescues_reported, adoptions_approved)

    def get_user_insights(self, user_id: int) -> Dict[str, Any]:
        """Generate personalized insights for a specific user.
        
        Args:
            user_id: The user's ID
            
        Returns:
            Dictionary with user-specific insights and encouragement messages.
        """
        insights = {}
        
        # Get user activity stats
        stats = self.get_user_activity_stats(user_id)
        rescue_status_dist = self.get_user_rescue_status_distribution(user_id)
        adoption_status_dist = self.get_user_adoption_status_distribution(user_id)
        
        total_rescues = stats.get("rescue_reports_filed", 0)
        rescued_count = rescue_status_dist.get("rescued", 0)
        failed_count = rescue_status_dist.get("failed", 0)
        pending_rescues = rescue_status_dist.get("pending", 0)
        ongoing_rescues = rescue_status_dist.get("on-going", 0)
        
        total_adoptions = stats.get("total_adoptions", 0)
        pending_adoptions = stats.get("pending_adoption_requests", 0)
        denied_adoptions = adoption_status_dist.get("denied", 0)
        
        # RESCUE INSIGHT - Personalized for user
        if total_rescues > 0:
            if rescued_count > 0:
                success_rate = (rescued_count / total_rescues) * 100
                rescue_headline = f"You've helped rescue {rescued_count} animal{'s' if rescued_count > 1 else ''}!"
                rescue_detail = f"{rescued_count} of your {total_rescues} report{'s' if total_rescues > 1 else ''} led to successful rescues."
            else:
                rescue_headline = f"You've reported {total_rescues} rescue{'s' if total_rescues > 1 else ''}."
                rescue_detail = "Your reports are being processed by our team."
            
            if pending_rescues > 0 or ongoing_rescues > 0:
                active = pending_rescues + ongoing_rescues
                rescue_action = f"🐾 {active} mission{'s' if active > 1 else ''} still in progress."
            elif rescued_count > 0:
                rescue_action = "✓ Thank you for making a difference!"
            else:
                rescue_action = "📋 Keep reporting animals in need!"
            
            insights["rescue_insight"] = {
                "headline": rescue_headline,
                "detail": rescue_detail,
                "action": rescue_action,
            }
        else:
            insights["rescue_insight"] = {
                "headline": "No rescues reported yet",
                "detail": "Spot an animal in need? Report it!",
                "action": "🐾 Your reports help save lives.",
            }
        
        # ADOPTION INSIGHT - Personalized for user
        if total_adoptions > 0 or pending_adoptions > 0 or denied_adoptions > 0:
            if total_adoptions > 0:
                adoption_headline = f"You've adopted {total_adoptions} animal{'s' if total_adoptions > 1 else ''}!"
                adoption_detail = f"Thank you for giving {'them' if total_adoptions > 1 else 'them'} a forever home."
            elif pending_adoptions > 0:
                adoption_headline = f"{pending_adoptions} adoption{'s' if pending_adoptions > 1 else ''} pending"
                adoption_detail = "Your application is being reviewed."
            else:
                adoption_headline = "Keep trying!"
                adoption_detail = "The right match is out there for you."
            
            if pending_adoptions > 0:
                adoption_action = f"⏳ {pending_adoptions} application{'s' if pending_adoptions > 1 else ''} awaiting review."
            elif total_adoptions > 0:
                adoption_action = "❤️ You're an amazing adopter!"
            else:
                adoption_action = "💡 Browse our available animals."
            
            insights["adoption_insight"] = {
                "headline": adoption_headline,
                "detail": adoption_detail,
                "action": adoption_action,
            }
        else:
            insights["adoption_insight"] = {
                "headline": "No adoptions yet",
                "detail": "Ready to give an animal a forever home?",
                "action": "❤️ Browse animals available for adoption.",
            }
        
        # ACTIVITY INSIGHT - Overall encouragement
        total_activity = total_rescues + total_adoptions + pending_adoptions
        if total_activity >= 5:
            activity_headline = "You're a PawRes hero!"
            activity_detail = f"With {total_activity} total contributions, you're making a huge impact."
            activity_action = "🌟 Keep up the amazing work!"
        elif total_activity >= 2:
            activity_headline = "Great contribution!"
            activity_detail = f"You've made {total_activity} contributions so far."
            activity_action = "📈 Every action counts!"
        elif total_activity == 1:
            activity_headline = "You've started helping!"
            activity_detail = "Your first contribution makes a difference."
            activity_action = "🚀 Keep going!"
        else:
            activity_headline = "Welcome to PawRes!"
            activity_detail = "Start your journey by adopting or reporting a rescue."
            activity_action = "🐕 Every animal deserves love."
        
        insights["activity_insight"] = {
            "headline": activity_headline,
            "detail": activity_detail,
            "action": activity_action,
        }
        
        # Store raw stats for display
        insights["rescued_count"] = rescued_count
        insights["total_rescues"] = total_rescues
        insights["total_adoptions"] = total_adoptions
        insights["pending_adoptions"] = pending_adoptions
        
        return insights

    def get_chart_insights(self) -> Dict[str, Any]:
        """Generate insights from chart data.
        
        Returns:
            Dictionary with key insights and actionable recommendations.
        """
        insights = {}
        
        # Get chart data for trend analysis
        (day_labels, rescued_counts, adopted_counts), type_dist, status_counts = self.get_chart_data()
        
        # Busiest rescue day (last 30 days)
        if rescued_counts and any(c > 0 for c in rescued_counts):
            max_idx = rescued_counts.index(max(rescued_counts))
            if rescued_counts[max_idx] > 0:
                insights["busiest_rescue_day"] = day_labels[max_idx]
                insights["busiest_rescue_count"] = rescued_counts[max_idx]
        
        # Most common animal type
        if type_dist:
            most_common = max(type_dist.items(), key=lambda x: x[1])
            insights["most_common_species"] = most_common[0]
            insights["most_common_count"] = most_common[1]
            insights["total_species"] = len(type_dist)
        
        # Rescue success rate
        rescue_status = self.get_rescue_status_distribution()
        total_missions = sum(rescue_status.values())
        rescued_count = rescue_status.get("rescued", 0)
        failed_count = rescue_status.get("failed", 0)
        active_count = rescue_status.get("pending", 0) + rescue_status.get("on-going", 0)
        
        if total_missions > 0:
            success_rate = (rescued_count / total_missions) * 100
            insights["rescue_success_rate"] = success_rate
            insights["total_rescues"] = rescued_count
            insights["active_missions"] = active_count
            insights["failed_missions"] = failed_count
        
        # Adoption approval rate
        adoption_status = self.get_adoption_status_distribution()
        total_requests = sum(adoption_status.values())
        approved_count = adoption_status.get("approved", 0)
        pending_count = adoption_status.get("pending", 0)
        denied_count = adoption_status.get("denied", 0)
        
        if total_requests > 0:
            approval_rate = (approved_count / total_requests) * 100
            insights["adoption_approval_rate"] = approval_rate
            insights["total_adoptions"] = approved_count
            insights["pending_adoptions"] = pending_count
            insights["denied_adoptions"] = denied_count
        
        # Top adopted species
        top_species = self.get_species_adoption_ranking(limit=3)
        if top_species:
            insights["top_adopted_species"] = top_species[0][0]
            insights["top_adopted_count"] = top_species[0][1]
            insights["species_ranking"] = top_species
        
        # Health status summary
        total_animals = sum(status_counts.values())
        healthy_count = status_counts.get("healthy", 0)
        recovering_count = status_counts.get("recovering", 0)
        injured_count = status_counts.get("injured", 0)
        
        if total_animals > 0:
            healthy_pct = (healthy_count / total_animals) * 100
            insights["healthy_percentage"] = healthy_pct
            insights["healthy_count"] = healthy_count
            insights["recovering_count"] = recovering_count
            insights["injured_count"] = injured_count
            insights["total_animals"] = total_animals
        
        # Urgency distribution
        urgency_dist = self.get_urgency_distribution()
        high_urgency = urgency_dist.get("high", 0)
        insights["high_urgency_count"] = high_urgency
        
        # 30-day trends
        total_rescued_30d = sum(rescued_counts)
        total_adopted_30d = sum(adopted_counts)
        insights["rescued_30d"] = total_rescued_30d
        insights["adopted_30d"] = total_adopted_30d
        
        # =====================================================
        # Generate intelligent, contextual insight messages
        # =====================================================
        
        # RESCUE INSIGHT - Contextual analysis
        if total_missions > 0:
            success_rate = insights.get("rescue_success_rate", 0)
            
            if success_rate >= 80:
                rescue_headline = f"Excellent performance! {success_rate:.0f}% rescue success rate."
                rescue_detail = f"Your team has successfully rescued {rescued_count} animals."
            elif success_rate >= 50:
                rescue_headline = f"Good progress with {success_rate:.0f}% success rate."
                rescue_detail = f"{rescued_count} rescued, {active_count} missions still active."
            else:
                rescue_headline = f"Needs attention: {success_rate:.0f}% success rate."
                rescue_detail = f"Consider reviewing protocols. {failed_count} missions unsuccessful."
            
            if active_count > 0:
                rescue_action = f"📋 {active_count} active mission{'s' if active_count > 1 else ''} require attention."
            elif high_urgency > 0:
                rescue_action = f"⚠️ {high_urgency} high-urgency case{'s' if high_urgency > 1 else ''} pending."
            else:
                rescue_action = "✓ All missions up to date."
            
            insights["rescue_insight"] = {
                "headline": rescue_headline,
                "detail": rescue_detail,
                "action": rescue_action,
            }
        else:
            insights["rescue_insight"] = {
                "headline": "No rescue missions yet",
                "detail": "Start by adding rescue reports from the community.",
                "action": "📋 Ready to receive rescue requests.",
            }
        
        # ADOPTION INSIGHT - Contextual analysis
        if total_requests > 0:
            approval_rate = insights.get("adoption_approval_rate", 0)
            
            if approval_rate >= 70:
                adoption_headline = f"Strong adoption rate: {approval_rate:.0f}% approved!"
            elif approval_rate >= 40:
                adoption_headline = f"Moderate adoption: {approval_rate:.0f}% approval rate."
            else:
                adoption_headline = f"Low approval rate: {approval_rate:.0f}%. Review criteria?"
            
            if approved_count > 0 and top_species:
                adoption_detail = f"{approved_count} animals found homes. {top_species[0][0]}s are most popular!"
            else:
                adoption_detail = f"{approved_count} adoption{'s' if approved_count != 1 else ''} completed so far."
            
            if pending_count > 0:
                adoption_action = f"📬 {pending_count} application{'s' if pending_count > 1 else ''} awaiting review."
            else:
                adoption_action = "✓ No pending applications."
            
            insights["adoption_insight"] = {
                "headline": adoption_headline,
                "detail": adoption_detail,
                "action": adoption_action,
            }
        else:
            insights["adoption_insight"] = {
                "headline": "No adoption requests yet",
                "detail": "Promote your available animals to attract adopters.",
                "action": "💡 Consider social media outreach.",
            }
        
        # HEALTH INSIGHT - Contextual analysis
        if total_animals > 0:
            healthy_pct = insights.get("healthy_percentage", 0)
            
            if healthy_pct >= 80:
                health_headline = f"Great health status: {healthy_pct:.0f}% of animals are healthy!"
            elif healthy_pct >= 50:
                health_headline = f"Moderate health: {healthy_pct:.0f}% healthy, {recovering_count} recovering."
            else:
                health_headline = f"Health concern: Only {healthy_pct:.0f}% are fully healthy."
            
            if recovering_count > 0 or injured_count > 0:
                health_detail = f"{recovering_count} animal{'s' if recovering_count != 1 else ''} recovering, {injured_count} need{'s' if injured_count == 1 else ''} medical care."
            else:
                health_detail = f"All {healthy_count} animals in your care are healthy!"
            
            if injured_count > 0:
                health_action = f"🏥 Prioritize care for {injured_count} injured animal{'s' if injured_count > 1 else ''}."
            elif recovering_count > 0:
                health_action = f"💊 Monitor {recovering_count} recovering animal{'s' if recovering_count > 1 else ''}."
            else:
                health_action = "✓ No immediate health concerns."
            
            # Add species info
            if type_dist:
                species_info = f"🐾 Population: {', '.join(f'{v} {k}s' for k, v in sorted(type_dist.items(), key=lambda x: -x[1])[:3])}"
                health_detail = species_info
            
            insights["health_insight"] = {
                "headline": health_headline,
                "detail": health_detail,
                "action": health_action,
            }
        else:
            insights["health_insight"] = {
                "headline": "No animals registered",
                "detail": "Add animals to start tracking their health.",
                "action": "📝 Add your first animal to get started.",
            }
        
        return insights

    def invalidate_cache(self) -> None:
        """Invalidate all cached analytics data.
        
        Call this after data modifications that affect analytics
        (e.g., new animal, new adoption request, etc.)
        """
        self._cache.clear()
        print("[DEBUG] AnalyticsService: Cache invalidated")


__all__ = ["AnalyticsService"]
