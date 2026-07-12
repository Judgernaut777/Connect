# Combined installation

Running more than one Connect product together. All four products are installable at `0.1.0`.

Read [COMPATIBILITY.md](COMPATIBILITY.md) alongside this — especially the Python floor (3.11 for
a single-venv install), the port registry, and the naming note below. For the containerised
four-service deployment, see [deploy/](deploy/).

> **Name note: BrainConnect's PyPI distribution is `brainconnect-ai`.** The plain `brainconnect`
> name is owned on PyPI by an unrelated neuroscience package, so BrainConnect publishes as
> `brainconnect-ai` — `pip install brainconnect-ai`. The **command and the import package stay
> `brainconnect`** (a distribution may be named differently from what it imports), so every
> `brainconnect ...` invocation below is unchanged. From a checkout, `pip install -e .` is
> unaffected. Do **not** `pip install brainconnect` (bare) — that fetches the stranger's library.

---

## Standalone installs (each product alone)

Every product runs standalone. These are the copy-pasteable per-product installs; see
[GETTING_STARTED.md](GETTING_STARTED.md) for what to do after each one.

### AgentConnect

```bash
git clone https://github.com/Judgernaut777/AgentConnect
cd AgentConnect
python3 -m venv .venv && source .venv/bin/activate
pip install -e packages/agentconnect-core -e packages/agentconnect-cli
export AGENTCONNECT_DB_PATH="$PWD/agentconnect.db"
agentconnect --help
```

The other packages — `agentconnect-router`, `-runtime`, `-model-manager`, `-api`, `-mcp`,
`-linear`, `-temporal` — are separate installs you add only when you need them.

### BrainConnect

```bash
git clone https://github.com/Judgernaut777/BrainConnect
cd BrainConnect
cp config.example.toml config.toml
python3 -m venv .venv
.venv/bin/python -m pip install -e .        # installs `brainconnect` + `brainconnect-librarian`

# Pick where the ledger lives BEFORE `init` — see the warning below:
export BRAINCONNECT_DB="$HOME/connect-data/brainconnect/wiki.db"
.venv/bin/brainconnect init                  # create the DB and scaffold dirs
```

> **Set the DB path before `init`.** With `config.toml` copied straight from the
> example, `brainconnect init` targets **`~/.wiki-brain/wiki.db`** by default — the
> conventional path for a *personal* BrainConnect ledger. If you already run
> BrainConnect for yourself, running `init` unguarded opens (and migrates forward)
> that existing personal ledger. Point a fresh install at its own store first: either
> `export BRAINCONNECT_DB=/path/to/ledger.db` (it overrides `config.toml` and is the
> safe choice for tests, scripts, and any second install) or edit the `[paths] db`
> line in `config.toml`. Opening any repo runs forward migrations on whatever this
> resolves to, so choose it before the first command touches a DB.

### ComputeConnect

```bash
git clone https://github.com/Judgernaut777/ComputeConnect
cd ComputeConnect
python3 -m venv .venv
.venv/bin/python -m pip install -e .
.venv/bin/computeconnect serve --port 8090   # six LocalComputeProvider routes + OpenAI layer
```

### ToolConnect

```bash
git clone https://github.com/Judgernaut777/ToolConnect
cd ToolConnect
python3 -m venv .venv
.venv/bin/python -m pip install -e .
.venv/bin/toolconnect init-db --db ./toolconnect.db
.venv/bin/toolconnect serve --db ./toolconnect.db --policies examples/policies.cedar  # 127.0.0.1:8095
```

`serve` refuses to start without a parseable policy file; an empty policy set denies everything.

---

## Two-product recipes

