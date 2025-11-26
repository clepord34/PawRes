"""RescueMission model."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, Optional


@dataclass
class RescueMission:
	id: Optional[int] = None
	user_id: int = 0
	animal_type: str = ""
	name: str = ""
	location: str = ""
	latitude: Optional[float] = None
	longitude: Optional[float] = None
	details: str = ""
	status: str = "pending"

	def to_dict(self) -> Dict[str, Any]:
		return asdict(self)

