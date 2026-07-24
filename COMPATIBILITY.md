# Compatibility

The canonical compatibility reference for the Connect ecosystem. Product repositories should
link here rather than maintain their own matrices, so that there is exactly one place where a
cross-product claim can be wrong.

All four products released `0.1.0` on 2026-07-12. What follows is keyed on those releases.

---

## Release status

<!-- BEGIN generated:tests (source: manifest/ecosystem.yaml — do not hand-edit) -->
| Product | Version | Maturity | Requires Python | Gate |
|---|---|---|---|---|
| AgentConnect | 0.1.0 | Release candidate | `>= 3.10` | 1060 passed / 3 skipped (`pytest`, offline) |
| BrainConnect | 0.1.0 (tag `v0.1.2-rc1` — version/tag mismatch, see note below) | Release candidate | `>= 3.11` | 949 passed / 0 failed (`python3 tests/acceptance.py`) |
| ComputeConnect | 0.1.0 | MVP (heterogeneity unproven) | `>= 3.11` | 129 passed, 140 collected (`pytest`, offline) |
| ToolConnect | 0.1.0 | MVP service | `>= 3.11` | 339 passed / 3 skipped, 342 collected (`pytest`, offline) |

ComputeConnect's offline gate excludes 11 real-engine tests that require a live llama.cpp on
`:8080`; 9 of those currently fail only because the host model was renamed
`qwen3-30b-a3b` → `qwen3.6-35b-a3b`, not because of a product bug. BrainConnect's
`pyproject` `package_version` (`0.1.0`) was never bumped to match its `v0.1.2-rc1` tag — both
numbers are recorded truthfully in [manifest/ecosystem.yaml](manifest/ecosystem.yaml) rather than
reconciled by fiat.
<!-- END generated:tests -->

