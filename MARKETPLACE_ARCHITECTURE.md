# Marketplace architecture

**The marketplace is a central part of the Connect product and the whole of its business
model. Connect owns the marketplace infrastructure; independent vendors own the products and
services listed in it. Connect does not sell the underlying hosting, inference, compute,
tools, memory, or storage itself.**

> **Status: target architecture, not shipped behavior.** No marketplace runtime exists in
> any repository today. This document specifies the marketplace the control-plane product is
> being built toward — its categories, metadata, sorting model, verification process, and
> revenue model — so implementation converges on it. Per [MANIFESTO §8](MANIFESTO.md), an
> unbuilt system is named as unbuilt. Read this as the contract the design must honor, not a
> description of running software. The marketplace may initially ship as a **module of the
> control-plane product**, not a separate service or repository; see
> [ADR 0002](docs/adr/0002-control-plane-repository-boundary.md).

---

## The one thing the marketplace is for

Connect facilitates; vendors provide. For any product or service a customer might need to run
agents, the marketplace provides **discovery, comparison, compatibility information, setup,
transactions, policy application, budget visibility, and lifecycle control**. The vendor
provides the actual hosting, model, compute, tool, memory, storage, or service.

This is why Connect can offer a marketplace of hosting without becoming a host, a marketplace
of inference without becoming an inference provider, and a marketplace of compute without
owning a GPU. The marketplace is a coordination surface, not a resale business.

## The free path comes first

A customer must be able to run a complete Connect environment **without paying Connect and
without using the marketplace at all** — customer-owned computers and GPUs, local and free
models, open-source harnesses, self-hosted memory and tools, customer-controlled databases
and secrets managers, and externally purchased subscriptions. The marketplace is an
**optional procurement and simplification path, not a mandatory gateway**, and the free path
is never intentionally degraded to push customers into it.

### Bring-your-own is first-class

Before a customer is shown any marketplace alternative, every applicable setup category must
let them connect what they already have:

- connect an existing account
- connect an existing subscription
- use an organization-provided account
- connect an existing contract
- add an existing server
- configure a custom endpoint
- use a local or self-hosted option
- choose a marketplace option

