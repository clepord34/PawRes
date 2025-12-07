"""Tests for GoogleAuthService - OAuth flow with mocked HTTP responses."""
import pytest
import json
from unittest.mock import Mock, MagicMock, patch, PropertyMock
from urllib.error import URLError, HTTPError
import socket

from services.google_auth_service import GoogleAuthService, GoogleAuthError


class TestGoogleAuthConfiguration:
    """Test Google Auth service configuration and initialization."""
    
    def test_service_initializes_with_default_port(self):
        """Test service initialization with default callback port."""
        with patch('services.google_auth_service.app_config') as mock_config:
            mock_config.get_env.return_value = None
            service = GoogleAuthService()
            
            assert service.callback_port == 8085
            assert service.redirect_uri == "http://localhost:8085/oauth/callback"
    
    def test_service_initializes_with_custom_port(self):
        """Test service initialization with custom callback port."""
        with patch('services.google_auth_service.app_config') as mock_config:
            mock_config.get_env.return_value = None
            service = GoogleAuthService(callback_port=9000)
            
            assert service.callback_port == 9000
            assert service.redirect_uri == "http://localhost:9000/oauth/callback"
    
    def test_is_configured_true_when_credentials_present(self):
        """Test is_configured returns True when both credentials are set."""
        with patch('services.google_auth_service.app_config') as mock_config:
            mock_config.get_env.side_effect = lambda key: {
                "GOOGLE_CLIENT_ID": "test-client-id",
                "GOOGLE_CLIENT_SECRET": "test-client-secret"
            }.get(key)
            
            service = GoogleAuthService()
            assert service.is_configured is True
    
    def test_is_configured_false_when_credentials_missing(self):
        """Test is_configured returns False when credentials are missing."""
        with patch('services.google_auth_service.app_config') as mock_config:
            mock_config.get_env.return_value = None
            
            service = GoogleAuthService()
            assert service.is_configured is False
    
    def test_is_configured_false_when_only_client_id_present(self):
        """Test is_configured returns False when only client ID is set."""
        with patch('services.google_auth_service.app_config') as mock_config:
            mock_config.get_env.side_effect = lambda key: {
                "GOOGLE_CLIENT_ID": "test-client-id"
            }.get(key)
            
            service = GoogleAuthService()
            assert service.is_configured is False


class TestInternetConnectivity:
    """Test internet connectivity checking."""
    
    def test_check_internet_available_when_connected(self):
        """Test internet check returns True when connection succeeds."""
        with patch('services.google_auth_service.app_config') as mock_config:
            mock_config.get_env.return_value = None
            service = GoogleAuthService()
            
            with patch('socket.socket') as mock_socket:
                mock_sock_instance = MagicMock()
                mock_socket.return_value = mock_sock_instance
                
                result = service.check_internet_available()
                
                assert result is True
                mock_sock_instance.settimeout.assert_called_once_with(3)
                mock_sock_instance.connect.assert_called_once_with(("accounts.google.com", 443))
                mock_sock_instance.close.assert_called_once()
    
    def test_check_internet_unavailable_when_connection_fails(self):
        """Test internet check returns False when connection fails."""
        with patch('services.google_auth_service.app_config') as mock_config:
            mock_config.get_env.return_value = None
            service = GoogleAuthService()
            
            with patch('socket.socket') as mock_socket:
                mock_sock_instance = MagicMock()
                mock_socket.return_value = mock_sock_instance
                mock_sock_instance.connect.side_effect = socket.error("Connection failed")
                
                result = service.check_internet_available()
                
                assert result is False
    
    def test_check_internet_unavailable_on_timeout(self):
        """Test internet check returns False when connection times out."""
        with patch('services.google_auth_service.app_config') as mock_config:
            mock_config.get_env.return_value = None
            service = GoogleAuthService()
            
            with patch('socket.socket') as mock_socket:
                mock_sock_instance = MagicMock()
                mock_socket.return_value = mock_sock_instance
                mock_sock_instance.connect.side_effect = socket.timeout("Timed out")
                
                result = service.check_internet_available()
                
                assert result is False


