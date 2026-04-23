---
name: tech-ops
description: "Activates for running production reliably — the operational state of systems that serve customers. Covers: SLO definition and error-budget tracking, incident management across the lifecycle (detection → response → resolution), blameless postmortems, reliability posture declarations, and on-call load/distribution trends. Also activates on oblique phrasings like 'we had an S1 last night,' 'cut a postmortem for yesterday's outage,' 'what's our error budget looking like,' 'on-call is burning out,' 'the database tier is unreliable,' 'write up the reliability section for the quarterly.' Does NOT activate on strategic technical direction (Technical Strategy); SDLC and development flow (Process Management); team-aggregate health or on-call scheduling specifics that live in PagerDuty/Opsgenie (Team Management for health; rotation tools for schedules); security posture (Security & Compliance owns risk; Tech Ops owns security-incident *operations* when they occur)."
requires: []
optional:
  - team-management
  - technical-strategy
---

# Tech Ops

## Scope

Running production reliably. The operational state of systems that serve customers — availability, performance, risk, readiness. Tracks SLOs and their error budgets, incident lifecycles, postmortems, and reliability posture. Role-shape module for hands-on-tech CTOs, or any engineering leader where production reliability is a first-order part of the job.

## Out of scope

- **Strategic technical direction** — Technical Strategy.
- **SDLC and development flow** — Process Management.
- **Team health and aggregate composition** — Team Management (but on-call *load* is a reliability metric tracked here).
- **On-call rotation schedules** — PagerDuty / Opsgenie / whatever the rotation tool is. This module tracks load and distribution as derived metrics, not the schedule itself.
- **Security posture and risk picture** — Security & Compliance. Tech Ops handles the *operations* of a security incident when one happens, but the ongoing risk register is S&C territory.

## Frameworks

