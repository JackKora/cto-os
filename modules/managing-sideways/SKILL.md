---
name: managing-sideways
description: "Activates for building and maintaining lateral relationships with peers — cross-functional leaders the user works with but doesn't have reporting authority over (CPO, VP Sales, VP Marketing, Head of Ops, Legal, Finance, etc.). Covers 1:1 preparation and capture, observable peer profiles, currency-of-exchange context, coalition building, stalled asks, relationship friction, and post-negotiation relationship signals. Also activates on oblique phrasings like 'prep for my 1:1 with [CPO],' 'I need something from [peer team] but they keep deprioritizing,' 'help me build the coalition for [X],' or 'how do I get [peer] on board with [Y].' Does NOT activate for substantive negotiation strategy or BATNA/walk-away preparation (Negotiation); direct reports (Managing Down); upward relationships (Managing Up); external peer CTOs and industry peers (External Network & Thought Leadership); or board-level stakeholders (Board Comms)."
requires: []
optional:
  - personal-os
  - business-alignment
  - attention-operations
  - negotiation
---

# Managing Sideways

## Scope

Building and maintaining the lateral relationships that make cross-functional work possible. Peers in the user's organization — fellow executives and leaders across functions (CPO, VP Sales, VP Marketing, Head of Ops, Legal, Finance, General Counsel, and so on) where the user has to get things done without reporting authority. Tracks observable peer profiles, 1:1 cadence, currency-of-exchange context, coalitions, stalled asks, relationship friction, and relationship signals after a negotiation concludes.

## Out of scope

- **Direct reports** — Managing Down.
- **Upward relationships** — Managing Up.
- **External peer CTOs, advisors, industry peers** — External Network & Thought Leadership.
- **Board-level stakeholders** — Board Comms.
- **Large-audience internal communication** — Org Comms.
- **Substantive negotiation strategy** — Negotiation owns the Seven Elements preparation, BATNA and reservation boundaries, offer packages, sequencing, round debriefs, and negotiation-specific lessons. Managing Sideways supplies peer context and receives post-negotiation relationship signals.

## Frameworks

