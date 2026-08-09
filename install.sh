#!/usr/bin/env bash
# CTO OS installer — two modes:
#   --server  bootstrap cto-os-data, install skill, wire local MCP (stdio)
#   --client  install skill locally, wire remote MCP (HTTPS bearer token)
# Idempotent: safe to re-run.

set -euo pipefail

# ---------- args ----------
MODE=""
DATA_DIR=""
ASSUME_YES=0
REVIEWER_ARG=""

usage() {
  cat <<EOF
Usage: $(basename "$0") --server [options]
       $(basename "$0") --client [options]

Modes:
  --server          This machine holds cto-os-data and runs the local MCP server.
                    Sets up cto-os-data, installs both skill symlinks, and wires
                    Claude Desktop and Codex to the local stdio MCP server.

  --client          This machine connects to a remote MCP server; no local data.
                    Installs both skill symlinks, writes shared client guidance,
                    and wires Claude Desktop, Claude Code, and Codex remotely.

Options:
  --data-dir PATH   (--server only) Path to cto-os-data directory.
                    Default: \$CTO_OS_DATA if set, otherwise ~/cto-os-data.
  --reviewer NAME   AI reviewer for the repo hook: auto, claude, codex, or none.
                    Existing repo-local choice is preserved when omitted.
  -y, --yes         Non-interactive; accept defaults.
  -h, --help        Show this help.

Environment variables (--client + -y mode):
  CTO_OS_REMOTE_URL     Remote MCP URL (e.g. https://YOUR_DOMAIN.duckdns.org/mcp).
  CTO_OS_BEARER_TOKEN   Raw bearer token for the remote MCP server.
  CTO_OS_REVIEWER       Reviewer override: auto, claude, codex, or none.

See docs/INSTALL.md for topology guidance (local-only vs server+remote vs server+client).
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --server) MODE="server"; shift ;;
    --client) MODE="client"; shift ;;
    --data-dir)
      [[ $# -ge 2 ]] || { echo "Error: --data-dir requires a value" >&2; exit 2; }
      DATA_DIR="$2"; shift 2 ;;
    --reviewer)
      [[ $# -ge 2 ]] || { echo "Error: --reviewer requires a value" >&2; exit 2; }
      REVIEWER_ARG="$2"; shift 2 ;;
    -y|--yes) ASSUME_YES=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown argument: $1" >&2; usage >&2; exit 2 ;;
  esac
done

if [[ -z "$MODE" ]]; then
  echo "Error: --server or --client is required." >&2
  usage >&2
  exit 1
fi

if [[ -n "$REVIEWER_ARG" && ! "$REVIEWER_ARG" =~ ^(auto|claude|codex|none)$ ]]; then
  echo "Error: --reviewer must be auto, claude, codex, or none" >&2
  exit 2
fi
if [[ -n "${CTO_OS_REVIEWER:-}" && ! "$CTO_OS_REVIEWER" =~ ^(auto|claude|codex|none)$ ]]; then
  echo "Error: CTO_OS_REVIEWER must be auto, claude, codex, or none" >&2
  exit 2
fi

# ---------- constants ----------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$SCRIPT_DIR"
TEMPLATES_DIR="$REPO_DIR/templates"
CLAUDE_SKILLS_SYMLINK="$HOME/.claude/skills/cto-os"
CODEX_SKILLS_SYMLINK="$HOME/.agents/skills/cto-os"
MARKER="<!-- cto-os-data-marker -->"
CLIENT_MARKER="<!-- cto-os-client-marker -->"
LEGACY_DATA_CLAUDE_SHA256="19ae6462505ab51cfee83cd28507163ea8c5f61dbcb96e31d6f12c4512847c17"
CODEX_HOME_DIR="${CODEX_HOME:-$HOME/.codex}"
CODEX_CONFIG="$CODEX_HOME_DIR/config.toml"
CODEX_GLOBAL_AGENTS="$CODEX_HOME_DIR/AGENTS.md"
INSTALL_WARNING_COUNT=0
CODEX_CLI_AVAILABLE=0
CODEX_CONFIG_VALIDATION="not validated (Codex CLI not found)"
CLAUDE_SKILL_STATUS="not attempted"
CODEX_SKILL_STATUS="not attempted"
CLIENT_INSTRUCTIONS_STATUS="not attempted"
CODEX_GUIDANCE_STATUS="not attempted"
CLAUDE_DESKTOP_CONFIG_STATUS="not attempted"
CLAUDE_CODE_CONFIG_STATUS="not attempted"
CODEX_CONFIG_STATUS="not attempted"
DATA_CODEX_INSTRUCTIONS_STATUS="not attempted"

# ---------- platform detection ----------
case "$(uname -s)" in
  Darwin)
    PLATFORM="macos"
    MCP_CONFIG="$HOME/Library/Application Support/Claude/claude_desktop_config.json"
    ;;
  Linux)
    PLATFORM="linux"
    MCP_CONFIG="${XDG_CONFIG_HOME:-$HOME/.config}/Claude/claude_desktop_config.json"
    ;;
  *)
    echo "Error: unsupported OS ($(uname -s)). macOS and Linux only." >&2
    exit 1
    ;;
