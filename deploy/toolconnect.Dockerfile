# ToolConnect tool-governance decision point (`toolconnect serve`).
#
# Build context is the ToolConnect repo root. Base install pulls cedarpy (prebuilt
# aarch64 wheels). `serve` requires an explicit Cedar policy file and a DB path; the
# policy is mounted read-only from deploy/policies.cedar and the DB lives on a volume.
#
# ToolConnect refuses a non-loopback bind without a token, so a bearer token
# (TOOLCONNECT_AUTH_TOKEN) is mandatory here — the container binds 0.0.0.0 so the
# other compose services can reach it.
FROM python:3.11-slim

ENV PIP_NO_CACHE_DIR=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

COPY pyproject.toml README.md LICENSE ./
COPY src ./src

RUN pip install .

RUN useradd --create-home --uid 10001 appuser
# Own /data so the non-root process can create the SQLite DB on the (root-owned by
# default) named volume.
RUN mkdir -p /data && chown appuser:appuser /data
USER appuser

EXPOSE 8095
# Policy is mounted at /etc/toolconnect/policy.cedar (see docker-compose.yml).
CMD ["sh", "-c", "exec toolconnect serve --db /data/toolconnect.db --policies /etc/toolconnect/policy.cedar --host 0.0.0.0 --port 8095"]
