---
name: product
description: "Activates for product *work* — product strategy, product goals, roadmap (now/next/later), initiative lifecycle (discovery → validated → in-flight → shipped | killed), prioritization decisions, user-research findings, structured product feedback from GTM and post-sale channels (sales, customer success, support, implementation, marketing, partners), the product-trio operating model (PM + design + engineering + data science), and the product function's operating cadence. Also activates on oblique phrasings like 'where's product at,' 'what's on the roadmap,' 'sales got pushback on pricing,' 'CS flagged a usability issue,' 'we're starting discovery on X,' 'we killed Y,' 'we ran interviews and found...,' 'prep for product review.' Does NOT activate on PM 1:1s / coaching / delegation (Managing Down), PM performance reviews / calibration / promotions / PIPs (Performance & Development), PM flow metrics like cycle time and WIP (Process Management, `flow_type: pm`), company goals or customer signal at CTO altitude (Business Alignment), technical architecture / ADRs / tech-debt (Technical Strategy), or the org structure of the product function (Org Design)."
requires: []
optional:
  - business-alignment
  - process-management
  - technical-strategy
  - managing-down
  - personal-os
---

# Product

## Scope

The substance of the product response — strategy, goals, roadmap, the bets we're making, and the evidence behind them. Captures the layered hierarchy from product strategy down through product goals, the now/next/later roadmap, active initiatives, prioritization decisions, user-research findings, and structured GTM/post-sale feedback. Also captures the operating model (how PM, design, engineering, and data science work together) and the cadence at which the product function reviews itself. The module is foundational on the product side — required deps are empty; it can activate before any of its optional readers exist.

## Out of scope

- **Company goals, customer signal capture, work-to-goals mapping** → Business Alignment. Product reads these as optional context (drives `product-goal.linked_company_goal`).
- **PM 1:1s, coaching, delegation, team-wide comms** → Managing Down. This module is about the product *work*; the leadership relationship with PMs sits there.
- **PM performance reviews, calibration, promotions, PIPs** → Performance & Development.
- **PM flow metrics (discovery → shipped cycle time, WIP, throughput)** → Process Management (`flow_type: pm`). `show-product-status` reads it but never owns it.
- **Technical architecture decisions, ADRs, tech-debt** → Technical Strategy.
- **Org structure of the product function** → Org Design.
- **Win-loss / aggregated competitive positioning** → Sales, not CTO OS. Individual win-loss items land here as `product-feedback` entries; aggregated competitive intel is not in scope.

## Frameworks

The module's spine follows **Ravi Mehta's product hierarchy**: company mission → company strategy → product strategy → product goals → product roadmap → initiatives. State maps onto each layer; the relationships between layers are explicit cross-references between types.

