---
name: process-management
description: "Activates for flow measurement, process retros, and bottleneck identification across the user's declared operating flows (PM, SDLC, Data Science, or custom). Covers: defining a flow and its measurement sources, measuring cycle time / lead time / WIP / throughput / batch size for a named flow, capturing bottleneck observations with Reinertsen-style classification (queue, batch size, WIP, variability, cadence), tracking bottleneck lifecycle (open → mitigated → resolved), and running flow retros. Also activates on oblique phrasings like 'cycle time looks off,' 'things are piling up,' 'flow feels slow,' 'WIP is growing,' 'why is SDLC so bogged down,' 'retro on last quarter's delivery.' Does NOT activate on specific project execution (owned by teams doing the work), reliability or incident response (Tech Ops), team-aggregate health (Team Management), or individual performance (Performance & Development)."
requires: []
optional: []
---

# Process Management

## Scope

How work moves through the organization from idea to customer. Owns measurement and continuous improvement of the operating flows — Product Management, SDLC, Data Science, or whatever else the user declares. Foundational — no outbound dependencies. Required by Org Design and Board Comms (they consume this module's metrics).

**v1 scope:** flow measurement + bottleneck tracking + flow retros. PM / SDLC / DS as *sub-flow modules* are deferred — in v1, each is a declarable flow the user adds to this module; if one accrues enough bespoke logic later, it can graduate into its own module.

## Out of scope

- **Specific project execution** — happens inside the flows; owned by the teams doing the work.
- **Reliability and incident response** — Tech Ops.
- **Team-aggregate health** — Team Management.
- **Individual performance** — Performance & Development.
- **Strategic team structure changes** — Org Design (which *depends on* this module's metrics but owns the structural decisions).

## Frameworks

- [Donald Reinertsen — *The Principles of Product Development Flow*](https://www.amazon.com/Principles-Product-Development-Flow-Generation/dp/1935401009) — explicitly cited in the PRD as the foundational framework.
  - *How this module applies it:* Reinertsen's eight principle categories — economics, queues, variability, batch size, WIP constraints, cadence, synchronization, fast feedback — are the diagnostic menu. Every bottleneck gets classified as one of {queue, batch-size, wip, variability, cadence, other} to force Reinertsen-style naming. Flow metrics tracked: cycle time, lead time, WIP, throughput. Little's Law (lead time = WIP ÷ throughput) is the identity — if two of three are measured, the third is derived. Don't force classification on every observation; use the framework for naming *what's wrong* when the user describes a flow symptom.

## Triggers

- "flow retro" / "process retro"
- "measure the SDLC flow" / "how's PM cycle time trending"
- "log a bottleneck" / "there's a bottleneck in..."
- "WIP is growing" / "cycle time looks off"
- "resolve the [X] bottleneck" / "we addressed the batch-size issue"
- "show me flow trends across all flows"
- Oblique: "things are piling up" / "everything feels slow" / "we're delivering slower than last quarter"

## Activation flow

Each step writes a concrete artifact and appends its step number to `activation_completed` in `_module.md`.

### 1. Declare flows to track

**Ask:** "Which flows do you want to track? Typical choices: SDLC (code → production), PM (discovery → shipped product), Data Science (question → insight). You can also define custom flows — e.g., 'design review pipeline' or 'customer-feedback intake.' For each, give it a short slug, a one-line description, and who owns it (which team or role)."
**Writes:** one file per flow at `cto-os-data/modules/process-management/state/flows/{flow-slug}.md` with `type: flow`, `slug: <flow-slug>`, `flow_type`, `owner`.
**Expects:** at least one flow file exists with frontmatter `flow_type` and `owner` set.

### 2. Declare measurement sources per flow

**Ask:** "For each flow you just defined, where does cycle/lead time measurement come from? Linear for SDLC, Jira or a PM tool for PM, a mix for DS. If no automated source, say so — we'll track manually via `log-flow-retro` instead."
**Writes:** updates each flow file with `sources` in frontmatter — a list of `{source_type, identifier, mode}` where mode is `automated` or `manual`.
**Expects:** each flow file's frontmatter has `sources` ≥ 1 entry.

### 3. Initial bottleneck inventory

**Ask:** "What's already broken? List bottlenecks you already know about — one per line, in the form '[flow]: [short description]'. We'll capture these as open bottlenecks so we can track whether they get resolved."
**Writes:** one file per bottleneck at `cto-os-data/modules/process-management/state/bottlenecks/{bottleneck-slug}.md` with `type: bottleneck`, `status: open`.
**Expects:** zero or more bottleneck files exist (can be empty — user may not know of any bottlenecks at activation).

## Skills

### `add-flow`

**Purpose:** Declare a new flow to track, post-activation. Creates a new flow file.

**Triggers:**
- "add a new flow: [name]"
- "start tracking our [X] flow"

**Reads:** `cto-os-data/modules/process-management/state/flows/` (check for slug collision).

**Writes:** `cto-os-data/modules/process-management/state/flows/{flow-slug}.md`, append-new-file.

### `update-flow`

**Purpose:** Change a flow's definition — new owner, new measurement sources, updated description, or revised current-metrics snapshot.

**Triggers:**
- "update the SDLC flow"
- "change [flow] owner to [team]"
- "[flow] cycle time just measured at X days"

**Reads:** `cto-os-data/modules/process-management/state/flows/{flow-slug}.md`.

**Writes:** `cto-os-data/modules/process-management/state/flows/{flow-slug}.md`, overwrite-with-history (prior definitions/measurements preserved in body under `## History`).

### `measure-flow`

**Purpose:** Compute or re-compute flow metrics for a named flow. Reads from integrations cache (Linear, GitHub, etc.) if automated, or prompts the user for values if manual. Writes the result into the flow's frontmatter.

**Triggers:**
- "measure SDLC cycle time"
- "measure [flow]"
- "re-measure all flows"

**Reads:**
- `cto-os-data/modules/process-management/state/flows/{flow-slug}.md` (definition + sources)
- `cto-os-data/integrations-cache/linear/`, `cto-os-data/integrations-cache/` (for automated measurement)

**Writes:** `cto-os-data/modules/process-management/state/flows/{flow-slug}.md` — updates `cycle_time_days`, `lead_time_days`, `wip`, `throughput_per_week`, `last_measured` in frontmatter, appends dated measurement snapshot to body history.

### `log-bottleneck`

**Purpose:** Capture a new bottleneck observation. Classifies per Reinertsen if possible.

**Triggers:**
- "log a bottleneck"
- "we have a batch-size problem in [flow]"
- "WIP is out of control in [flow]"

**Reads:**
- `cto-os-data/modules/process-management/state/flows/` (validate flow slug, get context)
- `cto-os-data/modules/process-management/state/bottlenecks/` (check for duplicates)

**Writes:** `cto-os-data/modules/process-management/state/bottlenecks/{bottleneck-slug}.md`, append-new-file with `status: open`.

### `resolve-bottleneck`

**Purpose:** Mark a bottleneck as `mitigated` (workaround in place) or `resolved` (fixed at the cause). Captures the resolution and any learnings.

**Triggers:**
- "resolve the [X] bottleneck"
- "we fixed [bottleneck]"
- "we have a workaround for [bottleneck] — mark it mitigated"

**Reads:** `cto-os-data/modules/process-management/state/bottlenecks/{bottleneck-slug}.md`.

**Writes:** `cto-os-data/modules/process-management/state/bottlenecks/{bottleneck-slug}.md`, update frontmatter (`status`, `resolved` date), append resolution notes to body.

### `log-flow-retro`

**Purpose:** Capture a retro on a specific flow. Structure: what went well in the flow, where flow was impeded, Reinertsen categories (queue / batch / WIP / variability / cadence) that showed up, what to try next.

**Triggers:**
- "flow retro on SDLC"
- "run a process retro on [flow]"
- "quarterly retro for PM flow"

**Reads:**
- `cto-os-data/modules/process-management/state/flows/{flow-slug}.md`
- `cto-os-data/modules/process-management/state/retros/{flow-slug}/` (recent retros for trend)

**Writes:** `cto-os-data/modules/process-management/state/retros/{flow-slug}/{YYYY-MM-DD}.md`, append-new-file.

### `show-flow-trends`

**Purpose:** Assemble a read-time view of current metrics across all flows, optionally with trend deltas from last measurement.

**Triggers:**
- "show flow trends"
- "how are our flows doing"
- "cross-flow dashboard"

**Reads:** `scan(type=["flow"], fields=["slug", "flow_type", "owner", "cycle_time_days", "lead_time_days", "wip", "throughput_per_week", "last_measured"])`.

**Writes:** —

## Persistence

- **`cto-os-data/modules/process-management/state/flows/{flow-slug}.md`** — one file per declared flow, overwrite-with-history. Frontmatter: `type: flow, slug: <flow-slug>, updated: <date>, flow_type: <pm|sdlc|ds|custom>, owner: <string>, sources: <list>, cycle_time_days: <number, optional>, lead_time_days: <number, optional>, wip: <number, optional>, throughput_per_week: <number, optional>, last_measured: <date, optional>`. Body: description + `## History` with dated measurement snapshots.
- **`cto-os-data/modules/process-management/state/retros/{flow-slug}/{YYYY-MM-DD}.md`** — append-new-file per retro. Frontmatter: `type: flow-retro, slug: <flow-slug>-<YYYY-MM-DD>, updated: <date>, flow: <flow-slug>, period: <string>`. Body: sections `## Went well`, `## Impeded flow`, `## Reinertsen categories`, `## To try next`.
- **`cto-os-data/modules/process-management/state/bottlenecks/{bottleneck-slug}.md`** — one file per bottleneck, overwrite-with-history (status transitions are history). Frontmatter: `type: bottleneck, slug: <bottleneck-slug>, updated: <date>, flow: <flow-slug>, status: <open|mitigated|resolved>, category: <queue|batch-size|wip|variability|cadence|other>, opened: <date>, resolved: <date, optional>`. Body: description + `## History` with dated transitions and notes.

**Overrides to the cross-cutting save rule** ([Persistence model](../../docs/ARCHITECTURE.md#persistence-model)): none — inherits the default.

## State location

`cto-os-data/modules/process-management/state/`
