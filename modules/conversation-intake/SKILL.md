---
name: conversation-intake
description: "Activates when the user pastes a meeting transcript (Granola-style, raw text, or otherwise) or asks to process / extract / capture / route content from a meeting they just had. Covers: extracting decisions, action items, observations, direct quotes, and open questions from a transcript; routing each item to the right module; surfacing concerns and opportunities by cross-checking against existing module state; and writing records only after explicit user confirmation. Also activates on oblique phrasings like 'log my meeting with Mike,' 'here's what we covered with the board,' 'pull the action items out of this,' 'what did I commit to in that conversation,' 'what should I write down from this.' Does NOT activate on live / real-time meeting capture (no audio ingestion), Slack thread ingestion (out of scope), unstructured 'notes I jotted down' that aren't transcripts (use working-note instead), or transcripts of meetings the user wasn't a participant in."
requires: []
optional: []
---

<!--
Authoring note: this skill is access-mechanism-agnostic. It describes what to read
and write — paths, frontmatter, state shape, scan queries — not how. The active host picks
the access mechanism (direct filesystem on a server install, MCP tools on a client
install) from the active project instructions.
-->

# Conversation Intake

## Scope

Turn raw meeting transcripts into structured records routed to the right modules. One verb: ingest a transcript the user pastes, extract the things worth keeping, route each one to its owning module, and write — but only after the user confirms a summary of everything proposed. Designed to make meeting capture frictionless without sacrificing the user's control over what lands in their data repo.

The module is intentionally generic — `transcript` is the first skill; future siblings (async-thread, voice-memo) can sit alongside it without restructuring.

## Out of scope

- **Real-time meeting capture.** No audio ingestion, no live transcription. The user brings a finished transcript.
- **Slack ingestion.** Async multi-party threads behave too differently from linear meeting transcripts; explicitly dropped from v1.
- **Loose notes the user jotted down.** Those belong in `notes/` as `working-note` — promote later if they crystallize. This skill expects a structured transcript with speaker turns.
- **Transcripts of meetings the user wasn't in.** Treats anyone-not-present as third-party, which puts most of the content under the PII/personal filter and produces near-empty output. Not a useful input.
- **Storing the raw transcript.** Provenance is captured on each extracted record (date, time, attendees). The transcript itself is never written to disk.

## Frameworks

No external framework — this is an infrastructure-style module like `data-backup`. Design invariants instead:

- **Never write before user confirmation.** The summary is presented; the user says go. Without an explicit confirmation, nothing persists. This invariant outranks every other instinct.
- **Never assume.** Unknown speakers, ambiguous claims, gaps in reasoning, and conflicts with existing state all stop the flow and ask the user. The skill never resolves ambiguity silently.
- **Decision and goal conflicts are blockers.** If the transcript says "we decided X" and an existing `decision`, `adr`, `design-decision`, `prioritization-decision`, `goal-horizon`, or `company-goal-horizon` record says otherwise, the skill stops before producing a summary and forces resolution. Other conflicts are flagged in the summary but not blocking.
- **No personal-life content.** Family, hobbies, health, weekend plans, kids, pets, vacations, relationships — none of it lands in any record, even when said by the user. Strip during the filter step.
- **No third-party PII.** Customer names, candidate names, customer emails, phone numbers, addresses — none of it. Internal teammates being discussed professionally is fine; their lives outside work is not.
- **Concerns and opportunities are theories, never facts.** Every item phrased tentatively ("I think…", "Maybe…", "It could mean…") and accompanied by a cited record from another module (path or slug). If no evidence surfaces, the section says so explicitly — never invent connections.
- **The raw transcript is never persisted.** Only structured records with lightweight provenance (meeting date, time, attendees). The transcript exists in the conversation buffer and nowhere else.

## Triggers

