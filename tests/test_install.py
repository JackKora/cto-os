"""End-to-end tests for install.sh idempotence and conflict safety."""
from __future__ import annotations

import json
import os
import shutil
import stat
import subprocess
import sys
import textwrap
import tomllib
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent


def _write_executable(path: Path, content: str) -> None:
    path.write_text(textwrap.dedent(content).lstrip(), encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR)


def _installer_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "cto-os"
    repo.mkdir()
    for name in ("install.sh", "pyproject.toml", "uv.lock"):
        shutil.copy2(REPO_ROOT / name, repo / name)
    for name in ("templates", "hooks", "mcp-server"):
        shutil.copytree(REPO_ROOT / name, repo / name)
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    return repo


def _fake_commands(tmp_path: Path, *, include_codex: bool = True) -> Path:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()

    _write_executable(
        bin_dir / "uv",
        r"""
        #!/usr/bin/env bash
        set -euo pipefail
        if [[ "${1:-}" == "python" && "${2:-}" == "find" ]]; then
          printf '%s\n' "$TEST_PYTHON"
        elif [[ "${1:-}" == "sync" ]]; then
          mkdir -p .venv/bin
          printf '%s\n' '#!/usr/bin/env bash' 'exec "$TEST_PYTHON" "$@"' > .venv/bin/python
          chmod +x .venv/bin/python
        else
          echo "unexpected fake uv invocation: $*" >&2
          exit 2
        fi
        """,
    )

    if include_codex:
        _write_executable(
            bin_dir / "codex",
            r"""
        #!/usr/bin/env python3
        import json
        import os
        import sys
        import tomllib
        from pathlib import Path

        args = sys.argv[1:]
        config = Path(os.environ["CODEX_HOME"]) / "config.toml"
        value = tomllib.loads(config.read_text()) if config.exists() else {}
        if args[:2] == ["mcp", "list"]:
            if isinstance(value.get("model"), list):
                print("invalid type: sequence, expected a string", file=sys.stderr)
                raise SystemExit(1)
            print("[]")
            raise SystemExit(0)
        if args[:3] == ["mcp", "get", "cto-os"]:
            server = value.get("mcp_servers", {}).get("cto-os")
            if not isinstance(server, dict):
                raise SystemExit(1)
            if os.environ.get("FAKE_CODEX_REJECT_CTO_OS") == "1":
                print("generated cto-os entry rejected", file=sys.stderr)
                raise SystemExit(1)
            print(json.dumps(server))
            raise SystemExit(0)
        raise SystemExit(f"unexpected fake codex invocation: {args}")
        """,
        )
    return bin_dir


def _environment(tmp_path: Path, bin_dir: Path) -> dict[str, str]:
    home = tmp_path / "home"
    home.mkdir()
    env = os.environ.copy()
    env.update(
        {
            "HOME": str(home),
            "XDG_CONFIG_HOME": str(home / ".config"),
            "CODEX_HOME": str(home / ".codex"),
            "PATH": f"{bin_dir}{os.pathsep}{env['PATH']}",
            "TEST_PYTHON": sys.executable,
            "SHELL": "/bin/zsh",
        }
    )
    return env


def _claude_desktop_config(env: dict[str, str]) -> Path:
    if sys.platform == "darwin":
        return Path(env["HOME"]) / "Library/Application Support/Claude/claude_desktop_config.json"
    return Path(env["XDG_CONFIG_HOME"]) / "Claude/claude_desktop_config.json"


def _run(repo: Path, env: dict[str, str], *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(repo / "install.sh"), *args],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
    )


def _state(paths: list[Path]) -> dict[str, tuple[str, str]]:
    result = {}
    for path in paths:
        if path.is_symlink():
            result[str(path)] = ("link", os.readlink(path))
        else:
            result[str(path)] = ("file", path.read_text(encoding="utf-8"))
    return result


def _identity(paths: list[Path]) -> dict[str, tuple[int, int]]:
    return {str(path): (path.stat().st_ino, path.stat().st_mtime_ns) for path in paths}