Each pair below is a seam that was exercised over the real transport during the Phase-5
integration run. Use **separate virtual environments** per product (the manifesto's modularity
principle, and it keeps BrainConnect's zero-model guarantee clean).

### AgentConnect + BrainConnect (human-gated memory over HTTP)

BrainConnect now ships an HTTP server, so the memory adapter has something real to talk to.

```bash
# In the BrainConnect venv — serve the ledger with a bearer token. Point
# BRAINCONNECT_DB at the ledger you initialised for this product; do NOT let it
# fall back to the personal default (~/.wiki-brain/wiki.db). See the standalone
# BrainConnect note above.
export BRAINCONNECT_DB="$HOME/connect-data/brainconnect/wiki.db"
.venv/bin/brainconnect serve --port 8787 --token "$BC_TOKEN"

# In the AgentConnect environment — setting BRAINCONNECT_URL both selects and enables
# the brainconnect memory backend (there is no separate "backend" switch):
export BRAINCONNECT_URL="http://localhost:8787"
export BRAINCONNECT_TOKEN="$BC_TOKEN"
```

`BRAINCONNECT_URL` is all it takes. AgentConnect no longer ships an active
`config/memory.yaml` — that file is now `config/memory.yaml.example` and is **not**
auto-loaded — so running `agentconnect-api` from a checkout no longer forces a
`wikibrain` backend or silently overrides your `BRAINCONNECT_URL`. If you prefer to
configure memory from a YAML file instead of the environment, copy the example and
point `AGENTCONNECT_MEMORY_CONFIG` at your copy (`export
AGENTCONNECT_MEMORY_CONFIG=/path/to/memory.yaml`); env still wins over the file.

Verified (2026-07-12, over the real HTTP transport, scratch ledger): with just
`BRAINCONNECT_URL`/`BRAINCONNECT_TOKEN` set, `agentconnect-api`'s `GET /health` reports
`"memory_backend":"brainconnect"`. A `POST /memory/capture` files a `pending` candidate
in BrainConnect over HTTP; after a human `POST /memory/promote` (operator token, with
`confidence` + `scope`), a `POST /memory/recall` returns that now-trusted claim
(`"trusted":true`, `"role":"trusted_authority"`) fetched from BrainConnect over HTTP.

The trust gradient is one-way by design: workers may **capture** (write-only), only a manager may
**recall**, and re-injection flows through AgentConnect's classify-and-redact pass. Promotion is
**human-only** — a captured claim lands `pending` and becomes trusted memory only when you promote
it from your own terminal.

> **Never serve BrainConnect's MCP `--review` mode to an agent.** That mode exposes
> `brain_pending` / `brain_promote` / `brain_reject` — the human gate. Promote from a terminal you
> control, not from an agent's tool list.

Alternatively, run both as **MCP servers behind one harness** (no HTTP): register AgentConnect's
`agentconnect-router` (or `agentconnect-mcp`) and BrainConnect's `brainconnect mcp serve` as two
stdio entries. The harness is then the only component touching both; nothing couples them, and the
agent must call `brain_capture` itself.

### AgentConnect + ComputeConnect (private local generation)

```bash
# In the ComputeConnect venv:
.venv/bin/computeconnect serve --port 8090

# In the AgentConnect environment — AGENTCONNECT_COMPUTE_URL registers ComputeConnect
# as the `local-manager` routing worker (env wins over config/compute.yaml):
export AGENTCONNECT_COMPUTE_URL="http://localhost:8090"
```

`/generate` defaults to the most restrictive privacy tier when none is supplied (CA-1), and cloud
placement requires positive re-verification; a `run_id` is echoed as `X-Run-Id` and is cancellable
via `POST /runs/{run_id}/cancel` (CA-3). Registration is now **declarative**: verified that with
`AGENTCONNECT_COMPUTE_URL` set, `agentconnect-api`'s `GET /health` lists `local-manager` among its
workers. On a host/venv where ComputeConnect can reach the host llama.cpp, its `/route/estimate`
returns `eligible=true` selecting the local model.

### AgentConnect + ToolConnect (fail-closed tool governance)

```bash
# In the ToolConnect venv:
.venv/bin/toolconnect init-db --db ./toolconnect.db
.venv/bin/toolconnect serve --db ./toolconnect.db --policies examples/policies.cedar
```

```bash
# In the AgentConnect environment — bind the fail-closed governor:
export AGENTCONNECT_TOOLCONNECT_URL="http://localhost:8095"
export AGENTCONNECT_TOOLCONNECT_TOKEN="$TC_TOKEN"   # if the server was started with a token
export AGENTCONNECT_TOOLCONNECT_MODE=required        # fail-closed; `advisory` logs but does not block
```

AgentConnect ships a first-class client: `agentconnect-core`'s `ToolConnectGovernor` consults
`POST /authorize` before a worker with declared tools runs, and closes the loop with
`POST /decisions/{id}/outcome`. It is **fail-closed** — an unreachable decision point denies. A
denied tool blocks the subtask **before** the worker spawns. Verified against a live server: a
read tool is allowed, a write tool is denied, and decisions carry `contract_version: "1.0"`.

---

## The full four-product install

The packaging validation on 2026-07-12 built wheels for all four products from pristine
`git archive` copies and installed **all twelve wheels plus dependencies — 86 packages — into a
single Python 3.11+ virtual environment with zero dependency conflicts** and eleven coexisting
console scripts. Separate venvs are still the recommended default; a single combined venv is a
verified, supported option when you want one environment.

The one non-obvious step is AgentConnect: its **root** `pyproject.toml` is dev-tooling
only (no `[build-system]`/`[project]`), and a flat-layout build from the repo root errors
on `config/` and `packages/`. AgentConnect's nine distributions each live under
`packages/agentconnect-*` and are built **per package**. The other three products are
single-package repos and build from their checkout root.

```bash
# 1. Build all twelve wheels into one wheelhouse:
python3 -m venv .buildenv && source .buildenv/bin/activate && pip install build
WHEELHOUSE="$PWD/wheelhouse"; mkdir -p "$WHEELHOUSE"

# AgentConnect — nine wheels, one per package under packages/agentconnect-*:
for pkg in AgentConnect/packages/agentconnect-*; do
  ( cd "$pkg" && python -m build --wheel --outdir "$WHEELHOUSE" )
done

# The other three — one wheel each, built from the repo root:
for repo in BrainConnect ComputeConnect ToolConnect; do
  ( cd "$repo" && python -m build --wheel --outdir "$WHEELHOUSE" )
done
# Nine AgentConnect wheels + three = twelve. Confirm: `ls "$WHEELHOUSE"/*.whl | wc -l` → 12.
deactivate

# 2. Install everything into one fresh venv from the wheelhouse:
python3.11 -m venv .venv && source .venv/bin/activate
pip install --find-links ./wheelhouse \
            brainconnect-ai \
            agentconnect-core agentconnect-cli agentconnect-api agentconnect-mcp \
            agentconnect-linear agentconnect-router agentconnect-model-manager \
            agentconnect-runtime agentconnect-temporal \
            computeconnect toolconnect
```

BrainConnect resolves by its distribution name `brainconnect-ai`, which is unambiguous on PyPI
(the bare `brainconnect` belongs to an unrelated project). To forbid PyPI entirely for an
air-gapped build, add `--no-index` and provide every dependency wheel under `./wheelhouse`.

Verify the eleven console scripts coexist:

```bash
agentconnect --help && brainconnect --help && computeconnect --help && toolconnect --help
```

---

## What "combined" does not buy you

- **No automatic memory capture.** AgentConnect does not write findings into BrainConnect for you;
  under the harness topology the agent must call `brain_capture` itself, and promotion is always a
  human act.
- **No shared trust model.** A completed AgentConnect task is not a promoted BrainConnect claim,
  and never becomes one without a human.
- **No shared database.** Each product keeps its own store, lifecycle, and backup job.
- **No automatic promotion or shared trust.** The seams are wired (memory backend, compute worker,
  and the fail-closed ToolConnect governor all bind via environment variables), but a completed
  AgentConnect task never becomes a trusted BrainConnect claim without a human.

If you want one system rather than a set of composable tools, the seams are real and tested — but
the coupling is deliberately thin, and the human gate is deliberately non-negotiable.

---

## Three-product and four-product, wired (env-driven)

The two-product seams compose. Point AgentConnect at any subset by setting the relevant
variables; unset ones simply leave that subsystem off (standalone behaviour is unchanged).

```bash
# AgentConnect API wired to all three peers at once:
export BRAINCONNECT_URL="http://localhost:8787"        BRAINCONNECT_TOKEN="$BC_TOKEN"
export AGENTCONNECT_COMPUTE_URL="http://localhost:8090"
export AGENTCONNECT_TOOLCONNECT_URL="http://localhost:8095" AGENTCONNECT_TOOLCONNECT_TOKEN="$TC_TOKEN"
export AGENTCONNECT_TOOLCONNECT_MODE=advisory
agentconnect-api      # GET /health then reports memory_backend=brainconnect and worker local-manager
```

Two-product subsets are just this with two of the three blocks omitted (AC+BC, AC+CC, AC+TC).

### Host-venv deployment (ComputeConnect `ok`)

The four-service stack also runs as **host processes in one venv** — useful when you want
ComputeConnect to reach a host-loopback engine (which a container cannot). This is the same
wiring the [deploy/](deploy/) Compose stack uses, minus containers. Verified on this host:
BrainConnect, ToolConnect and ComputeConnect on fresh ports, AgentConnect wired to all three;
`GET /health` on ComputeConnect reported `status: ok` with `local-llamacpp healthy`, and a
`/generate` placed real output on `qwen3-30b-a3b`. The **container** deployment reports
ComputeConnect `degraded` instead, because the host llama.cpp is loopback-bound and unreachable
from inside a container — see [deploy/README.md](deploy/README.md#why-computeconnect-is-degraded-in-docker-and-ok-on-a-hostvenv).

### Or just use Docker Compose

[deploy/](deploy/) ships a four-service `docker-compose.yml` that builds all four images from these
repos and wires them together, plus `connect-health` and `connect-smoke`. That is the shortest path
to a running ecosystem; it was built and run, and its captured output is in
[deploy/README.md](deploy/README.md).
