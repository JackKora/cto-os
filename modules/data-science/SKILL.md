---
name: data-science
description: "Activates for data science *work* — DS strategy, DS goals, DS initiative lifecycle (discovery → validated → in-flight → shipped | killed), structured experiments (A/B tests, holdouts, canaries, switchbacks per Kohavi), ML evals (model output quality scored on labeled/golden sets per Husain & Shankar), the model registry (training → staging → production → retired), insights with explicit consumed-by tracking (the loop-closure Peter Deng flagged — insights that get produced and ignored), the DS-product partnership operating model (embedded / hub-and-spoke / centralized / service-org), and the DS function's operating cadence. Also activates on oblique phrasings like 'we ran an experiment on the new classifier,' 'eval the model,' 'log the analysis,' 'the model just went to production,' 'we just retrained,' 'we decided X based on what data said,' 'show me where DS is at,' 'prep for the DS review.' Does NOT activate on DS flow metrics like cycle time and WIP (Process Management, `flow_type: ds`), model-serving SLOs / inference incidents / postmortems (Tech Ops), ML architecture or platform ADRs (Technical Strategy), DS-IC 1:1s / coaching / team comms (Managing Down), DS performance reviews / calibration / promotions / PIPs (Performance & Development), DS hiring (Hiring), or where DS reports / centralized vs embedded as an org-design call (Org Design — this module captures the *operating reality*, not the org-design decision)."
requires: []
optional:
  - business-alignment
  - process-management
  - technical-strategy
  - tech-ops
  - product
  - managing-down
  - personal-os
---

# Data Science

## Scope

The substance of the data-science function — strategy, goals, project-level initiatives, the experiments and ML evals that produce evidence, the production model registry, and the insights that should drive decisions but historically get produced and ignored. Also captures the operating model between DS and product (mirror of `product-trio-model` from the DS side) and the cadence at which the DS function reviews itself. Foundational on the DS side — required deps are empty; can activate before any optional readers exist.

## Out of scope

- **DS flow metrics** (discovery → shipped cycle time, WIP, throughput) — Process Management owns these via `flow_type: ds`. `show-ds-status` reads them but never owns them.
- **Model-serving SLOs, inference incidents, postmortems** — Tech Ops. `model.linked_slo` is a soft reference into Tech Ops' SLO records.
- **ML architecture / platform decisions** (which training framework, which serving infra, build-vs-buy on experimentation platform) — Technical Strategy ADRs.
- **DS-IC 1:1s, coaching, team-wide comms** — Managing Down. This module is about DS *work*; the leadership relationship sits there.
- **DS performance reviews, calibration, promotions, PIPs** — Performance & Development.
- **DS hiring pipeline** — Hiring.
- **DS team rubric / team retros** — Team Management. Generic rubric works.
- **Where DS reports / centralized vs embedded as an org-design decision** — Org Design. This module captures the *operating reality* (`ds-product-partnership.operating_model`), not the decision that produced it.
- **MLOps tooling internals** (experiment-tracking platform choice, model registry tool, monitoring vendor) — Technical Strategy ADRs.
- **Data quality / data tech-debt** — Technical Strategy with `area: data` on `tech-debt-item` for v1. May earn a dedicated type later.
- **DS roadmap as a now/next/later band layer** — deliberately omitted. DS work is experiment-driven and exploratory; goals + initiatives + experiments capture the work without forcing horizon bands. (Asymmetric to Product on this one point — intentional.)

## Frameworks

Module spine: Ravi Mehta's hierarchy adapted for DS — **company mission → company strategy → DS strategy → DS goals → DS initiatives → experiments / evals / models / insights.** State maps onto each layer; the relationships between layers are explicit cross-references between types.

