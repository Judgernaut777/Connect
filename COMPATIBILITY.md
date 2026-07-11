# Compatibility

The canonical compatibility reference for the Connect ecosystem. Product repositories should
link here rather than maintain their own matrices, so that there is exactly one place where a
cross-product claim can be wrong.

All four products released `0.1.0` on 2026-07-12. What follows is keyed on those releases.

---

## Release status

| Product | Version | Maturity | Requires Python | Gate (2026-07-12) |
|---|---|---|---|---|
| AgentConnect | 0.1.0 | Release candidate | `>= 3.10` | 945 passed / 3 skipped |
| BrainConnect | 0.1.0 | Release candidate | `>= 3.11` | 589 passed / 0 skipped |
| ComputeConnect | 0.1.0 | MVP (heterogeneity unproven) | `>= 3.11` | 66 passed |
| ToolConnect | 0.1.0 | MVP service | `>= 3.11` | 239 passed / 2 skipped |

AgentConnect's nine packages now all carry the same `0.1.0`, so "AgentConnect 0.1.0" names a
real, unified thing. Every product declares `Apache-2.0` as a PEP 639 SPDX
`License-Expression`; see [Licensing](#licensing).

### How to pin

Both installed-from-checkout products (`pip install -e`) should be pinned to a commit SHA or the
`0.1.0` tag under an editable install. For the combined install, BrainConnect must be pinned by
**wheel path or checkout**, never by PyPI name — see [gap 1](#1-pypi-name-collision-brainconnect-is-taken).

---

## The compatibility matrix

Every pairing below was **exercised over the real transport the row describes** during the
Phase-5 integration run on 2026-07-12 (real HTTP or MCP stdio, not an in-process shim).

| AgentConnect | Peer | Peer version | Transport | Status | What was verified |
|---|---|---|---|---|---|
| 0.1.0 | — | — | in-process + managed shell | ✅ | Full task loop driving a real `claude -p`; managed session cannot complete its own task |
| 0.1.0 | BrainConnect | 0.1.0 | HTTP `:8787` (bearer token) | ✅ | Capture, quarantine-on-injection, human-only promotion, nested refusal envelope, recall into a context pack |
| 0.1.0 | ComputeConnect | 0.1.0 | HTTP `:8090` (six routes) | ✅ | Real llama.cpp streaming generation, mid-stream cancel, CA-1 default-deny, CA-3 `run_id` |
| 0.1.0 | ToolConnect | 0.1.0 | HTTP `:8095` + MCP stdio | ⚠️ API-level | Real MCP ingest, authorize/outcome loop, fail-closed ambiguity/drift — but no shipped AgentConnect-side client |
| 0.1.0 | all three | 0.1.0 | composed | ✅ | Four-product composition end-to-end (Scenario 5) |

The ToolConnect row is marked ⚠️ because the binding is exercised at ToolConnect's decision API,
not through a first-class AgentConnect integration. See [gap 2](#2-agentconnect--toolconnect-is-api-level-only).

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
- CA-2 remains *proposed*, not implemented.

### ToolConnect decision API — AgentConnect ↔ ToolConnect

- There is **no shared `agentconnect-core` interface** for tool governance; ToolConnect defines
  its own HTTP surface, documented in its `docs/SERVICE.md` and pinned by
  `docs/AGENTCONNECT_CONTRACT.md`. `/authorize` returns a Decision; the caller executes the tool
  and closes the loop via `POST /decisions/{id}/outcome`. There is no invocation route.
- **This binding is API-level only.** AgentConnect ships no ToolConnect client; the contract was
  exercised against ToolConnect's API directly. See [gap 2](#2-agentconnect--toolconnect-is-api-level-only).

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
| AgentConnect HTTP API | Configurable | No fixed default; set the host/port explicitly. Authorization is enforced on every route. |
| BrainConnect HTTP API | `127.0.0.1:8787` | `brainconnect serve`; optional bearer token. The memory adapter targets this by default. |
| ComputeConnect HTTP API | `8090` | `computeconnect serve`. `8080` is the external llama.cpp engine (not a Connect product). |
| ToolConnect HTTP API | `127.0.0.1:8095` | `toolconnect serve`; loopback only. |

External, not a Connect product: the local llama.cpp inference engine on `:8080`, which
ComputeConnect consumes **read-only** and never manages.

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

### 1. PyPI name collision: `brainconnect` is taken

The name `brainconnect` is already registered on PyPI by an unrelated package. `pip install
brainconnect` from PyPI resolves that other project, not this one. **Consequences:**

- BrainConnect cannot be published to PyPI under this name without a rename or a namespace/scope.
  This is a real **release blocker** for PyPI publication.
- A combined install must install BrainConnect **by wheel path or from a checkout** (or with
  `--no-index --find-links`), never by bare name. See [COMBINED_INSTALL.md](COMBINED_INSTALL.md).

The names `agentconnect-*`, `computeconnect`, and `toolconnect` are free on PyPI.

### 2. AgentConnect ↔ ToolConnect is API-level only

ToolConnect's decision API is real and proven, but AgentConnect ships **no ToolConnect client**.
The Phase-5 binding was exercised against ToolConnect's `/authorize` and `/decisions/{id}/outcome`
directly. A first-class AgentConnect integration is not yet built.

### 3. ComputeConnect heterogeneity is unproven; the second provider is simulated

ComputeConnect's runtime is real, but on this single accelerator-less ARM host only one provider
(the local llama.cpp engine) is real; the second is a **simulated** cloud provider. The routing
and privacy machinery is exercised, but placement across genuinely heterogeneous hardware is
**not demonstrated**. Registering ComputeConnect as an AgentConnect routing worker is also
**programmatic only** — no environment/YAML declaration surface exists yet.

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
