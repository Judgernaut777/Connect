# Connect

**Today, Connect is a self-hosted, privacy-first ecosystem of infrastructure planes for
running coding agents you can audit. It is evolving into a free, open-source, zero-trust AI
control plane for *making agents usable*.**

Both statements are true, and this repository keeps them apart on purpose:

- **Today (current implementation).** Four standalone, self-hosted `0.1.0` products — the
  Work, Knowledge, Capability, and Compute planes (below) — plus *this* repository, an
  integration-and-documentation umbrella. Every product runs independently and is auditable.
- **Target (where this is going).** One control plane that coordinates native harnesses, work,
  memory, capabilities, compute, secure workspaces, organizations, flexible budgets, and a
  neutral marketplace — **without** becoming the customer's host, data custodian, consultant,
  or subscription vendor. The full statement is [PRODUCT_THESIS.md](PRODUCT_THESIS.md).

> **The target is not built yet.** The user-facing control-plane application, the marketplace,
> the onboarding wizard, and the generalized budget engine **do not exist**. Where they are
> described in these docs they are marked *design direction* — do not read the target product
> as a claim about current runtime. The control-plane application may need its own repository;
> that is [ADR 0002](docs/adr/0002-control-plane-repository-boundary.md), which remains
> **Proposed**, and no substantial control-plane implementation begins until it is accepted.

New here? The [documentation index](docs/README.md) maps every current document by topic and
labels each *current* or *target*.

This repository ships no application or library code — no importable package, no service, no
API. What it does ship: the [ecosystem manifest](manifest/ecosystem.yaml) (the pinned-commit
lockfile and source of truth for every version and test-count number in this document), a
Docker Compose deployment bundle under [deploy/](deploy/), and a handful of operational
scripts ([scripts/](scripts/), `deploy/connect-health`, `deploy/connect-smoke`). It exists to
explain how the products fit together, to keep that explanation honest and un-driftable, and
to be the single place a new user starts. Each product repository remains the authority on
installing, configuring, and using that specific product.

Every product works independently. None requires another to be useful.

## Five planes, one platform

Connect is not five unrelated apps that happen to share a naming convention. It is the
**Control plane** — a deliberately thin management plane — sitting over four infrastructure
planes, each owned by exactly one product:

| Plane | Product | Answers |
|---|---|---|
| **Work** | AgentConnect | What is being done, by which agent, under whose review, and is it recorded? |
| **Knowledge** | BrainConnect | What is trusted, who promoted it, and under what scope? |
| **Capability** | ToolConnect | Which tool may this principal call, and did the call get authorized? |
| **Compute** | ComputeConnect | Where does this workload run, and does that placement respect privacy? |

Connect itself — this repository — is the fifth plane, the **Control plane**, and it is
deliberately the thinnest one. It runs no workloads, holds no trust, decides no authorization,
and places no compute. Today it is the manifest, the deploy bundle, and the docs that keep the
other four honest about what they claim; the target control-plane application
([PRODUCT_THESIS.md](PRODUCT_THESIS.md)) coordinates the four without becoming a fifth opinion
competing with them for control. Either way it stays a thin coordinator, never a fifth authority.

