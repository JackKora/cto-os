# cto-os — skill repo

You are working on the **logic** side of CTO OS. This repo holds the MCP server, deterministic scripts, per-module skill definitions, canonical schema, and templates. It is paired with `cto-os-data`, a separate repo that holds user state.

**No user state ever lives here.** If a file would differ from user to user, it belongs in `cto-os-data`, not here.

## Where to read more

- `README.md` — overview, PRD, scope.
- `docs/ARCHITECTURE.md` — system-wide architecture (foundations, surfaces, storage, how the two repos connect, operations).
- `docs/SKILL_REPO.md` — deep dive on this repo (layout, MCP server, scripts, schema, patterns).
- `docs/DATA_REPO.md` — deep dive on the data repo (layout, module state, integrations cache).

## Layout

```
cto-os/
├── README.md              # overview + PRD
├── CLAUDE.md              # this file
├── SKILL.md               # root skill (Chat/Cowork activation trigger)
├── install.sh             # bootstraps cto-os-data, installs skill, merges MCP config
├── docs/                  # mirrors of the Notion architecture pages
├── modules/               # one directory per PRD module — SKILL.md + README.md each
├── scripts/               # deterministic Python helpers (see Scripts below)
├── mcp-server/server.py   # MCP bridge for Claude Desktop
├── meta/schema.md         # canonical frontmatter schema (single source of truth)
├── templates/             # files install.sh copies into a new cto-os-data
├── hooks/pre-commit       # git hook that runs the skill-reviewer on staged SKILL/CLAUDE changes
├── .claude/agents/        # Claude Code subagent definitions (skill-reviewer)
└── tests/                 # skill-review checklist; pytest + scenarios are aspirational
```

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

Surface-agnostic: Claude Desktop invokes them via the MCP `run_script` tool; Claude Code and Cowork invoke them directly via bash. Same script, same contract.

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

**1. Script tests — pytest. Not implemented.** Target: `pytest tests/` with fixtures in `tests/fixtures/cto-os-data-sample/`. No `pyproject.toml`, no suite, no fixtures exist. Build this out alongside the first real script.

**2. Skill behavior tests — scenarios. Not implemented.** Target: `tests/scenarios/` holds sample data-repo state plus a prompt plus the expected Claude response shape, reviewed manually.

**3. AI-assisted skill review. Implemented.** The `skill-reviewer` subagent (`.claude/agents/skill-reviewer.md`) applies the checklist at `tests/claude-review.md`. Fresh context per run. Invocations:

- **Pre-commit:** `hooks/pre-commit` calls `claude -p` headlessly and blocks the commit on `REVIEW: FAIL`. Triggered only when the staged diff includes `SKILL.md` or `CLAUDE.md`. Enabled by `install.sh` via `git config core.hooksPath hooks`. If the `claude` CLI isn't on PATH, the hook warns and skips.
- **On demand:** ask Claude Code to run the `skill-reviewer` subagent. Useful when writing or refactoring a module.

**4. Human review.** PR flow; solo review on fresh-eyes days. No CI gating today.

**When you change something, run the matching level.** Changing `SKILL.md` / `CLAUDE.md` → pre-commit fires level 3 automatically. Changing `meta/schema.md` → also bump `schema_version` and ship a migration (see Invariants above).

## Self-maintenance rules

When evolving this repo — apply these yourself, including when Claude Code is editing:

- After **adding a module directory** under `modules/`: create its `SKILL.md` + `README.md`, add it to the module index in `README.md`.
- After **adding a script** to `scripts/`: add a one-line entry to the Scripts inventory above, add a one-line entry to `README.md`, and add a pytest in `tests/` (once the pytest suite exists).
- After **renaming a convention or field** in `meta/schema.md`: bump the schema version, ship a migration (see invariants), update `docs/SKILL_REPO.md` if the convention is documented there.
- After **any architectural change**: update `docs/ARCHITECTURE.md` / `SKILL_REPO.md` / `DATA_REPO.md` in the same PR. Update this file's Layout section if directories changed.
- After **renaming a module slug**: use `scripts/rename_module.py` — never rename by hand; it must change in lockstep with `cto-os-data`.
