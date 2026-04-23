---
name: org-comms
description: "Activates for communicating to internal audiences at scale — the voice of leadership coming through recurring and ad-hoc updates. Covers: regular engineering updates (monthly/quarterly); all-hands content (eng section of company all-hands, or eng-specific all-hands); internal incident communications that pair with Tech Ops postmortems; cross-functional announcements (reorgs, policy changes, wins). Composes content by pulling from Team Management (team health), Business Alignment (goals progress), Process Management (flow metrics), and Tech Ops (reliability). Also activates on oblique phrasings like 'draft the monthly eng update,' 'write the eng section of all-hands,' 'write the incident comms for yesterday's outage,' 'announce the reorg to the eng org,' 'show me my comm calendar.' Does NOT activate on board-level communication (Board Comms); external thought leadership or public writing (External Network & Thought Leadership); team-specific comms to one team (Managing Down); or 1:1 comms with an individual (Managing Up / Down / Sideways)."
requires: []
optional:
  - personal-os
  - business-alignment
  - team-management
  - tech-ops
  - process-management
---

# Org Comms

## Scope

How the user communicates to internal audiences at scale — eng org, cross-functional peers, sometimes the whole company. Recurring cadences (monthly eng update, quarterly all-hands, etc.) plus ad-hoc announcements (reorgs, policy changes, wins, cross-functional launches). Composes content by pulling from other modules rather than holding original source material. Strategic and periodic — not daily work, but the quality of the output shapes leadership presence.

## Out of scope

- **Board-level communication** — Board Comms.
- **External audiences, public writing, thought leadership** — External Network & Thought Leadership.
- **Team-specific communication to one reporting team** — Managing Down (`draft-team-comms` skill).
- **1:1 or small-group communication** — Managing Up / Down / Sideways.
- **Drafting for other peoples' voices** — this module uses the user's voice (optional via Personal OS); peer-authored content is someone else's job.

## Frameworks

