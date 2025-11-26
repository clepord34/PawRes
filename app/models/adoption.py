"""AdoptionRequest model."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, Optional


@dataclass
class AdoptionRequest:
	id: Optional[int] = None
	user_id: int = 0
	animal_id: int = 0
	contact: str = ""
	reason: str = ""
	status: str = "pending"

	def to_dict(self) -> Dict[str, Any]:
		return asdict(self)

