# Installation Guide

CTO OS supports three topologies. Pick the one that matches how you want to use it, then follow the install steps for each machine involved.

---

## Topology comparison

| | Local only | Server + remote access | Server + client machine |
|---|---|---|---|
| **Best for** | Single machine, simple setup | Phone access, always-on jobs | Claude Code or Codex on laptop, data on server |
| `install.sh` flag | `--server` | `--server` on server | `--server` on server, `--client` on laptop |
| cto-os-data location | Local | Server | Server only |
| Caddy / TLS needed | No | Yes | Yes |
| Phone / Claude.ai mobile | No | Yes | Yes |
| Scheduled tasks | Manual / laptop cron | Server cron | Server cron |
| Claude Code / Codex | Direct file access or local MCP | On server | Remote MCP (no local data) |
| Sync / conflicts | N/A | N/A | None — single source of truth |

---

## Topology 1: Local only

**One machine. Data lives on your laptop. No remote access.**

This is the simplest path. Everything runs locally. Claude Desktop and Codex are configured for the stdio MCP server; Claude Code and Codex can also access files directly. No Caddy, no bearer tokens, no port-forwarding.

```bash
./install.sh --server
```

That's it. Follow the post-install prompts to set `CTO_OS_DATA` for direct shell use and restart Claude Desktop or Codex so it reloads MCP configuration.

To use a local coding host, open `~/cto-os-data` in Claude Code or Codex. The installer creates `CLAUDE.md` plus `AGENTS.md -> CLAUDE.md`, so both receive the same data-repo instructions.

---

## Topology 2: Server + remote access (phone, Claude.ai)

**An always-on Mac holds the data. Phone and other Claude clients connect via HTTPS.**

### Step 1 — Server install

On the always-on Mac:

```bash
./install.sh --server
```

### Step 2 — Enable remote HTTP access

After the server install, do the additional setup in [docs/REMOTE_SETUP.md](REMOTE_SETUP.md):

1. DuckDNS: keep hostname pointing at your home IP
2. Router: port-forward 443 → server Mac
3. Caddy: auto-TLS reverse proxy to localhost:8000
4. Generate bearer token + hash
5. Launchd: start MCP server in HTTP mode (`--http`) at boot

### Step 3 — Configure remote clients (phone, other machines)

On any MCP client:

```json
{
  "mcpServers": {
    "cto-os": {
      "url": "https://YOUR_DOMAIN.duckdns.org/mcp",
      "headers": { "Authorization": "Bearer YOUR_RAW_TOKEN" }
    }
  }
}
```

Claude Code or Codex on the server can stay local; they do not need to go through HTTP.

---

## Topology 3: Server + client machine (Claude Code or Codex on laptop)

**Data on server. Claude Code or Codex on the laptop uses remote MCP — no sync, no conflicts.**

### Step 1 — Server install + remote access

Same as Topology 2 above: `./install.sh --server` on the server, then follow [docs/REMOTE_SETUP.md](REMOTE_SETUP.md).

### Step 2 — Client install on laptop

On the laptop:

```bash
./install.sh --client
```

You'll be prompted for:
- Remote MCP URL (e.g. `https://YOUR_DOMAIN.duckdns.org/mcp`)
- Bearer token (the raw token from Step 1, not the hash)

The installer:
- Creates `~/.claude/skills/cto-os` → local cto-os repo
- Creates `~/.agents/skills/cto-os` → the same local cto-os repo
- Installs a managed `~/.claude/CLAUDE.md` with MCP-only instructions and creates `~/.codex/AGENTS.md` as a symlink to it
- Configures Claude Desktop, Claude Code, and Codex to use the remote MCP

### Step 3 — Use Claude Code or Codex from anywhere

Launch either host from any directory:

```bash
claude
codex
```

The skill is loaded from the host's global registry and the managed global instructions require MCP for data access. No local `cto-os-data` is needed.

---

## Re-running install

Both modes are idempotent. Re-run anytime to refresh the venv and update managed MCP entries or instruction files. Correct config entries are content and filesystem-identity no-ops, config symlinks remain symlinks, and unrelated entries are preserved. The installer migrates only an exact known legacy data-repo instruction template; customized and unknown versions are preserved with a warning.

```bash
./install.sh --server   # re-run server install
./install.sh --client   # re-run client install (prompts for URL/token again)
./install.sh --client -y  # non-interactive; reads CTO_OS_REMOTE_URL and CTO_OS_BEARER_TOKEN from env
./install.sh --server --reviewer codex  # explicit hook runner: auto/claude/codex/none
```

Reviewer selection is explicit environment (`CTO_OS_REVIEWER`) first, then repo-local `git config cto-os.reviewer`, then `auto`. An ordinary rerun preserves an existing repo-local choice. `auto` prefers Claude for compatibility with existing installs and falls back to Codex.

The Codex CLI is not required to write `~/.codex/config.toml`. When it is available, install validates the existing configuration before any writes and validates the generated `cto-os` entry afterward. Without it, install completes with a warning that CLI validation was unavailable.

---

## Upgrading

```bash
git pull          # pull latest cto-os
uv sync           # refresh venv with any new deps
./install.sh --server   # or --client — safe to re-run
```

If running in HTTP mode on the server, restart the MCP server after upgrading:

```bash
launchctl stop  com.cto-os.mcp-server
launchctl start com.cto-os.mcp-server
```
