#!/usr/bin/env python3
"""Seed ToolConnect with the `sandboxed_runtime` source.

Mirrors exactly how `local_model_manager` is registered against a running
ToolConnect deployment: source_id=sandboxed_runtime, tier=known,
transport=push, tools generate/write_file/read_file/run_shell each asserted
effect=write, reversible=false, asserted_by=operator.

  POST /sources            {source_id, tier, transport}
  POST /sources/{sid}/tools {tools: [{name}, ...]}     (push-style ingest)
  POST /assertions          {source_id, name, descriptor}   (one per tool)

Every asserted tool is effect=write, reads=[], writes=[] (so `reads_sensitive`
and `external_sink` are both false), reversible=false, asserted_by="operator".
That is exactly the shape a Cedar policy's "local-manager-generate-write"
widen rule for `principal.privacy_tier == "local"` already permits (see
`deploy/policies.cedar`) — no policy change needed; this script only
populates the catalog + assertions, same as local_model_manager's.

Idempotent: `register_source`/`ingest_payload`/`assert_tool` all overwrite
rather than error on a pre-existing source_id, so running this twice is safe.

Reads TOOLCONNECT_URL / TOOLCONNECT_AUTH_TOKEN from the environment — no
token is hardcoded. Source deploy/.env (or export the vars yourself) before
running this script.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request

BASE_URL = os.environ.get("TOOLCONNECT_URL", "http://127.0.0.1:8995")
TOKEN = os.environ.get("TOOLCONNECT_AUTH_TOKEN")

SOURCE_ID = "sandboxed_runtime"
TOOLS = ["generate", "write_file", "read_file", "run_shell"]


def _call(method: str, path: str, body: dict | None = None) -> dict:
    data = json.dumps(body or {}).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"
    req = urllib.request.Request(f"{BASE_URL}{path}", data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        print(f"HTTP {exc.code} on {method} {path}: {exc.read().decode()}", file=sys.stderr)
        raise


def main() -> int:
    if not TOKEN:
        print(
            "WARNING: TOOLCONNECT_AUTH_TOKEN is not set; requests will be sent with no "
            "Authorization header. Set it (see deploy/.env) if ToolConnect requires auth.",
            file=sys.stderr,
        )

    print(f"--- registering source {SOURCE_ID!r} ---")
    print(_call("POST", "/sources", {
        "source_id": SOURCE_ID, "tier": "known", "transport": "push",
        "declares": TOOLS,
    }))

    print(f"--- pushing tool declarations for {SOURCE_ID!r} ---")
    print(_call("POST", f"/sources/{SOURCE_ID}/tools", {
        "tools": [{"name": name} for name in TOOLS],
    }))

    print("--- asserting each tool (effect=write, reversible=false, asserted_by=operator) ---")
    for name in TOOLS:
        result = _call("POST", "/assertions", {
            "source_id": SOURCE_ID, "name": name,
            "descriptor": {
                "effect": "write",
                "reads": [],
                "writes": [],
                "scopes": [],
                "reversible": False,
                "idempotent": False,
                "requires_approval": False,
                "declassifies": False,
                "asserted_by": "operator",
            },
        })
        print(f"  {name}: {result}")

    print(f"\ndone. verify with: curl -H 'Authorization: Bearer <TOOLCONNECT_AUTH_TOKEN>' {BASE_URL}/catalog")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