esac

CLAUDE_CODE_CONFIG="$HOME/.claude/settings.json"
CLAUDE_CODE_CLAUDE_MD="$HOME/.claude/CLAUDE.md"

# ---------- helpers ----------
die() { echo "Error: $*" >&2; exit 1; }
info() { echo "==> $*"; }
warn() {
  echo "Warning: $*" >&2
  INSTALL_WARNING_COUNT=$((INSTALL_WARNING_COUNT + 1))
}

install_status_line() {
  local label="$1"
  local status="$2"
  local path="$3"
  printf '  %-18s [%s] %s\n' "$label:" "$status" "$path"
}

confirm() {
  local prompt="$1"
  if (( ASSUME_YES )); then return 0; fi
  read -r -p "$prompt [y/N] " reply
  [[ "$reply" =~ ^[Yy]$ ]]
}

ensure_symlink() {
  local link_path="$1"
  local target="$2"
  local label="$3"

  info "$label: $link_path"
  mkdir -p "$(dirname "$link_path")"

  if [[ -L "$link_path" ]]; then
    local current
    current="$(readlink "$link_path")"
    if [[ "$current" == "$target" ]]; then
      info "  already points at $target (ok)"
      return 0
    fi
    warn "$link_path points at $current, not $target; left unchanged"
    return 1
  fi

  if [[ -e "$link_path" ]]; then
    warn "$link_path exists and is not a symlink; left unchanged"
    return 1
  fi

  ln -s "$target" "$link_path"
  info "  created -> $target"
}

install_managed_file() {
  local source="$1"
  local destination="$2"
  local marker="$3"
  local label="$4"

  info "$label: $destination"
  mkdir -p "$(dirname "$destination")"

  if [[ -L "$destination" ]]; then
    warn "$destination is a symlink not managed by this installer; left unchanged"
    return 1
  fi

  if [[ -e "$destination" ]]; then
    if ! grep -qF "$marker" "$destination" 2>/dev/null; then
      warn "$destination exists without the CTO OS marker; left unchanged"
      return 1
    fi
    if cmp -s "$source" "$destination"; then
      info "  managed content is current (ok)"
      return 0
    fi
    local temp_file destination_mode
    destination_mode="$(DESTINATION_PATH="$destination" "$PREFLIGHT_PYTHON" <<'PY'
import os
import stat

print(format(stat.S_IMODE(os.stat(os.environ["DESTINATION_PATH"]).st_mode), "o"))
PY
)" || return 1
    temp_file="$(mktemp "$(dirname "$destination")/.cto-os-managed.XXXXXX")" || return 1
    if ! cp "$source" "$temp_file" || ! chmod "$destination_mode" "$temp_file" || ! mv -f "$temp_file" "$destination"; then
      rm -f "$temp_file"
      return 1
    fi
    info "  updated managed content"
    return 0
  fi

  cp "$source" "$destination"
  info "  written"
}

install_data_instructions() {
  local source="$TEMPLATES_DIR/CLAUDE.md"
  local destination="$DATA_DIR/CLAUDE.md"

  info "Data repo instructions: $destination"
  if [[ ! -e "$destination" && ! -L "$destination" ]]; then
    cp "$source" "$destination"
    info "  written"
    return
  fi
  if [[ -L "$destination" || ! -f "$destination" ]]; then
    warn "$destination is not a regular installer-managed file; left unchanged"
    return
  fi
  if cmp -s "$source" "$destination"; then
    info "  instructions are current (ok)"
    return
  fi

  local current_hash
  current_hash="$(INSTRUCTION_PATH="$destination" "$PREFLIGHT_PYTHON" <<'PY'
import hashlib
import os
from pathlib import Path

print(hashlib.sha256(Path(os.environ["INSTRUCTION_PATH"]).read_bytes()).hexdigest())
PY
)"
  if [[ "$current_hash" != "$LEGACY_DATA_CLAUDE_SHA256" ]]; then
    warn "$destination is customized or from an unknown version; left unchanged"
    return
  fi

  SOURCE_PATH="$source" DESTINATION_PATH="$destination" "$PREFLIGHT_PYTHON" <<'PY'
