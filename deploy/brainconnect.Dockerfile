# BrainConnect memory-ledger HTTP service (`brainconnect serve`).
#
# Build context is the WikiBrain repo root. The PyPI distribution name is
# `brainconnect-ai`; the import package and console command are both `brainconnect`.
# Base install only — the heavy optional extras (semantic/whisper/docs/safety-all,
# i.e. torch, sentence-transformers, onnxruntime) are deliberately NOT installed.
#
# Only the files the wheel build needs are copied, to keep the image lean:
#   pyproject.toml + cli/ (package-dir = cli) + README.md (readme) + LICENSE.
FROM python:3.11-slim

ENV PIP_NO_CACHE_DIR=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

COPY pyproject.toml README.md LICENSE ./
COPY cli ./cli

# Installs the `brainconnect` (zero-model CLI) and `brainconnect-librarian` scripts.
RUN pip install .

RUN mkdir -p /data
# BRAINCONNECT_DB points the ledger at a scratch volume path, never the host's
# real ~/.wiki-brain/wiki.db. `serve` requires the DB to exist, so init-if-absent.
ENV BRAINCONNECT_DB=/data/brain.db

RUN useradd --create-home --uid 10001 appuser
USER appuser

EXPOSE 8787
# init the ledger on first boot (idempotent), then serve on all interfaces so the
# other compose services can reach it. Token comes from BRAINCONNECT_TOKEN.
CMD ["sh", "-c", "test -f \"$BRAINCONNECT_DB\" || brainconnect init; exec brainconnect serve --host 0.0.0.0 --port 8787 --token \"$BRAINCONNECT_TOKEN\""]
