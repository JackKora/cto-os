---
name: personal-os
description: "Activates for personal operating-system work — the user's own goals, how they want to show up, their writing voice, personal retrospectives, and role altitude. Covers: setting or revising annual / quarterly / weekly goal cascades; defining or updating how the user wants to show up as a leader; capturing voice samples other comms modules will read; running weekly or ad-hoc personal retros. Also activates on oblique phrasings like 'what are my priorities this quarter,' 'I want to be the kind of leader who…,' 'let me reflect on this week,' or 'how am I actually showing up.' Does NOT activate on team-level goals (Team Management), team retros (Team Management), or stakeholder-facing work (Managing Up/Down/Sideways)."
requires: []
optional: []
---

# Personal Operating System

## Scope

The user's own operating system as a professional. How they think about where they're going, how they want to show up, and how they hold themselves accountable. Cascades long-term intent down to present-week actions. Serves as the canonical source of user-level context — altitude, goals, show-up definition, writing voice — that other modules consult via optional dependency.

## Out of scope

- **Team-aggregate goals and health** — Team Management.
- **1:1 notes and direct-report development** — Managing Down and Performance & Development.
- **External positioning and peer relationships** — External Network & Thought Leadership.
- **Career transitions between jobs** — this system is for on-the-job work, not between-jobs activities.

## Frameworks

