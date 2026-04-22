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

## `reliability-posture`

Singleton declaration of the org's reliability philosophy and policy. Owned by `tech-ops`.

```yaml
slo_coverage_target: string    # required; e.g., "all tier-1 services" or "top 10 user journeys"
severity_scale: list           # required; entries like ["S1", "S2", "S3", "S4"] with thresholds
postmortem_triggers: list      # required; which severities require postmortems
on_call_tool: string           # required; PagerDuty, Opsgenie, Incident.io, etc.
error_budget_policy: string    # required; prose describing what happens when a budget burns
toil_target: string            # optional; e.g., "<30% of eng time is toil"
```

Invariants: singleton at `state/reliability-posture.md` with `slug: current`. Prior versions preserved under `## History`.

**Current version:** 1.

---

## `slo`

A service-level objective with target, current reading, and error-budget state. Owned by `tech-ops`. One file per SLO.

```yaml
service: string              # required; the service or user journey this SLO covers
target: string               # required; e.g., "99.9% over 30 days"
current: string              # optional; current observed reading
error_budget_remaining: string  # optional; e.g., "62%"
measurement_source: string   # required; Datadog, Prometheus, custom, manual
last_measured: date          # optional
```

Invariants:
- Files live at `state/slos/{slo-slug}.md`.
- `slug` equals the SLO slug.
- Prior measurements preserved under `## History` in body.

**Current version:** 1.

---

## `incident`

An incident record tracking the lifecycle from detection through resolution. Owned by `tech-ops`. One file per incident. Lifecycle transitions preserved as history in the same file.

```yaml
severity: string                # required; matches posture's severity scale
opened: datetime                # required
resolved: datetime              # optional; set when status flips to resolved
status: enum                    # required; one of: open, mitigated, resolved
postmortem_required: bool       # required
slos_impacted: list             # optional; slugs of SLOs affected
on_call_responder: string       # optional; who was on call
```

Invariants:
- Files live at `state/incidents/{YYYY-MM-DD}-{incident-slug}.md`.
- `slug` equals the filename stem.
- Body sections: `## Timeline`, `## Mitigation`, `## History`.

**Current version:** 1.

---

## `postmortem`

A blameless postmortem in the Allspaw structure. Owned by `tech-ops`. Append-new-file per postmortem; links to exactly one incident.

```yaml
incident: string                  # required; incident slug
action_items_open_count: int      # required; tracked for rollups
action_items_total_count: int     # required
```

Invariants:
- Files live at `state/postmortems/{YYYY-MM-DD}-{incident-slug}.md`.
- `slug` equals the filename stem.
- Body sections: `## Timeline`, `## Contributing factors`, `## What went well`, `## What we'd do differently`, `## Action items`.
- No individual names in `## Contributing factors` — blameless by construction.

**Current version:** 1.

---

## `technical-strategy-doc`

A written technical strategy document following Larson's diagnosis / guiding policy / coherent actions structure. Owned by `technical-strategy`. One file per strategy area (platform, data, infra, security, etc.).

```yaml
area: string           # required; e.g., "platform", "data", "infrastructure", "security"
horizon: string        # required; e.g., "18 months", "2026"
status: enum           # required; one of: draft, active, archived
owner: string          # optional
```

Invariants:
- Files live at `state/strategies/{strategy-slug}.md`.
- `slug` equals the strategy slug.
- Body sections: `## Diagnosis`, `## Guiding policy`, `## Coherent actions`, `## History`.
- Prior versions preserved under `## History`.

**Current version:** 1.

---

## `adr`

An architecture decision record in Nygard's format. Owned by `technical-strategy`. Append-new-file per decision; **immutable once status is `accepted`** — body never changes after that, only frontmatter status transitions.

```yaml
title: string             # required
status: enum              # required; one of: proposed, accepted, superseded, deprecated
decision_type: enum       # required; one of: build-vs-buy, stack-choice, platform, architecture, other
superseded_by: string     # optional; adr slug that supersedes this one
```

