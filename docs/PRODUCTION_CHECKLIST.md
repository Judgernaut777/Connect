# Production deployment checklist

A pre-flight list for putting the Connect ecosystem in front of real work. Every item maps
to something verified in this cycle; the deep guides are linked. Treat unchecked boxes as
blockers, not suggestions.

## 1. Artifacts & install

- [ ] Each product pinned to `0.1.0` (or a specific commit SHA), not a floating branch.
- [ ] BrainConnect installed as **`brainconnect-ai`** (never `pip install brainconnect` bare).
- [ ] Combined install verified: `pip check` clean. (Verified here: 86 packages, zero
      conflicts, in one Python 3.11 venv.)
- [ ] If deploying with [deploy/](../deploy/): `docker compose build` succeeds for all four
      images and `docker compose up -d` brings all four to **healthy**.

## 2. Secrets & configuration

- [ ] `.env` created from `.env.example` with **real** `BRAINCONNECT_TOKEN` and
      `TOOLCONNECT_AUTH_TOKEN` (generate with `python -c "import secrets;print(secrets.token_urlsafe(32))"`).
- [ ] No placeholder token survives (`grep replace-with .env` returns nothing).
- [ ] `.env` is not committed and is `chmod 600`.
- [ ] AgentConnect wired to its peers via `BRAINCONNECT_URL`(+token), `AGENTCONNECT_COMPUTE_URL`,
      `AGENTCONNECT_TOOLCONNECT_URL`(+token). `GET /health` shows `memory_backend=brainconnect`
      and worker `local-manager`.
- [ ] `AGENTCONNECT_TOOLCONNECT_MODE` set deliberately: **`required`** (fail-closed) for prod.

## 3. Data paths & persistence

- [ ] BrainConnect points at a **dedicated** `BRAINCONNECT_DB` (never the developer's real
      `~/.wiki-brain/wiki.db`).
- [ ] AgentConnect `AGENTCONNECT_DB_PATH` and `AGENTCONNECT_ARTIFACT_DIR` on persistent
      storage (a named volume in Compose).
- [ ] ToolConnect `--db` on persistent storage; started with an explicit `--policies` file.
- [ ] ComputeConnect `--run-journal` set if you need restart reconciliation.

## 4. Security boundaries ([SECURITY_BOUNDARIES.md](SECURITY_BOUNDARIES.md))

- [ ] No service on a non-loopback interface **without** a token (ToolConnect enforces this;
      apply it to all four).
- [ ] TLS + primary rate limiting at a reverse proxy in front of the stack.
- [ ] Agents run under real OS isolation if untrusted — Connect is compliance, **not** a sandbox.
- [ ] BrainConnect MCP `--review` mode is **not** exposed to any agent (human gate).
- [ ] DB files and artifact dir protected by filesystem permissions / disk encryption.

## 5. Policy (ToolConnect)

- [ ] Cedar policy reviewed: it is **default-deny**; every intended tool has an explicit
      `permit`, and sensitive/write tools are asserted with honest descriptors.
- [ ] `toolconnect serve` starts cleanly (an unparseable policy refuses to start — good).

## 6. Observability ([OBSERVABILITY.md](OBSERVABILITY.md))

- [ ] `AGENTCONNECT_OBSERVABILITY` set for the worker type you run: `tmux` for terminal
      agents, `structured_log` (JSONL) and/or `otlp` for non-terminal.
- [ ] `AGENTCONNECT_OBSERVABILITY_FAILURE_POLICY` chosen (advisory vs task_blocking vs
      startup_fatal).
- [ ] Herdr: understood as **OFF pending an installable Herdr**
      ([OBSERVABILITY_HERDR.md](OBSERVABILITY_HERDR.md)); tmux is the live provider.
- [ ] `agentconnect observability providers` reports the providers you expect as `available`.

## 7. Backups ([BACKUP_RESTORE.md](BACKUP_RESTORE.md))

- [ ] Scheduled backups for AgentConnect (DB **and** artifact dir), BrainConnect, ToolConnect.
- [ ] A restore has been **tested**, not just configured.
- [ ] `toolconnect verify-audit` runs on a schedule (exit 1 on a broken chain).

## 8. Upgrade/rollback readiness ([UPGRADE_ROLLBACK.md](UPGRADE_ROLLBACK.md))

- [ ] Current versions/commits recorded.
- [ ] Team knows the order: upgrade ToolConnect → BrainConnect → ComputeConnect →
      AgentConnect; roll back in reverse; rollback = **restore a backup** (migrations are
      forward-only).

## 9. Final gate

- [ ] `./deploy/connect-health` — all four up.
- [ ] `./deploy/connect-smoke` — **6/6 pass** (capture → human promote → recall; authorize
      allow + deny; placement decision). A green smoke is the go/no-go signal.
- [ ] The one honest caveat is understood: ComputeConnect reports **`degraded`** in a
      container when the host engine is loopback-bound and unreachable — expected, not a
      failure. Run ComputeConnect with host networking or a reachable engine if you need
      real placement.