- [OKRs — John Doerr, *Measure What Matters*](https://www.whatmatters.com/) — used for the annual / quarterly / weekly goal cascade. Objectives are qualitative and aspirational; key results are measurable outcomes.
  - *How this module applies it:* personal OKRs only — no team or company cascade. Use the aspirational flavor: stretch goals where ~70% attainment is "on track" and 100% means the target wasn't ambitious enough. OKRs here are not a self-evaluation tool; they're for direction-setting and weekly focus. The `items` field in `goal-horizon` state holds the Objectives at that horizon; Key Results live in the body next to each Objective (one line per KR, measurable).

- [4Ls retrospective format — Liked / Learned / Lacked / Longed for](https://www.retrium.com/retrospective-techniques/the-4ls) — used for personal retros.
  - *How this module applies it:* body always has four headings in order — `## Liked`, `## Learned`, `## Lacked`, `## Longed for`. "Longed for" is specifically what was absent (missing support, clarity, time, energy) — not general wishes. Unlike team 4Ls, skip consolidation and voting; this is single-user reflection.

Show-up definition and voice samples are user-defined intent, not external framework work — no citation.

## Triggers

Example user phrasings that should activate this module.

- "what are my priorities this quarter" / "let me set my annual goals"
- "I want to show up as…" / "how am I showing up" / "update how I want to show up"
- "let me reflect on this week" / "personal retro" / "weekly reflection"
- "add a voice sample" / "capture how I write"
- "what's my altitude" / "update my altitude"
- Oblique: "I don't feel like I'm focused on the right things" (goals drift)
- Oblique: "I was too reactive this week" (retro trigger)

## Activation flow

Running this flow populates baseline state that other modules depend on. Each step writes one concrete artifact; resumption is implicit (if the target file exists and matches **Expects**, the step is done).

### 1. Capture altitude

**Ask:** "What's your current role altitude? Director, VP, SVP, or C-level? Add a one-line note on what shape the role actually takes (e.g., P&L-owning CTO, hands-on-tech VPE, platform SVP)."
**Writes:** `cto-os-data/modules/personal-os/state/altitude.md` with `type: altitude`, `slug: current`, `level`, `context`.
**Expects:** frontmatter `level` is one of director / vp / svp / c-level and `context` is a non-empty one-liner.

### 2. Capture annual goals

**Ask:** "What are your top 3 annual goals for this year? Keep each to one sentence. These are the highest-altitude goals that everything else cascades from."
**Writes:** `cto-os-data/modules/personal-os/state/goals/annual.md` with `type: goal-horizon`, `slug: annual`, `horizon: annual`, `period` set to the current year (e.g., `"2026"`), `items` populated with 3 entries.
**Expects:** frontmatter `items` has 3 entries; `period` matches the current year.

### 3. Define how to show up

**Ask:** "How do you want to show up as a leader right now? Write one paragraph describing the posture you want others to experience, then list 3 concrete behaviors that live up to it, then 2 anti-patterns you fall into when you're at your worst. This will tune tone and framing across other modules."
**Writes:** `cto-os-data/modules/personal-os/state/show-up.md` with `type: show-up`, `slug: current`.
**Expects:** file exists with non-empty body containing the three parts (posture paragraph, behaviors list, anti-patterns list).

### 4. First voice sample

**Ask:** "Paste a chunk of writing that sounds like you — a Slack post, an email, a doc excerpt. Anything 100+ words in the voice you want other modules to emulate. Tell me the register (casual / formal-internal / board-facing / technical) and where it came from if you remember."
**Writes:** `cto-os-data/modules/personal-os/state/voice/{YYYY-MM-DD}.md` where `{YYYY-MM-DD}` is today. `type: voice-sample`, `register`, `source` (optional).
**Expects:** file exists with body length ≥ 100 words and `register` set.

Further voice samples, quarterly/weekly goal cascades, and retros are added post-activation via the runtime skills below.

## Skills

### `set-goals`

**Purpose:** Update goals at a specific horizon (annual, quarterly, or weekly). Writes to exactly one file — the one for that horizon. Preserves prior versions as history in that file's body.

**Triggers:**
- "update my annual goals"
- "set my quarterly priorities"
- "plan my week" / "what should I focus on this week"

**Reads:**
- `cto-os-data/modules/personal-os/state/goals/{horizon}.md` for the horizon being updated (current items)
- `cto-os-data/modules/personal-os/state/goals/` siblings when the user wants a cascade view before writing (e.g., "let me see annual before I set quarterly")
- `cto-os-data/modules/personal-os/state/altitude.md` (framing)

**Writes:** `cto-os-data/modules/personal-os/state/goals/{horizon}.md`, overwrite-with-history (append prior version as a dated snapshot in that file's body before writing the new frontmatter). Only the one horizon's file changes.

### `cascade-goals`

**Purpose:** Take one horizon's goals and generate a draft for the next horizon down. Annual → 3–5 quarterly objectives; quarterly → 2–3 weekly priorities. User reviews and commits via `set-goals`.

**Triggers:**
- "cascade my annual goals to this quarter"
- "break down this quarter into this week"
- "what should my Q2 goals be given my annual priorities"

**Reads:** `cto-os-data/modules/personal-os/state/goals/{source-horizon}.md` (the level being cascaded from).

**Writes:** `cto-os-data/modules/personal-os/state/goals/{target-horizon}.md`, via `set-goals` semantics after user confirmation.

### `show-cascade`

**Purpose:** Assemble a read-time cascade view across all three horizons. Read-only; no writes.

**Triggers:**
- "show my goal cascade"
- "what are all my priorities right now"

**Reads:** `scan(type=["goal-horizon"], where={"module": "personal-os"}, fields=["horizon", "period", "items", "updated"])` — frontmatter-only; skips the history in each file's body. Only add `include_body=true` if the user asks for history context alongside the current items.

**Writes:** —

### `log-retro`

**Purpose:** Capture a personal retro using the 4Ls format. Default cadence is weekly but the skill doesn't enforce one.

**Triggers:**
- "let me do a personal retro"
- "weekly reflection"
- "I want to reflect on this week / month / sprint"
- Oblique: "this was a weird week" (offer retro)

**Reads:**
- `cto-os-data/modules/personal-os/state/show-up.md` (for context; retros often compare actual behavior to stated intent)
- `cto-os-data/modules/personal-os/state/retros/` (recent retros, for trend visibility)

**Writes:** `cto-os-data/modules/personal-os/state/retros/{YYYY-MM-DD}.md`, append-new-file.

### `update-show-up`

**Purpose:** Revise the show-up definition. Prior versions are preserved in the body.

**Triggers:**
- "update how I want to show up"
- "refine my show-up"
- Oblique: "I've been thinking about what kind of leader I want to be" (offer update)

**Reads:** `cto-os-data/modules/personal-os/state/show-up.md`.

**Writes:** `cto-os-data/modules/personal-os/state/show-up.md`, overwrite-with-history.

### `add-voice-sample`

**Purpose:** Capture another sample of the user's writing voice. Samples stack over time; comms modules read the most recent per register.

**Triggers:**
- "add a voice sample"
- "here's something I wrote that sounds like me"
- "capture this writing voice"

**Reads:** —

**Writes:** `cto-os-data/modules/personal-os/state/voice/{YYYY-MM-DD}.md`, append-new-file. If a file for today already exists, use `{YYYY-MM-DD}-N.md` where `N` is the next integer.

## Persistence

Paths this module writes to. Every `**Writes:**` path in Skills above appears here.

- **`cto-os-data/modules/personal-os/state/altitude.md`** — overwrite, singleton (`slug: current`). Frontmatter: `type: altitude, slug: current, updated: <date>, level: <director|vp|svp|c-level>, context: <string>`. Body: free-form notes on what the altitude implies; not required.
- **`cto-os-data/modules/personal-os/state/goals/{annual|quarterly|weekly}.md`** — three files, one per horizon. Each overwrites independently, with prior versions preserved as reverse-chronological snapshots in its own body. Frontmatter: `type: goal-horizon, slug: <horizon>, updated: <date>, horizon: <horizon>, period: <string>, items: <list>`. Body: starts with `## History`; each snapshot is a `### <YYYY-MM-DD>` sub-heading with the items at that point. One horizon's file changes don't touch the other two — that's the whole point of splitting.
- **`cto-os-data/modules/personal-os/state/show-up.md`** — overwrite, with history in body. Frontmatter: `type: show-up, slug: current, updated: <date>`. Body: current definition (posture paragraph, behaviors list, anti-patterns list), followed by `## History` with dated prior versions.
- **`cto-os-data/modules/personal-os/state/voice/{YYYY-MM-DD}.md`** — append-new-file per sample. Frontmatter: `type: voice-sample, slug: <YYYY-MM-DD>, updated: <date>, register: <string>, source: <string|null>`. Body: the sample text verbatim.
- **`cto-os-data/modules/personal-os/state/retros/{YYYY-MM-DD}.md`** — append-new-file per retro. Frontmatter: `type: retro-personal, slug: <YYYY-MM-DD>, updated: <date>, period: <string>`. Body: four sections — `## Liked`, `## Learned`, `## Lacked`, `## Longed for`.

**Overrides to the cross-cutting save rule** ([Persistence model](../../docs/ARCHITECTURE.md#persistence-model)): none — inherits the default. Writes happen without blocking when the target is clear (activation answers, "set my goals," "log a retro"); ambiguity triggers a confirmation as normal.

## State location

`cto-os-data/modules/personal-os/state/`
