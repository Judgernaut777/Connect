# Organization-aware onboarding

**The same Connect control plane scales from one person to a complex company. It does this by
adding *structure*, never by switching *products*.**

> **Status: design direction, not shipped behavior.** This document states the product model
> Connect is being built toward. Onboarding profiles, organizational import, ownership metadata,
> and the import/attach/transfer/federate operations described below are **not implemented in any
> `0.1.0` product today** — none of the four planes ships an onboarding wizard, an org directory,
> or a resource-ownership field. Read this as the target the planes are converging on and the
> contract the design must honor, not as a claim about current runtime. Per
> [MANIFESTO §8](../MANIFESTO.md), where a capability is not built, it is named as not built.
> When a piece of this lands in a plane, that plane's own docs say so in its own voice.

---

## The one decision this document makes

Organizational scale is **onboarding, not edition.** Connect does not sell an "individual
edition" and an "enterprise edition." It ships one control plane and meets each customer with a
setup experience sized to them. A person configuring Connect for personal coding and a company
with many departments are configuring **the same primitives** — they just see a different amount
of that surface at first.

The rejected alternative — and the thing this decision exists to forbid — is organizational scale
sitting behind a paywall: separate paid tiers, restricted editions, per-seat licensing, or a
"real" product a growing customer must migrate onto. Connect will not build that. See the
[MANIFESTO](../MANIFESTO.md#what-we-will-not-build) entry.

Two consequences follow, and both are load-bearing:

1. **Growth never requires migration.** A customer adds structure in place. Going from one user to
   a department to a multi-region company does not mean a new deployment, a new SKU, an export into
   a proprietary enterprise product, or handing Connect custody of organizational data.
2. **Smaller users lose nothing.** No capability is withheld from an individual to reserve it for a
   larger buyer. The individual experience is *simpler*, not *lesser* — advanced controls exist but
   stay out of the way until asked for (progressive disclosure).

---

## Where this lives: the management plane

Onboarding, the organizational model, and resource ownership are **Connect-plane** concerns —
this repository, the [Platform Management Plane](../README.md#five-planes-one-platform). Connect
holds the org model and the onboarding flow; it does **not** run workloads, hold trust, decide
authorization, or place compute. Each infrastructure plane owns the resources setup configures and
enforces the boundaries setup declares:

| Plane | Product | What org-aware setup configures here | Plane's own doc |
|---|---|---|---|
| **Work** | AgentConnect | Users, agents, workspaces, projects, scoped tokens, workspace templates, delegated workspace administration, task/audit ownership and history | [`docs/ORGANIZATION_AWARE_SETUP.md`](https://github.com/Judgernaut777/AgentConnect/blob/main/docs/ORGANIZATION_AWARE_SETUP.md) |
| **Knowledge** | BrainConnect | Personal / shared-project / team / department memory boundaries expressed as scopes; which memory stores may (and may not) merge on migration | [`docs/ORGANIZATION_AWARE_SETUP.md`](https://github.com/Judgernaut777/BrainConnect/blob/main/docs/ORGANIZATION_AWARE_SETUP.md) |
| **Capability** | ToolConnect | Approved and prohibited tools and models, internal/external tool registries, restricted marketplace catalogs, policy bindings scoped to org units | [`docs/ORGANIZATION_AWARE_SETUP.md`](https://github.com/Judgernaut777/ToolConnect/blob/main/docs/ORGANIZATION_AWARE_SETUP.md) |
| **Compute** | ComputeConnect | Shared and personal compute, hosting relationships, ownership-vs-authorized-use of nodes, regional and data-residency placement | [`docs/ORGANIZATION_AWARE_SETUP.md`](https://github.com/Judgernaut777/ComputeConnect/blob/main/docs/ORGANIZATION_AWARE_SETUP.md) |

The management plane stays thin here too: it proposes and records the org model; the planes enforce
it. Connect never becomes a fifth opinion competing with the four for control, and it never becomes
the place a customer's employee directory is permanently stored (see
[Importing an existing organization](#importing-an-existing-organization)).

---

## Onboarding profiles

Profiles are **presets that configure the same primitives with an appropriate amount of
structure.** They are not tiers, restricted editions, or subscription levels. A customer may start
with any profile and add complexity later without changing products. Everything a smaller profile
can do, a larger one can too.

### Individual

One person using Connect for personal work — coding, research, automation. Setup may include one
user; one or more local workspaces; selected harnesses; local or external models; a personal memory
provider; a secrets manager; basic sandbox settings; personal budgets; optional marketplace
providers. The interface **avoids introducing departments, roles, approval chains, and
organizational policies** unless the user chooses to add them.

### Household or small collaborative group

A few trusted people sharing selected workspaces or resources. Adds multiple users; shared and
private workspaces; simple `owner`/`member` roles; shared compute; shared marketplace purchases;
individual and group budgets; separate personal memory alongside shared project memory; basic
approval controls.

### Small team or business

A company that needs coordination without a complex administrative structure. Adds an organization;
one or more teams; `administrator`/`manager`/`member` roles; shared provider accounts; delegated
team budgets; workspace templates; approved tools and models; basic identity-provider integration;
audit visibility; team-level memory boundaries; default security and sandbox policies. **A small
organization should complete setup without a dedicated IT or compliance department.**

### Growing or mid-sized organization

Several teams, projects, and managers. Adds departments and teams; nested budget allocations;
role-based administration; centralized policy with team-level flexibility; shared and restricted
marketplace catalogs; identity-provider synchronization; approval and exception workflows; regional
or data-sensitivity rules; department-specific memory and tool access; cost and usage dashboards;
delegated workspace administration; reusable environment templates. The organization defines broad
boundaries while each team selects the models, tools, hosting, and compute that fit within them.

### Large organization

Many departments, business units, regions, and internal policies. Adds a hierarchical structure
(business units, divisions, departments, teams, projects); multiple administrators with scoped
authority; identity and group synchronization; inherited and overridden policies; departmental
budgets and sub-budgets; geographic and data-residency requirements; approved and prohibited
marketplace providers; separate compliance profiles; internal and external tool registries;
multiple secrets-management systems; multiple hosting and compute environments; cross-department
reporting; audit and evidence collection; exception and escalation paths; controlled delegation to
local administrators.

**A large organization is not forced into one rigid hierarchy.** Connect supports multiple
organizational dimensions through groups, tags, scopes, and policy bindings. A single user may
simultaneously belong to the engineering department, a security-review group, a temporary product
project, an EU data-handling group, and a specific budget allocation.

---

## Custom structure

Organizations may skip the presets and compose their own structure from primitives:

```text
organizations · organizational units · groups · roles · users · agents ·
projects · workspaces · policies · budgets · providers · tags · scopes
```

These combine freely. No customer is forced into a predefined corporate model to use Connect.

---

## Progressive setup

Setup uses progressive disclosure. An individual sees a short flow with only the decisions needed to
create a safe workspace. A large organization receives additional stages — organizational import,
identity integration, administrator delegation, policy inheritance, budget allocation, marketplace
restrictions, compliance requirements, regional deployment, audit configuration. **Advanced controls
exist without making the individual experience intimidating.**

The scaling path, with no product change at any arrow:

```text
Individual → Collaborative group → Team → Organization →
Multiple departments → Multiple regions or business units
```

Growth must never require purchasing a different edition, replacing the deployment, exporting into a
proprietary enterprise product, paying per-user licensing, or giving Connect custody of
organizational data.

---

## Policy inheritance

Structure implies a policy gradient. Each level may **narrow** permissions or provide **explicitly
allowed overrides**, according to organization policy:

```text
Company baseline policy → Department policy → Team policy → Workspace policy
```

Policy binding is a Connect-plane concept; enforcement lives in the planes (ToolConnect for tool and
model authorization, ComputeConnect for placement and residency, AgentConnect for workspace and
review controls, BrainConnect for memory scope). A parent may apply broader policy while letting
department-specific settings remain wherever they do not conflict.

---

## Organizational templates

Optional starting points that reduce setup time — never locked configurations. Examples: individual
developer; independent researcher; small software team; healthcare organization; financial-services
organization; educational institution; distributed company; regulated enterprise; multi-department
research organization. Each supplies understandable defaults for roles, policies, sandboxing, memory
boundaries, budgets, marketplace filters, and compliance-related controls. A template is a place to
start, not a place to stay.

---

## Bring-your-own services

**Bring what you already have. Replace or consolidate it only when doing so benefits you.**

Customers are never forced to repurchase, through the Connect marketplace, a service they already
own — a Claude/ChatGPT/other subscription, provider API accounts, enterprise model contracts,
rented compute, cloud credits, hosted dev environments, memory services, databases, secrets
managers, paid tools, existing MCP servers, internal integrations. The marketplace is **an available
procurement path, not a requirement.**

Every marketplace category in onboarding should offer: use an existing account; connect an existing
subscription; use an organization-provided service; enter existing provider credentials; configure a
custom endpoint; import an existing contract; or choose from the marketplace. For example:

```text
Claude
  ○ Connect my existing account
  ○ Use my organization's account
  ○ Choose a marketplace provider
  ○ Configure a custom compatible endpoint

Workspace hosting
  ○ Use this computer
  ○ Connect an existing server
  ○ Connect an existing hosting account
  ○ Choose a marketplace hosting provider
  ○ Configure a custom environment

Secrets manager
  ○ Use the local default
  ○ Connect my existing secrets manager
  ○ Use my organization's provider
  ○ Choose another marketplace option
  ○ Add a custom compatible provider
```

### Existing subscriptions and consumer accounts

Some harnesses use consumer or seat-based subscriptions rather than usage APIs. Where technically and
contractually supported, Connect helps users detect an existing installation, confirm the user is
already authenticated, launch the native harness inside a Connect workspace, associate it with a
workspace, apply local workspace controls around it, display it as an externally billed resource, and
track locally observable usage — **without** claiming authoritative provider billing.

Connect never asks for account passwords and never bypasses provider authentication. Authentication
stays with the provider's official app, CLI login, OAuth, or device-authorization flow. When a
subscription cannot expose detailed usage or billing, Connect labels it plainly:

```text
Billing source:       External subscription
Billing visibility:   Limited
Connect marketplace fee: None
```

### Existing commercial contracts

Organizations may register negotiated vendor agreements as customer-controlled provider
relationships. A contract record carries only the operational metadata the control plane needs
(provider identity; covered products; internal account/contract reference; applicable departments;
approved regions; customer-supplied pricing metadata; rate limits; usage commitments; renewal date;
data-processing terms; BAA availability; SOC 2 status; approved data classifications; authentication
method; billing ownership). **Sensitive contract documents remain in customer-controlled storage;
Connect references them without copying them into a central service.** Such resources appear
alongside marketplace options, clearly labeled:

```text
Acme Corporation contract
  Organization provided · Externally billed
  Approved for confidential data · Available to Engineering and Research
```

---

## Billing arrangements

Connect distinguishes several payment models and never fabricates cost:

| Arrangement | Connect's role | Marketplace fee |
|---|---|---|
| **Customer-owned billing** | Facilitates config, gives visibility where available, applies budgets/policies | None |
| **Marketplace billing** | Facilitates the transaction, imports authoritative transaction data | Disclosed fee |
| **Free / local resource** | Tracks operational use when useful; never assigns a fictional cost; never charges for customer-owned compute | None |
| **Unknown / partially visible** | Labels the limitation; permits optional customer-entered *estimates*, never presented as authoritative charges | None |

Consolidation is **gradual and voluntary.** A customer may run a Claude subscription externally
billed, an OpenAI API externally billed, local compute free/customer-owned, and a hosted workspace
marketplace-billed — all at once — and move resources into marketplace billing later only for the
convenience it buys (simpler billing, unified records, easier reconciliation, centralized vendor
management, automated provisioning, clearer allocation). **Connect earns that transition by making
the marketplace more convenient, never by degrading externally purchased services.**

---

## Bottom-up organizational adoption

Adoption commonly begins small and expands:

```text
Individual experiment → Team trial → Department adoption → Organization-wide standard
```

Existing work is preserved throughout. Users should never have to recreate workspaces, projects,
harness configurations, memory connections, tools, provider accounts, marketplace purchases,
policies, task history, or budget history. An existing personal or team deployment joins an
organization through a controlled transfer or association — never silently.

### Joining an organization

When an organization adopts Connect, existing users or teams accept an invitation to associate their
installation or identity. The flow distinguishes personal, organization-owned, shared, and
stays-separate resources, and shows a clear preview before anything moves:

```text
Your company has invited you to join Acme Connect.

  Personal workspace          → Keep personal
  BrainConnect Refactor       → Transfer to Engineering
  Existing Claude subscription → Continue using personally
  Company OpenAI contract     → Add to organization workspaces
  Local computer              → Allow for approved company tasks
```

The user and organization both see, before approval: ownership changes; administrative visibility;
applicable policies; budget changes; memory boundaries; provider access; audit behavior; and what
remains private. **Nothing is transferred silently.**

### Department-to-organization promotion

A department may already run its own Connect organization before the company adopts Connect broadly.
The larger organization imports or federates it **without rebuilding** — preserving department users
and groups, workspaces, delegated budgets, approved providers, marketplace purchases, local policies,
task and audit references, department memory boundaries, tool assertions, and hosting relationships.
The parent then applies broader policy while non-conflicting department settings remain (see
[Policy inheritance](#policy-inheritance)).

### Import, attach, transfer, or federate

Not every pre-existing deployment is absorbed the same way:

- **Import** — move selected configuration and resources into the organization-controlled
  deployment.
- **Attach** — keep the existing deployment but associate it with the organization for identity,
  policy, budgeting, or visibility.
- **Transfer** — change ownership of selected workspaces or marketplace resources from an individual
  or team to the organization.
- **Federate** — let an independently operated department or subsidiary participate while retaining
  operational control.

These matter for subsidiaries, contractors, research groups, acquisitions, international divisions,
regulated departments, and independently managed teams.

---

## Identity, ownership, and reversibility

### Identity reconciliation

When existing users join an organization, Connect reconciles identities **without assuming that
matching email addresses prove ownership.** Reconciliation may use organization invitations, verified
domain ownership, identity-provider authentication, administrator confirmation, user confirmation,
signed deployment invitations, or existing marketplace-account ownership. Duplicate identities are
**surfaced for review, never merged automatically.** Stable internal identities are preserved so
historical task, audit, budget, and marketplace records stay attributable after migration.

### Resource ownership

Every significant resource carries clear ownership metadata. **Owner** may be an individual, team,
department, organization, external provider, or shared group. Resources include workspaces, provider
connections, marketplace purchases, budgets, credentials, memory stores, hosting accounts, tool
registries, and compute nodes.

**Joining an organization does not automatically make every personal resource organization-owned.
Ownership and authorized use are distinct.** A personal machine can be *usable* for approved company
tasks while remaining individually *owned*, with organization visibility limited to availability and
approved usage — and no access to personal files:

```text
Resource:                          Personal workstation
Owner:                             Individual
Authorized use:                    Selected Engineering tasks
Organization visibility:           Availability and approved usage only
Organization access to personal files: None
```

### Migration preview and rollback

Before incorporating an individual or department, Connect generates a **migration preview**
identifying: resources being transferred; resources remaining personal; conflicting identities;
conflicting policies; duplicated provider accounts; overlapping marketplace purchases; budget
changes; incompatible compliance requirements; credentials requiring replacement; memory stores that
cannot be merged safely; and changes to administrative visibility. The customer approves the plan **in
sections**, and the operation is **reversible until a clearly identified finalization point.**

---

## Agent-led organizational setup

The agent-led option scales with organizational size. For an individual, an agent might inspect the
local computer, identify available models and harnesses, and propose a personal workspace. For a
small team, it might propose user roles, shared workspaces, team budgets, approved tools, and memory
boundaries. For a large organization, an authorized setup agent might read customer-provided
organizational configuration, inspect existing identity groups, query marketplace metadata, propose
department structures, generate policy templates, propose delegated budgets, identify compliance
requirements, compare hosting providers, identify incompatible services, and produce a complete
deployment plan.

**The agent never silently applies organization-wide changes.** The process is fixed:

```text
Inspect authorized configuration
→ Generate proposed organization model
→ Explain policies, budgets, and provider choices
→ Identify risks and unresolved decisions
→ Receive scoped human approval
→ Apply approved changes
→ Run validation checks
→ Revoke temporary setup privileges
```

A trusted customer-controlled agent may also help integrate existing users or departments into a
larger organization: inventory existing Connect resources, detect duplicate providers, identify
externally billed contracts, compare policies, propose workspace ownership, identify personal
resources, recommend budget mappings, propose organizational groups, flag compliance conflicts, and
create a migration plan. It **operates on customer-controlled data**, presents changes for approval,
and **must not** silently transfer ownership, expose personal resources, merge memory stores, or
replace billing relationships.

This mirrors the ecosystem's spine — *the model/agent proposes; deterministic code and humans
decide.* The setup agent proposes an org model; humans approve it in scope; the planes apply and
enforce it.

---

## Importing an existing organization

Larger customers should not recreate their organization by hand. Connect supports importing or
synchronizing organizational information from **customer-controlled** sources: identity providers,
directory services, HR systems, structured configuration files, existing team-management platforms,
and organization APIs. The customer is shown a **proposed organizational structure before it is
applied.**

**Connect must not require the central marketplace service to permanently store the customer's
employee directory.** Synchronization and policy evaluation happen **within the customer-controlled
Connect deployment** wherever possible. This keeps the management plane thin and keeps organizational
data in the customer's custody — the same discipline the rest of the ecosystem applies to trust,
authorization, and compute.

---

## Adoption principle

Connect meets customers where they already are. Individuals bring existing subscriptions; teams
bring existing workspaces; departments retain successful trials; organizations adopt Connect without
erasing the systems, contracts, and practices that led them to adopt it. Marketplace consolidation
happens because it is simpler and more valuable — **not because Connect forces customers to abandon
resources they already own.**

---

## See also

- [MANIFESTO.md](../MANIFESTO.md) — the engineering philosophy, including *what we will not build*.
- [README.md](../README.md#five-planes-one-platform) — the five-planes framing this model sits on.
- [ARCHITECTURE.md](../ARCHITECTURE.md) — how the planes interact through explicit contracts.
- Each plane's `docs/ORGANIZATION_AWARE_SETUP.md` — how that plane participates in org-aware setup
  and resource ownership (linked in the table [above](#where-this-lives-the-management-plane)).
