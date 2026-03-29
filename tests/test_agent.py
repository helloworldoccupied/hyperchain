"""Tests for Agent Factory (Layer 5)."""
import pytest

from hyperchain.agent import (
    Agent, AgentFactory, MockAdapter, ModelAdapter,
    MODEL_TIERS, validate_tier_compatibility,
)
from hyperchain.errors import TierMismatchError


class TestAgent:
    def test_create_agent_basic(self):
        agent = Agent(role="writer", model="claude-opus-4-6", tier=5)
        assert agent.role == "writer"
        assert agent.model == "claude-opus-4-6"
        assert agent.tier == 5

    def test_agent_default_fields(self):
        agent = Agent(role="test", model="mock")
        assert agent.permissions == []
        assert agent.output_schema == {}
        assert agent.tier == 1

    def test_has_permission(self):
        agent = Agent(role="writer", model="mock", permissions=["read", "write"])
        assert agent.has_permission("read") is True
        assert agent.has_permission("write") is True
        assert agent.has_permission("delete") is False


class TestAgentFactory:
    def test_create_with_known_model(self):
        factory = AgentFactory()
        agent = factory.create(role="writer", model="claude-opus-4-6")
        assert agent.tier == 5
        assert agent.role == "writer"

    def test_create_with_unknown_model_defaults_tier_1(self):
        factory = AgentFactory()
        agent = factory.create(role="test", model="some-unknown-model")
        assert agent.tier == 1

    def test_create_with_permissions_and_schema(self):
        factory = AgentFactory()
        schema = {"code": str, "explanation": str}
        agent = factory.create(
            role="writer", model="gpt-5.4",
            permissions=["read", "write", "execute"],
            output_schema=schema,
        )
        assert agent.permissions == ["read", "write", "execute"]
        assert agent.output_schema == schema
        assert agent.tier == 5

    def test_all_known_models_have_tiers(self):
        factory = AgentFactory()
        for model, expected_tier in MODEL_TIERS.items():
            agent = factory.create(role="test", model=model)
            assert agent.tier == expected_tier, f"Model {model} tier mismatch"


class TestTierCompatibility:
    def test_equal_tier_passes(self):
        writer = Agent(role="writer", model="claude-opus-4-6", tier=5)
        reviewer = Agent(role="reviewer", model="gpt-5.4", tier=5)
        validate_tier_compatibility(writer, reviewer)  # should not raise

    def test_higher_reviewer_passes(self):
        writer = Agent(role="writer", model="gpt-4o", tier=3)
        reviewer = Agent(role="reviewer", model="claude-opus-4-6", tier=5)
        validate_tier_compatibility(writer, reviewer)  # should not raise

    def test_lower_reviewer_raises(self):
        writer = Agent(role="writer", model="claude-opus-4-6", tier=5)
        reviewer = Agent(role="reviewer", model="mock", tier=1)
        with pytest.raises(TierMismatchError):
            validate_tier_compatibility(writer, reviewer)


class TestMockAdapter:
    def test_returns_default_response(self):
        adapter = MockAdapter()
        assert adapter.invoke("test") == "Mock response"

    def test_returns_custom_responses(self):
        adapter = MockAdapter(responses=["first", "second"])
        assert adapter.invoke("a") == "first"
        assert adapter.invoke("b") == "second"

    def test_cycles_responses(self):
        adapter = MockAdapter(responses=["A", "B"])
        assert adapter.invoke("1") == "A"
        assert adapter.invoke("2") == "B"
        assert adapter.invoke("3") == "A"

    def test_tracks_call_count(self):
        adapter = MockAdapter()
        assert adapter.call_count == 0
        adapter.invoke("x")
        adapter.invoke("y")
        assert adapter.call_count == 2

    def test_base_adapter_raises(self):
        adapter = ModelAdapter()
        with pytest.raises(NotImplementedError):
            adapter.invoke("test")
