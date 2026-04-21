#!/usr/bin/env bash
# CTO OS installer — bootstraps cto-os-data, installs skill symlink, writes MCP config.
# Idempotent: safe to re-run.

set -euo pipefail

# ---------- args ----------
DATA_DIR=""
ASSUME_YES=0

usage() {
  cat <<EOF
Usage: $(basename "$0") [options]

Options:
  --data-dir PATH   Path to cto-os-data directory
                    (default: prompt, with ~/cto-os-data as suggestion)
  -y, --yes         Non-interactive; accept defaults
  -h, --help        Show this help
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --data-dir)
      [[ $# -ge 2 ]] || { echo "Error: --data-dir requires a value" >&2; exit 2; }
      DATA_DIR="$2"; shift 2 ;;
    -y|--yes) ASSUME_YES=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown argument: $1" >&2; usage >&2; exit 2 ;;
  esac
done

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

# ---------- helpers ----------
die() { echo "Error: $*" >&2; exit 1; }
info() { echo "==> $*"; }

confirm() {
  local prompt="$1"
  if (( ASSUME_YES )); then return 0; fi
  read -r -p "$prompt [y/N] " reply
  [[ "$reply" =~ ^[Yy]$ ]]
}

# ---------- preflight ----------
info "Preflight checks"
command -v git >/dev/null || die "git not found"
command -v python3 >/dev/null || die "python3 not found (need >= 3.10)"

PY_OK="$(python3 -c 'import sys; print("yes" if sys.version_info >= (3,10) else "no")')"
[[ "$PY_OK" == "yes" ]] || die "python3 is older than 3.10"

[[ -d "$TEMPLATES_DIR" ]] || die "templates/ not found at $TEMPLATES_DIR"
for f in CLAUDE.md README.md gitignore; do
  [[ -f "$TEMPLATES_DIR/$f" ]] || die "missing template: $TEMPLATES_DIR/$f"
done

# ---------- configure git hooks path in this repo ----------
if git -C "$REPO_DIR" rev-parse --git-dir >/dev/null 2>&1; then
  if [[ -d "$REPO_DIR/hooks" ]]; then
    info "Configuring git hooks path in skill repo (core.hooksPath=hooks)"
    git -C "$REPO_DIR" config core.hooksPath hooks
  fi
fi

# ---------- resolve data dir ----------
DEFAULT_DATA_DIR="$HOME/cto-os-data"
if [[ -z "$DATA_DIR" ]]; then
  if (( ASSUME_YES )); then
    DATA_DIR="$DEFAULT_DATA_DIR"
  else
    read -r -p "Path for cto-os-data [$DEFAULT_DATA_DIR]: " input
    DATA_DIR="${input:-$DEFAULT_DATA_DIR}"
  fi
fi

# Expand leading ~
DATA_DIR="${DATA_DIR/#\~/$HOME}"
# Make absolute
[[ "$DATA_DIR" = /* ]] || DATA_DIR="$PWD/$DATA_DIR"

info "Data dir: $DATA_DIR"

# ---------- validate / create data dir ----------
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

# ---------- git init ----------
if [[ ! -d "$DATA_DIR/.git" ]]; then
  info "git init in $DATA_DIR"
  git -C "$DATA_DIR" init -q
fi

# ---------- copy templates (only if absent) ----------
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

# ---------- skill symlink ----------
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

# ---------- MCP config (merge) ----------
info "MCP config: $MCP_CONFIG"
mkdir -p "$(dirname "$MCP_CONFIG")"

MCP_CONFIG="$MCP_CONFIG" REPO_DIR="$REPO_DIR" DATA_DIR="$DATA_DIR" python3 <<'PY'
import json, os, sys
from pathlib import Path

path = Path(os.environ["MCP_CONFIG"])
repo = os.environ["REPO_DIR"]
data = os.environ["DATA_DIR"]

if path.exists():
    try:
        cfg = json.loads(path.read_text())
    except json.JSONDecodeError as e:
        sys.exit(f"  existing config is not valid JSON: {e}")
else:
    cfg = {}

cfg.setdefault("mcpServers", {})
cfg["mcpServers"]["cto-os"] = {
    "command": "python3",
    "args": [f"{repo}/mcp-server/server.py"],
    "env": {"CTO_OS_DATA": data},
}

path.write_text(json.dumps(cfg, indent=2) + "\n")
print(f"  updated mcpServers.cto-os")
PY

# ---------- shell rc hint (no auto-append) ----------
SHELL_NAME="$(basename "${SHELL:-bash}")"
case "$SHELL_NAME" in
  zsh)  RC_FILE="$HOME/.zshrc" ;;
  bash)
    if [[ "$PLATFORM" == "macos" ]]; then RC_FILE="$HOME/.bash_profile"
    else RC_FILE="$HOME/.bashrc"; fi
    ;;
  fish) RC_FILE="$HOME/.config/fish/config.fish" ;;
  *)    RC_FILE="<your shell rc>" ;;
esac

cat <<EOF

--------------------------------------------------------------------
Install complete.

Next steps (manual):

1. Export CTO_OS_DATA in your shell. Add to $RC_FILE:

     export CTO_OS_DATA="$DATA_DIR"

   (fish: \`set -Ux CTO_OS_DATA "$DATA_DIR"\`)

   Then open a new shell, or source the file.

2. Claude Desktop: quit and reopen so it picks up the new MCP server.

3. Cowork: grant project folder-scoped permission to:
     $DATA_DIR

4. Claude Code: \`cd "$DATA_DIR" && claude\` to use the skill.
--------------------------------------------------------------------
EOF
