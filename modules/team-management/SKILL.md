---
name: team-management
description: "Activates for team-aggregate health, team-level metadata, team retros, and composition tracking across the teams in the user's org. Covers: enumerating and updating teams (lead, mission, size, Team Topologies type), scoring team health on a standardized 5-point rubric, logging team retros in 4Ls format, tracking scores as a time series. Also activates on oblique phrasings like 'how is team X doing,' 'platform team seems stuck,' 'we need to rebalance headcount,' 'log retro for growth squad,' 'which teams are struggling.' Does NOT activate on individual-level performance (Performance & Development), direct-report coaching or 1:1s (Managing Down), strategic team structure changes (Org Design owns those decisions — this module tracks current reality), or personal retros (Personal OS)."
requires: []
optional:
  - hiring
  - performance-development
---

# Team Management

## Scope

The ongoing health and performance of the teams in your org, at the team-aggregate level. How each team is doing against its rubric, how it's staffed, how it's evolving. Daily driver — operational hub that Performance & Development and Managing Down optionally consume for roll-up views.

## Out of scope

- **Individual performance and development** — Performance & Development.
- **1:1 coaching and direct-report leadership** — Managing Down.
- **Strategic team structure changes** — Org Design (decisions); this module tracks current reality, not proposed reality.
- **Personal retros** — Personal OS.
- **Hiring execution** — Hiring owns the pipeline; this module tracks landed and departing headcount.

## Frameworks

