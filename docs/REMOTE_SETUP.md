# Remote MCP Setup

> **New here?** See [docs/INSTALL.md](INSTALL.md) first for topology overview and which install mode to use.

This guide covers the server-side steps to expose the MCP server over HTTPS (Caddy + DuckDNS + launchd), and the client-side steps to connect a second machine via `./install.sh --client`. The server mac sits always-on at home; Caddy handles TLS; traffic reaches you via a DuckDNS hostname.

**Architecture:**

```
internet (443)
  └─► router port-forward → Caddy (TLS via Let's Encrypt)
        └─► localhost:8000 → FastMCP (auth middleware)
              └─► cto-os-data
```

---

## Prerequisites

- macOS on the server machine (the always-on Mac)
- `cto-os` installed and working locally (`./install.sh` already run)
- Router admin access
- DuckDNS account (free) with a hostname created (referred to as `YOUR_DOMAIN.duckdns.org` throughout this guide)
- Ports 80 and 443 available on the server Mac

---

## 1. Give the server Mac a static local IP

In your router's DHCP settings, assign a fixed IP to the server Mac by its MAC address. This ensures the port-forward doesn't break when leases renew. Note the IP — you'll use it in step 3.

---

## 2. DuckDNS: keep the hostname pointed at your home IP

DuckDNS maps `YOUR_DOMAIN.duckdns.org` to your home's public IP. Since most home ISPs rotate IPs, set up a cron job to keep it updated.

