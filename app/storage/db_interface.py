"""Database interface protocol for the Paw Rescue application."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Protocol, Sequence, runtime_checkable


@runtime_checkable
class DatabaseInterface(Protocol):
    """Protocol defining the database interface contract."""
    
    @property
    def db_path(self) -> str:
        """Return the database file path."""
        ...
    
    def execute(
        self, 
        sql: str, 
        params: Optional[Sequence[Any]] = None, 
        commit: bool = True
    ) -> int:
        """Execute a SQL statement.
        
        Args:
            sql: SQL statement to execute
            params: Optional sequence of parameters for the statement
            commit: Whether to commit the transaction (default True)
        
        Returns:
            The lastrowid of the executed statement (0 if none)
        
        Example:
            user_id = db.execute(
                "INSERT INTO users (name, email) VALUES (?, ?)",
                ("Alice", "alice@example.com")
            )
        """
        ...
    
    def fetch_one(
        self, 
        sql: str, 
        params: Optional[Sequence[Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """Fetch a single row as a dictionary.
        
        Args:
            sql: SELECT statement to execute
            params: Optional sequence of parameters
        
        Returns:
            Dictionary with column names as keys, or None if no row found
        
        Example:
            user = db.fetch_one(
                "SELECT * FROM users WHERE email = ?",
                ("alice@example.com",)
            )
            if user:
                print(user["name"])  # "Alice"
        """
        ...
    
    def fetch_all(
        self, 
        sql: str, 
        params: Optional[Sequence[Any]] = None
    ) -> List[Dict[str, Any]]:
        """Fetch all matching rows as a list of dictionaries.
        
        Args:
            sql: SELECT statement to execute
            params: Optional sequence of parameters
        
        Returns:
            List of dictionaries, empty list if no rows found
        
        Example:
            animals = db.fetch_all(
                "SELECT * FROM animals WHERE status = ?",
                ("available",)
            )
            for animal in animals:
                print(animal["name"])
        """
        ...
    
    def create_tables(self) -> None:
        """Create all required database tables.
        
        This method should be idempotent - safe to call multiple times.
        It should use CREATE TABLE IF NOT EXISTS or equivalent.
        """
        ...


class MockDatabase:
    """Mock database implementation for testing.
    
    Provides in-memory storage that implements DatabaseInterface.
    Useful for unit tests that don't need a real database.
    
    Example:
        from storage.db_interface import MockDatabase
        
        def test_my_service():
            mock_db = MockDatabase()
            mock_db.set_fetch_one_result({"id": 1, "name": "Test"})
            
            service = MyService(mock_db)
            result = service.get_something()
            
            assert result["name"] == "Test"
    """
    
    def __init__(self, db_path: str = ":memory:"):
        self._db_path = db_path
        self._fetch_one_result: Optional[Dict[str, Any]] = None
        self._fetch_all_result: List[Dict[str, Any]] = []
        self._last_execute_sql: Optional[str] = None
        self._last_execute_params: Optional[Sequence[Any]] = None
        self._execute_return_value: int = 1
        self._tables_created: bool = False
    
    @property
    def db_path(self) -> str:
        return self._db_path
    
    def execute(
        self, 
        sql: str, 
        params: Optional[Sequence[Any]] = None, 
        commit: bool = True
    ) -> int:
        self._last_execute_sql = sql
        self._last_execute_params = params
        return self._execute_return_value
    
    def fetch_one(
        self, 
        sql: str, 
        params: Optional[Sequence[Any]] = None
    ) -> Optional[Dict[str, Any]]:
        self._last_execute_sql = sql
        self._last_execute_params = params
        return self._fetch_one_result
    
    def fetch_all(
        self, 
        sql: str, 
        params: Optional[Sequence[Any]] = None
    ) -> List[Dict[str, Any]]:
        self._last_execute_sql = sql
        self._last_execute_params = params
        return self._fetch_all_result
    
    def create_tables(self) -> None:
        self._tables_created = True
    
    # Test helper methods
    def set_fetch_one_result(self, result: Optional[Dict[str, Any]]) -> None:
        """Set the result to return from fetch_one."""
        self._fetch_one_result = result
    
    def set_fetch_all_result(self, result: List[Dict[str, Any]]) -> None:
        """Set the result to return from fetch_all."""
        self._fetch_all_result = result
    
    def set_execute_return_value(self, value: int) -> None:
        """Set the return value for execute (lastrowid)."""
        self._execute_return_value = value
    
    def get_last_sql(self) -> Optional[str]:
        """Get the last SQL statement executed."""
        return self._last_execute_sql
    
    def get_last_params(self) -> Optional[Sequence[Any]]:
        """Get the last parameters passed to execute/fetch."""
        return self._last_execute_params
    
    def was_tables_created(self) -> bool:
        """Check if create_tables was called."""
        return self._tables_created


# Type alias for dependency injection
# Services should use this type hint for database parameters
DB = DatabaseInterface
