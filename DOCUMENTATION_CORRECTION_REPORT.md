# Documentation correction report

**This is the permanent audit trail for the Connect ecosystem documentation-correction effort.
It records what changed, which contradictions were removed, what remains intentionally
deferred, and that no implementation was begun.** It exists so a future contributor can see
*why* the documentation reads the way it does.

The effort ran in two passes across the five repositories (Connect, AgentConnect, BrainConnect,
ToolConnect, ComputeConnect):

1. **Primary correction** — established the target product thesis, marketplace, data/compliance
   boundaries, transparency, generalized budget model, pluggable-enforcement workspace
   isolation, and the repository-boundary ADR; corrected contradictory current documentation.
2. **Final editorial cleanup** — rebuilt the documentation index, strengthened the manifesto
   into a definitive refusal, reframed the README opening as *current + target*, aligned the
   AgentConnect STATUS wording with the workspace-isolation architecture, verified cross-links
   and terminology, and produced this report.

The goal was not to add documentation but to make it the **single authoritative specification**
for implementation: one reasonable interpretation of the architecture, business model, privacy
model, marketplace model, and product direction.

---

## Files created

**Connect**
- `PRODUCT_THESIS.md` — canonical product statement (*Making Agents Usable*).
- `MARKETPLACE_ARCHITECTURE.md` — marketplace and the entire permitted business model.
- `DATA_AND_COMPLIANCE_BOUNDARIES.md` — component-level data matrix; enablement vs automatic compliance.
- `TRANSPARENCY.md` — storage, fees, ranking, sponsorship, benchmarks, telemetry commitments.
- `docs/SETUP_HUMAN_GUIDED.md` — the 15-stage visual setup flow.
- `docs/SETUP_AGENT_LED.md` — the zero-trust agent-led setup flow.
- `docs/adr/0002-control-plane-repository-boundary.md` — the control-plane repository ADR (Proposed).
- `DOCUMENTATION_CORRECTION_REPORT.md` — this report.

**AgentConnect**
- `docs/BUDGET_MODEL.md` — the generalized budget model.
- `docs/WORKSPACE_ISOLATION.md` — pluggable-enforcement workspace isolation (Levels 0–3).
- `docs/SETUP_INTEGRATION.md` — how the control plane configures the Work plane during setup.
- `docs/README.md` — the AgentConnect docs index.

**BrainConnect**
- `docs/KNOWLEDGE_PLANE.md` — the Knowledge plane's consolidated ecosystem responsibilities.

**ToolConnect**
- `docs/CAPABILITY_PLANE.md` — the Capability plane, incl. the decision/enforcement/reported/observed distinction.

**ComputeConnect**
- `docs/COMPUTE_PLANE.md` — the owned/rented/external/marketplace compute taxonomy.

## Files modified

**Connect** — `README.md` (current + target opening; documentation-index pointer), `MANIFESTO.md`
(the *will never become* / *will never degrade* enumerations; earned-not-forced; ComputeConnect
status fix), `docs/README.md` (rebuilt sectioned documentation index), `GETTING_STARTED.md` and
`CONTRIBUTING.md` (ComputeConnect heterogeneity status), `ARCHITECTURE.md` (ToolConnect-client
contradiction).

**AgentConnect** — `README.md`, `docs/STATUS.md`, `docs/ORGANIZATION_AWARE_SETUP.md` (isolation
reframed to pluggable enforcement; STATUS now leads with current-vs-target and points to
`WORKSPACE_ISOLATION.md`).

**BrainConnect** — `README.md` (index link; "Obsidian brainconnect" → "wiki" typo).

**ToolConnect** — `README.md`, `docs/STATUS.md`, `docs/ARCHITECTURE.md` (retired stale
"Design phase — no runtime" / "no contract exists" claims).

**ComputeConnect** — `README.md` (index link; inference-proxy clarification).

## Files archived

