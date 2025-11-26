"""Photo upload widget component."""
from __future__ import annotations
from typing import Optional, Callable, TYPE_CHECKING
import base64
import os

if TYPE_CHECKING:
    import flet as ft

try:
    import flet as ft
except ImportError:
    ft = None

# Import FileStore for file-based storage
from storage.file_store import get_file_store, FileStoreError


class PhotoUploadWidget:
    """Reusable photo upload widget with preview."""
    
    def __init__(
        self,
        page: object,
        initial_photo: Optional[str] = None,
        width: int = 100,
        height: int = 100
    ):
        """Initialize the photo upload widget."""
        if ft is None:
            raise RuntimeError("Flet must be installed to create photo upload widgets")
        
        self.page = page
        self.width = width
        self.height = height
        self.file_store = get_file_store()
        
        # Track the current photo - can be filename or base64
        self._photo_filename: Optional[str] = None
        self._photo_base64: Optional[str] = None
        self._original_filename: Optional[str] = None  # Track original for cleanup
        self._pending_image_bytes: Optional[bytes] = None  # Pending upload (not saved yet)
        
        # Create display container
        self.photo_display = self._create_photo_display(initial_photo)
        
        # Create file picker
        self.file_picker = ft.FilePicker(on_result=self._on_file_picked)
        page.overlay.append(self.file_picker)
    
    def _is_base64(self, data: str) -> bool:
        """Check if a string looks like base64 data (not a filename)."""
        if not data:
            return False
        # Filenames are typically short and have extensions
        # Base64 is long and doesn't have path separators
        if len(data) > 200 or '/' not in data and '\\' not in data and '.' not in data[-5:]:
            try:
                # Try to decode a small portion to verify it's base64
                base64.b64decode(data[:100] + '==', validate=True)
                return len(data) > 50  # Base64 images are usually long
            except Exception:
                pass
        return False
    
    def _load_photo_base64(self, photo: str) -> Optional[str]:
        """Load photo as base64, whether from filename or already base64."""
        if not photo:
            return None
        
        # Check if it's already base64 (legacy data)
        if self._is_base64(photo):
            self._photo_base64 = photo
            return photo
        
        # It's a filename - load from FileStore
        try:
            self._photo_filename = photo
            self._photo_base64 = self.file_store.read_file_as_base64(photo)
            return self._photo_base64
        except FileStoreError:
            # File not found - might be deleted or moved
            return None
    
    def _create_photo_display(self, initial_photo: Optional[str]) -> object:
        """Create the photo display container."""
        photo_base64 = self._load_photo_base64(initial_photo) if initial_photo else None
        
        if photo_base64:
            return ft.Container(
                content=ft.Image(
                    src_base64=photo_base64,
                    width=self.width,
                    height=self.height,
                    fit=ft.ImageFit.COVER,
                    border_radius=8,
                ),
                width=self.width,
                height=self.height,
                border_radius=8,
            )
        else:
            return ft.Container(
                width=self.width,
                height=self.height,
                bgcolor=ft.Colors.GREY_300,
                border_radius=8,
                alignment=ft.alignment.center,
            )
    
    def _on_file_picked(self, e: object):
        """Handle file selection - stores image data temporarily until save_with_name is called."""
        if e.files and len(e.files) > 0:
            file_info = e.files[0]
            file_path = file_info.path
            self._original_filename = file_info.name
            
            if not file_path:
                self.page.snack_bar = ft.SnackBar(ft.Text("Unable to access file. Please try again."))
                self.page.snack_bar.open = True
                self.page.update()
                return
            
            try:
                if not os.path.exists(file_path):
                    raise FileNotFoundError(f"File not found: {file_path}")
                
                # Read the file and store temporarily
                with open(file_path, "rb") as image_file:
                    self._pending_image_bytes = image_file.read()
                
                # Store base64 for display
                self._photo_base64 = base64.b64encode(self._pending_image_bytes).decode()
                
                # Clear any previously saved filename (new image selected)
                self._photo_filename = None
                
                # Update display
                self.photo_display.content = ft.Image(
                    src_base64=self._photo_base64,
                    width=self.width,
                    height=self.height,
                    fit=ft.ImageFit.COVER,
                    border_radius=8,
                )
                
                self.page.snack_bar = ft.SnackBar(ft.Text(f"Photo selected: {self._original_filename}"))
                self.page.snack_bar.open = True
                self.page.update()
                
            except FileStoreError as ex:
                self.page.snack_bar = ft.SnackBar(ft.Text(f"Upload error: {str(ex)}"))
                self.page.snack_bar.open = True
                self.page.update()
            except Exception as ex:
                import traceback
                traceback.print_exc()
                self.page.snack_bar = ft.SnackBar(ft.Text(f"Error loading photo: {str(ex)}"))
                self.page.snack_bar.open = True
                self.page.update()
        else:
            self.page.snack_bar = ft.SnackBar(ft.Text("No file selected."))
            self.page.snack_bar.open = True
            self.page.update()
    
    def save_with_name(self, animal_name: str) -> Optional[str]:
        """Save the pending image to FileStore with the animal's name.
        
        Call this when submitting the form (after animal name is known).
        
        Args:
            animal_name: The animal's name to use in the filename
            
        Returns:
            The saved filename, or None if no image pending
        """
        if not hasattr(self, '_pending_image_bytes') or not self._pending_image_bytes:
            # No new image selected, return existing filename if any
            return self._photo_filename
        
        try:
            # Save to FileStore with custom name
            filename = self.file_store.save_bytes(
                self._pending_image_bytes,
                original_name=self._original_filename or "photo.jpg",
                validate=True,
                custom_name=animal_name
            )
            
            self._photo_filename = filename
            self._pending_image_bytes = None  # Clear pending data
            return filename
            
        except FileStoreError as ex:
            print(f"[ERROR] Failed to save photo: {ex}")
            return None
    
    def get_photo_filename(self) -> Optional[str]:
        """Get the filename of the uploaded photo."""
        return self._photo_filename
    
    def get_photo_base64(self) -> Optional[str]:
        """Get the current photo data as base64 string."""
        return self._photo_base64
    
    def build(self) -> object:
        """Build and return the photo upload widget."""
        return ft.Container(
            ft.Column([
                self.photo_display,
                ft.ElevatedButton(
                    "+ Add Photo",
                    on_click=lambda e: self.file_picker.pick_files(
                        allowed_extensions=["jpg", "jpeg", "png", "gif"],
                        dialog_title="Select Animal Photo"
                    ),
                    style=ft.ButtonStyle(
                        bgcolor=ft.Colors.WHITE,
                        color=ft.Colors.BLACK54,
                        shape=ft.RoundedRectangleBorder(radius=20),
                        side=ft.BorderSide(1, ft.Colors.GREY_400),
                        padding=ft.padding.symmetric(horizontal=20, vertical=8),
                    )
                ),
            ], horizontal_alignment="center", spacing=10),
            padding=ft.padding.only(bottom=15),
        )


def create_photo_upload_widget(
    page: object,
    initial_photo: Optional[str] = None,
    width: int = 100,
    height: int = 100
) -> PhotoUploadWidget:
    """Factory function to create a photo upload widget."""
    return PhotoUploadWidget(page, initial_photo, width, height)


# Keep backward compatibility alias
def create_photo_upload_widget_legacy(
    page: object,
    initial_photo_base64: Optional[str] = None,
    width: int = 100,
    height: int = 100
) -> PhotoUploadWidget:
    """Legacy factory function (backward compatible parameter name)."""
    return PhotoUploadWidget(page, initial_photo_base64, width, height)
