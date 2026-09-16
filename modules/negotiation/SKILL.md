---
name: negotiation
description: "Activates for professional negotiations where partly shared and opposed interests must be converted into a meaningful agreement, concession, or commitment; the user has a real alternative or may walk away; and deliberate preparation is warranted. Covers negotiation preparation, BATNA and reservation-boundary discipline, round planning and debriefs, multi-issue offer packages, closure, and negotiation-specific learning. Also activates on natural phrasings like 'help me prepare for the renewal negotiation,' 'what is my walk-away,' 'design three offer packages,' 'plan the next round,' or 'we reached a deal — close this out.' Does NOT activate for ordinary persuasion, feedback, disagreement, coaching, relationship maintenance, legal analysis, routine purchasing, or personal-life negotiation."
requires: []
optional:
  - personal-os
  - managing-up
  - managing-down
  - managing-sideways
  - external-network
  - business-alignment
  - hiring
  - budget
  - legal
  - product
  - tech-ops
  - security-compliance
  - org-design
---

# Negotiation

## Scope

Prepare, run, and learn from consequential professional negotiations. This module owns negotiation strategy, sequencing, interaction planning, offer-package design, round debriefs, closure, and negotiation-specific lessons. A situation belongs here only when it has all four features: partly shared and partly opposed interests; a meaningful agreement, concession, or commitment at stake; a credible alternative or real walk-away choice; and enough consequence or complexity to justify deliberate preparation.

If one of those features is unclear, ask a short routing question before creating negotiation state. Relationship and subject-matter modules remain the sources of context; this module turns that context into a negotiation plan.

## Out of scope

- **Ordinary influence, persuasion, disagreement, feedback, or coaching.** Managing Up, Managing Down, or Managing Sideways owns the relationship work. A hard conversation is not automatically a negotiation.
- **Coalition building and routine stakeholder alignment.** Managing Sideways owns internal peer relationships and currency-of-exchange context; Negotiation takes over only when the four-part scope test is met.
- **Legal analysis, contract interpretation, and rights or obligations.** Legal owns issue spotting, legal workflow, redlines, and counsel coordination. Negotiation may use counsel-confirmed constraints to plan the interaction but never substitutes for Legal or counsel.
- **Subject decisions and source facts.** Hiring owns candidate and offer process facts; Budget owns cost envelopes; Business Alignment owns customer and company-goal context; Product owns roadmap facts; Tech Ops owns reliability facts; Security & Compliance owns risk and control facts; Org Design owns structural decisions; stakeholder modules own relationship profiles; External Network owns external-contact history. Negotiation reads those sources when relevant and does not duplicate them as canonical facts.
- **Personal-life negotiation.** Housing, family, divorce, personal purchases, and other non-work negotiations are outside CTO OS.

## Frameworks

Do not blend every framework below into one checklist. Always use the Seven Elements as the structural baseline, then select only the conversational and conditional lenses that fit the obstacle. Record the selected lenses and why they were selected in the negotiation body.

