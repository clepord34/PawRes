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
    
    bgcolor = ft.Colors.RED_700 if error else None
    snackbar = ft.SnackBar(
        ft.Text(message, color=ft.Colors.WHITE if error else None),
        bgcolor=bgcolor,
    )
    page.open(snackbar)


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
        page.close(dialog)
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
    
    page.open(dialog)
    
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
        page.close(dialog)
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
    
    page.open(dialog)
    
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
        page.close(dialog)
        if on_confirm:
            on_confirm()
    
    def handle_cancel(e):
        page.close(dialog)
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
    
    page.open(dialog)
    
    return dialog


__all__ = [
    "show_snackbar",
    "create_error_dialog",
    "create_success_dialog",
    "create_confirmation_dialog",
    "create_archive_dialog",
    "create_remove_dialog",
    "create_permanent_delete_dialog",
    "create_restore_dialog",
]


def create_archive_dialog(
    page,
    item_type: str = "item",
    item_name: str = "",
    on_confirm: Optional[Callable[[str], None]] = None,
    on_cancel: Optional[Callable] = None,
) -> object:
    """Create and show an archive confirmation dialog with optional note.
    
    Archive hides an item from active lists but still counts in analytics.
    User can add an optional note explaining why.
    
    Args:
        page: The Flet page instance
        item_type: Type of item (e.g., "rescue mission", "adoption request", "animal")
        item_name: Name/identifier of the item being archived
        on_confirm: Callback with archive note when confirmed
        on_cancel: Callback when cancelled
    
    Returns:
        The dialog instance
    """
    if ft is None:
        raise RuntimeError("Flet must be installed to create dialogs")
    
    note_field = ft.TextField(
        hint_text="Optional: Add a note explaining why...",
        multiline=True,
        min_lines=2,
        max_lines=3,
        width=300,
        border_color=ft.Colors.GREY_400,
    )
    
    def handle_confirm(e):
        page.close(dialog)
        if on_confirm:
            on_confirm(note_field.value or "")
    
    def handle_cancel(e):
        page.close(dialog)
        if on_cancel:
            on_cancel()
    
    display_name = f' "{item_name}"' if item_name else ""
    
    dialog = ft.AlertDialog(
        modal=True,
        title=ft.Row([
            ft.Icon(ft.Icons.ARCHIVE_OUTLINED, color=ft.Colors.AMBER_700, size=28),
            ft.Text(f"Archive {item_type.title()}", weight=ft.FontWeight.BOLD, color=ft.Colors.AMBER_700),
        ], spacing=8),
        content=ft.Column([
            ft.Text(
                f"Archive{display_name}?",
                size=16,
                text_align=ft.TextAlign.CENTER,
            ),
            ft.Container(height=8),
            ft.Text(
                "• Item will be hidden from active lists\n"
                "• Will still count in analytics/charts\n"
                "• Can be restored anytime",
                size=13,
                color=ft.Colors.GREY_600,
            ),
            ft.Container(height=12),
            note_field,
        ], tight=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
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
                "Archive",
                icon=ft.Icons.ARCHIVE,
                on_click=handle_confirm,
                style=ft.ButtonStyle(
                    bgcolor=ft.Colors.AMBER_700,
                    color=ft.Colors.WHITE,
                    shape=ft.RoundedRectangleBorder(radius=8),
                )
            ),
        ],
        actions_alignment=ft.MainAxisAlignment.CENTER,
    )
    
    page.open(dialog)
    
    return dialog


