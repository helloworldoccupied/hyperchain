"""Tests for Pipeline (integration of all 5 layers)."""
import pytest

from hyperchain.agent import Agent, AgentFactory, MockAdapter, validate_tier_compatibility
from hyperchain.audit_chain import AuditChain
from hyperchain.guards import GuardRegistry
from hyperchain.negotiation import NegotiationEngine
from hyperchain.pipeline import Pipeline, PipelineResult
from hyperchain.state_machine import StateMachine
from hyperchain.errors import TierMismatchError


class TestPipeline:
    def test_from_template(self):
        pipeline = Pipeline.from_template("code-review")
        assert pipeline.state_machine.current == "proposed"

    def test_full_run_completes(self):
        factory = AgentFactory()
        writer = factory.create(role="writer", model="gpt-5.4",
                                permissions=["read", "write"])
        reviewer = factory.create(role="reviewer", model="claude-opus-4-6",
                                  permissions=["read", "comment"])

        # Mock: propose, approve, execute, review
        adapter = MockAdapter(responses=[
            "proposal text",     # writer propose
            "APPROVE 0.9",       # reviewer approve
            "executed code",     # writer execute
            "APPROVE review",    # reviewer review
        ])
        pipeline = Pipeline.from_template("code-review")
        result = pipeline.run(
            task="Implement auth module",
            agents={"writer": writer, "reviewer": reviewer},
            adapter=adapter,
        )
        assert result.status == "completed"
        assert result.negotiation_result is not None
        assert result.negotiation_result.consensus is True
        assert len(result.audit_chain.entries) > 0

    def test_tier_mismatch_fails(self):
        factory = AgentFactory()
        writer = factory.create(role="writer", model="claude-opus-4-6")  # tier 5
        reviewer = factory.create(role="reviewer", model="mock")  # tier 1

        pipeline = Pipeline.from_template("code-review")
        result = pipeline.run(
            task="test",
            agents={"writer": writer, "reviewer": reviewer},
        )
        assert result.status == "failed"
        assert "error" in result.agent_outputs

    def test_missing_agents_fails(self):
        pipeline = Pipeline.from_template("code-review")
        result = pipeline.run(
            task="test",
            agents={"writer": Agent(role="writer", model="mock", tier=1)},
        )
        assert result.status == "failed"

    def test_deadlock_returns_deadlocked(self):
        factory = AgentFactory()
        writer = factory.create(role="writer", model="gpt-5.4")
        reviewer = factory.create(role="reviewer", model="claude-opus-4-6")

        # Reviewer always rejects
        adapter = MockAdapter(responses=["proposal", "REVISE 0.2 bad"])
        pipeline = Pipeline.from_template("code-review")
        neg = NegotiationEngine(max_rounds=2, consensus_threshold=0.9, on_deadlock="escalate")
        result = pipeline.run(
            task="test",
            agents={"writer": writer, "reviewer": reviewer},
            negotiation=neg,
            adapter=adapter,
        )
        assert result.status == "deadlocked"
        assert result.negotiation_result is not None
        assert result.negotiation_result.consensus is False

    def test_audit_chain_records_all_steps(self):
        factory = AgentFactory()
        writer = factory.create(role="writer", model="gpt-5.4")
        reviewer = factory.create(role="reviewer", model="claude-opus-4-6")

        adapter = MockAdapter(responses=[
            "proposal", "APPROVE 0.95",
            "code output", "APPROVE review",
        ])
        pipeline = Pipeline.from_template("code-review")
        result = pipeline.run(
            task="audit test",
            agents={"writer": writer, "reviewer": reviewer},
            adapter=adapter,
        )
        assert result.status == "completed"
        # Should have: start, negotiation_complete, assigned, executed, reviewed, delivered, verified, completed
        actions = [e["action"] for e in result.audit_chain.entries]
        assert "start" in actions
        assert "completed" in actions
        assert result.audit_chain.verify_integrity() is True

    def test_state_machine_ends_at_completed(self):
        factory = AgentFactory()
        writer = factory.create(role="writer", model="gpt-5.4")
        reviewer = factory.create(role="reviewer", model="claude-opus-4-6")

        adapter = MockAdapter(responses=[
            "proposal", "APPROVE 0.9", "code", "review ok",
        ])
        pipeline = Pipeline.from_template("code-review")
        result = pipeline.run(
            task="sm test",
            agents={"writer": writer, "reviewer": reviewer},
            adapter=adapter,
        )
        assert result.status == "completed"
        assert pipeline.state_machine.current == "completed"
