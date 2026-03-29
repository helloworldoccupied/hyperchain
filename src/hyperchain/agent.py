"""Agent Factory — Layer 5: model-agnostic agent creation with tier enforcement."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from hyperchain.errors import TierMismatchError

# Model tier mapping — higher tier = more capable
MODEL_TIERS: dict[str, int] = {
    "claude-opus-4-6": 5,
    "gpt-5.4": 5,
    "grok-4.20": 4,
    "claude-sonnet-4-6": 4,
    "gpt-4o": 3,
    "local/llama": 2,
    "mock": 1,
}


@dataclass
class Agent:
    """An AI agent with role, model binding, permissions, and output contract."""

    role: str
    model: str
    permissions: list[str] = field(default_factory=list)
    output_schema: dict[str, Any] = field(default_factory=dict)
    tier: int = 1

    def has_permission(self, perm: str) -> bool:
        """Check if this agent has a specific permission."""
        return perm in self.permissions


class ModelAdapter:
    """Base class for model adapters — subclass for each LLM backend."""

    def invoke(self, prompt: str, **kwargs: Any) -> str:
        """Send a prompt to the model and return the response text."""
        raise NotImplementedError("Subclasses must implement invoke()")


class MockAdapter(ModelAdapter):
    """Mock adapter that returns canned responses for testing."""

    def __init__(self, responses: list[str] | None = None) -> None:
        self._responses = list(responses) if responses else ["Mock response"]
        self._call_count = 0

    @property
    def call_count(self) -> int:
        return self._call_count

    def invoke(self, prompt: str, **kwargs: Any) -> str:
        self._call_count += 1
        idx = (self._call_count - 1) % len(self._responses)
        return self._responses[idx]


class AgentFactory:
    """Factory for creating agents with automatic tier assignment."""

    def create(
        self,
        role: str,
        model: str,
        permissions: list[str] | None = None,
        output_schema: dict[str, Any] | None = None,
    ) -> Agent:
        """Create an agent with the given role and model.

        The tier is automatically looked up from MODEL_TIERS.
        Unknown models default to tier 1.
        """
        tier = MODEL_TIERS.get(model, 1)
        return Agent(
            role=role,
            model=model,
            permissions=permissions or [],
            output_schema=output_schema or {},
            tier=tier,
        )


def validate_tier_compatibility(writer: Agent, reviewer: Agent) -> None:
    """Ensure reviewer tier >= writer tier.

    Raises TierMismatchError if the reviewer is weaker than the writer.
    """
    if reviewer.tier < writer.tier:
        raise TierMismatchError(writer.tier, reviewer.tier)
