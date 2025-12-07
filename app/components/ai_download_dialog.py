"""AI Model Download Dialog Component.

Shows progress when downloading AI models for the first time.
"""
from __future__ import annotations
from typing import Optional, Callable
import threading


def create_ai_download_dialog(page, on_complete: Optional[Callable] = None):
    """Create and show a dialog for downloading AI models with progress.
    
    Args:
        page: Flet page instance
        on_complete: Optional callback when download completes (receives bool success)
    """
    try:
        import flet as ft
    except Exception as exc:
        raise RuntimeError("Flet must be installed to build the UI") from exc
    
    from services.ai_classification_service import get_ai_classification_service
    
    # Cancellation flag
    cancel_requested = [False]
    download_thread = [None]
    
    progress_bar = ft.ProgressBar(width=400, value=0, color=ft.Colors.PURPLE_600, bgcolor=ft.Colors.PURPLE_100)
    progress_ring = ft.ProgressRing(width=16, height=16, stroke_width=2, color=ft.Colors.PURPLE_600)
    status_text = ft.Text("Preparing to download AI models...", size=14)
    current_step_text = ft.Text("Step 0 of 3", size=12, color=ft.Colors.BLACK54)
    
    # Cancel and Minimize buttons
    cancel_btn = ft.TextButton(
        "Cancel",
        on_click=None,  # Will be set after dialog is created
    )
    
    minimize_btn = ft.TextButton(
        "Minimize",
        on_click=None,  # Will be set after dialog is created
    )
    
    dialog = ft.AlertDialog(
        modal=True,
        title=ft.Row([
            ft.Icon(ft.Icons.DOWNLOAD, color=ft.Colors.PURPLE_600),
            ft.Text("Downloading AI Models", weight=ft.FontWeight.W_600),
        ], spacing=10),
        content=ft.Container(
            ft.Column([
                ft.Text(
                    "PawRes uses AI to automatically identify animal species and breeds. "
                    "This requires downloading 3 models (approx. 1GB total).",
                    size=13,
                    color=ft.Colors.BLACK87,
                ),
                ft.Divider(height=10),
                ft.Row([
                    progress_ring,
                    status_text,
                ], spacing=10, alignment=ft.MainAxisAlignment.START),
                current_step_text,
                progress_bar,
                ft.Text(
                    "This only needs to be done once. Models will be cached locally.",
                    size=11,
                    color=ft.Colors.BLACK54,
                    italic=True,
                ),
                ft.Text(
                    "Note: Cancel will stop after the current file completes.",
                    size=10,
                    color=ft.Colors.ORANGE_700,
                    italic=True,
                ),
            ], spacing=10, tight=True),
            width=450,
            padding=10,
        ),
        actions=[minimize_btn, cancel_btn],
        actions_alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
    )
    
    def cancel_download(e):
        """Cancel the download."""
        cancel_requested[0] = True
        
        # Request cancellation from the service
        service = get_ai_classification_service()
        service.cancel_download()
        
        cancel_btn.disabled = True
        cancel_btn.text = "Cancelling..."
        status_text.value = "Cancellation requested. Waiting for current file to complete..."
        page.update()
        
        # Note: Dialog will stay open until download thread returns
    
    def minimize_dialog(e):
        """Close dialog but continue download in background."""
        page.close(dialog)
        from components import show_snackbar
        
        service = get_ai_classification_service()
        if not service._check_network_connectivity():
            show_snackbar(page, "⚠️ No network connection. Download will retry when connected.", error=True)
        else:
            show_snackbar(page, "Download continuing in background...")
    
    cancel_btn.on_click = cancel_download
    minimize_btn.on_click = minimize_dialog
    
    def progress_callback(current: int, total: int, message: str):
        """Update progress UI."""
        # Always update UI, even during cancellation to show status
        status_text.value = message
        current_step_text.value = f"Step {current} of {total}"
        progress_bar.value = current / total if total > 0 else 0
        page.update()
        
        service = get_ai_classification_service()
        progress_state = service.get_download_progress()
        if progress_state.get("network_restored", False):
            from components import show_snackbar
            show_snackbar(page, "✓ Internet connection restored")
            # Clear the flag so we don't show snackbar repeatedly
            service._download_progress["network_restored"] = False
    
    def download_models_thread_func():
        """Download models in background thread."""
        service = get_ai_classification_service()
        
        if service.is_downloading():
            if service._cancel_requested:
                # Disable cancel button since cancellation is already in progress
                cancel_btn.disabled = True
                cancel_btn.text = "Cancelling..."
            
            progress = service.get_download_progress()
            status_text.value = progress["message"]
            current_step_text.value = f"Step {progress['current_step']} of {progress['total_steps']}"
            progress_bar.value = progress["progress"]
            page.update()
            
            # Poll for updates every 500ms until download completes
            import time
            while service.is_downloading():
                # Don't break on cancel - wait for service to actually stop
                time.sleep(0.5)
                progress = service.get_download_progress()
                status_text.value = progress["message"]
                current_step_text.value = f"Step {progress['current_step']} of {progress['total_steps']}"
                progress_bar.value = progress["progress"]
                page.update()
            
            # Download completed or cancelled (service.is_downloading() is now False)
            page.close(dialog)
            from components import show_snackbar
            if progress["progress"] >= 1.0:
                show_snackbar(page, "AI models downloaded successfully!")
                if on_complete:
                    on_complete(True)
            else:
                # Not complete - must have been cancelled or failed
                show_snackbar(page, "Download cancelled or incomplete", error=True)
                if on_complete:
                    on_complete(False)
            return
        
        download_status = service.get_download_status()
        if all(download_status.values()):
            # Already downloaded
            page.close(dialog)
            from components import show_snackbar
            show_snackbar(page, "AI models already downloaded!")
            if on_complete:
                on_complete(True)
            return
        
        success = service.download_all_models(progress_callback=progress_callback)
        
        # If cancelled, wait a moment for background threads to finish
        if cancel_requested[0]:
            import time
            # Wait for the service to finish cleaning up and release lock
            while service.is_downloading():
                time.sleep(0.1)
            # Give HuggingFace's download thread a moment to fully cleanup
            time.sleep(0.5)
        
        # Close dialog and notify completion
        page.close(dialog)
        
        if cancel_requested[0] or not success:
            from components import show_snackbar
            if cancel_requested[0]:
                show_snackbar(page, "Download cancelled", error=True)
            else:
                show_snackbar(page, "Failed to download AI models. Please check your connection.", error=True)
            if on_complete:
                on_complete(False)
            return
        
        from components import show_snackbar
        show_snackbar(page, "AI models downloaded successfully! Classification enabled.")
        
        if on_complete:
            on_complete(True)
    
    page.open(dialog)
    page.update()
    
    # Start download in background
    download_thread[0] = threading.Thread(target=download_models_thread_func, daemon=True)
    download_thread[0].start()


__all__ = ["create_ai_download_dialog"]
