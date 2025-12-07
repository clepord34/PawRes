"""Photo upload widget component."""
from __future__ import annotations
from typing import Optional, TYPE_CHECKING, Callable
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
from services.photo_service import get_photo_service


class PhotoUploadWidget:
    """Reusable photo upload widget with preview."""
    
    def __init__(
        self,
        page: object,
        initial_photo: Optional[str] = None,
        width: int = 100,
        height: int = 100,
        on_ai_analyze: Optional[Callable[[str], None]] = None,
        show_ai_button: bool = True,
        on_photo_changed: Optional[Callable[[], None]] = None,
    ):
        """Initialize the photo upload widget.
        
        Args:
            page: Flet page instance
            initial_photo: Initial photo filename or base64 to display
            width: Photo display width
            height: Photo display height
            on_ai_analyze: Callback when AI analyze button is clicked. Receives base64 image data.
            show_ai_button: Whether to show the AI analyze button
            on_photo_changed: Callback when a new photo is selected (to clear AI suggestion)
        """
        if ft is None:
            raise RuntimeError("Flet must be installed to create photo upload widgets")
        
        self.page = page
        self.width = width
        self.height = height
        self.file_store = get_file_store()
        self._photo_service = get_photo_service()
        self._on_ai_analyze = on_ai_analyze
        self._show_ai_button = show_ai_button
        self._on_photo_changed = on_photo_changed
        
        # Track the current photo - can be filename or base64
        self._photo_filename: Optional[str] = None
        self._photo_base64: Optional[str] = None
        self._original_filename: Optional[str] = None  # Track original for cleanup
        self._pending_image_bytes: Optional[bytes] = None  # Pending upload (not saved yet)
        
        self.photo_display = self._create_photo_display(initial_photo)
        
        self.file_picker = ft.FilePicker(on_result=self._on_file_picked)
        page.overlay.append(self.file_picker)
    
    def _load_photo_base64(self, photo: str) -> Optional[str]:
        """Load photo as base64, whether from filename or already base64."""
        if not photo:
            return None
        
        if self._photo_service.is_base64(photo):
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
                self.page.open(ft.SnackBar(ft.Text("Unable to access file. Please try again.")))
                self.page.update()
                return
            
            try:
                if not os.path.exists(file_path):
                    raise FileNotFoundError(f"File not found: {file_path}")
                
                # Read the file and store temporarily
                with open(file_path, "rb") as image_file:
                    self._pending_image_bytes = image_file.read()
                
                self._photo_base64 = base64.b64encode(self._pending_image_bytes).decode()
                
                # Clear any previously saved filename (new image selected)
                self._photo_filename = None
                
                self.photo_display.content = ft.Image(
                    src_base64=self._photo_base64,
                    width=self.width,
                    height=self.height,
                    fit=ft.ImageFit.COVER,
                    border_radius=8,
                )
                self.photo_display.update()
                
                self.update_ai_button_state()
                
                # Notify parent that photo changed (to clear AI suggestion)
                if self._on_photo_changed:
                    self._on_photo_changed()
                
                self.page.open(ft.SnackBar(ft.Text(f"Photo selected: {self._original_filename}")))
                self.page.update()
                
            except FileStoreError as ex:
                self.page.open(ft.SnackBar(ft.Text(f"Upload error: {str(ex)}")))
                self.page.update()
            except Exception as ex:
                import traceback
                traceback.print_exc()
                self.page.open(ft.SnackBar(ft.Text(f"Error loading photo: {str(ex)}")))
                self.page.update()
        else:
            self.page.open(ft.SnackBar(ft.Text("No file selected.")))
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
    
    def has_photo(self) -> bool:
        """Check if a photo is currently selected or uploaded."""
        return self._photo_base64 is not None
    
    def _handle_ai_analyze(self, e):
        """Handle AI analyze button click."""
        if self._on_ai_analyze and self._photo_base64:
            self._on_ai_analyze(self._photo_base64)
    
    def build(self) -> object:
        """Build and return the photo upload widget."""
        buttons = [
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
        ]
        
        if self._show_ai_button:
            from components.ai_suggestion_card import create_ai_analyze_button
            self._ai_button = create_ai_analyze_button(
                on_click=lambda: self._handle_ai_analyze(None),
                disabled=not self.has_photo(),
            )
            buttons.append(self._ai_button)
        
        return ft.Container(
            ft.Column([
                self.photo_display,
                ft.Row(buttons, spacing=8, alignment=ft.MainAxisAlignment.CENTER),
            ], horizontal_alignment="center", spacing=10),
            padding=ft.padding.only(bottom=15),
        )
    
    def update_ai_button_state(self):
        """Update the AI button enabled/disabled state based on photo availability."""
        if hasattr(self, '_ai_button') and self._show_ai_button:
            has_photo = self.has_photo()
            self._ai_button.disabled = not has_photo
            import flet as ft
            self._ai_button.style = ft.ButtonStyle(
                bgcolor=ft.Colors.PURPLE_700 if has_photo else ft.Colors.with_opacity(0.4, ft.Colors.PURPLE_700),
                color=ft.Colors.WHITE if has_photo else ft.Colors.with_opacity(0.6, ft.Colors.WHITE),
            )
            if hasattr(self.page, 'update'):
                self.page.update()


def create_photo_upload_widget(
    page: object,
    initial_photo: Optional[str] = None,
    width: int = 140,
    height: int = 140,
    on_ai_analyze: Optional[Callable[[str], None]] = None,
    show_ai_button: bool = True,
    on_photo_changed: Optional[Callable[[], None]] = None,
) -> PhotoUploadWidget:
    """Factory function to create a photo upload widget.
    
    Args:
        page: Flet page instance
        initial_photo: Initial photo filename or base64 to display
        width: Photo display width
        height: Photo display height
        on_ai_analyze: Callback when AI analyze button is clicked. Receives base64 image data.
        show_ai_button: Whether to show the AI analyze button
        on_photo_changed: Callback when a new photo is selected (to clear AI suggestion)
    """
    return PhotoUploadWidget(
        page, initial_photo, width, height,
        on_ai_analyze=on_ai_analyze,
        show_ai_button=show_ai_button,
        on_photo_changed=on_photo_changed,
    )
