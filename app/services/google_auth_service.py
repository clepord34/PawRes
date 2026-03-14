"""Google OAuth 2.0 authentication service for Flet apps.

Implements Google Sign-In using Flet's native OAuth support.
Works seamlessly across Desktop, Web, and Mobile.
"""
from __future__ import annotations

import os
from typing import Any, Callable, Dict, Optional

import app_config

class GoogleAuthError(Exception):
    """Exception raised for Google Auth errors."""
    pass

class GoogleAuthService:
    """Service to handle Flet integration with Google OAuth."""
    
    def __init__(self) -> None:
        """Initialize the Google Auth service configuration."""
        self.client_id = app_config.get_env("GOOGLE_CLIENT_ID")
        self.client_secret = app_config.get_env("GOOGLE_CLIENT_SECRET")
        
        # When using Flet Web, redirect_url is usually not strictly necessary if we omit it 
        # or just point it back to the exact root, but to be robust across tunnels:
        base_url = app_config.get_env("BASE_URL")
        if base_url:
            self.redirect_uri = f"{base_url.rstrip('/')}/oauth_callback"     
        else:
            self.redirect_uri = "http://localhost:8000/oauth_callback"

        self._provider = None

    @property
    def is_configured(self) -> bool:
        """Check if Google OAuth is properly configured."""
        return bool(self.client_id and self.client_secret)

    def get_provider(self):
        """Lazy load and return the Flet Google OAuth provider."""
        if not self.is_configured:
            return None
            
        if self._provider is None:
            # defer Flet import
            from flet.auth.providers import GoogleOAuthProvider
            
            self._provider = GoogleOAuthProvider(
                client_id=self.client_id,
                client_secret=self.client_secret,
                redirect_url=self.redirect_uri
            )
        return self._provider

__all__ = ["GoogleAuthService", "GoogleAuthError"]
