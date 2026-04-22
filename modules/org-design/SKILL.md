---
name: org-design
description: "Activates for optimizing how the engineering department is organized to deliver value — reorg proposals, team-structure changes, capacity re-allocation, bottleneck remediation. Uses the value-flow lens from Process Management and the team-topology lens from Team Topologies. Covers: authoring reorg proposals with diagnosis + proposed structure + tradeoffs + rollout plan; logging structural decisions that have been made; diagnosing specific org bottlenecks through Reinertsen + Conway's Law; assembling current-state org snapshots. Also activates on oblique phrasings like 'draft a reorg proposal,' 'we have a bottleneck at the integration layer,' 'reallocate capacity from product to platform,' 'we're going stream-aligned,' 'design review for the new platform team,' 'should we merge platform and infra-ops.' Does NOT activate on day-to-day team health tracking (Team Management owns current reality; this module changes it); hiring pipeline execution (Hiring); individual performance (Performance & Development); or flow measurement and process improvement within existing structures (Process Management — though this module consumes its output)."
requires:
  - process-management
  - business-alignment
optional:
  - team-management
  - hiring
  - budget
---

# Org Design

## Scope

Optimizing how the engineering department is organized to deliver value. Uses the value-flow lens (from Process Management / Reinertsen) and the team-topology lens (from Team Topologies) to decide team structure, capacity allocation, and bottleneck fixes. Low-frequency, high-leverage — most of the time no active proposals are in flight. Strategic and periodic module.

## Out of scope

- **Day-to-day team health tracking** — Team Management owns the current-state record; this module owns the *change* artifact.
- **Hiring pipeline execution** — Hiring. This module may *recommend* hiring moves as part of a proposal; Hiring executes.
- **Individual performance** — Performance & Development.
- **Flow measurement and process improvement inside existing structures** — Process Management (which this module consumes heavily as input).
- **Actual implementation of approved reorgs** — that lives in Managing Down (team comms), Org Comms (announcements), Team Management (updated team records), and Hiring (new reqs). This module records the decision; downstream modules enact it.

## Frameworks

