"""Google OAuth 2.0 authentication service for Flet apps.

Implements Google Sign-In using Flet's native OAuth support.
Works seamlessly across Desktop, Web, and Mobile.
"""
from __future__ import annotations

import os
from typing import Any, Callable, Dict, Optional
from urllib.parse import urlparse, urlunparse

import app_config

class GoogleAuthError(Exception):
    """Exception raised for Google Auth errors."""
    pass

class GoogleAuthService:
    """Service to handle Flet integration with Google OAuth."""

    CALLBACK_COMPLETE_PAGE_HTML = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Google Sign-In - PawRes</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
                background: linear-gradient(180deg, #e0f2f1 0%, #e8f5f3 25%, #f5f0e6 75%, #f0e6d3 100%);
            }
            .card {
                background: linear-gradient(180deg, #ffffff 0%, #fffdf8 100%);
                padding: 50px 60px;
                border-radius: 20px;
                text-align: center;
                box-shadow: 0 8px 32px rgba(0, 128, 128, 0.12);
                max-width: 420px;
                width: 92%;
            }
            .logo {
                margin-bottom: 16px;
            }
            .logo svg {
                width: 90px;
                height: 90px;
            }
            .brand-name {
                font-size: 32px;
                font-weight: 700;
                font-style: italic;
                color: #1a1a1a;
                margin-bottom: 6px;
            }
            .brand-tagline {
                font-size: 15px;
                color: #888;
                margin-bottom: 35px;
            }
            .badge {
                display: inline-flex;
                align-items: center;
                justify-content: center;
                width: 64px;
                height: 64px;
                border-radius: 50%;
                margin-bottom: 20px;
            }
            .badge svg {
                width: 34px;
                height: 34px;
            }
            .badge-success {
                background: linear-gradient(135deg, #00897b 0%, #00695c 100%);
                box-shadow: 0 4px 12px rgba(0, 137, 123, 0.3);
            }
            .badge-error {
                background: linear-gradient(135deg, #e53935 0%, #c62828 100%);
                box-shadow: 0 4px 12px rgba(229, 57, 53, 0.3);
            }
            h1 {
                font-size: 26px;
                font-weight: 600;
                margin-bottom: 12px;
            }
            .title-success { color: #00897b; }
            .title-error { color: #e53935; }
            p {
                color: #666;
                font-size: 15px;
                line-height: 1.5;
            }
            .error-detail {
                display: none;
                background: #fff5f5;
                border: 1px solid #ffcdd2;
                border-radius: 8px;
                padding: 12px 16px;
                margin-top: 16px;
                color: #c62828;
                font-size: 13px;
                word-break: break-word;
            }
        </style>
    </head>
    <body>
        <div class="card">
            <div class="logo">
                <svg viewBox="0 0 15 15" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M5 0C3.89543 0 3 0.895431 3 2V3C3 4.10457 3.89543 5 5 5C6.10457 5 7 4.10457 7 3V2C7 0.895431 6.10457 0 5 0Z" fill="#00897b"/>
                    <path d="M10 0C8.89543 0 8 0.895431 8 2V3C8 4.10457 8.89543 5 10 5C11.1046 5 12 4.10457 12 3V2C12 0.895431 11.1046 0 10 0Z" fill="#00897b"/>
                    <path d="M2 5C0.895431 5 0 5.89543 0 7V7.5C0 8.60457 0.895431 9.5 2 9.5C3.10457 9.5 4 8.60457 4 7.5V7C4 5.89543 3.10457 5 2 5Z" fill="#00897b"/>
                    <path d="M13 5C11.8954 5 11 5.89543 11 7V7.5C11 8.60457 11.8954 9.5 13 9.5C14.1046 9.5 15 8.60457 15 7.5V7C15 5.89543 14.1046 5 13 5Z" fill="#00897b"/>
                    <path d="M9.61273 7.77893C8.51793 6.44953 6.48207 6.44953 5.38727 7.77893L2.46943 11.322C1.2614 12.7889 2.30486 15 4.20516 15C4.47668 15 4.74447 14.9368 4.98732 14.8154L5.34699 14.6355C6.70234 13.9578 8.29766 13.9578 9.65301 14.6355L10.0127 14.8154C10.2555 14.9368 10.5233 15 10.7948 15C12.6951 15 13.7386 12.7889 12.5306 11.322L9.61273 7.77893Z" fill="#00897b"/>
                </svg>
            </div>
            <div class="brand-name">Paw Rescue</div>
            <div class="brand-tagline">Management System</div>

            <div id="successBadge" class="badge badge-success">
                <svg viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
                    <polyline points="20 6 9 17 4 12"></polyline>
                </svg>
            </div>
            <div id="errorBadge" class="badge badge-error" style="display: none;">
                <svg viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
                    <line x1="18" y1="6" x2="6" y2="18"></line>
                    <line x1="6" y1="6" x2="18" y2="18"></line>
                </svg>
            </div>

            <h1 id="title" class="title-success">Sign In Successful!</h1>
            <p id="message">You can close this window and return to PawRes.</p>
            <div id="errorDetail" class="error-detail"></div>
        </div>

        <script>
            (function () {
                const params = new URLSearchParams(window.location.search);
                const error = params.get("error_description") || params.get("error");
                if (!error) {
                    return;
                }

                document.getElementById("successBadge").style.display = "none";
                document.getElementById("errorBadge").style.display = "inline-flex";

                const title = document.getElementById("title");
                title.textContent = "Sign In Failed";
                title.className = "title-error";

                document.getElementById("message").textContent = "Please close this window and try again.";

                const detail = document.getElementById("errorDetail");
                detail.textContent = error;
                detail.style.display = "block";
            })();
        </script>
    </body>
    </html>
    """

    @staticmethod
    def _clean_env_url(value: Optional[str]) -> Optional[str]:
        """Return stripped URL or None for empty values."""
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None
    
    def __init__(self) -> None:
        """Initialize the Google Auth service configuration."""
        self.client_id = app_config.get_env("GOOGLE_CLIENT_ID")
        self.client_secret = app_config.get_env("GOOGLE_CLIENT_SECRET")
        self.web_client_id = app_config.get_env("GOOGLE_WEB_CLIENT_ID")
        self.web_client_secret = app_config.get_env("GOOGLE_WEB_CLIENT_SECRET")
        self.desktop_client_id = app_config.get_env("GOOGLE_DESKTOP_CLIENT_ID")
        self.desktop_client_secret = app_config.get_env("GOOGLE_DESKTOP_CLIENT_SECRET")
        redirect_uri = self._clean_env_url(app_config.get_env("GOOGLE_REDIRECT_URL"))
        self.explicit_redirect_uri = redirect_uri
        base_url = self._clean_env_url(app_config.get_env("BASE_URL"))
        self.base_url = None if self._is_trycloudflare_url(base_url) else base_url
        self._provider = None
        self._provider_mode = None

    @property
    def is_configured(self) -> bool:
        """Check if Google OAuth is properly configured."""
        has_default = bool(self.client_id and self.client_secret)
        has_web = bool(self.web_client_id and self.web_client_secret)
        has_desktop = bool(self.desktop_client_id and self.desktop_client_secret)
        return has_default or has_web or has_desktop

    @staticmethod
    def _is_trycloudflare_url(url: Optional[str]) -> bool:
        """Return True when URL host is a temporary trycloudflare domain."""
        if not url:
            return False
        return "trycloudflare.com" in url.lower()

    @staticmethod
    def _normalize_local_redirect(redirect_url: str) -> str:
        """Normalize local callback hosts to localhost for Google OAuth web rules."""
        parsed = urlparse(redirect_url)
        if parsed.scheme not in ("http", "https"):
            return redirect_url
        host = parsed.hostname or ""
        is_local = host in {"127.0.0.1", "0.0.0.0", "localhost"} or host.startswith("192.168.") or host.startswith("10.")
        if not is_local:
            return redirect_url
        normalized_netloc = f"localhost:{parsed.port}" if parsed.port else "localhost"
        return urlunparse((parsed.scheme, normalized_netloc, parsed.path, parsed.params, parsed.query, parsed.fragment))

    @staticmethod
    def _is_local_http_url(url: Optional[str]) -> bool:
        """Return True when URL points to localhost or private LAN host."""
        if not url:
            return False
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return False
        host = parsed.hostname or ""
        return host in {"127.0.0.1", "0.0.0.0", "localhost"} or host.startswith("192.168.") or host.startswith("10.")

    def _select_config(self, page: Optional[Any] = None) -> tuple[str, Optional[str], Optional[str]]:
        """Select OAuth config tuple as (mode, client_id, client_secret)."""
        is_web = bool(getattr(page, "web", False))
        if is_web:
            return (
                "web",
                self.web_client_id or self.client_id,
                self.web_client_secret or self.client_secret,
            )
        return (
            "desktop",
            self.desktop_client_id or self.client_id,
            self.desktop_client_secret or self.client_secret,
        )

    def _resolve_redirect_uri(self, mode: str, page: Optional[Any] = None) -> str:
        """Resolve redirect URI for current mode.

        Flet 0.28.x requires redirect_url for GoogleOAuthProvider.
        """
        page_url = getattr(page, "url", None)

        if not (self.explicit_redirect_uri or self.base_url):
            if mode == "desktop" and isinstance(page_url, str) and page_url.strip() and self._is_local_http_url(page_url):
                parsed = urlparse(page_url)
                page_redirect = urlunparse(
                    (
                        parsed.scheme,
                        parsed.netloc,
                        "/oauth_callback",
                        "",
                        "",
                        "",
                    )
                )
                return self._normalize_local_redirect(page_redirect)

            default_port = "8000" if mode == "web" else "8550"
            port = os.getenv("FLET_SERVER_PORT", default_port)
            return f"http://localhost:{port}/oauth_callback"

        if isinstance(page_url, str) and page_url.strip():
            parsed = urlparse(page_url)
            if parsed.scheme in ("http", "https") and parsed.netloc:
                page_redirect = urlunparse(
                    (
                        parsed.scheme,
                        parsed.netloc,
                        "/oauth_callback",
                        "",
                        "",
                        "",
                    )
                )
                return self._normalize_local_redirect(page_redirect)

        if self.explicit_redirect_uri:
            return self._normalize_local_redirect(self.explicit_redirect_uri)

        if self.base_url and not self._is_trycloudflare_url(self.base_url):
            return self._normalize_local_redirect(f"{self.base_url.rstrip('/')}/oauth_callback")

        default_port = "8000" if mode == "web" else "8550"
        port = os.getenv("FLET_SERVER_PORT", default_port)
        return f"http://localhost:{port}/oauth_callback"

    def get_provider(self, page: Optional[Any] = None):
        """Lazy load and return the Flet Google OAuth provider."""
        mode, selected_client_id, selected_client_secret = self._select_config(page)
        if not (selected_client_id and selected_client_secret):
            return None

        if self._provider is None or self._provider_mode != mode:
            # defer Flet import
            from flet.auth.providers import GoogleOAuthProvider

            kwargs = {
                "client_id": selected_client_id,
                "client_secret": selected_client_secret,
            }
            kwargs["redirect_url"] = self._resolve_redirect_uri(mode, page)

            self._provider = GoogleOAuthProvider(**kwargs)
            self._provider_mode = mode
        return self._provider

    def get_callback_complete_page_html(self) -> str:
        """Return branded OAuth completion page HTML for Google sign-in callback."""
        return self.CALLBACK_COMPLETE_PAGE_HTML

__all__ = ["GoogleAuthService", "GoogleAuthError"]