- "process this transcript"
- "extract from my meeting with [name]"
- "pull the decisions out of this"
- "what did I commit to in that conversation"
- "here's what we covered today — capture it"
- "log my meeting with [name]"
- "what should I write down from this"
- Pasted Granola-style block (speaker labels + utterances) without an explicit command
- Oblique: "interesting conversation just now — let me share it"
- Oblique: "before I forget, here's how the board call went"

## Activation flow

This module has no state-bearing activation steps — there's no config to capture, no rubric to define, no rhythm to declare. Activation is a single step: confirm the user understands the module's invariants, then mark active.

### 1. Confirm intent and invariants

**Ask:** "Activating Conversation Intake. Quick confirmation before first use: I'll only ever extract from transcripts you paste; I'll never store the raw transcript; I'll always show you a summary and wait for your go-ahead before writing anything; and I'll never extract personal-life content or third-party PII. Sound right?"
**Writes:** `cto-os-data/modules/conversation-intake/_module.md` — flips `active: true`, sets `activated_at`, appends `1` to `activation_completed`.
**Expects:** user-acknowledged module is active. No other state files.

## Skills

### `transcript`

**Purpose:** Ingest a pasted meeting transcript, extract decisions / action items / observations / quotes / open questions, route each to a target module, run a concerns/opportunities pass, present a confirmation summary, and (on confirmation) write the records.

**Triggers:**
- "process this transcript" / "extract from my meeting with [name]"
- "pull the decisions / actions / quotes out of this"
- "log my meeting with [name]"
- Pasted Granola-style block — speaker turns visible in the paste
- Oblique: "here's what we covered, capture it"

**Reads:**
- The pasted transcript (conversation buffer only; never written to disk).
- `scan(type=["altitude"], where={"module": "personal-os"})` — the user's role altitude. Sets the significance bar: what's worth capturing for a Director may be noise for an SVP. No transcript-specific capture policy exists; the bar comes from the system's general altitude + tracked-state awareness.
- `scan(type=["_module"], where={"active": true})` — to know which modules are available routing targets.
- Per-module scans of records the transcript may touch — examples:
  - `scan(type=["decision","adr","design-decision","prioritization-decision"])` — for decision conflicts *and* to know whether the target module has a native decision type (routing decision, see step 6).
  - `scan(type=["goal-horizon","company-goal-horizon","product-goal","ds-goal"])` — for goal conflicts and goal-relevant opportunities.
  - `scan(type=["stakeholder-profile"])` — for speaker identification.
  - `scan(type=["team"])`, `scan(type=["product-initiative","ds-initiative"])`, etc. — for routing context, significance signals, and supporting evidence in the concerns pass.
- `scan(type=["..."], fields=["slug","name","module"])` style queries to keep payloads small. Use `include_body` only when conflict-checking against a specific record's content.

**Writes (only after user confirmation, and only for items that clear the significance bar):**
- **Native-typed decisions** — a decision routed to a module that owns a native decision type is written as that type, in its native location, as a draft:
  - `technical-strategy/state/adrs/{adr-slug}.md` as `type: adr`, `status: proposed`.
  - `org-design/state/decisions/{YYYY-MM-DD}-{slug}.md` as `type: design-decision`.
  - `product/state/prioritization-decisions/{YYYY-MM-DD}-{slug}.md` as `type: prioritization-decision`.
  These require the native type's fields; the skill prompts for any it can't infer (never fabricates them).
- **Generic intake records** — everything else (all action items, observations, quotes, open questions, and decisions routed to a module with no native decision type) is written under the target module's `state/intake/<bucket>/` subtree using the new types in `meta/schema.md`:
  - `decision` → `state/intake/decisions/{YYYY-MM-DD}-{slug}.md`
  - `action-item` → `state/intake/action-items/{YYYY-MM-DD}-{slug}.md`
  - `observation` → `state/intake/observations/{YYYY-MM-DD}-{slug}.md`
  - `quote` → `state/intake/quotes/{YYYY-MM-DD}-{slug}.md`
  - `open-question` → `state/intake/questions/{YYYY-MM-DD}-{slug}.md`
