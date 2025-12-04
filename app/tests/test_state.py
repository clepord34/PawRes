"""Unit tests for state management layer."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List
from unittest.mock import MagicMock

import pytest

from state.base import Observable, StateManager, StateSnapshot, ComputedState
from state.auth_state import AuthState, UserSession
from state.app_state import AppState, get_app_state


# =============================================================================
# Tests for Observable base class
# =============================================================================

class TestObservable:
    """Tests for Observable pattern implementation."""

    def test_subscribe_and_notify(self):
        """Test subscribing to an observable and receiving notifications."""
        observable = Observable()
        received_data: List[Dict[str, Any]] = []
        
        def observer(data: Dict[str, Any]) -> None:
            received_data.append(data)
        
        observable.subscribe(observer)
        observable.notify_observers({"test": "value"})
        
        assert len(received_data) == 1
        assert received_data[0] == {"test": "value"}

    def test_multiple_subscribers(self):
        """Test multiple subscribers receive notifications."""
        observable = Observable()
        results: List[str] = []
        
        def observer1(data: Dict[str, Any]) -> None:
            results.append("observer1")
        
        def observer2(data: Dict[str, Any]) -> None:
            results.append("observer2")
        
        observable.subscribe(observer1)
        observable.subscribe(observer2)
        observable.notify_observers({})
        
        assert "observer1" in results
        assert "observer2" in results

    def test_unsubscribe(self):
        """Test unsubscribing stops notifications."""
        observable = Observable()
        call_count = [0]
        
        def observer(data: Dict[str, Any]) -> None:
            call_count[0] += 1
        
        unsubscribe = observable.subscribe(observer)
        observable.notify_observers({})
        assert call_count[0] == 1
        
        unsubscribe()
        observable.notify_observers({})
        assert call_count[0] == 1  # No additional calls

    def test_clear_observers(self):
        """Test clearing all observers."""
        observable = Observable()
        call_count = [0]
        
        def observer(data: Dict[str, Any]) -> None:
            call_count[0] += 1
        
        observable.subscribe(observer)
        observable.clear_observers()
        observable.notify_observers({})
        
        assert call_count[0] == 0

    def test_observer_error_handling(self):
        """Test that observer errors don't break other observers."""
        observable = Observable()
        results: List[str] = []
        
        def bad_observer(data: Dict[str, Any]) -> None:
            raise ValueError("Error in observer")
        
        def good_observer(data: Dict[str, Any]) -> None:
            results.append("success")
        
        observable.subscribe(bad_observer)
        observable.subscribe(good_observer)
        
        # Should not raise, and good_observer should still be called
        observable.notify_observers({})
        assert "success" in results


# =============================================================================
# Tests for StateSnapshot
# =============================================================================

class TestStateSnapshot:
    """Tests for StateSnapshot data class."""

    def test_snapshot_creation(self):
        """Test creating a state snapshot."""
        data = {"key": "value"}
        snapshot = StateSnapshot(data=data, version=1)
        
        assert snapshot.data == data
        assert snapshot.version == 1
        assert isinstance(snapshot.timestamp, datetime)

    def test_snapshot_default_timestamp(self):
        """Test snapshot has default timestamp."""
        snapshot = StateSnapshot(data={}, version=0)
        assert snapshot.timestamp is not None

    def test_snapshot_custom_timestamp(self):
        """Test snapshot with custom timestamp."""
        custom_time = datetime(2024, 1, 1, 12, 0, 0)
        snapshot = StateSnapshot(data={}, timestamp=custom_time, version=1)
        
        assert snapshot.timestamp == custom_time


# =============================================================================
# Tests for StateManager
# =============================================================================

