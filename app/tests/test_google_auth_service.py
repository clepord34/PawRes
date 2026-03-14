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
