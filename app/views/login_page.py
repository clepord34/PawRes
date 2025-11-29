"""Login page with email/password authentication."""
from __future__ import annotations

import threading
from typing import Optional

from services.auth_service import AuthService
from services.google_auth_service import GoogleAuthService
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
        self.google_auth = GoogleAuthService()

        # UI fields will be created when `build()` is called
        self._email_field = None
        self._password_field = None
        self._google_btn = None
        self._page = None

    def build(self, page) -> None:
        """Build the login UI on the provided `flet.Page` instance."""
        try:
            import flet as ft
        except Exception as exc:  # pragma: no cover - environment may not have flet
            raise RuntimeError("Flet must be installed to build the UI") from exc

        self._page = page
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
        # Check if Google OAuth is configured
        google_configured = self.google_auth.is_configured
        self._google_btn = ft.Container(
            ft.ElevatedButton(
                content=ft.Row([
                    ft.Image(src="https://www.google.com/favicon.ico", width=18, height=18),
                    ft.Text("Sign in with Google", size=14, color=ft.Colors.BLACK87 if google_configured else ft.Colors.GREY_400, weight="w500"),
                ], alignment="center", spacing=10),
                width=280,
                height=45,
                on_click=lambda e: self._on_google(page, e),
                disabled=not google_configured,
                style=ft.ButtonStyle(
                    bgcolor=ft.Colors.WHITE,
                    color=ft.Colors.BLACK87,
                    shape=ft.RoundedRectangleBorder(radius=8),
                    side=ft.BorderSide(1, ft.Colors.GREY_400 if google_configured else ft.Colors.GREY_300),
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
                    ft.Text("Or continue with:", size=12, color=ft.Colors.BLACK54, text_align="center"),
                    self._google_btn,
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
        """Handle Google Sign-In button click."""
        if not self.google_auth.is_configured:
            show_snackbar(page, "Google Sign-In not configured. Add GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET to .env")
            return
        
        show_snackbar(page, "Opening Google Sign-In... Please check your browser.")
        
        def on_google_complete(user_info):
            """Called when Google Sign-In succeeds."""
            try:
                # Register/login the user via OAuth
                email = user_info.get("email")
                name = user_info.get("name", email.split("@")[0] if email else "User")
                picture = user_info.get("picture")
                
                user = self.auth.login_oauth(
                    email=email,
                    name=name,
                    oauth_provider="google",
                    profile_picture=picture
                )
                
                # Update app state
                app_state = get_app_state()
                app_state.auth.login({
                    "id": user["id"],
                    "email": user["email"],
                    "name": user["name"],
                    "role": user.get("role", "user"),
                    "profile_picture": user.get("profile_picture"),
                })
                
                print(f"[DEBUG] Google user logged in: {email}")
                
                # Navigate to appropriate dashboard (must be done on main thread)
                redirect_route = app_state.auth.get_redirect_route()
                page.go(redirect_route)
                
            except Exception as ex:
                print(f"[ERROR] Google sign-in processing failed: {ex}")
                show_snackbar(page, f"Sign-in failed: {ex}")
        
        def on_google_error(error_msg):
            """Called when Google Sign-In fails."""
            print(f"[ERROR] Google sign-in failed: {error_msg}")
            show_snackbar(page, f"Google Sign-In failed: {error_msg}")
        
        # Run OAuth flow in background thread to not block UI
        self.google_auth.sign_in_async(
            on_complete=on_google_complete,
            on_error=on_google_error
        )


__all__ = ["LoginPage"]


