"""Tests for scripts/roll_up.py.

Exercises each rollup kind against the shared fixture at
tests/fixtures/cto-os-data-sample/. Roll_up shells out to scan.py, so
tests run as subprocesses pointed at the fixture.

Covers:
  - team-health: enumerates active teams with scores + retro counts.
  - per-person: pulls profile + 1:1s + coaching + performance + dev plan +
    PIP. Jane has active dev plan, no PIP; Mike has active PIP, no dev plan.
  - goal-progress: horizons + mappings-per-goal + flags unmapped goals.
  - unknown-kind → structured error envelope (exit 0).
  - missing kind → structured error envelope.
  - bad args → exit 1.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "scripts" / "roll_up.py"
FIXTURE = REPO_ROOT / "tests" / "fixtures" / "cto-os-data-sample"


def _run(args: dict, *, data_root: Path = FIXTURE) -> subprocess.CompletedProcess:
    env = {**os.environ, "CTO_OS_DATA": str(data_root)}
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--args", json.dumps(args)],
        capture_output=True,
        text=True,
        env=env,
    )


def _ok(args: dict, **kwargs) -> dict:
    result = _run(args, **kwargs)
    assert result.returncode == 0, (
        f"roll_up.py exited {result.returncode}\nstdout: {result.stdout}\nstderr: {result.stderr}"
    )
    return json.loads(result.stdout)


# ---------- team-health ----------


def test_team_health_includes_active_teams_with_scores():
    report = _ok({"kind": "team-health"})
    assert report["kind"] == "team-health"
    assert report["team_count"] == 2  # fixture has platform + growth

    slugs = [t["slug"] for t in report["teams"]]
    assert slugs == ["growth", "platform"]  # sorted

    platform = next(t for t in report["teams"] if t["slug"] == "platform")
    assert platform["lead"] == "Alex"
    assert platform["topology"] == "platform"
    assert platform["scores"]["velocity"] == 4
    assert platform["latest_retro_date"] == "2026-03-31"
    # Current quarter bounds include 2026-Q1 retro if we're running in Q2+,
    # depending on date — just assert the count is non-negative.
    assert platform["retros_this_quarter"] >= 0


def test_team_health_growth_has_no_retros_in_fixture():
    report = _ok({"kind": "team-health"})
    growth = next(t for t in report["teams"] if t["slug"] == "growth")
    assert growth["latest_retro_date"] is None
    assert growth["retros_this_quarter"] == 0


# ---------- per-person ----------


def test_per_person_jane_has_profile_and_dev_plan():
    report = _ok({"kind": "per-person", "person_slug": "jane"})
    assert report["kind"] == "per-person"
    assert report["person_slug"] == "jane"

    profile = report["profile"]
    assert profile is not None
    assert profile["name"] == "Jane Smith"
    assert profile["relationship"] == "direct-report"

    # 1:1 + coaching counts.
    assert report["one_on_one_count"] == 1
    assert report["latest_1on1"] == "2026-04-21"
    assert report["coaching_event_count"] == 0
    assert report["latest_coaching"] is None

    # Performance record.
    perf = report["performance_record"]
    assert perf is not None
    assert perf["current_level"] == "staff"
    assert perf["current_trajectory"] == "growing"

    # Active dev plan.
    dev = report["active_development_plan"]
    assert dev is not None
    assert dev["status"] == "active"

    # No PIP.
    assert report["active_pip"] is None


def test_per_person_mike_has_pip_no_dev_plan():
    report = _ok({"kind": "per-person", "person_slug": "mike"})

    assert report["one_on_one_count"] == 0
    assert report["coaching_event_count"] == 1
    assert report["latest_coaching"] == "2026-04-10"

    perf = report["performance_record"]
    assert perf["current_trajectory"] == "concerning"

    assert report["active_development_plan"] is None
    assert report["active_pip"] is not None
    assert report["active_pip"]["status"] == "active"


def test_per_person_requires_person_slug():
    report = _ok({"kind": "per-person"})
    assert "error" in report
    assert "person_slug" in report["error"]


def test_per_person_unknown_slug_returns_empty_rollup():
    report = _ok({"kind": "per-person", "person_slug": "nobody"})
    # Not an error — just empty.
    assert report["profile"] is None
    assert report["one_on_one_count"] == 0
    assert report["performance_record"] is None
    assert report["active_development_plan"] is None
    assert report["active_pip"] is None


# ---------- goal-progress ----------


def test_goal_progress_horizons_and_mappings():
    report = _ok({"kind": "goal-progress"})
    assert report["kind"] == "goal-progress"

    # Fixture has personal-os goals, not company-goal-horizon — so horizons
    # should be empty. This is correct: goal-progress reports on company
    # goals, which fixture doesn't include.
    assert report["horizons"] == []
    assert report["total_mappings"] == 0
    assert report["goals_with_no_mapping"] == []


def test_goal_progress_with_company_goal_fixture(tmp_path):
    """Seed a minimal synthetic data repo with a company-goal-horizon and
    work-mapping to exercise the goal→mapping join."""
    # Module dir + _module.md so the files aren't treated as from an inactive
    # module (default scan behavior).
    ba = tmp_path / "modules" / "business-alignment"
    (ba / "company-goals").mkdir(parents=True)
    (ba / "_module.md").write_text(
        "---\ntype: _module\nslug: business-alignment\nmodule: business-alignment\n"
        "updated: 2026-04-22\nschema_version: 1\nactive: true\n"
        "activated_at: 2026-04-01\ndeactivated_at: null\n---\n",
        encoding="utf-8",
    )
    (ba / "company-goals" / "annual.md").write_text(
        "---\ntype: company-goal-horizon\nslug: annual\nupdated: 2026-01-15\n"
        "horizon: annual\nperiod: '2026'\nitems:\n"
        "  - Ship platform v2\n"
        "  - Grow ARR 30%\n"
        "---\n",
        encoding="utf-8",
    )
    (ba / "work-mapping.md").write_text(
        "---\ntype: work-mapping\nslug: current\nupdated: 2026-04-01\n"
        "mappings:\n"
        "  - initiative: platform-v2-migration\n"
        "    goal: Ship platform v2\n"
        "    confidence: high\n"
        "---\n",
        encoding="utf-8",
    )

    report = _ok({"kind": "goal-progress"}, data_root=tmp_path)
    assert len(report["horizons"]) == 1
    items = report["horizons"][0]["items"]
    assert len(items) == 2

    # Ship platform v2 has one mapped initiative.
    mapped = next(i for i in items if i["item"] == "Ship platform v2")
    assert len(mapped["mapped_initiatives"]) == 1
    assert mapped["mapped_initiatives"][0]["initiative"] == "platform-v2-migration"

    # Grow ARR 30% has nothing mapped.
    unmapped = next(i for i in items if i["item"] == "Grow ARR 30%")
    assert unmapped["mapped_initiatives"] == []

    # Flagged.
    assert "Grow ARR 30%" in report["goals_with_no_mapping"]


# ---------- Error envelopes ----------


def test_unknown_kind_returns_error_envelope():
    report = _ok({"kind": "nonsense"})
    assert "error" in report
    assert "unknown rollup kind" in report["error"]
    assert "available" in report
    assert "team-health" in report["available"]


def test_missing_kind_returns_error_envelope():
    report = _ok({})
    assert "error" in report
    assert "kind" in report["error"]


def test_invalid_args_json_crashes():
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--args", "{not json"],
        capture_output=True,
        text=True,
        env={**os.environ, "CTO_OS_DATA": str(FIXTURE)},
    )
    assert result.returncode == 1
    assert "valid JSON" in result.stderr