None moved to a `docs/history/` directory. The ecosystem convention (per
[CONTRIBUTING.md](CONTRIBUTING.md)) is to correct obsolete claims **in place** or mark them
historical where a reader would look — sibling `ARCHITECTURE.md` / `STATUS.md` carry in-place
*superseded / historical* markers. This report is the audit trail that a separate archive
folder would otherwise provide. The retirement of Fascia-AI-OS is noted in
[README.md](README.md#history).

## Contradictions removed

| Area | Was | Now |
|---|---|---|
| **Product identity** | Connect presented only as a docs/integration umbrella (the complete story) | Current umbrella + target control plane, clearly separated; *Making Agents Usable* |
| **Marketplace business model** | Under-specified; revenue and neutrality unstated | Hosting a primary category; free alongside paid; neutral sorting (no profiling); verification separate from ranking; fees only on facilitated paid transactions + verification |
| **Hosting ownership** | Ambiguous | Connect never owns/resells/hosts compute or inference; independent vendors provide it |
| **Budget architecture** | Single global daily/weekly/monthly implied as the model | Generalized model (arbitrary amounts/intervals/overlap/scopes/delegation); the simple cap named a starting point |
| **Workspace isolation** | AgentConnect "rejected isolation as a concept" | Manages isolation via pluggable enforcement providers; not itself a container/VM runtime; Levels 0–1 ship, 2–3 target |
| **Data boundaries** | Scattered | One component-level matrix; prohibited central data enumerated; enablement ≠ automatic compliance |
| **Repository responsibilities** | Control-plane home unstated | ADR 0002 frames it (Proposed); no doc assumes it is resolved |
| **Setup workflows** | Partial | Human-guided (15-stage) and agent-led (zero-trust) flows documented |
| **Organizational setup** | — | Profiles-not-editions; bring-your-own; import/attach/transfer/federate; no silent transfer |
| **Cross-repo status drift** | ToolConnect "no runtime / no contract"; ComputeConnect "simulated/unproven" | Corrected to shipped MVP / adopted contract 1.1 / single-host heterogeneity proven 2026-07-27 |

## Remaining intentional decisions

- **Repository-boundary ADR ([ADR 0002](docs/adr/0002-control-plane-repository-boundary.md))
  remains `Proposed`.** This is deliberate. The choice between a separate control-plane
  repository (Option A, the current lean) and expanding Connect (Option B) requires the Lead's
  ratification, or a formal deferral. Until it is accepted, no substantial control-plane
  application implementation begins in the `Connect` repository. No document assumes the
  decision has been made.
- The ecosystem-wide **`GovernanceItem`** interface is recorded as *future direction only*; it
  is not designed or built.

## Implementation status

**This documentation effort did not begin implementing the control plane.** No control-plane
application, marketplace runtime, generalized budget engine, billing system, organizational
runtime, sandbox runtime, or new API was built. All target-product behavior is labeled *design
direction* in the document that describes it. Changes were documentation plus small
doc-generation/consistency fixes only.

## Validation

The documentation was checked for:

- **Consistency** — no current document contradicts another; the drift check
  (`verify docs match the manifest`) passes; sibling status claims reconciled.
- **Cross-links** — the major documents reference each other (Product Thesis ↔ Marketplace ↔
  Transparency ↔ Data & Compliance ↔ Setup; Human Setup ↔ Agent Setup ↔ Organization Model;
  Agent Setup → Work/Knowledge/Capability planes + Workspace Isolation); relative links resolve;
  no orphaned architecture documents.
- **Terminology** — consistent use of Control / Work / Knowledge / Capability / Compute Plane,
  Workspace, Organization, Marketplace, Bring Your Own, Externally Billed, Marketplace Billed,
  Customer-Owned, Zero Trust, and Making Agents Usable across repositories.
- **Product identity** — free, open-source, zero-trust control plane for making agents usable;
  current vs target distinguished without overstating completed work.
- **Business model** — no subscriptions/per-seat/enterprise-edition/consulting/hosting; fees
  only on facilitated marketplace transactions and verification; customer-owned resources free.
- **Privacy model** — data minimization; prohibited central data enumerated; compliance
  enablement distinguished from automatic compliance.
- **Marketplace model** — categories, metadata, neutral sorting, verification separate from
  ranking and sponsorship, searchable per-framework compliance evidence.
- **Organizational model** — profiles not editions; bottom-up adoption; import/attach/transfer/
  federate; personal resources stay personal unless explicitly transferred.

## Audit trail note

This report, plus the in-place *superseded* markers in sibling repositories, is the historical
record of why the documentation changed. It should be updated, not replaced, if a later
editorial pass makes further corrections.