- [Allan Cohen & David Bradford — *Influence Without Authority*](https://www.amazon.com/Influence-Without-Authority-Allan-Cohen/dp/0471463302) — currency-of-exchange model: identify what your peer values and what you can trade.
  - *How this module applies it:* peer profiles capture observable evidence about what currencies the peer values — hitting their numbers, political capital, reputation for delivery, protecting their team's focus, or career visibility. Use those currencies for ordinary influence, reciprocal support, and coalition design without inventing motives or treating relationships as purely transactional. When the interaction becomes a substantive negotiation, pass this context to Negotiation rather than extending the framework into BATNA or deal strategy here.

## Triggers

- "prep for my 1:1 with [peer]"
- "log my 1:1 with [peer]"
- "update [peer]'s profile"
- "add [person] as a peer" (new hire at peer level, new reorg putting someone adjacent)
- "[peer] is leaving" / "remove [peer]"
- "help me build the coalition for [initiative]"
- "[peer] is blocking [thing]" / "[peer] keeps deprioritizing [ask]"
- "how do I get [peer] on board with [Y]"
- "capture how the relationship changed after the negotiation"
- Oblique: "I'm frustrated with [peer]"
- Oblique: "I need something from [team] but it's not moving"

## Activation flow

Each step writes a concrete artifact and appends its step number to `activation_completed` in `_module.md`.

### 1. Enumerate key peers

**Ask:** "Who are the peers you work with most? Fellow leaders across functions — your CPO, VPs of Sales / Marketing / Ops / Product / Data, Legal, Finance, Head of People, and so on. Focus on the ones where cross-functional work is regular enough to matter. For each: name, function/title, short slug (kebab-case), and a one-line note on what you work on together."
**Writes:** one file per peer at `cto-os-data/modules/managing-sideways/state/people/{person-slug}.md` with `type: stakeholder-profile`, `slug: <person-slug>`, `name`, `role`, `function`, `relationship: peer`, `collaboration_area: <string>`.
**Expects:** at least one peer file exists with all five fields.

### 2. Baseline profile per peer

**Ask:** "For each peer, what do you already know about them — observable only, no inference? (a) communication preferences (channel, cadence, format); (b) what they want first (numbers / stories / risks / options); (c) typical concerns they push on; (d) how much context they want before an ask; (e) known sensitivities and past heated topics; (f) relationship status (trust level, open threads); (g) what currencies they value (from Cohen & Bradford — what do they care about getting). Skip fields you don't have a grounded answer for."
**Writes:** updates each peer file's frontmatter with the seven profile fields (profile standard six + `currencies`).
**Expects:** each peer file has at least `communication_preferences` and `what_they_want_first` set.

### 3. Set 1:1 cadence per peer

**Ask:** "What's the cadence with each peer? Weekly for your closest collaborator (often CPO for a CTO); bi-weekly to monthly for most; ad-hoc / quarterly for peripheral peers. For each: cadence + whether it's a scheduled 1:1 or opportunistic."
**Writes:** updates each peer file with `cadence` and `meeting_style` (scheduled | opportunistic) in frontmatter.
**Expects:** each peer file has `cadence` set.

## Skills

### `log-1on1-sideways`

**Purpose:** Capture a 1:1 with a peer. Topics, decisions, follow-ups, and signals such as currency movements, relationship-state changes, emerging friction, or post-negotiation trust effects.

**Triggers:**
- "log my 1:1 with [peer]"
- "just wrapped with [peer] — here's what happened"

**Reads:**
- `cto-os-data/modules/managing-sideways/state/people/{person-slug}.md`
- `cto-os-data/modules/managing-sideways/state/1on1s/{person-slug}/` (recent)
- `cto-os-data/modules/negotiation/state/negotiations/{negotiation-slug}.md` or its linked round only when the user explicitly asks to capture the negotiation's relationship effect; do not copy BATNA, reservation, leverage, or offer details into peer state

**Writes:** `cto-os-data/modules/managing-sideways/state/1on1s/{person-slug}/{YYYY-MM-DD}.md`, append-new-file.

### `prep-1on1-sideways`

**Purpose:** Prepare for an upcoming peer 1:1 or cross-functional meeting. Pulls recent notes, stalled asks, profile context, and shared-goal framing from Business Alignment. If the agenda is a substantive negotiation, route that portion to Negotiation.

**Triggers:**
- "prep for my 1:1 with [peer]"
- "what should I bring to tomorrow's 1:1 with [peer]"

**Reads:**
- `cto-os-data/modules/managing-sideways/state/people/{person-slug}.md`
- `cto-os-data/modules/managing-sideways/state/1on1s/{person-slug}/` (last 3)
- `cto-os-data/modules/business-alignment/state/work-mapping.md` (optional — shared goals)
- `cto-os-data/modules/personal-os/state/show-up.md` (optional — framing)

**Writes:** — (prep notes; follow-ups captured via `log-1on1-sideways`)

### `update-profile-sideways`

**Purpose:** Refine a peer's profile based on new observations, particularly currency shifts (what they care about moves with their strategic focus, incentives, or role).

**Triggers:**
- "update [peer]'s profile"
- "[peer] now cares about [X]"
- "[peer]'s currency has shifted"

**Reads:** `cto-os-data/modules/managing-sideways/state/people/{person-slug}.md`.

**Writes:** `cto-os-data/modules/managing-sideways/state/people/{person-slug}.md`, overwrite-with-history.

### `build-coalition`

**Purpose:** Map the peers whose support, neutrality, or input matters to a cross-functional initiative and plan relationship-aware alignment using observable currencies and shared goals. If the plan requires concessions, a reservation boundary, and a walk-away choice, route it to Negotiation.

**Triggers:**
- "help me build the coalition for [initiative]"
- "who needs to be aligned before I propose this"
- "map supporters and blockers for [initiative]"

**Reads:**
- relevant files in `cto-os-data/modules/managing-sideways/state/people/` (currencies, collaboration areas, relationship state)
- recent 1:1 notes for the peers involved
- `cto-os-data/modules/business-alignment/state/company-goals/` (optional — shared-goal framing)

**Writes:** — (produces an alignment plan; relationship changes and follow-ups are captured through the relevant peer profile or 1:1 record)

### `add-peer`

**Purpose:** Add a new peer post-activation — new hire at peer level, reorg, reporting-line change that puts someone adjacent.

**Triggers:**
- "add [person] as a peer"
- "new CPO: [name]"
- "[person] is now VP of [function]"

**Reads:** `cto-os-data/modules/managing-sideways/state/people/` (slug collision).

**Writes:** `cto-os-data/modules/managing-sideways/state/people/{person-slug}.md`, append-new-file.

### `remove-peer`

**Purpose:** Handle a peer moving out — role change, departure, reorg. Marks the profile inactive; file and history preserved.

**Triggers:**
- "[peer] is leaving"
- "[peer] moved to a different role"
- "remove [peer]"

**Reads:** `cto-os-data/modules/managing-sideways/state/people/{person-slug}.md`.

**Writes:** `cto-os-data/modules/managing-sideways/state/people/{person-slug}.md` — sets `active: false`, `departed_date`, reason in body.

## Persistence

- **`cto-os-data/modules/managing-sideways/_module.md`** — singleton module activation record, overwrite-in-place. Uses the baseline `_module` schema. Activation appends verified step numbers to `activation_completed`; only the final step sets `active: true`, `schema_version: 1`, `activated_at`, and `deactivated_at: null`.
- **`cto-os-data/modules/managing-sideways/state/people/{person-slug}.md`** — one file per peer, overwrite-with-history. Frontmatter: `type: stakeholder-profile, slug: <person-slug>, updated: <date>, active: <bool>, name: <string>, role: <string>, function: <string>, relationship: peer, collaboration_area: <string>, departed_date: <date, optional>, cadence: <string>, meeting_style: <scheduled|opportunistic>, communication_preferences: <string>, what_they_want_first: <string>, typical_concerns: <list>, context_needs: <string>, known_sensitivities: <list>, relationship_status: <string>, currencies: <list>`. All profile fields optional except `name`, `role`, `function`, `relationship`. Body: relationship notes + `## History`.
- **`cto-os-data/modules/managing-sideways/state/1on1s/{person-slug}/{YYYY-MM-DD}.md`** — append-new-file per 1:1. Frontmatter: `type: peer-1on1, slug: <person-slug>-<YYYY-MM-DD>, updated: <date>, person: <person-slug>`. Body sections: `## Topics`, `## Decisions`, `## Follow-ups`, `## Signals` (relationship state, currency movements, emerging friction or alignment).

**Overrides to the cross-cutting save rule** ([Persistence model](../../docs/ARCHITECTURE.md#persistence-model)): none — inherits the default. Peer notes are less sensitive by default than Managing Up/Down, but individual 1:1 files can be flagged `sensitivity: high` inline when the content warrants, such as candid peer-on-peer criticism or a post-negotiation trust signal. Negotiation strategy remains in the high-sensitivity Negotiation module rather than being copied here.

## State location

`cto-os-data/modules/managing-sideways/state/`
