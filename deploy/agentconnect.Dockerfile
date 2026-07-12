# AgentConnect API service (the task backplane's HTTP adapter).
#
# Build context is the mcp-agentconnect repo root (set in docker-compose.yml), so
# the COPY paths below are repo-relative. We install three of the nine AC packages:
#   - agentconnect-core  (the service, memory/compute/toolconnect clients live here)
#   - agentconnect-api   (the FastAPI adapter + the `agentconnect-api` entrypoint)
#   - agentconnect-cli   (the `agentconnect` operator CLI — needed so an operator can
#                         `agentconnect tokens issue` inside the container; the smoke
#                         test mints its bearer token that way)
# This is the base install: no Temporal, no Linear, no torch. core==0.1.0 is resolved
# from the local path, never from PyPI.
FROM python:3.11-slim

ENV PIP_NO_CACHE_DIR=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

COPY packages/agentconnect-core /src/agentconnect-core
COPY packages/agentconnect-api  /src/agentconnect-api
COPY packages/agentconnect-cli  /src/agentconnect-cli

# Install core first so the api's `agentconnect-core==0.1.0` pin resolves locally.
#
# httpx is added explicitly: agentconnect-core's three HTTP clients (memory adapter,
# ComputeConnect provider, ToolConnect governor) all `import httpx` lazily, but the
# package declares only pydantic + pyyaml — so a base `agentconnect-api` install
# cannot reach BrainConnect/ComputeConnect/ToolConnect over the network without it.
# (In a combined venv this is masked because ComputeConnect depends on httpx.)
# Deploy-layer workaround for a missing runtime dependency in agentconnect-core;
# reported upstream. Pin matches ComputeConnect's floor (httpx>=0.27).
RUN pip install /src/agentconnect-core \
 && pip install /src/agentconnect-api /src/agentconnect-cli "httpx>=0.27"

RUN mkdir -p /data/artifacts
ENV AGENTCONNECT_DB_PATH=/data/agentconnect.db \
    AGENTCONNECT_ARTIFACT_DIR=/data/artifacts \
    AGENTCONNECT_API_HOST=0.0.0.0 \
    AGENTCONNECT_API_PORT=8790

EXPOSE 8790
CMD ["agentconnect-api"]
