#!/usr/bin/env python3
"""Fail the build when README.md / COMPATIBILITY.md drift from the manifest.

manifest/ecosystem.yaml is the ecosystem's single source of truth for test
gate counts, package versions, maturity strings, and contract versions.
README.md and COMPATIBILITY.md carry human-readable tables and prose derived
from it, each wrapped in a pair of named markers:

    <!-- BEGIN generated:tests (source: manifest/ecosystem.yaml -- do not hand-edit) -->
    ...
    <!-- END generated:tests -->

    <!-- BEGIN generated:contracts (source: manifest/ecosystem.yaml -- do not hand-edit) -->
    ...
    <!-- END generated:contracts -->

A file may contain more than one `generated:tests` block (e.g. a version/
maturity table plus a separate test-count paragraph) -- every block is
checked, not just the first one that mentions a product.

Inside a `generated:tests` block, for each product row this checks (whichever
the manifest has non-None values for): test counts (passed/skipped/collected),
package_version (only once the row shows *some* version-shaped string, so a
test-counts-only paragraph is not required to also state a version), and
maturity (only once the row shows a version-shaped string too, since maturity
is always presented alongside version in these tables; matched
case-insensitively so "Release candidate" at a sentence/cell start doesn't
count as drift against the manifest's "release candidate").

Inside a `generated:contracts` block, every backtick-wrapped `X.Y`-shaped
token must be a contract version that actually appears somewhere in the
manifest's `contract_versions`, and every contract version the manifest
carries must appear somewhere in the block -- this catches both a stale
number and a silently-dropped one.

This script extracts the numbers quoted inside each marked block and
compares them against manifest/ecosystem.yaml. Any drift -- a stale test
count, a version string that no longer matches, a stale maturity label, an
unknown or missing contract version -- is a nonzero exit, which is what makes
the docs un-driftable in CI.

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
    # Anchored to start-of-line (optional leading whitespace) so prose that
    # merely *quotes* the marker syntax as an example -- e.g. inside a code
    # span like `<!-- BEGIN generated:tests --> ... <!-- END generated:tests -->`
    # embedded mid-sentence -- cannot be mistaken for a real generated block.
    # A genuine marker always occupies its own line; quoted-syntax prose does
    # not start the line with the literal comment.
    r"^[ \t]*<!--\s*BEGIN generated:(?P<name>[\w-]+)[^>]*-->(?P<body>.*?)"
    r"^[ \t]*<!--\s*END generated:(?P=name)\s*-->",
    re.DOTALL | re.MULTILINE,
)


class Drift(list):
    def add(self, msg: str) -> None:
        self.append(msg)


def extract_generated_blocks(text: str) -> list[tuple[str, str]]:
    """Return (marker_name, body) for every generated:* block in `text`."""
    return [(m.group("name"), m.group("body")) for m in _MARKER_RE.finditer(text)]


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


# Bare X.Y.Z, plus the PEP 440 pre/post-release suffixes this ecosystem
# actually uses (e.g. "0.1.2rc1"). Without the optional suffix group, a
# manifest package_version like "0.1.2rc1" never matches this pattern (no
# `\b` between the digit and the letter "r"), so the version-claim gate below
# never opens and that product's version silently goes unchecked -- exactly
# the kind of doc drift this script exists to catch.
_SEMVER_RE = re.compile(r"\b\d+\.\d+\.\d+(?:(?:rc|a|b|post|dev)\d+)?\b")


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


def check_maturity(row: str, maturity: str | None, product_key: str, drift: Drift, source: str) -> None:
    if not maturity:
        return
    if not _SEMVER_RE.search(row):
        # Same gate as check_version: only rows that already make a version
        # claim are expected to also state maturity (a test-counts-only
        # paragraph never does). Case-insensitive because a doc naturally
        # capitalizes "Release candidate" as a sentence/cell opener while the
        # manifest stores the lowercase "release candidate".
        return
    if maturity.lower() not in row.lower():
        drift.add(
            f"{source}: {product_key} maturity {maturity!r} not found in doc row: "
            f"{row.strip()!r}"
        )


_CONTRACT_VERSION_RE = re.compile(r"`(\d+\.\d+)`")


def all_contract_versions(manifest: dict) -> set[str]:
    versions: set[str] = set()
    for entry in manifest.get("products", {}).values():
        versions.update(entry.get("contract_versions", {}).values())
    return versions


def check_contracts(block: str, manifest: dict, drift: Drift, source: str) -> None:
    known = all_contract_versions(manifest)
    if not known:
        return
    found = set(_CONTRACT_VERSION_RE.findall(block))
    for version in sorted(found - known):
        drift.add(
            f"{source}: generated:contracts block cites contract version "
            f"`{version}`, which matches no product's contract_versions in the "
            f"manifest (known: {sorted(known)})"
        )
    missing = sorted(known - found)
    if missing:
        drift.add(
            f"{source}: generated:contracts block is missing manifest contract "
            f"version(s) {missing}"
        )


def check_file(path: Path, manifest: dict, drift: Drift) -> None:
    if not path.exists():
        drift.add(f"{path}: file not found")
        return
    text = path.read_text()
    blocks = extract_generated_blocks(text)
    tests_blocks = [body for name, body in blocks if name == "tests"]
    contracts_blocks = [body for name, body in blocks if name == "contracts"]
    if not tests_blocks:
        drift.add(
            f"{path}: no '<!-- BEGIN generated:tests ... -->' block found -- "
            "docs cannot be checked against the manifest"
        )
    if not contracts_blocks:
        drift.add(
            f"{path}: no '<!-- BEGIN generated:contracts ... -->' block found "
            "-- contract versions cannot be checked against the manifest"
        )
    if not tests_blocks and not contracts_blocks:
        return

    products = manifest.get("products", {})
    for key, display_name in DISPLAY_NAMES.items():
        entry = products.get(key)
        if not entry:
            continue
        found_any = False
        # Check every block that mentions this product, not just the first --
        # a doc may split a version/maturity table and a test-count paragraph
        # into separate generated:tests blocks, and each check below is a
        # no-op on a block that doesn't state the field it's checking.
        for block in tests_blocks:
            row = row_for_product(block, display_name)
            if row is None:
                continue
            found_any = True
            check_counts(row, entry.get("tests", {}), key, drift, str(path))
            check_version(row, entry.get("package_version"), key, drift, str(path))
            check_maturity(row, entry.get("maturity"), key, drift, str(path))
        if not found_any:
            drift.add(f"{path}: no generated:tests block row mentions {display_name}")

    for block in contracts_blocks:
        check_contracts(block, manifest, drift, str(path))


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
