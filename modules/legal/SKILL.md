---
name: legal
description: "Activates for the CTO's legal operating work: triaging a legal concern; reviewing customer, vendor, partner, or other commercial contracts and managing their legal positions, redlines, approvals, and counsel workflow; corporate governance, financings, diligence, and M&A; intellectual property, licensing, and open-source software questions; employment legal matters; privacy, data-protection, and product-regulation questions; disputes, demands, investigations, subpoenas, and legal holds; tracking legal obligations and deadlines; preparing a factual brief for counsel; and rolling up legal posture. Also activates on natural phrasings like 'the customer sent redlines,' 'can we use this OSS license,' 'do we need board approval,' 'we got a demand letter,' 'what do I need to ask our lawyer,' or 'what legal deadlines are coming up.' Contract bargaining strategy, concessions, sequencing, and interaction planning route to Negotiation, while Legal remains authoritative for legal analysis and legal positions. Does NOT activate for tax, real estate, antitrust, environmental, export-controls or sanctions work, other specialty legal practices, security-control operations, or ordinary people management. Requests for a definitive legal conclusion on an in-scope topic still activate; Legal reframes them toward issue spotting, factual preparation, and qualified counsel without delivering the conclusion."
requires: []
optional:
  - security-compliance
  - technical-strategy
  - product
  - hiring
  - performance-development
  - tech-ops
  - negotiation
---

# Legal

## Scope

Run the CTO's legal operating layer: issue spotting, preparation, workflow, and tracking for general legal intake and triage; commercial contracts; corporate governance and transactions, including M&A; intellectual property and licensing, including open-source software; employment legal matters; privacy, data protection, and product regulation; disputes and investigations; independently changing legal obligations; counsel briefings; and a current legal-posture rollup.

This module helps the user organize facts, unknowns, decisions, owners, deadlines, and questions for counsel. It does not substitute for qualified legal counsel, establish an attorney-client relationship, give legal advice, or make definitive legal conclusions. Applicable law and privilege depend on facts, jurisdiction, and counsel's judgment.

Legal owns contract interpretation, rights and obligations, redlines, legal positions, approvals, counsel workflow, and legal records. Negotiation owns counterpart bargaining strategy, concession design, sequencing, questions, and rounds when its four-part gate is met. A mixed contract request may use both modules: link their records, keep each module authoritative for its own facts, and do not duplicate canonical content.

## Out of scope

- **Tax.** Do not analyze, track, or brief tax matters here. Direct the user to qualified tax counsel or a tax professional.
- **Real estate.** Do not analyze, track, or brief real-estate matters here. Direct the user to qualified real-estate counsel.
- **Antitrust.** Do not analyze, track, or brief antitrust or competition-law matters here. Direct the user to qualified antitrust counsel.
- **Environmental.** Do not analyze, track, or brief environmental-law matters here. Direct the user to qualified environmental counsel.
- **Export controls and sanctions.** Do not analyze, track, or brief export-control or sanctions matters here. Direct the user to qualified specialist counsel.
- **Other specialty practices.** Any legal practice not named in Scope is outside this module. Recognize only enough to decline the work and direct the user to appropriately qualified specialist counsel; do not create a Legal module record for the substance.
- **Security operations and controls.** Security & Compliance owns controls, audits, and the security-risk register. Legal owns the legal questions, notification or contractual obligations, regulator/counsel workflow, and related deadlines.
- **Architecture and product decisions.** Technical Strategy and Product own the implementation or product decision. Legal supplies issue spots, constraints, and counsel-confirmed inputs.
- **Commercial economics, customer strategy, and bargaining mechanics.** Budget owns spend, constraints, approvals, forecast, and cost facts; Business Alignment owns the customer or partner strategy; Negotiation owns counterpart bargaining strategy, concessions, sequencing, questions, and rounds when its four-part gate is met. Legal owns rights, obligations, legal positions, redlines, approvals, renewal/termination terms, counsel workflow, and legal records.
- **Ordinary hiring, performance, or people-management execution.** Hiring and Performance & Development own the operating process. Legal owns employment-law issue spotting and counsel coordination when a legal issue exists.
- **Relationship management with legal leaders.** Managing Sideways owns the user's working relationship with a General Counsel, Head of Legal, or peer legal leader. This module owns the substance and workflow of legal matters.
- **Board narrative and meeting materials.** Board Comms owns the board-facing narrative. Legal owns the legal facts, approvals, constraints, and counsel questions that may feed it.
- **Document repository or e-signature workflow.** Store links or source references, not contract files, legal correspondence, investigation evidence, or signed originals.

