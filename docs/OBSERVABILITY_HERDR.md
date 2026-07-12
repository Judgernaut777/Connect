# Herdr visibility — honest status

**Short version:** the working live-terminal provider on this host is **tmux**. AgentConnect
also ships a **Herdr** provider, but it is **flag-gated OFF** because Herdr itself is not
installable in this environment. This document is deliberately honest about that seam so
nobody wires a dashboard that cannot exist yet.

## What Herdr is meant to be

Herdr is a multi-terminal "herding" viewer — one place to watch many live agent panes.
AgentConnect's observability layer is provider-neutral (see
[OBSERVABILITY.md](OBSERVABILITY.md)), and Herdr is one such provider: when enabled and
given a control socket, AgentConnect drives it as the live-terminal surface instead of (or
alongside) tmux.

## Why it is OFF here

Herdr is not installable on this box, so the provider cannot connect to anything. The design
choice is to make that **loud, not silent**: the Herdr provider only activates when you both
enable it and hand it a socket, and if you enable it without a socket it refuses with an
actionable message rather than pretending to work. Verified:

```console
$ AGENTCONNECT_OBSERVABILITY=structured_log,tmux,herdr \
  AGENTCONNECT_OBSERVABILITY_HERDR_ENABLED=1 \
  agentconnect observability providers
observability provider 'herdr' failed to start: Herdr provider enabled but
AGENTCONNECT_OBSERVABILITY_HERDR_SOCKET is unset; nothing to connect to.
[
  { "provider": "structured_log", "available": true, ... },
  { "provider": "tmux",           "available": true, "detail": "tmux 3.3a" }
]
```

Note what happened: Herdr announced its own failure with a clear reason, and the other two
providers came up fine. Under the default `advisory` failure policy a missing Herdr never
blocks agent work.

## The exact command to enable it (when you have a Herdr)

On a host where Herdr is installed and listening on a control socket:

```bash
export AGENTCONNECT_OBSERVABILITY=structured_log,herdr        # or tmux,herdr to run both
export AGENTCONNECT_OBSERVABILITY_HERDR_ENABLED=1
export AGENTCONNECT_OBSERVABILITY_HERDR_SOCKET=/run/herdr.sock   # <-- your real socket path
agentconnect observability providers    # herdr should now report available=true
```

Both flags are required: `AGENTCONNECT_OBSERVABILITY` must list `herdr` **and**
`AGENTCONNECT_OBSERVABILITY_HERDR_ENABLED` must be truthy **and**
`AGENTCONNECT_OBSERVABILITY_HERDR_SOCKET` must point at a live socket. Miss any one and the
provider stays inert (with the message above if the enable flag is set without a socket).

## Recommendation

Until a Herdr is installable here, **use the tmux provider** for live terminals and
`structured_log` (JSONL) or `otlp` for non-terminal workers. Everything you would want from a
Herdr wall — per-agent panes, attach, bounded redacted output — is already available through
tmux + `agentconnect agents attach|output`. Treat Herdr as a drop-in upgrade for the same
event stream, not a prerequisite.
