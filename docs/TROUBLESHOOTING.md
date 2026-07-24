# Troubleshooting

Symptoms seen while building and running the [deploy/](../deploy/) stack, with the actual
cause and fix. Each entry is something that was hit and resolved, not hypothetical.

## Install / build

### `agentconnect-api` can't reach BrainConnect/ComputeConnect/ToolConnect; recall warns "No module named 'httpx'"

**Cause:** older `agentconnect-core` lazily imported `httpx` in all three HTTP clients but
declared only `pydantic` + `pyyaml`, so a base `agentconnect-api` install had no `httpx`.
**Fix:** fixed upstream — `agentconnect-core` now declares `httpx>=0.27`. If you still see
this, the AgentConnect checkout predates the fix: update it and reinstall
`agentconnect-core`.

### `pip install brainconnect` installs the wrong package

**Cause:** the bare `brainconnect` name on PyPI is an unrelated project.
**Fix:** install the distribution **`brainconnect-ai`**; the command/import stay `brainconnect`.

### `agentconnect-api` install fails resolving `agentconnect-core==0.1.0` from PyPI

**Cause:** the packages are not published; the pin must resolve from a local path.
**Fix:** `pip install ./packages/agentconnect-core` **before** `agentconnect-api` (the deploy
Dockerfile installs core first).

### Docker build can't find the Dockerfile

**Cause:** the Dockerfiles live in `Connect/deploy/` but the build **context** is the sibling
product repo. The `dockerfile:` field is a relative path back into `deploy/`
(`../Connect/deploy/x.Dockerfile`).
**Fix:** keep `Connect/` and the four product repos as siblings under one parent, and run
`docker compose` from `Connect/deploy/`.

## Runtime

### ComputeConnect health is `degraded` / `/route/estimate` returns `no_compliant_provider`

**Cause (containers):** ComputeConnect points at `host.docker.internal:8080`, but the host
llama.cpp is bound to `127.0.0.1:8080` and a container cannot reach host loopback. The
`local-llamacpp` provider is `unreachable`; `sim-cloud` stays healthy ⇒ `degraded`. A
default-privacy request then finds no compliant provider (cloud is forbidden by default).
**This is expected.** **Fix if you need real local placement:** run ComputeConnect as a host
process (shares loopback — verified `status: ok`, real generation on `qwen3-30b-a3b`), bind
the engine to a container-reachable interface, or use host networking.

### ToolConnect `/health` returns 401

**Cause:** the server was started with a token, so **every** route (including `/health`)
requires `Authorization: Bearer <token>`.
**Fix:** send the token. `connect-health` reads `TOOLCONNECT_AUTH_TOKEN` from `.env` for
exactly this.

### `toolconnect serve` refuses to start

**Cause(s), each with an actionable message:** no `--policies` file; an unparseable Cedar
policy; or a non-loopback bind with no token.
**Fix:** provide a parseable policy file and, for a non-loopback bind, a token via
`$TOOLCONNECT_AUTH_TOKEN`.

### BrainConnect `serve` errors: "no database"

**Cause:** `serve` requires an existing DB; a fresh `BRAINCONNECT_DB` path has none.
**Fix:** `brainconnect init` first (the deploy image inits if the DB is absent). **Never**
point `BRAINCONNECT_DB` at the real `~/.wiki-brain/wiki.db` for a scratch/prod service.

### AgentConnect memory promote fails: "promote requires confidence"

**Cause:** AgentConnect's `POST /memory/promote` does not forward a confidence level, but
BrainConnect requires one (`low|medium|high|verified`).
**Fix:** perform the human promotion **directly against BrainConnect**
(`POST /candidates/{id}/promote` with `confidence` and a `scope`), which is where the human
gate lives anyway. `connect-smoke` does exactly this. (Reported upstream as an AC gap.)

### AgentConnect API returns 401 on every non-`/health` route

**Cause:** every route except `/health` needs a session token.
**Fix:** mint an operator token locally — `agentconnect tokens issue --actor <name>` (shown
once) — and send it as `Authorization: Bearer <token>`. In Compose:
`docker compose exec agentconnect agentconnect tokens issue --actor ops`.

### A `curl` with `-H "Authorization: Bearer $T"` gets 401 unexpectedly

**Cause:** an unquoted header variable splits on the space between `Bearer` and the token.
**Fix:** quote the whole header: `-H "Authorization: Bearer $T"`.

## Observability

### Herdr provider "failed to start: ... HERDR_SOCKET is unset"

**Cause:** Herdr was enabled without a control socket, and Herdr is not installable here.
**Fix:** this is the intended honest behaviour — the other providers still come up. Use the
**tmux** provider for live terminals; only enable Herdr when you have a real socket. See
[OBSERVABILITY_HERDR.md](OBSERVABILITY_HERDR.md).

### `agentconnect observability providers` shows only `noop`

**Cause:** `AGENTCONNECT_OBSERVABILITY` is unset (the zero-overhead default).
**Fix:** set it, e.g. `AGENTCONNECT_OBSERVABILITY=structured_log,tmux`.

### No tmux panes for agents

**Cause:** `tmux` not on PATH, or looking at the wrong server.
**Fix:** install tmux; the provider uses a dedicated socket — attach with
`tmux -L agentconnect-obs attach` (or the exact line from `agentconnect agents attach`).

## Health-check quick reference

```bash
./deploy/connect-health     # one line per service; exit non-zero if any is down
./deploy/connect-smoke      # full cross-product interaction; exit non-zero on any failure
docker compose logs <service>   # per-service logs when a container is unhealthy
docker compose ps               # health status + port map
```
