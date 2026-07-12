# Connect — full-stack deployment

One `docker compose` deployment that runs all four Connect products as four services and
wires AgentConnect to the other three over the compose network. Everything here was
**built and run from the pushed product repos** on an aarch64 Linux host with Docker +
Compose v2; the captured output below is real.

- **AgentConnect API** — the task backplane's HTTP adapter (`agentconnect-api`)
- **BrainConnect** — the trusted memory ledger (`brainconnect serve`)
- **ComputeConnect** — the compute/placement plane (`computeconnect serve`)
- **ToolConnect** — the tool-governance decision point (`toolconnect serve`)

## Layout

| File | What it is |
|---|---|
| `docker-compose.yml` | The four services, one network, named volumes, healthchecks |
| `agentconnect.Dockerfile` | Installs `agentconnect-core` + `-api` + `-cli` (+ `httpx`) from the AC repo |
| `brainconnect.Dockerfile` | Installs `brainconnect-ai` from the BrainConnect (WikiBrain) repo |
| `computeconnect.Dockerfile` | Installs `computeconnect` from the ComputeConnect repo |
| `toolconnect.Dockerfile` | Installs `toolconnect` from the ToolConnect repo |
| `policies.cedar` | Cedar policy set mounted into ToolConnect (default-deny + one safe allow) |
| `.env.example` | Environment template with **safe placeholder** tokens |
| `connect-health` | One command: are all four services up? |
| `connect-smoke` | One command: a real cross-product interaction across all four |

The build contexts are the **sibling product repos** (`../../mcp-agentconnect`,
`../../WikiBrain`, `../../ComputeConnect`, `../../ToolConnect`), so this directory must sit
at `Connect/deploy/` next to those checkouts.

## Prerequisites

- Docker + Docker Compose v2 (`docker compose version`).
- The four product repos checked out next to `Connect/` at their `0.1.0` tips.
- Optional: a llama.cpp (or any OpenAI-compatible) engine on the host for ComputeConnect
  to place real work on. Without one — or when it is bound to host loopback only —
  ComputeConnect comes up **`degraded`** and the stack is still healthy.

## Run it

```bash
cd Connect/deploy
cp .env.example .env          # then edit: set real BRAINCONNECT_TOKEN + TOOLCONNECT_AUTH_TOKEN
docker compose build
docker compose up -d
./connect-health              # all four services
./connect-smoke               # one real cross-product interaction
# ... when done:
docker compose down           # add -v to also drop the data volumes
```

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

`./connect-smoke`:

```
== Connect ecosystem smoke ==
[0] mint AgentConnect operator token
  PASS minted operator token
[1] AgentConnect capture -> BrainConnect
  PASS captured candidate_1 via backend=brainconnect
[2] human promote in BrainConnect (confidence=verified)
  PASS promoted to trusted claim
[3] AgentConnect recall <- BrainConnect
  PASS recalled the human-promoted trusted claim
[4] tool authorization via ToolConnect
  PASS read allowed, write denied (contract 1.0)
[5] placement decision from ComputeConnect
  PASS ComputeConnect returned a placement decision (eligible=False,
       reason=no_compliant_provider — expected 'degraded' when no local engine is reachable)
== SUMMARY: pass=6 fail=0 ==
```

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

Steps 1, 3 and 5 are genuinely **AgentConnect-orchestrated** cross-product calls over the
compose network: AgentConnect's memory adapter reaches BrainConnect, and its compute path
reaches ComputeConnect. Step 2 drives BrainConnect directly to exercise the **human-only
promotion gate** (an agent token cannot promote — that is by design). Step 4 drives
ToolConnect's decision API to show allow/deny; the AgentConnect **governor** path that
blocks a subtask before its worker spawns is proven separately by
`mcp-agentconnect/examples/demo_governor_chokepoint.py`.

## The one deploy-layer workaround

The AgentConnect image installs `httpx` explicitly. `agentconnect-core` lazily imports
`httpx` in its memory, compute and ToolConnect clients but declares only `pydantic` +
`pyyaml`, so a base `agentconnect-api` install cannot reach the sibling services without it.
A combined venv gets `httpx` transitively from ComputeConnect; an isolated AC image does
not. Reported upstream — the fix is to add `httpx>=0.27` to `agentconnect-core`'s deps.

## Cleanup

```bash
docker compose down        # stop + remove containers and the network
docker compose down -v     # also remove the brainconnect/toolconnect/agentconnect data volumes
```
