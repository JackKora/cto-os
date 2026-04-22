---
name: business-alignment
description: "Activates for company-level goal tracking, customer signal capture, CTO customer engagement, and work-to-goals alignment. Covers: setting and updating company goals (annual and quarterly), logging customer signal inbound from sales/marketing/support/onboarding, logging CTO-level customer interactions (advisory boards, sales calls, exec sponsor relationships, customer escalations, industry events), and mapping current engineering initiatives to company goals. Also activates on oblique phrasings like 'how does this ladder up,' 'a customer just told me X,' 'sales keeps hearing,' 'board asked about our goals,' 'are we working on the right things.' Does NOT activate on personal goals (Personal OS), board or internal communication output (Board Comms, Org Comms), team-level goals (Team Management), or individual performance (Performance & Development)."
requires: []
optional: []
---

# Business Alignment

## Scope

The connection between what your organization does and what the business needs. Tracks company goals, pulls external signal from customer-facing teams (sales, marketing, support, onboarding), captures CTO-level customer engagements outbound, and makes work-to-goals ties visible across the engineering org. Foundational — no outbound dependencies.

## Out of scope

- **Board-level strategic communication** — Board Comms consumes this module's data to build its narrative.
- **Internal comms reporting on goals progress** — Org Comms consumes this module's data to build its update cadence.
- **Personal goals and cascade** — Personal OS.
- **Team-level goals** — Team Management.
- **Individual performance tracking** — Performance & Development.

## Frameworks

