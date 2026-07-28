# Data and compliance boundaries

**Connect should handle as little customer data as technically possible, and is architected
so that it usually *cannot* access customer content. This document defines, component by
component, what data is processed, stored, transmitted, and retained — and what must never
reach a central Connect service.**

> **Status: this is the data-boundary contract the ecosystem is built to honor.** Some of it
> is enforced in shipped code today (BrainConnect's local ledger, ToolConnect's metadata-only
> events, ComputeConnect's default-deny privacy filter, the event bus's re-redaction). Some
> of it constrains components that do not exist yet (the control-plane application, the
> marketplace). Each row below marks which. Per [MANIFESTO §8](MANIFESTO.md), an unbuilt
> guarantee is named as unbuilt. The point of writing it down now is that the components not
> yet built must be built to satisfy this contract, not retrofitted to it later.

---

## The goal is architectural, not a policy promise

A privacy policy says "we will not look." Data minimization says "we cannot look, because the
content never reaches us." Connect aims for the second wherever possible. Customer content —
prompts, model outputs, source code, documents, patient data, company knowledge, private
memory, raw tool arguments and outputs, secrets, credentials, workspace files, terminal
contents — should remain within:

- the customer's device;
- customer-controlled infrastructure;
- customer-selected hosting, models, memory, and tools.

## Prohibited central data (all components)

Regardless of component, a central Connect service (the control-plane backend or the
marketplace) must **not** receive or store, by default:

- prompts or model outputs
- source code, documents, or workspace files
- patient data or other regulated content
- private memory content
- raw tool arguments or raw tool outputs
- secrets or credentials
- terminal contents
- a customer's permanent employee directory

The marketplace must function **without** workspace content or private agent context. If a
future feature appears to require any prohibited item centrally, that is a design defect to be
resolved by moving the computation to the customer-controlled deployment — not a reason to
relax this list.

## Component-by-component data matrix

Legend for **Enforced?**: **Shipped** = true in code today; **Design** = constrains a
component not yet built; **Mixed** = partly shipped.

### Connect control plane (management plane)