Invariants:
- Files live at `state/adrs/{adr-slug}.md`.
- `slug` equals the ADR slug.
- Body sections: `## Context`, `## Decision`, `## Consequences`.
- Body is immutable once status is `accepted`. Only frontmatter status / superseded_by may change afterward.

**Current version:** 1.

---

## `tech-debt-item`

A tracked tech-debt item with lifecycle (open → scheduled → resolved). Owned by `technical-strategy`. One file per debt item.

```yaml
area: string              # required; service or subsystem the debt lives in
severity: enum            # required; one of: low, medium, high
status: enum              # required; one of: open, scheduled, resolved
priority: int             # optional; ranking among open items
effort: string            # optional; rough estimate
scheduled_for: string     # optional; e.g., "Q3 2026"
opened: date              # required
resolved: date            # optional
```

Invariants:
- Files live at `state/tech-debt/{debt-slug}.md`.
- `slug` equals the debt slug.
- Prior priorities and status transitions preserved under `## History`.

**Current version:** 1.

---

## `workforce-plan`

Singleton workforce plan — headcount targets by team with rationale. Owned by `hiring`.

```yaml
period: string      # required; e.g., "2026", "2026-Q2"
targets: list       # required; each entry {team: string, target_headcount: int, rationale: string}
```

Invariants: singleton at `state/workforce-plan.md` with `slug: current`. `targets` has ≥ 1 entry. Prior versions preserved under `## History`.

**Current version:** 1.

---

## `interview-process`

Singleton playbook for the interview loop. Owned by `hiring`.

```yaml
rounds: list                # required; each entry {name: string, purpose: string, interviewer_role: string}
rubric_dimensions: list     # required; the dimensions every debrief scores
scorecard_template: string  # required; prose description or reference to the template
authority: string           # required; who has hire/no-hire authority
level_variants: list        # optional; per-level variations on the default loop
```

Invariants: singleton at `state/interview-process.md` with `slug: current`. `rounds` has ≥ 1 entry. `rubric_dimensions` has ≥ 3 entries. Prior versions preserved under `## History`.

**Current version:** 1.

---

## `requisition`

An open hiring requisition with its scorecard and pipeline status. Owned by `hiring`. One file per req.

```yaml
role: string         # required; role title
team: string         # required; team the hire lands on
level: string        # required; e.g., "senior", "staff", "VP"
scorecard: dict      # required; {mission: string, outcomes: list, competencies: list}
status: enum         # required; one of: sourcing, interviewing, offer-out, on-hold, filled, cancelled
owner: string        # required; who owns this req
opened: date         # required
closed_date: date    # optional; set when status flips to filled/cancelled
```

Invariants:
- Files live at `state/reqs/{req-slug}.md`.
- `slug` equals the req slug.
- A req can't be `sourcing` / `interviewing` without a non-empty scorecard.

**Current version:** 1.

---

## `candidate`

A candidate in a requisition's pipeline. Owned by `hiring`. One file per candidate per req; stage transitions tracked in the same file.

```yaml
name: string     # required
req: string      # required; req slug this candidate is interviewing for
stage: enum      # required; one of: applied, screening, onsite, offer, accepted, declined, rejected, withdrew
source: string   # required; where they came from (referral, inbound, recruiter, etc.)
```

Invariants:
- Files live at `state/candidates/{req-slug}/{candidate-slug}.md`.
- `slug` equals the candidate slug.
- Stage transitions preserved under `## History` in body.

**Current version:** 1.

---

## `interview-debrief`

A structured debrief for a single interview round with a candidate. Owned by `hiring`. Append-new-file per interview event.

```yaml
candidate: string    # required; candidate slug
req: string          # required; req slug
round: string        # required; which round this is (matches interview-process.rounds entries)
interviewer: string  # required
scores: dict         # required; keys match interview-process.rubric_dimensions
```

Invariants:
- Files live at `state/debriefs/{req-slug}/{candidate-slug}/{YYYY-MM-DD}-{round}.md`.
- `slug` equals `<candidate-slug>-<YYYY-MM-DD>-<round>`.
- Body ends with a recommendation (hire / no hire / hire with caveats).

**Current version:** 1.

---

## `ramp-plan`

