#!/usr/bin/env python3
"""Read-only structural/baseline validator for CTO_OS_DATA state surfaces.

This intentionally validates baseline frontmatter plus two diagnosed type fields;
it is not a general per-type schema engine. Exit 0 is clean, 1 has findings,
and 2 indicates bad invocation or an operational failure.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

import yaml


class ValidationCrash(Exception):
    pass


_FM = re.compile(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", re.DOTALL)
_SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def _parse_args(argv: list[str]) -> dict[str, Any]:
    parser = argparse.ArgumentParser(prog="validate_state.py")
    parser.add_argument("--args", default="{}")
    parsed = parser.parse_args(argv)
    try:
        args = json.loads(parsed.args)
    except json.JSONDecodeError as e:
        raise ValidationCrash(f"--args is not valid JSON: {e}")
    if not isinstance(args, dict):
        raise ValidationCrash("--args must be a JSON object")
    if set(args) - {"include_high_sensitivity"}:
        raise ValidationCrash(f"unknown args: {sorted(set(args) - {'include_high_sensitivity'})}")
    if "include_high_sensitivity" in args and not isinstance(args["include_high_sensitivity"], bool):
        raise ValidationCrash("include_high_sensitivity must be a boolean")
    return args


def _data_root() -> Path:
    value = os.environ.get("CTO_OS_DATA", "").strip()
    if not value:
        raise ValidationCrash("CTO_OS_DATA env var is missing or empty")
    root = Path(os.path.expanduser(value)).resolve()
    if not root.is_dir():
        raise ValidationCrash(f"{root} does not exist or is not a directory")
    return root


def _known_types() -> set[str]:
    schema = Path(__file__).resolve().parent.parent / "meta" / "schema.md"
    try:
        raw = schema.read_text(encoding="utf-8")
    except OSError as e:
        raise ValidationCrash(f"couldn't read {schema}: {e}")
    section = raw.split("## Schema versions", 1)
    if len(section) != 2:
        raise ValidationCrash("meta/schema.md: missing Schema versions table")
    types = set(re.findall(r"^\| `([^`]+)` \| \d+ \|", section[1], re.MULTILINE))
    if not types:
        raise ValidationCrash("meta/schema.md: couldn't parse Schema versions table")
    return types


def _parse(raw: str) -> tuple[dict[str, Any] | None, str | None]:
    match = _FM.match(raw)
    if not match:
        return None, "missing YAML frontmatter"
    try:
        fm = yaml.safe_load(match.group(1))
    except yaml.YAMLError as e:
        return None, f"malformed YAML frontmatter: {e.problem or 'parse error'}"
    if not isinstance(fm, dict):
        return None, "YAML frontmatter must be a mapping"
    return fm, None


def _candidate_paths(root: Path) -> list[Path]:
    paths: list[Path] = []
    modules = root / "modules"
    if modules.is_dir():
        for module in sorted(modules.iterdir()):
            if not module.is_dir():
                continue
            module_file = module / "_module.md"
            if module_file.is_file():
                paths.append(module_file)
            state = module / "state"
            if state.is_dir():
                paths.extend(p for p in sorted(state.rglob("*.md")) if p.is_file())
    notes = root / "notes"
    if notes.is_dir():
        paths.extend(p for p in sorted(notes.rglob("*.md")) if p.is_file())
    return paths


def _module_directories(root: Path) -> list[Path]:
    modules = root / "modules"
    if not modules.is_dir():
        return []
    return [module for module in sorted(modules.iterdir()) if module.is_dir()]


def _date(value: Any, *, nullable: bool = False) -> bool:
    if value is None:
        return nullable
    if isinstance(value, dt.datetime):
        return False
    if isinstance(value, dt.date):
        return True
    if not isinstance(value, str):
        return False
    try:
        return dt.date.fromisoformat(value).isoformat() == value
    except ValueError:
        return False


def _raw_high(raw: str) -> bool:
    header = _raw_frontmatter_header(raw)
    if header is None:
        return False
    return bool(
        re.search(
            r"(?m)^[ \t]*sensitivity[ \t]*:[ \t]*(?:high|\"high\"|'high')(?:[ \t]+#[^\r\n]*)?[ \t]*\r?$",
            header,
        )
    )


def _raw_frontmatter_header(raw: str) -> str | None:
    """Return the raw frontmatter header, including an unclosed candidate."""
    opening = re.match(r"^---[ \t]*\r?\n", raw)
    if not opening:
        return None
    closing = re.search(r"(?m)^---[ \t]*(?:\r?\n|$)", raw[opening.end() :])
    end = opening.end() + closing.start() if closing else len(raw)
    return raw[opening.end() : end]


def _finding(findings: list[dict[str, str]], path: str, code: str, message: str, field: str | None = None) -> None:
    item = {"path": path, "code": code, "message": message}
    if field:
        item["field"] = field
    findings.append(item)


def validate(root: Path, include_high: bool) -> dict[str, Any]:
    known_types = _known_types()
    paths = _candidate_paths(root)
    module_dirs = _module_directories(root)
    module_meta: dict[str, tuple[bool | None, bool | None]] = {
        module.name: (None, None) for module in module_dirs
    }
    for path in paths:
        rel = path.relative_to(root)
        if len(rel.parts) != 3 or rel.parts[0] != "modules" or rel.parts[2] != "_module.md":
            continue
        try:
            raw = path.read_text(encoding="utf-8")
            fm, error = _parse(raw)
        except (OSError, UnicodeDecodeError):
            fm, error = None, "unreadable"
        module_meta[rel.parts[1]] = ((fm or {}).get("sensitivity") == "high" if not error else None, bool((fm or {}).get("active", True)) if not error else None)

    findings: list[dict[str, str]] = []
    hidden_errors = 0
    skipped_high = 0
    validated = 0

    # Missing module metadata leaves sensitivity unknown, so hide the affected
    # module identity by default while still surfacing the structural problem.
    # Diagnose it before records to make the output ordering deterministic.
    for module in module_dirs:
        if (module / "_module.md").is_file():
            continue
        if include_high:
            _finding(
                findings,
                str((module / "_module.md").relative_to(root)),
                "missing_module_metadata",
                "required module metadata is missing",
            )
        else:
            hidden_errors += 1

    for path in paths:
        rel = str(path.relative_to(root))
        parts = Path(rel).parts
        module = parts[1] if len(parts) >= 2 and parts[0] == "modules" else None
        module_high = module_meta.get(module, (False, None))[0] if module else False
        try:
            raw = path.read_text(encoding="utf-8")
            fm, parse_error = _parse(raw)
        except UnicodeDecodeError:
            raw, fm, parse_error = "", None, "unreadable UTF-8"
        except OSError as e:
            raw, fm, parse_error = "", None, f"couldn't read file: {e}"
        file_high = (fm or {}).get("sensitivity") == "high" if fm else _raw_high(raw)
        hidden = not include_high and (module_high is True or module_high is None or file_high)
        if hidden:
            if parse_error:
                hidden_errors += 1
            else:
                skipped_high += 1
            continue
        if parse_error:
            _finding(findings, rel, "invalid_frontmatter", parse_error)
            continue
        validated += 1
        for field in ("type", "slug", "updated"):
            if field not in fm or fm[field] is None:
                _finding(findings, rel, "missing_field", f"missing required baseline field {field}", field)
        if "type" in fm and not isinstance(fm["type"], str):
            _finding(findings, rel, "invalid_type", "type must be a string", "type")
        elif isinstance(fm.get("type"), str) and fm["type"] not in known_types:
            _finding(findings, rel, "unknown_type", "type is not listed in meta/schema.md", "type")
        if "slug" in fm and (not isinstance(fm["slug"], str) or not _SLUG.fullmatch(fm["slug"])):
            _finding(findings, rel, "invalid_slug", "slug must be lowercase kebab-case", "slug")
        if "updated" in fm and not _date(fm["updated"]):
            _finding(findings, rel, "invalid_date", "updated must be an ISO YYYY-MM-DD date", "updated")
        if len(parts) == 3 and parts[0] == "modules" and parts[2] == "_module.md":
            slug = parts[1]
            if fm.get("type") != "_module": _finding(findings, rel, "invalid_module", "_module.md must have type: _module", "type")
            if fm.get("slug") != slug: _finding(findings, rel, "invalid_module", "slug must match module directory", "slug")
            if fm.get("module") != slug: _finding(findings, rel, "invalid_module", "module must match module directory", "module")
            if not isinstance(fm.get("schema_version"), int) or isinstance(fm.get("schema_version"), bool): _finding(findings, rel, "invalid_module", "schema_version must be an integer", "schema_version")
            if not isinstance(fm.get("active"), bool): _finding(findings, rel, "invalid_module", "active must be a boolean", "active")
            for field in ("activated_at", "deactivated_at"):
                if field not in fm or not _date(fm.get(field), nullable=True): _finding(findings, rel, "invalid_module", f"{field} must be a date or null", field)
        if fm.get("type") == "requisition" and not _date(fm.get("opened")):
            _finding(findings, rel, "invalid_date", "requisition.opened must be an ISO YYYY-MM-DD date", "opened")
        if fm.get("type") == "stakeholder-profile" and "tenure_months" in fm and (not isinstance(fm["tenure_months"], int) or isinstance(fm["tenure_months"], bool)):
            _finding(findings, rel, "invalid_type", "stakeholder-profile.tenure_months must be an integer", "tenure_months")
    return {"findings": findings, "summary": {"candidate_file_count": len(paths), "validated_file_count": validated, "finding_count": len(findings), "hidden_error_count": hidden_errors, "skipped_high_sensitivity_count": skipped_high}}


def main(argv: list[str] | None = None) -> int:
    try:
        args = _parse_args(argv or sys.argv[1:])
        result = validate(_data_root(), args.get("include_high_sensitivity", False))
    except ValidationCrash as e:
        print(str(e), file=sys.stderr)
        return 2
    print(json.dumps(result, default=str))
    return 1 if result["summary"]["finding_count"] or result["summary"]["hidden_error_count"] else 0


if __name__ == "__main__":
    sys.exit(main())
