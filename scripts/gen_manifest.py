#!/usr/bin/env python3
"""Generate manifest/ecosystem.yaml, the Connect ecosystem's source of truth.

For every product this walks the sibling checkout on disk (using the LOCAL
directory name -- `mcp-agentconnect`, `WikiBrain` -- because that is what
exists on the filesystem) and records the CANONICAL GitHub repository name
(`Judgernaut777/AgentConnect`, `Judgernaut777/BrainConnect`) into the
manifest's `repository` field. It always refreshes `commit` (`git rev-parse
HEAD`) and `tag` / `commits_since_tag` (`git describe --tags`).

By default it does NOT run any sibling's test suite -- it only touches git
and preserves whatever `tests:` block was already on disk. Pass
`--run-gates` to also re-run each sibling's gate and refresh the test
counts. This is deliberately opt-in: gates are slow, and a bad local
checkout state (uncommitted changes, wrong branch) should never silently
poison the pinned numbers.

Stdlib only -- no PyYAML, no third-party packages. See
`_manifest_yaml.py` for the minimal YAML subset this manifest uses.

Usage:
    python3 scripts/gen_manifest.py                 # refresh git SHAs/tags only
    python3 scripts/gen_manifest.py --run-gates      # also re-run gates
    python3 scripts/gen_manifest.py --manifest PATH  # write elsewhere
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _manifest_yaml as myaml  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_MANIFEST_PATH = REPO_ROOT / "manifest" / "ecosystem.yaml"

# Product registry: the one place that maps a manifest key to where its
# checkout lives on disk, its canonical GitHub name, and how its gate is
# invoked. Local dir names intentionally do not match the canonical
# product name for agentconnect (mcp-agentconnect) and brainconnect
# (WikiBrain) -- both repos are mid-rename on disk.
PRODUCTS: dict[str, dict] = {
    "agentconnect": {
        "repository": "Judgernaut777/AgentConnect",
        "local_dir": "../mcp-agentconnect",
        "gate": {
            "kind": "pytest",
            "cwd": ".",
            "note": (
                "Pass/skip counts are environment-dependent: sibling "
                "BrainConnect/WikiBrain checkout, fascia-guard, "
                "trufflehog/gitleaks binaries, and optional extras (litellm, "
                "temporalio, langgraph-checkpoint-sqlite, detect-secrets) "
                "each unlock more tests when present."
            ),
        },
    },
    "brainconnect": {
        "repository": "Judgernaut777/BrainConnect",
        "local_dir": "../WikiBrain",
        "gate": {
            "kind": "acceptance",
            "cwd": ".",
            "script": "tests/acceptance.py",
            "note": (
                "Do not set a global BRAINCONNECT_DB when running this gate "
                "-- it breaks per-check isolation. Check count varies with "
                "optional extras (the mixed-model embeddings checks self-skip "
                "without the [semantic] extra's numpy)."
            ),
        },
    },
    "computeconnect": {
        "repository": "Judgernaut777/ComputeConnect",
        "local_dir": "../ComputeConnect",
        "gate": {
            "kind": "pytest",
            "cwd": ".",
            "extra_args": ["--ignore=tests/test_real_engine.py"],
            "note": (
                "11 real-engine tests are excluded from the offline count; "
                "they need a live llama.cpp on :8080 and read their expected "
                "model ids from CC_REAL_MODEL / CC_REAL_MODEL_B (defaults "
                "track the current host deployment)."
            ),
        },
    },
    "toolconnect": {
        "repository": "Judgernaut777/ToolConnect",
        "local_dir": "../ToolConnect",
        "gate": {"kind": "pytest", "cwd": "."},
    },
    "connect": {
        "repository": "Judgernaut777/Connect",
        "local_dir": ".",
        "gate": None,  # docs + deploy bundle; no unit test suite
    },
    # The two control-plane repositories. They are not planes -- ADR 0002 makes
    # Connect-Control a *consumer* of this manifest -- but they ship code, carry
    # gates, and are released, so leaving them unpinned meant two of the six
    # repositories had no recorded commit, version, or gate anywhere.
    "connect-control": {
        "repository": "Judgernaut777/Connect-Control",
        "local_dir": "../Connect-Control",
        "maturity": (
            "R8 (four server-rendered surfaces + curated marketplace; "
            "workspaces, onboarding, and budgets do not exist)"
        ),
        "gate": {
            "kind": "pytest",
            "cwd": ".",
            "note": (
                "Offline count only. Five of the seven test modules skip "
                "wholesale without the `audit` extra, which needs sibling "
                "packages that are not on PyPI (connect-governance[app], "
                "agentconnect-core, toolconnect) -- so the marketplace, "
                "audit-projection, decision, and work-request route tests do "
                "not run in a standalone checkout."
            ),
        },
    },
    "connect-governance": {
        "repository": "Judgernaut777/Connect-Governance",
        "local_dir": "../Connect-Governance",
        "maturity": (
            "R8 (Decision Kernel, governed state, decision records, grants, "
            "marketplace classification)"
        ),
        "gate": {
            "kind": "pytest",
            "cwd": ".",
            "note": (
                "Needs the [app] extra: the Kernel itself depends only on "
                "pydantic, but the persistence, migration, and grant-signing "
                "tests import SQLAlchemy, Alembic, and cryptography."
            ),
        },
    },
}

# The order fields are emitted in. Entry dicts are built incrementally (and
# partly carried over from the previous manifest), so insertion order alone
# would append a newly-introduced key after `tests` and make the generated
# file's shape depend on when each product was first registered.
FIELD_ORDER = (
    "repository",
    "local_dir",
    "commit",
    "tag",
    "commits_since_tag",
    "package_version",
    "maturity",
    "note",
    "contract_versions",
    "tests",
)


def in_field_order(entry: dict) -> dict:
    """Reorder an entry into FIELD_ORDER, keeping any unrecognized keys last."""
    ordered = {k: entry[k] for k in FIELD_ORDER if k in entry}
    ordered.update({k: v for k, v in entry.items() if k not in ordered})
    return ordered


_PYTEST_COLLECTED_RE = re.compile(r"collected (\d+) item")
_ACCEPTANCE_RESULT_RE = re.compile(r"RESULT:\s*(\d+)\s*passed,\s*(\d+)\s*failed")


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd, cwd=str(cwd), capture_output=True, text=True, check=False
    )


def git_commit(local_dir: Path) -> str | None:
    proc = run(["git", "-C", str(local_dir), "rev-parse", "HEAD"], cwd=REPO_ROOT)
    if proc.returncode != 0:
        return None
    return proc.stdout.strip()


def git_tag_and_offset(local_dir: Path) -> tuple[str | None, int]:
    """Return (nearest_tag, commits_since_tag) via `git describe --tags`."""
    proc = run(
        ["git", "-C", str(local_dir), "describe", "--tags", "--long"], cwd=REPO_ROOT
    )
    if proc.returncode != 0:
        # `git describe` fails when no tag is an ancestor of HEAD (HEAD sits
        # on history that diverged from every tag). Fall back to the newest
        # tag in the repo and record the REAL distance from that tag to HEAD
        # via `git rev-list --count <tag>..HEAD`. Recording 0 here would read
        # as "HEAD is at the release tag" -- false when HEAD is off on a
        # divergent branch -- and would silently contradict the commit field.
        proc2 = run(
            ["git", "-C", str(local_dir), "tag", "--sort=-creatordate"], cwd=REPO_ROOT
        )
        tags = [t for t in proc2.stdout.splitlines() if t.strip()]
        if not tags:
            return None, 0
        tag = tags[0]
        proc3 = run(
            ["git", "-C", str(local_dir), "rev-list", "--count", f"{tag}..HEAD"],
            cwd=REPO_ROOT,
        )
        offset = int(proc3.stdout.strip()) if proc3.returncode == 0 else 0
        return tag, offset
    described = proc.stdout.strip()
    m = re.match(r"^(?P<tag>.+)-(?P<n>\d+)-g[0-9a-f]+$", described)
    if not m:
        return described, 0
    return m.group("tag"), int(m.group("n"))


def parse_pytest_counts(output: str) -> tuple[int | None, int | None, int | None]:
    """Return (passed, failed, skipped) parsed from a pytest run's output.

    Each keyword is searched for independently rather than with one combined
    pattern: a single all-optional regex matches the empty string at offset 0
    on normal output (every group None), and any fixed ordering breaks on
    pytest's real "N failed, M passed, K skipped" summary. Independent
    searches cannot match zero-width and are order-independent. A missing
    keyword stays None so a real count is never silently overwritten.

    The LAST occurrence of each keyword wins, not the first. pytest's
    collection header carries a count of its own -- "collected 1511 items /
    2 skipped" names the modules skipped at COLLECTION time, not the run's
    total -- and taking the first match let that 2 shadow the summary line's
    real 13, understating every product whose collection skips a module. The
    terminal summary is always the last thing pytest prints, so reading from
    the end is what makes this the authoritative number.
    """
    def find(keyword: str) -> int | None:
        matches = re.findall(rf"(\d+) {keyword}", output)
        return int(matches[-1]) if matches else None

    return find("passed"), find("failed"), find("skipped")


def gate_python(local_dir: Path) -> str:
    """The sibling's own .venv interpreter when it has one, else python3.

    Bare python3 only works where a combined all-products environment is on
    PATH (the CI/cloud configuration); on a dev host each sibling carries its
    deps in its own .venv and the system interpreter would fail collection.
    """
    venv_python = local_dir / ".venv" / "bin" / "python"
    return str(venv_python) if venv_python.exists() else "python3"


def run_pytest_gate(
    local_dir: Path, extra_args: list[str] | None, note: str | None
) -> dict:
    # No -q here: siblings that set addopts = "-q" would end up at -qq, which
    # suppresses the summary line entirely and leaves every count None.
    cmd = [gate_python(local_dir), "-m", "pytest", *(extra_args or [])]
    proc = run(cmd, cwd=local_dir)
    output = proc.stdout + "\n" + proc.stderr
    collected = None
    passed, failed, skipped = parse_pytest_counts(output)
    cm = _PYTEST_COLLECTED_RE.search(output)
    if cm:
        collected = int(cm.group(1))
    return {
        "runner": "pytest (offline)",
        "collected": collected,
        "passed": passed,
        "failed": failed if failed is not None else 0,
        "skipped": skipped,
        "note": note if proc.returncode == 0 else "gate exited non-zero; inspect output",
    }


def read_package_version(local_dir: Path) -> str | None:
    """[project].version from the sibling's pyproject.toml, or None.

    The manifest claims to be the source of truth for package versions, so
    refresh them from the checkout instead of preserving whatever was last
    written -- preservation is how the BrainConnect tag/package mismatch
    went unnoticed across two rc tags.
    """
    pyproject = local_dir / "pyproject.toml"
    if not pyproject.exists():
        return None
    try:
        import tomllib

        data = tomllib.loads(pyproject.read_text())
    except Exception:
        return None
    version = data.get("project", {}).get("version")
    return str(version) if version is not None else None


def run_acceptance_gate(local_dir: Path, script: str, note: str | None) -> dict:
    # Deliberately do NOT set a global BRAINCONNECT_DB here -- acceptance.py
    # manages its own per-check isolation and a global override breaks it.
    cmd = ["python3", script]
    proc = run(cmd, cwd=local_dir)
    output = proc.stdout + "\n" + proc.stderr
    m = _ACCEPTANCE_RESULT_RE.search(output)
    passed = int(m.group(1)) if m else None
    failed = int(m.group(2)) if m else None
    return {
        "runner": f"python3 {script}",
        "collected": None,
        "passed": passed,
        "failed": failed if failed is not None else 0,
        "skipped": None,
        "note": note if proc.returncode == 0 else "gate exited non-zero; inspect output",
    }


def refresh_product(
    key: str, spec: dict, existing: dict, run_gates: bool
) -> dict:
    local_dir = (REPO_ROOT / spec["local_dir"]).resolve()
    entry = dict(existing) if existing else {}
    entry["repository"] = spec["repository"]
    entry["local_dir"] = spec["local_dir"]

    # A sibling that is not checked out here keeps whatever the manifest
    # already recorded. Refreshing a subset of the ecosystem is the normal
    # case -- not every host clones all seven repositories -- and it must
    # degrade to "preserve", never to a crash (a missing checkout used to
    # raise FileNotFoundError out of the gate subprocess and abandon the
    # whole run, so one absent sibling blocked regenerating the other six).
    if not local_dir.is_dir():
        entry.setdefault("commit", None)
        entry.setdefault("tag", None)
        entry.setdefault("commits_since_tag", 0)
        entry.setdefault("package_version", None)
        entry.setdefault("maturity", spec.get("maturity"))
        entry.setdefault("note", None)
        entry.setdefault("contract_versions", {})
        entry.setdefault("tests", {})
        return in_field_order(entry)

    commit = git_commit(local_dir)
    if commit:
        entry["commit"] = commit
    tag, offset = git_tag_and_offset(local_dir)
    if tag:
        entry["tag"] = tag
        entry["commits_since_tag"] = offset

    package_version = read_package_version(local_dir)
    if package_version is not None:
        entry["package_version"] = package_version
    entry.setdefault("package_version", None)
    # An untagged product (the control-plane repos ship milestones, not tags)
    # still carries the keys, so a consumer reading the manifest as a lockfile
    # gets an explicit null rather than a KeyError.
    entry.setdefault("tag", None)
    entry.setdefault("commits_since_tag", 0)
    entry.setdefault("maturity", spec.get("maturity"))
    entry.setdefault("note", None)
    entry.setdefault("contract_versions", {})
    entry.setdefault("tests", {})

    if run_gates and spec.get("gate"):
        gate = spec["gate"]
        if gate["kind"] == "pytest":
            entry["tests"] = run_pytest_gate(
                local_dir, gate.get("extra_args"), gate.get("note")
            )
        elif gate["kind"] == "acceptance":
            entry["tests"] = run_acceptance_gate(
                local_dir, gate["script"], gate.get("note")
            )

    return in_field_order(entry)


def build_manifest(existing: dict | None, run_gates: bool) -> dict:
    existing_products = (existing or {}).get("products", {})
    manifest = {
        "release": (existing or {}).get("release", "0.1.0"),
        "generated_note": (
            "This file is generated by scripts/gen_manifest.py and is the "
            "ecosystem source of truth for product commits, tags, package "
            "versions, contract versions, and last-verified test gate "
            "counts. It doubles as the ecosystem lockfile: pin the exact "
            "commit field, not a floating tag or branch. Do not hand-edit "
            "outside of the documented generated_at placeholder; run the "
            "generator instead."
        ),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "products": {},
    }
    for key, spec in PRODUCTS.items():
        manifest["products"][key] = refresh_product(
            key, spec, existing_products.get(key, {}), run_gates
        )
    return manifest


def load_existing(path: Path) -> dict | None:
    if not path.exists():
        return None
    try:
        return myaml.load(path.read_text())
    except Exception:
        return None


def write_manifest(manifest: dict, path: Path) -> None:
    header = (
        "# Connect ecosystem manifest -- generated, do not hand-edit.\n"
        "# Regenerate with: python3 scripts/gen_manifest.py\n"
        "# Add --run-gates to also refresh test counts by re-running each\n"
        "# sibling product's gate. Without it, only git commits/tags refresh\n"
        "# and existing test counts are preserved.\n"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(header + myaml.dump(manifest))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Generate manifest/ecosystem.yaml: refreshes each sibling "
            "product's pinned commit and tag from git, and (with "
            "--run-gates) re-runs each sibling's gate to refresh test "
            "counts."
        )
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=DEFAULT_MANIFEST_PATH,
        help=f"path to write (default: {DEFAULT_MANIFEST_PATH})",
    )
    parser.add_argument(
        "--run-gates",
        action="store_true",
        help="also re-run each sibling's test gate and refresh test counts "
        "(slow; requires the sibling checkouts to have their deps installed)",
    )
    args = parser.parse_args(argv)

    existing = load_existing(args.manifest)
    manifest = build_manifest(existing, args.run_gates)
    write_manifest(manifest, args.manifest)
    print(f"wrote {args.manifest}")
    for key, entry in manifest["products"].items():
        print(f"  {key}: commit={entry.get('commit')} tag={entry.get('tag')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
