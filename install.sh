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

usage() {
  cat <<EOF
Usage: $(basename "$0") --server [options]
       $(basename "$0") --client [options]

Modes:
  --server          This machine holds cto-os-data and runs the local MCP server.
                    Sets up cto-os-data, installs the skill symlink, and wires
                    Claude Desktop to the local stdio MCP server.

  --client          This machine connects to a remote MCP server; no local data.
                    Installs the skill symlink, writes ~/.claude/CLAUDE.md, and
                    wires both Claude Desktop and Claude Code to the remote server.

Options:
  --data-dir PATH   (--server only) Path to cto-os-data directory.
                    Default: \$CTO_OS_DATA if set, otherwise ~/cto-os-data.
  -y, --yes         Non-interactive; accept defaults.
  -h, --help        Show this help.

Environment variables (--client + -y mode):
  CTO_OS_REMOTE_URL     Remote MCP URL (e.g. https://YOUR_DOMAIN.duckdns.org/mcp).
  CTO_OS_BEARER_TOKEN   Raw bearer token for the remote MCP server.

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

# ---------- constants ----------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$SCRIPT_DIR"
TEMPLATES_DIR="$REPO_DIR/templates"
SKILLS_SYMLINK="$HOME/.claude/skills/cto-os"
MARKER="<!-- cto-os-data-marker -->"

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

confirm() {
  local prompt="$1"
  if (( ASSUME_YES )); then return 0; fi
  read -r -p "$prompt [y/N] " reply
  [[ "$reply" =~ ^[Yy]$ ]]
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
}

# ---------- shared: venv ----------
build_venv() {
  info "Syncing Python deps via uv (creates .venv at repo root if needed)"
  (cd "$REPO_DIR" && uv sync)
  VENV_PYTHON="$REPO_DIR/.venv/bin/python"
  [[ -x "$VENV_PYTHON" ]] || die "uv sync completed but $VENV_PYTHON is missing or not executable"
}

# ---------- shared: skill symlink ----------
install_symlink() {
  info "Skill symlink: $SKILLS_SYMLINK"
  mkdir -p "$(dirname "$SKILLS_SYMLINK")"

  if [[ -L "$SKILLS_SYMLINK" ]]; then
    current="$(readlink "$SKILLS_SYMLINK")"
    if [[ "$current" == "$REPO_DIR" ]]; then
      info "  already points at $REPO_DIR (ok)"
    else
      die "  exists but points elsewhere: $current (remove manually if intended)"
    fi
  elif [[ -e "$SKILLS_SYMLINK" ]]; then
    die "  exists and is not a symlink: $SKILLS_SYMLINK"
  else
    ln -s "$REPO_DIR" "$SKILLS_SYMLINK"
    info "  created"
  fi
}

# ---------- server install ----------
install_server() {
  for f in CLAUDE.md README.md gitignore; do
    [[ -f "$TEMPLATES_DIR/$f" ]] || die "missing template: $TEMPLATES_DIR/$f"
  done

  # configure git hooks in skill repo
  if git -C "$REPO_DIR" rev-parse --git-dir >/dev/null 2>&1; then
    if [[ -d "$REPO_DIR/hooks" ]]; then
      info "Configuring git hooks path in skill repo (core.hooksPath=hooks)"
      git -C "$REPO_DIR" config core.hooksPath hooks
    fi
  fi

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

  # copy templates (only if absent)
  for f in CLAUDE.md README.md; do
    if [[ ! -e "$DATA_DIR/$f" ]]; then
      info "Writing $DATA_DIR/$f"
      cp "$TEMPLATES_DIR/$f" "$DATA_DIR/$f"
    fi
  done
  if [[ ! -e "$DATA_DIR/.gitignore" ]]; then
    info "Writing $DATA_DIR/.gitignore"
    cp "$TEMPLATES_DIR/gitignore" "$DATA_DIR/.gitignore"
  fi

  install_symlink

  # MCP config — stdio
  info "MCP config (stdio): $MCP_CONFIG"
  mkdir -p "$(dirname "$MCP_CONFIG")"
  MCP_CONFIG="$MCP_CONFIG" REPO_DIR="$REPO_DIR" DATA_DIR="$DATA_DIR" VENV_PYTHON="$VENV_PYTHON" \
    "$VENV_PYTHON" <<'PY'
import json, os, sys
from pathlib import Path

path = Path(os.environ["MCP_CONFIG"])
repo = os.environ["REPO_DIR"]
data = os.environ["DATA_DIR"]
venv_python = os.environ["VENV_PYTHON"]

if path.exists():
    try:
        cfg = json.loads(path.read_text())
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

path.write_text(json.dumps(cfg, indent=2) + "\n")
print(f"  updated mcpServers.cto-os (python={venv_python})")
PY

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

Next steps (manual):

1. Export CTO_OS_DATA in your shell. Add to $RC_FILE:

     export CTO_OS_DATA="$DATA_DIR"

   (fish: \`set -Ux CTO_OS_DATA "$DATA_DIR"\`)

   Then open a new shell, or source the file.

2. Claude Desktop: quit and reopen so it picks up the new MCP server.

3. Cowork: grant project folder-scoped permission to:
     $DATA_DIR

4. Claude Code: \`cd "$DATA_DIR" && claude\` to use the skill.

For remote access (phone, other machines): see docs/REMOTE_SETUP.md.
--------------------------------------------------------------------
EOF
}

# ---------- client install ----------
install_client() {
  [[ -f "$TEMPLATES_DIR/client-CLAUDE.md" ]] || die "missing template: $TEMPLATES_DIR/client-CLAUDE.md"

  build_venv
  install_symlink

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

  # write client CLAUDE.md to ~/.claude/CLAUDE.md
  info "Client CLAUDE.md: $CLAUDE_CODE_CLAUDE_MD"
  mkdir -p "$(dirname "$CLAUDE_CODE_CLAUDE_MD")"
  if [[ -e "$CLAUDE_CODE_CLAUDE_MD" ]]; then
    if (( ASSUME_YES )); then
      die "$CLAUDE_CODE_CLAUDE_MD already exists. Refusing to overwrite in -y mode. Remove it manually or run interactively."
    fi
    if confirm "  $CLAUDE_CODE_CLAUDE_MD already exists. Overwrite?"; then
      cp "$TEMPLATES_DIR/client-CLAUDE.md" "$CLAUDE_CODE_CLAUDE_MD"
      info "  overwritten"
    else
      info "  skipped (keeping existing file)"
    fi
  else
    cp "$TEMPLATES_DIR/client-CLAUDE.md" "$CLAUDE_CODE_CLAUDE_MD"
    info "  written"
  fi

  # write remote MCP config to Claude Desktop + Claude Code
  info "Claude Desktop MCP config: $MCP_CONFIG"
  mkdir -p "$(dirname "$MCP_CONFIG")"

  info "Claude Code MCP config:    $CLAUDE_CODE_CONFIG"
  mkdir -p "$(dirname "$CLAUDE_CODE_CONFIG")"

  REMOTE_URL="$REMOTE_URL" BEARER_TOKEN="$BEARER_TOKEN" \
  MCP_CONFIG="$MCP_CONFIG" CLAUDE_CODE_CONFIG="$CLAUDE_CODE_CONFIG" \
    "$VENV_PYTHON" <<'PY'
import json, os, sys
from pathlib import Path

url   = os.environ["REMOTE_URL"]
token = os.environ["BEARER_TOKEN"]
entry = {
    "url": url,
    "headers": {"Authorization": f"Bearer {token}"},
}

for env_key, label in [("MCP_CONFIG", "Claude Desktop"), ("CLAUDE_CODE_CONFIG", "Claude Code")]:
    path = Path(os.environ[env_key])
    if path.exists():
        try:
            cfg = json.loads(path.read_text())
        except json.JSONDecodeError as e:
            sys.exit(f"  {label} config is not valid JSON: {e}")
    else:
        cfg = {}
    cfg.setdefault("mcpServers", {})
    cfg["mcpServers"]["cto-os"] = entry
    path.write_text(json.dumps(cfg, indent=2) + "\n")
    print(f"  updated {label} mcpServers.cto-os (url={url})")
PY

  cat <<EOF

--------------------------------------------------------------------
Client install complete.

What was configured:
  Skill symlink:    $SKILLS_SYMLINK → $REPO_DIR
  Claude Code:      $CLAUDE_CODE_CLAUDE_MD
  Claude Desktop:   $MCP_CONFIG
  Claude Code cfg:  $CLAUDE_CODE_CONFIG

Next steps:

1. Claude Desktop: quit and reopen so it picks up the remote MCP.

2. Claude Code: launch from any directory — the skill and MCP are
   configured globally. All cto-os-data access goes over the remote MCP.

The bearer token is stored in plain text in the MCP config files above.
Treat those files with the same care as a password.
--------------------------------------------------------------------
EOF
}

# ---------- run ----------
preflight

case "$MODE" in
  server) install_server ;;
  client) install_client ;;
esac
