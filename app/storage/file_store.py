"""File storage helper for managing file uploads and downloads."""
from __future__ import annotations

import base64
import hashlib
import shutil
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any

import app_config


class FileStoreError(Exception):
    """Base exception for file store errors."""
    pass


class FileSizeError(FileStoreError):
    """Raised when file exceeds size limit."""
    pass


class FileTypeError(FileStoreError):
    """Raised when file type is not allowed."""
    pass


class FileNotFoundError(FileStoreError):
    """Raised when file does not exist."""
    pass


class FileStore:
    """File storage manager for handling uploads and downloads.
    
    Thread-safe file storage utility that manages files in a dedicated
    uploads directory within the storage folder.
    
    Attributes:
        uploads_dir: Path to the uploads directory
        max_size_mb: Maximum allowed file size in megabytes
        allowed_extensions: Tuple of allowed file extensions
    """
    
    def __init__(
        self,
        uploads_dir: Optional[Path] = None,
        max_size_mb: float = None,
        allowed_extensions: Tuple[str, ...] = None
    ) -> None:
        """Initialize the file store.
        
        Args:
            uploads_dir: Custom uploads directory path. Defaults to storage/uploads
            max_size_mb: Maximum file size in MB. Defaults to app_config.MAX_PHOTO_SIZE_MB
            allowed_extensions: Allowed file extensions. Defaults to app_config.ALLOWED_PHOTO_EXTENSIONS
        """
        self.uploads_dir = uploads_dir or (app_config.STORAGE_DIR / "uploads")
        self.max_size_mb = max_size_mb if max_size_mb is not None else app_config.MAX_PHOTO_SIZE_MB
        self.allowed_extensions = allowed_extensions or app_config.ALLOWED_PHOTO_EXTENSIONS
        
        # Ensure uploads directory exists
        self.uploads_dir.mkdir(parents=True, exist_ok=True)
    
    def _generate_unique_filename(self, original_name: str) -> str:
        """Generate a unique filename preserving the original extension.
        
        Args:
            original_name: Original filename with extension
            
        Returns:
            Unique filename with timestamp and UUID
        """
        ext = Path(original_name).suffix.lower()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = uuid.uuid4().hex[:8]
        return f"{timestamp}_{unique_id}{ext}"
    
    def _generate_named_filename(self, name: str, original_name: str) -> str:
        """Generate a filename based on a given name (e.g., animal name).
        
        Args:
            name: The name to use for the file (e.g., animal name)
            original_name: Original filename (for extension)
            
        Returns:
            Sanitized filename like 'pipay_20251125_abc123.jpg'
        """
        import re
        ext = Path(original_name).suffix.lower()
        # Sanitize name: lowercase, replace spaces with underscores, remove special chars
        safe_name = re.sub(r'[^a-zA-Z0-9_]', '', name.lower().replace(' ', '_'))
        if not safe_name:
            safe_name = "animal"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = uuid.uuid4().hex[:4]
        return f"{safe_name}_{timestamp}_{unique_id}{ext}"
    
    def _validate_extension(self, filename: str) -> bool:
        """Check if the file extension is allowed.
        
        Args:
            filename: Filename to check
            
        Returns:
            True if extension is allowed
            
        Raises:
            FileTypeError: If extension is not allowed
        """
        ext = Path(filename).suffix.lower()
        if ext not in self.allowed_extensions:
            raise FileTypeError(
                f"File type '{ext}' not allowed. "
                f"Allowed types: {', '.join(self.allowed_extensions)}"
            )
        return True
    
    def _validate_size(self, data: bytes) -> bool:
        """Check if the file size is within limits.
        
        Args:
            data: File content as bytes
            
        Returns:
            True if size is within limits
            
        Raises:
            FileSizeError: If file exceeds size limit
        """
        size_mb = len(data) / (1024 * 1024)
        if size_mb > self.max_size_mb:
            raise FileSizeError(
                f"File size ({size_mb:.2f} MB) exceeds limit ({self.max_size_mb} MB)"
            )
        return True
    
    def _compute_hash(self, data: bytes) -> str:
        """Compute MD5 hash of file content for integrity checking.
        
        Args:
            data: File content as bytes
            
        Returns:
            MD5 hex digest
        """
        return hashlib.md5(data).hexdigest()
    
    def save_base64_file(
        self,
        base64_data: str,
        original_name: str = "file.jpg",
        validate: bool = True
    ) -> str:
        """Save a base64 encoded file to disk.
        
        Args:
            base64_data: Base64 encoded file content
            original_name: Original filename (for extension)
            validate: Whether to validate type and size
            
        Returns:
            The saved filename (not full path)
            
        Raises:
            FileTypeError: If file type not allowed
            FileSizeError: If file too large
        """
        # Decode base64
        try:
            file_bytes = base64.b64decode(base64_data)
        except Exception as e:
            raise FileStoreError(f"Invalid base64 data: {e}")
        
        # Validate if requested
        if validate:
            self._validate_extension(original_name)
            self._validate_size(file_bytes)
        
        # Generate unique filename
        filename = self._generate_unique_filename(original_name)
        file_path = self.uploads_dir / filename
        
        # Write to disk
        try:
            with open(file_path, "wb") as f:
                f.write(file_bytes)
        except Exception as e:
            raise FileStoreError(f"Failed to save file: {e}")
        
        return filename
    
    def save_bytes(
        self,
        data: bytes,
        original_name: str = "file.jpg",
        validate: bool = True,
        custom_name: Optional[str] = None
    ) -> str:
        """Save raw bytes to disk.
        
        Args:
            data: File content as bytes
            original_name: Original filename (for extension)
            validate: Whether to validate type and size
            custom_name: Optional custom name to use in filename (e.g., animal name)
            
        Returns:
            The saved filename (not full path)
        """
        if validate:
            self._validate_extension(original_name)
            self._validate_size(data)
        
        # Use custom name if provided, otherwise generate unique
        if custom_name:
            filename = self._generate_named_filename(custom_name, original_name)
        else:
            filename = self._generate_unique_filename(original_name)
        file_path = self.uploads_dir / filename
        
        try:
            with open(file_path, "wb") as f:
                f.write(data)
        except Exception as e:
            raise FileStoreError(f"Failed to save file: {e}")
        
        return filename
    
    def save_base64_with_name(
        self,
        base64_data: str,
        name: str,
        original_name: str = "file.jpg",
        validate: bool = True
    ) -> str:
        """Save a base64 encoded file with a custom name.
        
        Args:
            base64_data: Base64 encoded file content
            name: Custom name to use in filename (e.g., animal name)
            original_name: Original filename (for extension)
            validate: Whether to validate type and size
            
        Returns:
            The saved filename (not full path)
        """
        try:
            file_bytes = base64.b64decode(base64_data)
        except Exception as e:
            raise FileStoreError(f"Invalid base64 data: {e}")
        
        if validate:
            self._validate_extension(original_name)
            self._validate_size(file_bytes)
        
        filename = self._generate_named_filename(name, original_name)
        file_path = self.uploads_dir / filename
        
        try:
            with open(file_path, "wb") as f:
                f.write(file_bytes)
        except Exception as e:
            raise FileStoreError(f"Failed to save file: {e}")
        
        return filename
    
    def read_file_as_base64(self, filename: str) -> str:
        """Read a file and return its content as base64.
        
        Args:
            filename: Filename (not full path) to read
            
        Returns:
            Base64 encoded file content
            
        Raises:
            FileNotFoundError: If file does not exist
        """
        file_path = self.uploads_dir / filename
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {filename}")
        
        try:
            with open(file_path, "rb") as f:
                return base64.b64encode(f.read()).decode()
        except Exception as e:
            raise FileStoreError(f"Failed to read file: {e}")
    
    def read_file_as_bytes(self, filename: str) -> bytes:
        """Read a file and return its raw bytes.
        
        Args:
            filename: Filename (not full path) to read
            
        Returns:
            File content as bytes
        """
        file_path = self.uploads_dir / filename
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {filename}")
        
        try:
            with open(file_path, "rb") as f:
                return f.read()
        except Exception as e:
            raise FileStoreError(f"Failed to read file: {e}")
    
    def delete_file(self, filename: str) -> bool:
        """Delete a file from storage.
        
        Args:
            filename: Filename (not full path) to delete
            
        Returns:
            True if file was deleted, False if it didn't exist
        """
        file_path = self.uploads_dir / filename
        
        if not file_path.exists():
            return False
        
        try:
            file_path.unlink()
            return True
        except Exception as e:
            raise FileStoreError(f"Failed to delete file: {e}")
    
    def rename_file(self, old_filename: str, new_name: str) -> str:
        """Rename a file with a new custom name while preserving extension.
        
        Args:
            old_filename: Current filename in storage
            new_name: New name to use (e.g., animal name like 'ashley')
            
        Returns:
            The new filename after renaming
            
        Raises:
            FileNotFoundError: If the old file doesn't exist
            FileStoreError: If rename operation fails
        """
        old_path = self.uploads_dir / old_filename
        
        if not old_path.exists():
            raise FileNotFoundError(f"File not found: {old_filename}")
        
        # Generate new filename with the new name
        new_filename = self._generate_named_filename(new_name, old_filename)
        new_path = self.uploads_dir / new_filename
        
        try:
            import shutil
            shutil.move(str(old_path), str(new_path))
            print(f"[INFO] Renamed photo: {old_filename} -> {new_filename}")
            return new_filename
        except Exception as e:
            raise FileStoreError(f"Failed to rename file: {e}")
    
    def file_exists(self, filename: str) -> bool:
        """Check if a file exists in storage.
        
        Args:
            filename: Filename (not full path) to check
            
        Returns:
            True if file exists
        """
        return (self.uploads_dir / filename).exists()
    
    def get_file_info(self, filename: str) -> Dict[str, Any]:
        """Get metadata about a stored file.
        
        Args:
            filename: Filename (not full path)
            
        Returns:
            Dictionary with file metadata
        """
        file_path = self.uploads_dir / filename
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {filename}")
        
        stat = file_path.stat()
        
        return {
            "filename": filename,
            "size_bytes": stat.st_size,
            "size_mb": stat.st_size / (1024 * 1024),
            "extension": file_path.suffix.lower(),
            "created_at": datetime.fromtimestamp(stat.st_ctime),
            "modified_at": datetime.fromtimestamp(stat.st_mtime),
            "full_path": str(file_path),
        }
    
    def list_files(self, extension: Optional[str] = None) -> List[str]:
        """List all files in the uploads directory.
        
        Args:
            extension: Optional filter by extension (e.g., '.jpg')
            
        Returns:
            List of filenames
        """
        files = []
        for item in self.uploads_dir.iterdir():
            if item.is_file():
                if extension is None or item.suffix.lower() == extension.lower():
                    files.append(item.name)
        return sorted(files)
    
    def get_total_size_mb(self) -> float:
        """Get total size of all stored files in MB.
        
        Returns:
            Total size in megabytes
        """
        total_bytes = sum(
            f.stat().st_size 
            for f in self.uploads_dir.iterdir() 
            if f.is_file()
        )
        return total_bytes / (1024 * 1024)
    
    def cleanup_old_files(self, days: int = 30) -> int:
        """Delete files older than specified days.
        
        Args:
            days: Delete files older than this many days
            
        Returns:
            Number of files deleted
        """
        from datetime import timedelta
        
        cutoff = datetime.now() - timedelta(days=days)
        deleted = 0
        
        for item in self.uploads_dir.iterdir():
            if item.is_file():
                if datetime.fromtimestamp(item.stat().st_mtime) < cutoff:
                    try:
                        item.unlink()
                        deleted += 1
                    except Exception:
                        pass  # Skip files that can't be deleted
        
        return deleted
    
    def copy_file(self, filename: str, destination: Path) -> str:
        """Copy a file to another location.
        
        Args:
            filename: Source filename in uploads
            destination: Destination directory
            
        Returns:
            Full path to copied file
        """
        source = self.uploads_dir / filename
        
        if not source.exists():
            raise FileNotFoundError(f"File not found: {filename}")
        
        destination = Path(destination)
        destination.mkdir(parents=True, exist_ok=True)
        
        dest_path = destination / filename
        shutil.copy2(source, dest_path)
        
        return str(dest_path)


