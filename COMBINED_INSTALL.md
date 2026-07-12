# Combined installation

Running more than one Connect product together. All four products are installable at `0.1.0`.

Read [COMPATIBILITY.md](COMPATIBILITY.md) alongside this — especially the Python floor (3.11 for
a single-venv install), the port registry, and the one real caveat below.

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
.venv/bin/brainconnect init                  # create the DB and scaffold dirs
```

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
# In the BrainConnect venv — serve the ledger with a bearer token:
.venv/bin/brainconnect serve --port 8787 --token "$BC_TOKEN"

# In the AgentConnect environment — point the memory adapter at it:
export AGENTCONNECT_MEMORY_BACKEND=brainconnect
export BRAINCONNECT_URL="http://localhost:8787"
export BRAINCONNECT_TOKEN="$BC_TOKEN"
```

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

# In the AgentConnect environment — its shipped HttpLocalComputeProvider targets it:
export COMPUTECONNECT_URL="http://localhost:8090"
```

`/generate` defaults to the most restrictive privacy tier when none is supplied (CA-1), and cloud
placement requires positive re-verification; a `run_id` is echoed as `X-Run-Id` and is cancellable
via `POST /runs/{run_id}/cancel` (CA-3). **Note:** registering ComputeConnect as an AgentConnect
routing worker is currently programmatic — there is no env/YAML declaration surface for it yet.

### AgentConnect + ToolConnect (fail-closed tool governance)

```bash
# In the ToolConnect venv:
.venv/bin/toolconnect init-db --db ./toolconnect.db
.venv/bin/toolconnect serve --db ./toolconnect.db --policies examples/policies.cedar
```

The caller asks `POST /authorize` before invoking a tool, performs the call itself, and closes the
loop with `POST /decisions/{id}/outcome`. **This binding is API-level only:** AgentConnect ships no
ToolConnect client, so today you wire the two through ToolConnect's HTTP API directly.

---

## The full four-product install

The packaging validation on 2026-07-12 built wheels for all four products from pristine
`git archive` copies and installed **all twelve wheels plus dependencies — 86 packages — into a
single Python 3.11+ virtual environment with zero dependency conflicts** and eleven coexisting
console scripts. Separate venvs are still the recommended default; a single combined venv is a
verified, supported option when you want one environment.

The only non-obvious step is BrainConnect, which must come from its wheel (PyPI name collision):

```bash
# 1. Build a wheel for each product from its checkout:
python3 -m venv .buildenv && source .buildenv/bin/activate && pip install build

for repo in AgentConnect BrainConnect ComputeConnect ToolConnect; do
  ( cd "$repo" && python -m build --wheel --outdir ../wheelhouse )
done
# AgentConnect is nine wheels; the other three are one each — twelve in total.
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
- **No first-class ToolConnect client in AgentConnect**, and **no declaration surface** for
  registering ComputeConnect as a routing worker — both are wired programmatically or at the API.

If you want one system rather than a set of composable tools, the seams are real and tested — but
the coupling is deliberately thin, and the human gate is deliberately non-negotiable.
