"""Tests for scripts/rename_module.py.

Run rename_module as a subprocess against synthetic skill + data repos laid
down in tmp_path. Each test builds the fake repo, initializes a git repo on
it (rename_module requires clean git state), and invokes the script.

Covers:
  - Dry-run reports planned changes without touching files.
  - Committed run renames the dir, updates SKILL.md name, updates requires
    in sibling modules, updates README.md and BACKLOG.md.
  - Data-repo side renames dir + updates _module.md.
  - Refuses on dirty git tree.
  - Refuses on slug collision.
  - Refuses on identical old_slug / new_slug.
  - Unmodified-references scan surfaces lingering text mentions.
  - skip_data_repo leaves data repo untouched.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "scripts" / "rename_module.py"


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        check=False,
    )


def _init_git(repo: Path) -> None:
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "test")
    _git(repo, "add", ".")
    _git(repo, "commit", "-qm", "initial")


def _write_skill_module(
    skill_repo: Path,
    slug: str,
    *,
    requires: list[str] | None = None,
    optional: list[str] | None = None,
    description: str = "test module",
) -> None:
    module_dir = skill_repo / "modules" / slug
    module_dir.mkdir(parents=True, exist_ok=True)
    requires_block = "requires:\n" + "".join(f"  - {r}\n" for r in requires or []) if requires else "requires: []\n"
    optional_block = "optional:\n" + "".join(f"  - {o}\n" for o in optional or []) if optional else "optional: []\n"
    body = (
        "---\n"
        f"name: {slug}\n"
        f'description: "{description}"\n'
        f"{requires_block}"
        f"{optional_block}"
        "---\n\n"
        f"# {slug}\n\n"
        "State location: `cto-os-data/modules/" + slug + "/state/`\n"
    )
    (module_dir / "SKILL.md").write_text(body, encoding="utf-8")
    (module_dir / "README.md").write_text(f"# {slug}\n", encoding="utf-8")


def _write_readme(skill_repo: Path, content: str) -> None:
    (skill_repo / "README.md").write_text(content, encoding="utf-8")


def _write_data_module(data_repo: Path, slug: str) -> None:
    module_dir = data_repo / "modules" / slug
    (module_dir / "state").mkdir(parents=True, exist_ok=True)
    (module_dir / "_module.md").write_text(
        "---\n"
        "type: _module\n"
        f"slug: {slug}\n"
        f"module: {slug}\n"
        "updated: 2026-04-22\n"
        "schema_version: 1\n"
        "active: true\n"
        "activated_at: 2026-03-01\n"
        "deactivated_at: null\n"
        "---\n",
        encoding="utf-8",
    )


def _run(
    skill_repo: Path, data_repo: Path | None, args: dict
) -> subprocess.CompletedProcess:
    env = {**os.environ}
    if data_repo is not None:
        env["CTO_OS_DATA"] = str(data_repo)
    else:
        env.pop("CTO_OS_DATA", None)

    # Temporarily override the script's auto-detected repo root by invoking
    # via the script's absolute path — rename_module uses Path(__file__) for
    # repo_root_default, so we need to run it from a location where that
    # resolves to our synthetic skill_repo. Easiest: stage a copy of the
    # script inside the synthetic repo.
    staged_scripts = skill_repo / "scripts"
    staged_scripts.mkdir(parents=True, exist_ok=True)
    staged_path = staged_scripts / "rename_module.py"
    if not staged_path.exists():
        shutil.copy(SCRIPT, staged_path)
        _git(skill_repo, "add", "scripts/rename_module.py")
        _git(skill_repo, "commit", "-qm", "stage rename_module")

    return subprocess.run(
        [sys.executable, str(staged_path), "--args", json.dumps(args)],
        capture_output=True,
        text=True,
        env=env,
    )


# ---------- Basic dry-run / committed flow ----------


def test_dry_run_reports_changes_without_touching_files(tmp_path):
    skill_repo = tmp_path / "skill"
    data_repo = tmp_path / "data"
    _write_skill_module(skill_repo, "old-name")
    _write_skill_module(skill_repo, "other", requires=["old-name"])
    _write_readme(skill_repo, "- [Old Name](modules/old-name/README.md)\n")
    _write_data_module(data_repo, "old-name")
    _init_git(skill_repo)
    _init_git(data_repo)

    result = _run(skill_repo, data_repo, {"old_slug": "old-name", "new_slug": "new-name"})
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report["status"] == "dry-run"

    paths = {(c["repo"], c["path"], c["action"]) for c in report["planned_changes"]}
    assert ("skill", "modules/old-name", "rename") in paths
    assert ("skill", "modules/new-name/SKILL.md", "update") in paths
    assert ("skill", "modules/other/SKILL.md", "update") in paths
    assert ("skill", "README.md", "update") in paths
    assert ("data", "modules/old-name", "rename") in paths
    assert ("data", "modules/new-name/_module.md", "update") in paths

    # Nothing actually moved.
    assert (skill_repo / "modules" / "old-name").is_dir()
    assert not (skill_repo / "modules" / "new-name").exists()
    assert (data_repo / "modules" / "old-name").is_dir()


def test_committed_run_applies_changes(tmp_path):
    skill_repo = tmp_path / "skill"
    data_repo = tmp_path / "data"
    _write_skill_module(skill_repo, "old-name")
    _write_skill_module(skill_repo, "other", requires=["old-name"])
    _write_readme(skill_repo, "Before: modules/old-name/README.md\n")
    _write_data_module(data_repo, "old-name")
    _init_git(skill_repo)
    _init_git(data_repo)

    result = _run(
        skill_repo, data_repo,
        {"old_slug": "old-name", "new_slug": "new-name", "dry_run": False},
    )
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report["status"] == "committed"

    # Directories moved.
    assert not (skill_repo / "modules" / "old-name").exists()
    assert (skill_repo / "modules" / "new-name" / "SKILL.md").is_file()
    assert not (data_repo / "modules" / "old-name").exists()
    assert (data_repo / "modules" / "new-name" / "_module.md").is_file()

    # SKILL.md frontmatter updated.
    renamed_skill = (skill_repo / "modules" / "new-name" / "SKILL.md").read_text(encoding="utf-8")
    assert "name: new-name" in renamed_skill
    assert "name: old-name" not in renamed_skill

    # Sibling requires list updated.
    sibling_skill = (skill_repo / "modules" / "other" / "SKILL.md").read_text(encoding="utf-8")
    assert "- new-name" in sibling_skill
    assert "- old-name" not in sibling_skill

    # README updated.
    readme = (skill_repo / "README.md").read_text(encoding="utf-8")
    assert "modules/new-name/README.md" in readme
    assert "modules/old-name/" not in readme

    # _module.md updated.
    module_md = (data_repo / "modules" / "new-name" / "_module.md").read_text(encoding="utf-8")
    assert "slug: new-name" in module_md
    assert "module: new-name" in module_md
    assert "old-name" not in module_md


# ---------- Refusal paths ----------


def test_refuses_on_dirty_skill_repo(tmp_path):
    skill_repo = tmp_path / "skill"
    data_repo = tmp_path / "data"
    _write_skill_module(skill_repo, "old-name")
    _write_data_module(data_repo, "old-name")
    _init_git(skill_repo)
    _init_git(data_repo)
    # Dirty the skill repo.
    (skill_repo / "dirty.txt").write_text("dirty", encoding="utf-8")

    result = _run(skill_repo, data_repo, {"old_slug": "old-name", "new_slug": "new-name"})
    assert result.returncode == 1
    report = json.loads(result.stdout)
    assert report["status"] == "error"
    assert any("skill repo" in e for e in report["errors"])


def test_refuses_on_slug_collision(tmp_path):
    skill_repo = tmp_path / "skill"
    data_repo = tmp_path / "data"
    _write_skill_module(skill_repo, "old-name")
    _write_skill_module(skill_repo, "new-name")
    _write_data_module(data_repo, "old-name")
    _init_git(skill_repo)
    _init_git(data_repo)

    result = _run(skill_repo, data_repo, {"old_slug": "old-name", "new_slug": "new-name"})
    assert result.returncode == 1
    report = json.loads(result.stdout)
    assert "already exists" in report["errors"][0]


def test_refuses_on_identical_slugs(tmp_path):
    skill_repo = tmp_path / "skill"
    _write_skill_module(skill_repo, "same")
    _init_git(skill_repo)

    result = _run(skill_repo, None, {"old_slug": "same", "new_slug": "same", "skip_data_repo": True})
    assert result.returncode == 1
    report = json.loads(result.stdout)
    assert "identical" in report["errors"][0]


def test_refuses_when_old_slug_missing(tmp_path):
    skill_repo = tmp_path / "skill"
    _write_skill_module(skill_repo, "real")
    _init_git(skill_repo)

    result = _run(
        skill_repo, None,
        {"old_slug": "ghost", "new_slug": "new-name", "skip_data_repo": True},
    )
    assert result.returncode == 1
    report = json.loads(result.stdout)
    assert "doesn't exist" in report["errors"][0]


# ---------- Unmodified references ----------


def test_unmodified_references_surfaced(tmp_path):
    skill_repo = tmp_path / "skill"
    _write_skill_module(skill_repo, "old-name")
    # Put an unstructured mention in a docs file — rename_module shouldn't
    # auto-rewrite this because it's not in a known target location.
    docs = skill_repo / "docs"
    docs.mkdir(parents=True)
    (docs / "notes.md").write_text(
        "Random prose referencing old-name by name in free text.\n",
        encoding="utf-8",
    )
    _init_git(skill_repo)

    result = _run(
        skill_repo, None,
        {"old_slug": "old-name", "new_slug": "new-name", "skip_data_repo": True},
    )
    assert result.returncode == 0
    report = json.loads(result.stdout)
    # The free-text mention should be flagged.
    unmod = report["unmodified_references"]
    assert any("docs/notes.md" in u["path"] for u in unmod), unmod


# ---------- skip_data_repo ----------


def test_skip_data_repo_leaves_data_alone(tmp_path):
    skill_repo = tmp_path / "skill"
    data_repo = tmp_path / "data"
    _write_skill_module(skill_repo, "old-name")
    _write_data_module(data_repo, "old-name")
    _init_git(skill_repo)
    _init_git(data_repo)

    result = _run(
        skill_repo, data_repo,
        {
            "old_slug": "old-name",
            "new_slug": "new-name",
            "dry_run": False,
            "skip_data_repo": True,
        },
    )
    assert result.returncode == 0
    # Skill renamed, data untouched.
    assert (skill_repo / "modules" / "new-name").is_dir()
    assert (data_repo / "modules" / "old-name").is_dir()
    # Report only contains skill-repo changes.
    report = json.loads(result.stdout)
    repos_in_plan = {c["repo"] for c in report["planned_changes"]}
    assert repos_in_plan == {"skill"}


# ---------- Bad args ----------


def test_missing_required_field_crashes(tmp_path):
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--args", json.dumps({"old_slug": "only-one"})],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 2
    assert "missing required field" in result.stderr
