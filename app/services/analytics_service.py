"""Analytics service for data aggregation and reporting."""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple
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
        
        self.animal_service = AnimalService(self.db)
        self.rescue_service = RescueService(self.db)
        self.adoption_service = AdoptionService(self.db)
        
        self._cache: QueryCache = get_query_cache()
        self._cache_ttl = 120

    def get_chart_data(self) -> Tuple[Tuple[List[str], List[int], List[int]], Dict[str, int], Dict[str, int]]:
        """Return aggregated data for charts.
        
        Returns:
            Tuple containing:
            - (day_labels, rescued_counts, adopted_counts): Daily trend data for last 1 month
            - type_dist: Dictionary of animal type distribution (empty dict if no data)
            - status_counts: Dictionary of health status counts (always includes healthy, recovering, injured)
        """
        now = datetime.utcnow()
        days: List[datetime] = []
        for i in range(29, -1, -1):
            d = now - timedelta(days=i)
            days.append(d)
        day_labels = [d.strftime("%m-%d") for d in days]
        day_dates = [d.strftime("%Y-%m-%d") for d in days]

        rescued_counts = [0 for _ in day_labels]
        adopted_counts = [0 for _ in day_labels]

        missions = self.rescue_service.get_all_missions_for_analytics() or []
        for ms in missions:
            status = (ms.get("status") or "").lower()
            base_status = RescueStatus.get_base_status(status)
            is_rescued = base_status == RescueStatus.RESCUED
            if not is_rescued:
                continue
            dt = ms.get("rescued_at") or ms.get("mission_date")
            if not dt:
                continue
            # Parse date using shared helper
            d = parse_datetime(dt)
            if d is None:
                continue
            date_str = d.strftime("%Y-%m-%d")
            if date_str in day_dates:
                idx = day_dates.index(date_str)
                rescued_counts[idx] += 1

        requests = self.adoption_service.get_all_requests_for_analytics() or []
        for req in requests:
            # Only count requests with approved status (current or archived)
            status_lower = (req.get("status") or "").lower()
            base_status = AdoptionStatus.get_base_status(status_lower)
            if base_status not in app_config.APPROVED_ADOPTION_STATUSES:
                continue
            dt = req.get("approved_at") or req.get("request_date")
            if not dt:
                continue
            d = parse_datetime(dt)
            if d is None:
                continue
            date_str = d.strftime("%Y-%m-%d")
            if date_str in day_dates:
                idx = day_dates.index(date_str)
                adopted_counts[idx] += 1

        type_dist, status_counts = self.get_animal_statistics()

        return (day_labels, rescued_counts, adopted_counts), type_dist, status_counts

    def get_chart_data_14_days(self) -> Tuple[List[str], List[int], List[int]]:
        """Return 14-day trend data for rescued vs adopted chart (admin dashboard).
        
        Returns:
            Tuple containing (day_labels, rescued_counts, adopted_counts)
        """
        now = datetime.utcnow()
        days: List[datetime] = []
        for i in range(13, -1, -1):
            d = now - timedelta(days=i)
            days.append(d)
        day_labels = [d.strftime("%m-%d") for d in days]
        day_dates = [d.strftime("%Y-%m-%d") for d in days]

        rescued_counts = [0 for _ in day_labels]
        adopted_counts = [0 for _ in day_labels]

        missions = self.rescue_service.get_all_missions_for_analytics() or []
        for ms in missions:
            status = (ms.get("status") or "").lower()
            base_status = RescueStatus.get_base_status(status)
            is_rescued = base_status == RescueStatus.RESCUED
            if not is_rescued:
                continue
            dt = ms.get("rescued_at") or ms.get("mission_date")
            if not dt:
                continue
            d = parse_datetime(dt)
            if d is None:
                continue
            date_str = d.strftime("%Y-%m-%d")
            if date_str in day_dates:
                idx = day_dates.index(date_str)
                rescued_counts[idx] += 1

        requests = self.adoption_service.get_all_requests_for_analytics() or []
        for req in requests:
            # Only count requests with approved status (current or archived)
            status_lower = (req.get("status") or "").lower()
            base_status = AdoptionStatus.get_base_status(status_lower)
            if base_status not in app_config.APPROVED_ADOPTION_STATUSES:
                continue
            dt = req.get("approved_at") or req.get("request_date")
            if not dt:
                continue
            d = parse_datetime(dt)
            if d is None:
                continue
            date_str = d.strftime("%Y-%m-%d")
            if date_str in day_dates:
                idx = day_dates.index(date_str)
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
        status_counts: Dict[str, int] = {
            "healthy": 0,
            "recovering": 0,
            "injured": 0,
        }
        
        for a in animals:
            t = (a.get("species") or "Unknown").strip().capitalize()
            s = (a.get("status") or "unknown").lower()
            base_s = AnimalStatus.get_base_status(s)
            type_dist[t] = type_dist.get(t, 0) + 1
            if base_s in status_counts:
                status_counts[base_s] += 1
            elif base_s in ("adopted", "processing", "unknown", ""):
                pass
            else:
                status_counts["injured"] += 1

        return type_dist, status_counts

    def get_dashboard_stats(self) -> Dict[str, Any]:
        """Get summary statistics for dashboard display.
        
        Excludes "removed" and "cancelled" items from all counts.
        Returns cached results for performance.
        
        Returns:
            Dictionary with total animals, adoptions, and pending requests
        """
        def _fetch_stats():
            animals = self.animal_service.get_all_animals_for_analytics() or []
            all_requests = self.adoption_service.get_all_requests_for_analytics() or []
            
            total_animals = len(animals)
            total_adoptions = len([r for r in all_requests 
                if AdoptionStatus.get_base_status((r.get("status") or "").lower()) in app_config.APPROVED_ADOPTION_STATUSES])
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
        
        this_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        last_month_end = this_month_start - timedelta(days=1)
        last_month_start = last_month_end.replace(day=1)
        
        def is_in_range(dt, start: datetime, end: datetime) -> bool:
            """Check if datetime is within range."""
            parsed = parse_datetime(dt)
            if parsed is None:
                return False
            return start <= parsed <= end
        
        animals = self.animal_service.get_all_animals_for_analytics() or []
        missions = self.rescue_service.get_all_missions_for_analytics() or []
        requests = self.adoption_service.get_all_requests_for_analytics() or []
        
        animals_this_month = len([a for a in animals if is_in_range(a.get("intake_date"), this_month_start, now)])
        animals_last_month = len([a for a in animals if is_in_range(a.get("intake_date"), last_month_start, last_month_end)])
        
        rescues_this_month = len([m for m in missions 
            if is_in_range(m.get("mission_date"), this_month_start, now)
            and RescueStatus.get_base_status((m.get("status") or "").lower()) == RescueStatus.RESCUED])
        rescues_last_month = len([m for m in missions 
            if is_in_range(m.get("mission_date"), last_month_start, last_month_end)
            and RescueStatus.get_base_status((m.get("status") or "").lower()) == RescueStatus.RESCUED])
        
        adoptions_this_month = len([r for r in requests 
            if is_in_range(r.get("request_date"), this_month_start, now) 
            and AdoptionStatus.get_base_status((r.get("status") or "").lower()) in app_config.APPROVED_ADOPTION_STATUSES])
        adoptions_last_month = len([r for r in requests 
            if is_in_range(r.get("request_date"), last_month_start, last_month_end)
            and AdoptionStatus.get_base_status((r.get("status") or "").lower()) in app_config.APPROVED_ADOPTION_STATUSES])
        
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
        
        Excludes "removed" and "cancelled" items from counts.
        
        Args:
            user_id: The user's ID
            
        Returns:
            Dictionary with user's adoption and rescue statistics
        """
        all_adoptions = self.adoption_service.get_all_requests_for_analytics() or []
        all_rescues = self.rescue_service.get_all_missions_for_analytics() or []
        
        user_adoptions = [a for a in all_adoptions if a.get("user_id") == user_id]
        user_rescues = [r for r in all_rescues if r.get("user_id") == user_id]
        
        total_adoptions = len([a for a in user_adoptions 
                              if AdoptionStatus.get_base_status((a.get("status") or "").lower()) == "approved"])
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
            if status == "approved":
                species = (req.get("animal_species") or "Unknown").strip().capitalize()
                species_counts[species] = species_counts.get(species, 0) + 1
        
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
        now = datetime.utcnow()
        days: List[datetime] = []
        for i in range(29, -1, -1):
            d = now - timedelta(days=i)
            days.append(d)
        day_labels = [d.strftime("%m-%d") for d in days]
        day_dates = [d.strftime("%Y-%m-%d") for d in days]

        rescues_reported = [0 for _ in day_labels]
        adoptions_approved = [0 for _ in day_labels]

        missions = self.rescue_service.get_all_missions_for_analytics() or []
        user_missions = [m for m in missions if m.get("user_id") == user_id]
        
        for ms in missions:
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
                status_lower = (req.get("status") or "").lower()
                base_status = AdoptionStatus.get_base_status(status_lower)
                if base_status in app_config.APPROVED_ADOPTION_STATUSES:
                    adoptions_approved[idx] += 1

        return (day_labels, rescues_reported, adoptions_approved)

    def get_user_insights(self, user_id: int) -> Dict[str, Any]:
        """Generate personalized insights for a specific user.
        
        Args:
            user_id: The user's ID
            
        Returns:
            Dictionary with user-specific insights and encouragement messages.
            Uses structured format for rich Flet rendering.
        """
        insights = {}
        
        stats = self.get_user_activity_stats(user_id)
        rescue_status_dist = self.get_user_rescue_status_distribution(user_id)
        adoption_status_dist = self.get_user_adoption_status_distribution(user_id)
        
        total_rescues = stats.get("rescue_reports_filed", 0)
        rescued_count = rescue_status_dist.get("rescued", 0)
        failed_count = rescue_status_dist.get("failed", 0)
        pending_rescues = rescue_status_dist.get("pending", 0)
        ongoing_rescues = rescue_status_dist.get("on-going", 0)
        
        total_adoptions = adoption_status_dist.get("approved", 0)
        pending_adoptions = adoption_status_dist.get("pending", 0)
        denied_adoptions = adoption_status_dist.get("denied", 0)
        
        # RESCUE INSIGHT - Personalized for user with rich formatting
        if total_rescues > 0:
            if rescued_count > 0:
                success_rate = (rescued_count / total_rescues) * 100
                rescue_headline = {
                    "text": f"You've helped rescue {rescued_count} animal{'s' if rescued_count > 1 else ''}!",
                    "icon": "VOLUNTEER_ACTIVISM",
                    "color": "GREEN_700",
                }
                rescue_detail = {
                    "parts": [
                        {"text": str(rescued_count), "weight": "bold", "color": "GREEN_600"},
                        {"text": " of your ", "weight": "normal"},
                        {"text": str(total_rescues), "weight": "bold", "color": "ORANGE_600"},
                        {"text": f" report{'s' if total_rescues > 1 else ''} led to successful rescues.", "weight": "normal"},
                    ]
                }
            else:
                rescue_headline = {
                    "text": f"You've reported {total_rescues} rescue{'s' if total_rescues > 1 else ''}.",
                    "icon": "PETS",
                    "color": "ORANGE_700",
                }
                rescue_detail = {
                    "parts": [
                        {"text": "Your reports are being processed by our team.", "weight": "normal"},
                    ]
                }
            
            if pending_rescues > 0 and ongoing_rescues > 0:
                rescue_action = {
                    "icon": "ASSIGNMENT",
                    "text": f"{pending_rescues} pending, {ongoing_rescues} on-going mission{'s' if (pending_rescues + ongoing_rescues) > 1 else ''}.",
                    "color": "BLUE_600",
                    "bg_color": "BLUE_50",
                    "severity": "info",
                }
            elif pending_rescues > 0:
                rescue_action = {
                    "icon": "SCHEDULE",
                    "text": f"{pending_rescues} mission{'s' if pending_rescues > 1 else ''} awaiting response.",
                    "color": "ORANGE_600",
                    "bg_color": "ORANGE_50",
                    "severity": "info",
                }
            elif ongoing_rescues > 0:
                rescue_action = {
                    "icon": "LOCAL_FIRE_DEPARTMENT",
                    "text": f"{ongoing_rescues} rescue{'s' if ongoing_rescues > 1 else ''} currently in progress.",
                    "color": "ORANGE_700",
                    "bg_color": "ORANGE_50",
                    "severity": "warning",
                }
            elif rescued_count > 0:
                rescue_action = {
                    "icon": "CHECK_CIRCLE",
                    "text": "All your reports have been resolved!",
                    "color": "GREEN_600",
                    "bg_color": "GREEN_50",
                    "severity": "success",
                }
            else:
                rescue_action = {
                    "icon": "PETS",
                    "text": "Keep reporting animals in need!",
                    "color": "TEAL_600",
                    "bg_color": "TEAL_50",
                    "severity": "info",
                }
            
            insights["rescue_insight"] = {
                "headline": rescue_headline,
                "detail": rescue_detail,
                "action": rescue_action,
            }
        else:
            insights["rescue_insight"] = {
                "headline": {
                    "text": "No rescues reported yet",
                    "icon": "INFO",
                    "color": "GREY_700",
                },
                "detail": {
                    "parts": [
                        {"text": "Spot an animal in need? ", "weight": "normal"},
                        {"text": "Report it!", "weight": "bold", "color": "ORANGE_600"},
                    ]
                },
                "action": {
                    "icon": "PETS",
                    "text": "Your reports help save lives.",
                    "color": "TEAL_600",
                    "bg_color": "TEAL_50",
                    "severity": "info",
                },
            }
        
        # ADOPTION INSIGHT - Personalized for user with rich formatting
        if total_adoptions > 0 or pending_adoptions > 0 or denied_adoptions > 0:
            breed_prefs = self.get_user_breed_preferences(user_id, limit=1)
            top_breed = breed_prefs[0][0] if breed_prefs else None
            top_breed_count = breed_prefs[0][1] if breed_prefs else 0
            
            if total_adoptions > 0:
                if top_breed and top_breed_count > 0:
                    adoption_headline = {
                        "text": f"You've adopted {total_adoptions} animal{'s' if total_adoptions > 1 else ''}!",
                        "icon": "HOME",
                        "color": "TEAL_700",
                    }
                    adoption_detail = {
                        "parts": [
                            {"text": "Your preference: ", "weight": "normal"},
                            {"text": top_breed, "weight": "bold", "color": "TEAL_600"},
                            {"text": f" ({top_breed_count} request{'s' if top_breed_count > 1 else ''}).", "weight": "normal"},
                        ]
                    }
                else:
                    adoption_headline = {
                        "text": f"You've adopted {total_adoptions} animal{'s' if total_adoptions > 1 else ''}!",
                        "icon": "HOME",
                        "color": "TEAL_700",
                    }
                    adoption_detail = {
                        "parts": [
                            {"text": "Thank you for giving ", "weight": "normal"},
                            {"text": "them", "weight": "bold", "color": "TEAL_600"},
                            {"text": " a forever home.", "weight": "normal"},
                        ]
                    }
            elif pending_adoptions > 0:
                adoption_headline = {
                    "text": f"{pending_adoptions} adoption{'s' if pending_adoptions > 1 else ''} pending",
                    "icon": "HOURGLASS_BOTTOM",
                    "color": "BLUE_700",
                }
                if top_breed:
                    adoption_detail = {
                        "parts": [
                            {"text": "Interested in ", "weight": "normal"},
                            {"text": top_breed, "weight": "bold", "color": "TEAL_600"},
                            {"text": ". Application being reviewed.", "weight": "normal"},
                        ]
                    }
                else:
                    adoption_detail = {
                        "parts": [
                            {"text": "Your application is being ", "weight": "normal"},
                            {"text": "reviewed", "weight": "bold", "color": "BLUE_600"},
                            {"text": ".", "weight": "normal"},
                        ]
                    }
            else:
                adoption_headline = {
                    "text": "Keep trying!",
                    "icon": "HELP_OUTLINE",
                    "color": "AMBER_700",
                }
                adoption_detail = {
                    "parts": [
                        {"text": "The right match is out there for you.", "weight": "normal"},
                    ]
                }
            
            if pending_adoptions > 0:
                adoption_action = {
                    "icon": "SCHEDULE",
                    "text": f"{pending_adoptions} application{'s' if pending_adoptions > 1 else ''} awaiting review.",
                    "color": "BLUE_600",
                    "bg_color": "BLUE_50",
                    "severity": "info",
                }
            elif total_adoptions > 0:
                adoption_action = {
                    "icon": "EMOJI_EVENTS",
                    "text": "You're an amazing adopter!",
                    "color": "AMBER_600",
                    "bg_color": "AMBER_50",
                    "severity": "success",
                }
            else:
                adoption_action = {
                    "icon": "PETS",
                    "text": "Browse our available animals.",
                    "color": "TEAL_600",
                    "bg_color": "TEAL_50",
                    "severity": "info",
                }
            
            insights["adoption_insight"] = {
                "headline": adoption_headline,
                "detail": adoption_detail,
                "action": adoption_action,
            }
        else:
            insights["adoption_insight"] = {
                "headline": {
                    "text": "No adoptions yet",
                    "icon": "INFO",
                    "color": "GREY_700",
                },
                "detail": {
                    "parts": [
                        {"text": "Ready to give an animal a ", "weight": "normal"},
                        {"text": "forever home", "weight": "bold", "color": "TEAL_600"},
                        {"text": "?", "weight": "normal"},
                    ]
                },
                "action": {
                    "icon": "FAVORITE",
                    "text": "Browse animals available for adoption.",
                    "color": "TEAL_600",
                    "bg_color": "TEAL_50",
                    "severity": "info",
                },
            }
        
        # ACTIVITY INSIGHT - Overall encouragement with rich formatting
        total_activity = total_rescues + total_adoptions + pending_adoptions
        breed_prefs_all = self.get_user_breed_preferences(user_id, limit=10)
        breed_diversity = len(breed_prefs_all)
        
        if total_activity >= 5:
            activity_headline = {
                "text": "You're a PawRes hero!",
                "icon": "EMOJI_EVENTS",
                "color": "AMBER_700",
            }
            if breed_diversity > 1:
                activity_detail = {
                    "parts": [
                        {"text": str(total_activity), "weight": "bold", "color": "AMBER_600"},
                        {"text": " contributions across ", "weight": "normal"},
                        {"text": str(breed_diversity), "weight": "bold", "color": "PURPLE_600"},
                        {"text": " breed types. ", "weight": "normal"},
                        {"text": "Amazing diversity!", "weight": "bold", "color": "GREEN_600"},
                    ]
                }
            else:
                activity_detail = {
                    "parts": [
                        {"text": "With ", "weight": "normal"},
                        {"text": str(total_activity), "weight": "bold", "color": "AMBER_600"},
                        {"text": " total contributions, you're making a ", "weight": "normal"},
                        {"text": "huge impact", "weight": "bold", "color": "GREEN_600"},
                        {"text": ".", "weight": "normal"},
                    ]
                }
            activity_action = {
                "icon": "VERIFIED",
                "text": "Keep up the amazing work!",
                "color": "AMBER_600",
                "bg_color": "AMBER_50",
                "severity": "success",
            }
        elif total_activity >= 2:
            activity_headline = {
                "text": "Great contribution!",
                "icon": "THUMB_UP",
                "color": "GREEN_700",
            }
            activity_detail = {
                "parts": [
                    {"text": "You've made ", "weight": "normal"},
                    {"text": str(total_activity), "weight": "bold", "color": "GREEN_600"},
                    {"text": " contributions so far.", "weight": "normal"},
                ]
            }
            activity_action = {
                "icon": "TRENDING_UP",
                "text": "Every action counts!",
                "color": "GREEN_600",
                "bg_color": "GREEN_50",
                "severity": "success",
            }
        elif total_activity == 1:
            activity_headline = {
                "text": "You've started helping!",
                "icon": "VOLUNTEER_ACTIVISM",
                "color": "TEAL_700",
            }
            activity_detail = {
                "parts": [
                    {"text": "Your ", "weight": "normal"},
                    {"text": "first contribution", "weight": "bold", "color": "TEAL_600"},
                    {"text": " makes a difference.", "weight": "normal"},
                ]
            }
            activity_action = {
                "icon": "TRENDING_UP",
                "text": "Keep going!",
                "color": "TEAL_600",
                "bg_color": "TEAL_50",
                "severity": "info",
            }
        else:
            activity_headline = {
                "text": "Welcome to PawRes!",
                "icon": "WAVING_HAND",
                "color": "BLUE_700",
            }
            activity_detail = {
                "parts": [
                    {"text": "Start your journey by ", "weight": "normal"},
                    {"text": "adopting", "weight": "bold", "color": "TEAL_600"},
                    {"text": " or ", "weight": "normal"},
                    {"text": "reporting a rescue", "weight": "bold", "color": "ORANGE_600"},
                    {"text": ".", "weight": "normal"},
                ]
            }
            activity_action = {
                "icon": "PETS",
                "text": "Every animal deserves love.",
                "color": "TEAL_600",
                "bg_color": "TEAL_50",
                "severity": "info",
            }
        
        insights["activity_insight"] = {
            "headline": activity_headline,
            "detail": activity_detail,
            "action": activity_action,
        }
        
        insights["rescued_count"] = rescued_count
        insights["total_rescues"] = total_rescues
        insights["total_adoptions"] = total_adoptions
        insights["pending_adoptions"] = pending_adoptions
        
        return insights

    def get_breed_insights(self) -> Dict[str, Any]:
        """Generate breed-specific insights with species context.
        
        Returns:
            Dictionary with structured breed insight data including:
            - headline: Main message about most popular breed
            - detail: Top 3 adopted breeds with species and breed diversity info
            - action: Most adopted breed or 30-day trend info
        """
        insight = {}
        
        requests = self.adoption_service.get_all_requests_for_analytics() or []
        
        breed_species_counts: Dict[str, Tuple[str, int]] = {}  # breed -> (species, count)
        
        for req in requests:
            status = AdoptionStatus.get_base_status((req.get("status") or "").lower())
            if status != "cancelled":
                breed = self._normalize_breed(req.get("animal_breed"))
                species = (req.get("animal_species") or "Unknown").strip().capitalize()
                
                if breed in breed_species_counts:
                    # Increment count (keep first species seen for this breed)
                    existing_species, count = breed_species_counts[breed]
                    breed_species_counts[breed] = (existing_species, count + 1)
                else:
                    breed_species_counts[breed] = (species, 1)
        
        sorted_breeds = sorted(breed_species_counts.items(), key=lambda x: x[1][1], reverse=True)
        
        if sorted_breeds:
            top_breed, (top_species, top_count) = sorted_breeds[0]
            total_breeds = len(sorted_breeds)
            
            # HEADLINE: Most popular breed with species
            breed_headline = {
                "text": f"{top_breed} ({top_species}) is most popular!",
                "icon": "EMOJI_EVENTS",
                "color": "PURPLE_700",
            }
            
            # DETAIL: Top 1 adopted breed with species only
            detail_parts = []
            detail_parts.append({"text": "Most adopted: ", "weight": "normal"})
            detail_parts.append({"text": f"{top_breed} ({top_species})", "weight": "bold", "color": "PURPLE_800"})
            
            breed_detail = {"parts": detail_parts}
            
            # ACTION: Most adopted breed or 30-day trend
            now = datetime.utcnow()
            thirty_days_ago = now - timedelta(days=30)
            
            recent_count = 0
            for req in requests:
                status = AdoptionStatus.get_base_status((req.get("status") or "").lower())
                if status != "cancelled":
                    breed = self._normalize_breed(req.get("animal_breed"))
                    if breed == top_breed:
                        dt = parse_datetime(req.get("request_date"))
                        if dt and dt >= thirty_days_ago:
                            recent_count += 1
            
            if recent_count > 0:
                breed_action = {
                    "icon": "TRENDING_UP",
                    "text": f"{top_breed} ({top_species}): {recent_count} request{'s' if recent_count > 1 else ''} in 30 days.",
                    "color": "PURPLE_600",
                    "bg_color": "PURPLE_50",
                    "severity": "info",
                }
            else:
                breed_action = {
                    "icon": "PETS",
                    "text": f"{top_breed} ({top_species}) is most adopted overall.",
                    "color": "PURPLE_600",
                    "bg_color": "PURPLE_50",
                    "severity": "info",
                }
            
            insight = {
                "headline": breed_headline,
                "detail": breed_detail,
                "action": breed_action,
            }
        else:
            # No breed data available
            insight = {
                "headline": {
                    "text": "No breed data yet",
                    "icon": "INFO",
                    "color": "GREY_700",
                },
                "detail": {
                    "parts": [
                        {"text": "Track adoption requests to see breed popularity trends.", "weight": "normal"},
                    ]
                },
                "action": {
                    "icon": "ADD_CIRCLE",
                    "text": "Start collecting breed information.",
                    "color": "PURPLE_600",
                    "bg_color": "PURPLE_50",
                    "severity": "info",
                },
            }
        
        return insight

    def get_chart_insights(self) -> Dict[str, Any]:
        """Generate insights from chart data.
        
        Returns:
            Dictionary with key insights and actionable recommendations.
        """
        insights = {}
        
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
        
        missions = self.rescue_service.get_all_missions_for_analytics() or []
        pending_high_urgency = len([
            m for m in missions
            if RescueStatus.get_base_status((m.get("status") or "").lower()) == "pending"
            and (m.get("urgency") or "").lower() == "high"
        ])
        ongoing_high_urgency = len([
            m for m in missions
            if RescueStatus.get_base_status((m.get("status") or "").lower()) == "on-going"
            and (m.get("urgency") or "").lower() == "high"
        ])
        insights["pending_high_urgency"] = pending_high_urgency
        insights["ongoing_high_urgency"] = ongoing_high_urgency
        insights["active_high_urgency"] = pending_high_urgency + ongoing_high_urgency
        
        # 30-day trends
        total_rescued_30d = sum(rescued_counts)
        total_adopted_30d = sum(adopted_counts)
        insights["rescued_30d"] = total_rescued_30d
        insights["adopted_30d"] = total_adopted_30d
        
        # Generate intelligent, contextual insight messages
        # Return structured data for rich Flet rendering
        
        # RESCUE INSIGHT - Contextual analysis
        if total_missions > 0:
            success_rate = insights.get("rescue_success_rate", 0)
            
            top_rescued_breeds = self.get_top_breeds_for_rescue(limit=1)
            top_rescued_breed_info = None
            if top_rescued_breeds:
                top_breed = top_rescued_breeds[0][0]
                missions = self.rescue_service.get_all_missions_for_analytics() or []
                for m in missions:
                    if self._normalize_breed(m.get("breed")) == top_breed:
                        species = (m.get("animal_type") or "Unknown").strip().capitalize()
                        top_rescued_breed_info = (top_breed, species)
                        break
            
            if success_rate >= 80:
                rescue_headline = {
                    "text": f"Excellent performance! {success_rate:.0f}% rescue success rate.",
                    "icon": "EMOJI_EVENTS",  # Trophy icon
                    "color": "GREEN_700",
                }
                detail_parts = [
                    {"text": "Your team has successfully rescued ", "weight": "normal"},
                    {"text": str(rescued_count), "weight": "bold", "color": "GREEN_600"},
                    {"text": " animals", "weight": "normal"},
                ]
                if top_rescued_breed_info:
                    breed, species = top_rescued_breed_info
                    detail_parts.extend([
                        {"text": ". Most rescued: ", "weight": "normal"},
                        {"text": f"{breed} ({species})", "weight": "bold", "color": "BLUE_600"},
                    ])
                else:
                    detail_parts.append({"text": ".", "weight": "normal"})
                rescue_detail = {"parts": detail_parts}
            elif success_rate >= 50:
                rescue_headline = {
                    "text": f"Good progress with {success_rate:.0f}% success rate.",
                    "icon": "TRENDING_UP",
                    "color": "BLUE_700",
                }
                rescue_detail = {
                    "parts": [
                        {"text": str(rescued_count), "weight": "bold", "color": "GREEN_600"},
                        {"text": " rescued, ", "weight": "normal"},
                        {"text": str(active_count), "weight": "bold", "color": "ORANGE_600"},
                        {"text": " missions still active.", "weight": "normal"},
                    ]
                }
            else:
                rescue_headline = {
                    "text": f"Needs attention: {success_rate:.0f}% success rate.",
                    "icon": "WARNING_AMBER",
                    "color": "ORANGE_700",
                }
                rescue_detail = {
                    "parts": [
                        {"text": "Consider reviewing protocols. ", "weight": "normal"},
                        {"text": str(failed_count), "weight": "bold", "color": "RED_600"},
                        {"text": " missions unsuccessful.", "weight": "normal"},
                    ]
                }
            
            active_high_urgency = insights.get("active_high_urgency", 0)
            pending_high_urgency = insights.get("pending_high_urgency", 0)
            ongoing_high_urgency = insights.get("ongoing_high_urgency", 0)
            
            if active_count > 0:
                rescue_action = {
                    "icon": "ASSIGNMENT",
                    "text": f"{active_count} active mission{'s' if active_count > 1 else ''} require attention.",
                    "color": "BLUE_600",
                    "bg_color": "BLUE_50",
                    "severity": "info",
                }
            elif active_high_urgency > 0:
                if pending_high_urgency > 0 and ongoing_high_urgency > 0:
                    rescue_action = {
                        "icon": "WARNING_AMBER",
                        "text": f"{pending_high_urgency} pending, {ongoing_high_urgency} on-going high-urgency case{'s' if active_high_urgency > 1 else ''}.",
                        "color": "AMBER_700",
                        "bg_color": "AMBER_50",
                        "severity": "warning",
                    }
                elif pending_high_urgency > 0:
                    rescue_action = {
                        "icon": "SCHEDULE",
                        "text": f"{pending_high_urgency} high-urgency case{'s' if pending_high_urgency > 1 else ''} pending.",
                        "color": "AMBER_700",
                        "bg_color": "AMBER_50",
                        "severity": "warning",
                    }
                else:
                    rescue_action = {
                        "icon": "LOCAL_FIRE_DEPARTMENT",
                        "text": f"{ongoing_high_urgency} high-urgency case{'s' if ongoing_high_urgency > 1 else ''} on-going.",
                        "color": "ORANGE_700",
                        "bg_color": "ORANGE_50",
                        "severity": "warning",
                    }
            else:
                rescue_action = {
                    "icon": "CHECK_CIRCLE",
                    "text": "All missions up to date.",
                    "color": "GREEN_600",
                    "bg_color": "GREEN_50",
                    "severity": "success",
                }
            
            insights["rescue_insight"] = {
                "headline": rescue_headline,
                "detail": rescue_detail,
                "action": rescue_action,
            }
        else:
            insights["rescue_insight"] = {
                "headline": {
                    "text": "No rescue missions yet",
                    "icon": "INFO",
                    "color": "GREY_700",
                },
                "detail": {
                    "parts": [
                        {"text": "Start by adding rescue reports from the community.", "weight": "normal"},
                    ]
                },
                "action": {
                    "icon": "ADD_CIRCLE",
                    "text": "Ready to receive rescue requests.",
                    "color": "TEAL_600",
                    "bg_color": "TEAL_50",
                    "severity": "info",
                },
            }
        
        # ADOPTION INSIGHT - Contextual analysis
        if total_requests > 0:
            approval_rate = insights.get("adoption_approval_rate", 0)
            
            if approval_rate >= 70:
                adoption_headline = {
                    "text": f"Strong adoption rate: {approval_rate:.0f}% approved!",
                    "icon": "THUMB_UP",
                    "color": "GREEN_700",
                }
            elif approval_rate >= 40:
                adoption_headline = {
                    "text": f"Moderate adoption: {approval_rate:.0f}% approval rate.",
                    "icon": "TRENDING_FLAT",
                    "color": "ORANGE_700",
                }
            else:
                adoption_headline = {
                    "text": f"Low approval rate: {approval_rate:.0f}%. Review criteria?",
                    "icon": "HELP_OUTLINE",
                    "color": "RED_700",
                }
            
            top_adopted_breeds = self.get_top_breeds_for_adoption(limit=1)
            top_adopted_breed_info = None
            if top_adopted_breeds:
                top_breed = top_adopted_breeds[0][0]
                requests = self.adoption_service.get_all_requests_for_analytics() or []
                for req in requests:
                    if self._normalize_breed(req.get("animal_breed")) == top_breed:
                        species = (req.get("animal_species") or "Unknown").strip().capitalize()
                        top_adopted_breed_info = (top_breed, species)
                        break
            
            if approved_count > 0 and top_adopted_breed_info:
                breed, species = top_adopted_breed_info
                adoption_detail = {
                    "parts": [
                        {"text": str(approved_count), "weight": "bold", "color": "TEAL_600"},
                        {"text": " animals found homes. ", "weight": "normal"},
                        {"text": f"{breed} ({species})", "weight": "bold", "color": "ORANGE_600"},
                        {"text": " is most popular!", "weight": "normal"},
                    ]
                }
            else:
                adoption_detail = {
                    "parts": [
                        {"text": str(approved_count), "weight": "bold", "color": "TEAL_600"},
                        {"text": f" adoption{'s' if approved_count != 1 else ''} completed so far.", "weight": "normal"},
                    ]
                }
            
            if pending_count > 0:
                adoption_action = {
                    "icon": "MARK_EMAIL_UNREAD",
                    "text": f"{pending_count} application{'s' if pending_count > 1 else ''} awaiting review.",
                    "color": "BLUE_600",
                    "bg_color": "BLUE_50",
                    "severity": "info",
                }
            else:
                adoption_action = {
                    "icon": "CHECK_CIRCLE",
                    "text": "No pending applications.",
                    "color": "GREEN_600",
                    "bg_color": "GREEN_50",
                    "severity": "success",
                }
            
            insights["adoption_insight"] = {
                "headline": adoption_headline,
                "detail": adoption_detail,
                "action": adoption_action,
            }
        else:
            insights["adoption_insight"] = {
                "headline": {
                    "text": "No adoption requests yet",
                    "icon": "INFO",
                    "color": "GREY_700",
                },
                "detail": {
                    "parts": [
                        {"text": "Promote your available animals to attract adopters.", "weight": "normal"},
                    ]
                },
                "action": {
                    "icon": "LIGHTBULB",
                    "text": "Consider social media outreach.",
                    "color": "AMBER_600",
                    "bg_color": "AMBER_50",
                    "severity": "tip",
                },
            }
        
        # HEALTH INSIGHT - Contextual analysis
        if total_animals > 0:
            healthy_pct = insights.get("healthy_percentage", 0)
            
            if healthy_pct >= 80:
                health_headline = {
                    "text": f"Great health status: {healthy_pct:.0f}% are healthy!",
                    "icon": "VERIFIED",
                    "color": "GREEN_700",
                }
            elif healthy_pct >= 50:
                health_headline = {
                    "text": f"Moderate health: {healthy_pct:.0f}% healthy, {recovering_count} recovering.",
                    "icon": "HEALING",
                    "color": "ORANGE_700",
                }
            else:
                health_headline = {
                    "text": f"Health concern: Only {healthy_pct:.0f}% are fully healthy.",
                    "icon": "WARNING",
                    "color": "RED_700",
                }
            
            if type_dist:
                species_parts = []
                sorted_species = sorted(type_dist.items(), key=lambda x: -x[1])[:3]
                for i, (species, count) in enumerate(sorted_species):
                    if i > 0:
                        species_parts.append({"text": ", ", "weight": "normal"})
                    species_parts.append({"text": str(count), "weight": "bold", "color": "TEAL_600"})
                    species_parts.append({"text": f" {species}{'s' if count > 1 else ''}", "weight": "normal"})
                
                breed_dist = self.get_breed_distribution()
                breed_count = len(breed_dist)
                if breed_count > 0:
                    species_parts.append({"text": f". {breed_count} unique breed", "weight": "normal"})
                    species_parts.append({"text": "s" if breed_count > 1 else "", "weight": "normal"})
                
                health_detail = {
                    "parts": [
                        {"text": "Population: ", "weight": "normal", "icon": "PETS"},
                    ] + species_parts
                }
            else:
                health_detail = {
                    "parts": [
                        {"text": f"All {healthy_count} animals in your care are healthy!", "weight": "normal"},
                    ]
                }
            
            if injured_count > 0:
                health_action = {
                    "icon": "LOCAL_HOSPITAL",
                    "text": f"Prioritize care for {injured_count} injured animal{'s' if injured_count > 1 else ''}.",
                    "color": "RED_600",
                    "bg_color": "RED_50",
                    "severity": "urgent",
                }
            elif recovering_count > 0:
                health_action = {
                    "icon": "HEALING",
                    "text": f"Monitor {recovering_count} recovering animal{'s' if recovering_count > 1 else ''}.",
                    "color": "ORANGE_600",
                    "bg_color": "ORANGE_50",
                    "severity": "warning",
                }
            else:
                health_action = {
                    "icon": "CHECK_CIRCLE",
                    "text": "No immediate health concerns.",
                    "color": "GREEN_600",
                    "bg_color": "GREEN_50",
                    "severity": "success",
                }
            
            insights["health_insight"] = {
                "headline": health_headline,
                "detail": health_detail,
                "action": health_action,
            }
        else:
            insights["health_insight"] = {
                "headline": {
                    "text": "No animals registered",
                    "icon": "INFO",
                    "color": "GREY_700",
                },
                "detail": {
                    "parts": [
                        {"text": "Add animals to start tracking their health.", "weight": "normal"},
                    ]
                },
                "action": {
                    "icon": "ADD_CIRCLE",
                    "text": "Add your first animal to get started.",
                    "color": "TEAL_600",
                    "bg_color": "TEAL_50",
                    "severity": "info",
                },
            }
        
        # BREED INSIGHT - Add breed-specific analysis
        insights["breed_insight"] = self.get_breed_insights()
        
        return insights

    def get_user_impact_insights(self, user_id: int) -> List[Dict[str, Any]]:
        """Generate personalized impact insights for the user dashboard.
        
        This method generates structured insight data that can be rendered
        by the frontend using Flet's rich text components (TextSpan).
        
        Args:
            user_id: The user's ID
            
        Returns:
            List of insight dictionaries, each containing:
            - icon: Icon name string (e.g., "PENDING_ACTIONS")
            - parts: List of text parts with styling info
            - color: Main color for the insight
            - bg_color: Background color for the insight badge
        """
        insights = []
        
        stats = self.get_user_activity_stats(user_id)
        rescue_status_dist = self.get_user_rescue_status_distribution(user_id)
        adoption_status_dist = self.get_user_adoption_status_distribution(user_id)
        
        rescued_successfully = rescue_status_dist.get("rescued", 0)
        pending_rescues = rescue_status_dist.get("pending", 0)
        ongoing_rescues = rescue_status_dist.get("on-going", 0)
        total_rescues = stats.get("rescue_reports_filed", 0)
        pending_adoptions = adoption_status_dist.get("pending", 0)
        total_adoptions = adoption_status_dist.get("approved", 0)
        
        active_missions = pending_rescues + ongoing_rescues
        if active_missions > 0:
            if pending_rescues > 0 and ongoing_rescues > 0:
                insights.append({
                    "icon": "PENDING_ACTIONS",
                    "parts": [
                        {"text": str(pending_rescues), "weight": "bold", "color": "ORANGE_700"},
                        {"text": f" rescue{'s' if pending_rescues > 1 else ''} pending, ", "weight": "normal", "color": "BLUE_700"},
                        {"text": str(ongoing_rescues), "weight": "bold", "color": "BLUE_700"},
                        {"text": " on-going", "weight": "normal", "color": "BLUE_700"},
                    ],
                    "color": "BLUE_700",
                    "bg_color": "BLUE_50",
                })
            elif pending_rescues > 0:
                insights.append({
                    "icon": "SCHEDULE",
                    "parts": [
                        {"text": str(pending_rescues), "weight": "bold", "color": "ORANGE_700"},
                        {"text": f" rescue report{'s' if pending_rescues > 1 else ''} awaiting response", "weight": "normal", "color": "ORANGE_700"},
                    ],
                    "color": "ORANGE_700",
                    "bg_color": "ORANGE_50",
                })
            else:
                insights.append({
                    "icon": "DIRECTIONS_RUN",
                    "parts": [
                        {"text": str(ongoing_rescues), "weight": "bold", "color": "BLUE_700"},
                        {"text": f" rescue mission{'s' if ongoing_rescues > 1 else ''} in progress", "weight": "normal", "color": "BLUE_700"},
                    ],
                    "color": "BLUE_700",
                    "bg_color": "BLUE_50",
                })
        
        if pending_adoptions > 0:
            insights.append({
                "icon": "HOURGLASS_BOTTOM",
                "parts": [
                    {"text": str(pending_adoptions), "weight": "bold", "color": "PURPLE_700"},
                    {"text": f" adoption application{'s' if pending_adoptions > 1 else ''} under review", "weight": "normal", "color": "PURPLE_700"},
                ],
                "color": "PURPLE_700",
                "bg_color": "PURPLE_50",
            })
        
        # Success message if they have successful rescues or adoptions
        if rescued_successfully > 0 and total_adoptions > 0:
            insights.append({
                "icon": "EMOJI_EVENTS",
                "parts": [
                    {"text": "Amazing! You've helped rescue ", "weight": "normal", "color": "AMBER_700"},
                    {"text": str(rescued_successfully), "weight": "bold", "color": "GREEN_700"},
                    {"text": " and adopted ", "weight": "normal", "color": "AMBER_700"},
                    {"text": str(total_adoptions), "weight": "bold", "color": "TEAL_700"},
                    {"text": f" animal{'s' if total_adoptions > 1 else ''}!", "weight": "normal", "color": "AMBER_700"},
                ],
                "color": "AMBER_700",
                "bg_color": "AMBER_50",
            })
        elif rescued_successfully > 0:
            insights.append({
                "icon": "VOLUNTEER_ACTIVISM",
                "parts": [
                    {"text": "Your reports led to ", "weight": "normal", "color": "GREEN_700"},
                    {"text": str(rescued_successfully), "weight": "bold", "color": "GREEN_700"},
                    {"text": f" successful rescue{'s' if rescued_successfully > 1 else ''}!", "weight": "normal", "color": "GREEN_700"},
                ],
                "color": "GREEN_700",
                "bg_color": "GREEN_50",
            })
        elif total_adoptions > 0:
            insights.append({
                "icon": "HOME",
                "parts": [
                    {"text": "You've given ", "weight": "normal", "color": "TEAL_700"},
                    {"text": str(total_adoptions), "weight": "bold", "color": "TEAL_700"},
                    {"text": f" animal{'s' if total_adoptions > 1 else ''} a forever home!", "weight": "normal", "color": "TEAL_700"},
                ],
                "color": "TEAL_700",
                "bg_color": "TEAL_50",
            })
        
        # Default encouraging message if no activity
        if not insights:
            if total_rescues == 0 and total_adoptions == 0:
                insights.append({
                    "icon": "PETS",
                    "parts": [
                        {"text": "Start your journey - ", "weight": "normal", "color": "TEAL_700"},
                        {"text": "report a rescue", "weight": "bold", "color": "ORANGE_600", "route": "/rescue_form"},
                        {"text": " or ", "weight": "normal", "color": "TEAL_700"},
                        {"text": "apply to adopt", "weight": "bold", "color": "TEAL_600", "route": "/available_adoption"},
                        {"text": "!", "weight": "normal", "color": "TEAL_700"},
                    ],
                    "color": "TEAL_700",
                    "bg_color": "TEAL_50",
                })
            else:
                insights.append({
                    "icon": "AUTO_AWESOME",
                    "parts": [
                        {"text": "Thank you for making a ", "weight": "normal", "color": "TEAL_700"},
                        {"text": "difference", "weight": "bold", "color": "TEAL_700"},
                        {"text": " in animals' lives!", "weight": "normal", "color": "TEAL_700"},
                    ],
                    "color": "TEAL_700",
                    "bg_color": "TEAL_50",
                })
        
        return insights[:2]  # Show max 2 insights

    def _normalize_breed(self, breed: Optional[str]) -> str:
        """Normalize breed value for analytics.
        
        Args:
            breed: Raw breed value from database
            
        Returns:
            Normalized breed string
        """
        if not breed or breed.strip() == "":
            return "Not Specified"
        
        breed_clean = breed.strip()
        
        # Normalize "Unknown" variants to "Not Specified"
        if breed_clean.lower() in ("unknown", "n/a", "not specified"):
            return "Not Specified"
        
        # Keep "Mixed Breed" as-is (capitalized)
        if breed_clean.lower() == "mixed breed":
            return "Mixed Breed"
        
        return breed_clean.capitalize()

    def get_breed_distribution(self) -> List[Tuple[str, int]]:
        """Get breed distribution for all animals regardless of status.
        
        Returns:
            List of (breed, count) tuples sorted by count descending.
            No limit - returns all breeds.
        """
        animals = self.animal_service.get_all_animals() or []
        
        breed_counts: Dict[str, int] = {}
        
        for animal in animals:
            breed = self._normalize_breed(animal.get("breed"))
            breed_counts[breed] = breed_counts.get(breed, 0) + 1
        
        sorted_breeds = sorted(breed_counts.items(), key=lambda x: x[1], reverse=True)
        return sorted_breeds

    def get_top_breeds_for_adoption(self, limit: int = 3) -> List[Tuple[str, int]]:
        """Get top breeds from ALL adoption requests (excluding cancelled).
        
        Args:
            limit: Maximum number of breeds to return (default 3)
            
        Returns:
            List of (breed, count) tuples sorted by count descending
        """
        requests = self.adoption_service.get_all_requests_for_analytics() or []
        
        breed_counts: Dict[str, int] = {}
        
        for req in requests:
            status = AdoptionStatus.get_base_status((req.get("status") or "").lower())
            if status != "cancelled":
                breed = self._normalize_breed(req.get("animal_breed"))
                breed_counts[breed] = breed_counts.get(breed, 0) + 1
        
        sorted_breeds = sorted(breed_counts.items(), key=lambda x: x[1], reverse=True)
        return sorted_breeds[:limit]

    def get_top_breeds_for_rescue(self, limit: int = 3) -> List[Tuple[str, int]]:
        """Get top breeds from ALL rescue missions (excluding cancelled).
        
        Args:
            limit: Maximum number of breeds to return (default 3)
            
        Returns:
            List of (breed, count) tuples sorted by count descending
        """
        missions = self.rescue_service.get_all_missions_for_analytics() or []
        
        breed_counts: Dict[str, int] = {}
        
        for mission in missions:
            status = RescueStatus.get_base_status((mission.get("status") or "").lower())
            if status != RescueStatus.CANCELLED:
                breed = self._normalize_breed(mission.get("breed"))
                breed_counts[breed] = breed_counts.get(breed, 0) + 1
        
        sorted_breeds = sorted(breed_counts.items(), key=lambda x: x[1], reverse=True)
        return sorted_breeds[:limit]

    def get_adoptable_breed_distribution(self, limit: int = 10) -> List[Tuple[str, int]]:
        """Get breed distribution for adoptable animals only (status='processing').
        
        Args:
            limit: Maximum number of breeds to return (default 10)
            
        Returns:
            List of (breed_with_species, count) tuples sorted by count descending.
            Format: "Breed (Species)" e.g., "Golden Retriever (Dog)"
        """
        animals = self.animal_service.get_adoptable_animals() or []
        
        breed_counts: Dict[str, int] = {}
        
        for animal in animals:
            breed = self._normalize_breed(animal.get("breed"))
            species = (animal.get("species") or "Unknown").strip().capitalize()
            breed_with_species = f"{breed} ({species})"
            breed_counts[breed_with_species] = breed_counts.get(breed_with_species, 0) + 1
        
        sorted_breeds = sorted(breed_counts.items(), key=lambda x: x[1], reverse=True)
        return sorted_breeds[:limit]

    def get_user_breed_preferences(self, user_id: int, limit: int = 5) -> List[Tuple[str, int]]:
        """Get breed preferences from user's adoption requests (all statuses except cancelled).
        
        Args:
            user_id: The user's ID
            limit: Maximum number of breeds to return (default 5)
            
        Returns:
            List of (breed_with_species, count) tuples sorted by count descending.
            Format: "Breed (Species)" e.g., "Golden Retriever (Dog)"
        """
        requests = self.adoption_service.get_all_requests_for_analytics() or []
        user_requests = [r for r in requests if r.get("user_id") == user_id]
        
        breed_counts: Dict[str, int] = {}
        
        for req in user_requests:
            status = AdoptionStatus.get_base_status((req.get("status") or "").lower())
            if status != "cancelled":
                breed = self._normalize_breed(req.get("animal_breed"))
                species = (req.get("animal_species") or "Unknown").strip().capitalize()
                breed_with_species = f"{breed} ({species})"
                breed_counts[breed_with_species] = breed_counts.get(breed_with_species, 0) + 1
        
        sorted_breeds = sorted(breed_counts.items(), key=lambda x: x[1], reverse=True)
        return sorted_breeds[:limit]

    def get_breed_trends(self, mode: str = "adoption") -> Tuple[List[str], List[Tuple[str, List[int]]]]:
        """Get 30-day trend data for top 3 breeds.
        
        Args:
            mode: "adoption" for adoption trends, "rescue" for rescue trends
            
        Returns:
            Tuple containing:
            - day_labels: List of date labels (MM-DD format)
            - breed_series: List of (breed_name, counts) tuples for top 3 breeds
        """
        now = datetime.utcnow()
        days: List[datetime] = []
        for i in range(29, -1, -1):
            d = now - timedelta(days=i)
            days.append(d)
        day_labels = [d.strftime("%m-%d") for d in days]
        day_dates = [d.strftime("%Y-%m-%d") for d in days]

        if mode == "adoption":
            top_breeds_data = self.get_top_breeds_for_adoption(limit=3)
        else:  # rescue
            top_breeds_data = self.get_top_breeds_for_rescue(limit=3)
        
        top_breeds = [breed for breed, _ in top_breeds_data]
        
        breed_counts: Dict[str, List[int]] = {breed: [0] * 30 for breed in top_breeds}
        
        if mode == "adoption":
            requests = self.adoption_service.get_all_requests_for_analytics() or []
            for req in requests:
                status = AdoptionStatus.get_base_status((req.get("status") or "").lower())
                if status != "cancelled":
                    dt = req.get("request_date")
                    if not dt:
                        continue
                    d = parse_datetime(dt)
                    if d is None:
                        continue
                    date_str = d.strftime("%Y-%m-%d")
                    if date_str in day_dates:
                        breed = self._normalize_breed(req.get("animal_breed"))
                        if breed in breed_counts:
                            idx = day_dates.index(date_str)
                            breed_counts[breed][idx] += 1
        else:  # rescue
            missions = self.rescue_service.get_all_missions_for_analytics() or []
            for mission in missions:
                status = RescueStatus.get_base_status((mission.get("status") or "").lower())
                if status != RescueStatus.CANCELLED:
                    dt = mission.get("mission_date")
                    if not dt:
                        continue
                    d = parse_datetime(dt)
                    if d is None:
                        continue
                    date_str = d.strftime("%Y-%m-%d")
                    if date_str in day_dates:
                        breed = self._normalize_breed(mission.get("breed"))
                        if breed in breed_counts:
                            idx = day_dates.index(date_str)
                            breed_counts[breed][idx] += 1
        
        # Convert to list of tuples
        breed_series = [(breed, counts) for breed, counts in breed_counts.items()]
        
        return day_labels, breed_series

    def invalidate_cache(self) -> None:
        """Invalidate all cached analytics data.
        
        Call this after data modifications that affect analytics
        (e.g., new animal, new adoption request, etc.)
        """
        self._cache.clear()


__all__ = ["AnalyticsService"]
