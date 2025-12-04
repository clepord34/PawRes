"""Unit tests for storage layer (Database, Cache, FileStore)."""
from __future__ import annotations

import os
import base64
import tempfile
import time
from pathlib import Path

import pytest

from storage.database import Database
from storage.cache import Cache, LRUCache, QueryCache, CacheEntry
from storage.file_store import FileStore, FileStoreError, FileSizeError, FileTypeError


class TestDatabase:
    """Tests for Database wrapper."""

    def test_create_database(self, temp_db: Database):
        """Test database creation and table setup."""
        # Tables should be created by fixture
        # Verify by checking if we can query users table
        result = temp_db.fetch_all("SELECT name FROM sqlite_master WHERE type='table'")
        table_names = [r["name"] for r in result]
        
        assert "users" in table_names
        assert "animals" in table_names
        assert "rescue_missions" in table_names
        assert "adoption_requests" in table_names

    def test_execute_insert(self, temp_db: Database):
        """Test inserting data and getting lastrowid."""
        last_id = temp_db.execute(
            "INSERT INTO users (name, email, role) VALUES (?, ?, ?)",
            ("Test", "test@test.com", "user")
        )
        assert last_id > 0

    def test_fetch_one_found(self, temp_db: Database):
        """Test fetching a single row that exists."""
        temp_db.execute(
            "INSERT INTO users (name, email, role) VALUES (?, ?, ?)",
            ("Fetch Test", "fetch@test.com", "user")
        )
        
        row = temp_db.fetch_one("SELECT * FROM users WHERE email = ?", ("fetch@test.com",))
        assert row is not None
        assert row["name"] == "Fetch Test"
        assert row["email"] == "fetch@test.com"

    def test_fetch_one_not_found(self, temp_db: Database):
        """Test fetching a row that doesn't exist returns None."""
        row = temp_db.fetch_one("SELECT * FROM users WHERE email = ?", ("nonexistent@test.com",))
        assert row is None

    def test_fetch_all_empty(self, temp_db: Database):
        """Test fetching all rows when table is empty."""
        rows = temp_db.fetch_all("SELECT * FROM users")
        assert rows == []

    def test_fetch_all_multiple(self, temp_db: Database):
        """Test fetching multiple rows."""
        temp_db.execute("INSERT INTO users (name, email, role) VALUES (?, ?, ?)", ("User1", "u1@test.com", "user"))
        temp_db.execute("INSERT INTO users (name, email, role) VALUES (?, ?, ?)", ("User2", "u2@test.com", "user"))
        temp_db.execute("INSERT INTO users (name, email, role) VALUES (?, ?, ?)", ("User3", "u3@test.com", "admin"))
        
        rows = temp_db.fetch_all("SELECT * FROM users ORDER BY name")
        assert len(rows) == 3
        assert rows[0]["name"] == "User1"
        assert rows[2]["name"] == "User3"

    def test_database_thread_safety(self, temp_db: Database):
        """Test that database operations work across multiple calls (fresh connections)."""
        # Each operation should use a fresh connection
        temp_db.execute("INSERT INTO animals (name, species, status) VALUES (?, ?, ?)", ("A1", "Dog", "healthy"))
        
        # Fetch in separate operation
        animal = temp_db.fetch_one("SELECT * FROM animals WHERE name = ?", ("A1",))
        assert animal is not None
        assert animal["species"] == "Dog"


