# The manifest-driven release model

How this repository keeps its cross-product claims from drifting away from the truth. The
short version: there is exactly one file a human or a script may trust, everything else is
generated from it, and CI refuses to let the two disagree.

## The manifest is the source of truth

**[manifest/ecosystem.yaml](../manifest/ecosystem.yaml)** records, per product: the canonical
GitHub repository name, the local directory it lives in on disk during development, the pinned
git commit, the nearest tag and how many commits `HEAD` sits ahead of it, the package version,
the contract versions it speaks, and the last-verified test gate result (passed / failed /
skipped / collected, plus a free-text `note` for caveats that don't fit a number).

This manifest doubles as the **ecosystem lockfile**. `commit` is what a reproducible build or
deploy should pin — not the tag, which moves, and not `main`, which is a moving target by
definition. See [COMPATIBILITY.md#how-to-pin](../COMPATIBILITY.md#how-to-pin) for the
per-product pinning recipe; the manifest is where those SHAs actually come from.

The manifest is generated. It carries a `generated_note` field explaining exactly that, and a
`generated_at` timestamp. Hand-editing it defeats the point — the whole model rests on the
manifest reflecting live git state, not someone's memory of it.

## Regenerating it: `scripts/gen_manifest.py`

```
python3 scripts/gen_manifest.py                # refresh commits/tags only (fast, git-only)
python3 scripts/gen_manifest.py --run-gates     # also re-run every sibling's gate
python3 scripts/gen_manifest.py --manifest PATH # write somewhere other than the default
```

Without `--run-gates` it touches nothing but git: `git -C <local_dir> rev-parse HEAD` for the
commit, `git -C <local_dir> describe --tags --long` for the tag and how far ahead of it `HEAD`
sits. The existing `tests:` block is carried forward unchanged. This is the mode CI runs — it
does not want to silently re-run four test suites just to check that a doc table is accurate.

With `--run-gates` it additionally re-runs each sibling's own gate and replaces the `tests:`
block with what actually happened this run:

| Product | Gate |
|---|---|
| AgentConnect | `pytest -q` |
| BrainConnect | `python3 tests/acceptance.py` |
| ComputeConnect | `pytest -q --ignore=tests/test_real_engine.py` |
| ToolConnect | `pytest -q` |
| Connect (this repo) | none — docs + deploy bundle, no unit suite |

**One documented hazard:** BrainConnect's acceptance suite manages its own per-check database
isolation. The generator deliberately does **not** export a global `BRAINCONNECT_DB` before
invoking it — doing so breaks that isolation and produces false results. If you're scripting
around this file, keep that constraint.

It is stdlib-only (see [scripts/_manifest_yaml.py](../scripts/_manifest_yaml.py), a deliberately
minimal YAML reader/writer for exactly the subset this manifest needs) so that regenerating the
manifest never requires installing anything beyond Python 3.11 itself.

## The doc tables are generated, not hand-maintained

README.md and COMPATIBILITY.md quote the manifest's version and test-gate numbers in prose and
tables. Every such block is wrapped:

```
<!-- BEGIN generated:tests (source: manifest/ecosystem.yaml — do not hand-edit) -->
...
<!-- END generated:tests -->
```

Anyone regenerating those numbers should replace only the text between the markers, and should
do it from the manifest, not from memory of the last release.

## Drift is a CI failure: `scripts/check_manifest.py`

```
python3 scripts/check_manifest.py                     # checks README.md + COMPATIBILITY.md
python3 scripts/check_manifest.py path/to/other.md     # or specific files
```

It finds every `generated:tests` block, locates each product's segment inside it (a table row
in COMPATIBILITY.md, a sentence fragment in README.md's prose summary — the search is
position-based, not line-based, so both shapes work), and cross-checks the `passed` /
`skipped` / `collected` numbers and any `package_version`-shaped string it finds against
`manifest/ecosystem.yaml`. Any mismatch — a stale count left behind after a manifest refresh,
a table row for a product that's gone missing — is a non-zero exit with a specific complaint,
not a silent pass. This is what makes "the docs say X" actually mean X, instead of meaning
"someone typed X once and nobody has checked since."

It's also stdlib-only, for the same reason as the generator: CI should not need extra
dependencies just to catch a stale number.

## How this ties into CI and releases

**[.github/workflows/ecosystem-ci.yml](../.github/workflows/ecosystem-ci.yml)** checks out this
repository, clones each sibling product at the commit/tag `manifest/ecosystem.yaml` pins, runs
each sibling's offline gate (ComputeConnect's real-engine tests excluded, same as the generator
excludes them), and finally runs `scripts/check_manifest.py`. A stale doc table fails the same
CI run that would catch a broken sibling test — there's one gate, not two.

**[.github/workflows/publish-images.yml](../.github/workflows/publish-images.yml)** builds the
four `deploy/*.Dockerfile` images and pushes them to GHCR when a release tag is pushed. It
checks out each sibling at the exact commit `manifest/ecosystem.yaml` records for that release,
so a published `connect-agentconnect:v0.1.0` image is built from precisely the commit the
manifest says `v0.1.0` was — not from whatever happened to be on a branch tip at build time.

The honest caveat for both workflows: they need the sibling repositories to be public and
clonable by whatever principal runs the workflow, and image publishing specifically needs those
siblings checked out as build contexts at workflow run time — the compose files and Dockerfiles
already assume that layout locally (see [deploy/README.md](../deploy/README.md)); the CI
workflows just automate producing it. Neither workflow has been run in this environment; both
are validated only by parsing (`python3 -c "import yaml; yaml.safe_load(open(...))"`) and by
matching them against the local `deploy/` bundle they drive.

## Why this exists

The Connect ecosystem's whole pitch is that its documentation is checked, not asserted — see
[CONTRIBUTING.md](../CONTRIBUTING.md#the-documentation-standard) and
[MANIFESTO.md](../MANIFESTO.md). Version numbers and test counts are the easiest claims in this
repository to let rot, because nothing fails to compile when they go stale. The manifest and
`check_manifest.py` close that specific gap: the numbers you read in README.md and
COMPATIBILITY.md are either current, or CI is red.
