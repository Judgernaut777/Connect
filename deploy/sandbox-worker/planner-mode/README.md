# AgentConnect planner mode — slash commands + enforcement hook

Turn a Claude Code session into a **planner that can only plan and delegate through
AgentConnect** — enforced by a hook, not just asked for. Pairs with the sandbox worker
in `../` (a `submit_subtask` runs host-sandboxed on the compute engine, in a git worktree
of the shared workspace, auto-committed + merged).

## What's here
- `commands/agentconnect.md` — `/agentconnect <goal>`: one-shot. Plan + delegate a goal in
  the current session (session keeps its normal tools).
- `commands/agentconnectmode.md` — `/agentconnectmode`: **enter enforced mode**. Sets a flag
  file; the hook then denies every tool except `mcp__agentconnect__*`, `Read/Glob/Grep`,
  `TodoWrite`, `AskUserQuestion`, `ToolSearch`. Persists until you exit.
- `commands/agentconnectmode-off.md` — `/agentconnectmode-off`: remove the flag, restore tools.
- `hooks/agentconnect-mode-guard.sh` — the `PreToolUse` guard. No-op when the flag is absent;
  when present, allows only the planner tool set and denies the rest (Edit/Write/Bash/Task/…).
  `Task`/Explore is intentionally denied — Explore subagents can run Bash, which would tunnel
  around the isolation; the planner grounds via Read/Grep instead.

## Install
```bash
./install.sh          # copies commands + hook into ~/.claude, merges the PreToolUse hook into settings.json
# override the flag location if your layout differs:
FLAG_DIR=/somewhere/writable ./install.sh
```
Then **start a new Claude Code session** (or run `/hooks`) so the commands + hook load.

Separately register the MCP server that carries the sandbox worker (once):
```bash
claude mcp add --scope user agentconnect /home/mini/connect-mcp/agentconnect-mcp-planner.sh
```

## Gotchas (learned the hard way)
- The flag file must **not** live under `~/.claude/` — Claude Code blocks writes there as
  "sensitive," which breaks the command's `!touch`. Default is `/home/mini/connect-mcp/`.
- Editing `agentconnect-mode-guard.sh` takes effect immediately (the hook re-runs it per tool
  call); editing the command `.md` files or the `settings.json` hook wiring needs a new session
  or `/hooks`.
- The flag is global to your user (all your sessions), not per-session. `/agentconnectmode-off`
  (or deleting the flag file) clears it everywhere.
- For delegation to actually run, the Connect stack + the compute engine must be up, and the
  target repo must be reachable by the sandbox worker (it worktrees off `WORKSPACE_DIR`, default
  the shared `~/connect-workspace` — point it at another repo to work there).
