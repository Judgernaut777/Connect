# ADR 0002 — Where the user-facing control-plane application lives

- Status: **Proposed** (raised by the ecosystem documentation-correction pass, 2026-07-28).
  This ADR frames the decision and its options; it is not yet ratified by the Lead.
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
  either overturning the docs-only rule or being carved into a new home.

## The decision this ADR governs

**Where does the user-facing control-plane application live — a new repository, or an expanded
`Connect`?** Until this ADR is accepted, **no substantial control-plane application
implementation begins in the `Connect` repository.** Documentation of the target product
(this pass) is explicitly permitted and is not "implementation."

Related and deliberately *not* re-opened here: the four planes keep their own repositories,
names, and release cadence ([MANIFESTO §*What we will not build*](../../MANIFESTO.md#what-we-will-not-build)).
This ADR is only about the fifth, control-plane surface.

## Options

### Option A — a separate control-plane repository

```text
Connect
    ecosystem manifest, compatibility, distribution and release integration (docs-only, as today)

ConnectWorkspace  (or ConnectControlPlane)
    the user-facing desktop/web control-plane application, including the marketplace module,
    organization management, and the budget interface
```

`Connect` stays the thin, drift-checked integration umbrella it is today; the application is a
new product repository that *consumes* the manifest and the four planes' contracts like any
other consumer.

### Option B — expand the existing `Connect` repository

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

## Leaning, and why it is not yet the decision

The evaluation leans toward **Option A**. The single most load-bearing property of the current
`Connect` repository is that *nothing in it compiles, so its honesty is enforced by review and
by the drift check, not by a test suite* ([CONTRIBUTING.md](../../CONTRIBUTING.md)). Putting a
large application in the same repository puts that property at risk and couples a fast-moving
app to a deliberately slow lockfile. Option A keeps each repository's job singular.

This ADR nonetheless remains **Proposed**, not Accepted, because the choice has consequences
the Lead should ratify explicitly — a new repository is a standing maintenance and
release-integration cost, and the alternative (formally deferring the whole control-plane app)
is also legitimate if the ecosystem is not ready to carry it.

## Marketplace placement

The marketplace may initially ship as a **module of the control-plane product**, not a
separate service or repository. Do **not** split it out solely for conceptual neatness; split
it only when it clearly owns an independent authority and operational lifecycle. This holds
under either option above. See [MARKETPLACE_ARCHITECTURE.md](../../MARKETPLACE_ARCHITECTURE.md).

## Consequences

- Until this ADR is **Accepted**, control-plane application code does not begin in `Connect`.
  The documentation of the target product (thesis, marketplace architecture, data/compliance
  boundaries, transparency, setup, budget model) proceeds now and is not gated by this ADR.
- If **Option A** is accepted, a new repository is created and registered in the
  [manifest](../../manifest/ecosystem.yaml) as a fifth tracked product; `Connect` keeps its
  docs-only rule and [ADR 0001](0001-deploy-directory.md) stands unchanged.
- If **Option B** is accepted, [ADR 0001](0001-deploy-directory.md) and
  [CONTRIBUTING.md](../../CONTRIBUTING.md) are amended in the same change to permit application
  code, and the drift-check/honesty model is re-designed for a repository that now compiles.
- If the decision is to **defer**, this ADR records that the control-plane app is intentionally
  not yet homed, and the target-product documentation stands as design direction until it is.
