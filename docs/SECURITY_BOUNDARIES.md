# Security boundaries

What the Connect ecosystem does and does **not** protect against. Read this before you
deploy anything past a trusted single-user host. The honest one-liner: **these are
compliance and governance layers over a cooperative API surface, not a sandbox.**

## The five boundaries, stated plainly

### 1. Compliance, not a sandbox

AgentConnect (and the ledgers generally) enforce policy at their **API surface**. A caller
that goes through the API is authenticated, authorized, and audited. A process with **direct
filesystem or database access bypasses all of it** — it can read artifact bodies, edit a
ledger row, or forge history. AgentConnect's own principle: *"if it is not recorded in
AgentConnect, it did not happen"* — which is a statement about the audit surface, not a claim
that the OS is confined. Run agents under real OS-level isolation (containers, users,
seccomp) if you need a sandbox; Connect does not provide one.

### 2. Human-only promotion (BrainConnect)

Trust in BrainConnect is **conferred by a human, never by an agent**. Workers may *capture*
(write-only) candidates; only a human *promotes* a candidate into trusted memory, from a
terminal they control. The promotion action is in AgentConnect's `AGENT_FORBIDDEN_ACTIONS`,
so no managed-agent token can promote whatever its scope claims. **Never** serve BrainConnect's
MCP `--review` mode (which exposes `brain_pending`/`brain_promote`/`brain_reject`) to an
agent — that hands the agent the gate. This is a trust boundary, and it is deliberately
non-negotiable.

### 3. Structural cloud default-deny (ComputeConnect)

ComputeConnect defaults to the **most restrictive privacy tier** when a request declares none
(contract amendment CA-1), and cloud placement requires **positive re-verification** — a
request is not sent to a cloud provider unless it is explicitly permitted to leave local
hardware. When both a header and a body declare a privacy tier, the **more restrictive one
wins** (more-restrictive precedence). Verified: in the container deployment, where only the
simulated cloud provider is healthy, a default-tier `/route/estimate` returns
`no_compliant_provider` rather than silently placing on cloud. Default-deny holds when
nothing is declared.

### 4. Fail-closed tool governor (AgentConnect ↔ ToolConnect)

Tool governance is the one place AgentConnect **departs from "adapters fail open."** The
`ToolConnectGovernor` denies when the decision point is unreachable, when a tool was never
asserted, and when the decision contract major is unrecognised. A denied tool blocks the
subtask **before** its worker spawns — no run, no artifact. Verified end-to-end: a read tool
is allowed, a write tool is denied (`default deny: no policy matched`), decisions carry
`contract_version: "1.0"`. Cedar itself is default-deny: a tool with no matching `permit` is
forbidden.

### 5. Direct-DB / on-disk caveats

Restated because it is the most common misread: the ledgers protect against a **cooperative
agent reaching them through the API**. Anything with direct access to the SQLite files or the
artifact directory is outside the trust boundary. Back those files with filesystem
permissions, disk encryption, and host isolation — the application layer cannot.

## Deployment hardening checklist (network surface)

- **Bind loopback, or require a token.** ToolConnect *refuses* a non-loopback bind without a
  bearer token; hold the other services to the same rule. In [deploy/](../deploy/) every
  cross-service call carries a token and the services are only reachable on the compose
  network plus mapped localhost ports.
- **Tokens are secrets.** `BRAINCONNECT_TOKEN`, `TOOLCONNECT_AUTH_TOKEN`, and AgentConnect's
  operator tokens are passwords. The `.env.example` ships obvious placeholders precisely so a
  real deploy cannot accidentally run with them. Never commit a filled `.env`.
- **Prefer env-supplied tokens over flags.** ToolConnect takes its token from an env var by
  name, not a bare `--token`, because argv is visible in `ps`. Follow that pattern.
- **Terminate TLS and rate-limit at a reverse proxy.** ToolConnect's built-in per-IP rate
  limiter is a backstop, not your primary control.
- **AgentConnect operator tokens are minted locally, shown once.** Only the SHA-256 is
  stored; treat a lost token as revoked and re-mint. Minting is an operator action, refused
  to managed-agent sessions.

## Known low-severity notes

The independent review found **no critical or high** issues. Three LOW notes are tracked in
[COMPATIBILITY.md](../COMPATIBILITY.md#5-three-low-severity-security-hardening-notes):
`sanitize_env` DSN-name gap, the ComputeConnect header-vs-body privacy precedence, and the
direct-DB caveat above. None changes the boundaries stated here.
