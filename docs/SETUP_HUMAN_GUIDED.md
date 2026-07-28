# Human-guided setup

**Connect must be usable by someone who has never touched a terminal, an API key, a secrets
manager, an MCP server, a model provider, or local inference. The human-guided flow is the
polished visual setup that makes that true.**

> **Status: design direction, not shipped behavior.** No onboarding wizard ships in any
> `0.1.0` product today — none of the planes has an installer UI, and the control-plane
> application that would host this flow is not yet built (see
> [ADR 0002](adr/0002-control-plane-repository-boundary.md)). This document specifies the flow
> the control-plane product is built toward. Per [MANIFESTO §8](../MANIFESTO.md), an unbuilt
> capability is named as unbuilt. Read it as the contract the design must honor.

---

## Principle: progressive disclosure

Beginners see understandable choices; advanced users retain access to full configuration and
native terminals. The same flow scales from an individual to a large multi-department
organization by *adding stages*, not by switching products (see
[ORGANIZATION_MODEL.md](ORGANIZATION_MODEL.md)). At every category, the customer may **bring
what they already have** before being shown any marketplace option (see
[ORGANIZATION_MODEL.md §Bring-your-own services](ORGANIZATION_MODEL.md#bring-your-own-services)).

## The flow

The human-guided flow covers fifteen stages. A smaller profile collapses or skips stages it
does not need; a larger one expands them.

| # | Stage | What the customer decides | Plane(s) that enforce it |
|---|---|---|---|
| 1 | **Intended use** | Coding, research, automation, or a mix; the kind of work agents will do | Connect (routing later) |
| 2 | **Organization size & structure** | Individual, household, small team, mid-sized, large, or custom — a *profile*, not an edition | Connect |
| 3 | **Existing resources** | Detect and attach what the customer already has: machines, GPUs, accounts, subscriptions, contracts, harnesses, servers | All planes |
| 4 | **Harness selection & installation** | Which coding/agent harnesses (Claude Code, Codex, others); install or attach them | Work (AgentConnect) |
| 5 | **Model & provider selection** | Local, free, existing-subscription, existing-contract, or marketplace model/inference providers | Compute + Work |
| 6 | **Memory configuration** | Local BrainConnect, an existing memory provider, or a marketplace option; personal vs shared scopes | Knowledge (BrainConnect) |
| 7 | **Tool configuration** | Approved/prohibited tools and MCP servers; internal vs external registries | Capability (ToolConnect) |
| 8 | **Secrets manager selection** | Local default, an existing secrets manager, an org provider, or a marketplace option | Connect + Work |
| 9 | **Compute configuration** | Use this computer, an owned server, an existing hosting account, rented/marketplace compute; regional/residency rules | Compute (ComputeConnect) |
| 10 | **Hosting configuration** | Local, owned, existing hosting account, or a marketplace hosting provider (a **primary** marketplace category) | Compute + Connect |
| 11 | **Workspace isolation** | Isolation level 0–3 (unmanaged → managed → container → microVM/remote), via pluggable enforcement providers | Work (AgentConnect) |
| 12 | **Security profile** | Zero-trust policy defaults, least-privilege grants, approval thresholds | Capability + Work |
| 13 | **Compliance requirements** | Regional filtering, retention, deletion, DPA/BAA/SOC 2 needs expressed as provider filters | Connect + Compute |
| 14 | **Budgets** | Arbitrary amounts, intervals, scopes; soft/hard limits, alerts, delegation | Work (AgentConnect) |
| 15 | **Validation & final review** | A preview of everything configured, with a clear approve step; the environment is validated before it is live | Connect + all planes |

## Beginners see less, advanced users lose nothing

- An **individual** typically sees stages 1, 3, 4, 5, 6, 14, 15 — a short flow that produces a
  safe personal workspace. Departments, roles, approval chains, and organizational policy stay
  out of the way unless the person asks for them.
- A **large organization** sees every stage, plus organizational import, identity integration,
  administrator delegation, policy inheritance, budget allocation, marketplace restrictions,
  compliance requirements, and regional deployment.

No capability is withheld from a smaller customer to reserve it for a larger buyer. The
individual experience is *simpler*, not *lesser*.

## Isolation levels (stage 11)

Workspace isolation is chosen here and enforced by the Work plane through **pluggable
enforcement providers** — AgentConnect is not itself a container or virtualization
implementation. The levels a customer chooses among:

- **Level 0** — unmanaged execution.
- **Level 1** — managed directories, environment, credentials, and tools.
- **Level 2** — container isolation.
- **Level 3** — strong isolation via microVMs or isolated remote workers.

See [AgentConnect workspace isolation](https://github.com/Judgernaut777/AgentConnect/blob/main/docs/WORKSPACE_ISOLATION.md)
for what ships today (Levels 0–1) versus what is design direction (Levels 2–3).

## Budgets (stage 14)

The budget stage configures the [generalized budget model](https://github.com/Judgernaut777/AgentConnect/blob/main/docs/BUDGET_MODEL.md):
any amount, any interval, any number of overlapping budgets, arbitrary scopes, and delegated
allocations. An individual sets one simple personal budget; an organization sets delegated
departmental budgets. The large-organization model is never forced onto an individual.

## See also

- [SETUP_AGENT_LED.md](SETUP_AGENT_LED.md) — the agent-led alternative to this flow.
- [ORGANIZATION_MODEL.md](ORGANIZATION_MODEL.md) — profiles, bring-your-own, ownership, adoption.
- [../PRODUCT_THESIS.md](../PRODUCT_THESIS.md) — the product this flow belongs to.
- [../MARKETPLACE_ARCHITECTURE.md](../MARKETPLACE_ARCHITECTURE.md) — the marketplace options each stage may offer.
