"""HyperChain: Enterprise Multi-AI Governance Framework."""
__version__ = "0.1.0"

from hyperchain.state_machine import StateMachine
from hyperchain.audit_chain import AuditChain
from hyperchain.guards import GuardRegistry, Verdict, guard
from hyperchain.agent import Agent, AgentFactory, ModelAdapter, MockAdapter, validate_tier_compatibility
from hyperchain.negotiation import NegotiationEngine, NegotiationResult
from hyperchain.pipeline import Pipeline, PipelineResult
from hyperchain.errors import (
    HyperChainError, StateTransitionError, AuditIntegrityError,
    GuardBlockedError, TierMismatchError,
)

__all__ = [
    "StateMachine", "AuditChain", "GuardRegistry", "Verdict", "guard",
    "Agent", "AgentFactory", "ModelAdapter", "MockAdapter", "validate_tier_compatibility",
    "NegotiationEngine", "NegotiationResult",
    "Pipeline", "PipelineResult",
    "HyperChainError", "StateTransitionError", "AuditIntegrityError",
    "GuardBlockedError", "TierMismatchError",
]