AgentConnect's nine packages now all carry the same `0.1.0`, so "AgentConnect 0.1.0" names a
real, unified thing. Every product declares `Apache-2.0` as a PEP 639 SPDX
`License-Expression`; see [Licensing](#licensing). These numbers are generated from
[manifest/ecosystem.yaml](manifest/ecosystem.yaml) — see [docs/RELEASE.md](docs/RELEASE.md).

### How to pin

Pin each product to the `0.1.0` tag (or a commit SHA under an editable install). BrainConnect
installs by its PyPI **distribution name `brainconnect-ai`** (`pip install "brainconnect-ai==0.1.0"`)
— the import package and command stay `brainconnect`; never `pip install brainconnect` bare. See
[note 1](#1-pypi-name--resolved-via-brainconnect-ai).

---

## The compatibility matrix

Every pairing below was **exercised over the real transport the row describes** during the
Phase-5 integration run on 2026-07-12 (real HTTP or MCP stdio, not an in-process shim).

| AgentConnect | Peer | Peer version | Transport | Status | What was verified |
|---|---|---|---|---|---|
| 0.1.0 | — | — | in-process + managed shell | ✅ | Full task loop driving a real `claude -p`; managed session cannot complete its own task |
| 0.1.0 | BrainConnect | 0.1.0 | HTTP `:8787` (bearer token) | ✅ | Capture, quarantine-on-injection, human-only promotion, nested refusal envelope, recall into a context pack |
| 0.1.0 | ComputeConnect | 0.1.0 | HTTP `:8090` (six routes) | ✅ | Real llama.cpp streaming generation, mid-stream cancel, CA-1 default-deny, CA-3 `run_id` |
| 0.1.0 | ToolConnect | 0.1.0 | HTTP `:8095` + MCP stdio | ✅ | Fail-closed `ToolConnectGovernor` in `agentconnect-core`: allow read / deny write, contract `1.0`, subtask blocked before worker spawn |
| 0.1.0 | all three | 0.1.0 | composed (Docker) | ✅ | Four-service Compose stack builds + comes up healthy; `connect-smoke` passes 6/6 (see [deploy/](deploy/)) |

The ToolConnect row is now ✅: `agentconnect-core` ships the `ToolConnectGovernor`, verified
end-to-end this cycle. See [note 2](#2-agentconnect--toolconnect--first-class-fail-closed-governor-shipped).

The composed row was verified in Docker Compose: all four images build, all four report healthy
(ComputeConnect `degraded` because the host llama.cpp is loopback-bound and unreachable from the
container — the control plane still answers), and the cross-product smoke passes. Exact recipe and
captured output live in [deploy/README.md](deploy/README.md).

---

## The contracts

Cross-product surface is expressed as an interface in `agentconnect-core`, never as shared code.

### MemoryAdapter — AgentConnect ↔ BrainConnect

- Registered in `agentconnect.core.bootstrap` under two service names that resolve to the same
  adapter and the same trusted authority: `brainconnect` (env `BRAINCONNECT_URL`, token
  `BRAINCONNECT_TOKEN`) and the legacy alias `wikibrain` (env `WIKIBRAIN_URL`, token
  `WIKIBRAIN_TOKEN`). Both default to `http://localhost:8787`, which is where `brainconnect serve`
  binds by default. Configure exactly one.
- **Actor-type mapping.** AgentConnect's actor vocabulary includes `system`; BrainConnect's
  ledger does not. The wire adapter maps `origin_actor_type="system"` to the ledger's `"tool"`
  (`_LEDGER_ACTOR_TYPE_MAP` in `core/memory.py`). Verified in Scenario 2.
- **Nested refusal envelope.** A promotion blocked by memory safety raises `MemorySafetyRefused`
  carrying the full nested envelope (engines, findings, spans). AgentConnect surfaces this rather
  than swallowing it.
- **The authority rule every consumer must obey:** `trusted: true` is the authority signal.
  `status: "promoted"` is **not** — a promoted claim in an open contradiction returns `promoted`
  *and* untrusted. A missing `trusted` means untrusted; never infer it from status.

### LocalComputeProvider — AgentConnect ↔ ComputeConnect

- Abstract base in `agentconnect.core.local_compute`; `HttpLocalComputeProvider` is the shipped
  client. ComputeConnect implements the engine side. Six routes: `GET /health`, `GET /models`,
  `GET /models/loaded`, `POST /route/estimate`, `POST /generate`, `POST /runs/{run_id}/cancel`.
- **Amendment CA-1 (privacy default-deny).** `/generate` accepts an optional `privacy_tier`;
  when absent it is treated as the **most restrictive** tier, and a positive re-verification is
  required before cloud placement. Cloud candidates are filtered *before* placement; an empty
  candidate set yields a structured refusal. Verified in Scenario 3.
- **Amendment CA-3 (run identity).** A `run_id` is accepted in the request body and echoed as an
  `X-Run-Id` header; `GET /runs/{run_id}` returns run metadata and cancellation state. Verified
  in Scenario 3 (a 1024-token generation cancelled mid-stream reported `finish_reason=cancelled`).
- **More-restrictive precedence.** When a privacy tier arrives on both the `X-Privacy-Tier`
  header and the request body, the **more restrictive** of the two wins — a request can be tightened
  by either channel, never loosened. Default-deny still holds when neither is present.
- **Declarative registration.** Setting `AGENTCONNECT_COMPUTE_URL` (env wins over
  `config/compute.yaml`) registers ComputeConnect as the `local-manager` worker; verified — it then
  appears in AgentConnect's `GET /health` worker list. Optional `AGENTCONNECT_COMPUTE_TOKEN` /
  `_TIMEOUT`.
- CA-2 remains *proposed*, not implemented.

### ToolConnect decision API — AgentConnect ↔ ToolConnect

- ToolConnect defines its own HTTP surface (its `docs/SERVICE.md`, pinned by
  `docs/AGENTCONNECT_CONTRACT.md`). `POST /authorize` returns a Decision carrying
  `contract_version` (currently **`1.0`**), `allowed`, `decision_id`, `reason`,
  `determining_policies`, and `default_deny`; the caller executes the tool and closes the loop
  via `POST /decisions/{id}/outcome`. There is **no invocation route** — ToolConnect decides, it
  does not execute.
- **AgentConnect ships a first-class client.** `agentconnect-core`'s `ToolConnectGovernor`
  (bound via `AGENTCONNECT_TOOLCONNECT_URL` / `_TOKEN` / `_MODE`) consults `/authorize` and is
  **fail-closed**: an unreachable point, an unasserted tool, or an unrecognised contract **major**
  all deny. A denied tool blocks the subtask before the worker spawns. Verified this cycle: read
  allowed (`permitted by local-reads`), write denied (`default deny: no policy matched`), contract
  `1.0`; `deploy/connect-smoke` exercises it and `examples/demo_governor_chokepoint.py` proves the
  subtask-block. See [note 2](#2-agentconnect--toolconnect--first-class-fail-closed-governor-shipped).

### Observability event model — AgentConnect

- AgentConnect emits a provider-neutral **observation event** stream; providers are additive and
  fail-isolated. Configured via `AGENTCONNECT_OBSERVABILITY` (`structured_log`, `tmux`, `herdr`,
  `otlp`), with `_FAILURE_POLICY` (`advisory`|`task_blocking`|`startup_fatal`), a JSONL
  `_LOG_PATH`, tmux socket/layout, Herdr enable+socket, and `AGENTCONNECT_OTLP_ENDPOINT`.
- Verified this cycle: `structured_log` and `tmux` (tmux 3.3a) report **available**; `herdr`
  reports its own failure with an actionable message when no socket is configured, and the other
  providers still come up. Consumed by `agentconnect agents list|tree|watch|attach|output|events|
  cancel` and `agentconnect observability providers|health`; `agents output` is bounded and
  redacted through the service's safety redactor. Full guide: [docs/OBSERVABILITY.md](docs/OBSERVABILITY.md).

There is no shared package and no monorepo. Separate repositories, explicit interfaces.

---

## Python version floor

| Product | Requires |
|---|---|
| AgentConnect | `>= 3.10` |
| BrainConnect | `>= 3.11` |
| ComputeConnect | `>= 3.11` |
| ToolConnect | `>= 3.11` |

**A single-venv combined install requires Python 3.11 or newer** — the higher floor. Installing
AgentConnect alone on 3.10 is supported; adding any other product to that interpreter is not.

---

## Port registry

Assignments as they ship at `0.1.0`. The one firm rule: no two products may claim the same port.
The historical `:8787` double-claim is **resolved** — the AgentConnect memory adapter's default
(`http://localhost:8787`) now points at BrainConnect's `serve` default, which is intentional, and
AgentConnect's own HTTP API has no fixed default port (it is configured explicitly).

| Product | Default port | Notes |
|---|---|---|
| AgentConnect HTTP API | `127.0.0.1:8790` | `agentconnect-api`; `AGENTCONNECT_API_HOST`/`_PORT` (default port `8790`). Authorization enforced on every route except `/health`. |
| BrainConnect HTTP API | `127.0.0.1:8787` | `brainconnect serve`; optional bearer token. The memory adapter targets this by default. |
| ComputeConnect HTTP API | `8090` | `computeconnect serve`. `8080` is the external llama.cpp engine (not a Connect product). |
| ToolConnect HTTP API | `127.0.0.1:8095` | `toolconnect serve`; loopback only. |

External, not a Connect product: the local llama.cpp inference engine on `:8080`, which
ComputeConnect consumes **read-only** and never manages.

The [deploy/](deploy/) Compose stack maps these container defaults to **off-reserved host ports**
to coexist with a running llama.cpp: AgentConnect `8890→8790`, BrainConnect `8887→8787`,
ComputeConnect `8990→8090`, ToolConnect `8995→8095`.

---

## Licensing

**The entire ecosystem is Apache-2.0.** No divergence to reconcile before vendoring.

| Product | License | Evidence |
|---|---|---|
| AgentConnect | Apache-2.0 | `LICENSE` + `NOTICE` at root; SPDX `License-Expression` in every package; license text in every wheel |
| BrainConnect | Apache-2.0 | `LICENSE` + `NOTICE` at root; SPDX metadata; license text in wheel |
| ComputeConnect | Apache-2.0 | `LICENSE` + `NOTICE` at root; SPDX metadata; license text in wheel |
| ToolConnect | Apache-2.0 | `LICENSE` + `NOTICE` at root; SPDX metadata; license text in wheel |

Apache-2.0 carries an explicit patent grant and a `NOTICE` propagation requirement. A single
bundle of all four satisfies one license, and each `NOTICE` must be preserved when redistributing.

---

## Known gaps

Standing list of places where the ecosystem does not do what a reasonable reader might assume.
Each is verified against the code this cycle.

### 0. AgentConnect HTTP API authorization/completion bypass ✅ fixed at `a07df7f`, retest confirms it stays fixed

`POST /tasks/{id}/complete` with `force: true` was once reachable by anyone who could open a
socket, letting a managed agent certify its own work without the audit. Fixed at `a07df7f`:
every transport routes through a single `authorize()` gate, `force` is removed from the
completion schema (the override is a separate operator-only endpoint that logs its reason), and
completion is attributed to the authenticated principal. An **independent security retest this
cycle re-ran the full bypass and confirmed it stays fixed** (`tests/test_http_authorization.py`
stands up a real uvicorn server on a real port).

### 1. PyPI name — RESOLVED via `brainconnect-ai`

The bare name `brainconnect` is registered on PyPI by an unrelated package, so BrainConnect
publishes under the distribution name **`brainconnect-ai`**: `pip install brainconnect-ai`. A
distribution name may differ from what it imports — the **import package and the console command
both stay `brainconnect`**. This is **resolved**, not a release blocker. The only rule that
survives: never `pip install brainconnect` bare, or you fetch the stranger's library. Verified in
this cycle — `brainconnect-ai` installs cleanly alongside `agentconnect-*`, `computeconnect`, and
`toolconnect` in one virtualenv (86 packages, `pip check` clean), and as the `connect/brainconnect`
container image in [deploy/](deploy/).

The names `agentconnect-*`, `computeconnect`, and `toolconnect` are free on PyPI.

> **Deploy-layer dependency note (found while building [deploy/](deploy/), since fixed
> upstream):** `agentconnect-core` lazily `import httpx` in all three of its HTTP clients (memory
> adapter, ComputeConnect provider, ToolConnect governor) but once declared only `pydantic` +
> `pyyaml`, so a base `agentconnect-api` install could not reach the sibling services. Reported
> upstream and fixed: `agentconnect-core` now declares `httpx>=0.27`, so no combined-venv
> masking or explicit deploy-image install is needed.

### 2. AgentConnect ↔ ToolConnect — first-class fail-closed governor shipped

`agentconnect-core` now ships a real `ToolConnectGovernor` client. AgentConnect consults it as a
genuine chokepoint: a denied tool blocks a subtask **before** its worker spawns, and an unreachable
decision point **denies** (fail-closed — the one place AgentConnect departs from "adapters fail
open"). Verified end-to-end this cycle against a live `toolconnect serve`: a read tool is allowed,
a write tool is denied, decisions carry contract version `1.0`, and the cross-product smoke in
[deploy/connect-smoke](deploy/connect-smoke) exercises exactly this. See
`mcp-agentconnect/examples/demo_governor_chokepoint.py` for the subtask-blocking proof.

### 3. ComputeConnect heterogeneity is unproven; the second provider is simulated

ComputeConnect's runtime is real, but on this single accelerator-less ARM host only one provider
(the local llama.cpp engine) is real; the second is a **simulated** cloud provider. The routing
and privacy machinery is exercised, but placement across genuinely heterogeneous hardware is
**not demonstrated**. Registering ComputeConnect as an AgentConnect routing worker is now
**declarative** — `AGENTCONNECT_COMPUTE_URL` (or `config/compute.yaml`) registers the
`local-manager` worker, which then appears in AgentConnect's `GET /health`. Verified in the
Compose stack; only the heterogeneity claim remains open.

### 4. The BrainConnect rename keeps `brain_*` MCP tools and the `~/.wiki-brain/` data dir

The package, console scripts, and `BRAINCONNECT_DB` variable are renamed. The **MCP tools remain
`brain_*`** (the agent-facing wire contract, deliberately stable) and the live data directory
remains `~/.wiki-brain/`. `WIKIBRAIN_DB` is honored as a deprecated fallback (with a warning) only
while `BRAINCONNECT_DB` is unset. These are documented limitations, not oversights.

### 5. Three low-severity security hardening notes

The independent review found no critical or high issues. Three LOW notes are recorded so nobody
is surprised:

- **`sanitize_env` DSN-name gap.** Environment sanitization is opt-in and does not cover a
  connection-string variable named as a DSN in every form.
- **ComputeConnect privacy-tier header vs body precedence.** When both an `X-Privacy-Tier` header
  and a body `privacy_tier` are present, the precedence is a documented behavior worth knowing;
  default-deny still holds when neither is present.
- **Direct-DB / on-disk caveats are compliance, not security.** The ledgers protect against a
  cooperative agent via the API surface; direct filesystem or database access bypasses those
  controls. This is the compliance-layer boundary, stated plainly, not a sandbox.

### 6. ToolConnect's "protocol-neutral" claim is only partially proven

Every tool ingested so far was MCP-shaped. The registry treats capability metadata as an untrusted
assertion (the property that lets a non-MCP source plug in), but ingesting a non-MCP descriptor
remains the test that would confirm or collapse the claim.