import os
import stat
import tempfile
from pathlib import Path

source = Path(os.environ["SOURCE_PATH"])
destination = Path(os.environ["DESTINATION_PATH"])
mode = stat.S_IMODE(destination.stat().st_mode)
fd, temp_name = tempfile.mkstemp(prefix=".CLAUDE.md.cto-os.", dir=destination.parent)
try:
    with os.fdopen(fd, "wb") as handle:
        handle.write(source.read_bytes())
    os.chmod(temp_name, mode)
    os.replace(temp_name, destination)
except Exception:
    Path(temp_name).unlink(missing_ok=True)
    raise
PY
  info "  migrated known legacy instructions"
}

# ---------- shared preflight ----------
preflight() {
  info "Preflight checks"
  command -v git >/dev/null || die "git not found"

  if ! command -v uv >/dev/null 2>&1; then
    cat >&2 <<'EOF'
Error: uv not found on PATH.

Python deps are managed via uv. Install it:

     curl -LsSf https://astral.sh/uv/install.sh | sh

Then re-run this script.
EOF
    exit 1
  fi

  [[ -f "$REPO_DIR/pyproject.toml" ]] || die "pyproject.toml not found at repo root"
  [[ -d "$TEMPLATES_DIR" ]] || die "templates/ not found at $TEMPLATES_DIR"

  PREFLIGHT_PYTHON="$(uv python find '>=3.12' 2>/dev/null)" || die "Python 3.12+ not found (uv could not resolve it)"
  [[ -x "$PREFLIGHT_PYTHON" ]] || die "resolved Python is not executable: $PREFLIGHT_PYTHON"

  # Validate every config this run may update before creating links, syncing the
  # venv, configuring git, or writing data. A malformed host config is a hard
  # stop: never make a partial install and then discover it cannot be merged.
  VALIDATE_CLAUDE_DESKTOP_CONFIG="$MCP_CONFIG"
  VALIDATE_CLAUDE_CODE_CONFIG=""
  if [[ "$MODE" == "client" ]]; then
    VALIDATE_CLAUDE_CODE_CONFIG="$CLAUDE_CODE_CONFIG"
  fi
  VALIDATE_CODEX_CONFIG="$CODEX_CONFIG"

  VALIDATE_CLAUDE_DESKTOP_CONFIG="$VALIDATE_CLAUDE_DESKTOP_CONFIG" \
  VALIDATE_CLAUDE_CODE_CONFIG="$VALIDATE_CLAUDE_CODE_CONFIG" \
  VALIDATE_CODEX_CONFIG="$VALIDATE_CODEX_CONFIG" \
    "$PREFLIGHT_PYTHON" <<'PY'
import json
import os
import sys
import tomllib
from pathlib import Path

for env_key in ("VALIDATE_CLAUDE_DESKTOP_CONFIG", "VALIDATE_CLAUDE_CODE_CONFIG"):
    raw_path = os.environ[env_key]
    if not raw_path:
        continue
    path = Path(raw_path)
    if not path.exists():
        continue
    try:
        value = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        sys.exit(f"existing config is not valid JSON: {path}: {exc}")
    if not isinstance(value, dict) or (
        "mcpServers" in value and not isinstance(value["mcpServers"], dict)
    ):
        sys.exit(f"existing config has an invalid mcpServers shape: {path}")

raw_codex_path = os.environ["VALIDATE_CODEX_CONFIG"]
if raw_codex_path:
    path = Path(raw_codex_path)
    if path.exists():
        try:
            value = tomllib.loads(path.read_text())
        except (OSError, tomllib.TOMLDecodeError) as exc:
            sys.exit(f"existing config is not valid TOML: {path}: {exc}")
        if "mcp_servers" in value and not isinstance(value["mcp_servers"], dict):
            sys.exit(f"existing config has an invalid mcp_servers shape: {path}")
        if "cto-os" in value.get("mcp_servers", {}) and not isinstance(
            value["mcp_servers"]["cto-os"], dict
        ):
            sys.exit(f"existing config has an invalid mcp_servers.cto-os shape: {path}")
PY

  if command -v codex >/dev/null 2>&1; then
    CODEX_CLI_AVAILABLE=1
    local codex_validation
    if ! codex_validation="$(codex mcp list 2>&1)"; then
      die "Codex rejected the existing config before install: $codex_validation"
    fi
  fi
}

