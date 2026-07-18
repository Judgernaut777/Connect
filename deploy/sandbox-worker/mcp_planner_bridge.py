#!/usr/bin/env python3
"""Serve the AgentConnect planner MCP server with `SandboxedRuntimeWorkerAdapter`
registered alongside whatever workers `service_from_env()` builds from the
environment (echo, and local_model_manager if ComputeConnect is configured).

This is a thin bridge, not a fork of `agentconnect.mcp.server`: it builds the
service exactly the way `agentconnect-mcp` does (`service_from_env()`, so the
same BRAINCONNECT_URL / AGENTCONNECT_COMPUTE_URL / AGENTCONNECT_TOOLCONNECT_URL /
AGENTCONNECT_DB_PATH env wiring applies unchanged), adds one more worker to its
registry, and hands the constructed service to the real
`agentconnect.mcp.server.build_mcp_server(service=...)` / the same transport
selection `main()` uses — no core package is modified or forked.

Run via `run-planner-mcp.sh.template` in this directory (copy it, source
deploy/.env, adjust paths, then exec this module with PYTHONPATH pointed at
this directory so `sandbox_adapter` is importable).
"""

from __future__ import annotations

import logging
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agentconnect.core.bootstrap import service_from_env  # noqa: E402
from agentconnect.mcp.server import build_mcp_server, transport_from_env  # noqa: E402

from sandbox_adapter import SandboxedRuntimeWorkerAdapter  # noqa: E402

_log = logging.getLogger(__name__)


def main() -> None:
    service = service_from_env()
    service.registry.register(SandboxedRuntimeWorkerAdapter())
    _log.info(
        "mcp_planner_bridge: registered sandbox-runtime worker (registry now: %s)",
        sorted(w.worker_id for w in service.registry.all()),
    )

    transport, host, port = transport_from_env()
    if transport == "stdio":
        build_mcp_server(service).run()
        return
    logging.basicConfig(level=logging.INFO)
    _log.info("agentconnect MCP (planner bridge) serving over %s on %s:%s", transport, host, port)
    build_mcp_server(service, host=host, port=port).run(transport=transport)


if __name__ == "__main__":
    main()