# Create a default instance for convenience
_default_store: Optional[FileStore] = None


def get_file_store() -> FileStore:
    """Get the default FileStore instance.
    
    Returns:
        Singleton FileStore instance
    """
    global _default_store
    if _default_store is None:
        _default_store = FileStore()
    return _default_store


# Convenience functions using the default store
def save_photo(base64_data: str, original_name: str = "photo.jpg") -> str:
    """Save a photo using the default store.
    
    Args:
        base64_data: Base64 encoded photo
        original_name: Original filename
        
    Returns:
        Saved filename
    """
    return get_file_store().save_base64_file(base64_data, original_name)


def read_photo(filename: str) -> str:
    """Read a photo as base64 using the default store.
    
    Args:
        filename: Photo filename
        
    Returns:
        Base64 encoded photo data
    """
    return get_file_store().read_file_as_base64(filename)


def delete_photo(filename: str) -> bool:
    """Delete a photo using the default store.
    
    Args:
        filename: Photo filename
        
    Returns:
        True if deleted
    """
    return get_file_store().delete_file(filename)


__all__ = [
    "FileStore",
    "FileStoreError",
    "FileSizeError",
    "FileTypeError",
    "FileNotFoundError",
    "get_file_store",
    "save_photo",
    "read_photo",
    "delete_photo",
]
