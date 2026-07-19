#!/usr/bin/env bash
# Install the AgentConnect planner-mode slash commands + enforcement hook into ~/.claude.
#
# Prereq (separate): the `agentconnect` MCP server must be registered for your user, e.g.
#   claude mcp add --scope user agentconnect /path/to/agentconnect-mcp-planner.sh
# (that launcher is the one that registers the sandbox-runtime worker — see ../README.md).
#
# Paths: the hook + commands reference the connect-worker layout (flag file under
# $FLAG_DIR, default /home/mini/connect-mcp). Override FLAG_DIR to relocate the mode flag;
# the script rewrites the copied hook + commands to match.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAUDE="${CLAUDE_HOME:-$HOME/.claude}"
FLAG_DIR="${FLAG_DIR:-/home/mini/connect-mcp}"
FLAG="$FLAG_DIR/agentconnect-mode.on"

mkdir -p "$CLAUDE/commands" "$CLAUDE/hooks" "$FLAG_DIR"
cp "$HERE"/commands/*.md "$CLAUDE/commands/"
cp "$HERE"/hooks/agentconnect-mode-guard.sh "$CLAUDE/hooks/"
chmod +x "$CLAUDE/hooks/agentconnect-mode-guard.sh"

# Relocate the flag path if FLAG_DIR was overridden (default already matches the files).
if [ "$FLAG" != "/home/mini/connect-mcp/agentconnect-mode.on" ]; then
  sed -i "s#/home/mini/connect-mcp/agentconnect-mode.on#$FLAG#g" \
    "$CLAUDE/hooks/agentconnect-mode-guard.sh" \
    "$CLAUDE/commands/agentconnectmode.md" "$CLAUDE/commands/agentconnectmode-off.md"
fi

# Merge the PreToolUse guard into settings.json (idempotent).
S="$CLAUDE/settings.json"; [ -f "$S" ] || echo '{}' > "$S"
if jq -e '.hooks.PreToolUse[]? | .hooks[]? | select(.command|test("agentconnect-mode-guard"))' "$S" >/dev/null 2>&1; then
  echo "PreToolUse guard already present in $S"
else
  tmp=$(mktemp)
  jq --arg cmd "$CLAUDE/hooks/agentconnect-mode-guard.sh" \
    '.hooks.PreToolUse = ((.hooks.PreToolUse // []) + [{"matcher":"*","hooks":[{"type":"command","command":$cmd}]}])' \
    "$S" > "$tmp" && mv "$tmp" "$S"
  echo "installed PreToolUse guard into $S"
fi

echo
echo "Installed: /agentconnect, /agentconnectmode, /agentconnectmode-off + the guard hook."
echo "Start a NEW Claude Code session (or run /hooks) to load them. Flag file: $FLAG"
