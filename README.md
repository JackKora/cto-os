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

- **Metrics everywhere, altitude-cadenced.** Individual weekly, team monthly, department quarterly, outcomes semi-annual or annual. Modules override when subject matter demands (Tech Ops SLOs are continuous). Each module picks the frameworks it applies; the universal principles are: measure what matters to the user, balance inputs and outputs, pair quantitative with qualitative, watch for metrics that look green while the underlying thing rots.
- **Rubric-based scoring.** For topics without clean quantitative metrics (architecture quality, team health, decision quality), modules use 5-point qualitative rubrics. Format standardized; criteria per-module. Scored as time series.
- **Feedback format.** Actionable, grounded in specific observed behavior, explicit about impact, suggesting what to do differently. Applied everywhere feedback is captured — 1:1s, peer feedback, incident learnings, retros.
- **Stakeholder profile format.** People-facing modules build lightweight profiles of the people they track. Observable preferences and behaviors only — no personality typologies. Fields: communication preferences, what they want first (numbers / stories / risks / options), typical concerns, context needs, known sensitivities, relationship status. Fields can be empty. Profiles evolve as observations accumulate.
- **Capture historic data.** Modules store history, not just current state — past goals, past decisions, past retros, past performance cycles, past board updates. Longitudinal questions stay answerable.
- **Story format.** A standard narrative template (context → action → outcome) used across every module that captures events, goals, or decisions. Lets state stay reusable across modules — a story captured in a 1:1 can feed a performance review; a decision captured once can be revisited later.
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

#### Personal

- [Personal Operating System](modules/personal-os/README.md) — foundational; canonical source for altitude, goals, show-up, voice, personal retros.

#### Operations

- [Attention & Operations](modules/attention-operations/README.md) — daily/weekly operational rhythm, inbox triage, morning briefings, week-starter and week-wrap.

### Planned — not yet implemented

Scope, frameworks, and dependencies for each planned module live in [docs/BACKLOG.md](docs/BACKLOG.md). Links below jump to the entry.

#### Stakeholder management

