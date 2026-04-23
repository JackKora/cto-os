---
name: attention-operations
description: "Activates for daily and weekly operational rhythm, inbox triage, and attention management — separating what needs response from FYI across Slack, email, Linear, and PR activity. Covers: morning briefings (what happened since yesterday, what's on today), week-starter (Monday look-forward), week-wrap (Friday look-back), inbox triage (attention-needed vs FYI classification), catch-up after time away. Also activates on oblique phrasings like 'what did I miss,' 'what's on my plate,' 'catch me up,' 'did anything happen overnight,' 'help me process my inbox,' 'my inbox is a mess.' Does NOT activate on team-level operations (Team Management), incident response (Tech Ops), personal reflection or goal-setting (Personal OS), or individual performance (Performance & Development)."
requires: []
optional:
  - personal-os
---

# Attention & Operations

## Scope

The user's daily and weekly operational rhythm. Filters incoming signal across Slack, email, Linear, and PR activity to separate attention-needed from FYI. Maintains situational awareness on what happened, what's on today, and what's coming this week. Produces three recurring artifacts: morning briefing, week-starter (Monday), week-wrap (Friday).

## Out of scope

- **Personal reflection, goals, show-up, voice** — Personal OS.
- **Team-aggregate operations and health** — Team Management.
- **Incident response and production reliability** — Tech Ops.
- **Individual performance tracking** — Performance & Development.
- **Strategic communication (board, org-wide)** — Board Comms, Org Comms.

## Frameworks

