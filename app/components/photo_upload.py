"""Photo upload widget component."""
from __future__ import annotations
from typing import Optional, TYPE_CHECKING, Callable
import asyncio
import base64
import os
import time
from pathlib import Path
from uuid import uuid4

if TYPE_CHECKING:
    import flet as ft

try:
    import flet as ft
except ImportError:
    ft = None

from storage.file_store import get_file_store, FileStoreError
from services.photo_service import get_photo_service


class PhotoUploadWidget:
    """Reusable photo upload widget with preview."""

    DEBUG_UPLOAD = False
    
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
        
        self._photo_filename: Optional[str] = None
        self._photo_base64: Optional[str] = None
        self._original_filename: Optional[str] = None
        self._upload_targets: dict[str, str] = {}
        self._upload_completed_targets: set[str] = set()
        self._current_web_upload_started_at: float = 0.0
        self._current_web_upload_known_files: set[str] = set()
        self._current_web_source_name: Optional[str] = None
        self._current_web_source_id: Optional[int] = None
        self._current_web_upload_progress_seen: bool = False
        self._current_web_upload_notified: bool = False
        self._pending_image_bytes: Optional[bytes] = None
        
        self.photo_display = self._create_photo_display(initial_photo)
        self._upload_progress = ft.ProgressBar(width=self.width, visible=False, value=0, color=ft.Colors.BLUE)
        
        self.file_picker = ft.FilePicker(on_result=self._on_file_picked, on_upload=self._on_file_upload)        
        page.overlay.append(self.file_picker)
    
    def _load_photo_base64(self, photo: str) -> Optional[str]:
        if not photo:
            return None
        
        if self._photo_service.is_base64(photo):
            self._photo_base64 = photo
            return photo
        
        try:
            self._photo_filename = photo
            self._photo_base64 = self.file_store.read_file_as_base64(photo)
            return self._photo_base64
        except FileStoreError:
            return None

    def _debug_log(self, message: str) -> None:
        if self.DEBUG_UPLOAD:
            print(f"[PhotoUpload] {message}")

    def _create_photo_display(self, initial_photo: Optional[str]) -> object:
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
    
    async def _on_file_picked(self, e: object):
        if e.files and len(e.files) > 0:
            file_info = e.files[0]
            file_path = file_info.path
            self._original_filename = file_info.name
            
            if not file_path:
                import app_config

                uploads_dir = app_config.APP_ROOT / "uploads"
                uploads_dir.mkdir(parents=True, exist_ok=True)
                self._current_web_upload_known_files = {p.name for p in uploads_dir.glob("*") if p.is_file()}
                self._current_web_upload_started_at = time.time()
                self._debug_log(
                    f"pick web file source={file_info.name} file_id={getattr(file_info, 'id', None)} known_files={sorted(self._current_web_upload_known_files)}"
                )

                self._upload_targets.pop(file_info.name, None)
                self._current_web_source_name = file_info.name
                self._current_web_source_id = getattr(file_info, "id", None)
                self._current_web_upload_progress_seen = False
                self._current_web_upload_notified = False
                self.page.run_task(self._start_web_upload, file_info.name, self._current_web_source_id)
                return

            try:
                if not os.path.exists(file_path):
                    raise FileNotFoundError(f"File not found: {file_path}")
                
                with open(file_path, "rb") as image_file:
                    self._pending_image_bytes = image_file.read()

                self._photo_base64 = base64.b64encode(self._pending_image_bytes).decode()
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

    async def _start_web_upload(self, source_name: str, source_id: Optional[int]) -> None:
        await asyncio.sleep(0.35)
        self._debug_log(f"starting deferred upload source={source_name} file_id={source_id}")
        await self._dispatch_web_upload(source_name, source_id, True)
        await self._watch_web_upload(source_name)

    async def _dispatch_web_upload(self, source_name: str, source_id: Optional[int], is_initial_dispatch: bool = False) -> None:
        await asyncio.sleep(0.25 if is_initial_dispatch else 0.05)
        upload_target_name = f"{uuid4().hex}_{source_name}"
        self._upload_targets[source_name] = upload_target_name
        upload_url = self.page.get_upload_url(upload_target_name, 600)
        self._debug_log(f"dispatch source={source_name} file_id={source_id} target={upload_target_name} initial={is_initial_dispatch}")
        self.file_picker.upload(
            [ft.FilePickerUploadFile(source_name, upload_url=upload_url, id=source_id, method="PUT")]
        )

    def _is_uploaded_file_ready(self, file_path: str) -> bool:
        if not os.path.exists(file_path):
            return False
        try:
            return os.path.getsize(file_path) > 0
        except OSError:
            return False

    def _resolve_uploaded_file_path(self, uploads_dir: Path, uploaded_name: str, event_file_name: str) -> str:
        direct_path = str(uploads_dir / uploaded_name)
        if self._is_uploaded_file_ready(direct_path):
            return direct_path

        suffix = f"_{event_file_name}" if event_file_name else ""
        if suffix:
            matches = [
                p for p in uploads_dir.glob(f"*{suffix}")
                if p.is_file()
            ]
            if matches:
                latest = max(matches, key=lambda p: p.stat().st_mtime)
                resolved_path = str(latest)
                if self._is_uploaded_file_ready(resolved_path):
                    return resolved_path

        return direct_path

    def _find_recent_uploaded_file(self, uploads_dir: Path) -> Optional[str]:
        candidates: list[Path] = []
        for file_path in uploads_dir.glob("*"):
            if not file_path.is_file():
                continue
            if not self._is_uploaded_file_ready(str(file_path)):
                continue

            try:
                stat = file_path.stat()
            except OSError:
                continue

            is_new_name = file_path.name not in self._current_web_upload_known_files
            is_recent = stat.st_mtime >= (self._current_web_upload_started_at - 0.2)
            if is_new_name or is_recent:
                candidates.append(file_path)

        if not candidates:
            return None

        latest = max(candidates, key=lambda p: p.stat().st_mtime)
        self._debug_log(f"recent uploaded candidate={latest.name}")
        return str(latest)

    def _finalize_uploaded_file(self, file_path: str, event_file_name: str) -> bool:
        import base64

        target_name = self._upload_targets.get(event_file_name, event_file_name)
        if target_name in self._upload_completed_targets:
            return True

        if not self._is_uploaded_file_ready(file_path):
            return False

        with open(file_path, "rb") as image_file:
            self._pending_image_bytes = image_file.read()

        self._photo_base64 = base64.b64encode(self._pending_image_bytes).decode()
        self._photo_filename = None

        self.photo_display.content = ft.Image(
            src_base64=self._photo_base64,
            width=self.width,
            height=self.height,
            fit=ft.ImageFit.COVER,
            border_radius=8,
        )
        self.photo_display.update()

        self._upload_progress.visible = False
        self._upload_progress.value = 0
        self._upload_progress.update()

        self.update_ai_button_state()

        if self._on_photo_changed:
            self._on_photo_changed()

        if not self._current_web_upload_notified:
            self.page.open(ft.SnackBar(ft.Text(f"Photo uploaded: {self._original_filename}")))
            self.page.update()
            self._current_web_upload_notified = True

        self._upload_completed_targets.add(target_name)
        self._upload_targets.pop(event_file_name, None)
        return True

    async def _watch_web_upload(self, event_file_name: str) -> None:
        import app_config

        deadline = time.time() + 30.0
        uploads_dir = app_config.APP_ROOT / "uploads"

        while time.time() < deadline:
            upload_target_name = self._upload_targets.get(event_file_name, event_file_name)

            if upload_target_name in self._upload_completed_targets:
                return

            file_path = self._resolve_uploaded_file_path(uploads_dir, upload_target_name, event_file_name)
            recent_file_path = self._find_recent_uploaded_file(uploads_dir)
            if recent_file_path:
                file_path = recent_file_path
            try:
                if self._finalize_uploaded_file(file_path, event_file_name):
                    return
            except Exception:
                import traceback
                traceback.print_exc()

            await asyncio.sleep(0.15)

        self._upload_progress.visible = False
        self._upload_progress.value = 0
        self._upload_progress.update()
        self._upload_targets.pop(event_file_name, None)
        self._debug_log(
            f"timeout source={event_file_name} files={[p.name for p in uploads_dir.glob('*') if p.is_file()]}"
        )
        self._current_web_source_name = None
        self._current_web_source_id = None
        self.page.open(ft.SnackBar(ft.Text("Upload timed out. Please try again.")))
        self.page.update()

    async def _on_file_upload(self, e: object):
        event_file_name = getattr(e, "file_name", "")
        target_name = self._upload_targets.get(event_file_name, event_file_name)
        if target_name in self._upload_completed_targets:
            return

        if e.error:
            self._debug_log(f"on_upload error file={getattr(e, 'file_name', None)} error={e.error}")
            if "stream has already been listened to" in str(e.error).lower():
                return
            self.page.open(ft.SnackBar(ft.Text(f"Upload error: {e.error}")))
            self._upload_progress.visible = False
            self.page.update()
            
            return

        self._current_web_upload_progress_seen = True
        if not self._upload_progress.visible:
            self._upload_progress.visible = True
            self._upload_progress.value = None
            self._upload_progress.update()
        self._debug_log(
            f"on_upload event file={getattr(e, 'file_name', None)} progress={getattr(e, 'progress', None)}"
        )

        if e.progress is None or e.progress < 1.0:
            return

        import app_config

        uploaded_name = self._upload_targets.get(event_file_name, event_file_name)
        uploads_dir = app_config.APP_ROOT / "uploads"
        file_path = self._resolve_uploaded_file_path(uploads_dir, uploaded_name, event_file_name)
        recent_file_path = self._find_recent_uploaded_file(uploads_dir)
        if recent_file_path:
            file_path = recent_file_path
        
        try:
            if self._finalize_uploaded_file(file_path, event_file_name):
                self._current_web_source_name = None
                self._current_web_source_id = None
            
            
        except Exception as ex:
            import traceback
            traceback.print_exc()
            return
            

    def save_with_name(self, animal_name: str) -> Optional[str]:
        if not hasattr(self, '_pending_image_bytes') or not self._pending_image_bytes:
            return self._photo_filename
        
        try:
            filename = self.file_store.save_bytes(
                self._pending_image_bytes,
                original_name=self._original_filename or "photo.jpg",
                validate=True,
                custom_name=animal_name
            )
            
            self._photo_filename = filename
            self._pending_image_bytes = None
            return filename
            
        except FileStoreError as ex:
            print(f"[ERROR] Failed to save photo: {ex}")
            return None
    
    def get_photo_filename(self) -> Optional[str]:
        return self._photo_filename
    
    def get_photo_base64(self) -> Optional[str]:
        return self._photo_base64
    
    def has_photo(self) -> bool:
        return self._photo_base64 is not None
    
    def _handle_ai_analyze(self, e):
        if self._on_ai_analyze and self._photo_base64:
            self._on_ai_analyze(self._photo_base64)
    
    def build(self) -> object:
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
                self._upload_progress,
                ft.Row(buttons, spacing=8, alignment=ft.MainAxisAlignment.CENTER),
            ], horizontal_alignment="center", spacing=10),
            padding=ft.padding.only(bottom=15),
        )
    
    def update_ai_button_state(self):
        if hasattr(self, '_ai_button') and self._show_ai_button:
            has_photo = self.has_photo()
            self._ai_button.disabled = not has_photo
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
    return PhotoUploadWidget(
        page, initial_photo, width, height,
        on_ai_analyze=on_ai_analyze,
        show_ai_button=show_ai_button,
        on_photo_changed=on_photo_changed,
    )
