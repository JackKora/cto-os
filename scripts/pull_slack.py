#!/usr/bin/env python3
"""
pull_slack.py — incremental pull of Slack messages into
`$CTO_OS_DATA/integrations-cache/slack/`.

Pulls messages from every channel the bot token has access to (public +
private channels the bot has been invited to). Resolves user IDs and channel
IDs to human-readable names so downstream consumers don't need a second
lookup.

Behavior:
  - TTL check. If the most-recent cached file is within the configured TTL
    (see `scripts/lib/integrations.yaml`, key `slack.ttl_minutes`), the pull
    is skipped unless `{"force": true}` is passed. Default TTL per
    docs/DATA_REPO.md is 240 minutes (4h).
  - Incremental via watermark on `ts` (Slack's monotonic message timestamp).
    Reads the newest cached file, finds the max `ts` per channel, passes it
    as `oldest` on the next `conversations.history` call. Dedupes on `ts`
    across prior + fresh.
  - Messages only. Reactions, files, thread replies are out of scope.

Auth: reads `SLACK_BOT_TOKEN` from env. Missing or empty → exit 1.
Token must have scopes: `channels:history`, `groups:history`, `channels:read`,
`groups:read`, `users:read`. Without them, Slack returns `ok: false` with an
error code and the script exits 1.

Output file shape: `$CTO_OS_DATA/integrations-cache/slack/{ISO_TIMESTAMP}.json`
  {
    "pulled_at":   "2026-04-22T10:00:00Z",
    "channels":    {"C123": {"id": "C123", "name": "eng-all", "is_private": false}, ...},
    "users":       {"U456": {"id": "U456", "name": "jane.doe", "real_name": "Jane Doe", "is_bot": false}, ...},
    "message_count": 42,
    "messages": [
      {
        "ts":           "1704902400.000123",
        "channel_id":   "C123",
        "channel_name": "eng-all",
        "user_id":      "U456",
        "user_name":    "jane.doe",
        "text":         "...",
        "thread_ts":    null,          // if replying in a thread
        "type":         "message",
        "subtype":      null,
        "is_bot":       false
      }
    ]
  }

Stdout (always JSON):
  {
    "status":            "pulled" | "skipped-ttl" | "error",
    "file_written":      "integrations-cache/slack/2026-04-22T10-00-00Z.json" | null,
    "message_count":     42,
    "new_since_last":    15,
    "channels_polled":   12,
    "message":           "..."   // on error/skip
  }

Exit codes:
  0 — success (including skipped-ttl)
  1 — crash (auth failure, HTTP error, bad env, Slack API error)
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import yaml


SLACK_API_BASE = "https://slack.com/api"
DEFAULT_TTL_MINUTES = 240   # fallback if integrations.yaml is missing
DEFAULT_MESSAGES_PER_CHANNEL = 200
WATERMARK_BUFFER_SECONDS = 60   # Slack ts is fractional-second — small buffer


# ---------- Errors ----------


class PullCrash(Exception):
    """Exit 1 — the script couldn't complete."""


# ---------- Path helpers (mirror pull_linear.py) ----------


def _data_root() -> Path:
    value = os.environ.get("CTO_OS_DATA", "").strip()
    if not value:
        raise PullCrash("CTO_OS_DATA env var is missing or empty")
    root = Path(os.path.expanduser(value)).resolve()
    if not root.is_dir():
        raise PullCrash(f"{root} does not exist or is not a directory")
    return root


def _cache_dir(data_root: Path) -> Path:
    d = data_root / "integrations-cache" / "slack"
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
    slack_cfg = cfg.get("slack") or {}
    return int(slack_cfg.get("ttl_minutes", DEFAULT_TTL_MINUTES))


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
    payload = _load_cache_file(cache_path)
    pulled_at = payload.get("pulled_at")
    if not pulled_at:
        return False
    try:
        pulled_dt = datetime.fromisoformat(pulled_at.replace("Z", "+00:00"))
    except ValueError:
        return False
    return (now - pulled_dt) < timedelta(minutes=ttl_minutes)


def _watermark_per_channel(cache_path: Path | None) -> dict[str, str]:
    """Return the max `ts` per channel across messages in the most-recent
    cache. Keys are channel_ids; values are Slack-format ts strings
    (e.g., '1704902400.000123'). Returns empty dict if no cache."""
    if cache_path is None:
        return {}
    payload = _load_cache_file(cache_path)
    messages = payload.get("messages") or []
    watermarks: dict[str, str] = {}
    for m in messages:
        ch = m.get("channel_id")
        ts = m.get("ts")
        if not ch or not ts:
            continue
        current = watermarks.get(ch)
        if current is None or _ts_gt(ts, current):
            watermarks[ch] = ts
    return watermarks


