"""Tests for scripts/pull_slack.py.

Mirrors the pull_linear pattern: load the script as a module so we can
monkeypatch urllib.request.urlopen with canned responses. Slack's API
pattern (POST form-encoded, multiple methods per run) differs from
Linear's single GraphQL endpoint, so the fake_urlopen here dispatches by
URL to return the right canned payload.

Covers:
  - Missing SLACK_BOT_TOKEN → exit 1.
  - Missing CTO_OS_DATA → exit 1.
  - Happy path: channels.list + users.list + conversations.history → cache
    file written, message flattened with channel/user name resolution.
  - TTL skip.
  - Force overrides TTL.
  - Watermark per channel: prior cache exists with a max `ts` per channel,
    next pull passes `oldest` as that ts minus buffer.
  - Dedup: same (channel_id, ts) collapses; fresh wins.
  - Slack `ok: false` → exit 1 with Slack API error message.
  - HTTP error → exit 1.
  - Only polls channels where `is_member: true` (bot isn't in every listed
    channel, and `conversations.history` would fail on those).
"""
from __future__ import annotations

import importlib.util
import io
import json
import os
import sys
import urllib.parse
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest


REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = REPO_ROOT / "scripts" / "pull_slack.py"


@pytest.fixture
def pull_slack_module():
    spec = importlib.util.spec_from_file_location("pull_slack", SCRIPT_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def data_root(tmp_path, monkeypatch):
    monkeypatch.setenv("CTO_OS_DATA", str(tmp_path))
    monkeypatch.setenv("SLACK_BOT_TOKEN", "xoxb-fake-token")
    return tmp_path


# ---------- Fake response ----------


class _FakeResponse:
    def __init__(self, payload: dict[str, Any]):
        self._body = json.dumps(payload).encode("utf-8")

    def read(self) -> bytes:
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False


def _request_method(req) -> str:
    """Extract the Slack method name from a request URL."""
    return req.full_url.rsplit("/", 1)[-1]


def _request_params(req) -> dict[str, str]:
    body = req.data.decode("utf-8") if req.data else ""
    return dict(urllib.parse.parse_qsl(body))


def _make_dispatcher(responses: dict[str, Any]):
    """Build a fake urlopen that dispatches on Slack method name.

    `responses` is a dict of {method_name: payload_or_list}. If the value is a
    list, successive calls to that method return successive payloads (for
    pagination tests)."""
    call_log: list[tuple[str, dict[str, str]]] = []

    def fake_urlopen(req, timeout=30):
        method = _request_method(req)
        params = _request_params(req)
        call_log.append((method, params))

        resp = responses.get(method)
        if resp is None:
            raise AssertionError(f"unexpected Slack method call: {method}")
        if isinstance(resp, list):
            if not resp:
                raise AssertionError(f"no more responses staged for {method}")
            payload = resp.pop(0)
        else:
            payload = resp
        return _FakeResponse(payload)

    return fake_urlopen, call_log


def _channels_list_response(channels: list[dict[str, Any]], next_cursor: str = "") -> dict[str, Any]:
    return {
        "ok": True,
        "channels": channels,
        "response_metadata": {"next_cursor": next_cursor},
    }


def _users_list_response(members: list[dict[str, Any]], next_cursor: str = "") -> dict[str, Any]:
    return {
        "ok": True,
        "members": members,
        "response_metadata": {"next_cursor": next_cursor},
    }


def _history_response(messages: list[dict[str, Any]], has_more: bool = False, next_cursor: str = "") -> dict[str, Any]:
    return {
        "ok": True,
        "messages": messages,
        "has_more": has_more,
        "response_metadata": {"next_cursor": next_cursor},
    }


# ---------- Preflight failures ----------


def test_missing_token_exits_1(pull_slack_module, tmp_path, monkeypatch):
    monkeypatch.setenv("CTO_OS_DATA", str(tmp_path))
    monkeypatch.delenv("SLACK_BOT_TOKEN", raising=False)

    assert pull_slack_module.main(["--args", "{}"]) == 1


def test_missing_data_root_exits_1(pull_slack_module, monkeypatch):
    monkeypatch.setenv("SLACK_BOT_TOKEN", "xoxb-fake")
    monkeypatch.delenv("CTO_OS_DATA", raising=False)

    assert pull_slack_module.main(["--args", "{}"]) == 1


def test_invalid_args_json_exits_1(pull_slack_module, data_root, capsys):
    assert pull_slack_module.main(["--args", "{not json"]) == 1
    out = capsys.readouterr().out
    payload = json.loads(out.strip().split("\n")[-1])
    assert payload["status"] == "error"


# ---------- Happy path ----------


def test_successful_pull_writes_cache(pull_slack_module, data_root, monkeypatch, capsys):
    fake_urlopen, call_log = _make_dispatcher({
        "conversations.list": _channels_list_response([
            {"id": "C1", "name": "eng-all", "is_private": False, "is_member": True},
            {"id": "C2", "name": "not-in-this-one", "is_private": False, "is_member": False},
        ]),
        "users.list": _users_list_response([
            {"id": "U1", "name": "jane", "real_name": "Jane Doe", "is_bot": False, "deleted": False},
            {"id": "U2", "name": "mike", "real_name": "Mike Smith", "is_bot": False, "deleted": False},
        ]),
        "conversations.history": _history_response([
            {"ts": "1704902400.000123", "user": "U1", "text": "hello", "type": "message"},
            {"ts": "1704902500.000456", "user": "U2", "text": "hi", "type": "message"},
        ]),
    })

    monkeypatch.setattr(pull_slack_module.urllib.request, "urlopen", fake_urlopen)

    exit_code = pull_slack_module.main(["--args", "{}"])
    assert exit_code == 0, capsys.readouterr()

    captured = capsys.readouterr()
    report = json.loads(captured.out.strip().split("\n")[-1])
    assert report["status"] == "pulled"
    assert report["message_count"] == 2
    assert report["new_since_last"] == 2
    assert report["channels_polled"] == 1  # only C1 — bot isn't in C2

    # History called exactly once (only for C1, not C2 which bot isn't in).
    history_calls = [c for c in call_log if c[0] == "conversations.history"]
    assert len(history_calls) == 1
    assert history_calls[0][1]["channel"] == "C1"

    # File content.
    rel = report["file_written"]
    out_file = data_root / rel
    assert out_file.is_file()
    payload = json.loads(out_file.read_text(encoding="utf-8"))
    assert payload["message_count"] == 2
    assert "C1" in payload["channels"]
    assert "C2" in payload["channels"]   # listed, just not polled
    assert payload["users"]["U1"]["name"] == "jane"

    # Messages flattened with name resolution.
    messages = payload["messages"]
    assert all(m["channel_name"] == "eng-all" for m in messages)
    user_names = {m["user_name"] for m in messages}
    assert user_names == {"jane", "mike"}


def test_no_channels_bot_is_in(pull_slack_module, data_root, monkeypatch, capsys):
    fake_urlopen, call_log = _make_dispatcher({
        "conversations.list": _channels_list_response([
            {"id": "C1", "name": "general", "is_private": False, "is_member": False},
        ]),
        "users.list": _users_list_response([]),
    })
    monkeypatch.setattr(pull_slack_module.urllib.request, "urlopen", fake_urlopen)

    exit_code = pull_slack_module.main(["--args", "{}"])
    assert exit_code == 0

    captured = capsys.readouterr()
    report = json.loads(captured.out.strip().split("\n")[-1])
    assert report["status"] == "pulled"
    assert report["message_count"] == 0
    assert report["channels_polled"] == 0
    # No conversations.history calls.
    assert not any(c[0] == "conversations.history" for c in call_log)


# ---------- TTL ----------


def test_ttl_skip_when_cache_fresh(pull_slack_module, data_root, monkeypatch, capsys):
    cache_dir = data_root / "integrations-cache" / "slack"
    cache_dir.mkdir(parents=True)
    fresh_ts = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    (cache_dir / "2026-04-22T09-00-00Z.json").write_text(
        json.dumps({"pulled_at": fresh_ts, "messages": []}),
        encoding="utf-8",
    )

    def fake_urlopen(*a, **kw):
        raise AssertionError("urlopen should not be called when cache is fresh")

    monkeypatch.setattr(pull_slack_module.urllib.request, "urlopen", fake_urlopen)

    assert pull_slack_module.main(["--args", "{}"]) == 0
    captured = capsys.readouterr()
    report = json.loads(captured.out.strip().split("\n")[-1])
    assert report["status"] == "skipped-ttl"


def test_force_overrides_ttl(pull_slack_module, data_root, monkeypatch, capsys):
    cache_dir = data_root / "integrations-cache" / "slack"
    cache_dir.mkdir(parents=True)
    fresh_ts = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    (cache_dir / "2026-04-22T09-00-00Z.json").write_text(
        json.dumps({"pulled_at": fresh_ts, "messages": []}),
        encoding="utf-8",
    )

    fake_urlopen, _ = _make_dispatcher({
        "conversations.list": _channels_list_response([]),
        "users.list": _users_list_response([]),
    })
    monkeypatch.setattr(pull_slack_module.urllib.request, "urlopen", fake_urlopen)

    assert pull_slack_module.main(["--args", json.dumps({"force": True})]) == 0
    captured = capsys.readouterr()
    report = json.loads(captured.out.strip().split("\n")[-1])
    assert report["status"] == "pulled"


# ---------- Watermark ----------


def test_watermark_per_channel_passed_as_oldest(pull_slack_module, data_root, monkeypatch, capsys):
    cache_dir = data_root / "integrations-cache" / "slack"
    cache_dir.mkdir(parents=True)
    stale_ts = (datetime.now(timezone.utc) - timedelta(hours=5)).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    # Seed a stale cache with prior messages for two channels.
    (cache_dir / "2026-04-22T05-00-00Z.json").write_text(
        json.dumps({
            "pulled_at": stale_ts,
            "channels": {
                "C1": {"id": "C1", "name": "eng", "is_private": False, "is_member": True},
                "C2": {"id": "C2", "name": "platform", "is_private": False, "is_member": True},
            },
            "users": {},
            "messages": [
                {"ts": "1704902500.000000", "channel_id": "C1", "channel_name": "eng",
                 "user_id": "U1", "user_name": "jane", "text": "old", "type": "message"},
                {"ts": "1704903000.000000", "channel_id": "C1", "channel_name": "eng",
                 "user_id": "U1", "user_name": "jane", "text": "older-on-C1", "type": "message"},
                {"ts": "1704904000.000000", "channel_id": "C2", "channel_name": "platform",
                 "user_id": "U2", "user_name": "mike", "text": "on-C2", "type": "message"},
            ],
        }),
        encoding="utf-8",
    )

    fake_urlopen, call_log = _make_dispatcher({
        "conversations.list": _channels_list_response([
            {"id": "C1", "name": "eng", "is_private": False, "is_member": True},
            {"id": "C2", "name": "platform", "is_private": False, "is_member": True},
        ]),
        "users.list": _users_list_response([
            {"id": "U1", "name": "jane", "real_name": "Jane", "is_bot": False, "deleted": False},
            {"id": "U2", "name": "mike", "real_name": "Mike", "is_bot": False, "deleted": False},
        ]),
        "conversations.history": [
            _history_response([
                {"ts": "1704903500.000000", "user": "U1", "text": "new on C1", "type": "message"},
            ]),
            _history_response([
                {"ts": "1704904500.000000", "user": "U2", "text": "new on C2", "type": "message"},
            ]),
        ],
    })

    monkeypatch.setattr(pull_slack_module.urllib.request, "urlopen", fake_urlopen)

    assert pull_slack_module.main(["--args", "{}"]) == 0

    # Two history calls, each with the appropriate oldest param.
    history_calls = [c for c in call_log if c[0] == "conversations.history"]
    assert len(history_calls) == 2
    by_channel = {c[1]["channel"]: c[1] for c in history_calls}

    # C1 max ts was 1704903000. Oldest should be that minus 60s buffer.
    assert by_channel["C1"]["oldest"] == f"{1704903000.0 - 60:.6f}"
    # C2 max ts was 1704904000.
    assert by_channel["C2"]["oldest"] == f"{1704904000.0 - 60:.6f}"


def test_dedup_on_same_ts_and_channel(pull_slack_module, data_root, monkeypatch, capsys):
    cache_dir = data_root / "integrations-cache" / "slack"
    cache_dir.mkdir(parents=True)
    stale_ts = (datetime.now(timezone.utc) - timedelta(hours=5)).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    (cache_dir / "2026-04-22T05-00-00Z.json").write_text(
        json.dumps({
            "pulled_at": stale_ts,
            "channels": {"C1": {"id": "C1", "name": "eng", "is_private": False, "is_member": True}},
            "users": {},
            "messages": [
                {"ts": "1704902500.000000", "channel_id": "C1", "channel_name": "eng",
                 "user_id": "U1", "user_name": "jane", "text": "original", "type": "message"},
            ],
        }),
        encoding="utf-8",
    )

    fake_urlopen, _ = _make_dispatcher({
        "conversations.list": _channels_list_response([
            {"id": "C1", "name": "eng", "is_private": False, "is_member": True},
        ]),
        "users.list": _users_list_response([
            {"id": "U1", "name": "jane", "real_name": "Jane", "is_bot": False, "deleted": False},
        ]),
        "conversations.history": _history_response([
            # Same ts as prior, new text (edit scenario).
            {"ts": "1704902500.000000", "user": "U1", "text": "edited", "type": "message"},
        ]),
    })
    monkeypatch.setattr(pull_slack_module.urllib.request, "urlopen", fake_urlopen)

    assert pull_slack_module.main(["--args", "{}"]) == 0

    captured = capsys.readouterr()
    report = json.loads(captured.out.strip().split("\n")[-1])
    merged = json.loads((data_root / report["file_written"]).read_text())
    assert len(merged["messages"]) == 1
    assert merged["messages"][0]["text"] == "edited"


# ---------- API + HTTP errors ----------


def test_slack_ok_false_exits_1(pull_slack_module, data_root, monkeypatch, capsys):
    fake_urlopen, _ = _make_dispatcher({
        "conversations.list": {"ok": False, "error": "invalid_auth"},
    })
    monkeypatch.setattr(pull_slack_module.urllib.request, "urlopen", fake_urlopen)

    assert pull_slack_module.main(["--args", "{}"]) == 1
    captured = capsys.readouterr()
    report = json.loads(captured.out.strip().split("\n")[-1])
    assert report["status"] == "error"
    assert "invalid_auth" in report["message"]


def test_http_error_exits_1(pull_slack_module, data_root, monkeypatch, capsys):
    import urllib.error

    def fake_urlopen(req, timeout=30):
        raise urllib.error.HTTPError(
            url="https://slack.com/api/conversations.list",
            code=429,
            msg="Too Many Requests",
            hdrs=None,  # type: ignore[arg-type]
            fp=io.BytesIO(b"rate limited"),
        )

    monkeypatch.setattr(pull_slack_module.urllib.request, "urlopen", fake_urlopen)

    assert pull_slack_module.main(["--args", "{}"]) == 1
    captured = capsys.readouterr()
    report = json.loads(captured.out.strip().split("\n")[-1])
    assert "Slack HTTP 429" in report["message"]


# ---------- Channel filter ----------


def test_channel_filter_limits_scope(pull_slack_module, data_root, monkeypatch, capsys):
    fake_urlopen, call_log = _make_dispatcher({
        "conversations.list": _channels_list_response([
            {"id": "C1", "name": "eng-all", "is_private": False, "is_member": True},
            {"id": "C2", "name": "random", "is_private": False, "is_member": True},
        ]),
        "users.list": _users_list_response([]),
        "conversations.history": _history_response([]),
    })
    monkeypatch.setattr(pull_slack_module.urllib.request, "urlopen", fake_urlopen)

    assert pull_slack_module.main(["--args", json.dumps({"channel_ids": ["C1"]})]) == 0

    history_calls = [c for c in call_log if c[0] == "conversations.history"]
    assert len(history_calls) == 1
    assert history_calls[0][1]["channel"] == "C1"
