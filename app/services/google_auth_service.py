"""Google OAuth 2.0 authentication service for Flet apps.

Implements Google Sign-In using OAuth 2.0 Authorization Code flow with PKCE.
Works for both desktop and web Flet applications.
"""
from __future__ import annotations

import base64
import hashlib
import json
import secrets
import threading
import urllib.parse
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Any, Callable, Dict, Optional

import app_config


# OAuth endpoints
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"

# Default local callback port
DEFAULT_CALLBACK_PORT = 8085
CALLBACK_PATH = "/oauth/callback"


class GoogleAuthError(Exception):
    """Exception raised for Google Auth errors."""
    pass


class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """HTTP handler to receive OAuth callback from Google."""
    
    auth_code: Optional[str] = None
    error: Optional[str] = None
    
    def do_GET(self) -> None:
        """Handle the OAuth callback GET request."""
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        
        if "code" in params:
            OAuthCallbackHandler.auth_code = params["code"][0]
            self._send_success_response()
        elif "error" in params:
            OAuthCallbackHandler.error = params.get("error_description", params["error"])[0]
            self._send_error_response(OAuthCallbackHandler.error)
        else:
            self._send_error_response("No authorization code received")
    
    def _send_success_response(self) -> None:
        """Send success HTML page styled to match PawRes branding."""
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Sign In Successful - PawRes</title>
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
                .success-badge {
                    display: inline-flex;
                    align-items: center;
                    justify-content: center;
                    width: 64px;
                    height: 64px;
                    background: linear-gradient(135deg, #00897b 0%, #00695c 100%);
                    border-radius: 50%;
                    margin-bottom: 20px;
                    box-shadow: 0 4px 12px rgba(0, 137, 123, 0.3);
                }
                .success-badge svg {
                    width: 34px;
                    height: 34px;
                }
                h1 { 
                    color: #00897b; 
                    font-size: 26px;
                    font-weight: 600;
                    margin-bottom: 12px; 
                }
                p { 
                    color: #666; 
                    font-size: 15px;
                    line-height: 1.5;
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
                
                <div class="success-badge">
                    <svg viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
                        <polyline points="20 6 9 17 4 12"></polyline>
                    </svg>
                </div>
                <h1>Sign In Successful!</h1>
                <p>You can close this window and return to PawRes.</p>
            </div>
        </body>
        </html>
        """
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))
    
    def _send_error_response(self, error: str) -> None:
        """Send error HTML page styled to match PawRes branding."""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Sign In Failed - PawRes</title>
            <style>
                * {{ margin: 0; padding: 0; box-sizing: border-box; }}
                body {{ 
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    display: flex; 
                    justify-content: center; 
                    align-items: center; 
                    min-height: 100vh; 
                    background: linear-gradient(180deg, #e0f2f1 0%, #e8f5f3 25%, #f5f0e6 75%, #f0e6d3 100%);
                }}
                .card {{ 
                    background: linear-gradient(180deg, #ffffff 0%, #fffdf8 100%);
                    padding: 50px 60px; 
                    border-radius: 20px; 
                    text-align: center; 
                    box-shadow: 0 8px 32px rgba(0, 128, 128, 0.12);
                    max-width: 420px;
                }}
                .logo {{ 
                    margin-bottom: 16px;
                }}
                .logo svg {{
                    width: 90px;
                    height: 90px;
                }}
                .brand-name {{
                    font-size: 32px;
                    font-weight: 700;
                    font-style: italic;
                    color: #1a1a1a;
                    margin-bottom: 6px;
                }}
                .brand-tagline {{
                    font-size: 15px;
                    color: #888;
                    margin-bottom: 35px;
                }}
                .error-badge {{
                    display: inline-flex;
                    align-items: center;
                    justify-content: center;
                    width: 64px;
                    height: 64px;
                    background: linear-gradient(135deg, #e53935 0%, #c62828 100%);
                    border-radius: 50%;
                    margin-bottom: 20px;
                    box-shadow: 0 4px 12px rgba(229, 57, 53, 0.3);
                }}
                .error-badge svg {{
                    width: 34px;
                    height: 34px;
                }}
                h1 {{ 
                    color: #e53935; 
                    font-size: 26px;
                    font-weight: 600;
                    margin-bottom: 12px; 
                }}
                p {{ 
                    color: #666; 
                    font-size: 15px;
                    line-height: 1.5;
                    margin-bottom: 8px;
                }}
                .error-detail {{
                    background: #fff5f5;
                    border: 1px solid #ffcdd2;
                    border-radius: 8px;
                    padding: 12px 16px;
                    margin-top: 16px;
                    color: #c62828;
                    font-size: 13px;
                }}
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
                
                <div class="error-badge">
                    <svg viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
                        <line x1="18" y1="6" x2="6" y2="18"></line>
                        <line x1="6" y1="6" x2="18" y2="18"></line>
                    </svg>
                </div>
                <h1>Sign In Failed</h1>
                <p>Please close this window and try again.</p>
                <div class="error-detail">{error}</div>
            </div>
        </body>
        </html>
        """
        self.send_response(400)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))
    
    def log_message(self, format: str, *args) -> None:
        """Suppress default HTTP server logging."""
        pass


