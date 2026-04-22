# MCP tool contracts

Canonical spec for the Chat-facing MCP server at `mcp-server/server.py`. This file is the source of truth for tool signatures, response shapes, error semantics, and guardrails. Update it in lockstep with the server implementation.

Background and scope decisions live in [docs/SKILL_REPO.md → MCP server](./SKILL_REPO.md#mcp-server). This doc just nails the contracts.

---

## Transport and lifecycle

- **Transport:** stdio. Claude Desktop launches the server per session via `claude_desktop_config.json`.
- **Authentication:** none. Single-user, local-disk.
- **Environment:** reads `CTO_OS_DATA` on startup. Missing or empty → fail fast with a clear error before accepting any request.
- **Cold start target:** < 200ms. No persistent index, no warmup.
- **Concurrency:** serial per-process. MCP handles one request at a time over stdio.

---

## Path handling (applies to every path-taking tool)

Every tool that accepts a `path` parameter resolves and validates it identically.

**Convention for prose / SKILL.md.** When a doc, SKILL.md, or CLAUDE.md mentions a data-repo path, write it with the literal `cto-os-data/` prefix (e.g., `cto-os-data/modules/personal-os/state/goals.md`). Claude strips that prefix when calling the MCP tool, because tool paths are relative to `$CTO_OS_DATA`. The prefix is for humans and for the skill-reviewer's cross-reference check — without it, those paths would be mistaken for skill-repo paths and fail to resolve.

**Resolution algorithm:**

1. Reject absolute paths. Inputs must be relative to `$CTO_OS_DATA`.
2. Reject any path containing a `..` component (belt-and-braces; step 4 would catch it anyway).
3. Join with `$CTO_OS_DATA` and canonicalize via `os.path.realpath` (follows symlinks).
4. Assert the canonical path has `realpath($CTO_OS_DATA)` as a prefix. If not, reject.

Violations raise `PathOutsideRoot`.

Empty paths are rejected with `InvalidPath`.

---

## Tools

Six tools. Signatures and response shapes are stable; response keys are additive (new fields may be added in a backward-compatible way; existing fields don't get renamed without a version bump).

### `read_file(path)`

Read a single file.

**Parameters:**

- `path` (string, required): relative to `$CTO_OS_DATA`.

**Returns:** the file's UTF-8 text content as a string.

**Errors:**

- `PathOutsideRoot` — resolution failed validation.
- `PathNotFound` — file doesn't exist.
- `PathIsDirectory` — path is a directory, not a file.
- `BinaryFileError` — content is not valid UTF-8.

**Notes:**

- No size limit enforced in v1. Trust the caller. If files get huge in practice, add a 10MB cap and `FileTooLarge`.
- Returns raw content, not a JSON envelope. If metadata is needed, call `list_directory` on the parent.

### `write_file(path, content)`

Create or overwrite a file.

**Parameters:**

- `path` (string, required): relative to `$CTO_OS_DATA`.
- `content` (string, required): UTF-8 text. Binary writes not supported.

**Returns:**

```json
{
  "chars_written": 1234,
  "created": true
}
```

`created` is `true` when the file didn't exist before this call, `false` when it was overwritten.

**Errors:**

- `PathOutsideRoot`
- `ForbiddenPath` — the path resolves inside a machine-managed subtree that writes aren't allowed into (see Forbidden write prefixes below).
- `PathIsDirectory` — path resolves to an existing directory.
- `PermissionDenied` — filesystem denied the write.

**Notes:**

- Auto-creates parent directories as needed (`mkdir -p` behavior).
- `chars_written` is `len(content)` — Unicode code points, not bytes. Matches the caller's mental model; bytes can be recovered via `list_directory`.
- No file locking. MCP is serial per-process; bash scripts on other surfaces use direct I/O. Concurrent writes to the same file from two surfaces at the same millisecond are a theoretical, not observed, risk; revisit if it ever bites.
- Writes are not atomic (no temp-file rename dance). If atomicity matters for a specific file, handle it at a higher level.

**Forbidden write prefixes.** `write_file` and `append_to_file` refuse any path whose first component is in `{.git, logs, integrations-cache}`. These subtrees are machine-managed (git itself, the MCP log file, `pull_*` script output) and writes through these tools would cause confusing breakage. Reads of those paths are still permitted.

### `append_to_file(path, content, allow_create=True)`

Append to a file.

**Parameters:**

- `path` (string, required): relative to `$CTO_OS_DATA`.
- `content` (string, required): UTF-8 text.
- `allow_create` (bool, optional, default `true`): when `true`, a missing file is created along with any missing parent directories. When `false`, a missing file raises `PathNotFound` — useful when the caller wants to guarantee it's extending an existing artifact rather than silently creating a new file on a typo'd path.

**Returns:**

```json
{
  "chars_written": 120,
  "created": false
}
```

**Errors:**

- `PathOutsideRoot`
- `ForbiddenPath` — path is inside a machine-managed subtree (see `write_file` above).
- `PathNotFound` — `allow_create=false` and the file doesn't exist.
- `PathIsDirectory`
- `PermissionDenied`

**Notes:**

- **No auto-newline.** The caller controls separators exactly. If a newline is needed, pass `"\n"` as part of `content`.
- Opens with `O_APPEND` on POSIX. Small writes (< PIPE_BUF bytes on the filesystem) are atomic per the kernel — no lock needed.
- `chars_written` is `len(content)` (Unicode code points).
- Auto-creates parent directories only when `allow_create=true`.

### `list_directory(path, recursive=False)`

Enumerate entries in a directory.

**Parameters:**

- `path` (string, required): relative to `$CTO_OS_DATA`. Use `"."` for the root.
- `recursive` (bool, optional, default `false`): when `true`, traverse into subdirectories. Returned `name` values are paths relative to the requested `path`.

**Returns:** array of entries.

```json
[
  {"name": "modules/personal-os/_module.md", "type": "file", "size": 512, "mtime": "2026-04-21T10:15:32Z"},
  {"name": "modules/personal-os/state", "type": "directory", "mtime": "2026-04-21T09:02:11Z"}
]
```

Field semantics:

- `type`: `"file"` or `"directory"`. Symlinks are dereferenced.
- `size`: bytes, present for files only.
- `mtime`: ISO 8601 UTC with `Z` suffix.

**Symlinks pointing outside `$CTO_OS_DATA`** are silently dropped from the result. This is expected behavior, not an error — a symlink that escapes the root can't be safely traversed by any other tool either, so listing it would be misleading. The drop is logged at `INFO` (one line per omitted entry) so you can find them if a file you expected to see is missing. If you see a listing that feels short, check the log.

**Errors:**

- `PathOutsideRoot`
- `PathNotFound`
- `PathIsFile` — path is a file, not a directory.

**Notes:**

- Dotfiles and `.git` are included. Caller filters if desired.
- Result order: sorted lexicographically by `name` for determinism.

### `scan(query_spec)`

The workhorse. Frontmatter scan + filter over `$CTO_OS_DATA`.

**Parameters:** a single `query_spec` object.

```json
{
  "type": ["team", "1on1"],
  "where": {"status": "struggling", "date_gte": "2026-01-01"},
  "fields": ["slug", "lead", "scores.overall", "updated"],
  "include_body": false
}
```

All keys optional; an empty spec returns every file's frontmatter.

**Returns:** full spec (baseline, with-bodies, cap-hit variants) is in [docs/SKILL_REPO.md → Context loading](./SKILL_REPO.md#context-loading-scan-dont-cache). The MCP tool is a thin proxy to `scripts/scan.py` — it passes `query_spec` through as `--args '<json>'` and returns the script's JSON stdout unchanged.

**Exit-code contract for `scan.py`:**

- **Exit 0 for every structured result.** That includes successful matches *and* query errors (unknown field, bad type, malformed filter). Query errors surface as a structured error envelope inside the JSON, not as a non-zero exit.
- **Non-zero exit means the script crashed** (uncaught exception, missing file, OS error). MCP raises `ScriptFailed` only in this case.

**Errors:**

- `ScriptNotImplemented` — `scan.py` hasn't been built yet. Remove when it exists.
- `ScriptFailed` — `scan.py` crashed (non-zero exit).
- `ScriptTimeout` — exceeded 10 seconds.

### `run_script(name, args)`

Invoke a whitelisted script in `scripts/`.

**Parameters:**

- `name` (string, required): script name without `.py`. Must be in the whitelist (below).
- `args` (object, required): arbitrary JSON, passed to the script as `--args '<json-string>'`.

**Returns:**

```json
{
  "exit_code": 0,
  "stdout": "<script's stdout, unparsed>",
  "stderr": "<script's stderr, possibly empty>"
}
```

MCP does not parse `stdout`. Scripts emit JSON by contract; the caller (Claude) parses it.

**Errors:**

- `ScriptNotInWhitelist` — `name` is not in the allowed set. The `scan` tool is always refused here (use `scan` directly).
- `ScriptNotFound` — whitelisted but `scripts/{name}.py` doesn't exist on disk.
- `ScriptTimeout` — exceeded 10 seconds.
- `ScriptFailed` — does NOT raise on non-zero exit. `exit_code` in the return value signals failure; the caller decides what to do.

**Whitelist (v1):**

```python
RUN_SCRIPT_WHITELIST = {
  "roll_up",
  "validate_deps",
  "rename_module",
}
```

Not whitelisted:

- `scan` — has its own first-class tool. Always refused.
- `pull_slack`, `pull_linear` — network I/O, long-running, side-effect-bearing. Keep them to Code/Cowork surfaces where bash invocation is direct.
- `migrate_*` — destructive. Run via the schema evolution flow (skill-initiated, explicit).

Adding a script to the whitelist is a deliberate code change, not a config toggle. This prevents an accidental "Chat can run anything" surface.

---

## Error taxonomy

Every error raised by the MCP surface uses one of these codes. Messages include a human-readable description of the specific failure.

| Code | Meaning |
| --- | --- |
| `DataRootNotSet` | `$CTO_OS_DATA` missing or empty at startup. |
| `InvalidPath` | Path is empty, absolute, or contains `..`. |
| `PathOutsideRoot` | Canonicalized path isn't under `$CTO_OS_DATA`. |
| `ForbiddenPath` | Write attempted to a machine-managed subtree (`.git/`, `logs/`, `integrations-cache/`). Reads of those paths are fine. |
| `PathNotFound` | Path doesn't exist. |
| `PathIsDirectory` | Expected a file, got a directory. |
| `PathIsFile` | Expected a directory, got a file. |
| `BinaryFileError` | Content is not valid UTF-8. |
| `PermissionDenied` | Filesystem denied the operation. |
| `ScriptNotInWhitelist` | `run_script` called with a non-whitelisted name. |
| `ScriptNotFound` | Whitelisted but the file is missing on disk. |
| `ScriptNotImplemented` | The script file exists but is empty / stub. Remove this code once all scripts are implemented. |
| `ScriptTimeout` | Script exceeded 10 seconds. |
| `ScriptFailed` | `scan.py` crashed (non-zero exit). `run_script` never raises this — it returns the exit code in its result. |

Error messages include enough context to debug without needing a stack trace — e.g., `"PathOutsideRoot: /etc/passwd is not under /Users/you/cto-os-data"`, not just `"path error"`.

---

## Testing strategy

Implemented (handler-level, not transport-level). Run via `uv run pytest tests/`.

- **`tests/test_mcp_path.py`** — unit tests for `_resolve_path` and a parametrized escape-attempt battery (`/etc/passwd`, `..`, `foo/../../../etc`, escaping symlinks) run against every path-taking tool.
- **`tests/test_mcp_files.py`** — `read_file`, `write_file`, `append_to_file`. Covers: UTF-8 and non-ASCII content, binary rejection, empty content, auto-create parents, `chars_written` counts code points not bytes, no auto-newline on append, overwrite vs create semantics.
- **`tests/test_mcp_list.py`** — file/dir entries sort and structure, recursive traversal, escaping-symlink omission, dotfile inclusion, errors for file-path and missing path.
- **`tests/test_mcp_scripts.py`** — whitelist enforcement (scan refused, unknown refused, pull_* refused), `ScriptNotFound` / `ScriptNotImplemented` / `ScriptTimeout`, non-zero exit passthrough, stdout/stderr capture, scan JSON proxy + bad-JSON handling.
- **`tests/test_mcp_helpers.py`** — `_iso_z` format and roundtrip.
- **`tests/conftest.py`** — `data_root` and `scripts_dir` fixtures monkeypatch `server.DATA_ROOT` / `server.SCRIPT_DIR` to pytest `tmp_path`; silences real file logging.

Not yet covered:

- **End-to-end stdio transport.** Needs the MCP SDK's test client; deferred until we confirm API shape against a running server. Current handler-level coverage validates behavior; the transport wrap is thin.
- **Cold-start timing (< 200ms).** Measure manually until it matters.

---

## Logging

The server writes structured logs to a local file. Stdout is reserved for the MCP transport; stderr is reserved for crash output and anything that must surface when the log file can't be opened.

**Location:** `$CTO_OS_DATA/logs/mcp.log`. Lives alongside `integrations-cache/` — both are operational, regenerable, and not user state. Gitignored via the data-repo `.gitignore` (the install template includes `logs/`).

**Rotation:** `logging.handlers.TimedRotatingFileHandler` with `when='midnight'`, `backupCount=1`. Rotates daily at local midnight; keeps the current file plus one previous day. Coverage is always ≥ 24 hours.

**Format:** pipe-delimited, one event per line. Picked over space-delimited so `awk -F'|'` / `cut -d'|'` parse cleanly — messages contain spaces, and space-delimited would be ambiguous.

```
2026-04-21T10:15:32Z | INFO    | scan         | matched 3 files, include_body=true
2026-04-21T10:15:33Z | ERROR   | write_file   | PathOutsideRoot: /etc/passwd is not under /Users/jack/cto-os-data
```

Fields: ISO-8601 UTC timestamp, level (padded to 7 chars), tool name or `server` for lifecycle events (padded to 14 — fits the longest tool name, `append_to_file`), message. Python formatter: `"%(asctime)s | %(levelname)-7s | %(name)-14s | %(message)s"`.

**Levels:**

- `INFO` — every tool invocation (one line per call), lifecycle events (startup, shutdown).
- `WARNING` — recoverable anomalies (e.g., a `list_directory` result that omitted escaping symlinks).
- `ERROR` — failed tool calls. Error code + message. No stack traces at this level.
- `DEBUG` — verbose traces for development. Off by default; enable with `CTO_OS_MCP_LOG_LEVEL=DEBUG` in the env.

**What's NOT logged:** file contents, query bodies with free-text user data. Log structure (tool name, path, result counts, error codes) — not substance. Keeps the log from becoming a side-channel for sensitive state.

---

## Implementation notes

Minor but easy-to-miss.

- **Import budget.** Cold start < 200ms means lazy imports where it costs nothing. `subprocess` is stdlib (cheap). The MCP SDK may not be — measure on first build and lazy-import the tool handlers if needed.
- **Timeout enforcement.** Use `subprocess.run(..., timeout=10)`. On timeout, `subprocess.TimeoutExpired` becomes `ScriptTimeout`.
- **stdout/stderr encoding.** Read subprocess streams as bytes, decode UTF-8 with `errors="replace"` — don't crash the MCP because a script emitted a stray byte.
- **Python version.** 3.13+ per `pyproject.toml`. Use modern type hints (`list[str]`, `str | None`).
- **Dependencies** are managed via `uv` in `pyproject.toml` with `uv.lock` committed for reproducibility. The MCP server runs under the venv Python (`.venv/bin/python`) — that path is wired into `claude_desktop_config.json` by `install.sh`, so no PATH resolution is needed at Desktop launch time.
- **Stdout is the MCP transport.** Never `print()` anything. All diagnostics go to the log file (see Logging above). Stderr is for last-ditch messages when the log file itself can't be opened.
- **Log dir creation.** On startup, ensure `$CTO_OS_DATA/logs/` exists (mkdir -p). If it can't be created, emit a single stderr line and fall back to stderr logging for the session.
