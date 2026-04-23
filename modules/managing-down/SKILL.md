---
name: managing-down
description: "Activates for leading and developing the people who report to the user directly. Covers: 1:1 prep and capture with direct reports, coaching conversations and feedback moments outside 1:1s, team-wide communication drafts in the user's voice, stakeholder profiles of reports (observable preferences and concerns), delegation decisions, and leadership-presence work. Also activates on oblique phrasings like 'prep for my 1:1 with Jane,' 'Mike has been drifting,' 'I need to give [report] feedback,' 'draft team-wide comms,' 'coach [report] on [topic],' 'delegate [task] to [report].' Does NOT activate on individual-level performance tracking, calibration, promotions, or PIPs (Performance & Development); team-aggregate health (Team Management); peer relationships (Managing Sideways); or upward relationships (Managing Up)."
requires: []
optional:
  - team-management
  - performance-development
  - personal-os
  - attention-operations
---

# Managing Down

## Scope

Leading and developing the people who report to the user directly. The leadership relationship — 1:1s, coaching, feedback in the moment, delegation, team-wide communication, maintaining presence. Tracks lightweight profiles of direct reports (observable preferences and behaviors only) and captures the ongoing cadence of interactions that build trust and deliver growth.

## Out of scope

- **Individual-level performance tracking, calibration, promotions, PIPs** — Performance & Development. This module is about the leadership *relationship*; Performance & Development owns the administrative arc.
- **Team-aggregate health and composition** — Team Management.
- **Peer relationships and cross-functional influence** — Managing Sideways.
- **Upward relationships** — Managing Up.
- **Hiring pipeline and onboarding ramp** — Hiring owns pre-ramp; this module picks up once the report is productive.

## Frameworks

