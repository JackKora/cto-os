# Installation Guide

CTO OS supports three topologies. Pick the one that matches how you want to use it, then follow the install steps for each machine involved.

---

## Topology comparison

| | Local only | Server + remote access | Server + client machine |
|---|---|---|---|
| **Best for** | Single machine, simple setup | Phone access, always-on jobs | Claude Code on laptop, data on server |
| `install.sh` flag | `--server` | `--server` on server | `--server` on server, `--client` on laptop |
| cto-os-data location | Local | Server | Server only |
| Caddy / TLS needed | No | Yes | Yes |
| Phone / Claude.ai mobile | No | Yes | Yes |
| Scheduled tasks | Manual / laptop cron | Server cron | Server cron |
| Claude Code | Direct file access | On server only | Remote MCP (no local data) |
| Sync / conflicts | N/A | N/A | None — single source of truth |

---

## Topology 1: Local only

**One machine. Data lives on your laptop. No remote access.**

This is the simplest path. Everything runs locally. Claude Desktop talks to the MCP server via stdio (subprocess). Claude Code accesses files directly. No Caddy, no bearer tokens, no port-forwarding.

```bash
./install.sh --server
```

That's it. Follow the post-install prompts to set `CTO_OS_DATA` and restart Claude Desktop.

To use Claude Code: `cd ~/cto-os-data && claude`

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

On any Claude client:

```json
{
  "mcpServers": {
    "cto-os": {
      "url": "https://korafam.duckdns.org/mcp",
      "headers": { "Authorization": "Bearer YOUR_RAW_TOKEN" }
    }
  }
}
```

Claude Code on the server still uses stdio (local) — it never goes through HTTP.

---

## Topology 3: Server + client machine (Claude Code on laptop)

**Data on server. Claude Code on laptop uses remote MCP — no sync, no conflicts.**

### Step 1 — Server install + remote access

Same as Topology 2 above: `./install.sh --server` on the server, then follow [docs/REMOTE_SETUP.md](REMOTE_SETUP.md).

### Step 2 — Client install on laptop

On the laptop:

```bash
./install.sh --client
```

You'll be prompted for:
- Remote MCP URL (e.g. `https://korafam.duckdns.org/mcp`)
- Bearer token (the raw token from Step 1, not the hash)

The installer:
- Creates `~/.claude/skills/cto-os` → local cto-os repo
- Writes `~/.claude/CLAUDE.md` with MCP-only instructions
- Configures both Claude Desktop and Claude Code to use the remote MCP

### Step 3 — Use Claude Code from anywhere

Launch Claude Code from any directory:

```bash
claude
```

The skill is loaded globally via `~/.claude/CLAUDE.md`. All data access goes through the remote MCP — no local `cto-os-data` needed.

---

## Re-running install

Both modes are idempotent. Re-run anytime to refresh the venv, update MCP config, or repair a broken symlink.

```bash
./install.sh --server   # re-run server install
./install.sh --client   # re-run client install (prompts for URL/token again)
./install.sh --client -y  # non-interactive; reads CTO_OS_REMOTE_URL and CTO_OS_BEARER_TOKEN from env
```

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