## Frameworks

No jurisdiction-specific doctrine or legal decision tree is encoded. The module uses these operational invariants:

- **Route before analysis.** Classify a new concern into exactly one in-scope domain before doing substantive preparation. If the domain is unclear, keep it at `general-intake` and identify the missing facts; never guess the governing legal specialty.
- **Separate facts from issue spots.** Attribute facts to their source, label unknowns, and phrase model-generated concerns as questions or issue spots. Only the user or counsel can supply a position; counsel-confirmed guidance is attributed, not re-derived.
- **Escalate by consequence and clock.** Imminent deadlines, regulator or law-enforcement contact, litigation threats, subpoenas, preservation concerns, personal safety, material transaction gates, and high-impact employment or privacy matters prompt immediate qualified-counsel escalation. The module can prepare the handoff while counsel responds.
- **Minimum necessary persistence.** Save operational summaries and references, not raw attorney communications, attachments, investigation evidence, or unnecessary personal data. Never copy secrets into state.
- **Privilege-aware, not privilege-creating.** `handling: privilege-sensitive` is a workflow and access cue only. The module never infers or promises attorney-client privilege or work-product protection, and mere storage, labeling, or counsel involvement does not create privilege.
- **Preserve; do not alter.** For disputes, investigations, subpoenas, or possible legal holds, do not recommend deleting, editing, backdating, concealing, or selectively curating relevant material. Escalate preservation questions to counsel.

## Triggers

- "I have a legal issue and I'm not sure where it belongs"
- "triage this legal question" / "should our lawyer look at this"
- "the customer sent redlines" / "review the MSA before I respond"
- "this vendor renewal has an auto-renew and a liability cap"
- "do we need board approval for this" / "prepare the legal workstream for the acquisition"
- "what diligence items are still open for the deal"
- "who owns this invention" / "can we ship this GPL dependency"
- "do our contractor agreements assign IP"
- "this termination could get contentious" / "does this classification need employment counsel"
- "we received a deletion request" / "do we need a DPA or transfer mechanism"
- "does this product flow need consent" / "what regulations should counsel assess"
- "we got a demand letter" / "a regulator contacted us" / "preserve records for this dispute"
- "track the filing deadline" / "what legal obligations are due next month"
- "prepare a brief for outside counsel" / "what questions should I ask our lawyer"
- "show me our legal posture" / "what legal matters are high priority right now"
- Oblique: "I don't want to reply to this email until someone legal sees it"
- Oblique: "there's a clause in the contract that makes me nervous"
- Oblique: "before we launch this, are there legal flags we should surface"

## Activation flow

Activation is deliberate and resumable. Read `cto-os-data/modules/legal/_module.md` first. For each step already listed in `activation_completed`, verify its expected artifact and invariant against that step's **Expects** before skipping it. If an expected artifact is missing or invalid, surface the activation drift and offer to repair or rerun that step with user authorization; do not silently skip it or treat activation as complete. Completing steps 1–3 appends the step number and updates `updated`, but leaves `active: false`. Only step 4 may set `active: true`.

### 1. Establish the legal operating posture

