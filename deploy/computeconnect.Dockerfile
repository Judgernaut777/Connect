# ComputeConnect compute-plane service (`computeconnect serve`).
#
# Build context is the ComputeConnect repo root. Base install: starlette + uvicorn +
# httpx (declared deps). No torch, no engine — ComputeConnect is a control/placement
# plane in front of an EXTERNAL engine, it never bundles one.
#
# The upstream llama.cpp engine is provided by the host. On Linux the host is reached
# via host.docker.internal (mapped to host-gateway in docker-compose.yml). If that
# engine is not reachable from inside the container (e.g. it is bound to the host's
# loopback only), the control plane still comes up: its simulated-cloud provider stays
# healthy and /health reports "degraded" rather than failing. That is expected and OK.
FROM python:3.11-slim

ENV PIP_NO_CACHE_DIR=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

COPY pyproject.toml README.md LICENSE ./
COPY src ./src

RUN pip install .

# Default upstream; overridden by COMPUTECONNECT_UPSTREAM in the environment.
ENV COMPUTECONNECT_UPSTREAM=http://host.docker.internal:8080

EXPOSE 8090
CMD ["sh", "-c", "exec computeconnect serve --host 0.0.0.0 --port 8090 --upstream \"$COMPUTECONNECT_UPSTREAM\""]
