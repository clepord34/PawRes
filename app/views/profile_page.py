"""Profile page for user self-service profile management."""
from __future__ import annotations

import hashlib
import hmac
import secrets
from typing import Any, Dict, Optional

from storage.database import Database
from storage.file_store import get_file_store, FileStoreError
from services.password_policy import get_password_policy, PasswordHistoryManager
from services.logging_service import get_auth_logger
from services.photo_service import load_photo
from state import get_app_state
import app_config
from components import (
    create_form_text_field, create_action_button,
    show_snackbar, create_gradient_background
)
from components.sidebar import create_admin_sidebar, create_user_sidebar


class ProfilePage:
    """User profile management page.
    
    Features:
    - View current profile info
    - Edit name and phone
    - Change password (with current password verification)
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize the profile page.
        
        Args:
            db_path: Path to the database file
        """
        self.db_path = db_path or app_config.DB_PATH
        self.db = Database(self.db_path)
        self.file_store = get_file_store()
        self.password_policy = get_password_policy()
        self.password_history = PasswordHistoryManager(self.db_path)
        self.auth_logger = get_auth_logger()
        
        # UI fields
        self._name_field = None
        self._phone_field = None
        self._current_password_field = None
        self._new_password_field = None
        self._confirm_password_field = None
        self._page = None
        self._user = None
        self._photo_widget = None
        self._file_picker = None
        self._pending_photo_bytes = None
        self._pending_photo_name = None
    
    def build(self, page) -> None:
        """Build the profile UI.
        
        Args:
            page: Flet page object
        """
        import flet as ft
        
        self._page = page
        page.title = "My Profile"
        
        app_state = get_app_state()
        user_id = app_state.auth.user_id
        
        if not user_id:
            page.go("/")
            return
        
        # Load user data
        self._user = self.db.fetch_one(
            "SELECT id, name, email, phone, role, created_at, last_login, oauth_provider, profile_picture FROM users WHERE id = ?",
            (user_id,)
        )
        
        if not self._user:
            show_snackbar(page, "User not found", error=True)
            page.go("/")
            return
        
        is_admin = app_state.auth.is_admin
        
        # Create appropriate sidebar
        if is_admin:
            sidebar = create_admin_sidebar(page, current_route="/profile")
        else:
            sidebar = create_user_sidebar(page, app_state.auth.user_name, current_route="/profile")
        
        # Header
        header = ft.Container(
            ft.Row([
                ft.Column([
                    ft.Text("My Profile", size=28, weight="bold", color=ft.Colors.BLACK87),
                    ft.Text(
                        f"Manage your account settings",
                        size=14, color=ft.Colors.BLACK54
                    ),
                ], spacing=5),
            ]),
            padding=ft.padding.only(bottom=30),
        )
        
        # Profile Info Card
        profile_card = self._build_profile_card()
        
        # Edit Profile Card
        edit_card = self._build_edit_card()
        
        # Change Password Card
        password_card = self._build_password_card()
        
        # Main content
        content = ft.Container(
            ft.Column([
                header,
                ft.Row([
                    ft.Column([profile_card], expand=1),
                    ft.Column([edit_card, password_card], spacing=20, expand=2),
                ], spacing=20, expand=True, alignment=ft.MainAxisAlignment.START,
                   vertical_alignment=ft.CrossAxisAlignment.START),
            ], spacing=20, scroll=ft.ScrollMode.AUTO, expand=True),
            padding=30,
            expand=True,
        )
        
        # Layout with sidebar
        layout = ft.Row([
            sidebar,
            content,
        ], spacing=0, expand=True)
        
        page.controls.clear()
        page.add(create_gradient_background(layout))
        page.update()
    
    def _build_profile_card(self) -> object:
        """Build the profile info card with photo."""
        import flet as ft
        import base64
        
        user = self._user
        
        # Profile photo - load from filename or base64
        profile_pic = user.get("profile_picture")
        photo_base64 = load_photo(profile_pic) if profile_pic else None
        
        # File picker for photo upload
        def on_photo_picked(e):
            if e.files and len(e.files) > 0:
                file_info = e.files[0]
                file_path = file_info.path
                
                if not file_path:
                    show_snackbar(self._page, "Unable to access file", error=True)
                    return
                
                try:
                    import os
                    if not os.path.exists(file_path):
                        raise FileNotFoundError(f"File not found: {file_path}")
                    
                    # Read file bytes
                    with open(file_path, "rb") as f:
                        self._pending_photo_bytes = f.read()
                    self._pending_photo_name = file_info.name
                    
                    # Update preview
                    photo_b64 = base64.b64encode(self._pending_photo_bytes).decode()
                    self._photo_widget.content = ft.Image(
                        src_base64=photo_b64,
                        width=104,
                        height=104,
                        fit=ft.ImageFit.COVER,
                        border_radius=52,
                    )
                    self._photo_widget.update()
                    show_snackbar(self._page, "Photo selected - click 'Save Changes' to save")
                except Exception as ex:
                    show_snackbar(self._page, f"Error loading photo: {ex}", error=True)
        
        self._file_picker = ft.FilePicker(on_result=on_photo_picked)
        self._page.overlay.append(self._file_picker)
        
        # Photo display container
        if photo_base64:
            photo_content = ft.Image(
                src_base64=photo_base64,
                width=104,
                height=104,
                fit=ft.ImageFit.COVER,
                border_radius=52,
            )
        else:
            photo_content = ft.Icon(ft.Icons.ACCOUNT_CIRCLE, size=90, color=ft.Colors.TEAL_600)
        
        self._photo_widget = ft.Container(
            content=photo_content,
            width=110,
            height=110,
            border_radius=55,
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            border=ft.border.all(3, ft.Colors.TEAL_400),
            bgcolor=ft.Colors.GREY_100,
        )
        
        # Photo upload button
        photo_upload_btn = ft.TextButton(
            "Change Photo",
            icon=ft.Icons.CAMERA_ALT,
            on_click=lambda e: self._file_picker.pick_files(
                allowed_extensions=["jpg", "jpeg", "png", "gif"],
                dialog_title="Select Profile Photo"
            ),
        )
        
        # Role badge
        role = user.get("role", "user")
        role_color = ft.Colors.PURPLE_600 if role == "admin" else ft.Colors.BLUE_600
        role_badge = ft.Container(
            ft.Text(role.title(), size=12, color=ft.Colors.WHITE, weight="bold"),
            bgcolor=role_color,
            padding=ft.padding.symmetric(horizontal=12, vertical=4),
            border_radius=4,
        )
        
        # OAuth badge
        oauth = user.get("oauth_provider")
        auth_method = oauth.title() if oauth else "Password"
        
        # Format dates
        created = user.get("created_at", "")
        if isinstance(created, str) and created:
            created = created[:10]
        
        last_login = user.get("last_login", "")
        if isinstance(last_login, str) and last_login:
            last_login = last_login[:16].replace("T", " ")
        else:
            last_login = "Never"
        
        return ft.Container(
            ft.Column([
                self._photo_widget,
                photo_upload_btn,
                ft.Text(user.get("name", ""), size=20, weight="bold", color=ft.Colors.BLACK87),
                ft.Text(user.get("email", ""), size=14, color=ft.Colors.BLACK54),
                role_badge,
                ft.Divider(height=20),
                self._info_row("Phone", user.get("phone") or "Not set"),
                self._info_row("Auth Method", auth_method),
                self._info_row("Member Since", str(created)),
                self._info_row("Last Login", str(last_login)),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
            bgcolor=ft.Colors.with_opacity(0.9, ft.Colors.WHITE),
            border_radius=12,
            padding=30,
            border=ft.border.all(1, ft.Colors.with_opacity(0.1, ft.Colors.BLACK)),
            width=280,
        )
    
    def _info_row(self, label: str, value: str) -> object:
        """Create an info row."""
        import flet as ft
        
        return ft.Container(
            ft.Row([
                ft.Text(label + ":", size=12, color=ft.Colors.BLACK54, width=100),
                ft.Text(value, size=12, color=ft.Colors.BLACK87),
            ]),
            width=240,
        )
    
    def _build_edit_card(self) -> object:
        """Build the edit profile card."""
        import flet as ft
        
        user = self._user
        
        self._name_field = ft.TextField(
            label="Name",
            value=user.get("name", ""),
            width=300,
        )
        
        self._phone_field = ft.TextField(
            label="Phone",
            value=user.get("phone", "") or "",
            width=300,
        )
        
        email_field = ft.TextField(
            label="Email",
            value=user.get("email", ""),
            width=300,
            disabled=True,
            helper_text="Email cannot be changed",
        )
        
        save_btn = create_action_button(
            "Save Changes",
            on_click=lambda e: self._save_profile(),
            width=150,
        )
        
        return ft.Container(
            ft.Column([
                ft.Text("Edit Profile", size=18, weight="bold", color=ft.Colors.BLACK87),
                ft.Divider(height=15),
                self._name_field,
                email_field,
                self._phone_field,
                ft.Container(save_btn, padding=ft.padding.only(top=10)),
            ], spacing=15),
            bgcolor=ft.Colors.with_opacity(0.9, ft.Colors.WHITE),
            border_radius=12,
            padding=25,
            border=ft.border.all(1, ft.Colors.with_opacity(0.1, ft.Colors.BLACK)),
        )
    
    def _build_password_card(self) -> object:
        """Build the change password card."""
        import flet as ft
        
        # Check if user uses OAuth (can't change password)
        is_oauth = bool(self._user.get("oauth_provider"))
        
        self._current_password_field = ft.TextField(
            label="Current Password",
            password=True,
            can_reveal_password=True,
            width=300,
            disabled=is_oauth,
        )
        
        self._new_password_field = ft.TextField(
            label="New Password",
            password=True,
            can_reveal_password=True,
            width=300,
            disabled=is_oauth,
        )
        
        self._confirm_password_field = ft.TextField(
            label="Confirm New Password",
            password=True,
            can_reveal_password=True,
            width=300,
            disabled=is_oauth,
        )
        
        requirements = ft.Text(
            self.password_policy.get_requirements_text(),
            size=11,
            color=ft.Colors.BLACK54,
        )
        
        change_btn = create_action_button(
            "Change Password",
            on_click=lambda e: self._change_password(),
            width=180,
        )
        
        content = [
            ft.Text("Change Password", size=18, weight="bold", color=ft.Colors.BLACK87),
            ft.Divider(height=15),
        ]
        
        if is_oauth:
            content.append(
                ft.Container(
                    ft.Row([
                        ft.Icon(ft.Icons.INFO, color=ft.Colors.BLUE_600, size=18),
                        ft.Text(
                            f"You're signed in with {self._user.get('oauth_provider', 'OAuth').title()}. "
                            "Password management is not available.",
                            size=13,
                            color=ft.Colors.BLUE_600,
                        ),
                    ], spacing=10),
                    bgcolor=ft.Colors.BLUE_50,
                    padding=15,
                    border_radius=8,
                )
            )
        else:
            content.extend([
                self._current_password_field,
                self._new_password_field,
                self._confirm_password_field,
                requirements,
                ft.Container(change_btn, padding=ft.padding.only(top=10)),
            ])
        
        return ft.Container(
            ft.Column(content, spacing=15),
            bgcolor=ft.Colors.with_opacity(0.9, ft.Colors.WHITE),
            border_radius=12,
            padding=25,
            border=ft.border.all(1, ft.Colors.with_opacity(0.1, ft.Colors.BLACK)),
        )
    
    def _save_profile(self) -> None:
        """Save profile changes including photo."""
        name = self._name_field.value.strip()
        phone = self._phone_field.value.strip() or None
        
        if not name:
            show_snackbar(self._page, "Name is required", error=True)
            return
        
        if len(name) > app_config.MAX_NAME_LENGTH:
            show_snackbar(
                self._page, 
                f"Name must be at most {app_config.MAX_NAME_LENGTH} characters",
                error=True
            )
            return
        
        user_id = self._user.get("id")
        
        # Handle photo upload if there's a pending photo
        photo_filename = None
        if self._pending_photo_bytes:
            try:
                # Save photo with user's name as filename base
                photo_filename = self.file_store.save_bytes(
                    self._pending_photo_bytes,
                    original_name=self._pending_photo_name or "profile.jpg",
                    validate=True,
                    custom_name=f"profile_{user_id}"
                )
                self._pending_photo_bytes = None
                self._pending_photo_name = None
            except FileStoreError as ex:
                show_snackbar(self._page, f"Error saving photo: {ex}", error=True)
                return
        
        # Build update query
        if photo_filename:
            self.db.execute(
                "UPDATE users SET name = ?, phone = ?, profile_picture = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (name, phone, photo_filename, user_id)
            )
        else:
            self.db.execute(
                "UPDATE users SET name = ?, phone = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (name, phone, user_id)
            )
        
        # Update app state
        app_state = get_app_state()
        app_state.auth.update_user_info(name=name)
        
        show_snackbar(self._page, "Profile updated successfully")
        
        # Refresh the page to show updated info
        self.build(self._page)
    
    def _change_password(self) -> None:
        """Change the user's password."""
        current = self._current_password_field.value
        new_password = self._new_password_field.value
        confirm = self._confirm_password_field.value
        
        if not current:
            show_snackbar(self._page, "Current password is required", error=True)
            return
        
        if not new_password:
            show_snackbar(self._page, "New password is required", error=True)
            return
        
        if new_password != confirm:
            show_snackbar(self._page, "Passwords do not match", error=True)
            return
        
        # Validate new password against policy
        is_valid, errors = self.password_policy.validate(new_password)
        if not is_valid:
            show_snackbar(self._page, errors[0], error=True)
            return
        
        user_id = self._user.get("id")
        
        # Verify current password
        user = self.db.fetch_one(
            "SELECT password_hash, password_salt FROM users WHERE id = ?",
            (user_id,)
        )
        
        if not user:
            show_snackbar(self._page, "User not found", error=True)
            return
        
        stored_hash = user.get("password_hash")
        stored_salt = user.get("password_salt")
        
        if not stored_hash or not stored_salt:
            show_snackbar(self._page, "Cannot change password for this account", error=True)
            return
        
        try:
            salt_bytes = bytes.fromhex(stored_salt)
            current_hash = hashlib.pbkdf2_hmac(
                "sha256", current.encode("utf-8"), salt_bytes, app_config.PBKDF2_ITERATIONS
            ).hex()
            
            if not hmac.compare_digest(current_hash, stored_hash):
                show_snackbar(self._page, "Current password is incorrect", error=True)
                return
        except Exception as e:
            show_snackbar(self._page, "Error verifying password", error=True)
            return
        
        # Check password history
        allowed, error = self.password_history.check_reuse(
            user_id, new_password, self.password_policy
        )
        if not allowed:
            show_snackbar(self._page, error, error=True)
            return
        
        # Hash new password
        new_salt = secrets.token_bytes(app_config.SALT_LENGTH)
        new_hash = hashlib.pbkdf2_hmac(
            "sha256", new_password.encode("utf-8"), new_salt, app_config.PBKDF2_ITERATIONS
        ).hex()
        new_salt_hex = new_salt.hex()
        
        # Update password
        self.db.execute(
            """
            UPDATE users SET 
                password_hash = ?, 
                password_salt = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (new_hash, new_salt_hex, user_id)
        )
        
        # Add to password history
        self.password_history.add_to_history(
            user_id, new_hash, new_salt_hex, self.password_policy.history_count
        )
        
        # Log the change
        if self.auth_logger:
            self.auth_logger.log_password_change(user_id, self._user.get("email"))
        
        # Clear password fields
        self._current_password_field.value = ""
        self._new_password_field.value = ""
        self._confirm_password_field.value = ""
        self._page.update()
        
        show_snackbar(self._page, "Password changed successfully")


__all__ = ["ProfilePage"]