class GoogleAuthService:
    """Service for Google OAuth 2.0 authentication.
    
    Usage:
        auth = GoogleAuthService()
        user_info = auth.sign_in()  # Opens browser, returns user info
        
    Requires GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in environment.
    """
    
    def __init__(self, callback_port: int = DEFAULT_CALLBACK_PORT) -> None:
        """Initialize the Google Auth service.
        
        Args:
            callback_port: Local port for OAuth callback (default 8085)
        """
        self.client_id = app_config.get_env("GOOGLE_CLIENT_ID")
        self.client_secret = app_config.get_env("GOOGLE_CLIENT_SECRET")
        self.callback_port = callback_port
        self.redirect_uri = f"http://localhost:{callback_port}{CALLBACK_PATH}"
        
        # State for PKCE and CSRF protection
        self._state: Optional[str] = None
        self._code_verifier: Optional[str] = None
    
    @property
    def is_configured(self) -> bool:
        """Check if Google OAuth is properly configured."""
        return bool(self.client_id and self.client_secret)
    
    def check_internet_available(self) -> bool:
        """Check if internet connection is available for OAuth.
        
        Returns:
            True if Google's OAuth servers are reachable, False otherwise
        """
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            try:
                sock.connect(("accounts.google.com", 443))
                return True
            finally:
                sock.close()
        except (socket.error, socket.timeout, OSError):
            return False
    
    def _generate_pkce_pair(self) -> tuple[str, str]:
        """Generate PKCE code verifier and challenge.
        
        Returns:
            Tuple of (code_verifier, code_challenge)
        """
        # Generate random 43-128 character verifier
        code_verifier = secrets.token_urlsafe(64)
        
        digest = hashlib.sha256(code_verifier.encode("ascii")).digest()
        code_challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
        
        return code_verifier, code_challenge
    
    def get_auth_url(self) -> str:
        """Generate the Google OAuth authorization URL.
        
        Returns:
            The URL to redirect the user to for authentication
            
        Raises:
            GoogleAuthError: If client_id is not configured
        """
        if not self.client_id:
            raise GoogleAuthError("GOOGLE_CLIENT_ID not configured")
        
        # Generate state for CSRF protection
        self._state = secrets.token_urlsafe(32)
        
        # Generate PKCE pair
        self._code_verifier, code_challenge = self._generate_pkce_pair()
        
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": "openid email profile",
            "state": self._state,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
            "access_type": "offline",
            "prompt": "select_account",
        }
        
        return f"{GOOGLE_AUTH_URL}?{urllib.parse.urlencode(params)}"
    
    def exchange_code(self, auth_code: str) -> Dict[str, Any]:
        """Exchange authorization code for tokens.
        
        Args:
            auth_code: The authorization code from Google
            
        Returns:
            Token response containing access_token, id_token, etc.
            
        Raises:
            GoogleAuthError: If token exchange fails
        """
        if not self.client_id or not self.client_secret:
            raise GoogleAuthError("Google OAuth credentials not configured")
        
        try:
            import urllib.request
            
            data = {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "code": auth_code,
                "redirect_uri": self.redirect_uri,
                "grant_type": "authorization_code",
                "code_verifier": self._code_verifier,
            }
            
            encoded_data = urllib.parse.urlencode(data).encode("utf-8")
            req = urllib.request.Request(
                GOOGLE_TOKEN_URL,
                data=encoded_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            with urllib.request.urlopen(req, timeout=30) as response:
                return json.loads(response.read().decode("utf-8"))
                
        except Exception as e:
            raise GoogleAuthError(f"Token exchange failed: {e}")
    
    def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """Get user information from Google.
        
        Args:
            access_token: The OAuth access token
            
        Returns:
            User info dict with email, name, picture, etc.
            
        Raises:
            GoogleAuthError: If user info request fails
        """
        try:
            import urllib.request
            
            req = urllib.request.Request(
                GOOGLE_USERINFO_URL,
                headers={"Authorization": f"Bearer {access_token}"}
            )
            
            with urllib.request.urlopen(req, timeout=30) as response:
                return json.loads(response.read().decode("utf-8"))
                
        except Exception as e:
            raise GoogleAuthError(f"Failed to get user info: {e}")
    
    def sign_in(self, on_complete: Optional[Callable[[Dict[str, Any]], None]] = None,
                on_error: Optional[Callable[[str], None]] = None) -> Optional[Dict[str, Any]]:
        """Perform full OAuth sign-in flow.
        
        Opens browser for Google sign-in, handles callback, and returns user info.
        
        Args:
            on_complete: Optional callback with user info on success
            on_error: Optional callback with error message on failure
            
        Returns:
            User info dict if successful, None if failed/cancelled
        """
        if not self.is_configured:
            error_msg = "Google Sign-In not configured. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET."
            if on_error:
                on_error(error_msg)
            return None
        
        if not self.check_internet_available():
            error_msg = "No internet connection. Google Sign-In requires an active internet connection."
            if on_error:
                on_error(error_msg)
            return None
        
        OAuthCallbackHandler.auth_code = None
        OAuthCallbackHandler.error = None
        
        # Start local server for callback
        try:
            server = HTTPServer(("localhost", self.callback_port), OAuthCallbackHandler)
            server.timeout = 300  # 5 minute timeout - give user plenty of time to sign in
        except OSError as e:
            error_msg = f"Could not start callback server: {e}"
            if on_error:
                on_error(error_msg)
            return None
        
        # Open browser to Google sign-in
        auth_url = self.get_auth_url()
        webbrowser.open(auth_url)
        
        # Wait for callback - handle multiple requests in case of browser prefetch
        # Keep handling requests until we get an auth code/error or timeout
        import time
        start_time = time.time()
        max_wait = 300  # 5 minutes max
        
        try:
            while True:
                if OAuthCallbackHandler.auth_code or OAuthCallbackHandler.error:
                    break
                
                if time.time() - start_time > max_wait:
                    break
                
                try:
                    server.handle_request()
                except Exception:
                    # Ignore errors during request handling, continue waiting
                    pass
        finally:
            server.server_close()
        
        if OAuthCallbackHandler.error:
            if on_error:
                on_error(OAuthCallbackHandler.error)
            return None
        
        if not OAuthCallbackHandler.auth_code:
            error_msg = "No authorization code received"
            if on_error:
                on_error(error_msg)
            return None
        
        # Exchange code for tokens
        try:
            tokens = self.exchange_code(OAuthCallbackHandler.auth_code)
            access_token = tokens.get("access_token")
            
            if not access_token:
                raise GoogleAuthError("No access token in response")
            
            user_info = self.get_user_info(access_token)
            
            user_info["_tokens"] = {
                "access_token": access_token,
                "refresh_token": tokens.get("refresh_token"),
                "expires_in": tokens.get("expires_in"),
            }
            
            if on_complete:
                on_complete(user_info)
            
            return user_info
            
        except GoogleAuthError as e:
            if on_error:
                on_error(str(e))
            return None
    
    def sign_in_async(self, on_complete: Callable[[Dict[str, Any]], None],
                      on_error: Callable[[str], None]) -> threading.Thread:
        """Perform OAuth sign-in in background thread.
        
        Use this for non-blocking sign-in in UI applications.
        
        Args:
            on_complete: Callback with user info on success
            on_error: Callback with error message on failure
            
        Returns:
            The started thread (for joining if needed)
        """
        thread = threading.Thread(
            target=self.sign_in,
            args=(on_complete, on_error),
            daemon=True
        )
        thread.start()
        return thread


__all__ = ["GoogleAuthService", "GoogleAuthError"]
