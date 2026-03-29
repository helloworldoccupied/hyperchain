"""Pipeline — integrates all 5 layers into a runnable workflow."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from hyperchain.agent import Agent, AgentFactory, ModelAdapter, MockAdapter, validate_tier_compatibility
from hyperchain.audit_chain import AuditChain
from hyperchain.guards import GuardRegistry, Verdict
from hyperchain.negotiation import NegotiationEngine, NegotiationResult
from hyperchain.state_machine import StateMachine


@dataclass
class PipelineResult:
    """Result of a pipeline execution."""

    status: str  # "completed" | "failed" | "deadlocked"
    audit_chain: AuditChain
    agent_outputs: dict[str, Any] = field(default_factory=dict)
    negotiation_result: NegotiationResult | None = None


class Pipeline:
    """Orchestrates agents, negotiation, state machine, audit chain, and guards.

    Parameters
    ----------
    sm : StateMachine
        The state machine governing the workflow.
    audit : AuditChain
        Audit chain for recording actions.
    guards : GuardRegistry | None
        Optional guard registry for enforcement.
    """

    def __init__(
        self,
        sm: StateMachine,
        audit: AuditChain | None = None,
        guards: GuardRegistry | None = None,
    ) -> None:
        self._sm = sm
        self._audit = audit or AuditChain()
        self._guards = guards or GuardRegistry()

    @property
    def state_machine(self) -> StateMachine:
        return self._sm

    @property
    def audit_chain(self) -> AuditChain:
        return self._audit

    @classmethod
    def from_template(cls, name: str) -> Pipeline:
        """Create a pre-configured pipeline from a built-in template.

        Supported templates: ``code-review``.
        """
        sm = StateMachine.from_template(name)
        return cls(sm=sm)

    def run(
        self,
        task: str,
        agents: dict[str, Agent],
        negotiation: NegotiationEngine | None = None,
        adapter: ModelAdapter | None = None,
        guards: list[str] | None = None,
    ) -> PipelineResult:
        """Execute the full pipeline for a task.

        Steps (code-review template):
        1. proposed -> negotiating: agents negotiate
        2. negotiating -> assigned
        3. assigned -> executing: writer produces output
        4. executing -> reviewing: reviewer reviews
        5. reviewing -> delivered
        6. delivered -> verified
        7. verified -> completed

        Parameters
        ----------
        task : str
            Description of the task.
        agents : dict[str, Agent]
            Named agents (must include "writer" and "reviewer" for code-review).
        negotiation : NegotiationEngine | None
            Negotiation engine (optional — uses default if None).
        adapter : ModelAdapter | None
            Model adapter for LLM calls (required for negotiation/execution).
        guards : list[str] | None
            Guard names to enforce (currently unused in MVP, reserved).
        """
        task_id = f"task-{id(self)}"
        writer = agents.get("writer")
        reviewer = agents.get("reviewer")

        if not writer or not reviewer:
            return PipelineResult(
                status="failed",
                audit_chain=self._audit,
                agent_outputs={"error": "Missing required agents: writer and reviewer"},
            )

        # Tier compatibility check
        try:
            validate_tier_compatibility(writer, reviewer)
        except Exception as e:
            self._audit.record(task_id=task_id, actor="pipeline", action="tier_check_failed",
                              evidence=str(e))
            return PipelineResult(
                status="failed",
                audit_chain=self._audit,
                agent_outputs={"error": str(e)},
            )

        # Use a default adapter if none provided
        _adapter = adapter or MockAdapter()

        # Step 1: proposed -> negotiating
        self._audit.record(task_id=task_id, actor="pipeline", action="start", evidence=task)
        self._sm.transition("negotiating")

        # Step 2: Run negotiation
        neg_engine = negotiation or NegotiationEngine(max_rounds=3)
        neg_result = neg_engine.negotiate(
            participants=[writer, reviewer],
            topic=task,
            context={"task": task},
            adapter=_adapter,
        )
        self._audit.record(
            task_id=task_id, actor=writer.role, action="negotiation_complete",
            evidence=f"consensus={neg_result.consensus}, rounds={neg_result.round_count}",
        )

        if not neg_result.consensus:
            return PipelineResult(
                status="deadlocked",
                audit_chain=self._audit,
                negotiation_result=neg_result,
                agent_outputs={"disagreements": neg_result.disagreements},
            )

        # Step 3: negotiating -> assigned
        self._sm.transition("assigned")
        self._audit.record(task_id=task_id, actor="pipeline", action="assigned",
                          evidence=f"writer={writer.model}")

        # Step 4: assigned -> executing
        self._sm.transition("executing")
        writer_output = _adapter.invoke(f"Execute: {task}")
        self._audit.record(
            task_id=task_id, actor=writer.model, action="executed",
            output_data=writer_output,
        )

        # Step 5: executing -> reviewing
        self._sm.transition("reviewing")
        review_output = _adapter.invoke(f"Review: {writer_output}")
        self._audit.record(
            task_id=task_id, actor=reviewer.model, action="reviewed",
            input_data=writer_output, output_data=review_output,
        )

        # Step 6: reviewing -> delivered
        self._sm.transition("delivered")
        self._audit.record(task_id=task_id, actor="pipeline", action="delivered",
                          evidence=review_output)

        # Step 7: delivered -> verified
        self._sm.transition("verified")
        self._audit.record(task_id=task_id, actor="pipeline", action="verified")

        # Step 8: verified -> completed
        self._sm.transition("completed")
        self._audit.record(task_id=task_id, actor="pipeline", action="completed")

        return PipelineResult(
            status="completed",
            audit_chain=self._audit,
            agent_outputs={"writer": writer_output, "reviewer": review_output},
            negotiation_result=neg_result,
        )
