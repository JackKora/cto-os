# Scripts

All scripts live in `scripts/` at the repo root. Each follows a common contract and gets invoked the same way across Chat, Code, and Cowork.

## Invocation

- **From Code or Cowork:** `uv run python scripts/{name}.py --args '{...}'` from the repo root.
- **From Chat (Claude Desktop via MCP):** via the `run_script` tool for whitelisted scripts, or the first-class `scan` tool for scan.

## Contract

- Accept JSON on the command line as `--args '{...}'`.
- Emit JSON on stdout.
- Read `CTO_OS_DATA` from the environment — never hardcode data-repo paths. (Exception: `validate_deps.py` operates on the skill repo itself and doesn't need `CTO_OS_DATA`.)
- Idempotent where possible (safe to re-run).

Exit-code semantics vary by script — see each script's docstring. Broadly:
- **`scan.py`**: exit 0 for every structured result (including query errors, which surface as an `error` field in the JSON). Non-zero only on crashes.
- **`validate_deps.py`**: exit 0 = clean, exit 1 = validation failure (cycle or unknown dep), exit 2 = operational crash.
- Other whitelisted scripts should follow `scan.py`'s model unless there's a reason not to.

Details, including which scripts are whitelisted for Chat and the scan guardrails, live in [docs/SKILL_REPO.md → Scripts](./SKILL_REPO.md#scripts) and [docs/MCP_TOOLS.md](./MCP_TOOLS.md).

## Inventory

- **`scan.py`** — frontmatter scan + filter across all of `cto-os-data` in one call. The workhorse for any "find me files where X" query. Supports `type`, `module`, `where` (with `_gte` / `_lte` / `_gt` / `_lt` suffix operators), `fields` projection, and `include_body` with `MAX_INLINE_MATCHES=5` / `MAX_BODY_BYTES=4096` guardrails. Default-excludes inactive modules and high-sensitivity files; callers opt in explicitly (`include_inactive`, `include_high_sensitivity`).
- **`validate_deps.py`** — walks `modules/*/SKILL.md`, builds the required-dep graph, fails on cycles or unknown required deps. Called by `hooks/pre-commit` whenever any module `SKILL.md` is staged. Also runnable on demand for debugging the graph.
- **`roll_up.py`** — on-demand cross-type aggregations. Three named rollups: `team-health` (all active teams + scores + retro counts), `per-person` (one direct report: profile + 1:1s + coaching + performance record + dev plan + PIP), `goal-progress` (company goals × work-mapping). Shells out to `scan.py` — keeps the subprocess contract as the interface. Adding a new rollup = adding a function to a dispatch dict.
- **`pull_linear.py`** — incremental pull of Linear issues into `cto-os-data/integrations-cache/linear/{timestamp}.json`. TTL-aware (see `scripts/lib/integrations.yaml`), watermark-based incremental on `updatedAt` with 5-min buffer, dedupes on issue ID. Reads `LINEAR_API_KEY` from env. Issues only; comments out of scope. Uses `urllib.request` from stdlib — no extra dep.
- **`pull_slack.py`** — incremental pull of Slack messages across bot-accessible channels, into `cto-os-data/integrations-cache/slack/{timestamp}.json`. TTL 240m default. Watermark per-channel on `ts`; dedupes on `(channel_id, ts)`. Resolves user IDs → names and channel IDs → names via `users.list` + `conversations.list`. Polls only channels where the bot is `is_member: true`. Reads `SLACK_BOT_TOKEN` from env (scopes required: `channels:history`, `groups:history`, `channels:read`, `groups:read`, `users:read`). Messages only.
- **`rename_module.py`** — renames a slug in lockstep across `cto-os/modules/` and `cto-os-data/modules/`. **Dry-run by default** — must explicitly pass `"dry_run": false` to commit. Refuses on dirty git working tree on either repo. Auto-rewrites module directory, SKILL.md `name:`, `_module.md` `module:`+`slug:`, sibling modules' `requires:`/`optional:`, README.md module index. Surfaces other textual references in a separate list (manual review) — doesn't auto-rewrite arbitrary text (false-positive risk).
- **`zip_data.py`** — produces a single zip archive of `$CTO_OS_DATA` for offsite backup. Includes `.git/` (history is part of the backup); excludes `logs/`, `integrations-cache/`, `.backups/`, `.DS_Store`, `.env*`. Writes to `$CTO_OS_DATA/.backups/cto-os-data-{timestamp}.zip` by default; optional `dest_path` (absolute) and `extra_excludes` args. Consumed by the `data-backup` module's `backup-to-drive` skill. Whitelisted for direct `run_script` invocation.
- **`migrate_{slug}_v{N}_to_v{N+1}.py`** — per-module schema migrations. Created on demand when a schema bumps. Commits a pre-migration snapshot to git before touching state; rollback = `git revert`.

## Tests

Each script has a test file at `tests/test_{script}.py` using the subprocess pattern — tests shell out to the script with real `--args '{...}'` invocations, asserting on exit code and parsed JSON stdout. This keeps tests aligned with the production contract rather than implementation details.

Run them:

```bash
uv run pytest tests/test_scan.py -v
uv run pytest tests/test_validate_deps.py -v
uv run pytest tests/ -q                  # full suite
```

Fixture for scan tests lives at `tests/fixtures/cto-os-data-sample/` — a miniature data repo with three modules of varying shapes (active/standard, active/high-sensitivity, inactive).

**When you add a new script:**
1. Write `scripts/{name}.py` following the contract above.
2. Write `tests/test_{name}.py` using the subprocess pattern (mirror `tests/test_scan.py`).
3. If the script has a pre-commit role, wire it into `hooks/pre-commit`.
4. If it should be callable from Chat (via MCP), add it to `RUN_SCRIPT_WHITELIST` in `mcp-server/server.py`.
5. Add a one-line entry to this file's Inventory and to `README.md`.