def _ts_gt(a: str, b: str) -> bool:
    """Compare two Slack ts strings numerically (they sort lexically
    correctly for valid values, but float comparison is safer)."""
    try:
        return float(a) > float(b)
    except ValueError:
        return a > b


# ---------- Slack API ----------


def _slack_request(token: str, method: str, params: dict[str, Any]) -> dict[str, Any]:
    """POST to Slack Web API. Slack accepts form-encoded body on most methods."""
    url = f"{SLACK_API_BASE}/{method}"
    body = urllib.parse.urlencode({
        k: v for k, v in params.items() if v is not None
    }).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/x-www-form-urlencoded; charset=utf-8",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace") if hasattr(e, "read") else ""
        raise PullCrash(f"Slack HTTP {e.code}: {detail[:500]}")
    except urllib.error.URLError as e:
        raise PullCrash(f"Slack request failed: {e.reason}")

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as e:
        raise PullCrash(f"Slack returned non-JSON response: {e}")

    if not payload.get("ok"):
        err = payload.get("error", "unknown")
        raise PullCrash(f"Slack API error on {method}: {err}")

    return payload


def _list_channels(token: str, channel_filter: list[str] | None) -> list[dict[str, Any]]:
    """Enumerate channels the bot can see (public + private it's been invited
    to). Uses `conversations.list` with cursor pagination."""
    channels: list[dict[str, Any]] = []
    cursor: str | None = None

    while True:
        params: dict[str, Any] = {
            "types": "public_channel,private_channel",
            "exclude_archived": "true",
            "limit": 200,
        }
        if cursor:
            params["cursor"] = cursor

        payload = _slack_request(token, "conversations.list", params)
        for ch in payload.get("channels") or []:
            if channel_filter and ch.get("id") not in channel_filter:
                continue
            channels.append({
                "id": ch.get("id"),
                "name": ch.get("name"),
                "is_private": bool(ch.get("is_private")),
                "is_member": bool(ch.get("is_member")),
            })

        next_cursor = (payload.get("response_metadata") or {}).get("next_cursor")
        if not next_cursor:
            break
        cursor = next_cursor

    return channels


def _list_users(token: str) -> dict[str, dict[str, Any]]:
    """Enumerate users for ID → name resolution. Returns {user_id: profile}."""
    users: dict[str, dict[str, Any]] = {}
    cursor: str | None = None

    while True:
        params: dict[str, Any] = {"limit": 200}
        if cursor:
            params["cursor"] = cursor

        payload = _slack_request(token, "users.list", params)
        for u in payload.get("members") or []:
            uid = u.get("id")
            if not uid:
                continue
            users[uid] = {
                "id": uid,
                "name": u.get("name"),
                "real_name": u.get("real_name"),
                "is_bot": bool(u.get("is_bot")),
                "deleted": bool(u.get("deleted")),
            }

        next_cursor = (payload.get("response_metadata") or {}).get("next_cursor")
        if not next_cursor:
            break
        cursor = next_cursor

    return users


def _fetch_channel_messages(
    token: str,
    channel_id: str,
    oldest_ts: str | None,
    limit: int,
) -> list[dict[str, Any]]:
    """Fetch messages from a single channel via `conversations.history`.
    Returns the raw message list (unflattened — caller handles shape)."""
    messages: list[dict[str, Any]] = []
    cursor: str | None = None
    remaining = limit

    while remaining > 0:
        page_size = min(remaining, 200)  # Slack's per-page cap is 999; 200 is polite
        params: dict[str, Any] = {
            "channel": channel_id,
            "limit": page_size,
        }
        if oldest_ts:
            params["oldest"] = oldest_ts
        if cursor:
            params["cursor"] = cursor

        payload = _slack_request(token, "conversations.history", params)
        batch = payload.get("messages") or []
        messages.extend(batch)
        remaining -= len(batch)

        if not payload.get("has_more"):
            break
        cursor = (payload.get("response_metadata") or {}).get("next_cursor")
        if not cursor:
            break

    return messages


