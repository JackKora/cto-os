# CTO OS — Architecture

Companion to the [PRD](https://www.notion.so/dscout/CTO-OS-product-requirements-34617a66c83d80358e71c722924cde93). The PRD defines *what* modules exist and *how* they compose. This doc defines *how the system is built*.

The system is split across two repos — `cto-os` (logic) and `cto-os-data` (your personal state). This page covers what spans both. Deep dives for each live in:

- [CTO OS — Skill repo (cto-os)](./SKILL_REPO.md)
- [CTO OS — Data repo (cto-os-data)](./DATA_REPO.md)

---

# Foundations

## Design goals (in priority order)

1. **Latency efficiency.** Anything deterministic runs as Python or bash, not as an LLM round-trip. The LLM's job is judgment; scripts do the counting.
2. **Token efficiency.** Claude reads the smallest slice of state that answers the question. Never "read ten files in sequence when one scan will do."
3. **Surface portability.** Same skill files work in Chat, Code, and Cowork. No branching on surface.
4. **No lock-in.** Markdown + git. Everything is readable in a plain editor, versionable, and portable. No proprietary formats, no hidden databases.
5. **Extensible without core changes.** A new module = a new directory conforming to conventions. No central registry to update.

These goals are in tension. When they conflict, the one listed earlier wins.

## Surfaces

The system runs on all three surfaces of Claude. Each has different affordances; the architecture assumes the lowest common denominator (disk + scripts) and lets each surface add what it can.

| Capability | Chat (Desktop) | Code | Cowork |
| --- | --- | --- | --- |
| File access | Local MCP | Direct disk | Direct disk (folder-permissioned) |
| Scheduled/async tasks | ❌ | via `cron` / external | ✅ native |
| Remote connectors (Linear, Gmail, Slack) | ✅ native | via bash + local scripts | via bash + local scripts |
| Chat history search | ✅ | ❌ | ❌ |
| Skill loading | ✅ `SKILL.md` | via `CLAUDE.md` reference | ✅ `SKILL.md` |

**All three surfaces read the same `~/cto-os-data/` directory on your laptop.** Claude Code `cd`'s into it. Claude Desktop accesses it via the local MCP server. Cowork is granted folder-scoped permission to it. Same files, same disk, edits are instantly visible everywhere. No sync dance between surfaces.

```
    ~/cto-os-data/   (single source of truth, on your laptop)
    ↑      ↑     ↑
    │      │     │
 Code   Desktop  Cowork
(cd)  (via MCP) (folder permission)

           ↓
  git push (periodic, for backup)
           ↓
     private remote
```

**Cowork permission boundary.** Grant Cowork access to `~/cto-os-data/` specifically, not a parent directory. Everything it needs is inside that folder; anything outside is none of its business. On macOS this works cleanly; on Windows there's currently a known restriction that confines Cowork to the user's home directory — fine as long as the data repo lives under `~/`.

**Concurrent writes.** The only coordination concern is two surfaces writing the same file at the same moment (e.g., hand-editing a journal while Cowork runs an overnight digest that appends to it). In practice: most writes are append-only, collisions are vanishingly rare, and scripts that do non-append writes use a short `fcntl` file lock. Not worth architecting around further until it actually bites.

**The skill is written once.** It references tools by logical name (`scan`, `write_file`). Each surface provides those tools via whatever mechanism is native — MCP in Chat, direct bash/filesystem in Code and Cowork. The skill never branches on surface.

**How the skill activates on each surface:**

- **Claude Code.** `cd ~/cto-os-data && claude`. Claude Code auto-loads `cto-os-data/CLAUDE.md` from cwd, which references the globally-installed `cto-os`. The skill is in scope for the whole session. No description matching needed — the presence of `CLAUDE.md` is the activation signal.
- **Claude Desktop (Chat).** Chat has a built-in skill router that reads every installed skill's root `SKILL.md` description and picks the best match for each user message. `cto-os/SKILL.md` must have a description specific enough to avoid false positives ("write me a haiku") and broad enough to catch oblique phrasings ("I had a weird convo with Mike yesterday" should match, since 1:1 content is in scope). Once the root skill has activated, per-module `SKILL.md` files are loaded on demand.
- **Cowork.** Same router behavior as Chat — description-based activation via root `SKILL.md`. Additionally, the Cowork project must be granted folder-scoped permission to `~/cto-os-data/`; without that, the skill activates but has nowhere to read or write state.

**Root `SKILL.md` is required, not optional.** Chat and Cowork have no other activation mechanism. Claude Code could in principle work without one (its `CLAUDE.md`-based activation is sufficient), but we keep a root `SKILL.md` for consistency.

**Primary use-by-surface pattern (suggested, not enforced):**

- **Chat** — interactive queries, 1:1 prep, journal writing, weekly review, cross-module questions
- **Code** — bulk operations, migrations, structural changes to the OS itself, batch index updates
- **Cowork** — scheduled digests, pre-meeting briefings, inbox-driven triggers, overnight rollups

## Storage format

**Format:** Markdown with YAML frontmatter. Nothing else.

**Why not SQLite / Notion DB / Airtable:** Markdown files are diffable, grep-able, editable by hand, and free of vendor lock-in. Structured queries are handled by a Python scan script (see [CTO OS — Skill repo](./SKILL_REPO.md)), not a DB engine. For a single-user knowledge base at this scale (hundreds to low thousands of files), filesystem + grep is faster than any DB round-trip and infinitely more portable.

**Frontmatter baseline:** Every file has YAML frontmatter with at minimum `type`, `slug`, `updated`. Each module defines its own additional fields. The canonical schema lives in `cto-os/meta/schema.md` and is the single source of truth — the pre-commit hook in `cto-os-data` validates against it.

**Versioning:** Both repos are git-versioned. `cto-os` is versioned because it's code; `cto-os-data` is versioned for backup and history (pushed periodically to a private remote). Commit cadence is the user's choice.

---

# How the two repos connect

Three thin mechanisms and one install script. No symlinks cross the repo boundary; no shared files.

## CTO_OS_DATA env var

Points at the path of `cto-os-data` on your machine (typically `~/cto-os-data`). The skill and all scripts read this to locate state. Resolution order:

1. `CTO_OS_DATA` environment variable (set by `install.sh` in the MCP config, shell profile, and Cowork project config)
2. Current working directory, if it contains `CLAUDE.md` and validates as a CTO OS data repo (how Claude Code picks it up when you `cd` into the data repo)
3. Fallback: error with a clear "set `CTO_OS_DATA`" message

In the normal single-laptop case, all three surfaces resolve to the same path. The env-var indirection exists so the skill remains portable to other setups (different user home, a second machine, a future cloud-hosted variant) without code changes.

## CLAUDE.md as the Code activation trigger

`cto-os-data/CLAUDE.md` tells Claude Code "this is a CTO OS data repo; use the globally-installed `cto-os`." That one file is what makes `cd ~/cto-os-data && claude` activate the skill automatically. Without it, Claude Code sees a plain directory and stays in generic mode. (Chat and Cowork use description-based activation via root `SKILL.md` — see Surfaces above.)

Note: `cto-os` also has its own `CLAUDE.md`, for when you `cd` into the skill repo to work on the code itself. Different audience, different purpose. See [CTO OS — Skill repo](./SKILL_REPO.md).

## Slug convention

`cto-os/modules/{slug}/` and `cto-os-data/modules/{slug}/` share the same slug but own different files — `SKILL.md` + `README.md` on the skill side, `_module.md` + `state/` on the data side. Renaming a module means renaming both directories in lockstep; `cto-os/scripts/rename_module.py` handles it.

## install.sh

`cto-os/install.sh` is idempotent — safe to re-run. Given a target path (e.g., `~/cto-os-data`), it:

1. `git init`s the data repo if needed and writes `CLAUDE.md`, `README.md`, `.gitignore` only if absent — never clobbering existing data.
2. Symlinks `~/.claude/skills/cto-os/` → the skill repo checkout so updates via `git pull` flow automatically.
3. Writes (or merges) the MCP entry in `claude_desktop_config.json` with `CTO_OS_DATA` set.
4. Prints one-screen follow-ups for Cowork and Claude Code that can't be fully automated.

## The three file types

Three files, three jobs, three homes.

- `CLAUDE.md` in `cto-os-data` — Claude Code's activation trigger when operating on user state.
- `CLAUDE.md` in `cto-os` — Claude Code's orientation when working on the system code itself.
- `SKILL.md` in `cto-os` (root + per-module) — Chat/Cowork skill router's activation trigger and the execution spec.
- `README.md` in both repos — for humans and general orientation.

Why not consolidate? `CLAUDE.md` can't be `SKILL.md` because they have different loading semantics (Claude Code's cwd-triggered vs. the skill router's description-matched) and different audiences. `README.md` can't be `CLAUDE.md` because READMEs are for humans skimming, and `CLAUDE.md` has instruction-prose that would confuse readers.

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

---

# Operations

## Security, privacy, secrets

- **Local-only by default.** State lives on your laptop and in a private git remote for `cto-os-data`. No cloud DB, no multi-tenant anything.
- **Secrets never in either repo.** API keys for Slack, Linear, Gmail live in macOS Keychain (accessed via `security` CLI in scripts) or a local `.env` file that's gitignored in both repos. Scripts read from env; they never accept secrets on the command line.
- **Sensitive modules flagged.** Performance & Development, Board Comms, and Managing Down contain information that could be damaging if leaked. Their state directories are marked in frontmatter (`sensitivity: high`) and the scan tool excludes them from queries unless explicitly included. This is defense-in-depth, not encryption.
- **Git remote considerations.** `cto-os-data` syncs to a **private** repo with 2FA enforced. `cto-os` can be public or private depending on whether you want to share the logic. `integrations-cache/` is gitignored in `cto-os-data` (pullable, not canonical).

## Testing and code review

Four levels.

**Script tests.** Standard pytest in `cto-os/tests/` with fixtures in `tests/fixtures/cto-os-data-sample/`. Every script (`scan.py`, `roll_up.py`, `pull_*.py`, migrations) gets unit tests. Runs in CI on push.

**Skill behavior tests.** Harder because the skill is prose. Maintain `tests/scenarios/` with expected-behavior traces — given a sample data repo and a prompt, what should Claude do? Eyeball manually at first; automate with Claude-as-judge later if the manual review gets tedious.

**AI-assisted skill review.** Prose skills have no compiler to catch inconsistencies, but Claude can review them well. On each PR to `cto-os`, a Claude Code Review action runs with a checklist encoded in `tests/claude-review.md`: check for internal contradictions between `SKILL.md` files, overlap in trigger phrases across sibling modules, activation flow steps that reference missing schema fields, and prose that contradicts the module's README.

**Human PR review.** Standard GitHub PR flow on `cto-os`, even solo — reviewer is you with fresh eyes next day, or anyone you invite. CI gates merges on the pytest suite and the AI review.

## Phasing

A rough build order that respects the required-dependency DAG and the PRD's "Foundations → Daily drivers → Role-shape → Strategic" sequence:

1. **Bootstrap.** Set up `cto-os` with: root layout, `meta/schema.md`, `scripts/scan.py`, `mcp-server/server.py` (minimum tool surface), and `install.sh`. Run `install.sh` to create an empty `cto-os-data` with `CLAUDE.md` and `README.md`. No modules yet in either repo.
2. **Foundations.** Personal OS, Process Management, Business Alignment — the three zero-outbound-dependency modules from the PRD. Each gets `cto-os/modules/{slug}/SKILL.md` + `README.md`, and on activation creates `cto-os-data/modules/{slug}/`. Validate activation flow end-to-end with one of them.
3. **Daily drivers.** Attention & Operations, Team Management, one of Managing Up/Down/Sideways.
4. **Integrations.** `pull_slack.py`, `pull_linear.py` — once daily drivers exist to consume the data.
5. **Role-shape.** Tech Ops, Technical Strategy, Hiring, Budget as needed.
6. **Strategic.** Org Design, Performance & Development, Board Comms.
7. **Deferred optimizations.** Listing index if scan latency ever becomes noticeable. Semantic search if keyword + frontmatter scan proves insufficient.

## Open architectural questions

- **Schema evolution edge cases.** The Schema evolution pattern (see [CTO OS — Skill repo](./SKILL_REPO.md)) handles straightforward migrations. What about irreversible field removals, or renames that need to preserve historical values? Tentatively: each migration documents its reversibility; irreversible ones require an explicit confirmation prompt during migration.

Other questions were resolved during design: the schema mirror was dropped (single source of truth in skill repo); Homebrew distribution was rejected as overkill (`install.sh` per machine); framework link rot is fix-on-detection (no link-check script); the data-repo changelog was dropped (git log suffices).
