# Schema

Canonical frontmatter schemas for every file in `cto-os-data`. Single source of truth. The data-repo pre-commit hook validates writes against this file.

When this file changes in a way that affects existing state, bump the relevant type's version and ship a migration (`scripts/migrate_{type}_v{N}_to_v{N+1}.py`). See [docs/SKILL_REPO.md → Schema evolution](../docs/SKILL_REPO.md#schema-evolution).

---

## Conventions

- **Frontmatter** is YAML between `---` markers at the top of each `.md` file.
- **`type`** is the discriminator — it selects which schema applies to the file.
- **Type names** are `lowercase-kebab-case`. A leading underscore (`_module`) marks meta files that hold module-level state rather than user content.
- **Required fields** must be present and non-null. **Optional fields** may be absent; the value falls back to the default documented per field.
- **Sensitivity** defaults to `standard`. Files or modules marked `sensitivity: high` are excluded from `scan` results unless the caller explicitly includes them.
- **Module extensions:** each module defines one or more per-type schemas below. Those schemas extend the baseline; they may add required and optional fields but must not contradict the baseline.

---

## Baseline (every frontmatter)

Applies to every `.md` file in `cto-os-data`, regardless of type.

```yaml
type: string          # required; lowercase-kebab-case; discriminator
slug: string          # required; unique within this module's files of the same type; lowercase-kebab-case
updated: date         # required; ISO 8601 (YYYY-MM-DD)
sensitivity: enum     # optional; one of: standard (default), high
```

Notes:
- `slug` uniqueness is scoped per-module per-type. Modules can't collide with each other regardless — they live in separate directories — so no global uniqueness requirement exists.
- `updated` bumps on every write. Modules are responsible for setting it correctly in their write path.
- `sensitivity` on a state file overrides the module-level default (see `_module.md` below).

---

## `_module` — module activation record

Lives at `cto-os-data/modules/{slug}/_module.md`. One per module. Tracks whether the module is active, when it was activated, and the schema version currently in use.

```yaml
type: _module                   # required; literal string "_module"
slug: string                    # required; matches the module directory name
module: string                  # required; same value as slug (explicit for readability)
updated: date                   # required
schema_version: int             # required; the canonical version for this module's types
active: bool                    # required
activated_at: date              # required if ever activated; null before first activation
deactivated_at: date            # required; null if currently active
sensitivity: enum               # optional; module-wide default inherited by state files unless overridden
activation_completed: list[int] # optional; step numbers of the module's activation flow that have finished
```

**Rules:**
- When `active` flips to `true`, set `activated_at` and clear `deactivated_at` (set to `null`).
- When `active` flips to `false`, set `deactivated_at`; leave `activated_at` untouched (history).
- `schema_version` is bumped only by a migration script, never by hand.
- `sensitivity: high` on `_module.md` applies defense-in-depth to every file in this module's `state/` unless a specific file sets its own value.
- Scan excludes `active: false` modules by default; callers must opt in to see inactive state.
- **`activation_completed`** is the authoritative resumption signal. File-presence is a useful secondary check (most steps write a concrete artifact), but a step is "done" only when its number is in this list. This handles edge cases cleanly: steps with branching answers captured into a shared file, multiple steps that target the same file, or steps with only behavioral effects. When omitted or empty, activation hasn't started.

**Current version:** 1.

---

## Per-module types

Each module introduces one or more types. Their schemas are defined under a `## <type>` heading, following the same shape as `_module` above.

When a module adds a type:

1. Add a `## <type>` section with the YAML block.
2. Declare required and optional fields; don't restate baseline fields.
3. Document any invariants (e.g., "one file per `person-slug` per `date`").
4. Add the type to the version table below with version `1`.
5. Set the owning module's `schema_version` in `_module.md` accordingly.

---

## `altitude`

The user's role altitude. One per user; owned by `personal-os`.

```yaml
level: enum        # required; one of: director, vp, svp, c-level
context: string    # required; one-line descriptor of the role's shape
```

Invariant: exactly one file per user at `state/altitude.md` with `slug: current`.

**Current version:** 1.

---

## `goal-horizon`

Personal goals at one of three horizons: annual, quarterly, or weekly. Owned by `personal-os`. One file per horizon; each updates on its own cadence without touching the others.