A first-30/60/90 day ramp plan for a new hire. Owned by `hiring`. Append-new-file per new hire; handoff to `performance-development` at end of ramp.

```yaml
person: string        # required; the new hire's slug
start_date: date      # required
ramp_status: enum     # required; one of: active, complete, interrupted
```

Invariants:
- Files live at `state/ramp-plans/{person-slug}.md`.
- `slug` equals the person slug.
- Body sections: `## First 30 days`, `## First 60 days`, `## First 90 days`, `## Success criteria`.

**Current version:** 1.

---

## `board-structure`

Singleton declaration of board composition and meeting cadence. Owned by `board-comms`.

```yaml
directors: list              # required; each {name, role: chair|lead-independent|investor|independent|other}
observers: list              # optional
cadence: string              # required; e.g., "quarterly"
pre_read_lead_time: string   # required; e.g., "3 days"
materials_format: string     # required; e.g., "narrative preferred", "deck + 6-pager hybrid"
committees: list             # optional; standing committees (audit, comp, nominating, etc.)
```

Invariants: singleton at `state/board-structure.md` with `slug: current`. Prior versions preserved under `## History`.

**Current version:** 1.

---

## `board-update-template`

Singleton declaration of the standard CTO-section structure for quarterly board updates. Owned by `board-comms`.

```yaml
sections: list              # required; each {name, purpose, typical_length_words}
target_length_words: int    # optional; total target
tone_notes: string          # optional
```

Invariants: singleton at `state/update-template.md` with `slug: current`. `sections` has ≥ 3 entries. Prior versions preserved under `## History`.

**Current version:** 1.

---

## `board-update`

A composed board update for a specific meeting. Owned by `board-comms`. Append-new-file per meeting.

```yaml
meeting_date: date        # required
status: enum              # required; one of: draft, final
quarter: string           # required; e.g., "2026-Q2"
```

Invariants:
- Files live at `state/updates/{YYYY-MM-DD}.md`.
- `slug` equals the filename stem.
- Body structure follows the declared update template's `sections`.

**Current version:** 1.

---

## `board-pre-read`

A topic-specific pre-read memo for a board meeting. Owned by `board-comms`. Append-new-file per pre-read.

```yaml
meeting_date: date        # required
topic: string             # required
pre_read_type: enum       # required; one of: risk, fundraising, m-and-a, strategic, other
```

Invariants:
- Files live at `state/pre-reads/{YYYY-MM-DD}-{topic-slug}.md`.
- `slug` equals the filename stem.
- Body follows 6-pager prose discipline — argument first, then detail.

**Current version:** 1.

---

## `board-meeting-log`

A record of what happened at a board meeting — director feedback, decisions, asks, open threads. Owned by `board-comms`. Append-new-file per meeting.

```yaml
meeting_date: date       # required
```

Invariants:
- Files live at `state/meetings/{YYYY-MM-DD}.md`.
- `slug` equals the filename stem.
- Body sections: `## Director feedback`, `## Decisions`, `## Asks of management`, `## Open threads`, `## Room tone`.

**Current version:** 1.

---

## `comm-surfaces`

Singleton declaration of internal comm surfaces (channels, lists, wikis, all-hands). Owned by `org-comms`.

```yaml
surfaces: list    # required; each {name, audience_scope, typical_comm_types}
```

Invariants: singleton at `state/surfaces.md` with `slug: current`. `surfaces` has ≥ 1 entry. Prior versions preserved under `## History`.

**Current version:** 1.

---

## `comm-cadences`

Singleton declaration of recurring internal-comm cadences. Owned by `org-comms`.

```yaml
cadences: list    # required; each {name, frequency, target_surfaces, structure_notes, due_relative_to_period}
```

Invariants: singleton at `state/cadences.md` with `slug: current`. `cadences` can be empty (users who communicate purely ad-hoc). Prior versions preserved under `## History`.

**Current version:** 1.

---

## `delivered-comm`

A composed internal communication — recurring update, all-hands content, incident comm, or cross-functional announcement. Owned by `org-comms`. Append-new-file per comm.

