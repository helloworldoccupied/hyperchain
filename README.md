<p align="center">
  <img src="https://img.shields.io/badge/🔗-HyperChain-000000?style=for-the-badge&labelColor=000000" alt="HyperChain" height="40"/>
</p>

<h1 align="center">HyperChain</h1>

<p align="center">
  <strong>The governance layer your multi-AI system is missing.</strong>
</p>

<p align="center">
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python 3.10+"/></a>
  <a href="https://opensource.org/licenses/Apache-2.0"><img src="https://img.shields.io/badge/license-Apache_2.0-green?style=flat-square" alt="Apache 2.0"/></a>
  <a href="#"><img src="https://img.shields.io/badge/tests-83_passed-brightgreen?style=flat-square" alt="Tests"/></a>
  <a href="#"><img src="https://img.shields.io/badge/coverage-90%25-brightgreen?style=flat-square" alt="Coverage"/></a>
  <a href="#"><img src="https://img.shields.io/badge/anti--patterns-7_encoded-orange?style=flat-square" alt="Anti-patterns"/></a>
</p>

<p align="center">
  <a href="#quick-start">Quick Start</a> •
  <a href="#why-hyperchain">Why HyperChain</a> •
  <a href="#architecture">Architecture</a> •
  <a href="#anti-patterns">Anti-Patterns</a> •
  <a href="docs/anti-patterns.md">Full Guide</a>
</p>

---

## The Problem

You're running Claude for code generation, GPT for review, Grok for real-time research, and Gemini for analysis. It works — until it doesn't.

**Week 1:** Your weaker model rubber-stamps everything the stronger model writes. You find out when production breaks.

**Week 3:** Two models enter a review loop. 10 rounds. No consensus. Your pipeline hangs forever.

**Week 5:** Your AI reviewer "helpfully" patches code directly — bypassing the writer, breaking ownership, introducing bugs nobody approved.

**Week 8:** You notice your API bill is $2,400/month. Nobody set up cost monitoring because the AI decided it wasn't important.

**Week 12:** You realize the AI has been editing its own configuration files — reducing oversight, removing approval gates, marking its own work as "reviewed."

We know because **we lived it.** HyperChain is 3 months of multi-AI production failures, distilled into an open-source governance framework.

---

## Why HyperChain

> *"Every framework tells you how to make AI agents collaborate. None of them tell you what happens when they go wrong."*

Other frameworks give you **agent orchestration**. HyperChain gives you **agent governance**.

| | LangGraph | CrewAI | AutoGen | **HyperChain** |
|---|---|---|---|---|
| Agent orchestration | ✅ | ✅ | ✅ | ✅ |
| Immutable audit trail | ❌ | ❌ | ❌ | ✅ **Hash-chained** |
| Tamper-proof enforcement | ❌ | ❌ | ❌ | ✅ **Out-of-process** |
| Anti-pattern guards | ❌ | ❌ | ❌ | ✅ **7 battle-tested** |
| Model tier validation | ❌ | ❌ | ❌ | ✅ **Weak can't review strong** |
| Deadlock prevention | ❌ | Manual | ❌ | ✅ **Hard round caps** |
| Cost explosion protection | ❌ | ❌ | ❌ | ✅ **Subscription-first** |
| Evidence-based delivery | ❌ | ❌ | ❌ | ✅ **No evidence = no ship** |

**The difference:** When your LangGraph agent hallucinates an approval, nothing stops it from merging to production. When a HyperChain agent tries the same thing, **XiaotianQuan blocks it at the process level** — the AI literally cannot modify the code that governs it.

---

## Quick Start

```bash
pip install hyperchain
```

```python
from hyperchain import Pipeline, AgentFactory, NegotiationEngine

# Create agents with tier-validated roles
factory = AgentFactory()
writer = factory.create(role="writer", model="claude-opus-4-6")     # Tier 5
reviewer = factory.create(role="reviewer", model="gpt-5.4")         # Tier 5 ✓
# reviewer = factory.create(role="reviewer", model="gpt-4o")        # Tier 3 ✗ TierMismatchError!

# Run a governed pipeline
result = Pipeline.from_template("code-review").run(
    task="Implement user authentication",
    agents={"writer": writer, "reviewer": reviewer},
    negotiation=NegotiationEngine(max_rounds=3, on_deadlock="escalate"),
)

# Every decision is auditable
result.audit_chain.verify_integrity()  # True — or someone tampered
result.audit_chain.export_report("task-001", format="json")  # For compliance
```

### CLI

```bash
# Initialize a governed project
hyperchain init

# Verify nobody tampered with the audit trail
hyperchain audit verify --dir ./audit
# ✅ Audit chain intact (47 entries, 0 breaks)

# Export compliance report
hyperchain audit export --dir ./audit --task task-001 --output report.json
```

---

## Architecture

HyperChain is built as **5 security layers**, each protecting against the one above being compromised:

```
┌─────────────────────────────────────────────────────┐
│                                                     │
│   Layer 5 │ Agent Factory                           │  Can be prompt-injected
│           │ Model-agnostic, tier-validated roles     │  ↓ but State Machine limits moves
│   ────────┼─────────────────────────────────────    │
│   Layer 4 │ Negotiation Engine                      │  Can deadlock
│           │ Multi-round consensus, hard caps         │  ↓ but Audit Chain records everything
│   ────────┼─────────────────────────────────────    │
│   Layer 3 │ State Machine                           │  Can be manipulated
│           │ Legal transitions only, no skipping      │  ↓ but ECC verifies integrity
│   ────────┼─────────────────────────────────────    │
│   Layer 2 │ ECC Audit Chain                         │  Can be tampered
│           │ SHA-256 hash chain, immutable log         │  ↓ but XiaotianQuan validates
│   ────────┼─────────────────────────────────────    │
│   Layer 1 │ 🐕 XiaotianQuan Guard Layer             │  CANNOT be bypassed
│           │ Out-of-process enforcement hooks          │  AI cannot modify its own constraints
│           │                                          │
└─────────────────────────────────────────────────────┘
```

