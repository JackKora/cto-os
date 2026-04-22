---
name: technical-strategy
description: "Activates for setting the technical direction of the organization — where the technology is going, what to build vs. buy, platform choices, R&D investment, tech-debt prioritization. Covers: writing and updating strategy documents (Larson-style), capturing architecture decisions as ADRs, tracking tech-debt items through lifecycle (open → scheduled → paid-down), superseding prior ADRs when decisions change. Also activates on oblique phrasings like 'should we build or buy,' 'write an ADR for the [X] decision,' 'what's our platform bet,' 'prioritize tech debt,' 'tech strategy for next 18 months,' 'we picked Kafka — document it.' Does NOT activate on flow and process improvement (Process Management); reliability and operations (Tech Ops); team structure decisions (Org Design); or cost-only build-vs-buy analysis without the architectural context (Budget — which provides cost inputs to this module)."
requires: []
optional:
  - business-alignment
  - budget
  - tech-ops
  - process-management
---

# Technical Strategy

## Scope

Setting the technical direction of the organization. Where the technology is going, what we build vs. buy, what platforms we bet on, how we invest in R&D, how we manage and pay down tech debt. Role-shape module — important for CTOs/VPEs at any scale, but takes on more weight the larger and more technically complex the org becomes.

## Out of scope