```yaml
comm_type: enum         # required; one of: recurring, all-hands, incident, announcement
status: enum            # required; one of: draft, final
surfaces: list          # required; where this went/will-go
audience_scope: string  # required
topic: string           # required
related_source: string  # optional; e.g., incident-slug for incident comms
```

Invariants:
- Files live at `state/delivered/{YYYY-MM-DD}-{comm-slug}.md`.
- `slug` equals the filename stem.
- Body structure varies by `comm_type`; recurring / announcement follow Minto prose; all-hands can include slide outlines; incident comms lead with "what happened / who's affected / what we're doing."

**Current version:** 1.

---

## `review-cycle`

Singleton declaration of the performance-review cycle — cadence, structure, rubric. Owned by `performance-development`.

```yaml
cadence: string                  # required; e.g., "semi-annual", "annual"
structure: list                  # required; entries indicate components (self-review, peer, upward, manager, etc.)
rubric_reference: string         # required; either inline or reference to a doc/link
calibration_expectation: string  # required; when/whether reviews go to calibration
cycle_dates: list                # required; period boundaries in the year
```

Invariants: singleton at `state/review-cycle.md` with `slug: current`. Prior versions preserved under `## History`.

**Current version:** 1.

---

## `leveling-ladder`

Singleton declaration of the leveling ladder — levels, expectations, variants. Owned by `performance-development`.

```yaml
levels: list                     # required; ordered list of level names
expectations_per_level: dict     # required; each key is a level, value describes expectations
variants: list                   # optional; per-function or per-track variants (IC/manager, specialist)
```

Invariants: singleton at `state/leveling-ladder.md` with `slug: current`. `levels` has ≥ 3 entries. Each level has expectations populated. Prior versions preserved under `## History`.

**Current version:** 1.

---

## `performance-record`

Per-report long-lived record of current level, trajectory, and pointers to active plans/PIPs. Owned by `performance-development`. One file per report. Scan-friendly rollup surface.

```yaml
active: bool                          # optional; defaults true. false when the report has left the user's org
current_level: string                 # required
level_tenure_months: int              # required
last_review_date: date                # optional
current_trajectory: enum              # required; one of: growing, steady, concerning, excelling
active_pip: string                    # optional; pip slug if an active PIP exists
active_development_plan: string       # optional; plan slug if an active dev plan exists
```

Invariants:
- Files live at `state/records/{person-slug}.md`.
- `slug` equals the person slug.
- Body holds trajectory narrative + `## History` with dated trajectory changes.
- Scan excludes `active: false` files by default.

**Current version:** 1.

---

## `performance-review`

A formal performance review for a specific report at a specific cycle. Owned by `performance-development`. **Immutable once status is `delivered`** — structural parallel to ADRs.

```yaml
person: string            # required; report slug
cycle: string             # required; which cycle this review covers
status: enum              # required; one of: draft, delivered
level_at_review: string   # required; level at time of review
```

Invariants:
- Files live at `state/reviews/{person-slug}/{cycle}-{YYYY-MM-DD}.md`.
- `slug` equals `<person-slug>-<cycle>-<YYYY-MM-DD>`.
- Body structure follows declared `review-cycle.structure`.
- Body immutable once status is `delivered`.

**Current version:** 1.

---

## `development-plan`

A development plan for a report — goals, check-ins, outcome. Owned by `performance-development`. One file per plan (a person can have multiple plans over time, each file scoped to its lifecycle).

```yaml
person: string            # required; report slug
status: enum              # required; one of: active, closed-succeeded, closed-abandoned
goals: list               # required
time_horizon: string      # required
check_in_cadence: string  # required
opened: date              # required
closed_date: date         # optional
```

Invariants:
- Files live at `state/development-plans/{person-slug}/{YYYY-MM-DD}.md`.
- `slug` equals `<person-slug>-<YYYY-MM-DD>`.
- Body: plan detail + `## Check-ins` with dated entries.

**Current version:** 1.

---

## `calibration-session`

A calibration session record — a cohort of reviews discussed and aligned on level/trajectory assessments. Owned by `performance-development`. Append-new-file per session.

