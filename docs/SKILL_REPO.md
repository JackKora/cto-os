# CTO OS — Skill repo (cto-os)

Child of [CTO OS — Architecture](./ARCHITECTURE.md). Covers everything specific to `cto-os`: layout, skill definitions, MCP server, scripts, canonical schema, and the design patterns that live on the skill side.

The skill repo holds the **code**. Public or private GitHub repo. Contains the MCP server, deterministic scripts, per-module skill definitions, and the canonical schema. No user state ever lives here.

---

# Layout

```
cto-os/                          # git repo — installed once, updated via git pull
├── README.md                          # human-facing overview
├── docs/
│   ├── ARCHITECTURE.md                # overview architecture doc (mirror of the Notion overview page)
│   ├── SKILL_REPO.md                  # skill repo deep-dive (mirror of this page)
│   └── DATA_REPO.md                   # data repo deep-dive (mirror of the data repo page)
├── CLAUDE.md                          # orientation for Claude Code working *on the skill code*
├── install.sh                         # bootstraps cto-os-data + installs skill
├── SKILL.md                           # root skill — required for Chat/Cowork activation
├── mcp-server/
│   └── server.py                      # thin Python MCP bridge
├── scripts/                           # deterministic helpers
│   ├── scan.py
│   ├── roll_up.py
│   ├── pull_slack.py
│   ├── pull_linear.py
│   ├── validate_deps.py
│   ├── rename_module.py
│   └── lib/
│       └── integrations.yaml          # per-source TTL config
├── meta/
│   └── schema.md                      # canonical frontmatter schemas (single source of truth)
├── tests/
│   ├── fixtures/cto-os-data-sample/   # fixture data repo for script tests
│   ├── scenarios/                     # expected-behavior traces for skill review
│   ├── claude-review.md               # AI skill review checklist
│   └── test_*.py                      # pytest suites
└── modules/                           # one directory per PRD module
    ├── personal-os/
    │   ├── SKILL.md                   # activation flow, triggers, frameworks
    │   └── README.md                  # module overview for humans
    ├── managing-down/
    │   ├── SKILL.md
    │   └── README.md
    ├── team-management/
    └── …
```

**Key properties:**

- **Logic only.** No user-specific values anywhere — the same checkout would work for any user.
- **Updated via `git pull`.** New modules, script fixes, schema revisions all flow in.
- **Installed globally** (once per machine) via a symlink from `~/.claude/skills/cto-os/` into this repo's checkout. All three surfaces (Chat, Cowork, Claude Code) pick up the skill through this symlink and activate it on description match against root `SKILL.md`. The data repo's `CLAUDE.md` biases Claude Code toward activating more liberally when cwd is that repo — but it's not what loads the skill.
- **Module per directory.** Each PRD module gets one directory under `modules/`. The directory holds the module's `SKILL.md` and its `README.md`.

---

# CLAUDE.md (for working on the skill repo)

When you `cd ~/cto-os && claude`, Claude Code auto-loads this file. It orients Claude on how the skill is built — different audience from `cto-os-data/CLAUDE.md`, which orients Claude to operate on user state.

**Purpose:** Tell Claude (a) this is the CTO OS skill repo, (b) the architecture lives in `docs/ARCHITECTURE.md` / `docs/SKILL_REPO.md` / `docs/DATA_REPO.md`, (c) conventions for modifying the system (test before merge, update changelog, bump schema_version if frontmatter changes), (d) which scripts exist and their contracts, (e) self-maintenance rules.

**Audience:** future-you or a collaborator iterating on the skill code — not an end user managing their CTO state. This `CLAUDE.md` should never talk about "your team" or "your 1:1s"; it talks about modules, scripts, and the MCP server.

---

# ARCHITECTURE.md and friends

Mirror of the Notion architecture pages, shipped in the repo so the design lives with the code.

- `docs/ARCHITECTURE.md` — mirror of [the overview page](./ARCHITECTURE.md) (foundations, how the two repos connect, cross-cutting patterns, operations).
- `docs/SKILL_REPO.md` — mirror of this page.
- `docs/DATA_REPO.md` — mirror of [the data repo page](./DATA_REPO.md).

Notion is the discussion surface; the repo files are canonical for implementation. Any architectural change lands in a PR that updates both the Notion pages and these files together.

---

# Skill definitions (SKILL.md)

