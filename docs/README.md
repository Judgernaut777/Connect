# docs/

Longer-form ecosystem documents that do not belong in a top-level file.

The top-level documents are deliberately short; material that outgrows them lands here rather
than bloating the front door. Start at the repository [README](../README.md) and
[PRODUCT_THESIS.md](../PRODUCT_THESIS.md); this folder holds the depth behind them.

## Product, marketplace, and policy (target product — design direction)

These describe the target control-plane product. The user-facing application, marketplace, and
onboarding they describe **do not ship yet**; each says so in its first lines.

| Document | Read it for |
|---|---|
| [ORGANIZATION_MODEL.md](ORGANIZATION_MODEL.md) | Organization-aware onboarding: profiles not editions, bring-your-own, ownership, adoption, billing arrangements |
| [SETUP_HUMAN_GUIDED.md](SETUP_HUMAN_GUIDED.md) | The 15-stage visual setup flow with progressive disclosure |
| [SETUP_AGENT_LED.md](SETUP_AGENT_LED.md) | Zero-trust agent-led setup: propose → approve → temporary grants → revoke |

The canonical product thesis, marketplace architecture, data/compliance boundaries, and
transparency commitments live at the repository root:
[PRODUCT_THESIS.md](../PRODUCT_THESIS.md), [MARKETPLACE_ARCHITECTURE.md](../MARKETPLACE_ARCHITECTURE.md),
[DATA_AND_COMPLIANCE_BOUNDARIES.md](../DATA_AND_COMPLIANCE_BOUNDARIES.md),
[TRANSPARENCY.md](../TRANSPARENCY.md).

## Operating the shipped stack (current behavior)

| Document | Read it for |
|---|---|
| [RELEASE.md](RELEASE.md) | The manifest-driven release model |
| [SECURITY_BOUNDARIES.md](SECURITY_BOUNDARIES.md) | The compliance/security boundary the planes enforce |
| [OBSERVABILITY.md](OBSERVABILITY.md) · [OBSERVABILITY_HERDR.md](OBSERVABILITY_HERDR.md) | The observation-event model and the (off) Herdr provider |
| [PRODUCTION_CHECKLIST.md](PRODUCTION_CHECKLIST.md) | Pre-flight before depending on the stack |
| [UPGRADE_ROLLBACK.md](UPGRADE_ROLLBACK.md) · [BACKUP_RESTORE.md](BACKUP_RESTORE.md) | Cross-product upgrade, rollback, backup, restore |
| [TROUBLESHOOTING.md](TROUBLESHOOTING.md) | Symptoms, causes, fixes from building the deploy stack |

## Decisions

| ADR | Decision |
|---|---|
| [adr/0001-deploy-directory.md](adr/0001-deploy-directory.md) | Connect may carry a `deploy/` directory (config + scripts, not product code) — Accepted |
| [adr/0002-control-plane-repository-boundary.md](adr/0002-control-plane-repository-boundary.md) | Where the user-facing control-plane application lives — Proposed |

## What belongs here

- Extended design notes that span more than one product
- Deep-dives referenced from [ARCHITECTURE.md](../ARCHITECTURE.md)
- Scope proposals for a proposed new product, once accepted
- Target-product design direction, clearly marked as not-yet-shipped

## What does not

The same rules as the repository root apply — see [CONTRIBUTING.md](../CONTRIBUTING.md). No
code. Nothing that describes a single product in isolation; that belongs in the product's own
repository.

## Where the product-level documents actually live

No product keeps its internals documented here. Follow the source.

| Topic | Where |
|---|---|
| Running the managed coding-agent loop | `docs/OPERATOR_GUIDE.md` in [AgentConnect](https://github.com/Judgernaut777/AgentConnect) |
| The generalized budget model, and workspace isolation via pluggable enforcement | `docs/BUDGET_MODEL.md`, `docs/WORKSPACE_ISOLATION.md` in AgentConnect |
| AgentConnect internals, safety, work queue, federation | `docs/` in AgentConnect |
| The memory ledger design contract, and the trust rule every consumer must obey | `docs/LEDGER_SPEC.md` in [BrainConnect](https://github.com/Judgernaut777/BrainConnect) |
| The knowledge plane's ecosystem responsibilities | `docs/KNOWLEDGE_PLANE.md` in BrainConnect |
| The ToolConnect service surface, and why it is a decision point rather than a proxy | `docs/SERVICE.md`, `docs/ARCHITECTURE.md`, `docs/CAPABILITY_PLANE.md` in [ToolConnect](https://github.com/Judgernaut777/ToolConnect) |
| The ComputeConnect runtime and the owned/rented/external/marketplace compute distinctions | `docs/ARCHITECTURE.md`, `docs/COMPUTE_PLANE.md` in [ComputeConnect](https://github.com/Judgernaut777/ComputeConnect) |

Read a product's `docs/STATUS.md` before trusting any capability it describes. Both MVP
products are explicit about their limits: ComputeConnect's cross-machine placement is open
(single-host heterogeneity was proven 2026-07-27), and ToolConnect still has no tool execution
and only a partially proven protocol-neutral claim.