- [Richard Rumelt — *Good Strategy, Bad Strategy*](https://www.amazon.com/Good-Strategy-Bad-Difference-Matters/dp/0307886239) — the strategy kernel: diagnosis, guiding policy, coherent actions. Strategy without all three is platitude.
  - *How this module applies it:* `product-strategy-doc` body uses Rumelt's kernel as the literal section headings. A strategy doc isn't valid until each section is populated. Forces the strategy to name *what's actually going on* (diagnosis) before declaring the bet (guiding policy) and the work that follows from the bet (coherent actions).

- [Marty Cagan — *Inspired* / SVPG](https://www.svpg.com/books/inspired-how-to-create-tech-products-customers-love/) — empowered product teams, discovery vs delivery, the four product risks (value, usability, feasibility, business viability).
  - *How this module applies it:* `product-initiative` lifecycle is Cagan's `discovery → validated → in-flight → shipped | killed`. Each initiative carries a `risks_assessed` list — discovery is "done enough" to transition to `validated` when ≥3 of the four risks have evidence. `product-trio-model` declares the empowered-team operating pattern. The "feature factory" anti-pattern is what this module is built to resist: the existence of `product-goal` (the measurement layer) and the outcome-orientation of the roadmap are both deliberate counters.

- [Teresa Torres — *Continuous Discovery Habits*](https://www.producttalk.org/continuous-discovery-habits/) — opportunity solution trees, the product trio, weekly customer touchpoints.
  - *How this module applies it:* both `user-research-finding` and `product-feedback` carry an `opportunity` tag using the same convention, so they roll up against the same opportunity tree at query time even though they're structurally distinct types. The product-trio terminology is retained at the type level (`product-trio-model`) even though we add data science as a fourth role — see the type's naming note. The module surfaces a "have we talked to a user this week" posture check mirroring Torres's habit cadence.

- [Janna Bastow — Now / Next / Later roadmap](https://www.producttalk.org/2020/04/the-now-next-later-roadmap/) + [Itamar Gilad — outcome roadmaps](https://itamargilad.com/the-evidence-guided-success-formula/) — outcome-banded, horizon-grouped roadmaps; release roadmaps deprecated in favor of outcome roadmaps.
  - *How this module applies it:* `product-roadmap` is a singleton with three horizons — now, next, later — and each band is a list of *outcomes* (not features, not release dates). Re-anchored quarterly via `update-roadmap`. Initiatives reference a roadmap band, but the band itself states outcome, not promised ship date. A roadmap entry that names a feature is a smell the skill calls out at write time.

## Triggers

- "update product strategy" / "rewrite the product strategy"
- "add a product goal" / "update progress on [goal]" / "we hit/missed [goal]"
- "re-anchor the roadmap" / "what's on the roadmap" / "move X from next to now"
- "we're starting discovery on X" / "add a new initiative"
- "X just shipped" / "we killed Y" / "move Z from discovery to in-flight"
- "log the prioritization decision" / "we decided to do A over B"
- "log the research" / "we ran interviews and found..." / "usability test results"
- "sales got pushback on pricing for [customer]"
- "CS flagged a usability issue"
- "support sees [pattern] across tickets"
- "implementation is hitting a compliance block at [customer]"
- "log product feedback" / "what's the feedback looking like" / "any pricing pushback recently"
- "prep for product review with [PM]" / "what should I bring to the product review"
- "where's product at" / "product status"
- "we just did the strategy refresh" / "change the product-review cadence"
- Oblique: "are we hitting our goals" (product framing routes here; company-goal framing routes to Business Alignment)
- Oblique: "are we shipping the right things" (when scoped to product work)
- Oblique: "is this an exploration bet or a known-impact thing" (prioritization framing)

## Activation flow

Each step writes one concrete artifact and appends its step number to `activation_completed` in `_module.md`. Steps are ordered to mirror the Ravi Mehta hierarchy: strategy first, then goals, then roadmap, then initiatives, then operating layer.

### 1. Capture current product strategy

**Ask:** "Walk me through your current product strategy using Rumelt's kernel. (a) *Diagnosis* — what's actually going on with users, the market, or the competitive landscape that we're responding to? (b) *Guiding policy* — what's the bet, the overall approach to the diagnosis? (c) *Coherent actions* — what concrete actions does the bet imply? Don't worry about polish; we'll iterate via `set-product-strategy`."
**Writes:** `cto-os-data/modules/product/state/strategies/current.md` with `type: product-strategy-doc`, `slug: current`, `area: <area>`, `horizon: <horizon>`, `status: active`.
**Expects:** body has all three sections (`## Diagnosis`, `## Guiding policy`, `## Coherent actions`) populated with prose.

### 2. Declare product goals

**Ask:** "What measurable product goals is product trying to move this horizon? Typically 3–5. For each: title, metric (the thing being measured), target (the value or movement), horizon (e.g., 2026-Q3), owner. If Business Alignment is active and a company-goal item this product goal ladders to is obvious, capture that link too."
**Writes:** one file per goal at `cto-os-data/modules/product/state/goals/{goal-slug}.md` with `type: product-goal`.
**Expects:** ≥ 2 goal files, each with `metric`, `target`, `horizon`, and `status` set (`status: on-track` is a fine default at activation).
**Skip if:** the user has no formalized product goals at all; capture in the body of the strategy doc that goals are deferred and revisit in 2–4 weeks.

### 3. Baseline the current roadmap

**Ask:** "Let's baseline the now/next/later roadmap. *Outcomes*, not features, not release dates. Now: what's committed for this quarter. Next: what's likely next quarter. Later: what's on the horizon beyond. An entry like 'reduce time-to-first-alert for new districts' is a good outcome; 'ship the new alerting UI' is a feature — push back if the user gives features."
**Writes:** `cto-os-data/modules/product/state/roadmap.md` with `type: product-roadmap`, `slug: current`, `horizon_anchor: <today>`, `now`/`next`/`later` lists populated.
**Expects:** at least the `now` band has ≥ 1 entry. `next` and `later` can be empty deliberately, but the user should declare them empty rather than skip the prompt.

### 4. Enumerate active initiatives

**Ask:** "Walk me through the 5–10 active initiatives in flight. For each: title, status (discovery / validated / in-flight), the user outcome it serves, the PM driving it, which roadmap band it sits in, which product goal it moves, customer segment if it serves a specific one, your confidence (low/medium/high), and which of Cagan's four risks (value, usability, feasibility, business viability) you've assessed so far."
**Writes:** one file per initiative at `cto-os-data/modules/product/state/initiatives/{initiative-slug}.md` with `type: product-initiative`.
**Expects:** ≥ 3 initiative files, each with `status`, `outcome`, `owner`, `roadmap_band`, `confidence` set. `risks_assessed` may be empty for newly-opened discovery items.

### 5. Declare product trio model

**Ask:** "How does the product team actually operate? (a) Discovery model — dual-track (continuous discovery alongside delivery), sequential (discover-then-deliver), or hybrid? (b) Scope negotiation — does PM own scope, does engineering, or is it joint? (c) Handoff artifact — what document crosses the PM→eng line (PRD, problem brief, opportunity brief)? (d) Design role — embedded in product teams, shared as a center of excellence, or none? (e) Data science role — embedded (DS sits inside product teams), shared (DS is a center of excellence across teams), separate (DS is a different org product asks for help from), or none (DS isn't part of this product surface)?"
**Writes:** `cto-os-data/modules/product/state/trio-model.md` with `type: product-trio-model`, `slug: current`.
**Expects:** `discovery_model`, `scope_negotiation`, `handoff_artifact`, `design_role`, `data_science_role` all set. If DS varies meaningfully by product, the body should document the variance (e.g., "embedded in safety products; not used in classroom-management-for-devices").

### 6. Declare operating cadence

**Ask:** "What's the product function's review rhythm? (a) Product reviews — how often, who presents (rotating PM / all PMs / on-demand), who attends? (b) Metrics review — frequency and owner. (c) Strategy refresh — how often, when was the last one, when's the next due? Watch for the failure mode where metrics-review cadence outpaces strategy-refresh cadence; if so, the metrics meeting will become a de facto strategy meeting."
**Writes:** `cto-os-data/modules/product/state/operating-cadence.md` with `type: product-operating-cadence`, `slug: current`.
**Expects:** `product_review`, `metrics_review`, `strategy_refresh` all populated. `strategy_refresh.next_refresh` should be a future date.

Research findings and product feedback are not part of activation — they're logged as they happen via `log-research-finding` and `log-product-feedback`.

## Skills

### `set-product-strategy`

**Purpose:** Update a product strategy doc. Preserves prior versions as `## History` snapshots in the body.

**Triggers:**
- "update product strategy"
- "rewrite the product strategy"
- "we're refreshing the product strategy"

**Reads:**
- `cto-os-data/modules/product/state/strategies/{strategy-slug}.md` (current version)
- `cto-os-data/modules/business-alignment/state/company-goals/` (optional — does the strategy still align with company goals?)

**Writes:** `cto-os-data/modules/product/state/strategies/{strategy-slug}.md`, overwrite-with-history. Also updates `operating-cadence.md`'s `strategy_refresh.last_refresh` to today.

### `set-product-goal`

**Purpose:** Add a new product goal or update an existing one's status, current reading, or target.

**Triggers:**
- "add a product goal"
- "update progress on [goal]"
- "we hit [goal]" / "we missed [goal]"
- "[goal] is now at risk"

**Reads:**
- `cto-os-data/modules/product/state/goals/{goal-slug}.md` (if updating)
- `cto-os-data/modules/business-alignment/state/company-goals/` (optional — for `linked_company_goal` resolution)

**Writes:** `cto-os-data/modules/product/state/goals/{goal-slug}.md`, overwrite-with-history per goal.

### `update-roadmap`

**Purpose:** Overwrite the now/next/later roadmap. Used for re-anchoring (typically quarterly) or moving an outcome between bands.

**Triggers:**
- "re-anchor the roadmap"
- "update what's now/next/later"
- "move [outcome] from next to now"
- "add [outcome] to later"

**Reads:** `cto-os-data/modules/product/state/roadmap.md`.

**Writes:** `cto-os-data/modules/product/state/roadmap.md`, overwrite-with-history. Bumps `horizon_anchor` to today on full re-anchor; leaves it unchanged on small adjustments.

### `log-initiative`

**Purpose:** Append a new initiative (typically in `status: discovery`).

**Triggers:**
- "we're starting discovery on X"
- "add a new initiative"
- "stand up an initiative for [outcome]"

**Reads:**
- `cto-os-data/modules/product/state/goals/` (slug resolution for `linked_product_goal`)
- `cto-os-data/modules/product/state/roadmap.md` (slug resolution for `roadmap_band`)

**Writes:** `cto-os-data/modules/product/state/initiatives/{initiative-slug}.md`, append-new-file.

### `update-initiative`

**Purpose:** Transition initiative status, update outcome, link to a product goal, mark which of the four risks have been assessed, update confidence.

**Triggers:**
- "X just shipped"
- "we killed Y"
- "move Z from discovery to in-flight"
- "we now have evidence on the value risk for [initiative]"
- "raise confidence on [initiative]"

**Reads:** `cto-os-data/modules/product/state/initiatives/{initiative-slug}.md`.

**Writes:** `cto-os-data/modules/product/state/initiatives/{initiative-slug}.md`, overwrite-with-history. On `discovery → validated`, the skill checks `risks_assessed` and surfaces a warning if fewer than 3 of the 4 risks have evidence (per Cagan).

### `log-prioritization-decision`

**Purpose:** Append a prioritization decision. Captures the framework used, options considered, choice made, rationale.

**Triggers:**
- "log the prioritization decision"
- "we decided to do A over B"
- "log the prio call"

**Reads:**
- `cto-os-data/modules/product/state/initiatives/` (initiative slug resolution for `initiatives_in` / `_chosen` / `_deferred` / `_killed`)

**Writes:** `cto-os-data/modules/product/state/prioritization-decisions/{YYYY-MM-DD}-{decision-slug}.md`, append-new-file. Immutable once written (parallel to ADRs).

**Skill-level note — the RICE confidence trap:** per Vijay Iyengar (Mixpanel) on Lenny's podcast, RICE systematically under-scores high-reach/high-impact innovation bets because confidence and effort are murky for novel work. Before scoring, the skill asks: *is this a known-impact prioritization (RICE/ICE is fine) or an exploration bet (use a different lens — expected learning value, optionality, time-to-evidence)?* Capture the answer in the decision body.

### `log-research-finding`

**Purpose:** Append a user-research finding from an interview, usability test, survey, prototype test, or analytics dig.

**Triggers:**
- "log the research"
- "we ran interviews and found..."
- "usability test results"
- "analytics show..."

**Reads:**
- `cto-os-data/modules/product/state/initiatives/` (slug resolution for `linked_initiative`)

**Writes:** `cto-os-data/modules/product/state/findings/{YYYY-MM-DD}-{finding-slug}.md`, append-new-file.

### `log-product-feedback`

**Purpose:** Append a structured feedback item from a GTM or post-sale channel. Captures `source` (sales / customer-success / support / implementation / marketing / partner), `category` (one of seven), `severity` (blocker / major / minor / fyi), customer if known, link to an initiative or opportunity if obvious.

**Triggers:**
- "sales got pushback on pricing for [customer]"
- "CS flagged a usability issue"
- "support sees [pattern] across tickets"
- "implementation is hitting a compliance block at [customer]"
- "log product feedback"
- "we lost a deal because..." (lands as `source: sales` + category appropriate)

**Reads:**
- `cto-os-data/modules/product/state/initiatives/` (for `linked_initiative` resolution)
- `cto-os-data/modules/product/state/feedback/` (recent, for pattern detection)

**Writes:** `cto-os-data/modules/product/state/feedback/{YYYY-MM-DD}-{feedback-slug}.md`, append-new-file.

**Categorization behavior:** on entry, the skill *proposes* the matching category and severity based on the user's phrasing and asks the user to confirm before saving. Keeps the taxonomy clean over time without making the user remember the seven values. The seven categories: `missing-capability`, `usability`, `reliability-performance`, `integration`, `pricing-packaging`, `compliance-security` (accessibility folds here — it's a procurement gate, not a usability sub-type), `support-enablement`.

### `show-feedback-rollup`

**Purpose:** Read-only assembly grouping recent `product-feedback` entries by category, by source, and by linked initiative. Blockers and high-severity items surface first; `fyi` items are filtered out unless explicitly requested.

**Triggers:**
- "what's the feedback looking like"
- "show product feedback"
- "any pricing pushback recently"
- "feedback by category"
- "what's sales been hearing"

**Reads:** `cto-os-data/modules/product/state/feedback/` (all, or scoped by time window).

**Writes:** — (read-only).

**Surfaces:** initiatives with no feedback supporting them (potential feature-factory smell), and feedback patterns with no initiative claiming them (orphan signal that may warrant a new initiative or roadmap re-anchor).

### `show-product-status`

**Purpose:** Read-only assembly of the current state of product: strategy summary, product goals with status, roadmap (now/next/later), active initiatives by band (with confidence and risks-assessed shown), recent findings, recent feedback summary, and operating-cadence touchpoints (next product review, strategy-refresh due date — flagged "overdue" if past).

**Triggers:**
- "where's product at"
- "product status"
- "what's on the roadmap"
- "show me product"

**Reads:**
- `cto-os-data/modules/product/state/` (all)
- `cto-os-data/modules/business-alignment/state/` (optional — for company→product goal cascade)
- `cto-os-data/modules/process-management/state/flows/` (optional — PM flow metrics if a `pm` flow exists)

**Writes:** —

### `prep-product-review`

**Purpose:** Prep a product-review meeting. Pulls active initiatives (filtered to the named PM's initiatives if a PM is named) + recent findings + recent feedback (filtered the same way) + roadmap + goal status + optionally the PM's profile from Managing Down.

**Triggers:**
- "prep for product review with [PM]"
- "what should I bring to the product review"
- "prep the product review"

**Reads:**
- `cto-os-data/modules/product/state/initiatives/`
- `cto-os-data/modules/product/state/findings/` (recent)
- `cto-os-data/modules/product/state/feedback/` (recent)
- `cto-os-data/modules/product/state/roadmap.md`
- `cto-os-data/modules/product/state/goals/`
- `cto-os-data/modules/managing-down/state/people/{pm-slug}.md` (optional)

**Writes:** —

### `update-operating-cadence`

**Purpose:** Overwrite the operating cadence. Also used to record when a strategy refresh actually happens (sets `strategy_refresh.last_refresh` and computes the next due date).

**Triggers:**
- "we just did the strategy refresh"
- "change the product-review cadence"
- "stand up a monthly metrics review"
- "the product review is moving to biweekly"

**Reads:** `cto-os-data/modules/product/state/operating-cadence.md`.

**Writes:** `cto-os-data/modules/product/state/operating-cadence.md`, overwrite-with-history.

## Persistence

- **`cto-os-data/modules/product/state/strategies/{strategy-slug}.md`** — one file per strategy area, overwrite-with-history. Frontmatter: `type: product-strategy-doc, slug: <area-slug>, updated: <date>, area: <string>, horizon: <string>, status: <draft|active|archived>, owner: <string, optional>`. Body sections: `## Diagnosis`, `## Guiding policy`, `## Coherent actions`, `## History`.
- **`cto-os-data/modules/product/state/goals/{goal-slug}.md`** — one file per product goal, overwrite-with-history. Frontmatter: `type: product-goal, slug: <goal-slug>, updated: <date>, title: <string>, metric: <string>, current: <string, optional>, target: <string>, horizon: <string>, status: <on-track|at-risk|off-track|hit|missed|retired>, linked_company_goal: <string, optional>, owner: <string>`. Body sections: `## Rationale`, `## Tracking notes`, `## History`.
- **`cto-os-data/modules/product/state/roadmap.md`** — singleton (`slug: current`), overwrite-with-history. Frontmatter: `type: product-roadmap, slug: current, updated: <date>, horizon_anchor: <date>, now: <list>, next: <list>, later: <list>`. Body: `## History`.
- **`cto-os-data/modules/product/state/initiatives/{initiative-slug}.md`** — one file per initiative, overwrite-with-history. Frontmatter: `type: product-initiative, slug: <initiative-slug>, updated: <date>, title: <string>, status: <discovery|validated|in-flight|shipped|killed>, outcome: <string>, linked_product_goal: <string, optional>, customer_segment: <string, optional>, roadmap_band: <now|next|later|none>, confidence: <low|medium|high>, risks_assessed: <list of value|usability|feasibility|business-viability>, opened: <date>, shipped_date: <date, optional>, killed_date: <date, optional>, owner: <string>`. Body sections: `## Hypothesis`, `## Evidence`, `## Decisions`, `## History`.
- **`cto-os-data/modules/product/state/prioritization-decisions/{YYYY-MM-DD}-{decision-slug}.md`** — append-new-file per decision; body immutable once written. Frontmatter: `type: prioritization-decision, slug: <YYYY-MM-DD>-<decision-slug>, updated: <date>, decision_summary: <string>, framework: <rice|ice|kano|value-vs-effort|opportunity-tree|other>, initiatives_in: <list>, initiatives_chosen: <list>, initiatives_deferred: <list>, initiatives_killed: <list>`. Body sections: `## Context`, `## Options`, `## Decision`, `## Rationale`, `## Review date`.
- **`cto-os-data/modules/product/state/findings/{YYYY-MM-DD}-{finding-slug}.md`** — append-new-file per finding. Frontmatter: `type: user-research-finding, slug: <YYYY-MM-DD>-<finding-slug>, updated: <date>, research_type: <interview|usability-test|survey|prototype-test|log-analysis|other>, participants_count: <int, optional>, opportunity: <string, optional>, linked_initiative: <string, optional>, confidence: <low|medium|high>`. Body sections: `## Finding`, `## Evidence`, `## Implication`, `## Follow-ups`.
- **`cto-os-data/modules/product/state/feedback/{YYYY-MM-DD}-{feedback-slug}.md`** — append-new-file per feedback item. Frontmatter: `type: product-feedback, slug: <YYYY-MM-DD>-<feedback-slug>, updated: <date>, source: <sales|customer-success|support|implementation|marketing|partner>, category: <missing-capability|usability|reliability-performance|integration|pricing-packaging|compliance-security|support-enablement>, customer: <string, optional>, linked_initiative: <string, optional>, opportunity: <string, optional>, severity: <blocker|major|minor|fyi>, verbatim: <bool>`. Body sections: `## Feedback`, `## Context`, `## Implication`, `## Follow-ups`.
- **`cto-os-data/modules/product/state/trio-model.md`** — singleton (`slug: current`), overwrite-with-history. Frontmatter: `type: product-trio-model, slug: current, updated: <date>, discovery_model: <dual-track|sequential|hybrid>, scope_negotiation: <pm-owns|eng-owns|joint>, handoff_artifact: <string>, pm_to_eng_ratio: <string, optional>, design_role: <embedded|shared|none>, data_science_role: <embedded|shared|separate|none>`. Body: prose documenting any per-product variance in DS integration + `## History`.
- **`cto-os-data/modules/product/state/operating-cadence.md`** — singleton (`slug: current`), overwrite-with-history. Frontmatter: `type: product-operating-cadence, slug: current, updated: <date>, product_review: <object>, metrics_review: <object>, strategy_refresh: <object>`. Body: `## History`.

**Overrides to the cross-cutting save rule** ([Persistence model](../../docs/ARCHITECTURE.md#persistence-model)): none — inherits the default. Sensitivity is `standard`.

## State location

`cto-os-data/modules/product/state/`
