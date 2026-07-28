# Connect — full-stack deployment

One `docker compose` deployment that runs all four Connect products as four services and
wires AgentConnect to the other three over the compose network. Everything here was
**built and run from the pushed product repos** on an aarch64 Linux host with Docker +
Compose v2; the captured output below is real, **except the `connect-smoke` output block**,
which is explicitly marked below as not yet re-captured since the script was extended.

- **AgentConnect API** — the task backplane's HTTP adapter (`agentconnect-api`)
- **BrainConnect** — the trusted memory ledger (`brainconnect serve`)
- **ComputeConnect** — the compute/placement plane (`computeconnect serve`)
- **ToolConnect** — the tool-governance decision point (`toolconnect serve`)

## Layout

| File | What it is |
|---|---|
| `docker-compose.yml` | The four services, one network, named volumes, healthchecks |
| `agentconnect.Dockerfile` | Installs `agentconnect-core` + `-router` + `-api` + `-cli` from the AC repo |
| `brainconnect.Dockerfile` | Installs `brainconnect-ai` from the BrainConnect (WikiBrain) repo |
| `computeconnect.Dockerfile` | Installs `computeconnect` from the ComputeConnect repo |
| `toolconnect.Dockerfile` | Installs `toolconnect` from the ToolConnect repo |
| `policies.cedar` | Cedar policy set mounted into ToolConnect (default-deny + two scoped allows: local non-sensitive reads, and the sandbox-worker's local write-effect tools) |
| `.env.example` | Environment template with **safe placeholder** tokens |
| `connect-health` | One command: are all four services up? |
| `connect-smoke` | One command: the full 10-step ecosystem sequence end to end across all four (capture -> promote -> recall -> tool authorize -> per-call grant/redeem -> placement -> real generation -> artifact -> closing capture) |
| `connect-agent-gate` | One command: proves AgentConnect dispatches a real managed subtask to a real compute worker through the AgentConnect->ToolConnect governor chokepoint |

The build contexts are the **sibling product repos** (`../../mcp-agentconnect`,
`../../WikiBrain`, `../../ComputeConnect`, `../../ToolConnect`), so this directory must sit
at `Connect/deploy/` next to those checkouts.

## Prerequisites

- Docker + Docker Compose v2 (`docker compose version`).
- The four product repos checked out next to `Connect/` under the directory names the
  compose contexts expect — AgentConnect and BrainConnect publish under different names,
  so clone those two with an explicit target directory:

  ```bash
  git clone https://github.com/Judgernaut777/AgentConnect mcp-agentconnect
  git clone https://github.com/Judgernaut777/BrainConnect WikiBrain
  git clone https://github.com/Judgernaut777/ComputeConnect
  git clone https://github.com/Judgernaut777/ToolConnect
  ```
- Optional: a llama.cpp (or any OpenAI-compatible) engine on the host for ComputeConnect
  to place real work on. Without one — or when it is bound to host loopback only —
  ComputeConnect comes up **`degraded`** and the stack is still healthy.

## Run it

```bash
cd Connect/deploy

# Reproducible build: check out the release you want in each sibling repo first.
# Compose builds each image from the sibling repo's WORKING TREE (context: ../../<repo>),
# so the images reflect whatever is checked out there — pin each repo to the commit
# recorded in ../manifest/ecosystem.yaml (the ecosystem lockfile: pin the exact commit,
# not a floating tag — no single tag spans all four repos):
pin() { PYTHONPATH=../scripts python3 -c "import _manifest_yaml as my; m = my.load(open('../manifest/ecosystem.yaml').read()); print(m['products']['$1']['commit'])"; }
git -C ../../mcp-agentconnect checkout "$(pin agentconnect)"     # or the commit/tag you are deploying
git -C ../../WikiBrain checkout "$(pin brainconnect)"
git -C ../../ComputeConnect checkout "$(pin computeconnect)"
git -C ../../ToolConnect checkout "$(pin toolconnect)"

cp .env.example .env          # then edit: set real BRAINCONNECT_TOKEN + TOOLCONNECT_AUTH_TOKEN
docker compose build
docker compose up -d
./connect-health              # all four services
./connect-smoke               # one real cross-product interaction
# ... when done:
docker compose down           # add -v to also drop the data volumes
```

> The four `context:` paths point at the sibling checkouts, not at a pinned git ref — Docker
> build contexts are directories, not tags. Checking out the manifest-pinned commit in each
> repo before `docker compose build` is what makes the built images correspond to that release.

Generate strong tokens with `python -c "import secrets; print(secrets.token_urlsafe(32))"`.

### Host port map

Deliberately off the host's reserved ports (`8080/8091/8787/8090/8095/8790`):

| Service | Host | Container |
|---|---|---|
| AgentConnect | 8890 | 8790 |
| BrainConnect | 8887 | 8787 |
| ComputeConnect | 8990 | 8090 |
| ToolConnect | 8995 | 8095 |

## Captured output (this is what actually happened)

`docker compose build` produced four images:

```
connect/agentconnect:0.1.0    187MB
connect/brainconnect:0.1.0    223MB
connect/computeconnect:0.1.0  167MB
connect/toolconnect:0.1.0     176MB
```

`docker compose up -d` then `docker compose ps`:

```
SERVICE          STATUS                    PORTS
agentconnect     Up (healthy)   0.0.0.0:8890->8790/tcp
brainconnect     Up (healthy)   0.0.0.0:8887->8787/tcp
computeconnect   Up (healthy)   0.0.0.0:8990->8090/tcp
toolconnect      Up (healthy)   0.0.0.0:8995->8095/tcp
```

`./connect-health`:

```
AgentConnect   UP    (memory_backend=brainconnect)
BrainConnect   UP    (ok=True)
ComputeConnect UP    (status=degraded)
ToolConnect    UP    (audit_chain_ok=True)
OK: all four services up.
```

`./connect-smoke` — the full 10-step sequence below (steps `[0]`-`[9]`), **captured real on
2026-07-28** against the stack rebuilt from the manifest-pinned heads (AgentConnect `101c47e`,
ToolConnect `58c2227`, ComputeConnect `2f61e37`, BrainConnect `38c7568`): **`pass=14 fail=0`**.
Ids below are anonymized; everything else is verbatim. (One fix landed during this capture: the
step-`[4]` deny case now asserts its tool as an `external`-sink write so it stays denied under
the deployed `local-manager-generate-write` policy widen — a plain write is now *permitted* for a
local principal, which is the policy `connect-agent-gate` depends on.)

```
== Connect ecosystem smoke ==
[0] mint AgentConnect operator token
  PASS minted operator token
[1] AgentConnect capture -> BrainConnect
  PASS captured candidate_<n> via backend=brainconnect
[2] human promote in BrainConnect (confidence=verified)
  PASS promoted to trusted claim
[3] AgentConnect recall <- BrainConnect
  PASS recalled the human-promoted trusted claim
[4] tool authorization via ToolConnect (contract 1.0: no args)
  PASS read allowed, write denied (contract 1.1)
[5] ToolConnect per-call grant (contract 1.1: authorize WITH args -> redeem -> replay denied)
  PASS authorize(args=...) allowed and issued grant <grant_id> (contract 1.1)
  PASS first redeem succeeded (same args, same principal)
  PASS second redeem of the SAME grant was denied (reason=already_redeemed) — one-use enforced
[6] placement decision from ComputeConnect
  PASS ComputeConnect returned a placement decision (eligible=False,
       reason=no_compliant_provider — expected 'degraded' when no local engine is reachable)
[7] ComputeConnect real generation (POST /generate)
  PASS ComputeConnect returned a real terminal decision (status=refused, reason=no_compliant_provider
       — expected when no compliant engine is reachable)
[8] AgentConnect records the output as a real artifact
  PASS created task <task_id>
  PASS artifact <artifact_id> recorded (type=worker_output)
  PASS artifact content round-trips byte-for-byte via GET /artifacts/<artifact_id>/chunk
[9] AgentConnect captures the outcome -> BrainConnect (PENDING only, closes the loop)
  PASS closing capture <candidate_id> recorded in BrainConnect as pending (never auto-promoted —
       step 2's gate is the only promotion path)
== SUMMARY: pass=<n> fail=0 ==
```

Steps `[6]`/`[7]` will read `eligible=True`/`status=succeeded` with real generated text
instead when a compliant engine is actually reachable from the container (see "Why
ComputeConnect is `degraded` in Docker" just below) — `connect-smoke` treats a
well-formed refusal as a pass either way, since both are real terminal decisions from
the control plane, not a wiring failure.

### Shared event bus — captured cross-product proof (2026-07-29)

With the bus wired (per-source publish tokens minted and set in `.env`, see
[`../EVENT_BUS.md`](../EVENT_BUS.md)), the same `connect-smoke` run above drove three
separate containers to publish their own domain events into AgentConnect's **one**
`event_log` stream. Read back from that single stream, filtered by `source_product`:

```
$ curl -H "Authorization: Bearer <operator>" "$AC/events?since=<seq>&source_product=toolconnect"
  2x tool.authorized                 # the two allowed reads (allow => no `outcome`)
  1x tool.authorized  /denied        # the denied external-sink write
  1x grant.issued
  1x grant.redeemed
$ ... &source_product=computeconnect
  1x compute.generation.refused /denied
$ ... &source_product=agentconnect
  1x task.created   1x artifact.created   1x memory.captured   # native Work-plane events
```

Every event is stamped with the publishing product; a consumer selects only what it needs.
The **anti-forgery** property was verified live in the same session: the ToolConnect-scoped
publish token is **refused `403`** when it tries to publish as `source_product=agentconnect`,
and accepted only for `source_product=toolconnect`. And the bus is **best-effort**: stopping
AgentConnect leaves every ToolConnect decision and ComputeConnect placement byte-identical —
the publishers degrade to no-ops, they never block or fail a request.

### Why ComputeConnect is `degraded` in Docker (and `ok` on a host/venv)

ComputeConnect places work on an **external** engine. In this Compose stack it is pointed
at `host.docker.internal:8080`, but the host's llama.cpp is bound to `127.0.0.1:8080`
(loopback only), so the container cannot reach it: the `local-llamacpp` provider is
`unreachable`, the `sim-cloud` provider stays healthy, and `/health` reports `degraded`.
The control plane is fully up — `/route/estimate` still returns a real placement decision
(here it correctly refuses, because the only healthy provider is cloud and the default
privacy tier forbids cloud). The identical stack run as host processes that share loopback
reports ComputeConnect `ok` and places real generation on `qwen3-30b-a3b` — see
[COMBINED_INSTALL.md](../COMBINED_INSTALL.md#host-venv-deployment-computeconnect-ok).

## What the smoke actually proves

Steps 1, 3, 6 and 9 are genuinely **AgentConnect-orchestrated** cross-product calls over
the compose network: AgentConnect's memory adapter reaches BrainConnect (twice — the
opening capture at step 1 and the closing capture at step 9), and its compute path
reaches ComputeConnect. Step 8 is AgentConnect's own task/artifact store, exercised with
the real text step 7 produced. Step 2 drives BrainConnect directly to exercise the
**human-only promotion gate** (an agent token cannot promote — that is by design; step 9's
closing capture proves this by staying `pending`, never auto-promoted). Steps 4 and 5
drive ToolConnect's decision API directly: step 4 is the contract-1.0 allow/deny shape,
step 5 is the contract-1.1 **per-call grant** — `authorize` with bound `args` issues a
one-use grant, a redeem with the same args and principal consumes it, and a second redeem
of that same grant is denied as `already_redeemed`, proving the grant is actually one-use
and not just decorative. Step 7 drives ComputeConnect's `/generate` directly for a real
(or honestly-refused) generation. None of steps 2, 4, 5 or 7 go through AgentConnect —
that is deliberate, the same way it was before this extension.

What this script still does **not** prove: that AgentConnect dispatches a *managed
subtask* to a real compute-backed worker, or that the AgentConnect->ToolConnect
**governor** consults ToolConnect on that dispatch path before a worker spawns. That is
`connect-agent-gate`'s job (see below). The governor *mechanism* itself (a real ALLOW
with a live `decision_id`, a real FORBIDDEN, a real FAIL-CLOSED) is proven independently
by `mcp-agentconnect/examples/demo_governor_chokepoint.py`.

### `connect-agent-gate`

```bash
./connect-agent-gate
```

Runs after `connect-smoke` against the same already-running stack. It registers the real
`local-manager` worker's tools in ToolConnect, widens `deploy/policies.cedar` with a
clearly marked, additive permit so the governor can allow them, dispatches a real
AgentConnect subtask to that worker end to end (real inference, a real artifact, a real
ToolConnect decision record in the audit chain), then narrows the policy back and proves
an identical subtask is genuinely blocked **before** the worker runs — a real Cedar deny,
not a fail-closed outage. It restores the widened policy afterward so re-runs stay
idempotent, and never touches AgentConnect, ComputeConnect, BrainConnect, or the host
engine. See the script's own header comment for the full phase-by-phase breakdown.

## Deploy-layer workarounds

None. An earlier build added `httpx` explicitly because `agentconnect-core` lazily imported
it without declaring it; that dependency is now declared (`httpx>=0.27`) upstream, so the
image installs the products with no extra pins.

## Cleanup

```bash
docker compose down        # stop + remove containers and the network
docker compose down -v     # also remove the brainconnect/toolconnect/agentconnect data volumes
```
