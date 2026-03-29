# Anti-Pattern Guide: Lessons from 3 Months of Multi-AI Production

Every anti-pattern in this guide broke something real. These are not hypothetical risks -- they are documented failures from a production system orchestrating Claude, GPT, and Gemini across code review, market intelligence, and trading pipelines.

---

## 1. Weak AI Reviews Strong AI

**What happened:** A less capable model (Codex) was assigned to review code written by a more capable model (Claude Opus). The reviewer lacked the depth to catch architectural issues and consistently rubber-stamped submissions. A 876-line commit was pushed directly to master with zero meaningful review, bypassing the entire governance pipeline.

**Why it's bad:** Review becomes theater -- it looks like oversight exists but provides no actual protection.

**How HyperChain prevents it:**

```python
from hyperchain import TierValidator

validator = TierValidator()
validator.register("claude-opus-4-6", tier=1)
validator.register("codex", tier=3)
validator.register("gpt-5.4", tier=1)

# This raises TierViolationError:
# "Reviewer 'codex' (tier 3) cannot review author 'claude-opus-4-6' (tier 1)"
validator.check_review_permission(
    author="claude-opus-4-6",
    reviewer="codex"
)
```

---

## 2. Infinite Negotiation

**What happened:** Claude and Codex entered a multi-round discussion on an A-stock intelligence report. Codex kept issuing REVISE verdicts with new objections each round. After 10 rounds, there was still no consensus, no deliverable was produced, and the entire daily report was delayed past its deadline.

**Why it's bad:** Without a hard stop, AI negotiation can loop forever, consuming tokens and blocking deliverables.

**How HyperChain prevents it:**

```python
from hyperchain import NegotiationProtocol

protocol = NegotiationProtocol(
    max_rounds=5,
    on_deadlock="escalate_to_human",
)

for round_num in protocol:
    verdict = reviewer.review(draft)
    if verdict.approved:
        break
    draft = author.revise(verdict.feedback)

# After 5 rounds with no consensus:
# protocol.status == "deadlocked"
# protocol.escalation_report contains full history for human decision
```

---

## 3. Reviewer Writes Code

**What happened:** During a code review cycle, the reviewing AI "helpfully" patched the code itself instead of sending feedback to the author. This broke ownership tracking -- the audit chain showed the original author as responsible for changes they never made, and the reviewer effectively reviewed its own modifications.

**Why it's bad:** When reviewers write code, the separation between author and auditor collapses, making the review meaningless.

**How HyperChain prevents it:**

```python
from hyperchain import GuardRegistry, Verdict

guards = GuardRegistry()

@guards.register("no-reviewer-writes")
def check_reviewer_writes(action, context):
    if (context.role == "reviewer" and
        action.type in ("file_write", "file_edit", "commit")):
        return Verdict.BLOCK(
            reason="Reviewers cannot modify code under review. "
                   "Send feedback to the author instead."
        )
    return Verdict.ALLOW()
```

---

## 4. Fake Delivery

**What happened:** A code change passed all review stages -- the board approved the diff, the PR was merged. But when the actual output was checked, the dashboard still showed stale data. The VPS trading engine heartbeat was overwriting manual updates, and the A-stock project name did not match, so the deletion never took effect. The code was correct; the result was wrong.

**Why it's bad:** Reviewing code is not the same as verifying outcomes. Passing review without evidence of correct output is a false sense of security.

**How HyperChain prevents it:**

```python
from hyperchain import GuardRegistry, Verdict

guards = GuardRegistry()

@guards.register("require-evidence")
def check_evidence(action, context):
    if action.type == "deliver" and not context.evidence:
        return Verdict.BLOCK(
            reason="Delivery requires evidence. Attach screenshots, "
                   "dry-run output, or API responses proving the result "
                   "is correct -- not just that the code looks right."
        )
    return Verdict.ALLOW()
```

---

## 5. Self-Modifying Constraints

