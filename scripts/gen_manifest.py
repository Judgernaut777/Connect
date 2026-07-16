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
        "gate": {"kind": "pytest", "cwd": "."},
    },
    "brainconnect": {
        "repository": "Judgernaut777/BrainConnect",
        "local_dir": "../WikiBrain",
        "gate": {"kind": "acceptance", "cwd": ".", "script": "tests/acceptance.py"},
    },
    "computeconnect": {
        "repository": "Judgernaut777/ComputeConnect",
        "local_dir": "../ComputeConnect",
        "gate": {
            "kind": "pytest",
            "cwd": ".",
            "extra_args": ["--ignore=tests/test_real_engine.py"],
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
}

_PYTEST_SUMMARY_RE = re.compile(
    r"(?:(?P<passed>\d+) passed)?"
    r"(?:.*?(?P<failed>\d+) failed)?"
    r"(?:.*?(?P<skipped>\d+) skipped)?",
)
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
        # No tags reachable at all -- fall back to the newest tag in the repo,
        # if any, with an unknown offset recorded as 0 rather than fabricated.
        proc2 = run(
            ["git", "-C", str(local_dir), "tag", "--sort=-creatordate"], cwd=REPO_ROOT
        )
        tags = [t for t in proc2.stdout.splitlines() if t.strip()]
        return (tags[0] if tags else None), 0
    described = proc.stdout.strip()
    m = re.match(r"^(?P<tag>.+)-(?P<n>\d+)-g[0-9a-f]+$", described)
    if not m:
        return described, 0
    return m.group("tag"), int(m.group("n"))


def run_pytest_gate(local_dir: Path, extra_args: list[str] | None) -> dict:
    cmd = ["python3", "-m", "pytest", "-q", *(extra_args or [])]
    proc = run(cmd, cwd=local_dir)
    output = proc.stdout + "\n" + proc.stderr
    passed = failed = skipped = collected = None
    m = _PYTEST_SUMMARY_RE.search(output)
    if m:
        passed = int(m.group("passed")) if m.group("passed") else None
        failed = int(m.group("failed")) if m.group("failed") else None
        skipped = int(m.group("skipped")) if m.group("skipped") else None
    cm = _PYTEST_COLLECTED_RE.search(output)
    if cm:
        collected = int(cm.group(1))
    return {
        "runner": "pytest (offline)",
        "collected": collected,
        "passed": passed,
        "failed": failed if failed is not None else 0,
        "skipped": skipped,
        "note": None if proc.returncode == 0 else "gate exited non-zero; inspect output",
    }


def run_acceptance_gate(local_dir: Path, script: str) -> dict:
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
        "note": None if proc.returncode == 0 else "gate exited non-zero; inspect output",
    }


def refresh_product(
    key: str, spec: dict, existing: dict, run_gates: bool
) -> dict:
    local_dir = (REPO_ROOT / spec["local_dir"]).resolve()
    entry = dict(existing) if existing else {}
    entry["repository"] = spec["repository"]
    entry["local_dir"] = spec["local_dir"]

    commit = git_commit(local_dir)
    if commit:
        entry["commit"] = commit
    tag, offset = git_tag_and_offset(local_dir)
    if tag:
        entry["tag"] = tag
        entry["commits_since_tag"] = offset

    entry.setdefault("package_version", None)
    entry.setdefault("maturity", None)
    entry.setdefault("note", None)
    entry.setdefault("contract_versions", {})
    entry.setdefault("tests", {})

    if run_gates and spec.get("gate"):
        gate = spec["gate"]
        if gate["kind"] == "pytest":
            entry["tests"] = run_pytest_gate(local_dir, gate.get("extra_args"))
        elif gate["kind"] == "acceptance":
            entry["tests"] = run_acceptance_gate(local_dir, gate["script"])

    return entry


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