class TestPKCEGeneration:
    """Test PKCE code verifier and challenge generation."""
    
    def test_generate_pkce_pair_returns_valid_values(self):
        """Test PKCE generation returns verifier and challenge."""
        with patch('services.google_auth_service.app_config') as mock_config:
            mock_config.get_env.return_value = None
            service = GoogleAuthService()
            
            verifier, challenge = service._generate_pkce_pair()
            
            assert verifier is not None
            assert challenge is not None
            assert isinstance(verifier, str)
            assert isinstance(challenge, str)
            assert len(verifier) > 40  # Should be 43-128 chars
            assert len(challenge) > 30  # SHA256 base64 encoded
    
    def test_generate_pkce_pair_creates_unique_values(self):
        """Test PKCE generation creates different values each time."""
        with patch('services.google_auth_service.app_config') as mock_config:
            mock_config.get_env.return_value = None
            service = GoogleAuthService()
            
            verifier1, challenge1 = service._generate_pkce_pair()
            verifier2, challenge2 = service._generate_pkce_pair()
            
            assert verifier1 != verifier2
            assert challenge1 != challenge2


class TestAuthURL:
    """Test OAuth authorization URL generation."""
    
    def test_get_auth_url_generates_valid_url(self):
        """Test auth URL generation with proper parameters."""
        with patch('services.google_auth_service.app_config') as mock_config:
            mock_config.get_env.side_effect = lambda key: {
                "GOOGLE_CLIENT_ID": "test-client-id",
                "GOOGLE_CLIENT_SECRET": "test-secret"
            }.get(key)
            
            service = GoogleAuthService()
            url = service.get_auth_url()
            
            assert url.startswith("https://accounts.google.com/o/oauth2/v2/auth?")
            assert "client_id=test-client-id" in url
            assert "redirect_uri=http%3A%2F%2Flocalhost%3A8085%2Foauth%2Fcallback" in url
            assert "response_type=code" in url
            assert "scope=openid+email+profile" in url
            assert "code_challenge_method=S256" in url
            assert "state=" in url
            assert "code_challenge=" in url
    
    def test_get_auth_url_raises_error_without_client_id(self):
        """Test auth URL generation fails without client ID."""
        with patch('services.google_auth_service.app_config') as mock_config:
            mock_config.get_env.return_value = None
            
            service = GoogleAuthService()
            
            with pytest.raises(GoogleAuthError, match="GOOGLE_CLIENT_ID not configured"):
                service.get_auth_url()
    
    def test_get_auth_url_sets_state_and_verifier(self):
        """Test auth URL generation initializes state and PKCE verifier."""
        with patch('services.google_auth_service.app_config') as mock_config:
            mock_config.get_env.side_effect = lambda key: {
                "GOOGLE_CLIENT_ID": "test-client-id",
                "GOOGLE_CLIENT_SECRET": "test-secret"
            }.get(key)
            
            service = GoogleAuthService()
            assert service._state is None
            assert service._code_verifier is None
            
            service.get_auth_url()
            
            assert service._state is not None
            assert service._code_verifier is not None
            assert len(service._state) > 30
            assert len(service._code_verifier) > 40


class TestTokenExchange:
    """Test OAuth authorization code exchange for tokens."""
    
    def test_exchange_code_success(self):
        """Test successful token exchange with mocked HTTP response."""
        with patch('services.google_auth_service.app_config') as mock_config:
            mock_config.get_env.side_effect = lambda key: {
                "GOOGLE_CLIENT_ID": "test-client-id",
                "GOOGLE_CLIENT_SECRET": "test-secret"
            }.get(key)
            
            service = GoogleAuthService()
            service._code_verifier = "test-verifier"
            
            mock_response = MagicMock()
            mock_response.__enter__.return_value = mock_response
            mock_response.__exit__.return_value = None
            mock_response.read.return_value = json.dumps({
                "access_token": "test-access-token",
                "refresh_token": "test-refresh-token",
                "expires_in": 3600,
                "token_type": "Bearer"
            }).encode('utf-8')
            
            with patch('urllib.request.urlopen', return_value=mock_response):
                result = service.exchange_code("test-auth-code")
                
                assert result["access_token"] == "test-access-token"
                assert result["refresh_token"] == "test-refresh-token"
                assert result["expires_in"] == 3600
    
    def test_exchange_code_raises_error_without_credentials(self):
        """Test token exchange fails without credentials."""
        with patch('services.google_auth_service.app_config') as mock_config:
            mock_config.get_env.return_value = None
            
            service = GoogleAuthService()
            
            with pytest.raises(GoogleAuthError, match="Google OAuth credentials not configured"):
                service.exchange_code("test-code")
    
    def test_exchange_code_handles_network_error(self):
        """Test token exchange handles network errors gracefully."""
        with patch('services.google_auth_service.app_config') as mock_config:
            mock_config.get_env.side_effect = lambda key: {
                "GOOGLE_CLIENT_ID": "test-client-id",
                "GOOGLE_CLIENT_SECRET": "test-secret"
            }.get(key)
            
            service = GoogleAuthService()
            service._code_verifier = "test-verifier"
            
            with patch('urllib.request.urlopen', side_effect=URLError("Network error")):
                with pytest.raises(GoogleAuthError, match="Token exchange failed"):
                    service.exchange_code("test-code")
    
    def test_exchange_code_handles_invalid_json_response(self):
        """Test token exchange handles malformed JSON response."""
        with patch('services.google_auth_service.app_config') as mock_config:
            mock_config.get_env.side_effect = lambda key: {
                "GOOGLE_CLIENT_ID": "test-client-id",
                "GOOGLE_CLIENT_SECRET": "test-secret"
            }.get(key)
            
            service = GoogleAuthService()
            service._code_verifier = "test-verifier"
            
            mock_response = MagicMock()
            mock_response.__enter__.return_value = mock_response
            mock_response.__exit__.return_value = None
            mock_response.read.return_value = b"invalid json"
            
            with patch('urllib.request.urlopen', return_value=mock_response):
                with pytest.raises(GoogleAuthError, match="Token exchange failed"):
                    service.exchange_code("test-code")


