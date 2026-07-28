# Product thesis

**Connect is a free, open-source, easy-to-use, zero-trust AI control plane for making
agents usable.**

The primary product phrase is **Making Agents Usable**.

> **Status: this document states the target product, and separates it from what ships
> today.** The five repositories today are an *integration and infrastructure* layer — four
> standalone products plus this documentation umbrella — not the visual control-plane
> application described below. Where this document describes the target product, it says so.
> Where it describes shipped behavior, it says that. Per [MANIFESTO §8](MANIFESTO.md), a
> capability that is not built is named as not built, in the place a reader would look for it.
> Nothing here should be read as a claim that the control-plane application, marketplace,
> onboarding wizard, or generalized budget engine already exists. They do not. This document
> is the thesis the ecosystem is being built toward, written down so implementation converges
> on it rather than on convention.

---

## What Connect is

Connect makes existing agent systems easier to install, configure, operate, coordinate,
secure, isolate, observe, budget, replace, and use together. It is a control plane: the
place a human or an agent goes to stand up a working environment, see what it costs, keep it
inside policy, and swap any piece of it out.

The stable, user-facing abstraction is the **workspace** — an isolated place where agent
work happens under a name, a policy, and a budget — **not** the harness that happens to run
inside it.

## What Connect is not

**Connect is not another coding harness.** It does not replace, and is not a competitor to:

- Claude Code
- Codex
- Hermes
- OpenHands
- other coding harnesses
- future agent executors
- existing meta-harnesses

