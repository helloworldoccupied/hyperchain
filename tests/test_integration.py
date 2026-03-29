"""Integration tests — all 3 layers working together."""
import pytest
from hyperchain import StateMachine, AuditChain, GuardRegistry, Verdict
from hyperchain.errors import GuardBlockedError


class TestLayersIntegrated:
    def test_state_machine_with_audit_chain(self):
        sm = StateMachine.from_template("code-review")
        chain = AuditChain()
        sm.on_transition(lambda frm, to, meta: chain.record(
            task_id="task-001", actor=meta.get("actor", "system"),
            action=f"{frm}_to_{to}",
        ))
        sm.transition("negotiating", metadata={"actor": "claude"})
        sm.transition("assigned", metadata={"actor": "human"})
        assert len(chain.entries) == 2
        assert chain.entries[0]["actor"] == "claude"
        assert chain.verify_integrity() is True

    def test_guard_blocks_illegal_delivery(self):
        registry = GuardRegistry()
        @registry.register(event="pre_delivery")
        def require_evidence(ctx):
            if not ctx.get("evidence"):
                return Verdict.block("Delivery requires evidence")
            return Verdict.allow()
        with pytest.raises(GuardBlockedError, match="evidence"):
            registry.enforce("pre_delivery", {"evidence": []})
        registry.enforce("pre_delivery", {"evidence": ["test.log"]})

    def test_full_pipeline_flow(self, tmp_path):
        sm = StateMachine.from_template("code-review")
        chain = AuditChain(storage=tmp_path / "audit")
        registry = GuardRegistry()
        @registry.register(event="pre_transition")
        def allow_all(ctx):
            return Verdict.allow()
        sm.on_transition(lambda frm, to, meta: chain.record(
            task_id="demo", actor=meta.get("actor", "?"), action=f"{frm}->{to}",
        ))
        for step, actor in [
            ("negotiating", "claude"), ("assigned", "human"),
            ("executing", "claude"), ("reviewing", "gpt"),
            ("delivered", "claude"), ("verified", "human"),
            ("completed", "human"),
        ]:
            registry.enforce("pre_transition", {"target": step})
            sm.transition(step, metadata={"actor": actor})
        assert sm.current == "completed"
        assert len(chain.entries) == 7
        assert chain.verify_integrity() is True
        chain.save()
        assert (tmp_path / "audit" / "chain.json").exists()
