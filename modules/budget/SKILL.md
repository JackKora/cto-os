---
name: budget
description: "Activates for financial stewardship of the engineering organization — budget planning, budget-to-actual tracking, forecasting, cost-allocation decisions, and compiling budget narratives for leadership or board reporting. Covers: declaring the budget category taxonomy (headcount, vendors/SaaS, cloud infra, tools, professional services, etc.); maintaining plan / actual / forecast amounts per category per period; running variance analyses; authoring budget narratives that explain spend decisions in Core-vs-Context terms. Also activates on oblique phrasings like 'forecast next quarter's eng spend,' 'vendor spend has drifted,' 'why are we over budget on [category],' 'compare capex vs opex for the GPU cluster,' 'draft the budget section of the board update.' Does NOT activate on the actual build-vs-buy architectural decisions (Technical Strategy owns those; this module provides cost context); workforce-level hiring plan (Hiring owns the plan; this module tracks the financial envelope); or non-engineering budget (out of scope)."
requires: []
optional:
  - hiring
  - tech-ops
  - business-alignment
  - technical-strategy
---

# Budget

## Scope

Financial stewardship of the engineering organization. Understanding where money goes, planning for the future, tracking actuals against plan. Headcount loaded cost, vendor and software spend, capex vs opex decisions, cost allocation across categories, budget-to-actual variance, forecast and planning. Role-shape module — essential for P&L-owning roles, optional for CTOs whose CFO or COO owns eng budget directly.

## Out of scope

- **Build-vs-buy decisions themselves** — Technical Strategy owns the architectural call; this module provides cost context via its reads.
- **Workforce plan** — Hiring owns the plan; this module tracks the financial envelope that plan operates within.
- **Non-engineering budget** — the module is scoped to engineering; broader company budgeting lives elsewhere.
- **Payroll execution** — out of scope; this module tracks *planned and actual* headcount-loaded cost at the aggregate, not individual compensation records (those are Hiring for candidates, HR systems for employees).
- **Invoice processing and vendor contract management** — assumed to live in a finance or procurement system; this module tracks aggregate spend per vendor or category, not per-invoice detail.

## Frameworks