# ---------- shared: venv ----------
build_venv() {
  info "Syncing Python deps via uv (creates .venv at repo root if needed)"
  (cd "$REPO_DIR" && uv sync)
  VENV_PYTHON="$REPO_DIR/.venv/bin/python"
  [[ -x "$VENV_PYTHON" ]] || die "uv sync completed but $VENV_PYTHON is missing or not executable"
}

# ---------- shared: repo + host registration ----------
install_skill_symlinks() {
  if ensure_symlink "$CLAUDE_SKILLS_SYMLINK" "$REPO_DIR" "Claude skill symlink"; then
    CLAUDE_SKILL_STATUS="ok"
  else
    CLAUDE_SKILL_STATUS="SKIPPED"
  fi
  if ensure_symlink "$CODEX_SKILLS_SYMLINK" "$REPO_DIR" "Codex skill symlink"; then
    CODEX_SKILL_STATUS="ok"
  else
    CODEX_SKILL_STATUS="SKIPPED"
  fi
}

configure_repo() {
  if ! git -C "$REPO_DIR" rev-parse --git-dir >/dev/null 2>&1; then
    return
  fi

  if [[ -d "$REPO_DIR/hooks" ]]; then
    info "Configuring git hooks path in skill repo (core.hooksPath=hooks)"
    git -C "$REPO_DIR" config core.hooksPath hooks
  fi

  local requested existing
  requested="${REVIEWER_ARG:-${CTO_OS_REVIEWER:-}}"
  existing="$(git -C "$REPO_DIR" config --local --get cto-os.reviewer || true)"

  if [[ -n "$requested" ]]; then
    git -C "$REPO_DIR" config --local cto-os.reviewer "$requested"
    info "Pre-commit reviewer: $requested"
  elif [[ -n "$existing" ]]; then
    info "Pre-commit reviewer: $existing (preserved)"
  else
    git -C "$REPO_DIR" config --local cto-os.reviewer auto
    info "Pre-commit reviewer: auto"
  fi
}

