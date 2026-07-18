"""Bridge AgentConnect's core `WorkerAdapter` interface to the sandbox-worker
container (see `Dockerfile` / `run_task.py` in this directory).

`SandboxedRuntimeWorkerAdapter.run()` is called by `AgentConnectService._execute`
*after* the ToolConnect governor has already authorized this worker's declared
tool set (see `capabilities().tools` / `capabilities().harness`) — this module
does no governance of its own, it only does the dispatch:

  1. `git worktree add` an isolated checkout of the shared workspace repo, on a
     new branch `acw/<subtask_id>`, so concurrent subtasks never collide and a
     subtask's changes are inspectable/mergeable independent of any other run.
  2. grant the sandboxed container's non-root uid write access to that worktree
     (POSIX ACL, additive — mirrors `run.sh`'s treatment of the shared
     workspace).
  3. `docker run --rm` the sandbox-worker image against that worktree with the
     same sandbox flags (read-only rootfs, non-root uid, all capabilities
     dropped, no-new-privileges, no host network beyond the compose network),
     passing the subtask's instructions and the requested model as env vars.
  4. parse the single `WORKER_RESULT_JSON: ` line the container prints, capture
     every file the run changed (plus the full diff) as durable ledger artifacts
     via `context.create_artifact`, and reduce all of it to a core `WorkerResult`.

Auto-commit-and-merge (on a subtask that succeeded, i.e. the container reported
`status == "completed"`):

  5. `git add -A` + `git commit` the worktree onto its `acw/<subtask_id>` branch,
     under a dedicated committer identity, so the work is a real commit rather
     than dirty files.
  6. When `AUTO_MERGE` is on (the default), merge that branch into the shared
     workspace's main branch: fast-forward when possible, otherwise a `--no-ff`
     merge commit. On a merge CONFLICT this never forces anything — the merge is
     aborted, the branch is left intact and unmerged, and a warning is recorded
     on the returned `WorkerResult` ("branch acw/<id> not merged: conflict with
     main, needs manual resolution"). The subtask's own `status` still reflects
     whether the *work* succeeded; a merge conflict is reported as a warning,
     not a failure — nothing is ever force-pushed or force-merged, so no work is
     ever lost.

A subtask that FAILED (container status != "completed") is never committed or
merged — its worktree is left exactly as the container left it, for a human to
inspect.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import uuid
from typing import Any, Optional

from agentconnect.core.models import (
    ArtifactType,
    FilesystemAccess,
    PrivacyTier,
    SandboxSpec,
    WorkerLocation,
)
from agentconnect.core.workers import (
    WorkerAdapter,
    WorkerArtifactRef,
    WorkerCapabilities,
    WorkerContext,
    WorkerResult,
)

RESULT_LINE_PREFIX = "WORKER_RESULT_JSON: "

# All defaults below are overridable via env or constructor kwargs. The literal
# defaults are this project's own conventions (host paths, image tag, network
# name) — not secrets — so they are safe to ship, and every one of them can be
# repointed for a different host/deployment without touching code.
DEFAULT_WORKSPACE_REPO = os.environ.get("WORKSPACE_DIR", "/home/mini/connect-workspace")
DEFAULT_WORKTREES_ROOT = os.environ.get(
    "WORKTREES_DIR", "/home/mini/connect-workspace-worktrees"
)
DEFAULT_IMAGE = os.environ.get("CONNECT_WORKER_IMAGE", "connect-worker:m1")
DEFAULT_NETWORK = os.environ.get("CONNECT_NETWORK", "connect_default")
DEFAULT_CONTAINER_UID = int(os.environ.get("CONTAINER_UID", "10001"))
DEFAULT_MODEL = os.environ.get("SANDBOX_WORKER_MODEL", "glm-4.7-flash")
# Compose-internal URL the *container* uses to reach ComputeConnect (not the
# host-loopback URL other scripts in this directory use).
DEFAULT_COMPUTE_BASE_URL = os.environ.get(
    "COMPUTECONNECT_CONTAINER_URL", "http://computeconnect:8090/v1"
)
DEFAULT_MEMORY = os.environ.get("SANDBOX_MEMORY_LIMIT", "2g")
DEFAULT_TIMEOUT_SECONDS = int(os.environ.get("SANDBOX_TIMEOUT_SECONDS", "600"))
DEFAULT_MAIN_BRANCH = os.environ.get("WORKSPACE_MAIN_BRANCH", "main")
DEFAULT_COMMITTER_NAME = os.environ.get("ACW_COMMITTER_NAME", "agentconnect-worker")
DEFAULT_COMMITTER_EMAIL = os.environ.get("ACW_COMMITTER_EMAIL", "worker@connect.local")


def _env_flag(name: str, default: bool) -> bool:
    val = os.environ.get(name)
    if val is None or val.strip() == "":
        return default
    return val.strip().lower() not in ("0", "false", "no", "off")


def _run(cmd: list[str], **kwargs: Any) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, **kwargs)


class SandboxedRuntimeWorkerAdapter(WorkerAdapter):
    """A core `WorkerAdapter` that dispatches to a host-sandboxed docker container
    running `agentconnect.runtime.agent.LangGraphAgentRuntime`, doing real tool
    work (shell/file read/write/generate) in an isolated git worktree of the
    shared workspace repo, then auto-commits (and, by default, merges) the
    result."""

    def __init__(
        self,
        *,
        worker_id: str = "sandbox-runtime",
        workspace_repo: str = DEFAULT_WORKSPACE_REPO,
        worktrees_root: str = DEFAULT_WORKTREES_ROOT,
        image: str = DEFAULT_IMAGE,
        network: str = DEFAULT_NETWORK,
        container_uid: int = DEFAULT_CONTAINER_UID,
        model: str = DEFAULT_MODEL,
        compute_base_url: str = DEFAULT_COMPUTE_BASE_URL,
        # Bare token (no "Bearer " prefix — run_task.py's backend adds the
        # scheme). Defaults from COMPUTECONNECT_TOKEN in the environment
        # (deploy/.env); unset means the container sends no Authorization
        # header at all, which is fine for a loopback dev deployment.
        compute_api_key: Optional[str] = None,
        memory: str = DEFAULT_MEMORY,
        timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
        auto_merge: Optional[bool] = None,
        main_branch: str = DEFAULT_MAIN_BRANCH,
        committer_name: str = DEFAULT_COMMITTER_NAME,
        committer_email: str = DEFAULT_COMMITTER_EMAIL,
    ) -> None:
        self._worker_id = worker_id
        self.workspace_repo = workspace_repo
        self.worktrees_root = worktrees_root
        self.image = image
        self.network = network
        self.container_uid = container_uid
        self.model = model
        self.compute_base_url = compute_base_url
        self.compute_api_key = (
            compute_api_key
            if compute_api_key is not None
            else os.environ.get("COMPUTECONNECT_TOKEN") or None
        )
        self.memory = memory
        self.timeout_seconds = timeout_seconds
        # AUTO_MERGE default on, matching the M2 handoff: config flag, env
        # overridable, explicit constructor arg wins over env.
        self.auto_merge = _env_flag("AUTO_MERGE", True) if auto_merge is None else auto_merge
        self.main_branch = main_branch
        self.committer_name = committer_name
        self.committer_email = committer_email

    @property
    def worker_id(self) -> str:
        return self._worker_id

    def capabilities(self) -> WorkerCapabilities:
        return WorkerCapabilities(
            worker_id=self._worker_id,
            harness="sandboxed_runtime",
            model=self.model,
            tools=["generate", "write_file", "read_file", "run_shell"],
            sandbox=SandboxSpec(
                filesystem=FilesystemAccess.workspace_write, network=True, shell=True
            ),
            # Everything happens inside a host-sandboxed, non-root, read-only-rootfs
            # container on the operator's own box, reaching only ComputeConnect over
            # the compose-internal network — nothing leaves the host. Eligible for
            # every privacy tier a local worker can honestly serve.
            privacy_tiers=list(PrivacyTier),
            capability_tags=["generate", "code", "edit", "shell"],
            location=WorkerLocation.local,
            cost_per_1k_tokens_usd=0.0,
            requires_approval=False,
        )

    # ------------------------------------------------------------------ run
    def run(self, subtask: Any, context: WorkerContext) -> WorkerResult:
        subtask_id = subtask.id
        branch = f"acw/{subtask_id}"
        worktree_dir = os.path.join(self.worktrees_root, subtask_id)
        model = (subtask.metadata or {}).get("model") or self.model

        warnings: list[str] = []

        worktree_err = self._create_worktree(branch, worktree_dir)
        if worktree_err:
            return WorkerResult(status="failed", summary=worktree_err, error=worktree_err)

        acl_warning = self._grant_container_access(worktree_dir)
        if acl_warning:
            warnings.append(acl_warning)

        try:
            proc = self._run_container(worktree_dir, subtask.instructions, model)
        except subprocess.TimeoutExpired:
            summary = (
                f"sandboxed_runtime container timed out after {self.timeout_seconds}s "
                f"(branch {branch}, worktree {worktree_dir} left in place)"
            )
            return WorkerResult(status="failed", summary=summary, error="timeout")

        container_result = self._parse_result_line(proc.stdout)
        if container_result is None:
            tail = "\n".join(proc.stdout.strip().splitlines()[-40:])
            summary = (
                f"sandboxed_runtime container produced no parseable "
                f"{RESULT_LINE_PREFIX.strip()} line (exit={proc.returncode}); "
                f"branch {branch} / worktree {worktree_dir} left in place for inspection"
            )
            err = f"stdout tail:\n{tail}\n\nstderr tail:\n{proc.stderr[-2000:]}"
            return WorkerResult(status="failed", summary=summary, error=err, warnings=warnings)

        container_status = container_result.get("status")
        container_summary = container_result.get("summary") or ""
        usage = container_result.get("usage") or {}

        artifact_refs, diff_text, changed_paths = self._capture_worktree_changes(
            worktree_dir, context, subtask_id
        )

        succeeded = container_status == "completed"

        # --- auto-commit-and-merge (only ever runs for a succeeded subtask) ---
        commit_sha: Optional[str] = None
        commit_error: Optional[str] = None
        merged = False
        merge_sha: Optional[str] = None
        merge_warning: Optional[str] = None

        if succeeded and changed_paths:
            commit_sha, commit_error = self._commit_worktree(
                worktree_dir, branch, subtask_id, container_summary
            )
            if commit_error:
                warnings.append(commit_error)
            elif commit_sha and self.auto_merge:
                merged, merge_sha, merge_warning = self._merge_into_main(branch, subtask_id)
                if merge_warning:
                    warnings.append(merge_warning)

        if not succeeded:
            files_note = (
                f"Changed files: {', '.join(changed_paths)}."
                if changed_paths
                else "No files were changed in the worktree."
            )
            merge_note = (
                f"{files_note} Subtask failed; branch {branch} left uncommitted in "
                f"worktree {worktree_dir} for inspection (no commit/merge attempted)."
            )
        elif not changed_paths:
            merge_note = f"No files were changed; nothing to commit on branch {branch}."
        elif commit_error:
            merge_note = (
                f"Changed files: {', '.join(changed_paths)}. Commit FAILED on branch "
                f"{branch}: {commit_error}. Worktree {worktree_dir} left for inspection."
            )
        elif commit_sha is None:
            # git add -A staged nothing (e.g. changes net out to no diff vs HEAD).
            merge_note = (
                f"Changed files: {', '.join(changed_paths)}, but nothing was staged "
                f"(no net change); nothing committed on branch {branch}."
            )
        elif merged:
            merge_note = (
                f"Committed {commit_sha[:12]} on branch {branch} "
                f"({', '.join(changed_paths)}) and merged into {self.main_branch} "
                f"({merge_sha[:12] if merge_sha else '?'})."
            )
        elif self.auto_merge:
            merge_note = (
                f"Committed {commit_sha[:12]} on branch {branch} "
                f"({', '.join(changed_paths)}); NOT merged ({merge_warning})."
            )
        else:
            merge_note = (
                f"Committed {commit_sha[:12]} on branch {branch} "
                f"({', '.join(changed_paths)}); AUTO_MERGE is off, left on the branch "
                f"for review."
            )

        summary = f"{container_summary} {merge_note}".strip()

        metrics: dict[str, Any] = dict(usage)
        metrics["changed_file_count"] = len(changed_paths)
        metrics["branch"] = branch
        metrics["worktree_dir"] = worktree_dir
        metrics["container_exit_code"] = proc.returncode
        metrics["container_status"] = container_status
        metrics["commit_sha"] = commit_sha
        metrics["auto_merge"] = self.auto_merge
        metrics["merged"] = merged
        metrics["merge_commit_sha"] = merge_sha
        metrics["main_branch"] = self.main_branch

        return WorkerResult(
            status="succeeded" if succeeded else "failed",
            summary=summary,
            artifacts=artifact_refs,
            metrics=metrics,
            warnings=warnings,
            error=None if succeeded else (container_result.get("error") or "worker reported failure"),
        )

    # ------------------------------------------------------------ internals
    def _create_worktree(self, branch: str, worktree_dir: str) -> Optional[str]:
        os.makedirs(self.worktrees_root, exist_ok=True)
        if os.path.exists(worktree_dir):
            return f"worktree dir already exists: {worktree_dir}"
        proc = _run(
            ["git", "-C", self.workspace_repo, "worktree", "add", "-b", branch, worktree_dir, "HEAD"]
        )
        if proc.returncode != 0:
            return f"git worktree add failed (branch {branch}): {proc.stderr.strip()}"
        return None

    def _grant_container_access(self, worktree_dir: str) -> Optional[str]:
        if shutil.which("setfacl"):
            proc = _run(
                [
                    "setfacl", "-R",
                    "-m", f"u:{self.container_uid}:rwx",
                    "-m", f"d:u:{self.container_uid}:rwx",
                    worktree_dir,
                ]
            )
            if proc.returncode != 0:
                return f"setfacl failed on {worktree_dir}: {proc.stderr.strip()}"
            return None
        # Fallback, matching run.sh's fallback for hosts without ACLs.
        proc = _run(["chmod", "-R", "o+w", worktree_dir])
        if proc.returncode != 0:
            return f"chmod fallback failed on {worktree_dir}: {proc.stderr.strip()}"
        return "setfacl not found; used chmod o+w fallback (world-writable worktree)"

    def _run_container(
        self, worktree_dir: str, instructions: str, model: str
    ) -> subprocess.CompletedProcess:
        cmd = [
            "docker", "run", "--rm",
            "--network", self.network,
            "-v", f"{worktree_dir}:/workspace",
            "--read-only",
            "--tmpfs", "/tmp",
            "--user", str(self.container_uid),
            "--cap-drop", "ALL",
            "--security-opt", "no-new-privileges",
            "--memory", self.memory,
            "--workdir", "/workspace",
            "-e", f"CC_BASE_URL={self.compute_base_url}",
        ]
        if self.compute_api_key:
            cmd += ["-e", f"CC_API_KEY={self.compute_api_key}"]
        cmd += [
            "-e", f"AGENTCONNECT_WORKER_MODEL={model}",
            "-e", f"AGENTCONNECT_TASK_INSTRUCTION={instructions}",
            "-e", f"TASK_ID=acw-{uuid.uuid4().hex[:12]}",
            self.image,
        ]
        return _run(cmd, timeout=self.timeout_seconds)

    @staticmethod
    def _parse_result_line(stdout: str) -> Optional[dict[str, Any]]:
        for line in reversed(stdout.splitlines()):
            line = line.strip()
            if line.startswith(RESULT_LINE_PREFIX):
                try:
                    return json.loads(line[len(RESULT_LINE_PREFIX):])
                except json.JSONDecodeError:
                    return None
        return None

    def _capture_worktree_changes(
        self, worktree_dir: str, context: WorkerContext, subtask_id: str
    ) -> tuple[list[WorkerArtifactRef], str, list[str]]:
        """Stage new files intent-to-add (`git add -N`, no content, no commit) so
        `git diff` and `git diff --name-only` report untracked files too, then read
        each changed file's current content off disk into a durable artifact."""
        _run(["git", "-C", worktree_dir, "add", "-A", "-N"])
        name_proc = _run(["git", "-C", worktree_dir, "diff", "--name-only"])
        changed_paths = [p for p in name_proc.stdout.splitlines() if p.strip()]

        diff_proc = _run(["git", "-C", worktree_dir, "diff"])
        diff_text = diff_proc.stdout

        artifact_refs: list[WorkerArtifactRef] = []
        for rel_path in changed_paths:
            abs_path = os.path.join(worktree_dir, rel_path)
            if not os.path.isfile(abs_path):
                continue  # deleted file: no content to snapshot, it's in the diff
            try:
                with open(abs_path, encoding="utf-8", errors="replace") as fh:
                    content = fh.read()
            except OSError as exc:
                content = f"[could not read {rel_path}: {exc}]"
            artifact = context.create_artifact(
                type=ArtifactType.worker_output,
                content=content,
                summary=f"sandbox-runtime: {rel_path} (subtask {subtask_id})",
            )
            artifact_refs.append(
                WorkerArtifactRef(
                    artifact_id=artifact.id,
                    type=ArtifactType.worker_output,
                    description=f"Contents of {rel_path} as left in the worktree",
                )
            )

        if diff_text.strip():
            diff_artifact = context.create_artifact(
                type=ArtifactType.patch,
                content=diff_text,
                summary=f"sandbox-runtime: full git diff for subtask {subtask_id}",
            )
            artifact_refs.append(
                WorkerArtifactRef(
                    artifact_id=diff_artifact.id,
                    type=ArtifactType.patch,
                    description="Full git diff of the worktree changes",
                )
            )

        return artifact_refs, diff_text, changed_paths

    def _commit_env(self) -> dict[str, str]:
        env = dict(os.environ)
        env.update(
            {
                "GIT_AUTHOR_NAME": self.committer_name,
                "GIT_AUTHOR_EMAIL": self.committer_email,
                "GIT_COMMITTER_NAME": self.committer_name,
                "GIT_COMMITTER_EMAIL": self.committer_email,
            }
        )
        return env

    def _commit_worktree(
        self, worktree_dir: str, branch: str, subtask_id: str, container_summary: str
    ) -> tuple[Optional[str], Optional[str]]:
        """`git add -A` + commit everything the container left in the worktree,
        under the adapter's dedicated committer identity. Returns
        `(commit_sha, error)`; `(None, None)` means there was nothing to commit
        (not an error)."""
        add = _run(["git", "-C", worktree_dir, "add", "-A"])
        if add.returncode != 0:
            return None, f"git add -A failed in {worktree_dir}: {add.stderr.strip()}"

        staged = _run(["git", "-C", worktree_dir, "diff", "--cached", "--quiet"])
        if staged.returncode == 0:
            return None, None  # nothing staged

        subject_line = (container_summary or "sandbox-runtime changes").strip().splitlines()
        subject = (subject_line[0] if subject_line else "sandbox-runtime changes")[:200]
        message = f"acw {subtask_id}: {subject}"
        if container_summary and container_summary.strip() != subject:
            message += f"\n\n{container_summary.strip()}"

        commit = _run(
            ["git", "-C", worktree_dir, "commit", "-m", message],
            env=self._commit_env(),
        )
        if commit.returncode != 0:
            return None, f"git commit failed on branch {branch}: {commit.stderr.strip()}"

        sha_proc = _run(["git", "-C", worktree_dir, "rev-parse", "HEAD"])
        sha = sha_proc.stdout.strip() if sha_proc.returncode == 0 else None
        return sha, None

    def _merge_into_main(
        self, branch: str, subtask_id: str
    ) -> tuple[bool, Optional[str], Optional[str]]:
        """Merge `branch` into `self.main_branch` in the shared workspace repo's
        primary checkout (not a worktree). Fast-forwards when possible, else
        creates a `--no-ff` merge commit. On any conflict this NEVER forces
        anything: the merge is aborted and both branches are left exactly as
        they were. Returns `(merged, merge_commit_sha, warning)`."""
        current = _run(["git", "-C", self.workspace_repo, "rev-parse", "--abbrev-ref", "HEAD"])
        current_branch = current.stdout.strip()
        if current.returncode != 0 or current_branch != self.main_branch:
            return False, None, (
                f"branch {branch} not merged: workspace repo's primary checkout is "
                f"not on {self.main_branch!r} (on {current_branch!r} or unreadable); "
                f"needs manual merge"
            )

        ff = _run(["git", "-C", self.workspace_repo, "merge", "--ff-only", branch])
        if ff.returncode == 0:
            sha = _run(["git", "-C", self.workspace_repo, "rev-parse", "HEAD"]).stdout.strip()
            return True, sha or None, None

        no_ff = _run(
            [
                "git", "-C", self.workspace_repo, "merge", "--no-ff", branch,
                "-m", f"Merge {branch} into {self.main_branch} (acw {subtask_id})",
            ],
            env=self._commit_env(),
        )
        if no_ff.returncode == 0:
            sha = _run(["git", "-C", self.workspace_repo, "rev-parse", "HEAD"]).stdout.strip()
            return True, sha or None, None

        # Conflict (or some other non-fast-forward failure): never force it.
        # Abort cleanly so main and the branch are both left exactly as they
        # were before this merge attempt — no work is ever lost.
        _run(["git", "-C", self.workspace_repo, "merge", "--abort"])
        warning = (
            f"branch {branch} not merged: conflict with {self.main_branch}, "
            f"needs manual resolution"
        )
        return False, None, warning