class TestCache:
    """Tests for Cache with TTL."""

    def test_cache_set_and_get(self):
        """Test basic set and get operations."""
        cache = Cache(ttl_seconds=60)
        cache.set("key1", "value1")
        
        assert cache.get("key1") == "value1"

    def test_cache_get_missing_key(self):
        """Test getting a key that doesn't exist."""
        cache = Cache(ttl_seconds=60)
        
        assert cache.get("missing") is None
        assert cache.get("missing", "default") == "default"

    def test_cache_expiration(self):
        """Test that entries expire after TTL."""
        cache = Cache(ttl_seconds=0.1)  # 100ms TTL
        cache.set("key", "value")
        
        assert cache.get("key") == "value"
        
        time.sleep(0.15)  # Wait for expiration
        assert cache.get("key") is None

    def test_cache_custom_ttl_per_entry(self):
        """Test that per-entry TTL overrides default."""
        cache = Cache(ttl_seconds=60)
        cache.set("short", "value", ttl_seconds=0.1)
        cache.set("long", "value", ttl_seconds=60)
        
        time.sleep(0.15)
        
        assert cache.get("short") is None  # Expired
        assert cache.get("long") == "value"  # Still valid

    def test_cache_delete(self):
        """Test deleting a cache entry."""
        cache = Cache(ttl_seconds=60)
        cache.set("delete_me", "value")
        
        assert cache.delete("delete_me") is True
        assert cache.get("delete_me") is None
        assert cache.delete("delete_me") is False  # Already deleted

    def test_cache_clear(self):
        """Test clearing all cache entries."""
        cache = Cache(ttl_seconds=60)
        cache.set("key1", "v1")
        cache.set("key2", "v2")
        cache.set("key3", "v3")
        
        count = cache.clear()
        assert count == 3
        assert cache.size() == 0

    def test_cache_has(self):
        """Test checking if key exists."""
        cache = Cache(ttl_seconds=60)
        cache.set("exists", "value")
        
        assert cache.has("exists") is True
        assert cache.has("not_exists") is False

    def test_cache_get_or_set(self):
        """Test get_or_set functionality."""
        cache = Cache(ttl_seconds=60)
        call_count = [0]
        
        def factory():
            call_count[0] += 1
            return "computed_value"
        
        # First call should compute
        result1 = cache.get_or_set("key", factory)
        assert result1 == "computed_value"
        assert call_count[0] == 1
        
        # Second call should use cache
        result2 = cache.get_or_set("key", factory)
        assert result2 == "computed_value"
        assert call_count[0] == 1  # Factory not called again

    def test_cache_stats(self):
        """Test cache statistics."""
        cache = Cache(ttl_seconds=60)
        cache.set("key", "value")
        
        cache.get("key")  # Hit
        cache.get("key")  # Hit
        cache.get("missing")  # Miss
        
        stats = cache.stats()
        assert stats["hits"] == 2
        assert stats["misses"] == 1
        assert stats["hit_rate_percent"] == pytest.approx(66.67, rel=0.1)


class TestLRUCache:
    """Tests for LRU Cache."""

    def test_lru_eviction(self):
        """Test LRU eviction when max size is exceeded."""
        cache = LRUCache(max_size=3)
        cache.set("a", 1)
        cache.set("b", 2)
        cache.set("c", 3)
        
        # Access 'a' to make it recently used
        cache.get("a")
        
        # Add new item - 'b' should be evicted (least recently used)
        cache.set("d", 4)
        
        assert cache.get("b") is None  # Evicted
        assert cache.get("a") == 1  # Still exists
        assert cache.get("c") == 3  # Still exists
        assert cache.get("d") == 4  # Newly added

    def test_lru_update_moves_to_end(self):
        """Test that updating a key moves it to end (most recent)."""
        cache = LRUCache(max_size=2)
        cache.set("a", 1)
        cache.set("b", 2)
        
        # Update 'a' - makes it most recent
        cache.set("a", 10)
        
        # Add new item - 'b' should be evicted
        cache.set("c", 3)
        
        assert cache.get("a") == 10
        assert cache.get("b") is None
        assert cache.get("c") == 3


class TestQueryCache:
    """Tests for QueryCache specialized for SQL queries."""

    def test_query_cache_basic(self):
        """Test basic query caching."""
        cache = QueryCache(ttl_seconds=60)
        
        cache.set("SELECT * FROM users", None, [{"id": 1, "name": "Test"}])
        
        result = cache.get("SELECT * FROM users", None)
        assert result == [{"id": 1, "name": "Test"}]

    def test_query_cache_with_params(self):
        """Test caching queries with different parameters."""
        cache = QueryCache(ttl_seconds=60)
        
        cache.set("SELECT * FROM users WHERE id = ?", (1,), {"id": 1})
        cache.set("SELECT * FROM users WHERE id = ?", (2,), {"id": 2})
        
        assert cache.get("SELECT * FROM users WHERE id = ?", (1,))["id"] == 1
        assert cache.get("SELECT * FROM users WHERE id = ?", (2,))["id"] == 2
        assert cache.get("SELECT * FROM users WHERE id = ?", (3,)) is None

    def test_query_cache_get_or_fetch(self):
        """Test get_or_fetch functionality."""
        cache = QueryCache(ttl_seconds=60)
        fetch_count = [0]
        
        def fetcher():
            fetch_count[0] += 1
            return [{"id": 1}]
        
        # First call fetches
        result1 = cache.get_or_fetch("SELECT * FROM test", None, fetcher)
        assert result1 == [{"id": 1}]
        assert fetch_count[0] == 1
        
        # Second call uses cache
        result2 = cache.get_or_fetch("SELECT * FROM test", None, fetcher)
        assert result2 == [{"id": 1}]
        assert fetch_count[0] == 1


