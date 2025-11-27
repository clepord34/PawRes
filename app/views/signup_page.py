"""Signup page for new user registration."""
from __future__ import annotations

from typing import Optional

from services.auth_service import AuthService
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
        self._name_field = None
        self._email_field = None
        self._password_field = None
        self._confirm_field = None

    def build(self, page) -> None:
        """Build the signup UI on the provided `flet.Page` instance."""
        try:
            import flet as ft
        except Exception as exc:  # pragma: no cover
            raise RuntimeError("Flet must be installed to build the UI") from exc

        page.title = "Sign Up"

        # Header with logo/title
        header = create_header()        # Name field with label
        name_label = create_form_label("Name")
        self._name_field = create_form_text_field(hint_text="Full Name...")

        # Email field with label
        email_label = create_form_label("Email Address")
        self._email_field = create_form_text_field(hint_text="Email...")

        # Password field with label
        password_label = create_form_label("Password")
        self._password_field = create_form_text_field(hint_text="Password...", password=True)

        # Confirm password field with label
        confirm_label = create_form_label("Confirm Password")
        self._confirm_field = create_form_text_field(hint_text="Confirm Password...", password=True)

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
                    ft.Container(height=25),  # spacing
                    ft.Container(name_label, width=280, alignment=ft.alignment.center_left),
                    ft.Container(height=8),
                    self._name_field,
                    ft.Container(height=10),
                    ft.Container(email_label, width=280, alignment=ft.alignment.center_left),
                    ft.Container(height=8),
                    self._email_field,
                    ft.Container(height=10),
                    ft.Container(password_label, width=280, alignment=ft.alignment.center_left),
                    ft.Container(height=8),
                    self._password_field,
                    ft.Container(height=10),
                    ft.Container(confirm_label, width=280, alignment=ft.alignment.center_left),
                    ft.Container(height=8),
                    self._confirm_field,
                    ft.Container(height=20),
                    ft.Row([submit_btn, back_btn], alignment="center", spacing=15),
                ],
                horizontal_alignment="center",
                spacing=0,
            ),
            padding=35,
            alignment=ft.alignment.center,
            width=400,
            bgcolor=ft.Colors.WHITE,
            border_radius=16,
            shadow=ft.BoxShadow(
                blur_radius=30, 
                spread_radius=0, 
                color=ft.Colors.with_opacity(0.15, ft.Colors.BLACK), 
                offset=(0, 10)
            ),
        )

        layout = ft.Column(
            [header, card],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            expand=True,
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

        if len(password) < 6:
            show_snackbar(page, "Password must be at least 6 characters")
            return

        try:
            user_id = self.auth.register_user(name, email, password)
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

