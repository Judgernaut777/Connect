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

COPY packages/agentconnect-core   /src/agentconnect-core
COPY packages/agentconnect-router /src/agentconnect-router
COPY packages/agentconnect-api    /src/agentconnect-api
COPY packages/agentconnect-cli    /src/agentconnect-cli

# Install core first so the api's `agentconnect-core==0.1.0` pin resolves locally.
# agentconnect-core declares httpx>=0.27 (its memory/compute/ToolConnect clients need
# it), so a base install reaches the sibling services without any extra pin here.
# agentconnect-router is required at import time by the api's /route/decide route
# (agentconnect.api.routes_route -> agentconnect.router.routing), so install it too.
RUN pip install /src/agentconnect-core \
 && pip install /src/agentconnect-router \
 && pip install /src/agentconnect-api /src/agentconnect-cli

ENV AGENTCONNECT_DB_PATH=/data/agentconnect.db \
    AGENTCONNECT_ARTIFACT_DIR=/data/artifacts \
    AGENTCONNECT_API_HOST=0.0.0.0 \
    AGENTCONNECT_API_PORT=8790

RUN useradd --create-home --uid 10001 appuser
# Own /data (ledger + artifacts) so the non-root process can write the (root-owned
# by default) named volume.
RUN mkdir -p /data/artifacts && chown -R appuser:appuser /data
USER appuser

EXPOSE 8790
CMD ["agentconnect-api"]