- [Kim Scott — *Radical Candor*](https://www.radicalcandor.com/) — care personally, challenge directly; feedback grounded in specific observed behavior.
  - *How this module applies it:* every coaching event and feedback moment captured here follows the Radical Candor frame — what specifically happened (observation), what impact it had (consequence), what to do differently (ask). No inference of motive, no character judgments. The 1:1 `## Signals` section uses the same lens: what did I observe, what might it mean, what will I do with it.

- [Andy Grove — *High Output Management*](https://www.amazon.com/High-Output-Management-Andrew-Grove/dp/0679762884) — 1:1 structure (report owns the agenda), delegation (task-relevant maturity), team-as-peer-group framing for managers.
  - *How this module applies it:* 1:1 prep puts the agenda on the report, not the manager. `prep-1on1-down` surfaces what the report has been working on, open threads from the last session, and any signals the user has captured — but keeps the decision of "what to discuss" with the report. Delegation capture uses task-relevant maturity framing: for this task, for this person, what level of oversight is right.

## Triggers

- "prep for my 1:1 with [report]"
- "log my 1:1 with [report]"
- "[report] has been drifting / stuck / doing great"
- "I need to give [report] feedback"
- "coach [report] on [topic]"
- "delegate [project] to [report]"
- "draft team-wide comms" / "announce [thing] to my team"
- "update [report]'s profile"
- "add [person] as a new direct report" / "[person] just joined my team"
- "[report] is leaving" / "remove [report]"
- Oblique: "Mike was weird in standup today"
- Oblique: "I'm not sure how to help Jane" / "[report] doesn't seem motivated"

## Activation flow

Each step writes a concrete artifact and appends its step number to `activation_completed` in `_module.md`.

### 1. Enumerate direct reports

**Ask:** "Walk me through your current direct reports. For each: name, role/title, short slug (kebab-case — first name, or first-last if you have two reports with the same first name), how long they've been reporting to you."
**Writes:** one file per report at `cto-os-data/modules/managing-down/state/people/{person-slug}.md` with `type: stakeholder-profile`, `slug: <person-slug>`, `name`, `role`, `relationship: direct-report`, `tenure_months: <int>`.
**Expects:** at least one report file exists with all four fields.

### 2. Baseline profile per report

**Ask:** "For each report, what do you already know about how they work — from observation, not inference? (a) communication preferences — channel, cadence, when they want a message and when they don't; (b) what they want first in a 1:1 — to vent, to think-out-loud, to get direction, to hear feedback; (c) typical concerns they raise; (d) how much context they want before an ask; (e) known sensitivities; (f) current trust and relationship status. Skip any field you don't have a grounded answer for."
**Writes:** updates each report file's frontmatter with the six profile fields.
**Expects:** each file has at least `communication_preferences` and `what_they_want_first` set.

### 3. Set 1:1 cadence per report

**Ask:** "What's the 1:1 cadence per report? Weekly is common for most; bi-weekly or less if the report is senior and you talk often otherwise. For each: cadence + who sets the agenda (the report usually, per Andy Grove)."
**Writes:** updates each report file with `cadence` and `agenda_owner` in frontmatter.
**Expects:** each report file has `cadence` set.

## Skills

### `log-1on1-down`

**Purpose:** Capture a 1:1 with a direct report. Topics the report brought, decisions made, follow-ups for either side, signals observed (motivation, confusion, blockers, growth moments).

**Triggers:**
- "log my 1:1 with [report]"
- "[report]'s 1:1 just ended — here's what happened"

**Reads:**
- `cto-os-data/modules/managing-down/state/people/{person-slug}.md`
- `cto-os-data/modules/managing-down/state/1on1s/{person-slug}/` (recent)

**Writes:** `cto-os-data/modules/managing-down/state/1on1s/{person-slug}/{YYYY-MM-DD}.md`, append-new-file.

### `prep-1on1-down`

**Purpose:** Prepare for an upcoming 1:1 with a report. Pulls recent 1:1 notes, open follow-ups, profile context, and any relevant signals from Team Management / Performance & Development to anticipate what might come up and what to raise if the report doesn't.

**Triggers:**
- "prep for my 1:1 with [report]"
- "what should I bring to [report]'s 1:1"

**Reads:**
- `cto-os-data/modules/managing-down/state/people/{person-slug}.md`
- `cto-os-data/modules/managing-down/state/1on1s/{person-slug}/` (last 3)
- `cto-os-data/modules/managing-down/state/coaching/{person-slug}/` (recent coaching events)
- `cto-os-data/modules/team-management/state/teams/` (optional — their team's current health)
- `cto-os-data/modules/performance-development/state/` (optional — any active development threads)
- `cto-os-data/modules/personal-os/state/show-up.md` (optional — framing)

**Writes:** — (prep notes surfaced; follow-ups captured through `log-1on1-down` later)

### `update-profile-down`

**Purpose:** Refine a report's profile based on new observations. Observations accumulate; profile evolves.

**Triggers:**
- "update [report]'s profile"
- "I noticed [report] consistently [behavior]"

**Reads:** `cto-os-data/modules/managing-down/state/people/{person-slug}.md`.

**Writes:** `cto-os-data/modules/managing-down/state/people/{person-slug}.md`, overwrite-with-history.

### `log-coaching`

**Purpose:** Capture a coaching conversation or substantial feedback moment that happens *outside* a regularly scheduled 1:1 — a hallway conversation, a course-correct after a meeting, a delegation handoff, a recognition moment. Different from `log-1on1-down` in that these are bite-sized and often in-the-moment.

**Triggers:**
- "log a coaching moment with [report]"
- "I just gave [report] feedback on [situation]"
- "[report] and I talked about [topic] after standup"

**Reads:**
- `cto-os-data/modules/managing-down/state/people/{person-slug}.md`

**Writes:** `cto-os-data/modules/managing-down/state/coaching/{person-slug}/{YYYY-MM-DD}.md`, append-new-file per coaching event.

### `draft-team-comms`

**Purpose:** Draft team-wide communication in the user's voice — reorg announcement, priority shift, praise for a shipped thing, a hard message about a miss.

**Triggers:**
- "draft team-wide comms"
- "announce [thing] to my team"
- "write a Slack post to the team about [X]"

**Reads:**
- `cto-os-data/modules/personal-os/state/voice/` (optional — tone)
- `cto-os-data/modules/personal-os/state/show-up.md` (optional — framing)
- `cto-os-data/modules/managing-down/state/people/` (awareness of audience sensitivities)

**Writes:** — (produces a draft for the user to review and send; capture-through only if the user asks to preserve the final version.)

### `add-report`

**Purpose:** Add a new direct report post-activation.

**Triggers:**
- "add [person] as a direct report"
- "[person] just joined my team"

**Reads:** `cto-os-data/modules/managing-down/state/people/` (slug collision check).

**Writes:** `cto-os-data/modules/managing-down/state/people/{person-slug}.md`, append-new-file.

### `remove-report`

**Purpose:** Handle a report leaving the team (reorg, departure, promoted out). Preserves the file and history — file is marked inactive so scan excludes it by default, but tenure-of-relationship context stays accessible if needed for succession or retrospective.

**Triggers:**
- "[report] is leaving the team"
- "[report] got promoted out"
- "remove [report]"

**Reads:** `cto-os-data/modules/managing-down/state/people/{person-slug}.md`.

**Writes:** `cto-os-data/modules/managing-down/state/people/{person-slug}.md` — sets `active: false`, `departed_date`, reason in body history.

## Persistence

- **`cto-os-data/modules/managing-down/state/people/{person-slug}.md`** — one file per direct report, overwrite-with-history. Frontmatter: `type: stakeholder-profile, slug: <person-slug>, updated: <date>, active: <bool>, name: <string>, role: <string>, relationship: direct-report, tenure_months: <int>, departed_date: <date, optional>, cadence: <string>, agenda_owner: <self|them|shared>, communication_preferences: <string>, what_they_want_first: <string>, typical_concerns: <list>, context_needs: <string>, known_sensitivities: <list>, relationship_status: <string>`. Body: free-form relationship notes + `## History`.
- **`cto-os-data/modules/managing-down/state/1on1s/{person-slug}/{YYYY-MM-DD}.md`** — append-new-file per 1:1. Frontmatter: `type: report-1on1, slug: <person-slug>-<YYYY-MM-DD>, updated: <date>, person: <person-slug>`. Body sections: `## Topics`, `## Decisions`, `## Follow-ups`, `## Signals`.
- **`cto-os-data/modules/managing-down/state/coaching/{person-slug}/{YYYY-MM-DD}.md`** — append-new-file per coaching event. Frontmatter: `type: coaching-event, slug: <person-slug>-<YYYY-MM-DD>, updated: <date>, person: <person-slug>, event_type: <feedback|recognition|delegation|course-correct|other>`. Body: Radical Candor structure — observation, impact, ask.

**Overrides to the cross-cutting save rule** ([Persistence model](../../docs/ARCHITECTURE.md#persistence-model)): 1:1 and coaching captures happen without blocking when the user narrates a just-happened event. Profile updates confirm when the inference is indirect.

**Sensitivity:** `sensitivity: high` at module level. Reports' profiles and 1:1 notes contain candid assessments, coaching signals, and private concerns. Scan excludes this module's state by default; callers opt in explicitly.

## State location

`cto-os-data/modules/managing-down/state/`
