---
name: code-contribution
description: "Activates for identifying and tracking the user's own hands-on technical contribution — where to dive in, what to pick up, and whether actual contribution is happening at the target rate. Covers: scanning open PRs, Linear tickets, and repo activity to surface contribution opportunities that match user-declared preferences (architecturally important spots, knotty bugs, learning opportunities, reliability gaps); logging contributions the user actually picked up (for longitudinal tracking of what kind of work they're engaging with); showing trends (am I hitting my target cadence or drifting into pure management). Also activates on oblique phrasings like 'scan the PRs this week,' 'find me something interesting to dive into,' 'I haven't shipped code in a month,' 'where should I spend an afternoon hacking,' 'show my contribution trend.' Does NOT activate on strategic technical direction (Technical Strategy); routine PR review as part of team leadership (Managing Down owns the coaching side of PR review); reliability operations (Tech Ops — though reliability gaps can surface here as contribution opportunities); or flow and process measurement (Process Management)."
requires: []
optional:
  - personal-os
  - technical-strategy
  - tech-ops
  - process-management
---

# Code Contribution Opportunities

## Scope

Staying technically engaged at the right level for a senior engineering leader. Identifies where hands-on contribution creates disproportionate value — knotty problems, architecturally important spots, learning opportunities, reliability gaps. Logs what the user actually picks up. Tracks trend vs. declared cadence. Optional-by-role module — meaningful for leaders who want to stay technical; skippable for those whose role or stage doesn't support it.

Deliberately light module. Most state is per-contribution logging; the scanning half is mostly read-time against integrations cache.

## Out of scope

- **Strategic technical direction** — Technical Strategy.
- **Routine PR review as coaching** — Managing Down owns the coaching side of PR review (giving feedback to a report on their PR). This module is about *the user's own* hands-on contribution.
- **Reliability operations** — Tech Ops. Reliability *gaps* can surface here as contribution opportunities, but the ongoing ops work is Tech Ops's.
- **Flow and process measurement** — Process Management.
- **Code-contribution metrics at the org level** — Process Management / Team Management own team-level throughput metrics; this module only tracks the user's individual contributions.

## Frameworks

