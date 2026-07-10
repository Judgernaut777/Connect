# Connect

**The Connect ecosystem is a self-hosted, privacy-first stack for running coding agents you can audit.**

This repository is documentation only. It contains no libraries, packages, services, or
APIs. It exists to explain how the products fit together, and to be the single place a new
user starts. Each product repository remains the authority on installing, configuring, and
using that specific product.

Every product works independently. None requires another to be useful.

## Status at a glance

Two products are implemented and runnable. The other two are pre-runtime: their charters are
defined and written down, but **neither has a runtime implementation.** ComputeConnect is at
the architecture stage with no code; ToolConnect has an in-memory validation prototype that is
deliberately not the product.

| Product | Status | What it is | Repository |
|---|---|---|---|
| **AgentConnect** | Implemented | Task, artifact, decision, review, routing, and handoff backplane for coding agents | [AgentConnect](https://github.com/Judgernaut777/AgentConnect) |
| **BrainConnect** | Implemented | Human-gated trusted memory ledger | [BrainConnect](https://github.com/Judgernaut777/BrainConnect) |
| **ComputeConnect** | Design phase | Compute-resource control plane. No code. | [ComputeConnect](https://github.com/Judgernaut777/ComputeConnect) |
| **ToolConnect** | Validation phase | Tool-governance platform. Validation prototype, no runtime. | [ToolConnect](https://github.com/Judgernaut777/ToolConnect) |

Neither pre-runtime product is installable, and nothing in this repository should be read
as implying otherwise. Neither is production-ready. ToolConnect has an in-memory validation
prototype that is deliberately *not* the product — it has no server, no daemon, and no tool
execution.

> **Naming in transition.** BrainConnect's repository has been renamed, but its identifiers
> have not. The console scripts are still `wiki` and `wiki-librarian`, the MCP server is
> still `wiki-brain`, the tools are still `brain_*`, and the environment variables are still
> `WIKIBRAIN_URL` and `WIKIBRAIN_DB`. AgentConnect's adapter class is still
> `WikiBrainMemoryAdapter`. Read "BrainConnect" and "WikiBrain" as the same product.

---

## The products

### AgentConnect

A control plane for managed coding-agent work. It provides a managed launch and shell
workflow for agents like Codex or Claude Code, records their work in an operator ledger,
injects bounded context into workers, supports review and audit, and prevents a normal
managed-agent session from marking its own task complete.

> If it is not recorded in AgentConnect, it did not happen.

**Works independently.** Nothing else in this list is required.

**Implementation status.** Implemented and runnable. Nine installable packages. Package
versions are not unified across them, so there is no single "AgentConnect version" yet.

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
task complete without the audit running — was **fixed** at commit `a07df7f`; every transport
now routes through one authorization gate. See [COMPATIBILITY.md](COMPATIBILITY.md#known-gaps).

### BrainConnect

A trusted memory ledger. Agents *propose* memory candidates; they never decide. Every
capture lands `pending` and becomes trusted memory only when a human promotes it. Claims are
scoped, provenance-backed, and governed by promotion, rejection, contradiction, and
supersession rules.

Two properties make it worth trusting. **The `wiki` command never calls a model** — storage,
search, and wiki generation are deterministic code with zero API calls. And **retrieval can
never widen trust**: the search backend nominates rows by id, while the ledger alone answers
for status, scope, and confidence.

**Works independently.** AgentConnect is an optional integration, not a dependency.

**Implementation status.** Implemented and runnable. No HTTP server — see the known gaps.

**What it owns.** Trust, provenance, scope, and the promotion, rejection, contradiction, and
supersession rules. The human gate.

**What it delegates.** Search sophistication to a pluggable retrieval backend, so a vector
store or graph index can be swapped in underneath without moving the trust boundary. Secret
and injection detection to third-party engines behind a policy seam it controls. Drafting to
a separate `wiki-librarian` process that speaks the OpenAI-compatible chat API to a local
endpoint such as Ollama or LM Studio.

### ComputeConnect

A compute-resource control plane: the authority on what compute exists, what it is capable
of, whether it is healthy, whether a given model will fit on it, and where a workload should
run.

**Architecture and design phase. There is no runtime implementation.**

**Works independently.** By design. Unproven, because nothing runs yet.

**Charter (provisional).** A heterogeneous compute-provider registry; delegation of runtime
and model lifecycle; placement policy; health; and execution metadata. It conforms to
AgentConnect's `LocalComputeProvider` contract, defined in
`agentconnect.core.local_compute`. That contract exists and ships today; the product that
implements it does not.

**What it delegates.** Inference itself. ComputeConnect never loads a tensor. Model
execution belongs to maintained engines and runtimes; ComputeConnect decides *where* work
runs, not *how* it is computed.

Its architecture proposal is published (commit `19e1406`); the repository is architecture and
interfaces only, with no code.

### ToolConnect

A tool-governance platform. It is the authority on which tools exist, what they do, who may
call them, whether they are healthy, and what happened when they were called.

**Validation phase. There is no runtime implementation.** There is an in-memory validation
prototype — roughly 600 lines under `src/toolconnect/`, with a 52-test suite that passes
offline — built to test assumptions, not to be the product. It has no server, no database,
no HTTP service, and no tool execution; a test asserts that no `invoke()` exists.

**Works independently.** By design. Unproven, because nothing runs yet.

**Charter.** A protocol-neutral tool registry; asserted governance metadata; policy
decisions; health; authorization records; and audit. Capability metadata is treated as an
untrusted registry assertion, never a server's self-claim. Tool authorization **fails
closed** — unlike a memory layer, it may not degrade to permissive when unavailable.

**ToolConnect is a policy and decision point, not a tool-execution proxy.** It does not sit
in the data path. Calls do not flow through it. In the vocabulary of XACML it is the policy
decision point, and the caller remains the thing that actually invokes the tool. This is the
distinction that keeps governance from collapsing into proxying.

**What it delegates.** Tool description and transport to the Model Context Protocol, and the
in-path proxy role to existing gateways that already do it well.

**Honest caveat.** ToolConnect's "protocol-neutral" claim is **unproven** — every tool the
prototype has ingested so far was MCP-shaped. Whether it should be built at all remains an
open go/no-go question its own roadmap will decide.

---

## Which product do I need?

| If you want to… | Use |
|---|---|
| Run a coding agent and keep an auditable record of the work | **AgentConnect** |
| Give agents durable memory without letting them decide what is true | **BrainConnect** |
| Route work across model tiers, keeping sensitive context out of the wrong models | **AgentConnect** |
| Browse and audit what your agents have learned, as a wiki you own | **BrainConnect** |
| Have agents contribute findings that a human promotes before anything trusts them | **AgentConnect + BrainConnect** |
| Manage local compute, or govern which agent may call which tool | Nothing runnable yet — ComputeConnect is design-phase, ToolConnect a validation prototype. |

**Start with one.** Both implemented products are standalone-first and useful alone. Reach
for the combined install only when you specifically want agent work recorded by AgentConnect
to feed a memory ledger you gate by hand — and read
[COMPATIBILITY.md](COMPATIBILITY.md) first, because that integration has a gap.

---

## Documentation

| Document | Read it for |
|---|---|
| **[MANIFESTO.md](MANIFESTO.md)** | The engineering philosophy — what we refuse to build, and why |
| **[GETTING_STARTED.md](GETTING_STARTED.md)** | Per-product quickstarts, standalone |
| **[COMBINED_INSTALL.md](COMBINED_INSTALL.md)** | Running AgentConnect and BrainConnect together |
| **[ARCHITECTURE.md](ARCHITECTURE.md)** | How the products interact, with deployment diagrams |
| **[COMPATIBILITY.md](COMPATIBILITY.md)** | Version matrix, Python floor, port registry, and known gaps |
| **[CONTRIBUTING.md](CONTRIBUTING.md)** | What belongs in this repository and what does not |
| **[docs/](docs/)** | Longer-form documents |

## Licensing

The products do not share a license. AgentConnect declares MIT; BrainConnect is Apache 2.0.
See [COMPATIBILITY.md](COMPATIBILITY.md#licensing) before you vendor either.

## History

Fascia-AI-OS is retired. It has been replaced by this documentation repository and by four
independently installable products.
