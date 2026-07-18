# sandbox-worker — a host-sandboxed AgentConnect tool-using worker (M1/M2)

A `WorkerAdapter` that lets AgentConnect delegate real tool work — writing files,
running shell commands, generating code — to a host-sandboxed Docker container,
instead of only the built-in `echo` / single-shot-generation workers. Each subtask
runs in its own isolated `git worktree` of a shared workspace repo, and (this is
the M2 auto-commit-and-merge addition) a *succeeded* subtask's changes are
committed to a per-subtask branch and, by default, merged back into the
workspace's main branch.

Two milestones landed here:

- **M1** — prove a container can be sandboxed (non-root uid, read-only rootfs, all
  capabilities dropped, no-new-privileges, no host network beyond the compose
  network) and still do real file/shell work against a bind-mounted workspace.
  (`Dockerfile`, `run_task.py`, `run.sh`.)
- **M2** — bridge that container to AgentConnect's core `WorkerAdapter` interface
  so a real subtask, governed by ToolConnect, routes into it
  (`sandbox_adapter.py`, `mcp_planner_bridge.py`, `register_toolconnect.py`,
  `smoke.py`), plus auto-commit-and-merge so a successful subtask's work lands as
  a real commit instead of being left dirty.

## Design

```
AgentConnectService._execute()
  -> ToolConnect governor authorizes sandboxed_runtime's declared tools
  -> SandboxedRuntimeWorkerAdapter.run(subtask, context)
       1. git worktree add -b acw/<subtask_id>  (isolated checkout, off the
          shared workspace repo's HEAD — concurrent subtasks never collide)
       2. grant the container's non-root uid write access to that worktree
          (setfacl, additive; chmod o+w fallback if setfacl is unavailable)
       3. docker run --rm <image>   (read-only rootfs, --user <uid>,
          --cap-drop ALL, --security-opt no-new-privileges, workspace bind-
          mounted at /workspace, ComputeConnect reachable over the compose
          network only)
            -> run_task.py drives agentconnect.runtime.agent.LangGraphAgentRuntime
               against a model reached through ComputeConnect's OpenAI-compatible
               endpoint, doing real tool use in /workspace
            -> prints exactly one `WORKER_RESULT_JSON: {...}` line on stdout
       4. capture every changed file (+ the full diff) as durable ledger
          artifacts via context.create_artifact
       5. if the container reported status == "completed":
            git add -A + git commit on acw/<subtask_id>, under a dedicated
            committer identity (ACW_COMMITTER_NAME / ACW_COMMITTER_EMAIL)
       6. if AUTO_MERGE is on (default) and step 5 committed something:
            merge acw/<subtask_id> into WORKSPACE_MAIN_BRANCH in the shared
            workspace repo's primary checkout — fast-forward if possible,
            else a --no-ff merge commit
       7. reduce all of it to a core WorkerResult (status/summary/artifacts/
          metrics/warnings/error)
```

### Auto-commit-and-merge semantics

- A subtask that **succeeded** (container status `completed`) with changed files:
  commits the worktree onto `acw/<subtask_id>`. If `AUTO_MERGE` is on, then tries
  to merge that branch into `WORKSPACE_MAIN_BRANCH` (default `main`):
  - **Fast-forward** if main hasn't moved since the branch was cut.
  - Otherwise a **`--no-ff` merge commit**.
  - On a **conflict** (or any other non-fast-forward failure): the merge is
    **aborted**, never forced. The branch is left intact and unmerged. The
    `WorkerResult` still reports `status="succeeded"` for the work itself, but
    carries a warning: `"branch acw/<id> not merged: conflict with main, needs
    manual resolution"`. No work is ever lost — the commit and the branch stay
    exactly as they were.
  - If `AUTO_MERGE` is off: commit only, branch is left for manual review.
- A subtask that **failed** (container status != `completed`, timed out, or
  produced no parseable result line): **never** committed or merged. The
  worktree is left exactly as the container left it, for a human to inspect.
- `WorkerResult.metrics` always carries `branch`, `worktree_dir`, `commit_sha`
  (`None` if nothing was committed), `auto_merge`, `merged`, `merge_commit_sha`,
  and `main_branch`, so a caller can inspect the outcome without parsing the
  summary text.

### Committer identity

Commits (and merge commits) are made under a dedicated identity —
`agentconnect-worker <worker@connect.local>` by default — set via
`GIT_AUTHOR_NAME`/`GIT_AUTHOR_EMAIL`/`GIT_COMMITTER_NAME`/`GIT_COMMITTER_EMAIL`
for just that `git commit`/`git merge` subprocess call, so it never touches your
own global/repo git config. Override with `ACW_COMMITTER_NAME` /
`ACW_COMMITTER_EMAIL`.

### ToolConnect governance

`sandbox_adapter.py` does no governance itself — by the time `.run()` is called,
`AgentConnectService._execute` has already asked the ToolConnect governor to
authorize this worker's declared tools (`capabilities().tools` /
`capabilities().harness`). `register_toolconnect.py` seeds ToolConnect's catalog
with the `sandboxed_runtime` source and its four tools
(`generate`/`write_file`/`read_file`/`run_shell`), each asserted
`effect=write, reversible=false, asserted_by=operator` — the same shape
`local_model_manager` is registered with, so no policy change is needed beyond
what a `principal.privacy_tier == "local"` widen rule already permits (see
`../policies.cedar`).

