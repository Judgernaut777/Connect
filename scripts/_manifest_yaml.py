"""Minimal, stdlib-only YAML reader/writer for the ecosystem manifest.

`gen_manifest.py` and `check_manifest.py` must have zero third-party
dependencies, so this module implements only the subset of YAML the
manifest actually needs: block mappings nested by two-space indentation,
with scalar leaves that are JSON-quoted strings, bare integers, `true` /
`false`, or `null`. No sequences, no flow style, no multi-line scalars.

The output is still valid, standard YAML — `yaml.safe_load()` parses it
identically to `load()` below. Round-tripped by
`tests/test_manifest_yaml_roundtrip` equivalent checks in check_manifest.py
(see its self-check on import).
"""
from __future__ import annotations

import json
import re
from typing import Any

_INT_RE = re.compile(r"^-?\d+$")

__all__ = ["dump", "load"]


def dump(obj: dict) -> str:
    """Serialize a nested dict of scalars to block-style YAML text."""
    lines: list[str] = []
    _dump_mapping(obj, 0, lines)
    return "\n".join(lines) + "\n"


def load(text: str) -> dict:
    """Parse block-style YAML text produced by `dump()` back into a dict."""
    entries: list[tuple[int, str]] = []
    for raw in text.splitlines():
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        entries.append((indent, stripped))
    root, idx = _load_block(entries, 0, 0)
    if idx != len(entries):
        raise ValueError(f"trailing unparsed content at entry {idx}")
    return root


# --- internals ---------------------------------------------------------


def _dump_scalar(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, str):
        return json.dumps(value)
    raise TypeError(f"unsupported manifest scalar type: {type(value)!r}")


def _dump_mapping(mapping: dict, indent: int, lines: list[str]) -> None:
    pad = " " * indent
    for key, value in mapping.items():
        if isinstance(value, dict):
            if value:
                lines.append(f"{pad}{key}:")
                _dump_mapping(value, indent + 2, lines)
            else:
                lines.append(f"{pad}{key}: {{}}")
        else:
            lines.append(f"{pad}{key}: {_dump_scalar(value)}")


def _parse_scalar(text: str) -> Any:
    text = text.strip()
    if text in ("", "null", "~"):
        return None
    if text == "true":
        return True
    if text == "false":
        return False
    if text == "{}":
        return {}
    if text.startswith('"') and text.endswith('"'):
        return json.loads(text)
    if text.startswith("'") and text.endswith("'") and len(text) >= 2:
        return text[1:-1]
    if _INT_RE.match(text):
        return int(text)
    return text


def _load_block(
    entries: list[tuple[int, str]], idx: int, indent: int
) -> tuple[dict, int]:
    result: dict[str, Any] = {}
    n = len(entries)
    while idx < n:
        cur_indent, line = entries[idx]
        if cur_indent < indent:
            break
        if cur_indent > indent:
            raise ValueError(f"unexpected indent at line: {line!r}")
        if ":" not in line:
            raise ValueError(f"expected 'key: value' at line: {line!r}")
        key, _, rest = line.partition(":")
        key = key.strip()
        rest = rest.strip()
        if rest == "":
            idx += 1
            if idx < n and entries[idx][0] > indent:
                nested, idx = _load_block(entries, idx, entries[idx][0])
                result[key] = nested
            else:
                result[key] = {}
            continue
        result[key] = _parse_scalar(rest)
        idx += 1
    return result, idx
