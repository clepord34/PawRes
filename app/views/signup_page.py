"""Signup page for new user registration."""
from __future__ import annotations

from typing import Optional

from services.auth_service import AuthService
import app_config
from components import create_header, create_action_button, create_gradient_background


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
        name_label = ft.Text("Name", size=13, weight="w500", color=ft.Colors.BLACK87)
        self._name_field = ft.TextField(
            hint_text="Full Name...",
            width=280,
            height=50,
            bgcolor=ft.Colors.WHITE,
            border_color=ft.Colors.GREY_300,
            focused_border_color=ft.Colors.TEAL_400,
            text_size=14,
            color=ft.Colors.BLACK,
            content_padding=ft.padding.all(12),
        )

        # Email field with label
        email_label = ft.Text("Email Address", size=13, weight="w500", color=ft.Colors.BLACK87)
        self._email_field = ft.TextField(
            hint_text="Email...",
            width=280,
            height=50,
            bgcolor=ft.Colors.WHITE,
            border_color=ft.Colors.GREY_300,
            focused_border_color=ft.Colors.TEAL_400,
            text_size=14,
            color=ft.Colors.BLACK,
            content_padding=ft.padding.all(12),
        )

        # Password field with label
        password_label = ft.Text("Password", size=13, weight="w500", color=ft.Colors.BLACK87)
        self._password_field = ft.TextField(
            hint_text="Password...",
            password=True, 
            can_reveal_password=True, 
            width=280,
            height=50,
            bgcolor=ft.Colors.WHITE,
            border_color=ft.Colors.GREY_300,
            focused_border_color=ft.Colors.TEAL_400,
            text_size=14,
            color=ft.Colors.BLACK,
            content_padding=ft.padding.all(12),
        )

        # Confirm password field with label
        confirm_label = ft.Text("Confirm Password", size=13, weight="w500", color=ft.Colors.BLACK87)
        self._confirm_field = ft.TextField(
            hint_text="Confirm Password...",
            password=True, 
            can_reveal_password=True, 
            width=280,
            height=50,
            bgcolor=ft.Colors.WHITE,
            border_color=ft.Colors.GREY_300,
            focused_border_color=ft.Colors.TEAL_400,
            text_size=14,
            color=ft.Colors.BLACK,
            content_padding=ft.padding.all(12),
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
            page.snack_bar = ft.SnackBar(ft.Text("All fields are required"))
            page.snack_bar.open = True
            page.update()
            return

        if password != confirm:
            page.snack_bar = ft.SnackBar(ft.Text("Passwords do not match"))
            page.snack_bar.open = True
            page.update()
            return

        if len(password) < 6:
            page.snack_bar = ft.SnackBar(ft.Text("Password must be at least 6 characters"))
            page.snack_bar.open = True
            page.update()
            return

        try:
            user_id = self.auth.register_user(name, email, password)
            print(f"[DEBUG] User registered successfully with ID: {user_id}")
        except ValueError as exc:
            print(f"[DEBUG] Registration failed - ValueError: {exc}")
            
            # Show error dialog for existing email
            def close_error_dialog(e):
                error_dialog.open = False
                page.update()
            
            error_dialog = ft.AlertDialog(
                modal=True,
                title=ft.Text("Registration Failed", weight=ft.FontWeight.BOLD, color=ft.Colors.RED_700),
                content=ft.Text(str(exc), text_align=ft.TextAlign.CENTER),
                actions=[
                    ft.ElevatedButton(
                        "OK",
                        on_click=close_error_dialog,
                        style=ft.ButtonStyle(
                            bgcolor=ft.Colors.RED_400,
                            color=ft.Colors.WHITE,
                            shape=ft.RoundedRectangleBorder(radius=8),
                            side=ft.BorderSide(2, ft.Colors.RED_600),
                        )
                    ),
                ],
                actions_alignment=ft.MainAxisAlignment.CENTER,
            )
            
            page.dialog = error_dialog
            error_dialog.open = True
            page.update()
            return
        except Exception as exc:
            print(f"[DEBUG] Registration failed - Exception: {exc}")
            import traceback
            traceback.print_exc()
            
            # Show generic error dialog
            def close_error_dialog(e):
                error_dialog.open = False
                page.update()
            
            error_dialog = ft.AlertDialog(
                modal=True,
                title=ft.Text("Registration Failed", weight=ft.FontWeight.BOLD, color=ft.Colors.RED_700),
                content=ft.Text("An error occurred during registration. Please try again.", text_align=ft.TextAlign.CENTER),
                actions=[
                    ft.ElevatedButton(
                        "OK",
                        on_click=close_error_dialog,
                        style=ft.ButtonStyle(
                            bgcolor=ft.Colors.RED_400,
                            color=ft.Colors.WHITE,
                            shape=ft.RoundedRectangleBorder(radius=8),
                            side=ft.BorderSide(2, ft.Colors.RED_600),
                        )
                    ),
                ],
                actions_alignment=ft.MainAxisAlignment.CENTER,
            )
            
            page.dialog = error_dialog
            error_dialog.open = True
            page.update()
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

