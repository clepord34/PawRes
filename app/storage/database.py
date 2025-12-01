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
			created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
			updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
			updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
			description TEXT,
			photo TEXT,
			rescue_mission_id INTEGER,
			FOREIGN KEY(rescue_mission_id) REFERENCES rescue_missions(id) ON DELETE SET NULL
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
			updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
			notes TEXT,
			status TEXT,
			is_closed INTEGER DEFAULT 0,
			admin_message TEXT,
			animal_type TEXT,
			animal_name TEXT,
			reporter_name TEXT,
			reporter_phone TEXT,
			urgency TEXT DEFAULT 'Medium',
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
			updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
			notes TEXT,
			animal_name TEXT,
			animal_species TEXT,
			admin_message TEXT,
			was_approved INTEGER DEFAULT 0,
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
			if 'rescue_mission_id' not in columns:
				cur.execute("ALTER TABLE animals ADD COLUMN rescue_mission_id INTEGER")
				conn.commit()
				print("[INFO] Added rescue_mission_id column to animals table")
			
			# Check if admin_message column exists in rescue_missions table
			cur.execute("PRAGMA table_info(rescue_missions)")
			rescue_columns = [row[1] for row in cur.fetchall()]
			if 'admin_message' not in rescue_columns:
				cur.execute("ALTER TABLE rescue_missions ADD COLUMN admin_message TEXT")
				conn.commit()
				print("[INFO] Added admin_message column to rescue_missions table")
			
			# Add new structured columns to rescue_missions
			if 'animal_type' not in rescue_columns:
				cur.execute("ALTER TABLE rescue_missions ADD COLUMN animal_type TEXT")
				conn.commit()
				print("[INFO] Added animal_type column to rescue_missions table")
			if 'animal_name' not in rescue_columns:
				cur.execute("ALTER TABLE rescue_missions ADD COLUMN animal_name TEXT")
				conn.commit()
				print("[INFO] Added animal_name column to rescue_missions table")
			if 'reporter_name' not in rescue_columns:
				cur.execute("ALTER TABLE rescue_missions ADD COLUMN reporter_name TEXT")
				conn.commit()
				print("[INFO] Added reporter_name column to rescue_missions table")
			if 'reporter_phone' not in rescue_columns:
				cur.execute("ALTER TABLE rescue_missions ADD COLUMN reporter_phone TEXT")
				conn.commit()
				print("[INFO] Added reporter_phone column to rescue_missions table")
			if 'urgency' not in rescue_columns:
				cur.execute("ALTER TABLE rescue_missions ADD COLUMN urgency TEXT DEFAULT 'Medium'")
				conn.commit()
				print("[INFO] Added urgency column to rescue_missions table")
			if 'is_closed' not in rescue_columns:
				cur.execute("ALTER TABLE rescue_missions ADD COLUMN is_closed INTEGER DEFAULT 0")
				conn.commit()
				print("[INFO] Added is_closed column to rescue_missions table")
			if 'updated_at' not in rescue_columns:
				cur.execute("ALTER TABLE rescue_missions ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
				conn.commit()
				print("[INFO] Added updated_at column to rescue_missions table")
			
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
				
				# Create new table with correct schema (includes updated_at and admin_message)
				cur.execute("""
					CREATE TABLE IF NOT EXISTS adoption_requests_new (
						id INTEGER PRIMARY KEY AUTOINCREMENT,
						user_id INTEGER NOT NULL,
						animal_id INTEGER,
						contact TEXT,
						reason TEXT,
						status TEXT,
						request_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
						updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
						notes TEXT,
						animal_name TEXT,
						animal_species TEXT,
						admin_message TEXT,
						FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
						FOREIGN KEY(animal_id) REFERENCES animals(id) ON DELETE SET NULL
					)
				")""")
				
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
			
			# Check if admin_message column exists in adoption_requests table (simple ADD COLUMN)
			cur.execute("PRAGMA table_info(adoption_requests)")
			adoption_cols_check = [row[1] for row in cur.fetchall()]
			if 'admin_message' not in adoption_cols_check:
				cur.execute("ALTER TABLE adoption_requests ADD COLUMN admin_message TEXT")
				conn.commit()
				print("[INFO] Added admin_message column to adoption_requests table")
			if 'updated_at' not in adoption_cols_check:
				cur.execute("ALTER TABLE adoption_requests ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
				conn.commit()
				print("[INFO] Added updated_at column to adoption_requests table")
			if 'was_approved' not in adoption_cols_check:
				cur.execute("ALTER TABLE adoption_requests ADD COLUMN was_approved INTEGER DEFAULT 0")
				conn.commit()
				# Backfill: mark existing approved requests
				cur.execute("UPDATE adoption_requests SET was_approved = 1 WHERE LOWER(status) = 'approved'")
				conn.commit()
				print("[INFO] Added was_approved column to adoption_requests table")
			
			# Add updated_at to animals table
			cur.execute("PRAGMA table_info(animals)")
			animal_cols = [row[1] for row in cur.fetchall()]
			if 'updated_at' not in animal_cols:
				cur.execute("ALTER TABLE animals ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
				conn.commit()
				print("[INFO] Added updated_at column to animals table")
			
			# Add updated_at to users table
			cur.execute("PRAGMA table_info(users)")
			user_cols_check = [row[1] for row in cur.fetchall()]
			if 'updated_at' not in user_cols_check:
				cur.execute("ALTER TABLE users ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
				conn.commit()
				print("[INFO] Added updated_at column to users table")
			
			# =========================================================================
			# Archive/Remove metadata columns migration
			# =========================================================================
			
			# Add archive/remove columns to rescue_missions
			cur.execute("PRAGMA table_info(rescue_missions)")
			rescue_cols_final = [row[1] for row in cur.fetchall()]
			if 'archived_at' not in rescue_cols_final:
				cur.execute("ALTER TABLE rescue_missions ADD COLUMN archived_at TIMESTAMP")
				conn.commit()
				print("[INFO] Added archived_at column to rescue_missions table")
			if 'archived_by' not in rescue_cols_final:
				cur.execute("ALTER TABLE rescue_missions ADD COLUMN archived_by INTEGER")
				conn.commit()
				print("[INFO] Added archived_by column to rescue_missions table")
			if 'archive_note' not in rescue_cols_final:
				cur.execute("ALTER TABLE rescue_missions ADD COLUMN archive_note TEXT")
				conn.commit()
				print("[INFO] Added archive_note column to rescue_missions table")
			if 'removed_at' not in rescue_cols_final:
				cur.execute("ALTER TABLE rescue_missions ADD COLUMN removed_at TIMESTAMP")
				conn.commit()
				print("[INFO] Added removed_at column to rescue_missions table")
			if 'removed_by' not in rescue_cols_final:
				cur.execute("ALTER TABLE rescue_missions ADD COLUMN removed_by INTEGER")
				conn.commit()
				print("[INFO] Added removed_by column to rescue_missions table")
			if 'removal_reason' not in rescue_cols_final:
				cur.execute("ALTER TABLE rescue_missions ADD COLUMN removal_reason TEXT")
				conn.commit()
				print("[INFO] Added removal_reason column to rescue_missions table")
			if 'previous_status' not in rescue_cols_final:
				cur.execute("ALTER TABLE rescue_missions ADD COLUMN previous_status TEXT")
				conn.commit()
				print("[INFO] Added previous_status column to rescue_missions table")
			
			# Add archive/remove columns to adoption_requests
			cur.execute("PRAGMA table_info(adoption_requests)")
			adopt_cols_final = [row[1] for row in cur.fetchall()]
			if 'archived_at' not in adopt_cols_final:
				cur.execute("ALTER TABLE adoption_requests ADD COLUMN archived_at TIMESTAMP")
				conn.commit()
				print("[INFO] Added archived_at column to adoption_requests table")
			if 'archived_by' not in adopt_cols_final:
				cur.execute("ALTER TABLE adoption_requests ADD COLUMN archived_by INTEGER")
				conn.commit()
				print("[INFO] Added archived_by column to adoption_requests table")
			if 'archive_note' not in adopt_cols_final:
				cur.execute("ALTER TABLE adoption_requests ADD COLUMN archive_note TEXT")
				conn.commit()
				print("[INFO] Added archive_note column to adoption_requests table")
			if 'removed_at' not in adopt_cols_final:
				cur.execute("ALTER TABLE adoption_requests ADD COLUMN removed_at TIMESTAMP")
				conn.commit()
				print("[INFO] Added removed_at column to adoption_requests table")
			if 'removed_by' not in adopt_cols_final:
				cur.execute("ALTER TABLE adoption_requests ADD COLUMN removed_by INTEGER")
				conn.commit()
				print("[INFO] Added removed_by column to adoption_requests table")
			if 'removal_reason' not in adopt_cols_final:
				cur.execute("ALTER TABLE adoption_requests ADD COLUMN removal_reason TEXT")
				conn.commit()
				print("[INFO] Added removal_reason column to adoption_requests table")
			if 'previous_status' not in adopt_cols_final:
				cur.execute("ALTER TABLE adoption_requests ADD COLUMN previous_status TEXT")
				conn.commit()
				print("[INFO] Added previous_status column to adoption_requests table")
			if 'denial_reason' not in adopt_cols_final:
				cur.execute("ALTER TABLE adoption_requests ADD COLUMN denial_reason TEXT")
				conn.commit()
				print("[INFO] Added denial_reason column to adoption_requests table")
			
			# Add archive/remove columns to animals
			cur.execute("PRAGMA table_info(animals)")
			animal_cols_final = [row[1] for row in cur.fetchall()]
			if 'archived_at' not in animal_cols_final:
				cur.execute("ALTER TABLE animals ADD COLUMN archived_at TIMESTAMP")
				conn.commit()
				print("[INFO] Added archived_at column to animals table")
			if 'archived_by' not in animal_cols_final:
				cur.execute("ALTER TABLE animals ADD COLUMN archived_by INTEGER")
				conn.commit()
				print("[INFO] Added archived_by column to animals table")
			if 'archive_note' not in animal_cols_final:
				cur.execute("ALTER TABLE animals ADD COLUMN archive_note TEXT")
				conn.commit()
				print("[INFO] Added archive_note column to animals table")
			if 'removed_at' not in animal_cols_final:
				cur.execute("ALTER TABLE animals ADD COLUMN removed_at TIMESTAMP")
				conn.commit()
				print("[INFO] Added removed_at column to animals table")
			if 'removed_by' not in animal_cols_final:
				cur.execute("ALTER TABLE animals ADD COLUMN removed_by INTEGER")
				conn.commit()
				print("[INFO] Added removed_by column to animals table")
			if 'removal_reason' not in animal_cols_final:
				cur.execute("ALTER TABLE animals ADD COLUMN removal_reason TEXT")
				conn.commit()
				print("[INFO] Added removal_reason column to animals table")
			if 'previous_status' not in animal_cols_final:
				cur.execute("ALTER TABLE animals ADD COLUMN previous_status TEXT")
				conn.commit()
				print("[INFO] Added previous_status column to animals table")
			
			# Migrate existing rescue mission data: extract animal_type and name from notes field
			cur.execute("SELECT id, notes FROM rescue_missions WHERE animal_type IS NULL AND notes IS NOT NULL")
			missions_to_migrate = cur.fetchall()
			for mission in missions_to_migrate:
				mid, notes = mission[0], mission[1]
				if notes:
					animal_type = None
					name = None
					urgency = "Medium"
					for line in notes.split("\n"):
						if line.lower().startswith("type:"):
							animal_type = line.split(":", 1)[1].strip()
						elif line.lower().startswith("name:"):
							name = line.split(":", 1)[1].strip()
						elif "[urgency:" in line.lower():
							# Extract urgency from [Urgency: High - ...]
							urgency_part = line.lower().split("[urgency:")[1].split("]")[0].strip()
							if "high" in urgency_part:
								urgency = "High"
							elif "low" in urgency_part:
								urgency = "Low"
					if animal_type or name:
						cur.execute(
							"UPDATE rescue_missions SET animal_type = ?, animal_name = ?, urgency = ? WHERE id = ?",
							(animal_type, name, urgency, mid)
						)
			conn.commit()
			if missions_to_migrate:
				print(f"[INFO] Migrated {len(missions_to_migrate)} rescue missions to use structured columns")
				
		except Exception as e:
			# Log but don't fail - column might already be in the CREATE TABLE statement
			print(f"[INFO] Schema migration note: {e}")
		finally:
			conn.close()