- [Matthew Skelton & Manuel Pais — *Team Topologies*](https://teamtopologies.com/) — four team types (stream-aligned, enabling, complicated-subsystem, platform), interaction modes (collaboration, X-as-a-Service, facilitating), and cognitive-load framing.
  - *How this module applies it:* every proposal uses Team Topologies vocabulary — current team types, proposed team types, interaction-mode changes. The reverse Conway maneuver (design team boundaries to match the software architecture you want) is a standard move that proposals should name when invoked. Cognitive load is the diagnostic for "this team's scope is too big" — make it explicit.

- [Melvin Conway — Conway's Law](https://en.wikipedia.org/wiki/Conway%27s_law) — "Organizations which design systems are constrained to produce designs which are copies of the communication structures of these organizations."
  - *How this module applies it:* Conway's Law is the diagnostic frame for "the architecture we have is shaped by the org we have." Bottleneck analysis asks: is this a technical bottleneck or is it an org-boundary bottleneck that presents as a technical one? The reverse Conway maneuver (change the org to change the resulting architecture) is the first-class intervention.

- Value-flow lens — drawn from [Reinertsen's *Flow*](https://www.amazon.com/Principles-Product-Development-Flow-Generation/dp/1935401009) via the required dependency on Process Management.
  - *How this module applies it:* the test for any proposed structural change is "does this improve value flow?" If yes, what flow metric and by how much? Proposals that don't move flow (cycle time, lead time, WIP, throughput) are presumed to be political, cosmetic, or a solution looking for a problem — the proposal should defend them explicitly. Read current flow state from Process Management before diagnosing.

## Triggers

- "draft a reorg proposal" / "write up the [X] reorg"
- "update the [proposal-slug] proposal"
- "log the decision: we're merging platform and infra-ops"
- "we have a bottleneck at the integration layer — analyze it"
- "show me the current org snapshot" / "current-state org view"
- "update design principles" / "revise our org-design principles"
- Oblique: "should we go stream-aligned"
- Oblique: "the architecture is stuck because the teams are wrong"
- Oblique: "we need to reallocate capacity"

## Activation flow

Each step writes a concrete artifact and appends its step number to `activation_completed` in `_module.md`.

### 1. Capture current org-structure baseline

**Ask:** "Walk me through the current engineering org. If Team Management is active, I can pull the team list directly and ask you to confirm the reporting lines. If not, enumerate: for each team, lead, mission, size, topology type (stream-aligned / enabling / complicated-subsystem / platform), and who they report to. Then the layer above — which directors/VPs own which teams — up through the user."
**Writes:** This step *reads* from Team Management when available and produces a baseline snapshot as the first `design-proposal`-type document with `proposal_type: snapshot`, `status: implemented` (it represents the current reality). If Team Management isn't active, the step captures enough team data in this file to proceed, and advises the user to activate Team Management later for the canonical team record.
**Expects:** `cto-os-data/modules/org-design/state/proposals/{YYYY-MM-DD}-current-state-snapshot.md` exists with the org structure captured.

### 2. Declare design principles

**Ask:** "What properties do you want your org to have — i.e., the principles you'll use to evaluate any structural proposal? Examples: 'optimize for flow over resource utilization,' 'keep teams ≤ 8 people,' 'product teams own production operations for their services,' 'platform teams serve other teams, don't gate them,' 'every team has a clear primary user.' Capture 4–8 principles that are specific enough to disagree with."
**Writes:** `cto-os-data/modules/org-design/state/design-principles.md` with `type: design-principles`, `slug: current`, `principles` list.
**Expects:** frontmatter `principles` has ≥ 3 entries.

## Skills

### `draft-design-proposal`

**Purpose:** Compose a new reorg / org-design proposal. Pulls current state from Team Management and flow metrics from Process Management; uses Team Topologies + Conway's Law framing; references the declared design principles.

**Triggers:**
- "draft a reorg proposal"
- "write up the [X] reorg"
- "propose merging [team-A] and [team-B]"

**Reads:**
- `cto-os-data/modules/org-design/state/design-principles.md`
- `cto-os-data/modules/team-management/state/teams/` (optional — current teams)
- `cto-os-data/modules/process-management/state/flows/` (optional — current flow state)
- `cto-os-data/modules/business-alignment/state/company-goals/` (strategic framing)
- `cto-os-data/modules/hiring/state/workforce-plan.md` (optional — feasibility)
- `cto-os-data/modules/budget/state/` (optional — cost of proposed changes)
- `cto-os-data/modules/org-design/state/proposals/` (prior proposals for context, superseded state)

**Writes:** `cto-os-data/modules/org-design/state/proposals/{YYYY-MM-DD}-{proposal-slug}.md`, append-new-file with `status: draft`.

### `update-design-proposal`

**Purpose:** Revise a draft proposal — new options, updated tradeoffs, incorporated feedback, status transitions (draft → review → approved → implemented, or draft → rejected).

**Triggers:**
- "update the [proposal-slug] proposal"
- "we got feedback on [proposal] — revise"
- "move the [proposal] to approved"

**Reads:** `cto-os-data/modules/org-design/state/proposals/{proposal-slug}.md`.

**Writes:** `cto-os-data/modules/org-design/state/proposals/{proposal-slug}.md`, overwrite-with-history.

### `log-design-decision`

**Purpose:** Capture a structural decision that's been made — either from an approved proposal or a lightweight decision that didn't warrant a full proposal. Distinct from `update-design-proposal` because a decision can originate outside the proposal flow (e.g., reactive move to break a bottleneck).

**Triggers:**
- "log the decision: we're [structural move]"
- "capture that we merged [team-A] into [team-B]"
- "record the decision to spin up [new team]"

**Reads:**
- `cto-os-data/modules/org-design/state/proposals/` (link to proposal if one exists)
- `cto-os-data/modules/org-design/state/design-principles.md` (which principles this decision lands against)

**Writes:** `cto-os-data/modules/org-design/state/decisions/{YYYY-MM-DD}-{decision-slug}.md`, append-new-file.

### `analyze-bottleneck`

**Purpose:** Diagnose a specific org bottleneck through the combined Reinertsen + Conway's Law lens. Is this a flow issue (queue / batch / WIP / variability / cadence) that happens to involve an org boundary, or is it a Conway problem (the architecture is shaped by a team structure that's wrong)? Produces a written analysis that feeds a proposal or decision.

**Triggers:**
- "we have a bottleneck at [X] — analyze"
- "diagnose the integration-layer bottleneck"
- "why is [flow] stuck — is it Conway or is it the process"

**Reads:**
- `cto-os-data/modules/process-management/state/flows/` (flow metrics, existing bottleneck records)
- `cto-os-data/modules/process-management/state/bottlenecks/` (existing bottleneck observations)
- `cto-os-data/modules/team-management/state/teams/` (team structure at the bottleneck point)

**Writes:** `cto-os-data/modules/org-design/state/bottleneck-analyses/{YYYY-MM-DD}-{bottleneck-slug}.md`, append-new-file.

### `show-org-snapshot`

**Purpose:** Assemble a read-time view of the current org structure across teams, topology types, reporting lines, and headcount distribution. Pulls from Team Management as the canonical source.

**Triggers:**
- "show org snapshot"
- "current-state org view"
- "give me the org rollup"

**Reads:** `scan(type=["team"], where={"active": true}, fields=["slug", "lead", "mission", "size", "topology", "retro_cadence"])`.

**Writes:** —

### `update-design-principles`

**Purpose:** Revise the declared design principles.

**Triggers:**
- "update design principles"
- "add a principle: [X]"
- "we're no longer committed to [principle]"

**Reads:** `cto-os-data/modules/org-design/state/design-principles.md`.

**Writes:** `cto-os-data/modules/org-design/state/design-principles.md`, overwrite-with-history.

## Persistence

- **`cto-os-data/modules/org-design/state/design-principles.md`** — singleton (`slug: current`), overwrite-with-history. Frontmatter: `type: design-principles, slug: current, updated: <date>, principles: <list>`. Body: rationale per principle + `## History`.
- **`cto-os-data/modules/org-design/state/proposals/{YYYY-MM-DD}-{proposal-slug}.md`** — one file per proposal, overwrite-with-history (status transitions in body under `## History`). Frontmatter: `type: design-proposal, slug: <YYYY-MM-DD>-<proposal-slug>, updated: <date>, proposal_type: <reorg|new-team|merge|split|snapshot>, status: <draft|review|approved|implemented|rejected|superseded>, proposed_date: <date>, decided_date: <date, optional>, supersedes: <proposal-slug, optional>, superseded_by: <proposal-slug, optional>`. Body sections: `## Diagnosis`, `## Proposed structure`, `## Tradeoffs`, `## Rollout plan`, `## Principles invoked`.
- **`cto-os-data/modules/org-design/state/decisions/{YYYY-MM-DD}-{decision-slug}.md`** — append-new-file per logged decision. Frontmatter: `type: design-decision, slug: <YYYY-MM-DD>-<decision-slug>, updated: <date>, decision_summary: <string>, linked_proposal: <proposal-slug, optional>`. Body: context, decision, rationale, review-date, principles invoked.
- **`cto-os-data/modules/org-design/state/bottleneck-analyses/{YYYY-MM-DD}-{bottleneck-slug}.md`** — append-new-file per analysis. Frontmatter: `type: bottleneck-analysis, slug: <YYYY-MM-DD>-<bottleneck-slug>, updated: <date>, bottleneck_reference: <bottleneck-slug from process-management, optional>, diagnosis_lens: <reinertsen|conway|both>`. Body sections: `## Symptoms`, `## Reinertsen view`, `## Conway view`, `## Recommended intervention`.

**Overrides to the cross-cutting save rule** ([Persistence model](../../docs/ARCHITECTURE.md#persistence-model)): proposals save as `draft` on first write; user confirms each status transition (draft → review → approved → implemented). `log-design-decision` asks for confirmation before writing — decisions are durable artifacts that shouldn't accrete casually.

**Sensitivity:** standard default at module level. Proposals touching exec-level personnel moves or pre-announcement reorg plans can be flagged `sensitivity: high` per-file.

## State location

`cto-os-data/modules/org-design/state/`
