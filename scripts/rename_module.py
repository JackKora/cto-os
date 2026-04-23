#!/usr/bin/env python3
"""
rename_module.py — rename a module slug in lockstep across the skill repo
(this repo) and the data repo ($CTO_OS_DATA).

Safe by default:
  - Dry-run unless the caller explicitly opts in.
  - Refuses to operate if either repo has uncommitted changes — the caller
    must review + commit the rename diff cleanly.
  - Refuses if the `new_slug` is already taken on either side.

What it rewrites automatically:
  - Renames the module directory on both repos.
  - Updates `modules/<new_slug>/SKILL.md` frontmatter `name:` in the skill repo.
  - Updates `modules/<new_slug>/_module.md` frontmatter `module:` and `slug:`
    in the data repo.
  - Updates `requires:` / `optional:` entries in other modules' SKILL.md
    frontmatter that reference the old slug (exact match only, inside those
    frontmatter blocks).
  - Updates the line in `README.md`'s module index.

What it flags but does NOT auto-rewrite:
  - Any other textual reference to the old slug anywhere in either repo.
    Surfaced in the `unmodified_references` list of the report so the user
    can review and fix by hand. Auto-rewriting arbitrary text risks false
    positives (e.g., a person named the same thing).

Usage:
    uv run python scripts/rename_module.py --args \\
        '{"old_slug": "managing-down", "new_slug": "direct-reports"}'

    # Commit instead of dry-run:
    uv run python scripts/rename_module.py --args \\
        '{"old_slug": "managing-down", "new_slug": "direct-reports", "dry_run": false}'

Args (JSON object):
    old_slug:        string, required
    new_slug:        string, required
    dry_run:         bool, optional (default: true)
    skip_data_repo:  bool, optional (default: false) — skip data-repo work
                     entirely, e.g., when the data repo hasn't been set up yet

Contract:
  - Exit 0: success (dry-run or committed).
  - Exit 1: validation failure (slug collision, dirty git tree, old slug
            not found). Report printed to stdout.
  - Exit 2: operational crash.

Output (stdout, always JSON):
  {
    "status": "dry-run" | "committed" | "error",
    "old_slug": "...",
    "new_slug": "...",
    "planned_changes": [
      {"repo": "skill" | "data", "path": "...", "action": "rename" | "update", "detail": "..."}
    ],
    "unmodified_references": [
      {"repo": "skill" | "data", "path": "...", "line": 42,
       "preview": "...old-slug..."}
    ],
    "errors": []
  }
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


# ---------- Errors ----------


class RenameCrash(Exception):
    """Exit 2 — the script couldn't operate."""


class RenameValidation(Exception):
    """Exit 1 — validation failure; structured report printed."""


# ---------- Repo root detection ----------


def _repo_root_default() -> Path:
    return Path(__file__).resolve().parent.parent


def _data_root() -> Path | None:
    value = os.environ.get("CTO_OS_DATA", "").strip()
    if not value:
        return None
    root = Path(os.path.expanduser(value)).resolve()
    return root if root.is_dir() else None


# ---------- Git cleanliness ----------


