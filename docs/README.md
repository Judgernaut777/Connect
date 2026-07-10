# docs/

Longer-form ecosystem documents that do not belong in a top-level file.

**This directory is currently empty of content.** It exists because the top-level documents
are deliberately short, and material that outgrows them lands here rather than bloating the
front door.

## What belongs here

- Extended design notes that span more than one product
- Deep-dives referenced from [ARCHITECTURE.md](../ARCHITECTURE.md)
- Scope proposals for the design-phase products, once accepted
- A roadmap, if the ecosystem ever wants a single sequenced one

## What does not

The same rules as the repository root apply — see [CONTRIBUTING.md](../CONTRIBUTING.md). No
code. Nothing that describes a single product in isolation; that belongs in the product's own
repository.

## Where the product-level documents actually live

No product keeps its internals documented here. Follow the source.

| Topic | Where |
|---|---|
| Running the managed coding-agent loop | `docs/OPERATOR_GUIDE.md` in [AgentConnect](https://github.com/Judgernaut777/AgentConnect) |
| AgentConnect internals, safety, work queue, federation | `docs/` in AgentConnect |
| The memory ledger design contract, and the trust rule every consumer must obey | `docs/LEDGER_SPEC.md` in [BrainConnect](https://github.com/Judgernaut777/BrainConnect) |
| Schema migrations and the live-database hazard | `docs/MIGRATIONS.md` in BrainConnect |
| Memory safety, and why trusted is not the same as safe to expose | `docs/SAFETY.md` in BrainConnect |
| The tool-governance charter, and why it is a decision point rather than a proxy | `docs/ARCHITECTURE.md` and `docs/STATUS.md` in [ToolConnect](https://github.com/Judgernaut777/ToolConnect) |
| The compute control-plane charter | [ComputeConnect](https://github.com/Judgernaut777/ComputeConnect) — proposal not yet pushed |

Read a design-phase product's `docs/STATUS.md` before trusting any interface it describes.
ToolConnect's is explicit that every signature in its architecture document is illustrative,
not a committed API.
