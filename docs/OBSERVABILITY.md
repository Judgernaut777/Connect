# Observability

How to watch agent work across the Connect ecosystem — for **terminal** workers (a live
tmux pane per agent) and **non-terminal** workers (JSONL on disk, OTLP to a collector).
AgentConnect owns this surface; the other three products expose health and audit endpoints
that plug into the same operational picture.

Everything below was run from the published `agentconnect-cli` on this host.

## The model

AgentConnect emits **observation events** (a provider-neutral event model) as agents are
launched, produce output, delegate, succeed, fail, or are cancelled. A **provider** decides
what to do with those events. Providers are additive and independently fail-isolated: a
broken provider degrades, it does not take the task down (unless you opt into a stricter
failure policy).

Configuration is entirely environment-driven:

| Variable | Meaning |
|---|---|
| `AGENTCONNECT_OBSERVABILITY` | comma list of providers: `structured_log`, `tmux`, `herdr`, `otlp` |
| `AGENTCONNECT_OBSERVABILITY_FAILURE_POLICY` | `advisory` (default) · `task_blocking` · `startup_fatal` |
| `AGENTCONNECT_OBSERVABILITY_LOG_PATH` | JSONL path (default `~/.agentconnect/observability/events.jsonl`) |
| `AGENTCONNECT_OBSERVABILITY_TMUX_SOCKET` | dedicated tmux socket (default `agentconnect-obs`) |
| `AGENTCONNECT_OBSERVABILITY_TMUX_LAYOUT` | tmux layout hint (default `tiled`) |
| `AGENTCONNECT_OBSERVABILITY_HERDR_ENABLED` | `1`/`true` to enable the Herdr provider |
| `AGENTCONNECT_OBSERVABILITY_HERDR_SOCKET` | Herdr control socket path |
| `AGENTCONNECT_OTLP_ENDPOINT` | OTLP collector base URL (enables the `otlp` provider) |

Unset `AGENTCONNECT_OBSERVABILITY` ⇒ a single `noop` provider ⇒ no overhead. Verified:

```console
$ agentconnect observability providers
[ { "provider": "noop", "available": true, ... } ]
```

## Inspecting agents

The CLI reads the same ledger the service writes, so these work whether or not a live
provider is attached:

```bash
agentconnect agents list   <task_id>   # every observed agent for a task
agentconnect agents tree   <task_id>   # the delegation tree (from ledger records)
agentconnect agents watch  <task_id>   # live-refresh the delegation tree
agentconnect agents events <task_id>   # raw observation events
agentconnect agents output <agent_id>  # bounded, redacted terminal output
agentconnect agents attach <agent_id>  # real attach instructions for a live agent
agentconnect agents cancel <agent_id>  # cancel a live agent (propagates to the process)
agentconnect observability providers   # configured providers + their health (JSON)
agentconnect observability health      # aggregate observability health
```

`agents output` is **bounded and redacted** through AgentConnect's own safety layer — the
same redactor the service uses — so surfacing an agent's terminal never leaks secrets it
scrubs elsewhere.

## Terminal workers — the tmux live provider (the one that works here)

The tmux provider is a **real, working** live-terminal provider. With `tmux` on PATH:

```bash
export AGENTCONNECT_OBSERVABILITY=structured_log,tmux
agentconnect-api      # or the router / a launch — agents now get a live pane
```

Verified on this host:

```console
$ AGENTCONNECT_OBSERVABILITY=structured_log,tmux agentconnect observability providers
  structured_log  available=true  jsonl at ~/.agentconnect/observability/events.jsonl
  tmux            available=true  tmux 3.3a  (socket=agentconnect-obs)
```

Each observed agent gets a pane on the dedicated `agentconnect-obs` socket (kept off your
default tmux server so it cannot clobber your own sessions). Attach with the instructions
from `agentconnect agents attach`, or directly:

```bash
tmux -L agentconnect-obs attach
```

## Non-terminal workers — JSONL and OTLP

Not every worker has a terminal (an HTTP worker, a queue consumer, a CI runner). For those:

- **`structured_log`** appends one JSON object per event to
  `AGENTCONNECT_OBSERVABILITY_LOG_PATH`. Tail it, ship it to your log stack, or replay it.
  Available with no dependency (verified above).
- **`otlp`** exports spans/events to an OpenTelemetry collector when
  `AGENTCONNECT_OTLP_ENDPOINT` is set (it auto-adds `otlp` to the provider list). This is the
  path for a non-terminal fleet observed in Grafana/Tempo/Jaeger rather than a tmux wall.

You can run several at once: `structured_log,tmux,otlp` gives you a live wall **and** a
durable JSONL trail **and** collector export from the same event stream.

## The other three products

- **BrainConnect** — `GET /health` reports ledger + safety-engine health; `brainconnect
  ledger-health` and `brainconnect health` give a composite score. Safety engines that
  cannot run report `unavailable`, never "clean".
- **ComputeConnect** — `GET /health` reports each provider's health and a top-level
  `status` of `ok` / `degraded` / `down`; run metadata is at `GET /runs/{run_id}`.
- **ToolConnect** — `GET /health` includes `audit_chain_ok`; `toolconnect audit` prints
  recent decisions and `toolconnect verify-audit` walks the tamper-evident hash chain
  (exit 1 if broken — cron-shaped).

## Failure policy

`advisory` (default) keeps agents running even if a provider throws. Choose `task_blocking`
when an unobserved agent is unacceptable (the task fails rather than run blind), or
`startup_fatal` when a misconfigured provider should stop the process from coming up at all.
Pick per your risk posture; the default favours availability.
