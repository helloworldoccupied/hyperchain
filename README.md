# HyperChain

**Enterprise Multi-AI Governance Framework**

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-green.svg)](https://opensource.org/licenses/Apache-2.0)
[![PyPI version](https://img.shields.io/pypi/v/hyperchain.svg)](https://pypi.org/project/hyperchain/)

> Battle-tested multi-AI collaboration framework with built-in audit chains and tamper-proof enforcement.

## Why HyperChain?

When you orchestrate multiple AI models (Claude, GPT, Gemini) in production pipelines, governance breaks down fast. HyperChain is the framework that keeps them honest.

- **Anti-Pattern Guards** -- Encodes 7 hard-won lessons from production into enforceable rules. Weak reviewers can't rubber-stamp strong models. Infinite negotiation loops get hard-capped. Self-modifying constraints are blocked at the process level.
- **ECC Audit Chain** -- Every state transition, every AI decision, every review verdict is hash-chained into a tamper-proof log. If an AI deletes an inconvenient entry, the chain breaks and you know immediately.
- **XiaotianQuan Enforcement** -- An out-of-process watchdog that AIs cannot disable, modify, or negotiate with. It enforces governance rules from outside the AI's execution context, eliminating the fox-guarding-henhouse problem.

## Architecture

```
+------------------------------------------------------------------+
|                        HyperChain Stack                          |
+------------------------------------------------------------------+
|                                                                  |
|  Layer 5: CLI & SDK                                              |
|  +-----------+  +-----------+  +-------------+                   |
|  | hyperchain|  | Python    |  | Config      |                   |
|  | CLI       |  | SDK       |  | Templates   |                   |
|  +-----------+  +-----------+  +-------------+                   |
|                                                                  |
|  Layer 4: Governance Engine                                      |
|  +-----------+  +-----------+  +-------------+                   |
|  | Guard     |  | Tier      |  | Cost        |                   |
|  | Registry  |  | Validator |  | Monitor     |                   |
|  +-----------+  +-----------+  +-------------+                   |
|                                                                  |
|  Layer 3: State Machine                                          |
|  +-----------+  +-----------+  +-------------+                   |
|  | Pipeline  |  | Transition|  | Negotiation |                   |
|  | Templates |  | Engine    |  | Protocol    |                   |
|  +-----------+  +-----------+  +-------------+                   |
|                                                                  |
|  Layer 2: Audit Chain (ECC)                                      |
|  +-----------+  +-----------+  +-------------+                   |
|  | Hash-     |  | Integrity |  | Evidence    |                   |
|  | Chained   |  | Verifier  |  | Attachments |                   |
|  | Records   |  |           |  |             |                   |
|  +-----------+  +-----------+  +-------------+                   |
|                                                                  |
|  Layer 1: XiaotianQuan (Out-of-Process Enforcement)              |
|  +-----------+  +-----------+  +-------------+                   |
|  | Watchdog  |  | Rule      |  | Violation   |                   |
|  | Process   |  | Engine    |  | Reporter    |                   |
|  +-----------+  +-----------+  +-------------+                   |
|                                                                  |
+------------------------------------------------------------------+
```

## Quick Start

```python
from hyperchain import StateMachine, AuditChain, GuardRegistry, Verdict

# Create pipeline
sm = StateMachine.from_template("code-review")
chain = AuditChain(storage="./audit")
guards = GuardRegistry()

# Wire audit to state machine
sm.on_transition(lambda frm, to, meta: chain.record(
    task_id="task-001", actor=meta.get("actor", "system"),
    action=f"{frm}->{to}",
))

# Run pipeline
sm.transition("negotiating", metadata={"actor": "claude"})
sm.transition("assigned", metadata={"actor": "human"})

# Verify integrity
assert chain.verify_integrity()
chain.save()
```

## Installation

```bash
pip install hyperchain
```

## CLI

Initialize a new project with governance defaults:

```bash
hyperchain init
```

Verify the audit chain has not been tampered with:

```bash
hyperchain audit verify
```

## Anti-Patterns Guide

HyperChain encodes 7 battle-tested anti-patterns discovered during 3 months of multi-AI production use. Each one broke something real before it became a guard rail.

See the full guide: [docs/anti-patterns.md](docs/anti-patterns.md)

## Contributing

Contributions are welcome. Please open an issue first to discuss what you would like to change.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Write tests for your changes
4. Ensure all tests pass (`pytest`)
5. Submit a pull request

## License

Apache 2.0. See [LICENSE](LICENSE) for details.

## Born from Production

HyperChain was extracted from a real multi-AI enterprise system that ran for 3 months in production, orchestrating Claude, GPT, and Gemini across software development, market intelligence, and quantitative trading pipelines. Every guard, every audit rule, and every enforcement mechanism exists because something went wrong without it. The anti-patterns guide documents the actual failures that shaped this framework. This is not a theoretical governance library -- it is scar tissue turned into code.
