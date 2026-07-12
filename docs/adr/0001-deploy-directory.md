# ADR 0001 — Connect may carry a `deploy/` directory (config + scripts, not product code)

- Status: Accepted (ratified by the Lead, 2026-07-12)
- Context: Connect is the documentation umbrella for the four-product ecosystem
  (AgentConnect, BrainConnect, ComputeConnect, ToolConnect). Its founding rule
  ([CONTRIBUTING.md](../../CONTRIBUTING.md)) is **docs only — no code**: product code
  lives in the product repositories, and Connect never becomes a place where a
  cross-product claim can drift from the thing it describes.

## Decision

Connect may host a single `deploy/` directory containing **deployment configuration
and scripts**, and nothing else:

- Dockerfiles (one per product), each installing that product **from its published
  repository** into a lean `python:3.11-slim` image.
- A `docker-compose.yml` wiring the four services together over one network.
- Shell scripts for operations: `connect-health` and `connect-smoke`.
- A Cedar policy file for the ToolConnect service (`policies.cedar`).
- An environment template with **safe placeholders** (`.env.example`).

What `deploy/` must **not** contain: Python product or library code, business logic,
or anything that reimplements a product. A Dockerfile that `pip install`s a product is
configuration; a `.py` that patches a product's behaviour is not, and does not belong
here. The products remain the single source of truth for their own code.

## Consequences

- The umbrella can now answer "how do I run all four at once?" with a recipe that is
  **executed, not imagined** — the binding rule for every recipe in these docs is that
  it was run from the published artifacts and passed.
- There is exactly one deployment definition for the ecosystem, versioned alongside the
  compatibility matrix it must agree with.
- A deploy-layer workaround (e.g. installing a runtime dependency a product forgot to
  declare) is permitted **in the Dockerfile** and must be documented as such, with the
  upstream gap reported — it is a deployment fact, not a fork of the product.

## Notes captured while implementing this ADR

- Build context for each image is the **product repo root** (a sibling of `Connect/`);
  the Dockerfile is referenced back into `deploy/` via a relative path. BuildKit accepts
  a Dockerfile outside the context, so the Dockerfiles stay in `deploy/`.
- ComputeConnect points at the host llama.cpp engine via `host.docker.internal`
  (`host-gateway`). When that engine is loopback-bound on the host it is unreachable from
  the container, so ComputeConnect comes up **`degraded`** (its simulated-cloud provider
  stays healthy). This is accepted: the control plane is up and answering. On a host/venv
  deployment that shares loopback, the same ComputeConnect reports `ok` and places real
  generation on `qwen3-30b-a3b`.
- `agentconnect-core` lazily imports **httpx** in its memory / compute / ToolConnect
  clients but does not declare it. The AgentConnect image installs `httpx` explicitly as a
  deploy-layer workaround; the upstream fix is to add it to `agentconnect-core`.