| | |
|---|---|
| **Ships today** | Manifest, deploy bundle, cross-product docs — **no code, no service** ([README](README.md)) |
| **Target role** | Org model, onboarding, marketplace discovery, budget *visibility*, policy configuration, cross-plane observability |
| **Processed locally** | Org structure, onboarding choices, policy bindings, cost *view* — within the customer-controlled deployment wherever possible |
| **Stored centrally** | Nothing today. Target: as little as possible; **not** the employee directory permanently ([ORGANIZATION_MODEL §Importing an existing organization](docs/ORGANIZATION_MODEL.md#importing-an-existing-organization)) |
| **Transmitted** | N/A today. Target: marketplace **transaction metadata only** (see marketplace row) |
| **Default retention** | N/A today |
| **Optional telemetry** | Off by default; opt-in; never customer content ([TRANSPARENCY.md](TRANSPARENCY.md)) |
| **Prohibited central data** | The full [prohibited list](#prohibited-central-data-all-components) |
| **Enforced?** | **Design** (control-plane app unbuilt; see [ADR 0002](docs/adr/0002-control-plane-repository-boundary.md)) |

### Work plane — AgentConnect

| | |
|---|---|
| **Processed locally** | Tasks, assignments, attempts, artifacts, reviews, routing decisions; harness coordination |
| **Stored** | Local operator ledger (SQLite); workspaces on the customer's disk |
| **Transmitted** | Best-effort metadata to the event bus (below); model calls go to the customer's chosen provider, not Connect. Secrets are **never** placed in model context |
| **Default retention** | Ledger persists locally until the operator deletes it; no central copy |
| **Optional telemetry** | Event-bus publish is opt-in and metadata-only |
| **Prohibited central data** | Workspace files, terminal contents, prompts, outputs, secrets never leave the deployment centrally |
| **Enforced?** | **Shipped** (local ledger, secret-free model context) |

### Knowledge plane — BrainConnect

| | |
|---|---|
| **Processed locally** | Memory candidates, promotion/rejection, provenance, contradiction, recall — deterministic, zero model calls in the `brainconnect` command |
| **Stored** | Local SQLite ledger (default `~/.wiki-brain/wiki.db`), outside the working tree; generated wiki is a local projection |
| **Transmitted** | Loopback HTTP by default (`127.0.0.1:8787`); optional librarian drafting speaks to a customer-chosen local/self-hosted model endpoint; foreign-store federation is **read-only** and copies nothing |
| **Default retention** | Local, operator-controlled; no external service may write trusted memory |
| **Optional telemetry** | Metadata-only event-bus publish (reserved) |
| **Prohibited central data** | Memory content never transmitted to a central Connect service |
| **Enforced?** | **Shipped** (local-first ledger, read-only federation) |

### Capability plane — ToolConnect

| | |
|---|---|
| **Processed locally** | Tool identity, authorization decisions, argument-bound grants, outcome records |
| **Stored** | Local SQLite; a tamper-evident audit chain. The decision core has **no `invoke()`** and is never on the data path — it never computes or stores raw arguments |
| **Transmitted** | Metadata-only events (ids, hashes, decision outcomes, policy names); `args_hash` is published, **never the arguments it was hashed from**. Publisher is **off unless explicitly configured** |
| **Default retention** | Local audit chain; operator-controlled |
| **Optional telemetry** | Event-bus publish disabled by default (requires both bus URL and token) |
| **Prohibited central data** | Raw tool payloads, arguments, outputs, prompts, secrets — structurally absent because the core never holds them |
| **Enforced?** | **Shipped** (no data path, metadata-only events, default-off publisher) |

### Compute plane — ComputeConnect

| | |
|---|---|
| **Processed locally** | Provider discovery, resource fit, placement, privacy tiers, health |
| **Stored** | Provider registry and optional run journal; no prompt or output content |
| **Transmitted** | Routes inference to customer-run engines as a **thin proxy**; never loads a tensor; hides topology from consumers; structural **default-deny** privacy filtering (absent tier ⇒ most restrictive) |
| **Default retention** | Operational metadata only; no content retention |
| **Optional telemetry** | Metadata-only edge-triggered provider events |
| **Prohibited central data** | Prompts and outputs are proxied, not stored centrally by Connect |
| **Enforced?** | **Shipped** (default-deny filter, topology hiding, thin proxy) |

### Event bus (cross-plane)

| | |
|---|---|
| **What it is** | One append-only, best-effort **projection** stream in AgentConnect's existing ledger — *never a system of record, never authoritative* |
| **Transmitted** | Ids, hashes, decision outcomes, policy names, redacted summaries |
| **Store-side control** | Every ingested event is **re-redacted** against its declared privacy tier regardless of publisher pre-redaction |
| **Prohibited central data** | **Never** raw tool arguments, prompts, model output, secrets, or artifact content |
| **Enforced?** | **Shipped** (re-redaction, projection semantics) — [EVENT_BUS.md](EVENT_BUS.md) |

### Marketplace (target)

| | |
|---|---|
| **Processed** | Discovery, comparison, transactions, disclosed fees |
| **May receive** | For a marketplace-billed transaction: authoritative transaction data, disclosed fee, payment status, vendor & customer transaction identifiers |
| **Must not require** | Workspace content or private agent context to function |
| **Payment data** | Payment-card data stays with the payment processor whenever technically possible; Connect minimizes possession of financial data |
| **Prohibited central data** | The full [prohibited list](#prohibited-central-data-all-components); customer content is excluded from central marketplace processing by default |
| **Enforced?** | **Design** (marketplace unbuilt; see [MARKETPLACE_ARCHITECTURE.md](MARKETPLACE_ARCHITECTURE.md)) |

---

## Compliance enablement is not automatic compliance

**Installing Connect does not make a customer GDPR-, SOC 2-, or HIPAA-compliant.** Compliance
depends on the deployment, provider choices, contracts, organizational policy, technical
configuration, and operational procedures — none of which a control plane can supply on the
customer's behalf. Any documentation that says otherwise is wrong and must be corrected.

What Connect *does* is make compliant systems significantly easier to design and operate,
through:

- data minimization (this document)
- data-flow visibility (the cost and observability views)
- customer-controlled infrastructure (nothing forces a hosted model)
- least privilege and zero-trust policy
- workspace isolation ([AgentConnect workspace isolation](https://github.com/Judgernaut777/AgentConnect/blob/main/docs/WORKSPACE_ISOLATION.md))
- auditability (per-plane audit surfaces)
- regional filtering and retention controls (provider metadata)
- provider evidence and marketplace metadata (below)
- exportability and deletion configuration

## Marketplace compliance evidence

Compliance-related provider characteristics are searchable and **distinguishable per
framework** — never collapsed into a single "compliant" badge. The full field lists live in
[MARKETPLACE_ARCHITECTURE.md §Compliance evidence](MARKETPLACE_ARCHITECTURE.md#compliance-evidence-is-searchable-and-distinguishable):

- **GDPR:** processing/storage regions, DPA availability, subprocessors, retention/deletion/
  export controls, international-transfer mechanism, customer-managed encryption, controller/
  processor roles.
- **SOC 2:** Type I/II, report period, covered services, report availability, verification
  date, complementary user-entity controls, scope exclusions.
- **HIPAA:** BAA availability, covered products, PHI-capable status, encryption, audit
  controls, retention behavior, access controls, scope exclusions.

These fields let a customer *find* providers whose evidence fits their obligations. They are
inputs to the customer's compliance work, not a substitute for it.

## See also

- [PRODUCT_THESIS.md](PRODUCT_THESIS.md) — data belongs to the customer.
- [MARKETPLACE_ARCHITECTURE.md](MARKETPLACE_ARCHITECTURE.md) — the compliance-evidence fields.
- [TRANSPARENCY.md](TRANSPARENCY.md) — the public commitments and telemetry controls.
- [EVENT_BUS.md](EVENT_BUS.md) — the projection contract and re-redaction.
- [docs/SECURITY_BOUNDARIES.md](docs/SECURITY_BOUNDARIES.md) — the security/compliance boundary the planes enforce.