```yaml
participants: list    # required; people in the room
cohort: string        # required; which group was calibrated (e.g., "eng-managers", "all reports")
```

Invariants:
- Files live at `state/calibrations/{YYYY-MM-DD}.md`.
- `slug` equals the filename stem.
- Body sections: `## Per-person assessments`, `## Dissent & resolution`, `## Final decisions`, `## Open threads`.

**Current version:** 1.

---

## `promotion-case`

A written case for promoting a report to the next level. Owned by `performance-development`. Append-new-file per case.

```yaml
person: string          # required; report slug
from_level: string      # required
to_level: string        # required
status: enum            # required; one of: draft, submitted, approved, denied
submitted_date: date    # optional
decision_date: date     # optional
```

Invariants:
- Files live at `state/promotion-cases/{person-slug}/{cycle}-{YYYY-MM-DD}.md`.
- `slug` equals `<person-slug>-<cycle>-<YYYY-MM-DD>`.
- Body sections: `## Case summary`, `## Evidence per dimension`, `## Trajectory`, `## Risks`.

**Current version:** 1.

---

## `pip`

A Performance Improvement Plan for a report. Owned by `performance-development`. One file per PIP lifecycle; check-ins captured in body.

```yaml
person: string           # required; report slug
status: enum             # required; one of: active, closed-successful, closed-exit, closed-role-change
gap_summary: string      # required; what's the performance gap being addressed
success_criteria: list   # required; measurable criteria for closing successfully
time_horizon: string     # required; e.g., "30 days", "60 days"
check_in_cadence: string # required; e.g., "weekly"
opened: date             # required
closed_date: date        # optional
```

Invariants:
- Files live at `state/pips/{person-slug}/{YYYY-MM-DD}.md`.
- `slug` equals `<person-slug>-<YYYY-MM-DD>`.
- Body: plan detail + `## Check-ins` with dated entries + outcome notes at close.

**Current version:** 1.

---

## `succession-note`

Succession-planning notes for a key role — who could succeed the current occupant, readiness, gaps. Owned by `performance-development`. One file per role (candidates listed inside).

```yaml
role: string             # required; role being planned for
current_occupant: string # optional; person slug of current holder
candidates: list         # required; each {person-slug, readiness: now|1-year|2-plus-years, gap_notes}
```

Invariants:
- Files live at `state/succession/{role-slug}.md`.
- `slug` equals the role slug.
- Prior candidate lists preserved under `## History`.

**Current version:** 1.

---

## `design-principles`

Singleton declaration of the org-design principles — the user's stated criteria for evaluating any structural proposal. Owned by `org-design`.

```yaml
principles: list    # required; each entry is a prose principle
```

Invariants: singleton at `state/design-principles.md` with `slug: current`. `principles` has ≥ 3 entries. Prior versions preserved under `## History`.

**Current version:** 1.

---

## `design-proposal`

A reorg / org-design proposal at some point in its lifecycle (draft → review → approved → implemented, or rejected / superseded). Owned by `org-design`. One file per proposal.

```yaml
proposal_type: enum    # required; one of: reorg, new-team, merge, split, snapshot
status: enum           # required; one of: draft, review, approved, implemented, rejected, superseded
proposed_date: date    # required
decided_date: date     # optional
supersedes: string     # optional; proposal slug this supersedes
superseded_by: string  # optional; proposal slug that supersedes this one
```

Invariants:
- Files live at `state/proposals/{YYYY-MM-DD}-{proposal-slug}.md`.
- `slug` equals the filename stem.
- Body sections: `## Diagnosis`, `## Proposed structure`, `## Tradeoffs`, `## Rollout plan`, `## Principles invoked`.
- The `snapshot` variant is the current-state capture produced at activation (status: implemented, proposal_type: snapshot).

**Current version:** 1.

---

## `design-decision`

A structural decision that's been made and recorded — often from an approved proposal, sometimes lightweight / reactive. Owned by `org-design`. Append-new-file per decision.

```yaml
decision_summary: string   # required; one-line statement of what was decided
linked_proposal: string    # optional; proposal slug if this decision originates from one
```

