"""Audit log viewer page for admin security monitoring."""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from datetime import datetime
import csv

from services.logging_service import read_log_entries, LOGS_DIR
import app_config
from components import (
    create_action_button, show_snackbar, create_gradient_background,
    create_page_title, create_section_card, create_scrollable_data_table,
    show_page_loading, finish_page_loading,
)
from components.sidebar import create_admin_sidebar


class AuditLogPage:
    """Admin page for viewing security audit logs.
    
    Features:
    - View auth, admin, and security logs
    - Filter by date range and log level
    - Export logs to CSV
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize the audit log page.
        
        Args:
            db_path: Path to the database file (not used but kept for consistency)
        """
        # UI state
        self._log_type = "security"
        self._level_filter = None
        self._level_value = "all"
        self._entries: List[Dict[str, Any]] = []
        self._log_table = None
        self._table_container = None
        self._page = None
        self._tab_index = 0
    
    def build(self, page) -> None:
        """Build the audit log UI.
        
        Args:
            page: Flet page object
        """
        import flet as ft
        
        self._page = page
        page.title = "Audit Logs"
        
        sidebar = create_admin_sidebar(page, current_route="/audit_logs")
        _gradient_ref = show_page_loading(page, sidebar, "Loading logs...")
        sidebar = create_admin_sidebar(page, current_route="/audit_logs")
        
        # Log type tabs
        log_tabs = ft.Tabs(
            selected_index=self._tab_index,
            animation_duration=300,
            indicator_color=ft.Colors.TEAL_600,
            label_color=ft.Colors.TEAL_700,
            unselected_label_color=ft.Colors.GREY_600,
            tabs=[
                ft.Tab(text="Security", icon=ft.Icons.SECURITY),
                ft.Tab(text="Authentication", icon=ft.Icons.LOGIN),
                ft.Tab(text="Admin Actions", icon=ft.Icons.ADMIN_PANEL_SETTINGS),
            ],
            on_change=lambda e: self._on_tab_change(e.control.selected_index),
        )
        
        # Level filter
        self._level_filter = ft.Dropdown(
            hint_text="Filter by level",
            width=150,
            options=[
                ft.dropdown.Option("all", "All Levels"),
                ft.dropdown.Option("INFO", "Info"),
                ft.dropdown.Option("WARNING", "Warning"),
                ft.dropdown.Option("ERROR", "Error"),
            ],
            value=self._level_value,
            border_radius=8,
            on_change=lambda e: self._on_level_change(e.control.value),
        )
        
        # Refresh button
        refresh_btn = ft.IconButton(
            ft.Icons.REFRESH,
            tooltip="Refresh logs",
            on_click=lambda e: self.build(page),
        )
        
        filter_row = ft.Container(
            ft.Row([
                log_tabs,
                ft.Container(expand=True),
                self._level_filter,
                refresh_btn,
                create_action_button(
                    "Export CSV",
                    on_click=lambda e: self._export_csv(),
                    icon=ft.Icons.DOWNLOAD,
                    width=140
                ),
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.padding.symmetric(vertical=10),
        )
        
        self._build_table()
        
        # Log location info
        log_info = ft.Container(
            ft.Row([
                ft.Icon(ft.Icons.FOLDER, size=16, color=ft.Colors.BLACK54),
                ft.Text(f"Logs stored in: {LOGS_DIR}", size=12, color=ft.Colors.BLACK54),
            ], spacing=10),
            padding=ft.padding.only(top=15),
        )
        
        # Main content
        content_items = [
            create_page_title("Audit Logs"),
            ft.Container(height=10),
            filter_row,
            create_section_card(
                title="Log Entries",
                content=self._log_table,
                show_divider=True,
            ),
            log_info,
            ft.Container(height=30),
        ]
        
        main_content = ft.Container(
            ft.Column(content_items, spacing=0, scroll=ft.ScrollMode.AUTO, horizontal_alignment="center"),
            padding=30,
            expand=True,
        )
        
        # Layout with sidebar
        layout = ft.Row([
            sidebar,
            main_content,
        ], spacing=0, expand=True)
        
        finish_page_loading(page, _gradient_ref, layout)
    
    def _on_tab_change(self, index: int) -> None:
        """Handle log type tab change."""
        log_types = ["security", "auth", "admin"]
        self._log_type = log_types[index]
        self._tab_index = index
        self.build(self._page)
    
    def _on_level_change(self, value: str) -> None:
        """Handle level filter change."""
        self._level_value = value
        self.build(self._page)
    
    def _build_table(self) -> None:
        """Build the log table."""
        import flet as ft
        
        level_filter = None if self._level_value == "all" else self._level_value
        
        self._entries = read_log_entries(
            log_type=self._log_type,
            limit=200,
            level=level_filter
        )
        
        table_rows = []
        for entry in self._entries:
            row_data = self._create_log_row_data(entry)
            table_rows.append(row_data)
        
        table_columns = [
            {"label": "Timestamp", "expand": 2},
            {"label": "Level", "expand": 1},
            {"label": "Event", "expand": 4},
        ]
        
        self._log_table = create_scrollable_data_table(
            columns=table_columns,
            rows=table_rows,
            height=400,
            empty_message="No log entries found. Logs will appear here as security events occur.",
            column_spacing=15,
            heading_row_height=45,
            data_row_height=55,
        )
    
    def _create_log_row_data(self, entry: Dict[str, Any]) -> List[object]:
        """Create table row data for a log entry."""
        import flet as ft
        
        level = entry.get("level", "INFO")
        
        # Level badge color
        level_colors = {
            "INFO": ft.Colors.BLUE_600,
            "WARNING": ft.Colors.ORANGE_600,
            "ERROR": ft.Colors.RED_600,
        }
        level_color = level_colors.get(level, ft.Colors.GREY_600)
        
        level_badge = ft.Container(
            ft.Text(level, size=11, color=ft.Colors.WHITE, weight="bold"),
            bgcolor=level_color,
            padding=ft.padding.symmetric(horizontal=8, vertical=3),
            border_radius=4,
        )
        
        # Parse message for better display
        message = entry.get("message", "")
        
        parts = message.split(" | ", 1)
        if len(parts) >= 1:
            event_type = parts[0]
            details = parts[1] if len(parts) > 1 else ""
            
            message_content = ft.Column([
                ft.Text(event_type, weight="bold", color=ft.Colors.BLACK87, size=12),
                ft.Text(details, color=ft.Colors.BLACK54, size=11) if details else ft.Container(),
            ], spacing=2)
        else:
            message_content = ft.Text(message, color=ft.Colors.BLACK87, size=12)
        
        return [
            ft.Text(entry.get("timestamp", ""), size=11, color=ft.Colors.BLACK54),
            level_badge,
            message_content,
        ]
    
    def _export_csv(self) -> None:
        """Export current logs to CSV."""
        if not self._entries:
            show_snackbar(self._page, "No logs to export", error=True)
            return
        
        try:
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{self._log_type}_logs_{timestamp}.csv"
            filepath = app_config.STORAGE_DIR / "data" / "exports" / filename
            
            # Ensure exports directory exists
            filepath.parent.mkdir(parents=True, exist_ok=True)
            
            # Write CSV
            with open(filepath, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=["timestamp", "level", "message"])
                writer.writeheader()
                for entry in self._entries:
                    writer.writerow({
                        "timestamp": entry.get("timestamp", ""),
                        "level": entry.get("level", ""),
                        "message": entry.get("message", ""),
                    })
            
            show_snackbar(self._page, f"Exported to {filename}")
            
        except Exception as e:
            show_snackbar(self._page, f"Export failed: {e}", error=True)


__all__ = ["AuditLogPage"]