**Ask:** "Let's establish the legal operating posture. What entities and primary jurisdictions are in scope? Who is the internal legal owner? Is counsel in-house, external, mixed, or not yet retained, and what is each counsel relationship's scope? What events must be escalated immediately, who can approve legal positions or contract exceptions, and what response-time expectations should this module use? Please describe roles and source references; don't paste privileged advice or confidential engagement terms."
**Writes:** `cto-os-data/modules/legal/state/legal-posture.md` with `type: legal-posture`, `slug: current`, plus `cto-os-data/modules/legal/_module.md` with `1` appended to `activation_completed` and `sensitivity: high`.
**Expects:** `legal-posture.md` identifies at least one entity or operating scope, primary jurisdictions (which may be `unknown` pending counsel), a legal owner, counsel model, approval authority, and escalation criteria. `_module.md.activation_completed` contains `1`; the module remains inactive.

### 2. Seed the current matter docket

**Ask:** "What active legal matters should be on the docket now? For each, give a short title, domain (general intake, commercial contract, corporate governance or transaction, IP/licensing/OSS, employment, privacy/data/product regulation, or dispute/investigation), factual summary and source, owner, current status, urgency, known deadline, counsel involvement, next action, and whether it needs privilege-sensitive handling. Don't paste raw legal advice, correspondence, evidence, or unnecessary personal data. If there are no active matters, say so explicitly."
**Writes:** one file per disclosed matter at `cto-os-data/modules/legal/state/matters/{matter-slug}.md` with `type: legal-matter`, plus `cto-os-data/modules/legal/_module.md` with `2` appended to `activation_completed`.
**Expects:** each disclosed matter has a durable slug, one allowed domain, attributed facts separated from unknowns and issue spots, an owner, status, urgency, next action, and handling cue; or the user explicitly attests that there are no active matters. `_module.md.activation_completed` contains `2`; the module remains inactive.

### 3. Seed independently tracked obligations

**Ask:** "Which legal obligations need their own deadline or recurrence tracking? Examples include a contractual notice, filing, approval, renewal, consent, reporting duty, or retention/preservation instruction within this module's scope. For each, give the source reference, jurisdiction if known, owner, due date or recurrence, status, related matter, and whether counsel has confirmed it. If none are currently known, say so explicitly."
**Writes:** one file per disclosed obligation at `cto-os-data/modules/legal/state/obligations/{obligation-slug}.md` with `type: legal-obligation`, plus `cto-os-data/modules/legal/_module.md` with `3` appended to `activation_completed`.
**Expects:** each disclosed obligation is independently actionable and has a source reference, owner, status, and either a due date, recurrence, or explicit `unknown` timing; unverified obligations are labeled `issue-spotted`, not stated as law. Or the user explicitly attests that there are no known obligations. `_module.md.activation_completed` contains `3`; the module remains inactive.

### 4. Confirm boundaries and activate

**Ask:** "Ready to activate Legal? Confirm that this module supports issue spotting, preparation, workflow, and tracking but does not replace qualified counsel or make definitive legal conclusions; that all saved state is high-sensitivity; that `privilege-sensitive` is only a handling cue and does not create privilege; and that I'll show proposed legal-state writes for explicit approval and minimize stored legal content."
**Writes:** `cto-os-data/modules/legal/_module.md` — append `4` to `activation_completed`, set `schema_version: 1`, `active: true`, `activated_at: <date>`, `deactivated_at: null`, `updated: <date>`, and `sensitivity: high`.
**Expects:** the user explicitly confirms the boundaries; `_module.md` has `activation_completed: [1, 2, 3, 4]`, `schema_version: 1`, `active: true`, and `sensitivity: high`. `legal-posture.md` exists, so activation always produces concrete v1 state even when the initial matter and obligation sets are empty.

## Skills

The user never needs to invoke these internal names. Route from natural language using the rules below.

**Router:**

1. A new, ambiguous, or mixed concern starts with `intake-and-triage`.
2. A clearly scoped new concern or an existing matter routes to exactly one domain skill. Preserve one primary `domain`; link adjacent context rather than duplicating the matter.
3. A deadline or recurring duty that changes independently routes to `track-legal-obligation`, linked back to the matter when applicable.
4. A request to package facts and questions for a lawyer routes to `prepare-counsel-brief`.
5. A request about the whole docket routes to `show-legal-posture`; a change to the operating model routes to `update-legal-posture`.
6. An out-of-scope specialty stops at the boundary in **Out of scope**. Do not force-fit it into `general-intake`.

