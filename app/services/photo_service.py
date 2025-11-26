"""Photo service for loading and managing animal photos."""
from __future__ import annotations

from typing import Optional
from storage.file_store import get_file_store, FileStoreError


class PhotoService:
    """Service for loading and managing photos."""
    
    def __init__(self):
        self.file_store = get_file_store()
    
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
        if data.endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp')):
            return False
        
        # Long strings without file extensions are likely base64
        return len(data) > 200
    
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
        except Exception:
            return None
    
    def save_photo_from_base64(self, base64_data: str, original_name: str = "photo.jpg") -> str:
        """Save base64 photo data to FileStore.
        
        Args:
            base64_data: Base64 encoded image data
            original_name: Original filename for extension detection
            
        Returns:
            Filename to store in database
        """
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
        except FileStoreError:
            return False


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


__all__ = ["PhotoService", "get_photo_service", "load_photo"]