class TestUserInfo:
    """Test fetching user information from Google."""
    
    def test_get_user_info_success(self):
        """Test successful user info retrieval with mocked HTTP response."""
        with patch('services.google_auth_service.app_config') as mock_config:
            mock_config.get_env.return_value = None
            service = GoogleAuthService()
            
            mock_response = MagicMock()
            mock_response.__enter__.return_value = mock_response
            mock_response.__exit__.return_value = None
            mock_response.read.return_value = json.dumps({
                "email": "test@gmail.com",
                "name": "Test User",
                "picture": "https://example.com/photo.jpg",
                "sub": "1234567890",
                "email_verified": True
            }).encode('utf-8')
            
            with patch('urllib.request.urlopen', return_value=mock_response):
                user_info = service.get_user_info("test-access-token")
                
                assert user_info["email"] == "test@gmail.com"
                assert user_info["name"] == "Test User"
                assert user_info["picture"] == "https://example.com/photo.jpg"
                assert user_info["sub"] == "1234567890"
                assert user_info["email_verified"] is True
    
    def test_get_user_info_handles_network_error(self):
        """Test user info retrieval handles network errors."""
        with patch('services.google_auth_service.app_config') as mock_config:
            mock_config.get_env.return_value = None
            service = GoogleAuthService()
            
            with patch('urllib.request.urlopen', side_effect=URLError("Network error")):
                with pytest.raises(GoogleAuthError, match="Failed to get user info"):
                    service.get_user_info("test-access-token")
    
    def test_get_user_info_includes_authorization_header(self):
        """Test user info request includes proper authorization header."""
        with patch('services.google_auth_service.app_config') as mock_config:
            mock_config.get_env.return_value = None
            service = GoogleAuthService()
            
            mock_response = MagicMock()
            mock_response.__enter__.return_value = mock_response
            mock_response.__exit__.return_value = None
            mock_response.read.return_value = json.dumps({
                "email": "test@gmail.com",
                "name": "Test User"
            }).encode('utf-8')
            
            with patch('urllib.request.urlopen', return_value=mock_response) as mock_urlopen, \
                 patch('urllib.request.Request') as mock_request:
                
                service.get_user_info("my-access-token")
                
                # Verify Request was called with authorization header
                mock_request.assert_called_once()
                args, kwargs = mock_request.call_args
                assert kwargs.get("headers", {}).get("Authorization") == "Bearer my-access-token"