1. Log in at [duckdns.org](https://www.duckdns.org), create a hostname if you haven't, and copy your account token.

2. Add a cron job on the server Mac:
   ```bash
   crontab -e
   ```
   Add this line (replace `YOUR_DOMAIN` with your DuckDNS subdomain — just the part before `.duckdns.org` — and `YOUR_DUCKDNS_TOKEN` with your account token):
   ```
   */5 * * * * curl -s "https://www.duckdns.org/update?domains=YOUR_DOMAIN&token=YOUR_DUCKDNS_TOKEN&ip=" > /dev/null 2>&1
   ```
   This runs every 5 minutes and silently updates the IP if it changed.

3. Verify it's working:
   ```bash
   curl "https://www.duckdns.org/update?domains=YOUR_DOMAIN&token=YOUR_DUCKDNS_TOKEN&ip="
   # Should return: OK
   ```

---

## 3. Router: port-forward 443 to the server Mac

In your router's port-forwarding settings, create a rule:

| Field | Value |
|---|---|
| External port | 443 |
| Internal IP | *(server Mac's static LAN IP from step 1)* |
| Internal port | 443 |
| Protocol | TCP |

Also forward port 80 — Caddy uses it briefly for Let's Encrypt ACME challenges before redirecting all traffic to HTTPS.

| Field | Value |
|---|---|
| External port | 80 |
| Internal IP | *(server Mac's static LAN IP)* |
| Internal port | 80 |
| Protocol | TCP |

---

## 4. Install and configure Caddy

Caddy auto-provisions a TLS certificate from Let's Encrypt and terminates HTTPS, so FastMCP only sees local plain HTTP.

```bash
brew install caddy
```

Generate your Caddyfile from the template, replacing `YOUR_DOMAIN` with your real DuckDNS hostname:

```bash
# In the cto-os repo
sed "s/YOUR_DOMAIN/yourname.duckdns.org/" mcp-server/Caddyfile.template > mcp-server/Caddyfile
```

`mcp-server/Caddyfile` is gitignored — your domain stays local, never committed.

Then deploy it to Caddy's config location:

```bash
sudo mkdir -p /etc/caddy
sudo cp /path/to/cto-os/mcp-server/Caddyfile /etc/caddy/Caddyfile
```

Start Caddy as a system service (runs at boot, survives login/logout):

```bash
sudo brew services start caddy
```

Verify Caddy is running and the certificate issued:

```bash
sudo brew services list | grep caddy
# Should show: caddy  started

curl -I https://YOUR_DOMAIN.duckdns.org/
# Should return HTTP 404 (Caddy is up; MCP server not started yet)
```

> **Note:** Certificate issuance requires ports 80 and 443 to be reachable from the internet. If you get a TLS error on first start, check the port-forward and wait 60 seconds for Let's Encrypt to complete.

---

## 5. Generate a bearer token

You need two values: a **raw token** (used in Claude's config) and an **argon2 hash** (stored on the server).

From the `cto-os` repo directory:

```bash
# Step 1: generate the raw token — save this, you'll put it in Claude's config
uv run python -c "import secrets; print(secrets.token_urlsafe(32))"
# Example output: xK8mP2qR9vLnT4wY7jA1sD6fH0cE5bN3

# Step 2: hash it — paste YOUR_RAW_TOKEN from step 1
uv run python -c "from argon2 import PasswordHasher; import sys; print(PasswordHasher().hash(sys.argv[1]))" YOUR_RAW_TOKEN
# Example output: $argon2id$v=19$m=65536,t=3,p=4$...
```

Keep the raw token somewhere safe (password manager). You only need it when adding a new Claude client. The hash is what lives on the server.

---

## 6. Configure the server: environment variables

The server reads sensitive config from environment variables, not from files in the repo.

Add these two lines to `/etc/launchd.conf` (create it if it doesn't exist — this file sets env vars system-wide, available to launchd services):

```bash
sudo sh -c 'echo "setenv CTO_OS_DATA /path/to/your/cto-os-data" >> /etc/launchd.conf'
sudo sh -c 'echo "setenv CTO_OS_MCP_TOKEN_HASH \$argon2id\$v=19\$..." >> /etc/launchd.conf'
```

> **Alternative (recommended):** put the env vars directly in the launchd plist (step 7), which is more reliable and doesn't require the global `launchd.conf`.

---

## 7. Auto-start the MCP server at boot (launchd)

1. Copy the plist template:
   ```bash
   cp /path/to/cto-os/mcp-server/com.cto-os.mcp-server.plist.template \
      ~/Library/LaunchAgents/com.cto-os.mcp-server.plist
   ```

2. Edit the plist and replace the three placeholders:
   - `REPO_PATH` → absolute path to your `cto-os` repo (e.g. `/Users/jack/cto-os`)
   - `DATA_PATH` → absolute path to your `cto-os-data` dir (e.g. `/Users/jack/cto-os-data`)
   - `TOKEN_HASH` → the argon2 hash from step 5

   ```bash
   nano ~/Library/LaunchAgents/com.cto-os.mcp-server.plist
   ```

3. Load and start it:
   ```bash
   launchctl load ~/Library/LaunchAgents/com.cto-os.mcp-server.plist
   launchctl start com.cto-os.mcp-server
   ```

4. Verify it's running:
   ```bash
   launchctl list | grep cto-os
   # Should show a PID in the first column (non-zero = running)

   curl -s http://localhost:8000/mcp
   # Should return: {"error":"Unauthorized"} with HTTP 401
   ```

To reload after editing the plist:
```bash
launchctl unload ~/Library/LaunchAgents/com.cto-os.mcp-server.plist
launchctl load   ~/Library/LaunchAgents/com.cto-os.mcp-server.plist
```

---

## 8. Configure Claude clients

### Claude Desktop (remote machine)

In `~/Library/Application Support/Claude/claude_desktop_config.json`, add:

```json
{
  "mcpServers": {
    "cto-os": {
      "url": "https://YOUR_DOMAIN.duckdns.org/mcp",
      "headers": {
        "Authorization": "Bearer YOUR_RAW_TOKEN"
      }
    }
  }
}
```

Replace `YOUR_RAW_TOKEN` with the raw token from step 5.

### Claude on iOS / android (claude.ai)

In Claude's settings → Integrations → Add integration:

- **URL:** `https://YOUR_DOMAIN.duckdns.org/mcp`
- **Header name:** `Authorization`
- **Header value:** `Bearer YOUR_RAW_TOKEN`

### Claude Code CLI (remote machine)

Add to `~/.claude/settings.json` or the project `.claude/settings.json`:

```json
{
  "mcpServers": {
    "cto-os": {
      "url": "https://YOUR_DOMAIN.duckdns.org/mcp",
      "headers": {
        "Authorization": "Bearer YOUR_RAW_TOKEN"
      }
    }
  }
}
```

---

## 9. Verify end-to-end

```bash
# 1. No token → 401
curl -s -o /dev/null -w "%{http_code}" https://YOUR_DOMAIN.duckdns.org/mcp
# Expected: 401

# 2. Wrong token → 401
curl -s -o /dev/null -w "%{http_code}" https://YOUR_DOMAIN.duckdns.org/mcp \
     -H "Authorization: Bearer wrongtoken"
# Expected: 401

# 3. Six wrong tokens → 429 on the sixth
for i in {1..6}; do
  curl -s -o /dev/null -w "attempt $i: %{http_code}\n" https://YOUR_DOMAIN.duckdns.org/mcp \
       -H "Authorization: Bearer wrongtoken"
done
# Expected: 401 five times, then 429

# 4. Correct token → MCP handshake
curl -s https://YOUR_DOMAIN.duckdns.org/mcp \
     -H "Authorization: Bearer YOUR_RAW_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"jsonrpc":"2.0","method":"initialize","id":1,"params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1"}}}'
# Expected: JSON response with serverInfo
```

---

## Maintenance

**Rotate the token:** generate a new raw token + hash, update `TOKEN_HASH` in the plist, reload launchd, update all clients.

**View server logs:**
```bash
tail -f ~/cto-os-data/logs/mcp.log            # main structured log
tail -f ~/cto-os-data/logs/mcp-http.stderr.log # uvicorn stderr
```

**Check Caddy logs:**
```bash
sudo tail -f /var/log/caddy/access.log 2>/dev/null || journalctl -u caddy -f
```

**Update cto-os:**
```bash
git pull          # in cto-os repo
uv sync           # pick up any new deps
launchctl stop  com.cto-os.mcp-server
launchctl start com.cto-os.mcp-server
```

---

## 10. Client install (laptop / second machine)

To use Claude Code on a laptop with data on this server — no local `cto-os-data`, no sync, no conflicts — run the client installer on the laptop:

```bash
./install.sh --client
```

You'll be prompted for the remote MCP URL (`https://YOUR_DOMAIN.duckdns.org/mcp`) and the raw bearer token from step 5. The installer:

- Creates `~/.claude/skills/cto-os` → local cto-os repo
- Writes `~/.claude/CLAUDE.md` instructing Claude to use MCP for all data access
- Configures both Claude Desktop and Claude Code (`~/.claude/settings.json`) with the remote URL + token

After install, launch Claude Code from any directory — no need to `cd` into a data repo.
