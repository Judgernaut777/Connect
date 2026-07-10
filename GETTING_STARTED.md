# Getting started

Pick the product you actually need. Both implemented products are standalone — installing
one does not require the other. If you are not sure which you want, read the
["Which product do I need?"](README.md#which-product-do-i-need) table first.

Commands below are POSIX (Linux/macOS). Each product documents Windows equivalents in its
own repository; those repositories remain the authority if anything here has drifted.

---

## AgentConnect only

**Requires Python ≥ 3.10.**

AgentConnect is a control plane for managed coding-agent work. The stable path is the
managed coding-agent loop.

```bash
git clone https://github.com/Judgernaut777/AgentConnect
cd AgentConnect

python -m venv .venv && source .venv/bin/activate

# The CLI is required. Core alone gives you the library, not the command.
pip install -e packages/agentconnect-core -e packages/agentconnect-cli

export AGENTCONNECT_DB_PATH=/srv/agentconnect/agentconnect.db
agentconnect --help
```

`agentconnect` must be on `PATH` **inside the agent's shell**, not only in yours. That is
the single most common setup failure.

Then run the loop — create a task, launch a workspace with a scoped token, and hand the
shell to your agent:

```bash
agentconnect tasks create --title "…" --goal "…" --by you
agentconnect launch codex --task "$TASK" --claim --repo .
agentconnect shell --task "$TASK" -- <agent-command>
```

A managed agent session cannot mark its own task complete. That is deliberate, and it is the
point of the product. An HTTP-API bypass that once let an agent do exactly that was fixed at
commit `a07df7f`; the HTTP adapter now authenticates and the token decides. See
[COMPATIBILITY.md](COMPATIBILITY.md#known-gaps).

**Read next:** `docs/OPERATOR_GUIDE.md` in the AgentConnect repository. It walks the whole
loop with exact commands, and its failure-modes section lists what actually goes wrong.

The other packages — `agentconnect-router`, `-runtime`, `-model-manager`, `-api`, `-mcp`,
`-linear`, `-temporal` — are separate installs. You do not need them for the loop above.

---

## BrainConnect only

**Requires Python ≥ 3.11.**

BrainConnect is a trusted memory ledger. The loop is: stand it up → capture sources → let
the librarian draft facts → **you approve** → your agents recall.

The commands still use the old WikiBrain names. See the
[naming note](README.md#status-at-a-glance).

```bash
git clone https://github.com/Judgernaut777/BrainConnect
cd BrainConnect

cp config.example.toml config.toml
python3 -m venv .venv
.venv/bin/python -m pip install -e ./cli   # installs both `wiki` and `wiki-librarian`

wiki init                                   # create the DB and scaffold dirs
```

Capture something. Every source enters `pending`, behind the human gate:

```bash
wiki capture --origin me "TIL: HTTP caches key on the request, not the response"
wiki pending list
wiki promote candidate_1 --scope repo:my-app --confidence verified
wiki recall --query "http cache" --scope repo:my-app --profile manager_brief
```

**The `wiki` command makes zero model calls.** Only `wiki-librarian` — a separate process —
uses a model, and only to *draft* candidates you then review. Point it at a local endpoint
in `config.toml` under `[librarian]`; a local Ollama or LM Studio works, as does a hosted
endpoint via an API-key environment variable.

Agents reach the same concepts over MCP as `brain_recall`, `brain_capture`, and
`brain_feedback`. The human-gated `brain_pending` / `brain_promote` / `brain_reject` tools
exist **only** under `wiki mcp serve --review`.

> **Never point an agent at `--review`.** That mode hands the promotion gate — the thing that
> makes the ledger trustworthy — to the party the gate exists to constrain.

**Hacking on it?** `Repo.open()` runs forward schema migrations on **every** open, including
the one the MCP server performs at launch. The database lives at an absolute path from
`config.toml`, so passing a temporary repo root does **not** isolate it. Set
`WIKIBRAIN_DB=/tmp/scratch.db` in tests, scripts, and MCP verification so they cannot touch
your live `~/.wiki-brain/wiki.db`.

---

## ComputeConnect only

**Not installable. There is no code.**

ComputeConnect is in the architecture and design phase. Its charter is a heterogeneous
compute-provider registry, runtime and model lifecycle delegation, placement policy, health,
and execution metadata, conforming to AgentConnect's `LocalComputeProvider` contract.

There is nothing to install and no timeline to report. The contract it will implement already
ships inside `agentconnect.core.local_compute`; the implementation does not exist. Its
architecture proposal is published (commit `19e1406`) in
[its repository](https://github.com/Judgernaut777/ComputeConnect), which is documentation
only.

---

## ToolConnect only

**Not installable. There is no runtime implementation.**

ToolConnect is in its validation phase. There is an in-memory prototype — roughly 600 lines
with a 52-test suite that passes offline — built to test assumptions, **not to be the
product.** It has no server, no database, no HTTP service, and no tool execution. You can run
its test suite from a clone, but there is nothing to deploy.

Its charter is a protocol-neutral tool registry, asserted governance metadata, policy
decisions, health, authorization records, and audit. It is a **policy and decision point, not
a tool-execution proxy** — it does not sit in the data path, and tool calls do not flow
through it. Its tool authorization **fails closed**: unlike a memory layer, it may not degrade
to permissive when unavailable.

Read [its repository](https://github.com/Judgernaut777/ToolConnect) before proposing work; its
`docs/STATUS.md` is explicit about what the prototype does and does not settle — including that
the "protocol-neutral" claim is still unproven, because every tool ingested so far was
MCP-shaped.

---

## Combined ecosystem installation

**Available today:** AgentConnect, BrainConnect.
**Design-stage, not installable:** ComputeConnect, ToolConnect.

A combined install therefore means **two products**, and it comes with a real caveat: the
network path between them does not exist yet.

The integration is defined and semantically tested — AgentConnect registers a BrainConnect
memory adapter pointed at `http://localhost:8787` by default — but BrainConnect ships no HTTP
server to answer there. The cross-repo test substitutes an in-process transport.

Do not skip [COMBINED_INSTALL.md](COMBINED_INSTALL.md); it explains exactly what works, what
does not, and which of the two supported topologies you actually want. Read
[COMPATIBILITY.md](COMPATIBILITY.md) alongside it for the Python floor, the port registry,
and the licensing divergence.

Four-product installation instructions will be written when the design-stage products have
runnable releases. Not before.
