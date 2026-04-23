#!/usr/bin/env python3
"""
scan.py — the workhorse.

Walks $CTO_OS_DATA looking for `.md` files with YAML frontmatter, applies a
caller-supplied query (type filter, where predicate, module scope, field
projection, optional body inclusion), and returns a compact JSON result.

Contract (see docs/SKILL_REPO.md → "Context loading: scan, don't cache"
and docs/MCP_TOOLS.md → `scan(query_spec)`):

- Input: `--args '<json>'` where <json> is a query spec object.
- Output: JSON on stdout.
- Exit code: 0 for every structured result (including query errors carried in
  an `error` field). Non-zero only for crashes (bad args, missing env, I/O).

Query spec:
  {
    "type":         ["team", "1on1"],           // optional; whitelist of frontmatter `type` values
    "module":       "managing-down",             // optional; restrict to one module's subtree
    "where":        {"status": "struggling",     // optional; predicate on frontmatter fields
                     "date_gte": "2026-01-01",   //   suffix operators: _gte, _lte, _gt, _lt
                     "tag": "urgent"},           //   exact match or list membership (see below)
    "fields":       ["slug", "lead"],           // optional; project frontmatter to these keys
    "include_body": false,                       // optional; default false
    "include_inactive": false,                   // optional; default false — excludes modules with active:false
    "include_high_sensitivity": false            // optional; default false — excludes sensitivity:high
  }

Where semantics:
  - Exact match: `{"status": "struggling"}` matches files whose frontmatter `status` equals "struggling".
  - List as value: `{"status": ["x", "y"]}` matches files whose frontmatter `status` is either x or y.
  - Frontmatter field is a list: `{"tag": "urgent"}` matches if "urgent" is in file's `tag` list.
  - Suffix operators on date or number: `_gte`, `_lte`, `_gt`, `_lt`.
    Example: `{"updated_gte": "2026-01-01"}`.

Response shapes (see docs/SKILL_REPO.md for canonical spec):
  Baseline:
    {"matches": [{"path": "...", "frontmatter": {...}}]}
  With bodies, under cap:
    {"matches": [{"path": "...", "frontmatter": {...}, "body": "...", "body_truncated": false}]}
  Match-cap hit (include_body=true but > MAX_INLINE_MATCHES matches):
    {"truncated_bodies": true, "matches": [{"path": "...", "frontmatter": {...}}]}
  Query error:
    {"error": "message", "query": {...}}

Guardrails (enforced here, not in skill prose):
  MAX_INLINE_MATCHES = 5
  MAX_BODY_BYTES     = 4096
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


# ---------- Guardrails (per docs/SKILL_REPO.md) ----------

MAX_INLINE_MATCHES = 5
MAX_BODY_BYTES = 4096
BODY_TRUNCATION_MARKER = "\n... [truncated, {n} more bytes — use read_file for full content]"


# ---------- Paths excluded from the walk ----------

# Top-level subtrees of $CTO_OS_DATA that scan never reads. Logs are the
# server's own surface; integrations-cache is regenerable noise scan doesn't
# need to parse (users query cached state via other paths); .git is git's.
EXCLUDED_TOP_LEVEL_DIRS = {".git", "logs", "integrations-cache"}


# ---------- Errors ----------


class ScanError(Exception):
    """Surfaced as a structured error in the JSON response with exit 0."""


class ScanCrash(Exception):
    """Surfaced as a crash — exit 1."""


# ---------- Data root resolution ----------


def _resolve_data_root() -> Path:
    value = os.environ.get("CTO_OS_DATA", "").strip()
    if not value:
        raise ScanCrash("CTO_OS_DATA env var is missing or empty")
    root = Path(os.path.expanduser(value)).resolve()
    if not root.is_dir():
        raise ScanCrash(f"{root} does not exist or is not a directory")
    return root


# ---------- Frontmatter parsing ----------

_FRONTMATTER_PATTERN = re.compile(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", re.DOTALL)


def _parse_frontmatter(raw: str) -> tuple[dict[str, Any] | None, str]:
    """Split a .md file's raw text into (frontmatter_dict, body_text).
    Returns (None, raw) if no frontmatter present."""
    match = _FRONTMATTER_PATTERN.match(raw)
    if not match:
        return None, raw
    yaml_text = match.group(1)
    body = match.group(2)
    try:
        frontmatter = yaml.safe_load(yaml_text) or {}
    except yaml.YAMLError:
        return None, raw
    if not isinstance(frontmatter, dict):
        return None, raw
    return frontmatter, body


# ---------- Walking ----------


@dataclass
class _ModuleMeta:
    slug: str
    active: bool
    sensitivity_high: bool


def _load_module_metas(data_root: Path) -> dict[str, _ModuleMeta]:
    """Read each modules/{slug}/_module.md for active + sensitivity flags."""
    metas: dict[str, _ModuleMeta] = {}
    modules_dir = data_root / "modules"
    if not modules_dir.is_dir():
        return metas
    for module_dir in sorted(modules_dir.iterdir()):
        if not module_dir.is_dir():
            continue
        slug = module_dir.name
        module_file = module_dir / "_module.md"
        if not module_file.is_file():
            metas[slug] = _ModuleMeta(slug=slug, active=True, sensitivity_high=False)
            continue
        try:
            raw = module_file.read_text(encoding="utf-8")
        except OSError:
            metas[slug] = _ModuleMeta(slug=slug, active=True, sensitivity_high=False)
            continue
        fm, _ = _parse_frontmatter(raw)
        active = bool((fm or {}).get("active", True))
        sensitivity_high = (fm or {}).get("sensitivity") == "high"
        metas[slug] = _ModuleMeta(slug=slug, active=active, sensitivity_high=sensitivity_high)
    return metas


def _iter_md_files(
    data_root: Path,
    module_filter: str | None,
) -> list[Path]:
    """Yield all .md files under data_root, skipping excluded top-level subtrees.
    If module_filter is set, restrict to that module's directory only."""
    paths: list[Path] = []

    if module_filter:
        start = data_root / "modules" / module_filter
        if not start.is_dir():
            return paths
        for candidate in start.rglob("*.md"):
            if candidate.is_file():
                paths.append(candidate)
        return paths

    for entry in sorted(data_root.iterdir()):
        if not entry.is_dir():
            continue
        if entry.name in EXCLUDED_TOP_LEVEL_DIRS:
            continue
        for candidate in entry.rglob("*.md"):
            if candidate.is_file():
                paths.append(candidate)
    return paths


