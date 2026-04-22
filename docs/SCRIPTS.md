# Scripts

All scripts live in `scripts/` at the repo root. **Currently stubs** (empty placeholders). Each follows a common contract and gets invoked the same way across Chat, Code, and Cowork.

## Invocation

- **From Code or Cowork:** `uv run python scripts/{name}.py --args '{...}'` from the repo root.
- **From Chat (Claude Desktop via MCP):** via the `run_script` tool for whitelisted scripts, or the first-class `scan` tool for scan.

## Contract

- Accept JSON on the command line as `--args '{...}'`.
- Emit JSON on stdout.
- Read `CTO_OS_DATA` from the environment — never hardcode data-repo paths.
- Idempotent where possible (safe to re-run).

Details, including which scripts are whitelisted for Chat and the scan guardrails, live in [docs/SKILL_REPO.md → Scripts](./SKILL_REPO.md#scripts) and [docs/MCP_TOOLS.md](./MCP_TOOLS.md).

## Inventory

- **`scan.py`** — frontmatter scan + filter across all of `cto-os-data` in one call. The workhorse for any "find me files where X" query. Supports `include_body` for narrow lookups that want content, not just paths.
- **`roll_up.py`** — on-demand rollups (teams, projects, people). Compact current-state tables.
- **`pull_slack.py`** — Slack API pull into `cto-os-data/integrations-cache/slack/`. TTL-aware, deduplicates on message ID.
- **`pull_linear.py`** — Linear GraphQL pull into `cto-os-data/integrations-cache/linear/`.
- **`validate_deps.py`** — builds the required-dependency DAG from each module's `SKILL.md` frontmatter and fails on cycles.
- **`rename_module.py`** — renames a slug in lockstep across `cto-os/modules/` and `cto-os-data/modules/`. Never rename a module by hand.
- **`migrate_{slug}_v{N}_to_v{N+1}.py`** — per-module schema migrations. Commits a pre-migration snapshot to git before touching state; rollback = `git revert`.
