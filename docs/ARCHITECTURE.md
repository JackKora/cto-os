# CTO OS — Architecture

Companion to the [PRD](https://www.notion.so/dscout/CTO-OS-product-requirements-34617a66c83d80358e71c722924cde93). The PRD defines *what* modules exist and *how* they compose. This doc defines *how the system is built*.

The system is split across two repos — `cto-os` (logic) and `cto-os-data` (your personal state). This page covers what spans both. Deep dives for each live in:

- [CTO OS — Skill repo (cto-os)](./SKILL_REPO.md)
- [CTO OS — Data repo (cto-os-data)](./DATA_REPO.md)

---

# Foundations

## Design goals (in priority order)

1. **Latency efficiency.** Anything deterministic runs as Python or bash, not as an LLM round-trip. The LLM's job is judgment; scripts do the counting.
2. **Token efficiency.** The active host reads the smallest slice of state that answers the question. Never "read ten files in sequence when one scan will do."
3. **Host portability.** The same skill files work in Claude, Cowork, and Codex. No host-specific branching in skill prose.
4. **No lock-in.** Markdown + git. Everything is readable in a plain editor, versionable, and portable. No proprietary formats, no hidden databases.
5. **Extensible without core changes.** A new module = a new directory conforming to conventions. No central registry to update.

These goals are in tension. When they conflict, the one listed earlier wins.

## Hosts

The system runs on Claude and Codex hosts with different affordances. The architecture assumes two access mechanisms—MCP and direct filesystem access—and keeps skill behavior independent of the mechanism.

| Capability | Claude Desktop | Claude Code | Cowork | Codex app / CLI / IDE |
| --- | --- | --- | --- | --- |
| File access | MCP | Direct disk or MCP | Direct disk (folder-permissioned) | Direct disk or MCP |
| Scheduled/async tasks | ❌ | via `cron` / external | ✅ native | via external scheduling |
| Project instructions | — | `CLAUDE.md` | project context | `AGENTS.md` |
| Skill registry | `~/.claude/skills` | `~/.claude/skills` | `~/.claude/skills` | `~/.agents/skills` |

**On a local/server install, every host reads the same `~/cto-os-data/` directory.** Claude Code and Codex can open it directly, Claude Desktop accesses it through the local MCP server, and Cowork is granted folder-scoped permission. On a client install the data stays on the server and Claude/Codex clients use the remote HTTPS MCP. There is still one source of truth and no copied skill tree.

```
    ~/cto-os-data/   (single source of truth, on your laptop)
    ↑      ↑       ↑       ↑
    │      │       │       │
 Code   Desktop  Cowork   Codex
(disk)  (MCP)   (disk)  (disk/MCP)

           ↓
  git push (periodic, for backup)
           ↓
     private remote
```

**Cowork permission boundary.** Grant Cowork access to `~/cto-os-data/` specifically, not a parent directory. Everything it needs is inside that folder; anything outside is none of its business. On macOS this works cleanly; on Windows there's currently a known restriction that confines Cowork to the user's home directory — fine as long as the data repo lives under `~/`.

**Concurrent writes.** The only coordination concern is two surfaces writing the same file at the same moment (e.g., hand-editing a journal while Cowork runs an overnight digest that appends to it). In practice: most writes are append-only, collisions are vanishingly rare, and scripts that do non-append writes use a short `fcntl` file lock. Not worth architecting around further until it actually bites.

**The skill is written once.** It references operations by logical name (`scan`, `write_file`). Each host supplies them through MCP or direct filesystem access. The skill never branches on host.

**How the skill activates on each surface:**

`install.sh` points both host registries at the same checkout: `~/.claude/skills/cto-os` for Claude and `~/.agents/skills/cto-os` for Codex. The skill activates when the user's request matches root `SKILL.md`'s `description:` frontmatter. Per-module `SKILL.md` files load on demand once the root is active.

- **Claude Desktop (Chat).** The built-in skill router reads each installed skill's root `SKILL.md` description and picks the best match for each user message. `cto-os/SKILL.md`'s description must be specific enough to avoid false positives ("write me a haiku") and broad enough to catch oblique phrasings ("I had a weird convo with Mike yesterday" should match, since 1:1 content is in scope).
- **Cowork.** Same router behavior as Chat — description-based activation via root `SKILL.md`. Additionally, the Cowork project must be granted folder-scoped permission to `~/cto-os-data/`; without that, the skill activates but has nowhere to read or write state.
- **Claude Code.** Same skill registry (`~/.claude/skills/cto-os/`), same description-based activation. *Additionally*, when cwd is `cto-os-data/`, Claude Code loads that repo's `CLAUDE.md` into always-on context. That file instructs Claude to default to the `cto-os` skill for any request that could plausibly be CTO-domain work — biasing activation to be more permissive inside the data repo than the pure description-match rule would allow. The skill is not *auto-loaded* by cwd; `CLAUDE.md` just tells Claude to invoke it liberally.
- **Codex.** Discovers the same checkout through `~/.agents/skills/cto-os/`. When Codex opens either repo it reads `AGENTS.md`, which is a symlink to that repo's canonical `CLAUDE.md`; there is no second instruction document to maintain.

**Root `SKILL.md` is required, not optional.** Its description is the shared activation lever across hosts.

**Primary use-by-surface pattern (suggested, not enforced):**

- **Chat** — interactive queries, 1:1 prep, journal writing, weekly review, cross-module questions
- **Code** — bulk operations, migrations, structural changes to the OS itself, batch index updates
- **Cowork** — scheduled digests, pre-meeting briefings, inbox-driven triggers, overnight rollups
- **Codex** — the same interactive and long-running work through the app, CLI, or IDE

## Storage format

**Format:** Markdown with YAML frontmatter. Nothing else.

**Why not SQLite / Notion DB / Airtable:** Markdown files are diffable, grep-able, editable by hand, and free of vendor lock-in. Structured queries are handled by a Python scan script (see [CTO OS — Skill repo](./SKILL_REPO.md)), not a DB engine. For a single-user knowledge base at this scale (hundreds to low thousands of files), filesystem + grep is faster than any DB round-trip and infinitely more portable.

**Frontmatter baseline:** Every file has YAML frontmatter with at minimum `type`, `slug`, `updated`. Each module defines its own additional fields. The canonical schema lives in `cto-os/meta/schema.md` and is the single source of truth — the pre-commit hook in `cto-os-data` validates against it.

**Versioning:** Both repos are git-versioned. `cto-os` is versioned because it's code; `cto-os-data` is versioned for backup and history (pushed periodically to a private remote). Commit cadence is the user's choice.

---

# How the two repos connect

Thin host adapters plus one install script connect the repos. No symlinks cross the repo boundary; no user state is shared into the skill repo.

## CTO_OS_DATA env var

Points at the path of `cto-os-data` on your machine (typically `~/cto-os-data`). The skill and all scripts read this to locate state — no cwd auto-detection, no fallback. If `CTO_OS_DATA` is unset or empty, scripts and the MCP server error out with a clear "set `CTO_OS_DATA`" message.

How it gets set, per surface:

- **Claude Desktop.** `install.sh` writes it into the `mcpServers.cto-os.env` block of `claude_desktop_config.json`. The MCP server inherits it when Claude Desktop spawns it.
- **Claude Code.** The user exports it in their shell profile (`install.sh` prints the exact line to add). Any `claude` session inherits it.
- **Cowork.** The user sets it in the Cowork project config.
- **Codex.** `install.sh` adds it to the local stdio MCP server entry. Direct script invocations inherit it from the shell like Claude Code.

In the normal single-laptop case, all hosts resolve to the same path. The env-var indirection keeps the skill portable to other setups without code changes.

## Project instructions as local activation bias

`cto-os-data/CLAUDE.md` is loaded into Claude Code's always-on context whenever cwd is the data repo. It doesn't *trigger* activation — the skill is already in scope via the global `~/.claude/skills/cto-os/` symlink. What it does is **bias** activation: it tells Claude to default to invoking `cto-os` for any request that could plausibly be CTO-domain work, prefer activating over asking, and skip the skill only for clearly-unrelated tasks (shell admin, unrelated coding).

The effect: inside the data repo, vague or oblique requests that wouldn't match description-based dispatch in Chat still route through the skill in Code. That's the user-facing payoff — less need to overspecify context when working in the data repo.

Each repo also has `AGENTS.md -> CLAUDE.md`, so Codex receives the same instructions without a copied file. The `cto-os` skill repo has its own canonical `CLAUDE.md` for working on system code. Different audience, different purpose. See [CTO OS — Skill repo](./SKILL_REPO.md).

## Slug convention

`cto-os/modules/{slug}/` and `cto-os-data/modules/{slug}/` share the same slug but own different files — `SKILL.md` + `README.md` on the skill side, `_module.md` + `state/` on the data side. Renaming a module means renaming both directories in lockstep; `cto-os/scripts/rename_module.py` handles it.

## install.sh

`cto-os/install.sh` is idempotent — safe to re-run. Given a target path (e.g., `~/cto-os-data`), it:

1. `git init`s the data repo if needed, writes missing templates, safely migrates the exact known legacy `CLAUDE.md`, preserves customized instructions, and creates `AGENTS.md -> CLAUDE.md` when that path is free.
2. Symlinks both `~/.claude/skills/cto-os/` and `~/.agents/skills/cto-os/` to the skill repo checkout so updates via `git pull` flow automatically.
3. Merges the `cto-os` MCP entry into Claude and Codex config while preserving unrelated entries and config symlinks. Identical output is not rewritten. If the Codex CLI is available, a read-only preflight validates the entire existing config before any install writes.
4. Configures the repo-local pre-commit reviewer (`auto`, `claude`, `codex`, or `none`) without replacing an existing explicit choice on an ordinary rerun.
5. Leaves conflicting unmanaged files or symlinks intact and reports warnings instead of overwriting them.

## The instruction and skill files

Each file has one job and one canonical home.

- `CLAUDE.md` in each repo — the canonical project instructions for that repo's audience.
- `AGENTS.md` in each repo — a symlink to its `CLAUDE.md`, exposing identical instructions to Codex.
- `SKILL.md` in `cto-os` (root + per-module) — the shared skill body and activation description, loaded through each host's global skill registry.
- `README.md` in both repos — for humans and general orientation.

Why not consolidate? `CLAUDE.md` can't be `SKILL.md` because they have different loading semantics (cwd-scoped always-on context vs. registry-scoped description-matched activation) and different audiences. `README.md` can't be `CLAUDE.md` because READMEs are for humans skimming, and `CLAUDE.md` has instruction-prose that would confuse readers.

---

# Activation & onboarding

From the PRD: "A module's framework serves as the activation spine." Architectural implications:

- Each module's `SKILL.md` (in `cto-os/modules/{slug}/`) contains an **activation flow** section: a sequence of questions, framework-derived, that populate the module's baseline state.
- Activation creates `cto-os-data/modules/{slug}/` if it doesn't exist, writes the baseline state files (e.g., `state/altitude.md`, `state/goals/annual.md`, `state/show-up.md` for Personal OS), and creates a `_module.md` with `active: true` and an `activated_at` timestamp.
- Activation can be **resumed**. If interrupted, `_module.md` tracks which activation questions are complete vs pending. Next invocation picks up where it left off.
- Activation **checks dependencies** first. If a required dependency is inactive, activation offers to activate it first (and explains what gets unlocked).

**No central activation registry.** The scan tool run over `_module.md` files across `cto-os-data/modules/` *is* the registry. You can ask at any time: "which modules are active?" and get a current answer.

**Why activation state lives in `cto-os-data`, not `cto-os`:** activation is per-user. Putting it in the skill repo would either mean writing user state into shared code (wrong) or introduce copy/symlink synchronization.

---

# Cross-module access & dependency graph

**Modules read each other's state directly** via the scan tool. There is no "module API" layer — the shared schema and directory conventions *are* the API.

**Dependency rules (from PRD, mapped to architecture):**

- **Required dependencies form a DAG.** Acyclic. Enforced by a pre-commit script (`cto-os/scripts/validate_deps.py`) that parses each `SKILL.md`'s frontmatter, builds the graph, and fails if a cycle exists.
- **Optional dependencies may be bidirectional** and can form cycles. Not validated.
- When a module is **inactive**, its state files still exist on disk but scan excludes them by default (filter on `active: true` in the module's `_module.md`). This preserves history when a module is deactivated.

**Personal OS as intent/identity layer:** A handful of modules read `cto-os-data/modules/personal-os/state/show-up.md` and the voice samples in `cto-os-data/modules/personal-os/state/voice/` to tune their outputs. This is an optional dependency declared in each consuming module's `SKILL.md`. When Personal OS is inactive, those modules fall back to generic-professional voice.

**No global event bus, no pub/sub.** State is pulled on demand. Simpler, cheaper, and fits the single-user model.

---

# Persistence model

When and how the skill writes state to `cto-os-data`. One cross-cutting rule for every module.

## The rule

- **Every write is transparent.** Claude uses the first-class `write_file` / `append_to_file` tools (via MCP in Chat, directly in Code/Cowork). Every save appears in the transcript with its target path. No wrapping helpers, no background writes, no saves the user can't see.
- **Default is just save.** When the target file and content are clear from context, Claude saves without blocking for confirmation. "Clear" means one of:
  - The user issued an explicit save command ("save this," "remember," "log," "add to my notes").
  - The user narrated a flow-ending event a specific module owns ("I just had a 1:1 with Jane" → managing-down).
  - Claude is inside an activation flow, where writing answers is the point.
  - The module has a scheduled checkpoint (periodic retro, weekly review) and the user reached it.
- **Ask only when genuinely ambiguous.** Claude pauses for confirmation when:
  - Two modules plausibly own the content and the wrong choice would misfile it.
  - A write would overwrite existing material with different facts (losing content matters).
  - The user's phrasing was exploratory ("I'm wondering whether…") rather than declarative.
  - Claude would have to fabricate required frontmatter fields it can't ground in what the user said.
- **Never silent, never speculative.** No writes that don't surface in the transcript. No writes that present inference as fact — if Claude had to guess, frame the guess in the body ("Inferred from:") or don't write.

## What each write carries

- **Path.** Derived from the module's convention. The module's `SKILL.md` declares path templates (e.g., `state/people/{person-slug}/{date}.md`).
- **Semantics.** One of **append** (1:1 notes, journal, retros), **overwrite** (current goals — with history in the body), or **upsert** (stakeholder-profile fields). Declared per-path in each module's `SKILL.md`.
- **Frontmatter.** Required fields per `meta/schema.md`. Populated before the write; the data-repo pre-commit hook validates on save and rejects incomplete frontmatter.

## Undo

Every write is a git-tracked change in `cto-os-data`. Claude doesn't build a custom undo — `git checkout -- <path>` restores a file, `git reset --hard HEAD` drops a not-yet-committed batch, and reverts work for anything already committed. If the user asks to undo, Claude names the git command rather than re-editing the file back.

## Module responsibility

Every `SKILL.md` in `modules/{slug}/` must include a **Persistence** section that declares:

- Paths this module writes to.
- Per-path semantics (append / overwrite / upsert).
- Path templates (how Claude constructs the filename).
- Required frontmatter.
- Any module-specific override to the cross-cutting "ambiguous → ask" rule (rare; modules should inherit the default).

A module without a Persistence section fails the skill-review checklist.

## Escape valve — top-level `notes/`

Not every save has a module home. `cto-os-data/notes/` is an explicit top-level convention for cross-module / pre-activation thinking — a holding pen for working threads that don't yet belong to a single module's state. Full spec: [docs/DATA_REPO.md → Working notes](./DATA_REPO.md#working-notes-top-level-notes).

This is **not** a way to bypass module state. Modules with declared paths still own their content; if a module is active and owns the content, it goes there. Notes is for the case where no module owns it yet.

**Working notes override the "default: just save" rule above.** The skill does not auto-save notes — even when the filename and content look obvious. For substantial cross-module threads, the skill *suggests* saving a working note ("This thread spans X and Y; want me to save it as `notes/YYYY-MM-DD-{slug}.md`?") and waits for confirmation. This asymmetry is deliberate: the holding-pen exists *because* the target is unclear, which is exactly the condition the rule above flags as "ask, don't assume." Documenting the override here ensures it survives future skill rewrites.

---

# Operations

## Security, privacy, secrets

- **Local-only by default.** State lives on your laptop and in a private git remote for `cto-os-data`. No cloud DB, no multi-tenant anything.
- **Secrets never in either repo.** API keys for Slack, Linear, Gmail live in macOS Keychain (accessed via `security` CLI in scripts) or a local `.env` file that's gitignored in both repos. Scripts read from env; they never accept secrets on the command line.
- **Sensitive modules flagged.** Performance & Development, Board Comms, and Managing Down contain information that could be damaging if leaked. Their state directories are marked in frontmatter (`sensitivity: high`) and the scan tool excludes them from queries unless explicitly included. This is defense-in-depth, not encryption.
- **Git remote considerations.** `cto-os-data` syncs to a **private** repo with 2FA enforced. `cto-os` can be public or private depending on whether you want to share the logic. `integrations-cache/` is gitignored in `cto-os-data` (pullable, not canonical).

## Testing and code review

Two layers, both enforced via the pre-commit hook (`hooks/pre-commit`, wired up by `install.sh`).

**Script and MCP tests.** Standard pytest in `cto-os/tests/` with fixtures in `tests/fixtures/cto-os-data-sample/`. Every script (`scan.py`, `validate_deps.py`, `roll_up.py`, `pull_*.py`, `rename_module.py`) and the MCP server has a test file using the subprocess pattern — tests shell out with real `--args '{...}'` invocations, asserting on exit code and parsed JSON stdout. Run with `uv run pytest tests/ -q`.

**AI-assisted skill review.** Prose skills have no compiler, so the shared procedure in `meta/skill-reviewer.md` applies the checklist at `tests/claude-review.md`. Thin adapters expose it to Claude (`.claude/agents/skill-reviewer.md`) and Codex (`.codex/agents/skill-reviewer.toml`). The pre-commit hook selects a runner through `CTO_OS_REVIEWER`, repo-local `cto-os.reviewer`, or `auto` (Claude first for backward compatibility, then Codex), and reviews staged skills, project instructions, docs, and reviewer files. The hook also runs `validate_deps.py` on any staged module `SKILL.md` to fail the commit on dep-graph cycles or unknown required deps.

Human PR review is the final gate — fresh eyes the next day, or an invited reviewer.
