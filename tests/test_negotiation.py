"""Tests for Negotiation Engine (Layer 4)."""
import pytest

from hyperchain.agent import Agent, MockAdapter
from hyperchain.negotiation import NegotiationEngine, NegotiationResult, _parse_review


class TestParseReview:
    def test_approve_with_score(self):
        verdict, score, disagreements = _parse_review("APPROVE 0.95")
        assert verdict == "APPROVE"
        assert score == 0.95
        assert disagreements == []

    def test_revise_with_issues(self):
        verdict, score, disagreements = _parse_review("REVISE 0.4 missing tests; bad naming")
        assert verdict == "REVISE"
        assert score == 0.4
        assert disagreements == ["missing tests", "bad naming"]

    def test_approve_no_score(self):
        verdict, score, _ = _parse_review("APPROVE")
        assert verdict == "APPROVE"
        assert score == 1.0


class TestNegotiationEngine:
    def _make_agents(self):
        writer = Agent(role="writer", model="claude-opus-4-6", tier=5)
        reviewer = Agent(role="reviewer", model="gpt-5.4", tier=5)
        return writer, reviewer

    def test_immediate_consensus(self):
        writer, reviewer = self._make_agents()
        # Writer proposes, reviewer approves immediately
        adapter = MockAdapter(responses=["My proposal", "APPROVE 0.9"])
        engine = NegotiationEngine(max_rounds=5, consensus_threshold=0.8)
        result = engine.negotiate([writer, reviewer], "test topic", adapter=adapter)
        assert result.consensus is True
        assert result.round_count == 2  # 1 propose + 1 review
        assert result.final_verdict == "My proposal"

    def test_consensus_after_revision(self):
        writer, reviewer = self._make_agents()
        # Round 1: propose + reject, Round 2: revise + approve
        adapter = MockAdapter(responses=[
            "First draft",
            "REVISE 0.3 needs more detail",
            "Revised draft",
            "APPROVE 0.85",
        ])
        engine = NegotiationEngine(max_rounds=5, consensus_threshold=0.8)
        result = engine.negotiate([writer, reviewer], "code review", adapter=adapter)
        assert result.consensus is True
        assert result.round_count == 4  # 2 rounds x 2 entries each

    def test_deadlock_escalate(self):
        writer, reviewer = self._make_agents()
        # Reviewer always rejects
        adapter = MockAdapter(responses=["proposal", "REVISE 0.2 still bad"])
        engine = NegotiationEngine(max_rounds=2, consensus_threshold=0.8, on_deadlock="escalate")
        result = engine.negotiate([writer, reviewer], "topic", adapter=adapter)
        assert result.consensus is False
        assert result.final_verdict == ""

    def test_deadlock_majority_passes(self):
        writer, reviewer = self._make_agents()
        # Last score is 0.6 > 0.5, majority policy accepts
        adapter = MockAdapter(responses=["proposal", "REVISE 0.6 minor issue"])
        engine = NegotiationEngine(max_rounds=1, consensus_threshold=0.8, on_deadlock="majority")
        result = engine.negotiate([writer, reviewer], "topic", adapter=adapter)
        assert result.consensus is True

    def test_deadlock_majority_fails(self):
        writer, reviewer = self._make_agents()
        # Last score is 0.3 <= 0.5, majority policy rejects
        adapter = MockAdapter(responses=["proposal", "REVISE 0.3 major issues"])
        engine = NegotiationEngine(max_rounds=1, consensus_threshold=0.8, on_deadlock="majority")
        result = engine.negotiate([writer, reviewer], "topic", adapter=adapter)
        assert result.consensus is False

    def test_deadlock_chair_decides(self):
        writer, reviewer = self._make_agents()
        adapter = MockAdapter(responses=["my proposal", "REVISE 0.2 nope"])
        engine = NegotiationEngine(max_rounds=1, consensus_threshold=0.8, on_deadlock="chair_decides")
        result = engine.negotiate([writer, reviewer], "topic", adapter=adapter)
        assert result.consensus is True
        assert result.final_verdict == "my proposal"

    def test_disagreements_preserved(self):
        writer, reviewer = self._make_agents()
        adapter = MockAdapter(responses=["draft", "APPROVE 0.9"])
        engine = NegotiationEngine(max_rounds=5, consensus_threshold=0.8)
        result = engine.negotiate([writer, reviewer], "topic", adapter=adapter)
        assert isinstance(result.disagreements, list)

    def test_invalid_params(self):
        with pytest.raises(ValueError):
            NegotiationEngine(max_rounds=0)
        with pytest.raises(ValueError):
            NegotiationEngine(consensus_threshold=1.5)
        with pytest.raises(ValueError):
            NegotiationEngine(on_deadlock="invalid")

    def test_too_few_participants(self):
        adapter = MockAdapter()
        engine = NegotiationEngine()
        writer = Agent(role="writer", model="mock", tier=1)
        with pytest.raises(ValueError, match="at least 2"):
            engine.negotiate([writer], "topic", adapter=adapter)

    def test_adapter_required(self):
        engine = NegotiationEngine()
        writer = Agent(role="writer", model="mock", tier=1)
        reviewer = Agent(role="reviewer", model="mock", tier=1)
        with pytest.raises(ValueError, match="adapter is required"):
            engine.negotiate([writer, reviewer], "topic")
