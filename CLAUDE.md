# cto-os — skill repo

You are working on the **logic** side of CTO OS. This repo holds the MCP server, deterministic scripts, per-module skill definitions, canonical schema, and templates. It is paired with `cto-os-data`, a separate repo that holds user state.

**No user state ever lives here.** If a file would differ from user to user, it belongs in `cto-os-data`, not here.

## Where to read more

- `README.md` — overview, PRD, scope.
- `docs/ARCHITECTURE.md` — system-wide architecture (foundations, surfaces, storage, how the two repos connect, operations).
- `docs/SKILL_REPO.md` — deep dive on this repo (layout, MCP server, scripts, schema, patterns).
- `docs/DATA_REPO.md` — deep dive on the data repo (layout, module state, integrations cache).
- `docs/MCP_TOOLS.md` — canonical contracts for the Chat-facing MCP server (signatures, response shapes, errors, whitelist).

## Layout

```
cto-os/
├── README.md              # overview + PRD
├── CLAUDE.md              # this file
├── SKILL.md               # root skill (Chat/Cowork activation trigger)
├── install.sh             # bootstraps cto-os-data, installs skill, merges MCP config
├── pyproject.toml         # Python deps (managed via uv); requires-python = ">=3.13"
├── uv.lock                # uv lockfile; committed for reproducible installs
├── .venv/                 # gitignored; created by `uv sync` on install
├── docs/                  # mirrors of the Notion architecture pages
├── modules/               # one directory per PRD module — SKILL.md + README.md each
├── scripts/               # deterministic Python helpers (see Scripts below)
├── mcp-server/server.py   # MCP bridge for Claude Desktop
├── meta/schema.md         # canonical frontmatter schema (single source of truth)
├── templates/             # files install.sh copies into a new cto-os-data
├── hooks/pre-commit       # git hook that runs the skill-reviewer on staged SKILL/CLAUDE changes
├── .claude/agents/        # Claude Code subagent definitions (skill-reviewer)
└── tests/                 # pytest suite for the MCP server + skill-review checklist; scenarios/ is aspirational
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
- **Required dependencies form a DAG.** `scripts/validate_deps.py` is the intended enforcer (not yet implemented); it will fail on cycles. Optional dependencies may be bidirectional.
- **Bump `schema_version` and ship a migration when `meta/schema.md` changes.** Migration script lives at `scripts/migrate_{slug}_v{N}_to_v{N+1}.py`. Never mutate the schema without one.
- **Architectural changes update `docs/` in the same PR.** Notion is the discussion surface; the `docs/` mirrors are canonical.
- **Paths in scripts are relative to `CTO_OS_DATA`.** Never hardcode a path to the data repo; read `CTO_OS_DATA` from the environment.

## Scripts

All scripts live in `scripts/`. **None are implemented yet** — the files exist as empty placeholders. The contract below is what new scripts must satisfy when written:

- Accept JSON via a single `--args '{...}'` flag.
- Emit JSON on stdout.
- Read `CTO_OS_DATA` from the environment.
- Idempotent where possible (safe to re-run).

Surface-agnostic: Claude Desktop invokes them via the MCP `run_script` tool; Claude Code and Cowork invoke them directly via `uv run python scripts/{name}.py --args '{...}'` from the repo root. Same script, same contract. `uv run` handles venv resolution — don't activate `.venv` manually.

**Deps are managed by uv.** Runtime: `uv add <pkg>`. Dev: `uv add --dev <pkg>`. `uv.lock` is committed; never hand-edit it.

Current inventory:

- `scan.py` — the workhorse. Frontmatter scan + filter over all of `cto-os-data` in one call. Always prefer `scan` over reading N files in sequence.
- `roll_up.py` — on-demand rollups (teams, projects, people). Compact current-state tables.
- `pull_slack.py` — Slack API → `cto-os-data/integrations-cache/slack/`. TTL-aware, dedups on message ID.
- `pull_linear.py` — Linear GraphQL → `cto-os-data/integrations-cache/linear/`.
- `validate_deps.py` — intended: build the required-dependency DAG from each module's `SKILL.md` frontmatter; fail on cycles. When implemented, should be added to `hooks/pre-commit`.
- `rename_module.py` — renames a slug in lockstep across `cto-os/modules/` and `cto-os-data/modules/`.
- `migrate_{slug}_v{N}_to_v{N+1}.py` — per-module schema migrations. Commits a pre-migration snapshot to git before touching state; rollback = `git revert`.

Detailed contracts, MCP tool surface, and the scripts-vs-MCP decision rule live in `docs/SKILL_REPO.md`.

## Editing conventions

- **Prefer editing existing files over creating new ones.** The layout is deliberately flat.
- **Never introduce a new top-level directory** without updating `docs/ARCHITECTURE.md`, `docs/SKILL_REPO.md`, and this file's layout section.
- **A new script earns its existence** by being called more than 2–3 times, or by clearly winning the deterministic-offload decision rule in `docs/SKILL_REPO.md`. Otherwise keep it as skill prose + `scan`.
- **A new module =** `modules/{slug}/SKILL.md` + `modules/{slug}/README.md` + an entry in `README.md`'s module index.
- **Skill prose lives in `SKILL.md` files.** Never duplicate it into `README.md` or `CLAUDE.md`. These pointers stay thin.

## Testing

Four levels. Today only level 3 is wired up; levels 1, 2, 4 are the target.

**1. Script tests — pytest. Partial.** Run via `uv run pytest tests/`. MCP server has coverage (`tests/test_mcp_*.py`): path defense, file I/O, directory listing, script invocation + timeouts, whitelist enforcement, helpers. Scripts (`scan.py`, `roll_up.py`, etc.) are stubs with no tests yet. Add tests alongside each script as it lands. Fixtures in `tests/fixtures/cto-os-data-sample/` are still aspirational — current tests use pytest `tmp_path` directly.

**2. Skill behavior tests — scenarios. Not implemented.** Target: `tests/scenarios/` holds sample data-repo state plus a prompt plus the expected Claude response shape, reviewed manually.

**3. AI-assisted skill review. Implemented.** The `skill-reviewer` subagent (`.claude/agents/skill-reviewer.md`) applies the checklist at `tests/claude-review.md`. Fresh context per run. Invocations:

- **Pre-commit:** `hooks/pre-commit` calls `claude -p` headlessly and blocks the commit on `REVIEW: FAIL`. Triggered only when the staged diff includes `SKILL.md` or `CLAUDE.md`. Enabled by `install.sh` via `git config core.hooksPath hooks`. If the `claude` CLI isn't on PATH, the hook warns and skips.
- **On demand:** ask Claude Code to run the `skill-reviewer` subagent. Useful when writing or refactoring a module.

**4. Human review.** PR flow; solo review on fresh-eyes days. No CI gating today.

**When you change something, run the matching level.** Changing `SKILL.md` / `CLAUDE.md` → pre-commit fires level 3 automatically. Changing `meta/schema.md` → also bump `schema_version` and ship a migration (see Invariants above).

## Self-maintenance rules

When evolving this repo — apply these yourself, including when Claude Code is editing.

**Catch-all:** If a change alters how users or Claude interact with the system — installation, activation, persistence, the MCP/scripts contract, the skill-review checklist, or any convention documented in `docs/` — update `README.md` and the relevant `docs/*.md` files in the same commit. A change that's user-visible or contract-affecting is never complete without doc updates.

**Specific rules:**

- After **adding a module directory** under `modules/`: create its `SKILL.md` + `README.md`, add it to the module index in `README.md`.
- After **adding a script** to `scripts/`: add a one-line entry to the Scripts inventory above, add a one-line entry to `README.md`, and add a pytest in `tests/` (once the pytest suite exists).
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
