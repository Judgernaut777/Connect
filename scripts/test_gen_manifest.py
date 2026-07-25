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
