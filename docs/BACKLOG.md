# Module backlog

Scope, frameworks, and dependencies for modules not yet implemented. Each entry is the seed of what will become a `modules/{slug}/README.md` when the module lands.

**How to graduate a module out of this file:**

1. Create `modules/{slug}/` in the skill repo. Seed its `README.md` from this entry.
2. Write `modules/{slug}/SKILL.md` per [docs/SKILL_REPO.md → Per-module SKILL.md format](./SKILL_REPO.md#per-module-skillmd-format).
3. Add the module's type schemas to [meta/schema.md](../meta/schema.md).
4. Remove the entry from this file.
5. Move the module from "Planned" to "Implemented" in the root [README.md](../README.md).

---

## Activation priority tiers (PRD §6)

Recommended sequence when adopting. Per-module tier is also noted in each entry below.

- **Foundations** (zero outbound dependencies; unlock most downstream capability): *(all three — Personal OS, Process Management, Business Alignment — are implemented.)*
- **Daily drivers** (high operational value, low dependency cost): *(all implemented — Attention & Operations, Team Management, Managing Up / Down / Sideways.)*
- **Role-shape** (match the shape of the specific job): Budget. *(Tech Ops, Technical Strategy, and Hiring are already implemented.)*
- **Strategic and periodic** (low-frequency, high-leverage): Org Design. *(Performance & Development, Board Comms, and Organizational Communications are already implemented.)*
- **Optional by role**: External Network & Thought Leadership, Code Contribution Opportunities, Security & Compliance.

---

## Personal

<a id="external-network"></a>
### External Network & Thought Leadership

- **Slug:** `external-network`
- **Activation priority:** Optional by role.
- **Scope:** External relationships and public presence as a leader. Peer CTOs, advisors, mentors/mentees, industry peers. Conference speaking, public writing, community engagement.
- **Out of scope:** Internal thought leadership (Managing Down for your org; Org Comms for broader internal audiences; Technical Strategy for the substance of technical positioning). Internal peer relationships (Managing Sideways).
- **Frameworks:**
  - [Granovetter — *The Strength of Weak Ties*](https://www.jstor.org/stable/2776392) — why broader networks beat deeper ones for information flow; who to cultivate and why.
  - [Dorie Clark — *Stand Out*](https://dorieclark.com/standout/) — thought-leadership posture, content cadence, platform-building.
- **Depends on:**
  - Required: none
  - Optional: `personal-os` (voice, show-up, stated intent), `attention-operations` (flags external items needing response)
- **Example tasks:**
  - "I'm speaking at QCon next month — help me draft the outline."
  - "Prep for coffee with Jane (peer CTO at AcmeCo)."
  - "Draft a LinkedIn post about our platform migration."
  - "I want to ramp up a mentoring practice — who should I prioritize?"
- **Target state location:** `cto-os-data/modules/external-network/state/`

---

## Operations

---

## Strategic

<a id="org-design"></a>
### Org Design

- **Slug:** `org-design`
- **Activation priority:** Strategic and periodic.
- **Scope:** Optimizing how your department is organized to deliver value. Using the value-flow lens to decide team structure, capacity allocation, and bottleneck fixes. Low-frequency, high-leverage.
- **Out of scope:** Day-to-day team health (Team Management); hiring execution (Hiring).
- **Frameworks:**
  - [Matthew Skelton & Manuel Pais — *Team Topologies*](https://teamtopologies.com/) — team types, interaction modes, reverse Conway maneuver.
  - [Conway's Law](https://en.wikipedia.org/wiki/Conway%27s_law) — org structure constrains system architecture; design team boundaries with intended software boundaries in mind.
  - Value-flow lens — drawn from Process Management / Reinertsen (via the required dependency).
- **Depends on:**
  - Required: `process-management`, `business-alignment`
  - Optional: `team-management` (current team state), `hiring` (hiring plan feasibility), `budget` (cost of proposed changes)
- **Example tasks:**
  - "Draft a reorg proposal: merge platform and infra-ops into a single team."
  - "We have a bottleneck at the integration layer — what are the options?"
  - "Re-allocate 20% of engineering capacity from product to platform — walk through the tradeoffs."
  - "Capture the decision: we're adopting a stream-aligned model."
- **Target state location:** `cto-os-data/modules/org-design/state/`

---

## Communication

---

## People & execution

<a id="code-contribution"></a>
### Code Contribution Opportunities

- **Slug:** `code-contribution`
- **Activation priority:** Optional by role.
- **Scope:** Staying technically engaged at the right level. Identifying where your hands-on contribution would create disproportionate value — knotty problems, architecturally important spots, learning opportunities.
- **Out of scope:** Strategic technical direction (Technical Strategy); routine PR review (owned by the teams whose work it is).
- **Frameworks:**
  - [Donald Reinertsen — *The Principles of Product Development Flow*](https://www.amazon.com/Principles-Product-Development-Flow-Generation/dp/1935401009) — bottleneck identification; marginal value of contribution. Used as an opportunity-spotting lens, not a primary framework.
- **Depends on:**
  - Required: none
  - Optional: `personal-os` (stated intent — e.g., "stay technical" or "X PRs/quarter" — shifts how aggressively opportunities are surfaced), `technical-strategy` (platform priorities guide where contribution matters most), `tech-ops` (reliability gaps as contribution opportunities), `process-management`
- **Example tasks:**
  - "Scan the PRs open this week — where should I dive in?"
  - "Find me an architecturally interesting ticket to take this sprint."
  - "Is there a knotty bug that would teach me the new subsystem?"
  - "I haven't shipped code in a month — nudge me."
- **Target state location:** `cto-os-data/modules/code-contribution/state/`

---

## Governance

<a id="security-compliance"></a>
### Security & Compliance

- **Slug:** `security-compliance`
- **Activation priority:** Optional by role.
- **Scope:** Managing the security and compliance posture of the organization. Understanding risk, ensuring controls are working, meeting obligations to customers and regulators. Security program measurement, compliance reporting, audit responses, risk register maintenance, coordination with Tech Ops on security incidents.
- **Out of scope:** Operational incident response and remediation (Tech Ops owns incident operations; Security & Compliance surfaces the risk picture).
- **Frameworks:**
  - [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework) — Identify / Protect / Detect / Respond / Recover as the canonical posture lens.
  - [CIS Critical Security Controls](https://www.cisecurity.org/controls) — practical, prioritized control inventory for measuring and improving posture.
- **Depends on:**
  - Required: none
  - Optional: `tech-ops` (security incidents feed risk picture), `technical-strategy` (security-relevant tech decisions)
- **Example tasks:**
  - "Update the risk register with findings from the Q2 pentest."
  - "Draft the SOC 2 control-ownership matrix."
  - "Prep the security section of the board deck."
  - "A customer asked for our security posture — compile the response."
- **Target state location:** `cto-os-data/modules/security-compliance/state/`
- **Sensitivity:** high (risk register, audit findings, unpatched vulnerabilities).

<a id="budget"></a>
### Budget

- **Slug:** `budget`
- **Activation priority:** Role-shape (for P&L-owning roles).
- **Scope:** Financial stewardship of your organization. Understanding where money goes, planning for the future, tracking actuals against plan. Headcount planning and cost, vendor and software spend, capex vs opex decisions, cost allocation, budget-to-actual tracking, forecast and planning.
- **Out of scope:** Build-vs-buy decisions themselves (Technical Strategy makes the call; Budget provides cost context).
- **Frameworks:**
  - No single canonical framework cited. Uses standard financial-planning concepts: fully-loaded headcount cost, capex vs opex, unit economics per customer or per request, zero-based budgeting as a periodic reset lens.
  - If a specific discipline becomes central, upgrade to a named framework (candidates: [Geoffrey Moore — *Core vs Context*](https://a16z.com/the-core-vs-context-model/) for "where to spend" framing).
- **Depends on:**
  - Required: none
  - Optional: `hiring` (open reqs and planned hires drive headcount cost), `tech-ops` (infrastructure spend), `business-alignment` (financial context, company targets), `technical-strategy` (build-vs-buy cost decisions)
- **Example tasks:**
  - "Forecast Q3 eng spend given the current hiring plan."
  - "Capex vs opex decision on the new GPU cluster."
  - "Compare vendor spend this quarter to last — what's drifted?"
  - "Draft the engineering budget narrative for the CFO."
- **Target state location:** `cto-os-data/modules/budget/state/`
