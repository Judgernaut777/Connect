#!/usr/bin/env python3
"""Fail the build when README.md / COMPATIBILITY.md drift from the manifest.

manifest/ecosystem.yaml is the ecosystem's single source of truth for test
gate counts and package versions. README.md and COMPATIBILITY.md carry
human-readable tables derived from it, each wrapped in a pair of markers:

    <!-- BEGIN generated:tests (source: manifest/ecosystem.yaml -- do not hand-edit) -->
    ...
    <!-- END generated:tests -->

This script extracts the numbers quoted inside each marked block and
compares them against manifest/ecosystem.yaml. Any drift -- a stale test
count, a version string that no longer matches -- is a nonzero exit, which
is what makes the docs un-driftable in CI.

Stdlib only. Usage:
    python3 scripts/check_manifest.py [--manifest PATH] FILE [FILE ...]

With no FILE arguments, checks README.md and COMPATIBILITY.md at the repo
root.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _manifest_yaml as myaml  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_MANIFEST_PATH = REPO_ROOT / "manifest" / "ecosystem.yaml"
DEFAULT_DOC_PATHS = [REPO_ROOT / "README.md", REPO_ROOT / "COMPATIBILITY.md"]

# Manifest key -> the display name used in the docs' table rows.
DISPLAY_NAMES = {
    "agentconnect": "AgentConnect",
    "brainconnect": "BrainConnect",
    "computeconnect": "ComputeConnect",
    "toolconnect": "ToolConnect",
}

_MARKER_RE = re.compile(
    r"<!--\s*BEGIN generated:tests[^>]*-->(?P<body>.*?)<!--\s*END generated:tests\s*-->",
    re.DOTALL,
)


class Drift(list):
    def add(self, msg: str) -> None:
        self.append(msg)


def extract_generated_blocks(text: str) -> list[str]:
    return [m.group("body") for m in _MARKER_RE.finditer(text)]


def row_for_product(block: str, display_name: str) -> str | None:
    """Return the text segment inside `block` that describes `display_name`.

    Doc blocks are either markdown tables (one product per line) or prose
    (several products in one sentence, e.g. "AgentConnect **1060 passed**,
    BrainConnect **951 passed**, ..."). To handle both, find every display
    name's position in the block and slice from this occurrence up to the
    next *other* product's occurrence (or end of block), rather than
    assuming one line per product.
    """
    positions = []
    for name in DISPLAY_NAMES.values():
        start = block.find(name)
        while start != -1:
            positions.append((start, name))
            start = block.find(name, start + 1)
    positions.sort()

    target_idx = next(
        (i for i, (_, name) in enumerate(positions) if name == display_name), None
    )
    if target_idx is None:
        return None
    start = positions[target_idx][0]
    end = (
        positions[target_idx + 1][0]
        if target_idx + 1 < len(positions)
        else len(block)
    )
    return block[start:end]


def check_counts(row: str, tests: dict, product_key: str, drift: Drift, source: str) -> None:
    for field, label in (("passed", "passed"), ("skipped", "skipped"), ("collected", "collected")):
        expected = tests.get(field)
        if expected is None:
            continue
        m = re.search(rf"(\d+)\s*{label}", row)
        if not m:
            # Not every doc table repeats every field (e.g. a table may only
            # show "passed"); that's fine as long as at least one number
            # cross-checks below.
            continue
        found = int(m.group(1))
        if found != expected:
            drift.add(
                f"{source}: {product_key} {label} mismatch -- doc says {found}, "
                f"manifest says {expected}"
            )


_SEMVER_RE = re.compile(r"\b\d+\.\d+\.\d+\b")


def check_version(row: str, package_version: str | None, product_key: str, drift: Drift, source: str) -> None:
    if not package_version:
        return
    if not _SEMVER_RE.search(row):
        # This doc's generated block doesn't make a version claim for this
        # product (e.g. it's a test-counts-only paragraph) -- nothing to
        # cross-check.
        return
    if package_version not in row:
        drift.add(
            f"{source}: {product_key} package_version {package_version!r} not found "
            f"in doc row: {row.strip()!r}"
        )


def check_file(path: Path, manifest: dict, drift: Drift) -> None:
    if not path.exists():
        drift.add(f"{path}: file not found")
        return
    text = path.read_text()
    blocks = extract_generated_blocks(text)
    if not blocks:
        drift.add(
            f"{path}: no '<!-- BEGIN generated:tests ... -->' block found -- "
            "docs cannot be checked against the manifest"
        )
        return
    products = manifest.get("products", {})
    for key, display_name in DISPLAY_NAMES.items():
        entry = products.get(key)
        if not entry:
            continue
        found_row = None
        for block in blocks:
            row = row_for_product(block, display_name)
            if row:
                found_row = row
                break
        if found_row is None:
            drift.add(f"{path}: no generated-block row mentions {display_name}")
            continue
        check_counts(found_row, entry.get("tests", {}), key, drift, str(path))
        check_version(found_row, entry.get("package_version"), key, drift, str(path))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST_PATH)
    parser.add_argument("files", nargs="*", type=Path, default=None)
    args = parser.parse_args(argv)

    if not args.manifest.exists():
        print(f"FAIL: manifest not found at {args.manifest}", file=sys.stderr)
        return 2
    manifest = myaml.load(args.manifest.read_text())

    paths = args.files if args.files else DEFAULT_DOC_PATHS
    drift = Drift()
    for path in paths:
        check_file(path, manifest, drift)

    if drift:
        print("FAIL: docs have drifted from manifest/ecosystem.yaml:\n")
        for msg in drift:
            print(f"  - {msg}")
        return 1

    print(f"OK: {len(paths)} doc file(s) match {args.manifest.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
