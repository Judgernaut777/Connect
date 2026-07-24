# Connect

**The Connect ecosystem is a self-hosted, privacy-first stack for running coding agents you can audit.**

This repository ships no application or library code — no importable package, no service, no
API. What it does ship: the [ecosystem manifest](manifest/ecosystem.yaml) (the pinned-commit
lockfile and source of truth for every version and test-count number in this document), a
Docker Compose deployment bundle under [deploy/](deploy/), and a handful of operational
scripts ([scripts/](scripts/), `deploy/connect-health`, `deploy/connect-smoke`). It exists to
explain how the products fit together, to keep that explanation honest and un-driftable, and
to be the single place a new user starts. Each product repository remains the authority on
installing, configuring, and using that specific product.

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
at its repository root and inside every wheel.

<!-- BEGIN generated:tests (source: manifest/ecosystem.yaml — do not hand-edit) -->
Test gates, from the ecosystem manifest:
AgentConnect **1060 passed / 3 skipped**, BrainConnect **949 passed / 0 failed**,
ComputeConnect **129 passed** (140 collected, offline gate), ToolConnect **339 passed / 3
skipped** (342 collected).

ComputeConnect's 11 real-engine tests are excluded from that offline count — they need a live
llama.cpp on `:8080`, and 9 of them currently fail only because the host model was renamed
`qwen3-30b-a3b` → `qwen3.6-35b-a3b`, not because of a product bug. BrainConnect's
`package_version` (`0.1.0`) has not yet been bumped to match its `v0.1.2-rc1` tag — recorded
here truthfully, not smoothed over.
<!-- END generated:tests -->

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
and [COMBINED_INSTALL.md](COMBINED_INSTALL.md) first. All four install into one virtualenv with
zero dependency conflicts (verified: 86 packages, `pip check` clean), and the four-service stack
also ships as a Docker Compose deployment under [deploy/](deploy/) that builds, comes up healthy,
and passes a real cross-product smoke test.

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
| **[manifest/ecosystem.yaml](manifest/ecosystem.yaml)** | The ecosystem source of truth / lockfile: pinned commits, tags, package and contract versions, test gate counts |
| **[docs/RELEASE.md](docs/RELEASE.md)** | The manifest-driven release model: how the manifest, generated doc tables, drift check, and image publishing fit together |
| **[deploy/](deploy/)** | Docker Compose full-stack deployment, `connect-health`, `connect-smoke` |
| **[docs/](docs/)** | Longer-form guides: observability, upgrade/rollback, backup/restore, security, production checklist, troubleshooting |

## Release model

This repository's product claims are generated, not hand-maintained. **[manifest/ecosystem.yaml](manifest/ecosystem.yaml)**
is the single source of truth — pinned commit SHAs (it doubles as the ecosystem lockfile), tags,
package versions, contract versions, and last-verified test gate counts for every product,
including this one. The tables above are derived from it and wrapped in
`<!-- BEGIN generated:tests --> … <!-- END generated:tests -->` markers.
**[scripts/check_manifest.py](scripts/check_manifest.py)** parses those markers and fails
non-zero the moment a doc number drifts from the manifest — that is what makes this document
un-driftable rather than merely aspirational. **[scripts/gen_manifest.py](scripts/gen_manifest.py)**
regenerates the manifest itself from each sibling checkout's live git state, optionally
(`--run-gates`) re-running each sibling's gate to refresh test counts. Release images are built
only from the commits the manifest pins — see **[docs/RELEASE.md](docs/RELEASE.md)** for the
full model and **[.github/workflows/](.github/workflows/)** for the CI that enforces it.

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

Ecosystem-level status, stated plainly:

- **PyPI name — RESOLVED.** BrainConnect publishes as the distribution **`brainconnect-ai`**
  (`pip install brainconnect-ai`); the import package and console command stay `brainconnect`.
  The old `brainconnect` collision is no longer a publication blocker. Do **not** `pip install
  brainconnect` bare — that is an unrelated third-party package.
- **AgentConnect ↔ ToolConnect — first-class client shipped.** `agentconnect-core` now carries a
  fail-closed `ToolConnectGovernor` that AgentConnect consults as a real chokepoint (a denied tool
  blocks a subtask before its worker spawns). Verified end-to-end against a live `toolconnect serve`
  (allow a read tool, deny a write tool, contract `1.0`).
- **ComputeConnect wiring — declarative.** Registering ComputeConnect as an AgentConnect worker is
  now driven by `AGENTCONNECT_COMPUTE_URL` (or `config/compute.yaml`); the `local-manager` worker
  appears in `GET /health` when configured. Verified in the Compose stack.

The one honest deploy-layer caveat found while building [deploy/](deploy/) — `agentconnect-core`
lazily imported **httpx** for all three of its HTTP clients without declaring it as a
dependency — was reported upstream and is fixed: `agentconnect-core` now declares
`httpx>=0.27`, so a base install reaches the sibling services with no extra pin.

Three low-severity security hardening notes are recorded in
[COMPATIBILITY.md](COMPATIBILITY.md#known-gaps). The independent security review found **no
critical or high** issues.

## History

Fascia-AI-OS is retired. It has been replaced by this documentation repository and by four
independently installable, Apache-2.0, `0.1.0` products.
