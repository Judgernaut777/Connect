# Connect documentation index

**Start here.** This is the single map of every current Connect document — what it is, whether
it describes shipped behavior or target architecture, and where it lives. New contributors
should read [PRODUCT_THESIS.md](../PRODUCT_THESIS.md) and [MANIFESTO.md](../MANIFESTO.md) first,
then follow the section they need below.

Two states are labeled throughout the docs and in this index:

- **Current** — behavior that ships in a `0.1.0` product today.
- **Target** — design direction the ecosystem is converging on. The user-facing control-plane
  application, marketplace, onboarding wizard, and generalized budget engine **do not exist
  yet**; documents describing them say so in their opening lines.

The repository-boundary decision ([ADR 0002](adr/0002-control-plane-repository-boundary.md)) is
**Accepted** (2026-08-04): the user-facing control-plane application lives in a separate
repository, [`Connect-Control`](https://github.com/Judgernaut777/Connect-Control). This
repository remains docs-and-integration only.

---

## Product

| Document | State | Read it for |
|---|---|---|
| [PRODUCT_THESIS.md](../PRODUCT_THESIS.md) | Target | The canonical product: *Making Agents Usable*; free, open-source, zero-trust control plane; current vs target; the five planes |
| [MANIFESTO.md](../MANIFESTO.md) | Mixed | The engineering philosophy and **what Connect will never become / never degrade** |
| [README.md](../README.md) | Mixed | The front door: what ships today vs the target product |

## Architecture

| Document | State | Read it for |
|---|---|---|
| [ARCHITECTURE.md](../ARCHITECTURE.md) | Current | How the four planes interact through explicit contracts; wiring diagrams |
| [COMPATIBILITY.md](../COMPATIBILITY.md) | Current | The 0.1.0 version matrix, port registry, contracts, and known gaps (canonical) |
| [EVENT_BUS.md](../EVENT_BUS.md) | Current | The cross-plane observability stream — a projection, never a system of record |
| Plane docs (siblings) | Mixed | [Work](https://github.com/Judgernaut777/AgentConnect/blob/main/docs/README.md) · [Knowledge](https://github.com/Judgernaut777/BrainConnect/blob/main/docs/KNOWLEDGE_PLANE.md) · [Capability](https://github.com/Judgernaut777/ToolConnect/blob/main/docs/CAPABILITY_PLANE.md) · [Compute](https://github.com/Judgernaut777/ComputeConnect/blob/main/docs/COMPUTE_PLANE.md) |

## Marketplace

| Document | State | Read it for |
|---|---|---|
| [MARKETPLACE_ARCHITECTURE.md](../MARKETPLACE_ARCHITECTURE.md) | Target | Categories (hosting primary), free+paid listings, metadata, neutral sorting, verification, and the entire permitted revenue model |

## Setup

| Document | State | Read it for |
|---|---|---|
| [SETUP_HUMAN_GUIDED.md](SETUP_HUMAN_GUIDED.md) | Target | The 15-stage visual setup flow with progressive disclosure |
| [SETUP_AGENT_LED.md](SETUP_AGENT_LED.md) | Target | Zero-trust agent-led setup: propose → approve → temporary grants → revoke |
| [GETTING_STARTED.md](../GETTING_STARTED.md) | Current | Per-product standalone quickstarts (today's install path) |
| [COMBINED_INSTALL.md](../COMBINED_INSTALL.md) | Current | Two-product recipes and the full four-product install |

## Organizations

| Document | State | Read it for |
|---|---|---|
| [ORGANIZATION_MODEL.md](ORGANIZATION_MODEL.md) | Target | Organization-aware onboarding: profiles not editions, bring-your-own, ownership, adoption, billing arrangements |

## Privacy & Compliance

| Document | State | Read it for |
|---|---|---|
| [DATA_AND_COMPLIANCE_BOUNDARIES.md](../DATA_AND_COMPLIANCE_BOUNDARIES.md) | Mixed | The component-level data matrix, prohibited central data, and compliance enablement vs automatic compliance |
| [SECURITY_BOUNDARIES.md](SECURITY_BOUNDARIES.md) | Current | The compliance/security boundary the planes enforce |

## Transparency

| Document | State | Read it for |
|---|---|---|
| [TRANSPARENCY.md](../TRANSPARENCY.md) | Mixed | What Connect stores/doesn't, when a fee applies, ranking, sponsorship labeling, benchmark sourcing, telemetry control |

## ADRs

| ADR | Status | Decision |
|---|---|---|
| [adr/0001-deploy-directory.md](adr/0001-deploy-directory.md) | Accepted | Connect may carry a `deploy/` directory (config + scripts, not product code) |
| [adr/0002-control-plane-repository-boundary.md](adr/0002-control-plane-repository-boundary.md) | **Accepted** | The user-facing control-plane application lives in a separate repository, `Connect-Control`; Connect stays docs-only |

## Operations

| Document | State | Read it for |
|---|---|---|
| [RELEASE.md](RELEASE.md) | Current | The manifest-driven release model |
| [OBSERVABILITY.md](OBSERVABILITY.md) · [OBSERVABILITY_HERDR.md](OBSERVABILITY_HERDR.md) | Current | The observation-event model and the (off) Herdr provider |
| [PRODUCTION_CHECKLIST.md](PRODUCTION_CHECKLIST.md) | Current | Pre-flight before depending on the stack |
| [TROUBLESHOOTING.md](TROUBLESHOOTING.md) | Current | Symptoms, causes, fixes from building the deploy stack |
| [CONTRIBUTING.md](../CONTRIBUTING.md) | Current | What belongs in this repository (docs, no code) and the honesty standard |

## Recovery

| Document | State | Read it for |
|---|---|---|
| [BACKUP_RESTORE.md](BACKUP_RESTORE.md) | Current | Per-product backup and restore |
| [UPGRADE_ROLLBACK.md](UPGRADE_ROLLBACK.md) | Current | Cross-product upgrade and rollback sequencing |

## Historical documents

There is no `docs/history/` directory. Obsolete claims are corrected in place or marked
historical where they sit, per [CONTRIBUTING.md](../CONTRIBUTING.md):

- Superseded design/status text carries an in-place *superseded / historical* marker in the
  document where a reader would look (e.g. sibling `ARCHITECTURE.md` / `STATUS.md` banners).
- The [DOCUMENTATION_CORRECTION_REPORT.md](../DOCUMENTATION_CORRECTION_REPORT.md) is the audit
  trail for the ecosystem documentation-correction pass — what changed and why.
- Fascia-AI-OS is retired; it was replaced by this documentation repository and the four
  independently installable products (see [README.md](../README.md#history)).

---

## Where product-level documents live

No product keeps its internals documented here. Connect states a product's purpose in a
paragraph and links out; the product repository is the authority.

| Topic | Where |
|---|---|
| Running the managed coding-agent loop | `docs/OPERATOR_GUIDE.md` in [AgentConnect](https://github.com/Judgernaut777/AgentConnect) |
| The generalized budget model, and workspace isolation via pluggable enforcement | `docs/BUDGET_MODEL.md`, `docs/WORKSPACE_ISOLATION.md` in AgentConnect |
| The memory ledger design contract and the trust rule every consumer must obey | `docs/LEDGER_SPEC.md`, `docs/KNOWLEDGE_PLANE.md` in [BrainConnect](https://github.com/Judgernaut777/BrainConnect) |
| The ToolConnect service surface, and why it is a decision point rather than a proxy | `docs/SERVICE.md`, `docs/CAPABILITY_PLANE.md` in [ToolConnect](https://github.com/Judgernaut777/ToolConnect) |
| The ComputeConnect runtime and the owned/rented/external/marketplace compute distinctions | `docs/ARCHITECTURE.md`, `docs/COMPUTE_PLANE.md` in [ComputeConnect](https://github.com/Judgernaut777/ComputeConnect) |

Read a product's `docs/STATUS.md` before trusting any capability it describes. Both MVP
products are explicit about their limits: ComputeConnect's cross-machine placement is open
(single-host heterogeneity was proven 2026-07-27), and ToolConnect still has no tool execution
and only a partially proven protocol-neutral claim.