- [Richard Rumelt — *Good Strategy, Bad Strategy*](https://www.amazon.com/Good-Strategy-Bad-Difference-Matters/dp/0307886239) — the strategy kernel: diagnosis, guiding policy, coherent actions.
  - *How this module applies it:* `ds-strategy-doc` body uses Rumelt's kernel as the literal section headings. Forces the strategy to name *what's going on with our data and our models* (diagnosis) before declaring the bet (guiding policy) and the work that follows (coherent actions). Identical shape to `product-strategy-doc` and `technical-strategy-doc`; only the subject domain differs.

- [Ronny Kohavi — *Trustworthy Online Controlled Experiments*](https://experimentguide.com/) — the experimentation platform as both safety net (abort fast on bad launches) and oracle (tell us what works); trust as the foundational property.
  - *How this module applies it:* `ds-experiment` is structured around hypothesis → design → primary-metric → result → decision. The `status` transition from `running` to `completed` enforces the safety-net property at the skill level: `update-ds-experiment` warns when an experiment closes without a `## Decision` body section populated. Orphan experiments (closed without decision) are flagged by `show-ds-status`. Distinct from `ml-eval` — experiments compare variants in flight; evals score against a reference.

- [Hamel Husain & Shreya Shankar — AI evals](https://hamel.dev/blog/posts/evals/) — evals as a first-class discipline for AI/ML product builders: systematically scoring model output on labeled / golden / human-rated sets, distinct from production A/B tests.
  - *How this module applies it:* `ml-eval` is a dedicated type with its own enum (`offline-benchmark | online-scoring | human-rated | synthetic | comparative`) and its own lifecycle (`designing → running → completed`). On a `completed` eval whose target_model is in `production`, `update-ml-eval` updates the target model's `latest_eval` pointer so the model registry always knows its most recent quality reading.

- [Teresa Torres — *Continuous Discovery Habits*](https://www.producttalk.org/continuous-discovery-habits/) — opportunity tagging convention.
  - *How this module applies it:* `insight` entries carry an `opportunity` tag using the same convention as Product's `user-research-finding` and `product-feedback`. Three inbound surfaces across two modules roll up against the same opportunity tree at query time.

- Hub-and-spoke operating model (2026 industry consensus — [Atlan](https://atlan.com/know/centralized-vs-federated-data-teams-in-the-ai-era/), [Sigma](https://www.sigmacomputing.com/blog/data-org-dilemma)) — central DS platform + governance with federated domain ownership. AI raises both the cost of misalignment *and* the demand for speed and autonomy; hub-and-spoke balances both.
  - *How this module applies it:* `ds-product-partnership.operating_model` includes `hub-and-spoke` as a first-class enum value alongside `embedded`, `centralized`, `service-org`. The mirror field in `product.product-trio-model.data_science_role` uses a different shape (`embedded | shared | separate | none`) because it's describing the relationship from product's POV. The two stay distinct on purpose — see the type's coexistence note.

## Triggers

- "update DS strategy" / "rewrite the data-science strategy"
- "add a DS goal" / "we hit/missed [DS goal]"
- "we're starting an investigation on X" / "add a DS initiative"
- "we just shipped the new classifier" / "we killed that model investigation"
- "log the experiment" / "we're running an A/B on the new ranker" / "the holdout test ended"
- "eval the model" / "log the eval results" / "run a golden-set eval on [model]"
- "register a new model" / "[model] just went to production" / "retire [model]"
- "we just retrained" / "log the retraining"
- "log the analysis" / "log an insight" / "we learned X from looking at the data"
- "we decided X based on [insight]" / "exec staff acted on [insight]" / "consumed [insight]"
- "show me where DS is at" / "DS status"
- "what's in the insight pipeline" / "any orphan insights"
- "prep for the DS review with [IC]" / "what should I bring to the DS review"
- "change the DS-product partnership model" / "we're moving to hub-and-spoke"
- "we just did the DS strategy refresh"
- Oblique: "is the model still working" (model-review framing, routes here)
- Oblique: "did anything come of that analysis" (insight-loop-closure framing)
- Oblique: "what did the experiment tell us" (experiment decision-capture)

## Activation flow

Each step writes one concrete artifact and appends its step number to `activation_completed` in `_module.md`. Steps mirror the Ravi Mehta hierarchy adapted for DS. Roadmap step is deliberately omitted (see Out of scope).

### 1. Capture current DS strategy

**Ask:** "Walk me through your current DS strategy using Rumelt's kernel. (a) *Diagnosis* — what's actually going on with your data, your models, your team, or the AI/ML landscape that you're responding to? (b) *Guiding policy* — what's the bet, the overall approach? (c) *Coherent actions* — what concrete actions does the bet imply? Don't worry about polish; we'll iterate via `set-ds-strategy`."
**Writes:** `cto-os-data/modules/data-science/state/strategies/current.md` with `type: ds-strategy-doc`, `slug: current`, `area: <area>`, `horizon: <horizon>`, `status: active`.
**Expects:** body has `## Diagnosis`, `## Guiding policy`, `## Coherent actions` populated with prose.

### 2. Declare DS goals

**Ask:** "What measurable DS goals are you tracking this horizon? Typically 3–5. For each: title, metric (the thing being measured — e.g., 'safety classifier F1', 'time-from-question-to-insight', 'model retraining cadence adherence'), target, horizon, owner. If `business-alignment` is active and an obvious link to a company goal exists, capture that too."
**Writes:** one file per goal at `cto-os-data/modules/data-science/state/goals/{goal-slug}.md` with `type: ds-goal`.
**Expects:** ≥ 2 goal files with `metric`, `target`, `horizon`, `status` set.
**Skip if:** the user has no formalized DS goals; capture in strategy body that goals are deferred and revisit in 2–4 weeks.

### 3. Enumerate active DS initiatives

**Ask:** "Walk me through the active DS initiatives — substantial projects, not ad-hoc analyses. New model builds, multi-week investigations, dashboards with stakeholder commitment. For each: title, status (discovery / validated / in-flight), outcome it serves, owner, your confidence, optional linked DS goal, optional linked product initiative (if the DS work is the back-end of a product initiative)."
**Writes:** one file per initiative at `cto-os-data/modules/data-science/state/initiatives/{initiative-slug}.md` with `type: ds-initiative`.
**Expects:** ≥ 2 initiative files with `status`, `outcome`, `owner`, `confidence` set.

### 4. Baseline the model registry

**Ask:** "What models do you have in production right now? For each: title, model family (e.g., 'safety-text-classifier', 'alert-prioritizer'), version, owner, training data pointer (free-text — a path or description, not the data itself), retraining cadence (weekly / on-drift / ad-hoc), latest eval if you have one, linked SLO slug if Tech Ops has an inference SLO for this model."
**Writes:** one file per production model at `cto-os-data/modules/data-science/state/models/{model-slug}.md` with `type: model`, `stage: production`.
**Expects:** if the org ships production models, ≥ 1 model file. If the org doesn't ship models at all, skip this step and note in strategy body.

### 5. Declare DS-product partnership

**Ask:** "What's the operating model between DS and product? (a) *Operating model* — embedded (DS sits inside product teams), hub-and-spoke (central DS platform + federated domain experts), centralized (we own everything, product comes to us), or service-org (we're a different org product asks for help from)? (b) *Supported product areas* — which product surfaces actively use DS? Examples of DS-heavy surfaces in general B2B SaaS: recommendations, fraud detection, content classification, anomaly detection, search ranking. *Edtech overlay*: safety classification, content moderation for student communications, learning-recommendation engines. Surfaces not listed imply DS isn't involved there — many products have non-DS surfaces alongside DS-heavy ones, and capturing the asymmetry is the point. (c) *Intake process* — how does product ask DS for work? (d) *Roadmap sync cadence* — how often do DS and product re-sync? (e) *Governance owner* (hub-and-spoke only) — who owns the central platform and standards?"
**Writes:** `cto-os-data/modules/data-science/state/partnership.md` with `type: ds-product-partnership`, `slug: current`.
**Expects:** `operating_model`, `supported_product_areas`, `intake_process`, `roadmap_sync_cadence` all set. Per-surface variance in body prose if needed.

### 6. Declare operating cadence

**Ask:** "What's the DS function's review rhythm? (a) *Practitioner review* — DS ICs walking through experiments / initiatives / model state. Frequency, presenter pattern, attendees. (b) *Analytics review* — DS metrics, goal-progress, experiment results. Frequency and owner. (c) *Model review* — periodic review of production model health: drift, error analysis, retraining triggers. Frequency, owner, scope. (d) *Strategy refresh* — frequency, last refresh date, when's the next due?"
**Writes:** `cto-os-data/modules/data-science/state/operating-cadence.md` with `type: ds-operating-cadence`, `slug: current`.
**Expects:** `practitioner_review`, `analytics_review`, `model_review`, `strategy_refresh` all populated.

Experiments, evals, and insights are not part of activation — they're logged as they happen via `log-ds-experiment`, `log-ml-eval`, and `log-insight`.

## Skills

### `set-ds-strategy`

**Purpose:** Update a DS strategy doc. Preserves prior versions as `## History` snapshots. Updates `operating-cadence.strategy_refresh.last_refresh` to today as a side effect.

**Triggers:**
- "update DS strategy"
- "rewrite the data-science strategy"
- "refresh DS strategy"

**Reads:**
- `cto-os-data/modules/data-science/state/strategies/{strategy-slug}.md`
- `cto-os-data/modules/business-alignment/state/company-goals/` (optional — does the strategy still ladder up?)

**Writes:** `cto-os-data/modules/data-science/state/strategies/{strategy-slug}.md`, overwrite-with-history. Also `cto-os-data/modules/data-science/state/operating-cadence.md` (updates `strategy_refresh.last_refresh`).

### `set-ds-goal`

**Purpose:** Add a new DS goal or update an existing one (status, current reading, target).

**Triggers:**
- "add a DS goal"
- "update progress on [DS goal]"
- "we hit [DS goal]" / "we missed [DS goal]"

**Reads:**
- `cto-os-data/modules/data-science/state/goals/{goal-slug}.md` (if updating)
- `cto-os-data/modules/business-alignment/state/company-goals/` (optional — for `linked_company_goal` resolution)

**Writes:** `cto-os-data/modules/data-science/state/goals/{goal-slug}.md`, overwrite-with-history per goal.

### `log-ds-initiative`

**Purpose:** Append a new DS initiative (typically in `status: discovery`).

**Triggers:**
- "we're starting an investigation on X"
- "add a DS initiative"
- "stand up an initiative for [outcome]"

**Reads:**
- `cto-os-data/modules/data-science/state/goals/` (slug resolution for `linked_ds_goal`)
- `cto-os-data/modules/product/state/initiatives/` (optional — slug resolution for `linked_product_initiative`)

**Writes:** `cto-os-data/modules/data-science/state/initiatives/{initiative-slug}.md`, append-new-file.

### `update-ds-initiative`

**Purpose:** Transition initiative status, update outcome, link to a product initiative, update confidence.

**Triggers:**
- "X just shipped"
- "we killed Y"
- "move Z from discovery to in-flight"
- "link [DS initiative] to [product initiative]"

**Reads:** `cto-os-data/modules/data-science/state/initiatives/{initiative-slug}.md`.

**Writes:** `cto-os-data/modules/data-science/state/initiatives/{initiative-slug}.md`, overwrite-with-history.

### `log-ds-experiment`

**Purpose:** Append a new experiment in `status: designing` or `running`. Captures hypothesis, design type, primary metric, target model if applicable, linked initiative.

**Triggers:**
- "log the experiment"
- "we're running an A/B on the new ranker"
- "starting a holdout test on [model]"
- "design a switchback experiment for [feature]"

**Reads:**
- `cto-os-data/modules/data-science/state/initiatives/` (slug resolution for `linked_ds_initiative`)
- `cto-os-data/modules/data-science/state/models/` (slug resolution for `linked_model`)

**Writes:** `cto-os-data/modules/data-science/state/experiments/{YYYY-MM-DD}-{experiment-slug}.md`, append-new-file.

### `update-ds-experiment`

**Purpose:** Transition experiment status (running → completed | killed | inconclusive), record result, record decision. **Enforces decision-capture** on `completed` transitions: warns when `## Decision` body section is empty (Kohavi's oracle property at the skill level).

**Triggers:**
- "the experiment just ended"
- "the holdout came back inconclusive"
- "we decided to ship the new ranker based on the experiment"
- "killed the switchback test"

**Reads:** `cto-os-data/modules/data-science/state/experiments/{YYYY-MM-DD}-{experiment-slug}.md`.

**Writes:** `cto-os-data/modules/data-science/state/experiments/{YYYY-MM-DD}-{experiment-slug}.md`, overwrite-with-history. On a `completed` transition with empty `## Decision`, surfaces a warning to the user (does not block).

### `log-ml-eval`

**Purpose:** Append a new eval. Captures eval_type (offline-benchmark / online-scoring / human-rated / synthetic / comparative), target model, dataset pointer, metric name, linked DS initiative if applicable.

**Triggers:**
- "log an eval on [model]"
- "run a golden-set eval"
- "human-rate the new classifier output"
- "comparative eval [model-v2] vs [model-v1]"

**Reads:**
- `cto-os-data/modules/data-science/state/models/` (slug resolution for `target_model`, `baseline_model`)
- `cto-os-data/modules/data-science/state/initiatives/` (slug resolution for `linked_ds_initiative`)

**Writes:** `cto-os-data/modules/data-science/state/evals/{YYYY-MM-DD}-{eval-slug}.md`, append-new-file.

### `update-ml-eval`

**Purpose:** Transition eval status (designing → running → completed), record score. On `completed` for a `target_model` in `stage: production`, updates `model.latest_eval` pointer as a side effect — the model registry always knows its most recent quality reading.

**Triggers:**
- "the eval just finished"
- "log the eval score"
- "[eval] came back at F1 0.87"

**Reads:** `cto-os-data/modules/data-science/state/evals/{YYYY-MM-DD}-{eval-slug}.md`.

**Writes:** `cto-os-data/modules/data-science/state/evals/{YYYY-MM-DD}-{eval-slug}.md`, overwrite-with-history. On `completed` transition for a production model, also `cto-os-data/modules/data-science/state/models/{target-model-slug}.md` (updates `latest_eval` pointer).

### `register-model`

**Purpose:** Append a new model registry entry. Default `stage: training` unless the user specifies otherwise. Sets `deployed_date` when the entry is created with or transitions into `stage: production`.

**Triggers:**
- "register a new model"
- "we have a new training run for [model-family]"
- "add [model] to the registry"

**Reads:**
- `cto-os-data/modules/data-science/state/models/` (collision check)
- `cto-os-data/modules/tech-ops/state/slos/` (optional — slug resolution for `linked_slo`)
- `cto-os-data/modules/data-science/state/initiatives/` (optional — slug resolution for `linked_ds_initiative`)

**Writes:** `cto-os-data/modules/data-science/state/models/{model-slug}.md`, append-new-file.

### `update-model`

**Purpose:** Lifecycle stage transitions (training → staging → production → retired), retraining events captured in body's `## Retraining log`, latest_eval pointer updates, owner changes.

**Triggers:**
- "[model] just went to production"
- "retire [model]"
- "promote [model] from staging to production"
- "we just retrained [model]"
- "log the retraining for [model]"

**Reads:** `cto-os-data/modules/data-science/state/models/{model-slug}.md`.

**Writes:** `cto-os-data/modules/data-science/state/models/{model-slug}.md`, overwrite-with-history. On `production` transition, sets `deployed_date`. On `retired` transition, sets `retired_date`.

### `log-insight`

**Purpose:** Append an insight. Captures source analysis (where it came from), insight statement, confidence, opportunity tag if known. Defaults `status: open` with empty `consumed_by` — the orphan-by-default posture is intentional; insights only count as consumed when someone explicitly records consumption.

**Triggers:**
- "log an insight"
- "log the analysis finding"
- "we learned X from the data"
- "the dashboard surfaced a pattern"

**Reads:**
- `cto-os-data/modules/data-science/state/insights/` (recent — for pattern detection)

**Writes:** `cto-os-data/modules/data-science/state/insights/{YYYY-MM-DD}-{insight-slug}.md`, append-new-file.

### `consume-insight`

**Purpose:** Record that an insight was consumed. Appends consumers to `consumed_by` list, optionally sets `drove_decision` (free-text or slug pointing to a `prioritization-decision` in product or an `adr` in technical-strategy), transitions `status` from `open` to `consumed`. The loop-closure ritual Peter Deng's framing demands.

**Triggers:**
- "we decided X based on [insight]"
- "consumed [insight] in the staff meeting"
- "exec staff acted on [insight]"
- "[product team] used [insight] for prioritization"
- "log that [insight] drove [decision]"

**Reads:** `cto-os-data/modules/data-science/state/insights/{YYYY-MM-DD}-{insight-slug}.md`.

**Writes:** `cto-os-data/modules/data-science/state/insights/{YYYY-MM-DD}-{insight-slug}.md`, overwrite-with-history. Body's `## Implication` may be amended with the consumption note; `## Follow-ups` may be amended with what to track next.

### `show-ds-status`

**Purpose:** Read-only assembly of the DS function's state: strategy summary, goals with status, active initiatives, active experiments grouped by status, production models with stage and latest_eval, recent insights, cadence touchpoints (next practitioner review, model-review due, strategy-refresh due — flagged "overdue" if past).

**Triggers:**
- "show me where DS is at"
- "DS status"
- "what's data science up to"
- "show me the models in production"

**Reads:**
- `cto-os-data/modules/data-science/state/` (all)
- `cto-os-data/modules/process-management/state/flows/` (optional — DS flow metrics if a `ds` flow exists)
- `cto-os-data/modules/business-alignment/state/company-goals/` (optional — for goal cascade)
- `cto-os-data/modules/product/state/trio-model.md` (optional — for partnership symmetry check; surfaces an informational note when the two views disagree)

**Writes:** —

### `prep-ds-review`

**Purpose:** Prep a DS review meeting. Pulls active initiatives + active experiments + recent evals + recent insights + roadmap-of-sorts (filtered to the IC's work if a specific IC is named) + optional IC profile from Managing Down.

**Triggers:**
- "prep for the DS review with [IC]"
- "what should I bring to the DS review"
- "prep the practitioner review"

**Reads:**
- `cto-os-data/modules/data-science/state/initiatives/`
- `cto-os-data/modules/data-science/state/experiments/`
- `cto-os-data/modules/data-science/state/evals/` (recent)
- `cto-os-data/modules/data-science/state/insights/` (recent)
- `cto-os-data/modules/managing-down/state/people/{ic-slug}.md` (optional)

**Writes:** —

### `show-insight-pipeline`

**Purpose:** Read-only assembly of insights grouped by status. **Surfaces orphans first** (status `open` with empty `consumed_by` after N days; default N=14). The point: per Peter Deng, insights produced and ignored are the failure mode. This view exists to close the loop or kill the orphan.

**Triggers:**
- "what's in the insight pipeline"
- "any orphan insights"
- "show insights by status"
- "what insights have we produced lately"

**Reads:** `cto-os-data/modules/data-science/state/insights/` (all, with status filter and age computation).

**Writes:** —

### `update-ds-partnership`

**Purpose:** Overwrite the DS-product partnership singleton. Used when the operating model shifts (e.g., centralized → hub-and-spoke) or when supported product areas change.

**Triggers:**
- "change the DS-product partnership"
- "we're moving to hub-and-spoke"
- "[product area] is now in DS scope"
- "we're no longer supporting [product area]"

**Reads:** `cto-os-data/modules/data-science/state/partnership.md`.

**Writes:** `cto-os-data/modules/data-science/state/partnership.md`, overwrite-with-history.

### `update-ds-operating-cadence`

**Purpose:** Overwrite the operating cadence. Used to log when a strategy refresh actually happens (sets `strategy_refresh.last_refresh` and computes the next due date), to change review cadences, or to add a model-review.

**Triggers:**
- "we just did the DS strategy refresh"
- "change the practitioner review cadence"
- "the model review is moving to weekly"
- "stand up a monthly analytics review"

**Reads:** `cto-os-data/modules/data-science/state/operating-cadence.md`.

**Writes:** `cto-os-data/modules/data-science/state/operating-cadence.md`, overwrite-with-history.

## Persistence

- **`cto-os-data/modules/data-science/state/strategies/{strategy-slug}.md`** — one file per strategy area, overwrite-with-history. Frontmatter: `type: ds-strategy-doc, slug: <area-slug>, updated: <date>, area: <string>, horizon: <string>, status: <draft|active|archived>, owner: <string, optional>`. Body sections: `## Diagnosis`, `## Guiding policy`, `## Coherent actions`, `## History`.
- **`cto-os-data/modules/data-science/state/goals/{goal-slug}.md`** — one file per DS goal, overwrite-with-history. Frontmatter: `type: ds-goal, slug: <goal-slug>, updated: <date>, title: <string>, metric: <string>, current: <string, optional>, target: <string>, horizon: <string>, status: <on-track|at-risk|off-track|hit|missed|retired>, linked_company_goal: <string, optional>, owner: <string>`. Body sections: `## Rationale`, `## Tracking notes`, `## History`.
- **`cto-os-data/modules/data-science/state/initiatives/{initiative-slug}.md`** — one file per initiative, overwrite-with-history. Frontmatter: `type: ds-initiative, slug: <initiative-slug>, updated: <date>, title: <string>, status: <discovery|validated|in-flight|shipped|killed>, outcome: <string>, linked_ds_goal: <string, optional>, linked_product_initiative: <string, optional>, confidence: <low|medium|high>, opened: <date>, shipped_date: <date, optional>, killed_date: <date, optional>, owner: <string>`. Body sections: `## Hypothesis`, `## Evidence`, `## Decisions`, `## History`.
- **`cto-os-data/modules/data-science/state/experiments/{YYYY-MM-DD}-{experiment-slug}.md`** — append-new-file per experiment, overwrite-with-history on status transitions. Frontmatter: `type: ds-experiment, slug: <YYYY-MM-DD>-<experiment-slug>, updated: <date>, title: <string>, design: <a-b-test|holdout|canary|switchback|observational|other>, hypothesis: <string>, primary_metric: <string>, linked_ds_initiative: <string, optional>, linked_model: <string, optional>, status: <designing|running|completed|killed|inconclusive>, started_date: <date>, ended_date: <date, optional>, owner: <string>`. Body sections: `## Design`, `## Result`, `## Decision`, `## Follow-ups`. `## Decision` empty until experiment closes.
- **`cto-os-data/modules/data-science/state/evals/{YYYY-MM-DD}-{eval-slug}.md`** — append-new-file per eval, overwrite-with-history on status transitions. Frontmatter: `type: ml-eval, slug: <YYYY-MM-DD>-<eval-slug>, updated: <date>, title: <string>, eval_type: <offline-benchmark|online-scoring|human-rated|synthetic|comparative>, target_model: <string>, baseline_model: <string, optional>, dataset: <string>, metric_name: <string>, score: <string, optional>, baseline_score: <string, optional>, status: <designing|running|completed>, linked_ds_initiative: <string, optional>, owner: <string>`. Body sections: `## Setup`, `## Result`, `## Conclusion`, `## Follow-ups`.
- **`cto-os-data/modules/data-science/state/models/{model-slug}.md`** — one file per model, overwrite-with-history. Frontmatter: `type: model, slug: <model-slug>, updated: <date>, title: <string>, model_family: <string>, version: <string>, stage: <training|staging|production|retired>, owner: <string>, training_data: <string>, retraining_cadence: <string>, latest_eval: <string, optional>, linked_slo: <string, optional>, linked_ds_initiative: <string, optional>, deployed_date: <date, optional>, retired_date: <date, optional>`. Body sections: `## Description`, `## Performance history`, `## Retraining log`, `## History`.
- **`cto-os-data/modules/data-science/state/insights/{YYYY-MM-DD}-{insight-slug}.md`** — append-new-file per insight, overwrite-with-history on consumption events. Frontmatter: `type: insight, slug: <YYYY-MM-DD>-<insight-slug>, updated: <date>, title: <string>, confidence: <low|medium|high>, source_analysis: <string>, opportunity: <string, optional>, consumed_by: <list>, drove_decision: <string, optional>, status: <open|consumed|parked|superseded>, owner: <string>`. Body sections: `## Insight`, `## Evidence`, `## Implication`, `## Follow-ups`.
- **`cto-os-data/modules/data-science/state/partnership.md`** — singleton (`slug: current`), overwrite-with-history. Frontmatter: `type: ds-product-partnership, slug: current, updated: <date>, operating_model: <embedded|hub-and-spoke|centralized|service-org>, supported_product_areas: <list>, intake_process: <string>, roadmap_sync_cadence: <string>, governance_owner: <string, optional>`. Body: prose documenting per-surface variance + `## History`.
- **`cto-os-data/modules/data-science/state/operating-cadence.md`** — singleton (`slug: current`), overwrite-with-history. Frontmatter: `type: ds-operating-cadence, slug: current, updated: <date>, practitioner_review: <object>, analytics_review: <object>, model_review: <object>, strategy_refresh: <object>`. Body: `## History`.

**Overrides to the cross-cutting save rule** ([Persistence model](../../docs/ARCHITECTURE.md#persistence-model)): none — inherits the default. Sensitivity is `standard`.

## State location

`cto-os-data/modules/data-science/state/`