```yaml
horizon: enum        # required; one of: annual, quarterly, weekly. Same value as slug — explicit discriminator for scan.
period: string       # required; "2026" for annual, "2026-Q2" for quarterly, "2026-W16" for weekly
items: list[string]  # required; the goals themselves
```

Invariants:
- Files live at `state/goals/{annual|quarterly|weekly}.md`.
- `slug` equals `horizon`.
- Each file holds its own reverse-chronological snapshots under `## History` in the body.

**Current version:** 1.

---

## `show-up`

Declarative statement of how the user wants to show up as a leader. Owned by `personal-os`.

No required fields beyond baseline. Body carries the content: posture paragraph, concrete behaviors list, anti-patterns list, followed by `## History` for prior versions.

Invariant: exactly one file per user at `state/show-up.md` with `slug: current`.

**Current version:** 1.

---

## `voice-sample`

A chunk of the user's writing used by comms-generating modules to emulate tone. Owned by `personal-os`.

```yaml
register: string   # required; e.g., casual, formal-internal, board-facing, technical
source: string     # optional; where the sample came from (e.g., "Slack post 2026-03-15")
```

Invariants:
- Files live at `state/voice/{YYYY-MM-DD}.md` (or `{YYYY-MM-DD}-N.md` if multiple in one day).
- `slug` equals the filename stem.
- Body ≥ 100 words (activation gate; runtime skill can relax).

**Current version:** 1.

---

## `daily-briefing`

A morning briefing produced by `attention-operations`. One file per calendar day.

No required fields beyond baseline. Body has three sections: `## Since last` (delta from the previous briefing), `## Today` (agenda, key meetings, open decisions), `## Open threads` (carry-overs).

Invariants:
- Files live at `state/briefings/{YYYY-MM-DD}.md`.
- `slug` equals the filename stem.

**Current version:** 1.

---

## `weekly-starter`

Monday look-forward produced by `attention-operations`. One per ISO week.

```yaml
period: string     # required; ISO week in "YYYY-W##" form (e.g., "2026-W16")
```

Body sections: `## Priorities`, `## Key meetings`, `## Decisions coming up`, `## Carry-over`.

Invariants:
- Files live at `state/weekly/{YYYY-W##}-starter.md`.
- `slug` equals the filename stem (`<YYYY-W##>-starter`).

**Current version:** 1.

---

## `weekly-wrap`

Friday look-back produced by `attention-operations`. One per ISO week.

```yaml
period: string     # required; ISO week in "YYYY-W##" form
```

Body sections: `## Shipped`, `## Decisions made`, `## Carry-over to next week`, `## Open items`.

Invariants:
- Files live at `state/weekly/{YYYY-W##}-wrap.md`.
- `slug` equals the filename stem (`<YYYY-W##>-wrap`).

**Current version:** 1.

---

## `rhythm`

User's declared daily and weekly operational cadence. Owned by `attention-operations`.

```yaml
daily_mode: enum         # required; one of: async (Cowork-delivered), on-demand
weekly_events: list      # required; subset of ["starter", "wrap"]; may be empty to skip both
priority_order: list     # required; ranked source surfaces (e.g., ["slack-dms", "email", "linear-prs", "slack-channels"])
```

Invariant: exactly one file per user at `state/rhythm.md` with `slug: current`. Prior versions preserved under `## History` in body.

**Current version:** 1.

---

## `triage-rules`

Ruleset for classifying incoming signal as attention-needed vs FYI. Owned by `attention-operations`.

```yaml
rules: list        # required; each entry is {pattern: string, category: enum(attention-needed|fyi), condition?: string}
```

Invariants:
- Exactly one file per user at `state/triage-rules.md` with `slug: current`.
- `rules` has ≥ 3 entries after activation.
- Prior versions preserved under `## History` in body.

**Current version:** 1.

---

## `attention-sources`

Declared integration sources (Slack workspaces, Gmail scopes, Linear workspaces) this module reads from. Owned by `attention-operations`.

```yaml
sources: list      # required; each entry is {kind: enum(slack|gmail|linear|other), identifier: string, scope: string}
```

Invariants:
- Exactly one file per user at `state/sources.md` with `slug: current`.
- `sources` has ≥ 1 entry after activation.
- Prior versions preserved under `## History` in body.

**Current version:** 1.

---

## `company-goal-horizon`

Company goals at annual or quarterly horizon. Owned by `business-alignment`. One file per horizon.

