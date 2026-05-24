# Data Science

**Scope:** The substance of the data-science function — strategy (Rumelt kernel), DS goals (cascaded from company goals), DS initiative lifecycle (discovery → validated → in-flight → shipped | killed), structured experiments (Kohavi-style: hypothesis / design / metric / result / decision), ML evals (model output quality on labeled / golden / human-rated sets per Husain & Shankar), model registry (training → staging → production → retired), insights with explicit consumed-by tracking (the loop-closure Peter Deng flagged), DS-product partnership operating model (embedded / hub-and-spoke / centralized / service-org), and operating cadence (practitioner review / analytics review / model review / strategy refresh).

**Out of scope:** DS flow metrics like cycle time and WIP (Process Management, `flow_type: ds`); model-serving SLOs, inference incidents, postmortems (Tech Ops); ML architecture or platform ADRs (Technical Strategy); DS-IC 1:1s and team comms (Managing Down); DS performance reviews / calibration / promotions / PIPs (Performance & Development); DS hiring (Hiring); DS team rubric (Team Management — generic works); where DS reports as an org-design call (Org Design — this module captures the operating reality, not the decision); MLOps tooling internals (Technical Strategy ADRs); data quality / data tech-debt (Technical Strategy `tech-debt-item` with `area: data` for v1); DS roadmap as a now/next/later band layer (deliberately omitted — DS work is experiment-driven, captured via goals + initiatives + experiments).

**Frameworks:** [Richard Rumelt — *Good Strategy, Bad Strategy*](https://www.amazon.com/Good-Strategy-Bad-Difference-Matters/dp/0307886239), [Ronny Kohavi — *Trustworthy Online Controlled Experiments*](https://experimentguide.com/), [Hamel Husain & Shreya Shankar — AI evals](https://hamel.dev/blog/posts/evals/), [Teresa Torres — *Continuous Discovery Habits*](https://www.producttalk.org/continuous-discovery-habits/), hub-and-spoke operating model ([Atlan](https://atlan.com/know/centralized-vs-federated-data-teams-in-the-ai-era/), [Sigma](https://www.sigmacomputing.com/blog/data-org-dilemma)). Module spine: Ravi Mehta's hierarchy adapted for DS (company mission → company strategy → DS strategy → DS goals → DS initiatives → experiments / evals / models / insights).

**Depends on:**
- Required: none (foundational on the DS side)
- Optional: business-alignment, process-management, technical-strategy, tech-ops, product, managing-down, personal-os

**Example tasks:**
- "Activate the data-science module and walk me through current strategy, goals, and models."
- "Log an experiment — we're running an A/B on the new alert ranker."
- "Eval the new safety classifier on the September golden set."
- "Register the v2 alert-prioritizer model in staging."
- "Promote the alert-prioritizer to production."
- "Log an insight — the dashboard shows district-admin users open Alerts 3x more than IT users."
- "Consume that insight — exec staff used it to greenlight the new prioritization push."
- "Prep for the DS review with [IC]."
- "Show me the insight pipeline — any orphans?"
- "We're moving from centralized DS to hub-and-spoke; update the partnership model."

**State location:** `cto-os-data/modules/data-science/state/`