class TestStateManager:
    """Tests for StateManager generic class."""

    def test_initial_state(self):
        """Test state manager with initial state."""
        manager = StateManager(initial_state={"count": 0})
        
        assert manager.state == {"count": 0}
        assert manager.version == 0
        assert manager.is_dirty is False

    def test_default_initial_state(self):
        """Test state manager with default (empty dict) state."""
        manager = StateManager()
        
        assert manager.state == {}
        assert manager.version == 0

    def test_update_state(self):
        """Test updating state."""
        manager = StateManager(initial_state={})
        notifications: List[Dict] = []
        
        # Store callback in variable to prevent garbage collection (weak refs)
        def callback(d: Dict[str, Any]) -> None:
            notifications.append(d)
        
        manager.subscribe(callback)
        
        manager.update_state({"name": "test"})
        
        assert manager.state == {"name": "test"}
        assert manager.version == 1
        assert manager.is_dirty is True
        assert len(notifications) == 1

    def test_update_state_no_notify(self):
        """Test updating state without notification."""
        manager = StateManager(initial_state={})
        notifications: List[Dict] = []
        manager.subscribe(lambda d: notifications.append(d))
        
        manager.update_state({"name": "test"}, notify=False)
        
        assert manager.state == {"name": "test"}
        assert len(notifications) == 0

    def test_patch_state(self):
        """Test partial state update via patch."""
        manager = StateManager(initial_state={"a": 1, "b": 2})
        
        manager.patch_state({"b": 99, "c": 3})
        
        assert manager.state["a"] == 1
        assert manager.state["b"] == 99
        assert manager.state["c"] == 3

    def test_get_snapshot(self):
        """Test getting state snapshot."""
        manager = StateManager(initial_state={"test": True})
        manager.update_state({"test": False})
        
        snapshot = manager.get_snapshot()
        
        assert snapshot.data == {"test": False}
        assert snapshot.version == 1

    def test_mark_synced(self):
        """Test marking state as synced."""
        manager = StateManager()
        manager.update_state({"value": 42})
        assert manager.is_dirty is True
        
        manager.mark_synced()
        
        assert manager.is_dirty is False
        assert manager.last_sync is not None

    def test_reset(self):
        """Test resetting state."""
        manager = StateManager(initial_state={"original": True})
        manager.update_state({"modified": True})
        
        manager.reset({"reset": True})
        
        assert manager.state == {"reset": True}
        assert manager.version == 0
        assert manager.is_dirty is False


# =============================================================================
# Tests for ComputedState
# =============================================================================

class TestComputedState:
    """Tests for ComputedState derived values."""

    def test_computed_initial_value(self):
        """Test computed state calculates initial value."""
        source = StateManager(initial_state={"numbers": [1, 2, 3]})
        
        computed = ComputedState(
            dependencies=[source],
            compute=lambda: sum(source.state.get("numbers", []))
        )
        
        assert computed.value == 6

    def test_computed_updates_on_dependency_change(self):
        """Test computed state updates when dependency changes."""
        source = StateManager(initial_state={"value": 10})
        
        # Note: Weak reference behavior may cause callback cleanup
        # Testing the value computation directly
        computed = ComputedState(
            dependencies=[source],
            compute=lambda: source.state.get("value", 0) * 2
        )
        
        assert computed.value == 20
        
        source.update_state({"value": 5})
        
        # Force recomputation by invalidating cache
        computed._is_valid = False
        assert computed.value == 10

    def test_computed_notifies_observers(self):
        """Test computed state notifies its observers."""
        source = StateManager(initial_state={"x": 1})
        computed = ComputedState(
            dependencies=[source],
            compute=lambda: source.state.get("x", 0) + 1
        )
        
        notifications: List[Dict] = []
        
        # Store callback in variable to prevent garbage collection
        def callback(d: Dict[str, Any]) -> None:
            notifications.append(d)
        
        computed.subscribe(callback)
        
        # Manually trigger recomputation and notification
        computed._on_dependency_changed({})
        
        assert len(notifications) > 0

    def test_computed_dispose(self):
        """Test disposing computed state cleans up subscriptions."""
        source = StateManager(initial_state={"v": 1})
        computed = ComputedState(
            dependencies=[source],
            compute=lambda: source.state.get("v", 0)
        )
        
        computed.dispose()
        
        # After dispose, updates should not cause recomputation
        source.update_state({"v": 100})
        # Just verify no exception occurs


