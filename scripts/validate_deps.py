#!/usr/bin/env python3
"""
validate_deps.py — build the required-dependency DAG from each module's
SKILL.md frontmatter, fail on cycles or unknown references.

This is the *skill-repo-side* check, not a data-repo operation. It walks
`{repo_root}/modules/` and inspects each `SKILL.md`'s YAML frontmatter for
`requires:` (and `optional:`, which we report but don't validate — optional
deps may form cycles per the architecture docs).

Invoked by the pre-commit hook when any module's `SKILL.md` changes, and
runnable on demand for debugging the dependency graph.

Contract (exit codes — note this differs from scan.py's contract):
- Exit 0: no cycles, no unknown required deps. Graph report printed to stdout.
- Exit 1: at least one cycle or unknown required dep detected. Report still
  printed to stdout (diagnostic); pre-commit hook fails the commit.
- Exit 2: operational error (crash) — bad args, unreadable files, etc.

Usage:
    uv run python scripts/validate_deps.py --args '{}'
    uv run python scripts/validate_deps.py --args '{"repo_root": "/abs/path"}'

Args (JSON object):
    repo_root: string, optional. Overrides the auto-detected repo root. The
               script computes the repo root from its own location by default
               (scripts/validate_deps.py → parent of scripts/ is the repo).

Output shape (stdout, always JSON):
    {
      "modules": ["personal-os", "team-management", ...],
      "edges":   [["board-comms", "business-alignment"], ...],
      "cycles":  [["a", "b", "c", "a"], ...],      // empty when clean
      "unknown_required_deps": [                      // empty when clean
        {"module": "board-comms", "requires": "no-such-module"}
      ]
    }
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

import yaml


# ---------- Errors ----------


class ValidationCrash(Exception):
    """Surfaced as exit 2 — the script itself couldn't operate."""


# ---------- Frontmatter parsing (matches scan.py) ----------