Two layers:

- **Root `cto-os/SKILL.md`** is what the Chat/Cowork skill router reads to decide whether to activate the system at all. Required, not optional.
- **Per-module `cto-os/modules/{slug}/SKILL.md`** is loaded on demand once the root skill has activated, based on the specific task.

Each `SKILL.md`:

- **Purpose:** Defines *when* this module's capabilities should trigger and *how* to execute them. Includes activation flow (see [CTO OS — Architecture](./ARCHITECTURE.md)), the module's frameworks, and its skill list.
- **Trigger specificity:** Has a clear description section that distinguishes it from sibling modules — this is what the router uses to pick the right one. Vague triggers cause wrong-module selection. The root description in particular needs to be specific enough to avoid false positives ("write me a haiku" should not match) and broad enough to catch oblique phrasings ("I had a weird convo with Mike yesterday" should match, since 1:1 content is in scope).
- **References, not duplicates:** Points to state files in `cto-os-data`, scripts in `cto-os/scripts/`, and schemas rather than inlining them. Inlined state goes stale.
- **Persistence section required on every per-module `SKILL.md`.** Declares the paths this module writes to, their semantics (append / overwrite / upsert), filename templates, required frontmatter, and any module-specific overrides to the cross-cutting save rule. See the [Persistence model](./ARCHITECTURE.md#persistence-model) in the architecture doc. The skill-reviewer fails a module that's missing this section.

## Per-module SKILL.md format

Every file at `modules/{slug}/SKILL.md` follows this structure. The skill-reviewer fails a module that's missing required frontmatter fields or required body sections.

### Frontmatter

```yaml
---
name: {module-slug}      # required; matches the directory name exactly
description: string      # required; activation trigger for the skill router
requires:                # required; may be empty list
  - {module-slug}
  - ...
optional:                # required; may be empty list
  - {module-slug}
  - ...
---
```

Rules:

- `name` must match the directory slug. Mismatch fails review.
- `description` is the activation trigger. Specific enough to not false-match unrelated topics, broad enough to catch oblique phrasings. See trigger-specificity guidance above.
- `requires` lists modules whose activation this module strictly depends on. Parsed by `scripts/validate_deps.py` to build the DAG and detect cycles. Cycles fail the pre-commit.
- `optional` lists modules this one *can* read from but doesn't require. Cycles are permitted here — they're not validated.
- Both lists hold slugs only (no descriptions, no link syntax).

### Required body sections

In this order, using these exact headings:

1. `## Scope` — one paragraph. What this module does.
2. `## Out of scope` — one paragraph. What it doesn't do and which module owns it instead.
3. `## Frameworks` — bulleted list. Each item has two parts:
   - Top bullet: `[Framework name](canonical-link)` + one sentence on what the module uses it for.
   - Indented sub-bullet labeled *"How this module applies it:"* — 2–5 lines specifying which flavor / variant is in use, what's skipped, how it maps to the module's state. This disambiguates the framework for runtime; without it, Claude's interpretation can drift.

   **Framework-familiarity check when authoring.** For each framework:
   - If it's well-known (OKRs, DORA, SPACE, Radical Candor, Andy Grove / *High Output Management*, *Working Backwards*, Reinertsen's Flow Principles, 4Ls retro, *How to Measure Anything*, etc.), the name + link + application note is sufficient. Claude's training covers the details.
   - If it's **not** well-known (internal framework, niche method, bespoke model), also create `frameworks/{slug}.md` at the skill repo root with a canonical summary (definition, how to apply it, common pitfalls), and reference it from the SKILL.md bullet as `See [frameworks/{slug}.md](../../frameworks/{slug}.md)`.

   When in doubt, create the dedicated note. Interpretation drift is cheaper to prevent than to debug.
4. `## Triggers` — bulleted list of example user phrasings that should activate this module. Used by the skill router and the skill-reviewer's trigger-overlap check.
5. `## Activation flow` — numbered list of steps; see format below.
6. `## Skills` — the named runtime tasks this module performs; see format below.
7. `## Persistence` — paths, semantics, templates, required frontmatter; see the Persistence model.
8. `## State location` — one line: `cto-os-data/modules/{slug}/state/`.

Modules may add additional sections after `## State location` (e.g., examples, escalation paths). Required sections must appear in the order above.

### Activation flow format