class TestFileStore:
    """Tests for FileStore."""

    @pytest.fixture
    def file_store(self) -> FileStore:
        """Create a FileStore with temporary directory."""
        temp_dir = tempfile.mkdtemp()
        return FileStore(uploads_dir=Path(temp_dir))

    def test_save_and_read_base64(self, file_store: FileStore):
        """Test saving and reading base64 data."""
        # Create a simple 1x1 PNG (valid image)
        png_data = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        )
        base64_data = base64.b64encode(png_data).decode()
        
        filename = file_store.save_base64_file(base64_data, "test.png", validate=False)
        
        assert filename is not None
        assert file_store.file_exists(filename)
        
        # Read it back
        read_data = file_store.read_file_as_base64(filename)
        assert read_data == base64_data

    def test_save_with_validation(self, file_store: FileStore):
        """Test that invalid file types are rejected."""
        # Invalid extension
        with pytest.raises(FileTypeError):
            file_store.save_base64_file("dGVzdA==", "test.txt", validate=True)

    def test_delete_file(self, file_store: FileStore):
        """Test deleting a file."""
        png_data = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        )
        base64_data = base64.b64encode(png_data).decode()
        
        filename = file_store.save_base64_file(base64_data, "delete_me.png", validate=False)
        
        assert file_store.file_exists(filename)
        assert file_store.delete_file(filename) is True
        assert file_store.file_exists(filename) is False

    def test_delete_nonexistent_file(self, file_store: FileStore):
        """Test deleting a file that doesn't exist."""
        assert file_store.delete_file("nonexistent.png") is False

    def test_get_file_info(self, file_store: FileStore):
        """Test getting file metadata."""
        png_data = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        )
        base64_data = base64.b64encode(png_data).decode()
        
        filename = file_store.save_base64_file(base64_data, "info.png", validate=False)
        
        info = file_store.get_file_info(filename)
        assert info["filename"] == filename
        assert info["extension"] == ".png"
        assert info["size_bytes"] > 0

    def test_list_files(self, file_store: FileStore):
        """Test listing files in the store."""
        png_data = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        )
        base64_data = base64.b64encode(png_data).decode()
        
        file_store.save_base64_file(base64_data, "file1.png", validate=False)
        file_store.save_base64_file(base64_data, "file2.png", validate=False)
        file_store.save_base64_file(base64_data, "file3.jpg", validate=False)
        
        all_files = file_store.list_files()
        assert len(all_files) == 3
        
        png_files = file_store.list_files(extension=".png")
        assert len(png_files) == 2

    def test_unique_filenames(self, file_store: FileStore):
        """Test that saved files get unique names."""
        png_data = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        )
        base64_data = base64.b64encode(png_data).decode()
        
        filename1 = file_store.save_base64_file(base64_data, "same.png", validate=False)
        filename2 = file_store.save_base64_file(base64_data, "same.png", validate=False)
        
        # Filenames should be different (unique timestamp + UUID)
        assert filename1 != filename2


class TestCacheEntry:
    """Tests for CacheEntry class."""

    def test_cache_entry_is_expired(self):
        """Test expiration detection."""
        entry = CacheEntry("value", ttl_seconds=0.1)
        
        assert entry.is_expired() is False
        time.sleep(0.15)
        assert entry.is_expired() is True

    def test_cache_entry_time_remaining(self):
        """Test time remaining calculation."""
        entry = CacheEntry("value", ttl_seconds=1.0)
        
        remaining = entry.time_remaining()
        assert 0.9 < remaining <= 1.0  # Should be close to 1 second

    def test_cache_entry_never_expires(self):
        """Test entry with zero TTL never expires."""
        entry = CacheEntry("value", ttl_seconds=0)
        
        assert entry.is_expired() is False
        # time_remaining for infinite is float('inf') - remaining
        assert entry.time_remaining() > 1000000  # Effectively infinite
