#!/usr/bin/env python3
"""
pull_linear.py — incremental pull of Linear issues into
`$CTO_OS_DATA/integrations-cache/linear/`.

Behavior:
  - TTL check. If the most-recent cached file is within the configured TTL
    (see `scripts/lib/integrations.yaml`, key `linear.ttl_minutes`), the
    pull is skipped unless `{"force": true}` is passed. Default TTL per
    docs/DATA_REPO.md is 30 minutes.
  - Incremental via watermark on `updatedAt`. Reads the newest cached file,
    finds the max `updatedAt` across issues, and queries Linear for issues
    updated since (max - 5 minutes) to guard against clock skew and
    eventual-consistency drift. Dedupes on Linear issue ID in the result
    file (union of the prior cache + newly-pulled).
  - Issues only in v1. Comments are out of scope per the batch decision;
    Attention & Operations doesn't need them yet.

Auth: reads `LINEAR_API_KEY` from env. Missing or empty → exit 1.

Output file: `$CTO_OS_DATA/integrations-cache/linear/{ISO_TIMESTAMP}.json`,
shape:
  {
    "pulled_at": "2026-04-22T10:00:00Z",
    "since": "2026-04-22T09:00:00Z" | null,
    "issue_count": 42,
    "issues": [
      {
        "id": "...", "identifier": "ENG-123", "title": "...",
        "state": {"name": "In Progress", "type": "started"},
        "team": {"id": "...", "name": "Platform", "key": "ENG"},
        "assignee": {"id": "...", "name": "Jane", "email": "..."},
        "priority": 2,
        "createdAt": "...", "updatedAt": "...", "completedAt": null,
        "labels": ["bug", "platform"],
        "url": "https://linear.app/..."
      }
    ]
  }

Stdout (always JSON):
  {
    "status": "pulled" | "skipped-ttl" | "error",
    "file_written": "integrations-cache/linear/2026-04-22T10-00-00Z.json" | null,
    "issue_count": 42,
    "new_since_last": 15,
    "message": "..."   // present only on error/skip
  }

Exit codes:
  0 — success (including skipped-ttl)
  1 — crash (auth failure, HTTP error, bad env)
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import yaml


LINEAR_GRAPHQL_URL = "https://api.linear.app/graphql"
DEFAULT_TTL_MINUTES = 30   # fallback if integrations.yaml is missing / silent
DEFAULT_LIMIT = 500
WATERMARK_BUFFER_MINUTES = 5


# ---------- Errors ----------


class PullCrash(Exception):
    """Exit 1 — the script couldn't complete."""


# ---------- Path helpers ----------


def _data_root() -> Path:
    value = os.environ.get("CTO_OS_DATA", "").strip()
    if not value:
        raise PullCrash("CTO_OS_DATA env var is missing or empty")
    root = Path(os.path.expanduser(value)).resolve()
    if not root.is_dir():
        raise PullCrash(f"{root} does not exist or is not a directory")
    return root


def _cache_dir(data_root: Path) -> Path:
    d = data_root / "integrations-cache" / "linear"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _integrations_config_path() -> Path:
    return Path(__file__).resolve().parent / "lib" / "integrations.yaml"


def _load_ttl_minutes() -> int:
    path = _integrations_config_path()
    if not path.is_file():
        return DEFAULT_TTL_MINUTES
    try:
        cfg = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError:
        return DEFAULT_TTL_MINUTES
    linear_cfg = cfg.get("linear") or {}
    return int(linear_cfg.get("ttl_minutes", DEFAULT_TTL_MINUTES))


# ---------- Cache inspection ----------


def _newest_cache_file(cache_dir: Path) -> Path | None:
    files = sorted(
        (p for p in cache_dir.glob("*.json") if p.is_file()),
        key=lambda p: p.name,
    )
    return files[-1] if files else None