## Files

| File | What it is |
|---|---|
| `Dockerfile` | Sandbox worker image: `agentconnect-core`/`-model-manager`/`-runtime[worker]` installed from a local monorepo checkout, non-root uid 10001 |
| `run_task.py` | The container's entrypoint: drives `LangGraphAgentRuntime` against ComputeConnect, prints `WORKER_RESULT_JSON: {...}` |
| `sandbox_adapter.py` | `SandboxedRuntimeWorkerAdapter` — the core `WorkerAdapter` bridge, worktree + sandbox dispatch + auto-commit-and-merge |
| `mcp_planner_bridge.py` | Serves the AgentConnect MCP server with `SandboxedRuntimeWorkerAdapter` registered alongside `service_from_env()`'s usual workers |
| `register_toolconnect.py` | One-time (idempotent) ToolConnect catalog seed for the `sandboxed_runtime` source |
| `run.sh` | Build the image + a host-sandboxed standalone proof run (sandbox flags, then the default fizzbuzz task) |
| `smoke.py` | End-to-end smoke test: real subtask -> ToolConnect governor -> sandboxed container -> commit -> merge, against a scratch ledger |
| `run-planner-mcp.sh.template` | Launcher template for the MCP server wrapper (copy it, fill in paths, never commit a filled-in copy) |
| `README.md` | This file |

## Running it

Everything reads its secrets from the environment — nothing here has a
hardcoded token. Source `../.env` (copy `../.env.example` first if you haven't)
before running anything that talks to BrainConnect/ComputeConnect/ToolConnect:

```bash
cd deploy
cp .env.example .env && $EDITOR .env   # if you haven't already for the main stack
set -a; . ./.env; set +a
```

1. **Build + sandbox-proof the image** (needs a local checkout of
   `mcp-agentconnect` — set `MONOREPO_DIR` if it's not a sibling of `Connect/`):

   ```bash
   cd sandbox-worker
   MONOREPO_DIR=/path/to/mcp-agentconnect WORKSPACE_DIR=/path/to/connect-workspace ./run.sh
   ```

   This builds `connect-worker:m1` (override with `CONNECT_WORKER_IMAGE`), proves
   the sandbox flags (uid, read-only rootfs, workspace write), then runs the
   default fizzbuzz task standalone (no AgentConnect ledger involved).

2. **Register the `sandboxed_runtime` source with ToolConnect** (once per
   ToolConnect deployment):

   ```bash
   python3 register_toolconnect.py
   ```

3. **Run the end-to-end smoke test** (real subtask through the ledger, governor,
   sandboxed container, commit, merge):

   ```bash
   /path/to/mcp-agentconnect/.venv/bin/python3 smoke.py
   ```

   Uses a scratch ledger db/artifact dir, so it never touches a live planner's
   task history. It prints the commit sha, whether the merge landed, and the
   resulting `git log` on both the worktree and (if `AUTO_MERGE` is on) the
   workspace's main branch.

4. **Wire it into an MCP client**: copy `run-planner-mcp.sh.template` to e.g.
   `~/connect-mcp/run-planner-mcp.sh`, set `CONNECT_DEPLOY_DIR` /
   `SANDBOX_WORKER_DIR` / `MCP_AGENTCONNECT_VENV` for your host, `chmod +x` it,
   and point your MCP client at the copy. It sources `../.env` for secrets and
   never inlines a token.

## Configuration reference

All of `sandbox_adapter.py`'s host paths/names are environment-overridable
(see `../.env.example` for the full list with defaults):
`WORKSPACE_DIR`, `WORKTREES_DIR`, `CONNECT_WORKER_IMAGE`, `CONNECT_NETWORK`,
`COMPUTECONNECT_CONTAINER_URL`, `CONTAINER_UID`, `AUTO_MERGE`,
`WORKSPACE_MAIN_BRANCH`, `ACW_COMMITTER_NAME`, `ACW_COMMITTER_EMAIL`,
`SANDBOX_WORKER_MODEL`, `SANDBOX_MEMORY_LIMIT`, `SANDBOX_TIMEOUT_SECONDS`. The
one secret it reads is `COMPUTECONNECT_TOKEN` (bare, no `Bearer ` prefix — it's
threaded into the container as `CC_API_KEY`, and `run_task.py`'s
`OpenAICompatibleBackend` adds the scheme itself); unset means the container
sends no `Authorization` header, which is fine for a token-free loopback/compose
deployment.

## Relationship to any existing loose-file deployment

This directory is the canonical, secret-free, GitHub-ready copy of the M1/M2
design. If you already have a loose-file deployment of an earlier version of
this worker (e.g. under `~/connect-worker` / `~/connect-mcp`) pointed at by a
running MCP client, it is **not** touched or repointed by anything in this
directory — that's a deliberate, separate step for whenever you're ready to
switch a live deployment over to the repo-tracked copy.