- [Matthew Skelton & Manuel Pais — *Team Topologies*](https://teamtopologies.com/) — four team types (stream-aligned, enabling, complicated-subsystem, platform) and interaction modes between teams.
  - *How this module applies it:* each team's frontmatter carries `topology: stream-aligned | enabling | complicated-subsystem | platform`. Set at team enumeration and updated when composition or purpose changes. Interaction modes (collaboration, X-as-a-Service, facilitating) aren't tracked in frontmatter — too much noise and they fluctuate — but get captured in team-retro bodies when they surface as a friction point.

- [Patrick Lencioni — *The Five Dysfunctions of a Team*](https://www.tablegroup.com/product/dysfunctions/) — trust, conflict, commitment, accountability, results as the diagnostic hierarchy.
  - *How this module applies it:* diagnostic lens, not a literal scoring mapping. The five dysfunctions inform *what to look for* when team health scores drop: low accountability often means the trust/conflict foundation is shaky. Rubric dimensions default to more-measurable proxies (velocity, morale, quality, delivery predictability, clarity of direction); Lencioni concepts show up in retro discussion when scores are ambiguous.

## Triggers

- "score team X" / "team health for platform"
- "log team retro" / "retro for growth squad"
- "add a new team" / "we're spinning up [team]"
- "update [team]" / "[team] got a new lead"
- "how's [team] trending" / "which teams are struggling"
- "show me team health across the org"
- Oblique: "I'm worried about [team]" / "[team] seems stuck" / "[team]'s delivery feels off"

## Activation flow

Each step writes a concrete artifact and appends its step number to `activation_completed` in `_module.md`.

### 1. Enumerate teams with baseline metadata

**Ask:** "Walk me through the teams in your org. For each: short slug (kebab-case), lead's name, one-line mission, current headcount, and which Team Topologies type it is (stream-aligned / enabling / complicated-subsystem / platform). If unsure on the topology, default to stream-aligned — that's where most product teams live."
**Writes:** one file per team at `cto-os-data/modules/team-management/state/teams/{team-slug}.md` with `type: team`, `slug: <team-slug>`, `lead`, `mission`, `size`, `topology`.
**Expects:** at least one team file exists with all four required fields populated.

### 2. Declare team-health rubric (or accept default)

**Ask:** "The default team-health rubric has five dimensions scored 1–5: **velocity** (throughput vs capacity), **morale** (observable energy and engagement), **quality** (defect rate, rework, craft), **delivery predictability** (hitting stated dates), **clarity of direction** (team knows why they're doing what they're doing). Keep the default, customize the dimensions, or define your own? Rubric lives at the module level — all teams get scored against the same dimensions."
**Writes:** `cto-os-data/modules/team-management/state/rubric.md` with `type: team-rubric`, `slug: current`, `dimensions` list.
**Expects:** frontmatter `dimensions` has ≥ 3 entries; `scale: "1-5"`.

### 3. Establish retro cadence per team

**Ask:** "What's the retro cadence per team? Common: weekly for daily-driver teams, monthly for platform, quarterly for enabling. Set a default plus per-team overrides if any team is different. These are reminders; the module doesn't enforce — `log-team-retro` works any time."
**Writes:** updates each team file at `cto-os-data/modules/team-management/state/teams/{team-slug}.md` with `retro_cadence` field in frontmatter.
**Expects:** every team file has `retro_cadence` set (default, or custom).

## Skills

### `add-team`

**Purpose:** Create a new team record, post-activation. For when a team spins up or the user didn't enumerate it during activation.

**Triggers:**
- "add a new team: [name]"
- "we just stood up [team]"

**Reads:**
- `cto-os-data/modules/team-management/state/teams/` (check for slug collision)
- `cto-os-data/modules/team-management/state/rubric.md` (so the new team gets initialized with the rubric dimensions)

**Writes:** `cto-os-data/modules/team-management/state/teams/{team-slug}.md`, append-new-file.

### `update-team`

**Purpose:** Change team metadata — new lead, new mission, new size, topology change.

**Triggers:**
- "update [team]"
- "[team] has a new lead"
- "[team] grew to 8 people"
- "[team] is becoming a platform team"

**Reads:** `cto-os-data/modules/team-management/state/teams/{team-slug}.md`.

**Writes:** `cto-os-data/modules/team-management/state/teams/{team-slug}.md`, overwrite-with-history (prior metadata preserved in body under `## History`).

### `deprecate-team`

**Purpose:** Mark a team as no longer active (disbanded, absorbed, reorged). Preserves history — file stays on disk, but scan excludes it by default.

**Triggers:**
- "[team] is being disbanded"
- "deprecate [team]"
- "[team] absorbed into [other-team]"

**Reads:** `cto-os-data/modules/team-management/state/teams/{team-slug}.md`.

**Writes:** `cto-os-data/modules/team-management/state/teams/{team-slug}.md` — sets `active: false`, records reason and date in body history.

### `score-team`

**Purpose:** Run the team-health rubric against a specific team. Captures current scores and preserves the prior scores in history.

**Triggers:**
- "score team X"
- "team health for [team]"
- "run the rubric on [team]"

**Reads:**
- `cto-os-data/modules/team-management/state/rubric.md` (dimensions being scored)
- `cto-os-data/modules/team-management/state/teams/{team-slug}.md` (current scores for delta context)
- `cto-os-data/modules/team-management/state/retros/{team-slug}/` (recent retros for signal)

**Writes:** `cto-os-data/modules/team-management/state/teams/{team-slug}.md` — updates `scores` dict in frontmatter, appends dated scoring snapshot to body history.

### `log-team-retro`

**Purpose:** Capture a team retro in 4Ls format (Liked / Learned / Lacked / Longed for). Reuses the same retro convention as Personal OS — different subject, same structure.

**Triggers:**
- "log team retro for [team]"
- "retro on growth squad's sprint"
- "[team] wrapped their quarter — capture a retro"

**Reads:**
- `cto-os-data/modules/team-management/state/teams/{team-slug}.md` (team context)
- `cto-os-data/modules/team-management/state/retros/{team-slug}/` (prior retros)

**Writes:** `cto-os-data/modules/team-management/state/retros/{team-slug}/{YYYY-MM-DD}.md`, append-new-file.

### `show-team-health`

**Purpose:** Assemble a read-time summary of all active teams' current rubric scores, with trend deltas from last scoring if available.

**Triggers:**
- "show team health"
- "which teams are struggling"
- "team health across the org"
- "rollup on all teams"

**Reads:** `scan(type=["team"], where={"active": true}, fields=["slug", "lead", "size", "topology", "scores", "updated"])`.

**Writes:** —

## Persistence

- **`cto-os-data/modules/team-management/state/teams/{team-slug}.md`** — one file per team, overwrite-with-history. Frontmatter: `type: team, slug: <team-slug>, updated: <date>, active: <bool>, lead: <string>, mission: <string>, size: <int>, topology: <stream-aligned|enabling|complicated-subsystem|platform>, retro_cadence: <string>, scores: <dict, keys match rubric dimensions>`. Body: description + `## History` with dated metadata changes and scoring snapshots (both lifecycle types preserved in the same file per the "one file per unit" pattern).
- **`cto-os-data/modules/team-management/state/retros/{team-slug}/{YYYY-MM-DD}.md`** — append-new-file per team retro. Frontmatter: `type: team-retro, slug: <team-slug>-<YYYY-MM-DD>, updated: <date>, team: <team-slug>, period: <string>`. Body: four sections — `## Liked`, `## Learned`, `## Lacked`, `## Longed for`, matching Personal OS's `retro-personal` structure.
- **`cto-os-data/modules/team-management/state/rubric.md`** — singleton (`slug: current`), overwrite-with-history. Frontmatter: `type: team-rubric, slug: current, updated: <date>, scale: "1-5", dimensions: <list of {name, description}>`. Body: optional prose on how to score each dimension, followed by `## History`.

**Overrides to the cross-cutting save rule** ([Persistence model](../../docs/ARCHITECTURE.md#persistence-model)): none — inherits the default.

## State location

`cto-os-data/modules/team-management/state/`
