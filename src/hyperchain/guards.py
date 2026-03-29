"""XiaotianQuan Guard Layer (Layer 1) - Pre-action safety guards."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Callable

from hyperchain.errors import GuardBlockedError


@dataclass
class Verdict:
    """Result of a guard check."""

    allowed: bool
    reason: str = ""
    guard_name: str = ""

    @classmethod
    def allow(cls) -> Verdict:
        return cls(allowed=True)

    @classmethod
    def block(cls, reason: str) -> Verdict:
        return cls(allowed=False, reason=reason)


GuardFn = Callable[[dict], Verdict]


class GuardRegistry:
    """Registry of guard functions keyed by event type."""

    def __init__(self) -> None:
        self._guards: dict[str, list[tuple[str, GuardFn]]] = {}

    def register(self, event: str):
        """Decorator to register a guard function for an event."""
        def decorator(fn: GuardFn) -> GuardFn:
            self.register_fn(event, fn)
            return fn
        return decorator

    def register_fn(self, event: str, fn: GuardFn) -> None:
        """Directly register a guard function for an event."""
        if event not in self._guards:
            self._guards[event] = []
        self._guards[event].append((fn.__name__, fn))

    def check(self, event: str, context: dict) -> Verdict:
        """Run all guards for an event. First block wins."""
        guards = self._guards.get(event, [])
        for name, fn in guards:
            verdict = fn(context)
            if not verdict.allowed:
                verdict.guard_name = name
                return verdict
        return Verdict.allow()

    def enforce(self, event: str, context: dict) -> None:
        """Run check and raise GuardBlockedError if blocked."""
        verdict = self.check(event, context)
        if not verdict.allowed:
            raise GuardBlockedError(
                guard_name=verdict.guard_name,
                reason=verdict.reason,
            )


def guard(event: str, tool: str | None = None):
    """Standalone decorator that tags a function with guard metadata."""
    def decorator(fn: GuardFn) -> GuardFn:
        fn._guard_event = event  # type: ignore[attr-defined]
        fn._guard_tool = tool  # type: ignore[attr-defined]
        return fn
    return decorator


# ---------------------------------------------------------------------------
# Built-in guards
# ---------------------------------------------------------------------------

_DESTRUCTIVE_PATTERNS = [
    re.compile(r"rm\s+-rf\s+/"),
    re.compile(r"DROP\s+TABLE", re.IGNORECASE),
    re.compile(r"git\s+reset\s+--hard"),
    re.compile(r"git\s+push\s+--force"),
    re.compile(r"git\s+push\s+.*\b(main|master)\b"),
]


def _guard_destructive_bash(ctx: dict) -> Verdict:
    """Block destructive bash commands."""
    cmd = ctx.get("command", "")
    for pattern in _DESTRUCTIVE_PATTERNS:
        if pattern.search(cmd):
            return Verdict.block(f"Destructive command blocked: {pattern.pattern}")
    return Verdict.allow()


BUILTIN_GUARDS: list[tuple[str, GuardFn]] = [
    ("bash", _guard_destructive_bash),
]
