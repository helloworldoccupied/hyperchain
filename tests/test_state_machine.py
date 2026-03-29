"""Tests for HyperChain State Machine (Layer 3)."""
import time
import pytest
from hyperchain.state_machine import StateMachine
from hyperchain.errors import StateTransitionError


class TestStateMachineCreation:
    """Tests for StateMachine initialization and validation."""

    def test_initial_state(self):
        sm = StateMachine(
            states=["draft", "review", "done"],
            transitions={"draft": ["review"], "review": ["done"]},
            initial="draft",
        )
        assert sm.current == "draft"

    def test_invalid_initial_raises(self):
        with pytest.raises(ValueError, match="not in states"):
            StateMachine(
                states=["draft", "review"],
                transitions={"draft": ["review"]},
                initial="nonexistent",
            )

    def test_transition_to_unlisted_raises(self):
        with pytest.raises(ValueError, match="not in states"):
            StateMachine(
                states=["draft", "review"],
                transitions={"draft": ["unknown_target"]},
                initial="draft",
            )


class TestStateMachineTransitions:
    """Tests for state transition logic."""

    @pytest.fixture
    def simple_sm(self):
        return StateMachine(
            states=["a", "b", "c"],
            transitions={"a": ["b"], "b": ["c", "a"]},
            initial="a",
        )

    def test_legal_transition(self, simple_sm):
        simple_sm.transition("b")
        assert simple_sm.current == "b"

    def test_illegal_transition_raises(self, simple_sm):
        with pytest.raises(StateTransitionError) as exc_info:
            simple_sm.transition("c")
        err = exc_info.value
        assert err.current == "a"
        assert err.target == "c"
        assert err.legal == ["b"]

    def test_chain_of_transitions(self, simple_sm):
        simple_sm.transition("b")
        simple_sm.transition("c")
        assert simple_sm.current == "c"

    def test_rejected_can_restart(self):
        sm = StateMachine(
            states=["proposed", "reviewing", "rejected", "completed"],
            transitions={
                "proposed": ["reviewing"],
                "reviewing": ["completed", "rejected"],
                "rejected": ["proposed"],
            },
            initial="proposed",
        )
        sm.transition("reviewing")
        sm.transition("rejected")
        sm.transition("proposed")
        assert sm.current == "proposed"

    def test_terminal_state_no_transitions(self):
        sm = StateMachine(
            states=["start", "end"],
            transitions={"start": ["end"]},
            initial="start",
        )
        sm.transition("end")
        assert sm.legal_transitions == []
        with pytest.raises(StateTransitionError):
            sm.transition("start")


class TestStateMachineHistory:
    """Tests for transition history tracking."""

    def test_records_transitions(self):
        sm = StateMachine(
            states=["a", "b", "c"],
            transitions={"a": ["b"], "b": ["c"]},
            initial="a",
        )
        sm.transition("b")
        sm.transition("c")
        assert len(sm.history) == 2
        assert sm.history[0]["from"] == "a"
        assert sm.history[0]["to"] == "b"
        assert sm.history[1]["from"] == "b"
        assert sm.history[1]["to"] == "c"

    def test_includes_timestamps(self):
        sm = StateMachine(
            states=["a", "b"],
            transitions={"a": ["b"]},
            initial="a",
        )
        before = time.time()
        sm.transition("b")
        after = time.time()
        ts = sm.history[0]["timestamp"]
        assert before <= ts <= after

    def test_includes_metadata(self):
        sm = StateMachine(
            states=["a", "b"],
            transitions={"a": ["b"]},
            initial="a",
        )
        sm.transition("b", metadata={"reason": "test", "author": "claude"})
        assert sm.history[0]["metadata"] == {"reason": "test", "author": "claude"}


class TestStateMachineCallbacks:
    """Tests for on_transition callbacks."""

    def test_on_transition_callback(self):
        sm = StateMachine(
            states=["a", "b"],
            transitions={"a": ["b"]},
            initial="a",
        )
        calls = []
        sm.on_transition(lambda f, t, m: calls.append((f, t, m)))
        sm.transition("b", metadata={"x": 1})
        assert calls == [("a", "b", {"x": 1})]

    def test_multiple_callbacks(self):
        sm = StateMachine(
            states=["a", "b"],
            transitions={"a": ["b"]},
            initial="a",
        )
        results_1 = []
        results_2 = []
        sm.on_transition(lambda f, t, m: results_1.append(t))
        sm.on_transition(lambda f, t, m: results_2.append(t))
        sm.transition("b")
        assert results_1 == ["b"]
        assert results_2 == ["b"]


class TestPipelineTemplate:
    """Tests for built-in pipeline templates."""

    def test_code_review_pipeline(self):
        sm = StateMachine.from_template("code-review")
        assert sm.current == "proposed"

        # Full happy path
        sm.transition("negotiating")
        sm.transition("assigned")
        sm.transition("executing")
        sm.transition("reviewing")
        sm.transition("delivered")
        sm.transition("verified")
        sm.transition("completed")
        assert sm.current == "completed"

    def test_code_review_pipeline_rejection(self):
        sm = StateMachine.from_template("code-review")
        sm.transition("negotiating")
        sm.transition("assigned")
        sm.transition("executing")
        sm.transition("reviewing")
        sm.transition("rejected")
        # Rejected can go back to executing
        sm.transition("executing")
        assert sm.current == "executing"

    def test_unknown_template_raises(self):
        with pytest.raises(ValueError, match="Unknown template"):
            StateMachine.from_template("nonexistent")
