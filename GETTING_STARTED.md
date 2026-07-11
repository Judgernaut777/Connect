# Getting started

Pick the product you actually need. Every product is standalone — installing one does not
require the others. If you are not sure which you want, read the
["Which product do I need?"](README.md#which-product-do-i-need) table first.

Commands below are POSIX (Linux/macOS). Each product documents Windows equivalents in its own
repository; those repositories remain the authority if anything here has drifted.

---

## AgentConnect only

**Requires Python ≥ 3.10. Maturity: release candidate.**

AgentConnect is a control plane for managed coding-agent work. The stable path is the managed
coding-agent loop.

```bash
git clone https://github.com/Judgernaut777/AgentConnect
cd AgentConnect

python3 -m venv .venv && source .venv/bin/activate

# The CLI is required. Core alone gives you the library, not the command.
pip install -e packages/agentconnect-core -e packages/agentconnect-cli

export AGENTCONNECT_DB_PATH="$PWD/agentconnect.db"
agentconnect --help
```

`agentconnect` must be on `PATH` **inside the agent's shell**, not only in yours. That is the
single most common setup failure.

Then run the loop — create a task, launch a workspace with a scoped token, and hand the shell to
your agent:

```bash
agentconnect tasks create --title "…" --goal "…" --by you
agentconnect launch codex --task "$TASK" --claim --repo .
agentconnect shell --task "$TASK" -- <agent-command>
```

A managed agent session cannot mark its own task complete. That is deliberate, and it is the point
of the product. An HTTP-API bypass that once let an agent do exactly that was fixed at commit
`a07df7f`, and an independent retest this cycle confirmed it stays fixed. See
[COMPATIBILITY.md](COMPATIBILITY.md#known-gaps).

**Read next:** `docs/OPERATOR_GUIDE.md` in the AgentConnect repository. It walks the whole loop
with exact commands, and its failure-modes section lists what actually goes wrong.

The other packages — `agentconnect-router`, `-runtime`, `-model-manager`, `-api`, `-mcp`,
`-linear`, `-temporal` — are separate installs. You do not need them for the loop above.

---

## BrainConnect only

**Requires Python ≥ 3.11. Maturity: release candidate.**

BrainConnect is a trusted memory ledger. The loop is: stand it up → capture sources → let the
librarian draft facts → **you approve** → your agents recall.

The package and commands are renamed from WikiBrain; the MCP tools are still `brain_*` and the data
directory is still `~/.wiki-brain/`. See the [naming note](README.md#status-at-a-glance).

```bash
git clone https://github.com/Judgernaut777/BrainConnect
cd BrainConnect

cp config.example.toml config.toml
python3 -m venv .venv
.venv/bin/python -m pip install -e .        # installs `brainconnect` + `brainconnect-librarian`

.venv/bin/brainconnect init                  # create the DB and scaffold dirs
```

Capture something. Every source enters `pending`, behind the human gate:

```bash
brainconnect capture --origin me "TIL: HTTP caches key on the request, not the response"
brainconnect pending list
brainconnect promote candidate_1 --scope repo:my-app --confidence verified
brainconnect recall --query "http cache" --scope repo:my-app --profile manager_brief
```

**The `brainconnect` command makes zero model calls.** Only `brainconnect-librarian` — a separate
process — uses a model, and only to *draft* candidates you then review. Point it at a local endpoint
in `config.toml` under `[librarian]`; a local Ollama or LM Studio works, as does a hosted endpoint
via an API-key environment variable.

Agents reach the same concepts over MCP as `brain_recall`, `brain_capture`, and `brain_feedback`.
The human-gated `brain_pending` / `brain_promote` / `brain_reject` tools exist **only** under
`brainconnect mcp serve --review`. To reach the ledger over HTTP instead, run `brainconnect serve`
(default `127.0.0.1:8787`, optional `--token`).

> **Never point an agent at `--review`.** That mode hands the promotion gate — the thing that makes
> the ledger trustworthy — to the party the gate exists to constrain.

**Hacking on it?** `Repo.open()` runs forward schema migrations on **every** open, including the one
the MCP server performs at launch. The database lives at an absolute path from `config.toml`, so
passing a temporary repo root does **not** isolate it. Set `BRAINCONNECT_DB=/tmp/scratch.db` in
tests, scripts, and MCP verification so they cannot touch your live `~/.wiki-brain/wiki.db`.
(`WIKIBRAIN_DB` is honored as a deprecated fallback only while `BRAINCONNECT_DB` is unset.)

---

## ComputeConnect only

**Requires Python ≥ 3.11. Maturity: MVP — heterogeneity unproven.**

ComputeConnect is a local-compute provider and control plane. It serves a model to a
`LocalComputeProvider` client behind a placement and privacy policy.

```bash
git clone https://github.com/Judgernaut777/ComputeConnect
cd ComputeConnect
python3 -m venv .venv
.venv/bin/python -m pip install -e .

.venv/bin/computeconnect serve --port 8090   # 6 LocalComputeProvider routes + OpenAI /v1 layer
```

It implements `GET /health`, `GET /models`, `GET /models/loaded`, `POST /route/estimate`,
`POST /generate`, and `POST /runs/{run_id}/cancel`, plus an OpenAI-compatible `/v1` layer.
`/generate` defaults to the **most restrictive** privacy tier when none is given (CA-1), and a
`run_id` is echoed as `X-Run-Id` and is cancellable (CA-3).

**Know before you build on it:** on a single-node host the runtime is real but the *second* provider
is **simulated**. Placement across genuinely heterogeneous hardware has not been demonstrated.
ComputeConnect also never manages an engine's lifecycle — it consumes the local llama.cpp engine on
`:8080` **read-only**. Read its `docs/STATUS.md` before proposing work.

---

## ToolConnect only

**Requires Python ≥ 3.11. Maturity: MVP service.**

ToolConnect is a tool-governance decision point. It answers "may this principal call this tool" and
records what happened — it never executes the tool.

```bash
git clone https://github.com/Judgernaut777/ToolConnect
cd ToolConnect
python3 -m venv .venv
.venv/bin/python -m pip install -e .

.venv/bin/toolconnect init-db --db ./toolconnect.db
.venv/bin/toolconnect serve --db ./toolconnect.db --policies examples/policies.cedar  # 127.0.0.1:8095
```

The caller asks `POST /authorize`, invokes the tool itself, and closes the loop with
`POST /decisions/{id}/outcome`. There is deliberately **no invocation route** — a test asserts no
`invoke()` exists. Authorization **fails closed**: `serve` refuses to start without a parseable
policy file, and an empty policy set denies everything.

Capability metadata is treated as an **untrusted registry assertion**, never a server's self-claim —
an operator must assert a descriptor before a tool becomes invocable, and post-assertion drift
revokes invocability until re-asserted. Read its `docs/SERVICE.md` and `docs/STATUS.md`; the
"protocol-neutral" claim is only partially proven, because the tools ingested so far were MCP-shaped.

---

## Combined ecosystem installation

All four products are installable, so a combined install is real. See
[COMBINED_INSTALL.md](COMBINED_INSTALL.md) for the two-product recipes (AgentConnect + BrainConnect,
+ ComputeConnect, + ToolConnect) and the verified single-venv four-product install (86 packages,
zero conflicts).

One caveat carries into every combined recipe: **the PyPI name `brainconnect` is taken by an
unrelated package**, so BrainConnect must be installed by wheel path or from a checkout, never by
bare name. Read [COMPATIBILITY.md](COMPATIBILITY.md) alongside it for the Python floor, the port
registry, and the contract amendments.
