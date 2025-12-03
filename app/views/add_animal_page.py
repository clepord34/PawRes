"""Form page for adding new animals to the system."""
from __future__ import annotations

import os
import shutil
from typing import Optional

from services.animal_service import AnimalService
from services.import_service import ImportService
import app_config
from components import (
    create_page_header, create_gradient_background, create_animal_form, show_snackbar
)


class AddAnimalPage:
    def __init__(self, db_path: Optional[str] = None) -> None:
        self.db_path = db_path or app_config.DB_PATH
        self.service = AnimalService(self.db_path)
        self.import_service = ImportService(self.db_path)

    def build(self, page) -> None:
        """Build the add animal form on the provided `flet.Page`."""
        try:
            import flet as ft
        except Exception as exc:
            raise RuntimeError("Flet is required") from exc

        page.title = "Add Animal"

        # Header with logo
        header = create_page_header("Paw Rescue")

        def handle_submit(form_data):
            """Handle form submission."""
            try:
                # Save photo with animal name (deferred save)
                photo_filename = None
                photo_widget = form_data.get("photo_widget")
                if photo_widget:
                    photo_filename = photo_widget.save_with_name(form_data["name"])

                # Insert into DB via AnimalService
                animal_id = self.service.add_animal(
                    name=form_data["name"],
                    type=form_data["type"],
                    age=form_data["age"],
                    health_status=form_data["health_status"],
                    photo=photo_filename,
                )

                show_snackbar(page, f"Animal added successfully (ID: {animal_id})")
                page.go("/admin")
            except Exception as exc:
                import traceback
                traceback.print_exc()
                show_snackbar(page, f"Error: {str(exc)}", error=True)

        def handle_cancel():
            """Handle cancel button click."""
            page.go("/admin")

        # =====================================================================
        # Bulk Import Dialog
        # =====================================================================
        
        def show_bulk_import_dialog():
            """Show the bulk import dialog."""
            
            # File picker for import
            def on_import_file_selected(e: ft.FilePickerResultEvent):
                """Handle import file selection."""
                if not e.files or len(e.files) == 0:
                    return
                
                file_path = e.files[0].path
                if not file_path:
                    show_snackbar(page, "Could not access the selected file", error=True)
                    return
                
                # Close the bulk import dialog first
                page.close(bulk_import_dlg)
                
                # Show loading snackbar
                show_snackbar(page, "Importing animals...")
                
                try:
                    # Run import
                    result = self.import_service.import_from_file(file_path)
                    
                    # Show result dialog
                    self._show_import_result_dialog(page, result)
                    
                except Exception as exc:
                    import traceback
                    traceback.print_exc()
                    show_snackbar(page, f"Import error: {str(exc)}", error=True)
            
            file_picker = ft.FilePicker(on_result=on_import_file_selected)
            page.overlay.append(file_picker)
            page.update()
            
            def on_import_click(e):
                """Open file picker for import."""
                file_picker.pick_files(
                    allowed_extensions=["csv", "xlsx", "xls"],
                    dialog_title="Select Import File",
                )
            
            def on_download_csv(e):
                """Download CSV template."""
                csv_path = ImportService.get_csv_template_path()
                if not os.path.exists(csv_path):
                    # Generate template if it doesn't exist
                    if not ImportService.generate_csv_template(csv_path):
                        show_snackbar(page, "Failed to create CSV template", error=True)
                        return
                self._download_template(page, csv_path, "animal_import_template.csv")
            
            def on_download_excel(e):
                """Download Excel template."""
                excel_path = ImportService.get_excel_template_path()
                if not os.path.exists(excel_path):
                    # Generate template if it doesn't exist
                    if not ImportService.generate_excel_template(excel_path):
                        show_snackbar(page, "Failed to create Excel template", error=True)
                        return
                self._download_template(page, excel_path, "animal_import_template.xlsx")
            
            # Template download buttons
            csv_btn = ft.TextButton(
                "CSV",
                icon=ft.Icons.DOWNLOAD,
                on_click=on_download_csv,
                style=ft.ButtonStyle(color=ft.Colors.TEAL_700),
            )
            
            excel_btn = ft.TextButton(
                "Excel",
                icon=ft.Icons.DOWNLOAD,
                on_click=on_download_excel,
                style=ft.ButtonStyle(color=ft.Colors.TEAL_700),
            )
            
            # Import button
            import_btn = ft.ElevatedButton(
                "📁 Select File to Import",
                on_click=on_import_click,
                style=ft.ButtonStyle(
                    bgcolor=ft.Colors.TEAL_600,
                    color=ft.Colors.WHITE,
                    shape=ft.RoundedRectangleBorder(radius=8),
                ),
                width=220,
                height=40,
            )
            
            # Dialog content
            content = ft.Column([
                ft.Text(
                    "Import multiple animals from a CSV or Excel file",
                    size=13,
                    color=ft.Colors.GREY_700,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Row([
                    ft.Text("Download Template:", size=12, color=ft.Colors.GREY_700),
                    csv_btn,
                    excel_btn,
                ], spacing=5, alignment=ft.MainAxisAlignment.CENTER),
                import_btn,
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=12, tight=True)
            
            bulk_import_dlg = ft.AlertDialog(
                title=ft.Row([
                    ft.Icon(ft.Icons.UPLOAD_FILE, color=ft.Colors.TEAL_700, size=24),
                    ft.Text("Bulk Import", size=18, weight="w600", color=ft.Colors.TEAL_700),
                ], spacing=10),
                content=content,
                actions=[
                    ft.TextButton("Cancel", on_click=lambda e: page.close(bulk_import_dlg)),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )
            
            page.open(bulk_import_dlg)

        # Create the animal form using shared component
        animal_form = create_animal_form(
            page=page,
            mode="add",
            on_submit=handle_submit,
            on_cancel=handle_cancel,
            on_bulk_import=show_bulk_import_dialog,
        )

        # Build the form card
        card = animal_form.build()

        # Main layout
        layout = ft.Column([
            header,
            card,
            ft.Container(height=20),  # Bottom padding
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10, scroll=ft.ScrollMode.AUTO)

        page.controls.clear()
        page.add(create_gradient_background(layout))
        page.update()
    
    def _download_template(self, page, src_path: str, filename: str) -> None:
        """Copy template file to a user-accessible location."""
        import flet as ft
        
        def on_save_result(e: ft.FilePickerResultEvent):
            if e.path:
                try:
                    shutil.copy2(src_path, e.path)
                    show_snackbar(page, f"Template saved to: {e.path}")
                except Exception as ex:
                    show_snackbar(page, f"Error saving template: {ex}", error=True)
        
        # Create file picker for save dialog
        save_picker = ft.FilePicker(on_result=on_save_result)
        page.overlay.append(save_picker)
        page.update()
        
        # Open save dialog
        save_picker.save_file(
            file_name=filename,
            allowed_extensions=["csv", "xlsx"] if filename.endswith(".xlsx") else ["csv"],
            dialog_title=f"Save {filename}",
        )
    
    def _show_import_result_dialog(self, page, result) -> None:
        """Show dialog with import results."""
        import flet as ft
        
        if result.success_count == 0 and not result.errors:
            # Empty file
            show_snackbar(page, "No animals found in the file", error=True)
            return
        
        # Build content based on result
        if result.all_failed:
            icon = ft.Icon(ft.Icons.ERROR, color=ft.Colors.RED_600, size=32)
            title = ft.Text("Import Failed", size=16, weight="bold", color=ft.Colors.RED_600)
            summary = ft.Text(f"No animals imported. All {len(result.errors)} rows had errors.", size=12)
        elif result.has_errors:
            icon = ft.Icon(ft.Icons.WARNING, color=ft.Colors.ORANGE_600, size=32)
            title = ft.Text("Completed with Errors", size=16, weight="bold", color=ft.Colors.ORANGE_700)
            summary = ft.Row([
                ft.Text(f"✓ {result.success_count} imported", size=12, color=ft.Colors.GREEN_700),
                ft.Text(f"✗ {len(result.errors)} failed", size=12, color=ft.Colors.RED_600),
            ], spacing=15, alignment=ft.MainAxisAlignment.CENTER)
        else:
            icon = ft.Icon(ft.Icons.CHECK_CIRCLE, color=ft.Colors.GREEN_600, size=32)
            title = ft.Text("Import Successful", size=16, weight="bold", color=ft.Colors.GREEN_700)
            summary = ft.Text(f"Successfully imported {result.success_count} animals!", size=12)
        
        # Error details (if any)
        error_section = None
        if result.errors:
            error_items = []
            for err in result.errors[:5]:  # Show max 5 errors
                error_items.append(
                    ft.Text(f"• Row {err.row}: {err.message}", size=10, color=ft.Colors.RED_700)
                )
            if len(result.errors) > 5:
                error_items.append(
                    ft.Text(f"  ... and {len(result.errors) - 5} more", size=10, color=ft.Colors.GREY_600, italic=True)
                )
            
            error_section = ft.Container(
                ft.Column([
                    ft.Text("Errors:", size=11, weight="w600", color=ft.Colors.RED_700),
                    ft.Column(error_items, spacing=2, scroll=ft.ScrollMode.AUTO, height=80),
                ], spacing=4),
                bgcolor=ft.Colors.RED_50,
                padding=8,
                border_radius=6,
            )
        
        # Build dialog content
        content_items = [icon, title, summary]
        if error_section:
            content_items.append(error_section)
        
        # Action buttons
        actions = []
        if result.success_count > 0:
            actions.append(
                ft.TextButton(
                    "View Animals",
                    on_click=lambda e: (page.close(dlg), page.go("/animals_list?admin=1")),
                )
            )
        actions.append(
            ft.TextButton("OK", on_click=lambda e: page.close(dlg))
        )
        
        dlg = ft.AlertDialog(
            content=ft.Column(content_items, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8, tight=True),
            actions=actions,
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        page.open(dlg)


__all__ = ["AddAnimalPage"]

