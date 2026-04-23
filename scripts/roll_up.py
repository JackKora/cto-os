#!/usr/bin/env python3
"""
roll_up.py — on-demand cross-type aggregations over CTO_OS_DATA.

Where `scan` handles single-type filter-and-project queries, roll_up handles
cross-type aggregations that would otherwise require multiple scan rounds
plus LLM-side counting and joining. Each rollup is a named, hand-written
aggregation — adding a new rollup = adding a function to the dispatch dict.

Available rollups (v1):

  team-health
    Every active team with current rubric scores, last-retro date, and
    retro-count (in the current quarter). Good for "how are all my teams
    doing" roll-up views.

  per-person
    For one direct report: profile summary + 1:1 count + coaching-event
    count + latest coaching date + performance record + active development
    plan + active PIP. Requires {"person_slug": "..."} in args. Implicitly
    passes include_high_sensitivity=true to scan — per-person rollups exist
    precisely to pull together content from sensitivity-high modules that
    the user is authorized to see.

  goal-progress
    Company goals (annual + quarterly) cross-referenced against the
    work-mapping to show which initiatives ladder to which goals, and
    flags any goal with no mapped work.

Invocation contract matches every other script:
  uv run python scripts/roll_up.py --args '{"kind": "team-health"}'
  uv run python scripts/roll_up.py --args '{"kind": "per-person", "person_slug": "jane"}'

Implementation note: roll_up shells out to `scan.py` rather than importing
it. Keeps the production path identical to the test path (both use the
subprocess contract) and keeps scripts surface-agnostic. The added latency
is a handful of subprocess startups per rollup — fine for user-initiated
roll-up views, not a bottleneck.

Stdout: JSON object, shape varies by rollup kind. Error envelope for
unknown-kind or bad-args.

Exit codes:
  0 — success or structured error
  1 — crash (bad env, scan subprocess blew up)
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Any


SCAN_SCRIPT = Path(__file__).resolve().parent / "scan.py"


# ---------- Errors ----------


class RollupError(Exception):
    """Structured error — exit 0 with error envelope."""


class RollupCrash(Exception):
    """Exit 1 — the script couldn't complete."""


# ---------- Scan helper ----------


def _scan(spec: dict[str, Any]) -> dict[str, Any]:
    """Shell out to scan.py with the given query spec. Returns parsed JSON."""
    result = subprocess.run(
        [sys.executable, str(SCAN_SCRIPT), "--args", json.dumps(spec)],
        capture_output=True,
        text=True,
        env=os.environ,
    )
    if result.returncode != 0:
        raise RollupCrash(
            f"scan.py exited {result.returncode}: {result.stderr.strip()[:500]}"
        )
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as e:
        raise RollupCrash(f"scan.py returned non-JSON: {e}")
    if "error" in payload:
        raise RollupCrash(f"scan.py query error: {payload['error']}")
    return payload


# ---------- Quarter helpers ----------


def _current_quarter_bounds(today: date | None = None) -> tuple[str, str]:
    """Return (start_iso, end_iso) for the calendar quarter containing today."""
    d = today or date.today()
    quarter = (d.month - 1) // 3 + 1
    start_month = 3 * (quarter - 1) + 1
    start = date(d.year, start_month, 1)
    # End of quarter = day before next quarter starts.
    next_start_month = start_month + 3
    if next_start_month > 12:
        end = date(d.year, 12, 31)
    else:
        end = date(d.year, next_start_month, 1)
        # Back up one day by using strftime approach below — simpler: the
        # GTE/LT pair is cleaner than computing end exactly.
    return start.isoformat(), end.isoformat()


# ---------- Rollups ----------


