# Sandbox worker: a host-sandboxed AgentConnect tool-using worker.
#
# A container that runs agentconnect.runtime.agent.LangGraphAgentRuntime against a
# model reached through ComputeConnect's OpenAI-compatible endpoint, doing real
# file/shell tool use in a shared workspace bind-mounted at /workspace.
#
# Build needs network (installs the runtime's [worker] extra + langgraph from PyPI);
# the three local agentconnect-* packages are copied in from a local checkout of the
# mcp-agentconnect monorepo (they are not published to PyPI), staged into the build
# context by run.sh from $MONOREPO_DIR/packages.
#
# Runtime is intended to be launched read-only + non-root (see run.sh): this image
# does not need to write anywhere except /workspace (bind mount) and /tmp (tmpfs).

FROM python:3.11-slim

# --- Build stage (root): install dependencies from the local package sources ---
WORKDIR /build

COPY agentconnect-core/ /build/agentconnect-core/
COPY agentconnect-model-manager/ /build/agentconnect-model-manager/
COPY agentconnect-runtime/ /build/agentconnect-runtime/

RUN pip install --no-cache-dir \
        /build/agentconnect-core \
        /build/agentconnect-model-manager \
        "/build/agentconnect-runtime[worker]" \
    && rm -rf /build

# --- Application code ---
RUN mkdir -p /app
COPY run_task.py /app/run_task.py

# --- Non-root user (uid 10001), matching the sandboxed run profile in run.sh ---
RUN useradd --uid 10001 --create-home --shell /usr/sbin/nologin worker

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    HOME=/tmp

WORKDIR /workspace

USER 10001

ENTRYPOINT ["python", "/app/run_task.py"]