def create_remove_dialog(
    page,
    item_type: str = "item",
    item_name: str = "",
    on_confirm: Optional[Callable[[str], None]] = None,
    on_cancel: Optional[Callable] = None,
) -> object:
    """Create and show a remove confirmation dialog with required reason.
    
    Remove is for spam, duplicates, test data, etc. Items are hidden and
    DON'T count in analytics. Requires a reason.
    
    Args:
        page: The Flet page instance
        item_type: Type of item (e.g., "rescue mission", "adoption request", "animal")
        item_name: Name/identifier of the item being removed
        on_confirm: Callback with removal reason when confirmed
        on_cancel: Callback when cancelled
    
    Returns:
        The dialog instance
    """
    if ft is None:
        raise RuntimeError("Flet must be installed to create dialogs")
    
    reason_dropdown = ft.Dropdown(
        label="Reason for removal",
        hint_text="Select a reason...",
        width=300,
        options=[
            ft.dropdown.Option("spam", "Spam / Fake"),
            ft.dropdown.Option("duplicate", "Duplicate Entry"),
            ft.dropdown.Option("test", "Test Data"),
            ft.dropdown.Option("invalid", "Invalid / Incorrect"),
            ft.dropdown.Option("other", "Other"),
        ],
        border_color=ft.Colors.GREY_400,
    )
    
    other_reason_field = ft.TextField(
        hint_text="Specify reason...",
        width=300,
        visible=False,
        border_color=ft.Colors.GREY_400,
    )
    
    error_text = ft.Text("", color=ft.Colors.RED_600, size=12, visible=False)
    
    def on_reason_change(e):
        other_reason_field.visible = reason_dropdown.value == "other"
        error_text.visible = False
        page.update()
    
    reason_dropdown.on_change = on_reason_change
    
    def handle_confirm(e):
        if not reason_dropdown.value:
            error_text.value = "Please select a reason"
            error_text.visible = True
            page.update()
            return
        
        if reason_dropdown.value == "other" and not other_reason_field.value:
            error_text.value = "Please specify the reason"
            error_text.visible = True
            page.update()
            return
        
        reason = other_reason_field.value if reason_dropdown.value == "other" else reason_dropdown.value
        
        page.close(dialog)
        if on_confirm:
            on_confirm(reason)
    
    def handle_cancel(e):
        page.close(dialog)
        if on_cancel:
            on_cancel()
    
    display_name = f' "{item_name}"' if item_name else ""
    
    dialog = ft.AlertDialog(
        modal=True,
        title=ft.Row([
            ft.Icon(ft.Icons.DELETE_OUTLINE, color=ft.Colors.ORANGE_700, size=28),
            ft.Text(f"Remove {item_type.title()}", weight=ft.FontWeight.BOLD, color=ft.Colors.ORANGE_700),
        ], spacing=8),
        content=ft.Column([
            ft.Text(
                f"Remove{display_name}?",
                size=16,
                text_align=ft.TextAlign.CENTER,
            ),
            ft.Container(height=8),
            ft.Text(
                "• Item will be hidden from all lists\n"
                "• Will NOT count in analytics/charts\n"
                "• Can be restored or permanently deleted later",
                size=13,
                color=ft.Colors.GREY_600,
            ),
            ft.Container(height=12),
            reason_dropdown,
            other_reason_field,
            error_text,
        ], tight=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
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
                "Remove",
                icon=ft.Icons.DELETE,
                on_click=handle_confirm,
                style=ft.ButtonStyle(
                    bgcolor=ft.Colors.ORANGE_700,
                    color=ft.Colors.WHITE,
                    shape=ft.RoundedRectangleBorder(radius=8),
                )
            ),
        ],
        actions_alignment=ft.MainAxisAlignment.CENTER,
    )
    
    page.open(dialog)
    
    return dialog


