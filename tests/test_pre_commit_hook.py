"""Behavioral tests for Claude/Codex selection in hooks/pre-commit."""
from __future__ import annotations

import os
import shutil
import stat
import subprocess
import textwrap
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent


def _write_executable(path: Path, content: str) -> None:
    path.write_text(textwrap.dedent(content).lstrip(), encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR)


def _repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    (repo / "hooks").mkdir(parents=True)
    (repo / "docs").mkdir()
    shutil.copy2(REPO_ROOT / "hooks/pre-commit", repo / "hooks/pre-commit")
    (repo / "docs/change.md").write_text("review me\n", encoding="utf-8")
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    subprocess.run(["git", "-C", str(repo), "add", "docs/change.md"], check=True)
    return repo


def _reviewers(tmp_path: Path, verdict: str = "PASS") -> tuple[Path, Path]:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    log = tmp_path / "reviewer.log"
    _write_executable(
        bin_dir / "claude",
        f"""
        #!/usr/bin/env bash
        printf 'claude\n' >> "$REVIEWER_LOG"
        printf 'REVIEW: {verdict}\n'
        """,
    )
    _write_executable(
        bin_dir / "codex",
        f"""
        #!/usr/bin/env bash
        set -euo pipefail
        printf 'codex\n' >> "$REVIEWER_LOG"
        output_file=""
        skip_git_repo_check=false
        while [[ $# -gt 0 ]]; do
          case "$1" in
            --skip-git-repo-check)
              skip_git_repo_check=true
              shift
              ;;
            -o)
              output_file="$2"
              shift 2
              ;;
            *)
              shift
              ;;
          esac
        done
        [[ "$skip_git_repo_check" == true && -n "$output_file" ]] || exit 2
        printf 'REVIEW: {verdict}\n' > "$output_file"
        """,
    )
    return bin_dir, log


