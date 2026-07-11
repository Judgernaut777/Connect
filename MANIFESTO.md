# Manifesto

The engineering philosophy of the Connect ecosystem. These are not aspirations. Each
principle below is followed by how it is actually enforced in the code today — and, where
it is not yet enforced, that is said plainly.

---

## 1. Standalone first

Every product must be useful alone, installable alone, and comprehensible alone. A user
who wants only a memory ledger should never be made to stand up a control plane to get
one.

The ecosystem is a set of products that happen to compose, not a distributed system that
has been chopped into repositories. If a product cannot justify its existence without its
siblings, it is a module, and it belongs inside one of them.

**In practice:** all four products run standalone at `0.1.0`. AgentConnect runs with no memory
layer configured; BrainConnect runs with no control plane; ComputeConnect serves a model with no
consumer attached; ToolConnect answers authorization decisions with no agent registered. No
product's README asks you to install another to complete a first task.

## 2. Modular architecture

Install what you use. Nothing more should be pulled into your environment because
something else in the family needed it.

**In practice:** AgentConnect ships as nine installable packages — core, cli, router,
runtime, model-manager, api, mcp, linear, temporal, all at a unified `0.1.0`. Core alone gives
you the library, not the command; the CLI is a separate install. BrainConnect separates the
deterministic `brainconnect` command from the model-bearing `brainconnect-librarian` into two
console scripts and two processes, precisely so that installing memory does not install an
inference dependency.

## 3. Adapters over forks

When we need to talk to something, we define the narrowest interface that expresses the
need, and we implement it against the thing. We do not fork the thing, and we do not
absorb it.

An adapter is a statement about what we require. A fork is a statement that we now own
someone else's maintenance burden. The second is almost never what we meant.

**In practice:** `agentconnect.core` declares `LocalComputeProvider` as an abstract base
and `HttpLocalComputeProvider` as one implementation — AgentConnect defines the contract
for local inference and deliberately does not own the engine. Memory is reached through a
pluggable `MemoryAdapter`, of which the BrainConnect adapter is one. BrainConnect in turn
exposes a pluggable retrieval backend, so a vector store or graph index can be swapped in
underneath it. The MCP server is a thin adapter over the router service, not the router
itself.

## 4. Use maintained third-party software

We do not rewrite what is already maintained, tested, and better than what we would
produce. Reimplementation is a cost we pay forever, in exchange for a dependency we
removed once.

The corollary: we integrate third-party software *at its own boundary*, as an optional
engine behind an interface we control. We take its capability; we do not take its
opinions about our data model.

**In practice:** the MCP servers use `FastMCP` from the official Model Context Protocol SDK
rather than a hand-rolled protocol implementation. ComputeConnect routes to a maintained
llama.cpp engine and never loads a tensor itself. ToolConnect uses Cedar as its policy engine
rather than inventing an authorization language. BrainConnect's built-in secret and injection
scanners are deliberately limited pure-stdlib rulesets; established detectors plug in as optional
engines behind that seam. We own the *domain policy*; we rent the *commodity runtime*. Policy
stays ours. Detection, transport, and inference are theirs.

## 5. Lightweight defaults

The default configuration is the conservative one. Expensive, clever, or surprising
behaviour is opt-in, and the person opting in should have to say so out loud.

**In practice:** BrainConnect's `recall` returns promoted claims only — no pending, no
superseded, eight items. Pending material comes back only when explicitly requested, and
is labelled `trusted: false`. The `brainconnect` command makes zero model calls by
construction, not by configuration. The librarian speaks the OpenAI-compatible chat API over
stdlib HTTP and therefore has **no required dependency** at all. ComputeConnect's `/generate`
treats an absent privacy tier as the *most restrictive* one — the conservative default is the
one you get when you say nothing.

## 6. Optional advanced integrations

Sophistication is available and never assumed. Every heavyweight integration —
durable workflow engines, issue trackers, vector retrieval, model endpoints — sits behind
a flag, an adapter, or a separate package.

Graceful degradation is the rule: no memory layer means stateless operation, not a crash.
An optional integration that can take the system down when absent was never optional.

**In practice:** Temporal, Linear, and the model manager are separate AgentConnect
packages you may simply not install. Memory capture is optional and must never be fatal.

## 7. Explicit boundaries

We say what a thing is *not*. A boundary that is only implied will be crossed, and the
crossing will be discovered in production by someone who trusted us.

The three boundaries that matter most today:

- **AgentConnect is a compliance and control layer, not a security sandbox.** It records
  what a cooperative agent did. It does not contain a hostile one.
- **`trusted` is authority; it is not safety.** Promotion decides whether a claim speaks
  for the ledger. It says nothing about whether the text carries an API key.
- **Safety subtracts; it never vouches.** No safety engine and no safety policy may ever
  set `trusted`. A scanner can withhold, mask, or flag. It can never bless.

Each boundary is load-bearing. `status: "promoted"` is *not* the authority signal —
`trusted: true` is, and a promoted claim sitting in an open contradiction comes back
promoted *and* untrusted. Consumers that infer trust from status are wrong, and the
ecosystem will not quietly accommodate them.

## 8. Honest documentation

Documentation states what is true now, not what is intended. A passing test suite is
described by what it actually exercises. A missing feature is named as missing, in the
place a reader would look for it.

Three examples, all currently stated in the products' own docs and in
[COMPATIBILITY.md](COMPATIBILITY.md#known-gaps):

- ComputeConnect: the runtime is real, but on this single-node host the *second* provider is
  **simulated**. So the product is called an MVP whose heterogeneity is unproven — not a
  finished compute fabric. A tested privacy filter is not the same as demonstrated placement
  across real hardware.
- Publishing: the PyPI name `brainconnect` is **taken** by an unrelated package. That is
  written down as a release blocker, not omitted because it is inconvenient — a combined
  install must use the wheel path, and we say so where a reader would go to install.
- Safety scanning: an engine that could not run is never mistaken for one that found nothing.

This document is held to the same rule. Where a principle above is aspirational rather
than enforced, it says so. Where the ecosystem currently falls short — see
[COMPATIBILITY.md](COMPATIBILITY.md#known-gaps) for the standing list — the shortfall is
written down rather than smoothed over.

---

## What we will not build

- A monorepo. The products keep their own names, repositories, and release cadence.
- A god object that all four products import. Shared surface is contract, not code.
- A security sandbox marketed as one without the isolation to back it.
- A memory system in which an agent can decide what is true.