configure_codex_mcp() {
  local transport="$1"
  info "Codex MCP config ($transport): $CODEX_CONFIG"

  # Codex validates by reading its live config, so a generated candidate cannot
  # be validated at an alternate path without potentially changing relative-path
  # semantics. Keep an exact snapshot of the resolved target and restore it if
  # the CLI rejects the candidate.
  local rollback_snapshot
  rollback_snapshot="$(mktemp "${TMPDIR:-/tmp}/cto-os-codex-config.XXXXXX")" || die "could not create Codex config rollback snapshot"

  if ! CODEX_CONFIG="$CODEX_CONFIG" TRANSPORT="$transport" \
  DATA_DIR="${DATA_DIR:-}" REPO_DIR="$REPO_DIR" VENV_PYTHON="$VENV_PYTHON" \
  REMOTE_URL="${REMOTE_URL:-}" BEARER_TOKEN="${BEARER_TOKEN:-}" \
  CODEX_ROLLBACK_SNAPSHOT="$rollback_snapshot" \
    "$VENV_PYTHON" <<'PY'
import os
import base64
import json
import stat
import tempfile
from pathlib import Path

import tomlkit

logical_path = Path(os.environ["CODEX_CONFIG"])
path = logical_path.resolve(strict=False) if logical_path.is_symlink() else logical_path
path.parent.mkdir(parents=True, exist_ok=True)
transport = os.environ["TRANSPORT"]

original_bytes = path.read_bytes() if path.exists() else None
original = original_bytes.decode() if original_bytes is not None else None
snapshot = {
    "path": str(path),
    "existed": original_bytes is not None,
    "mode": stat.S_IMODE(path.stat().st_mode) if path.exists() else None,
    "content": base64.b64encode(original_bytes).decode() if original_bytes is not None else None,
    "changed": False,
}
snapshot_path = Path(os.environ["CODEX_ROLLBACK_SNAPSHOT"])
snapshot_path.write_text(json.dumps(snapshot), encoding="utf-8")
snapshot_path.chmod(0o600)

doc = tomlkit.parse(original) if original is not None else tomlkit.document()
if "mcp_servers" not in doc:
    doc["mcp_servers"] = tomlkit.table()
elif isinstance(doc["mcp_servers"], tomlkit.items.InlineTable):
    expanded_servers = tomlkit.table()
    for name, value in doc["mcp_servers"].items():
        expanded_servers[name] = value
    doc["mcp_servers"] = expanded_servers

server = tomlkit.table()
if transport == "stdio":
    server["command"] = os.environ["VENV_PYTHON"]
    server["args"] = [f'{os.environ["REPO_DIR"]}/mcp-server/server.py']
    environment = tomlkit.table()
    environment["CTO_OS_DATA"] = os.environ["DATA_DIR"]
    server["env"] = environment
elif transport == "remote":
    server["url"] = os.environ["REMOTE_URL"]
    headers = tomlkit.table()
    headers["Authorization"] = f'Bearer {os.environ["BEARER_TOKEN"]}'
    server["http_headers"] = headers
else:
    raise SystemExit(f"unsupported Codex MCP transport: {transport}")

doc["mcp_servers"]["cto-os"] = server
rendered = tomlkit.dumps(doc)
if original == rendered:
    print("  mcp_servers.cto-os is current (ok)")
    raise SystemExit(0)

snapshot["changed"] = True
snapshot_path.write_text(json.dumps(snapshot), encoding="utf-8")
mode = snapshot["mode"] if snapshot["mode"] is not None else 0o600
fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.cto-os.", dir=path.parent)
try:
    with os.fdopen(fd, "w") as handle:
        handle.write(rendered)
    os.chmod(temp_name, mode)
    os.replace(temp_name, path)
except Exception:
    Path(temp_name).unlink(missing_ok=True)
    raise
print("  updated mcp_servers.cto-os")
PY
  then
    rm -f "$rollback_snapshot"
    die "could not write Codex MCP configuration"
  fi

  if (( CODEX_CLI_AVAILABLE )); then
    if ! codex mcp get cto-os --json >/dev/null; then
      local rollback_error
      if ! rollback_error="$(CODEX_ROLLBACK_SNAPSHOT="$rollback_snapshot" "$VENV_PYTHON" <<'PY'
import base64
import json
import os
import tempfile
from pathlib import Path

snapshot_path = Path(os.environ["CODEX_ROLLBACK_SNAPSHOT"])
snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
if not snapshot["changed"]:
    raise SystemExit(0)

path = Path(snapshot["path"])
if snapshot["existed"]:
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.cto-os-restore.", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(base64.b64decode(snapshot["content"]))
        os.chmod(temp_name, snapshot["mode"])
        os.replace(temp_name, path)
    except Exception:
        Path(temp_name).unlink(missing_ok=True)
        raise
else:
    path.unlink(missing_ok=True)
PY
)"; then
        rm -f "$rollback_snapshot"
        die "Codex rejected the generated cto-os MCP configuration and the previous config could not be restored: $rollback_error"
      fi
      rm -f "$rollback_snapshot"
      die "Codex rejected the generated cto-os MCP configuration; restored the previous config"
    fi
    info "  validated with codex mcp get"
    CODEX_CONFIG_VALIDATION="validated by Codex CLI"
  else
    warn "codex CLI not found; wrote $CODEX_CONFIG but could not CLI-validate it"
  fi
  rm -f "$rollback_snapshot"
  CODEX_CONFIG_STATUS="ok"
}

