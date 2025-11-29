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
			oauth_provider TEXT,
			profile_picture TEXT,
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
			animal_id INTEGER,
			contact TEXT,
			reason TEXT,
			status TEXT,
			request_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
			notes TEXT,
			animal_name TEXT,
			animal_species TEXT,
			FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
			FOREIGN KEY(animal_id) REFERENCES animals(id) ON DELETE SET NULL
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
			
			# Check if oauth columns exist in users table (for legacy databases)
			cur.execute("PRAGMA table_info(users)")
			user_columns = [row[1] for row in cur.fetchall()]
			if 'oauth_provider' not in user_columns:
				cur.execute("ALTER TABLE users ADD COLUMN oauth_provider TEXT")
				conn.commit()
			if 'profile_picture' not in user_columns:
				cur.execute("ALTER TABLE users ADD COLUMN profile_picture TEXT")
				conn.commit()
			
			# Check if photo column exists in animals table (for legacy databases)
			cur.execute("PRAGMA table_info(animals)")
			columns = [row[1] for row in cur.fetchall()]
			if 'photo' not in columns:
				cur.execute("ALTER TABLE animals ADD COLUMN photo TEXT")
				conn.commit()
			
			# Check if adoption_requests needs migration (animal_id should allow NULL)
			cur.execute("PRAGMA table_info(adoption_requests)")
			adoption_columns = {row[1]: row for row in cur.fetchall()}
			
			# Check if animal_id column has NOT NULL constraint (notnull is index 3)
			animal_id_info = adoption_columns.get('animal_id')
			needs_migration = False
			
			if animal_id_info:
				# notnull is at index 3: 0=cid, 1=name, 2=type, 3=notnull, 4=dflt_value, 5=pk
				is_not_null = animal_id_info[3] == 1
				if is_not_null:
					needs_migration = True
					print("[INFO] Migrating adoption_requests table to allow NULL animal_id...")
			
			# Also check if animal_name column exists
			if 'animal_name' not in adoption_columns:
				needs_migration = True
			
			# Also check if animal_species column exists
			if 'animal_species' not in adoption_columns:
				needs_migration = True
			
			if needs_migration:
				# Need to recreate table with new schema (SQLite doesn't support ALTER COLUMN)
				cur.execute("PRAGMA foreign_keys = OFF")
				
				# Create new table with correct schema
				cur.execute("""
					CREATE TABLE IF NOT EXISTS adoption_requests_new (
						id INTEGER PRIMARY KEY AUTOINCREMENT,
						user_id INTEGER NOT NULL,
						animal_id INTEGER,
						contact TEXT,
						reason TEXT,
						status TEXT,
						request_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
						notes TEXT,
						animal_name TEXT,
						animal_species TEXT,
						FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
						FOREIGN KEY(animal_id) REFERENCES animals(id) ON DELETE SET NULL
					)
				""")
				
				# Copy data from old table (handle missing columns gracefully)
				if 'animal_species' in adoption_columns:
					cur.execute("""
						INSERT INTO adoption_requests_new (id, user_id, animal_id, contact, reason, status, request_date, notes, animal_name, animal_species)
						SELECT id, user_id, animal_id, contact, reason, status, request_date, notes, animal_name, animal_species
						FROM adoption_requests
					""")
				elif 'animal_name' in adoption_columns:
					cur.execute("""
						INSERT INTO adoption_requests_new (id, user_id, animal_id, contact, reason, status, request_date, notes, animal_name)
						SELECT id, user_id, animal_id, contact, reason, status, request_date, notes, animal_name
						FROM adoption_requests
					""")
				else:
					cur.execute("""
						INSERT INTO adoption_requests_new (id, user_id, animal_id, contact, reason, status, request_date, notes)
						SELECT id, user_id, animal_id, contact, reason, status, request_date, notes
						FROM adoption_requests
					""")
				
				# Drop old table and rename new one
				cur.execute("DROP TABLE adoption_requests")
				cur.execute("ALTER TABLE adoption_requests_new RENAME TO adoption_requests")
				
				conn.commit()
				cur.execute("PRAGMA foreign_keys = ON")
				print("[INFO] Successfully migrated adoption_requests table")
				
		except Exception as e:
			# Log but don't fail - column might already be in the CREATE TABLE statement
			print(f"[INFO] Schema migration note: {e}")
		finally:
			conn.close()
