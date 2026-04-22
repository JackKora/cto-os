---
name: hiring
description: "Activates for the full hiring lifecycle — workforce planning, requisition opening with scorecards, candidate pipeline tracking, interview debrief capture, offer construction, and ramp planning for new hires. Covers: declaring the interview process playbook, opening and closing reqs, moving candidates through stages, logging interview debriefs in structured scorecard format, constructing offers (pulling cost context from Budget when available), and authoring ramp plans that cover a new hire's first 30 / 60 / 90 days. Also activates on oblique phrasings like 'open a req for [role],' 'prep for today's candidate debrief,' 'draft an offer for [name],' 'plan [name]'s ramp,' 'we need to rebalance the hiring plan,' 'interviewing [candidate] for [role].' Does NOT activate on ongoing performance after ramp (Performance & Development takes over); team-aggregate health (Team Management); or role-definition work that's pre-planning (Org Design)."
requires: []
optional:
  - business-alignment
  - budget
  - team-management
---

# Hiring

## Scope

Bringing talented people into the organization. Owns the full lifecycle from identifying a hiring need through to the new person being productive on the team. Covers workforce planning (what we need to hire and why), the declared interview process (rounds, scorecards, debrief cadence), active requisitions and their scorecards, candidate pipelines, interview debriefs, offer construction, and ramp-plan authorship for new hires. Role-shape module — essential in growth-phase orgs, less central in steady-state.

## Out of scope