A numbered list of steps. Each step should capture at least one concrete artifact in `cto-os-data` — no step produces "answers" that aren't saved somewhere. Preferred pattern: one file per step.

**Resumption** is tracked by `activation_completed: list[int]` in the module's `_module.md`. When a step finishes (writes succeed, user confirms), its number is appended. On re-entering activation, Claude checks this list and skips completed steps. File-presence is a useful secondary signal — if an earlier step's target file is missing while its number is in the list, something drifted and Claude should flag it — but `activation_completed` is the source of truth.

```markdown
### 1. {Short step title}

**Ask:** "Verbatim question Claude asks the user."
**Writes:** `state/{path}.md` with `type: {type-slug}` frontmatter.
**Expects:** one sentence describing what a complete output looks like (used to judge resumption).
**Skip if:** optional — condition under which the step is skipped (e.g., "required dependency `personal-os` already supplies this").
```

Rules:

- Every step must have **Ask**, **Writes**, and **Expects**.
- **Skip if** is optional and only appears when the step has a genuine skip condition.
- Resumption: on re-entering activation, Claude reads each target file; if it exists and matches **Expects**, the step is done. Otherwise, run it.
- Branching questions (e.g., "are you hands-on-tech or P&L-oriented?") still have a **Writes** — the answer is saved to a file so later steps can read it. Prefer `state/activation.md` or a per-decision file.

### Skills list format

Each skill is a named runtime task the module performs once activated. Format per skill:

```markdown
### `skill-slug`

**Purpose:** one sentence describing what this skill does.
**Triggers:** bulleted list of user phrasings that should invoke it.
**Reads:** bulleted list of file paths or scan queries the skill pulls from.
**Writes:** file path(s) and the Persistence semantics (append / overwrite / upsert). Use `—` if this skill doesn't write.
```

Rules:

- Skill slugs are `lowercase-kebab-case` and unique within the module.
- `**Writes**` must be consistent with the module's `## Persistence` section; if a path appears here but not there, review fails.
- Skills that only read (e.g., "summarize quarterly 1:1 trend for a person") are fine; mark **Writes** as `—`.

---

# MCP server

**MCP is Chat-only.** Chat (Desktop) has no direct bash, so the MCP server is the mechanism Claude uses to reach disk and run scripts. Code and Cowork have native bash/file tools — Claude runs scripts directly via `uv run python scripts/scan.py --args '...'` from the repo root. No MCP involved.

You never manually start the MCP server. Claude Desktop launches it via stdio per session based on `claude_desktop_config.json`.

**Scope:** A thin Python MCP server living in `cto-os/mcp-server/`. No auth (local, stdio, single user). No domain logic — the skill owns all judgment; MCP just bridges Claude to the filesystem of `cto-os-data` and to the scripts in `cto-os/scripts/`.

**Tool surface (minimum viable).** Canonical contracts — signatures, response shapes, errors, path handling, whitelist — live in [docs/MCP_TOOLS.md](./MCP_TOOLS.md). Summary below.

| Tool | Purpose |
| --- | --- |
| `read_file(path)` | Read one file (path relative to `CTO_OS_DATA`). |
| `write_file(path, content)` | Overwrite or create. |
| `append_to_file(path, content)` | Append — used for 1:1 notes, journal entries, retro logs. |
| `list_directory(path, recursive=False)` | Enumerate. |
| `scan(query_spec)` | The workhorse. Grep + frontmatter filter over the whole `cto-os-data` tree in one call. Supports `include_body` for collapsing the typical scan → read_file flow into one turn; see Context loading below for the spec, tradeoffs, and guardrails. |
| `run_script(name, args)` | Invoke a whitelisted script from `cto-os/scripts/`. Returns stdout/stderr. |

All paths passed to these tools are relative to `CTO_OS_DATA` (i.e., relative to `cto-os-data`). The MCP refuses to operate outside that root.

**Explicitly *not* in the MCP surface:**

- Semantic / embedding search. Defer to a later phase. Grep over frontmatter + full-text gets ~90% of the way for a personal KB this size.
- A `get_team_health()`-style domain tool. That's skill logic, not MCP logic — it would force the MCP to know the schema, which couples it to the OS content.
- Auth. This is single-user, local-disk. If this ever goes multi-user, it gets rewritten.