- [Google — *Site Reliability Engineering*](https://sre.google/sre-book/table-of-contents/) — SLOs, error budgets, toil reduction, on-call discipline.
  - *How this module applies it:* SLOs are the primary reliability abstraction. Every critical user journey gets an SLO with a target (e.g., 99.9% availability), an observed-current reading, and an error-budget state (burn rate, remaining). Error-budget policy is explicit: when the budget is exhausted, feature work pauses until it's restored. The module doesn't enforce this — it surfaces the state; policy is organizational. Toil is discussed in postmortems as a root cause but not tracked as a dedicated type yet (could graduate later).

- [DORA](https://dora.dev/) — deploy frequency, lead time, change-fail rate, MTTR.
  - *How this module applies it:* change-fail rate and MTTR are reliability-adjacent and tracked here (incident data supplies them directly). Deploy frequency and lead time are process metrics owned by Process Management's SDLC flow — this module reads them rather than owns them.

- [John Allspaw — blameless postmortems (Etsy)](https://www.etsy.com/codeascraft/blameless-postmortems) — learning-oriented incident review.
  - *How this module applies it:* postmortems follow a fixed structure: timeline, contributing factors (not "root cause" singular), what went well, what we'd do differently, action items with owners. Names appear in timeline attribution but not in contributing-factor analysis — focus on systems, not individuals. Action items are tracked until closed; the postmortem file is the canonical place for their status.

## Triggers

- "log an incident" / "we had an S1"
- "update the incident" / "the outage is mitigated"
- "cut a postmortem" / "run the postmortem for [incident]"
- "define an SLO for [service]"
- "what's our error budget" / "SLO status"
- "on-call load trends" / "how's on-call going"
- "show reliability" / "reliability dashboard"
- "update our reliability posture"
- Oblique: "we had an outage last night"
- Oblique: "the database tier has been unstable"
- Oblique: "write up the reliability section for the quarterly"

## Activation flow

Each step writes a concrete artifact and appends its step number to `activation_completed` in `_module.md`.

### 1. Declare reliability posture

**Ask:** "What's your org's reliability posture? Cover: (a) what SLO coverage are you aiming for — all user-facing services? Tier-1 only? (b) incident severity scale — what are your sev tiers, and what triggers postmortem (usually S1 / S2 mandatory; S3 optional); (c) on-call tooling (PagerDuty, Opsgenie, custom); (d) error-budget policy — do you pause feature work when a budget burns, and at what threshold? (e) toil tolerance — any explicit targets like '<30% of eng time is toil.'"
**Writes:** `cto-os-data/modules/tech-ops/state/reliability-posture.md` with `type: reliability-posture`, `slug: current`, `slo_coverage_target`, `severity_scale`, `postmortem_triggers`, `on_call_tool`, `error_budget_policy`, `toil_target`.
**Expects:** frontmatter has `severity_scale` (list), `on_call_tool`, and `error_budget_policy` set at minimum.

### 2. Baseline SLOs

**Ask:** "Give me your most critical 3–10 SLOs. For each: service/endpoint, the SLO target (e.g., '99.9% availability over 30d'), current reading if you know it, and where it's measured from (Datadog, Prometheus, custom). Skip if you don't have formal SLOs yet — we'll create a single placeholder and capture 'no SLOs defined yet' as the initial reliability signal."
**Writes:** one file per SLO at `cto-os-data/modules/tech-ops/state/slos/{slo-slug}.md` with `type: slo`, `slug: <slo-slug>`, `service`, `target`, `current`, `error_budget_remaining`, `measurement_source`.
**Expects:** at least one SLO file exists OR the reliability posture explicitly records "no SLOs defined yet" as a known gap.

### 3. Seed recent incident history

**Ask:** "List the last 3–10 incidents so the module has context to roll up from. Quick capture for each: date, severity, one-line description, status (resolved or still open), whether a postmortem was done. Full postmortem capture happens separately for incidents that need one."
**Writes:** one file per incident at `cto-os-data/modules/tech-ops/state/incidents/{YYYY-MM-DD}-{incident-slug}.md` with `type: incident`, `slug`, `severity`, `opened`, `resolved`, `status`, `postmortem_required`.
**Expects:** zero or more incident files exist (can be zero — user may not want to backfill history).

## Skills

### `define-slo`

**Purpose:** Add or update an SLO. Captures target, measurement source, current state. Updates to an existing SLO preserve history.

**Triggers:**
- "define an SLO for [service]"
- "update the [service] SLO"
- "new SLO: [service] at [target]"

**Reads:**
- `cto-os-data/modules/tech-ops/state/slos/` (existing SLOs, slug collision)
- `cto-os-data/modules/tech-ops/state/reliability-posture.md` (for posture alignment)

**Writes:** `cto-os-data/modules/tech-ops/state/slos/{slo-slug}.md`, overwrite-with-history.

### `log-incident`

**Purpose:** Open a new incident record. Captures initial detection context — who noticed, what's happening, severity call, any immediate mitigation.

**Triggers:**
- "log an incident"
- "we have an S1 / S2 / S3"
- "opening an incident: [summary]"

**Reads:**
- `cto-os-data/modules/tech-ops/state/reliability-posture.md` (severity scale)
- `cto-os-data/modules/tech-ops/state/slos/` (which SLOs are impacted)

**Writes:** `cto-os-data/modules/tech-ops/state/incidents/{YYYY-MM-DD}-{incident-slug}.md`, append-new-file with `status: open`.

### `update-incident`

**Purpose:** Transition an incident through its lifecycle (open → mitigated → resolved), capture timeline events, note SLO impact, flag whether a postmortem is required.

**Triggers:**
- "update [incident]"
- "[incident] is mitigated / resolved"
- "add timeline entry to [incident]"

**Reads:** `cto-os-data/modules/tech-ops/state/incidents/{incident-slug}.md`.

**Writes:** `cto-os-data/modules/tech-ops/state/incidents/{incident-slug}.md`, overwrite-with-history (status transitions and timeline events preserved in body under `## Timeline` and `## History`).

### `run-postmortem`

**Purpose:** Capture a blameless postmortem for an incident. Enforces the structure: timeline, contributing factors (plural), what went well, what we'd do differently, action items with owners.

**Triggers:**
- "postmortem for [incident]"
- "run the postmortem"
- "write up yesterday's outage"

**Reads:**
- `cto-os-data/modules/tech-ops/state/incidents/{incident-slug}.md` (the incident being reviewed)
- `cto-os-data/modules/tech-ops/state/postmortems/` (recent postmortems for pattern-spotting)

**Writes:** `cto-os-data/modules/tech-ops/state/postmortems/{YYYY-MM-DD}-{incident-slug}.md`, append-new-file.

### `show-reliability`

**Purpose:** Assemble a read-time reliability dashboard across SLOs, recent incidents, open postmortem action items, and on-call load trends.

**Triggers:**
- "show reliability"
- "reliability dashboard"
- "how are our SLOs doing"
- "what's the error budget picture"

**Reads:**
- `scan(type=["slo"], fields=["slug", "service", "target", "current", "error_budget_remaining", "last_measured"])`
- `scan(type=["incident"], where={"status": "open"}, fields=["slug", "severity", "opened"])`
- `scan(type=["postmortem"], fields=["slug", "incident", "action_items_open_count", "updated"])`

**Writes:** —

### `update-posture`

**Purpose:** Revise reliability posture — new severity scale, different error-budget policy, changed on-call tooling.

**Triggers:**
- "update our reliability posture"
- "change the error budget policy"
- "we're switching from Opsgenie to PagerDuty"

**Reads:** `cto-os-data/modules/tech-ops/state/reliability-posture.md`.

**Writes:** `cto-os-data/modules/tech-ops/state/reliability-posture.md`, overwrite-with-history.

## Persistence

- **`cto-os-data/modules/tech-ops/state/reliability-posture.md`** — singleton (`slug: current`), overwrite-with-history. Frontmatter: `type: reliability-posture, slug: current, updated: <date>, slo_coverage_target: <string>, severity_scale: <list>, postmortem_triggers: <list>, on_call_tool: <string>, error_budget_policy: <string>, toil_target: <string>`. Body: rationale + `## History`.
- **`cto-os-data/modules/tech-ops/state/slos/{slo-slug}.md`** — one file per SLO, overwrite-with-history. Frontmatter: `type: slo, slug: <slo-slug>, updated: <date>, service: <string>, target: <string>, current: <string, optional>, error_budget_remaining: <string, optional>, measurement_source: <string>, last_measured: <date, optional>`. Body: definition + `## History` with dated measurement snapshots.
- **`cto-os-data/modules/tech-ops/state/incidents/{YYYY-MM-DD}-{incident-slug}.md`** — one file per incident, overwrite-with-history (lifecycle transitions preserved). Frontmatter: `type: incident, slug: <YYYY-MM-DD>-<incident-slug>, updated: <date>, severity: <string>, opened: <datetime>, resolved: <datetime, optional>, status: <open|mitigated|resolved>, postmortem_required: <bool>, slos_impacted: <list, optional>, on_call_responder: <string, optional>`. Body: `## Timeline`, `## Mitigation`, `## History`.
- **`cto-os-data/modules/tech-ops/state/postmortems/{YYYY-MM-DD}-{incident-slug}.md`** — append-new-file per postmortem. Frontmatter: `type: postmortem, slug: <YYYY-MM-DD>-<incident-slug>, updated: <date>, incident: <incident-slug>, action_items_open_count: <int>, action_items_total_count: <int>`. Body sections: `## Timeline`, `## Contributing factors`, `## What went well`, `## What we'd do differently`, `## Action items` (with owners + status).

**Overrides to the cross-cutting save rule** ([Persistence model](../../docs/ARCHITECTURE.md#persistence-model)): incident captures happen without blocking during active incidents (user is narrating in real time; friction would hurt response). Postmortem and posture changes confirm when content is ambiguous.

**Sensitivity:** standard by default at module level. Individual incidents or postmortems touching security material, customer data exposure, or personnel issues can be flagged `sensitivity: high` per-file to scope their scan exclusion.

## State location

`cto-os-data/modules/tech-ops/state/`