def test_server_install_is_idempotent_and_preserves_other_config(tmp_path: Path) -> None:
    repo = _installer_repo(tmp_path)
    bin_dir = _fake_commands(tmp_path)
    env = _environment(tmp_path, bin_dir)
    home = Path(env["HOME"])
    data = tmp_path / "cto-os-data"
    claude_config = _claude_desktop_config(env)
    claude_config.parent.mkdir(parents=True)
    claude_config.write_text(
        json.dumps({"theme": "dark", "mcpServers": {"other": {"command": "other"}}}),
        encoding="utf-8",
    )
    codex_config = Path(env["CODEX_HOME"]) / "config.toml"
    codex_config.parent.mkdir(parents=True)
    codex_config.write_text('[general]\nvalue = "keep"\n\n[mcp_servers.other]\nurl = "https://other"\n')

    first = _run(repo, env, "--server", "--data-dir", str(data), "--reviewer", "codex", "-y")
    assert first.returncode == 0, first.stderr
    assert "Host registration:" in first.stdout
    assert first.stdout.count("[ok]") >= 5

    tracked = [
        data / "CLAUDE.md",
        data / "README.md",
        data / ".gitignore",
        data / "AGENTS.md",
        home / ".claude/skills/cto-os",
        home / ".agents/skills/cto-os",
        claude_config,
        codex_config,
    ]
    first_state = _state(tracked)
    config_identity = _identity([claude_config, codex_config])

    second = _run(repo, env, "--server", "--data-dir", str(data), "-y")
    assert second.returncode == 0, second.stderr
    assert _state(tracked) == first_state
    assert _identity([claude_config, codex_config]) == config_identity

    claude = json.loads(claude_config.read_text())
    assert claude["theme"] == "dark"
    assert claude["mcpServers"]["other"] == {"command": "other"}
    assert claude["mcpServers"]["cto-os"]["env"]["CTO_OS_DATA"] == str(data)
    codex = tomllib.loads(codex_config.read_text())
    assert codex["general"]["value"] == "keep"
    assert codex["mcp_servers"]["other"]["url"] == "https://other"
    assert codex["mcp_servers"]["cto-os"]["env"]["CTO_OS_DATA"] == str(data)
    reviewer = subprocess.run(
        ["git", "-C", str(repo), "config", "--local", "--get", "cto-os.reviewer"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    assert reviewer == "codex"


def test_client_install_is_idempotent_and_updates_managed_guidance(tmp_path: Path) -> None:
    repo = _installer_repo(tmp_path)
    bin_dir = _fake_commands(tmp_path)
    env = _environment(tmp_path, bin_dir)
    env.update(
        {
            "CTO_OS_REMOTE_URL": "https://cto.example/mcp",
            "CTO_OS_BEARER_TOKEN": "existing-remote-token",
        }
    )
    home = Path(env["HOME"])
    managed = home / ".claude/CLAUDE.md"
    managed.parent.mkdir(parents=True)
    managed.write_text("<!-- cto-os-client-marker -->\noutdated\n", encoding="utf-8")
    managed.chmod(0o640)

    first = _run(repo, env, "--client", "-y")
    assert first.returncode == 0, first.stderr
    assert managed.read_text() == (repo / "templates/client-CLAUDE.md").read_text()
    assert stat.S_IMODE(managed.stat().st_mode) == 0o640
    assert "Install status:" in first.stdout
    assert first.stdout.count("[ok]") >= 7

    tracked = [
        managed,
        home / ".codex/AGENTS.md",
        home / ".claude/skills/cto-os",
        home / ".agents/skills/cto-os",
        _claude_desktop_config(env),
        home / ".claude/settings.json",
        home / ".codex/config.toml",
    ]
    first_state = _state(tracked)
    config_identity = _identity(
        [_claude_desktop_config(env), home / ".claude/settings.json", home / ".codex/config.toml"]
    )
    second = _run(repo, env, "--client", "-y")
    assert second.returncode == 0, second.stderr
    assert _state(tracked) == first_state
    assert _identity(
        [_claude_desktop_config(env), home / ".claude/settings.json", home / ".codex/config.toml"]
    ) == config_identity
    assert stat.S_IMODE(managed.stat().st_mode) == 0o640

    authorization = "Bearer existing-remote-token"
    for path in (_claude_desktop_config(env), home / ".claude/settings.json"):
        entry = json.loads(path.read_text())["mcpServers"]["cto-os"]
        assert entry == {
            "url": "https://cto.example/mcp",
            "headers": {"Authorization": authorization},
        }
    codex = tomllib.loads((home / ".codex/config.toml").read_text())
    assert codex["mcp_servers"]["cto-os"]["http_headers"]["Authorization"] == authorization


def test_config_symlinks_are_preserved_and_targets_are_updated(tmp_path: Path) -> None:
    repo = _installer_repo(tmp_path)
    bin_dir = _fake_commands(tmp_path)
    env = _environment(tmp_path, bin_dir)
    env.update({"CTO_OS_REMOTE_URL": "https://cto.example/mcp", "CTO_OS_BEARER_TOKEN": "token"})
    home = Path(env["HOME"])
    dotfiles = home / "dotfiles"
    dotfiles.mkdir()

    logical_paths = [
        _claude_desktop_config(env),
        home / ".claude/settings.json",
        home / ".codex/config.toml",
    ]
    target_paths = [dotfiles / "desktop.json", dotfiles / "claude-code.json", dotfiles / "codex.toml"]
    target_paths[0].write_text('{"desktop": true}\n', encoding="utf-8")
    target_paths[1].write_text('{"code": true}\n', encoding="utf-8")
    target_paths[2].write_text(
        'model = "keep"\nmcp_servers = { other = { url = "https://other" } }\n', encoding="utf-8"
    )
    for logical, target in zip(logical_paths, target_paths, strict=True):
        logical.parent.mkdir(parents=True, exist_ok=True)
        logical.symlink_to(target)

    result = _run(repo, env, "--client", "-y")
    assert result.returncode == 0, result.stderr
    assert all(path.is_symlink() for path in logical_paths)
    assert json.loads(target_paths[0].read_text())["mcpServers"]["cto-os"]["url"] == env[
        "CTO_OS_REMOTE_URL"
    ]
    assert json.loads(target_paths[1].read_text())["mcpServers"]["cto-os"]["url"] == env[
        "CTO_OS_REMOTE_URL"
    ]
    codex = tomllib.loads(target_paths[2].read_text())
    assert codex["mcp_servers"]["cto-os"]["url"] == env["CTO_OS_REMOTE_URL"]
    assert codex["mcp_servers"]["other"]["url"] == "https://other"


def test_codex_config_is_written_when_cli_is_absent(tmp_path: Path) -> None:
    repo = _installer_repo(tmp_path)
    bin_dir = _fake_commands(tmp_path, include_codex=False)
    env = _environment(tmp_path, bin_dir)
    env["PATH"] = f"{bin_dir}:/usr/bin:/bin:/usr/sbin:/sbin"
    env.update({"CTO_OS_REMOTE_URL": "https://cto.example/mcp", "CTO_OS_BEARER_TOKEN": "token"})

    result = _run(repo, env, "--client", "-y")
    assert result.returncode == 0, result.stderr
    codex_config = Path(env["CODEX_HOME"]) / "config.toml"
    server = tomllib.loads(codex_config.read_text())["mcp_servers"]["cto-os"]
    assert server["url"] == env["CTO_OS_REMOTE_URL"]
    assert "could not CLI-validate" in result.stderr
    assert "Install completed with 1 warning(s); review the warnings above." in result.stderr
    assert "existing conflicting files were left unchanged" not in result.stderr


def test_rejected_codex_candidate_restores_regular_config_and_can_rerun(tmp_path: Path) -> None:
    repo = _installer_repo(tmp_path)
    bin_dir = _fake_commands(tmp_path)
    env = _environment(tmp_path, bin_dir)
    env.update(
        {
            "CTO_OS_REMOTE_URL": "https://cto.example/mcp",
            "CTO_OS_BEARER_TOKEN": "token",
            "FAKE_CODEX_REJECT_CTO_OS": "1",
        }
    )
    codex_config = Path(env["CODEX_HOME"]) / "config.toml"
    codex_config.parent.mkdir(parents=True)
    original = b'# preserve these exact bytes\nmodel = "keep"\n[mcp_servers.other]\nurl = "https://other"\n'
    codex_config.write_bytes(original)
    codex_config.chmod(0o640)

    rejected = _run(repo, env, "--client", "-y")
    assert rejected.returncode != 0
    assert "rejected the generated cto-os MCP configuration; restored the previous config" in rejected.stderr
    assert codex_config.read_bytes() == original
    assert stat.S_IMODE(codex_config.stat().st_mode) == 0o640

    env.pop("FAKE_CODEX_REJECT_CTO_OS")
    repaired = _run(repo, env, "--client", "-y")
    assert repaired.returncode == 0, repaired.stderr
    config = tomllib.loads(codex_config.read_text())
    assert config["mcp_servers"]["other"]["url"] == "https://other"
    assert config["mcp_servers"]["cto-os"]["url"] == env["CTO_OS_REMOTE_URL"]


def test_rejected_codex_candidate_restores_symlink_target(tmp_path: Path) -> None:
    repo = _installer_repo(tmp_path)
    bin_dir = _fake_commands(tmp_path)
    env = _environment(tmp_path, bin_dir)
    env.update(
        {
            "CTO_OS_REMOTE_URL": "https://cto.example/mcp",
            "CTO_OS_BEARER_TOKEN": "token",
            "FAKE_CODEX_REJECT_CTO_OS": "1",
        }
    )
    home = Path(env["HOME"])
    target = home / "dotfiles" / "codex.toml"
    target.parent.mkdir(parents=True)
    original = b'model = "keep"\n[mcp_servers.other]\nurl = "https://other"\n'
    target.write_bytes(original)
    target.chmod(0o640)
    logical_config = Path(env["CODEX_HOME"]) / "config.toml"
    logical_config.parent.mkdir()
    logical_config.symlink_to(target)

    rejected = _run(repo, env, "--client", "-y")
    assert rejected.returncode != 0
    assert logical_config.is_symlink()
    assert os.readlink(logical_config) == str(target)
    assert target.read_bytes() == original
    assert stat.S_IMODE(target.stat().st_mode) == 0o640

    env.pop("FAKE_CODEX_REJECT_CTO_OS")
    repaired = _run(repo, env, "--client", "-y")
    assert repaired.returncode == 0, repaired.stderr
    assert logical_config.is_symlink()
    assert tomllib.loads(target.read_text())["mcp_servers"]["cto-os"]["url"] == env[
        "CTO_OS_REMOTE_URL"
    ]


def test_rejected_codex_candidate_removes_new_config_target(tmp_path: Path) -> None:
    repo = _installer_repo(tmp_path)
    bin_dir = _fake_commands(tmp_path)
    env = _environment(tmp_path, bin_dir)
    env.update(
        {
            "CTO_OS_REMOTE_URL": "https://cto.example/mcp",
            "CTO_OS_BEARER_TOKEN": "token",
            "FAKE_CODEX_REJECT_CTO_OS": "1",
        }
    )
    codex_config = Path(env["CODEX_HOME"]) / "config.toml"

    rejected = _run(repo, env, "--client", "-y")
    assert rejected.returncode != 0
    assert not codex_config.exists()

    env.pop("FAKE_CODEX_REJECT_CTO_OS")
    repaired = _run(repo, env, "--client", "-y")
    assert repaired.returncode == 0, repaired.stderr
    assert tomllib.loads(codex_config.read_text())["mcp_servers"]["cto-os"]["url"] == env[
        "CTO_OS_REMOTE_URL"
    ]


def test_client_preserves_unmanaged_global_instructions(tmp_path: Path) -> None:
    repo = _installer_repo(tmp_path)
    bin_dir = _fake_commands(tmp_path)
    env = _environment(tmp_path, bin_dir)
    env.update({"CTO_OS_REMOTE_URL": "https://cto.example/mcp", "CTO_OS_BEARER_TOKEN": "token"})
    home = Path(env["HOME"])
    unmanaged = home / ".claude/CLAUDE.md"
    unmanaged.parent.mkdir(parents=True)
    unmanaged.write_text("my unrelated global instructions\n", encoding="utf-8")

    result = _run(repo, env, "--client", "-y")
    assert result.returncode == 0
    assert unmanaged.read_text() == "my unrelated global instructions\n"
    assert not (home / ".codex/AGENTS.md").exists()
    assert f"{unmanaged} exists without the CTO OS marker; left unchanged" in result.stderr
    assert "Install completed with 2 warning(s); review the warnings above." in result.stderr
    assert any(
        "Client instructions:" in line and "[SKIPPED]" in line
        for line in result.stdout.splitlines()
    )
    assert any(
        "Codex guidance:" in line and "[SKIPPED]" in line
        for line in result.stdout.splitlines()
    )
    assert "skill and MCP are configured globally" not in result.stdout


def test_client_reports_conflicting_skill_symlinks_as_skipped(tmp_path: Path) -> None:
    repo = _installer_repo(tmp_path)
    bin_dir = _fake_commands(tmp_path)
    env = _environment(tmp_path, bin_dir)
    env.update({"CTO_OS_REMOTE_URL": "https://cto.example/mcp", "CTO_OS_BEARER_TOKEN": "token"})
    home = Path(env["HOME"])
    claude_skill = home / ".claude/skills/cto-os"
    codex_skill = home / ".agents/skills/cto-os"
    for path, target_name in ((claude_skill, "other-claude"), (codex_skill, "other-codex")):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.symlink_to(home / target_name)

    result = _run(repo, env, "--client", "-y")
    assert result.returncode == 0, result.stderr
    assert os.readlink(claude_skill) == str(home / "other-claude")
    assert os.readlink(codex_skill) == str(home / "other-codex")
    assert any(
        "Claude skill:" in line and "[SKIPPED]" in line
        for line in result.stdout.splitlines()
    )
    assert any(
        "Codex skill:" in line and "[SKIPPED]" in line
        for line in result.stdout.splitlines()
    )
    assert "skill and MCP are configured globally" not in result.stdout


def test_malformed_config_stops_before_any_install_write(tmp_path: Path) -> None:
    repo = _installer_repo(tmp_path)
    bin_dir = _fake_commands(tmp_path)
    env = _environment(tmp_path, bin_dir)
    colon_home = tmp_path / "home:with-colon"
    colon_home.mkdir()
    env.update(
        {
            "HOME": str(colon_home),
            "XDG_CONFIG_HOME": str(colon_home / ".config"),
            "CODEX_HOME": str(colon_home / ".codex"),
        }
    )
    home = colon_home
    data = tmp_path / "cto-os-data"
    config = _claude_desktop_config(env)
    config.parent.mkdir(parents=True)
    config.write_text("{not-json", encoding="utf-8")

    result = _run(repo, env, "--server", "--data-dir", str(data), "-y")
    assert result.returncode != 0
    assert "not valid JSON" in result.stderr
    assert not data.exists()
    assert not (repo / ".venv").exists()
    assert not (home / ".claude/skills/cto-os").exists()
    assert not (home / ".agents/skills/cto-os").exists()
    assert (
        subprocess.run(
            ["git", "-C", str(repo), "config", "--local", "--get", "core.hooksPath"],
            capture_output=True,
            text=True,
        ).returncode
        != 0
    )


def test_client_malformed_claude_code_config_with_colon_path_stops_before_writes(
    tmp_path: Path,
) -> None:
    repo = _installer_repo(tmp_path)
    bin_dir = _fake_commands(tmp_path)
    env = _environment(tmp_path, bin_dir)
    colon_home = tmp_path / "home:with-colon"
    colon_home.mkdir()
    env.update(
        {
            "HOME": str(colon_home),
            "XDG_CONFIG_HOME": str(colon_home / ".config"),
            "CODEX_HOME": str(colon_home / ".codex"),
            "CTO_OS_REMOTE_URL": "https://cto.example/mcp",
            "CTO_OS_BEARER_TOKEN": "token",
        }
    )
    config = colon_home / ".claude/settings.json"
    config.parent.mkdir(parents=True)
    config.write_text("{not-json", encoding="utf-8")

    result = _run(repo, env, "--client", "-y")
    assert result.returncode != 0
    assert "not valid JSON" in result.stderr
    assert not (repo / ".venv").exists()
    assert not (colon_home / ".claude/skills/cto-os").exists()
    assert not (colon_home / ".agents/skills/cto-os").exists()
    assert not (colon_home / ".claude/CLAUDE.md").exists()
    assert not (colon_home / ".codex/AGENTS.md").exists()
    assert (
        subprocess.run(
            ["git", "-C", str(repo), "config", "--local", "--get", "core.hooksPath"],
            capture_output=True,
            text=True,
        ).returncode
        != 0
    )


def test_malformed_codex_config_also_stops_before_writes(tmp_path: Path) -> None:
    repo = _installer_repo(tmp_path)
    bin_dir = _fake_commands(tmp_path)
    env = _environment(tmp_path, bin_dir)
    home = Path(env["HOME"])
    data = tmp_path / "cto-os-data"
    codex_config = Path(env["CODEX_HOME"]) / "config.toml"
    codex_config.parent.mkdir(parents=True)
    codex_config.write_text("[broken\n", encoding="utf-8")

    result = _run(repo, env, "--server", "--data-dir", str(data), "-y")
    assert result.returncode != 0
    assert "not valid TOML" in result.stderr
    assert not data.exists()
    assert not (repo / ".venv").exists()
    assert not (home / ".claude/skills/cto-os").exists()
    assert not (home / ".agents/skills/cto-os").exists()


def test_semantically_invalid_codex_config_stops_before_writes(tmp_path: Path) -> None:
    repo = _installer_repo(tmp_path)
    bin_dir = _fake_commands(tmp_path)
    env = _environment(tmp_path, bin_dir)
    home = Path(env["HOME"])
    data = tmp_path / "cto-os-data"
    codex_config = Path(env["CODEX_HOME"]) / "config.toml"
    codex_config.parent.mkdir(parents=True)
    codex_config.write_text("model = []\n", encoding="utf-8")

    result = _run(repo, env, "--server", "--data-dir", str(data), "-y")
    assert result.returncode != 0
    assert "Codex rejected the existing config before install" in result.stderr
    assert not data.exists()
    assert not (repo / ".venv").exists()
    assert not (home / ".claude/skills/cto-os").exists()
    assert not (home / ".agents/skills/cto-os").exists()


def test_existing_server_migrates_exact_known_legacy_instructions(tmp_path: Path) -> None:
    repo = _installer_repo(tmp_path)
    bin_dir = _fake_commands(tmp_path)
    env = _environment(tmp_path, bin_dir)
    data = tmp_path / "cto-os-data"
    data.mkdir()
    shutil.copy2(REPO_ROOT / "tests/fixtures/legacy-data-CLAUDE-v1.md", data / "CLAUDE.md")

    result = _run(repo, env, "--server", "--data-dir", str(data), "-y")
    assert result.returncode == 0, result.stderr
    assert (data / "CLAUDE.md").read_text() == (repo / "templates/CLAUDE.md").read_text()
    assert "migrated known legacy instructions" in result.stdout
    assert (data / "AGENTS.md").is_symlink()


def test_existing_server_preserves_customized_instructions(tmp_path: Path) -> None:
    repo = _installer_repo(tmp_path)
    bin_dir = _fake_commands(tmp_path)
    env = _environment(tmp_path, bin_dir)
    data = tmp_path / "cto-os-data"
    data.mkdir()
    customized = "<!-- cto-os-data-marker -->\n# My customized instructions\n"
    (data / "CLAUDE.md").write_text(customized, encoding="utf-8")

    result = _run(repo, env, "--server", "--data-dir", str(data), "-y")
    assert result.returncode == 0, result.stderr
    assert (data / "CLAUDE.md").read_text() == customized
    assert "customized or from an unknown version; left unchanged" in result.stderr
    assert (data / "AGENTS.md").is_symlink()
