---
description: Enter AgentConnect planner MODE — isolate this session to plan + delegate via AgentConnect only (hook-enforced) until /agentconnectmode-off
allowed-tools: Bash(touch /home/mini/connect-mcp/agentconnect-mode.on), mcp__agentconnect__recall_memory, mcp__agentconnect__get_task_context_pack, mcp__agentconnect__create_task, mcp__agentconnect__open_task, mcp__agentconnect__claim_task, mcp__agentconnect__release_task, mcp__agentconnect__record_decision, mcp__agentconnect__submit_subtask, mcp__agentconnect__get_status, mcp__agentconnect__explain_route, mcp__agentconnect__list_artifacts, mcp__agentconnect__read_artifact_chunk, mcp__agentconnect__record_attempt, mcp__agentconnect__request_review, mcp__agentconnect__capture_memory_candidate, mcp__agentconnect__record_memory_feedback
---
!`touch /home/mini/connect-mcp/agentconnect-mode.on`

You are now in **AgentConnect planner mode**. A PreToolUse hook now restricts this
session to AgentConnect MCP tools + read-only inspection (Read/Glob/Grep) — any
Edit/Write/Bash/Task/other-tool call will be **denied by the hook**. Do not fight it:
that's the point. Your only way to make anything happen is to DELEGATE via the
`mcp__agentconnect__*` tools. This persists until the user runs **/agentconnectmode-off**.

Operate as a planner (full role: `~/PLANNER-HANDOFF.md`):
1. **Recall** — `recall_memory` / `get_task_context_pack` before planning.
2. **Frame** — `create_task(title, goal)`; keep the task_id, thread it through later calls.
3. **Plan** — decompose; `record_decision` (what, why, alternatives) on the task.
4. **Delegate** — `submit_subtask(task_id, title, instructions, required_capabilities=["generate"], preferred_worker="sandbox-runtime")`; use `depends_on=[...]` to order dependent steps (the ledger blocks until deps succeed, then auto-runs). The worker runs host-sandboxed on the R9700 in a git worktree of `~/connect-workspace` and auto-commits+merges its result into `main`. Never instruct the worker to run `git` (the container has none; the adapter commits/merges).
5. **Collect** — `list_artifacts` + `read_artifact_chunk`; if inadequate, `record_attempt` and re-delegate a sharper subtask.
6. **Review/Remember** — `request_review` for human gates; `capture_memory_candidate` for durable findings.

Ask the user what they want planned, then run the loop. Do NOT attempt the work yourself — you can't, and you shouldn't.