def _rollup_team_health(_args: dict[str, Any]) -> dict[str, Any]:
    teams_resp = _scan({
        "type": ["team"],
        "where": {"active": True},
        "fields": [
            "slug", "lead", "mission", "size", "topology",
            "retro_cadence", "scores", "updated",
        ],
    })
    teams = teams_resp.get("matches", [])

    # One retro scan per team — bounded and cheap.
    quarter_start, _ = _current_quarter_bounds()

    summaries: list[dict[str, Any]] = []
    for team in teams:
        fm = team.get("frontmatter", {})
        slug = fm.get("slug")
        if not slug:
            continue

        retros_resp = _scan({
            "type": ["team-retro"],
            "where": {"team": slug},
            "fields": ["slug", "updated", "period"],
        })
        retro_matches = retros_resp.get("matches", [])

        latest_retro_date: str | None = None
        retros_this_quarter = 0
        for r in retro_matches:
            rfm = r.get("frontmatter", {})
            u = _as_iso_date(rfm.get("updated"))
            if u and (latest_retro_date is None or u > latest_retro_date):
                latest_retro_date = u
            if u and u >= quarter_start:
                retros_this_quarter += 1

        summaries.append({
            "slug": slug,
            "lead": fm.get("lead"),
            "topology": fm.get("topology"),
            "size": fm.get("size"),
            "scores": fm.get("scores") or {},
            "retro_cadence": fm.get("retro_cadence"),
            "latest_retro_date": latest_retro_date,
            "retros_this_quarter": retros_this_quarter,
            "last_updated": _as_iso_date(fm.get("updated")),
        })

    # Sort by slug for deterministic output.
    summaries.sort(key=lambda s: s["slug"] or "")
    return {
        "kind": "team-health",
        "teams": summaries,
        "team_count": len(summaries),
    }


def _rollup_per_person(args: dict[str, Any]) -> dict[str, Any]:
    person_slug = args.get("person_slug")
    if not isinstance(person_slug, str) or not person_slug:
        raise RollupError("per-person rollup requires 'person_slug' in args")

    # Profile — stakeholder-profile with relationship=direct-report.
    profile_resp = _scan({
        "type": ["stakeholder-profile"],
        "where": {"slug": person_slug},
        "include_high_sensitivity": True,
    })
    profiles = profile_resp.get("matches", [])
    # Narrow to direct-report if multiple modules have a profile with this slug.
    direct_report_profile = next(
        (p for p in profiles if p.get("frontmatter", {}).get("relationship") == "direct-report"),
        None,
    )

    # 1:1s — from Managing Down (sensitivity: high).
    onones_resp = _scan({
        "type": ["report-1on1"],
        "where": {"person": person_slug},
        "fields": ["slug", "updated"],
        "include_high_sensitivity": True,
    })
    onones = onones_resp.get("matches", [])
    latest_1on1 = _max_field(onones, "updated")

    # Coaching events — from Managing Down.
    coaching_resp = _scan({
        "type": ["coaching-event"],
        "where": {"person": person_slug},
        "fields": ["slug", "updated", "event_type"],
        "include_high_sensitivity": True,
    })
    coaching = coaching_resp.get("matches", [])
    latest_coaching = _max_field(coaching, "updated")

    # Performance record — from Performance & Development (sensitivity: high).
    perf_resp = _scan({
        "type": ["performance-record"],
        "where": {"slug": person_slug},
        "include_high_sensitivity": True,
    })
    perf_matches = perf_resp.get("matches", [])
    perf_record = perf_matches[0].get("frontmatter") if perf_matches else None

    # Active development plan.
    dev_plan_resp = _scan({
        "type": ["development-plan"],
        "where": {"person": person_slug, "status": "active"},
        "include_high_sensitivity": True,
    })
    dev_plans = dev_plan_resp.get("matches", [])
    active_dev_plan = dev_plans[0].get("frontmatter") if dev_plans else None

    # Active PIP.
    pip_resp = _scan({
        "type": ["pip"],
        "where": {"person": person_slug, "status": "active"},
        "include_high_sensitivity": True,
    })
    pips = pip_resp.get("matches", [])
    active_pip = pips[0].get("frontmatter") if pips else None

    return {
        "kind": "per-person",
        "person_slug": person_slug,
        "profile": direct_report_profile.get("frontmatter") if direct_report_profile else None,
        "profile_path": direct_report_profile.get("path") if direct_report_profile else None,
        "one_on_one_count": len(onones),
        "latest_1on1": latest_1on1,
        "coaching_event_count": len(coaching),
        "latest_coaching": latest_coaching,
        "performance_record": perf_record,
        "active_development_plan": active_dev_plan,
        "active_pip": active_pip,
    }


