"""HyperChain custom exceptions."""


class HyperChainError(Exception):
    """Base exception for all HyperChain errors."""


class StateTransitionError(HyperChainError):
    """Raised when an illegal state transition is attempted."""
    def __init__(self, current: str, target: str, legal: list[str]):
        self.current = current
        self.target = target
        self.legal = legal
        super().__init__(f"Illegal transition: '{current}' \u2192 '{target}'. Legal targets: {legal}")


class AuditIntegrityError(HyperChainError):
    """Raised when audit chain integrity check fails."""
    def __init__(self, entry_index: int, expected_hash: str, actual_hash: str):
        self.entry_index = entry_index
        super().__init__(f"Audit chain broken at entry {entry_index}: expected prev_hash={expected_hash[:16]}..., got {actual_hash[:16]}...")


class GuardBlockedError(HyperChainError):
    """Raised when a guard blocks an action."""
    def __init__(self, guard_name: str, reason: str):
        self.guard_name = guard_name
        self.reason = reason
        super().__init__(f"Guard '{guard_name}' blocked: {reason}")


class TierMismatchError(HyperChainError):
    """Raised when reviewer model tier is lower than writer tier."""
    def __init__(self, writer_tier: int, reviewer_tier: int):
        super().__init__(f"Reviewer tier ({reviewer_tier}) must be >= writer tier ({writer_tier})")
