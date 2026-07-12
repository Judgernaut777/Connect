# Backup & restore

Every stateful Connect product has an online backup and a restore path. There is **no
shared database** — each product owns its own store — so back up each one on its own
schedule. All commands below were run from the published CLIs on this host; the exact
output is shown.

| Product | Store | Backup | Restore |
|---|---|---|---|
| AgentConnect | ledger SQLite (`AGENTCONNECT_DB_PATH`) + artifact dir | `agentconnect backup <dest>` | `agentconnect restore <src>` |
| BrainConnect | ledger SQLite (`BRAINCONNECT_DB`) | `brainconnect backup --out <path>` | `brainconnect restore --from <path>` |
| ToolConnect | decision/audit SQLite (`--db`) | `toolconnect backup --db <db> --out <path>` | copy the snapshot back (see below) |

ComputeConnect is effectively stateless — its only durable state is the optional
`--run-journal` SQLite used for restart reconciliation; snapshot that file if you set one.

## AgentConnect

Online, consistent snapshot of the ledger (safe while `agentconnect-api` is running):

```console
$ agentconnect backup /backups/agentconnect-$(date +%F).db
{ ... "sessions": 0 }          # 266240 bytes written
```

Restore overwrites the live ledger — stop the API first, then:

```bash
agentconnect restore /backups/agentconnect-2026-07-12.db
```

Back up the **artifact directory** (`AGENTCONNECT_ARTIFACT_DIR`, default
`~/.agentconnect/artifacts`) alongside the DB — artifact bodies live on disk, not in the
ledger. A plain `tar` or `rsync` of that directory is enough; it is content-addressed.

## BrainConnect

WAL-safe snapshot to a single file (safe while `brainconnect serve` is running):

```console
$ brainconnect backup --out /backups/brain-$(date +%F).db
backup: wrote /backups/brain-2026-07-12.db (217088 bytes, integrity=ok, schema v9)
  contents: claims=1, memory_candidates=1, sources=1, recall_feedback=0
```

The backup verifies its own SQLite integrity and reports the schema version and row
counts, so a backup that silently truncated is caught at write time. Restore replaces the
live ledger and first snapshots the current state to `<db>.pre-restore`:

```bash
# stop `brainconnect serve` first
brainconnect restore --from /backups/brain-2026-07-12.db
```

## ToolConnect

Consistent snapshot; it also **checks the audit hash chain** as it writes, so a backup is
only produced from an untampered database:

```console
$ toolconnect backup --db /var/lib/toolconnect/toolconnect.db --out /backups/tc-$(date +%F).db
backed up ... -> /backups/tc-2026-07-12.db (audit chain ok=True, records=7)
```

Verify any database (live or a restored copy) independently:

```console
$ toolconnect verify-audit --db /backups/tc-2026-07-12.db
audit chain OK (7 records)          # exit 0; exit 1 if the chain is broken
```

To restore, stop `toolconnect serve`, copy the snapshot into place as the `--db` path, and
run `toolconnect verify-audit --db <path>` before serving again — a restored decision point
must prove its audit chain before it starts making decisions.

## Docker Compose

In the [deploy/](../deploy/) stack each store lives on a named volume
(`brainconnect-data`, `toolconnect-data`, `agentconnect-data`). Back up by running the same
CLI **inside the container** and copying the file out, e.g.:

```bash
docker compose exec brainconnect brainconnect backup --out /data/brain-backup.db
docker cp connect-brainconnect-1:/data/brain-backup.db ./brain-backup.db
```

`docker compose down` keeps volumes; `docker compose down -v` destroys them — take a backup
first if you mean to keep the data.

## Schedule

- Back up each product on its own cron; stagger them so you never snapshot mid-cross-call.
- Keep AgentConnect's DB and artifact dir in the **same** backup window — they reference
  each other.
- Periodically run `toolconnect verify-audit` and `brainconnect backup` (which self-checks
  integrity) against your newest backups; an untested backup is a guess.