def _git_is_clean(repo_root: Path) -> tuple[bool, str]:
    """Check whether a repo has a clean working tree.

    Returns (is_clean, detail). detail is the `git status --porcelain` output
    when not clean, or 'not a git repo' when the dir isn't git-tracked."""
    try:
        result = subprocess.run(
            ["git", "-C", str(repo_root), "status", "--porcelain"],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        return False, "git CLI not found"
    if result.returncode != 0:
        return False, f"not a git repo (or git failed): {result.stderr.strip()}"
    status = result.stdout
    if status.strip():
        return False, status
    return True, ""


# ---------- Plan + execution ----------


@dataclass
class PlannedChange:
    repo: str            # "skill" or "data"
    path: str            # repo-relative path
    action: str          # "rename" or "update"
    detail: str          # short description
    # For `update` actions: pre-computed new content. Held here so we apply
    # all reads first, then all writes.
    new_content: str | None = None
    # For `rename` actions: destination path (repo-relative).
    dest_path: str | None = None


@dataclass
class _UnmodifiedRef:
    repo: str
    path: str
    line: int
    preview: str


@dataclass
class _Plan:
    changes: list[PlannedChange] = field(default_factory=list)
    unmodified: list[_UnmodifiedRef] = field(default_factory=list)


# ---------- Frontmatter-scoped rewrites ----------

_FRONTMATTER_BLOCK = re.compile(r"^(---\s*\n)(.*?)(\n---\s*\n)", re.DOTALL)


def _rewrite_frontmatter_only(
    content: str, rewrite_fn
) -> tuple[str, bool]:
    """Apply rewrite_fn to the frontmatter block only; leave body untouched.
    Returns (new_content, changed)."""
    match = _FRONTMATTER_BLOCK.match(content)
    if not match:
        return content, False
    opener, yaml_body, closer = match.group(1), match.group(2), match.group(3)
    new_yaml = rewrite_fn(yaml_body)
    if new_yaml == yaml_body:
        return content, False
    new_content = opener + new_yaml + closer + content[match.end():]
    return new_content, True


def _replace_list_member(yaml_body: str, old: str, new: str) -> str:
    """Replace `- old` entries inside `requires:` and `optional:` list blocks.
    Simple line-level replacement — safe because we only touch list items
    with the exact old value, inside known blocks."""
    lines = yaml_body.split("\n")
    inside_deps_block = False
    for i, line in enumerate(lines):
        stripped = line.strip()
        # Start/end of requires/optional blocks. Both are top-level keys
        # (no leading spaces) in our SKILL.md frontmatter.
        if re.match(r"^(requires|optional)\s*:", line):
            inside_deps_block = True
            continue
        if inside_deps_block:
            # A dep-block entry is "  - <slug>" with two-space indent. If a
            # line doesn't start with whitespace it's a new top-level key,
            # which ends the block.
            if line and not line.startswith((" ", "\t")):
                inside_deps_block = False
                continue
            if stripped == f"- {old}":
                # Preserve original indentation.
                indent = line[: len(line) - len(line.lstrip())]
                lines[i] = f"{indent}- {new}"
    return "\n".join(lines)


def _replace_scalar_field(yaml_body: str, field_name: str, old: str, new: str) -> str:
    """Replace the value of a scalar frontmatter field, e.g., `name: old` →
    `name: new`. Quoted and unquoted values both handled; we don't re-quote."""
    pattern = re.compile(
        rf"^({re.escape(field_name)}\s*:\s*)(['\"]?){re.escape(old)}\2(\s*)$",
        re.MULTILINE,
    )

    def _sub(match: re.Match[str]) -> str:
        prefix, quote, trailing = match.group(1), match.group(2), match.group(3)
        return f"{prefix}{quote}{new}{quote}{trailing}"

    return pattern.sub(_sub, yaml_body)


# ---------- Plan builders ----------


def _plan_skill_repo(
    repo_root: Path, old_slug: str, new_slug: str
) -> list[PlannedChange]:
    changes: list[PlannedChange] = []
    old_dir = repo_root / "modules" / old_slug
    new_dir = repo_root / "modules" / new_slug

    if not old_dir.is_dir():
        raise RenameValidation(
            f"skill repo: modules/{old_slug}/ doesn't exist"
        )
    if new_dir.exists():
        raise RenameValidation(
            f"skill repo: modules/{new_slug}/ already exists — slug collision"
        )

    # 1. Directory rename.
    changes.append(
        PlannedChange(
            repo="skill",
            path=f"modules/{old_slug}",
            dest_path=f"modules/{new_slug}",
            action="rename",
            detail=f"modules/{old_slug}/ → modules/{new_slug}/",
        )
    )

    # 2. Update SKILL.md frontmatter `name:` inside the renamed directory.
    #    We plan the update against the old path; execution applies it after
    #    the rename, so we re-point to the new path below.
    skill_file = old_dir / "SKILL.md"
    if skill_file.is_file():
        content = skill_file.read_text(encoding="utf-8")

        def rewrite(fm: str) -> str:
            return _replace_scalar_field(fm, "name", old_slug, new_slug)

        new_content, changed = _rewrite_frontmatter_only(content, rewrite)
        if changed:
            changes.append(
                PlannedChange(
                    repo="skill",
                    path=f"modules/{new_slug}/SKILL.md",
                    action="update",
                    detail=f"frontmatter name: {old_slug} → {new_slug}",
                    new_content=new_content,
                )
            )

    # 3. Update `requires:` / `optional:` entries in every OTHER module's SKILL.md.
    modules_dir = repo_root / "modules"
    for sibling in sorted(modules_dir.iterdir()):
        if not sibling.is_dir():
            continue
        if sibling.name in (old_slug, new_slug):
            continue
        sibling_skill = sibling / "SKILL.md"
        if not sibling_skill.is_file():
            continue
        content = sibling_skill.read_text(encoding="utf-8")
        new_content, changed = _rewrite_frontmatter_only(
            content,
            lambda fm: _replace_list_member(fm, old_slug, new_slug),
        )
        if changed:
            changes.append(
                PlannedChange(
                    repo="skill",
                    path=f"modules/{sibling.name}/SKILL.md",
                    action="update",
                    detail=f"requires/optional: {old_slug} → {new_slug}",
                    new_content=new_content,
                )
            )

    # 4. Update README.md module-index links/paths.
    readme = repo_root / "README.md"
    if readme.is_file():
        content = readme.read_text(encoding="utf-8")
        new_content = _rewrite_readme_references(content, old_slug, new_slug)
        if new_content != content:
            changes.append(
                PlannedChange(
                    repo="skill",
                    path="README.md",
                    action="update",
                    detail=f"references to {old_slug}",
                    new_content=new_content,
                )
            )

    return changes


def _plan_data_repo(
    data_root: Path, old_slug: str, new_slug: str
) -> list[PlannedChange]:
    changes: list[PlannedChange] = []
    old_dir = data_root / "modules" / old_slug
    new_dir = data_root / "modules" / new_slug

    if not old_dir.is_dir():
        # Data-repo module may never have been activated — that's OK, nothing
        # to rename on the data side.
        return changes
    if new_dir.exists():
        raise RenameValidation(
            f"data repo: modules/{new_slug}/ already exists — slug collision"
        )

    changes.append(
        PlannedChange(
            repo="data",
            path=f"modules/{old_slug}",
            dest_path=f"modules/{new_slug}",
            action="rename",
            detail=f"modules/{old_slug}/ → modules/{new_slug}/",
        )
    )

    module_file = old_dir / "_module.md"
    if module_file.is_file():
        content = module_file.read_text(encoding="utf-8")

        def rewrite(fm: str) -> str:
            fm = _replace_scalar_field(fm, "module", old_slug, new_slug)
            fm = _replace_scalar_field(fm, "slug", old_slug, new_slug)
            return fm

        new_content, changed = _rewrite_frontmatter_only(content, rewrite)
        if changed:
            changes.append(
                PlannedChange(
                    repo="data",
                    path=f"modules/{new_slug}/_module.md",
                    action="update",
                    detail=f"frontmatter module/slug: {old_slug} → {new_slug}",
                    new_content=new_content,
                )
            )

    return changes


# ---------- README rewriters ----------

# README: replace `modules/old-slug/README.md` and `modules/old-slug/SKILL.md`
# style links, plus bare mentions like `modules/old-slug/` in prose/tree.
_README_PATH_TOKENS = (
    "modules/{slug}/README.md",
    "modules/{slug}/SKILL.md",
    "modules/{slug}/",
    "cto-os-data/modules/{slug}/",
)


def _rewrite_readme_references(content: str, old_slug: str, new_slug: str) -> str:
    new_content = content
    for template in _README_PATH_TOKENS:
        new_content = new_content.replace(
            template.format(slug=old_slug),
            template.format(slug=new_slug),
        )
    return new_content


# ---------- Unmodified-reference scan ----------


def _scan_for_unmodified_references(
    repo_root: Path, old_slug: str, touched_paths: set[str], repo_label: str
) -> list[_UnmodifiedRef]:
    """Walk the repo looking for remaining textual references to the old slug
    in .md / .py / .yaml / .sh files we didn't auto-rewrite. Skip .git, .venv,
    __pycache__, and anything we already planned to update."""
    results: list[_UnmodifiedRef] = []

    skip_dirs = {".git", ".venv", "__pycache__", "node_modules", "logs",
                 "integrations-cache", ".pytest_cache"}
    scan_extensions = {".md", ".py", ".yaml", ".yml", ".sh", ".toml"}

    for root, dirs, files in os.walk(repo_root):
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        for fname in files:
            if Path(fname).suffix not in scan_extensions:
                continue
            abs_path = Path(root) / fname
            rel = abs_path.relative_to(repo_root).as_posix()
            if rel in touched_paths:
                continue
            # Also skip the inside of the renamed directory — it's been moved.
            if rel.startswith(f"modules/{old_slug}/"):
                continue
            try:
                text = abs_path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            for i, line in enumerate(text.splitlines(), start=1):
                if old_slug in line:
                    results.append(
                        _UnmodifiedRef(
                            repo=repo_label,
                            path=rel,
                            line=i,
                            preview=line.strip()[:200],
                        )
                    )
    return results


# ---------- Execution ----------


def _apply_changes(
    skill_root: Path, data_root: Path | None, changes: list[PlannedChange]
) -> None:
    """Execute the planned changes. Order matters:
       1. Apply all `update` changes first (targeting the POST-rename paths
          for the renamed module itself) — we wrote them against the new
          path in the plan.
       2. Then apply `rename` changes.
    Actually the simplest ordering: do renames FIRST, then updates, because
    the update content for the renamed module's own files was planned at the
    new path, so the file needs to be there first."""
    renames = [c for c in changes if c.action == "rename"]
    updates = [c for c in changes if c.action == "update"]

    # Apply renames first.
    for change in renames:
        root = skill_root if change.repo == "skill" else data_root
        if root is None:
            raise RenameCrash(
                f"data repo root not set; cannot apply rename {change.path}"
            )
        src = root / change.path
        dst = root / (change.dest_path or "")
        if dst.exists():
            raise RenameCrash(f"destination already exists: {dst}")
        shutil.move(str(src), str(dst))

    # Apply updates.
    for change in updates:
        root = skill_root if change.repo == "skill" else data_root
        if root is None:
            raise RenameCrash(
                f"data repo root not set; cannot apply update {change.path}"
            )
        target = root / change.path
        if not target.parent.is_dir():
            raise RenameCrash(f"target parent doesn't exist: {target.parent}")
        if change.new_content is None:
            raise RenameCrash(f"planned update has no content: {change.path}")
        target.write_text(change.new_content, encoding="utf-8")


# ---------- CLI ----------


def _parse_args(argv: list[str]) -> dict[str, Any]:
    parser = argparse.ArgumentParser(
        prog="rename_module.py",
        description="Rename a module slug in lockstep across skill + data repos.",
    )
    parser.add_argument(
        "--args",
        required=True,
        help='JSON object: {"old_slug":"","new_slug":"","dry_run":true,"skip_data_repo":false}',
    )
    parsed = parser.parse_args(argv)
    try:
        opts = json.loads(parsed.args)
    except json.JSONDecodeError as e:
        raise RenameCrash(f"--args is not valid JSON: {e}")
    if not isinstance(opts, dict):
        raise RenameCrash("--args must be a JSON object")
    for key in ("old_slug", "new_slug"):
        if key not in opts:
            raise RenameCrash(f"--args missing required field: {key}")
        if not isinstance(opts[key], str) or not opts[key]:
            raise RenameCrash(f"--args.{key} must be a non-empty string")
    return opts


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    try:
        opts = _parse_args(argv)
    except RenameCrash as e:
        print(str(e), file=sys.stderr)
        return 2

    old_slug = opts["old_slug"]
    new_slug = opts["new_slug"]
    dry_run = bool(opts.get("dry_run", True))
    skip_data_repo = bool(opts.get("skip_data_repo", False))

    if old_slug == new_slug:
        print(json.dumps({
            "status": "error",
            "errors": ["old_slug and new_slug are identical"],
        }))
        return 1

    skill_root = _repo_root_default()
    data_root = None if skip_data_repo else _data_root()

    errors: list[str] = []

    # Git-cleanliness check (both repos).
    clean, detail = _git_is_clean(skill_root)
    if not clean:
        errors.append(f"skill repo has uncommitted changes:\n{detail}")
    if data_root is not None:
        clean, detail = _git_is_clean(data_root)
        if not clean:
            errors.append(f"data repo has uncommitted changes:\n{detail}")

    if errors:
        print(json.dumps({
            "status": "error",
            "old_slug": old_slug,
            "new_slug": new_slug,
            "errors": errors,
        }))
        return 1

    # Build the plan.
    try:
        plan = _Plan()
        plan.changes.extend(_plan_skill_repo(skill_root, old_slug, new_slug))
        if data_root is not None:
            plan.changes.extend(_plan_data_repo(data_root, old_slug, new_slug))
    except RenameValidation as e:
        print(json.dumps({
            "status": "error",
            "old_slug": old_slug,
            "new_slug": new_slug,
            "errors": [str(e)],
        }))
        return 1

    # Scan for residual textual references.
    touched_skill = {c.path for c in plan.changes if c.repo == "skill"}
    touched_data = {c.path for c in plan.changes if c.repo == "data"}
    plan.unmodified.extend(
        _scan_for_unmodified_references(skill_root, old_slug, touched_skill, "skill")
    )
    if data_root is not None:
        plan.unmodified.extend(
            _scan_for_unmodified_references(data_root, old_slug, touched_data, "data")
        )

    if not dry_run:
        try:
            _apply_changes(skill_root, data_root, plan.changes)
        except RenameCrash as e:
            print(str(e), file=sys.stderr)
            return 2

    report = {
        "status": "dry-run" if dry_run else "committed",
        "old_slug": old_slug,
        "new_slug": new_slug,
        "planned_changes": [
            {
                "repo": c.repo,
                "path": c.path,
                "action": c.action,
                "detail": c.detail,
            }
            for c in plan.changes
        ],
        "unmodified_references": [
            {"repo": u.repo, "path": u.path, "line": u.line, "preview": u.preview}
            for u in plan.unmodified
        ],
        "errors": [],
    }
    print(json.dumps(report))
    return 0


if __name__ == "__main__":
    sys.exit(main())