def _rollup_goal_progress(_args: dict[str, Any]) -> dict[str, Any]:
    goals_resp = _scan({
        "type": ["company-goal-horizon"],
        "fields": ["slug", "horizon", "period", "items", "owner", "updated"],
    })
    goals = goals_resp.get("matches", [])

    mapping_resp = _scan({
        "type": ["work-mapping"],
        "fields": ["slug", "mappings", "updated"],
    })
    mapping_matches = mapping_resp.get("matches", [])
    mappings: list[dict[str, Any]] = []
    for m in mapping_matches:
        mappings.extend(m.get("frontmatter", {}).get("mappings") or [])

    # Index mappings by goal value (a free-text string matched against the
    # company-goal items — imperfect but the best we can do without a
    # structured goal-ID system).
    per_goal: dict[str, list[dict[str, Any]]] = {}
    for mapping in mappings:
        goal_text = mapping.get("goal")
        if not goal_text:
            continue
        per_goal.setdefault(goal_text, []).append({
            "initiative": mapping.get("initiative"),
            "confidence": mapping.get("confidence"),
        })

    horizons: list[dict[str, Any]] = []
    for g in goals:
        fm = g.get("frontmatter", {})
        items = fm.get("items") or []
        items_with_mappings: list[dict[str, Any]] = []
        for item in items:
            items_with_mappings.append({
                "item": item,
                "mapped_initiatives": per_goal.get(item, []),
            })
        horizons.append({
            "horizon": fm.get("horizon"),
            "period": fm.get("period"),
            "owner": fm.get("owner"),
            "items": items_with_mappings,
        })
    horizons.sort(key=lambda h: (h.get("horizon") or "", h.get("period") or ""))

    goals_with_no_mapping = [
        item["item"]
        for h in horizons
        for item in h["items"]
        if not item["mapped_initiatives"]
    ]

    return {
        "kind": "goal-progress",
        "horizons": horizons,
        "goals_with_no_mapping": goals_with_no_mapping,
        "total_mappings": len(mappings),
    }


# ---------- Helpers ----------


def _as_iso_date(value: Any) -> str | None:
    """Normalize a value (possibly a date, datetime, or ISO string) to an
    ISO-8601 string. Returns None on unusable values."""
    if value is None:
        return None
    if isinstance(value, str):
        return value
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    return None


def _max_field(matches: list[dict[str, Any]], field_name: str) -> str | None:
    """Return the max (string-comparable) value of `field_name` across a set
    of scan matches."""
    best: str | None = None
    for m in matches:
        v = _as_iso_date(m.get("frontmatter", {}).get(field_name))
        if v and (best is None or v > best):
            best = v
    return best


# ---------- Dispatch ----------


_ROLLUPS = {
    "team-health": _rollup_team_health,
    "per-person": _rollup_per_person,
    "goal-progress": _rollup_goal_progress,
}


# ---------- CLI ----------


def _parse_args(argv: list[str]) -> dict[str, Any]:
    parser = argparse.ArgumentParser(
        prog="roll_up.py",
        description="On-demand cross-type aggregations over CTO_OS_DATA.",
    )
    parser.add_argument(
        "--args",
        required=True,
        help='JSON object: {"kind":"team-health"|"per-person"|"goal-progress", ...}',
    )
    parsed = parser.parse_args(argv)
    try:
        opts = json.loads(parsed.args)
    except json.JSONDecodeError as e:
        raise RollupCrash(f"--args is not valid JSON: {e}")
    if not isinstance(opts, dict):
        raise RollupCrash("--args must be a JSON object")
    return opts


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    try:
        opts = _parse_args(argv)
    except RollupCrash as e:
        print(str(e), file=sys.stderr)
        return 1

    kind = opts.get("kind")
    if not isinstance(kind, str):
        print(json.dumps({"error": "missing 'kind' field", "query": opts}))
        return 0

    handler = _ROLLUPS.get(kind)
    if handler is None:
        print(json.dumps({
            "error": f"unknown rollup kind: {kind!r}",
            "available": sorted(_ROLLUPS.keys()),
            "query": opts,
        }))
        return 0

    try:
        result = handler(opts)
    except RollupError as e:
        print(json.dumps({"error": str(e), "query": opts}))
        return 0
    except RollupCrash as e:
        print(f"roll_up.py crashed: {e}", file=sys.stderr)
        return 1

    print(json.dumps(result, default=_json_default))
    return 0


def _json_default(obj: Any) -> Any:
    import datetime as _dt

    if isinstance(obj, (_dt.date, _dt.datetime)):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


if __name__ == "__main__":
    sys.exit(main())