**Lifecycle:** stdio, launched by Claude Desktop per-session. Startup < 200ms. No persistent index to warm up.

**Configuration:**

```json
{
  "mcpServers": {
    "cto-os": {
      "command": "python",
      "args": ["~/cto-os/mcp-server/server.py"],
      "env": { "CTO_OS_DATA": "~/cto-os-data" }
    }
  }
}
```

**File watching / change detection:** Not needed for scan-on-demand. Skipped to keep the server trivial.

---

# Scripts

All scripts live in `cto-os/scripts/` and are surface-agnostic. In Chat they're invoked via the MCP's `run_script` tool; in Code and Cowork they're invoked directly by Claude via bash. Same script, same contract, different entry point.

**Scripts:**

- `scan.py` — the workhorse. Frontmatter scan + filter over all of `cto-os-data` in one call. See Context loading below.
- `roll_up.py` — on-demand rollups (teams, projects, people). Returns compact tables of current-state metrics.
- `pull_slack.py` — Slack API → `cto-os-data/integrations-cache/slack/`. Handles TTL checks and dedup. See [CTO OS — Data repo](./DATA_REPO.md) for cache semantics.
- `pull_linear.py` — Linear GraphQL → `cto-os-data/integrations-cache/linear/`.
- `validate_deps.py` — parses each module's `SKILL.md` frontmatter, builds the required-dependency DAG, fails on cycles.
- `rename_module.py` — renames `{slug}` in lockstep across both repos.
- `migrate_{slug}_v{N}_to_v{N+1}.py` — per-module schema migrations. See Schema evolution below.

**Script contract:**

- Accept JSON over argv (single `--args '{...}'` flag).
- Emit JSON on stdout.
- Read `CTO_OS_DATA` from the environment; never hardcode data paths.
- Idempotent where possible (safe to re-run).

**Invocation:**

- **From Code / Cowork:** `uv run python scripts/{name}.py --args '{...}'` from the repo root. `uv run` handles venv resolution, no activation dance.
- **From the MCP server:** `subprocess.run([sys.executable, ...])` — the server already runs under the venv Python, so `sys.executable` is the venv Python. See `docs/MCP_TOOLS.md`.

The MCP's `run_script` tool is whitelisted — only names present in `cto-os/scripts/` can be invoked, and side-effect-bearing scripts are excluded from the whitelist. No arbitrary code execution.

**Dependencies** are managed via `uv` in `pyproject.toml` at repo root. `uv.lock` is committed for reproducible installs. Add a runtime dep with `uv add <package>`; add a dev dep with `uv add --dev <package>`.

**External integrations — MCP vs local script:**

| Source | Native MCP connector | Recommended approach |
| --- | --- | --- |
| Slack | Yes (Chat only) | Hybrid. MCP for interactive "send this message" in Chat. `pull_slack.py` for bulk reads, scheduled digests, and anywhere in Code/Cowork. |
| Linear | Yes (Chat only) | Hybrid. MCP for interactive ticket creation in Chat. `pull_linear.py` for bulk queries and background work. |
| Gmail | Yes (Chat only) | MCP for "reply to this thread" in Chat. Local script for inbox triage passes that read hundreds of headers. |
| Google Calendar | Yes (Chat only) | MCP is fine — calendar ops are small and interactive. |
| Notion | Yes | MCP — low volume, schema discovery matters. |
| Figma | Yes | MCP — design-phase tool, not daily-driver. |

**Decision rule for a new integration:**

- **Read-heavy, bulk, or scheduled?** → local Python client in `cto-os/scripts/`. Authenticate via local secrets (macOS Keychain, 1Password CLI, or env var — never a secret in either repo).
- **Interactive, low-volume, exploratory?** → MCP connector.
- **Both?** → both. They don't conflict.

---

# Canonical schema

`cto-os/meta/schema.md` is the single source of truth for all frontmatter schemas used across the system. Every file in `cto-os-data` validates against it on write (enforced by a pre-commit hook in the data repo that reads the schema directly from the installed skill path).

The schema changes only via intentional updates to `cto-os`. Migrations for existing state are handled by the Schema evolution pattern below.

There is no mirrored copy of the schema in `cto-os-data`. Considered it; rejected because the mirror would go stale whenever anyone forgot to run a sync script, and the data repo is never cloned without the skill repo in practice.

---

# README conventions (skill side)