- [Harvard Negotiation Project — Seven Elements](https://www.pon.harvard.edu/daily/negotiation-skills-daily/what-is-negotiation/) — the structural preparation baseline for every negotiation: interests, legitimacy, relationships, alternatives/BATNA, options, commitments, and communication.
  - *How this module applies it:* every `negotiation` record has a Seven Elements preparation section. Separate the user's known alternative from an aspiration; derive a reservation boundary from user-supplied or sourced constraints; and identify missing evidence rather than filling gaps. Revisit the seven elements after each material round.

- [Chris Voss / Black Swan — the conversational method associated with *Never Split the Difference* and its evolved concepts](https://www.blackswanltd.com/newsletter/expert-negotiator-concepts-that-have-evolved-since-never-split-the-difference-was-published) — the default conversational layer, using tactical empathy, labels, mirrors, calibrated questions, accusation audits, and deliberate tone.
  - *How this module applies it:* use this layer by default unless `negotiation-posture.conversational_layer` says otherwise. Choose a small number of techniques that serve the next interaction; do not turn them into a script dump or use empathy as manipulation. These concepts remain attributed to Chris Voss / Black Swan; they are not represented as CTO OS inventions, and no copyrighted book prose is reproduced.

- [3-D Negotiation](https://www.library.hbs.edu/working-knowledge/negotiating-in-three-dimensions) — conditional lens for obstacles in setup, deal design, parties, sequence, forum, or process rather than at-the-table wording.
  - *Select when:* the current table cannot produce a good outcome because the wrong people, issues, sequence, venue, mandate, or deal structure are in place. Record the setup obstacle and the proposed change. Do not select it merely because a negotiation has multiple stakeholders.

- [Difficult Conversations](https://www.pon.harvard.edu/tag/difficult-conversations-how-to-discuss-what-matters-most/) — conditional lens for blame, feelings, identity, trust, or relationship damage that is blocking productive negotiation.
  - *Select when:* the relational layer is itself material to the outcome. Separate observable contribution from blame, acknowledge feelings without inventing them, and plan for identity or trust concerns. Relationship repair does not erase reservation boundaries.

- [MESO — Multiple Equivalent Simultaneous Offers](https://www.pon.harvard.edu/daily/negotiation-skills-daily/managing-the-negotiators-dilemma-nb/) — conditional lens for multi-issue package design.
  - *Select when:* at least two tradable issues allow genuinely different packages that are approximately equivalent to the user. Explain the tradeoffs and equivalence assumptions; never present knowingly unequal packages as equivalent.

## Evidence and safety rules

- Separate **sourced facts**, **user assertions**, and **counterpart hypotheses** in every preparation and debrief. A counterpart's stated position is a fact that they said it, not proof of the underlying interest.
- Never fabricate alternatives, competing offers, deadlines, authority, facts, leverage, constraints, or counterpart intent. Mark unknowns and identify how the user could verify them.
- Never facilitate or recommend coercion, fraud, deceptive scarcity, false urgency, fake authority, fabricated competition, or threats the user cannot and will not carry out.
- Do not infer that the user can commit the company. Record the authority boundary, and make contingent commitments when authority is incomplete.
- Keep the reservation boundary and BATNA distinct: the BATNA is the best available alternative if no agreement is reached; the reservation boundary is the worst acceptable deal relative to that alternative and other constraints.
- Treat counterpart hypotheses as working theories with confidence and evidence. Revise them after each round; never launder them into facts.
- Preserve dignity and the working relationship where feasible, without pressuring the user to accept a deal that crosses a grounded boundary.

## Triggers

- "prepare me for the renewal negotiation"
- "I need to negotiate roadmap scope for committed headcount"
- "what is my BATNA and walk-away on this vendor deal"
- "design several offer packages for these issues"
- "plan the next round with the customer"
- "debrief today's negotiation — they moved on term but not price"
- "we have agreement in principle; help me make the commitments precise"
- "we walked away — close the negotiation and capture what we learned"
- "show me every active negotiation and the next move"
- Oblique: "they want three concessions before they will sign, and I need to know what I can trade"
- Oblique: "we keep arguing at the table, but I think the real problem is who has authority"

## Activation flow

Activation is deliberate and resumable. Read `cto-os-data/modules/negotiation/_module.md` first. For every step listed in `activation_completed`, verify the expected artifact and invariants below before skipping it. If an artifact is absent or invalid, surface the drift and offer to repair or rerun that step; do not silently treat it as complete. Completing steps 1–3 appends each step number and updates `updated`, while leaving `active: false`. Only step 4 may activate the module.

### 1. Establish framework preferences and ethical boundaries

**Ask:** "Negotiation always uses the Harvard Seven Elements for structure. By default, should the conversational layer use the Chris Voss / Black Swan approach, or do you prefer plain-direct or custom guidance? The conditional lenses are 3-D Negotiation for setup and deal-design problems, Difficult Conversations for blame/feelings/identity/trust, and MESO for multi-issue packages; they will be selected only when their routing criteria fit. What ethical boundaries or company rules should always constrain negotiation behavior? I will never use fabricated alternatives, deadlines, authority, scarcity, threats, or competing offers."
**Writes:** `cto-os-data/modules/negotiation/state/posture.md` with `type: negotiation-posture`, plus `cto-os-data/modules/negotiation/_module.md` with `1` appended to `activation_completed` and `sensitivity: high`.
**Expects:** `posture.md` has `structural_baseline: seven-elements`, `conversational_layer: black-swan|plain-direct|custom`, an `ethical_boundaries` list, and `custom_conversational_guidance` when the layer is `custom`. `_module.md.activation_completed` contains `1`; the module remains inactive.

### 2. Seed the negotiation playbook

**Ask:** "What professional negotiation practices have reliably worked for you, and what failure modes do you want to avoid? Ground each learned pattern in a negotiation you experienced or state it explicitly as a personal rule. If you have none to seed, we'll create an empty evidence ledger rather than invent lessons."
**Writes:** `cto-os-data/modules/negotiation/state/playbook.md` with `type: negotiation-playbook`, plus `cto-os-data/modules/negotiation/_module.md` with `2` appended to `activation_completed`.
**Expects:** `playbook.md` exists with `principles`, `effective_patterns`, and `failure_modes` lists (each may be empty), `last_reviewed`, and an evidence-ledger body that attributes every non-empty learned entry to a user statement or negotiation/round. `_module.md.activation_completed` contains `2`; the module remains inactive.

### 3. Seed current negotiations

**Ask:** "Which professional negotiations are currently consequential enough to track? For each: title; kind (internal resource, role and scope, compensation, hiring offer, customer commercial, vendor commercial, partnership, dispute resolution, or other); counterparties; what meaningful agreement or commitment is at stake; your known authority boundary; current status (preparing, active, paused, or agreement in principle); subject modules that hold source context; and the next known interaction date if any. Please distinguish facts you can source, your own assertions, and hypotheses about the counterpart. If none are active, say so explicitly."
**Writes:** one file per disclosed negotiation at `cto-os-data/modules/negotiation/state/negotiations/{negotiation-slug}.md` with `type: negotiation`, plus `cto-os-data/modules/negotiation/_module.md` with `3` appended to `activation_completed`.
**Expects:** each disclosed negotiation passes the four-part scope test, has a durable slug, allowed `kind` and `status`, at least one counterparty, an authority boundary (which may explicitly be unknown pending confirmation), and body sections separating facts, user assertions, and counterpart hypotheses; or the user explicitly attests that there are no current negotiations. `_module.md.activation_completed` contains `3`; the module remains inactive.

### 4. Confirm handling and activate

**Ask:** "Ready to activate Negotiation? Confirm that all negotiation state is high-sensitivity; that alternatives, reservation boundaries, leverage, authority, and counterpart hypotheses must never be invented; that the Seven Elements are always the preparation baseline; that Black Swan is the default conversational layer unless your posture says otherwise; and that coercion, fraud, deceptive scarcity, fake authority, false threats, and fabricated competing offers are prohibited."
**Writes:** `cto-os-data/modules/negotiation/_module.md` — append `4` to `activation_completed`, set `schema_version: 1`, `active: true`, `activated_at: <date>`, `deactivated_at: null`, `updated: <date>`, and `sensitivity: high`.
**Expects:** the user explicitly confirms the handling and ethical boundaries; `_module.md` has `activation_completed: [1, 2, 3, 4]`, `schema_version: 1`, `active: true`, and `sensitivity: high`. `posture.md` and `playbook.md` both exist, so activation always produces concrete v1 state even when there are no current negotiations.

## Skills

Users route by natural-language intent. The names below are internal capability labels, not commands users need to know.

### `prepare-negotiation`

**Purpose:** Create or refresh the complete Seven Elements preparation for one qualifying professional negotiation, with explicit evidence labels, authority and walk-away discipline, and only the conditional lenses whose routing criteria fit.

**Triggers:**
- "help me prepare for [negotiation]"
- "work out my BATNA and reservation boundary"
- "we need a plan before the vendor call"

**Reads:**
- `cto-os-data/modules/negotiation/state/posture.md`
- `cto-os-data/modules/negotiation/state/playbook.md`
- `cto-os-data/modules/negotiation/state/negotiations/{negotiation-slug}.md` and its recent rounds, if it already exists
- `cto-os-data/modules/personal-os/state/show-up.md` only when leadership posture should shape the interaction
- relevant stakeholder profile and recent interaction state from Managing Up, Managing Down, Managing Sideways, or External Network only when that module owns a counterparty relationship
- relevant Business Alignment, Hiring, Budget, Legal, Product, Tech Ops, Security & Compliance, or Org Design state only when that module owns a material fact or constraint; Legal remains authoritative for legal interpretation and counsel-confirmed positions

**Writes:** `cto-os-data/modules/negotiation/state/negotiations/{negotiation-slug}.md`, append-new-file or overwrite-with-history.

### `plan-next-round`

**Purpose:** Turn the current negotiation state into a focused next-round plan: objective, information to learn, message sequence, calibrated conversational moves, authority checks, likely branches, and stopping condition.

**Triggers:**
- "plan the next round"
- "what should I do on tomorrow's negotiation call"
- "they rejected the first offer — plan the response"

**Reads:**
- the negotiation record, recent `negotiation-round` files, posture, and playbook
- relevant relationship state only when the next round carries a relationship issue

**Writes:** `cto-os-data/modules/negotiation/state/negotiations/{negotiation-slug}.md`, overwrite-with-history; updates the current-plan body section and `next_round_date` when known.

### `design-offer-packages`

**Purpose:** Design defensible multi-issue packages using MESO when its routing criteria are satisfied, without disguising unequal value or crossing authority and reservation boundaries.

**Triggers:**
- "design three offer packages"
- "what can we trade across term, scope, and price"
- "give me equivalent packages for the next round"

**Reads:**
- the negotiation record, posture, and playbook
- Budget, Hiring, Business Alignment, Legal, Product, Tech Ops, Security & Compliance, or Org Design state only when it supplies an actual package constraint, approval, valuation input, operational boundary, or counsel-confirmed position

**Writes:** `cto-os-data/modules/negotiation/state/negotiations/{negotiation-slug}.md`, overwrite-with-history; updates the options and current-plan sections with package assumptions and equivalence rationale.

### `debrief-round`

**Purpose:** Capture one meaningful interaction, distinguish observation from interpretation, update the Seven Elements and counterpart hypotheses, and identify the next action without rewriting history.

**Triggers:**
- "debrief today's negotiation"
- "here is what happened in round two"
- "they moved on scope but held on price"

**Reads:** the negotiation record, its prior rounds, posture, and playbook.

**Writes:**
- `cto-os-data/modules/negotiation/state/rounds/{negotiation-slug}/{YYYY-MM-DD}-{sequence}.md`, append-new-file.
- `cto-os-data/modules/negotiation/state/negotiations/{negotiation-slug}.md`, overwrite-with-history to update current state, selected lenses, next action, and status if warranted.

### `close-negotiation`

**Purpose:** Close a negotiation as agreed, no agreement, or withdrawn; make commitments and owners precise; compare the result with the grounded alternative and boundary; and capture relationship and subject-module handoffs.

**Triggers:**
- "we reached a deal — close it out"
- "we walked away"
- "the negotiation is over without agreement"

**Reads:** the negotiation record, all of its rounds, posture, and playbook; relevant Legal state when legal documentation or counsel confirmation is still required.

**Writes:** `cto-os-data/modules/negotiation/state/negotiations/{negotiation-slug}.md`, overwrite-with-history; sets a terminal status and `closed`, and adds outcome, commitments, owners, open contingencies, and handoffs to the body.

### `update-negotiation-playbook`

**Purpose:** Convert repeated or explicitly user-endorsed negotiation lessons into reusable guidance, with traceable evidence and without generalizing from one ambiguous interaction.

**Triggers:**
- "add this lesson to my negotiation playbook"
- "what negotiation patterns are emerging"
- "update the playbook from the closed deals"

**Reads:** `cto-os-data/modules/negotiation/state/playbook.md` plus only the negotiation and round records cited as evidence.

**Writes:** `cto-os-data/modules/negotiation/state/playbook.md`, overwrite-with-history.

### `show-negotiation-portfolio`

**Purpose:** Show active, paused, agreement-in-principle, and recently closed negotiations with status, next interaction, unresolved authority or evidence gaps, and required user attention.

**Triggers:**
- "show my negotiation portfolio"
- "which negotiations need attention"
- "what deals are active and what is the next move"

**Reads:** all `negotiation` records, with recent `negotiation-round` records only where needed to explain current state.

**Writes:** —

## Persistence

- **`cto-os-data/modules/negotiation/_module.md`** — singleton module activation record, overwrite-in-place. Uses the baseline `_module` schema. Activation appends verified step numbers to `activation_completed`; step 1 sets `sensitivity: high`; only step 4 sets `schema_version: 1`, `active: true`, `activated_at`, and `deactivated_at: null`.
- **`cto-os-data/modules/negotiation/state/posture.md`** — singleton (`slug: current`), overwrite-with-history. Frontmatter: `type: negotiation-posture, slug: current, updated: <date>, structural_baseline: seven-elements, conversational_layer: <black-swan|plain-direct|custom>, conditional_lenses: <list drawn from three-d|difficult-conversations|meso>, ethical_boundaries: <list[string]>, custom_conversational_guidance: <string, optional>`. Body records rationale and `## History`.
- **`cto-os-data/modules/negotiation/state/negotiations/{negotiation-slug}.md`** — one living record per negotiation, overwrite-with-history. Frontmatter: `type: negotiation, slug: <negotiation-slug>, updated: <date>, title: <string>, kind: <internal-resource|role-and-scope|compensation|hiring-offer|customer-commercial|vendor-commercial|partnership|dispute-resolution|other>, counterparties: <list[string]>, status: <preparing|active|paused|agreement-in-principle|closed-agreed|closed-no-agreement|withdrawn>, opened: <date>, closed: <date, optional>, subject_modules: <list[string]>, authority_boundary: <string>, conversational_layer: <black-swan|plain-direct|custom>, conditional_lenses: <list drawn from three-d|difficult-conversations|meso>, next_round_date: <date, optional>`. Body sections: `## Scope test`, `## Sourced facts`, `## User assertions`, `## Counterpart hypotheses`, `## Seven Elements` (interests, legitimacy, relationships, alternatives/BATNA, options, commitments, communication), `## Lens selection`, `## Current plan`, `## Outcome and handoffs`, and `## History`.
- **`cto-os-data/modules/negotiation/state/rounds/{negotiation-slug}/{YYYY-MM-DD}-{sequence}.md`** — append-new-file per meaningful interaction. Frontmatter: `type: negotiation-round, slug: <negotiation-slug>-<sequence>, updated: <date>, negotiation: <negotiation-slug>, sequence: <int>, occurred: <date>, interaction: <meeting|call|written-exchange|offer-exchange|internal-alignment>, outcome: <advanced|unchanged|set-back|agreement-in-principle|closed-agreed|closed-no-agreement|walked-away>, next_action: <string, optional>`. Body sections: `## Observed facts`, `## User actions and assertions`, `## Counterpart statements`, `## Interpretations and hypotheses`, `## Concessions and commitments`, `## Seven Elements changes`, and `## Next round`.
- **`cto-os-data/modules/negotiation/state/playbook.md`** — singleton (`slug: current`), overwrite-with-history. Frontmatter: `type: negotiation-playbook, slug: current, updated: <date>, principles: <list[string]>, effective_patterns: <list[string]>, failure_modes: <list[string]>, last_reviewed: <date>`. Body sections: `## Evidence ledger` and `## History`; every learned entry cites an explicit user rule or one or more negotiation/round slugs.

**Overrides to the cross-cutting save rule** ([Persistence model](../../docs/ARCHITECTURE.md#persistence-model)): all module state is high-sensitivity. Clear user-provided preparation, round, closure, and playbook content inherits the default save rule. A model-generated counterpart hypothesis, inferred alternative, or inferred reservation boundary must be previewed and explicitly approved before it is persisted; it can never be stored as a fact. Never persist raw contract documents, confidential attachments, credentials, or unnecessary personal data.

## State location

`cto-os-data/modules/negotiation/state/`
