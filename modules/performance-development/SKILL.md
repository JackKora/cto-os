---
name: performance-development
description: "Activates for developing the people already on the team over the arc of their careers. Covers: performance review cycles (quarterly, semi-annual, annual — whatever the user runs), leveling ladder definition and reference, per-person performance records tracking trends across cycles, development plans with goals and check-ins, calibration sessions across a team or org, promotion-case authorship, PIP lifecycle management, and succession-planning notes for key roles. Also activates on oblique phrasings like 'draft a review for [report],' 'prep for calibration,' 'build a promotion case for [report],' 'open a PIP for [report],' 'who could succeed me / [other leader],' 'update the leveling ladder,' 'log a development-plan check-in with [report].' Does NOT activate on pre-ramp hiring (Hiring owns pipeline + ramp); team-aggregate health (Team Management); day-to-day 1:1 coaching signals (Managing Down captures those; this module reads them as input for reviews and PIPs); peer or upward performance (those aren't the user's to manage)."
requires:
  - team-management
optional:
  - hiring
  - managing-down
---

# Performance & Development

## Scope

Developing the people the user has hired over the arc of their careers. Maintains a clear view of individual performance, growth, and trajectory for each direct report. Runs the performance-review cycle, owns calibration, authors promotion cases, manages PIPs end-to-end, and holds succession-planning notes for key roles. Reads from Managing Down (coaching signals) and Team Management (team context); writes its own artifacts and handoffs back to Managing Down via references.

## Out of scope

- **Pre-ramp hiring pipeline and initial ramp plan** — Hiring owns everything from req through end-of-ramp; this module picks up when the report is past ramp and being managed as a performing member of the team.
- **Team-aggregate health** — Team Management (which reads individual-trend data from here for roll-ups).
- **Day-to-day 1:1 coaching** — Managing Down. Coaching events captured there are *input* to reviews here; reviews themselves are this module.
- **Peer or upward performance** — not the user's to manage. Managing Up / Sideways tracks the relationship; performance management is the other person's manager's job.

## Frameworks

