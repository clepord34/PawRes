"""Base state management classes with observer pattern."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, Generic, List, Optional, TypeVar
from dataclasses import dataclass, field
from datetime import datetime
import threading
import weakref


# Type variable for generic state
T = TypeVar('T')


class Observable:
    """Base class implementing the observer pattern."""
    
    def __init__(self):
        self._observers: List[weakref.ref] = []
        self._lock = threading.RLock()
    
    def subscribe(self, callback: Callable[[Dict[str, Any]], None]) -> Callable[[], None]:
        """Subscribe to state changes. Returns an unsubscribe function."""
        with self._lock:
            # Store weak reference to allow garbage collection
            ref = weakref.ref(callback)
            self._observers.append(ref)
            
            # Return unsubscribe function
            def unsubscribe():
                with self._lock:
                    try:
                        self._observers.remove(ref)
                    except ValueError:
                        pass  # Already removed
            
            return unsubscribe
    
    def notify_observers(self, data: Dict[str, Any]) -> None:
        """Notify all observers of a state change.
        
        Args:
            data: Dictionary containing the changed data
        """
        with self._lock:
            # Clean up dead references and collect live callbacks
            live_observers = []
            for ref in self._observers:
                callback = ref()
                if callback is not None:
                    live_observers.append(ref)
            
            self._observers = live_observers
        
        # Notify outside the lock to prevent deadlocks
        for ref in live_observers:
            callback = ref()
            if callback is not None:
                try:
                    callback(data)
                except Exception as e:
                    print(f"[ERROR] Observer callback failed: {e}")
    
    def clear_observers(self) -> None:
        """Remove all observers."""
        with self._lock:
            self._observers.clear()


@dataclass
class StateSnapshot(Generic[T]):
    """Immutable snapshot of state at a point in time.
    
    Attributes:
        data: The state data
        timestamp: When this snapshot was created
        version: Incrementing version number for change detection
    """
    data: T
    timestamp: datetime = field(default_factory=datetime.utcnow)
    version: int = 0


class StateManager(Observable, Generic[T]):
    """Generic state manager with caching and dirty tracking.
    
    Provides:
    - Centralized state storage
    - Change notification via observer pattern
    - Version tracking for optimistic concurrency
    - Dirty flag for detecting unsaved changes
    
    Example:
        class UserState(StateManager[Dict[str, Any]]):
            def __init__(self):
                super().__init__(initial_state={})
            
            def set_user(self, user_data):
                self.update_state(user_data)
        
        user_state = UserState()
        user_state.subscribe(lambda data: update_ui(data))
        user_state.set_user({"name": "Alice", "role": "admin"})
    """
    
    def __init__(self, initial_state: Optional[T] = None):
        """Initialize the state manager.
        
        Args:
            initial_state: Initial state value (defaults to empty dict)
        """
        super().__init__()
        self._state: T = initial_state if initial_state is not None else {}  # type: ignore
        self._version: int = 0
        self._is_dirty: bool = False
        self._last_sync: Optional[datetime] = None
        self._state_lock = threading.RLock()
    
    @property
    def state(self) -> T:
        """Get the current state (read-only access)."""
        with self._state_lock:
            return self._state
    
    @property
    def version(self) -> int:
        """Get the current state version."""
        with self._state_lock:
            return self._version
    
    @property
    def is_dirty(self) -> bool:
        """Check if state has unsaved changes."""
        with self._state_lock:
            return self._is_dirty
    
    @property
    def last_sync(self) -> Optional[datetime]:
        """Get timestamp of last sync with backend."""
        with self._state_lock:
            return self._last_sync
    
    def get_snapshot(self) -> StateSnapshot[T]:
        """Get an immutable snapshot of the current state.
        
        Returns:
            StateSnapshot with current data, timestamp, and version
        """
        with self._state_lock:
            return StateSnapshot(
                data=self._state,
                timestamp=datetime.utcnow(),
                version=self._version
            )
    
    def update_state(self, new_state: T, notify: bool = True) -> None:
        """Update the state and optionally notify observers.
        
        Args:
            new_state: New state value
            notify: Whether to notify observers (default True)
        """
        with self._state_lock:
            self._state = new_state
            self._version += 1
            self._is_dirty = True
        
        if notify:
            self.notify_observers({"state": new_state, "version": self._version})
    
    def patch_state(self, updates: Dict[str, Any], notify: bool = True) -> None:
        """Partially update state by merging updates.
        
        Only works if state is a dict-like object.
        
        Args:
            updates: Dictionary of updates to merge
            notify: Whether to notify observers (default True)
        """
        with self._state_lock:
            if isinstance(self._state, dict):
                self._state.update(updates)  # type: ignore
                self._version += 1
                self._is_dirty = True
        
        if notify:
            self.notify_observers({"updates": updates, "version": self._version})
    
    def mark_synced(self) -> None:
        """Mark state as synchronized with backend."""
        with self._state_lock:
            self._is_dirty = False
            self._last_sync = datetime.utcnow()
    
    def reset(self, initial_state: Optional[T] = None) -> None:
        """Reset state to initial value.
        
        Args:
            initial_state: New initial state (defaults to empty dict)
        """
        with self._state_lock:
            self._state = initial_state if initial_state is not None else {}  # type: ignore
            self._version = 0
            self._is_dirty = False
            self._last_sync = None
        
        self.notify_observers({"reset": True, "state": self._state})


class ComputedState(Observable):
    """Computed/derived state that depends on other states.
    
    Automatically updates when dependencies change.
    
    Example:
        # Create a computed state that filters animals by status
        filtered_animals = ComputedState(
            dependencies=[animal_state],
            compute=lambda: [a for a in animal_state.animals if a["status"] == "healthy"]
        )
    """
    
    def __init__(
        self,
        dependencies: List[Observable],
        compute: Callable[[], Any]
    ):
        """Initialize computed state.
        
        Args:
            dependencies: List of Observable objects this depends on
            compute: Function that computes the derived value
        """
        super().__init__()
        self._compute = compute
        self._cached_value: Any = None
        self._is_valid: bool = False
        self._unsubscribers: List[Callable[[], None]] = []
        
        # Subscribe to all dependencies
        for dep in dependencies:
            unsub = dep.subscribe(self._on_dependency_changed)
            self._unsubscribers.append(unsub)
        
        # Compute initial value
        self._recompute()
    
    @property
    def value(self) -> Any:
        """Get the computed value, recomputing if necessary."""
        if not self._is_valid:
            self._recompute()
        return self._cached_value
    
    def _on_dependency_changed(self, data: Dict[str, Any]) -> None:
        """Handle dependency change."""
        self._is_valid = False
        self._recompute()
        self.notify_observers({"value": self._cached_value})
    
    def _recompute(self) -> None:
        """Recompute the derived value."""
        try:
            self._cached_value = self._compute()
            self._is_valid = True
        except Exception as e:
            print(f"[ERROR] ComputedState computation failed: {e}")
            self._is_valid = False
    
    def dispose(self) -> None:
        """Clean up subscriptions."""
        for unsub in self._unsubscribers:
            unsub()
        self._unsubscribers.clear()
        self.clear_observers()