For a mixed contract request, route the legal analysis and position workflow here and the bargaining process to Negotiation only when the four-part gate is met. Cross-link the `legal-matter` and `negotiation` records using their existing related-record and subject-module references; do not copy canonical facts between them. Ordinary redline review or approval routing does not activate Negotiation.

For every route, distinguish sourced fact, user assertion, counsel-attributed guidance, unknown, and model-generated issue spot. Never convert an issue spot into an asserted obligation or legal conclusion.

### `intake-and-triage`

**Purpose:** Turn a new in-scope concern into a structured matter, select one domain, identify the clock and consequence, and determine whether qualified counsel should be engaged now.

**Triggers:**
- "triage this legal issue"
- "I don't know what kind of legal problem this is"
- "should this go to our lawyer"
- "something in this email worries me"

**Reads:**
- `cto-os-data/modules/legal/state/legal-posture.md`
- `scan(type=["legal-matter"], fields=["slug","title","domain","status","owner"], include_high_sensitivity=true)` to avoid duplicates
- Source material the user supplies, without persisting the raw source

**Writes:** `cto-os-data/modules/legal/state/matters/{matter-slug}.md`, append-new-file or overwrite-with-history when the user identifies an existing matter.

### `commercial-contracts`

**Purpose:** Prepare and track an in-scope customer, vendor, partner, licensing-commercial, or other operating agreement review, including contract interpretation, redlines, legal positions, approvals, and counsel workflow, without presenting issue spots as legal advice. When substantive bargaining passes the four-part gate, Negotiation owns the counterpart interaction strategy and rounds.

**Triggers:**
- "the customer sent redlines"
- "review the MSA / DPA / order form"
- "what contract points need counsel"
- "this renewal or termination clause is a concern"

**Reads:**
- `cto-os-data/modules/legal/state/legal-posture.md`
- `cto-os-data/modules/legal/state/matters/{matter-slug}.md` when one exists
- User-supplied agreement or redline source, held outside module state
- Relevant Product or Security & Compliance state only when the user's question requires factual product, data, or control context
- `cto-os-data/modules/negotiation/state/negotiations/{negotiation-slug}.md` (optional — only when a linked qualifying negotiation supplies a confirmed bargaining status, commitment, or outcome relevant to the legal workflow)

**Writes:** `cto-os-data/modules/legal/state/matters/{matter-slug}.md`, append-new-file or overwrite-with-history. Record legal positions, owners, open questions, approval exceptions, source links, and the linked negotiation path when applicable; do not store the agreement or redline itself or duplicate the negotiation plan.

### `corporate-governance-and-transactions`

**Purpose:** Coordinate legal workflow for entity governance, board or stockholder approvals, financings, diligence, and M&A, including decision gates and counsel-owned workstreams.

**Triggers:**
- "do we need board or stockholder approval"
- "prepare the legal checklist for the financing"
- "what diligence is still open"
- "track the legal workstream for the acquisition"

**Reads:**
- `cto-os-data/modules/legal/state/legal-posture.md`
- `cto-os-data/modules/legal/state/matters/{matter-slug}.md`
- Relevant Security & Compliance, Product, or Technical Strategy state when needed for the specific transaction's factual diligence context

**Writes:** `cto-os-data/modules/legal/state/matters/{matter-slug}.md`, append-new-file or overwrite-with-history. Record governance questions, approval gates, diligence requests, counsel attribution, owners, and dates; do not assert that an approval is legally sufficient unless counsel has confirmed it.

### `ip-licensing-and-oss`

**Purpose:** Spot and organize intellectual-property ownership, assignment, inbound/outbound licensing, brand, and open-source software concerns for counsel or authorized policy review.

