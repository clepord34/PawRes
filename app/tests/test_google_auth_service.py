import pytest
from services.google_auth_service import GoogleAuthService

def test_is_configured_true(monkeypatch):
    monkeypatch.setattr('app_config.get_env', lambda k: "dummy" if "GOOGLE" in k else None)
    service = GoogleAuthService()
    assert service.is_configured is True

def test_is_configured_false(monkeypatch):
    monkeypatch.setattr('app_config.get_env', lambda k: None)
    service = GoogleAuthService()
    assert service.is_configured is False


def test_select_config_prefers_web_credentials(monkeypatch):
    env = {
        "GOOGLE_CLIENT_ID": "default-id",
        "GOOGLE_CLIENT_SECRET": "default-secret",
        "GOOGLE_WEB_CLIENT_ID": "web-id",
        "GOOGLE_WEB_CLIENT_SECRET": "web-secret",
        "GOOGLE_DESKTOP_CLIENT_ID": "desktop-id",
        "GOOGLE_DESKTOP_CLIENT_SECRET": "desktop-secret",
        "GOOGLE_REDIRECT_URL": None,
        "BASE_URL": None,
    }
    monkeypatch.setattr("app_config.get_env", lambda k: env.get(k))
    service = GoogleAuthService()

    page = type("Page", (), {"web": True})()
    mode, client_id, client_secret = service._select_config(page)

    assert mode == "web"
    assert client_id == "web-id"
    assert client_secret == "web-secret"


def test_desktop_redirect_uri_uses_page_url(monkeypatch):
    env = {
        "GOOGLE_CLIENT_ID": "default-id",
        "GOOGLE_CLIENT_SECRET": "default-secret",
        "GOOGLE_WEB_CLIENT_ID": None,
        "GOOGLE_WEB_CLIENT_SECRET": None,
        "GOOGLE_DESKTOP_CLIENT_ID": "desktop-id",
        "GOOGLE_DESKTOP_CLIENT_SECRET": "desktop-secret",
        "GOOGLE_REDIRECT_URL": "https://expired.trycloudflare.com/oauth_callback",
        "BASE_URL": "https://expired.trycloudflare.com",
    }
    monkeypatch.setattr("app_config.get_env", lambda k: env.get(k))
    service = GoogleAuthService()
    page = type("Page", (), {"url": "http://127.0.0.1:63721"})()

    assert service._resolve_redirect_uri("desktop", page) == "http://localhost:63721/oauth_callback"


def test_web_redirect_defaults_to_localhost(monkeypatch):
    env = {
        "GOOGLE_CLIENT_ID": "default-id",
        "GOOGLE_CLIENT_SECRET": "default-secret",
        "GOOGLE_WEB_CLIENT_ID": "web-id",
        "GOOGLE_WEB_CLIENT_SECRET": "web-secret",
        "GOOGLE_DESKTOP_CLIENT_ID": None,
        "GOOGLE_DESKTOP_CLIENT_SECRET": None,
        "GOOGLE_REDIRECT_URL": None,
        "BASE_URL": "https://expired.trycloudflare.com",
    }
    monkeypatch.setattr("app_config.get_env", lambda k: env.get(k))
    monkeypatch.setenv("FLET_SERVER_PORT", "8000")
    service = GoogleAuthService()

    assert service._resolve_redirect_uri("web") == "http://localhost:8000/oauth_callback"


def test_blank_redirect_and_base_fallback_to_localhost(monkeypatch):
    env = {
        "GOOGLE_CLIENT_ID": "default-id",
        "GOOGLE_CLIENT_SECRET": "default-secret",
        "GOOGLE_WEB_CLIENT_ID": "web-id",
        "GOOGLE_WEB_CLIENT_SECRET": "web-secret",
        "GOOGLE_DESKTOP_CLIENT_ID": None,
        "GOOGLE_DESKTOP_CLIENT_SECRET": None,
        "GOOGLE_REDIRECT_URL": "   ",
        "BASE_URL": "   ",
    }
    monkeypatch.setattr("app_config.get_env", lambda k: env.get(k))
    monkeypatch.setenv("FLET_SERVER_PORT", "8000")

    service = GoogleAuthService()

    assert service._resolve_redirect_uri("web") == "http://localhost:8000/oauth_callback"


def test_web_ignores_page_url_when_env_urls_missing(monkeypatch):
    env = {
        "GOOGLE_CLIENT_ID": "default-id",
        "GOOGLE_CLIENT_SECRET": "default-secret",
        "GOOGLE_WEB_CLIENT_ID": "web-id",
        "GOOGLE_WEB_CLIENT_SECRET": "web-secret",
        "GOOGLE_DESKTOP_CLIENT_ID": None,
        "GOOGLE_DESKTOP_CLIENT_SECRET": None,
        "GOOGLE_REDIRECT_URL": None,
        "BASE_URL": None,
    }
    monkeypatch.setattr("app_config.get_env", lambda k: env.get(k))
    monkeypatch.setenv("FLET_SERVER_PORT", "8000")

    service = GoogleAuthService()
    page = type("Page", (), {"url": "https://example.com/app"})()

    assert service._resolve_redirect_uri("web", page) == "http://localhost:8000/oauth_callback"


def test_desktop_ignores_non_local_page_url_when_env_urls_missing(monkeypatch):
    env = {
        "GOOGLE_CLIENT_ID": "default-id",
        "GOOGLE_CLIENT_SECRET": "default-secret",
        "GOOGLE_WEB_CLIENT_ID": "web-id",
        "GOOGLE_WEB_CLIENT_SECRET": "web-secret",
        "GOOGLE_DESKTOP_CLIENT_ID": "desktop-id",
        "GOOGLE_DESKTOP_CLIENT_SECRET": "desktop-secret",
        "GOOGLE_REDIRECT_URL": None,
        "BASE_URL": None,
    }
    monkeypatch.setattr("app_config.get_env", lambda k: env.get(k))
    monkeypatch.setenv("FLET_SERVER_PORT", "8550")

    service = GoogleAuthService()
    page = type("Page", (), {"url": "https://example.com/app"})()

    assert service._resolve_redirect_uri("desktop", page) == "http://localhost:8550/oauth_callback"


def test_web_ignores_trycloudflare_env_urls(monkeypatch):
    env = {
        "GOOGLE_CLIENT_ID": "default-id",
        "GOOGLE_CLIENT_SECRET": "default-secret",
        "GOOGLE_WEB_CLIENT_ID": "web-id",
        "GOOGLE_WEB_CLIENT_SECRET": "web-secret",
        "GOOGLE_DESKTOP_CLIENT_ID": "desktop-id",
        "GOOGLE_DESKTOP_CLIENT_SECRET": "desktop-secret",
        "GOOGLE_REDIRECT_URL": "https://expired.trycloudflare.com/oauth_callback",
        "BASE_URL": "https://expired.trycloudflare.com",
    }
    monkeypatch.setattr("app_config.get_env", lambda k: env.get(k))
    monkeypatch.setenv("FLET_SERVER_PORT", "8000")

    service = GoogleAuthService()
    page = type("Page", (), {"url": "https://example.com/app"})()

    assert service._resolve_redirect_uri("web", page) == "http://localhost:8000/oauth_callback"
