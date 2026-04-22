---
name: security-compliance
description: "Activates for security and compliance posture work — the CTO-level view of the security program, what controls are in place, what risks are open, and how the org tracks against the compliance regimes it's committed to (SOC 2, ISO 27001, HIPAA, etc.). Covers: risk register maintenance (ISO-27001-style), control inventory and ownership (CIS-based, mapped to regimes), compliance regime status tracking, ISO 27001 Statement of Applicability, audit event capture (SOC 2 Type 1/2, ISO surveillance, customer assessments, pentests), posture rollup through the NIST CSF lens, risk-briefing authorship (often feeds Board Comms pre-reads). Also activates on oblique phrasings like 'what's our SOC 2 status,' 'log a new risk,' 'update the risk register,' 'we just got the pentest findings,' 'draft the risk briefing for the board,' 'who owns control [X],' 'are we ready for the Type 2 audit.' Does NOT activate on security-incident operational response (Tech Ops runs incidents; this module captures the resulting risk picture); security-adjacent architecture decisions (Technical Strategy owns the call; this module informs it with risk context); policy authoring (policies typically live in legal/HR docs — this module references them); or employee security training execution (operational elsewhere)."
requires: []
optional:
  - tech-ops
  - technical-strategy
---

# Security & Compliance

## Scope

Managing the security and compliance posture of the organization. Understanding risk, ensuring controls are working, meeting obligations to customers and regulators. Risk register maintenance, control inventory and ownership, compliance regime status tracking (SOC 2, ISO 27001, HIPAA, whatever the org is committed to), ISO-27001-specific artifacts (Statement of Applicability), audit event capture, posture rollup. Role-shape / optional-by-role module — critical for orgs with enterprise customers, less central for early-stage consumer.

## Out of scope

- **Security-incident operational response** — Tech Ops runs incidents (detection through resolution); this module captures the *resulting risk picture* — what got exposed, what control failed, what's the residual risk.
- **Security-adjacent architecture decisions** — Technical Strategy owns the decision (e.g., "we're adopting a zero-trust network"); this module provides the risk context that informs it.
- **Policy authoring and document management** — policies typically live in legal/HR document systems; this module references them by name / ID, doesn't author or store them.
- **Employee security training execution** — operational; lives in an LMS or equivalent.
- **Threat intelligence and active threat-hunting** — out of scope for a CTO-OS Security & Compliance module; too tactical.
- **Vulnerability scanning infrastructure** — the scanner is infrastructure; this module tracks *findings and their resolution* at the risk-register level.

## Frameworks

Four frameworks, each with a distinct purpose. Don't conflate.

- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework) — strategic posture lens: Identify / Protect / Detect / Respond / Recover.
  - *How this module applies it:* the rollup frame for `show-posture`. Every control is tagged with which NIST CSF function(s) it supports. Gaps surface as "we're thin on Detect" or "Respond is disproportionate to our size." Not a certification standard; not audited against directly.