def create_permanent_delete_dialog(
    page,
    item_type: str = "item",
    item_name: str = "",
    on_confirm: Optional[Callable] = None,
    on_cancel: Optional[Callable] = None,
) -> object:
    """Create and show a permanent delete confirmation dialog.
    
    Permanent delete completely removes an item from the database.
    This action cannot be undone. Only available for removed items.
    
    Args:
        page: The Flet page instance
        item_type: Type of item (e.g., "rescue mission", "adoption request", "animal")
        item_name: Name/identifier of the item being deleted
        on_confirm: Callback when confirmed
        on_cancel: Callback when cancelled
    
    Returns:
        The dialog instance
    """
    if ft is None:
        raise RuntimeError("Flet must be installed to create dialogs")
    
    def handle_confirm(e):
        page.close(dialog)
        if on_confirm:
            on_confirm()
    
    def handle_cancel(e):
        page.close(dialog)
        if on_cancel:
            on_cancel()
    
    display_name = f' "{item_name}"' if item_name else ""
    
    dialog = ft.AlertDialog(
        modal=True,
        title=ft.Row([
            ft.Icon(ft.Icons.DELETE_FOREVER, color=ft.Colors.RED_700, size=28),
            ft.Text("Permanent Delete", weight=ft.FontWeight.BOLD, color=ft.Colors.RED_700),
        ], spacing=8),
        content=ft.Column([
            ft.Text(
                f"Permanently delete this {item_type}{display_name}?",
                size=16,
                text_align=ft.TextAlign.CENTER,
            ),
            ft.Container(height=12),
            ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.WARNING_AMBER, color=ft.Colors.RED_700, size=20),
                    ft.Text(
                        "This action CANNOT be undone!",
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.RED_700,
                    ),
                ], spacing=8, alignment=ft.MainAxisAlignment.CENTER),
                padding=12,
                bgcolor=ft.Colors.RED_50,
                border_radius=8,
            ),
            ft.Container(height=8),
            ft.Text(
                "The item and all associated data will be\npermanently removed from the database.",
                size=13,
                color=ft.Colors.GREY_600,
                text_align=ft.TextAlign.CENTER,
            ),
        ], tight=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
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
                "Delete Forever",
                icon=ft.Icons.DELETE_FOREVER,
                on_click=handle_confirm,
                style=ft.ButtonStyle(
                    bgcolor=ft.Colors.RED_700,
                    color=ft.Colors.WHITE,
                    shape=ft.RoundedRectangleBorder(radius=8),
                )
            ),
        ],
        actions_alignment=ft.MainAxisAlignment.CENTER,
    )
    
    page.open(dialog)
    
    return dialog


def create_restore_dialog(
    page,
    item_type: str = "item",
    item_name: str = "",
    previous_status: str = "",
    on_confirm: Optional[Callable] = None,
    on_cancel: Optional[Callable] = None,
) -> object:
    """Create and show a restore confirmation dialog.
    
    Restores an archived or removed item to its previous status.
    
    Args:
        page: The Flet page instance
        item_type: Type of item (e.g., "rescue mission", "adoption request", "animal")
        item_name: Name/identifier of the item being restored
        previous_status: The status the item will be restored to
        on_confirm: Callback when confirmed
        on_cancel: Callback when cancelled
    
    Returns:
        The dialog instance
    """
    if ft is None:
        raise RuntimeError("Flet must be installed to create dialogs")
    
    def handle_confirm(e):
        page.close(dialog)
        if on_confirm:
            on_confirm()
    
    def handle_cancel(e):
        page.close(dialog)
        if on_cancel:
            on_cancel()
    
    display_name = f' "{item_name}"' if item_name else ""
    status_info = f' to "{previous_status}"' if previous_status else ""
    
    dialog = ft.AlertDialog(
        modal=True,
        title=ft.Row([
            ft.Icon(ft.Icons.RESTORE, color=ft.Colors.TEAL_600, size=28),
            ft.Text(f"Restore {item_type.title()}", weight=ft.FontWeight.BOLD, color=ft.Colors.TEAL_600),
        ], spacing=8),
        content=ft.Column([
            ft.Text(
                f"Restore{display_name}{status_info}?",
                size=16,
                text_align=ft.TextAlign.CENTER,
            ),
            ft.Container(height=8),
            ft.Text(
                "• Item will reappear in active lists\n"
                "• Will resume counting in analytics\n"
                "• Previous status will be restored",
                size=13,
                color=ft.Colors.GREY_600,
            ),
        ], tight=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
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
                "Restore",
                icon=ft.Icons.RESTORE,
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
    
    page.open(dialog)
    
    return dialog
