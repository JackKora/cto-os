"""Tests for small helpers in server.py."""
from datetime import datetime, timezone

import server


def test_iso_z_known_epoch():
    # 2026-01-01T00:00:00 UTC
    result = server._iso_z(1767225600.0)
    assert result == "2026-01-01T00:00:00Z"


def test_iso_z_roundtrip_seconds():
    now = datetime.now(tz=timezone.utc)
    iso = server._iso_z(now.timestamp())
    parsed = datetime.strptime(iso, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    # Truncates to whole seconds
    assert abs((parsed - now).total_seconds()) < 1.0


def test_iso_z_format_length():
    # Fixed-length format: YYYY-MM-DDTHH:MM:SSZ == 20 chars
    iso = server._iso_z(datetime.now(tz=timezone.utc).timestamp())
    assert len(iso) == 20
    assert iso[-1] == "Z"
