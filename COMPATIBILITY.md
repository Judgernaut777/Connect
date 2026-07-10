# Compatibility

The intended canonical compatibility reference for the Connect ecosystem. Product
repositories should link here rather than maintain their own matrices, so that there is
exactly one place where a cross-product claim can be wrong.

**It is not canonical yet.** Nothing has been released, so there is nothing to be canonical
about. What follows is the current honest state and the policy that will govern the matrix
once releases exist.

---

## Release status

**No product in this ecosystem has shipped a release.**

| Product | Phase | Latest tag | Package versions | Notes |
|---|---|---|---|---|
| AgentConnect | Implemented | `v0.1.0-mvp-control-loop` | span `0.1.0`–`0.2.0` across nine packages | Versions are not unified across packages |
| BrainConnect | Implemented | `v0.1.0` | `0.2.0` (`cli`) | Repository renamed; identifiers still say `wiki`/`wikibrain` |
| ComputeConnect | Design | — | — | No runtime. Proposal not yet pushed. |
| ToolConnect | Design | — | — | No runtime. Proposal published at `c6c4480`. |

Because AgentConnect's packages do not share a version number, "AgentConnect 0.2.0" does not
currently name a thing. Do not write it down as though it does.

### How to pin, today

Until releases exist, **pin to commit SHAs.** Both implemented products are installed from a
git checkout with `pip install -e`, so a tag or branch name is the only thing standing between
you and a silent change under an editable install.

---

## The compatibility matrix

Reserved for when two products have releases that can be meaningfully paired. The shape it
will take:

| AgentConnect | BrainConnect | Python | Status | Notes |
|---|---|---|---|---|
| — | — | — | — | *No releases. No verified pairs.* |

