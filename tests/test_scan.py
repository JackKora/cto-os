"""Tests for scripts/scan.py.

Run scan as a subprocess (same contract the MCP server uses — JSON args in via
`--args`, JSON stdout out, CTO_OS_DATA from env). Tests exercise:

- Activation filtering (inactive modules excluded by default)
- Sensitivity filtering (sensitivity:high excluded by default, at both module
  and file level; include_high_sensitivity opts in)
- Type filtering
- Where predicate (exact, list, suffix operators)
- Fields projection
- include_body under and over the match cap
- Body truncation marker
- Query-error response shape (exit 0 with structured error envelope)
- Crash behaviour (missing CTO_OS_DATA → exit 1)
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parent.parent
SCAN_SCRIPT = REPO_ROOT / "scripts" / "scan.py"
FIXTURE_DATA_ROOT = REPO_ROOT / "tests" / "fixtures" / "cto-os-data-sample"


def _run_scan(query: dict, *, data_root: Path = FIXTURE_DATA_ROOT) -> subprocess.CompletedProcess:
    """Invoke scan.py as a subprocess. Returns the CompletedProcess; callers
    decide whether to json.loads(stdout)."""
    env = {**os.environ, "CTO_OS_DATA": str(data_root)}
    return subprocess.run(
        [sys.executable, str(SCAN_SCRIPT), "--args", json.dumps(query)],
        capture_output=True,
        text=True,
        env=env,
    )


def _scan_json(query: dict, **kwargs) -> dict:
    result = _run_scan(query, **kwargs)
    assert result.returncode == 0, (
        f"scan.py exited {result.returncode}\nstdout: {result.stdout}\nstderr: {result.stderr}"
    )
    return json.loads(result.stdout)


# ---------- Default-filter behavior ----------


def test_default_excludes_inactive_module():
    """Hiring is marked active: false in the fixture — its files should not appear."""
    result = _scan_json({})
    paths = [m["path"] for m in result["matches"]]
    assert not any("hiring/" in p for p in paths), f"hiring files leaked: {paths}"


def test_default_excludes_high_sensitivity_module():
    """Managing Down is sensitivity:high at module level — nothing from it by default."""
    result = _scan_json({})
    paths = [m["path"] for m in result["matches"]]
    assert not any("managing-down/" in p for p in paths), (
        f"managing-down files leaked: {paths}"
    )


def test_include_inactive_opts_in():
    result = _scan_json({"include_inactive": True})
    paths = [m["path"] for m in result["matches"]]
    assert any("hiring/" in p for p in paths), "hiring/ files missing after opt-in"


def test_include_high_sensitivity_opts_in():
    result = _scan_json({"include_high_sensitivity": True})
    paths = [m["path"] for m in result["matches"]]
    assert any("managing-down/" in p for p in paths), (
        "managing-down/ files missing after opt-in"
    )


# ---------- Type filter ----------


def test_type_filter_single():
    result = _scan_json({"type": ["team"]})
    for m in result["matches"]:
        assert m["frontmatter"].get("type") == "team", m
    assert len(result["matches"]) == 2, "expected 2 teams in fixture (platform, growth)"


def test_type_filter_list():
    result = _scan_json({"type": ["team", "team-retro"]})
    types = {m["frontmatter"].get("type") for m in result["matches"]}
    assert types == {"team", "team-retro"}, types


def test_type_filter_no_match():
    result = _scan_json({"type": ["no-such-type"]})
    assert result["matches"] == []


# ---------- Where predicate ----------


def test_where_exact_match():
    result = _scan_json({"type": ["team"], "where": {"lead": "Alex"}})
    assert len(result["matches"]) == 1
    assert result["matches"][0]["frontmatter"]["slug"] == "platform"


def test_where_value_list_membership():
    """Caller passes a list of acceptable values — match if field is in the list."""
    result = _scan_json(
        {"type": ["team"], "where": {"lead": ["Alex", "Jamie"]}}
    )
    assert len(result["matches"]) == 2


def test_where_suffix_gte():
    # Both retros exist: personal-os retro (2026-04-15) + team-management retro (2026-03-31).
    # Suffix applies to both — only personal retro is >= 2026-04-01.
    result = _scan_json(
        {
            "type": ["retro-personal", "team-retro"],
            "where": {"updated_gte": "2026-04-01"},
        }
    )
    assert len(result["matches"]) == 1
    assert result["matches"][0]["frontmatter"]["type"] == "retro-personal"


def test_where_no_match_returns_empty():
    result = _scan_json({"type": ["team"], "where": {"lead": "nobody"}})
    assert result["matches"] == []


# ---------- Module filter ----------


def test_module_filter_scopes_search():
    result = _scan_json({"module": "personal-os"})
    for m in result["matches"]:
        assert m["path"].startswith("modules/personal-os/"), m


# ---------- Fields projection ----------


def test_fields_projects_frontmatter():
    result = _scan_json(
        {"type": ["team"], "fields": ["slug", "lead", "size"]}
    )
    for m in result["matches"]:
        assert set(m["frontmatter"].keys()) <= {"slug", "lead", "size"}
        assert "mission" not in m["frontmatter"]


def test_fields_missing_key_just_absent():
    result = _scan_json({"type": ["team"], "fields": ["no-such-field"]})
    for m in result["matches"]:
        assert m["frontmatter"] == {}


# ---------- include_body ----------


def test_include_body_under_cap_returns_bodies():
    # Narrow query to one file so we stay under the cap.
    result = _scan_json(
        {"type": ["show-up"], "include_body": True}
    )
    assert len(result["matches"]) == 1
    m = result["matches"][0]
    assert "body" in m and m["body"], "body should be present and non-empty"
    assert m["body_truncated"] is False
    assert "truncated_bodies" not in result


def test_include_body_over_cap_returns_paths_only():
    # Fixture has ~7 files in active + standard-sensitivity scope. Requesting
    # bodies with no filter should trip the cap (5).
    result = _scan_json({"include_body": True})
    assert result.get("truncated_bodies") is True, result
    for m in result["matches"]:
        assert "body" not in m
        assert "body_truncated" not in m


def test_body_truncation_marker_when_body_too_long(tmp_path):
    """Seed a temp data repo with an oversized file to exercise the byte cap."""
    modules_dir = tmp_path / "modules" / "oversize-test"
    state_dir = modules_dir / "state"
    state_dir.mkdir(parents=True)
    (modules_dir / "_module.md").write_text(
        "---\ntype: _module\nslug: oversize-test\nmodule: oversize-test\n"
        "updated: 2026-04-21\nschema_version: 1\nactive: true\n"
        "activated_at: 2026-04-21\ndeactivated_at: null\n---\n",
        encoding="utf-8",
    )
    long_body = "x" * 10_000  # well over MAX_BODY_BYTES (4096)
    (state_dir / "long.md").write_text(
        "---\ntype: long-doc\nslug: long\nupdated: 2026-04-21\n---\n" + long_body,
        encoding="utf-8",
    )

    result = _scan_json({"type": ["long-doc"], "include_body": True}, data_root=tmp_path)
    assert len(result["matches"]) == 1
    m = result["matches"][0]
    assert m["body_truncated"] is True
    assert "truncated," in m["body"]
    assert "use read_file for full content" in m["body"]
    # Body bytes (before marker) should be <= cap.
    body_bytes = m["body"].split("\n... [truncated,")[0].encode("utf-8")
    assert len(body_bytes) <= 4096


# ---------- Query errors (exit 0 with structured error) ----------


def test_unknown_field_returns_error_envelope():
    result = _run_scan({"nonsense_field": 42})
    assert result.returncode == 0, f"unknown field should exit 0, not crash: {result.stderr}"
    data = json.loads(result.stdout)
    assert "error" in data
    assert "unknown query fields" in data["error"]
    assert data["query"] == {"nonsense_field": 42}


def test_wrong_type_returns_error_envelope():
    result = _run_scan({"type": "should-be-a-list"})  # string instead of list
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert "error" in data
    assert data["query"]["type"] == "should-be-a-list"


# ---------- Crashes ----------


def test_missing_data_root_crashes():
    """No CTO_OS_DATA env var → exit 1."""
    env = {k: v for k, v in os.environ.items() if k != "CTO_OS_DATA"}
    result = subprocess.run(
        [sys.executable, str(SCAN_SCRIPT), "--args", "{}"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 1
    assert "CTO_OS_DATA" in result.stderr


def test_invalid_args_json_crashes():
    result = subprocess.run(
        [sys.executable, str(SCAN_SCRIPT), "--args", "{not valid json"],
        capture_output=True,
        text=True,
        env={**os.environ, "CTO_OS_DATA": str(FIXTURE_DATA_ROOT)},
    )
    assert result.returncode == 1
    assert "valid JSON" in result.stderr