Invariants:
- Files live at `state/decisions/{YYYY-MM-DD}-{decision-slug}.md`.
- `slug` equals the filename stem.
- Body: context + decision + rationale + review-date + principles invoked.

**Current version:** 1.

---

## `bottleneck-analysis`

A written diagnosis of a specific org bottleneck using the Reinertsen + Conway's Law lens. Owned by `org-design`. Append-new-file per analysis.

```yaml
bottleneck_reference: string   # optional; slug of a corresponding `bottleneck` record in process-management, if one exists
diagnosis_lens: enum           # required; one of: reinertsen, conway, both
```

Invariants:
- Files live at `state/bottleneck-analyses/{YYYY-MM-DD}-{bottleneck-slug}.md`.
- `slug` equals the filename stem.
- Body sections: `## Symptoms`, `## Reinertsen view`, `## Conway view`, `## Recommended intervention`.

**Current version:** 1.

---

## `budget-structure`

Singleton declaration of the budget category taxonomy. Owned by `budget`.

```yaml
categories: list            # required; each {name, slug, capex_opex, description}
currency: string            # required; ISO 4217 code (USD, EUR, etc.)
period_granularity: enum    # required; one of: monthly, quarterly, annual
```

Invariants: singleton at `state/budget-structure.md` with `slug: current`. `categories` has ≥ 3 entries. Prior versions preserved under `## History`.

**Current version:** 1.

---

## `budget-category`

A single budget category with current-period plan / actual / forecast in frontmatter and period history in body. Owned by `budget`. One file per category.

```yaml
category_name: string              # required
capex_opex: enum                   # required; one of: capex, opex
currency: string                   # required; ISO 4217 code
current_period: string             # required; e.g., "2026-Q2", "2026-03", "2026"
current_plan_amount: number        # required
current_actual_amount: number      # required; defaults to 0 at period start
current_forecast_amount: number    # optional; revised estimate for end-of-period
ytd_plan: number                   # optional; year-to-date plan if applicable
ytd_actual: number                 # optional; year-to-date actual if applicable
```

Invariants:
- Files live at `state/categories/{category-slug}.md`.
- `slug` equals the category slug.
- Body holds notes + `## Period history` with dated snapshots of prior periods' plan / actual / forecast.
- `close-period` skill is the only writer of history entries; manual edits to `## Period history` discouraged.

**Current version:** 1.

---

## `compliance-posture`

Singleton declaration of compliance-regime commitments, statuses, and target maturity. Owned by `security-compliance`.

```yaml
regimes: list           # required; each {name, status, owner, target_date, scope_statement}
target_cis_ig: string   # optional; e.g., "IG2"
nist_csf_notes: string  # optional; target-profile notes
```

Invariants: singleton at `state/compliance-posture.md` with `slug: current`. Prior versions preserved under `## History`. `regimes` can be empty only if the org is pre-commitment.

**Current version:** 1.

---

## `risk-register-entry`

A single entry in the risk register, with severity / likelihood / mitigation / status. Owned by `security-compliance`. One file per risk.

```yaml
category: enum            # required; one of: data, access, availability, compliance, vendor, other
severity: enum            # required; one of: low, medium, high, critical
likelihood: enum          # required; one of: low, medium, high
status: enum              # required; one of: open, mitigating, monitored, resolved, accepted
owner: string             # required
opened: date              # required
closed_date: date         # optional
related_controls: list    # optional; slugs of controls that mitigate this risk
```

Invariants:
- Files live at `state/risks/{risk-slug}.md`.
- `slug` equals the risk slug.
- Prior status transitions preserved under `## History`.

**Current version:** 1.

---

## `control`

A security or compliance control with ownership, regime mapping, and implementation status. Owned by `security-compliance`. One file per control.

```yaml
name: string                    # required
cis_control_id: string          # optional; CIS Control catalog ID
nist_csf_functions: list        # optional; one or more of: identify, protect, detect, respond, recover
soc2_criteria: list             # optional; SOC 2 Trust Services Criteria this control supports
iso_annex_a: list               # optional; ISO 27001 Annex A references
owner: string                   # required
implementation_status: enum     # required; one of: not-implemented, partial, implemented, needs-remediation
```