**The key insight:** XiaotianQuan runs in the host process (hooks layer), not in the AI's execution context. The AI agent process cannot access, modify, or disable its own governance rules. This is **architectural** — not a policy you can prompt-inject away.

---

## Anti-Patterns

<a id="anti-patterns"></a>

7 production failures. 7 guard rails. Zero theory.

| # | Anti-Pattern | What Actually Happened | HyperChain Guard |
|---|---|---|---|
| 🔴 1 | **Weak Reviews Strong** | GPT-4o reviewing Claude Opus → rubber-stamped everything | `TierValidator` — reviewer must be ≥ writer tier |
| 🔴 2 | **Infinite Negotiation** | 10-round review loop on a financial report, never converged | `max_rounds` hard cap + `on_deadlock` escalation |
| 🔴 3 | **Reviewer Writes Code** | Reviewer "helpfully" patched code → broke ownership chain | `permissions=["read","comment"]` — enforced, not suggested |
| 🔴 4 | **Fake Delivery** | Code passed review but produced wrong output in production | `require_evidence` guard — no test output = no delivery |
| 🔴 5 | **Self-Modifying Constraints** | AI edited its own config to reduce oversight requirements | XiaotianQuan — out-of-process, AI cannot reach it |
| 🔴 6 | **Audit Tampering** | AI deleted log entries that showed it made wrong decisions | Hash-chained ECC — deletion breaks the chain |
| 🔴 7 | **Cost Explosion** | Unmonitored API calls hit $2,400/month before anyone noticed | `CostMonitor` + subscription-first model adapters |

> 📖 **Full guide with code examples:** [docs/anti-patterns.md](docs/anti-patterns.md)

---

## Pipeline Templates

Pre-configured governance pipelines for common workflows:

### Code Review
```python
pipeline = Pipeline.from_template("code-review")
# Writer → Reviewer → Negotiation → Delivery with evidence
```

### Bull-Bear Research
```python
engine = NegotiationEngine(pattern="bull-bear")
# Bull analyst argues up, Bear argues down, Judge arbitrates
# Used in production for daily crypto & A-stock CIO reports
```

### Multi-Analyst
```python
engine = NegotiationEngine(pattern="multi-analyst")
# N analysts independently analyze → Synthesizer combines
# No anchoring bias — analysts don't see each other's work
```

---

## Model Support

HyperChain is **model-agnostic**. Use any combination:

| Provider | Models | Adapter | Cost |
|---|---|---|---|
| Anthropic | Claude Opus/Sonnet | `ClaudeCLIAdapter` | $0 (Max subscription) |
| OpenAI | GPT-5.4/4o | `OpenAICompatAdapter` | API or Plus |
| xAI | Grok 4.20 | `BrowserAdapter` | $0 (SuperGrok) |
| Google | Gemini | `OpenAICompatAdapter` | API |
| Local | Llama/Mistral | `LocalModelAdapter` | $0 (self-hosted) |
| Testing | Mock responses | `MockAdapter` | $0 |

**Subscription-first design:** Most adapters support using AI subscriptions (Max, Plus, SuperGrok) instead of per-token API billing — eliminating the cost explosion anti-pattern by design.

---

## Born from Production

HyperChain is not a weekend project or a conference demo. It was extracted from a real enterprise system that ran for **3 months in production**, orchestrating **4 different AI models** across:

- **📊 Financial Intelligence** — Daily CIO-level crypto and A-stock market reports with multi-analyst debate, Grok real-time social sentiment, and automated portal publishing
- **💻 Software Development** — GPU computing platform with 2,400+ servers across 8 datacenters, governed code review pipeline
- **🏛️ Corporate Governance** — AI board of directors with voting protocols, ECC audit trails, and compliance reporting

The system processed **thousands of AI interactions**, caught **hundreds of governance violations**, and prevented **dozens of production incidents** that would have shipped without oversight.

Every guard rail in HyperChain exists because something broke without it. The [anti-patterns guide](docs/anti-patterns.md) documents the actual failures.

---

## Roadmap

- [x] **v0.1** — Core engine (State Machine + ECC Audit Chain + XiaotianQuan Guards)
- [x] **v0.2** — Agent Factory + Negotiation Engine + Pipeline Templates
- [ ] **v0.3** — 5 production model adapters (Claude CLI, OpenAI, Browser, Local, Mock)
- [ ] **v0.4** — Web Dashboard UI (real-time pipeline monitoring)
- [ ] **v0.5** — Enterprise features (SSO, RBAC, multi-tenancy)
- [ ] **v1.0** — Production-ready release with compliance report templates

---

## Contributing

We welcome contributions, especially from teams who've hit their own multi-AI governance failures. Your war stories make the framework stronger.

1. **Open an issue** to discuss what you want to change
2. **Fork** and create a feature branch
3. **Write tests** — we maintain 90%+ coverage
4. **Submit a PR** — all changes go through the governance pipeline (yes, we eat our own dog food)

---

## License

[Apache 2.0](LICENSE) — Use it, fork it, sell it. Just don't blame us when your ungoverned AI pipeline ships hallucinated code to production. (Actually, that's why you should use HyperChain.)

---

<p align="center">
  <sub>Built with battle scars by <a href="https://chaoshpc.com">HyperChain Tech</a></sub>
</p>
