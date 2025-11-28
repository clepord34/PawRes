"""Dialog and notification components."""
from __future__ import annotations
from typing import Callable, Optional

try:
    import flet as ft
except ImportError:
    ft = None


def show_snackbar(page, message: str, error: bool = False) -> None:
    """Show a snackbar notification.
    
    Args:
        page: The Flet page instance
        message: Message to display
        error: Whether this is an error message (red styling)
    """
    if ft is None:
        raise RuntimeError("Flet must be installed to show snackbars")
    
    bgcolor = ft.Colors.RED_400 if error else None
    page.snack_bar = ft.SnackBar(
        ft.Text(message, color=ft.Colors.WHITE if error else None),
        bgcolor=bgcolor,
    )
    page.snack_bar.open = True
    page.update()


def create_error_dialog(
    page,
    title: str = "Error",
    message: str = "An error occurred",
    on_close: Optional[Callable] = None,
) -> object:
    """Create and show an error dialog.
    
    Args:
        page: The Flet page instance
        title: Dialog title
        message: Error message
        on_close: Optional callback when dialog closes
    
    Returns:
        The dialog instance
    """
    if ft is None:
        raise RuntimeError("Flet must be installed to create dialogs")
    
    def close_dialog(e):
        dialog.open = False
        page.update()
        if on_close:
            on_close()
    
    dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text(title, weight=ft.FontWeight.BOLD, color=ft.Colors.RED_700),
        content=ft.Text(message, text_align=ft.TextAlign.CENTER),
        actions=[
            ft.ElevatedButton(
                "OK",
                on_click=close_dialog,
                style=ft.ButtonStyle(
                    bgcolor=ft.Colors.RED_400,
                    color=ft.Colors.WHITE,
                    shape=ft.RoundedRectangleBorder(radius=8),
                )
            ),
        ],
        actions_alignment=ft.MainAxisAlignment.CENTER,
    )
    
    page.dialog = dialog
    dialog.open = True
    page.update()
    
    return dialog


def create_success_dialog(
    page,
    title: str = "Success",
    message: str = "Operation completed successfully",
    on_close: Optional[Callable] = None,
) -> object:
    """Create and show a success dialog.
    
    Args:
        page: The Flet page instance
        title: Dialog title
        message: Success message
        on_close: Optional callback when dialog closes
    
    Returns:
        The dialog instance
    """
    if ft is None:
        raise RuntimeError("Flet must be installed to create dialogs")
    
    def close_dialog(e):
        dialog.open = False
        page.update()
        if on_close:
            on_close()
    
    dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text(title, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_700),
        content=ft.Text(message, text_align=ft.TextAlign.CENTER),
        actions=[
            ft.ElevatedButton(
                "OK",
                on_click=close_dialog,
                style=ft.ButtonStyle(
                    bgcolor=ft.Colors.GREEN_600,
                    color=ft.Colors.WHITE,
                    shape=ft.RoundedRectangleBorder(radius=8),
                )
            ),
        ],
        actions_alignment=ft.MainAxisAlignment.CENTER,
    )
    
    page.dialog = dialog
    dialog.open = True
    page.update()
    
    return dialog


def create_confirmation_dialog(
    page,
    title: str = "Confirm",
    message: str = "Are you sure?",
    on_confirm: Optional[Callable] = None,
    on_cancel: Optional[Callable] = None,
    confirm_text: str = "Yes",
    cancel_text: str = "No",
) -> object:
    """Create and show a confirmation dialog.
    
    Args:
        page: The Flet page instance
        title: Dialog title
        message: Confirmation message
        on_confirm: Callback when confirmed
        on_cancel: Callback when cancelled
        confirm_text: Text for confirm button
        cancel_text: Text for cancel button
    
    Returns:
        The dialog instance
    """
    if ft is None:
        raise RuntimeError("Flet must be installed to create dialogs")
    
    def handle_confirm(e):
        dialog.open = False
        page.update()
        if on_confirm:
            on_confirm()
    
    def handle_cancel(e):
        dialog.open = False
        page.update()
        if on_cancel:
            on_cancel()
    
    dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text(title, weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK87),
        content=ft.Text(message, text_align=ft.TextAlign.CENTER),
        actions=[
            ft.ElevatedButton(
                cancel_text,
                on_click=handle_cancel,
                style=ft.ButtonStyle(
                    bgcolor=ft.Colors.WHITE,
                    color=ft.Colors.GREY_700,
                    shape=ft.RoundedRectangleBorder(radius=8),
                    side=ft.BorderSide(1, ft.Colors.GREY_400),
                )
            ),
            ft.ElevatedButton(
                confirm_text,
                on_click=handle_confirm,
                style=ft.ButtonStyle(
                    bgcolor=ft.Colors.TEAL_600,
                    color=ft.Colors.WHITE,
                    shape=ft.RoundedRectangleBorder(radius=8),
                )
            ),
        ],
        actions_alignment=ft.MainAxisAlignment.CENTER,
    )
    
    page.dialog = dialog
    dialog.open = True
    page.update()
    
    return dialog


def create_delete_confirmation_dialog(
    page,
    item_name: str = "this item",
    on_confirm: Optional[Callable] = None,
    on_cancel: Optional[Callable] = None,
) -> object:
    """Create and show a delete confirmation dialog.
    
    Args:
        page: The Flet page instance
        item_name: Name of item being deleted
        on_confirm: Callback when confirmed
        on_cancel: Callback when cancelled
    
    Returns:
        The dialog instance
    """
    if ft is None:
        raise RuntimeError("Flet must be installed to create dialogs")
    
    dialog = None
    
    def handle_confirm(e):
        nonlocal dialog
        if dialog:
            dialog.open = False
            page.update()
        if on_confirm:
            on_confirm()
    
    def handle_cancel(e):
        nonlocal dialog
        if dialog:
            dialog.open = False
            page.update()
        if on_cancel:
            on_cancel()
    
    dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text("Delete Confirmation", weight=ft.FontWeight.BOLD, color=ft.Colors.RED_700),
        content=ft.Text(
            f"Are you sure you want to delete {item_name}?\nThis action cannot be undone.",
            text_align=ft.TextAlign.CENTER
        ),
        actions=[
            ft.ElevatedButton(
                "Cancel",
                on_click=handle_cancel,
                style=ft.ButtonStyle(
                    bgcolor=ft.Colors.WHITE,
                    color=ft.Colors.GREY_700,
                    shape=ft.RoundedRectangleBorder(radius=8),
                    side=ft.BorderSide(1, ft.Colors.GREY_400),
                )
            ),
            ft.ElevatedButton(
                "Delete",
                on_click=handle_confirm,
                style=ft.ButtonStyle(
                    bgcolor=ft.Colors.RED_600,
                    color=ft.Colors.WHITE,
                    shape=ft.RoundedRectangleBorder(radius=8),
                )
            ),
        ],
        actions_alignment=ft.MainAxisAlignment.CENTER,
    )
    
    # Add dialog to page overlay for Flet 0.21+
    page.overlay.append(dialog)
    dialog.open = True
    page.update()
    
    return dialog


__all__ = [
    "show_snackbar",
    "create_error_dialog",
    "create_success_dialog",
    "create_confirmation_dialog",
    "create_delete_confirmation_dialog",
]