- [GTD — David Allen, *Getting Things Done*](https://gettingthingsdone.com/) — the foundational five-step workflow (capture → clarify → organize → reflect → engage).
  - *How this module applies it:* inbox triage implements the "clarify" step — every item resolves to attention-needed or FYI, full stop. Skip the 2-minute rule, sub-categories, and persistent next-action lists; items that become attention-needed escalate to the user directly. Weekly rhythm implements "reflect" — split into two events (week-starter Monday, week-wrap Friday) because a single weekly review conflates look-forward and look-back work that benefit from separation.

- [Eisenhower Matrix (urgent vs important)](https://en.wikipedia.org/wiki/Time_management#The_Eisenhower_Method) — prioritization frame.
  - *How this module applies it:* used only when triage surfaces more than ~5 attention-needed items in one pass. Tag them urgent / important / both / neither as a tiebreaker. Don't force categorization on every item — most are obviously one thing.

## Triggers

- "what did I miss" / "catch me up" / "give me a briefing"
- "morning briefing" / "daily briefing" / "daily catchup"
- "week-starter" / "Monday briefing" / "what's on for this week"
- "week-wrap" / "Friday summary" / "what shipped this week"
- "help me process my inbox" / "inbox triage" / "triage my Slack"
- "attention needed?" / "is this FYI or something I should respond to"
- Oblique: "I was out for a few days — catch me up"
- Oblique: "my inbox is a mess" / "I have 200 unread messages"
- Oblique: "what should I be focused on right now" (when framed operationally — goal-framing routes to Personal OS)

## Activation flow

Each step writes one concrete artifact and adds its step number to `activation_completed` in `_module.md`.

### 1. Declare rhythm preferences

**Ask:** "Walk me through your daily and weekly rhythm. When do you start your day? Do you want a morning briefing delivered asynchronously (via Cowork on a schedule) or on-demand? Do you want both a Monday week-starter and a Friday week-wrap, or just one? Any surfaces you want prioritized — Slack DMs over channels, email over Linear, PRs you're author/reviewer on over repo-wide?"
**Writes:** `cto-os-data/modules/attention-operations/state/rhythm.md` with `type: rhythm`, `slug: current`, `daily_mode`, `weekly_events`, `priority_order`.
**Expects:** frontmatter has `daily_mode` set, `weekly_events` is a non-empty list, `priority_order` is a non-empty list.

### 2. Capture baseline triage rules

**Ask:** "What patterns do you already know? Examples: recruiter emails are FYI unless I'm actively searching; messages from my boss are attention-needed; DMs from direct reports depend on keywords; mentions in #alerts channel are attention-needed. Give me 5–10 pattern→category rules to start with. These evolve — the module refines them as it learns."
**Writes:** `cto-os-data/modules/attention-operations/state/triage-rules.md` with `type: triage-rules`, `slug: current`, `rules` list in frontmatter.
**Expects:** frontmatter `rules` has ≥ 3 entries, each with `pattern` (string) and `category` (attention-needed | fyi) and optional `condition`.

### 3. Declare integration sources

**Ask:** "Which integration sources should I read from for briefings and triage? For each, scope it down: which Slack workspace(s) and channels, which Gmail address(es) and label/folder scope, which Linear workspace. Saying 'all DMs but only specific channels' is fine."
**Writes:** `cto-os-data/modules/attention-operations/state/sources.md` with `type: attention-sources`, `slug: current`, `sources` list.
**Expects:** frontmatter `sources` has ≥ 1 entry with `kind` (slack | gmail | linear | other), `identifier`, and `scope` description.

## Skills

### `morning-briefing`

**Purpose:** Generate today's daily briefing — what happened since the last briefing, what's on today, open threads that need attention.

**Triggers:**
- "morning briefing" / "give me a briefing"
- "what did I miss overnight"
- "catch me up on today"

**Reads:**
- `cto-os-data/modules/attention-operations/state/rhythm.md` (user's declared cadence and priorities)
- `cto-os-data/modules/attention-operations/state/triage-rules.md` (classification)
- `cto-os-data/modules/attention-operations/state/sources.md` (which integrations to pull from)
- `cto-os-data/modules/attention-operations/state/briefings/` (yesterday's briefing, for "since last" delta)
- `cto-os-data/integrations-cache/slack/`, `cto-os-data/integrations-cache/gmail/`, `cto-os-data/integrations-cache/linear/` (raw signal)
- Personal OS (optional) — `cto-os-data/modules/personal-os/state/goals/weekly.md` to frame priority filtering

**Writes:** `cto-os-data/modules/attention-operations/state/briefings/{YYYY-MM-DD}.md`, append-new-file.

### `week-starter`

**Purpose:** Monday look-forward. What's on the calendar this week, key decisions coming up, open threads from last week still alive, this week's top 2–3 priorities.

**Triggers:**
- "week-starter" / "Monday briefing"
- "what's on for this week"
- "plan my week" (operational framing — goal-setting framing routes to Personal OS `set-goals`)

**Reads:**
- `cto-os-data/modules/attention-operations/state/weekly/` (last Friday's wrap, for carry-over)
- `cto-os-data/modules/attention-operations/state/briefings/` (recent daily context)
- `cto-os-data/modules/attention-operations/state/sources.md`
- Personal OS (optional) — `cto-os-data/modules/personal-os/state/goals/weekly.md` and `goals/quarterly.md` for intent framing

**Writes:** `cto-os-data/modules/attention-operations/state/weekly/{YYYY-W##}-starter.md`, append-new-file.

### `week-wrap`

**Purpose:** Friday look-back. What shipped, what decisions were made, what's carrying over, open items to pick up Monday.

**Triggers:**
- "week-wrap" / "Friday summary"
- "what shipped this week"
- "wrap up the week"

**Reads:**
- `cto-os-data/modules/attention-operations/state/briefings/` (this week's daily briefings for raw material)
- `cto-os-data/modules/attention-operations/state/weekly/{YYYY-W##}-starter.md` (for delta vs plan)
- `cto-os-data/integrations-cache/linear/` (shipped tickets, merged PRs)

**Writes:** `cto-os-data/modules/attention-operations/state/weekly/{YYYY-W##}-wrap.md`, append-new-file.

### `triage-inbox`

**Purpose:** Walk the user through unread/unprocessed items across declared sources, classify each as attention-needed or FYI, surface the attention-needed set for action.

**Triggers:**
- "help me process my inbox" / "inbox triage"
- "triage my Slack" / "triage my email"
- "my inbox is a mess"

**Reads:**
- `cto-os-data/modules/attention-operations/state/triage-rules.md` (apply first)
- `cto-os-data/modules/attention-operations/state/sources.md` (scope)
- `cto-os-data/integrations-cache/` (raw unread items)
- Personal OS (optional) — `cto-os-data/modules/personal-os/state/show-up.md` and `goals/weekly.md` to bias classification toward stated intent

**Writes:** — (no persistent output; classifications are ephemeral and surfaced to the user. If the triage produces a new rule the user wants to capture, route through `update-triage-rules`.)

### `update-triage-rules`

**Purpose:** Add, modify, or remove rules in the triage ruleset. Invoked when the user notices a systematic miscategorization during triage, or when their context shifts (e.g., starting an active job search).

**Triggers:**
- "add a triage rule"
- "update my triage rules"
- "recruiter emails should now be attention-needed" (example of in-flight rule update)

**Reads:** `cto-os-data/modules/attention-operations/state/triage-rules.md`.

**Writes:** `cto-os-data/modules/attention-operations/state/triage-rules.md`, overwrite-with-history.

### `update-rhythm`

**Purpose:** Revise declared daily/weekly rhythm preferences.

**Triggers:**
- "change my rhythm" / "update my briefing schedule"
- "I'm going to stop doing Monday briefings"
- "switch morning briefing from async to on-demand"

**Reads:** `cto-os-data/modules/attention-operations/state/rhythm.md`.

**Writes:** `cto-os-data/modules/attention-operations/state/rhythm.md`, overwrite-with-history.

### `update-sources`

**Purpose:** Add or remove integration sources, or change scope within a source (e.g., add a new Slack channel, narrow Gmail scope to Primary).

**Triggers:**
- "add Slack channel X to my sources"
- "stop reading my personal Gmail in briefings"
- "I have a new Linear workspace, add it"

**Reads:** `cto-os-data/modules/attention-operations/state/sources.md`.

**Writes:** `cto-os-data/modules/attention-operations/state/sources.md`, overwrite-with-history.

## Persistence

- **`cto-os-data/modules/attention-operations/state/briefings/{YYYY-MM-DD}.md`** — append-new-file per day. Frontmatter: `type: daily-briefing, slug: <YYYY-MM-DD>, updated: <date>`. Body sections: `## Since last`, `## Today`, `## Open threads`. References but does not inline content from sensitive modules.
- **`cto-os-data/modules/attention-operations/state/weekly/{YYYY-W##}-starter.md`** — append-new-file per week. Frontmatter: `type: weekly-starter, slug: <YYYY-W##>-starter, updated: <date>, period: <YYYY-W##>`. Body sections: `## Priorities`, `## Key meetings`, `## Decisions coming up`, `## Carry-over`.
- **`cto-os-data/modules/attention-operations/state/weekly/{YYYY-W##}-wrap.md`** — append-new-file per week. Frontmatter: `type: weekly-wrap, slug: <YYYY-W##>-wrap, updated: <date>, period: <YYYY-W##>`. Body sections: `## Shipped`, `## Decisions made`, `## Carry-over to next week`, `## Open items`.
- **`cto-os-data/modules/attention-operations/state/rhythm.md`** — overwrite, singleton (`slug: current`), with history in body. Frontmatter: `type: rhythm, slug: current, updated: <date>, daily_mode: <async|on-demand>, weekly_events: <list>, priority_order: <list>`. Body: optional prose notes + `## History`.
- **`cto-os-data/modules/attention-operations/state/triage-rules.md`** — overwrite, singleton (`slug: current`), with history in body. Frontmatter: `type: triage-rules, slug: current, updated: <date>, rules: <list of {pattern, category, condition?}>`. Body: optional prose rationale + `## History`.
- **`cto-os-data/modules/attention-operations/state/sources.md`** — overwrite, singleton (`slug: current`), with history in body. Frontmatter: `type: attention-sources, slug: current, updated: <date>, sources: <list of {kind, identifier, scope}>`. Body: optional prose + `## History`.

**Overrides to the cross-cutting save rule** ([Persistence model](../../docs/ARCHITECTURE.md#persistence-model)): none — inherits the default. Briefings, starters, and wraps save without blocking when generated (the user asked for one). Triage rule changes ask for confirmation if the user's phrasing was exploratory ("maybe recruiter emails should be…") rather than declarative.

**Sensitivity note:** default inherits `standard`. Briefings reference (by path) but do not inline content from modules marked `sensitivity: high` — they link to 1:1 notes, performance files, and board material rather than reproducing them. User can set `sensitivity: high` on this module's `_module.md` during activation to further restrict cross-module inclusion.

## State location

`cto-os-data/modules/attention-operations/state/`
