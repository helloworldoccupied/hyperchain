"""Negotiation Engine — Layer 4: multi-round consensus protocol."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from hyperchain.agent import Agent, ModelAdapter


@dataclass
class NegotiationRound:
    """Record of a single negotiation round."""

    round_number: int
    actor: str
    action: str  # "propose" | "review" | "revise"
    content: str
    consensus_score: float = 0.0


@dataclass
class NegotiationResult:
    """Result of a negotiation session."""

    consensus: bool
    rounds: list[NegotiationRound] = field(default_factory=list)
    final_verdict: str = ""
    disagreements: list[str] = field(default_factory=list)

    @property
    def round_count(self) -> int:
        return len(self.rounds)


def _parse_review(response: str) -> tuple[str, float, list[str]]:
    """Parse a review response into verdict, score, and disagreements.

    Expected format from mock/real adapter:
        APPROVE 0.9
        or
        REVISE 0.5 issue1; issue2
    Falls back to heuristic parsing.
    """
    response = response.strip()
    parts = response.split(None, 2)

    verdict = parts[0].upper() if parts else "REVISE"
    score = 0.0
    disagreements: list[str] = []

    if len(parts) >= 2:
        try:
            score = float(parts[1])
        except ValueError:
            score = 1.0 if verdict == "APPROVE" else 0.3

    if len(parts) >= 3:
        disagreements = [d.strip() for d in parts[2].split(";") if d.strip()]

    if verdict == "APPROVE" and score == 0.0:
        score = 1.0

    return verdict, score, disagreements


class NegotiationEngine:
    """Multi-round consensus engine with deadlock prevention.

    Parameters
    ----------
    max_rounds : int
        Hard cap on negotiation rounds (prevents infinite loops).
    consensus_threshold : float
        Score needed to declare consensus (0.0-1.0).
    on_deadlock : str
        Action when max_rounds reached without consensus:
        "escalate" — mark as deadlocked for human review.
        "majority" — accept if last score > 0.5.
        "chair_decides" — accept writer's last proposal.
    """

    def __init__(
        self,
        max_rounds: int = 5,
        consensus_threshold: float = 0.8,
        on_deadlock: str = "escalate",
    ) -> None:
        if max_rounds < 1:
            raise ValueError("max_rounds must be >= 1")
        if not 0.0 <= consensus_threshold <= 1.0:
            raise ValueError("consensus_threshold must be between 0.0 and 1.0")
        if on_deadlock not in ("escalate", "majority", "chair_decides"):
            raise ValueError(f"Invalid on_deadlock: {on_deadlock}")

        self.max_rounds = max_rounds
        self.consensus_threshold = consensus_threshold
        self.on_deadlock = on_deadlock

    def negotiate(
        self,
        participants: list[Agent],
        topic: str,
        context: dict[str, Any] | None = None,
        adapter: ModelAdapter | None = None,
    ) -> NegotiationResult:
        """Run propose-review negotiation between participants.

        Expects exactly 2 participants: [writer, reviewer].
        The writer proposes, reviewer critiques, writer revises until
        consensus or max_rounds.
        """
        if len(participants) < 2:
            raise ValueError("Need at least 2 participants for negotiation")
        if adapter is None:
            raise ValueError("adapter is required")

        writer, reviewer = participants[0], participants[1]
        rounds: list[NegotiationRound] = []
        all_disagreements: list[str] = []
        last_score = 0.0

        ctx_str = str(context) if context else ""

        for i in range(1, self.max_rounds + 1):
            # Writer proposes (or revises)
            action = "propose" if i == 1 else "revise"
            prompt = f"[{action}] Topic: {topic}\nContext: {ctx_str}"
            if all_disagreements:
                prompt += f"\nAddress: {'; '.join(all_disagreements)}"

            proposal = adapter.invoke(prompt)
            rounds.append(NegotiationRound(
                round_number=i,
                actor=writer.role,
                action=action,
                content=proposal,
            ))

            # Reviewer critiques
            review_prompt = f"[review] Proposal: {proposal}\nTopic: {topic}"
            review_response = adapter.invoke(review_prompt)
            verdict, score, disagreements = _parse_review(review_response)
            last_score = score

            rounds.append(NegotiationRound(
                round_number=i,
                actor=reviewer.role,
                action="review",
                content=review_response,
                consensus_score=score,
            ))

            all_disagreements.extend(disagreements)

            if score >= self.consensus_threshold:
                return NegotiationResult(
                    consensus=True,
                    rounds=rounds,
                    final_verdict=proposal,
                    disagreements=all_disagreements,
                )

        # Deadlock — max_rounds reached without consensus
        return self._handle_deadlock(rounds, all_disagreements, last_score)

    def _handle_deadlock(
        self,
        rounds: list[NegotiationRound],
        disagreements: list[str],
        last_score: float,
    ) -> NegotiationResult:
        """Handle deadlock based on configured policy."""
        # Find last proposal from writer
        last_proposal = ""
        for r in reversed(rounds):
            if r.action in ("propose", "revise"):
                last_proposal = r.content
                break

        if self.on_deadlock == "majority" and last_score > 0.5:
            return NegotiationResult(
                consensus=True,
                rounds=rounds,
                final_verdict=last_proposal,
                disagreements=disagreements,
            )

        if self.on_deadlock == "chair_decides":
            return NegotiationResult(
                consensus=True,
                rounds=rounds,
                final_verdict=last_proposal,
                disagreements=disagreements,
            )

        # "escalate" or majority with low score — no consensus
        return NegotiationResult(
            consensus=False,
            rounds=rounds,
            final_verdict="",
            disagreements=disagreements,
        )
