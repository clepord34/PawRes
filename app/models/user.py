"""User model."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, Optional


@dataclass
class User:
	id: Optional[int] = None
	name: str = ""
	email: str = ""
	password: str = ""
	role: str = "user"

	def to_dict(self, include_password: bool = False) -> Dict[str, Any]:
		"""Return a dict representation. Password excluded by default."""
		data = asdict(self)
		if not include_password:
			data.pop("password", None)
		return data

