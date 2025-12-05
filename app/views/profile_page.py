"""Profile page for user self-service profile management."""
from __future__ import annotations

from typing import Optional

from storage.file_store import get_file_store, FileStoreError
from services.user_service import UserService
from services.auth_service import AuthService
from services.password_policy import get_password_policy
from services.photo_service import load_photo
from services.google_auth_service import GoogleAuthService
from state import get_app_state
import app_config
from components import (
    create_action_button,
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
        self.user_service = UserService(self.db_path)
        self.auth_service = AuthService(self.db_path)
        self.google_auth = GoogleAuthService()
        self.file_store = get_file_store()
        self.password_policy = get_password_policy()
        
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
        
        # Load user data through service
        self._user = self.user_service.get_user_profile(user_id)
        
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
        
        # Linked Accounts Card
        linked_accounts_card = self._build_linked_accounts_card()
        
        # Change Password Card
        password_card = self._build_password_card()
        
        # Main content
        content = ft.Container(
            ft.Column([
                header,
                ft.Row([
                    ft.Column([profile_card], expand=1),
                    ft.Column([edit_card, linked_accounts_card, password_card], spacing=20, expand=2),
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
        
        # Check if user uses OAuth and has no password
        is_oauth = bool(self._user.get("oauth_provider"))
        has_password = bool(self._user.get("password_hash"))
        
        # Need to fetch password_hash since get_user_profile doesn't include it
        user_with_password = self.user_service.db.fetch_one(
            "SELECT password_hash FROM users WHERE id = ?",
            (self._user.get("id"),)
        )
        has_password = bool(user_with_password and user_with_password.get("password_hash"))
        
        self._current_password_field = ft.TextField(
            label="Current Password",
            password=True,
            can_reveal_password=True,
            width=300,
            disabled=is_oauth and not has_password,
        )
        
        self._new_password_field = ft.TextField(
            label="New Password",
            password=True,
            can_reveal_password=True,
            width=300,
        )
        
        self._confirm_password_field = ft.TextField(
            label="Confirm New Password",
            password=True,
            can_reveal_password=True,
            width=300,
        )
        
        requirements = ft.Text(
            self.password_policy.get_requirements_text(),
            size=11,
            color=ft.Colors.BLACK54,
        )
        
        content = []
        
        if is_oauth and not has_password:
            # OAuth user without password - show "Set Password" section
            content.extend([
                ft.Text("Set Password", size=18, weight="bold", color=ft.Colors.BLACK87),
                ft.Divider(height=15),
                ft.Container(
                    ft.Row([
                        ft.Icon(ft.Icons.INFO, color=ft.Colors.BLUE_600, size=18),
                        ft.Text(
                            f"You're signed in with {self._user.get('oauth_provider', 'OAuth').title()}. "
                            "Set a password to enable password login.",
                            size=13,
                            color=ft.Colors.BLUE_600,
                        ),
                    ], spacing=10),
                    bgcolor=ft.Colors.BLUE_50,
                    padding=15,
                    border_radius=8,
                ),
                ft.Container(height=10),
                self._new_password_field,
                self._confirm_password_field,
                requirements,
                ft.Container(
                    create_action_button(
                        "Set Password",
                        on_click=lambda e: self._set_password(),
                        width=150,
                    ),
                    padding=ft.padding.only(top=10),
                ),
            ])
        elif is_oauth and has_password:
            # OAuth user with password - show change password
            content.extend([
                ft.Text("Change Password", size=18, weight="bold", color=ft.Colors.BLACK87),
                ft.Divider(height=15),
                ft.Container(
                    ft.Row([
                        ft.Icon(ft.Icons.CHECK_CIRCLE, color=ft.Colors.GREEN_600, size=18),
                        ft.Text(
                            "Password is set. You can sign in with Google or your password.",
                            size=13,
                            color=ft.Colors.GREEN_700,
                        ),
                    ], spacing=10),
                    bgcolor=ft.Colors.GREEN_50,
                    padding=15,
                    border_radius=8,
                ),
                ft.Container(height=10),
                self._current_password_field,
                self._new_password_field,
                self._confirm_password_field,
                requirements,
                ft.Container(
                    create_action_button(
                        "Change Password",
                        on_click=lambda e: self._change_password(),
                        width=180,
                    ),
                    padding=ft.padding.only(top=10),
                ),
            ])
        else:
            # Regular password user - show change password
            content.extend([
                ft.Text("Change Password", size=18, weight="bold", color=ft.Colors.BLACK87),
                ft.Divider(height=15),
                self._current_password_field,
                self._new_password_field,
                self._confirm_password_field,
                requirements,
                ft.Container(
                    create_action_button(
                        "Change Password",
                        on_click=lambda e: self._change_password(),
                        width=180,
                    ),
                    padding=ft.padding.only(top=10),
                ),
            ])
        
        return ft.Container(
            ft.Column(content, spacing=15),
            bgcolor=ft.Colors.with_opacity(0.9, ft.Colors.WHITE),
            border_radius=12,
            padding=25,
            border=ft.border.all(1, ft.Colors.with_opacity(0.1, ft.Colors.BLACK)),
        )
    
    def _build_linked_accounts_card(self) -> object:
        """Build the linked accounts management card."""
        import flet as ft
        
        user = self._user
        has_google = bool(user.get("oauth_provider") == "google")
        google_configured = self.google_auth.is_configured
        
        # Check if user has password (need to fetch since profile doesn't include it)
        user_with_password = self.user_service.db.fetch_one(
            "SELECT password_hash FROM users WHERE id = ?",
            (user.get("id"),)
        )
        has_password = bool(user_with_password and user_with_password.get("password_hash"))
        
        content = [
            ft.Text("Linked Accounts", size=18, weight="bold", color=ft.Colors.BLACK87),
            ft.Divider(height=15),
        ]
        
        # Google Account Row
        if has_google:
            # Google is linked - show unlink option
            google_status = ft.Container(
                ft.Row([
                    ft.Image(src="https://www.google.com/favicon.ico", width=20, height=20),
                    ft.Text("Google Account", size=14, weight="w500"),
                    ft.Container(
                        ft.Text("Connected", size=11, color=ft.Colors.WHITE),
                        bgcolor=ft.Colors.GREEN_600,
                        padding=ft.padding.symmetric(horizontal=8, vertical=2),
                        border_radius=4,
                    ),
                ], spacing=10),
                padding=ft.padding.only(bottom=10),
            )
            content.append(google_status)
            
            if has_password:
                # Can unlink if they have a password
                unlink_btn = ft.OutlinedButton(
                    "Unlink Google Account",
                    icon=ft.Icons.LINK_OFF,
                    on_click=lambda e: self._unlink_google(),
                    style=ft.ButtonStyle(
                        color=ft.Colors.RED_600,
                        side=ft.BorderSide(1, ft.Colors.RED_300),
                    ),
                )
                content.append(unlink_btn)
            else:
                # Can't unlink - no password set - point to Set Password section
                content.append(
                    ft.Container(
                        ft.Row([
                            ft.Icon(ft.Icons.INFO_OUTLINE, color=ft.Colors.AMBER_700, size=16),
                            ft.Text(
                                "Set a password below to enable unlinking",
                                size=12,
                                color=ft.Colors.AMBER_700,
                            ),
                        ], spacing=8),
                        bgcolor=ft.Colors.AMBER_50,
                        padding=10,
                        border_radius=6,
                    )
                )
        else:
            # Google is not linked - show link option
            google_status = ft.Container(
                ft.Row([
                    ft.Image(src="https://www.google.com/favicon.ico", width=20, height=20),
                    ft.Text("Google Account", size=14, weight="w500"),
                    ft.Container(
                        ft.Text("Not Connected", size=11, color=ft.Colors.WHITE),
                        bgcolor=ft.Colors.GREY_500,
                        padding=ft.padding.symmetric(horizontal=8, vertical=2),
                        border_radius=4,
                    ),
                ], spacing=10),
                padding=ft.padding.only(bottom=10),
            )
            content.append(google_status)
            
            if google_configured:
                link_btn = ft.ElevatedButton(
                    content=ft.Row([
                        ft.Image(src="https://www.google.com/favicon.ico", width=16, height=16),
                        ft.Text("Link Google Account", size=13),
                    ], spacing=8),
                    on_click=lambda e: self._link_google(),
                    style=ft.ButtonStyle(
                        bgcolor=ft.Colors.WHITE,
                        color=ft.Colors.BLACK87,
                        side=ft.BorderSide(1, ft.Colors.GREY_400),
                    ),
                )
                content.append(link_btn)
            else:
                content.append(
                    ft.Text(
                        "Google Sign-In is not configured",
                        size=12,
                        color=ft.Colors.GREY_500,
                        italic=True,
                    )
                )
        
        return ft.Container(
            ft.Column(content, spacing=10),
            bgcolor=ft.Colors.with_opacity(0.9, ft.Colors.WHITE),
            border_radius=12,
            padding=25,
            border=ft.border.all(1, ft.Colors.with_opacity(0.1, ft.Colors.BLACK)),
        )
    
    def _link_google(self) -> None:
        """Link Google account to current user."""
        import flet as ft
        
        user_id = self._user.get("id")
        user_email = self._user.get("email")
        
        show_snackbar(self._page, "Opening Google Sign-In... Please check your browser.")
        
        def on_google_complete(user_info):
            """Called when Google Sign-In succeeds."""
            try:
                google_email = user_info.get("email")
                
                # Verify it's the same email as the account
                if user_email and google_email != user_email:
                    show_snackbar(
                        self._page, 
                        f"Google email ({google_email}) doesn't match your account email ({user_email})",
                        error=True
                    )
                    return
                
                # Link the account
                success, msg = self.auth_service.link_google_account(user_id, "google")
                
                if success:
                    # Update app state
                    app_state = get_app_state()
                    app_state.auth.patch_state({"oauth_provider": "google"})
                    
                    show_snackbar(self._page, "Google account linked successfully!")
                    
                    # Refresh the page
                    self.build(self._page)
                else:
                    show_snackbar(self._page, msg, error=True)
                    
            except Exception as ex:
                print(f"[ERROR] Google linking failed: {ex}")
                show_snackbar(self._page, f"Failed to link Google account: {ex}", error=True)
        
        def on_google_error(error_msg):
            """Called when Google Sign-In fails."""
            print(f"[ERROR] Google sign-in failed: {error_msg}")
            show_snackbar(self._page, f"Google Sign-In failed: {error_msg}", error=True)
        
        self.google_auth.sign_in_async(
            on_complete=on_google_complete,
            on_error=on_google_error
        )
    
    def _unlink_google(self) -> None:
        """Unlink Google account from current user."""
        import flet as ft
        
        user_id = self._user.get("id")
        
        def confirm_unlink(e):
            self._page.close(dialog)
            
            success, msg = self.auth_service.unlink_google_account(user_id)
            
            if success:
                # Update app state
                app_state = get_app_state()
                app_state.auth.patch_state({"oauth_provider": None})
                
                show_snackbar(self._page, "Google account unlinked successfully")
                
                # Refresh the page
                self.build(self._page)
            else:
                show_snackbar(self._page, msg, error=True)
        
        def cancel(e):
            self._page.close(dialog)
        
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Unlink Google Account?", weight="bold"),
            content=ft.Text(
                "You will no longer be able to sign in with Google. "
                "You can still sign in using your password.",
                size=14,
            ),
            actions=[
                ft.TextButton("Cancel", on_click=cancel),
                ft.ElevatedButton(
                    "Unlink",
                    on_click=confirm_unlink,
                    style=ft.ButtonStyle(
                        bgcolor=ft.Colors.RED_600,
                        color=ft.Colors.WHITE,
                    ),
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self._page.open(dialog)
    
    def _save_profile(self) -> None:
        """Save profile changes including photo."""
        from services.user_service import UserServiceError
        
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
        
        # Update profile through service
        try:
            self.user_service.update_user_profile(
                user_id=user_id,
                name=name,
                phone=phone,
                profile_picture=photo_filename
            )
        except UserServiceError as ex:
            show_snackbar(self._page, str(ex), error=True)
            return
        
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
        
        user_id = self._user.get("id")
        
        # Use service to change password (handles validation, history, logging)
        result = self.user_service.change_user_password(
            user_id=user_id,
            current_password=current,
            new_password=new_password
        )
        
        if not result.get("success"):
            show_snackbar(self._page, result.get("error", "Failed to change password"), error=True)
            return
        
        # Clear password fields
        self._current_password_field.value = ""
        self._new_password_field.value = ""
        self._confirm_password_field.value = ""
        self._page.update()
        
        show_snackbar(self._page, "Password changed successfully")
    
    def _set_password(self) -> None:
        """Set password for OAuth user."""
        new_password = self._new_password_field.value
        confirm = self._confirm_password_field.value
        
        if not new_password:
            show_snackbar(self._page, "Password is required", error=True)
            return
        
        if new_password != confirm:
            show_snackbar(self._page, "Passwords do not match", error=True)
            return
        
        user_id = self._user.get("id")
        
        # Use service to set password for OAuth user
        result = self.user_service.set_password_for_oauth_user(
            user_id=user_id,
            new_password=new_password
        )
        
        if not result.get("success"):
            show_snackbar(self._page, result.get("error", "Failed to set password"), error=True)
            return
        
        # Clear password fields
        self._new_password_field.value = ""
        self._confirm_password_field.value = ""
        
        show_snackbar(self._page, "Password set successfully! You can now sign in with your password.")
        
        # Refresh the page to show updated UI
        self.build(self._page)


__all__ = ["ProfilePage"]