- [Geoffrey Moore — Core vs Context](https://a16z.com/the-core-vs-context-model/) — two-axis model for deciding what to invest in vs. what to outsource or commoditize: (a) is this *core* (competitive differentiation, customer-facing) or *context* (necessary but not differentiating); (b) is this *mission-critical* (failure is catastrophic) or *non-mission-critical*.
  - *How this module applies it:* the lens for budget-narrative decisions. Core + mission-critical gets primary investment (hire, build, own). Context + mission-critical gets outsourced to best-in-class (pay for the SaaS). Context + non-mission-critical gets automated, deprioritized, or eliminated. When `draft-budget-narrative` composes a section for a board or exec update, it can frame category-level spend decisions against this model. Don't force every category into the matrix — use it where the spend choice is contested or underexplained.

Standard financial-planning concepts form the conceptual basis but aren't single-framework cited: capex vs opex (what gets depreciated vs expensed in-period); fully-loaded headcount cost (salary + benefits + equipment + space); unit economics (cost per customer, per request, per user); zero-based budgeting as a periodic reset discipline. These show up in the module's prose and in variance reasoning; no single framework anchors them.

## Triggers

- "update the budget plan for [period]"
- "log actual spend for [category]: $X"
- "forecast next quarter"
- "show variance" / "where are we over/under budget"
- "close the [period] — snapshot to history"
- "add a new budget category: [name]"
- "vendor spend has drifted — help me think through it"
- "draft the budget section of the board update"
- "capex vs opex for the GPU cluster"
- Oblique: "why is [category] so expensive"
- Oblique: "we need to cut spend by X% — what's the least-painful path"

## Activation flow

Each step writes a concrete artifact and appends its step number to `activation_completed` in `_module.md`.

### 1. Declare budget structure

**Ask:** "Walk me through the budget category taxonomy. Typical engineering categories: headcount (salaries + benefits + equipment), cloud infrastructure, vendor SaaS / tools, professional services (consultants / contractors), training & education, travel, hardware capex, miscellaneous. For each category: name, short slug, capex-vs-opex classification, and whether you want to further break it down (e.g., cloud broken into AWS / GCP / Datadog). Currency default (USD unless multi-currency)."
**Writes:** `cto-os-data/modules/budget/state/budget-structure.md` with `type: budget-structure`, `slug: current`, `categories`, `currency`, `period_granularity` (monthly, quarterly, annual).
**Expects:** frontmatter `categories` has ≥ 3 entries; `currency` and `period_granularity` set.

### 2. Seed current period plan + actuals per category

**Ask:** "For the current period (e.g., this quarter or this fiscal year), what's the planned amount per category, and actuals so far if you're mid-period? Rough is fine; we'll refine as actuals come in."
**Writes:** one file per category at `cto-os-data/modules/budget/state/categories/{category-slug}.md` with `type: budget-category`, `slug: <category-slug>`, `current_period`, `current_plan_amount`, `current_actual_amount`, `current_forecast_amount`, `currency`, `capex_opex`.
**Expects:** one category file per entry in `budget-structure.categories` exists, each with `current_plan_amount` set.

## Skills

### `update-budget-structure`

**Purpose:** Revise the category taxonomy — add a new category, merge two, deprecate one, change capex/opex classification, change period granularity.

**Triggers:**
- "update budget structure"
- "add a new budget category: [name]"
- "change the period to quarterly"

**Reads:** `cto-os-data/modules/budget/state/budget-structure.md`.

**Writes:** `cto-os-data/modules/budget/state/budget-structure.md`, overwrite-with-history. If a category is added, also creates the corresponding `categories/{category-slug}.md` via `add-category`.

### `add-category`

**Purpose:** Create a new budget-category file with initial plan/actual/forecast values for the current period.

**Triggers:**
- "add a budget category: [name]"
- "we need to track [new vendor] separately"

**Reads:** `cto-os-data/modules/budget/state/budget-structure.md` (validate the category is in the structure, or add it first).

**Writes:** `cto-os-data/modules/budget/state/categories/{category-slug}.md`, append-new-file.

### `update-category`

**Purpose:** Update the current period's plan, actual, or forecast for a specific category. The primary runtime skill — how spend actuals and forecast revisions land in state.

**Triggers:**
- "log actual for [category]: $X"
- "update [category] plan to $Y"
- "revise forecast on [category]"
- "[category] just came in at $Z"

**Reads:** `cto-os-data/modules/budget/state/categories/{category-slug}.md`.

**Writes:** `cto-os-data/modules/budget/state/categories/{category-slug}.md`, overwrite-with-history (period snapshots accumulate in body under `## Period history`).

### `close-period`

**Purpose:** Snapshot the current period's plan / actual / forecast per category to history, and roll forward to the next period (clearing `current_actual_amount` and setting `current_period` to the next boundary). Invoked at period boundaries — monthly, quarterly, or annual depending on `period_granularity`.

**Triggers:**
- "close the [period]"
- "roll to next period"
- "end of Q2 — close out"

**Reads:**
- `cto-os-data/modules/budget/state/budget-structure.md` (period granularity, next period calculation)
- `cto-os-data/modules/budget/state/categories/` (all category files)

**Writes:** updates every category file — appends a `## Period history` entry with the closing period's frontmatter snapshot, then resets `current_period` and `current_actual_amount` for the new period. Plan and forecast carry forward as defaults; user edits from there.

### `show-variance`

**Purpose:** Read-time cross-category variance view. Plan vs actual vs forecast per category for the current period, trend against prior periods, biggest over/under-runs surfaced.

**Triggers:**
- "show variance"
- "where are we over/under budget"
- "budget-to-actual for this quarter"

**Reads:** `scan(type=["budget-category"], fields=["slug", "current_period", "current_plan_amount", "current_actual_amount", "current_forecast_amount", "capex_opex"])`.

**Writes:** —

### `draft-budget-narrative`

**Purpose:** Compose a budget narrative for a reporting audience — board update, exec-team review, CFO check-in. Pulls current state and period trends; frames non-obvious category-level decisions through Core vs Context where that adds clarity.

**Triggers:**
- "draft the budget section of the board update"
- "write the budget narrative for the exec review"
- "explain the [category] overrun"

**Reads:**
- `cto-os-data/modules/budget/state/categories/` (current state)
- `cto-os-data/modules/budget/state/budget-structure.md` (framing)
- `cto-os-data/modules/business-alignment/state/company-goals/` (optional — strategic framing)
- `cto-os-data/modules/technical-strategy/state/` (optional — if build-vs-buy ADRs exist to cite)
- `cto-os-data/modules/personal-os/state/voice/` (optional — tone)

**Writes:** — (narrative produced for user to review; user captures final version elsewhere — typically Board Comms or Org Comms — through those modules' skills)

## Persistence

- **`cto-os-data/modules/budget/state/budget-structure.md`** — singleton (`slug: current`), overwrite-with-history. Frontmatter: `type: budget-structure, slug: current, updated: <date>, categories: <list of {name, slug, capex_opex, description}>, currency: <string>, period_granularity: <monthly|quarterly|annual>`. Body: narrative on choices + `## History`.
- **`cto-os-data/modules/budget/state/categories/{category-slug}.md`** — one file per category, overwrite-with-history. Frontmatter: `type: budget-category, slug: <category-slug>, updated: <date>, category_name: <string>, capex_opex: <capex|opex>, currency: <string>, current_period: <string>, current_plan_amount: <number>, current_actual_amount: <number, defaults to 0>, current_forecast_amount: <number, optional>, ytd_plan: <number, optional>, ytd_actual: <number, optional>`. Body: notes on the category + `## Period history` with per-period snapshots of plan / actual / forecast.

**Overrides to the cross-cutting save rule** ([Persistence model](../../docs/ARCHITECTURE.md#persistence-model)): `close-period` is a bulk, mildly destructive operation (it resets actuals and rolls periods). Always confirm explicitly before running — the user should see the list of affected files and confirm. Other writes inherit the default.

**Sensitivity:** standard default at module level. Specific categories (e.g., comp-related headcount, M&A reserves, fundraising-sensitive spend) can be flagged `sensitivity: high` per-file.

## State location

`cto-os-data/modules/budget/state/`