- [Managing Up](docs/BACKLOG.md#managing-up)
- [Managing Down](docs/BACKLOG.md#managing-down)
- [Managing Sideways](docs/BACKLOG.md#managing-sideways)

#### Personal

- [External Network & Thought Leadership](docs/BACKLOG.md#external-network)

#### Operations

- [Team Management](docs/BACKLOG.md#team-management)
- [Tech Ops](docs/BACKLOG.md#tech-ops)

#### Strategic

- [Org Design](docs/BACKLOG.md#org-design)
- [Process Management](docs/BACKLOG.md#process-management)
- [Business Alignment](docs/BACKLOG.md#business-alignment)
- [Technical Strategy](docs/BACKLOG.md#technical-strategy)

#### Communication

- [Organizational Communications](docs/BACKLOG.md#org-comms)
- [Board Comms](docs/BACKLOG.md#board-comms)

#### People & execution

- [Hiring](docs/BACKLOG.md#hiring)
- [Performance & Development](docs/BACKLOG.md#performance-development)
- [Code Contribution Opportunities](docs/BACKLOG.md#code-contribution)

#### Governance

- [Security & Compliance](docs/BACKLOG.md#security-compliance)
- [Budget](docs/BACKLOG.md#budget)

---

## Surfaces

CTO OS runs on three different Claude surfaces. You use them for different things.

**Chat (Claude Desktop).** The interactive app. Best for ad-hoc questions — "what's on my plate today," "help me think through this reorg," "draft a note to my boss" — quick triage, weekly reviews, and anything that benefits from back-and-forth conversation.

**Code (Claude Code CLI).** The command-line tool, launched from a terminal. Good for two kinds of work.

- Bulk changes to the skill itself — authoring new modules, restructuring existing ones, schema migrations, or anything that involves editing many files at once.
- Day-to-day use of the skill when you want a longer, more focused session. **Launch Code from your `cto-os-data` directory, not the `cto-os` source repo** — that's what tells Claude to activate the skill for managing your state rather than working on the system itself (`cd ~/cto-os-data && claude`). Advantages over Chat: unlimited conversation length (no running out of context mid-flow), direct file access (no MCP roundtrip), the ability to work with git / grep / your editor alongside Claude, and easier handling of multi-step work that persists across days. Worth reaching for when you're doing reflective work (weekly review, quarter planning), drafting longer artifacts (board update, strategy memo), or want uninterrupted time to think through a problem.

**Cowork.** Runs tasks on a schedule, in the background, without you watching. Best for morning briefings, pre-meeting prep that lands in your inbox, overnight digests, weekly wraps — anything that benefits from arriving before you ask for it.

All three read and write the same state on your laptop — your `cto-os-data` directory. There's no copying between surfaces; same disk, same files. Edits made in one surface are immediately visible in the others.

Under the hood, Chat reaches your files through a local MCP server (a small translation layer that starts with Claude Desktop). Code and Cowork access the filesystem directly. Same state, same results — just two different mechanisms. You don't need to think about this day-to-day.

---

## Your data

Your state lives in a single directory on your laptop — `~/cto-os-data` by default, configurable via the `CTO_OS_DATA` environment variable at install time. Every module writes there, and nothing outside CTO OS touches it.

**Completely separate from the app.** The `cto-os` repo (this one) is code — same for every user, public or shared. Your data repo is yours only. You upgrade the app with `git pull` on `cto-os`; your data stays untouched. You can delete the app entirely and your data is still a complete, human-readable record — just without the tooling to query it efficiently.

### Backup

**Daily git commits are the baseline.**

`cto-os-data` is already a git repo (install does `git init`). Set up a Cowork task or cron job that runs the following in that directory once a day:

```bash
git add -A && git commit -m "auto" || true
```

This gives you per-change history as a side effect of using the system: every state write becomes a commit you can inspect, diff, or roll back. Without it, a fat-fingered `rm` or a bad write can't be recovered.

**Then pick an offsite strategy on top of that.** The daily commit buys versioning; offsite is about surviving laptop loss.

- **Push to a private git remote.** Extend the daily task: `git add -A && git commit -m "auto" && git push`. Private repo only (GitHub, GitLab, Bitbucket), 2FA enforced. Versioning + offsite in one command.
- **Sync the directory to a cloud drive.** Put `cto-os-data` inside a Google Drive / iCloud / Dropbox synced folder, or symlink it there. The `.git/` directory comes along automatically, so you keep local versioning; the provider gives you offsite. Simpler than managing a git remote — but read the sensitivity note below first.

You can do both; they don't conflict.

### ⚠️ This directory likely contains highly sensitive material

> **Treat `cto-os-data` like your most sensitive work document.** 1:1 notes, performance records, board-level material, candid peer feedback, strategic decisions, commentary on stakeholders.
>
> - **Never push to a public repo.** Ever. Private remote with 2FA enforced is the minimum bar for git-based backup.
> - **Be thoughtful with cloud sync.** Providers can be subpoenaed, accounts can be compromised, shared folders can leak. If you're uncomfortable with the offsite options for a particular category of content, keeping `cto-os-data` local-only (daily commits without push or cloud sync) is a legitimate choice — you lose laptop-failure resilience but you gain total isolation.
> - **Modules flag their own sensitive subtrees** with `sensitivity: high`. Scan excludes those by default — a query has to opt in to see them. Defense in depth, not encryption.
> - **No secrets in the data repo either.** API keys, tokens, passwords live in macOS Keychain or a gitignored `.env`, never in a module's state.

---

## Where to go deeper

- [CLAUDE.md](CLAUDE.md) — conventions for editing this repo.
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — system-wide architecture.
- [docs/SKILL_REPO.md](docs/SKILL_REPO.md) — this repo deep dive (MCP, scripts, scan, schema).
- [docs/MCP_TOOLS.md](docs/MCP_TOOLS.md) — canonical MCP tool contracts.
- [docs/SCRIPTS.md](docs/SCRIPTS.md) — deterministic-script inventory and contract.
- [docs/DATA_REPO.md](docs/DATA_REPO.md) — data repo deep dive.
- [docs/BACKLOG.md](docs/BACKLOG.md) — scope for modules not yet implemented.
