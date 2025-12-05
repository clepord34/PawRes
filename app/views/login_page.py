"""Login page with email/phone and password authentication."""
from __future__ import annotations

from typing import Optional

from services.auth_service import AuthService, AuthResult
from services.google_auth_service import GoogleAuthService
from state import get_app_state
import app_config
from components import (
    create_header, create_gradient_background, create_action_button,
    create_form_text_field, show_snackbar, create_error_dialog, create_info_dialog
)


class LoginPage:
    """Login page with email/phone and password plus Google OAuth support."""

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

        # Email/Phone field with icon - Enter key moves to password field
        self._email_field = create_form_text_field(
            hint_text="Enter email or phone number",
            prefix_icon=ft.Icons.CONTACT_MAIL_OUTLINED,
            on_submit=lambda e: self._password_field.focus(),
        )
        
        # Password field with icon - Enter key triggers login
        self._password_field = create_form_text_field(
            hint_text="Enter your password",
            password=True,
            prefix_icon=ft.Icons.LOCK_OUTLINE,
            on_submit=lambda e: self._on_login(page, e),
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
        
        # Emergency Report Button
        emergency_btn = ft.Container(
            ft.ElevatedButton(
                content=ft.Row([
                    ft.Icon(ft.Icons.EMERGENCY, size=18, color=ft.Colors.WHITE),
                    ft.Text("Emergency Report Rescue", size=14, color=ft.Colors.WHITE, weight="w600"),
                ], alignment="center", spacing=8),
                width=280,
                height=48,
                on_click=lambda e: page.go("/emergency_rescue"),
                style=ft.ButtonStyle(
                    bgcolor=ft.Colors.RED_600,
                    color=ft.Colors.WHITE,
                    shape=ft.RoundedRectangleBorder(radius=8),
                    elevation=3,
                )
            ),
            padding=ft.padding.only(top=15),
        )

        # Simple text labels (no icons since they're in the text fields)
        email_label = ft.Text("Email or Phone Number", size=13, weight="w500", color=ft.Colors.BLACK87)
        password_label = ft.Text("Password", size=13, weight="w500", color=ft.Colors.BLACK87)

        # create a centered card/container for the form
        card = ft.Container(
            ft.Column(
                [
                    ft.Text("Login Your Account", size=24, weight="w600", color=ft.Colors.BLACK87),
                    ft.Container(height=25),  # spacing
                    ft.Container(email_label, width=280, alignment=ft.alignment.center_left),
                    ft.Container(height=6),
                    self._email_field,
                    ft.Container(height=15),
                    ft.Container(password_label, width=280, alignment=ft.alignment.center_left),
                    ft.Container(height=6),
                    self._password_field,
                    ft.Container(height=8),
                    login_btn,
                    ft.Container(
                        ft.Row([
                            ft.Container(ft.Divider(color=ft.Colors.GREY_300), expand=True),
                            ft.Text("  or  ", size=12, color=ft.Colors.BLACK45),
                            ft.Container(ft.Divider(color=ft.Colors.GREY_300), expand=True),
                        ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                        width=280,
                        padding=ft.padding.symmetric(vertical=5),
                    ),
                    self._google_btn,
                    signup_link,
                    emergency_btn,
                ],
                horizontal_alignment="center",
                spacing=0,
            ),
            padding=40,
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

        # Scrollable centered layout with gradient background
        layout = ft.Column(
            [header, card],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            expand=True,
            scroll=ft.ScrollMode.AUTO,
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

        email_or_phone = (self._email_field.value or "").strip()
        password = (self._password_field.value or "")

        if not email_or_phone or not password:
            missing = []
            if not email_or_phone:
                missing.append("email or phone number")
            if not password:
                missing.append("password")
            create_info_dialog(
                page,
                title="Missing Information",
                message=f"Please enter your {' and '.join(missing)}.",
                details="All fields are required to log in."
            )
            return

        # Use the new login method that returns result status
        user, result = self.auth.login(email_or_phone, password)
        
        if result == AuthResult.ACCOUNT_LOCKED:
            # Check lockout status to show remaining time
            is_locked, remaining = self.auth.get_lockout_status(email_or_phone)
            if remaining:
                create_error_dialog(
                    page,
                    title="Account Temporarily Locked",
                    message=f"Too many failed login attempts.",
                    details=f"Your account has been locked for security reasons.\n\nPlease try again in {remaining} minute(s)."
                )
            else:
                create_error_dialog(
                    page, 
                    title="Account Locked",
                    message="This account is temporarily locked.",
                    details="Please wait a few minutes before trying again."
                )
            return
        
        if result == AuthResult.ACCOUNT_DISABLED:
            create_error_dialog(
                page,
                title="Account Disabled",
                message="This account has been disabled by an administrator.",
                details="If you believe this is a mistake, please contact the system administrator for assistance."
            )
            return
        
        if not user:
            # Get current attempt count to show warning
            max_attempts = getattr(app_config, 'MAX_FAILED_LOGIN_ATTEMPTS', 5)
            
            attempts = self.auth.get_failed_login_attempts(email_or_phone)
            
            if attempts is not None:
                remaining_attempts = max_attempts - attempts
                
                if remaining_attempts <= 0:
                    # Account just got locked
                    is_locked, remaining_time = self.auth.get_lockout_status(email_or_phone)
                    if remaining_time:
                        create_error_dialog(
                            page,
                            title="Account Locked",
                            message="Too many failed login attempts.",
                            details=f"Your account has been temporarily locked.\n\nPlease try again in {remaining_time} minute(s)."
                        )
                    else:
                        create_error_dialog(
                            page,
                            title="Account Locked",
                            message="This account is temporarily locked.",
                            details="Please wait a few minutes before trying again."
                        )
                    return
                elif remaining_attempts <= 3:
                    # Show warning when 3 or fewer attempts remaining
                    create_info_dialog(
                        page,
                        title="Login Failed",
                        message="Invalid email/phone or password.",
                        details=f"Warning: {remaining_attempts} attempt(s) remaining before your account is temporarily locked.",
                        icon="warning"
                    )
                    return
            
            create_error_dialog(
                page,
                title="Login Failed",
                message="Invalid email/phone or password.",
                details="Please check your credentials and try again."
            )
            return

        role = user.get("role") or "user"
        user_id = user.get("id")
        user_name = user.get("name")
        email = user.get("email")
        phone = user.get("phone")
        
        # Use centralized state management for login
        # Pass user data as dictionary matching AuthState.login() signature
        app_state = get_app_state()
        app_state.auth.login({
            "id": user_id,
            "email": email,
            "phone": phone,
            "name": user_name,
            "role": role
        })

        # navigate by role using state's redirect logic
        redirect_route = app_state.auth.get_redirect_route()
        page.go(redirect_route)

    def _on_google(self, page, e) -> None:
        """Handle Google Sign-In button click."""
        try:
            import flet as ft
        except Exception:
            return
        
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
                
                user, result = self.auth.login_oauth(
                    email=email,
                    name=name,
                    oauth_provider="google",
                    profile_picture=picture
                )
                
                if result == AuthResult.OAUTH_CONFLICT:
                    # User exists with password but no OAuth linked
                    # Show dialog asking if they want to link the account
                    def link_account(e):
                        """Link Google account to existing password account."""
                        success, msg = self.auth.link_google_account(user["id"], "google")
                        if success:
                            # Now log them in
                            app_state = get_app_state()
                            app_state.auth.login({
                                "id": user["id"],
                                "email": user.get("email"),
                                "phone": user.get("phone"),
                                "name": user.get("name"),
                                "role": user.get("role", "user"),
                                "profile_picture": user.get("profile_picture"),
                                "oauth_provider": "google",
                            })
                            page.close(dialog)
                            redirect_route = app_state.auth.get_redirect_route()
                            page.go(redirect_route)
                        else:
                            page.close(dialog)
                            show_snackbar(page, msg, error=True)
                    
                    def cancel(e):
                        page.close(dialog)
                        show_snackbar(page, "Google Sign-In cancelled")
                    
                    dialog = ft.AlertDialog(
                        modal=True,
                        title=ft.Text("Account Already Exists", weight="bold"),
                        content=ft.Column([
                            ft.Text(
                                f"An account with email '{email}' already exists with a password.",
                                size=14,
                            ),
                            ft.Container(height=10),
                            ft.Text(
                                "Would you like to link your Google account to this existing account? "
                                "You'll then be able to sign in with either your password or Google.",
                                size=13,
                                color=ft.Colors.GREY_700,
                            ),
                        ], tight=True),
                        actions=[
                            ft.TextButton("Cancel", on_click=cancel),
                            ft.ElevatedButton(
                                "Link Google Account",
                                on_click=link_account,
                                style=ft.ButtonStyle(
                                    bgcolor=ft.Colors.TEAL_600,
                                    color=ft.Colors.WHITE,
                                ),
                            ),
                        ],
                        actions_alignment=ft.MainAxisAlignment.END,
                    )
                    page.open(dialog)
                    return
                
                # Successful OAuth login
                app_state = get_app_state()
                app_state.auth.login({
                    "id": user["id"],
                    "email": user.get("email"),
                    "phone": user.get("phone"),
                    "name": user.get("name"),
                    "role": user.get("role", "user"),
                    "profile_picture": user.get("profile_picture"),
                    "oauth_provider": user.get("oauth_provider"),
                })
                
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


