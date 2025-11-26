"""Animal model."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, Optional


@dataclass
class Animal:
	id: Optional[int] = None
	name: str = ""
	type: str = ""
	age: Optional[int] = None
	health_status: str = "unknown"

	def to_dict(self) -> Dict[str, Any]:
		return asdict(self)