Harnesses remain the native executors. The [Work plane](#the-five-planes) (AgentConnect)
coordinates them as **interchangeable execution options**, so a workspace can move from one
harness to another without the user rebuilding the environment around it. Connect adds the
control plane those harnesses lack; it does not add a new harness for them to compete with.

Connect is also not a hosting provider, a GPU cloud, an inference host, a managed-memory
host, a hosted-workspace operator, a data custodian, a consulting organization, or a
subscription vendor. Each of those is a deliberate refusal — see
[the business model](#the-business-model-in-one-paragraph) and
[MANIFESTO §*What we will not build*](MANIFESTO.md#what-we-will-not-build).

## Making agents usable

An agent is *runnable* today for someone who is comfortable with a terminal, an API key, a
secrets manager, an MCP server, and a model provider. It is not yet *usable* — not for a
person who has never touched any of those, and not at the scale of a company that needs many
agents under many budgets and policies without a new tool for each concern. "Making agents
usable" is the work of closing that gap:

- **Install** — detect what a customer already has; stand up the missing pieces without a
  scavenger hunt across five READMEs.
- **Configure** — one guided flow over harnesses, models, memory, tools, secrets, compute,
  hosting, isolation, security, compliance, and budgets.
- **Operate & coordinate** — run and observe work across harnesses through the Work plane,
  with one abstraction (the workspace) rather than one per tool.
- **Secure & isolate** — zero-trust policy and pluggable workspace isolation, so a workspace
  is bounded by default rather than by remembering to bound it.
- **Observe & budget** — one view of what is happening and what it costs, across resources
  the customer owns, rents, and buys.
- **Replace** — every piece is swappable: harness, model, memory provider, tool, compute,
  hosting. Nothing in the control plane is a lock-in point.
- **Use together** — the seams between these are the product; the individual pieces already
  exist in the world.

## The five planes

Connect is organized around distinct authorities. No plane replaces the authority beneath
it. This is the same table the [README](README.md#five-planes-one-platform) and
[ARCHITECTURE.md](ARCHITECTURE.md) use, stated here in product terms.

| Plane | Product | Owns |
|---|---|---|
| **Control** | Connect | Visual workspaces, setup/onboarding, organization config, marketplace discovery, external-service attachment, budget visibility, remote workspace access, policy configuration, control-plane status, cross-plane observability |
| **Work** | AgentConnect | Tasks, assignments, delegation, attempts, execution records, artifacts, review, worker & harness coordination, workspace lifecycle, budget enforcement against work, organizational workflow |
| **Knowledge** | BrainConnect | Trusted durable memory, provenance, candidates, contradiction, supersession, recall, memory-provider interoperability, human-controlled trust promotion |
| **Capability** | ToolConnect | Tool identity, trusted tool metadata, assertions, authorization, bounded discovery, grants, capability policy, outcome evidence, tool audit |
| **Compute** | ComputeConnect | Compute & provider discovery, resource fit, workload placement, privacy-aware routing, hardware knowledge, provider availability, compute cost & capability metadata |

The Control plane coordinates the other four; it does not run their workloads, hold their
trust, decide their authorizations, or place their compute. It stays deliberately thin.

**Repository note.** The *Connect repository* today owns ecosystem integration, release
coordination, deployment composition, compatibility, manifests, and cross-repository
documentation. The user-facing **control-plane application** described above may require a
separate repository; that decision is made in
[ADR 0002](docs/adr/0002-control-plane-repository-boundary.md) and no substantial
control-plane implementation begins in this repository until that ADR is accepted.

## Current state vs target

| | Ships today | Target product |
|---|---|---|
| **Connect repo** | Manifest, deploy bundle, cross-product docs (no code) | Coordinates a visual control-plane app; app repo decided by [ADR 0002](docs/adr/0002-control-plane-repository-boundary.md) |
| **Planes** | Four standalone `0.1.0` products with named limitations ([README](README.md#status-at-a-glance)) | The same four, coordinated under one control plane |
| **Setup** | Per-product READMEs; a documented org-aware *design direction* ([docs/ORGANIZATION_MODEL.md](docs/ORGANIZATION_MODEL.md)) | Human-guided and agent-led onboarding ([docs/SETUP_HUMAN_GUIDED.md](docs/SETUP_HUMAN_GUIDED.md), [docs/SETUP_AGENT_LED.md](docs/SETUP_AGENT_LED.md)) |
| **Marketplace** | Documented architecture only ([MARKETPLACE_ARCHITECTURE.md](MARKETPLACE_ARCHITECTURE.md)) | Neutral discovery/comparison/transactions for independent vendors |
| **Budgets** | AgentConnect's current simple budget ([AgentConnect BUDGET_MODEL.md](https://github.com/Judgernaut777/AgentConnect/blob/main/docs/BUDGET_MODEL.md)) | Generalized budgets: arbitrary amounts, intervals, overlap, scopes, delegation |

The current simple pieces must not be mistaken for the final ones. In particular, the
current budget implementation is a starting point, not the target model.

## The business model, in one paragraph

Connect must be genuinely usable **for free**: a complete environment built from
customer-owned computers and GPUs, local or free models, open-source harnesses, self-hosted
memory and tools, and externally purchased subscriptions the customer already has — with no
payment to Connect. The free path is never intentionally degraded to force marketplace use.
There are **no Connect subscriptions** at any organizational size, no per-seat licensing, no
feature-gated "enterprise edition," no professional-services or consulting business, and no
Connect-owned hosting, inference, or compute. Connect **never charges for customer-owned
resources** or for attaching an existing account, subscription, or contract. Revenue comes
only from **marketplace transaction fees** (charged when Connect actually facilitates a paid
transaction between a customer and an independent vendor) and **transparent vendor
verification fees** (which never buy a favorable outcome, ranking, or wording). See
[MARKETPLACE_ARCHITECTURE.md](MARKETPLACE_ARCHITECTURE.md) for the full model and
[TRANSPARENCY.md](TRANSPARENCY.md) for the commitments.

## Data belongs to the customer

Connect should handle as little customer data as technically possible, and is architected so
that it usually *cannot* access customer content — prompts, outputs, code, documents,
memory, secrets, tool payloads, or workspace files stay within the customer's device and
customer-controlled infrastructure. The marketplace does not require workspace content or
private agent context to function. Personalization belongs to the *customer's own agent*
operating on customer-controlled context, never to a centralized behavioral profile held by
Connect. See [DATA_AND_COMPLIANCE_BOUNDARIES.md](DATA_AND_COMPLIANCE_BOUNDARIES.md).

## The controlling statement

> Connect is a free, open-source, top-of-the-line, easy-to-use, zero-trust AI control plane
> for making agents usable. It coordinates native harnesses, work, memory, capabilities,
> compute, secure workspaces, organizations, flexible budgets, and a neutral marketplace
> without becoming the customer's host, data custodian, consultant, or subscription vendor.
> Customers may freely use their own models, subscriptions, contracts, tools, memory,
> hosting, and compute. Connect earns revenue only when it facilitates optional marketplace
> transactions or performs transparent vendor verification. Personalization belongs with the
> customer's own agent, operating on customer-controlled context.

## See also

- [README.md](README.md) — what exists today and how the products fit together.
- [MANIFESTO.md](MANIFESTO.md) — the engineering philosophy and *what we will not build*.
- [MARKETPLACE_ARCHITECTURE.md](MARKETPLACE_ARCHITECTURE.md) — the marketplace and business model.
- [DATA_AND_COMPLIANCE_BOUNDARIES.md](DATA_AND_COMPLIANCE_BOUNDARIES.md) — the data matrix and compliance stance.
- [TRANSPARENCY.md](TRANSPARENCY.md) — the public commitments.
- [docs/ORGANIZATION_MODEL.md](docs/ORGANIZATION_MODEL.md) — organization-aware onboarding.
- [docs/adr/0002-control-plane-repository-boundary.md](docs/adr/0002-control-plane-repository-boundary.md) — where the control-plane application lives.
