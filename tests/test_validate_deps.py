"""Tests for scripts/validate_deps.py.

Subprocess-based, same pattern as scan tests. Exercises:

- Clean graph on the real repo (exit 0, no cycles/unknowns)
- Synthetic fake-repo fixture with a direct cycle (exit 1, cycle reported)
- Transitive cycle across three modules (exit 1, cycle deduplicated across rotations)
- Unknown required dep (exit 1, listed)
- Module with no SKILL.md (graceful; counts as empty-deps module)
- Module with malformed frontmatter `requires:` (exit 2 — crash)
- Optional cycles are permitted (exit 0)
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "scripts" / "validate_deps.py"


def _run(repo_root: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--args",
            json.dumps({"repo_root": str(repo_root)}),
        ],
        capture_output=True,
        text=True,
    )


def _json(result: subprocess.CompletedProcess) -> dict:
    return json.loads(result.stdout)


def _write_module(
    repo_root: Path,
    slug: str,
    *,
    requires: list[str] | None = None,
    optional: list[str] | None = None,
    include_readme: bool = True,
    raw_frontmatter: str | None = None,
) -> None:
    """Helper to lay down a minimal SKILL.md (+ README.md) for a module inside a
    synthetic fake repo_root. `raw_frontmatter` lets tests inject malformed input."""
    module_dir = repo_root / "modules" / slug
    module_dir.mkdir(parents=True, exist_ok=True)

    if raw_frontmatter is not None:
        body = raw_frontmatter
    else:
        body = "---\n"
        body += f"name: {slug}\n"
        body += 'description: "test module"\n'
        body += "requires:\n"
        for r in requires or []:
            body += f"  - {r}\n"
        body += "optional:\n"
        for o in optional or []:
            body += f"  - {o}\n"
        body += "---\n\n# Test\n"

    (module_dir / "SKILL.md").write_text(body, encoding="utf-8")
    if include_readme:
        (module_dir / "README.md").write_text(f"# {slug}\n", encoding="utf-8")


# ---------- Real-repo sanity check ----------


def test_real_repo_is_clean():
    """The actual cto-os repo graph should validate cleanly."""
    result = _run(REPO_ROOT)
    assert result.returncode == 0, (
        f"real repo failed validation\nstdout: {result.stdout}\nstderr: {result.stderr}"
    )
    report = _json(result)
    assert report["cycles"] == []
    assert report["unknown_required_deps"] == []
    assert len(report["modules"]) >= 19  # current count; lower-bound, not exact


# ---------- Synthetic fake-repo tests ----------


def test_clean_synthetic_repo(tmp_path):
    _write_module(tmp_path, "a")
    _write_module(tmp_path, "b", requires=["a"])
    _write_module(tmp_path, "c", requires=["a", "b"])

    result = _run(tmp_path)
    assert result.returncode == 0
    report = _json(result)
    assert sorted(report["modules"]) == ["a", "b", "c"]
    assert sorted(report["edges"]) == [["b", "a"], ["c", "a"], ["c", "b"]]
    assert report["cycles"] == []
    assert report["unknown_required_deps"] == []


def test_direct_cycle_detected(tmp_path):
    _write_module(tmp_path, "a", requires=["b"])
    _write_module(tmp_path, "b", requires=["a"])

    result = _run(tmp_path)
    assert result.returncode == 1
    report = _json(result)
    assert len(report["cycles"]) == 1
    cycle = report["cycles"][0]
    # One representation of the a↔b cycle.
    assert cycle[0] == cycle[-1]  # first node repeated at end
    assert set(cycle) == {"a", "b"}


def test_transitive_cycle_detected(tmp_path):
    _write_module(tmp_path, "a", requires=["b"])
    _write_module(tmp_path, "b", requires=["c"])
    _write_module(tmp_path, "c", requires=["a"])

    result = _run(tmp_path)
    assert result.returncode == 1
    report = _json(result)
    assert len(report["cycles"]) == 1, (
        f"rotations should be deduplicated, got {report['cycles']}"
    )
    cycle = report["cycles"][0]
    assert set(cycle) == {"a", "b", "c"}
    assert cycle[0] == cycle[-1]


def test_unknown_required_dep(tmp_path):
    _write_module(tmp_path, "a", requires=["nonexistent-module"])

    result = _run(tmp_path)
    assert result.returncode == 1
    report = _json(result)
    assert report["cycles"] == []
    assert report["unknown_required_deps"] == [
        {"module": "a", "requires": "nonexistent-module"}
    ]


def test_optional_cycles_are_permitted(tmp_path):
    """Optional deps may form cycles per the architecture docs."""
    _write_module(tmp_path, "a", optional=["b"])
    _write_module(tmp_path, "b", optional=["a"])

    result = _run(tmp_path)
    assert result.returncode == 0, f"optional cycles should not fail: {result.stdout}"
    report = _json(result)
    assert report["cycles"] == []
    assert report["unknown_required_deps"] == []


def test_module_without_skill_md(tmp_path):
    """Structurally invalid but not a deps failure — module has empty deps."""
    _write_module(tmp_path, "a")
    (tmp_path / "modules" / "no-skill").mkdir(parents=True)

    result = _run(tmp_path)
    assert result.returncode == 0
    report = _json(result)
    assert set(report["modules"]) == {"a", "no-skill"}


def test_malformed_requires_crashes(tmp_path):
    """`requires: "not a list"` → exit 2 (crash), not exit 1."""
    raw = (
        "---\n"
        "name: bad\n"
        'description: "bad"\n'
        'requires: "this-should-be-a-list"\n'
        "optional: []\n"
        "---\n"
    )
    _write_module(tmp_path, "bad", raw_frontmatter=raw)

    result = _run(tmp_path)
    assert result.returncode == 2
    assert "must be a list" in result.stderr


def test_empty_modules_dir(tmp_path):
    (tmp_path / "modules").mkdir()

    result = _run(tmp_path)
    assert result.returncode == 0
    report = _json(result)
    assert report["modules"] == []
    assert report["edges"] == []


def test_no_modules_dir(tmp_path):
    """Not the end of the world — no modules, no cycles, no unknowns."""
    result = _run(tmp_path)
    assert result.returncode == 0
    report = _json(result)
    assert report["modules"] == []


# ---------- CLI behavior ----------


def test_default_args_runs_against_real_repo():
    """Without --args, defaults to auto-detected repo root (the real repo)."""
    result = subprocess.run(
        [sys.executable, str(SCRIPT)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    report = _json(result)
    assert len(report["modules"]) >= 19


def test_invalid_args_json_crashes():
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--args", "{not json"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 2
    assert "valid JSON" in result.stderr
