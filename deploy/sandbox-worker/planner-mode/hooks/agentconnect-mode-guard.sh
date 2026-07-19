#!/usr/bin/env bash
# PreToolUse guard: when AgentConnect planner mode is ON (flag file present),
# allow ONLY AgentConnect MCP tools + read-only inspection; deny everything else
# (Edit/Write/Bash/Task/other MCP) so the session can only plan + delegate.
FLAG="/home/mini/connect-mcp/agentconnect-mode.on"
[ -f "$FLAG" ] || exit 0            # mode OFF -> allow everything, no interference
input=$(cat)
tool=$(printf '%s' "$input" | python3 -c "import sys,json;print(json.load(sys.stdin).get('tool_name',''))" 2>/dev/null)
cmd=$(printf '%s' "$input" | python3 -c "import sys,json;print((json.load(sys.stdin).get('tool_input') or {}).get('command',''))" 2>/dev/null)
case "$tool" in
  mcp__agentconnect__*|Read|Glob|Grep|TodoWrite|AskUserQuestion|ToolSearch) exit 0 ;;   # allowed: delegate + read-only planning
  Bash)
    # toggle exemption: the on/off commands must be able to touch/rm the flag even in mode
    case "$cmd" in *agentconnect-mode.on*) exit 0 ;; esac ;;
esac
# deny anything else, with a clear reason
printf '%s\n' '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"AgentConnect planner mode: this session is isolated to AgentConnect. Do the work by delegating via mcp__agentconnect__* (submit_subtask to sandbox-runtime), not by editing/running files yourself. Run /agentconnectmode-off to exit."}}'
exit 0
