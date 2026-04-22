#!/usr/bin/env python3
"""
CTO OS — MCP server.

Chat-facing MCP server that bridges Claude Desktop to the cto-os-data
filesystem and the deterministic scripts in cto-os/scripts/.

Spec (source of truth): docs/MCP_TOOLS.md.
"""

from __future__ import annotations

import json
import logging
import logging.handlers
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP


# ---------- Constants ----------

SCRIPT_TIMEOUT_SECONDS = 10

# Scripts callable via run_script. Adding to this set is a deliberate code change.
RUN_SCRIPT_WHITELIST: frozenset[str] = frozenset({
    "roll_up",
    "validate_deps",
    "rename_module",
})

# Scripts with their own first-class tool; always refused by run_script.
RUN_SCRIPT_RESERVED: frozenset[str] = frozenset({
    "scan",
})

# Top-level subtrees of $CTO_OS_DATA that write_file / append_to_file refuse to touch.
# These are machine-managed surfaces — git, logs, integrations cache — and writes
# through the MCP tools would cause confusing breakage.
WRITE_FORBIDDEN_PREFIXES: frozenset[str] = frozenset({
    ".git",
    "logs",
    "integrations-cache",
})


# ---------- Errors ----------

class McpError(Exception):
    """Base error. The class-level `code` is prepended to the message for telemetry."""

    code: str = "McpError"

    def __init__(self, message: str) -> None:
        super().__init__(f"{self.code}: {message}")


class DataRootNotSet(McpError):         code = "DataRootNotSet"
class InvalidPath(McpError):             code = "InvalidPath"
class PathOutsideRoot(McpError):         code = "PathOutsideRoot"
class ForbiddenPath(McpError):           code = "ForbiddenPath"
class PathNotFound(McpError):            code = "PathNotFound"
class PathIsDirectory(McpError):         code = "PathIsDirectory"
class PathIsFile(McpError):              code = "PathIsFile"
class BinaryFileError(McpError):         code = "BinaryFileError"
class PermissionDenied(McpError):        code = "PermissionDenied"
class ScriptNotInWhitelist(McpError):    code = "ScriptNotInWhitelist"
class ScriptNotFound(McpError):          code = "ScriptNotFound"
class ScriptNotImplemented(McpError):    code = "ScriptNotImplemented"
class ScriptTimeout(McpError):           code = "ScriptTimeout"
class ScriptFailed(McpError):            code = "ScriptFailed"


# ---------- Loggers (module-level; handler attached in _configure_logging) ----------

LOG_SERVER = logging.getLogger("server")
LOG_READ_FILE = logging.getLogger("read_file")
LOG_WRITE_FILE = logging.getLogger("write_file")
LOG_APPEND_TO_FILE = logging.getLogger("append_to_file")
LOG_LIST_DIRECTORY = logging.getLogger("list_directory")
LOG_SCAN = logging.getLogger("scan")
LOG_RUN_SCRIPT = logging.getLogger("run_script")

# ---------- Globals, set in main() ----------

DATA_ROOT: Path | None = None


# ---------- Startup ----------

def _resolve_data_root() -> Path:
    value = os.environ.get("CTO_OS_DATA", "").strip()
    if not value:
        raise DataRootNotSet("CTO_OS_DATA env var is missing or empty")
    root = Path(os.path.expanduser(value)).resolve()
    if not root.is_dir():
        raise DataRootNotSet(f"{root} does not exist or is not a directory")
    return root


def _configure_logging(data_root: Path) -> None:
    """Configure file logging with daily rotation. Falls back to stderr if log dir creation fails."""
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-7s | %(name)-14s | %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%SZ",
    )

    root_logger = logging.getLogger()
    level_name = os.environ.get("CTO_OS_MCP_LOG_LEVEL", "INFO").upper()
    root_logger.setLevel(getattr(logging, level_name, logging.INFO))

    log_dir = data_root / "logs"
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
        handler: logging.Handler = logging.handlers.TimedRotatingFileHandler(
            filename=str(log_dir / "mcp.log"),
            when="midnight",
            backupCount=1,
            encoding="utf-8",
            utc=True,
        )
    except OSError as e:
        # Last-ditch fallback — log dir unavailable. Emit one line to stderr and carry on
        # with stderr logging for the session.
        print(f"server | could not create {log_dir}: {e}; logging to stderr", file=sys.stderr)
        handler = logging.StreamHandler(sys.stderr)

    handler.setFormatter(formatter)
    root_logger.addHandler(handler)


# ---------- Path handling ----------

def _resolve_path(user_path: str) -> Path:
    """Validate and resolve a caller-provided path against DATA_ROOT. Raises on any escape."""
    if not user_path:
        raise InvalidPath("path is empty")
    if os.path.isabs(user_path):
        raise InvalidPath(f"path must be relative to CTO_OS_DATA: got {user_path!r}")
    if ".." in Path(user_path).parts:
        raise InvalidPath(f"path may not contain '..': {user_path!r}")

    candidate = (DATA_ROOT / user_path).resolve()
    try:
        candidate.relative_to(DATA_ROOT)
    except ValueError:
        raise PathOutsideRoot(f"{candidate} is not under {DATA_ROOT}")
    return candidate