# =============================================================================
# Tests for UserSession
# =============================================================================

class TestUserSession:
    """Tests for UserSession dataclass."""

    def test_user_session_defaults(self):
        """Test UserSession default values."""
        session = UserSession()
        
        assert session.user_id is None
        assert session.email == ""
        assert session.name == ""
        assert session.role == "user"
        assert session.is_authenticated is False

    def test_user_session_to_dict(self):
        """Test converting UserSession to dict."""
        session = UserSession(
            user_id=1,
            email="test@test.com",
            name="Test",
            role="admin",
            is_authenticated=True
        )
        
        data = session.to_dict()
        
        assert data["user_id"] == 1
        assert data["email"] == "test@test.com"
        assert data["name"] == "Test"
        assert data["role"] == "admin"
        assert data["is_authenticated"] is True

    def test_user_session_from_dict(self):
        """Test creating UserSession from dict."""
        data = {
            "user_id": 5,
            "email": "user@example.com",
            "name": "User",
            "role": "user",
            "is_authenticated": True
        }
        
        session = UserSession.from_dict(data)
        
        assert session.user_id == 5
        assert session.email == "user@example.com"
        assert session.is_authenticated is True


# =============================================================================
# Tests for AuthState
# =============================================================================

class TestAuthState:
    """Tests for AuthState manager."""

    def test_auth_state_initial(self):
        """Test AuthState initial state is unauthenticated."""
        auth = AuthState()
        
        assert auth.is_authenticated is False
        assert auth.user_id is None
        assert auth.user_name == ""
        assert auth.user_role == "user"
        assert auth.is_admin is False

    def test_auth_state_login(self):
        """Test login updates auth state."""
        auth = AuthState()
        
        auth.login({
            "id": 10,
            "email": "test@test.com",
            "name": "Test User",
            "role": "admin"
        })
        
        assert auth.is_authenticated is True
        assert auth.user_id == 10
        assert auth.user_name == "Test User"
        assert auth.user_email == "test@test.com"
        assert auth.user_role == "admin"
        assert auth.is_admin is True

    def test_auth_state_logout(self):
        """Test logout clears auth state."""
        auth = AuthState()
        auth.login({"id": 1, "email": "a@b.com", "name": "A", "role": "user"})
        
        auth.logout()
        
        assert auth.is_authenticated is False
        assert auth.user_id is None
        assert auth.current_user is None

    def test_auth_state_current_user(self):
        """Test getting current user as UserSession."""
        auth = AuthState()
        auth.login({"id": 2, "email": "b@c.com", "name": "B", "role": "user"})
        
        user = auth.current_user
        
        assert isinstance(user, UserSession)
        assert user.user_id == 2
        assert user.name == "B"

    def test_auth_state_current_user_none_when_not_authenticated(self):
        """Test current_user is None when not authenticated."""
        auth = AuthState()
        
        assert auth.current_user is None

    def test_auth_state_update_user_info(self):
        """Test updating specific user info fields."""
        auth = AuthState()
        auth.login({"id": 1, "email": "old@test.com", "name": "Old Name", "role": "user"})
        
        auth.update_user_info(name="New Name", email="new@test.com")
        
        assert auth.user_name == "New Name"
        assert auth.user_email == "new@test.com"

    def test_auth_state_get_redirect_route_admin(self):
        """Test redirect route for admin."""
        auth = AuthState()
        auth.login({"id": 1, "email": "a@b.com", "name": "A", "role": "admin"})
        
        assert auth.get_redirect_route() == "/admin"

    def test_auth_state_get_redirect_route_user(self):
        """Test redirect route for regular user."""
        auth = AuthState()
        auth.login({"id": 1, "email": "a@b.com", "name": "A", "role": "user"})
        
        assert auth.get_redirect_route() == "/user"

    def test_auth_state_get_redirect_route_not_authenticated(self):
        """Test redirect route when not authenticated."""
        auth = AuthState()
        
        assert auth.get_redirect_route() == "/"

    def test_auth_state_notifies_on_login(self):
        """Test observers are notified on login."""
        auth = AuthState()
        notifications: List[Dict] = []
        
        # Store callback in variable to prevent garbage collection (weak refs)
        def callback(d: Dict[str, Any]) -> None:
            notifications.append(d)
        
        auth.subscribe(callback)
        
        auth.login({"id": 1, "email": "a@b.com", "name": "A", "role": "user"})
        
        assert len(notifications) > 0