**Triggers:**
- "can we ship this OSS dependency"
- "is this license compatible with our distribution"
- "who owns this invention or code"
- "does the contractor agreement assign IP"

**Reads:**
- `cto-os-data/modules/legal/state/legal-posture.md`
- `cto-os-data/modules/legal/state/matters/{matter-slug}.md`
- Relevant Technical Strategy, Product, Hiring, or Security & Compliance state when needed for facts
- User-supplied license, notice, policy, or agreement source, without copying it into module state

**Writes:** `cto-os-data/modules/legal/state/matters/{matter-slug}.md`, append-new-file or overwrite-with-history. Preserve license identifiers, source links, distribution/use facts, ownership assertions and their sources, unknowns, and questions for counsel.

### `employment-legal`

**Purpose:** Prepare and track employment-law concerns while keeping ordinary hiring, performance, and management execution in their owning modules.

**Triggers:**
- "this termination may create legal risk"
- "should employment counsel review this classification"
- "we received an accommodation or leave request"
- "there's a wage, discrimination, retaliation, or harassment concern"

**Reads:**
- `cto-os-data/modules/legal/state/legal-posture.md`
- `cto-os-data/modules/legal/state/matters/{matter-slug}.md`
- Relevant Hiring or Performance & Development records only when necessary and authorized
- User-supplied policy or communication source, with unnecessary personal and health details excluded from state

**Writes:** `cto-os-data/modules/legal/state/matters/{matter-slug}.md`, append-new-file or overwrite-with-history. Minimize personal data, attribute allegations rather than treating them as facts, separate management actions from legal guidance, and escalate time-sensitive or high-impact concerns to qualified employment counsel.

### `privacy-data-and-product-regulation`

**Purpose:** Organize privacy, data-protection, data-transfer, data-subject-rights, consumer-protection, accessibility, AI/product, and other non-specialty product-regulation questions within the declared scope and jurisdictions.

**Triggers:**
- "we received a deletion or access request"
- "do we need a DPA or transfer mechanism"
- "does this flow need notice or consent"
- "what legal questions should counsel answer before launch"

**Reads:**
- `cto-os-data/modules/legal/state/legal-posture.md`
- `cto-os-data/modules/legal/state/matters/{matter-slug}.md`
- Relevant Security & Compliance, Product, or Technical Strategy state for data flows, controls, architecture, and product facts
- User-supplied request, notice, agreement, or regulatory source, without storing the raw material

**Writes:** `cto-os-data/modules/legal/state/matters/{matter-slug}.md`, append-new-file or overwrite-with-history. Record jurisdictions, product/data facts, response clock, issue spots, owners, and counsel questions; do not claim compliance or noncompliance without counsel-confirmed support.

### `disputes-and-investigations`

**Purpose:** Coordinate facts, deadlines, preservation flags, and counsel handoff for disputes, claims, demands, subpoenas, regulator inquiries, internal investigations, and threatened or active litigation.

**Triggers:**
- "we received a demand letter or subpoena"
- "a regulator or law-enforcement agency contacted us"
- "this could become litigation"
- "we may need a legal hold"
- "track the internal investigation"

**Reads:**
- `cto-os-data/modules/legal/state/legal-posture.md`
- `cto-os-data/modules/legal/state/matters/{matter-slug}.md`
- Relevant Security & Compliance or Tech Ops records when an incident supplies factual context
- User-supplied notice or source, without storing the raw communication or evidence

**Writes:** `cto-os-data/modules/legal/state/matters/{matter-slug}.md`, append-new-file or overwrite-with-history. Record receipt and response dates, source references, attributed allegations, preservation status, counsel involvement, and next actions. Do not conduct a legal investigation, determine liability, or advise alteration or deletion of potentially relevant material.

### `track-legal-obligation`

**Purpose:** Create, update, satisfy, supersede, or flag an independently changing legal or contractual obligation and its operational clock.

**Triggers:**
- "track this filing / notice / approval / renewal"
- "what is due next month"
- "mark the notice obligation satisfied"
- "counsel confirmed the deadline changed"

