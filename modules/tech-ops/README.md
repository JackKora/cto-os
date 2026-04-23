# Tech Ops

**Scope:** Running production reliably. SLOs and error budgets, incident lifecycle management (detection → response → resolution), blameless postmortems, reliability posture declarations, on-call load trends. Role-shape module for hands-on-tech CTOs and VPEs where production reliability is a first-order part of the role.

**Out of scope:** Strategic technical direction (Technical Strategy); SDLC and development flow (Process Management); team-aggregate health (Team Management); on-call rotation schedules (PagerDuty/Opsgenie own those); security risk posture (Security & Compliance, though Tech Ops runs security-incident *operations* when one occurs).

**Frameworks:** [Google — *Site Reliability Engineering*](https://sre.google/sre-book/table-of-contents/), [DORA](https://dora.dev/), [Allspaw — blameless postmortems](https://www.etsy.com/codeascraft/blameless-postmortems).

**Depends on:**
- Required: none
- Optional: `team-management` (who's on-call, team capacity for incident load), `technical-strategy` (platform choices shape what's operationally possible)

**Example tasks:**
- "Log an S1 — auth tier is degraded."
- "Cut a postmortem for yesterday's database outage."
- "What's our error budget looking like for checkout?"
- "Define an SLO for the session pipeline at 99.9% over 30 days."
- "Show me reliability across all SLOs and open action items from recent postmortems."

**State location:** `cto-os-data/modules/tech-ops/state/`