- Items judged **summary-only** (tactical, ephemeral, below altitude) are never written — they appear in the summary's "Everything else" section for the user's awareness only. Each record carries provenance (`meeting_date`, `meeting_time`, `attendees`). No `state/` files are written under `conversation-intake` itself — every record routes out.

**Flow:**

1. **Receive the paste.** Treat everything in the user's message after the trigger as transcript content. Hold it in the conversation buffer; do not write it anywhere.

2. **First-pass parse.**
   - Identify speakers from the transcript's labels. For each one, attempt to match against `stakeholder-profile` records and the user's own name.
   - Scan for logic gaps — claims that depend on unstated context, references to people/projects/decisions the skill can't resolve from module state, and statements that contradict known facts.
   - Run targeted scans for conflicts: if the transcript mentions a decision, scan decision-shaped types; if it mentions goals, scan goal-shaped types; etc.

3. **Ask for resolutions.** Before extracting anything, surface every gap:
   - "I see three speakers labeled A, B, C and a fourth labeled 'Speaker 4' — who is each? I can match A against [stakeholder slugs found]."
   - "The conversation references a 'Project Atlas decision from last quarter' but I don't see a matching record. Is this a real decision I'm missing, or are they referring to something informal?"
   - "The transcript says the team decided to deprecate X, but the existing ADR `state/adrs/x-keep.md` says we'd keep X through 2026. **This is a blocker — I won't proceed until you tell me which is current.**"

   Decision and goal conflicts are blockers — do not move to step 4 until resolved. Other ambiguities are noted and carried into the summary as flags.

