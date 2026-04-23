---
name: managing-up
description: "Activates for managing the relationship, narrative, and perception upward with whoever the user reports to (and skip-levels where relevant). Covers: 1:1 prep and capture with your boss, executive summaries translating team-level work to higher altitude, selling ideas upward, managing perceptions through periodic touchpoints, tracking stakeholder profiles (what your boss wants first, typical concerns, known sensitivities). Also activates on oblique phrasings like 'prep for my 1:1 with my boss,' 'draft an exec summary,' 'help me sell the X proposal upward,' 'my boss pushed back,' 'I need to manage [exec] better.' Does NOT activate on direct-report relationships (Managing Down), peer relationships (Managing Sideways), external peer/mentor relationships (External Network & Thought Leadership), or board-level communication (Board Comms)."
requires: []
optional:
  - personal-os
  - business-alignment
  - team-management
  - attention-operations
---

# Managing Up

## Scope

Managing the relationship, narrative, and perception upward with whoever the user reports to. Translating team-level work into a story that resonates at higher altitude. Tracks a lightweight profile of upward stakeholders (boss, skip-level, dotted-line) and captures the 1:1 cadence and follow-up threads that accrue between them.

## Out of scope

- **Direct reports and coaching** — Managing Down.
- **Peer and cross-functional relationships** — Managing Sideways.
- **External advisors, mentors, peer CTOs** — External Network & Thought Leadership.
- **Board-level strategic communication** — Board Comms.
- **Organization-wide internal communication** — Org Comms.

## Frameworks

