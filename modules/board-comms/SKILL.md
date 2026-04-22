---
name: board-comms
description: "Activates for board-level strategic communication — quarterly board updates, pre-read memos for upcoming meetings, post-meeting capture of decisions and feedback, and the ongoing narrative across meetings. Covers: composing the CTO section of a board update by pulling from Business Alignment (company goals), Process Management (flow KPIs), Tech Ops (material incidents), Security & Compliance (material risks), Hiring (exec-level changes), and Budget (financial posture); authoring topic-specific pre-reads (risk briefing, fundraising narrative, M&A analysis); capturing what happens at the meeting itself (director feedback, decisions, follow-ups). Also activates on oblique phrasings like 'draft the CTO section for Q2 board,' 'write the pre-read on [topic],' 'capture yesterday's board meeting,' 'risk briefing for the board,' 'update board structure — new director joined.' Does NOT activate on operational internal comms (Org Comms); peer CTO or external-investor relationships outside board meetings (External Network & Thought Leadership); or investor day / all-hands-style content for broader audiences (Org Comms)."
requires:
  - business-alignment
  - process-management
optional:
  - tech-ops
  - security-compliance
  - hiring
  - budget
  - personal-os
---

# Board Comms

## Scope

Strategic narrative at the highest altitude — where the business is, where it's going, what's changing, what the risks are. Composes the quarterly board update and its pre-reads by pulling from other modules' state. Captures what happens *at* board meetings — director feedback, decisions, follow-ups — so the narrative has continuity across quarters.

Strategic and periodic module — most of the work is concentrated around meeting cycles.

## Out of scope

- **Operational internal communications** — Org Comms.
- **External investor relationships outside board meetings** — External Network & Thought Leadership.
- **All-hands content for broader internal audiences** — Org Comms.
- **Peer CTO relationships** — External Network & Thought Leadership.
- **Day-to-day updates to exec team** — Managing Up (for your direct manager) or Managing Sideways (peers).

## Frameworks

