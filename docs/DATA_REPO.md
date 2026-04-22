# CTO OS — Data repo (cto-os-data)

Child of [CTO OS — Architecture](./ARCHITECTURE.md). Covers everything specific to `cto-os-data`: layout, `CLAUDE.md`, module state conventions, integrations cache semantics.

The data repo holds your **personal state**. Private git repo, backed up to a private remote. Contains only content — no logic, no scripts, no skill definitions.

---

# Layout

```
cto-os-data/                           # git repo — your private data, backed up to private remote
├── CLAUDE.md                          # project constitution for Claude Code
├── README.md                          # short orientation
├── .gitignore                         # excludes integrations-cache/, logs/, secrets
├── modules/                           # slugs must match cto-os/modules/
│   ├── personal-os/
│   │   ├── _module.md                 # activation state, schema_version
│   │   └── state/
│   │       ├── altitude.md
│   │       ├── show-up.md
│   │       ├── goals/                 # one file per horizon
│   │       │   ├── annual.md
│   │       │   ├── quarterly.md
│   │       │   └── weekly.md
│   │       ├── voice/                 # one file per sample
│   │       │   └── 2026-03-15.md
│   │       └── retros/                # one file per retro
│   │           └── 2026-04-21.md
│   ├── managing-down/
│   │   ├── _module.md
│   │   └── state/
│   │       └── people/{person-slug}/…
│   ├── team-management/
│   │   ├── _module.md
│   │   └── state/
│   │       └── teams/platform.md
│   └── …
├── integrations-cache/                # gitignored, regenerable
│   ├── slack/
│   ├── linear/
│   └── gmail/
└── logs/                              # gitignored; MCP server writes mcp.log here (rotated daily, last 24h+)
```

**Key properties:**