- [Andy Grove — *High Output Management*](https://www.amazon.com/High-Output-Management-Andrew-Grove/dp/0679762884) — the managing-your-manager and altitude-shifting chapters.
  - *How this module applies it:* Grove's core frame — your boss's time is the leverage point; 1:1 ownership sits with the report, not the manager. 1:1 prep puts the agenda on you, not them. When translating upward, Grove's altitude framing applies: strip detail the boss can't act on at their altitude, keep decisions and risks they own. "What does my boss need to know, decide, or de-risk?" is the filter.

- Stakeholder-needs analysis (cross-cutting stakeholder profile format, see `docs/ARCHITECTURE.md` and `README.md`).
  - *How this module applies it:* the boss's profile captures observable preferences only — what they ask for first (numbers / stories / risks / options), their typical concerns, what context they need before an ask, what topics they've reacted to before. Used by `prep-1on1-up` and `draft-exec-summary` to tune framing. Profile evolves as observations accumulate; don't infer personality, only capture behavior.

## Triggers

- "prep for my 1:1 with [boss]"
- "log my 1:1 with [boss]"
- "draft an exec summary" / "translate this for my boss"
- "help me sell [idea/proposal] upward"
- "my boss pushed back on [X] — help me reframe"
- "update my boss's profile"
- "add [person] as an upward stakeholder" (new boss, new skip-level, interim exec)
- Oblique: "I need to manage [exec] better"
- Oblique: "my boss seems to be losing patience with [X]"

## Activation flow

Each step writes a concrete artifact and appends its step number to `activation_completed` in `_module.md`.

### 1. Enumerate upward stakeholders

**Ask:** "Who do you report to? Start with your direct manager. If skip-level matters (a skip who takes active interest in your work, a dotted-line manager, or an exec you're accountable to on a specific initiative), include them too. For each: name, role, short slug (kebab-case of first name or first-last)."
**Writes:** one file per stakeholder at `cto-os-data/modules/managing-up/state/people/{person-slug}.md` with `type: stakeholder-profile`, `slug: <person-slug>`, `name`, `role`, `relationship: direct-manager | skip-level | dotted-line | other`.
**Expects:** at least one stakeholder file exists with all four fields set.

### 2. Baseline profile per stakeholder

**Ask:** "For each upward stakeholder, what do you already know about how they work? Use observable behavior, not inferred personality: (a) how do they want to communicate — channel, cadence, format; (b) what do they want first in an update — numbers, stories, risks, options; (c) typical concerns they push on; (d) how much context before an ask; (e) known sensitivities or topics they've reacted to before; (f) relationship status — current trust level, any open threads. Skip any field you don't have a grounded answer for — empty is fine."
**Writes:** updates each stakeholder file's frontmatter with the six profile fields.
**Expects:** each file's frontmatter has at least `communication_preferences` and `what_they_want_first` set (the two most-used fields).

### 3. Set 1:1 cadence

**Ask:** "What's the 1:1 cadence with each upward stakeholder? Weekly / bi-weekly / monthly / ad-hoc. Who sets the agenda — you or them?"
**Writes:** updates each stakeholder file's frontmatter with `cadence` and `agenda_owner` (self | them | shared).
**Expects:** each stakeholder file has `cadence` set.

## Skills

### `log-1on1-up`

**Purpose:** Capture a 1:1 meeting with an upward stakeholder. Topics discussed, decisions made, follow-ups, signals about perception and concerns.

**Triggers:**
- "log my 1:1 with [boss]"
- "just finished my 1:1, here's what happened"

**Reads:**
- `cto-os-data/modules/managing-up/state/people/{person-slug}.md` (context)
- `cto-os-data/modules/managing-up/state/1on1s/{person-slug}/` (recent history)

**Writes:** `cto-os-data/modules/managing-up/state/1on1s/{person-slug}/{YYYY-MM-DD}.md`, append-new-file.

### `prep-1on1-up`

**Purpose:** Prepare for an upcoming 1:1. Pulls recent 1:1 notes, open threads, the stakeholder's profile, and any relevant current work from Team Management / Business Alignment to surface what to raise, what to translate upward, and what the stakeholder is likely to ask.

**Triggers:**
- "prep for my 1:1 with [boss]"
- "what should I bring to tomorrow's 1:1 with [boss]"

**Reads:**
- `cto-os-data/modules/managing-up/state/people/{person-slug}.md`
- `cto-os-data/modules/managing-up/state/1on1s/{person-slug}/` (last 3 most recent)
- `cto-os-data/modules/team-management/state/teams/` (optional — team-level summaries)
- `cto-os-data/modules/business-alignment/state/work-mapping.md` (optional — what ladders up)
- `cto-os-data/modules/personal-os/state/show-up.md` (optional — framing)

**Writes:** — (surfaced to user as prep notes; no persistent artifact unless the user captures follow-ups, which route through `log-1on1-up`)

### `update-profile-up`

**Purpose:** Refine an upward stakeholder's profile based on new observations. Fields grow richer over time; prior profile versions preserved as history.

**Triggers:**
- "update my boss's profile"
- "I noticed [boss] keeps pushing on [X]"
- "[boss] responded well to [framing] — capture that"

**Reads:** `cto-os-data/modules/managing-up/state/people/{person-slug}.md`.

**Writes:** `cto-os-data/modules/managing-up/state/people/{person-slug}.md`, overwrite-with-history.

### `draft-exec-summary`

**Purpose:** Translate detailed team- or initiative-level work into an executive-summary-suitable narrative, tuned to the target boss's profile. Uses the stakeholder's `what_they_want_first` to order content and `communication_preferences` to pick form.

**Triggers:**
- "draft an exec summary of [topic] for my boss"
- "translate this for [boss]"
- "write this up at VP altitude"

**Reads:**
- `cto-os-data/modules/managing-up/state/people/{person-slug}.md` (the target's profile)
- Relevant source material via `scan` (user points at what)
- `cto-os-data/modules/personal-os/state/voice/` (optional — tone)

**Writes:** — (produces output for the user to review and copy; user decides whether to capture it)

### `add-upward-stakeholder`

**Purpose:** Add a new upward stakeholder post-activation — new boss, new skip-level, interim exec.

**Triggers:**
- "new boss: [name]"
- "add [person] as a skip-level"
- "[person] is my dotted-line manager now"

**Reads:** `cto-os-data/modules/managing-up/state/people/` (check slug collision).

**Writes:** `cto-os-data/modules/managing-up/state/people/{person-slug}.md`, append-new-file.

## Persistence

- **`cto-os-data/modules/managing-up/state/people/{person-slug}.md`** — one file per upward stakeholder, overwrite-with-history. Frontmatter: `type: stakeholder-profile, slug: <person-slug>, updated: <date>, name: <string>, role: <string>, relationship: <direct-manager|skip-level|dotted-line|other>, cadence: <string>, agenda_owner: <self|them|shared>, communication_preferences: <string>, what_they_want_first: <string>, typical_concerns: <list>, context_needs: <string>, known_sensitivities: <list>, relationship_status: <string>`. All profile fields optional. Body: free-form notes on the relationship + `## History` with dated profile snapshots when fields change.
- **`cto-os-data/modules/managing-up/state/1on1s/{person-slug}/{YYYY-MM-DD}.md`** — append-new-file per 1:1. Frontmatter: `type: boss-1on1, slug: <person-slug>-<YYYY-MM-DD>, updated: <date>, person: <person-slug>`. Body sections: `## Topics`, `## Decisions`, `## Follow-ups`, `## Signals` (perception / mood / concerns noticed).

**Overrides to the cross-cutting save rule** ([Persistence model](../../docs/ARCHITECTURE.md#persistence-model)): 1:1 captures happen without blocking when the user narrates a 1:1 that just ended. Profile updates confirm when the inference is indirect ("my boss seemed annoyed" — ask whether to capture as a profile update or just note in today's 1:1 body).

**Sensitivity:** `sensitivity: high` at module level. Notes about upward stakeholders are often candid (your real assessment of your boss, org frustrations, confidential information shared in 1:1s). Scan excludes this module's state by default; callers opt in explicitly.

## State location

`cto-os-data/modules/managing-up/state/`
