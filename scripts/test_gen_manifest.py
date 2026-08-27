#!/usr/bin/env python3
"""Regression tests for scripts/gen_manifest.py's count/offset parsing.

Stdlib only (unittest + subprocess), matching the manifest tooling's
zero-third-party-dependency rule. Run with:

    python3 -m unittest scripts/test_gen_manifest.py

These pin two bugs that silently corrupted the generated manifest:

  * parse_pytest_counts: the old single all-optional summary regex matched
    the empty string at offset 0 on normal pytest output, nulling real
    passed/skipped counts, and assumed passed-before-failed ordering.
  * git_tag_and_offset: the describe-fails fallback recorded offset 0
    ("HEAD is at the tag") even when HEAD was several commits past a tag on
    divergent history, contradicting the pinned commit field.
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gen_manifest as gm  # noqa: E402


class ParsePytestCountsTest(unittest.TestCase):
    def test_normal_summary_is_parsed(self) -> None:
        out = "collected 1042 items\n\n....\n1028 passed, 16 skipped in 5.23s\n"
        self.assertEqual(gm.parse_pytest_counts(out), (1028, None, 16))

    def test_failed_before_passed_ordering(self) -> None:
        # pytest prints failures first: "N failed, M passed, K skipped".
        out = "1 failed, 1027 passed, 16 skipped in 5s\n"
        self.assertEqual(gm.parse_pytest_counts(out), (1027, 1, 16))

    def test_no_summary_stays_none(self) -> None:
        self.assertEqual(gm.parse_pytest_counts("collected 0 items\n"), (None, None, None))

    def test_collection_header_does_not_shadow_the_summary(self) -> None:
        """pytest's collection header carries its own `N skipped`.

        "collected 1511 items / 2 skipped" counts modules skipped at
        COLLECTION time. Reading the first match anywhere in the output took
        that 2 as the run's total and silently understated the real 13 --
        which check_manifest.py then enforced into README as the correct
        number.
        """
        out = (
            "plugins: anyio-4.14.2\n"
            "collected 1511 items / 2 skipped\n\n"
            "tests/test_a.py ....s...  [ 50%]\n"
            "======== 1500 passed, 13 skipped, 2 warnings in 57.20s ========\n"
        )
        self.assertEqual(gm.parse_pytest_counts(out), (1500, None, 13))

    def test_deselected_header_does_not_shadow_the_summary(self) -> None:
        out = (
            "collected 200 items / 3 deselected / 197 selected\n"
            "==== 190 passed, 7 skipped, 3 deselected in 2s ====\n"
        )
        self.assertEqual(gm.parse_pytest_counts(out), (190, None, 7))


class FieldOrderTest(unittest.TestCase):
    """The generated file's shape must not depend on registration history.

    Entries are built incrementally and partly carried over from the previous
    manifest, so a key introduced later (`tag` on the untagged control-plane
    repos) was appended after `tests` and gave those products a different
    field order from every other product.
    """

    def test_a_late_added_key_is_emitted_in_canonical_position(self) -> None:
        entry = {"repository": "r", "tests": {"passed": 1}, "tag": None, "commit": "c"}
        self.assertEqual(
            list(gm.in_field_order(entry)),
            ["repository", "commit", "tag", "tests"],
        )

    def test_unrecognized_keys_are_kept_last_not_dropped(self) -> None:
        entry = {"tests": {}, "repository": "r", "future_field": 1}
        ordered = gm.in_field_order(entry)
        self.assertEqual(list(ordered), ["repository", "tests", "future_field"])
        self.assertEqual(ordered["future_field"], 1)


class MissingSiblingCheckoutTest(unittest.TestCase):
    """A sibling that is not cloned here must preserve, never crash.

    Refreshing a subset of the ecosystem is the normal case -- not every host
    clones all seven repositories. The gate subprocess used to raise
    FileNotFoundError on the absent directory and abandon the whole run, so
    one missing sibling blocked regenerating the other six.
    """

    def test_missing_checkout_preserves_the_existing_entry(self) -> None:
        existing = {
            "commit": "e3ff00d69fc2702e2aa2ec27022e093ffc67bb92",
            "tag": "v0.1.0",
            "commits_since_tag": 11,
            "package_version": "0.1.0",
            "maturity": "MVP service",
            "tests": {"runner": "pytest (offline)", "passed": 485, "failed": 0},
        }
        spec = {
            "repository": "Judgernaut777/ToolConnect",
            "local_dir": "../definitely-not-checked-out",
            "gate": {"kind": "pytest", "cwd": "."},
        }
        entry = gm.refresh_product("toolconnect", spec, existing, run_gates=True)
        self.assertEqual(entry["commit"], existing["commit"])
        self.assertEqual(entry["tests"]["passed"], 485)
        self.assertEqual(entry["repository"], "Judgernaut777/ToolConnect")

    def test_missing_checkout_with_no_history_is_still_well_formed(self) -> None:
        spec = {
            "repository": "Judgernaut777/Nowhere",
            "local_dir": "../definitely-not-checked-out",
            "maturity": "seeded from the registry",
            "gate": {"kind": "pytest", "cwd": "."},
        }
        entry = gm.refresh_product("nowhere", spec, {}, run_gates=True)
        self.assertIsNone(entry["commit"])
        self.assertEqual(entry["maturity"], "seeded from the registry")
        self.assertEqual(entry["tests"], {})


class GitTagOffsetFallbackTest(unittest.TestCase):
    def _git(self, repo: Path, *args: str) -> str:
        env = {
            "GIT_AUTHOR_NAME": "t",
            "GIT_AUTHOR_EMAIL": "t@t",
            "GIT_COMMITTER_NAME": "t",
            "GIT_COMMITTER_EMAIL": "t@t",
        }
        return subprocess.run(
            ["git", "-C", str(repo), *args],
            capture_output=True,
            text=True,
            check=True,
            env={**__import__("os").environ, **env},
        ).stdout.strip()

    def test_offset_is_real_distance_when_tag_not_ancestor(self) -> None:
        # Build a repo whose HEAD is on history that diverged from the tag,
        # so `git describe --tags` fails and the fallback path is taken.
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._git(repo, "init", "-q")
            (repo / "f").write_text("root\n")
            self._git(repo, "add", ".")
            self._git(repo, "commit", "-qm", "root")
            root = self._git(repo, "rev-parse", "HEAD")

            # Tagged release on a side branch off root.
            self._git(repo, "checkout", "-qb", "rel")
            (repo / "f").write_text("release\n")
            self._git(repo, "commit", "-aqm", "release")
            self._git(repo, "tag", "v0.1.0")

            # HEAD moves to divergent history that does NOT contain the tag.
            self._git(repo, "checkout", "-q", root)
            self._git(repo, "checkout", "-qb", "work")
            (repo / "f").write_text("work\n")
            self._git(repo, "commit", "-aqm", "work")

            tag, offset = gm.git_tag_and_offset(repo)
            self.assertEqual(tag, "v0.1.0")
            # HEAD is 1 commit past the (divergent) tag, not at it.
            self.assertEqual(offset, 1)


if __name__ == "__main__":
    unittest.main()
