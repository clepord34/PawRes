"""Login page with email/password authentication."""
from __future__ import annotations

from typing import Optional

from services.auth_service import AuthService
from state import get_app_state
import app_config
from components import (
    create_header, create_form_card, create_gradient_background, create_action_button,
    create_form_text_field, create_form_label, show_snackbar
)


class LoginPage:
    """Responsive login page for mobile/tablet/desktop.

    Example usage in a Flet app:

        import flet as ft
        from pages.login_page import LoginPage

        def main(page: ft.Page):
            login = LoginPage(db_path="app.db")
            login.build(page)

        ft.app(target=main)
    """

    def __init__(self, db_path: Optional[str] = None) -> None:
        # allow injecting a DB path or Database instance via AuthService
        self.auth = AuthService(db_path or app_config.DB_PATH)

        # UI fields will be created when `build()` is called
        self._email_field = None
        self._password_field = None

    def build(self, page) -> None:
        """Build the login UI on the provided `flet.Page` instance."""
        try:
            import flet as ft
        except Exception as exc:  # pragma: no cover - environment may not have flet
            raise RuntimeError("Flet must be installed to build the UI") from exc

        page.title = "Login"

        # Header with logo/title - matching the image design
        header = create_header()

        # Email field with icon
        self._email_field = create_form_text_field(
            hint_text="Enter your email",
            prefix_icon=ft.Icons.EMAIL_OUTLINED,
        )
        
        # Password field with icon
        self._password_field = create_form_text_field(
            hint_text="Enter your password",
            password=True,
            prefix_icon=ft.Icons.LOCK_OUTLINE,
        )

        # Login button - full width teal
        login_btn = ft.Container(
            create_action_button(
                "Login",
                on_click=lambda e: self._on_login(page, e),
                width=280,
                height=45
            ),
            padding=ft.padding.only(top=5, bottom=10),
        )
        
        # Google button - white with border
        google_btn = ft.Container(
            ft.ElevatedButton(
                content=ft.Row([
                    ft.Image(src="https://www.google.com/favicon.ico", width=18, height=18),
                    ft.Text("Google Account", size=14, color=ft.Colors.BLACK87, weight="w500"),
                ], alignment="center", spacing=10),
                width=280,
                height=45,
                on_click=lambda e: self._on_google(page, e),
                style=ft.ButtonStyle(
                    bgcolor=ft.Colors.WHITE,
                    color=ft.Colors.BLACK87,
                    shape=ft.RoundedRectangleBorder(radius=8),
                    side=ft.BorderSide(1, ft.Colors.GREY_400),
                )
            ),
            padding=ft.padding.only(bottom=10),
        )
        
        # Sign up link
        signup_link = ft.Row([
            ft.Text("Don't have an account?", size=13, color=ft.Colors.BLACK54),
            ft.TextButton(
                "Sign Up here", 
                on_click=lambda e: page.go("/signup"),
                style=ft.ButtonStyle(
                    color=ft.Colors.TEAL_600,
                    padding=0,
                )
            )
        ], alignment="center", spacing=5)

        # Label above email field
        email_label = create_form_label("Email Address", icon=ft.Icons.EMAIL)
        
        # Label above password field
        password_label = create_form_label("Password", icon=ft.Icons.LOCK)

        # create a centered card/container for the form
        card = ft.Container(
            ft.Column(
                [
                    ft.Text("Login Your Account", size=24, weight="w600", color=ft.Colors.BLACK87),
                    ft.Container(height=25),  # spacing
                    ft.Container(email_label, width=280, alignment=ft.alignment.center_left),
                    ft.Container(height=8),
                    self._email_field,
                    ft.Container(height=10),
                    ft.Container(password_label, width=280, alignment=ft.alignment.center_left),
                    ft.Container(height=8),
                    self._password_field,
                    login_btn,
                    ft.Text("Log in using your account in:", size=12, color=ft.Colors.BLACK54, text_align="center"),
                    google_btn,
                    signup_link,
                    ft.Container(
                        ft.Text("Login Page", size=13, color=ft.Colors.BLACK45, text_align="center"),
                        padding=ft.padding.only(top=10),
                    ),
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

        # Simple centered layout with gradient background
        layout = ft.Column(
            [header, card],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            expand=True,
        )

        page.controls.clear()
        page.add(create_gradient_background(layout))
        page.update()

    # ---- event handlers ----
    def _on_login(self, page, e) -> None:
        try:
            import flet as ft
        except Exception:
            return

        email = (self._email_field.value or "").strip()
        password = (self._password_field.value or "")

        if not email or not password:
            show_snackbar(page, "Please enter email and password")
            return

        user = self.auth.login(email, password)
        if not user:
            show_snackbar(page, "Invalid email or password")
            return

        role = user.get("role") or "user"
        user_id = user.get("id")
        user_name = user.get("name")
        
        # Use centralized state management for login
        # Pass user data as dictionary matching AuthState.login() signature
        app_state = get_app_state()
        app_state.auth.login({
            "id": user_id,
            "email": email,
            "name": user_name,
            "role": role
        })
        print(f"[DEBUG] User logged in via AppState: ID={user_id}, Email={email}, Role={role}")

        # navigate by role using state's redirect logic
        redirect_route = app_state.auth.get_redirect_route()
        page.go(redirect_route)

    def _on_google(self, page, e) -> None:
        # Placeholder for Google login flow. In a desktop/web Flet app you'd
        # typically open an OAuth flow; here we simply show a message.
        show_snackbar(page, "Google sign-in is not implemented.")


__all__ = ["LoginPage"]


