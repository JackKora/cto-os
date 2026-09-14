# Security & Compliance

**Scope:** The CTO-level view of the security program and compliance obligations. Risk register maintenance, control inventory with ownership and regime mapping, compliance regime status tracking (SOC 2, ISO 27001, HIPAA, etc.), ISO 27001 Statement of Applicability, audit event capture (SOC 2 Type 1/2, ISO surveillance, customer assessments, pentests), posture rollup, and source risk summaries for downstream communications.

**Out of scope:** Board-facing narrative and pre-read authorship (Board Comms owns those and may consume a source risk summary from this module); security-incident operational response (Tech Ops runs incidents; this module captures the resulting risk picture); security-adjacent architecture decisions (Technical Strategy makes those; this module informs them); legal conclusions, notification or contractual obligations, regulator/counsel workflow, and legal deadlines (Legal owns those); policy authoring and document management (legal/HR systems); employee security training execution; threat intelligence and active threat-hunting; vulnerability scanner infrastructure (this module tracks findings, not the scanner).

**Frameworks:** Four, with distinct purposes:
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework) — strategic posture lens (Identify / Protect / Detect / Respond / Recover).
- [CIS Critical Security Controls](https://www.cisecurity.org/controls) — prescriptive control catalog (IG1/IG2/IG3 maturity).
- [ISO/IEC 27001](https://www.iso.org/isoiec-27001-information-security.html) — international certifiable ISMS standard.
- [SOC 2](https://www.aicpa-cima.com/topic/audit-assurance/audit-and-assurance-greater-than-soc-2) — AICPA audit (Trust Services Criteria, Type 1 / Type 2).

**Depends on:**
- Required: none
- Optional: `tech-ops` (security incidents feed the risk picture), `technical-strategy` (security-relevant decisions), `legal` (confirmed legal obligations and linked matter status when they determine compliance scope, timing, or briefing context)

**Example tasks:**
- "Log a new risk — third-party library with known CVE."
- "We just completed SOC 2 Type 2 — update posture and log the audit event."
- "Summarize security risk posture for the next board pre-read."
- "Update the Statement of Applicability — we're scoping out Annex A.5.3."
- "Customer sent a security questionnaire — compile the response from current posture."

**State location:** `cto-os-data/modules/security-compliance/state/`

**Sensitivity:** high (risk register, audit findings, unpatched vulnerabilities — a map of the org's security weaknesses).
