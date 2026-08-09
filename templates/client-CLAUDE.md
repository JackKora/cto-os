<!-- cto-os-client-marker -->
# CTO OS — client install

This machine has a **client install** of CTO OS. The `cto-os-data` directory lives on a remote server and is accessed exclusively through the `cto-os` MCP server over HTTPS.

## Critical: no local data

`cto-os-data` does **not** exist on this machine. Never use direct file tools (Read, Edit, Write, Bash) to access data paths — they will fail. All data access must go through the MCP tools listed below.

## MCP tools for data access

Use these for everything that would otherwise be a direct file operation:

| Tool | Use for |
|---|---|
| `read_file(path)` | Read a file from cto-os-data |
| `write_file(path, content)` | Create or overwrite a file |
| `append_to_file(path, content)` | Append to a file |
| `list_directory(path, recursive)` | Enumerate files (replaces `find`) |
| `scan(query_spec)` | Frontmatter search across all modules — primary discovery tool |
| `grep(pattern, path, recursive)` | Text search inside file bodies |
| `run_script(name, args)` | Run a server-side script (roll_up, zip_data, validate_deps, rename_module) |

All paths are relative to the root of `cto-os-data` on the server.

## What lives locally

- The skill definitions, symlinked from the local `cto-os` repo into the active host's user skill registry
- The MCP server config for Claude Desktop, Claude Code, and Codex — already wired by install

## What stays on the server

- All `cto-os-data` files and module state
- Git history and auto-commits (cron job on the server)
- Backups (`zip_data` via `run_script`)
- Scheduled pull jobs (Linear, Slack integrations)

Do not attempt git operations on `cto-os-data` from here — there is no local repo to operate on.

## Skill reference

Use the active `cto-os` skill directory. Its root `SKILL.md` provides system orientation, and `modules/{slug}/SKILL.md` contains each module's detailed workflow.