- [Brad Feld & Mahendra Ramsinghani — *Startup Boards*](https://feld.com/category/books/startup-boards/) — board-director perspective on what directors actually want from a functional CTO update.
  - *How this module applies it:* Feld's frame anchors what a board update is *for* — helping directors fulfill their fiduciary duty, spotting risks early, supporting the CEO strategically. Not a status report. Draft updates here de-emphasize "what we shipped" and emphasize "what's changed, what's at risk, what's the ask." Directors want context for hard questions; this module's output is shaped to give them that.

- [Amazon narrative format / 6-pager](https://www.amazon.com/Working-Backwards-Insights-Stories-Secrets/dp/1250267595) — argument-first prose structure for board pre-reads.
  - *How this module applies it:* pre-reads follow the Amazon 6-pager discipline: open with the answer, then context, then detail. No slides; no bullet-dump. Board updates themselves can be more structured (sections) but each section leads with the answer. Body-first not appendix-first — if a section needs 3 paragraphs to explain the current state, the executive summary goes up top.

## Triggers

- "draft the CTO section for [Q#] board update"
- "write the pre-read on [topic]"
- "risk briefing for next board meeting"
- "fundraising narrative for [round]"
- "log yesterday's board meeting"
- "capture board feedback from [meeting]"
- "update board structure — [name] joined / left / new observer"
- "revise the board update template"
- "backfill last [N] board meetings into the module"
- Oblique: "I need to tell the board about [material event]"
- Oblique: "prep me for Thursday's board meeting"

## Activation flow

Each step writes a concrete artifact and appends its step number to `activation_completed` in `_module.md`.

### 1. Declare board structure

**Ask:** "Walk me through the board. Directors (name, role — chair, lead-independent, investor-director, etc.), observers if any, meeting cadence (typically quarterly; some boards meet monthly during rapid change), and any standing committees (audit, comp, etc.). What's the usual pre-read deadline before a meeting — 3 days? A week? Any materials-format norms (deck expected, narrative preferred, hybrid)?"
**Writes:** `cto-os-data/modules/board-comms/state/board-structure.md` with `type: board-structure`, `slug: current`, `directors`, `observers`, `cadence`, `pre_read_lead_time`, `materials_format`, `committees`.
**Expects:** frontmatter has `directors` list ≥ 1 entry, `cadence`, and `pre_read_lead_time` set.

### 2. Declare the update template

**Ask:** "What's the structure of the CTO section in your standard board update? Typical sections: company-level context, engineering-org state, reliability / material incidents, strategic initiatives & decisions, team and hiring posture, financial / budget posture, risks, asks of the board. Which of these apply, what's the order, what's the target length per section? If you don't have a template yet, we'll seed with a reasonable default and refine."
**Writes:** `cto-os-data/modules/board-comms/state/update-template.md` with `type: board-update-template`, `slug: current`, `sections`, `target_length_words`, `tone_notes`.
**Expects:** frontmatter `sections` has ≥ 3 entries.

Historical backfill (prior board meetings and updates) happens post-activation via the `backfill-history` skill — not mandatory for the module to be useful.

## Skills

### `update-board-structure`

**Purpose:** Revise declared board structure — new director, departure, cadence change, new committee.

**Triggers:**
- "update board structure"
- "[name] joined the board as a director"
- "cadence shifted from quarterly to monthly"

**Reads:** `cto-os-data/modules/board-comms/state/board-structure.md`.

**Writes:** `cto-os-data/modules/board-comms/state/board-structure.md`, overwrite-with-history.

### `update-update-template`

**Purpose:** Revise the board-update template — sections, order, length norms, tone notes.

**Triggers:**
- "revise the update template"
- "change the structure of the CTO section"
- "board feedback: shorter, fewer sections"

**Reads:** `cto-os-data/modules/board-comms/state/update-template.md`.

**Writes:** `cto-os-data/modules/board-comms/state/update-template.md`, overwrite-with-history.

### `draft-board-update`

**Purpose:** Compose a board update for an upcoming meeting. Pulls from the required and optional dependencies — Business Alignment (company goals + progress), Process Management (flow KPIs), Tech Ops (material reliability events), Security & Compliance (material risks), Hiring (exec-level changes), Budget (financial posture). Follows the declared update template. Respects sensitivity — this module has `sensitivity: high`, and cross-module reads are allowed here because the board is authorized to see sensitive material.

**Triggers:**
- "draft the [Q#] board update"
- "write the CTO section for next board"
- "compose the update for [meeting date]"

**Reads:**
- `cto-os-data/modules/board-comms/state/board-structure.md`
- `cto-os-data/modules/board-comms/state/update-template.md`
- `cto-os-data/modules/board-comms/state/updates/` (recent updates for continuity)
- `cto-os-data/modules/board-comms/state/meetings/` (recent meeting feedback)
- `cto-os-data/modules/business-alignment/state/` (goals + progress)
- `cto-os-data/modules/process-management/state/flows/` (flow KPIs)
- `cto-os-data/modules/tech-ops/state/incidents/`, `cto-os-data/modules/tech-ops/state/postmortems/` (material reliability events)
- `cto-os-data/modules/security-compliance/state/` (optional — material risks)
- `cto-os-data/modules/hiring/state/workforce-plan.md` (optional — exec changes)
- `cto-os-data/modules/budget/state/` (optional — financial posture)
- `cto-os-data/modules/personal-os/state/voice/` (optional — tone)

**Writes:** `cto-os-data/modules/board-comms/state/updates/{YYYY-MM-DD}.md`, append-new-file. Saved as a draft (`status: draft`); user revises and flips to `final` before the meeting.

### `draft-pre-read`

**Purpose:** Compose a topic-specific pre-read memo for a board meeting. Covers risk briefings, fundraising narratives, M&A analysis, strategic-pivot pre-reads — anything meeting-adjacent but not part of the regular update. Amazon 6-pager structure.

**Triggers:**
- "write the pre-read on [topic]"
- "risk briefing for next board"
- "fundraising narrative for [round]"
- "M&A pre-read for [target]"

**Reads:**
- `cto-os-data/modules/board-comms/state/board-structure.md` (audience framing)
- Relevant source modules depending on topic (security-compliance for risk briefings, budget for fundraising, business-alignment for strategic pivots)
- `cto-os-data/modules/personal-os/state/voice/` (optional — tone)

**Writes:** `cto-os-data/modules/board-comms/state/pre-reads/{YYYY-MM-DD}-{topic-slug}.md`, append-new-file.

### `log-board-meeting`

**Purpose:** Capture what happened at the meeting — director feedback, decisions made, asks of management, open threads, tone of the room. Feeds next quarter's `draft-board-update` with continuity.

**Triggers:**
- "log yesterday's board meeting"
- "capture board feedback from [meeting date]"
- "board meeting just ended — here's what happened"

**Reads:**
- `cto-os-data/modules/board-comms/state/board-structure.md`
- The corresponding `updates/{YYYY-MM-DD}.md` (what was presented) if exists

**Writes:** `cto-os-data/modules/board-comms/state/meetings/{YYYY-MM-DD}.md`, append-new-file.

### `backfill-history`

**Purpose:** Seed the module with past board meetings and updates retrospectively. Useful when a user activates the module mid-company, after years of board history lives in slide decks elsewhere. Captures summary-level records, not full historical reproductions.

**Triggers:**
- "backfill last [N] board meetings"
- "seed the last year of board history"

**Reads:** — (user-provided input)

**Writes:** creates multiple `cto-os-data/modules/board-comms/state/meetings/{YYYY-MM-DD}.md` and/or `cto-os-data/modules/board-comms/state/updates/{YYYY-MM-DD}.md` files, each append-new-file.

## Persistence

- **`cto-os-data/modules/board-comms/state/board-structure.md`** — singleton (`slug: current`), overwrite-with-history. Frontmatter: `type: board-structure, slug: current, updated: <date>, directors: <list>, observers: <list, optional>, cadence: <string>, pre_read_lead_time: <string>, materials_format: <string>, committees: <list, optional>`. Body: context + `## History`.
- **`cto-os-data/modules/board-comms/state/update-template.md`** — singleton (`slug: current`), overwrite-with-history. Frontmatter: `type: board-update-template, slug: current, updated: <date>, sections: <list>, target_length_words: <int, optional>, tone_notes: <string, optional>`. Body: rationale + `## History`.
- **`cto-os-data/modules/board-comms/state/updates/{YYYY-MM-DD}.md`** — one file per meeting's update, append-new-file. Frontmatter: `type: board-update, slug: <YYYY-MM-DD>, updated: <date>, meeting_date: <date>, status: <draft|final>, quarter: <string>`. Body: sections from the update template.
- **`cto-os-data/modules/board-comms/state/pre-reads/{YYYY-MM-DD}-{topic-slug}.md`** — append-new-file per pre-read. Frontmatter: `type: board-pre-read, slug: <YYYY-MM-DD>-<topic-slug>, updated: <date>, meeting_date: <date>, topic: <string>, pre_read_type: <risk|fundraising|m-and-a|strategic|other>`. Body: 6-pager prose.
- **`cto-os-data/modules/board-comms/state/meetings/{YYYY-MM-DD}.md`** — append-new-file per board meeting. Frontmatter: `type: board-meeting-log, slug: <YYYY-MM-DD>, updated: <date>, meeting_date: <date>`. Body sections: `## Director feedback`, `## Decisions`, `## Asks of management`, `## Open threads`, `## Room tone`.

**Overrides to the cross-cutting save rule** ([Persistence model](../../docs/ARCHITECTURE.md#persistence-model)): board updates and pre-reads save as `status: draft` on first write; the user explicitly flips to `final` before the meeting. Nothing commits to `final` without confirmation. Meeting logs save without blocking when the user narrates a just-ended meeting.

**Sensitivity:** `sensitivity: high` at module level. Board-level material (risks, financial posture, strategic shifts, personnel moves at the exec level) is damaging if leaked. Scan excludes this module's state by default; callers opt in explicitly. Draft updates that reference Managing Down or Performance & Development content (e.g., exec-level changes) should *reference by name and path only*, not inline the underlying sensitive content.

## State location

`cto-os-data/modules/board-comms/state/`