4. **Filter personal-life content and PII.** Drop content matching:
   - Family / partner / kids / pets references.
   - Health / medical / mental-health details (the user's or anyone else's).
   - Weekend / vacation / hobby / personal-event discussion.
   - Phone numbers, addresses, personal emails, dates of birth.
   - Third-party identifiers: customer names, candidate names, customer-side individual contacts (unless they're already in a `stakeholder-profile`).

   Keep a tally: `personal_dropped` (count), `pii_dropped` (count). Used in the Filtered Content line of the summary.

5. **Extract by taxonomy.** Walk the remaining transcript and bucket content into:
   - **Decisions** — something the group concluded, with rationale and confidence (`low | medium | high` in how clearly the transcript states it).
   - **Action items** — a commitment to do something, with an owner, optional due date, and status (`open` by default).
   - **Observations** — signals worth noting that aren't decisions or actions ("Mike seemed checked out," "the team kept circling back to the migration risk").
   - **Quotes** — verbatim language worth preserving (perf feedback wording, customer language a CS lead reported, board-ready phrasing).
   - **Open questions** — things the meeting raised but didn't resolve, with a guess at who could answer.

   For each item, record: the content itself, the source speaker, the proposed target module, and any links to existing records (for observations, the linked goal / project / person).

6. **Significance triage.** CTO OS is not a tactical decision log. Most of what's said in a meeting does not deserve a record. Using the user's altitude (from the `altitude` read) and the tracked-state scans, sort every extracted item into one of two tiers:
   - **Capture-worthy** — clears the bar on at least one axis: **durability** (would plausibly be referenced again in a month), **reversibility** (expensive or slow to undo — the system's values treat most decisions as cheaply reversible, so it's the costly ones worth recording), **linkage** (touches an existing goal / strategy / ADR / person's trajectory / risk / initiative — this is the strongest signal and is the same scan the concerns pass uses), or **altitude/scope** (operates at or above the user's altitude; affects multiple teams, the roadmap, the budget, or the org). This set should usually be small.
   - **Summary-only** — tactical, ephemeral, below altitude, cheaply reversible. Shown in the summary so nothing is silently dropped, but never written unless the user explicitly promotes it.

   The bar is altitude-relative: a library choice is capture-worthy for a Director, noise for a C-level. When genuinely unsure, place the item in summary-only and let the user pull it up — never over-capture.

7. **Route to target modules.** For each **capture-worthy** item, propose a target module based on its content. Examples:
   - A decision about platform architecture → `technical-strategy`.
   - An action item the user committed to → owning module by topic (e.g., `managing-down` for a coaching follow-up, `business-alignment` for a customer-engagement commitment).
   - An observation about a direct report → `managing-down`.
   - A quote of board-ready phrasing → `board-comms`.
   - An open question about hiring strategy → `hiring`.

   **Native-type routing (decisions only).** Decisions are the only taxonomy bucket with native equivalents in the system. When a capture-worthy decision routes to a module that owns a native decision type, propose saving it *as that native type, in its native location*, rather than as a generic intake record:
   - `technical-strategy` → `adr` (write as `status: proposed` — never `accepted` off a transcript).
   - `org-design` → `design-decision`.
   - `product` → `prioritization-decision`.

   Native types carry required fields a transcript rarely supplies in full (an ADR needs `title`, `decision_type`, and `## Context` / `## Decision` / `## Consequences`). The skill surfaces what it can infer and **asks the user to fill the rest at confirmation** — it never fabricates them. All other taxonomy types, and decisions routed to a module with no native decision type, are saved as the generic intake type under `state/intake/<bucket>/`.

   For unrouteable items, **ask the user** explicitly: "I have an item about [X] — I don't see a clean module for it. Options: A, B, C, or skip. Where does it go?"

8. **Concerns / Opportunities pass.** With the capture-worthy set in hand, scan target modules (and adjacent modules) for supporting or contradicting evidence relative to the user's goals and active work:
   - "Mike committing to lead the migration intersects with the `performance-record` showing he's currently flagged `concerning` — *I think* this might be ambitious; might be worth a sanity check. [link: state/records/mike.md]"
   - "The decision to push the Q3 launch overlaps with the `company-goal-horizon` `2026-Q3` item about shipping by August — *maybe* the goal needs updating; the timeline implied here is later. [link: state/company-goals/quarterly.md]"
   - Every theory tentatively phrased and accompanied by a cited record. If nothing surfaces: "**None surfaced this meeting.**" — never invent connections.

9. **Render the confirmation summary** using the template below. Wait for explicit user approval before any write. If any capture-worthy decision is routing to a native type, prompt for its missing required fields as part of the confirmation.

10. **On confirmation, write the records.** Native-typed decisions go to their module's native path (e.g., `state/adrs/{slug}.md`); all other capture-worthy items go to `state/intake/<bucket>/{YYYY-MM-DD}-{slug}.md`. Each file gets full frontmatter (type, slug, updated, provenance, plus type-specific fields). Summary-only items are not written. Surface the file paths written so the user can verify.

**Confirmation summary template** (rendered as Markdown):

```
## Meeting intake — {{meeting_date}} {{meeting_time}}
**Attendees:** {{name list, resolved against stakeholder-profile where possible}}

### 📌 To capture
The only items I'll write. Usually small. I render only the per-type subsections
that have items; the rest are omitted.

#### Decisions
| # | Decision | Rationale | Conf | Source | Target module | Save as |
|---|---|---|---|---|---|---|
{{"Save as" is the native type + "(draft)" for adr/design-decision/prioritization-decision,
or "intake" for the generic type. Add a "Conflicts?" note inline if one was flagged.}}

#### Action items
| # | Action | Owner | Due | Status | Source | Target module |
|---|---|---|---|---|---|---|

#### Observations
| # | Observation | Possible meaning | Conf | Source | Target module | Linked record |
|---|---|---|---|---|---|---|

#### Quotes
| # | Quote | Source | Context | Target module | Why preserved |
|---|---|---|---|---|---|

#### Open questions
| # | Question | Who could answer | Target module | Why it matters |
|---|---|---|---|---|

### Everything else (not captured — for your eyes only)
Terse, one line per item, grouped by type. Shown so nothing is silently dropped —
say "pull up #N" (continue numbering from the To-capture set) to promote any into
the capture set.

- Decisions: {{tactical decision · another}}
- Action items: {{routine action · another}}
- Observations: {{…}}
- Quotes: {{…}}
- Open questions: {{…}}

(Each line that's empty renders as "(none)".)

### Concerns / Opportunities
{{Numbered list. Each: tentative phrasing, cited evidence with module path. Or:
"None surfaced this meeting."}}

### Filtered content
Dropped {{N}} items as personal/small-talk, {{M}} as third-party PII.

---
**Confirm to write?** Decisions saving as a native type (adr / design-decision /
prioritization-decision) may need a couple of required fields from you first — I'll
ask before writing. Nothing persists until you say go.
```

Within **To capture**, render only the per-type subsections that have items. The **Everything else** type lines render "(none)" when empty so the structure stays visible.

## Persistence

This module writes nothing to its own `state/` directory — every captured record routes out to a target module. The only file under `conversation-intake/` itself is the module's `_module.md`. Only **capture-worthy** items are written; summary-only items are never persisted.

Writes land in one of two places depending on the routing decision in the `transcript` flow:

- **`cto-os-data/modules/conversation-intake/_module.md`** — module activation record (`type: _module`). Overwrite (singleton). Written once by step 1 of the activation flow to flip `active: true`, set `activated_at`, and append `1` to `activation_completed`. Subsequent updates only on deactivation or schema-version migrations.

**Native-typed decisions** — when a capture-worthy decision routes to a module that owns a native decision type, it is written as that type in the target module's *native* location (not under `intake/`), as a draft. These follow the owning module's existing schema (see `meta/schema.md`):

- **`cto-os-data/modules/technical-strategy/state/adrs/{adr-slug}.md`** — `type: adr`, written `status: proposed`. Append-new-file.
- **`cto-os-data/modules/org-design/state/decisions/{YYYY-MM-DD}-{slug}.md`** — `type: design-decision`. Append-new-file.
- **`cto-os-data/modules/product/state/prioritization-decisions/{YYYY-MM-DD}-{slug}.md`** — `type: prioritization-decision`. Append-new-file.

**Generic intake records** — everything else (all action items, observations, quotes, open questions, and decisions routed to a module with no native decision type) lands under the target module's `state/intake/<bucket>/` subtree, using the types defined in `meta/schema.md`. Each carries baseline fields (`type`, `slug`, `updated`) plus provenance (`meeting_date`, `meeting_time`, `attendees`):

- **`cto-os-data/modules/{target}/state/intake/decisions/{YYYY-MM-DD}-{slug}.md`** — `type: decision`. Append-new-file per decision.
- **`cto-os-data/modules/{target}/state/intake/action-items/{YYYY-MM-DD}-{slug}.md`** — `type: action-item`. Append-new-file per action.
- **`cto-os-data/modules/{target}/state/intake/observations/{YYYY-MM-DD}-{slug}.md`** — `type: observation`. Append-new-file per observation.
- **`cto-os-data/modules/{target}/state/intake/quotes/{YYYY-MM-DD}-{slug}.md`** — `type: quote`. Append-new-file per quote.
- **`cto-os-data/modules/{target}/state/intake/questions/{YYYY-MM-DD}-{slug}.md`** — `type: open-question`. Append-new-file per question.

The `intake/` subtree keeps generic records separate from each module's native types: `scan(type=["decision"], module="managing-down")` returns just the intake-sourced decisions filed under managing-down, while `scan(type=["adr"])` still returns only first-class ADRs (including any this skill seeded as `status: proposed`).

**Overrides to the cross-cutting save rule** ([Persistence model](../../docs/ARCHITECTURE.md#persistence-model)): the confirmation step is the override. Every write — native or generic, across every target module — is gated behind a single explicit user confirmation at the end of the flow, even for modules whose default behavior would otherwise permit silent writes.

## State location

`cto-os-data/modules/conversation-intake/state/` — empty by design (only `_module.md` lives here at the module root). All extracted records live in their target module's `state/intake/` subtree.
