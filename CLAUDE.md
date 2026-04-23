# cto-os — skill repo

You are working on the **logic** side of CTO OS. This repo holds the MCP server, deterministic scripts, per-module skill definitions, canonical schema, and templates. It is paired with `cto-os-data`, a separate repo that holds user state.

**No user state ever lives here.** If a file would differ from user to user, it belongs in `cto-os-data`, not here.

## Where to read more

- `README.md` — overview, PRD, scope.
- `docs/ARCHITECTURE.md` — system-wide architecture (foundations, surfaces, storage, how the two repos connect, operations).
- `docs/SKILL_REPO.md` — deep dive on this repo (layout, MCP server, scripts, schema, patterns).
- `docs/DATA_REPO.md` — deep dive on the data repo (layout, module state, integrations cache).
- `docs/MCP_TOOLS.md` — canonical contracts for the Chat-facing MCP server (signatures, response shapes, errors, whitelist).
- `docs/SCRIPTS.md` — inventory and contract for the deterministic scripts in `scripts/`.

## Layout

```
cto-os/
├── README.md              # overview + PRD
├── CLAUDE.md              # this file
├── SKILL.md               # root skill (description drives activation on all surfaces)
├── install.sh             # bootstraps cto-os-data, installs skill, merges MCP config
├── pyproject.toml         # Python deps (managed via uv); requires-python = ">=3.13"
├── uv.lock                # uv lockfile; committed for reproducible installs
├── .venv/                 # gitignored; created by `uv sync` on install
├── docs/                  # architecture, skill repo, data repo, MCP tools, scripts
├── modules/               # one directory per PRD module — SKILL.md + README.md each
├── scripts/               # deterministic Python helpers (see Scripts below)
├── mcp-server/server.py   # MCP bridge for Claude Desktop
├── meta/schema.md         # canonical frontmatter schema (single source of truth)
├── templates/             # files install.sh copies into a new cto-os-data
├── hooks/pre-commit       # git hook that runs the skill-reviewer on staged SKILL/CLAUDE changes
├── .claude/agents/        # Claude Code subagent definitions (skill-reviewer)
└── tests/                 # pytest suite + skill-review checklist
```

## Dev setup

If you're just working on the code (not installing the whole system for end use), skip `install.sh` and bring up the venv directly:

```bash
uv sync                        # creates .venv/, installs runtime + dev deps from pyproject.toml + uv.lock
uv run pytest tests/ -v        # runs the test suite
uv run python scripts/scan.py --args '{}'   # runs a script directly
```

`uv run` handles venv resolution — never activate `.venv` manually. Add deps with `uv add <pkg>` (runtime) or `uv add --dev <pkg>` (dev). `uv.lock` is the source of truth for pinned versions; commit any change to it alongside the `pyproject.toml` change that caused it.

Full system install (data repo, Desktop MCP config, symlink, hooks): `./install.sh`. Only needed when you want to actually use the skill via Chat / Cowork / Claude Code, not to develop on it.

## Conversation discipline

**Answer questions before acting. Never take action on a question — wait for explicit instruction.**

When the user asks a question — "should we do X?", "what about Y?", "how would Z work?", "is this the right pattern?", "will this cause problem P?" — the response is the answer. Not edits, not file writes, not commits. Stop after the answer.

Actions only start when the user explicitly says so: "do it," "go," "apply that," "make the change," or equivalent. A question is never a task, even when the answer makes a change seem obviously next. Wait.

This rule outranks any instinct to be helpful-by-doing.

## Key invariants

- **No user state in this repo.** Ever. User state = `cto-os-data`.
- **No secrets in this repo.** Ever. Secrets = macOS Keychain or a gitignored `.env` in the data repo.
- **Every module needs `SKILL.md` + `README.md`.** Under `modules/{slug}/`. The slug must match the slug in `cto-os-data/modules/{slug}/`.
- **Required dependencies form a DAG.** `scripts/validate_deps.py` enforces this — wired into `hooks/pre-commit`, fails on cycles or unknown required deps. Optional dependencies may be bidirectional (not validated).
- **Bump `schema_version` and ship a migration when `meta/schema.md` changes.** Migration script lives at `scripts/migrate_{slug}_v{N}_to_v{N+1}.py`. Never mutate the schema without one.
- **Architectural changes update `docs/` in the same PR.** Notion is the discussion surface; the `docs/` mirrors are canonical.
- **Paths in scripts are relative to `CTO_OS_DATA`.** Never hardcode a path to the data repo; read `CTO_OS_DATA` from the environment.

