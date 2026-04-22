# cto-os

The logic side of CTO OS — a personal operating system for a senior engineering leader.

This repo holds the skill definitions, deterministic scripts, MCP server, canonical schema, and templates. It is paired with a separate private repo (`cto-os-data`) that holds user state.

## What CTO OS is

A composable set of modules — stakeholder management, team management, technical strategy, business alignment, hiring, board comms, and more — that run on top of Claude to help a senior engineering leader (Director / VP / SVP / C-level) manage their people, technology, communication, and decisions. Each module is a focused capability with its own framework and skills. Modules share state and read each other's context. The system is altitude-aware, values-driven, and frameworks-first.

## Install

See [install.sh](install.sh). Requires macOS or Linux, git, Python 3.13+, and [uv](https://docs.astral.sh/uv/).

```bash
./install.sh              # interactive
./install.sh --yes        # accept defaults
./install.sh --help
```

Install creates a `.venv` at the repo root via `uv sync` and points Claude Desktop at that venv's Python. For dev / direct script invocation from Code or Cowork, run `uv run python scripts/<name>.py --args '{...}'` from the repo root.

Details: [CLAUDE.md](CLAUDE.md), [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

---

## Design principles

The "why" — these inform every module decision.

- **It's a system, not a set of standalone skills.** Modules are complementary and connected.
- **Senior leadership thinking, altitude-configurable.** Director / VP / SVP / C-level captured at activation. Horizon length, abstraction, and stakeholder scope shift with altitude; underlying behaviors (push thinking up, altitude-aware, frameworks-first) are universal.
- **Business-first by default.** Sales, marketing, support, compliance, customers — all in scope. Tech-centric framing is permitted where the subject matter demands (Security & Compliance, Tech Ops, Technical Strategy, SDLC) but doesn't bleed into business-first modules.
- **"How you want to show up" is the north star.** Stated intent in Personal OS drives behavior across modules.
- **Acts as an executive coach**, not just a task executor. Pushes thinking to higher altitudes, challenges reasoning, surfaces assumptions, asks pointed questions.
- **Role- and industry-adaptive.** Leans on durable frameworks over job titles and process names — both change across jobs and over time.
- **Modules own their skills.** Each module contains specific named tasks (e.g., "draft a performance review," "scan email and summarize"). Skills evolve; modules surface them proactively when context warrants.
- **Frameworks-first, per module.** The right framework is chosen when a module is built and lives inside that module. No shared frameworks library.

## Values

Eight values, in tension by design. Applied as an evaluation lens; resolving tensions case-by-case with sound judgment is the art.

- **Start with the user.** Work backwards from their needs — external (customers) or internal (your devops users are your app devs).
- **Act like an owner.** Think long-term. Act on behalf of the whole company, not just your team. Never say "that's not my job."
- **Learn and be curious.** Never stop learning. Seek diverse perspectives. Work to disconfirm your own beliefs.
- **Raise the bar.** Care about craft. Fix problems so they stay fixed; don't let defects pass down the line.
- **Leave ego at the door.** Mission over rightness. Quick to lend a hand, slow to point a finger. No fiefdoms, no "not my problem."
- **Move with urgency.** Most decisions are reversible. Take calculated risks. Focus on what matters and move.
- **Play on one team.** No us-vs-them between departments or functions. For managers: your team is your peer group of other leaders, not your direct reports — your reports are the team you *serve* (see [Andy Grove, *High Output Management*](https://www.amazon.com/High-Output-Management-Andrew-Grove/dp/0679762884)).
- **Be candid.** Share context openly. Give feedback grounded in specific observed behavior. Care personally, challenge directly (see [Kim Scott, *Radical Candor*](https://www.amazon.com/Radical-Candor-Revised-Kick-Ass-Humanity/dp/1250235375)).

The system surfaces value tensions explicitly rather than smoothing them over. Example tensions:

- *Move with urgency* ↔ *Raise the bar* — ship the working patch today, or hold a day to properly address the root cause?
- *Be candid* ↔ *Leave ego at the door* — call out a peer's flawed plan in the room, or pull them aside afterward?

## Cross-cutting patterns

Applied across all modules.

- **Metrics everywhere, altitude-cadenced.** Individual-level weekly, team monthly, department quarterly, outcomes semi-annual or annual. Modules override when subject matter demands (Tech Ops SLOs are continuous). Metric design follows [DORA](https://dora.dev/), [SPACE](https://queue.acm.org/detail.cfm?id=3454124), and [*Working Backwards*](https://www.amazon.com/Working-Backwards-Insights-Stories-Secrets/dp/1250267595): measure what matters to the user; pick a balanced basket, not a single metric; distinguish inputs from outputs; pair quantitative with qualitative; watch for [watermelon metrics](https://www.callcentrehelper.com/beware-of-watermelon-metrics-205604.htm) and gaming. See [*How to Measure Anything*](https://www.amazon.com/How-Measure-Anything-Intangibles-Business/dp/1118539273) (Hubbard) on measuring intangibles.
- **Rubric-based scoring.** For topics without clean quantitative metrics (architecture quality, team health, decision quality), modules use 5-point qualitative rubrics. Format standardized; criteria per-module. Scored as time series.
- **Feedback format.** Actionable, grounded in specific observed behavior, explicit about impact, suggesting what to do differently. Applied everywhere feedback is captured — 1:1s, peer feedback, incident learnings, retros.
- **Stakeholder profile format.** People-facing modules build lightweight profiles of the people they track. Observable preferences and behaviors only — no personality typologies. Fields: communication preferences, what they want first (numbers / stories / risks / options), typical concerns, context needs, known sensitivities, relationship status. Fields can be empty. Profiles evolve as observations accumulate.
- **Capture historic data.** Modules store history, not just current state — past goals, past decisions, past retros, past performance cycles, past board updates. Longitudinal questions stay answerable.
- **Story format.** Borrowed from [interview-coach-skill](https://github.com/JackKora/interview-coach-skill). Used to capture events, goals, decisions.
- **Decision capture.** Context, options considered, choice made, rationale, review date. Applied per module to its own decisions — no standalone decision log.
- **Retrospective format.** Shared structure across modules (team retros, incident retros, project retros, personal retros).
- **Writing voice.** User-provided samples. Owned by Personal OS; read by comms-generating modules via optional dependency.

## System properties

- **Modularity** — activate / deactivate without breaking neighbors.
- **Portability** — works across employers as role and process specifics change.
- **Extensibility** — new modules, skills, and frameworks plug in cleanly.
- **Discoverability** — the system helps the user find the right skill at the right time.
- **Coherence** — modules feel like parts of one system, not a skill grab-bag.

## Activation order

Recommended sequence when first adopting.

1. **Foundations.** Personal OS, Process Management, Business Alignment — the three zero-outbound-dependency modules. They don't block on anything and unlock the most downstream capability.
2. **Daily drivers.** Attention & Operations, Team Management, one or more of Managing Up / Down / Sideways depending on role. High operational value, low dependency cost.
3. **Role-shape modules.** Match the shape of the specific job — Tech Ops and Technical Strategy for hands-on-tech CTOs, Hiring for growth-phase orgs, Budget for P&L-owning roles, Customer Engagement (under Business Alignment) for customer-facing CTOs.
4. **Strategic and periodic.** Org Design, Performance & Development, Board Comms. Low-frequency, high-leverage. Activate once daily drivers are steady.
5. **Optional by role.** External Network & Thought Leadership, Code Contribution Opportunities, Security & Compliance.

---

## Modules

### Implemented

- [Personal Operating System](modules/personal-os/README.md) — foundational; canonical source for altitude, goals, show-up, voice, personal retros.

### Planned — not yet implemented

Links resolve as each module lands.

#### Stakeholder management

- [Managing Up](modules/managing-up/README.md)
- [Managing Down](modules/managing-down/README.md)
- [Managing Sideways](modules/managing-sideways/README.md)

#### Personal

- [External Network & Thought Leadership](modules/external-network/README.md)

#### Operations

- [Attention & Operations](modules/attention-operations/README.md)
- [Team Management](modules/team-management/README.md)
- [Tech Ops](modules/tech-ops/README.md)

#### Strategic

- [Org Design](modules/org-design/README.md)
- [Process Management](modules/process-management/README.md)
- [Business Alignment](modules/business-alignment/README.md)
- [Technical Strategy](modules/technical-strategy/README.md)

#### Communication

- [Organizational Communications](modules/org-comms/README.md)
- [Board Comms](modules/board-comms/README.md)

#### People & execution

- [Hiring](modules/hiring/README.md)
- [Performance & Development](modules/performance-development/README.md)
- [Code Contribution Opportunities](modules/code-contribution/README.md)

#### Governance

- [Security & Compliance](modules/security-compliance/README.md)
- [Budget](modules/budget/README.md)

### Authoring a new module

Start from the skeletons at [`templates/module-SKILL.md`](templates/module-SKILL.md) and [`templates/module-README.md`](templates/module-README.md). Format spec: [docs/SKILL_REPO.md → Per-module SKILL.md format](docs/SKILL_REPO.md#per-module-skillmd-format). Schema to validate against: [meta/schema.md](meta/schema.md).

---

## Scripts

All scripts live in `scripts/`. **Currently stubs** (empty placeholders); contracts and guardrails documented in [docs/SKILL_REPO.md](docs/SKILL_REPO.md).

- `scan.py` — frontmatter scan + filter over all of `cto-os-data` in one call. Supports `include_body` for narrow lookups.
- `roll_up.py` — on-demand rollups (teams, projects, people).
- `pull_slack.py` — Slack API → integrations cache.
- `pull_linear.py` — Linear GraphQL → integrations cache.
- `validate_deps.py` — build required-dependency DAG; fail on cycles.
- `rename_module.py` — rename slug in lockstep across skill + data repos.
- `migrate_{slug}_v{N}_to_v{N+1}.py` — per-module schema migrations.

---

## Where to go deeper

- [CLAUDE.md](CLAUDE.md) — conventions for editing this repo.
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — system-wide architecture.
- [docs/SKILL_REPO.md](docs/SKILL_REPO.md) — this repo deep dive (MCP, scripts, scan, schema).
- [docs/MCP_TOOLS.md](docs/MCP_TOOLS.md) — canonical MCP tool contracts.
- [docs/DATA_REPO.md](docs/DATA_REPO.md) — data repo deep dive.
