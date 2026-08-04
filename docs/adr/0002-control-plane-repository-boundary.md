# ADR 0002 — Where the user-facing control-plane application lives

- Status: **Accepted** (2026-08-04).
- Decision: **Option A — a separate control-plane repository**, named **`Connect-Control`**.
- Rationale: The four infrastructure planes are stable at `0.1.x` (two release candidates,
  two MVPs with named gaps), the governance slice (ToolConnect contract `1.1` enforcement at
  the final invocation boundary) is in progress, and control-plane work now needs a home
  that does not pollute the docs-only umbrella. The evaluation below showed that the most
  load-bearing property of this repository — that nothing in it compiles, so its honesty is
  enforced by review and the drift check, not a test suite — would be put at risk by
  expanding `Connect` (Option B). A separate repository keeps each repository's job
  singular: `Connect` stays the thin, drift-checked integration umbrella; `Connect-Control`
  owns the application's stack, packaging, and cadence as a consumer of the manifest and the
  four planes' contracts.
- Context: The [product thesis](../../PRODUCT_THESIS.md) defines a target **user-facing
  control-plane application** — visual workspaces, human-guided and agent-led onboarding,
  organization configuration, marketplace discovery, budget visibility, policy configuration,
  and cross-plane observability. None of that exists today. The `Connect` repository today is
  a **docs-and-integration umbrella**: it ships the [ecosystem manifest](../../manifest/ecosystem.yaml),
  the [deploy bundle](../../deploy/), cross-product documentation, and operational scripts —
  and, by [CONTRIBUTING.md](../../CONTRIBUTING.md) and [ADR 0001](0001-deploy-directory.md),
  it deliberately ships **no importable, installable, or executed product code**. The
  control-plane application is exactly such code (a desktop/web app, a marketplace module, an
  organization-management layer, a budget interface). It cannot land in `Connect` without
  either overturning the docs-only rule or being carved into a new home. This ADR chooses the
  new home.

## The decision this ADR governs

**Where does the user-facing control-plane application live — a new repository, or an expanded
`Connect`?** With this ADR accepted, that question is answered: a new repository,
**`Connect-Control`**. The `Connect` repository remains docs-and-integration only.

Related and deliberately *not* re-opened here: the four planes keep their own repositories,
names, and release cadence ([MANIFESTO §*What we will not build*](../../MANIFESTO.md#what-we-will-not-build)).
This ADR is only about the fifth, control-plane surface.

## Options

### Option A — a separate control-plane repository ✅ accepted

```text
Connect
    ecosystem manifest, compatibility, distribution and release integration (docs-only, as today)

Connect-Control
    the user-facing desktop/web control-plane application, including the marketplace module,
    organization management, and the budget interface
```

`Connect` stays the thin, drift-checked integration umbrella it is today; the application is a
new product repository that *consumes* the manifest and the four planes' contracts like any
other consumer. The ADR's option sketch named the repo `ConnectWorkspace` (or
`ConnectControlPlane`); the accepted name is **`Connect-Control`**, matching the ecosystem's
`*Connect` product naming convention.

### Option B — expand the existing `Connect` repository ❌ rejected

```text
Connect
    release integration + the user-facing control-plane application in one repository
```

`Connect` takes on application code, reversing the docs-only rule ([ADR 0001](0001-deploy-directory.md),
[CONTRIBUTING.md](../../CONTRIBUTING.md)) for this surface.

## Evaluation

| Criterion | Option A — separate repo | Option B — expand Connect |
|---|---|---|
| **Release cadence** | App ships on its own cadence; the manifest/lockfile stays slow and stable | App churn and manifest stability collide in one release stream |
| **Dependency boundaries** | Clean: the docs umbrella keeps zero runtime deps; the app owns its stack | The umbrella acquires a large desktop/web dependency tree |
| **Desktop & web packaging** | Natural home for build/packaging toolchains | Packaging config mixed into a docs repo |
| **Documentation ownership** | `Connect` remains the neutral cross-product doc authority; app docs live with the app | Cross-product neutrality blurs with product-specific docs |
| **Marketplace code** | Lives with the app (a module of it), not a separate service — see [note](#marketplace-placement) | Same module, but inside the umbrella |
| **Organization-management code** | With the app | In the umbrella |
| **Budget interface** | With the app (consumes the Work plane's [budget model](https://github.com/Judgernaut777/AgentConnect/blob/main/docs/BUDGET_MODEL.md)) | In the umbrella |
| **Deployment composition** | Unchanged: `Connect/deploy/` still composes the stack, now including the app image | Same, but authored beside the app |
| **Risk of repository sprawl** | One more repo to track in the manifest | None |
| **Risk of turning Connect into a monolith** | Avoided — the umbrella stays thin | **High** — the umbrella becomes the app, the docs authority, and the release integrator at once |

## Why Option A

The evaluation leans toward **Option A**, and this ADR now ratifies that leaning. The single
most load-bearing property of the current `Connect` repository is that *nothing in it
compiles, so its honesty is enforced by review and by the drift check, not by a test suite*
([CONTRIBUTING.md](../../CONTRIBUTING.md)). Putting a large application in the same
repository would put that property at risk and couple a fast-moving app to a deliberately
slow lockfile. Option A keeps each repository's job singular. The standing cost it adds — a
new repository to maintain and to register in release integration — is accepted explicitly,
and is paid down by registering `Connect-Control` in the
[manifest](../../manifest/ecosystem.yaml) when it ships its first release (see Consequences).

## Marketplace placement

The marketplace may initially ship as a **module of the control-plane product**, not a
separate service or repository. Do **not** split it out solely for conceptual neatness; split
it only when it clearly owns an independent authority and operational lifecycle. This holds
under the accepted option. See [MARKETPLACE_ARCHITECTURE.md](../../MARKETPLACE_ARCHITECTURE.md).

## Consequences

- Control-plane application code lives in **`Connect-Control`** and does not begin in
  `Connect`. The `Connect` repository keeps its docs-only rule; [ADR 0001](0001-deploy-directory.md)
  and [CONTRIBUTING.md](../../CONTRIBUTING.md) stand unchanged.
- `Connect-Control` is registered in the [manifest](../../manifest/ecosystem.yaml) as a fifth
  tracked product when it ships its first release; until then the manifest continues to track
  the four infrastructure planes only, and `Connect-Control` is documented as a scaffold.
- The marketplace ships initially as a module of `Connect-Control`, per the placement note
  above.
- `Connect/deploy/` continues to compose the stack; the application image is added to that
  composition when a runnable artifact exists — and not before.
- The alternative this ADR weighed and rejected — deferring the control-plane application
  entirely — is recorded here: the ecosystem is ready to carry a scaffolded control-plane
  home, and the target-product documentation (thesis, marketplace architecture,
  data/compliance boundaries, transparency, setup, budget model) now has an implementation
  home to converge on.