- [Colin Bryar & Bill Carr — *Working Backwards*](https://www.amazon.com/Working-Backwards-Insights-Stories-Secrets/dp/1250267595) — Amazon's customer-backwards discipline: start with the customer and work back to the work.
  - *How this module applies it:* for company goals, the press-release-first technique applies when a goal is fuzzy — write what it would look like for the customer when this goal is achieved, then derive measurable outputs. For customer signal capture, prefer "the job the customer was hiring us to do that we didn't serve well" over generic "here's what they said." Inputs are what we control (discovery calls, advisory board frequency); outputs are what the goal moves (retention, expansion, NPS). Track both; use inputs to diagnose when outputs lag.

- [Clayton Christensen — Jobs to be Done](https://hbr.org/2016/09/know-your-customers-jobs-to-be-done) — the "job" a customer is hiring your product to do.
  - *How this module applies it:* every customer signal gets tagged with the job-to-be-done the customer was trying to accomplish. Rolls up across many signals — repeated missed jobs become product insights that ladder up to company-goal changes. For work-to-goals mapping, ask: "which jobs does this initiative serve, and are those the jobs our current goals prioritize?" Misalignment there is the first thing to surface.

## Triggers

- "set company goals" / "update our annual/quarterly goals"
- "capture customer feedback" / "log customer signal"
- "I had a customer call" / "advisory board" / "sales call with [customer]"
- "how does [initiative] ladder up" / "work-to-goals heatmap"
- "show me our current customer-engagement cadence"
- "update the work-mapping"
- Oblique: "sales keeps hearing..." / "support's been flagging..."
- Oblique: "are we working on the right things" (if framed against company goals; personal-priority framing routes to Personal OS)

## Activation flow

Each step writes a concrete artifact and appends its step number to `activation_completed` in `_module.md`.

### 1. Capture current company goals

**Ask:** "What are the company's current goals? Start with the top 3–5 annual. If you're mid-year, also capture this quarter's goals as a separate list. These are the company's goals — if you're a CTO of a small company you may know them verbatim; if you're in a larger org, use what's been communicated from the CEO/exec team."
**Writes:** `cto-os-data/modules/business-alignment/state/company-goals/annual.md` with `type: company-goal-horizon`, `slug: annual`, `horizon: annual`, `period` set to current year, `items` populated. If mid-year or later, also `cto-os-data/modules/business-alignment/state/company-goals/quarterly.md` with `horizon: quarterly`.
**Expects:** annual file exists with `items` ≥ 3 entries and `period` matching current year.

### 2. Declare external-signal sources

**Ask:** "Which customer-facing teams or channels should I watch for signal? Sales, marketing, support, onboarding, customer success — any, all, or subsets. For each, what's the scope (specific channels, specific people, specific reporting surfaces)? This tells me where to listen when you say 'capture customer signal' and which cached data to prioritize."
**Writes:** `cto-os-data/modules/business-alignment/state/signal-sources.md` with `type: signal-sources`, `slug: current`, `sources` list.
**Expects:** frontmatter `sources` has ≥ 1 entry with `source_type`, `identifier`, and `scope`.

### 3. Declare CTO customer-engagement cadence

**Ask:** "What's your engagement cadence with customers at the CTO level? For each type — advisory board, direct sales calls, exec sponsor 1:1s, customer escalations, industry events — how often does it happen, and how often *should* it? A CTO at a fast-growth B2B SaaS might do 2 sales calls a week; an SVP at a large enterprise might do quarterly advisory boards only. Whatever yours is, capture it."
**Writes:** `cto-os-data/modules/business-alignment/state/engagement-cadence.md` with `type: engagement-cadence`, `slug: current`, `cadences` list.
**Expects:** frontmatter `cadences` has ≥ 1 entry with `engagement_type` and `target_frequency`.

### 4. Baseline work-to-goals mapping

**Ask:** "What are the top 5–10 engineering initiatives in flight right now? For each, which company goal does it ladder up to, and how confident are you in that tie? Mark anything low-confidence — we'll surface those when reviewing whether we're working on the right things."
**Writes:** `cto-os-data/modules/business-alignment/state/work-mapping.md` with `type: work-mapping`, `slug: current`, `mappings` list.
**Expects:** frontmatter `mappings` has ≥ 3 entries with `initiative`, `goal`, `confidence` (one of low/medium/high).

## Skills

### `set-company-goals`

**Purpose:** Update company goals at a specific horizon (annual or quarterly). Preserves prior versions as history in the target file's body.

**Triggers:**
- "update company goals"
- "set quarterly priorities"
- "new year — reset the annual goals"

**Reads:**
- `cto-os-data/modules/business-alignment/state/company-goals/{horizon}.md` (current items)

**Writes:** `cto-os-data/modules/business-alignment/state/company-goals/{horizon}.md`, overwrite-with-history.

### `log-customer-signal`

**Purpose:** Capture a piece of external signal from a customer-facing team or direct customer interaction. Tags with the job-to-be-done when identifiable.

**Triggers:**
- "capture customer signal"
- "support just flagged..."
- "sales told me..."
- "customer said..."

**Reads:**
- `cto-os-data/modules/business-alignment/state/signal-sources.md` (validate source)
- `cto-os-data/modules/business-alignment/state/company-goals/` (framing: does this signal touch a current goal?)

**Writes:** `cto-os-data/modules/business-alignment/state/signals/{YYYY-MM-DD}-{source-slug}.md`, append-new-file per signal event.

### `log-customer-engagement`

**Purpose:** Capture a CTO-level customer engagement event — advisory board, sales call, exec sponsor 1:1, escalation, industry event.

**Triggers:**
- "log a customer call"
- "advisory board just ended"
- "exec sponsor 1:1 with [customer]"
- "handle a customer escalation"

**Reads:**
- `cto-os-data/modules/business-alignment/state/engagement-cadence.md` (what type is this, does it fit cadence)
- Personal OS (optional) — `cto-os-data/modules/personal-os/state/voice/` to match writing tone for follow-ups

**Writes:** `cto-os-data/modules/business-alignment/state/engagements/{YYYY-MM-DD}-{customer-slug}.md`, append-new-file per engagement.

### `show-work-to-goals`

**Purpose:** Assemble a current view of which engineering initiatives ladder to which company goals, including confidence in each tie and any goals with no work-against-them or initiatives with no goal-they-serve.

**Triggers:**
- "show work-to-goals"
- "which goals are we not working on"
- "are we aligned"
- "work-to-goals heatmap"

**Reads:**
- `cto-os-data/modules/business-alignment/state/company-goals/annual.md` and `quarterly.md`
- `cto-os-data/modules/business-alignment/state/work-mapping.md`

**Writes:** —

### `update-engagement-cadence`

**Purpose:** Revise declared CTO-customer engagement cadence.

**Triggers:**
- "change my customer engagement cadence"
- "I'm going to start doing more advisory boards"
- "step back on sales calls"

**Reads:** `cto-os-data/modules/business-alignment/state/engagement-cadence.md`.

**Writes:** `cto-os-data/modules/business-alignment/state/engagement-cadence.md`, overwrite-with-history.

### `update-work-mapping`

**Purpose:** Add, remove, or re-confidence entries in the work-to-goals mapping. Invoked when initiatives change scope, ship, or get killed.

**Triggers:**
- "update the work-mapping"
- "add [initiative] to work-mapping"
- "we killed [initiative]"
- "I'm less confident [initiative] serves [goal]"

**Reads:** `cto-os-data/modules/business-alignment/state/work-mapping.md`.

**Writes:** `cto-os-data/modules/business-alignment/state/work-mapping.md`, overwrite-with-history.

## Persistence

- **`cto-os-data/modules/business-alignment/state/company-goals/{annual|quarterly}.md`** — two files, one per horizon. Each overwrites independently, with prior versions preserved as reverse-chronological snapshots in its own body. Frontmatter: `type: company-goal-horizon, slug: <horizon>, updated: <date>, horizon: <annual|quarterly>, period: <string>, items: <list>, owner: <string, optional>`. Body: `## History` with dated snapshots.
- **`cto-os-data/modules/business-alignment/state/signal-sources.md`** — singleton (`slug: current`), overwrite-with-history. Frontmatter: `type: signal-sources, slug: current, updated: <date>, sources: <list of {source_type, identifier, scope}>`. Body: `## History`.
- **`cto-os-data/modules/business-alignment/state/signals/{YYYY-MM-DD}-{source-slug}.md`** — append-new-file per incoming signal. Frontmatter: `type: customer-signal, slug: <YYYY-MM-DD>-<source-slug>, updated: <date>, source: <string>, channel: <string>, job_to_be_done: <string, optional>, implication: <string>`. Body: the signal itself, verbatim or summarized.
- **`cto-os-data/modules/business-alignment/state/engagements/{YYYY-MM-DD}-{customer-slug}.md`** — append-new-file per engagement. Frontmatter: `type: customer-engagement, slug: <YYYY-MM-DD>-<customer-slug>, updated: <date>, engagement_type: <enum>, customer: <string>, outcomes: <list>`. Body: notes from the engagement.
- **`cto-os-data/modules/business-alignment/state/engagement-cadence.md`** — singleton (`slug: current`), overwrite-with-history. Frontmatter: `type: engagement-cadence, slug: current, updated: <date>, cadences: <list of {engagement_type, target_frequency}>`. Body: `## History`.
- **`cto-os-data/modules/business-alignment/state/work-mapping.md`** — singleton (`slug: current`), overwrite-with-history. Frontmatter: `type: work-mapping, slug: current, updated: <date>, mappings: <list of {initiative, goal, confidence}>`. Body: `## History`.

**Overrides to the cross-cutting save rule** ([Persistence model](../../docs/ARCHITECTURE.md#persistence-model)): none — inherits the default.

## State location

`cto-os-data/modules/business-alignment/state/`