- **Ongoing performance after ramp** — Performance & Development takes over once ramp is complete.
- **Team-aggregate health and composition** — Team Management (which consumes Hiring's output: "who joined / who left").
- **Role-need identification that predates the req** — Org Design (strategic team structure decisions) or Team Management (baseline team composition). Hiring picks up once a req is justified and ready to open.
- **Individual 1:1 and coaching of existing reports** — Managing Down.

## Frameworks

- [Geoff Smart & Randy Street — *Who: The A Method for Hiring*](https://www.amazon.com/Who-Geoff-Smart/dp/0345504194) — scorecard-driven, outcome-focused hiring. Start with the scorecard, not the JD.
  - *How this module applies it:* every requisition starts with a scorecard — mission for the role, outcomes expected in the first year, competencies required. The scorecard is the source of truth for interview design and debrief rubrics. `open-requisition` can't complete without a scorecard in place. Candidates are evaluated against the scorecard, not against vague "culture fit" signals.

- [Google — structured interviewing (re:Work)](https://rework.withgoogle.com/guides/hiring-use-structured-interviewing/) — consistent questions, rubric scoring, reduced bias.
  - *How this module applies it:* the declared `interview-process` singleton specifies the loop — which rounds, which interviewer roles, and which rubric dimensions. Every interview debrief scores against those rubric dimensions (1–4 typically; a clear range, not an open scale). Debrief capture enforces the structure — interviewers write their assessment against each dimension before seeing others' debriefs.

## Triggers

- "open a req for [role]" / "close the [role] req"
- "update the workforce plan" / "rebalance headcount"
- "log candidate: [name] for [role]"
- "update [candidate] — moved to onsite / rejected / accepted"
- "prep for today's debrief on [candidate]"
- "log debrief for [candidate] on [round]"
- "construct an offer for [candidate]"
- "write ramp plan for [new hire]"
- "update the interview process" / "we're adding a technical screen"
- Oblique: "I need to hire [X] by Q3"
- Oblique: "how's the [role] pipeline looking"

## Activation flow

Each step writes a concrete artifact and appends its step number to `activation_completed` in `_module.md`.

### 1. Workforce plan

**Ask:** "What's the current workforce plan? Break it down by team: headcount targets (year-end or quarter-end), what roles are open vs. planned-but-not-open, rationale (why each role is needed). If you have a formal plan, walk me through it; if not, let's capture your best current picture — we'll refine as the year goes."
**Writes:** `cto-os-data/modules/hiring/state/workforce-plan.md` with `type: workforce-plan`, `slug: current`, `period`, `targets`, `rationale`.
**Expects:** frontmatter has `period` set and `targets` has at least one team entry.

### 2. Interview process playbook

**Ask:** "How does your interview loop work? Typical rounds (recruiter screen, hiring-manager screen, technical, onsite panel, exec, reference checks), rubric dimensions used at debrief, scorecard structure, who has the hire/no-hire authority. If you have variations by level (IC vs. lead vs. exec), capture those separately."
**Writes:** `cto-os-data/modules/hiring/state/interview-process.md` with `type: interview-process`, `slug: current`, `rounds`, `rubric_dimensions`, `scorecard_template`, `authority`, `level_variants`.
**Expects:** frontmatter has `rounds` (list ≥ 1), `rubric_dimensions` (list ≥ 3), and `authority` set.

### 3. Active requisitions

**Ask:** "Which reqs are currently open? For each: role title, team, level, short scorecard (mission + outcomes + competencies), status (actively sourcing / actively interviewing / offer out / on hold), who owns it."
**Writes:** one file per active req at `cto-os-data/modules/hiring/state/reqs/{req-slug}.md` with `type: requisition`, `slug`, `role`, `team`, `level`, `scorecard`, `status`, `owner`.
**Expects:** at least one req file exists, or the user explicitly confirms no reqs are currently open (activation can complete with zero reqs — small / late-stage orgs may have none).

## Skills

### `update-workforce-plan`

**Purpose:** Revise the workforce plan — new targets, role changes, budget shifts.

**Triggers:**
- "update workforce plan"
- "rebalance headcount"
- "we got approval for two more SREs — update the plan"

**Reads:**
- `cto-os-data/modules/hiring/state/workforce-plan.md`
- `cto-os-data/modules/business-alignment/state/company-goals/` (optional — strategic framing)
- `cto-os-data/modules/budget/state/` (optional — cost constraints)

**Writes:** `cto-os-data/modules/hiring/state/workforce-plan.md`, overwrite-with-history.

### `update-interview-process`

**Purpose:** Revise the interview process — new rounds, changed rubric, new level variant.

**Triggers:**
- "update the interview process"
- "we're adding a technical screen"
- "change the rubric for staff-level"

**Reads:** `cto-os-data/modules/hiring/state/interview-process.md`.

**Writes:** `cto-os-data/modules/hiring/state/interview-process.md`, overwrite-with-history.

### `open-requisition`

**Purpose:** Open a new req. Requires a scorecard (per *Who*) before the req is considered complete.

**Triggers:**
- "open a req for [role]"
- "new req: [role]"

**Reads:**
- `cto-os-data/modules/hiring/state/workforce-plan.md` (validate against plan)
- `cto-os-data/modules/hiring/state/interview-process.md` (defaults for scorecard template)

**Writes:** `cto-os-data/modules/hiring/state/reqs/{req-slug}.md`, append-new-file with `status: sourcing`.

### `close-requisition`

**Purpose:** Close a req (filled, cancelled, or on-hold-indefinitely). Preserves history.

**Triggers:**
- "close the [role] req"
- "we filled [role]"
- "cancel the [role] req"

**Reads:** `cto-os-data/modules/hiring/state/reqs/{req-slug}.md`.

**Writes:** `cto-os-data/modules/hiring/state/reqs/{req-slug}.md` — sets `status: filled|cancelled|on-hold`, `closed_date`, reason in body.

### `log-candidate`

**Purpose:** Add a candidate to a req's pipeline.

**Triggers:**
- "log candidate: [name] for [role]"
- "new candidate: [name]"

**Reads:** `cto-os-data/modules/hiring/state/reqs/{req-slug}.md` (valid req, capacity).

**Writes:** `cto-os-data/modules/hiring/state/candidates/{req-slug}/{candidate-slug}.md`, append-new-file with `stage: applied`.

### `update-candidate`

**Purpose:** Move a candidate through pipeline stages (applied → screening → onsite → offer → accepted/declined/rejected). Captures stage transitions in history.

**Triggers:**
- "update [candidate] — moved to onsite"
- "[candidate] accepted / rejected / withdrew"
- "progress [candidate] in [role]"

**Reads:** `cto-os-data/modules/hiring/state/candidates/{req-slug}/{candidate-slug}.md`.

**Writes:** `cto-os-data/modules/hiring/state/candidates/{req-slug}/{candidate-slug}.md`, overwrite-with-history (stage transitions preserved in body under `## History`).

### `log-debrief`

**Purpose:** Capture an interview debrief. Structured by the rubric dimensions declared in the interview process; each dimension scored independently before the interviewer sees others'.

**Triggers:**
- "log debrief for [candidate] on [round]"
- "capture my interview notes for [candidate]"

**Reads:**
- `cto-os-data/modules/hiring/state/interview-process.md` (rubric dimensions)
- `cto-os-data/modules/hiring/state/candidates/{req-slug}/{candidate-slug}.md` (context)

**Writes:** `cto-os-data/modules/hiring/state/debriefs/{req-slug}/{candidate-slug}/{YYYY-MM-DD}-{round}.md`, append-new-file.

### `construct-offer`

**Purpose:** Build an offer for a candidate. Pulls from workforce-plan (approved band), budget (cost context if available), and the interview debriefs (strengths to emphasize). Does not send the offer — produces a structured proposal the user reviews, edits, and sends externally.

**Triggers:**
- "construct an offer for [candidate]"
- "draft offer: [candidate] for [role]"

**Reads:**
- `cto-os-data/modules/hiring/state/candidates/{req-slug}/{candidate-slug}.md`
- `cto-os-data/modules/hiring/state/debriefs/{req-slug}/{candidate-slug}/` (all debriefs for that candidate)
- `cto-os-data/modules/hiring/state/workforce-plan.md` (bands, approved comp)
- `cto-os-data/modules/budget/state/` (optional — cost envelope)

**Writes:** —  (produces proposal for user review; if user captures the final offer, it goes into the candidate file's body under `## Offer`)

### `log-ramp-plan`

**Purpose:** Author a ramp plan for a new hire (30 / 60 / 90 day expectations). Created post-offer-accepted; handoff to Performance & Development happens at end of ramp.

**Triggers:**
- "write ramp plan for [new hire]"
- "[new hire] starts in two weeks — draft their first-90"

**Reads:**
- `cto-os-data/modules/hiring/state/candidates/{req-slug}/{candidate-slug}.md` (scorecard, expectations)
- `cto-os-data/modules/team-management/state/teams/{team-slug}.md` (optional — team they're joining)

**Writes:** `cto-os-data/modules/hiring/state/ramp-plans/{person-slug}.md`, append-new-file.

## Persistence

- **`cto-os-data/modules/hiring/state/workforce-plan.md`** — singleton (`slug: current`), overwrite-with-history. Frontmatter: `type: workforce-plan, slug: current, updated: <date>, period: <string>, targets: <list of {team, target_headcount, rationale}>`. Body: overall narrative + `## History`.
- **`cto-os-data/modules/hiring/state/interview-process.md`** — singleton (`slug: current`), overwrite-with-history. Frontmatter: `type: interview-process, slug: current, updated: <date>, rounds: <list>, rubric_dimensions: <list>, scorecard_template: <string>, authority: <string>, level_variants: <list, optional>`. Body: rationale + `## History`.
- **`cto-os-data/modules/hiring/state/reqs/{req-slug}.md`** — one file per req, overwrite-with-history. Frontmatter: `type: requisition, slug: <req-slug>, updated: <date>, role: <string>, team: <string>, level: <string>, scorecard: <dict of {mission, outcomes, competencies}>, status: <sourcing|interviewing|offer-out|on-hold|filled|cancelled>, owner: <string>, opened: <date>, closed_date: <date, optional>`. Body: `## History`.
- **`cto-os-data/modules/hiring/state/candidates/{req-slug}/{candidate-slug}.md`** — one file per candidate per req, overwrite-with-history (stage transitions are history). Frontmatter: `type: candidate, slug: <candidate-slug>, updated: <date>, name: <string>, req: <req-slug>, stage: <applied|screening|onsite|offer|accepted|declined|rejected|withdrew>, source: <string>`. Body: candidate context + `## History` + `## Offer` (if an offer was constructed).
- **`cto-os-data/modules/hiring/state/debriefs/{req-slug}/{candidate-slug}/{YYYY-MM-DD}-{round}.md`** — append-new-file per interview. Frontmatter: `type: interview-debrief, slug: <candidate-slug>-<YYYY-MM-DD>-<round>, updated: <date>, candidate: <candidate-slug>, req: <req-slug>, round: <string>, interviewer: <string>, scores: <dict, keys match rubric dimensions>`. Body: observations + recommendation (hire / no hire / hire with caveats).
- **`cto-os-data/modules/hiring/state/ramp-plans/{person-slug}.md`** — append-new-file per ramp plan. Frontmatter: `type: ramp-plan, slug: <person-slug>, updated: <date>, person: <person-slug>, start_date: <date>, ramp_status: <active|complete|interrupted>`. Body sections: `## First 30 days`, `## First 60 days`, `## First 90 days`, `## Success criteria`.

**Overrides to the cross-cutting save rule** ([Persistence model](../../docs/ARCHITECTURE.md#persistence-model)): candidate and debrief captures happen without blocking during active recruiting cycles (speed matters). Candidate files containing comp asks or private feedback can be flagged `sensitivity: high` per-file; module default is `standard`.

## State location

`cto-os-data/modules/hiring/state/`