**Reads:**
- `cto-os-data/modules/legal/state/legal-posture.md`
- `cto-os-data/modules/legal/state/obligations/{obligation-slug}.md` when updating
- `cto-os-data/modules/legal/state/matters/{matter-slug}.md` when linked
- The cited source or counsel-attributed confirmation

**Writes:** `cto-os-data/modules/legal/state/obligations/{obligation-slug}.md`, append-new-file or overwrite-with-history. An AI-spotted item remains `confirmation_status: issue-spotted`; only attribute `user-confirmed` or `counsel-confirmed` to an explicit source.

### `prepare-counsel-brief`

**Purpose:** Produce a concise, factual, decision-oriented brief that lets qualified counsel understand a matter quickly and answer the user's explicit questions.

**Triggers:**
- "prepare a brief for counsel"
- "summarize this for our lawyer"
- "what questions should I ask outside counsel"
- "package the facts and timeline before the call"

**Reads:**
- `cto-os-data/modules/legal/state/legal-posture.md`
- `cto-os-data/modules/legal/state/matters/{matter-slug}.md`
- Linked `cto-os-data/modules/legal/state/obligations/{obligation-slug}.md` files
- Only the minimum authorized adjacent-module state and user-supplied sources needed for the brief

**Writes:** `cto-os-data/modules/legal/state/counsel-briefs/{YYYY-MM-DD}-{matter-slug}-{brief-slug}.md`, append-new immutable file. Separate facts, assertions, unknowns, issue spots, timeline, desired outcome, and questions; identify every source path or external reference. Do not label the brief privileged unless the user requests `handling: privilege-sensitive`, and explain that the label does not determine legal privilege.

### `update-legal-posture`

**Purpose:** Update entities, jurisdictions, counsel model, approval authority, escalation criteria, or response expectations as the legal operating model changes.

**Triggers:**
- "update our legal posture"
- "we retained new outside counsel"
- "change who can approve contract exceptions"
- "add a jurisdiction to scope"

**Reads:** `cto-os-data/modules/legal/state/legal-posture.md`.

**Writes:** `cto-os-data/modules/legal/state/legal-posture.md`, overwrite-with-history.

### `show-legal-posture`

**Purpose:** Assemble a read-time rollup of the current docket without persisting a duplicate report: matters by domain, urgency and status; overdue or upcoming obligations; waiting-on-counsel items; unresolved intake; and explicit data gaps.

**Triggers:**
- "show our legal posture"
- "what legal matters need attention"
- "what is waiting on counsel"
- "what legal deadlines are coming up"

**Reads:**
- `cto-os-data/modules/legal/state/legal-posture.md`
- `scan(type=["legal-matter"], fields=["slug","title","domain","status","urgency","owner","next_action_due","counsel_involved"], include_high_sensitivity=true)`
- `scan(type=["legal-obligation"], fields=["slug","domain","status","owner","due_date","recurrence","confirmation_status","related_matter"], include_high_sensitivity=true)`
- `scan(type=["counsel-brief"], fields=["slug","matter","prepared_on","purpose","supersedes"], include_high_sensitivity=true)` only when the user asks about briefing history

**Writes:** —

## Persistence