- [Donald Reinertsen — *The Principles of Product Development Flow*](https://www.amazon.com/Principles-Product-Development-Flow-Generation/dp/1935401009) — applied here as an opportunity-spotting lens, not as a primary framework.
  - *How this module applies it:* when scanning for opportunities, prioritize work that unsticks flow — bottlenecks a senior hand could dislodge, knotty problems that cost junior engineers disproportionate time, architectural decisions that need someone with broad context. The marginal-value-of-contribution frame: where would *this* contributor (senior, broad, limited hours) create the most value? Not the same as "what needs doing most" — it's "where is my contribution worth most."

## Triggers

- "scan the PRs open this week"
- "find me an architecturally interesting ticket"
- "what's a knotty bug worth diving into"
- "where should I spend an afternoon hacking"
- "log the contribution I just picked up"
- "I shipped [PR] — log it"
- "show my contribution trend" / "am I on target"
- "update my contribution preferences"
- "add / remove a source repo"
- Oblique: "I haven't shipped code in a month"
- Oblique: "nudge me — I need to stay technical"

## Activation flow

Each step writes a concrete artifact and appends its step number to `activation_completed` in `_module.md`.

### 1. Declare contribution preferences

**Ask:** "What's your target contribution cadence and shape? (a) Target — a number (e.g., 'one PR per quarter,' '5 hours/week hands-on,' 'at least one architectural contribution per year') or a rhythm statement. (b) Preferred types — architectural contributions, knotty bug fixes, learning opportunities (new systems or languages), reliability gaps, platform improvements. Rank or pick the top 2–3. (c) Anti-patterns — what you explicitly don't want to pick up (e.g., 'not routine feature work,' 'not anything your team would do better without you')."
**Writes:** `cto-os-data/modules/code-contribution/state/preferences.md` with `type: contribution-preferences`, `slug: current`, `target_cadence`, `preferred_types`, `anti_patterns`.
**Expects:** frontmatter `target_cadence` and `preferred_types` set; `anti_patterns` optional but encouraged.

### 2. Declare repo/source scope

**Ask:** "Which repos and sources should `scan-for-opportunities` pull from? Typically: GitHub repos you want to be active in (not everything — pick the 2–5 that matter most for staying technical), Linear projects or views if that's where tickets surface, specific domains (e.g., 'platform repos only, not product'). Also: where are open PRs pulled from — your own org's GitHub, or broader?"
**Writes:** `cto-os-data/modules/code-contribution/state/sources.md` with `type: contribution-sources`, `slug: current`, `sources` list.
**Expects:** frontmatter `sources` has ≥ 1 entry with `source_type`, `identifier`, and `scope`.

## Skills

### `scan-for-opportunities`

**Purpose:** Read from the integrations cache (GitHub PRs, Linear tickets, Tech Ops reliability gaps) and surface a ranked list of opportunities that fit the declared preferences. Read-only; no persistent output. Ephemeral suggestions that the user acts on (or doesn't).

**Triggers:**
- "scan the PRs this week"
- "find me something to dive into"
- "what's open that I could help with"

**Reads:**
- `cto-os-data/modules/code-contribution/state/preferences.md`
- `cto-os-data/modules/code-contribution/state/sources.md`
- `cto-os-data/integrations-cache/linear/`, `cto-os-data/integrations-cache/github/` (if applicable)
- `cto-os-data/modules/tech-ops/state/incidents/`, `cto-os-data/modules/tech-ops/state/postmortems/` (optional — reliability gaps surface as opportunities)
- `cto-os-data/modules/technical-strategy/state/tech-debt/` (optional — tech debt items the user could personally take)
- `cto-os-data/modules/personal-os/state/goals/weekly.md` (optional — alignment check)

**Writes:** —  (ephemeral; if the user picks something up, they log it via `log-contribution`)

### `log-contribution`

**Purpose:** Capture a contribution the user actually picked up — PR authored, bug they personally fixed, architectural doc they wrote. Records what it was, what type, what value it created (in their judgment), and any follow-ups.

**Triggers:**
- "log the contribution I picked up"
- "I shipped [PR]"
- "captured this fix"
- "wrote the [doc/ADR] — log it"

**Reads:**
- `cto-os-data/modules/code-contribution/state/preferences.md` (tag-against-preference check)
- `cto-os-data/modules/code-contribution/state/log/` (recent contributions for context)

**Writes:** `cto-os-data/modules/code-contribution/state/log/{YYYY-MM-DD}-{contribution-slug}.md`, append-new-file.

### `update-preferences`

**Purpose:** Revise contribution preferences — changed target cadence, new preferred types, updated anti-patterns.

**Triggers:**
- "update my contribution preferences"
- "change my target to [cadence]"
- "I'm going to focus on architectural work this quarter"

**Reads:** `cto-os-data/modules/code-contribution/state/preferences.md`.

**Writes:** `cto-os-data/modules/code-contribution/state/preferences.md`, overwrite-with-history.

### `update-sources`

**Purpose:** Revise declared sources — add a repo, remove one, change scope.

**Triggers:**
- "add [repo] to my contribution sources"
- "remove [repo] — not relevant anymore"
- "narrow scope to platform repos"

**Reads:** `cto-os-data/modules/code-contribution/state/sources.md`.

**Writes:** `cto-os-data/modules/code-contribution/state/sources.md`, overwrite-with-history.

### `show-contribution-trend`

**Purpose:** Assemble a read-time view of contributions over time — count by quarter, distribution across preferred types vs. anti-patterns, time-since-last-contribution, alignment with declared target cadence.

**Triggers:**
- "show contribution trend"
- "am I on target"
- "how much have I contributed this quarter"

**Reads:**
- `cto-os-data/modules/code-contribution/state/preferences.md` (target cadence for comparison)
- `scan(type=["contribution-log-entry"], fields=["slug", "contribution_type", "delivered_date", "fit_preference"])`

**Writes:** —

## Persistence

- **`cto-os-data/modules/code-contribution/state/preferences.md`** — singleton (`slug: current`), overwrite-with-history. Frontmatter: `type: contribution-preferences, slug: current, updated: <date>, target_cadence: <string>, preferred_types: <list>, anti_patterns: <list>`. Body: rationale + `## History`.
- **`cto-os-data/modules/code-contribution/state/sources.md`** — singleton (`slug: current`), overwrite-with-history. Frontmatter: `type: contribution-sources, slug: current, updated: <date>, sources: <list of {source_type, identifier, scope}>`. Body: notes + `## History`.
- **`cto-os-data/modules/code-contribution/state/log/{YYYY-MM-DD}-{contribution-slug}.md`** — append-new-file per contribution. Frontmatter: `type: contribution-log-entry, slug: <YYYY-MM-DD>-<contribution-slug>, updated: <date>, contribution_type: <architectural|bug-fix|learning|reliability|platform|other>, artifact_link: <string, optional>, delivered_date: <date>, effort_hours: <number, optional>, fit_preference: <bool>, value_notes: <string, optional>`. Body: what was done, why, any follow-ups.

**Overrides to the cross-cutting save rule** ([Persistence model](../../docs/ARCHITECTURE.md#persistence-model)): none — inherits the default.

**Sensitivity:** standard. Nothing sensitive here generally.

## State location

`cto-os-data/modules/code-contribution/state/`
