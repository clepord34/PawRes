"""State management module for centralized app state."""
from __future__ import annotations

from .base import StateManager, Observable
from .auth_state import AuthState
from .animal_state import AnimalState
from .rescue_state import RescueState
from .adoption_state import AdoptionState
from .ui_state import UIState
from .app_state import AppState, get_app_state

__all__ = [
    "StateManager",
    "Observable",
    "AuthState",
    "AnimalState",
    "RescueState",
    "AdoptionState",
    "UIState",
    "AppState",
    "get_app_state",
]