def _module_slug_for_path(data_root: Path, path: Path) -> str | None:
    """Given an absolute path inside data_root/modules/{slug}/..., return the slug.
    Returns None if the file isn't under modules/."""
    try:
        rel = path.relative_to(data_root)
    except ValueError:
        return None
    parts = rel.parts
    if len(parts) < 2 or parts[0] != "modules":
        return None
    return parts[1]


# ---------- Query application ----------


_SUFFIX_OPERATORS = ("_gte", "_lte", "_gt", "_lt")


def _coerce_for_compare(value: Any) -> Any:
    """Coerce values that PyYAML might produce into comparable forms for the
    where predicate. Specifically: `datetime.date` / `datetime.datetime`
    become ISO-8601 strings (which compare lexically-correctly against caller
    strings like '2026-04-01'). Leaves other types alone."""
    import datetime as _dt

    if isinstance(value, (_dt.date, _dt.datetime)):
        return value.isoformat()
    return value


def _where_passes(frontmatter: dict[str, Any], where: dict[str, Any]) -> bool:
    """Apply the where predicate. Returns True if the file matches every clause."""
    for key, expected in where.items():
        if any(key.endswith(op) for op in _SUFFIX_OPERATORS):
            field, op = _split_suffix_op(key)
            actual = _coerce_for_compare(frontmatter.get(field))
            expected_c = _coerce_for_compare(expected)
            if actual is None:
                return False
            try:
                if op == "_gte" and not (actual >= expected_c):
                    return False
                if op == "_lte" and not (actual <= expected_c):
                    return False
                if op == "_gt" and not (actual > expected_c):
                    return False
                if op == "_lt" and not (actual < expected_c):
                    return False
            except TypeError:
                # Mismatched types (comparing string to int, etc.) — treat as no-match.
                return False
            continue

        actual = frontmatter.get(key)
        if isinstance(expected, list):
            # Caller passed a list of acceptable values.
            if isinstance(actual, list):
                if not any(v in actual for v in expected):
                    return False
            else:
                if _coerce_for_compare(actual) not in expected:
                    return False
        else:
            if isinstance(actual, list):
                if expected not in actual:
                    return False
            else:
                if _coerce_for_compare(actual) != expected:
                    return False
    return True


def _split_suffix_op(key: str) -> tuple[str, str]:
    """Split "updated_gte" → ("updated", "_gte")."""
    for op in _SUFFIX_OPERATORS:
        if key.endswith(op):
            return key[: -len(op)], op
    raise AssertionError(f"not a suffix-op key: {key!r}")


# ---------- Main flow ----------


def _validate_query(query: dict[str, Any]) -> None:
    """Raise ScanError with a structured error for any unknown / mistyped field."""
    allowed = {
        "type",
        "module",
        "where",
        "fields",
        "include_body",
        "include_inactive",
        "include_high_sensitivity",
    }
    unknown = set(query) - allowed
    if unknown:
        raise ScanError(f"unknown query fields: {sorted(unknown)}")

    for key, expected_type in (
        ("type", (list, type(None))),
        ("module", (str, type(None))),
        ("where", (dict, type(None))),
        ("fields", (list, type(None))),
        ("include_body", (bool, type(None))),
        ("include_inactive", (bool, type(None))),
        ("include_high_sensitivity", (bool, type(None))),
    ):
        if key in query and not isinstance(query[key], expected_type):
            raise ScanError(
                f"field {key!r} must be {expected_type}, got {type(query[key]).__name__}"
            )