- **State only.** If you deleted `cto-os` from your laptop, `cto-os-data` would still be a complete, human-readable record of your work — just without the tooling to query it efficiently.
- **Directory per activated module.** A `modules/{slug}/` directory exists if that module has ever been activated. Deactivation flips `active: false` in `_module.md` but keeps the directory, preserving history.
- **State files are flat within a module** but hierarchical across modules via `modules/{slug}/state/…`. Cross-module reads always go through the scan script, never via hardcoded paths — this makes module renames safe.
- **Backup via git.** Committed to a private remote with 2FA enforced.
- **Activation state lives here, not in the skill repo.** Activation is per-user; putting it in the skill repo would either mean writing user state into shared code or introduce copy/symlink synchronization.
- **No meta/ directory.** No changelog (git log suffices), no schema mirror (skill repo's `meta/schema.md` is the single source of truth).

---

# CLAUDE.md (project constitution)

**Audience:** Claude Code, when launched with `cto-os-data/` as cwd. This is the activation trigger that makes `cd ~/cto-os-data && claude` pick up the CTO OS skill automatically.

**Purpose:** Top-of-context instructions that tell Claude (a) what this repo is, (b) where the skill lives (`~/.claude/skills/cto-os/` → `cto-os`), (c) key conventions and invariants, (d) which scripts exist and when to use them, (e) self-maintenance rules for the data repo.

**Why in data and not skill:** it points *at* the skill, it doesn't *contain* the skill. It also needs to ship with the data repo so cloning `cto-os-data` onto a new machine immediately signals "this is a CTO OS repo" to Claude Code.

**Do not confuse with the skill repo's `CLAUDE.md`.** That one orients Claude when you're modifying the system's code. This one orients Claude when you're using the system to manage your state.

**Length budget:** ~300 lines. If it grows past that, sections get moved into pointer references (`See cto-os/modules/{x}/SKILL.md for…`).

---

# Module state

Each activated module has a directory under `cto-os-data/modules/{slug}/` containing two things:

**`_module.md`** — activation state and per-module metadata:

```yaml
---
module: personal-os
active: true
activated_at: 2026-03-01
deactivated_at: null
schema_version: 1
---
```

**`state/`** — the module's actual content. Structure is defined by the module's own `SKILL.md` in `cto-os`. State files use frontmatter + markdown body.

## Historic data & rubric scoring

From the PRD: modules store history, not just current state. The pattern:

- Each module that scores things keeps its scores at a predictable path (e.g., `state/scores/{subject-slug}.md` or `state/teams/{slug}.md`) with a time-series body and frontmatter holding the current snapshot.
- History is append-only markdown; current values are mirrored into frontmatter for cheap scan access.
- Example: `cto-os-data/modules/team-management/state/teams/platform.md` has frontmatter `scores: {velocity: 7, morale: 6, …}` (current) and a body containing quarterly snapshots in reverse chronological order.
- "How has team platform trended" → scan returns the path, then skill reads the body. Two tool calls, predictable cost.

**One file per subject, not split current/history.** Keeping current + history in one file means there's one canonical place for a subject, and the scan tool doesn't need to know about the current/history split. Less surface area. Files get longer over time — when one exceeds ~500 lines, the module's `SKILL.md` includes an archival rule: oldest history moves to `state/archive/{year}/`.

## File granularity — one file per independently-changing unit

How do you decide what a "subject" is? The rule:

> **One file per independently-changing unit of state.** A unit is whatever has its own update cadence, its own historical lineage, or its own access pattern. Scan assembles multi-unit views at read time; write-time co-location should only happen when the things truly co-evolve.

Examples of unit choices across modules:

| Module | Unit | File layout |
| --- | --- | --- |
| Managing Down | 1:1 per (person, date) | `state/people/{person-slug}/{date}.md` |
| Managing Up / Sideways | one profile per stakeholder | `state/people/{slug}.md` |
| Team Management | one health record per team | `state/teams/{slug}.md` |
| Performance & Development | one track per person | `state/people/{slug}.md` |
| Hiring | one per (req, candidate) | `state/reqs/{req}/{candidate-slug}.md` |
| Tech Ops | one per incident | `state/incidents/{id}.md` |
| Board Comms | one per meeting | `state/meetings/{date}.md` |
| Personal OS | one per horizon | `state/goals/{horizon}.md` |

**When NOT to split:**

- **Singletons.** User altitude, show-up definition — one logical unit (the user), one file.
- **Attributes that only make sense together.** A team's `(name, lead, charter)` tuple doesn't benefit from three files.
- **Churn-ratio test.** If you'd rewrite the same file on 80%+ of any given update regardless, splitting isn't buying anything.

**Design-time question for any new module:** *"What's the thing that changes on its own?"* That's your unit. Make a file per unit.

## Sensitive modules

Performance & Development, Board Comms, and Managing Down contain information that could be damaging if leaked. Their state directories are marked in frontmatter (`sensitivity: high`) and the scan tool excludes them from queries unless explicitly included. This is defense-in-depth, not encryption.

---

# Integrations cache

`cto-os-data/integrations-cache/{source}/` holds the output of `pull_*` scripts. Timestamped filenames, markdown or JSON depending on the source.

**Properties:**

- **Gitignored** — regenerable, not canonical.
- **Read-only to the skill.** Claude queries it via `scan` like any other data, but never writes there directly. Only the `pull_*` scripts write here.
- **Enables cross-source queries** without hitting multiple APIs from the LLM context (e.g., "which teams have high Slack volume *and* declining morale").

## Freshness policy (TTL)

Each source has a TTL declared in `cto-os/scripts/lib/integrations.yaml`:

```yaml
slack:
  ttl_minutes: 240        # 4h
linear:
  ttl_minutes: 30
gmail:
  ttl_minutes: 60
```

Pull scripts check the most recent timestamped file in the cache and skip the pull if within TTL. The skill invokes pull transparently; it's a no-op when cache is fresh. User override: an explicit "refresh" instruction forces a pull regardless of TTL.

## Incremental pulls without gaps or overlaps

Pulls are incremental — each run fetches only what's new since the last run. Done naively this is fragile (gaps if a pull is delayed, duplicates if a pull retries). The design:

- **Watermark is a message timestamp, not a pull timestamp.** Each pull's `since` parameter is the timestamp of the *latest message already in cache*, not the time of the last pull. This closes the window: if a message arrived between pulls, the next pull picks it up because its timestamp is newer than what's cached.
- **Small overlap buffer.** Pulls fetch from (latest cached timestamp − 5 minutes) as defense in depth against clock skew and API-side eventual consistency.
- **Dedup on append.** Every item has a stable ID from the source (Slack `ts`, Linear issue ID, Gmail message ID). If the cache already contains that ID, skip the append. For sources without reliable stable IDs, fall back to a content hash.

Result: each pull is idempotent and safe to re-run. Missed pulls don't lose data; spurious pulls don't duplicate.

## Append, don't overwrite

Each pull writes a new timestamped file rather than replacing the previous one. Default `scan` queries return the latest; older pulls remain available for longitudinal questions ("what was the team saying about X last quarter"). Storage cost is trivial for text data, and the history makes debugging easier — you can see what the cache looked like at any past moment.

---

# README (data side)

`cto-os-data/README.md` is short. Reminds you what's in the repo and that logic lives in `cto-os`. Hand-written once, rarely edited. Not regenerated from anything.

---

# Self-maintenance rules (data side)

Rules for Claude Code working in the data repo:

- After activating or deactivating a module: verify the module directory exists and `_module.md` is current.
- After a schema migration completes: confirm `schema_version` in `_module.md` matches the canonical version in the skill repo.
- Never hand-edit `_module.md`'s `active` flag or `schema_version` — those are managed by the skill's activation flow and migration scripts.
- `integrations-cache/` is never committed. If something there looks valuable, copy it into `modules/{slug}/state/` with proper frontmatter.
- `logs/` is never committed. MCP server writes rotated logs here; safe to delete any time.

**What the system does *not* try to maintain automatically:** state file contents. Every write surfaces in the transcript via the underlying tool call — no silent background rewriting. The skill saves without blocking when the target and content are clear and asks only when genuinely ambiguous. Full rule: see the [Persistence model](./ARCHITECTURE.md#persistence-model) section in the architecture doc.
