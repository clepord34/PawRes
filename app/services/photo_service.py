"""Photo service for loading and managing animal photos."""
from __future__ import annotations

import base64
from typing import Optional, Tuple
from enum import Enum

from storage.file_store import get_file_store, FileStoreError
import app_config


class PhotoValidationResult(Enum):
    """Result of photo validation."""
    VALID = "valid"
    INVALID_FORMAT = "invalid_format"
    INVALID_SIZE = "size_exceeded"
    INVALID_TYPE = "invalid_type"
    DECODE_ERROR = "decode_error"


class PhotoServiceError(Exception):
    """Base exception for photo service errors."""
    pass


class PhotoService:
    """Service for loading, validating, and managing photos.
    
    Provides:
    - Photo loading from storage or base64
    - MIME type validation for security
    - Size validation
    - Base64 detection and handling
    """
    
    def __init__(self):
        """Initialize photo service with file store."""
        self.file_store = get_file_store()
        self._allowed_mime_types = app_config.ALLOWED_MIME_TYPES
        self._max_size_mb = app_config.MAX_PHOTO_SIZE_MB
        self._allowed_extensions = app_config.ALLOWED_PHOTO_EXTENSIONS
    
    def is_base64(self, data: str) -> bool:
        """Check if a string is base64 data (not a filename).
        
        Args:
            data: String to check
            
        Returns:
            True if data appears to be base64 encoded
        """
        if not data:
            return False
        
        # Filenames are short and have extensions like .jpg, .png
        # Base64 is very long (images are typically 10KB+ = 13K+ base64 chars)
        if len(data) < 100:
            return False
        
        # Check if it looks like a filename (has extension at end)
        if data.endswith(self._allowed_extensions):
            return False
        
        # Long strings without file extensions are likely base64
        return len(data) > 200
    
    def validate_base64_image(self, base64_data: str) -> Tuple[PhotoValidationResult, str]:
        """Validate base64 encoded image data.
        
        Performs MIME type and size validation for security.
        
        Args:
            base64_data: Base64 encoded image data
            
        Returns:
            Tuple of (result, message) where result is PhotoValidationResult
        """
        if not base64_data:
            return PhotoValidationResult.INVALID_FORMAT, "No image data provided"
        
        # Try to decode to check size
        try:
            decoded = base64.b64decode(base64_data)
        except Exception as e:
            return PhotoValidationResult.DECODE_ERROR, f"Invalid base64 data: {e}"
        
        # Check file size
        size_mb = len(decoded) / (1024 * 1024)
        if size_mb > self._max_size_mb:
            return PhotoValidationResult.INVALID_SIZE, f"Image too large ({size_mb:.2f}MB). Max: {self._max_size_mb}MB"
        
        # Check MIME type by magic bytes
        mime_type = self._detect_mime_type(decoded)
        if mime_type not in self._allowed_mime_types:
            return PhotoValidationResult.INVALID_TYPE, f"Invalid image type. Allowed: {', '.join(self._allowed_mime_types)}"
        
        return PhotoValidationResult.VALID, "Image is valid"
    
    def _detect_mime_type(self, data: bytes) -> Optional[str]:
        """Detect MIME type from file magic bytes.
        
        Args:
            data: Raw file bytes
            
        Returns:
            Detected MIME type or None
        """
        if len(data) < 4:
            return None
        
        # Check magic bytes for common image formats
        if data[:3] == b'\xff\xd8\xff':
            return "image/jpeg"
        elif data[:8] == b'\x89PNG\r\n\x1a\n':
            return "image/png"
        elif data[:6] in (b'GIF87a', b'GIF89a'):
            return "image/gif"
        elif data[:4] == b'RIFF' and data[8:12] == b'WEBP':
            return "image/webp"
        
        return None
    
    def load_photo_as_base64(self, photo_data: Optional[str]) -> Optional[str]:
        """Load a photo as base64 for display, handling both formats.
        
        Args:
            photo_data: Either a filename (from FileStore) or base64 data (legacy)
            
        Returns:
            Base64 encoded image data for display, or None if not found
        """
        if not photo_data:
            return None
        
        # If it's already base64, return as-is
        if self.is_base64(photo_data):
            return photo_data
        
        # It's a filename - load from FileStore
        try:
            return self.file_store.read_file_as_base64(photo_data)
        except FileStoreError:
            # File not found
            return None
        except Exception as e:
            print(f"[ERROR] PhotoService: Failed to load photo: {e}")
            return None
    
    def save_photo_from_base64(
        self, 
        base64_data: str, 
        original_name: str = "photo.jpg",
        validate: bool = True
    ) -> str:
        """Save base64 photo data to FileStore.
        
        Args:
            base64_data: Base64 encoded image data
            original_name: Original filename for extension detection
            validate: Whether to validate image before saving
            
        Returns:
            Filename to store in database
            
        Raises:
            PhotoServiceError: If validation fails
        """
        if validate:
            result, message = self.validate_base64_image(base64_data)
            if result != PhotoValidationResult.VALID:
                raise PhotoServiceError(message)
        
        return self.file_store.save_base64_file(base64_data, original_name)
    
    def delete_photo(self, photo_data: Optional[str]) -> bool:
        """Delete a photo file if it's stored in FileStore.
        
        Args:
            photo_data: Either a filename or base64 data
            
        Returns:
            True if deleted, False otherwise
        """
        if not photo_data or self.is_base64(photo_data):
            return False
        
        try:
            return self.file_store.delete_file(photo_data)
        except FileStoreError as e:
            print(f"[WARN] PhotoService: Could not delete photo: {e}")
            return False
    
    def get_photo_info(self, photo_data: Optional[str]) -> Optional[dict]:
        """Get information about a stored photo.
        
        Args:
            photo_data: Either a filename or base64 data
            
        Returns:
            Dict with photo metadata or None
        """
        if not photo_data:
            return None
        
        if self.is_base64(photo_data):
            try:
                decoded = base64.b64decode(photo_data)
                return {
                    "type": "base64",
                    "size_bytes": len(decoded),
                    "size_mb": len(decoded) / (1024 * 1024),
                    "mime_type": self._detect_mime_type(decoded),
                }
            except Exception:
                return None
        
        try:
            return self.file_store.get_file_info(photo_data)
        except FileStoreError:
            return None


# Singleton instance
_photo_service: Optional[PhotoService] = None


def get_photo_service() -> PhotoService:
    """Get the singleton PhotoService instance."""
    global _photo_service
    if _photo_service is None:
        _photo_service = PhotoService()
    return _photo_service


def load_photo(photo_data: Optional[str]) -> Optional[str]:
    """Convenience function to load a photo as base64.
    
    Args:
        photo_data: Either a filename or base64 data from database
        
    Returns:
        Base64 data for display, or None
    """
    return get_photo_service().load_photo_as_base64(photo_data)


__all__ = [
    "PhotoService", 
    "PhotoServiceError",
    "PhotoValidationResult",
    "get_photo_service", 
    "load_photo",
]