```yaml
horizon: enum           # required; one of: annual, quarterly
period: string          # required; "2026" for annual, "2026-Q2" for quarterly
items: list[string]     # required; the goals themselves
owner: string           # optional; typically "CEO" or the company-level owner
```

Invariants:
- Files live at `state/company-goals/{annual|quarterly}.md`.
- `slug` equals `horizon`.
- Prior versions preserved under `## History` in body.

**Current version:** 1.

---

## `signal-sources`

Declared sources of external customer signal (which customer-facing teams/channels to watch). Owned by `business-alignment`.

```yaml
sources: list    # required; each entry is {source_type: sales|marketing|support|onboarding|other, identifier: string, scope: string}
```

Invariants: singleton at `state/signal-sources.md` with `slug: current`. `sources` has ≥ 1 entry after activation. Prior versions preserved under `## History` in body.

**Current version:** 1.

---

## `customer-signal`

A single piece of external signal captured from a customer-facing team or direct customer interaction. Owned by `business-alignment`.

```yaml
source: string            # required; slug of the source (sales/support/marketing/etc.)
channel: string           # required; free-text — "conversation with CS lead", "support ticket trend", etc.
job_to_be_done: string    # optional; JTBD tag when identifiable
implication: string       # required; one-sentence summary of what the signal means for us
```

Invariants:
- Files live at `state/signals/{YYYY-MM-DD}-{source-slug}.md`.
- `slug` equals the filename stem.

**Current version:** 1.

---

## `customer-engagement`

A single CTO-level customer engagement event. Owned by `business-alignment`.

```yaml
engagement_type: enum     # required; one of: advisory-board, sales-call, exec-sponsor, escalation, industry-event, other
customer: string          # required; customer identifier (slug-style)
outcomes: list[string]    # required; what came out of the engagement — commitments, follow-ups, decisions
```

Invariants:
- Files live at `state/engagements/{YYYY-MM-DD}-{customer-slug}.md`.
- `slug` equals the filename stem.

**Current version:** 1.

---

## `engagement-cadence`

Declared CTO customer-engagement cadence per engagement type. Owned by `business-alignment`.

```yaml
cadences: list    # required; each entry is {engagement_type: enum, target_frequency: string}
```

Invariants: singleton at `state/engagement-cadence.md` with `slug: current`. Prior versions preserved under `## History` in body.

**Current version:** 1.

---

## `work-mapping`

Mapping of current engineering initiatives to the company goals they ladder to. Owned by `business-alignment`.

```yaml
mappings: list    # required; each entry is {initiative: string, goal: string, confidence: low|medium|high}
```

Invariants: singleton at `state/work-mapping.md` with `slug: current`. `mappings` has ≥ 1 entry after activation. Prior versions preserved under `## History` in body.

**Current version:** 1.

---

## `flow`

A declared operating flow (PM, SDLC, DS, or custom) with definition, measurement sources, and current metrics. Owned by `process-management`. One file per flow.

```yaml
flow_type: enum               # required; one of: pm, sdlc, ds, custom
owner: string                 # required; which team or role owns this flow
sources: list                 # required; each entry {source_type: string, identifier: string, mode: automated|manual}
cycle_time_days: number       # optional; current measurement
lead_time_days: number        # optional
wip: number                   # optional; units in progress
throughput_per_week: number   # optional
last_measured: date           # optional
```

Invariants:
- Files live at `state/flows/{flow-slug}.md`.
- `slug` equals the flow slug.
- Prior definitions + measurements preserved under `## History` in body.

**Current version:** 1.

---

## `flow-retro`

A retrospective on a specific flow. Owned by `process-management`.

```yaml
flow: string      # required; the flow slug this retro is about
period: string    # required; human description of what the retro covers (e.g., "Q2 2026")
```

Invariants:
- Files live at `state/retros/{flow-slug}/{YYYY-MM-DD}.md`.
- `slug` equals `<flow-slug>-<YYYY-MM-DD>`.
- Body sections: `## Went well`, `## Impeded flow`, `## Reinertsen categories`, `## To try next`.

**Current version:** 1.

---

## `bottleneck`

A bottleneck observation in a named flow, classified per Reinertsen. Owned by `process-management`. One file per bottleneck — status transitions live in the same file's history.

```yaml
flow: string          # required; flow slug this bottleneck is in
status: enum          # required; one of: open, mitigated, resolved
category: enum        # required; one of: queue, batch-size, wip, variability, cadence, other
opened: date          # required; when the bottleneck was first logged
resolved: date        # optional; when marked resolved (or mitigated)
```

