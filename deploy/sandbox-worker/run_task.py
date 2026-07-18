#!/usr/bin/env python3
"""Sandbox-worker entrypoint: run one tool-using AgentConnect task through
``agentconnect.runtime.agent.LangGraphAgentRuntime``, driven by a model reached
over ComputeConnect's OpenAI-compatible endpoint, against the workspace bind-
mounted at /workspace.

Standalone use: run with the defaults below (a hardcoded fizzbuzz task, no
bridge to the AgentConnect router/broker). Dispatched use: the instruction and
model are env-driven (``AGENTCONNECT_TASK_INSTRUCTION`` / ``AGENTCONNECT_WORKER_MODEL``)
so a ``SandboxedRuntimeWorkerAdapter`` on the host can dispatch an arbitrary
subtask's instructions into this container via ``docker run``, and parse the
result back out over stdout.

The final line of stdout is always exactly one machine-parseable line:

    WORKER_RESULT_JSON: {"status": ..., "summary": ..., "changed_artifacts": [...], "usage": ...}

Everything above it is a human-readable trace (safe to show a person, not
meant to be parsed).

No secrets are hardcoded here: CC_API_KEY (if unset) simply results in no
Authorization header being sent to ComputeConnect, which is fine for a
loopback / compose-internal deployment with no token configured. Set
COMPUTECONNECT_TOKEN in deploy/.env and let the launcher/adapter thread it
through as CC_API_KEY when a token is required.
"""

from __future__ import annotations

import json
import os

from agentconnect.common.schemas import AvailableModel, TaskSubmission
from agentconnect.model_manager.backends import OpenAICompatibleBackend
from agentconnect.runtime.agent import LangGraphAgentRuntime, RuntimeConfig

DEFAULT_TASK = (
    "In the current directory, create fizzbuzz.py that prints FizzBuzz for 1..15 "
    "(rules: multiples of 3 -> Fizz, multiples of 5 -> Buzz, multiples of both -> "
    "FizzBuzz, otherwise the number itself, one line per number 1 through 15). "
    "Then run it with `python3 fizzbuzz.py` and confirm the output is correct "
    "before finishing."
)

RESULT_LINE_PREFIX = "WORKER_RESULT_JSON: "


def env(name: str, default: str) -> str:
    val = os.environ.get(name)
    return val if val else default


def main() -> int:
    base_url = env("CC_BASE_URL", "http://computeconnect:8090/v1")
    # Bare token (no "Bearer " prefix) — OpenAICompatibleBackend adds the scheme
    # itself. Empty/unset means no Authorization header is sent at all.
    api_key = os.environ.get("CC_API_KEY") or None
    # AGENTCONNECT_WORKER_MODEL is the dispatched-run name (set by
    # SandboxedRuntimeWorkerAdapter); MODEL_ID is the standalone name (set by
    # run.sh). Either may be present; the dispatched name wins.
    model_id = os.environ.get("AGENTCONNECT_WORKER_MODEL") or env("MODEL_ID", "glm-4.7-flash")
    workspace_root = env("WORKSPACE_ROOT", "/workspace")
    task_id = env("TASK_ID", "sandbox-worker-standalone")
    # AGENTCONNECT_TASK_INSTRUCTION is the dispatched-run name; TASK_TEXT is the
    # older/standalone name.
    task_text = os.environ.get("AGENTCONNECT_TASK_INSTRUCTION") or env("TASK_TEXT", DEFAULT_TASK)
    max_steps = int(env("MAX_STEPS", "12"))
    max_output_tokens = int(env("MAX_OUTPUT_TOKENS", "1200"))

    print(f"[run_task] ComputeConnect base_url={base_url} model_id={model_id}", flush=True)
    print(f"[run_task] workspace_root={workspace_root} task_id={task_id}", flush=True)
    print(f"[run_task] instruction={task_text!r}", flush=True)

    backend = OpenAICompatibleBackend(
        base_url=base_url,
        models=[AvailableModel(model_id=model_id)],
        api_key=api_key,
        timeout=180.0,
    )

    config = RuntimeConfig(
        workspace_root=workspace_root,
        model_id=model_id,
        max_steps=max_steps,
        max_output_tokens=max_output_tokens,
        temperature=0.2,
        allow_shell=True,
        allow_browser=False,
    )

    runtime = LangGraphAgentRuntime(backend, config)
    task = TaskSubmission(task=task_text, agent_type="worker")

    print("[run_task] --- dispatching task to LangGraphAgentRuntime.run() ---", flush=True)
    result = runtime.run(task, task_id=task_id)

    print("\n[run_task] === WorkerResult (human trace) ===", flush=True)
    print(json.dumps(result.model_dump(), indent=2), flush=True)

    print("\n[run_task] === tool trace (WorkerResult.evidence_refs) ===", flush=True)
    for ref in result.evidence_refs:
        print(f"  - {ref}", flush=True)

    usage = result.usage.model_dump() if result.usage is not None else None
    machine_result = {
        "status": result.status,
        "summary": result.summary,
        "changed_artifacts": list(result.changed_artifacts),
        "usage": usage,
    }
    # Exactly one line, exactly this prefix, printed LAST so a caller can safely
    # take the final non-empty line of stdout as the machine-parseable result.
    print(f"\n[run_task] === final status: {result.status} ===", flush=True)
    print(f"{RESULT_LINE_PREFIX}{json.dumps(machine_result)}", flush=True)

    return 0 if result.status == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