## Scripts

All scripts live in `scripts/`. The shared contract — every script must satisfy this:

- Accept JSON via a single `--args '{...}'` flag.
- Emit JSON on stdout.
- Read `CTO_OS_DATA` from the environment.
- Idempotent where possible (safe to re-run).

Surface-agnostic: Claude Desktop invokes them via the MCP `run_script` tool; Claude Code and Cowork invoke them directly via `uv run python scripts/{name}.py --args '{...}'` from the repo root. Same script, same contract. `uv run` handles venv resolution — don't activate `.venv` manually.

**Deps are managed by uv.** Runtime: `uv add <pkg>`. Dev: `uv add --dev <pkg>`. `uv.lock` is committed; never hand-edit it.

Inventory:

- **`scan.py`** — frontmatter scan + filter over all of `cto-os-data` in one call. Supports `type`, `where`, `module`, `fields`, `include_body`, and opt-in flags for inactive / high-sensitivity modules. Enforces the `MAX_INLINE_MATCHES=5` / `MAX_BODY_BYTES=4096` guardrails. Always prefer `scan` over reading N files in sequence. Tests: `tests/test_scan.py` (fixture at `tests/fixtures/cto-os-data-sample/`).
- **`validate_deps.py`** — walks `modules/*/SKILL.md`, builds the required-dep graph, fails on cycles or unknown required deps. Called by `hooks/pre-commit` whenever any module `SKILL.md` is staged. Tests: `tests/test_validate_deps.py`.
- **`roll_up.py`** — on-demand cross-type aggregations. Three named rollups: `team-health` (all active teams + scores + retro counts), `per-person` (one direct report + 1:1s + coaching + perf record + dev plan + PIP), `goal-progress` (company goals × work-mapping join, flags unmapped goals). Adding a new rollup = adding a function to a dispatch dict. Tests: `tests/test_roll_up.py`.
- **`pull_linear.py`** — incremental pull of Linear issues → `cto-os-data/integrations-cache/linear/{timestamp}.json`. TTL-aware (configured in `scripts/lib/integrations.yaml`), watermark-based incremental (`updatedAt` minus 5-min buffer), dedups on issue ID. Reads `LINEAR_API_KEY` from env. Uses `urllib.request` (stdlib, no extra dep). Issues only; comments out of scope. Tests: `tests/test_pull_linear.py` (mocks `urlopen`).
- **`pull_slack.py`** — incremental pull of Slack messages across bot-accessible channels → `cto-os-data/integrations-cache/slack/{timestamp}.json`. TTL-aware (240m default), watermark per-channel on `ts`, dedups on `(channel_id, ts)`. Resolves user + channel IDs to names inline. Polls only channels where `is_member: true`. Reads `SLACK_BOT_TOKEN` from env (bot scopes required: `channels:history`, `groups:history`, `channels:read`, `groups:read`, `users:read`). Messages only. Tests: `tests/test_pull_slack.py` (mocks `urlopen`).
- **`rename_module.py`** — renames a slug in lockstep across `cto-os/modules/` and `cto-os-data/modules/`. Dry-run by default — requires `"dry_run": false` to commit. Refuses on dirty git working tree on either repo. Auto-rewrites: module dir, SKILL.md `name:`, `_module.md` `module:`/`slug:`, sibling modules' `requires:`/`optional:`, README.md module-index paths. Surfaces other textual references for manual review (doesn't auto-rewrite — risk of false positives). Tests: `tests/test_rename_module.py`.
- `migrate_{slug}_v{N}_to_v{N+1}.py` — per-module schema migrations. Created on demand when a schema bumps. Commits a pre-migration snapshot to git before touching state; rollback = `git revert`.