def _load_cache_file(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _cache_is_fresh(cache_path: Path, ttl_minutes: int, now: datetime) -> bool:
    """Parse the cache file's `pulled_at` to decide if we're within TTL."""
    payload = _load_cache_file(cache_path)
    pulled_at = payload.get("pulled_at")
    if not pulled_at:
        return False
    try:
        pulled_dt = datetime.fromisoformat(pulled_at.replace("Z", "+00:00"))
    except ValueError:
        return False
    age = now - pulled_dt
    return age < timedelta(minutes=ttl_minutes)


def _watermark_from_cache(cache_path: Path | None) -> str | None:
    """Return the max `updatedAt` across issues in the most-recent cache, or
    None if no cache exists."""
    if cache_path is None:
        return None
    payload = _load_cache_file(cache_path)
    issues = payload.get("issues") or []
    max_updated: str | None = None
    for issue in issues:
        u = issue.get("updatedAt")
        if u and (max_updated is None or u > max_updated):
            max_updated = u
    return max_updated


# ---------- Linear API ----------


_ISSUE_QUERY = """
query IssuesSince($first: Int!, $after: String, $filter: IssueFilter) {
  issues(first: $first, after: $after, filter: $filter) {
    nodes {
      id
      identifier
      title
      description
      priority
      state { name type }
      team { id name key }
      assignee { id name email }
      createdAt
      updatedAt
      completedAt
      labels { nodes { name } }
      url
    }
    pageInfo { hasNextPage endCursor }
  }
}
""".strip()


def _linear_request(api_key: str, query: str, variables: dict[str, Any]) -> dict[str, Any]:
    body = json.dumps({"query": query, "variables": variables}).encode("utf-8")
    req = urllib.request.Request(
        LINEAR_GRAPHQL_URL,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Authorization": api_key,
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace") if hasattr(e, "read") else ""
        raise PullCrash(f"Linear HTTP {e.code}: {detail[:500]}")
    except urllib.error.URLError as e:
        raise PullCrash(f"Linear request failed: {e.reason}")
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as e:
        raise PullCrash(f"Linear returned non-JSON response: {e}")
    if "errors" in payload:
        raise PullCrash(f"Linear GraphQL errors: {json.dumps(payload['errors'])[:500]}")
    return payload


def _build_filter(
    since_iso: str | None, team_ids: list[str] | None
) -> dict[str, Any]:
    filter_obj: dict[str, Any] = {}
    if since_iso:
        filter_obj["updatedAt"] = {"gte": since_iso}
    if team_ids:
        filter_obj["team"] = {"id": {"in": team_ids}}
    return filter_obj


def _flatten_issue(node: dict[str, Any]) -> dict[str, Any]:
    """Shape Linear's nested GraphQL response into something flat and
    friendlier for scan / read consumption later."""
    labels = [n["name"] for n in (node.get("labels") or {}).get("nodes", [])]
    return {
        "id": node.get("id"),
        "identifier": node.get("identifier"),
        "title": node.get("title"),
        "description": node.get("description"),
        "priority": node.get("priority"),
        "state": node.get("state"),
        "team": node.get("team"),
        "assignee": node.get("assignee"),
        "createdAt": node.get("createdAt"),
        "updatedAt": node.get("updatedAt"),
        "completedAt": node.get("completedAt"),
        "labels": labels,
        "url": node.get("url"),
    }


def _fetch_issues(
    api_key: str,
    since_iso: str | None,
    team_ids: list[str] | None,
    limit: int,
) -> list[dict[str, Any]]:
    """Pull up to `limit` issues total, paginating through Linear's cursor API."""
    issues: list[dict[str, Any]] = []
    after: str | None = None
    remaining = limit

    while remaining > 0:
        page_size = min(remaining, 100)  # Linear's per-page cap is 250; 100 is a polite default
        variables: dict[str, Any] = {"first": page_size, "after": after}
        filter_obj = _build_filter(since_iso, team_ids)
        if filter_obj:
            variables["filter"] = filter_obj

        payload = _linear_request(api_key, _ISSUE_QUERY, variables)
        data = (payload.get("data") or {}).get("issues") or {}
        nodes = data.get("nodes") or []
        page_info = data.get("pageInfo") or {}

        for node in nodes:
            issues.append(_flatten_issue(node))

        remaining -= len(nodes)
        if not page_info.get("hasNextPage"):
            break
        after = page_info.get("endCursor")
        if not after:
            break

    return issues


# ---------- Dedup + merge ----------


def _merge_issues(
    prior: list[dict[str, Any]], fresh: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Union prior + fresh, dedupe on `id`. When both sides have the same id,
    prefer the fresher one (fresh overwrites prior)."""
    merged: dict[str, dict[str, Any]] = {}
    for issue in prior:
        iid = issue.get("id")
        if iid:
            merged[iid] = issue
    for issue in fresh:
        iid = issue.get("id")
        if iid:
            merged[iid] = issue
    # Stable order: by updatedAt descending so the freshest are first.
    return sorted(
        merged.values(),
        key=lambda i: i.get("updatedAt") or "",
        reverse=True,
    )


# ---------- CLI ----------


def _parse_args(argv: list[str]) -> dict[str, Any]:
    parser = argparse.ArgumentParser(
        prog="pull_linear.py",
        description="Incremental pull of Linear issues into integrations-cache.",
    )
    parser.add_argument(
        "--args",
        default="{}",
        help='JSON object: {"team_ids":[...],"force":false,"limit":500}',
    )
    parsed = parser.parse_args(argv)
    try:
        opts = json.loads(parsed.args)
    except json.JSONDecodeError as e:
        raise PullCrash(f"--args is not valid JSON: {e}")
    if not isinstance(opts, dict):
        raise PullCrash("--args must be a JSON object")
    return opts


def _iso_now(now: datetime) -> str:
    return now.replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _file_stamp(now: datetime) -> str:
    """Filename-safe timestamp (colons replaced)."""
    return now.strftime("%Y-%m-%dT%H-%M-%SZ")


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    now = datetime.now(timezone.utc)

    try:
        opts = _parse_args(argv)
    except PullCrash as e:
        print(json.dumps({"status": "error", "message": str(e)}))
        return 1

    force = bool(opts.get("force", False))
    team_ids = opts.get("team_ids") or None
    limit = int(opts.get("limit", DEFAULT_LIMIT))

    api_key = os.environ.get("LINEAR_API_KEY", "").strip()
    if not api_key:
        print(json.dumps({"status": "error", "message": "LINEAR_API_KEY env var not set"}))
        return 1

    try:
        data_root = _data_root()
    except PullCrash as e:
        print(json.dumps({"status": "error", "message": str(e)}))
        return 1

    cache_dir = _cache_dir(data_root)
    newest = _newest_cache_file(cache_dir)
    ttl_minutes = _load_ttl_minutes()

    if not force and newest is not None and _cache_is_fresh(newest, ttl_minutes, now):
        result = {
            "status": "skipped-ttl",
            "file_written": None,
            "issue_count": 0,
            "new_since_last": 0,
            "message": (
                f"newest cache {newest.name} is within TTL ({ttl_minutes}m); "
                f"pass {{\"force\": true}} to override"
            ),
        }
        print(json.dumps(result))
        return 0

    # Watermark for incremental.
    watermark = _watermark_from_cache(newest)
    since_iso: str | None = None
    if watermark:
        try:
            wm_dt = datetime.fromisoformat(watermark.replace("Z", "+00:00"))
            buffered = wm_dt - timedelta(minutes=WATERMARK_BUFFER_MINUTES)
            since_iso = buffered.replace(microsecond=0).isoformat().replace("+00:00", "Z")
        except ValueError:
            since_iso = None  # Unparseable — fall back to full pull.

    try:
        fresh_issues = _fetch_issues(api_key, since_iso, team_ids, limit)
    except PullCrash as e:
        print(json.dumps({"status": "error", "message": str(e)}))
        return 1

    prior_issues: list[dict[str, Any]] = []
    if newest is not None:
        prior_issues = _load_cache_file(newest).get("issues") or []

    prior_ids = {i.get("id") for i in prior_issues if i.get("id")}
    new_since_last = sum(1 for i in fresh_issues if i.get("id") not in prior_ids)

    merged = _merge_issues(prior_issues, fresh_issues)

    out_name = _file_stamp(now) + ".json"
    out_path = cache_dir / out_name
    payload = {
        "pulled_at": _iso_now(now),
        "since": since_iso,
        "issue_count": len(merged),
        "issues": merged,
    }
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    rel_out = f"integrations-cache/linear/{out_name}"
    print(json.dumps({
        "status": "pulled",
        "file_written": rel_out,
        "issue_count": len(merged),
        "new_since_last": new_since_last,
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