- **`cto-os/README.md`** — overview of the system for humans browsing the code repo. Points at `docs/ARCHITECTURE.md` for details.
- **`cto-os/modules/{slug}/README.md`** — per-module reference. Lists frameworks used and 3–5 example concrete tasks. Regenerated from the module's `SKILL.md` as needed.

**Format for module READMEs:**

```
# {Module name}
**Scope:** One paragraph.
**Out of scope:** One paragraph.
**Frameworks:** [Name 1](link), [Name 2](link).
**Depends on:** required / optional lists.
**Example tasks:**
- …
- …
**State location:** cto-os-data/modules/{slug}/state/
```

---

# Context loading: scan, don't cache

The rule: when Claude needs to answer a cross-cutting question (e.g., "which teams are struggling"), it runs a `scan` call, not N file reads.

**Why not a materialized index.** A pre-aggregated top-level index file (with team health scores, OKR progress, project status) goes stale the moment any contributing file changes. The maintenance burden scales with every module added: who regenerates it, when, how completely. Every stale index leads to wrong answers that look authoritative.

**Scan-on-demand.** The `scan` tool (MCP-backed in Chat, direct script invocation in Code/Cowork) reads all frontmatter across `cto-os-data` in one call, filters by whatever predicate the caller asks for, and returns a compact result. Performance: frontmatter-only parse of ~1000 files completes in < 500ms on a laptop.

## Query interface

```python
scan({
  "type": ["team"],
  "where": {"status": "struggling"},
  "fields": ["slug", "lead", "scores.overall", "updated"],
  "include_body": False
})
```

Parameters:

| Parameter | Default | Purpose |
| --- | --- | --- |
| `type` | — | Filter matches by frontmatter `type` field (list). |
| `where` | — | Frontmatter predicate dict. |
| `fields` | all frontmatter | Which frontmatter fields to return on each match. |
| `include_body` | `false` | **Latency lever.** When true, include each matched file's markdown body in the response. Opt-in, guarded by caps. See below. |

## The three-call baseline

For lookup queries that need file *contents* (not just paths), the default flow spans three sequential LLM turns:

1. Claude decides to scan; emits `scan(...)` args.
2. Scan result returns paths; Claude emits `read_file(...)` calls (in parallel if multiple).
3. File contents return; Claude synthesizes the answer.

Parallel tool calls within a single turn are effectively free — N parallel `read_file`s at ~50ms of disk each add near-zero latency. What *does* cost latency is the sequential LLM turns, each waiting 1–4s for generation. Steps 2 and 3 together add ~2–4s of pure generation wait.

This three-turn flow remains the fallback and is never obsolete.

## `include_body` — collapsing to two turns

Opt-in on the scan call. When `include_body=true`, scan returns each matched file's body alongside the path and frontmatter. Claude synthesizes the answer directly from the scan response — no second turn for `read_file`. The flow becomes:

1. Claude emits `scan(..., include_body=true)`.
2. Scan returns paths + bodies; Claude synthesizes the answer.

Two turns instead of three. At typical generation rates that's ~2–4s saved.

**When to use:**

- You expect ≤ 5 matches, AND
- The bodies likely contain the final answer directly (narrow time-bounded lookup, specific subject, single person).
- Example: "what did I discuss with Jane last week" → typically 1–3 1:1 notes, each a few hundred words.

**When NOT to use:**

- Listing / triage queries: "which teams are struggling," "all 1:1s this quarter." Bodies are noise when the answer is a list of pointers. Use paths-only.
- Broad searches that might return many matches. Bodies blow up the context window.
- When you're exploring — fetch paths first, then decide which bodies you actually need.

**Tradeoffs (not a free win):**

- **Input tokens** billed on the next turn. Trivial at personal-tool scale.
- **Prefill time** on the next turn — roughly 200–500ms for modest payloads. Prefill is parallelized, so this is much cheaper than equivalent generation time.
- **Context budget pressure** — the real concern. If bodies push other state out of Claude's working context, reasoning quality drops. This is why guardrails exist.

## Guardrails (enforced in `scripts/scan.py`, not prose)

Skill authors can't bypass these by asking nicely. They live in code.

