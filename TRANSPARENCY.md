# Transparency

**Your data stays yours. Your tools stay yours. Your choices stay yours. Connect helps them
work together.**

This document is the plain statement of what Connect does and does not do with data, money,
and rankings. It exists so a customer never has to reverse-engineer the business model from
behavior.

> **Status: these are the commitments the product is built to keep.** Where a commitment
> constrains a component that does not exist yet (the marketplace, the control-plane
> application), it is a design constraint on that component. Where it describes shipped
> behavior, it is verifiable in the code today. Per [MANIFESTO §8](MANIFESTO.md), an unbuilt
> guarantee is named as unbuilt.

---

## What Connect stores

As little as technically possible. In the current products, the durable stores are
**local to the customer's deployment**: AgentConnect's operator ledger, BrainConnect's memory
ledger, ToolConnect's audit chain, ComputeConnect's provider registry. See
[DATA_AND_COMPLIANCE_BOUNDARIES.md](DATA_AND_COMPLIANCE_BOUNDARIES.md) for the component-level
matrix.

## What Connect does not store

By default, and by design, a central Connect service does not receive or store: prompts,
model outputs, source code, documents, regulated content, private memory content, raw tool
arguments or outputs, secrets, credentials, workspace files, terminal contents, or a
customer's permanent employee directory. The marketplace works **without** workspace content
or private agent context.

## What leaves the customer environment

- **Model, tool, memory, compute, and hosting traffic** goes to the providers the *customer*
  selected — their own accounts, subscriptions, contracts, or marketplace choices — not to
  Connect.
- **The event bus**, when enabled, carries a redacted, metadata-only projection (ids, hashes,
  outcomes, policy names), re-redacted store-side against each event's privacy tier. Never raw
  arguments, prompts, output, secrets, or artifact content.
- **Marketplace transactions**, when a customer buys through the marketplace, produce
  transaction metadata (ids, disclosed fee, payment status, vendor/customer transaction
  identifiers). Payment-card data stays with the payment processor whenever technically
  possible.

Nothing else leaves by default. Telemetry is covered [below](#how-telemetry-is-controlled).

## How marketplace transactions work

Independent vendors provide the products and services; Connect facilitates discovery,
comparison, setup, and the transaction. Connect does not sell the underlying hosting,
inference, compute, tools, memory, or storage itself. See
[MARKETPLACE_ARCHITECTURE.md](MARKETPLACE_ARCHITECTURE.md).

## When Connect receives a fee

Connect earns money in exactly two ways:

1. A **marketplace transaction fee**, charged **only** when Connect actually facilitates a
   paid transaction between a customer and an independent vendor. The fee is disclosed.
2. A **vendor verification / certification fee**, paid by a vendor for a defined evaluation.

Connect charges **nothing** for: customer-owned computers, GPUs, or servers; local or free
models; attaching an existing account, subscription, or contract; externally purchased
services; self-hosting; or free and open-source marketplace listings. There are **no Connect
subscriptions, no per-seat licensing, no feature-gated enterprise edition, and no
professional-services or consulting business.** See
[MANIFESTO §*What we will not build*](MANIFESTO.md#what-we-will-not-build).

## How verification works

A vendor may pay for verification. **Payment buys the evaluation, never the outcome** — not a
positive result, not preferred ranking, not favorable wording, not recommendation status. Every
verification result states what was tested, the standard used, the tested version, the date,
the evidence, the limitations, and any expiration or re-verification requirement. Free and
community projects have routes to verification (automated checks, community verification,
grants, waived fees, sponsored reviews) so verification is not a pay-to-appear wall.

## How rankings and sorting work

Connect provides **neutral sorting, filtering, comparison, and structured metadata** on
published criteria. Connect does **not** build a centralized behavioral profile to decide what
a customer should buy, and is not a personalized recommendation service. Personalization
belongs to the **customer's own agent**, which may use privately held context (budget, privacy
needs, hardware, policy, existing subscriptions, compliance requirements) to query marketplace
hooks and propose options — with that context staying customer-controlled.

General beginner presets may be offered, but they are **non-personalized by default,
explainable, clearly labeled as general defaults, based on published criteria, and easy to
override.**

## How sponsorship is labeled

Any sponsored or paid placement is clearly labeled as such and is kept separate from
verification results and from neutral sorting. A paid placement never presents itself as a
verification outcome or a neutral ranking.

## How benchmark data is sourced and dated

Every benchmark shown in a marketplace listing carries its **source and date**, so a stale
number reads as stale rather than as a current fact. Benchmarks are metadata on the listing,
not claims made by Connect.

## How telemetry is controlled

Telemetry is **off by default and opt-in.** It never includes customer content. A customer can
see what any enabled telemetry contains and turn it off. The current products already run
local-first with no required outbound telemetry; the control-plane product must preserve this
default when it is built.

## How data can be exported or deleted

The customer's durable data lives in customer-controlled stores, so export and deletion are
operations the customer controls. Marketplace listings expose provider export and deletion
support as searchable metadata so a customer can choose providers whose export/deletion
behavior fits their obligations. See
[DATA_AND_COMPLIANCE_BOUNDARIES.md](DATA_AND_COMPLIANCE_BOUNDARIES.md).

## Compliance, stated honestly

Installing Connect does **not** make a customer GDPR-, SOC 2-, or HIPAA-compliant. Connect
*enables* compliant designs through data minimization, data-flow visibility,
customer-controlled infrastructure, least privilege, zero-trust policy, workspace isolation,
auditability, regional filtering, retention controls, provider evidence, and marketplace
metadata. Compliance still depends on the customer's deployment, contracts, policy, and
operations.

## The commitment

> Your data stays yours. Your tools stay yours. Your choices stay yours. Connect helps them
> work together.

## See also

- [PRODUCT_THESIS.md](PRODUCT_THESIS.md)
- [MARKETPLACE_ARCHITECTURE.md](MARKETPLACE_ARCHITECTURE.md)
- [DATA_AND_COMPLIANCE_BOUNDARIES.md](DATA_AND_COMPLIANCE_BOUNDARIES.md)
- [MANIFESTO.md](MANIFESTO.md#what-we-will-not-build)