Invariants:
- Files live at `state/bottlenecks/{bottleneck-slug}.md`.
- `slug` equals the filename stem.
- Prior statuses and resolution notes preserved under `## History` in body.

**Current version:** 1.

---

## `team`

A team record — metadata plus current health-rubric scores. Owned by `team-management`. One file per team.

```yaml
active: bool                # required; false when deprecated/disbanded
lead: string                # required
mission: string             # required; one-line team mission
size: int                   # required; current headcount
topology: enum              # required; one of: stream-aligned, enabling, complicated-subsystem, platform
retro_cadence: string       # required; e.g., "weekly", "monthly", "quarterly"
scores: dict                # optional; keys match rubric dimensions; values are ints 1–5
```

Invariants:
- Files live at `state/teams/{team-slug}.md`.
- `slug` equals the team slug.
- Body holds `## History` with dated metadata changes *and* scoring snapshots.
- Scan excludes `active: false` teams by default.

**Current version:** 1.

---

## `team-retro`

A team retrospective in 4Ls format (Liked / Learned / Lacked / Longed for). Owned by `team-management`. Same body structure as `retro-personal`; different subject and scope.

```yaml
team: string      # required; team slug
period: string    # required; human description of what the retro covers
```

Invariants:
- Files live at `state/retros/{team-slug}/{YYYY-MM-DD}.md`.
- `slug` equals `<team-slug>-<YYYY-MM-DD>`.
- Body sections: `## Liked`, `## Learned`, `## Lacked`, `## Longed for`.

Kept module-scoped alongside `retro-personal` and `flow-retro`. If all retros converge on identical structure, consolidate into a shared `retro` type via migration later.

**Current version:** 1.

---

## `team-rubric`

Singleton rubric definition used to score all teams on the same dimensions. Owned by `team-management`.

```yaml
scale: string       # required; always "1-5" in v1 (per the cross-cutting rubric pattern)
dimensions: list    # required; each entry {name: string, description: string}
```

Invariants: singleton at `state/rubric.md` with `slug: current`. `dimensions` has ≥ 3 entries. Prior versions preserved under `## History` in body.

**Current version:** 1.

---

## `stakeholder-profile`

A lightweight profile of a person the user works with. **Shared type** used across `managing-up`, `managing-down`, and `managing-sideways`; each module writes its own files (module-scoped slug uniqueness applies).

```yaml
active: bool                         # optional; defaults true. false marks departed/removed stakeholders
name: string                         # required; person's full name (free-text)
role: string                         # required; role or title
relationship: enum                   # required; one of: direct-manager, skip-level, dotted-line, direct-report, peer, other
function: string                     # optional; peer's function (managing-sideways only)
collaboration_area: string           # optional; what this peer collaborates on (managing-sideways only)
tenure_months: int                   # optional; how long they've reported to the user (managing-down only)
departed_date: date                  # optional; set when active flips to false
cadence: string                      # optional; 1:1 cadence description
agenda_owner: enum                   # optional; self | them | shared (managing-up, managing-down)
meeting_style: enum                  # optional; scheduled | opportunistic (managing-sideways)

# Cross-cutting stakeholder-profile fields (all optional; per PRD, fields can be empty):
communication_preferences: string    # channel / cadence / format preferences
what_they_want_first: string         # numbers / stories / risks / options
typical_concerns: list               # recurring topics they push on
context_needs: string                # how much background before the ask
known_sensitivities: list            # heated topics, past incidents to avoid repeating
relationship_status: string          # current state of trust, open threads
currencies: list                     # Cohen/Bradford currency analysis (managing-sideways)
```

Invariants:
- Files live at `state/people/{person-slug}.md` within the owning module.
- `slug` equals the person slug (kebab-case).
- Scan excludes `active: false` files by default.
- Prior profile versions preserved under `## History` in body when fields change materially.

**Current version:** 1.

---

## `boss-1on1`

A 1:1 meeting with an upward stakeholder. Owned by `managing-up`.

```yaml
person: string       # required; stakeholder slug the 1:1 is with
```

Invariants:
- Files live at `state/1on1s/{person-slug}/{YYYY-MM-DD}.md`.
- `slug` equals `<person-slug>-<YYYY-MM-DD>`.
- Body sections: `## Topics`, `## Decisions`, `## Follow-ups`, `## Signals`.