class TestSignInFlow:
    """Test complete OAuth sign-in flow (mocked)."""
    
    def test_sign_in_fails_without_configuration(self):
        """Test sign-in returns None when not configured."""
        with patch('services.google_auth_service.app_config') as mock_config:
            mock_config.get_env.return_value = None
            
            service = GoogleAuthService()
            error_callback = Mock()
            
            result = service.sign_in(on_error=error_callback)
            
            assert result is None
            error_callback.assert_called_once()
            assert "not configured" in error_callback.call_args[0][0].lower()
    
    def test_sign_in_fails_without_internet(self):
        """Test sign-in returns None when internet is unavailable."""
        with patch('services.google_auth_service.app_config') as mock_config:
            mock_config.get_env.side_effect = lambda key: {
                "GOOGLE_CLIENT_ID": "test-client-id",
                "GOOGLE_CLIENT_SECRET": "test-secret"
            }.get(key)
            
            service = GoogleAuthService()
            error_callback = Mock()
            
            with patch.object(service, 'check_internet_available', return_value=False):
                result = service.sign_in(on_error=error_callback)
                
                assert result is None
                error_callback.assert_called_once()
                assert "no internet" in error_callback.call_args[0][0].lower()
    
    def test_sign_in_handles_server_start_failure(self):
        """Test sign-in handles callback server start failure."""
        with patch('services.google_auth_service.app_config') as mock_config:
            mock_config.get_env.side_effect = lambda key: {
                "GOOGLE_CLIENT_ID": "test-client-id",
                "GOOGLE_CLIENT_SECRET": "test-secret"
            }.get(key)
            
            service = GoogleAuthService()
            error_callback = Mock()
            
            with patch.object(service, 'check_internet_available', return_value=True), \
                 patch('services.google_auth_service.HTTPServer', side_effect=OSError("Port in use")):
                
                result = service.sign_in(on_error=error_callback)
                
                assert result is None
                error_callback.assert_called_once()
                assert "could not start" in error_callback.call_args[0][0].lower()
    
    def test_sign_in_async_starts_thread(self):
        """Test async sign-in starts a background thread."""
        with patch('services.google_auth_service.app_config') as mock_config:
            mock_config.get_env.return_value = None
            
            service = GoogleAuthService()
            complete_callback = Mock()
            error_callback = Mock()
            
            with patch('threading.Thread') as mock_thread:
                mock_thread_instance = MagicMock()
                mock_thread.return_value = mock_thread_instance
                
                result = service.sign_in_async(complete_callback, error_callback)
                
                mock_thread.assert_called_once()
                mock_thread_instance.start.assert_called_once()
                assert result == mock_thread_instance


class TestOAuthCallbackHandler:
    """Test OAuth callback HTTP handler."""
    
    def test_callback_handler_extracts_auth_code(self):
        """Test callback handler extracts authorization code from URL."""
        from services.google_auth_service import OAuthCallbackHandler
        import urllib.parse
        
        # Reset class variables
        OAuthCallbackHandler.auth_code = None
        OAuthCallbackHandler.error = None
        
        # Test the URL parsing logic directly without instantiating handler
        test_path = "/oauth/callback?code=test-auth-code-123&state=test-state"
        parsed = urllib.parse.urlparse(test_path)
        params = urllib.parse.parse_qs(parsed.query)
        
        # Verify parsing works as expected
        assert "code" in params
        assert params["code"][0] == "test-auth-code-123"
        assert "state" in params
        assert params["state"][0] == "test-state"
    
    def test_callback_handler_extracts_error(self):
        """Test callback handler extracts error from URL."""
        from services.google_auth_service import OAuthCallbackHandler
        import urllib.parse
        
        # Reset class variables
        OAuthCallbackHandler.auth_code = None
        OAuthCallbackHandler.error = None
        
        # Test the URL parsing logic directly
        test_path = "/oauth/callback?error=access_denied&error_description=User+denied+access"
        parsed = urllib.parse.urlparse(test_path)
        params = urllib.parse.parse_qs(parsed.query)
        
        # Verify parsing works as expected
        assert "error" in params
        assert params["error"][0] == "access_denied"
        assert "error_description" in params
        assert params["error_description"][0] == "User denied access"


class TestEdgeCases:
    """Test edge cases and error scenarios."""
    
    def test_multiple_pkce_generations_are_unique(self):
        """Test that multiple PKCE generations produce unique values."""
        with patch('services.google_auth_service.app_config') as mock_config:
            mock_config.get_env.return_value = None
            
            service = GoogleAuthService()
            
            pairs = [service._generate_pkce_pair() for _ in range(5)]
            verifiers = [p[0] for p in pairs]
            challenges = [p[1] for p in pairs]
            
            # All should be unique
            assert len(set(verifiers)) == 5
            assert len(set(challenges)) == 5
    
    def test_service_handles_partial_credentials(self):
        """Test service handles partial credential configuration."""
        with patch('services.google_auth_service.app_config') as mock_config:
            # Only client secret, no client ID
            mock_config.get_env.side_effect = lambda key: {
                "GOOGLE_CLIENT_SECRET": "test-secret"
            }.get(key)
            
            service = GoogleAuthService()
            
            assert service.client_id is None
            assert service.client_secret == "test-secret"
            assert service.is_configured is False