- **Flow and process improvement** — Process Management.
- **Reliability and production operations** — Tech Ops (which consumes strategy decisions but doesn't set them).
- **Team structure decisions** — Org Design (structure follows strategy; this module owns the strategy, Org Design owns the resulting team changes).
- **Hiring decisions driven by strategy** — Hiring (which takes strategic direction as input).
- **Pure cost analysis** — Budget (which provides cost inputs to build-vs-buy ADRs but doesn't own the architectural call).

## Frameworks

- [Will Larson — *An Elegant Puzzle: Systems of Engineering Management*](https://lethain.com/elegant-puzzle/) — modern engineering-leader reference for strategy writing and platform thinking.
  - *How this module applies it:* Larson's strategy-writing frame anchors `technical-strategy-doc` authorship. Strategy documents here follow his structure — concrete diagnosis of the current state, guiding policy (the principles we'll use to decide), coherent actions (what we'll do, not just what we value). Distinguishes strategy docs ("what direction we're heading") from ADRs ("the specific decisions we make along the way"). Platform thinking — what's a shared foundation vs. what's owned by product teams — is a recurring strategy-doc theme captured when relevant.

- [Michael Nygard — Architecture Decision Records (ADRs)](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions) — lightweight, durable format for capturing technical decisions.
  - *How this module applies it:* every ADR follows the Nygard structure: title, status (proposed / accepted / deprecated / superseded), context (forces at play), decision (what was chosen), consequences (trade-offs accepted). Build-vs-buy decisions are ADRs with `decision_type: build-vs-buy`; stack choices use `decision_type: stack-choice`; platform decisions use `decision_type: platform`. Keeping a single `adr` type (with a discriminator) beats proliferating distinct types — the Nygard format covers all of them with small per-kind context variation.

## Triggers

- "write a strategy doc" / "platform strategy for next 18 months"
- "write an ADR for [decision]"
- "update the ADR on [X]"
- "supersede the [old] ADR with [new]"
- "should we build or buy [capability]"
- "log a tech-debt item" / "we have tech debt in [area]"
- "prioritize tech debt"
- "resolve tech debt: [item]"
- "what's our current tech strategy"
- Oblique: "we're at a stack decision point on [area]"
- Oblique: "the [X] system is hurting us — what are we going to do about it"

## Activation flow

Each step writes a concrete artifact and appends its step number to `activation_completed` in `_module.md`.

### 1. Baseline strategy documents

**Ask:** "Do you have existing strategy documents? If yes, which ones — platform strategy, data strategy, infrastructure strategy — and are they current? If no, pick one area where you most need written direction and we'll stub it now; the rest can follow. If you don't have any and don't need one yet, we can skip and just activate the ADR and tech-debt sides."
**Writes:** one file per strategy doc at `cto-os-data/modules/technical-strategy/state/strategies/{strategy-slug}.md` with `type: technical-strategy-doc`, `slug`, `area`, `horizon`, `status`. If the user has no strategy docs, this step produces zero files and is marked complete on that basis.
**Expects:** zero or more strategy-doc files exist. (Activation can complete with none — strategy docs are not mandatory.)

### 2. Active tech-debt inventory

**Ask:** "What are the top 5–10 tech-debt items you already know about? For each: short name, area (service or subsystem), severity (low / medium / high), why it's debt, what it'd take to pay down. Rough is fine — we'll refine priority over time."
**Writes:** one file per debt item at `cto-os-data/modules/technical-strategy/state/tech-debt/{debt-slug}.md` with `type: tech-debt-item`, `slug`, `area`, `severity`, `status: open`.
**Expects:** zero or more tech-debt files exist.

### 3. Declare ADR cadence and format

**Ask:** "How will ADRs work here? Any deviations from the Nygard format? Where are they stored if you already have a separate repo (e.g., inside the codebase) — or should this module be the canonical store? Do you want to backfill any prior important decisions as ADRs?"
**Writes:** updates `cto-os-data/modules/technical-strategy/state/_module.md` (not a schema file itself — uses the `_module` type for module-level config) with an `adr_config` field capturing these choices.
**Expects:** `_module.md` has `activation_completed` entry for step 3 regardless of whether backfill happens.

## Skills

### `write-strategy`

**Purpose:** Author or update a strategy document for a specific area (platform, data, infra, security, etc.). Follows Larson's diagnosis → guiding policy → coherent actions structure.

**Triggers:**
- "write the platform strategy"
- "update the data strategy"
- "draft a strategy for [area]"

**Reads:**
- `cto-os-data/modules/technical-strategy/state/strategies/{strategy-slug}.md` (existing, if updating)
- `cto-os-data/modules/business-alignment/state/company-goals/` (optional — company-level framing)
- `cto-os-data/modules/tech-ops/state/reliability-posture.md` (optional — constraints)

**Writes:** `cto-os-data/modules/technical-strategy/state/strategies/{strategy-slug}.md`, overwrite-with-history.

### `write-adr`

**Purpose:** Capture a new architecture decision in Nygard format.

**Triggers:**
- "write an ADR for [decision]"
- "document the [X] decision"
- "we just picked [technology] — capture the ADR"

**Reads:**
- `cto-os-data/modules/technical-strategy/state/adrs/` (check slug, look at relevant prior ADRs)
- `cto-os-data/modules/business-alignment/state/` (optional — strategic alignment)
- `cto-os-data/modules/budget/state/` (optional — cost context for build-vs-buy)

**Writes:** `cto-os-data/modules/technical-strategy/state/adrs/{adr-slug}.md`, append-new-file with `status: accepted` (or `proposed` if still under debate).

### `supersede-adr`

**Purpose:** Mark an old ADR as superseded by a new one. Preserves the original (ADRs are immutable once accepted) and links forward.

**Triggers:**
- "supersede the [old] ADR with [new]"
- "we're reversing the [X] decision"
- "[new ADR] replaces [old ADR]"

**Reads:**
- `cto-os-data/modules/technical-strategy/state/adrs/{old-adr-slug}.md`

**Writes:**
- `cto-os-data/modules/technical-strategy/state/adrs/{old-adr-slug}.md` — updates frontmatter `status: superseded`, `superseded_by: <new-adr-slug>`; body unchanged (ADRs are immutable).
- A new ADR via `write-adr` if it doesn't exist yet.

### `log-tech-debt`

**Purpose:** Capture a new tech-debt item.

**Triggers:**
- "log a tech-debt item"
- "we have debt in [area]"
- "[X] has become a debt problem"

**Reads:** `cto-os-data/modules/technical-strategy/state/tech-debt/` (slug collision, related items).

**Writes:** `cto-os-data/modules/technical-strategy/state/tech-debt/{debt-slug}.md`, append-new-file with `status: open`.

### `prioritize-tech-debt`

**Purpose:** Re-rank or re-classify open tech-debt items. Updates priority, severity, or scheduling in place; prior rankings preserved in history.

**Triggers:**
- "prioritize tech debt"
- "re-rank debt for this quarter"
- "schedule the [X] debt for Q2"

**Reads:** `scan(type=["tech-debt-item"], where={"status": "open"}, fields=["slug", "area", "severity", "effort", "priority"])`.

**Writes:** each affected tech-debt file, overwrite-with-history.

### `resolve-tech-debt`

**Purpose:** Mark a tech-debt item as paid down. Captures how it was resolved and any learnings.

**Triggers:**
- "resolve tech debt: [item]"
- "we paid down [debt]"
- "[debt] is done"

**Reads:** `cto-os-data/modules/technical-strategy/state/tech-debt/{debt-slug}.md`.

**Writes:** `cto-os-data/modules/technical-strategy/state/tech-debt/{debt-slug}.md` — sets `status: resolved`, `resolved: <date>`, appends resolution notes to body.

## Persistence

- **`cto-os-data/modules/technical-strategy/state/strategies/{strategy-slug}.md`** — one file per strategy document, overwrite-with-history. Frontmatter: `type: technical-strategy-doc, slug: <strategy-slug>, updated: <date>, area: <string>, horizon: <string>, status: <draft|active|archived>, owner: <string, optional>`. Body: Larson structure — `## Diagnosis`, `## Guiding policy`, `## Coherent actions`, followed by `## History` for prior versions.
- **`cto-os-data/modules/technical-strategy/state/adrs/{adr-slug}.md`** — append-new-file per decision. ADRs are immutable once accepted; status transitions (proposed → accepted, accepted → superseded) update frontmatter but body stays. Frontmatter: `type: adr, slug: <adr-slug>, updated: <date>, title: <string>, status: <proposed|accepted|superseded|deprecated>, decision_type: <build-vs-buy|stack-choice|platform|architecture|other>, superseded_by: <adr-slug, optional>`. Body sections: `## Context`, `## Decision`, `## Consequences`.
- **`cto-os-data/modules/technical-strategy/state/tech-debt/{debt-slug}.md`** — one file per debt item, overwrite-with-history. Frontmatter: `type: tech-debt-item, slug: <debt-slug>, updated: <date>, area: <string>, severity: <low|medium|high>, status: <open|scheduled|resolved>, priority: <int, optional>, effort: <string, optional>, scheduled_for: <string, optional>, opened: <date>, resolved: <date, optional>`. Body: description + `## History` with priority changes and resolution notes.

**Overrides to the cross-cutting save rule** ([Persistence model](../../docs/ARCHITECTURE.md#persistence-model)): ADRs are immutable once status flips to `accepted` — the body doesn't change after that (only frontmatter status/superseded_by can update). Other writes inherit the default.

## State location

`cto-os-data/modules/technical-strategy/state/`
