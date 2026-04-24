"""Tests for scripts/zip_data.py.

Builds a synthetic data repo in tmp_path, runs zip_data as a subprocess,
and asserts on the resulting archive's contents.

Covers:
  - Default excludes: logs/, integrations-cache/, .backups/, .DS_Store, .env*.
  - Explicit inclusion of .git/ (full-history backup).
  - Default output path under $CTO_OS_DATA/.backups/.
  - Custom dest_path (absolute).
  - extra_excludes honored.
  - Bad args rejected with exit 1.
  - Missing CTO_OS_DATA rejected with exit 1.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "scripts" / "zip_data.py"


def _run(args: dict, *, data_root: Path, env_extra: dict | None = None):
    env = {**os.environ, "CTO_OS_DATA": str(data_root)}
    if env_extra:
        env.update(env_extra)
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--args", json.dumps(args)],
        capture_output=True,
        text=True,
        env=env,
    )


def _ok(args: dict, *, data_root: Path) -> dict:
    result = _run(args, data_root=data_root)
    assert result.returncode == 0, (
        f"zip_data.py exited {result.returncode}\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )
    return json.loads(result.stdout)


def _build_fixture(root: Path) -> None:
    """Create a synthetic data repo with every kind of path the script cares about."""
    # Regular module state — must be included.
    (root / "modules" / "personal-os" / "state").mkdir(parents=True)
    (root / "modules" / "personal-os" / "state" / "altitude.md").write_text(
        "---\ntype: altitude\nslug: current\n---\nvp\n", encoding="utf-8"
    )
    (root / "modules" / "personal-os" / "_module.md").write_text(
        "---\ntype: _module\nslug: personal-os\n---\n", encoding="utf-8"
    )

    # .git/ — MUST be included (point of a backup).
    (root / ".git").mkdir()
    (root / ".git" / "HEAD").write_text("ref: refs/heads/main\n", encoding="utf-8")
    (root / ".git" / "objects").mkdir()
    (root / ".git" / "objects" / "pack-dummy").write_text("binary-ish\n", encoding="utf-8")

    # logs/ — excluded.
    (root / "logs").mkdir()
    (root / "logs" / "mcp.log").write_text("log line\n", encoding="utf-8")

    # integrations-cache/ — excluded.
    (root / "integrations-cache" / "slack").mkdir(parents=True)
    (root / "integrations-cache" / "slack" / "2026-04-20.json").write_text(
        '{"x": 1}', encoding="utf-8"
    )

    # .backups/ — excluded (self-reference).
    (root / ".backups").mkdir()
    (root / ".backups" / "prev.zip").write_bytes(b"old zip")

    # .DS_Store cruft — excluded.
    (root / ".DS_Store").write_bytes(b"\x00")
    (root / "modules" / ".DS_Store").write_bytes(b"\x00")

    # .env + .env.local secrets — excluded.
    (root / ".env").write_text("SECRET=1\n", encoding="utf-8")
    (root / ".env.local").write_text("LOCAL_SECRET=2\n", encoding="utf-8")


def _archived_names(zip_path: Path) -> list[str]:
    with zipfile.ZipFile(zip_path) as zf:
        return sorted(zf.namelist())


# ---------- happy path ----------


def test_default_run_produces_zip_under_backups(tmp_path: Path):
    _build_fixture(tmp_path)
    report = _ok({}, data_root=tmp_path)

    zip_path = Path(report["zip_path"])
    assert zip_path.is_file(), f"zip not created at {zip_path}"
    assert zip_path.parent == tmp_path / ".backups"
    assert zip_path.name.startswith("cto-os-data-")
    assert zip_path.suffix == ".zip"

    assert report["size_bytes"] > 0
    assert report["file_count"] > 0
    assert report["excluded_count"] > 0
    assert "timestamp" in report


def test_git_dir_is_included(tmp_path: Path):
    _build_fixture(tmp_path)
    report = _ok({}, data_root=tmp_path)

    names = _archived_names(Path(report["zip_path"]))
    # Archive paths are prefixed with the data-root directory name (tmp_path.name).
    assert any(n.endswith("/.git/HEAD") for n in names), (
        f".git/HEAD missing from archive.\nEntries: {names}"
    )
    assert any(n.endswith("/.git/objects/pack-dummy") for n in names)


def test_default_excludes_are_applied(tmp_path: Path):
    _build_fixture(tmp_path)
    report = _ok({}, data_root=tmp_path)

    names = _archived_names(Path(report["zip_path"]))
    flat = "\n".join(names)

    # Directories we should never ship.
    assert "/logs/" not in flat, f"logs/ leaked into archive:\n{flat}"
    assert "/integrations-cache/" not in flat, (
        f"integrations-cache/ leaked into archive:\n{flat}"
    )
    assert "/.backups/" not in flat, f".backups/ leaked (self-reference):\n{flat}"

    # Files we should never ship.
    assert not any(n.endswith("/.DS_Store") for n in names), (
        f".DS_Store leaked:\n{flat}"
    )
    assert not any(n.endswith("/.env") for n in names), f".env leaked:\n{flat}"
    assert not any(n.endswith("/.env.local") for n in names), (
        f".env.local leaked:\n{flat}"
    )


def test_regular_state_is_included(tmp_path: Path):
    _build_fixture(tmp_path)
    report = _ok({}, data_root=tmp_path)

    names = _archived_names(Path(report["zip_path"]))
    assert any(n.endswith("/modules/personal-os/state/altitude.md") for n in names)
    assert any(n.endswith("/modules/personal-os/_module.md") for n in names)


# ---------- dest_path override ----------


def test_custom_dest_path(tmp_path: Path):
    _build_fixture(tmp_path)
    dest = tmp_path / "custom" / "out.zip"
    report = _ok({"dest_path": str(dest)}, data_root=tmp_path)
    assert Path(report["zip_path"]) == dest
    assert dest.is_file()


def test_dest_path_must_be_absolute(tmp_path: Path):
    _build_fixture(tmp_path)
    result = _run({"dest_path": "relative/out.zip"}, data_root=tmp_path)
    assert result.returncode == 1
    assert "absolute" in result.stderr.lower()


# ---------- extra_excludes ----------


def test_extra_excludes_honored(tmp_path: Path):
    _build_fixture(tmp_path)
    # Add a directory we'll ask the script to exclude.
    (tmp_path / "scratch").mkdir()
    (tmp_path / "scratch" / "note.md").write_text("skip me\n", encoding="utf-8")

    report = _ok({"extra_excludes": ["scratch"]}, data_root=tmp_path)
    names = _archived_names(Path(report["zip_path"]))
    assert not any("scratch" in n for n in names)

    # Sanity check: without the exclude, scratch would appear.
    report2 = _ok({}, data_root=tmp_path)
    names2 = _archived_names(Path(report2["zip_path"]))
    assert any("scratch/note.md" in n for n in names2)


def test_extra_excludes_type_validation(tmp_path: Path):
    _build_fixture(tmp_path)
    result = _run({"extra_excludes": "scratch"}, data_root=tmp_path)  # not a list
    assert result.returncode == 1
    assert "list" in result.stderr.lower()


# ---------- error paths ----------


def test_missing_cto_os_data_crashes(tmp_path: Path):
    _build_fixture(tmp_path)
    env = {k: v for k, v in os.environ.items() if k != "CTO_OS_DATA"}
    env["CTO_OS_DATA"] = ""
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--args", "{}"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 1
    assert "CTO_OS_DATA" in result.stderr


def test_bad_args_json_crashes(tmp_path: Path):
    _build_fixture(tmp_path)
    env = {**os.environ, "CTO_OS_DATA": str(tmp_path)}
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--args", "{not json"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 1
    assert "valid JSON" in result.stderr


def test_args_must_be_object(tmp_path: Path):
    _build_fixture(tmp_path)
    result = _run(args=[], data_root=tmp_path)  # list, not object
    assert result.returncode == 1
    assert "JSON object" in result.stderr
