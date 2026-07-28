# Agent-led setup

**A customer must also be able to use an existing trusted agent to set Connect up — and that
agent must operate under the same zero-trust discipline as the rest of the ecosystem.**

> **Status: design direction, not shipped behavior.** No agent-led setup flow ships in any
> `0.1.0` product today, and the control-plane application that would host it is not yet built
> (see [ADR 0002](adr/0002-control-plane-repository-boundary.md)). This document specifies the
> flow the product is built toward. Per [MANIFESTO §8](../MANIFESTO.md), an unbuilt capability
> is named as unbuilt.

---

## Principle: the agent proposes; deterministic code and humans decide

Agent-led setup mirrors the ecosystem's spine — *the model/agent proposes; deterministic code
and humans decide* (the same rule that governs [BrainConnect](https://github.com/Judgernaut777/BrainConnect)
memory promotion and [ToolConnect](https://github.com/Judgernaut777/ToolConnect) authorization).
The setup agent may inspect, compare, and propose; it may not silently apply.

## What the setup agent may do

With scoped permission, a trusted, customer-controlled setup agent may:

- inspect authorized local configuration
- detect installed harnesses
- identify existing subscriptions
- identify customer-owned compute
- query marketplace metadata
- read preferences from customer-controlled memory
- compare providers
- propose a workspace architecture
- propose organization structures
- propose budgets
- propose security policy
- propose compliance filters
- install selected components
- configure adapters
- validate the completed environment

## The zero-trust flow

Setup stays zero trust. The sequence is fixed, and privileges are temporary:

```text
Inspect with scoped permission
→ Propose
→ Explain changes and tradeoffs
→ Receive approval
→ Apply with temporary grants
→ Validate
→ Revoke setup privileges
```

Scoped inspection, then a proposal a human can read, then approval, then application under
*temporary* grants that are revoked when setup finishes. Nothing about this flow leaves the
agent holding standing privileges.

## What the setup agent must never do silently

The setup agent must **not** silently:

- transfer ownership of any resource
- reveal personal resources
- purchase marketplace services
- change organization-wide policy
- merge memory stores
- install privileged software
- expose credentials

Each of these requires explicit, scoped human approval — surfaced in a preview, not performed
as a side effect. This is the same boundary the human-guided flow enforces; the agent does not
get a shortcut around it.

## Scaling with organization size

- For an **individual**, the agent might inspect the local machine, identify available models
  and harnesses, and propose a personal workspace.
- For a **small team**, it might propose user roles, shared workspaces, team budgets, approved
  tools, and memory boundaries.
- For a **large organization**, an authorized setup agent might read customer-provided
  organizational configuration, inspect existing identity groups, query marketplace metadata,
  propose department structures, generate policy templates, propose delegated budgets, identify
  compliance requirements, compare hosting providers, identify incompatible services, and
  produce a complete deployment plan — always presented for scoped approval, never applied
  organization-wide on its own.

The migration and org-integration side of agent-led setup — integrating existing users or
departments into a larger organization — is specified in
[ORGANIZATION_MODEL.md §Agent-led organizational setup](ORGANIZATION_MODEL.md#agent-led-organizational-setup),
under the same must-not-silently constraints.

## See also

- [SETUP_HUMAN_GUIDED.md](SETUP_HUMAN_GUIDED.md) — the visual alternative.
- [ORGANIZATION_MODEL.md](ORGANIZATION_MODEL.md) — org-aware setup, ownership, and adoption.
- [../PRODUCT_THESIS.md](../PRODUCT_THESIS.md) — the product this flow belongs to.
- [../MANIFESTO.md](../MANIFESTO.md) — the propose-not-decide spine.
