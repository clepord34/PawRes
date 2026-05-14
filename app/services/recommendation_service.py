"""Rule-based recommendation service for personalized pet suggestions."""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import app_config
from storage.database import Database


class RecommendationService:
    """Recommend adoptable animals based on user preferences and history."""

    SPECIES_WEIGHT = 30
    BREED_WEIGHT = 25
    BREED_PARTIAL_WEIGHT = 15
    AGE_WEIGHT = 20
    NOT_APPLIED_WEIGHT = 15
    NEWNESS_WEIGHT = 10

    HISTORY_SPECIES_WEIGHT = 20
    POPULAR_WEIGHT = 10

    def __init__(self, db: Optional[Database | str] = None, *, ensure_tables: bool = True) -> None:
        if isinstance(db, Database):
            self.db = db
        else:
            self.db = Database(db if isinstance(db, str) else app_config.DB_PATH)

        if ensure_tables:
            self.db.create_tables()

    def save_preferences(self, user_id: int, prefs: Dict[str, Any]) -> int:
        """Insert or update user preferences and return the row id."""
        if not user_id:
            raise ValueError("user_id is required")

        species = self._normalize_list_value(prefs.get("preferred_species"))
        breeds = self._normalize_list_value(prefs.get("preferred_breeds"))
        age_min = self._normalize_int(prefs.get("preferred_age_min"))
        age_max = self._normalize_int(prefs.get("preferred_age_max"))
        living = self._normalize_text(prefs.get("living_situation"))
        activity = self._normalize_text(prefs.get("activity_level"))
        experience = self._normalize_text(prefs.get("experience_level"))
        now = datetime.now()

        existing = self.db.fetch_one(
            "SELECT id FROM user_preferences WHERE user_id = ?",
            (user_id,),
        )

        if existing:
            self.db.execute(
                """
                UPDATE user_preferences
                SET preferred_species = ?,
                    preferred_breeds = ?,
                    preferred_age_min = ?,
                    preferred_age_max = ?,
                    living_situation = ?,
                    activity_level = ?,
                    experience_level = ?,
                    updated_at = ?
                WHERE user_id = ?
                """,
                (
                    species,
                    breeds,
                    age_min,
                    age_max,
                    living,
                    activity,
                    experience,
                    now,
                    user_id,
                ),
            )
            return int(existing.get("id"))

        return self.db.execute(
            """
            INSERT INTO user_preferences (
                user_id,
                preferred_species,
                preferred_breeds,
                preferred_age_min,
                preferred_age_max,
                living_situation,
                activity_level,
                experience_level,
                created_at,
                updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                species,
                breeds,
                age_min,
                age_max,
                living,
                activity,
                experience,
                now,
                now,
            ),
        )

    def get_preferences(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Return preference row for a user, or None if not set."""
        if not user_id:
            return None
        return self.db.fetch_one(
            "SELECT * FROM user_preferences WHERE user_id = ?",
            (user_id,),
        )

    def get_recommendations(self, user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Return scored recommendations using stored preferences."""
        prefs = self.get_preferences(user_id)
        if not prefs:
            return self.get_recommendations_without_preferences(user_id, limit=limit)

        species_pref = self._parse_list(prefs.get("preferred_species"))
        breeds_pref = self._parse_list(prefs.get("preferred_breeds"))
        age_min = self._normalize_int(prefs.get("preferred_age_min"))
        age_max = self._normalize_int(prefs.get("preferred_age_max"))

        applied_ids = self._get_applied_animal_ids(user_id)
        animals = self._get_adoptable_animals()
        if not animals:
            return []

        results = []
        for animal in animals:
            animal_id = animal.get("id")
            if animal_id in applied_ids:
                continue

            score = 0
            reasons = []
            matched_preference = False

            species = (animal.get("species") or "").strip()
            if species_pref and species:
                if species.lower() in [s.lower() for s in species_pref]:
                    score += self.SPECIES_WEIGHT
                    reasons.append("Matches preferred species")
                    matched_preference = True

            breed = (animal.get("breed") or "").strip()
            if breeds_pref and breed:
                breed_lower = breed.lower()
                for pref in breeds_pref:
                    pref_lower = pref.lower()
                    if pref_lower == breed_lower:
                        score += self.BREED_WEIGHT
                        reasons.append("Matches preferred breed")
                        matched_preference = True
                        break
                    if pref_lower in breed_lower or breed_lower in pref_lower:
                        score += self.BREED_PARTIAL_WEIGHT
                        reasons.append("Similar breed preference")
                        matched_preference = True
                        break

            age = self._normalize_int(animal.get("age"))
            if age is not None and (age_min is not None or age_max is not None):
                min_ok = age >= age_min if age_min is not None else True
                max_ok = age <= age_max if age_max is not None else True
                if min_ok and max_ok:
                    score += self.AGE_WEIGHT
                    reasons.append("Fits your age range")
                    matched_preference = True

            has_filters = bool(species_pref or breeds_pref or age_min is not None or age_max is not None)
            if has_filters and not matched_preference:
                continue

            score += self.NOT_APPLIED_WEIGHT
            reasons.append("Not previously applied")

            if self._is_recent(animal):
                score += self.NEWNESS_WEIGHT
                reasons.append("Recently added")

            if score <= 0:
                continue

            results.append({
                "animal": animal,
                "score": score,
                "match_reasons": reasons,
            })

        results.sort(key=lambda r: (r["score"], self._get_recency_score(r["animal"])), reverse=True)
        return results[:max(0, limit)]

    def get_recommendations_without_preferences(self, user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Fallback recommendations using adoption history and popularity."""
        applied_ids = self._get_applied_animal_ids(user_id)
        preferred_species = self._get_preferred_species_from_history(user_id)
        animals = self._get_adoptable_animals_with_popularity()
        if not animals:
            return []

        results = []
        for animal in animals:
            animal_id = animal.get("id")
            if animal_id in applied_ids:
                continue

            score = 0
            reasons = []

            species = (animal.get("species") or "").strip()
            if preferred_species and species and species.lower() == preferred_species.lower():
                score += self.HISTORY_SPECIES_WEIGHT
                reasons.append("Based on your past adoptions")

            request_count = self._normalize_int(animal.get("request_count")) or 0
            if request_count >= 3:
                score += self.POPULAR_WEIGHT
                reasons.append("Popular with adopters")
            elif request_count > 0:
                score += self.POPULAR_WEIGHT // 2
                reasons.append("Trending with adopters")

            if self._is_recent(animal):
                score += self.NEWNESS_WEIGHT
                reasons.append("Recently added")

            score += self.NOT_APPLIED_WEIGHT
            reasons.append("Not previously applied")

            if not reasons:
                reasons.append("Adoptable now")

            results.append({
                "animal": animal,
                "score": score,
                "match_reasons": reasons,
            })

        results.sort(key=lambda r: (r["score"], self._get_recency_score(r["animal"])), reverse=True)
        return results[:max(0, limit)]

    def _get_adoptable_animals(self) -> List[Dict[str, Any]]:
        adoptable_states = [s.lower() for s in app_config.ADOPTABLE_STATUSES]
        placeholders = ",".join(["?" for _ in adoptable_states])
        sql = f"SELECT * FROM animals WHERE LOWER(status) IN ({placeholders}) ORDER BY intake_date DESC"
        return self.db.fetch_all(sql, adoptable_states)

    def _get_adoptable_animals_with_popularity(self) -> List[Dict[str, Any]]:
        adoptable_states = [s.lower() for s in app_config.ADOPTABLE_STATUSES]
        placeholders = ",".join(["?" for _ in adoptable_states])
        sql = f"""
            SELECT a.*, COUNT(ar.id) as request_count
            FROM animals a
            LEFT JOIN adoption_requests ar ON ar.animal_id = a.id
            WHERE LOWER(a.status) IN ({placeholders})
            GROUP BY a.id
            ORDER BY request_count DESC, a.intake_date DESC
        """
        return self.db.fetch_all(sql, adoptable_states)

    def _get_applied_animal_ids(self, user_id: int) -> set[int]:
        if not user_id:
            return set()
        rows = self.db.fetch_all(
            "SELECT DISTINCT animal_id FROM adoption_requests WHERE user_id = ? AND animal_id IS NOT NULL",
            (user_id,),
        )
        return {int(r["animal_id"]) for r in rows if r.get("animal_id") is not None}

    def _get_preferred_species_from_history(self, user_id: int) -> Optional[str]:
        if not user_id:
            return None
        rows = self.db.fetch_all(
            """
            SELECT COALESCE(a.species, ar.animal_species) as species
            FROM adoption_requests ar
            LEFT JOIN animals a ON ar.animal_id = a.id
            WHERE ar.user_id = ?
            """,
            (user_id,),
        )
        counts: Dict[str, int] = {}
        for row in rows:
            species = (row.get("species") or "").strip()
            if not species:
                continue
            key = species.lower()
            counts[key] = counts.get(key, 0) + 1
        if not counts:
            return None
        best = max(counts.items(), key=lambda item: item[1])[0]
        return best

    def _is_recent(self, animal: Dict[str, Any]) -> bool:
        dt = self._parse_datetime(animal.get("intake_date"))
        if dt is None:
            dt = self._parse_datetime(animal.get("updated_at"))
        if dt is None:
            return False
        return datetime.now() - dt <= timedelta(days=30)

    def _get_recency_score(self, animal: Dict[str, Any]) -> float:
        dt = self._parse_datetime(animal.get("intake_date"))
        if dt is None:
            dt = self._parse_datetime(animal.get("updated_at"))
        if dt is None:
            return 0.0
        return dt.timestamp()

    def _parse_datetime(self, value: Any) -> Optional[datetime]:
        if not value:
            return None
        if isinstance(value, datetime):
            return value
        text = str(value).strip()
        if not text:
            return None
        try:
            return datetime.fromisoformat(text.replace("Z", "+00:00"))
        except ValueError:
            pass
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
            try:
                return datetime.strptime(text, fmt)
            except ValueError:
                continue
        return None

    def _normalize_list_value(self, value: Any) -> Optional[str]:
        if value is None:
            return None
        if isinstance(value, str):
            trimmed = value.strip()
            return trimmed if trimmed else None
        if isinstance(value, (list, tuple, set)):
            items = [str(v).strip() for v in value if str(v).strip()]
            return ", ".join(items) if items else None
        return str(value).strip() or None

    def _normalize_text(self, value: Any) -> Optional[str]:
        if value is None:
            return None
        text = str(value).strip()
        return text if text else None

    def _normalize_int(self, value: Any) -> Optional[int]:
        if value is None or value == "":
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    def _parse_list(self, value: Any) -> List[str]:
        if not value:
            return []
        if isinstance(value, (list, tuple, set)):
            return [str(v).strip() for v in value if str(v).strip()]
        if isinstance(value, str):
            return [part.strip() for part in value.split(",") if part.strip()]
        return [str(value).strip()]


__all__ = ["RecommendationService"]