Invariants:
- Files live at `state/controls/{control-slug}.md`.
- `slug` equals the control slug.
- Body: description + evidence references + `## History` of status transitions.

**Current version:** 1.

---

## `statement-of-applicability`

Singleton ISO 27001 Statement of Applicability — which Annex A controls are in scope / excluded, with justifications. Owned by `security-compliance`.

```yaml
iso_version: string    # required; e.g., "ISO/IEC 27001:2022"
annex_a_scope: list    # required; each {control_id, status: applicable|excluded, justification, implementing_control: <control-slug>}
```

Invariants: singleton at `state/statement-of-applicability.md` with `slug: current`. Prior versions preserved under `## History`.

**Current version:** 1.

---

## `audit-event`

An audit event — SOC 2 Type 1/2, ISO surveillance or recertification, pentest engagement, customer security assessment, internal audit. Owned by `security-compliance`. Append-new-file per audit.

```yaml
audit_type: enum           # required; one of: soc2-type1, soc2-type2, soc2-bridge, iso-surveillance, iso-recertification, pentest, customer-assessment, internal
regime: string             # optional; which regime this audit is against (e.g., "SOC 2", "ISO 27001")
scope: string              # required
started_date: date         # required
completed_date: date       # optional
status: enum               # required; one of: in-progress, completed, findings-open
findings_open_count: int   # required
findings_total_count: int  # required
```

Invariants:
- Files live at `state/audits/{YYYY-MM-DD}-{audit-slug}.md`.
- `slug` equals the filename stem.
- Body sections: `## Scope`, `## Findings`, `## Remediation plan`, `## Status updates`.

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
| `reliability-posture` | 1 | `tech-ops` |
| `slo` | 1 | `tech-ops` |
| `incident` | 1 | `tech-ops` |
| `postmortem` | 1 | `tech-ops` |
| `technical-strategy-doc` | 1 | `technical-strategy` |
| `adr` | 1 | `technical-strategy` |
| `tech-debt-item` | 1 | `technical-strategy` |
| `workforce-plan` | 1 | `hiring` |
| `interview-process` | 1 | `hiring` |
| `requisition` | 1 | `hiring` |
| `candidate` | 1 | `hiring` |
| `interview-debrief` | 1 | `hiring` |
| `ramp-plan` | 1 | `hiring` |
| `board-structure` | 1 | `board-comms` |
| `board-update-template` | 1 | `board-comms` |
| `board-update` | 1 | `board-comms` |
| `board-pre-read` | 1 | `board-comms` |
| `board-meeting-log` | 1 | `board-comms` |
| `comm-surfaces` | 1 | `org-comms` |
| `comm-cadences` | 1 | `org-comms` |
| `delivered-comm` | 1 | `org-comms` |
| `review-cycle` | 1 | `performance-development` |
| `leveling-ladder` | 1 | `performance-development` |
| `performance-record` | 1 | `performance-development` |
| `performance-review` | 1 | `performance-development` |
| `development-plan` | 1 | `performance-development` |
| `calibration-session` | 1 | `performance-development` |
| `promotion-case` | 1 | `performance-development` |
| `pip` | 1 | `performance-development` |
| `succession-note` | 1 | `performance-development` |
| `design-principles` | 1 | `org-design` |
| `design-proposal` | 1 | `org-design` |
| `design-decision` | 1 | `org-design` |
| `bottleneck-analysis` | 1 | `org-design` |
| `budget-structure` | 1 | `budget` |
| `budget-category` | 1 | `budget` |
| `compliance-posture` | 1 | `security-compliance` |
| `risk-register-entry` | 1 | `security-compliance` |
| `control` | 1 | `security-compliance` |
| `statement-of-applicability` | 1 | `security-compliance` |
| `audit-event` | 1 | `security-compliance` |

Version bumps ship with a migration at `scripts/migrate_{type}_v{N}_to_v{N+1}.py`. The migration runs automatically the next time a surface loads and detects drift; it commits a pre-migration snapshot to git so rollback is `git revert`.