A row may be added only when the pairing has been exercised **over the transport the row
describes**. A pairing verified by an in-process test does not earn a row that implies a
network path. See [Known gaps](#known-gaps).

ComputeConnect and ToolConnect enter this matrix when they have runnable releases. A charter
is not a version.

---

## Python version floor

| Product | Requires |
|---|---|
| AgentConnect | `>= 3.10` |
| BrainConnect | `>= 3.11` |

**A combined install requires Python 3.11 or newer** — the higher of the two floors.
Installing AgentConnect alone on 3.10 is supported; adding BrainConnect to that interpreter is
not.

The products should be installed into **separate virtual environments** regardless. See
[COMBINED_INSTALL.md](COMBINED_INSTALL.md#use-separate-virtual-environments).

---

## Provisional port registry

**These assignments are provisional.** They are documented rather than frozen, because
freezing a number without the product owner's agreement would create a false constraint that
somebody later has to litigate. The one firm rule is that **no two products may claim the same
port.**

| Product | Port | Status |
|---|---|---|
| AgentConnect HTTP API | Configurable | `8787` suggested **only if not used elsewhere**. Used as the example value for `AGENTCONNECT_API_URL` in AgentConnect's compliance documentation. |
| BrainConnect HTTP API | Unassigned | Must be chosen, and must differ from AgentConnect's, **before** `wiki serve` is implemented. `WIKIBRAIN_URL` currently defaults to `:8787`, which is the collision. |
| ComputeConnect HTTP API | Unassigned | No runtime exists. |
| ToolConnect HTTP API | Unassigned | No runtime exists. |

The live conflict is that `WIKIBRAIN_URL` defaults to `http://localhost:8787` while
AgentConnect's own documentation puts its API on the same port. Nothing binds either today, so
nothing breaks today. It becomes a first-day bug the moment `wiki serve` ships. Resolve it
before writing that server, not after.

---

## Licensing

**The products do not share a license.**

| Product | License | Evidence |
|---|---|---|
| AgentConnect | MIT | Declared as `license = { text = "MIT" }` in package metadata and stated in the README. **No `LICENSE` file is present in the repository.** |
| BrainConnect | Apache 2.0 | `LICENSE` and `NOTICE` files present at the repository root |
| ComputeConnect | — | Not yet declared |
| ToolConnect | — | Not yet declared |

Two consequences worth knowing before you vendor either implemented product:

- Apache 2.0 carries an explicit patent grant and a `NOTICE` propagation requirement; MIT
  carries neither. Redistributing them as a single bundle means satisfying both.
- AgentConnect's missing `LICENSE` file is a real defect, not a formality. A declared license
  with no accompanying file leaves the actual grant ambiguous to anyone doing license review
  by tooling. It should be added to that repository.

---

## Known gaps

Standing list of places where the ecosystem does not do what a reasonable reader would assume.
Each is either verified against the code or explicitly attributed to the reporting product.

### 0. AgentConnect HTTP API authorization and completion bypass 🔴 open

**An authorization and completion bypass in AgentConnect's HTTP API is open at the time of
writing.**

**Do not enable the HTTP API (`agentconnect-api`) for managed-agent access until the fix
lands.** The completion gate — the property that a managed agent session cannot mark its own
task complete — is the mechanism the product exists to provide, and the HTTP path does not
currently enforce it.

The CLI-driven managed loop described in [GETTING_STARTED.md](GETTING_STARTED.md) and
[COMBINED_INSTALL.md](COMBINED_INSTALL.md) does not require the HTTP API, and neither combined
topology uses it.

*Reported by the AgentConnect maintainers. Recorded here as an operational warning; it has not
been independently reproduced from this repository.* This entry is removed, and replaced with
the fixing commit, once AgentConnect reports it fixed.

### 1. BrainConnect has no HTTP server — the memory integration cannot be wired

AgentConnect registers `WikiBrainMemoryAdapter` against `WIKIBRAIN_URL`, defaulting to
`http://localhost:8787`. BrainConnect ships nothing that binds that port. The repository
contains no `uvicorn`, `FastAPI`, `flask`, or `http.server` import. `wiki serve` does not exist
and is a tracked, deferred follow-up.

The cross-repo integration test substitutes an in-process transport into `wiki.api`. It drives
a real ledger, real promotion, and the real trust filter. **It does not exercise a socket.**

> A green integration suite means the semantics agree, not that the network path exists.

**Impact:** Topology B in [ARCHITECTURE.md](ARCHITECTURE.md#two-product-integration) is
unavailable. Setting `WIKIBRAIN_URL` will fail at connect time.

### 2. Port `8787` is doubly claimed

`WIKIBRAIN_URL` defaults to `http://localhost:8787`. AgentConnect's compliance documentation
uses `:8787` as its example `AGENTCONNECT_API_URL`. A future `wiki serve` binding its default
port alongside an `agentconnect-api` following that example will collide.

**Impact:** none today, because gap 1 means nothing binds the port. See the
[provisional port registry](#provisional-port-registry).

### 3. The BrainConnect rename is incomplete

The product and its repository are named BrainConnect. Everything else is not. The console
scripts are `wiki` and `wiki-librarian`, the MCP server is `wiki-brain`, the tools are
`brain_*`, the database is `~/.wiki-brain/wiki.db`, the environment variables are
`WIKIBRAIN_URL` and `WIKIBRAIN_DB`, and AgentConnect's adapter class is
`WikiBrainMemoryAdapter`.

**Impact:** every identifier a user types still says WikiBrain. Renaming them is a breaking
change and has not been scheduled.

### 4. AgentConnect package versions are not unified

Its nine packages carry a mix of `0.1.0` and `0.2.0`. There is no single AgentConnect version
number to record in a matrix row.

**Impact:** a matrix keyed on "AgentConnect version" cannot be built until the packages are
versioned together or the matrix is keyed per-package.

### 5. ComputeConnect's architecture proposal is unpublished

The charter is defined, but the repository contains only a stub README. Readers following the
link from this documentation will not find the design it describes.

**Impact:** documentation-only. Nothing depends on it, because nothing runs.

---

## Versioning policy (proposed, not adopted)

Offered as the policy this document would enforce. It has not been agreed to and no product
currently follows it.

1. **Semantic versioning per product**, with all packages inside a product released at one
   version. A product's version names the whole product or it names nothing.
2. **Cross-product compatibility is declared by the consumer.** AgentConnect states which
   BrainConnect versions its memory adapter supports; BrainConnect does not speculate about
   AgentConnect.
3. **A matrix row requires an exercised pairing over the real transport.** Semantic agreement
   verified in-process is documented as exactly that, and never as a supported pairing.
4. **Contract changes are major.** `MemoryAdapter` and `LocalComputeProvider` are the
   ecosystem's public surface. Breaking either is a major bump in the product that owns the
   interface — which is AgentConnect for both.
5. **A design-phase product has no version.** ComputeConnect and ToolConnect acquire versions
   when they have code, not when they have a charter.