_FRONTMATTER_PATTERN = re.compile(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", re.DOTALL)


def _parse_frontmatter(raw: str) -> dict[str, Any] | None:
    match = _FRONTMATTER_PATTERN.match(raw)
    if not match:
        return None
    try:
        fm = yaml.safe_load(match.group(1)) or {}
    except yaml.YAMLError:
        return None
    return fm if isinstance(fm, dict) else None


# ---------- Graph construction ----------


def _repo_root_default() -> Path:
    """scripts/validate_deps.py lives at {repo_root}/scripts/validate_deps.py."""
    return Path(__file__).resolve().parent.parent


def _collect_modules(
    repo_root: Path,
) -> tuple[list[str], dict[str, list[str]], dict[str, list[str]]]:
    """Walk repo_root/modules and collect each module's requires + optional lists.

    Returns:
        (module_slugs, requires_map, optional_map)
    """
    modules_dir = repo_root / "modules"
    if not modules_dir.is_dir():
        return [], {}, {}

    slugs: list[str] = []
    requires_map: dict[str, list[str]] = {}
    optional_map: dict[str, list[str]] = {}

    for module_dir in sorted(modules_dir.iterdir()):
        if not module_dir.is_dir():
            continue
        slug = module_dir.name
        skill_file = module_dir / "SKILL.md"
        if not skill_file.is_file():
            # A module dir without SKILL.md is a structural issue flagged elsewhere
            # (checklist item #3). validate_deps just records its existence with empty deps.
            slugs.append(slug)
            requires_map[slug] = []
            optional_map[slug] = []
            continue

        try:
            raw = skill_file.read_text(encoding="utf-8")
        except OSError as e:
            raise ValidationCrash(f"couldn't read {skill_file}: {e}")

        fm = _parse_frontmatter(raw)
        if fm is None:
            slugs.append(slug)
            requires_map[slug] = []
            optional_map[slug] = []
            continue

        requires = fm.get("requires") or []
        optional = fm.get("optional") or []
        if not isinstance(requires, list):
            raise ValidationCrash(
                f"{skill_file}: `requires` must be a list, got {type(requires).__name__}"
            )
        if not isinstance(optional, list):
            raise ValidationCrash(
                f"{skill_file}: `optional` must be a list, got {type(optional).__name__}"
            )

        slugs.append(slug)
        requires_map[slug] = [str(r) for r in requires]
        optional_map[slug] = [str(r) for r in optional]

    return slugs, requires_map, optional_map


def _find_cycles(graph: dict[str, list[str]]) -> list[list[str]]:
    """DFS with tri-color marking to detect cycles. Returns every distinct cycle
    found. A cycle is reported as a list of nodes starting at the first revisited
    node, with that node repeated at the end for visual clarity —
    e.g., ['a', 'b', 'c', 'a']. Rotated representations of the same cycle are
    deduplicated."""
    UNVISITED, IN_PROGRESS, DONE = 0, 1, 2
    state: dict[str, int] = {node: UNVISITED for node in graph}
    cycles: list[list[str]] = []
    seen_cycles: set[tuple[str, ...]] = set()

    def dfs(node: str, path: list[str]) -> None:
        state[node] = IN_PROGRESS
        for dep in graph.get(node, []):
            if dep not in state:
                # Unknown dep — reported separately; not a cycle.
                continue
            if state[dep] == IN_PROGRESS:
                # Back edge — cycle found.
                try:
                    start = path.index(dep)
                except ValueError:
                    continue
                cycle = path[start:] + [dep]
                canonical = _canonicalize_cycle(cycle[:-1])
                if canonical not in seen_cycles:
                    seen_cycles.add(canonical)
                    cycles.append(cycle)
            elif state[dep] == UNVISITED:
                dfs(dep, path + [dep])
        state[node] = DONE

    for node in graph:
        if state[node] == UNVISITED:
            dfs(node, [node])
    return cycles


def _canonicalize_cycle(cycle: list[str]) -> tuple[str, ...]:
    """Canonical form: rotate the cycle so the lexicographically-smallest node
    starts it. Used to dedupe rotated representations of the same cycle."""
    if not cycle:
        return tuple()
    min_idx = min(range(len(cycle)), key=lambda i: cycle[i])
    rotated = cycle[min_idx:] + cycle[:min_idx]
    return tuple(rotated)


def _find_unknown_deps(
    requires_map: dict[str, list[str]], known_slugs: set[str]
) -> list[dict[str, str]]:
    """Flag required deps that don't resolve to a known module slug."""
    unknowns: list[dict[str, str]] = []
    for module, deps in requires_map.items():
        for dep in deps:
            if dep not in known_slugs:
                unknowns.append({"module": module, "requires": dep})
    return unknowns


# ---------- CLI ----------


def _parse_args(argv: list[str]) -> dict[str, Any]:
    parser = argparse.ArgumentParser(
        prog="validate_deps.py",
        description="Validate the required-dependency DAG across all modules.",
    )
    parser.add_argument(
        "--args",
        default="{}",
        help="Optional JSON object. Supported keys: repo_root.",
    )
    parsed = parser.parse_args(argv)
    try:
        opts = json.loads(parsed.args)
    except json.JSONDecodeError as e:
        raise ValidationCrash(f"--args is not valid JSON: {e}")
    if not isinstance(opts, dict):
        raise ValidationCrash("--args must be a JSON object")
    return opts


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    try:
        opts = _parse_args(argv)
    except ValidationCrash as e:
        print(str(e), file=sys.stderr)
        return 2

    repo_root = Path(opts.get("repo_root") or _repo_root_default()).resolve()
    if not repo_root.is_dir():
        print(f"repo_root not a directory: {repo_root}", file=sys.stderr)
        return 2

    try:
        slugs, requires_map, _optional_map = _collect_modules(repo_root)
    except ValidationCrash as e:
        print(str(e), file=sys.stderr)
        return 2

    known = set(slugs)

    graph: dict[str, list[str]] = {slug: list(requires_map[slug]) for slug in slugs}
    cycles = _find_cycles(graph)
    unknowns = _find_unknown_deps(requires_map, known)

    edges = sorted(
        (mod, dep)
        for mod, deps in requires_map.items()
        for dep in deps
    )

    report: dict[str, Any] = {
        "modules": slugs,
        "edges": [list(edge) for edge in edges],
        "cycles": cycles,
        "unknown_required_deps": unknowns,
    }

    print(json.dumps(report))

    if cycles or unknowns:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
