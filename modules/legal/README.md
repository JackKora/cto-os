# Legal

**Scope:** The CTO's legal operating layer for issue spotting, preparation, workflow, and tracking: general legal intake and triage; commercial contracts; corporate governance and transactions, including M&A; IP and licensing, including OSS; employment legal matters; privacy, data protection, and product regulation; disputes and investigations; legal obligations; counsel briefing; and legal-posture rollup. It does not substitute for qualified legal counsel or make definitive legal conclusions.

**Out of scope:** Tax, real estate, antitrust, environmental, export-controls and sanctions, and every other specialty practice not named in scope. Also excluded: security-control operations, commercial economics and customer strategy, ordinary people-management execution, architecture and product decisions, relationship management with legal leaders, board narrative, document storage, e-signature workflow, and definitive legal advice or conclusions.

**Frameworks:** Module-native operational invariants: route before analysis; separate sourced facts, assertions, unknowns, and issue spots; escalate by consequence and clock; persist the minimum necessary; treat privilege labels as handling cues rather than privilege determinations; and preserve potentially relevant material.

**Depends on:**
- Required: none
- Optional: `security-compliance`, `technical-strategy`, `product`, `hiring`, `performance-development`, `tech-ops`

**Example tasks:**
- "The customer sent an MSA with redlines — organize the open points and questions for counsel."
- "Can we ship this OSS dependency, and what facts does counsel need?"
- "We received a demand letter — capture the response clock and prepare the counsel handoff."
- "Track the contractual notice deadline and show me what's due this month."
- "Show our current legal posture by matter, urgency, and obligation."

**State location:** `cto-os-data/modules/legal/state/`

**Sensitivity:** high. Legal state may contain confidential strategy, allegations, dispute context, employment information, or counsel-related workflow. Storage or a `privilege-sensitive` handling cue does not create attorney-client privilege or work-product protection.
