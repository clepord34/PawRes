"""User management page for admin operations."""
from __future__ import annotations

import csv
from datetime import datetime
from typing import Any, Dict, List, Optional

from services.user_service import UserService, UserServiceError
from services.password_policy import get_password_policy
from state import get_app_state
import app_config
from components import (
    create_action_button,
    show_snackbar, create_gradient_background, create_page_title,
    create_section_card, create_scrollable_data_table, create_stat_card,
    show_page_loading, finish_page_loading,
    is_mobile, create_responsive_layout, responsive_padding,
    create_admin_drawer,
)
from components.sidebar import create_admin_sidebar


class UserManagementPage:
    """Admin page for managing users.
    
    Features:
    - List all users with search/filter
    - Create new users
    - Edit user information
    - Enable/disable users
    - Reset user passwords
    - Delete users
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize the user management page.
        
        Args:
            db_path: Path to the database file
        """
        self.db_path = db_path or app_config.DB_PATH
        self.service = UserService(self.db_path)
        self.password_policy = get_password_policy()
        
        # UI state
        self._users: List[Dict[str, Any]] = []
        self._search_field = None
        self._role_filter = None
        self._include_disabled = None
        self._user_table = None
        self._table_container = None  # Container holding the table for updates
        self._page = None
    
    def build(self, page) -> None:
        """Build the user management UI.
        
        Args:
            page: Flet page object
        """
        import flet as ft
        
        self._page = page
        page.title = "User Management"
        
        app_state = get_app_state()
        
        _mobile = is_mobile(page)
        sidebar = create_admin_sidebar(page, current_route="/user_management")
        drawer = create_admin_drawer(page, current_route="/user_management") if _mobile else None
        _gradient_ref = show_page_loading(page, None if _mobile else sidebar, "Loading users...")
        sidebar = create_admin_sidebar(page, current_route="/user_management")
        
        # Stats row
        stats = self.service.get_user_stats()
        stats_row = ft.ResponsiveRow([
            ft.Container(create_stat_card("Total Users", str(stats["total"]), value_color=ft.Colors.BLUE_600), col={"xs": 6, "md": 3}),
            ft.Container(create_stat_card("Admins", str(stats["admins"]), value_color=ft.Colors.PURPLE_600), col={"xs": 6, "md": 3}),
            ft.Container(create_stat_card("Regular Users", str(stats["users"]), value_color=ft.Colors.GREEN_600), col={"xs": 6, "md": 3}),
            ft.Container(create_stat_card("Disabled", str(stats["disabled"]), value_color=ft.Colors.RED_600), col={"xs": 6, "md": 3}),
        ], spacing=15)
        
        # Search and filter row
        self._search_field = ft.TextField(
            hint_text="Search by name or email...",
            width=250,
            prefix_icon=ft.Icons.SEARCH,
            border_radius=8,
            on_change=lambda e: self._refresh_users(),
        )
        
        self._role_filter = ft.Dropdown(
            hint_text="Filter by role",
            width=140,
            options=[
                ft.dropdown.Option("all", "All Roles"),
                ft.dropdown.Option("admin", "Admin"),
                ft.dropdown.Option("user", "User"),
            ],
            value="all",
            border_radius=8,
            on_change=lambda e: self._refresh_users(),
        )
        
        self._include_disabled = ft.Checkbox(
            label="Show disabled",
            value=True,
            on_change=lambda e: self._refresh_users(),
        )
        
        # Refresh button
        refresh_btn = ft.IconButton(
            ft.Icons.REFRESH,
            tooltip="Refresh list",
            icon_color=ft.Colors.TEAL_600,
            on_click=lambda e: self.build(page),
        )
        
        # Export button
        export_btn = create_action_button(
            "Export",
            on_click=lambda e: self._export_csv(),
            icon=ft.Icons.DOWNLOAD,
            width=110,
        )
        
        filter_row = ft.Container(
            ft.Row([
                self._search_field,
                self._role_filter,
                self._include_disabled,
                ft.Container(expand=True),
                ft.Text(f"{len(self._users)} user(s)", size=13, color=ft.Colors.BLACK54),
                refresh_btn,
                export_btn,
                create_action_button(
                    "Add User",
                    on_click=lambda e: self._show_create_dialog(),
                    icon=ft.Icons.PERSON_ADD,
                    width=130
                ),
            ], spacing=12, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.padding.symmetric(vertical=15),
        )
        
        self._refresh_users()
        
        self._table_container = ft.Container(content=self._user_table)
        
        # Main content
        content_items = [
            create_page_title("User Management"),
            ft.Container(height=10),
            stats_row,
            filter_row,
            create_section_card(
                title="Users",
                content=self._table_container,
                show_divider=True,
            ),
            ft.Container(height=30),
        ]
        
        main_content = ft.Container(
            ft.Column(content_items, spacing=0, scroll=ft.ScrollMode.AUTO, horizontal_alignment="center"),
            padding=responsive_padding(page),
            expand=True,
        )
        
        # Layout with sidebar
        layout = create_responsive_layout(page, sidebar, main_content, drawer, title="User Management")
        
        finish_page_loading(page, _gradient_ref, layout)
    
    def _refresh_users(self) -> None:
        """Refresh the user list based on current filters."""
        import flet as ft
        
        search = self._search_field.value if self._search_field else None
        role = self._role_filter.value if self._role_filter else "all"
        include_disabled = self._include_disabled.value if self._include_disabled else True
        
        role_filter = None if role == "all" else role
        
        self._users = self.service.list_users(
            include_disabled=include_disabled,
            role_filter=role_filter,
            search=search
        )
        
        table_rows = []
        for user in self._users:
            row_data = self._create_user_row_data(user)
            table_rows.append(row_data)
        
        table_columns = [
            {"label": "User", "expand": 2},
            {"label": "Email", "expand": 2},
            {"label": "Role", "expand": 1},
            {"label": "Status", "expand": 1},
            {"label": "Last Login", "expand": 2},
            {"label": "Actions", "expand": 2},
        ]
        
        self._user_table = create_scrollable_data_table(
            columns=table_columns,
            rows=table_rows,
            height=400,
            empty_message="No users found",
            column_spacing=15,
            heading_row_height=45,
            data_row_height=55,
        )
        
        if self._table_container:
            self._table_container.content = self._user_table
        
        if self._page:
            self._page.update()
    
    def _create_user_row_data(self, user: Dict[str, Any]) -> List[object]:
        """Create table row data for a user."""
        import flet as ft
        
        user_id = user.get("id")
        is_disabled = user.get("is_disabled", False)
        is_current_user = get_app_state().auth.user_id == user_id
        
        # Status badge
        if is_disabled:
            status = ft.Container(
                ft.Text("Disabled", size=11, color=ft.Colors.WHITE),
                bgcolor=ft.Colors.RED_600,
                padding=ft.padding.symmetric(horizontal=8, vertical=3),
                border_radius=4,
            )
        else:
            status = ft.Container(
                ft.Text("Active", size=11, color=ft.Colors.WHITE),
                bgcolor=ft.Colors.GREEN_600,
                padding=ft.padding.symmetric(horizontal=8, vertical=3),
                border_radius=4,
            )
        
        # Role badge
        role = user.get("role", "user")
        role_color = ft.Colors.PURPLE_600 if role == "admin" else ft.Colors.BLUE_600
        role_badge = ft.Container(
            ft.Text(role.title(), size=11, color=ft.Colors.WHITE),
            bgcolor=role_color,
            padding=ft.padding.symmetric(horizontal=8, vertical=3),
            border_radius=4,
        )
        
        # Last login
        last_login = user.get("last_login")
        if last_login:
            if isinstance(last_login, str):
                last_login_text = last_login[:16].replace("T", " ")
            else:
                last_login_text = str(last_login)[:16]
        else:
            last_login_text = "Never"
        
        # Action buttons
        actions = ft.Row([
            ft.IconButton(
                ft.Icons.EDIT,
                icon_size=18,
                tooltip="Edit",
                on_click=lambda e, u=user: self._show_edit_dialog(u),
            ),
            ft.IconButton(
                ft.Icons.LOCK_RESET,
                icon_size=18,
                tooltip="Reset Password",
                on_click=lambda e, u=user: self._show_reset_password_dialog(u),
            ),
        ], spacing=0)
        
        if not is_current_user:
            if is_disabled:
                actions.controls.append(
                    ft.IconButton(
                        ft.Icons.CHECK_CIRCLE,
                        icon_size=18,
                        icon_color=ft.Colors.GREEN_600,
                        tooltip="Enable",
                        on_click=lambda e, u=user: self._enable_user(u),
                    )
                )
            else:
                actions.controls.append(
                    ft.IconButton(
                        ft.Icons.BLOCK,
                        icon_size=18,
                        icon_color=ft.Colors.ORANGE_600,
                        tooltip="Disable",
                        on_click=lambda e, u=user: self._disable_user(u),
                    )
                )
            
            actions.controls.append(
                ft.IconButton(
                    ft.Icons.DELETE,
                    icon_size=18,
                    icon_color=ft.Colors.RED_600,
                    tooltip="Delete",
                    on_click=lambda e, u=user: self._show_delete_dialog(u),
                )
            )
        
        return [
            ft.Text(user.get("name", ""), size=12, color=ft.Colors.BLACK87),
            ft.Text(user.get("email", ""), size=12, color=ft.Colors.BLACK54),
            role_badge,
            status,
            ft.Text(last_login_text, size=12, color=ft.Colors.BLACK54),
            actions,
        ]
    
    def _show_create_dialog(self) -> None:
        """Show dialog to create a new user."""
        import flet as ft
        
        name_field = ft.TextField(
            label="Name",
            hint_text="Enter user's name",
            autofocus=True,
        )
        email_field = ft.TextField(
            label="Email",
            hint_text="Enter user's email",
        )
        password_field = ft.TextField(
            label="Password",
            hint_text="Enter password",
            password=True,
            can_reveal_password=True,
        )
        phone_field = ft.TextField(
            label="Phone (optional)",
            hint_text="Enter phone number",
        )
        role_dropdown = ft.Dropdown(
            label="Role",
            options=[
                ft.dropdown.Option("user", "User"),
                ft.dropdown.Option("admin", "Admin"),
            ],
            value="user",
        )
        
        # Password requirements hint
        requirements_text = ft.Text(
            self.password_policy.get_requirements_text(),
            size=11,
            color=ft.Colors.BLACK54,
        )
        
        def on_create(e):
            try:
                admin_id = get_app_state().auth.user_id
                user_id = self.service.create_user(
                    admin_id=admin_id,
                    name=name_field.value,
                    email=email_field.value,
                    password=password_field.value,
                    role=role_dropdown.value,
                    phone=phone_field.value or None,
                )
                self._page.close(dialog)
                show_snackbar(self._page, f"User created successfully (ID: {user_id})")
                self._refresh_users()
            except UserServiceError as ex:
                show_snackbar(self._page, str(ex), color="error")
        
        dialog = ft.AlertDialog(
            title=ft.Text("Create New User"),
            content=ft.Container(
                ft.Column([
                    name_field,
                    email_field,
                    password_field,
                    requirements_text,
                    phone_field,
                    role_dropdown,
                ], spacing=10, tight=True),
                width=400,
            ),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: self._page.close(dialog)),
                ft.ElevatedButton("Create", on_click=on_create),
            ],
        )
        
        self._page.open(dialog)
    
    def _show_edit_dialog(self, user: Dict[str, Any]) -> None:
        """Show dialog to edit a user."""
        import flet as ft
        
        user_id = user.get("id")
        is_current_user = get_app_state().auth.user_id == user_id
        
        name_field = ft.TextField(
            label="Name",
            value=user.get("name", ""),
        )
        email_field = ft.TextField(
            label="Email",
            value=user.get("email", ""),
        )
        phone_field = ft.TextField(
            label="Phone",
            value=user.get("phone", "") or "",
        )
        role_dropdown = ft.Dropdown(
            label="Role",
            options=[
                ft.dropdown.Option("user", "User"),
                ft.dropdown.Option("admin", "Admin"),
            ],
            value=user.get("role", "user"),
            disabled=is_current_user,  # Can't change own role
        )
        
        def on_save(e):
            try:
                admin_id = get_app_state().auth.user_id
                self.service.update_user(
                    admin_id=admin_id,
                    user_id=user_id,
                    name=name_field.value,
                    email=email_field.value,
                    phone=phone_field.value or None,
                    role=role_dropdown.value if not is_current_user else None,
                )
                self._page.close(dialog)
                show_snackbar(self._page, "User updated successfully")
                self._refresh_users()
            except UserServiceError as ex:
                show_snackbar(self._page, str(ex), color="error")
        
        dialog = ft.AlertDialog(
            title=ft.Text(f"Edit User: {user.get('name')}"),
            content=ft.Container(
                ft.Column([
                    name_field,
                    email_field,
                    phone_field,
                    role_dropdown,
                    ft.Text(
                        "Note: You cannot change your own role.",
                        size=11, color=ft.Colors.ORANGE_700
                    ) if is_current_user else ft.Container(),
                ], spacing=10, tight=True),
                width=400,
            ),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: self._page.close(dialog)),
                ft.ElevatedButton("Save", on_click=on_save),
            ],
        )
        
        self._page.open(dialog)
    
    def _show_reset_password_dialog(self, user: Dict[str, Any]) -> None:
        """Show dialog to reset a user's password."""
        import flet as ft
        
        user_id = user.get("id")
        
        password_field = ft.TextField(
            label="New Password",
            hint_text="Enter new password",
            password=True,
            can_reveal_password=True,
        )
        confirm_field = ft.TextField(
            label="Confirm Password",
            hint_text="Confirm new password",
            password=True,
            can_reveal_password=True,
        )
        
        requirements_text = ft.Text(
            self.password_policy.get_requirements_text(),
            size=11,
            color=ft.Colors.BLACK54,
        )
        
        def on_reset(e):
            if password_field.value != confirm_field.value:
                show_snackbar(self._page, "Passwords do not match", color="error")
                return
            
            try:
                admin_id = get_app_state().auth.user_id
                self.service.reset_password(
                    admin_id=admin_id,
                    user_id=user_id,
                    new_password=password_field.value,
                )
                self._page.close(dialog)
                show_snackbar(self._page, "Password reset successfully")
            except UserServiceError as ex:
                show_snackbar(self._page, str(ex), color="error")
        
        dialog = ft.AlertDialog(
            title=ft.Text(f"Reset Password: {user.get('name')}"),
            content=ft.Container(
                ft.Column([
                    password_field,
                    confirm_field,
                    requirements_text,
                ], spacing=10, tight=True),
                width=400,
            ),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: self._page.close(dialog)),
                ft.ElevatedButton("Reset Password", on_click=on_reset),
            ],
        )
        
        self._page.open(dialog)
    
    def _show_delete_dialog(self, user: Dict[str, Any]) -> None:
        """Show confirmation dialog for deleting a user."""
        import flet as ft
        
        user_id = user.get("id")
        
        def on_delete(e):
            try:
                admin_id = get_app_state().auth.user_id
                self.service.delete_user(admin_id, user_id)
                self._page.close(dialog)
                show_snackbar(self._page, "User deleted successfully")
                self._refresh_users()
            except UserServiceError as ex:
                show_snackbar(self._page, str(ex), color="error")
        
        dialog = ft.AlertDialog(
            title=ft.Text("Delete User"),
            content=ft.Column([
                ft.Text(f"Are you sure you want to delete '{user.get('name')}'?"),
                ft.Text("This action cannot be undone.", color=ft.Colors.RED_600, size=12),
                ft.Text("Consider disabling the user instead.", color=ft.Colors.BLACK54, size=12),
            ], spacing=10, tight=True),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: self._page.close(dialog)),
                ft.ElevatedButton(
                    "Delete",
                    on_click=on_delete,
                    style=ft.ButtonStyle(bgcolor=ft.Colors.RED_600, color=ft.Colors.WHITE),
                ),
            ],
        )
        
        self._page.open(dialog)
    
    def _disable_user(self, user: Dict[str, Any]) -> None:
        """Disable a user account."""
        try:
            admin_id = get_app_state().auth.user_id
            self.service.disable_user(admin_id, user.get("id"))
            show_snackbar(self._page, f"User '{user.get('name')}' has been disabled")
            self._refresh_users()
        except UserServiceError as ex:
            show_snackbar(self._page, str(ex), color="error")
    
    def _enable_user(self, user: Dict[str, Any]) -> None:
        """Enable a disabled user account."""
        try:
            admin_id = get_app_state().auth.user_id
            self.service.enable_user(admin_id, user.get("id"))
            show_snackbar(self._page, f"User '{user.get('name')}' has been enabled")
            self._refresh_users()
        except UserServiceError as ex:
            show_snackbar(self._page, str(ex), color="error")
    
    def _export_csv(self) -> None:
        """Export current user list to CSV."""
        if not self._users:
            show_snackbar(self._page, "No users to export", error=True)
            return
        
        try:
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"users_export_{timestamp}.csv"
            filepath = app_config.STORAGE_DIR / "data" / "exports" / filename
            
            # Ensure exports directory exists
            filepath.parent.mkdir(parents=True, exist_ok=True)
            
            # Write CSV
            fieldnames = ["id", "name", "email", "phone", "role", "oauth_provider", "is_disabled", 
                          "failed_login_attempts", "locked_until", "last_login", "last_password_change", 
                          "created_at", "updated_at"]
            with open(filepath, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for user in self._users:
                    writer.writerow({
                        "id": user.get("id", ""),
                        "name": user.get("name", ""),
                        "email": user.get("email", ""),
                        "phone": user.get("phone", ""),
                        "role": user.get("role", ""),
                        "oauth_provider": user.get("oauth_provider", ""),
                        "is_disabled": user.get("is_disabled", False),
                        "failed_login_attempts": user.get("failed_login_attempts", 0),
                        "locked_until": user.get("locked_until", ""),
                        "last_login": user.get("last_login", ""),
                        "last_password_change": user.get("last_password_change", ""),
                        "created_at": user.get("created_at", ""),
                        "updated_at": user.get("updated_at", ""),
                    })
            
            show_snackbar(self._page, f"Exported {len(self._users)} users to {filename}")
            
        except Exception as e:
            show_snackbar(self._page, f"Export failed: {e}", error=True)


__all__ = ["UserManagementPage"]
