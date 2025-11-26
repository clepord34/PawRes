"""SQLite database wrapper with thread-safe operations."""
from __future__ import annotations

import sqlite3
from typing import Any, Dict, List, Optional, Sequence, Tuple
import app_config


class Database:
	"""Lightweight sqlite3 wrapper. Thread-safe: opens a fresh connection per operation."""

	def __init__(self, db_path: Optional[str] = None) -> None:
		self.db_path = db_path if db_path is not None else app_config.DB_PATH

	def _get_connection(self) -> sqlite3.Connection:
		"""Create a fresh connection for this operation."""
		conn = sqlite3.connect(self.db_path, detect_types=sqlite3.PARSE_DECLTYPES)
		conn.row_factory = sqlite3.Row
		conn.execute("PRAGMA foreign_keys = ON;")
		return conn

	def execute(self, sql: str, params: Optional[Sequence[Any]] = None, commit: bool = True) -> int:
		"""Execute a statement. Returns lastrowid."""
		conn = self._get_connection()
		try:
			cur = conn.cursor()
			params = tuple(params or ())
			cur.execute(sql, params)
			if commit:
				conn.commit()
			return cur.lastrowid
		finally:
			conn.close()

	def fetch_one(self, sql: str, params: Optional[Sequence[Any]] = None) -> Optional[Dict[str, Any]]:
		"""Fetch a single row as dict, or None."""
		conn = self._get_connection()
		try:
			cur = conn.cursor()
			cur.execute(sql, tuple(params or ()))
			row = cur.fetchone()
			if row is None:
				return None
			return dict(row)
		finally:
			conn.close()

	def fetch_all(self, sql: str, params: Optional[Sequence[Any]] = None) -> List[Dict[str, Any]]:
		"""Fetch all rows as list of dicts."""
		conn = self._get_connection()
		try:
			cur = conn.cursor()
			cur.execute(sql, tuple(params or ()))
			rows = cur.fetchall()
			return [dict(r) for r in rows]
		finally:
			conn.close()

	def create_tables(self) -> None:
		"""Create required tables if they don't exist."""
		users_sql = """
		CREATE TABLE IF NOT EXISTS users (
			id INTEGER PRIMARY KEY AUTOINCREMENT,
			name TEXT NOT NULL,
			email TEXT UNIQUE NOT NULL,
			phone TEXT,
			password_hash TEXT,
			password_salt TEXT,
			role TEXT DEFAULT 'user',
			created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
		);
		"""

		animals_sql = """
		CREATE TABLE IF NOT EXISTS animals (
			id INTEGER PRIMARY KEY AUTOINCREMENT,
			name TEXT,
			species TEXT,
			breed TEXT,
			age INTEGER,
			status TEXT,
			intake_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
			description TEXT,
			photo TEXT
		);
		"""

		rescue_sql = """
		CREATE TABLE IF NOT EXISTS rescue_missions (
			id INTEGER PRIMARY KEY AUTOINCREMENT,
			user_id INTEGER,
			animal_id INTEGER,
			location TEXT,
			latitude REAL,
			longitude REAL,
			mission_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
			notes TEXT,
			status TEXT,
			FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE SET NULL,
			FOREIGN KEY(animal_id) REFERENCES animals(id) ON DELETE SET NULL
		);
		"""

		adoption_sql = """
		CREATE TABLE IF NOT EXISTS adoption_requests (
			id INTEGER PRIMARY KEY AUTOINCREMENT,
			user_id INTEGER NOT NULL,
			animal_id INTEGER NOT NULL,
			contact TEXT,
			reason TEXT,
			status TEXT,
			request_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
			notes TEXT,
			FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
			FOREIGN KEY(animal_id) REFERENCES animals(id) ON DELETE CASCADE
		);
		"""

		# First, create all tables
		for stmt in (users_sql, animals_sql, rescue_sql, adoption_sql):
			# Use execute without params; commit after each to ensure persistence
			self.execute(stmt)

		# Then, handle any schema migrations for existing tables
		# This ensures we don't try to ALTER a table that doesn't exist yet
		conn = self._get_connection()
		try:
			cur = conn.cursor()
			# Check if photo column exists in animals table (for legacy databases)
			cur.execute("PRAGMA table_info(animals)")
			columns = [row[1] for row in cur.fetchall()]
			if 'photo' not in columns:
				cur.execute("ALTER TABLE animals ADD COLUMN photo TEXT")
				conn.commit()
		except Exception as e:
			# Log but don't fail - photo column is already in the CREATE TABLE statement
			print(f"[INFO] Schema migration note: {e}")
		finally:
			conn.close()