- [CIS Critical Security Controls](https://www.cisecurity.org/controls) — prescriptive control catalog, organized into Implementation Groups (IG1 / IG2 / IG3) by org maturity.
  - *How this module applies it:* the source-of-truth for what controls exist and what implementation group level applies. A startup aiming at IG1; a mid-stage company at IG2; a regulated-industry org at IG3. The `control` type's `cis_control_id` field points back to the CIS catalog entry. When `log-risk` surfaces a gap, the question is: "which CIS control would close this gap, and are we meeting that control?"

- [ISO/IEC 27001](https://www.iso.org/isoiec-27001-information-security.html) — international certifiable ISMS standard. Requires an Information Security Management System with documented scope, risk assessment, Statement of Applicability (SoA) covering Annex A controls, internal audits, management review.
  - *How this module applies it:* the `statement-of-applicability` type is the ISO-27001 SoA — which Annex A controls are in scope, which are excluded, and the justification. Risk register entries follow ISO's risk-based ISMS logic (identify → assess → treat → monitor). The `compliance-posture` tracks certification status (scoping / audit-in-progress / certified / renewal-due).

- [SOC 2](https://www.aicpa-cima.com/topic/audit-assurance/audit-and-assurance-greater-than-soc-2) — AICPA audit standard with Trust Services Criteria (Security required; Availability / Processing Integrity / Confidentiality / Privacy optional). Type 1 (point-in-time control design) vs. Type 2 (operating effectiveness over a window, typically 6–12 months).
  - *How this module applies it:* the `control` type's `soc2_criteria` field lists which Trust Services Criteria a control supports. Audit events capture SOC 2 Type 1 / Type 2 / bridge-letter events. When a customer asks for the SOC 2 report, the compliance-posture frontmatter shows the current status and the audit-events surface recent letters. SOC 2 is US-centric but increasingly expected globally by enterprise customers.

## Triggers

- "log a risk" / "add to the risk register"
- "update the risk register" / "risk [X] has changed"
- "resolve risk [X]" / "we mitigated [risk]"
- "what's our SOC 2 status" / "are we ready for the Type 2 audit"
- "update the Statement of Applicability" / "ISO Annex A review"
- "log an audit event" / "pentest findings came in"
- "who owns control [X]" / "update control ownership"
- "draft the risk briefing for the board" / "risk briefing for customer assessment"
- "show security posture" / "NIST CSF rollup"
- "update compliance posture" / "we're committing to ISO 27001 next year"
- Oblique: "customer just asked for our security posture — compile the response"
- Oblique: "the [vulnerability type] news — is that something we need to respond to"

## Activation flow

Each step writes a concrete artifact and appends its step number to `activation_completed` in `_module.md`.

### 1. Declare compliance posture

**Ask:** "Which compliance regimes is the org committed to or pursuing? Common: SOC 2 Type 1, SOC 2 Type 2, ISO 27001, HIPAA, PCI DSS, FedRAMP. For each: current status (scoping / audit-in-progress / certified / renewal-due / considering), target date if committed, owner, scope statement (which entities / products are covered). Also: overall target maturity (CIS IG1 / IG2 / IG3) and the NIST CSF target profile if you have one."
**Writes:** `cto-os-data/modules/security-compliance/state/compliance-posture.md` with `type: compliance-posture`, `slug: current`, `regimes`, `target_cis_ig`, `nist_csf_notes`.
**Expects:** frontmatter `regimes` has ≥ 1 entry with `name`, `status`, and `owner`. (An org committed to nothing is unusual — but the module can activate with an empty `regimes` list if the user is pre-commitment.)

### 2. Seed the risk register

**Ask:** "What are the top 10–20 known risks? For each: short title, category (data / access / availability / compliance / vendor / other), severity (low / medium / high / critical), likelihood (low / medium / high), current mitigations, owner, status (open / mitigating / accepted / resolved). Rough assessments are fine — risks get refined over time."
**Writes:** one file per risk at `cto-os-data/modules/security-compliance/state/risks/{risk-slug}.md` with `type: risk-register-entry`, `slug: <risk-slug>`, `category`, `severity`, `likelihood`, `status`, `owner`, `opened`.
**Expects:** at least one risk file exists, or the user explicitly attests to no known risks (unusual — prompt them to think harder; in the worst case zero-risk activation is allowed).

### 3. Enumerate key controls

**Ask:** "List the key controls you already have in place. For each: short name, CIS control ID if you know it, which NIST CSF functions it supports, which compliance regimes it's mapped to (SOC 2 criteria, ISO Annex A reference), owner, implementation status (not-implemented / partial / implemented / needs-remediation). If you don't have a formal control catalog yet, start with the top 10–20 controls your org clearly has — access controls, backup and recovery, incident response process, vulnerability scanning, vendor reviews."
**Writes:** one file per control at `cto-os-data/modules/security-compliance/state/controls/{control-slug}.md` with `type: control`, `slug: <control-slug>`, `name`, `cis_control_id`, `nist_csf_functions`, `soc2_criteria`, `iso_annex_a`, `owner`, `implementation_status`.
**Expects:** at least one control file exists.

## Skills

### `update-compliance-posture`

**Purpose:** Revise compliance regime commitments, status, or target maturity.

**Triggers:**
- "update compliance posture"
- "we're adding ISO 27001 to our target"
- "SOC 2 Type 2 audit just finished — update status to certified"

**Reads:** `cto-os-data/modules/security-compliance/state/compliance-posture.md`.

**Writes:** `cto-os-data/modules/security-compliance/state/compliance-posture.md`, overwrite-with-history.

### `log-risk`

**Purpose:** Add a new risk to the register.

**Triggers:**
- "log a risk"
- "add to the risk register: [description]"
- "new finding from [source]"

**Reads:**
- `cto-os-data/modules/security-compliance/state/risks/` (check for duplicates)
- `cto-os-data/modules/security-compliance/state/controls/` (which controls are relevant)

**Writes:** `cto-os-data/modules/security-compliance/state/risks/{risk-slug}.md`, append-new-file with `status: open`.

### `update-risk`

**Purpose:** Revise an existing risk — severity reassessment, new mitigations, owner change, status transition (open → mitigating → monitored).

**Triggers:**
- "update risk [risk-slug]"
- "risk [X] got worse"
- "we added a mitigation on [risk]"

**Reads:** `cto-os-data/modules/security-compliance/state/risks/{risk-slug}.md`.

**Writes:** `cto-os-data/modules/security-compliance/state/risks/{risk-slug}.md`, overwrite-with-history.

### `resolve-risk`

**Purpose:** Close a risk as resolved or accepted (residual risk tolerated).

**Triggers:**
- "resolve risk [X]"
- "we mitigated [risk] — close it"
- "accept risk [X] — residual is fine"

**Reads:** `cto-os-data/modules/security-compliance/state/risks/{risk-slug}.md`.

**Writes:** `cto-os-data/modules/security-compliance/state/risks/{risk-slug}.md` — sets `status: resolved | accepted`, `closed_date`, resolution notes in body.

### `update-control`

**Purpose:** Add, update, or retire a control. Changes to control ownership, implementation status, regime mapping, or scope.

**Triggers:**
- "update control [X]"
- "[name] now owns [control]"
- "[control] is fully implemented"
- "add a new control for [purpose]"

**Reads:** `cto-os-data/modules/security-compliance/state/controls/{control-slug}.md` (if updating).

**Writes:** `cto-os-data/modules/security-compliance/state/controls/{control-slug}.md`, overwrite-with-history (for updates) or append-new-file (for new controls).

### `log-audit-event`

**Purpose:** Capture an audit event — SOC 2 Type 1 / Type 2 audit, ISO surveillance audit, customer security assessment, pentest engagement, internal audit. Records the scope, findings, and status.

**Triggers:**
- "log the SOC 2 Type 2 audit"
- "pentest findings just came in"
- "[customer] sent us a security questionnaire"
- "ISO surveillance audit scheduled"

**Reads:**
- `cto-os-data/modules/security-compliance/state/compliance-posture.md` (which regime this audit is against)
- `cto-os-data/modules/security-compliance/state/risks/` (findings may map to existing risks)

**Writes:** `cto-os-data/modules/security-compliance/state/audits/{YYYY-MM-DD}-{audit-slug}.md`, append-new-file.

### `update-soa`

**Purpose:** Maintain the ISO 27001 Statement of Applicability — which Annex A controls are in scope, which are excluded, and the justification for each. Invoked during ISO 27001 scoping, audit prep, or when controls land/retire.

**Triggers:**
- "update the Statement of Applicability"
- "SoA review for ISO audit"
- "add Annex A [X] to scope"

**Reads:**
- `cto-os-data/modules/security-compliance/state/statement-of-applicability.md`
- `cto-os-data/modules/security-compliance/state/controls/` (which implemented controls map to which Annex A)

**Writes:** `cto-os-data/modules/security-compliance/state/statement-of-applicability.md`, overwrite-with-history.

### `show-posture`

**Purpose:** Assemble a read-time rollup of current posture — NIST CSF view (which functions are covered, thin, or absent based on implemented controls); regime statuses; open risks summarized by severity; recent audit events.

**Triggers:**
- "show security posture"
- "NIST CSF rollup"
- "what's the risk picture right now"

**Reads:**
- `cto-os-data/modules/security-compliance/state/compliance-posture.md`
- `scan(type=["risk-register-entry"], where={"status": "open"}, fields=["slug", "severity", "likelihood", "category"])`
- `scan(type=["control"], fields=["slug", "nist_csf_functions", "implementation_status"])`
- `scan(type=["audit-event"], fields=["slug", "audit_type", "completed_date"])` (recent audits)

**Writes:** —

### `draft-risk-briefing`

**Purpose:** Compose a risk briefing for a specific audience — board, customer assessment response, CEO check-in. Pulls open risks, audit status, and recent events; frames through the audience's lens (board wants material risks and business impact; customer wants implementation evidence for their specific concerns).

**Triggers:**
- "draft the risk briefing for the board"
- "customer just asked for our security posture — compile the response"
- "write the risk summary for CEO 1:1"

**Reads:**
- `cto-os-data/modules/security-compliance/state/compliance-posture.md`
- `cto-os-data/modules/security-compliance/state/risks/` (open risks, especially high/critical)
- `cto-os-data/modules/security-compliance/state/audits/` (recent audit outcomes)
- `cto-os-data/modules/security-compliance/state/controls/` (implementation status for asked-about areas)
- `cto-os-data/modules/personal-os/state/voice/` (optional — tone)

**Writes:** —  (produces a draft for the user; board-facing output flows through Board Comms' `draft-pre-read` skill; customer-facing output is sent externally)

## Persistence

- **`cto-os-data/modules/security-compliance/state/compliance-posture.md`** — singleton (`slug: current`), overwrite-with-history. Frontmatter: `type: compliance-posture, slug: current, updated: <date>, regimes: <list of {name, status, owner, target_date, scope_statement}>, target_cis_ig: <string, optional>, nist_csf_notes: <string, optional>`. Body: narrative + `## History`.
- **`cto-os-data/modules/security-compliance/state/risks/{risk-slug}.md`** — one file per risk, overwrite-with-history. Frontmatter: `type: risk-register-entry, slug: <risk-slug>, updated: <date>, category: <data|access|availability|compliance|vendor|other>, severity: <low|medium|high|critical>, likelihood: <low|medium|high>, status: <open|mitigating|monitored|resolved|accepted>, owner: <string>, opened: <date>, closed_date: <date, optional>, related_controls: <list of control slugs>`. Body: description + current mitigations + `## History` of transitions.
- **`cto-os-data/modules/security-compliance/state/controls/{control-slug}.md`** — one file per control, overwrite-with-history. Frontmatter: `type: control, slug: <control-slug>, updated: <date>, name: <string>, cis_control_id: <string, optional>, nist_csf_functions: <list of {identify|protect|detect|respond|recover}>, soc2_criteria: <list, optional>, iso_annex_a: <list, optional>, owner: <string>, implementation_status: <not-implemented|partial|implemented|needs-remediation>`. Body: description + evidence references + `## History`.
- **`cto-os-data/modules/security-compliance/state/statement-of-applicability.md`** — singleton (`slug: current`), overwrite-with-history. Frontmatter: `type: statement-of-applicability, slug: current, updated: <date>, iso_version: <string>, annex_a_scope: <list of {control_id, status: applicable|excluded, justification, implementing_control: <control-slug>}>`. Body: narrative + `## History`.
- **`cto-os-data/modules/security-compliance/state/audits/{YYYY-MM-DD}-{audit-slug}.md`** — append-new-file per audit event. Frontmatter: `type: audit-event, slug: <YYYY-MM-DD>-<audit-slug>, updated: <date>, audit_type: <soc2-type1|soc2-type2|soc2-bridge|iso-surveillance|iso-recertification|pentest|customer-assessment|internal>, regime: <string, optional>, scope: <string>, started_date: <date>, completed_date: <date, optional>, status: <in-progress|completed|findings-open>, findings_open_count: <int>, findings_total_count: <int>`. Body sections: `## Scope`, `## Findings`, `## Remediation plan`, `## Status updates`.

**Overrides to the cross-cutting save rule** ([Persistence model](../../docs/ARCHITECTURE.md#persistence-model)): control-ownership and status transitions ask for confirmation — these are governance artifacts that shouldn't accrete casually. Audit-event captures during active audits may happen iteratively; first write captures initial scope, subsequent updates add findings and status as they come in.

**Sensitivity:** `sensitivity: high` at module level. Risk registers, audit findings, unpatched vulnerabilities, and control gaps are damaging if leaked — they're a map of the org's security weaknesses. Scan excludes this module's state by default; callers opt in explicitly. Cross-module consumers (Board Comms drafting a risk briefing) should reference-by-path but not inline raw risk-register content except to the extent the board audience is authorized to see it.

## State location

`cto-os-data/modules/security-compliance/state/`
