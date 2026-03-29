"""HyperChain State Machine — manages workflow state transitions with history and callbacks."""
from __future__ import annotations

import time
from typing import Any, Callable

from hyperchain.errors import StateTransitionError

# Type alias for transition callbacks: (from_state, to_state, metadata) -> None
TransitionCallback = Callable[[str, str, dict[str, Any] | None], None]

# Built-in templates
_TEMPLATES: dict[str, dict] = {
    "code-review": {
        "states": [
            "proposed", "negotiating", "assigned", "executing",
            "reviewing", "delivered", "verified", "completed",
            "rejected", "failed",
        ],
        "transitions": {
            "proposed": ["negotiating", "rejected"],
            "negotiating": ["assigned", "rejected"],
            "assigned": ["executing", "rejected"],
            "executing": ["reviewing", "failed"],
            "reviewing": ["delivered", "rejected"],
            "delivered": ["verified", "rejected"],
            "verified": ["completed"],
            "rejected": ["executing", "proposed"],
            "failed": ["proposed"],
        },
        "initial": "proposed",
    },
}


class StateMachine:
    """A finite state machine with history tracking and transition callbacks.

    Parameters
    ----------
    states : list[str]
        All valid state names.
    transitions : dict[str, list[str]]
        Mapping of source state to list of allowed target states.
    initial : str
        The starting state (must be in *states*).
    """

    def __init__(
        self,
        states: list[str],
        transitions: dict[str, list[str]],
        initial: str,
    ) -> None:
        state_set = set(states)

        if initial not in state_set:
            raise ValueError(f"Initial state '{initial}' not in states: {states}")

        # Validate that all transition targets are known states
        for src, targets in transitions.items():
            for t in targets:
                if t not in state_set:
                    raise ValueError(f"Transition target '{t}' not in states: {states}")

        self._states = list(states)
        self._transitions = {s: list(ts) for s, ts in transitions.items()}
        self._current = initial
        self._history: list[dict[str, Any]] = []
        self._callbacks: list[TransitionCallback] = []

    # -- Properties ----------------------------------------------------------

    @property
    def current(self) -> str:
        """Return the current state."""
        return self._current

    @property
    def history(self) -> list[dict[str, Any]]:
        """Return the list of recorded transitions."""
        return list(self._history)

    @property
    def legal_transitions(self) -> list[str]:
        """Return the list of states reachable from the current state."""
        return list(self._transitions.get(self._current, []))

    # -- Mutators ------------------------------------------------------------

    def transition(self, target: str, metadata: dict[str, Any] | None = None) -> None:
        """Transition to *target* state.

        Raises
        ------
        StateTransitionError
            If *target* is not a legal transition from the current state.
        """
        legal = self.legal_transitions
        if target not in legal:
            raise StateTransitionError(self._current, target, legal)

        from_state = self._current
        self._current = target

        record: dict[str, Any] = {
            "from": from_state,
            "to": target,
            "timestamp": time.time(),
            "metadata": metadata,
        }
        self._history.append(record)

        for cb in self._callbacks:
            cb(from_state, target, metadata)

    def on_transition(self, callback: TransitionCallback) -> None:
        """Register a callback invoked on every successful transition."""
        self._callbacks.append(callback)

    # -- Factory -------------------------------------------------------------

    @classmethod
    def from_template(cls, name: str) -> StateMachine:
        """Create a StateMachine from a built-in template.

        Supported templates: ``code-review``.
        """
        if name not in _TEMPLATES:
            raise ValueError(f"Unknown template '{name}'. Available: {list(_TEMPLATES.keys())}")
        tpl = _TEMPLATES[name]
        return cls(states=tpl["states"], transitions=tpl["transitions"], initial=tpl["initial"])