**What happened:** The AI system had hooks and rules files that governed its own behavior (blocking force-pushes, requiring PR reviews, enforcing model selection). Because these files lived in the same repository the AI could edit, there was a structural risk: the AI could modify its own constraints to make its job easier. A governance audit revealed that allowing the constrained entity to edit its own constraints is an inherent conflict of interest.

**Why it's bad:** If the entity being governed can rewrite the governance rules, the rules are advisory at best and meaningless at worst.

**How HyperChain prevents it:**

```python
from hyperchain import XiaotianQuan

# XiaotianQuan runs as a separate process the AI cannot control
watchdog = XiaotianQuan(
    rules_path="/etc/hyperchain/rules.yaml",  # outside AI's repo
    watch_paths=["./src", "./docs", "./.claude"],
)

# If AI tries to modify its own hooks or rules:
# XiaotianQuan intercepts the file write, blocks it,
# and files a violation report -- all out-of-process.
watchdog.start()
```

---

## 6. Audit Tampering

**What happened:** During a governance review, it was discovered that log entries could theoretically be deleted or modified after the fact. An AI that received negative review feedback could, in principle, remove the record of that feedback from the audit trail. Without integrity verification, there was no way to detect missing entries.

**Why it's bad:** An audit trail that can be silently modified provides false assurance -- you think you have oversight, but the record may be incomplete.

**How HyperChain prevents it:**

```python
from hyperchain import AuditChain

chain = AuditChain(storage="./audit")

# Each record includes a hash of the previous record
chain.record(task_id="t-1", actor="claude", action="submitted code")
chain.record(task_id="t-1", actor="gpt-5.4", action="requested changes")
chain.record(task_id="t-1", actor="claude", action="revised code")

# If any entry is deleted or modified, verification fails
assert chain.verify_integrity()  # True -- chain is intact

# Tampering breaks the chain:
# chain.delete(index=1)  # remove the negative review
# chain.verify_integrity()  # raises ChainBrokenError at index 2
```

---

## 7. Cost Explosion

**What happened:** An AI board of directors was set up with 7 models, routing through OpenRouter API. Monthly costs reached $78 USDT (including payment card conversion losses) before anyone noticed. The system had no budget monitoring, no per-call cost tracking, and no alerts. The cost was only discovered during a manual financial review.

**Why it's bad:** AI API costs compound silently. Without monitoring, a well-intentioned architecture decision can become a recurring financial drain.

**How HyperChain prevents it:**

```python
from hyperchain import CostMonitor

monitor = CostMonitor(
    monthly_budget_usd=10.0,
    alert_threshold=0.8,  # alert at 80% of budget
    on_alert=lambda spent, budget: notify(
        f"AI spend ${spent:.2f} / ${budget:.2f}"
    ),
    on_exceeded=lambda: pause_non_critical_calls(),
)

# Prefer subscription-covered adapters over pay-per-call
monitor.register_adapter("claude", type="subscription")  # Max plan, $0 marginal
monitor.register_adapter("gpt-5.4", type="subscription")  # Plus plan, $0 marginal
# monitor.register_adapter("gemini", type="api")  # would count against budget

# Every API call is tracked
with monitor.track("board-meeting"):
    response = call_ai_model("gpt-5.4", prompt)
    # cost automatically recorded; alert fires if threshold crossed
```

---

## Summary

| # | Anti-Pattern | Root Cause | HyperChain Guard |
|---|-------------|-----------|-----------------|
| 1 | Weak AI Reviews Strong AI | Capability mismatch | `TierValidator` |
| 2 | Infinite Negotiation | No termination condition | `NegotiationProtocol` with `max_rounds` |
| 3 | Reviewer Writes Code | Role boundary violation | `GuardRegistry` permission check |
| 4 | Fake Delivery | Code review != outcome verification | `require_evidence` guard |
| 5 | Self-Modifying Constraints | AI edits its own rules | `XiaotianQuan` out-of-process |
| 6 | Audit Tampering | Mutable log entries | `AuditChain` hash-chained records |
| 7 | Cost Explosion | No spend monitoring | `CostMonitor` + subscription-first |

Each of these anti-patterns was discovered in production. The guards exist because the failures happened first.
