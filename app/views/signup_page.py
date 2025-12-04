"""Signup page for new user registration."""
from __future__ import annotations

import base64
from typing import Optional

from services.auth_service import AuthService
from services.password_policy import get_password_policy, validate_password
from storage.file_store import get_file_store
import app_config
from components import (
    create_header, create_action_button, create_gradient_background,
    create_form_text_field, create_form_label, show_snackbar, create_error_dialog
)


class SignupPage:
    """Responsive signup page.

    Builds a responsive form with `name`, `email`, `password`, and
    `confirm password` fields and uses `AuthService.register_user()`.
    """

    def __init__(self, db_path: Optional[str] = None) -> None:
        self.auth = AuthService(db_path or app_config.DB_PATH)
        self.file_store = get_file_store()
        self._name_field = None
        self._email_field = None
        self._password_field = None
        self._confirm_field = None
        self._photo_widget = None
        self._file_picker = None
        self._pending_photo_bytes = None
        self._pending_photo_name = None
        self._page = None

    def build(self, page) -> None:
        """Build the signup UI on the provided `flet.Page` instance."""
        try:
            import flet as ft
        except Exception as exc:  # pragma: no cover
            raise RuntimeError("Flet must be installed to build the UI") from exc

        self._page = page
        page.title = "Sign Up"

        # Header with logo/title
        header = create_header(padding=ft.padding.only(bottom=0),
                               title_size=20,
                               subtitle_size=12,
                               icon_size=55)
        
        # File picker for photo upload
        def on_photo_picked(e):
            if e.files and len(e.files) > 0:
                file_info = e.files[0]
                file_path = file_info.path
                
                if not file_path:
                    show_snackbar(page, "Unable to access file", error=True)
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
                        width=84,
                        height=84,
                        fit=ft.ImageFit.COVER,
                        border_radius=42,
                    )
                    self._photo_widget.update()
                except Exception as ex:
                    show_snackbar(page, f"Error loading photo: {ex}", error=True)
        
        self._file_picker = ft.FilePicker(on_result=on_photo_picked)
        page.overlay.append(self._file_picker)
        
        # Photo display container - default icon with teal border
        self._photo_widget = ft.Container(
            content=ft.Icon(ft.Icons.ACCOUNT_CIRCLE, size=70, color=ft.Colors.GREY_400),
            width=90,
            height=90,
            border_radius=45,
            bgcolor=ft.Colors.GREY_100,
            alignment=ft.alignment.center,
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            border=ft.border.all(3, ft.Colors.TEAL_400),
        )
        
        # Photo upload button
        photo_upload_btn = ft.TextButton(
            "Add Photo",
            icon=ft.Icons.CAMERA_ALT,
            on_click=lambda e: self._file_picker.pick_files(
                allowed_extensions=["jpg", "jpeg", "png", "gif"],
                dialog_title="Select Profile Photo"
            ),
            style=ft.ButtonStyle(
                color=ft.Colors.TEAL_600,
            ),
        )
        
        # Profile photo section
        photo_section = ft.Column([
            self._photo_widget,
            photo_upload_btn,
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2)
        
        # Form fields with icons
        self._name_field = create_form_text_field(
            hint_text="Enter your full name",
            prefix_icon=ft.Icons.PERSON_OUTLINE,
        )
        self._email_field = create_form_text_field(
            hint_text="Enter your email",
            prefix_icon=ft.Icons.EMAIL_OUTLINED,
        )
        self._password_field = create_form_text_field(
            hint_text="Enter your password",
            password=True,
            prefix_icon=ft.Icons.LOCK_OUTLINE,
        )
        self._confirm_field = create_form_text_field(
            hint_text="Confirm your password",
            password=True,
            prefix_icon=ft.Icons.LOCK_OUTLINE,
        )

        # Simple text labels
        name_label = ft.Text("Full Name", size=13, weight="w500", color=ft.Colors.BLACK87)
        email_label = ft.Text("Email Address", size=13, weight="w500", color=ft.Colors.BLACK87)
        password_label = ft.Text("Password", size=13, weight="w500", color=ft.Colors.BLACK87)
        confirm_label = ft.Text("Confirm Password", size=13, weight="w500", color=ft.Colors.BLACK87)
        
        # Password requirements hint
        policy = get_password_policy()
        password_hint = ft.Container(
            ft.Text(
                "8+ chars, uppercase, lowercase, number, special char",
                size=11,
                color=ft.Colors.GREY_600,
                italic=True,
            ),
            width=280,
            alignment=ft.alignment.center_left,
        )

        # Create Account button - teal
        submit_btn = create_action_button(
            "Create Account",
            on_click=lambda e: self._on_submit(page, e),
            width=130,
            height=45
        )

        # Back to Login button - outlined
        back_btn = create_action_button(
            "Back to Login",
            on_click=lambda e: page.go("/"),
            width=130,
            height=45,
            outlined=True,
            bgcolor=ft.Colors.TEAL_600
        )

        card = ft.Container(
            ft.Column(
                [
                    ft.Text("Create Your Account", size=24, weight="w600", color=ft.Colors.BLACK87),
                    ft.Container(height=12),  # spacing
                    photo_section,
                    ft.Container(height=12),  # spacing
                    ft.Container(name_label, width=280, alignment=ft.alignment.center_left),
                    ft.Container(height=4),
                    self._name_field,
                    ft.Container(height=10),
                    ft.Container(email_label, width=280, alignment=ft.alignment.center_left),
                    ft.Container(height=4),
                    self._email_field,
                    ft.Container(height=10),
                    ft.Container(password_label, width=280, alignment=ft.alignment.center_left),
                    ft.Container(height=2),
                    password_hint,
                    ft.Container(height=2),
                    self._password_field,
                    ft.Container(height=10),
                    ft.Container(confirm_label, width=280, alignment=ft.alignment.center_left),
                    ft.Container(height=4),
                    self._confirm_field,
                    ft.Container(height=18),
                    ft.Row([submit_btn, back_btn], alignment="center", spacing=15),
                ],
                horizontal_alignment="center",
                spacing=0,
                scroll=ft.ScrollMode.AUTO,
            ),
            padding=ft.padding.symmetric(horizontal=10, vertical=16),
            alignment=ft.alignment.center,
            width=375,
            bgcolor=ft.Colors.WHITE,
            border_radius=16,
            shadow=ft.BoxShadow(
                blur_radius=30, 
                spread_radius=0, 
                color=ft.Colors.with_opacity(0.15, ft.Colors.BLACK), 
                offset=(0, 8)
            ),
        )

        # Wrap in a scrollable container for the whole page
        scrollable_content = ft.Container(
            ft.Column(
                [header, card],
                alignment=ft.MainAxisAlignment.START,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=20,
            ),
            padding=ft.padding.symmetric(vertical=20),
        )

        layout = ft.Column(
            [scrollable_content],
            alignment=ft.MainAxisAlignment.START,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            expand=True,
            scroll=ft.ScrollMode.AUTO,
        )

        page.controls.clear()
        page.add(create_gradient_background(layout))
        page.update()

    def _on_submit(self, page, e) -> None:
        try:
            import flet as ft
        except Exception:
            return

        name = (self._name_field.value or "").strip()
        email = (self._email_field.value or "").strip()
        password = (self._password_field.value or "")
        confirm = (self._confirm_field.value or "")

        if not name or not email or not password or not confirm:
            show_snackbar(page, "All fields are required")
            return

        if password != confirm:
            show_snackbar(page, "Passwords do not match")
            return

        # Validate password against policy
        is_valid, errors = validate_password(password)
        if not is_valid:
            show_snackbar(page, errors[0])  # Show first validation error
            return

        # Save profile picture if one was selected
        profile_picture_filename = None
        if self._pending_photo_bytes and self._pending_photo_name:
            try:
                # Use email prefix as custom name
                username = email.split("@")[0] if email else "user"
                profile_picture_filename = self.file_store.save_bytes(
                    data=self._pending_photo_bytes,
                    original_name=self._pending_photo_name,
                    validate=False,
                    custom_name=f"profile_{username}"
                )
                print(f"[DEBUG] Saved profile picture: {profile_picture_filename}")
            except Exception as ex:
                print(f"[WARN] Could not save profile picture: {ex}")
                # Continue without profile picture

        try:
            user_id = self.auth.register_user(
                name, email, password, 
                profile_picture=profile_picture_filename
            )
            print(f"[DEBUG] User registered successfully with ID: {user_id}")
        except ValueError as exc:
            print(f"[DEBUG] Registration failed - ValueError: {exc}")
            create_error_dialog(page, title="Registration Failed", message=str(exc))
            return
        except Exception as exc:
            print(f"[DEBUG] Registration failed - Exception: {exc}")
            import traceback
            traceback.print_exc()
            create_error_dialog(page, title="Registration Failed", message="An error occurred during registration. Please try again.")
            return

        # Success: show success message and redirect
        
        # Clear page and show success message
        import time
        
        success_card = ft.Container(
            ft.Column([
                ft.Icon(ft.Icons.CHECK_CIRCLE, size=80, color=ft.Colors.GREEN_600),
                ft.Text("Account Created!", size=32, weight="bold", color=ft.Colors.GREEN_700),
                ft.Text("Your account has been successfully created.", size=16, color=ft.Colors.BLACK87),
                ft.Text("Redirecting to login page...", size=14, color=ft.Colors.BLACK54),
                ft.ProgressRing(color=ft.Colors.TEAL_400),
            ], 
            horizontal_alignment="center", 
            alignment="center",
            spacing=20),
            padding=40,
            alignment=ft.alignment.center,
            width=500,
            bgcolor=ft.Colors.WHITE,
            border_radius=12,
            border=ft.border.all(2, ft.Colors.GREEN_300),
            shadow=ft.BoxShadow(blur_radius=15, spread_radius=3, color=ft.Colors.GREEN_100, offset=(0, 4)),
        )
        
        layout = ft.Column(
            [success_card],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            expand=True,
        )
        
        page.controls.clear()
        page.add(create_gradient_background(layout))
        page.update()        # Wait 2 seconds then redirect
        time.sleep(2)
        page.go("/")


__all__ = ["SignupPage"]