- [Kim Scott — *Radical Candor*](https://www.radicalcandor.com/) — feedback discipline: specific observed behavior, impact, ask.
  - *How this module applies it:* performance reviews, calibration input, promotion cases, and PIP updates all follow the same feedback structure. No inferred motives, no character statements. "When [specific behavior] happens, [specific impact]. The ask is [specific change] by [specific time]." Works for praise and criticism equally — praise is also grounded in specifics. Review rubrics that lean toward vague trait judgments ("great communicator") get rewritten to behavioral evidence.

- [Carol Dweck — *Mindset*](https://www.amazon.com/Mindset-Psychology-Carol-S-Dweck/dp/0345472322) — growth mindset as the development frame.
  - *How this module applies it:* development plans target learnable behaviors and skill-building, not fixed traits. Promotion cases emphasize trajectory ("here's what they've grown into") alongside current level. PIPs frame the gap as addressable — the PIP is a path to success or an exit, not a formality. Feedback language avoids fixing-trait phrasings ("you're bad at presenting") in favor of growth-oriented phrasings ("your next step on presenting is [specific behavior]").

## Triggers

- "draft a review for [report]" / "log the review for [report]"
- "prep for calibration" / "log yesterday's calibration session"
- "build a promotion case for [report]"
- "open a PIP for [report]" / "update the PIP for [report]" / "close [report]'s PIP"
- "log a development-plan check-in with [report]" / "update [report]'s development plan"
- "succession planning for [role]" / "who could succeed [key person]"
- "update the leveling ladder" / "revise the review cycle"
- "show me performance rollup across my org"
- Oblique: "I'm worried about [report]'s trajectory" (might lead to development-plan or PIP)
- Oblique: "time to think about who's ready for promotion"

## Activation flow

Each step writes a concrete artifact and appends its step number to `activation_completed` in `_module.md`.

### 1. Declare review cycle

**Ask:** "Walk me through your performance-review cycle. Cadence (annual, semi-annual, quarterly, rolling), structure (self-review? peer-review? upward? manager-authored only?), rubric or scorecard used, calibration expectation (do reviews go to a calibration session before delivery?), and when the cycle dates fall in the year."
**Writes:** `cto-os-data/modules/performance-development/state/review-cycle.md` with `type: review-cycle`, `slug: current`, `cadence`, `structure`, `rubric_reference`, `calibration_expectation`, `cycle_dates`.
**Expects:** frontmatter has `cadence`, `structure`, and `calibration_expectation` set.

### 2. Declare leveling ladder

**Ask:** "What's your leveling ladder? Levels (e.g., junior / mid / senior / staff / principal / VP — whatever your taxonomy is), expectations per level (scope of impact, autonomy, depth of technical or leadership skill), and any per-function variants (IC vs. manager track, specialist variants). If you don't have a formal ladder, we can capture a working version and refine."
**Writes:** `cto-os-data/modules/performance-development/state/leveling-ladder.md` with `type: leveling-ladder`, `slug: current`, `levels`, `expectations_per_level`, `variants`.
**Expects:** frontmatter `levels` has ≥ 3 entries; `expectations_per_level` populated for each.

### 3. Baseline per-report performance records

**Ask:** "Let's initialize performance records for each of your direct reports. Pulling names from Team Management / Managing Down if those modules are active — otherwise enumerate. For each report: current level, how long at this level, latest review date (approximate is fine), current trajectory (growing / steady / concerning)."
**Writes:** one file per report at `cto-os-data/modules/performance-development/state/records/{person-slug}.md` with `type: performance-record`, `slug: <person-slug>`, `current_level`, `level_tenure_months`, `last_review_date`, `current_trajectory`, `active_pip`, `active_development_plan`.
**Expects:** at least one performance-record file exists (or the user explicitly has no direct reports — unusual but possible at e.g. an advisory role, in which case activation captures that).

## Skills

### `update-review-cycle`

**Purpose:** Revise declared review cycle — cadence change, structure update, new rubric.

**Triggers:**
- "update our review cycle"
- "switching from annual to semi-annual"
- "add peer review to the cycle"

**Reads:** `cto-os-data/modules/performance-development/state/review-cycle.md`.

**Writes:** `cto-os-data/modules/performance-development/state/review-cycle.md`, overwrite-with-history.

### `update-leveling-ladder`

**Purpose:** Revise the leveling ladder — new levels, refined expectations, added track variant.

**Triggers:**
- "update the leveling ladder"
- "add a new level between staff and principal"
- "revise expectations for [level]"

**Reads:** `cto-os-data/modules/performance-development/state/leveling-ladder.md`.

**Writes:** `cto-os-data/modules/performance-development/state/leveling-ladder.md`, overwrite-with-history.

### `open-development-plan`

**Purpose:** Create a development plan for a report — explicit growth goals, check-in cadence, success criteria, time horizon.

**Triggers:**
- "open a development plan for [report]"
- "[report] wants to grow into [area] — plan it"

**Reads:**
- `cto-os-data/modules/performance-development/state/records/{person-slug}.md`
- `cto-os-data/modules/performance-development/state/leveling-ladder.md` (target-level expectations)
- `cto-os-data/modules/managing-down/state/people/{person-slug}.md` (optional — profile context)
- `cto-os-data/modules/managing-down/state/1on1s/{person-slug}/` (optional — recent signals)

**Writes:** `cto-os-data/modules/performance-development/state/development-plans/{person-slug}/{YYYY-MM-DD}.md`, append-new-file with `status: active`. Also updates the person's `performance-record.md` with `active_development_plan: <plan-slug>`.

### `update-development-plan`

**Purpose:** Log a check-in against an active plan, update progress, revise goals, or close the plan (succeeded or abandoned).

**Triggers:**
- "log a development-plan check-in with [report]"
- "update [report]'s development plan"
- "close [report]'s development plan — they hit the goals"

**Reads:** `cto-os-data/modules/performance-development/state/development-plans/{person-slug}/{plan-slug}.md`.

**Writes:** `cto-os-data/modules/performance-development/state/development-plans/{person-slug}/{plan-slug}.md`, overwrite-with-history (check-ins and status transitions in body). When closing, updates the person's record accordingly.

### `log-performance-review`

**Purpose:** Capture a performance review for a report. Follows the declared review cycle's structure. **Reviews are immutable once status is `delivered`** — structural parallel to ADRs. A delivered review is a historical record of what was said.

**Triggers:**
- "draft a review for [report]"
- "log the review for [report] — I delivered it yesterday"

**Reads:**
- `cto-os-data/modules/performance-development/state/review-cycle.md` (structure)
- `cto-os-data/modules/performance-development/state/leveling-ladder.md` (expectations at level)
- `cto-os-data/modules/performance-development/state/records/{person-slug}.md`
- Prior reviews in `cto-os-data/modules/performance-development/state/reviews/{person-slug}/`
- `cto-os-data/modules/managing-down/state/coaching/{person-slug}/` (optional — in-cycle coaching signals)
- `cto-os-data/modules/managing-down/state/1on1s/{person-slug}/` (optional)

**Writes:** `cto-os-data/modules/performance-development/state/reviews/{person-slug}/{cycle}-{YYYY-MM-DD}.md`, append-new-file with `status: draft`. Delivery flips to `status: delivered` and is then immutable.

### `log-calibration`

**Purpose:** Capture a calibration session — what level each person was assessed at, dissent raised and resolved, final decisions, open threads.

**Triggers:**
- "log yesterday's calibration session"
- "calibration just ended — capture it"

**Reads:**
- `cto-os-data/modules/performance-development/state/reviews/` (recent reviews for the cohort being calibrated)
- `cto-os-data/modules/performance-development/state/leveling-ladder.md`

**Writes:** `cto-os-data/modules/performance-development/state/calibrations/{YYYY-MM-DD}.md`, append-new-file.

### `draft-promotion-case`

**Purpose:** Compose a promotion case for a report. Pulls from prior reviews, development plan check-ins, and coaching signals to build the leveling-ladder evidence argument.

**Triggers:**
- "build a promotion case for [report]"
- "draft promo case: [report] to [level]"

**Reads:**
- `cto-os-data/modules/performance-development/state/records/{person-slug}.md`
- `cto-os-data/modules/performance-development/state/leveling-ladder.md` (target-level expectations)
- `cto-os-data/modules/performance-development/state/reviews/{person-slug}/` (recent reviews)
- `cto-os-data/modules/performance-development/state/development-plans/{person-slug}/` (growth evidence)
- `cto-os-data/modules/managing-down/state/coaching/{person-slug}/` (optional — recognition moments)

**Writes:** `cto-os-data/modules/performance-development/state/promotion-cases/{person-slug}/{cycle}-{YYYY-MM-DD}.md`, append-new-file with `status: draft`. Status transitions to `submitted` / `approved` / `denied` as the case moves through calibration.

### `open-pip`

**Purpose:** Start a Performance Improvement Plan for a report. Captures the gap being addressed, success criteria, timeline, and cadence of check-ins. PIPs are high-stakes — opening one explicitly engages a path that ends in either success or exit.

**Triggers:**
- "open a PIP for [report]"
- "put [report] on a PIP — here's why"

**Reads:**
- `cto-os-data/modules/performance-development/state/records/{person-slug}.md`
- `cto-os-data/modules/performance-development/state/reviews/{person-slug}/` (pattern of concerns)
- `cto-os-data/modules/managing-down/state/coaching/{person-slug}/` (prior feedback already given)

**Writes:** `cto-os-data/modules/performance-development/state/pips/{person-slug}/{YYYY-MM-DD}.md`, append-new-file with `status: active`. Updates the person's `performance-record.md` with `active_pip: <pip-slug>`.

### `update-pip`

**Purpose:** Log a PIP check-in. Captures progress against the gap, whether milestones are being met, any adjustments to the plan.

**Triggers:**
- "update [report]'s PIP"
- "PIP check-in with [report]"

**Reads:** `cto-os-data/modules/performance-development/state/pips/{person-slug}/{pip-slug}.md`.

**Writes:** `cto-os-data/modules/performance-development/state/pips/{person-slug}/{pip-slug}.md`, overwrite-with-history.

### `close-pip`

**Purpose:** Close a PIP as successful (report re-cleared the bar) or unsuccessful (ends in exit / role change). Captures the outcome and learnings.

**Triggers:**
- "close [report]'s PIP — they hit the bar"
- "close the PIP — we're parting ways"

**Reads:** `cto-os-data/modules/performance-development/state/pips/{person-slug}/{pip-slug}.md`.

**Writes:** `cto-os-data/modules/performance-development/state/pips/{person-slug}/{pip-slug}.md` — sets `status: closed-successful | closed-exit | closed-role-change`, `closed_date`. Updates the person's record to clear `active_pip`.

### `log-succession-note`

**Purpose:** Capture succession thinking for a key role — who could succeed the current occupant, what gaps the successor(s) would need to close, contingency posture. One file per (key role, successor candidate) pairing, OR per key role with multiple candidates in the body.

**Triggers:**
- "log succession note for [role]"
- "succession planning: [role]"
- "who could succeed [person]"

**Reads:**
- `cto-os-data/modules/performance-development/state/records/` (candidate trajectories)
- `cto-os-data/modules/performance-development/state/leveling-ladder.md`
- `cto-os-data/modules/team-management/state/teams/` (context on the role)

**Writes:** `cto-os-data/modules/performance-development/state/succession/{role-slug}.md`, overwrite-with-history. One file per key role; candidates listed inside.

### `show-performance-rollup`

**Purpose:** Assemble a read-time view of current performance posture across the user's org — who's on a PIP, who's in an active development plan, who's up for promotion consideration, distribution by level, trajectories.

**Triggers:**
- "show performance rollup"
- "where is everyone right now"
- "who's on PIP / development plan / promotion track"

**Reads:** `scan(type=["performance-record"], fields=["slug", "current_level", "current_trajectory", "active_pip", "active_development_plan", "last_review_date"])`.

**Writes:** —

## Persistence

- **`cto-os-data/modules/performance-development/state/review-cycle.md`** — singleton (`slug: current`), overwrite-with-history. Frontmatter: `type: review-cycle, slug: current, updated: <date>, cadence: <string>, structure: <list>, rubric_reference: <string>, calibration_expectation: <string>, cycle_dates: <list>`. Body: notes + `## History`.
- **`cto-os-data/modules/performance-development/state/leveling-ladder.md`** — singleton (`slug: current`), overwrite-with-history. Frontmatter: `type: leveling-ladder, slug: current, updated: <date>, levels: <list>, expectations_per_level: <dict>, variants: <list, optional>`. Body: narrative + `## History`.
- **`cto-os-data/modules/performance-development/state/records/{person-slug}.md`** — one file per report, overwrite-with-history. Frontmatter: `type: performance-record, slug: <person-slug>, updated: <date>, active: <bool>, current_level: <string>, level_tenure_months: <int>, last_review_date: <date, optional>, current_trajectory: <growing|steady|concerning|excelling>, active_pip: <pip-slug, optional>, active_development_plan: <plan-slug, optional>`. Body: trend narrative + `## History` with dated trajectory changes.
- **`cto-os-data/modules/performance-development/state/reviews/{person-slug}/{cycle}-{YYYY-MM-DD}.md`** — append-new-file per review. Frontmatter: `type: performance-review, slug: <person-slug>-<cycle>-<YYYY-MM-DD>, updated: <date>, person: <person-slug>, cycle: <string>, status: <draft|delivered>, level_at_review: <string>`. Body sections match the declared review structure. **Immutable** once status is `delivered`.
- **`cto-os-data/modules/performance-development/state/development-plans/{person-slug}/{YYYY-MM-DD}.md`** — append-new-file per plan; one file per plan lifecycle (check-ins captured in body history). Frontmatter: `type: development-plan, slug: <person-slug>-<YYYY-MM-DD>, updated: <date>, person: <person-slug>, status: <active|closed-succeeded|closed-abandoned>, goals: <list>, time_horizon: <string>, check_in_cadence: <string>, opened: <date>, closed_date: <date, optional>`. Body: plan detail + `## Check-ins` with dated entries.
- **`cto-os-data/modules/performance-development/state/calibrations/{YYYY-MM-DD}.md`** — append-new-file per calibration session. Frontmatter: `type: calibration-session, slug: <YYYY-MM-DD>, updated: <date>, participants: <list>, cohort: <string>`. Body sections: `## Per-person assessments`, `## Dissent & resolution`, `## Final decisions`, `## Open threads`.
- **`cto-os-data/modules/performance-development/state/promotion-cases/{person-slug}/{cycle}-{YYYY-MM-DD}.md`** — append-new-file per case. Frontmatter: `type: promotion-case, slug: <person-slug>-<cycle>-<YYYY-MM-DD>, updated: <date>, person: <person-slug>, from_level: <string>, to_level: <string>, status: <draft|submitted|approved|denied>, submitted_date: <date, optional>, decision_date: <date, optional>`. Body sections: `## Case summary`, `## Evidence per dimension`, `## Trajectory`, `## Risks`.
- **`cto-os-data/modules/performance-development/state/pips/{person-slug}/{YYYY-MM-DD}.md`** — one file per PIP lifecycle, overwrite-with-history. Frontmatter: `type: pip, slug: <person-slug>-<YYYY-MM-DD>, updated: <date>, person: <person-slug>, status: <active|closed-successful|closed-exit|closed-role-change>, gap_summary: <string>, success_criteria: <list>, time_horizon: <string>, check_in_cadence: <string>, opened: <date>, closed_date: <date, optional>`. Body: plan detail + `## Check-ins` + outcome notes.
- **`cto-os-data/modules/performance-development/state/succession/{role-slug}.md`** — one file per key role, overwrite-with-history. Frontmatter: `type: succession-note, slug: <role-slug>, updated: <date>, role: <string>, current_occupant: <person-slug, optional>, candidates: <list of {person-slug, readiness: now|1-year|2-plus-years, gap_notes}>`. Body: context + `## History`.

**Overrides to the cross-cutting save rule** ([Persistence model](../../docs/ARCHITECTURE.md#persistence-model)): performance reviews save as `status: draft` first; the user explicitly flips to `delivered` when the review has actually been delivered to the report (body is then immutable). Promotion cases have similar draft/submitted lifecycle. PIPs always require explicit user confirmation before `open-pip` writes — this is a high-stakes action and should never happen on a loose narrative.

**Sensitivity:** `sensitivity: high` at module level. Reviews, PIPs, calibration, and promotion cases all contain material that's damaging if leaked (career-impacting, legally sensitive in the PIP case). Scan excludes this module's state by default.

## State location

`cto-os-data/modules/performance-development/state/`