def _run(repo: Path, bin_dir: Path, log: Path, **extra: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env.pop("CTO_OS_REVIEWER", None)
    env.update(
        {
            "PATH": f"{bin_dir}{os.pathsep}{os.defpath}",
            "REVIEWER_LOG": str(log),
            "TMPDIR": str(repo.parent),
        }
    )
    env.update(extra)
    return subprocess.run(
        [str(repo / "hooks/pre-commit")],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
    )


def _commit(repo: Path, message: str) -> None:
    subprocess.run(
        [
            "git",
            "-C",
            str(repo),
            "-c",
            "user.name=Test",
            "-c",
            "user.email=test@example.com",
            "commit",
            "-q",
            "-m",
            message,
        ],
        check=True,
    )


def test_explicit_repo_config_selects_codex(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    bin_dir, log = _reviewers(tmp_path)
    subprocess.run(["git", "-C", str(repo), "config", "cto-os.reviewer", "codex"], check=True)

    result = _run(repo, bin_dir, log)
    assert result.returncode == 0, result.stderr
    assert log.read_text() == "codex\n"
    assert "with codex" in result.stdout


def test_environment_overrides_repo_config(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    bin_dir, log = _reviewers(tmp_path)
    subprocess.run(["git", "-C", str(repo), "config", "cto-os.reviewer", "codex"], check=True)

    result = _run(repo, bin_dir, log, CTO_OS_REVIEWER="claude")
    assert result.returncode == 0, result.stderr
    assert log.read_text() == "claude\n"


def test_auto_prefers_claude_for_backward_compatibility(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    bin_dir, log = _reviewers(tmp_path)

    result = _run(repo, bin_dir, log)
    assert result.returncode == 0, result.stderr
    assert log.read_text() == "claude\n"


def test_auto_falls_back_to_codex_when_outer_reviewer_is_set(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setenv("CTO_OS_REVIEWER", "none")
    repo = _repo(tmp_path)
    bin_dir, log = _reviewers(tmp_path)
    (bin_dir / "claude").unlink()

    result = _run(repo, bin_dir, log)
    assert result.returncode == 0, result.stderr
    assert log.read_text() == "codex\n"


def test_non_pass_verdict_blocks_commit(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    bin_dir, log = _reviewers(tmp_path, verdict="FAIL")
    subprocess.run(["git", "-C", str(repo), "config", "cto-os.reviewer", "codex"], check=True)

    result = _run(repo, bin_dir, log)
    assert result.returncode == 1
    assert "REVIEW: FAIL" in result.stdout
    assert "reported issues" in result.stderr


def test_deleted_module_skill_runs_dependency_and_ai_review(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    _commit(repo, "baseline")
    skill = repo / "modules/example/SKILL.md"
    skill.parent.mkdir(parents=True)
    skill.write_text("---\nname: example\ndescription: test\nrequires: []\noptional: []\n---\n")
    subprocess.run(["git", "-C", str(repo), "add", str(skill.relative_to(repo))], check=True)
    _commit(repo, "add module")
    skill.unlink()
    subprocess.run(["git", "-C", str(repo), "add", "-u"], check=True)

    bin_dir, log = _reviewers(tmp_path)
    _write_executable(
        bin_dir / "uv",
        """
        #!/usr/bin/env bash
        printf 'uv\n' >> "$REVIEWER_LOG"
        printf '{"ok": true}\n'
        """,
    )

    result = _run(repo, bin_dir, log)
    assert result.returncode == 0, result.stderr
    assert log.read_text() == "uv\nclaude\n"
    assert "validate_deps.py" in result.stdout
    assert "modules/example/SKILL.md" in result.stdout


def test_dependency_validation_uses_staged_project_and_snapshot(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    skill = repo / "modules/example/SKILL.md"
    skill.parent.mkdir(parents=True)
    skill.write_text("---\nname: example\nrequires: [bad-dependency]\n---\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(repo), "add", str(skill.relative_to(repo))], check=True)
    skill.write_text("---\nname: example\nrequires: []\n---\n", encoding="utf-8")

    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    log = tmp_path / "reviewer.log"
    _write_executable(
        bin_dir / "uv",
        """
        #!/usr/bin/env bash
        set -euo pipefail
        project=""
        script=""
        root=""
        while [[ $# -gt 0 ]]; do
          case "$1" in
            --project)
              project="$2"
              shift 2
              ;;
            python)
              script="$2"
              shift 2
              ;;
            --args)
              root="${2#*\\\"repo_root\\\":\\\"}"
              root="${root%%\\\"*}"
              shift 2
              ;;
            *)
              shift
              ;;
          esac
        done
        printf 'project:%s\\nscript:%s\\nroot:%s\\n' "$project" "$script" "$root" >> "$REVIEWER_LOG"
        if grep -q 'bad-dependency' "$root/modules/example/SKILL.md"; then
          printf '{"ok": false, "source": "staged"}\\n'
          exit 1
        fi
        printf '{"ok": true}\\n'
        """,
    )

    result = _run(repo, bin_dir, log, CTO_OS_REVIEWER="none")
    assert result.returncode == 1
    assert '"source": "staged"' in result.stderr
    invocation = dict(
        line.split(":", maxsplit=1)
        for line in log.read_text(encoding="utf-8").splitlines()
    )
    snapshot_root = Path(invocation["root"])
    assert snapshot_root != repo
    assert Path(invocation["project"]) == snapshot_root
    assert Path(invocation["script"]) == snapshot_root / "scripts/validate_deps.py"
    assert not snapshot_root.exists()


def test_claude_reviews_staged_snapshot_not_working_tree(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    change = repo / "docs/change.md"
    change.write_text("staged content\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(repo), "add", "docs/change.md"], check=True)
    change.write_text("working tree fix\n", encoding="utf-8")

    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    log = tmp_path / "reviewer.log"
    _write_executable(
        bin_dir / "claude",
        """
        #!/usr/bin/env bash
        set -euo pipefail
        printf 'claude:%s\\n' "$PWD" >> "$REVIEWER_LOG"
        printf 'prompt:%s\\n' "$*" >> "$REVIEWER_LOG"
        grep -q 'staged content' docs/change.md
        printf 'REVIEW: PASS\\n'
        """,
    )

    result = _run(repo, bin_dir, log, CTO_OS_REVIEWER="claude")
    assert result.returncode == 0, result.stderr
    entries = log.read_text(encoding="utf-8")
    snapshot_root = entries.splitlines()[0].removeprefix("claude:")
    assert Path(snapshot_root) != repo
    assert "staged Git index snapshot" in entries
    assert not Path(snapshot_root).exists()


def test_empty_checklist_contract_uses_exact_pass_verdict() -> None:
    procedure = (REPO_ROOT / "meta/skill-reviewer.md").read_text()
    assert "REVIEW: PASS (empty checklist)" not in procedure
    assert "emit exact `REVIEW: PASS`" in procedure