Attaching an existing resource is always free — Connect never charges a marketplace fee for a
resource the customer already owns or already pays a third party for. See
[docs/ORGANIZATION_MODEL.md §Bring-your-own services](docs/ORGANIZATION_MODEL.md#bring-your-own-services).

### Consolidation is earned, never forced

Customers may later move externally billed services into marketplace billing because it
simplifies billing, budgeting, provisioning, transaction records, and vendor management.
Connect must earn that transition through convenience. It must **not** impair or degrade an
externally purchased service to force consolidation.

## Marketplace categories

The marketplace architecture must support at least the following categories. **Hosting is a
primary, first-class category — not a minor subtype of inference.**

- hosting providers
- hosted Connect workspaces
- hosted AgentConnect deployments
- hosted BrainConnect deployments
- hosted memory systems
- remote development environments
- sandbox providers
- model providers
- inference providers
- rented GPUs
- compute providers
- storage systems
- databases
- vector databases
- secrets managers
- coding and agent harnesses
- tools
- MCP servers
- integrations
- security products
- compliance-supporting products
- workspace templates

## Free and paid listings, side by side

Free and open-source options appear **alongside** commercial and managed options. A free
listing is not second-class merely because it produces no transaction fee. The marketplace
must make it easy to find free, open-source, local, self-hosted, community-maintained, paid,
managed, and verified options — as distinct, filterable facets, not buried beneath paid
inventory.

## Listing metadata

Listings expose structured, sortable, current metadata. At minimum:

| Group | Fields |
|---|---|
| **Commercial** | price; billing unit; free tier; open-source status; license |
| **Capability** | current benchmark results; benchmark source; benchmark date; latency; context limits; hardware requirements; local support |
| **Data & residency** | supported regions; data-processing regions; data-storage regions; retention policy; deletion support; exportability; encryption; customer-managed-key support |
| **Compatibility** | compatibility; supported harnesses; supported Connect planes |
| **Trust** | verification status; reliability information; known limitations; community feedback |

Benchmark data must always carry its **source and date** so a stale number is visibly stale
rather than silently authoritative (see [TRANSPARENCY.md](TRANSPARENCY.md)).

## Neutral sorting, not centralized personalization

Connect provides sorting, filtering, comparison, structured metadata, general beginner
presets, compatibility information, and **hooks and APIs for customer-controlled agents**.
Connect must **not** build a centralized behavioral profile in order to decide what a customer
should purchase. Connect is not a personalized recommendation service or an "AI concierge."

The intended division of labor:

```text
Connect marketplace
    provides transparent capability data

Customer-controlled agent
    knows the customer's private needs and preferences

Customer-controlled agent
    queries marketplace hooks and proposes options
```

The customer's own agent may use privately held context — preferred cost level, privacy
requirements, available hardware, organizational policy, existing subscriptions, compliance
requirements, task requirements — to propose options. That context stays customer-controlled
whenever possible; it does not flow into a central Connect profile.

### General recommendations

Connect may still offer transparent general starting points for inexperienced users. These
must be **non-personalized by default, explainable, clearly identified as general defaults,
based on published criteria, and easy to override.** They are presets, not a profile.

## Verification

Vendors may pay for a defined verification process. Verification may cover compatibility,
security properties, capability claims, permissions, integration tests, performance claims,
version tracking, and compliance-related evidence.

**Payment buys the evaluation, never the outcome.** Paying for verification does not purchase
a positive result, preferred ranking, favorable wording, or recommendation status. A
verification result must identify:

- what was tested
- the standard used
- the tested version
- the date
- the evidence
- limitations
- expiration or re-verification requirements

Free and community projects must have reasonable routes to verification — automated checks,
community verification, grants, waived fees, or sponsored reviews — so verification does not
become a pay-to-appear wall that excludes open-source listings.

Verification is separate from ranking and from sponsorship. See [TRANSPARENCY.md](TRANSPARENCY.md)
for how each is labeled.

## Compliance evidence is searchable and distinguishable

Compliance-related characteristics must be **searchable and distinguishable**, never collapsed
into one vague "compliant" badge. The marketplace defines dedicated fields per framework so a
customer can query for the specific evidence they need.

**GDPR-related fields:** processing regions; storage regions; DPA availability; subprocessor
information; retention controls; deletion support; export support; international-transfer
mechanism; customer-managed encryption; data-controller and processor roles where declared.

**SOC 2-related fields:** Type I or Type II; report period; covered services; report
availability; verification date; complementary user-entity controls; known scope exclusions.

**HIPAA-related fields:** BAA availability; covered products; PHI-capable status; encryption;
audit controls; retention behavior; access controls; scope exclusions.

The marketplace must support queries such as:

```text
Show hosting providers that:
- support EU deployment;
- offer a DPA;
- have a current SOC 2 Type II report;
- will sign a BAA;
- support customer-managed keys;
- retain no prompt content.
```

Presence of these fields is compliance **enablement**, not a claim that installing Connect or
buying a listing makes a customer compliant. See
[DATA_AND_COMPLIANCE_BOUNDARIES.md](DATA_AND_COMPLIANCE_BOUNDARIES.md).

## Revenue model

Permitted revenue sources are exactly these:

- transaction fees on independent hosting services
- transaction fees on paid model or inference usage purchased through the marketplace
- transaction fees on rented compute purchased through the marketplace
- transaction fees on paid tools
- transaction fees on memory providers
- transaction fees on storage and database services
- transaction fees on secrets-management products
- transaction fees on sandbox or remote-workspace services
- vendor verification fees
- compatibility certification fees
- marketplace integration fees paid by vendors
- referral or partner payments

**A marketplace transaction fee applies only when Connect actually facilitates a paid
marketplace transaction.** Connect never charges for customer-owned resources, for attaching
an existing account/subscription/contract, for an externally purchased service, for
self-hosting, or for free and open-source marketplace entries.

### What Connect must never charge for

- using the customer's own computer, GPU, or server
- using the customer's own local model
- connecting an existing API key, subscription, or contract
- using an externally purchased service or one under an existing organization contract
- self-hosting
- using free or open-source marketplace entries

## Payment and data minimization

Payment processors should handle payment credentials, transaction processing, and vendor
payouts wherever possible. Connect minimizes possession of financial and customer data.
Payment-card data should remain with the marketplace payment processor whenever technically
possible.

For each billing arrangement, Connect's role and fee are fixed (this is the same table as
[docs/ORGANIZATION_MODEL.md §Billing arrangements](docs/ORGANIZATION_MODEL.md#billing-arrangements)):

| Arrangement | What Connect may receive | Marketplace fee |
|---|---|---|
| **Marketplace-billed** | Authoritative transaction data, disclosed fee, payment status, vendor & customer transaction identifiers | Disclosed fee |
| **Externally billed** | Imported billing data via supported APIs, or customer-entered cost data (labeled if incomplete) | None |
| **Customer-owned** | Operational usage only; never a fictional provider charge | None |
| **Free** | Usage where useful; displayed as free | None |

## Centralized cost view, not centralized billing

Connect may provide a unified control-plane view of costs **without becoming the underlying
billing provider.** The view clearly distinguishes marketplace-billed, externally billed,
customer-owned, and free resources, and never manufactures a cost for a resource Connect does
not bill.

## See also

- [PRODUCT_THESIS.md](PRODUCT_THESIS.md) — the product this marketplace belongs to.
- [DATA_AND_COMPLIANCE_BOUNDARIES.md](DATA_AND_COMPLIANCE_BOUNDARIES.md) — what data the marketplace may and may not touch.
- [TRANSPARENCY.md](TRANSPARENCY.md) — how fees, verification, ranking, and sponsorship are disclosed.
- [docs/ORGANIZATION_MODEL.md](docs/ORGANIZATION_MODEL.md) — bring-your-own services and billing arrangements in setup.
- [MANIFESTO.md](MANIFESTO.md#what-we-will-not-build) — the refusals that bound this model.
