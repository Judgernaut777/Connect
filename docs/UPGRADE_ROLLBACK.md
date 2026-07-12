# Upgrade & rollback

How to move the ecosystem from one release to the next (RC1 → RC2) and how to get back if a
release misbehaves. The governing principles come from each product's own ADRs; this
document is the cross-product sequencing.

## Before you touch anything

1. **Back up every stateful product** ([BACKUP_RESTORE.md](BACKUP_RESTORE.md)). A rollback
   is only as good as the backup you took before the upgrade.
2. **Record the current versions and commits.** Pin points are the `0.1.0` tags (or commit
   SHAs). Note them so a rollback is a known target, not a guess.
3. **Check compatibility.** [COMPATIBILITY.md](../COMPATIBILITY.md) is keyed on the release
   versions and the verified contracts (MemoryAdapter, LocalComputeProvider, ToolConnect
   decision contract, observability event model). A cross-product upgrade is only safe when
   the contract majors still match — see below.

## The contract-major rule (why staged upgrades are safe)

The seams are versioned, and every client **fails safe on a major it does not recognise**:

- **ToolConnect decision contract** — the governor is pinned to a contract major. A
  ToolConnect that announces a *different* major is read as a **deny**, not an allow. So you
  can upgrade ToolConnect first: worst case, tool authorizations fail closed until
  AgentConnect catches up. Never the other way around.
- **MemoryAdapter** — memory **fails open**: an absent or incompatible BrainConnect degrades
  recall to task-state-only, it never blocks a task. So BrainConnect can be upgraded (or
  briefly down) without stalling AgentConnect.
- **LocalComputeProvider** — an unreachable/incompatible ComputeConnect just leaves the
  `local-manager` worker unusable; other workers are unaffected.

Net: **fail-closed dependency (ToolConnect) first, fail-open dependencies after.**

## Recommended RC1 → RC2 order

1. **ToolConnect** — upgrade the decision point first (it fails closed, so a mismatch is
   safe, not silently permissive). Run `toolconnect verify-audit` after restart.
2. **BrainConnect** — upgrade the ledger. Its schema **migrates forward automatically on
   open** (every `Repo.open()`), so serving the new version against the old DB migrates it.
   *This is why you took a backup:* migration is forward-only.
3. **ComputeConnect** — upgrade the compute plane (near-stateless; only the optional run
   journal persists).
4. **AgentConnect** — upgrade the orchestrator last, once its three dependencies speak the
   new contracts.

Health-gate each step before moving on: `./deploy/connect-health`, then re-run the seam you
just touched. Only proceed when the step is green.

### Docker Compose

```bash
cd Connect/deploy
git -C ../../ToolConnect fetch && git -C ../../ToolConnect checkout <rc2-tag>   # repeat per repo
docker compose build toolconnect && docker compose up -d toolconnect
./connect-health                       # gate
# ...then brainconnect, computeconnect, agentconnect in that order...
./connect-smoke                        # full cross-product gate at the end
```

Rebuild and recreate **one service at a time**, health-gating between each. `depends_on`
healthchecks in the compose file already hold AgentConnect back until BrainConnect and
ToolConnect are healthy.

### Single-venv

Upgrade in place with `pip install -U` (BrainConnect by its distribution name):

```bash
pip install -U "toolconnect==<rc2>"          # then restart toolconnect serve; verify-audit
pip install -U "brainconnect-ai==<rc2>"       # then restart brainconnect serve (DB auto-migrates)
pip install -U "computeconnect==<rc2>"        # then restart computeconnect serve
pip install -U "agentconnect-core==<rc2>" "agentconnect-api==<rc2>" "agentconnect-cli==<rc2>"
```

## Rollback

Because BrainConnect migrations are **forward-only**, a rollback is a **restore**, not a
downgrade of the running DB:

1. Stop the affected service.
2. Reinstall/redeploy the previous pinned version (previous tag / previous image).
3. **Restore that product's pre-upgrade backup** ([BACKUP_RESTORE.md](BACKUP_RESTORE.md)) —
   the old binary must not open a DB a newer binary already migrated.
4. For ToolConnect, run `toolconnect verify-audit` before serving again.
5. Health-gate (`connect-health`) and re-run the smoke (`connect-smoke`).

Roll back in the reverse of the upgrade order (AgentConnect first, ToolConnect last) so the
fail-closed dependency is the last thing you move.

## Sanity gate after any upgrade or rollback

```bash
./deploy/connect-health     # all four up
./deploy/connect-smoke      # capture -> human promote -> recall; authorize allow/deny; placement
```

A green smoke is the definition of "the ecosystem still works end-to-end."