Read the table as infrastructure layers a coding-agent platform needs, not as an org chart. A
single unit of agent work in AgentConnect's Work plane can reach into BrainConnect's Knowledge
plane (capture/recall), ComputeConnect's Compute plane (placement), and ToolConnect's Capability
plane (authorization) — each through one explicit, versioned contract (see
[The contracts](COMPATIBILITY.md#the-contracts)), never through shared code or a shared database.
[ARCHITECTURE.md](ARCHITECTURE.md) has the wiring diagrams; [Which product do I need?](#which-product-do-i-need)
below has the plain-language version.

The planes communicate two ways: **synchronously** through the explicit versioned contracts
above (a unit of work calls memory, compute, and tool authorization directly), and
**asynchronously** through a shared, best-effort [event bus](EVENT_BUS.md) — one append-only
stream every plane can publish to and replay, for observability and debugging without adding
point-to-point coupling. The bus is a *projection, never a system of record*: a plane that
can't reach it keeps working unchanged, so it loosens coupling rather than creating a new
central dependency.

**This framing does not imply uniform readiness.** The Work and Knowledge planes
(AgentConnect, BrainConnect) are release candidates; the Capability and Compute planes
(ToolConnect, ComputeConnect) are MVPs with named, open gaps — see
[Maturity and known limitations](#maturity-and-known-limitations). A platform is only as strong
as its least-mature plane, and right now that is Capability and Compute, not Work or Knowledge.

## Status at a glance

All four products now have a runtime and a `0.1.0` release. Two are release candidates; two
are minimum-viable but real, with limitations named below rather than smoothed over.

<!-- BEGIN generated:tests (source: manifest/ecosystem.yaml — do not hand-edit) -->
| Product | Version | Maturity | What it is | Repository |
|---|---|---|---|---|
| **AgentConnect** | 0.1.0 | Release candidate | Task, artifact, decision, review, routing, and handoff backplane for coding agents | [AgentConnect](https://github.com/Judgernaut777/AgentConnect) |
| **BrainConnect** | 0.1.2rc1 (tag `v0.1.2-rc1`) | Release candidate | Human-gated trusted memory ledger | [BrainConnect](https://github.com/Judgernaut777/BrainConnect) |
| **ComputeConnect** | 0.1.0 | MVP (single-host heterogeneity proven 2026-07-27; cross-machine open) | Local-compute provider / control plane | [ComputeConnect](https://github.com/Judgernaut777/ComputeConnect) |
| **ToolConnect** | 0.1.0 | MVP service | Tool-governance decision point | [ToolConnect](https://github.com/Judgernaut777/ToolConnect) |
<!-- END generated:tests -->

Every product is installable, runs standalone, and ships an Apache-2.0 `LICENSE` and `NOTICE`
at its repository root and inside every wheel.

<!-- BEGIN generated:tests (source: manifest/ecosystem.yaml — do not hand-edit) -->
Test gates, from the ecosystem manifest:
AgentConnect **1288 passed / 3 skipped** (1291 collected), BrainConnect **956 passed / 0
failed**, ComputeConnect **155 passed** (offline gate), ToolConnect **485 passed / 3
skipped**.

ComputeConnect's 11 real-engine tests are excluded from that offline count — they need a live
llama.cpp on `:8080`. They now read their expected model ids from `CC_REAL_MODEL` /
`CC_REAL_MODEL_B` (the 2026-07-17 failures caused by the host model rename
`qwen3-30b-a3b` → `qwen3.6-35b-a3b` are fixed; last live run: 149 passed / 5 skipped).
BrainConnect's package version is `0.1.2rc1`, matching its `v0.1.2-rc1` tag — the
long-standing tag/package mismatch was closed on 2026-07-27.
<!-- END generated:tests -->

<!-- BEGIN generated:contracts (source: manifest/ecosystem.yaml — do not hand-edit) -->
Cross-product contract versions, from the ecosystem manifest: `memory_adapter` `1.0`,
`local_compute_provider` `1.0`, `toolconnect_governor` `1.1`.
<!-- END generated:contracts -->

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

**Honest status — single-host heterogeneity proven; cross-machine open.** ComputeConnect's
premise is routing across *heterogeneous* compute. As of 2026-07-27 that is proven for the
single-host case: two real, materially different engines (35B MoE / 16k ctx and 4B dense /
8k ctx) with preference-driven selection, capacity-forced placement, and real generation from
both — see ComputeConnect's `docs/validation/heterogeneity-2026-07-27.md`. What remains open is
placement across genuinely different *machines* (a GPU-class remote node); its `docs/STATUS.md`
tracks that as the next step.

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
| **[docs/README.md](docs/README.md)** | **The documentation index** — every current document by topic, each labeled *current* or *target*. Start here. |
| **[DOCUMENTATION_CORRECTION_REPORT.md](DOCUMENTATION_CORRECTION_REPORT.md)** | The audit trail: what the documentation-correction effort changed, and why |
| **[PRODUCT_THESIS.md](PRODUCT_THESIS.md)** | The canonical product — *making agents usable* — and current state vs target (design direction) |
| **[MARKETPLACE_ARCHITECTURE.md](MARKETPLACE_ARCHITECTURE.md)** | The marketplace and the entire business model: categories, metadata, neutral sorting, verification, fees (design direction) |
| **[DATA_AND_COMPLIANCE_BOUNDARIES.md](DATA_AND_COMPLIANCE_BOUNDARIES.md)** | The component-level data matrix and what compliance enablement is (and is not) |
| **[TRANSPARENCY.md](TRANSPARENCY.md)** | Plain commitments: what Connect stores, when it earns a fee, how ranking and telemetry work |
| **[MANIFESTO.md](MANIFESTO.md)** | The engineering philosophy — what we refuse to build, and why |
| **[GETTING_STARTED.md](GETTING_STARTED.md)** | Per-product quickstarts, standalone |
| **[COMBINED_INSTALL.md](COMBINED_INSTALL.md)** | Two-product recipes and the full four-product install |
| **[ARCHITECTURE.md](ARCHITECTURE.md)** | How the products interact, with deployment diagrams |
| **[docs/ORGANIZATION_MODEL.md](docs/ORGANIZATION_MODEL.md)** | Organization-aware onboarding — how one control plane scales from an individual to a company by adding structure, not switching editions (design direction) |
| **[docs/SETUP_HUMAN_GUIDED.md](docs/SETUP_HUMAN_GUIDED.md)** | The 15-stage visual setup flow for people new to terminals, keys, and providers (design direction) |
| **[docs/SETUP_AGENT_LED.md](docs/SETUP_AGENT_LED.md)** | Zero-trust agent-led setup — the agent proposes, humans approve, privileges are temporary (design direction) |
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
- **ComputeConnect — MVP.** Runtime is real; **single-host two-engine heterogeneity is proven**
  (2026-07-27); cross-machine placement remains open.
- **ToolConnect — MVP service.** Runtime is real; still no tool execution by design, and the
  protocol-neutral claim is only partially proven.

Ecosystem-level status, stated plainly:

- **PyPI name — RESOLVED.** BrainConnect publishes as the distribution **`brainconnect-ai`**
  (`pip install brainconnect-ai`); the import package and console command stay `brainconnect`.
  The old `brainconnect` collision is no longer a publication blocker. Do **not** `pip install
  brainconnect` bare — that is an unrelated third-party package.
- **AgentConnect ↔ ToolConnect — enforcement at the final invocation boundary.** `agentconnect-core`
  carries a fail-closed `ToolConnectGovernor`; as of contract **`1.1`** (2026-07-27) authorization
  binds the exact final arguments of every side-effecting tool call: authorize issues a one-use
  argument-bound grant, the act loop redeems it immediately before executing the same frozen
  arguments, and any deny/outage/redeem failure refuses execution. The earlier pre-spawn toolset
  check remains as a cheap early filter, not the enforcement point.
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
