"""HyperChain: Enterprise Multi-AI Governance Framework."""
__version__ = "0.1.0"

from hyperchain.state_machine import StateMachine
from hyperchain.audit_chain import AuditChain
from hyperchain.guards import GuardRegistry, Verdict, guard
from hyperchain.errors import (
    HyperChainError, StateTransitionError, AuditIntegrityError,
    GuardBlockedError, TierMismatchError,
)

__all__ = [
    "StateMachine", "AuditChain", "GuardRegistry", "Verdict", "guard",
    "HyperChainError", "StateTransitionError", "AuditIntegrityError",
    "GuardBlockedError", "TierMismatchError",
]