- [Amazon narrative format / 6-pager](https://www.amazon.com/Working-Backwards-Insights-Stories-Secrets/dp/1250267595) — prose over bullets; memo as argument structure.
  - *How this module applies it:* recurring updates and all-hands prose follow the narrative discipline — open with the answer, then context, then detail. Don't bullet-dump. For all-hands content that includes slides, slides exist to support the narrative, not replace it. Every draft starts with "what do I want the audience to know, decide, or feel" before any structure.

- [Barbara Minto — *The Pyramid Principle*](https://www.amazon.com/Pyramid-Principle-Logic-Writing-Thinking/dp/0273710516) — top-down reasoning; lead with the main point; structured argument hierarchy.
  - *How this module applies it:* every delivered comm has one pyramid top — the single thing the audience should remember. Supporting points ladder under it. Incident comms especially benefit from Minto discipline: the top is "what happened, who's affected, what we're doing"; detail lives below.

## Triggers

- "draft the monthly eng update"
- "write the eng section for next all-hands"
- "draft incident comms for [incident]"
- "announce the reorg to the eng org"
- "write a Slack post to #eng-all about [X]"
- "show me my comm calendar" / "what comms do I owe this month"
- "log the final comm I sent" (capture what went out, for voice consistency and longitudinal tracking)
- "update our comm surfaces" / "add #eng-announcements to surfaces"
- "update our comm cadences" / "change monthly update to bi-monthly"
- Oblique: "how did I frame [topic] last time I announced something similar"

## Activation flow

Each step writes a concrete artifact and appends its step number to `activation_completed` in `_module.md`.

### 1. Declare comm surfaces

**Ask:** "Walk me through the surfaces you communicate on. Slack channels (eng-announcements, all-hands, etc.), email lists, all-hands-slides repo, internal wiki spaces, anywhere else comms go. For each: name, audience scope (eng org / whole company / cross-functional subset), typical comm types that land there."
**Writes:** `cto-os-data/modules/org-comms/state/surfaces.md` with `type: comm-surfaces`, `slug: current`, `surfaces` list.
**Expects:** frontmatter `surfaces` has ≥ 1 entry with `name`, `audience_scope`, and `typical_comm_types`.

### 2. Declare recurring cadences

**Ask:** "What's your recurring comm cadence? Typical: monthly engineering update, quarterly all-hands section, maybe weekly leadership notes. For each cadence: name, frequency (weekly / monthly / quarterly), target surface(s), typical structure/length, when it's due relative to the period boundary. If you have no recurring cadence today, we can skip and add via `update-cadences` once you set one."
**Writes:** `cto-os-data/modules/org-comms/state/cadences.md` with `type: comm-cadences`, `slug: current`, `cadences` list.
**Expects:** `cadences` has 0+ entries. (Can be empty; users who communicate purely ad-hoc can proceed and add cadences later.)

## Skills

### `draft-recurring-update`

**Purpose:** Compose a recurring update (monthly eng, quarterly, etc.) by pulling from Team Management, Business Alignment, Process Management, and Tech Ops. Structures per the Amazon narrative format — lead with the "what should you take away," then context, then detail.

**Triggers:**
- "draft the monthly eng update"
- "write the [cadence] update"
- "time for the [period] update"

**Reads:**
- `cto-os-data/modules/org-comms/state/cadences.md` (which cadence, target structure)
- `cto-os-data/modules/org-comms/state/surfaces.md` (target surface format)
- `cto-os-data/modules/org-comms/state/delivered/` (recent updates for continuity, voice)
- `cto-os-data/modules/team-management/state/` (optional — team state)
- `cto-os-data/modules/business-alignment/state/company-goals/` + `work-mapping.md` (optional — goals progress)
- `cto-os-data/modules/process-management/state/flows/` (optional — flow KPIs if surfacing to audience)
- `cto-os-data/modules/tech-ops/state/incidents/`, `postmortems/` (optional — reliability narrative)
- `cto-os-data/modules/personal-os/state/voice/` (optional — tone)

**Writes:** `cto-os-data/modules/org-comms/state/delivered/{YYYY-MM-DD}-{comm-slug}.md` with `comm_type: recurring`, `status: draft`. User flips to `final` once sent.

### `draft-all-hands-content`

**Purpose:** Compose content for an upcoming all-hands — either the eng section of a company all-hands, or eng-specific all-hands material. Can produce narrative prose, slide-deck outline, or hybrid.

**Triggers:**
- "write the eng section for next all-hands"
- "all-hands content for [date]"
- "prep the eng all-hands"

**Reads:**
- `cto-os-data/modules/org-comms/state/surfaces.md`
- `cto-os-data/modules/org-comms/state/delivered/` (prior all-hands for continuity)
- Module state as above (team / goals / flows / reliability)
- `cto-os-data/modules/personal-os/state/voice/`, `show-up.md` (optional — tone and posture)

**Writes:** `cto-os-data/modules/org-comms/state/delivered/{YYYY-MM-DD}-{comm-slug}.md` with `comm_type: all-hands`, `status: draft`.

### `draft-incident-comms`

**Purpose:** Compose internal communications for an active or recently-resolved incident. Pairs with Tech Ops postmortems — the incident-comms are the *announcement*, the postmortem is the *learning document*. Minto discipline especially important here: top = what happened, who's affected, what we're doing.

**Triggers:**
- "draft incident comms for [incident]"
- "announcement for yesterday's outage"
- "internal update on the [incident] postmortem"

**Reads:**
- `cto-os-data/modules/tech-ops/state/incidents/{incident-slug}.md` (facts)
- `cto-os-data/modules/tech-ops/state/postmortems/{postmortem-slug}.md` (optional — if postmortem done)
- `cto-os-data/modules/org-comms/state/surfaces.md` (which channel, audience)
- `cto-os-data/modules/org-comms/state/delivered/` (prior incident comms for consistent framing)

**Writes:** `cto-os-data/modules/org-comms/state/delivered/{YYYY-MM-DD}-{comm-slug}.md` with `comm_type: incident`, `status: draft`.

### `draft-announcement`

**Purpose:** Ad-hoc cross-functional announcement — reorg, policy change, new hire at exec level, a win worth celebrating, a cross-functional launch.

**Triggers:**
- "announce the reorg to the eng org"
- "write the announcement for [event]"
- "draft a Slack post about [X]"

**Reads:**
- `cto-os-data/modules/org-comms/state/surfaces.md` (pick channel, format)
- `cto-os-data/modules/org-comms/state/delivered/` (voice consistency)
- Relevant source modules depending on the topic
- `cto-os-data/modules/personal-os/state/voice/`, `show-up.md` (optional)

**Writes:** `cto-os-data/modules/org-comms/state/delivered/{YYYY-MM-DD}-{comm-slug}.md` with `comm_type: announcement`, `status: draft`.

### `update-surfaces`

**Purpose:** Add / remove / revise comm surfaces. Invoked when a new channel stands up, an old one deprecates, or audience scope changes.

**Triggers:**
- "add [channel] to our comm surfaces"
- "we deprecated [surface]"
- "update surfaces"

**Reads:** `cto-os-data/modules/org-comms/state/surfaces.md`.

**Writes:** `cto-os-data/modules/org-comms/state/surfaces.md`, overwrite-with-history.

### `update-cadences`

**Purpose:** Add / remove / revise recurring cadences.

**Triggers:**
- "add a new cadence: [name]"
- "change monthly update to bi-monthly"
- "stop doing the weekly leadership note"

**Reads:** `cto-os-data/modules/org-comms/state/cadences.md`.

**Writes:** `cto-os-data/modules/org-comms/state/cadences.md`, overwrite-with-history.

### `show-comm-calendar`

**Purpose:** Assemble a read-time view of recurring cadences + what's due / upcoming based on current date. Useful when the user asks "what comms do I owe."

**Triggers:**
- "show my comm calendar"
- "what comms do I owe this month"
- "what's coming up"

**Reads:**
- `cto-os-data/modules/org-comms/state/cadences.md`
- `cto-os-data/modules/org-comms/state/delivered/` (what's been delivered in the current period)

**Writes:** —

## Persistence

- **`cto-os-data/modules/org-comms/state/surfaces.md`** — singleton (`slug: current`), overwrite-with-history. Frontmatter: `type: comm-surfaces, slug: current, updated: <date>, surfaces: <list of {name, audience_scope, typical_comm_types}>`. Body: notes + `## History`.
- **`cto-os-data/modules/org-comms/state/cadences.md`** — singleton (`slug: current`), overwrite-with-history. Frontmatter: `type: comm-cadences, slug: current, updated: <date>, cadences: <list of {name, frequency, target_surfaces, structure_notes, due_relative_to_period}>`. Body: rationale + `## History`.
- **`cto-os-data/modules/org-comms/state/delivered/{YYYY-MM-DD}-{comm-slug}.md`** — append-new-file per delivered comm. Frontmatter: `type: delivered-comm, slug: <YYYY-MM-DD>-<comm-slug>, updated: <date>, comm_type: <recurring|all-hands|incident|announcement>, status: <draft|final>, surfaces: <list>, audience_scope: <string>, topic: <string>, related_source: <string, optional>`. Body: the comm itself. Structure varies by `comm_type` — recurring/announcement tend toward Minto prose; all-hands can include slide outlines; incident comms follow the top-down "what happened / who's affected / what we're doing" pattern.

**Overrides to the cross-cutting save rule** ([Persistence model](../../docs/ARCHITECTURE.md#persistence-model)): drafts save as `status: draft` automatically; user confirms before flipping to `final`. `draft-incident-comms` runs without blocking during active incidents (speed matters) but saves with `status: draft` — confirmation on `final` even then, since incident comms are especially high-stakes.

**Sensitivity:** standard default at module level. Individual delivered comms touching sensitive topics (reorg announcement with exec-level moves, incident comms exposing security or data issues) can be flagged `sensitivity: high` per-file.

## State location

`cto-os-data/modules/org-comms/state/`
