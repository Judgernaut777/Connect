---
description: Plan a goal and delegate execution to AgentConnect (host-sandboxed workers on the R9700)
argument-hint: <goal to accomplish>
allowed-tools: mcp__agentconnect__recall_memory, mcp__agentconnect__get_task_context_pack, mcp__agentconnect__create_task, mcp__agentconnect__open_task, mcp__agentconnect__claim_task, mcp__agentconnect__release_task, mcp__agentconnect__record_decision, mcp__agentconnect__submit_subtask, mcp__agentconnect__get_status, mcp__agentconnect__explain_route, mcp__agentconnect__list_artifacts, mcp__agentconnect__read_artifact_chunk, mcp__agentconnect__record_attempt, mcp__agentconnect__request_review, mcp__agentconnect__capture_memory_candidate, mcp__agentconnect__record_memory_feedback
---

Act as an AgentConnect PLANNER for this goal:

**$ARGUMENTS**

Do NOT do the work yourself with your own Edit/Write/Bash. Plan it, then DELEGATE every
unit of work through the `mcp__agentconnect__*` tools. Full role: `~/PLANNER-HANDOFF.md`.

Run this loop:
1. **Recall** — `recall_memory` (and `get_task_context_pack` if a task exists) for prior knowledge.
2. **Frame** — `create_task(title, goal)`; keep the returned task_id and thread it through every later call.
3. **Plan** — decompose into subtasks; `record_decision` on the task (what, why, alternatives).
4. **Delegate** — for each unit: `submit_subtask(task_id, title, instructions, required_capabilities=["generate"], preferred_worker="sandbox-runtime")`. Use `depends_on=[<subtask_id>...]` to order dependent steps — the ledger blocks a subtask until its deps succeed, then auto-runs it. The worker runs host-sandboxed on the R9700 in a git worktree of `~/connect-workspace` and auto-commits+merges its result into `main`.
5. **Collect** — on success, `list_artifacts` + `read_artifact_chunk` to read the output; if inadequate, `record_attempt` and re-delegate a sharper subtask (don't do it yourself).
6. **Govern/Review** — a subtask blocked by ToolConnect is policy, not a bug; use `request_review` for a human gate on anything consequential.
7. **Remember** — `capture_memory_candidate` for durable findings (lands in BrainConnect as pending; humans promote to trusted).

Never instruct the worker to run `git` (commit/branch/merge) — the container has no git and doesn't need it; the adapter commits the worktree and merges into `main` automatically on success. Just tell the worker to create/edit/run files in the current directory. Also: `submit_subtask`'s `filesystem` arg, if set, takes the enum member `workspace_write` (not "workspace"/"rw").

What AgentConnect CAN do: real generation + tool use (shell/fs) in the sandboxed worker — analysis, code, edits, running commands, tests — committed to the shared repo. What it CANNOT: anything outside that sandbox/workspace or a non-loopback network. For side-effecting steps beyond the workspace, delegate the *generation* of the artifact and say who applies it.

If **$ARGUMENTS** is empty, ask what goal to plan, then run the loop.