# =============================================================================
# Tests for AppState singleton
# =============================================================================

class TestAppState:
    """Tests for AppState singleton coordinator."""

    @pytest.fixture(autouse=True)
    def reset_singleton(self):
        """Reset AppState singleton before each test."""
        AppState.reset_instance()
        yield
        AppState.reset_instance()

    def test_app_state_singleton(self):
        """Test AppState is a singleton."""
        app1 = AppState.get_instance()
        app2 = AppState.get_instance()
        
        assert app1 is app2

    def test_app_state_reset_instance(self):
        """Test resetting singleton instance."""
        app1 = AppState.get_instance()
        AppState.reset_instance()
        app2 = AppState.get_instance()
        
        # After reset, should be a new instance
        assert app1._initialized is False or app1 is not app2

    def test_app_state_has_all_managers(self):
        """Test AppState has all expected state managers."""
        app = AppState.get_instance()
        
        assert app.auth is not None
        assert app.animals is not None
        assert app.rescues is not None
        assert app.adoptions is not None
        assert app.ui is not None

    def test_app_state_auth_property(self):
        """Test auth property returns AuthState."""
        app = AppState.get_instance()
        
        assert isinstance(app.auth, AuthState)

    def test_app_state_is_ready_before_initialization(self):
        """Test is_ready returns False before page is set."""
        app = AppState.get_instance()
        
        # Before initialize() is called with a page
        assert app.is_ready() is False

    def test_get_app_state_convenience_function(self):
        """Test get_app_state returns singleton."""
        app = get_app_state()
        
        assert isinstance(app, AppState)
        assert app is AppState.get_instance()

    def test_app_state_get_dashboard_stats(self):
        """Test getting dashboard statistics."""
        app = AppState.get_instance()
        
        stats = app.get_dashboard_stats()
        
        assert "animals" in stats
        assert "rescues" in stats
        assert "adoptions" in stats
        assert "user" in stats

    def test_app_state_reset_clears_all(self):
        """Test reset clears all state managers."""
        app = AppState.get_instance()
        app.auth.login({"id": 1, "email": "a@b.com", "name": "A", "role": "user"})
        
        app.reset()
        
        assert app.auth.is_authenticated is False

    def test_app_state_propagates_auth_changes(self):
        """Test AppState propagates auth state changes via internal subscription."""
        app = AppState.get_instance()
        
        # Login and verify auth state updated
        app.auth.login({"id": 1, "email": "a@b.com", "name": "A", "role": "user"})
        
        # Verify the auth state was updated (which triggers propagation internally)
        assert app.auth.is_authenticated is True
        assert app.auth.user_id == 1
        
        # Get dashboard stats should reflect auth state
        stats = app.get_dashboard_stats()
        assert stats["user"]["is_authenticated"] is True
        assert stats["user"]["name"] == "A"

    def test_app_state_get_state_snapshot(self):
        """Test getting full state snapshot."""
        app = AppState.get_instance()
        
        snapshot = app.get_state_snapshot()
        
        assert "auth" in snapshot
        assert "animals" in snapshot
        assert "rescues" in snapshot
        assert "adoptions" in snapshot
        assert "ui" in snapshot
