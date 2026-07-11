# Connect

**The Connect ecosystem is a self-hosted, privacy-first stack for running coding agents you can audit.**

This repository is documentation only. It contains no libraries, packages, services, or
APIs. It exists to explain how the products fit together, and to be the single place a new
user starts. Each product repository remains the authority on installing, configuring, and
using that specific product.

Every product works independently. None requires another to be useful.

## Status at a glance

All four products now have a runtime and a `0.1.0` release. Two are release candidates; two
are minimum-viable but real, with limitations named below rather than smoothed over.

| Product | Version | Maturity | What it is | Repository |
|---|---|---|---|---|
| **AgentConnect** | 0.1.0 | Release candidate | Task, artifact, decision, review, routing, and handoff backplane for coding agents | [AgentConnect](https://github.com/Judgernaut777/AgentConnect) |
| **BrainConnect** | 0.1.0 | Release candidate | Human-gated trusted memory ledger | [BrainConnect](https://github.com/Judgernaut777/BrainConnect) |
| **ComputeConnect** | 0.1.0 | MVP (heterogeneity unproven) | Local-compute provider / control plane | [ComputeConnect](https://github.com/Judgernaut777/ComputeConnect) |
| **ToolConnect** | 0.1.0 | MVP service | Tool-governance decision point | [ToolConnect](https://github.com/Judgernaut777/ToolConnect) |

Every product is installable, runs standalone, and ships an Apache-2.0 `LICENSE` and `NOTICE`
at its repository root and inside every wheel. Test gates as verified on 2026-07-12:
AgentConnect **945 passed / 3 skipped**, BrainConnect **589 passed / 0 skipped**,
ComputeConnect **66 passed**, ToolConnect **239 passed / 2 skipped**.

"Runtime exists" does not mean "production-ready." Read
[the maturity and known-limitations section](#maturity-and-known-limitations) before you
depend on any of them, and [COMPATIBILITY.md](COMPATIBILITY.md) before you pair two.

> **Naming: the BrainConnect rename is now done in code, with one shim.** As of 2026-07-12
> the Python package is `brainconnect`, the console scripts are `brainconnect` and
> `brainconnect-librarian`, and the isolation variable is `BRAINCONNECT_DB`. **The MCP tools
> are still `brain_*`** — that is the agent-facing wire contract and was deliberately left
> stable. `WIKIBRAIN_DB` is still honored as a deprecated fallback (with a warning) only
> while `BRAINCONNECT_DB` is unset. The on-disk data directory remains `~/.wiki-brain/`, a
> documented limitation: moving a user's live data was out of scope for the rename.

---

## The products

### AgentConnect

A control plane for managed coding-agent work. It provides a managed launch and shell
workflow for agents like Codex or Claude Code, records their work in an operator ledger,
injects bounded context into workers, supports review and audit, and prevents a normal
managed-agent session from marking its own task complete.

> If it is not recorded in AgentConnect, it did not happen.

**Works independently.** Nothing else in this list is required.

**Maturity: release candidate.** Nine installable packages, all at a unified `0.1.0`.
Verified end-to-end this cycle driving a real `claude -p` agent through the full loop —
task, launch, managed shell, artifact, review, audit, complete — including the property that
a managed session's attempt to complete its own task is refused.

**What it owns.** The task, artifact, decision, review, and handoff ledger; routing and
model tiering; the worker runtime; workspaces and scoped session tokens; the completion and
audit gates. It also owns the two cross-product contracts, `MemoryAdapter` and
`LocalComputeProvider`.

**What it delegates.** Durable workflow execution to Temporal, issue tracking to Linear, and
the tool protocol to `FastMCP` from the official Model Context Protocol SDK. Each is a
separate, optional package. It declares the local-inference contract and deliberately does
not own the engine behind it.

**Boundary.** AgentConnect is a compliance and control layer, **not a security sandbox.** It
records what a cooperative agent did. It does not contain a hostile one.

An authorization and completion bypass in the HTTP API — a managed agent could mark its own
task complete without the audit running — was **fixed** at commit `a07df7f`, and an
independent security retest this cycle confirmed it **stays fixed**. Every transport now
routes through one authorization gate. See [COMPATIBILITY.md](COMPATIBILITY.md#known-gaps).

### BrainConnect

A trusted memory ledger. Agents *propose* memory candidates; they never decide. Every
capture lands `pending` and becomes trusted memory only when a human promotes it. Claims are
scoped, provenance-backed, and governed by promotion, rejection, contradiction, and
supersession rules.

Two properties make it worth trusting. **The `brainconnect` command never calls a model** —
storage, search, and wiki generation are deterministic code with zero API calls. And
**retrieval can never widen trust**: the search backend nominates rows by id, while the
ledger alone answers for status, scope, and confidence.

**Works independently.** AgentConnect is an optional integration, not a dependency.

**Maturity: release candidate.** Reachable three ways — in-process Python API, MCP stdio, and
now an HTTP service (`brainconnect serve`, default `127.0.0.1:8787`, optional bearer token).
Verified this cycle serving a real AgentConnect control plane over HTTP: capture,
quarantine-on-injection, human-only promotion, and a nested safety-refusal envelope.

**What it owns.** Trust, provenance, scope, and the promotion, rejection, contradiction, and
supersession rules. The human gate.

**What it delegates.** Search sophistication to a pluggable retrieval backend, so a vector
store or graph index can be swapped in underneath without moving the trust boundary. Secret
and injection detection to third-party engines behind a policy seam it controls. Drafting to
a separate `brainconnect-librarian` process that speaks the OpenAI-compatible chat API to a
local endpoint such as Ollama or LM Studio.

### ComputeConnect

A local-compute provider and control plane: the authority on what compute exists, what it is
capable of, whether it is healthy, whether a given model will fit on it, and where a workload
should run.

**Maturity: MVP.** A real runtime — `computeconnect serve` (default port `8090`) implements
all six `LocalComputeProvider` routes plus an OpenAI-compatible layer, with structural
default-deny privacy filtering. Verified this cycle streaming real generation from the local
llama.cpp engine and cancelling it mid-stream, driven by AgentConnect's shipped
`HttpLocalComputeProvider` client.

**Honest limitation — heterogeneity is unproven.** ComputeConnect's premise is routing across
*heterogeneous* compute. On this single accelerator-less ARM host there is exactly one real
provider (the local llama.cpp engine); the second provider is **simulated**. The routing and
privacy machinery is real and tested, but the value proposition — placing work across genuinely
different hardware — has not been demonstrated on real second hardware. Its own `docs/STATUS.md`
records this and treats "should this exist as a separate product" as an open question.

**Works independently.** It conforms to AgentConnect's `LocalComputeProvider` contract, defined
in `agentconnect.core.local_compute`, and needs nothing else installed to run.

**What it delegates.** Inference itself. ComputeConnect never loads a tensor. It decides *where*
work runs, not *how* it is computed, and it does not manage the lifecycle of the engines it
routes to.

### ToolConnect

A tool-governance decision point. It is the authority on which tools exist, what they do, who
may call them, whether they are healthy, and what happened when they were called.

**Maturity: MVP service.** The Phase-1 in-memory decision core is now wrapped in a runtime:
SQLite persistence, a loopback HTTP service (`toolconnect serve`, default `127.0.0.1:8095`),
a real MCP-stdio discovery adapter, and an installable wheel with a CLI. Verified this cycle
ingesting a real MCP server over stdio and answering authorization decisions — deny before an
operator assertion, permit/forbid after, fail-closed on ambiguity and on post-assertion drift,
with a verifiable audit chain.

**ToolConnect is a policy and decision point, not a tool-execution proxy.** It does not sit in
the data path. Calls do not flow through it. There is deliberately **no `invoke()`** anywhere —
a test asserts its absence. In XACML terms it is the policy decision point; the caller remains
the thing that actually invokes the tool. `/authorize` answers "may this principal call this
tool"; the caller performs the call and closes the loop via `/decisions/{id}/outcome`.

**Fails closed.** Tool authorization may not degrade to permissive when unavailable. `serve`
refuses to start without a parseable policy file; an empty policy set denies everything.

**Honest caveat.** The "protocol-neutral" claim remains **partially unproven** — the tools
ingested so far were MCP-shaped. The registry treats capability metadata as an untrusted
assertion, never a server's self-claim, which is the property that lets a non-MCP source plug
in later.

---

## Which product do I need?

Each product is standalone-first: reach for one, add others only when you want what the seam
between them buys you.

| If you want to… | Use |
|---|---|
| Run a coding agent and keep an auditable record of the work | **AgentConnect** |
| Give agents durable memory without letting them decide what is true | **BrainConnect** |
| Browse and audit what your agents have learned, as a wiki you own | **BrainConnect** |
| Route work across model tiers, keeping sensitive context out of the wrong models | **AgentConnect** |
| Serve a local model to a control plane with structural privacy default-deny | **ComputeConnect** |
| Decide which agent may call which tool, with a fail-closed audited record | **ToolConnect** |
| Have agents contribute findings that a human promotes before anything trusts them | **AgentConnect + BrainConnect** |
| Run generation on your own hardware behind a placement/privacy policy | **AgentConnect + ComputeConnect** |
| Govern tool access for agent work you are already recording | **AgentConnect + ToolConnect** |

**Start with one.** Every product is useful alone. Reach for a combined install only when you
specifically want the seam between two of them — and read [COMPATIBILITY.md](COMPATIBILITY.md)
and [COMBINED_INSTALL.md](COMBINED_INSTALL.md) first, because the combined install has one real
caveat (the PyPI name `brainconnect` is taken, so BrainConnect must be installed by path).

---

## Documentation

| Document | Read it for |
|---|---|
| **[MANIFESTO.md](MANIFESTO.md)** | The engineering philosophy — what we refuse to build, and why |
| **[GETTING_STARTED.md](GETTING_STARTED.md)** | Per-product quickstarts, standalone |
| **[COMBINED_INSTALL.md](COMBINED_INSTALL.md)** | Two-product recipes and the full four-product install |
| **[ARCHITECTURE.md](ARCHITECTURE.md)** | How the products interact, with deployment diagrams |
| **[COMPATIBILITY.md](COMPATIBILITY.md)** | 0.1.0 version matrix, Python floors, port registry, contracts, known gaps |
| **[CONTRIBUTING.md](CONTRIBUTING.md)** | What belongs in this repository and what does not |
| **[docs/](docs/)** | Longer-form documents |

## Licensing

**The entire ecosystem is Apache-2.0.** Every product repository ships a `LICENSE` and a
`NOTICE` at its root, declares `Apache-2.0` as a PEP 639 SPDX `License-Expression` in package
metadata, and carries the license text inside every built wheel (under `*.dist-info/licenses/`).
There is no license divergence to reconcile. See [COMPATIBILITY.md](COMPATIBILITY.md#licensing).

## Maturity and known limitations

Read this before depending on anything here. The honest, per-product state:

- **AgentConnect — release candidate.** The most exercised product; the historical HTTP auth
  bypass stays fixed under independent retest.
- **BrainConnect — release candidate.** HTTP serve is new this cycle; the rename is done in
  code except for the `brain_*` MCP tool names and the `~/.wiki-brain/` data directory.
- **ComputeConnect — MVP.** Runtime is real; **heterogeneous compute is unproven** because
  the only second provider on this host is simulated.
- **ToolConnect — MVP service.** Runtime is real; still no tool execution by design, and the
  protocol-neutral claim is only partially proven.

Ecosystem-level gaps, stated plainly:

- **PyPI name collision (release blocker for publication).** `brainconnect` is already taken
  on PyPI by an unrelated package. BrainConnect **cannot** be `pip install`-ed by that name
  from PyPI; a combined install must use the wheel path or `--no-index`. Publishing under this
  name is impossible without a rename or a namespace/scope.
- **AgentConnect ↔ ToolConnect is API-level only.** The decision API is proven, but there is
  no shipped AgentConnect-side ToolConnect client. The binding was exercised at the API, not
  through a first-class AgentConnect integration.
- **Registering ComputeConnect as an AgentConnect routing worker is programmatic.** It works in
  code; there is no environment-variable or YAML declaration surface for it yet.

Three low-severity security hardening notes are recorded in
[COMPATIBILITY.md](COMPATIBILITY.md#known-gaps). The independent security review found **no
critical or high** issues.

## History

Fascia-AI-OS is retired. It has been replaced by this documentation repository and by four
independently installable, Apache-2.0, `0.1.0` products.