- **Match-count cap — `MAX_INLINE_MATCHES = 5`.** If the query matches more than 5 files *and* `include_body=true`, scan returns paths-only and sets `truncated_bodies: true` on the response. Bodies are not silently dropped; the response tells the caller to narrow the query or fall back to the paths-only flow.
- **Per-file body cap — `MAX_BODY_BYTES = 4096`.** Each body is truncated at this byte length. The response marks `body_truncated: true` on that match and appends to the body:

  ```
  ... [truncated, N more bytes — use read_file for full content]
  ```

- **Opt-in only.** Default `include_body=false`. A caller must explicitly ask. This keeps the default cheap and makes the optimization a deliberate choice.

## Response shape

Baseline (`include_body=false`):

```json
{
  "matches": [
    {"path": "modules/team-management/state/teams/platform.md", "frontmatter": {...}}
  ]
}
```

With bodies, under the match cap (`include_body=true`):

```json
{
  "matches": [
    {
      "path": "modules/managing-down/state/people/jane/2026-04-15.md",
      "frontmatter": {...},
      "body": "...markdown body, possibly truncated...",
      "body_truncated": false
    }
  ]
}
```

Match cap hit (more than `MAX_INLINE_MATCHES` matches, `include_body=true`):

```json
{
  "truncated_bodies": true,
  "matches": [
    {"path": "...", "frontmatter": {...}}
  ]
}
```

When `truncated_bodies: true` is set, fall back to the three-turn paths-only flow: read the scan result, decide which files matter, call `read_file` on just those.

## Where indexes still earn their keep

There is no persistent listing index. `scan` walks `cto-os-data` directly each call; at current repo sizes this is fast enough that an index wouldn't pay for its own maintenance cost. The two-pass filter (frontmatter-only → selective body read) is the optimization that matters.

---

# Deterministic offload

Any deterministic subtask that an LLM would otherwise do by reading files and reasoning is better done by a Python script. The LLM calls the script, reads the compact result, and reasons on that. This is the principle; the concrete inventory is above in Scripts.

**When to offload — decision rule:**

1. Is the operation *deterministic* (same input → same output, no judgment)? If yes, candidate for offload.
2. Would the naive LLM approach require reading > 3 files or > 2KB of raw text? If yes, offload almost certainly wins on tokens and latency.
3. Is there a stable API upstream (Slack, Linear, Gmail)? If yes, a Python client is faster and cheaper than the corresponding MCP integration for bulk reads.

**Anti-pattern to avoid:** Building a script for every conceivable query. Scripts earn their existence by being called > 2–3 times or by clearly winning on the decision rule above. Everything else stays as skill prose + `scan`.

---

# Schema evolution

When a frontmatter schema changes in `cto-os/meta/schema.md`, existing state files in `cto-os-data` need to migrate. The pattern:

1. Each module tracks its current `schema_version` in `cto-os-data/modules/{slug}/_module.md`.
2. On skill load, the skill compares each module's `schema_version` against the canonical version declared in `meta/schema.md`.
3. If behind, the skill invokes `migrate_{slug}_v{N}_to_v{N+1}.py` in-place on the module's state files.
4. The migration script commits a **pre-migration snapshot** to git before touching anything — rollback is a single `git revert` away.
5. On success, the migration updates `schema_version` in `_module.md`.
6. Multi-step jumps (v1 → v3) run the migrations sequentially.

**No separate backup machinery.** Git is the backup. The pre-migration commit is the restore point.

**Authoring a migration:** drop a new `migrate_{slug}_v{N}_to_v{N+1}.py` in `scripts/`, write a pytest case in `tests/` using fixture data, bump the canonical `schema_version` in `meta/schema.md`. The migration runs automatically the next time any CTO OS surface loads and detects the drift.

---

# Self-maintenance rules (skill side)

Rules for anyone — including Claude Code — evolving the skill repo:

- After adding a new module directory under `cto-os/modules/`: create its `SKILL.md` + `README.md`, and list it in `cto-os/README.md`.
- After adding a script to `cto-os/scripts/`: add a one-line entry to `cto-os/README.md`'s script index and a pytest in `tests/`.
- After renaming a convention or field in `meta/schema.md`: bump the schema version, ship a migration script (see Schema evolution above), and document in the skill repo's changelog.
- After any architectural change: update `docs/ARCHITECTURE.md` / `docs/SKILL_REPO.md` / `docs/DATA_REPO.md` in the same PR. Notion pages are the discussion surface; the repo mirrors are canonical.