- **`cto-os-data/modules/legal/_module.md`** — singleton overwrite. Frontmatter: `type: _module, slug: legal, module: legal, updated: <date>, schema_version: 1, active: <bool>, activated_at: <date|null>, deactivated_at: <date|null>, sensitivity: high, activation_completed: <list[int]>`. Activation steps append their number without discarding earlier progress; only step 4 activates the module.
- **`cto-os-data/modules/legal/state/legal-posture.md`** — singleton (`slug: current`), overwrite-with-history. Frontmatter: `type: legal-posture, slug: current, updated: <date>, entities: <list[string]>, jurisdictions: <list[string]>, legal_owner: <string>, counsel_model: <none|external|in-house|mixed>, counsel_scopes: <list of role/scope references>, approval_authority: <string>, escalation_criteria: <list[string]>, response_expectations: <string>`. Body sections: `## Operating model`, `## Escalation and approvals`, `## Handling notes`, `## Source references`, `## History`.
- **`cto-os-data/modules/legal/state/matters/{matter-slug}.md`** — one file per independently changing matter, append-new-file then overwrite-with-history. Frontmatter: `type: legal-matter, slug: <matter-slug>, updated: <date>, title: <string>, domain: <general-intake|commercial-contract|corporate-governance-transaction|ip-licensing-oss|employment|privacy-data-product-regulation|dispute-investigation>, status: <intake|triage|active|waiting-on-counsel|waiting-on-counterparty|resolved|closed>, urgency: <low|medium|high|critical>, owner: <string>, opened: <date>, next_action: <string>, next_action_due: <date|null>, counsel_involved: <bool>, handling: <standard|privilege-sensitive>, related_obligations: <list[legal-obligation slug]>, related_records: <list[path]>`. Body sections: `## Sourced facts`, `## Assertions and positions`, `## Issue spots`, `## Unknowns`, `## Timeline`, `## Next steps`, `## Source references`, `## History`. Status and urgency describe the operating workflow, not the merits or a legal conclusion. `handling` is an access cue, not a privilege determination.
- **`cto-os-data/modules/legal/state/obligations/{obligation-slug}.md`** — one file per independently tracked obligation, append-new-file then overwrite-with-history. Frontmatter: `type: legal-obligation, slug: <obligation-slug>, updated: <date>, domain: <same enum as legal-matter>, obligation_kind: <filing|notice|consent|approval|renewal|reporting|retention-preservation|restriction|other>, status: <identified|pending|satisfied|waived|superseded|overdue>, owner: <string>, source_reference: <string>, jurisdiction: <string|unknown>, due_date: <date|null>, recurrence: <string|null>, confirmation_status: <issue-spotted|user-confirmed|counsel-confirmed>, related_matter: <legal-matter slug|null>, completed_date: <date|null>`. Body sections: `## Operational description`, `## Basis and attribution`, `## Evidence references`, `## History`. This record tracks workflow; it is not an independent assertion of what the law requires. Only set `satisfied`, `waived`, or `superseded` from an explicit user- or counsel-attributed source.
- **`cto-os-data/modules/legal/state/counsel-briefs/{YYYY-MM-DD}-{matter-slug}-{brief-slug}.md`** — immutable append-new-file. Frontmatter: `type: counsel-brief, slug: <YYYY-MM-DD>-<matter-slug>-<brief-slug>, updated: <date>, prepared_on: <date>, matter: <legal-matter slug>, purpose: <string>, audience: <role or counsel reference>, handling: <standard|privilege-sensitive>, supersedes: <counsel-brief slug|null>, source_paths: <list[path]>`. Body sections: `## Requested outcome`, `## Sourced facts`, `## Assertions and positions`, `## Timeline`, `## Unknowns`, `## Issue spots`, `## Questions for counsel`, `## Sources`. Never edit a counsel brief after creation; create a new file with `supersedes` when correcting or refreshing it.

**Overrides to the cross-cutting save rule** ([Persistence model](../../docs/ARCHITECTURE.md#persistence-model)): before every write under this module, show the proposed content and target path and obtain explicit user confirmation. Minimize the record to what the workflow needs. Do not persist raw attorney communications, legal advice, contract documents, investigation evidence, or unnecessary personal data; save a user-approved operational summary and source reference instead. Ask whether to use `handling: privilege-sensitive` when counsel or a dispute/investigation is involved, but never infer privilege or claim that the cue, storage location, counsel involvement, or module sensitivity creates it.

**Sensitivity:** set `sensitivity: high` on `cto-os-data/modules/legal/_module.md`. All state inherits that default. Scans exclude Legal state unless the caller deliberately opts into high-sensitivity data, and cross-module reads must use the minimum necessary fields. Do not inline raw legal narratives into general rollups or other modules.

## State location

`cto-os-data/modules/legal/state/`