def _flatten_message(
    raw: dict[str, Any],
    channel: dict[str, Any],
    users: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Shape a raw Slack message into the flat record consumers read."""
    user_id = raw.get("user") or raw.get("bot_id")
    user_record = users.get(user_id or "", {})
    return {
        "ts": raw.get("ts"),
        "channel_id": channel.get("id"),
        "channel_name": channel.get("name"),
        "user_id": user_id,
        "user_name": user_record.get("name") or raw.get("username"),
        "text": raw.get("text", ""),
        "thread_ts": raw.get("thread_ts"),
        "type": raw.get("type"),
        "subtype": raw.get("subtype"),
        "is_bot": bool(user_record.get("is_bot") or raw.get("bot_id") or raw.get("subtype") == "bot_message"),
    }


# ---------- Dedup + merge ----------


def _merge_messages(
    prior: list[dict[str, Any]], fresh: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Union prior + fresh, dedupe on (channel_id, ts). Fresh overwrites prior."""
    merged: dict[tuple[str, str], dict[str, Any]] = {}
    for m in prior:
        key = (m.get("channel_id") or "", m.get("ts") or "")
        if key[1]:
            merged[key] = m
    for m in fresh:
        key = (m.get("channel_id") or "", m.get("ts") or "")
        if key[1]:
            merged[key] = m
    return sorted(
        merged.values(),
        key=lambda m: m.get("ts") or "",
        reverse=True,
    )


# ---------- CLI ----------


def _parse_args(argv: list[str]) -> dict[str, Any]:
    parser = argparse.ArgumentParser(
        prog="pull_slack.py",
        description="Incremental pull of Slack messages into integrations-cache.",
    )
    parser.add_argument(
        "--args",
        default="{}",
        help='JSON object: {"channel_ids":[...],"force":false,"messages_per_channel_limit":200}',
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
    return now.strftime("%Y-%m-%dT%H-%M-%SZ")


def _watermark_to_oldest(ts: str) -> str:
    """Subtract a buffer from a Slack ts to guard against clock skew.
    Slack ts is seconds since epoch as a string like '1704902400.000123'."""
    try:
        seconds = float(ts) - WATERMARK_BUFFER_SECONDS
    except ValueError:
        return ts
    return f"{seconds:.6f}"


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
    channel_filter = opts.get("channel_ids") or None
    msg_limit = int(opts.get("messages_per_channel_limit", DEFAULT_MESSAGES_PER_CHANNEL))

    token = os.environ.get("SLACK_BOT_TOKEN", "").strip()
    if not token:
        print(json.dumps({"status": "error", "message": "SLACK_BOT_TOKEN env var not set"}))
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
            "message_count": 0,
            "new_since_last": 0,
            "channels_polled": 0,
            "message": (
                f"newest cache {newest.name} is within TTL ({ttl_minutes}m); "
                f'pass {{"force": true}} to override'
            ),
        }
        print(json.dumps(result))
        return 0

    watermarks = _watermark_per_channel(newest)

    try:
        channels = _list_channels(token, channel_filter)
        users = _list_users(token)
    except PullCrash as e:
        print(json.dumps({"status": "error", "message": str(e)}))
        return 1

    # Only poll channels the bot is actually a member of. `conversations.history`
    # will fail on channels the bot isn't in.
    pollable = [c for c in channels if c.get("is_member")]

    fresh_messages: list[dict[str, Any]] = []
    try:
        for channel in pollable:
            cid = channel.get("id")
            if not cid:
                continue
            oldest = None
            wm = watermarks.get(cid)
            if wm:
                oldest = _watermark_to_oldest(wm)
            raw_messages = _fetch_channel_messages(token, cid, oldest, msg_limit)
            for raw in raw_messages:
                fresh_messages.append(_flatten_message(raw, channel, users))
    except PullCrash as e:
        print(json.dumps({"status": "error", "message": str(e)}))
        return 1

    prior_messages: list[dict[str, Any]] = []
    if newest is not None:
        prior_messages = _load_cache_file(newest).get("messages") or []

    prior_keys = {(m.get("channel_id"), m.get("ts")) for m in prior_messages}
    new_since_last = sum(
        1 for m in fresh_messages if (m.get("channel_id"), m.get("ts")) not in prior_keys
    )

    merged = _merge_messages(prior_messages, fresh_messages)

    out_name = _file_stamp(now) + ".json"
    out_path = cache_dir / out_name
    payload = {
        "pulled_at": _iso_now(now),
        "channels": {c["id"]: c for c in channels if c.get("id")},
        "users": users,
        "message_count": len(merged),
        "messages": merged,
    }
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    rel_out = f"integrations-cache/slack/{out_name}"
    print(json.dumps({
        "status": "pulled",
        "file_written": rel_out,
        "message_count": len(merged),
        "new_since_last": new_since_last,
        "channels_polled": len(pollable),
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
