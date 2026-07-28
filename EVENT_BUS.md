# The Connect event bus

The canonical, cross-product **event stream** for the Connect ecosystem. It exists so the
five planes can be observed, replayed, and debugged as one system without coupling them
through direct point-to-point calls.

This document is the **contract**. AgentConnect hosts the reference implementation (its
`event_log` + HTTP surface, see `mcp-agentconnect/docs/EVENT_BUS.md`); ToolConnect and
ComputeConnect publish into it; BrainConnect's publisher is reserved but not yet wired
(see [Status](#status)). Product repos should link here rather than restate the contract.

---

## The one load-bearing rule

**The bus is a projection, never a system of record.**

Every product keeps its own authoritative store — AgentConnect's ledger, BrainConnect's
trusted memory ledger, ToolConnect's hash-chained audit chain, ComputeConnect's run
journal. The bus is a *downstream copy* of selected facts, for observability, analytics,
and debugging. Nothing reads the bus to make an authorization, trust, placement, or work
decision. Two consequences the whole design depends on:

1. **Publishers emit best-effort and never block.** If the bus is unconfigured, unreachable,
   slow, or erroring, the publishing product behaves *exactly* as it would with no bus at
   all. A tool decision, a memory promotion, a generation — none of them wait on, or fail
   because of, the bus. This is what keeps the bus from becoming the central dependency the
   ecosystem was built to avoid.
2. **The bus is lossy-tolerant by contract.** A consumer must treat it as a stream that can
   have gaps under failure, not as the truth. For truth, ask the owning product. The bus's
   monotonic `seq` lets a consumer detect its own gaps and re-poll; it does not promise that
   every fact that ever happened was successfully published.

If you ever find yourself wanting the bus to be authoritative, that is a signal the fact
belongs in a product's own contract, not here.

## The envelope

```json
{
  "seq": 42,
  "event_id": "event_ab12cd34ef56",
  "ts": 1785165727.15,
  "type": "tool.authorized",
  "source_product": "toolconnect",
  "outcome": "denied",
  "actor": "connect-smoke",
  "task_id": "task_...",
  "subtask_id": null,
  "run_id": null,
  "privacy_tier": "local_only",
  "entity_id": null,
  "payload": { "decision_id": "...", "args_hash": "sha256:...", "reason": "..." }
}
```

- **`seq`** — strictly monotonic, assigned by the store. A consumer resumes with
  `?since=<last_seq>`. `seq` is `null` in a publish *response* only when an idempotent
  `event_id` replay matched an existing row.
- **`source_product`** — `agentconnect | brainconnect | toolconnect | computeconnect`. The
  authority for which product emitted the event; see [anti-forgery](#authorization--anti-forgery).
- **`type`** — a value from the [vocabulary](#vocabulary).
- **`privacy_tier`** — the content-sensitivity tier the payload was redacted against. Drives
  fail-closed re-redaction at ingest.
- **`payload`** — a small object of ids, hashes, names, decisions, reasons, and counts.
  **Never** raw tool arguments, prompts, model output, secrets, or artifact content.

## Vocabulary

Namespaced by plane. The store reuses one flat event-type space; the prefixes are a naming
convention, and `source_product` is the authoritative producer tag.

| Plane | Product | Types |
|---|---|---|
| Work | AgentConnect | `task.created`, `task.claimed`, `task.completed`, `task.failed`, `task.cancelled`, `subtask.completed`, `subtask.failed`, `state.changed` |
| Capability | ToolConnect | `tool.authorized` (allow = no `outcome`; deny = `outcome:"denied"`), `tool.executed`, `grant.issued`, `grant.redeemed` |
| Compute | ComputeConnect | `provider.offline`, `provider.degraded`, `provider.recovered`, `compute.generation.placed`, `compute.generation.refused` |
| Knowledge | BrainConnect | `memory.captured`, `memory.promoted`, `memory.rejected` — **reserved, publisher not yet wired** |

An allow and a deny share `tool.authorized`, distinguished by the presence of `outcome` —
so a consumer counting denials filters on `outcome == "denied"`, and the two are never
separate wire ids.

## Transport

- **Publish** — `POST {bus}/events`, `Authorization: Bearer <publish-token>`. Body is the
  envelope minus `seq` (`type` and `source_product` required; the store assigns `seq`,
  `event_id`, `ts` when absent). Returns `{seq, event_id}`. Optional caller-supplied
  `event_id` makes a retry idempotent.
- **Consume** — `GET {bus}/events?since=<seq>&type=<t>&source_product=<p>&limit=<n>` for
  replay/poll, and `GET {bus}/events/stream` (SSE, `Last-Event-ID`) for a live tail. Both
  filters are repeatable/CSV and additive — an existing consumer that passes neither sees
  everything. Consumption uses the host's operator auth.

## Authorization & anti-forgery

A publish token is scoped to **exactly one** `source_product`, minted by an operator:

```
agentconnect tokens publish --source-product toolconnect
```

A `toolconnect`-scoped token can only create `toolconnect` events — a mismatched
`source_product` is a hard `403`, and the stored row is stamped from the *authenticated
token*, never from the body's claim. So a compromised or buggy ComputeConnect can never
forge a ToolConnect audit event onto the stream. This is the property that lets a security
reviewer trust `source_product` on a `tool.denied`.

## Privacy

Publishers **pre-redact** — they put only ids/hashes/names/reasons/counts on the wire, and
set `privacy_tier` from the domain object. The store does **not** trust that: it
**re-redacts every ingested event fail-closed** against its declared tier before the event
is ever readable. `secret_sensitive` drops the payload to a marker; an unknown or missing
tier is treated as most-restrictive. Redaction is recursive — nested credential-shaped keys
are masked at any depth. Raw sensitive content cannot reach a reader even from a hostile
publisher.

## Why a bus (and why not more)

The reviewer's case for the bus: looser coupling, replay, observability, analytics, and
debugging, without any product losing ownership — AgentConnect still owns work, BrainConnect
trust, ToolConnect permissions, ComputeConnect placement. The bus changes the *communication
model*, not the authority model. It is deliberately **not** a message queue, not a workflow
engine, and not a delivery-guaranteed log: it is a best-effort observability stream over the
one store AgentConnect already keeps.

## Status

| Publisher | State |
|---|---|
| AgentConnect (host + Work plane) | Shipped — ingress + native `work.*`/`state.changed` emission |
| ToolConnect (Capability plane) | Shipped — best-effort `tool.*` / `grant.*` |
| ComputeConnect (Compute plane) | Shipped — best-effort `provider.*` / `compute.generation.*` |
| BrainConnect (Knowledge plane) | **Reserved** — `knowledge.*` names fixed; publisher deliberately not wired yet |

Wiring the BrainConnect publisher is a one-module follow-up against this contract: emit
`memory.captured` / `memory.promoted` / `memory.rejected` best-effort at its ledger write
points, behind a `--source-product brainconnect` token. It is held only pending a product
decision, not a technical one.
