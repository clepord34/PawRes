"""Animal service for CRUD operations on animals."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from storage.database import Database
from storage.file_store import get_file_store, FileStoreError
from services.photo_service import get_photo_service
import app_config


class AnimalService:
    def __init__(self, db: Optional[Database | str] = None, *, ensure_tables: bool = True) -> None:
        """Create service with a Database instance or path.

        Args:
            db: Database instance or path to sqlite file. If None, defaults
                to DB_PATH from app_config.
            ensure_tables: if True the service will call `create_tables()` on
                the Database to ensure the `animals` table exists.
        """
        if isinstance(db, Database):
            self.db = db
        else:
            self.db = Database(db if isinstance(db, str) else app_config.DB_PATH)

        if ensure_tables:
            self.db.create_tables()
        
        self.file_store = get_file_store()
        self.photo_service = get_photo_service()

    def add_animal(
        self,
        name: str,
        type: str,
        age: Optional[int] = None,
        health_status: str = "unknown",
        breed: Optional[str] = None,
        description: Optional[str] = None,
        photo: Optional[str] = None,
    ) -> int:
        """Insert a new animal and return its id.

        Note: `type` maps to the `species` column in the DB; `health_status`
        maps to `status`. `photo` should be base64-encoded image data.
        """
        sql = (
            "INSERT INTO animals (name, species, breed, age, status, description, photo) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)"
        )
        last_id = self.db.execute(sql, (name, type, breed, age, health_status, description, photo))
        return last_id

    def get_all_animals(self) -> List[Dict[str, Any]]:
        """Return all animals as list of dicts (DB column names).

        The returned dicts use the DB column names (e.g., `species`). If you
        prefer model objects, convert using the `Animal` dataclass.
        """
        rows = self.db.fetch_all("SELECT * FROM animals ORDER BY id")
        return rows

    def get_animal_by_id(self, animal_id: int) -> Optional[Dict[str, Any]]:
        """Return a single animal by id, or None if not found.

        The returned dict uses the DB column names (e.g., `species`).
        """
        return self.db.fetch_one("SELECT * FROM animals WHERE id = ?", (animal_id,))

    def update_animal(self, animal_id: int, **fields: Any) -> bool:
        """Update allowed fields for an animal. Returns True if updated.

        Allowed fields: `name`, `type` (mapped to `species`), `breed`,
        `age`, `health_status` (mapped to `status`), `description`, `photo`.
        """
        if not fields:
            return False

        # map input field names to DB column names
        mapping = {
            "type": "species",
            "health_status": "status",
            "name": "name",
            "breed": "breed",
            "age": "age",
            "description": "description",
            "photo": "photo",
        }

        set_clauses = []
        params: List[Any] = []
        for key, value in fields.items():
            col = mapping.get(key)
            if not col:
                # ignore unknown fields
                continue
            set_clauses.append(f"{col} = ?")
            params.append(value)

        if not set_clauses:
            return False

        params.append(animal_id)
        sql = f"UPDATE animals SET {', '.join(set_clauses)} WHERE id = ?"
        self.db.execute(sql, params)
        return True

    def delete_animal(self, animal_id: int) -> bool:
        """Delete an animal by id, including its photo file. 
        
        Preserves adoption request records for data analytics:
        - Stores the animal name and species in dedicated columns before deletion
        - The database ON DELETE SET NULL will set animal_id to NULL automatically
        - Keeps original status unchanged
        
        Note: Rescue missions are user-reported animals, NOT linked to admin animals,
        so they are not affected by this operation.
        
        Returns True if deleted.
        """
        # Get the animal first to check for photo, name, and species
        existing = self.db.fetch_one("SELECT id, photo, name, species FROM animals WHERE id = ?", (animal_id,))
        if not existing:
            return False
        
        animal_name = existing.get('name', 'Unknown')
        animal_species = existing.get('species', 'Unknown')
        photo_data = existing.get('photo')
        
        # Store the animal name and species in adoption_requests BEFORE deleting the animal
        # This preserves the info for display purposes after the animal is deleted
        # The ON DELETE SET NULL in the foreign key will handle setting animal_id to NULL
        self.db.execute(
            "UPDATE adoption_requests SET animal_name = ?, animal_species = ? WHERE animal_id = ?",
            (animal_name, animal_species, animal_id)
        )
        
        # Count how many records we're preserving
        preserved = self.db.fetch_one(
            "SELECT COUNT(*) as count FROM adoption_requests WHERE animal_id = ?",
            (animal_id,)
        )
        preserved_count = preserved.get('count', 0) if preserved else 0
        if preserved_count > 0:
            print(f"[INFO] Stored animal info ({animal_name}, {animal_species}) in {preserved_count} adoption record(s)")
        
        # Delete the animal - ON DELETE SET NULL will automatically set animal_id to NULL
        # in the adoption_requests table
        self.db.execute("DELETE FROM animals WHERE id = ?", (animal_id,))
        print(f"[INFO] Deleted animal {animal_id}: {animal_name}")
        
        # Delete the photo file AFTER successful database deletion
        if photo_data and not self.photo_service.is_base64(photo_data):
            try:
                self.file_store.delete_file(photo_data)
                print(f"[INFO] Deleted photo file: {photo_data}")
            except FileStoreError as e:
                print(f"[WARN] Could not delete photo file: {e}")
        
        return True

    def get_adoptable_animals(self) -> List[Dict[str, Any]]:
        """Return animals considered adoptable.

        The service treats animals with `status` in this list as adoptable:
        `('available','adoptable','healthy','ready')`.
        """
        adoptable_states = ("available", "adoptable", "healthy", "ready")
        placeholders = ",".join(["?" for _ in adoptable_states])
        sql = f"SELECT * FROM animals WHERE status IN ({placeholders}) ORDER BY id"
        rows = self.db.fetch_all(sql, adoptable_states)
        return rows

    def update_animal_photo(self, animal_id: int, new_photo: str) -> bool:
        """Update an animal's photo, deleting the old photo file if it exists.
        
        Args:
            animal_id: The ID of the animal to update
            new_photo: New photo filename (from FileStore)
            
        Returns:
            True if the photo was updated successfully
        """
        if not new_photo:
            return False
        
        # Get existing animal to check for old photo
        existing = self.db.fetch_one("SELECT id, photo FROM animals WHERE id = ?", (animal_id,))
        if not existing:
            return False
        
        # Delete old photo file if it exists and is a filename (not base64)
        old_photo = existing.get('photo')
        if old_photo and not self.photo_service.is_base64(old_photo):
            try:
                self.file_store.delete_file(old_photo)
                print(f"[INFO] Deleted old photo file: {old_photo}")
            except FileStoreError as e:
                print(f"[WARN] Could not delete old photo file: {e}")
        
        sql = "UPDATE animals SET photo = ? WHERE id = ?"
        self.db.execute(sql, (new_photo, animal_id))
        return True


__all__ = ["AnimalService"]