Detailed contracts, MCP tool surface, and the scripts-vs-MCP decision rule live in `docs/SKILL_REPO.md`.

## Editing conventions

- **Prefer editing existing files over creating new ones.** The layout is deliberately flat.
- **Never introduce a new top-level directory** without updating `docs/ARCHITECTURE.md`, `docs/SKILL_REPO.md`, and this file's layout section.
- **A new script earns its existence** by being called more than 2–3 times, or by clearly winning the deterministic-offload decision rule in `docs/SKILL_REPO.md`. Otherwise keep it as skill prose + `scan`.
- **A new module =** `modules/{slug}/SKILL.md` + `modules/{slug}/README.md` + an entry in `README.md`'s module index.
- **Skill prose lives in `SKILL.md` files.** Never duplicate it into `README.md` or `CLAUDE.md`. These pointers stay thin.

## Testing

Two layers: pytest for scripts + MCP, and an AI-assisted skill review for prose.

### Script and MCP tests — pytest

Run the full suite:

```bash
uv run pytest tests/ -v          # verbose output
uv run pytest tests/ -q          # quick summary
uv run pytest tests/test_scan.py # single file
```

Coverage:

- **`tests/test_mcp_*.py`** — the MCP server (path defense, file I/O, directory listing, script invocation with timeouts, whitelist enforcement, helpers).
- **`tests/test_scan.py`** — the `scan` workhorse (type/where/fields/module filters, `include_body` with cap + truncation, sensitivity and active filtering, query-error envelope, crash paths). Uses the fixture at `tests/fixtures/cto-os-data-sample/`.
- **`tests/test_validate_deps.py`** — the dep-graph validator (clean graphs, direct/transitive cycles, unknown deps, optional cycles permitted, malformed input crashes).
- **`tests/test_roll_up.py`** — named rollups (team-health, per-person, goal-progress) against the fixture. Synthesizes additional fixture for goal-progress scenario.
- **`tests/test_pull_linear.py`** — Linear pull with mocked `urlopen`: TTL skip, force override, watermark incremental, dedup, HTTP errors, GraphQL errors.
- **`tests/test_pull_slack.py`** — Slack pull with mocked `urlopen`, dispatched across `conversations.list` / `users.list` / `conversations.history`: TTL skip, force override, watermark per-channel, dedup on (channel, ts), `ok: false` errors, HTTP errors, channel filter.
- **`tests/test_rename_module.py`** — synthetic skill + data repos in `tmp_path`; dry-run vs. commit, dirty-tree refusal, slug collision refusal, unmodified-reference scan.

**When changing a script:**
- Run its test file: `uv run pytest tests/test_<script>.py`.
- If behavior changes or new cases are introduced, add tests in the same file.
- If the change touches how scan reads module state (sensitivity, active, types), update the fixture at `tests/fixtures/cto-os-data-sample/` to cover the new behavior, and add assertions that exercise it.

**When adding a new module:**
- The fixture at `tests/fixtures/cto-os-data-sample/` does NOT need to include every real module. It exists to exercise scan behavior across a few representative shapes (one active+standard, one active+high-sensitivity, one inactive). Only update it when the new module introduces a *shape* the fixture doesn't already cover — e.g., a novel frontmatter pattern a scan filter needs to exercise.

**When adding a new script:**
- Create `tests/test_<script>.py` following the subprocess pattern in `tests/test_scan.py` (JSON args in, JSON stdout out, `CTO_OS_DATA` env). Test the contract at the process boundary, not by importing.
- Add a one-line entry to the Scripts inventory above + `README.md`.
- If the script has a pre-commit role, wire it into `hooks/pre-commit`.

### AI-assisted skill review

The `skill-reviewer` subagent (`.claude/agents/skill-reviewer.md`) applies the checklist at `tests/claude-review.md`. Fresh context per run. Invocations:

- **Pre-commit:** `hooks/pre-commit` calls `claude -p` headlessly and blocks the commit on `REVIEW: FAIL`. Triggered when the staged diff includes `SKILL.md` or `CLAUDE.md`. Enabled by `install.sh` via `git config core.hooksPath hooks`. If the `claude` CLI isn't on PATH, the hook warns and skips.
- **Alongside pre-commit:** the same hook also runs `validate_deps.py` whenever any `modules/**/SKILL.md` is staged. That check blocks the commit on any required-dep cycle or unknown-dep reference. Unlike skill-reviewer, it does not skip if `claude` is missing — it only requires `uv`.
- **On demand:** ask Claude Code to run the `skill-reviewer` subagent. Useful when writing or refactoring a module. Run `validate_deps.py` directly with `uv run python scripts/validate_deps.py` when you want the graph report without a commit.

### When you change something, run the matching check

- Changing `scripts/<name>.py` → `uv run pytest tests/test_<script>.py`.
- Changing `mcp-server/server.py` → `uv run pytest tests/test_mcp_*.py`.
- Changing any module's `SKILL.md` → pre-commit fires `validate_deps.py` (deps) + skill-reviewer (qualitative) automatically. To preview before commit, run either manually.
- Changing `CLAUDE.md` → pre-commit fires skill-reviewer.
- Changing `meta/schema.md` → also bump `schema_version` for the affected type(s) and ship a migration (see Invariants).
- Changing `tests/fixtures/cto-os-data-sample/` → run `uv run pytest tests/test_scan.py` to catch fixture-dependent failures.

## Self-maintenance rules

When evolving this repo — apply these yourself, including when Claude Code is editing.

**Catch-all:** If a change alters how users or Claude interact with the system — installation, activation, persistence, the MCP/scripts contract, the skill-review checklist, or any convention documented in `docs/` — update `README.md` and the relevant `docs/*.md` files in the same commit. A change that's user-visible or contract-affecting is never complete without doc updates.

**Specific rules:**

- After **adding a module directory** under `modules/`: create its `SKILL.md` + `README.md`, add it to the module index in `README.md`, and declare any new frontmatter types in `meta/schema.md`.
- After **adding a script** to `scripts/`: add a one-line entry to the Scripts inventory above, add a one-line entry to `README.md`, and add a pytest in `tests/` following the subprocess pattern.
- After **renaming a convention or field** in `meta/schema.md`: bump the schema version, ship a migration (see invariants), update `docs/SKILL_REPO.md` if the convention is documented there.
- After **any architectural change**: update `docs/ARCHITECTURE.md` / `SKILL_REPO.md` / `DATA_REPO.md` in the same PR. Update this file's Layout section if directories changed.
- After **renaming a module slug**: use `scripts/rename_module.py` — never rename by hand; it must change in lockstep with `cto-os-data`.
- After **changing the root `SKILL.md`** (description, module map, or posture): audit `README.md`'s module index and `docs/SKILL_REPO.md`'s skill-definitions section for drift.
- After **adding a file to `templates/`**: distinguish which kind it is:
  - **Install-time template** (copied into a new `cto-os-data` by `install.sh`, e.g., `CLAUDE.md`, `README.md`, `gitignore`): update `install.sh` to copy it, and list it in `README.md` under what a fresh `cto-os-data` contains.
  - **Module-authoring template** (used when drafting a new module, e.g., `module-SKILL.md`, `module-README.md`): reference it from the module-authoring pointer in `README.md`; do not add to `install.sh`.
- After **adding a hook to `hooks/`**: update `install.sh` if wiring is needed, add it to `README.md`, and reference it in this file's Testing section if it runs the skill-reviewer or any other checks.
- After **adding a subagent under `.claude/agents/`**: name and describe it in this file's Testing section (if review-related) or a dedicated section, and list it in `README.md`.
- After **changing `install.sh` behavior** (new flag, new prompt, new side effect): update the install instructions in `README.md`.
- After **changing `tests/claude-review.md`**: if the change alters what the skill-reviewer fails on, reflect it in this file's Testing section.
- After **adding or upgrading a Python dep**: use `uv add` / `uv add --dev`, never hand-edit `pyproject.toml` or `uv.lock`. Commit both `pyproject.toml` and `uv.lock` in the same commit.