# ---------- server install ----------
install_server() {
  for f in CLAUDE.md README.md gitignore; do
    [[ -f "$TEMPLATES_DIR/$f" ]] || die "missing template: $TEMPLATES_DIR/$f"
  done

  build_venv

  # resolve data dir
  if [[ -n "${CTO_OS_DATA:-}" ]]; then
    DEFAULT_DATA_DIR="$CTO_OS_DATA"
  else
    DEFAULT_DATA_DIR="$HOME/cto-os-data"
  fi
  if [[ -z "$DATA_DIR" ]]; then
    if (( ASSUME_YES )); then
      DATA_DIR="$DEFAULT_DATA_DIR"
    else
      read -r -p "Path for cto-os-data [$DEFAULT_DATA_DIR]: " input
      DATA_DIR="${input:-$DEFAULT_DATA_DIR}"
    fi
  fi
  DATA_DIR="${DATA_DIR/#\~/$HOME}"
  [[ "$DATA_DIR" = /* ]] || DATA_DIR="$PWD/$DATA_DIR"
  info "Data dir: $DATA_DIR"

  # validate / create data dir
  if [[ -e "$DATA_DIR" && ! -d "$DATA_DIR" ]]; then
    die "$DATA_DIR exists but is not a directory"
  fi
  if [[ -d "$DATA_DIR" ]]; then
    if [[ -f "$DATA_DIR/CLAUDE.md" ]] && grep -q "$MARKER" "$DATA_DIR/CLAUDE.md" 2>/dev/null; then
      info "Existing cto-os-data repo detected; re-running idempotently."
    elif [[ -z "$(ls -A "$DATA_DIR" 2>/dev/null)" ]]; then
      info "Directory is empty; will initialize."
    else
      die "$DATA_DIR exists and is not a cto-os-data repo. Refusing to write."
    fi
  else
    confirm "Create $DATA_DIR?" || die "Aborted."
    mkdir -p "$DATA_DIR"
  fi

  # git init
  if [[ ! -d "$DATA_DIR/.git" ]]; then
    info "git init in $DATA_DIR"
    git -C "$DATA_DIR" init -q
  fi

  # Install project instructions, migrating only the exact known legacy template.
  install_data_instructions
  if [[ ! -e "$DATA_DIR/README.md" ]]; then
    info "Writing $DATA_DIR/README.md"
    cp "$TEMPLATES_DIR/README.md" "$DATA_DIR/README.md"
  fi
  if [[ ! -e "$DATA_DIR/.gitignore" ]]; then
    info "Writing $DATA_DIR/.gitignore"
    cp "$TEMPLATES_DIR/gitignore" "$DATA_DIR/.gitignore"
  fi

  if ensure_symlink "$DATA_DIR/AGENTS.md" "CLAUDE.md" "Data repo Codex instructions"; then
    DATA_CODEX_INSTRUCTIONS_STATUS="ok"
  else
    DATA_CODEX_INSTRUCTIONS_STATUS="SKIPPED"
  fi

  install_skill_symlinks

  # MCP config — stdio
  info "MCP config (stdio): $MCP_CONFIG"
  mkdir -p "$(dirname "$MCP_CONFIG")"
  MCP_CONFIG="$MCP_CONFIG" REPO_DIR="$REPO_DIR" DATA_DIR="$DATA_DIR" VENV_PYTHON="$VENV_PYTHON" \
    "$VENV_PYTHON" <<'PY'
import json, os, stat, sys, tempfile
from pathlib import Path

logical_path = Path(os.environ["MCP_CONFIG"])
path = logical_path.resolve(strict=False) if logical_path.is_symlink() else logical_path
path.parent.mkdir(parents=True, exist_ok=True)
repo = os.environ["REPO_DIR"]
data = os.environ["DATA_DIR"]
venv_python = os.environ["VENV_PYTHON"]

original = None
if path.exists():
    try:
        original = path.read_text()
        cfg = json.loads(original)
    except json.JSONDecodeError as e:
        sys.exit(f"  existing config is not valid JSON: {e}")
else:
    cfg = {}

cfg.setdefault("mcpServers", {})
cfg["mcpServers"]["cto-os"] = {
    "command": venv_python,
    "args": [f"{repo}/mcp-server/server.py"],
    "env": {"CTO_OS_DATA": data},
}

rendered = json.dumps(cfg, indent=2) + "\n"
if original == rendered:
    print(f"  mcpServers.cto-os is current (python={venv_python})")
    raise SystemExit(0)

mode = stat.S_IMODE(path.stat().st_mode) if path.exists() else 0o600
fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.cto-os.", dir=path.parent)
try:
    with os.fdopen(fd, "w") as handle:
        handle.write(rendered)
    os.chmod(temp_name, mode)
    os.replace(temp_name, path)
except Exception:
    Path(temp_name).unlink(missing_ok=True)
    raise
print(f"  updated mcpServers.cto-os (python={venv_python})")
PY
  CLAUDE_DESKTOP_CONFIG_STATUS="ok"

  configure_codex_mcp stdio

  # shell rc hint
  SHELL_NAME="$(basename "${SHELL:-bash}")"
  case "$SHELL_NAME" in
    zsh)  RC_FILE="$HOME/.zshrc" ;;
    bash)
      if [[ "$PLATFORM" == "macos" ]]; then RC_FILE="$HOME/.bash_profile"
      else RC_FILE="$HOME/.bashrc"; fi ;;
    fish) RC_FILE="$HOME/.config/fish/config.fish" ;;
    *)    RC_FILE="<your shell rc>" ;;
  esac

  cat <<EOF

--------------------------------------------------------------------
Server install complete.

Host registration:
EOF
  install_status_line "Claude skill" "$CLAUDE_SKILL_STATUS" "$CLAUDE_SKILLS_SYMLINK"
  install_status_line "Codex skill" "$CODEX_SKILL_STATUS" "$CODEX_SKILLS_SYMLINK"
  install_status_line "Data repo Codex" "$DATA_CODEX_INSTRUCTIONS_STATUS" "$DATA_DIR/AGENTS.md"
  install_status_line "Claude Desktop MCP" "$CLAUDE_DESKTOP_CONFIG_STATUS" "$MCP_CONFIG"
  install_status_line "Codex MCP" "$CODEX_CONFIG_STATUS" "$CODEX_CONFIG ($CODEX_CONFIG_VALIDATION)"
  cat <<EOF

Next steps (manual):

1. Export CTO_OS_DATA in your shell. Add to $RC_FILE:

     export CTO_OS_DATA="$DATA_DIR"

   (fish: \`set -Ux CTO_OS_DATA "$DATA_DIR"\`)

   Then open a new shell, or source the file.

2. Claude Desktop: quit and reopen so it picks up the new MCP server.

   Codex: if installed, restart it as well. Config status: $CODEX_CONFIG_VALIDATION.

3. Cowork: grant project folder-scoped permission to:
     $DATA_DIR

4. Open \`$DATA_DIR\` in a host with an [ok] skill registration above.

For remote access (phone, other machines): see docs/REMOTE_SETUP.md.
--------------------------------------------------------------------
EOF
}

# ---------- client install ----------
install_client() {
  [[ -f "$TEMPLATES_DIR/client-CLAUDE.md" ]] || die "missing template: $TEMPLATES_DIR/client-CLAUDE.md"

  build_venv
  install_skill_symlinks

  # prompt for remote URL
  REMOTE_URL=""
  if (( ASSUME_YES )); then
    REMOTE_URL="${CTO_OS_REMOTE_URL:-}"
    [[ -n "$REMOTE_URL" ]] || die "--yes requires CTO_OS_REMOTE_URL env var to be set"
  else
    while [[ -z "$REMOTE_URL" ]]; do
      read -r -p "Remote MCP URL (e.g. https://YOUR_DOMAIN.duckdns.org/mcp): " REMOTE_URL
      [[ -n "$REMOTE_URL" ]] || echo "  URL is required."
    done
  fi

  # prompt for bearer token (masked)
  BEARER_TOKEN=""
  if (( ASSUME_YES )); then
    BEARER_TOKEN="${CTO_OS_BEARER_TOKEN:-}"
    [[ -n "$BEARER_TOKEN" ]] || die "--yes requires CTO_OS_BEARER_TOKEN env var to be set"
  else
    while [[ -z "$BEARER_TOKEN" ]]; do
      read -rs -p "Bearer token (input hidden): " BEARER_TOKEN
      echo
      [[ -n "$BEARER_TOKEN" ]] || echo "  Token is required."
    done
  fi

  # Install one managed client instruction file and point Codex at it.
  if install_managed_file \
    "$TEMPLATES_DIR/client-CLAUDE.md" \
    "$CLAUDE_CODE_CLAUDE_MD" \
    "$CLIENT_MARKER" \
    "Client instructions"; then
    CLIENT_INSTRUCTIONS_STATUS="ok"
    if ensure_symlink \
      "$CODEX_GLOBAL_AGENTS" \
      "$CLAUDE_CODE_CLAUDE_MD" \
      "Codex client instructions"; then
      CODEX_GUIDANCE_STATUS="ok"
    else
      CODEX_GUIDANCE_STATUS="SKIPPED"
    fi
  else
    CLIENT_INSTRUCTIONS_STATUS="SKIPPED"
    CODEX_GUIDANCE_STATUS="SKIPPED"
    warn "Codex client instruction link was not created because the canonical Claude instruction file is unmanaged"
  fi

  # write remote MCP config to Claude Desktop + Claude Code
  info "Claude Desktop MCP config: $MCP_CONFIG"
  mkdir -p "$(dirname "$MCP_CONFIG")"

  info "Claude Code MCP config:    $CLAUDE_CODE_CONFIG"
  mkdir -p "$(dirname "$CLAUDE_CODE_CONFIG")"

  REMOTE_URL="$REMOTE_URL" BEARER_TOKEN="$BEARER_TOKEN" \
  MCP_CONFIG="$MCP_CONFIG" CLAUDE_CODE_CONFIG="$CLAUDE_CODE_CONFIG" \
    "$VENV_PYTHON" <<'PY'
import json, os, stat, sys, tempfile
from pathlib import Path

url   = os.environ["REMOTE_URL"]
token = os.environ["BEARER_TOKEN"]
entry = {
    "url": url,
    "headers": {"Authorization": f"Bearer {token}"},
}

for env_key, label in [("MCP_CONFIG", "Claude Desktop"), ("CLAUDE_CODE_CONFIG", "Claude Code")]:
    logical_path = Path(os.environ[env_key])
    path = logical_path.resolve(strict=False) if logical_path.is_symlink() else logical_path
    path.parent.mkdir(parents=True, exist_ok=True)
    original = None
    if path.exists():
        try:
            original = path.read_text()
            cfg = json.loads(original)
        except json.JSONDecodeError as e:
            sys.exit(f"  {label} config is not valid JSON: {e}")
    else:
        cfg = {}
    cfg.setdefault("mcpServers", {})
    cfg["mcpServers"]["cto-os"] = entry
    rendered = json.dumps(cfg, indent=2) + "\n"
    if original == rendered:
        print(f"  {label} mcpServers.cto-os is current (url={url})")
        continue
    mode = stat.S_IMODE(path.stat().st_mode) if path.exists() else 0o600
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.cto-os.", dir=path.parent)
    try:
        with os.fdopen(fd, "w") as handle:
            handle.write(rendered)
        os.chmod(temp_name, mode)
        os.replace(temp_name, path)
    except Exception:
        Path(temp_name).unlink(missing_ok=True)
        raise
    print(f"  updated {label} mcpServers.cto-os (url={url})")
PY
  CLAUDE_DESKTOP_CONFIG_STATUS="ok"
  CLAUDE_CODE_CONFIG_STATUS="ok"

  configure_codex_mcp remote

  cat <<EOF

--------------------------------------------------------------------
Client install complete.

Install status:
EOF
  install_status_line "Claude skill" "$CLAUDE_SKILL_STATUS" "$CLAUDE_SKILLS_SYMLINK"
  install_status_line "Codex skill" "$CODEX_SKILL_STATUS" "$CODEX_SKILLS_SYMLINK"
  install_status_line "Client instructions" "$CLIENT_INSTRUCTIONS_STATUS" "$CLAUDE_CODE_CLAUDE_MD"
  install_status_line "Codex guidance" "$CODEX_GUIDANCE_STATUS" "$CODEX_GLOBAL_AGENTS"
  install_status_line "Claude Desktop MCP" "$CLAUDE_DESKTOP_CONFIG_STATUS" "$MCP_CONFIG"
  install_status_line "Claude Code MCP" "$CLAUDE_CODE_CONFIG_STATUS" "$CLAUDE_CODE_CONFIG"
  install_status_line "Codex MCP" "$CODEX_CONFIG_STATUS" "$CODEX_CONFIG ($CODEX_CONFIG_VALIDATION)"
  cat <<EOF

Next steps:

1. Claude Desktop: quit and reopen so it picks up the remote MCP.

2. Claude Code: launch from any directory. The [ok] entries above are available
   globally; skipped items were left unchanged. All cto-os-data access goes over
   the remote MCP.

3. Codex: if installed, launch from any directory when its [ok] skill and MCP
   entries above are present. Validation status: $CODEX_CONFIG_VALIDATION.

The bearer token is stored in plain text in the MCP config files above.
Treat those files with the same care as a password.
--------------------------------------------------------------------
EOF
}

# ---------- run ----------
preflight
configure_repo

case "$MODE" in
  server) install_server ;;
  client) install_client ;;
esac

if (( INSTALL_WARNING_COUNT > 0 )); then
  echo "" >&2
  echo "Install completed with $INSTALL_WARNING_COUNT warning(s); review the warnings above." >&2
fi