def scan(data_root: Path, query: dict[str, Any]) -> dict[str, Any]:
    _validate_query(query)

    type_filter = query.get("type")
    module_filter = query.get("module")
    where_predicate = query.get("where") or {}
    fields = query.get("fields")
    include_body = bool(query.get("include_body", False))
    include_inactive = bool(query.get("include_inactive", False))
    include_high_sensitivity = bool(query.get("include_high_sensitivity", False))

    module_metas = _load_module_metas(data_root)
    md_files = _iter_md_files(data_root, module_filter)

    matches: list[dict[str, Any]] = []

    for path in md_files:
        slug = _module_slug_for_path(data_root, path)
        if slug is not None:
            meta = module_metas.get(slug)
            if meta is not None:
                if not include_inactive and not meta.active:
                    continue
                # Module-level sensitivity gate
                if not include_high_sensitivity and meta.sensitivity_high:
                    continue

        try:
            raw = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        except OSError:
            continue

        frontmatter, body = _parse_frontmatter(raw)
        if frontmatter is None:
            continue

        # File-level sensitivity gate (overrides module default).
        if not include_high_sensitivity and frontmatter.get("sensitivity") == "high":
            continue

        if type_filter is not None:
            if frontmatter.get("type") not in type_filter:
                continue

        if where_predicate and not _where_passes(frontmatter, where_predicate):
            continue

        rel_path = str(path.relative_to(data_root))

        if fields:
            projected = {k: frontmatter.get(k) for k in fields if k in frontmatter}
        else:
            projected = dict(frontmatter)

        match: dict[str, Any] = {"path": rel_path, "frontmatter": projected}

        if include_body:
            match["body"], match["body_truncated"] = _maybe_truncate_body(body)

        matches.append(match)

    # Cap check — if include_body was requested but we exceed the cap, strip bodies.
    if include_body and len(matches) > MAX_INLINE_MATCHES:
        stripped = [{"path": m["path"], "frontmatter": m["frontmatter"]} for m in matches]
        return {"truncated_bodies": True, "matches": stripped}

    return {"matches": matches}


def _maybe_truncate_body(body: str) -> tuple[str, bool]:
    """Truncate body if it exceeds MAX_BODY_BYTES. Appends a marker noting
    how many bytes were cut. Truncation is byte-level, not character-level,
    because the cap is expressed in bytes in the spec."""
    body_bytes = body.encode("utf-8")
    if len(body_bytes) <= MAX_BODY_BYTES:
        return body, False
    extra = len(body_bytes) - MAX_BODY_BYTES
    # Cut on a byte boundary, then decode with errors='ignore' to drop any
    # half-character fragment at the cut.
    truncated_bytes = body_bytes[:MAX_BODY_BYTES]
    truncated = truncated_bytes.decode("utf-8", errors="ignore")
    truncated += BODY_TRUNCATION_MARKER.format(n=extra)
    return truncated, True


# ---------- CLI ----------


def _parse_args(argv: list[str]) -> dict[str, Any]:
    parser = argparse.ArgumentParser(
        prog="scan.py",
        description="Frontmatter scan + filter over CTO_OS_DATA.",
    )
    parser.add_argument(
        "--args",
        required=True,
        help="Query spec as a JSON object.",
    )
    parsed = parser.parse_args(argv)
    try:
        query = json.loads(parsed.args)
    except json.JSONDecodeError as e:
        raise ScanCrash(f"--args is not valid JSON: {e}")
    if not isinstance(query, dict):
        raise ScanCrash("--args must be a JSON object")
    return query


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    try:
        query = _parse_args(argv)
    except ScanCrash as e:
        print(str(e), file=sys.stderr)
        return 1

    try:
        data_root = _resolve_data_root()
    except ScanCrash as e:
        print(str(e), file=sys.stderr)
        return 1

    try:
        result = scan(data_root, query)
    except ScanError as e:
        # Query error → exit 0 with structured error envelope per the spec.
        print(json.dumps({"error": str(e), "query": query}))
        return 0
    except (OSError, ValueError) as e:
        # Unexpected crash — exit non-zero.
        print(f"scan.py crashed: {e}", file=sys.stderr)
        return 1

    print(json.dumps(result, default=_json_default))
    return 0


def _json_default(obj: Any) -> Any:
    """JSON encoder for types PyYAML produces that json doesn't natively handle."""
    import datetime as _dt

    if isinstance(obj, (_dt.date, _dt.datetime)):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


if __name__ == "__main__":
    sys.exit(main())
