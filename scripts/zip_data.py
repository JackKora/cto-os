#!/usr/bin/env python3
"""
zip_data.py — zip the CTO OS data repo for offsite backup.

Produces a single zip archive of `$CTO_OS_DATA` at a timestamped path
inside `$CTO_OS_DATA/.backups/` by default. The `.git/` directory is
*included* (the whole point of a backup is preserving history); only
regenerable / ephemeral / secret paths are excluded.

Default excludes (relative to $CTO_OS_DATA):
  - logs/                 (regenerable; MCP server writes here)
  - integrations-cache/   (regenerable; pull_* scripts re-populate)
  - .backups/             (self-reference; would compound on each run)
  - .DS_Store             (macOS cruft)
  - .env, .env.*          (secrets; must never leave local disk)

Contract:
  - Accepts JSON on stdin via `--args '{...}'`.
  - Emits JSON on stdout.
  - Reads `CTO_OS_DATA` from the environment.
  - Exit 0 on success; 1 on crash (bad args, missing env, IO error).

Args (all optional):
  {
    "dest_path":  "/abs/path/to/output.zip",   // override default location
    "extra_excludes": ["node_modules", "tmp"]  // additional path prefixes to skip
  }

Output:
  {
    "zip_path":       "/abs/path/to/zip",
    "size_bytes":     <int>,
    "file_count":     <int>,
    "excluded_count": <int>,
    "timestamp":      "YYYY-MM-DDTHH-MM-SS"    // filename-safe UTC
  }

Usage:
    uv run python scripts/zip_data.py --args '{}'
    uv run python scripts/zip_data.py --args '{"extra_excludes": ["tmp"]}'
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# Excludes that are always applied. Users can add via `extra_excludes`.
DEFAULT_EXCLUDE_DIRS: frozenset[str] = frozenset({
    "logs",
    "integrations-cache",
    ".backups",
})

DEFAULT_EXCLUDE_FILE_NAMES: frozenset[str] = frozenset({
    ".DS_Store",
})

# Prefixes for file-name-level excludes (e.g., ".env", ".env.local").
DEFAULT_EXCLUDE_FILE_PREFIXES: tuple[str, ...] = (".env",)


class ZipDataCrash(Exception):
    """Fatal error — surfaces to stderr with exit 1."""


def _resolve_data_root() -> Path:
    value = os.environ.get("CTO_OS_DATA", "").strip()
    if not value:
        raise ZipDataCrash("CTO_OS_DATA env var is missing or empty")
    path = Path(value).expanduser().resolve()
    if not path.is_dir():
        raise ZipDataCrash(f"CTO_OS_DATA does not point to a directory: {path}")
    return path


def _utc_timestamp() -> str:
    """Filename-safe UTC timestamp: YYYY-MM-DDTHH-MM-SS."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%S")


def _should_skip(
    rel: Path,
    extra_exclude_dirs: frozenset[str],
) -> bool:
    """Return True if the relative path should be excluded from the zip."""
    # Any top-level directory match (whole path prefix).
    top = rel.parts[0] if rel.parts else ""
    if top in DEFAULT_EXCLUDE_DIRS or top in extra_exclude_dirs:
        return True

    # File-name-level excludes — check the leaf only.
    name = rel.name
    if name in DEFAULT_EXCLUDE_FILE_NAMES:
        return True
    for prefix in DEFAULT_EXCLUDE_FILE_PREFIXES:
        if name == prefix or name.startswith(prefix + "."):
            return True

    return False


def _build_zip(
    data_root: Path,
    dest: Path,
    extra_exclude_dirs: frozenset[str],
) -> tuple[int, int]:
    """Write the archive. Returns (file_count, excluded_count)."""
    dest.parent.mkdir(parents=True, exist_ok=True)

    file_count = 0
    excluded_count = 0

    with zipfile.ZipFile(dest, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(data_root):
            root_path = Path(root)
            rel_root = root_path.relative_to(data_root)

            # Prune directories in-place so os.walk doesn't descend.
            pruned: list[str] = []
            for d in list(dirs):
                rel_child = rel_root / d
                if _should_skip(rel_child, extra_exclude_dirs):
                    pruned.append(d)
            if pruned:
                excluded_count += len(pruned)
                dirs[:] = [d for d in dirs if d not in pruned]

            for fname in files:
                rel_file = rel_root / fname
                if _should_skip(rel_file, extra_exclude_dirs):
                    excluded_count += 1
                    continue
                abs_file = root_path / fname
                # Write with the archive path = relative to data_root,
                # under a top-level directory named after the repo. Zip readers
                # will see `cto-os-data/...` when they extract.
                arcname = Path(data_root.name) / rel_file
                zf.write(abs_file, arcname=str(arcname))
                file_count += 1

    return file_count, excluded_count


def _parse_args(argv: list[str]) -> dict[str, Any]:
    parser = argparse.ArgumentParser(
        prog="zip_data.py",
        description="Zip CTO_OS_DATA for offsite backup.",
    )
    parser.add_argument(
        "--args",
        required=True,
        help="Argument spec as a JSON object.",
    )
    parsed = parser.parse_args(argv)
    try:
        args = json.loads(parsed.args)
    except json.JSONDecodeError as e:
        raise ZipDataCrash(f"--args is not valid JSON: {e}")
    if not isinstance(args, dict):
        raise ZipDataCrash("--args must be a JSON object")
    return args


def _resolve_dest(data_root: Path, dest_path: str | None, timestamp: str) -> Path:
    if dest_path:
        p = Path(dest_path).expanduser()
        if not p.is_absolute():
            raise ZipDataCrash(f"dest_path must be absolute: {dest_path}")
        return p
    return data_root / ".backups" / f"cto-os-data-{timestamp}.zip"


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    try:
        args = _parse_args(argv)
        data_root = _resolve_data_root()
    except ZipDataCrash as e:
        print(str(e), file=sys.stderr)
        return 1

    extra_excludes = args.get("extra_excludes", [])
    if not isinstance(extra_excludes, list) or not all(
        isinstance(x, str) for x in extra_excludes
    ):
        print("extra_excludes must be a list of strings", file=sys.stderr)
        return 1

    dest_path_arg = args.get("dest_path")
    if dest_path_arg is not None and not isinstance(dest_path_arg, str):
        print("dest_path must be a string if provided", file=sys.stderr)
        return 1

    timestamp = _utc_timestamp()

    try:
        dest = _resolve_dest(data_root, dest_path_arg, timestamp)
        file_count, excluded_count = _build_zip(
            data_root, dest, frozenset(extra_excludes)
        )
        size_bytes = dest.stat().st_size
    except ZipDataCrash as e:
        print(str(e), file=sys.stderr)
        return 1
    except OSError as e:
        print(f"I/O error: {e}", file=sys.stderr)
        return 1

    result = {
        "zip_path": str(dest),
        "size_bytes": size_bytes,
        "file_count": file_count,
        "excluded_count": excluded_count,
        "timestamp": timestamp,
    }
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