**Current version:** 1.

---

## `report-1on1`

A 1:1 meeting with a direct report. Owned by `managing-down`. Structurally identical to `boss-1on1` today; kept as a distinct type because module scope and sensitivity differ, and domain may diverge over time.

```yaml
person: string       # required; report slug the 1:1 is with
```

Invariants:
- Files live at `state/1on1s/{person-slug}/{YYYY-MM-DD}.md`.
- `slug` equals `<person-slug>-<YYYY-MM-DD>`.
- Body sections: `## Topics`, `## Decisions`, `## Follow-ups`, `## Signals`.

**Current version:** 1.

---

## `peer-1on1`

A 1:1 meeting with a peer. Owned by `managing-sideways`. Same body structure as `boss-1on1` / `report-1on1`; `## Signals` tends to capture currency and coalition movement rather than coaching signals.

```yaml
person: string       # required; peer slug the 1:1 is with
```

Invariants:
- Files live at `state/1on1s/{person-slug}/{YYYY-MM-DD}.md`.
- `slug` equals `<person-slug>-<YYYY-MM-DD>`.
- Body sections: `## Topics`, `## Decisions`, `## Follow-ups`, `## Signals`.

**Current version:** 1.

---

## `coaching-event`

A coaching or feedback moment with a direct report that happens *outside* a scheduled 1:1. Owned by `managing-down`. Distinct from `report-1on1` because it's bite-sized and in-the-moment, and it needs to be findable for Performance & Development roll-ups later.

```yaml
person: string       # required; report slug
event_type: enum     # required; one of: feedback, recognition, delegation, course-correct, other
```

Invariants:
- Files live at `state/coaching/{person-slug}/{YYYY-MM-DD}.md`.
- `slug` equals `<person-slug>-<YYYY-MM-DD>`.
- Body follows the Radical Candor structure: observation, impact, ask.

**Current version:** 1.

---

## `retro-personal`

A personal retrospective in 4Ls format (Liked / Learned / Lacked / Longed for). Owned by `personal-os`.

```yaml
period: string     # required; human description of what the retro covers (e.g., "week ending 2026-04-21")
```

Invariants:
- Files live at `state/retros/{YYYY-MM-DD}.md`.
- `slug` equals the filename stem.
- Body contains four sections: `## Liked`, `## Learned`, `## Lacked`, `## Longed for`.

Kept module-scoped (vs. a shared `retro` type) until other modules add retros — then consolidate via migration.

**Current version:** 1.

---

## Schema versions

Current canonical version per type.

| Type | Version | Introduced by |
| --- | --- | --- |
| `_module` | 1 | baseline |
| `altitude` | 1 | `personal-os` |
| `goal-horizon` | 1 | `personal-os` |
| `show-up` | 1 | `personal-os` |
| `voice-sample` | 1 | `personal-os` |
| `retro-personal` | 1 | `personal-os` |
| `daily-briefing` | 1 | `attention-operations` |
| `weekly-starter` | 1 | `attention-operations` |
| `weekly-wrap` | 1 | `attention-operations` |
| `rhythm` | 1 | `attention-operations` |
| `triage-rules` | 1 | `attention-operations` |
| `attention-sources` | 1 | `attention-operations` |
| `company-goal-horizon` | 1 | `business-alignment` |
| `signal-sources` | 1 | `business-alignment` |
| `customer-signal` | 1 | `business-alignment` |
| `customer-engagement` | 1 | `business-alignment` |
| `engagement-cadence` | 1 | `business-alignment` |
| `work-mapping` | 1 | `business-alignment` |
| `flow` | 1 | `process-management` |
| `flow-retro` | 1 | `process-management` |
| `bottleneck` | 1 | `process-management` |
| `team` | 1 | `team-management` |
| `team-retro` | 1 | `team-management` |
| `team-rubric` | 1 | `team-management` |
| `stakeholder-profile` | 1 | `managing-up` / `managing-down` / `managing-sideways` (shared) |
| `boss-1on1` | 1 | `managing-up` |
| `report-1on1` | 1 | `managing-down` |
| `peer-1on1` | 1 | `managing-sideways` |
| `coaching-event` | 1 | `managing-down` |

Version bumps ship with a migration at `scripts/migrate_{type}_v{N}_to_v{N+1}.py`. The migration runs automatically the next time a surface loads and detects drift; it commits a pre-migration snapshot to git so rollback is `git revert`.