def _check_write_allowed(resolved: Path) -> None:
    """Reject writes into top-level subtrees reserved for machine-managed state."""
    try:
        rel = resolved.relative_to(DATA_ROOT)
    except ValueError:
        # Should be unreachable — _resolve_path caught this. Defensive anyway.
        raise PathOutsideRoot(f"{resolved} is not under {DATA_ROOT}")

    if not rel.parts:
        raise ForbiddenPath("cannot write to the CTO_OS_DATA root itself")

    top = rel.parts[0]
    if top in WRITE_FORBIDDEN_PREFIXES:
        raise ForbiddenPath(
            f"writes to {top}/ are not allowed (machine-managed subtree); "
            f"got {rel}"
        )


# ---------- Helpers ----------

def _iso_z(epoch: float) -> str:
    """ISO-8601 UTC with 'Z' suffix, from a POSIX epoch timestamp."""
    return datetime.fromtimestamp(epoch, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


SCRIPT_DIR: Path = Path(__file__).resolve().parent.parent / "scripts"


def _invoke_script(name: str, args: dict[str, Any], log: logging.Logger) -> dict[str, Any]:
    """Run `scripts/{name}.py --args '<json>'`. Returns {exit_code, stdout, stderr}."""
    script_path = SCRIPT_DIR / f"{name}.py"
    if not script_path.is_file():
        raise ScriptNotFound(f"scripts/{name}.py does not exist")
    if script_path.stat().st_size == 0:
        raise ScriptNotImplemented(f"scripts/{name}.py is empty (not yet implemented)")

    try:
        completed = subprocess.run(
            [sys.executable, str(script_path), "--args", json.dumps(args)],
            capture_output=True,
            timeout=SCRIPT_TIMEOUT_SECONDS,
            env=os.environ,
        )
    except subprocess.TimeoutExpired:
        log.error(f"ScriptTimeout: {name}.py exceeded {SCRIPT_TIMEOUT_SECONDS}s")
        raise ScriptTimeout(f"{name}.py exceeded {SCRIPT_TIMEOUT_SECONDS}s")

    return {
        "exit_code": completed.returncode,
        "stdout": completed.stdout.decode("utf-8", errors="replace"),
        "stderr": completed.stderr.decode("utf-8", errors="replace"),
    }


# ---------- Server ----------

mcp = FastMCP("cto-os")


@mcp.tool()
def read_file(path: str) -> str:
    """Read a single file's UTF-8 text content. Path is relative to CTO_OS_DATA."""
    try:
        resolved = _resolve_path(path)
    except McpError as e:
        LOG_READ_FILE.error(str(e))
        raise

    if not resolved.exists():
        LOG_READ_FILE.error(f"PathNotFound: {path}")
        raise PathNotFound(f"{path} does not exist")
    if resolved.is_dir():
        LOG_READ_FILE.error(f"PathIsDirectory: {path}")
        raise PathIsDirectory(f"{path} is a directory")

    try:
        content = resolved.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        LOG_READ_FILE.error(f"BinaryFileError: {path}")
        raise BinaryFileError(f"{path} is not valid UTF-8")
    except PermissionError as e:
        LOG_READ_FILE.error(f"PermissionDenied: {path} ({e})")
        raise PermissionDenied(f"{path} ({e})")

    LOG_READ_FILE.info(f"read {len(content)} chars from {path}")
    return content


@mcp.tool()
def write_file(path: str, content: str) -> dict[str, Any]:
    """Create or overwrite a file with UTF-8 text content. Auto-creates parent dirs."""
    try:
        resolved = _resolve_path(path)
        _check_write_allowed(resolved)
    except McpError as e:
        LOG_WRITE_FILE.error(str(e))
        raise

    if resolved.is_dir():
        LOG_WRITE_FILE.error(f"PathIsDirectory: {path}")
        raise PathIsDirectory(f"{path} is a directory")

    created = not resolved.exists()
    try:
        resolved.parent.mkdir(parents=True, exist_ok=True)
        resolved.write_text(content, encoding="utf-8")
    except PermissionError as e:
        LOG_WRITE_FILE.error(f"PermissionDenied: {path} ({e})")
        raise PermissionDenied(f"{path} ({e})")

    LOG_WRITE_FILE.info(f"wrote {len(content)} chars to {path} (created={created})")
    return {"chars_written": len(content), "created": created}


@mcp.tool()
def append_to_file(path: str, content: str, allow_create: bool = True) -> dict[str, Any]:
    """Append UTF-8 text to a file. No auto-newline — caller controls separators.

    When ``allow_create`` is True (default), a missing file is created along with any missing
    parent directories. When False, a missing file raises ``PathNotFound`` — useful when the
    caller wants to guarantee it's extending an existing artifact rather than silently
    creating one on typo'd path.
    """
    try:
        resolved = _resolve_path(path)
        _check_write_allowed(resolved)
    except McpError as e:
        LOG_APPEND_TO_FILE.error(str(e))
        raise

    if resolved.is_dir():
        LOG_APPEND_TO_FILE.error(f"PathIsDirectory: {path}")
        raise PathIsDirectory(f"{path} is a directory")

    exists = resolved.exists()
    if not exists and not allow_create:
        LOG_APPEND_TO_FILE.error(f"PathNotFound: {path} (allow_create=False)")
        raise PathNotFound(f"{path} does not exist and allow_create is False")

    created = not exists
    try:
        if created:
            resolved.parent.mkdir(parents=True, exist_ok=True)
        with resolved.open("a", encoding="utf-8") as f:
            f.write(content)
    except PermissionError as e:
        LOG_APPEND_TO_FILE.error(f"PermissionDenied: {path} ({e})")
        raise PermissionDenied(f"{path} ({e})")

    LOG_APPEND_TO_FILE.info(f"appended {len(content)} chars to {path} (created={created})")
    return {"chars_written": len(content), "created": created}


@mcp.tool()
def list_directory(path: str, recursive: bool = False) -> list[dict[str, Any]]:
    """Enumerate entries in a directory. Use '.' for the CTO_OS_DATA root."""
    try:
        resolved = _resolve_path(path)
    except McpError as e:
        LOG_LIST_DIRECTORY.error(str(e))
        raise

    if not resolved.exists():
        LOG_LIST_DIRECTORY.error(f"PathNotFound: {path}")
        raise PathNotFound(f"{path} does not exist")
    if resolved.is_file():
        LOG_LIST_DIRECTORY.error(f"PathIsFile: {path}")
        raise PathIsFile(f"{path} is a file")

    entries: list[dict[str, Any]] = []
    iterator = resolved.rglob("*") if recursive else resolved.iterdir()

    for child in iterator:
        # Drop entries whose resolved target escapes the root (e.g., symlinks).
        try:
            child_resolved = child.resolve()
            child_resolved.relative_to(DATA_ROOT)
        except ValueError:
            # Symlink target escapes the root — expected, not an error. Dropped from result.
            LOG_LIST_DIRECTORY.info(f"omitting escaping symlink: {child}")
            continue
        except OSError as e:
            LOG_LIST_DIRECTORY.warning(f"unreadable entry dropped: {child} ({e})")
            continue

        try:
            stat = child.stat()
        except OSError as e:
            LOG_LIST_DIRECTORY.warning(f"stat failed on {child}: {e}")
            continue

        rel_name = str(child.relative_to(resolved))
        mtime = _iso_z(stat.st_mtime)

        if child.is_dir():
            entries.append({"name": rel_name, "type": "directory", "mtime": mtime})
        elif child.is_file():
            entries.append({
                "name": rel_name,
                "type": "file",
                "size": stat.st_size,
                "mtime": mtime,
            })
        # Other types (sockets, FIFOs, devices) are silently skipped.

    entries.sort(key=lambda e: e["name"])
    LOG_LIST_DIRECTORY.info(f"listed {len(entries)} entries in {path} (recursive={recursive})")
    return entries


@mcp.tool()
def scan(query_spec: dict[str, Any]) -> dict[str, Any]:
    """Frontmatter scan + filter across CTO_OS_DATA. Thin proxy to scripts/scan.py."""
    result = _invoke_script("scan", query_spec, LOG_SCAN)
    LOG_SCAN.info(f"scan invoked; exit={result['exit_code']}")

    if result["exit_code"] != 0:
        # scan.py is expected to emit structured JSON even on query errors; a non-zero exit
        # signals a genuine script failure, not just a bad query.
        raise ScriptFailed(f"scan.py exited {result['exit_code']}: {result['stderr'][:200]}")

    try:
        return json.loads(result["stdout"])
    except json.JSONDecodeError as e:
        raise ScriptFailed(f"scan.py produced invalid JSON: {e}")


@mcp.tool()
def run_script(name: str, args: dict[str, Any]) -> dict[str, Any]:
    """Invoke a whitelisted script in scripts/. Does NOT raise on non-zero exit."""
    if name in RUN_SCRIPT_RESERVED:
        LOG_RUN_SCRIPT.error(f"ScriptNotInWhitelist: {name!r} is reserved")
        raise ScriptNotInWhitelist(f"{name!r} is reserved; use the scan tool directly")

    if name not in RUN_SCRIPT_WHITELIST:
        LOG_RUN_SCRIPT.error(f"ScriptNotInWhitelist: {name!r} not in whitelist")
        raise ScriptNotInWhitelist(f"{name!r} not in whitelist")

    result = _invoke_script(name, args, LOG_RUN_SCRIPT)
    LOG_RUN_SCRIPT.info(f"run_script {name}; exit={result['exit_code']}")
    return result


# ---------- Main ----------

def main() -> None:
    global DATA_ROOT

    try:
        DATA_ROOT = _resolve_data_root()
    except DataRootNotSet as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)

    _configure_logging(DATA_ROOT)

    LOG_SERVER.info(f"server start; CTO_OS_DATA={DATA_ROOT}")
    try:
        mcp.run()
    except Exception as e:
        LOG_SERVER.exception(f"server crashed: {e}")
        raise
    finally:
        LOG_SERVER.info("server stop")


if __name__ == "__main__":
    main()
