"""Tests for scripts/pull_linear.py.

Pull_linear makes HTTP calls to Linear's GraphQL API. We don't want that
happening in CI, so the tests monkeypatch urllib.request.urlopen via
importlib (loading pull_linear as a module, monkeypatching, then invoking
main directly — different pattern from the other subprocess-style tests,
but necessary to intercept the HTTP layer).

Covers:
  - Missing LINEAR_API_KEY → exit 1 with clear error.
  - Missing CTO_OS_DATA → exit 1.
  - Happy path: issues fetched, cached file written with expected shape.
  - TTL skip: recent cache exists → no HTTP call, status=skipped-ttl.
  - Force=True overrides TTL.
  - Watermark: prior cache exists (but stale) → GraphQL filter includes
    updatedAt gte (watermark - 5min).
  - Dedup: prior + fresh merge, same-id issue overwritten by fresher version.
  - HTTP 401 → exit 1 with 'Linear HTTP' in error.
  - GraphQL errors field → exit 1 with message.
"""
from __future__ import annotations

import importlib.util
import io
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest


REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = REPO_ROOT / "scripts" / "pull_linear.py"


@pytest.fixture
def pull_linear_module():
    """Load pull_linear.py as a module so we can monkeypatch its internals."""
    spec = importlib.util.spec_from_file_location("pull_linear", SCRIPT_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def data_root(tmp_path, monkeypatch):
    monkeypatch.setenv("CTO_OS_DATA", str(tmp_path))
    monkeypatch.setenv("LINEAR_API_KEY", "fake-api-key")
    return tmp_path


# ---------- Fake urlopen ----------


class _FakeResponse:
    def __init__(self, payload: dict[str, Any], status: int = 200):
        self._body = json.dumps(payload).encode("utf-8")
        self.status = status

    def read(self) -> bytes:
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False


def _issue_node(
    id: str,
    identifier: str,
    title: str,
    updated: str,
    *,
    priority: int = 2,
    state_name: str = "In Progress",
    team_key: str = "ENG",
) -> dict[str, Any]:
    return {
        "id": id,
        "identifier": identifier,
        "title": title,
        "description": None,
        "priority": priority,
        "state": {"name": state_name, "type": "started"},
        "team": {"id": "team-1", "name": "Platform", "key": team_key},
        "assignee": {"id": "user-1", "name": "Jane", "email": "j@example.com"},
        "createdAt": "2026-04-01T00:00:00Z",
        "updatedAt": updated,
        "completedAt": None,
        "labels": {"nodes": [{"name": "bug"}]},
        "url": f"https://linear.app/acme/issue/{identifier}",
    }


def _canned_issues_response(nodes: list[dict[str, Any]], has_next: bool = False, end_cursor: str | None = None) -> dict[str, Any]:
    return {
        "data": {
            "issues": {
                "nodes": nodes,
                "pageInfo": {
                    "hasNextPage": has_next,
                    "endCursor": end_cursor,
                },
            }
        }
    }


# ---------- Preflight failures ----------


def test_missing_api_key_exits_1(pull_linear_module, tmp_path, monkeypatch):
    monkeypatch.setenv("CTO_OS_DATA", str(tmp_path))
    monkeypatch.delenv("LINEAR_API_KEY", raising=False)

    exit_code = pull_linear_module.main(["--args", "{}"])
    assert exit_code == 1


def test_missing_data_root_exits_1(pull_linear_module, monkeypatch):
    monkeypatch.setenv("LINEAR_API_KEY", "fake")
    monkeypatch.delenv("CTO_OS_DATA", raising=False)

    exit_code = pull_linear_module.main(["--args", "{}"])
    assert exit_code == 1


def test_invalid_args_json_exits_1(pull_linear_module, data_root, capsys):
    exit_code = pull_linear_module.main(["--args", "{not json"])
    assert exit_code == 1
    out = capsys.readouterr()
    payload = json.loads(out.out.strip().split("\n")[-1])
    assert payload["status"] == "error"


# ---------- Happy path ----------


def test_successful_pull_writes_cache(pull_linear_module, data_root, monkeypatch, capsys):
    captured_requests: list[Any] = []

    def fake_urlopen(req, timeout=30):
        captured_requests.append(req)
        return _FakeResponse(_canned_issues_response([
            _issue_node("I-1", "ENG-1", "first", "2026-04-22T09:00:00Z"),
            _issue_node("I-2", "ENG-2", "second", "2026-04-22T09:30:00Z"),
        ]))

    monkeypatch.setattr(pull_linear_module.urllib.request, "urlopen", fake_urlopen)

    exit_code = pull_linear_module.main(["--args", "{}"])
    assert exit_code == 0, capsys.readouterr()

    captured = capsys.readouterr()
    report = json.loads(captured.out.strip().split("\n")[-1])
    assert report["status"] == "pulled"
    assert report["issue_count"] == 2
    assert report["new_since_last"] == 2

    # File exists with expected shape.
    rel = report["file_written"]
    out_file = data_root / rel
    assert out_file.is_file()
    payload = json.loads(out_file.read_text(encoding="utf-8"))
    assert payload["issue_count"] == 2
    assert len(payload["issues"]) == 2
    ids = {i["id"] for i in payload["issues"]}
    assert ids == {"I-1", "I-2"}

    # Labels flattened.
    for issue in payload["issues"]:
        assert issue["labels"] == ["bug"]

    # Auth header was set on request.
    assert len(captured_requests) == 1
    req = captured_requests[0]
    assert req.headers.get("Authorization") == "fake-api-key"


# ---------- TTL ----------


def test_ttl_skip_when_cache_fresh(pull_linear_module, data_root, monkeypatch, capsys):
    cache_dir = data_root / "integrations-cache" / "linear"
    cache_dir.mkdir(parents=True)
    fresh_ts = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    (cache_dir / "2026-04-22T09-00-00Z.json").write_text(
        json.dumps({"pulled_at": fresh_ts, "issues": []}),
        encoding="utf-8",
    )

    def fake_urlopen(*a, **kw):
        raise AssertionError("urlopen should not be called when cache is fresh")

    monkeypatch.setattr(pull_linear_module.urllib.request, "urlopen", fake_urlopen)

    exit_code = pull_linear_module.main(["--args", "{}"])
    assert exit_code == 0
    captured = capsys.readouterr()
    report = json.loads(captured.out.strip().split("\n")[-1])
    assert report["status"] == "skipped-ttl"


def test_force_overrides_ttl(pull_linear_module, data_root, monkeypatch, capsys):
    cache_dir = data_root / "integrations-cache" / "linear"
    cache_dir.mkdir(parents=True)
    fresh_ts = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    (cache_dir / "2026-04-22T09-00-00Z.json").write_text(
        json.dumps({"pulled_at": fresh_ts, "issues": []}),
        encoding="utf-8",
    )

    called = []

    def fake_urlopen(req, timeout=30):
        called.append(req)
        return _FakeResponse(_canned_issues_response([
            _issue_node("I-new", "ENG-N", "forced", "2026-04-22T10:00:00Z"),
        ]))

    monkeypatch.setattr(pull_linear_module.urllib.request, "urlopen", fake_urlopen)

    exit_code = pull_linear_module.main(["--args", json.dumps({"force": True})])
    assert exit_code == 0
    assert len(called) == 1
    captured = capsys.readouterr()
    report = json.loads(captured.out.strip().split("\n")[-1])
    assert report["status"] == "pulled"


# ---------- Watermark + dedup ----------


def test_watermark_filter_applied_when_prior_cache_exists(pull_linear_module, data_root, monkeypatch, capsys):
    # Seed stale cache: pulled_at well outside TTL.
    cache_dir = data_root / "integrations-cache" / "linear"
    cache_dir.mkdir(parents=True)
    stale_ts = (datetime.now(timezone.utc) - timedelta(hours=5)).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    prior_issue = _issue_node("I-old", "ENG-OLD", "old", "2026-04-22T08:00:00Z")
    (cache_dir / "2026-04-22T05-00-00Z.json").write_text(
        json.dumps({
            "pulled_at": stale_ts,
            "issue_count": 1,
            "issues": [_flatten(prior_issue)],
        }),
        encoding="utf-8",
    )

    captured_bodies: list[dict[str, Any]] = []

    def fake_urlopen(req, timeout=30):
        captured_bodies.append(json.loads(req.data.decode("utf-8")))
        return _FakeResponse(_canned_issues_response([
            _issue_node("I-new", "ENG-NEW", "new", "2026-04-22T10:00:00Z"),
        ]))

    monkeypatch.setattr(pull_linear_module.urllib.request, "urlopen", fake_urlopen)

    exit_code = pull_linear_module.main(["--args", "{}"])
    assert exit_code == 0

    # Request body should include an updatedAt filter.
    assert len(captured_bodies) == 1
    variables = captured_bodies[0]["variables"]
    assert "filter" in variables
    assert "updatedAt" in variables["filter"]
    since = variables["filter"]["updatedAt"]["gte"]
    # Watermark was 08:00:00; buffer is 5 minutes, so since should be 07:55:00.
    assert since == "2026-04-22T07:55:00Z"

    # Merged cache file has both prior and fresh issues.
    captured = capsys.readouterr()
    report = json.loads(captured.out.strip().split("\n")[-1])
    merged = json.loads((data_root / report["file_written"]).read_text())
    ids = {i["id"] for i in merged["issues"]}
    assert ids == {"I-old", "I-new"}


def test_dedup_on_same_id(pull_linear_module, data_root, monkeypatch, capsys):
    cache_dir = data_root / "integrations-cache" / "linear"
    cache_dir.mkdir(parents=True)
    stale_ts = (datetime.now(timezone.utc) - timedelta(hours=5)).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    prior = _flatten(_issue_node("I-1", "ENG-1", "old title", "2026-04-22T08:00:00Z"))
    (cache_dir / "2026-04-22T05-00-00Z.json").write_text(
        json.dumps({"pulled_at": stale_ts, "issue_count": 1, "issues": [prior]}),
        encoding="utf-8",
    )

    def fake_urlopen(req, timeout=30):
        # Same id, fresher updatedAt, new title.
        return _FakeResponse(_canned_issues_response([
            _issue_node("I-1", "ENG-1", "new title", "2026-04-22T10:00:00Z"),
        ]))

    monkeypatch.setattr(pull_linear_module.urllib.request, "urlopen", fake_urlopen)

    exit_code = pull_linear_module.main(["--args", "{}"])
    assert exit_code == 0

    captured = capsys.readouterr()
    report = json.loads(captured.out.strip().split("\n")[-1])
    merged = json.loads((data_root / report["file_written"]).read_text())
    assert len(merged["issues"]) == 1
    assert merged["issues"][0]["title"] == "new title"


# ---------- HTTP / GraphQL errors ----------


def test_http_401_returns_error(pull_linear_module, data_root, monkeypatch, capsys):
    import urllib.error

    def fake_urlopen(req, timeout=30):
        error_body = io.BytesIO(b'{"error":"unauthorized"}')
        raise urllib.error.HTTPError(
            url="https://api.linear.app/graphql",
            code=401,
            msg="Unauthorized",
            hdrs=None,  # type: ignore[arg-type]
            fp=error_body,
        )

    monkeypatch.setattr(pull_linear_module.urllib.request, "urlopen", fake_urlopen)

    exit_code = pull_linear_module.main(["--args", "{}"])
    assert exit_code == 1
    captured = capsys.readouterr()
    report = json.loads(captured.out.strip().split("\n")[-1])
    assert report["status"] == "error"
    assert "Linear HTTP 401" in report["message"]


def test_graphql_errors_returns_error(pull_linear_module, data_root, monkeypatch, capsys):
    def fake_urlopen(req, timeout=30):
        return _FakeResponse({"errors": [{"message": "Bad query"}]})

    monkeypatch.setattr(pull_linear_module.urllib.request, "urlopen", fake_urlopen)

    exit_code = pull_linear_module.main(["--args", "{}"])
    assert exit_code == 1
    captured = capsys.readouterr()
    report = json.loads(captured.out.strip().split("\n")[-1])
    assert report["status"] == "error"
    assert "GraphQL" in report["message"]


# ---------- Helper ----------


def _flatten(node: dict[str, Any]) -> dict[str, Any]:
    """Same flattening pull_linear does, useful for seeding prior cache."""
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
