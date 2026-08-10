"""Tests for scripts/validate_deps.py.

Subprocess-based, same pattern as scan tests. Exercises:

- Clean graph on the real repo (exit 0, no cycles/unknowns)
- Synthetic fake-repo fixture with a direct cycle (exit 1, cycle reported)
- Transitive cycle across three modules (exit 1, cycle deduplicated across rotations)
- Unknown required dep (exit 1, listed)
- Structural and frontmatter parse failures (exit 2)
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
        if requires is not None:
            if requires:
                body += "requires:\n"
                for r in requires:
                    body += f"  - {r}\n"
            else:
                body += "requires: []\n"
        if optional is not None:
            if optional:
                body += "optional:\n"
                for o in optional:
                    body += f"  - {o}\n"
            else:
                body += "optional: []\n"
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


def test_module_without_skill_md_crashes(tmp_path):
    _write_module(tmp_path, "a")
    (tmp_path / "modules" / "no-skill").mkdir(parents=True)

    result = _run(tmp_path)
    assert result.returncode == 2
    assert "modules/no-skill/SKILL.md" in result.stderr


def test_non_utf8_skill_md_crashes_concisely(tmp_path):
    module_dir = tmp_path / "modules" / "non-utf8"
    module_dir.mkdir(parents=True)
    (module_dir / "SKILL.md").write_bytes(b"\xff\xfe")

    result = _run(tmp_path)

    assert result.returncode == 2
    assert "modules/non-utf8/SKILL.md" in result.stderr
    assert "UTF-8" in result.stderr
    assert "Traceback" not in result.stderr


@pytest.mark.parametrize("raw, expected", [
    ("name: bad\n", "missing YAML frontmatter"),
    ("---\nname: [unterminated\n---\n", "malformed YAML frontmatter"),
    ("---\n- not-a-mapping\n---\n", "must be a mapping"),
])
def test_invalid_frontmatter_crashes(tmp_path, raw, expected):
    _write_module(tmp_path, "bad", raw_frontmatter=raw)
    result = _run(tmp_path)
    assert result.returncode == 2
    assert "modules/bad/SKILL.md" in result.stderr
    assert expected in result.stderr


def test_valid_empty_dependency_lists_are_clean(tmp_path):
    _write_module(tmp_path, "empty", requires=[], optional=[])
    result = _run(tmp_path)
    assert result.returncode == 0


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


@pytest.mark.parametrize(
    ("field", "yaml_value", "type_name"),
    [
        ("requires", "{}", "dict"),
        ("requires", '""', "str"),
        ("requires", "null", "NoneType"),
        ("requires", "false", "bool"),
        ("requires", "0", "int"),
        ("optional", "{}", "dict"),
        ("optional", '""', "str"),
        ("optional", "null", "NoneType"),
        ("optional", "false", "bool"),
        ("optional", "0", "int"),
    ],
)
def test_falsey_non_list_dependency_fields_crash(tmp_path, field, yaml_value, type_name):
    raw = (
        "---\n"
        "name: bad\n"
        'description: "bad"\n'
        f"{field}: {yaml_value}\n"
        "---\n"
    )
    _write_module(tmp_path, "bad", raw_frontmatter=raw)

    result = _run(tmp_path)

    assert result.returncode == 2
    assert "modules/bad/SKILL.md" in result.stderr
    assert f"`{field}` must be a list, got {type_name}" in result.stderr
    assert "Traceback" not in result.stderr


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
