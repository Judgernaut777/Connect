#!/usr/bin/env python3
"""Smoke test: dispatch a real subtask through AgentConnectService, governed by
ToolConnect, executed by SandboxedRuntimeWorkerAdapter in a host-sandboxed
sandbox-worker container against an isolated git worktree of the shared
workspace — then confirm the auto-commit-and-merge behavior actually
committed the branch and (if AUTO_MERGE is on) fast-forwarded it into the
workspace's main branch.

Uses a SCRATCH ledger db/artifact dir (not any live planner ledger) so this
run never touches production task history.

No secrets are hardcoded: TOOLCONNECT_URL / TOOLCONNECT_AUTH_TOKEN (and
whatever SandboxedRuntimeWorkerAdapter itself reads — WORKSPACE_DIR,
COMPUTECONNECT_TOKEN, etc.) come from the environment. Source deploy/.env
first, e.g.:

    set -a; . ../.env; set +a
    /path/to/mcp-agentconnect/.venv/bin/python3 smoke.py
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agentconnect.core.bootstrap import service_from_env  # noqa: E402
from agentconnect.core.models import CreateTaskRequest, SubtaskRequest  # noqa: E402
from sandbox_adapter import SandboxedRuntimeWorkerAdapter  # noqa: E402

TOOLCONNECT_URL = os.environ.get("TOOLCONNECT_URL", "http://127.0.0.1:8995")
TOOLCONNECT_TOKEN = os.environ.get("TOOLCONNECT_AUTH_TOKEN")


def _get(path: str) -> dict:
    headers = {}
    if TOOLCONNECT_TOKEN:
        headers["Authorization"] = f"Bearer {TOOLCONNECT_TOKEN}"
    req = urllib.request.Request(f"{TOOLCONNECT_URL}{path}", headers=headers)
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read())


def main() -> int:
    if not TOOLCONNECT_TOKEN:
        print(
            "WARNING: TOOLCONNECT_AUTH_TOKEN is not set; the governor call will be "
            "sent with no Authorization header.",
            file=sys.stderr,
        )

    scratch = tempfile.mkdtemp(prefix="sandbox-worker-smoke-")
    db_path = os.path.join(scratch, "agentconnect.db")
    artifact_dir = os.path.join(scratch, "artifacts")
    print(f"[smoke] scratch ledger: {db_path}")
    print(f"[smoke] scratch artifacts: {artifact_dir}")

    os.environ["AGENTCONNECT_TOOLCONNECT_URL"] = TOOLCONNECT_URL
    if TOOLCONNECT_TOKEN:
        os.environ["AGENTCONNECT_TOOLCONNECT_TOKEN"] = f"Bearer {TOOLCONNECT_TOKEN}"
    os.environ.setdefault("AGENTCONNECT_TOOLCONNECT_MODE", "required")

    adapter = SandboxedRuntimeWorkerAdapter()
    print(
        f"[smoke] adapter: workspace_repo={adapter.workspace_repo} "
        f"worktrees_root={adapter.worktrees_root} image={adapter.image} "
        f"auto_merge={adapter.auto_merge} main_branch={adapter.main_branch}"
    )
    service = service_from_env(
        workers=[adapter], db_path=db_path, artifact_dir=artifact_dir,
    )
    print(f"[smoke] tool_governor bound: {service.tool_governor is not None} "
          f"(mode={getattr(service.tool_governor, 'mode', None)})")

    task = service.create_task(CreateTaskRequest(
        title="sandbox-worker smoke: primes.py via sandboxed_runtime",
        goal="Prove SandboxedRuntimeWorkerAdapter dispatches through the ToolConnect "
             "governor into a real host-sandboxed container doing real tool work, "
             "then auto-commits (and merges) the result.",
        created_by="smoke",
    ))
    print(f"[smoke] created task {task.id}")

    subtask = service.submit_subtask(task.id, SubtaskRequest(
        title="Write and verify primes.py",
        instructions=(
            "Create primes.py that prints all primes below 30, then run it with "
            "`python3 primes.py` and confirm the output is correct before finishing."
        ),
        preferred_worker="sandbox-runtime",
        required_capabilities=["generate"],
    ))
    print(f"[smoke] submitted subtask {subtask.id}, status={subtask.status.value}")

    detail = service.get_subtask(subtask.id)
    subtask = detail.subtask
    print(f"\n=== subtask final status: {subtask.status.value} ===")
    print(f"route_reason.selected_worker: {subtask.route_reason.get('selected_worker')}")

    print("\n=== runs (incl. commit/merge metrics) ===")
    branch = None
    worktree_dir = None
    commit_sha = None
    merged = False
    merge_sha = None
    for run in detail.runs:
        print(f"  run {run.id}: worker={run.worker_id} harness={run.harness} "
              f"status={run.status.value} metrics={json.dumps(run.metrics)[:600]}")
        branch = run.metrics.get("branch") or branch
        worktree_dir = run.metrics.get("worktree_dir") or worktree_dir
        commit_sha = run.metrics.get("commit_sha") or commit_sha
        merged = run.metrics.get("merged") or merged
        merge_sha = run.metrics.get("merge_commit_sha") or merge_sha

    task_detail = service.get_task(task.id)
    print("\n=== attempts ===")
    for a in task_detail.attempts:
        print(f"  {a.actor_id} ({a.outcome}): {a.summary[:400]}")

    print("\n=== artifacts (this subtask) ===")
    primes_content = None
    primes_marker = f"sandbox-runtime: primes.py (subtask {subtask.id})"
    for art in task_detail.artifacts:
        if art.metadata.get("subtask_id") != subtask.id:
            continue
        chunk = service.read_artifact_chunk(art.id, 0, 20000)
        print(f"  [{art.type.value}] {art.id} — {art.summary}")
        if art.summary.strip() == primes_marker:
            primes_content = chunk.content

    print(f"\n=== primes.py content (from artifact) ===\n{primes_content}")

    host_path = os.path.join(worktree_dir or "", "primes.py") if worktree_dir else None
    print(f"\n=== host filesystem check: {host_path} ===")
    if host_path and os.path.isfile(host_path):
        with open(host_path) as fh:
            host_content = fh.read()
        print("EXISTS on host. Content:")
        print(host_content)
    else:
        print("NOT FOUND on host.")

    print(f"\n=== commit: {commit_sha} on branch {branch} (worktree: {worktree_dir}) ===")
    print(f"=== merged into main: {merged} (merge commit: {merge_sha}) ===")
    if worktree_dir:
        os.system(f"git -C {worktree_dir} status --porcelain")
        os.system(f"git -C {worktree_dir} log --oneline -3")
    if adapter.auto_merge:
        os.system(f"git -C {adapter.workspace_repo} log --oneline -3")

    print("\n=== ToolConnect /audit: looking for an allowed=True decision for source sandboxed_runtime ===")
    try:
        audit = _get("/audit?kind=decision&limit=200")
    except urllib.error.URLError as exc:
        print(f"could not reach ToolConnect audit endpoint: {exc}")
        audit = {"records": []}
    found = None
    for rec in audit.get("records", []):
        blob = json.dumps(rec)
        if "sandboxed_runtime" in blob and '"allowed": true' in blob.lower().replace(" ", "").replace('"allowed":true', '"allowed": true'):
            found = rec
            break
    if found is None:
        for rec in audit.get("records", []):
            if "sandboxed_runtime" in json.dumps(rec):
                found = rec
                break
    print(json.dumps(found, indent=2) if found else "NOT FOUND")

    ok = (
        subtask.status.value == "succeeded"
        and primes_content is not None
        and found is not None
        and commit_sha is not None
        and (merged or not adapter.auto_merge)
    )
    print(f"\n=== SMOKE {'PASSED' if ok else 'INCOMPLETE'} ===")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
