"""Data class for AI classification results."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, List, Dict


@dataclass
class BreedPrediction:
    """A single breed prediction with confidence score."""
    breed: str
    confidence: float  # 0.0 - 1.0
    
    def to_dict(self) -> Dict:
        return {
            "breed": self.breed,
            "confidence": self.confidence,
        }


@dataclass
class ClassificationResult:
    """Result from AI image classification.
    
    Attributes:
        species: Detected species ("Dog", "Cat", or "Other")
        species_confidence: Confidence score for species detection (0.0 - 1.0)
        breed: Best matching breed name (formatted nicely, e.g., "Golden Retriever")
        breed_confidence: Confidence score for breed prediction (0.0 - 1.0)
        alternative_breeds: List of alternative breed predictions
        is_mixed_breed: True if confidence is below threshold (suggests Aspin/Puspin)
        error: Error message if classification failed
        raw_breed: Original breed name from model (e.g., "golden_retriever")
    """
    species: str = "Not Specified"
    species_confidence: float = 0.0
    breed: str = "Not Specified"
    breed_confidence: float = 0.0
    alternative_breeds: List[BreedPrediction] = field(default_factory=list)
    is_mixed_breed: bool = False
    error: Optional[str] = None
    raw_breed: str = ""
    
    @property
    def success(self) -> bool:
        """Check if classification was successful."""
        return self.error is None and self.species != "Not Specified"
    
    @property
    def has_breed(self) -> bool:
        """Check if a breed was detected."""
        return self.breed not in ("Not Specified", "Mixed Breed", "")
    
    @property
    def species_emoji(self) -> str:
        """Get emoji for the detected species."""
        emojis = {
            "Dog": "🐕",
            "Cat": "🐱",
            "Other": "🐾",
            "Not Specified": "❓",
        }
        return emojis.get(self.species, "🐾")
    
    @property
    def confidence_level(self) -> str:
        """Get human-readable confidence level."""
        if self.breed_confidence >= 0.80:
            return "High"
        elif self.breed_confidence >= 0.58:
            return "Medium"
        else:
            return "Low"
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "species": self.species,
            "species_confidence": self.species_confidence,
            "breed": self.breed,
            "breed_confidence": self.breed_confidence,
            "alternative_breeds": [b.to_dict() for b in self.alternative_breeds],
            "is_mixed_breed": self.is_mixed_breed,
            "error": self.error,
            "raw_breed": self.raw_breed,
        }
    
    @classmethod
    def from_error(cls, error_message: str) -> "ClassificationResult":
        """Create a result representing an error."""
        return cls(error=error_message)
    
    @classmethod
    def create_mixed_breed(cls, species: str, species_confidence: float) -> "ClassificationResult":
        """Create a result for mixed breed (Aspin/Puspin)."""
        if species == "Dog":
            breed = "Aspin (Mixed Breed)"
        elif species == "Cat":
            breed = "Puspin (Mixed Breed)"
        else:
            breed = "Mixed Breed"
        
        return cls(
            species=species,
            species_confidence=species_confidence,
            breed=breed,
            breed_confidence=0.0,
            is_mixed_breed=True,
        )


__all__ = ["ClassificationResult", "BreedPrediction"]
