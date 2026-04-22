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
- **Strategic and periodic** (low-frequency, high-leverage): Org Design, Performance & Development, Board Comms, Organizational Communications.
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

<a id="org-comms"></a>
### Organizational Communications

- **Slug:** `org-comms`
- **Activation priority:** Strategic and periodic.
- **Scope:** How you communicate to internal audiences at scale. The voice of leadership coming through recurring and ad-hoc updates. Maintaining clarity, consistency, and connection between the work and the broader context. Regular written/spoken updates, progress-against-goals narratives, all-hands content, internal incident comms, cross-functional announcements.
- **Out of scope:** Board-level comms (Board Comms); external comms and thought leadership (External Network & Thought Leadership); day-to-day 1:1 or team comms (Managing Down).
- **Frameworks:**
  - [Amazon narrative format / 6-pager](https://www.amazon.com/Working-Backwards-Insights-Stories-Secrets/dp/1250267595) — prose over bullets; memos as argument structure.
  - [Barbara Minto — *The Pyramid Principle*](https://www.amazon.com/Pyramid-Principle-Logic-Writing-Thinking/dp/0273710516) — top-down reasoning; lead with the answer; structured argument.
- **Depends on:**
  - Required: none
  - Optional: `personal-os` (voice and show-up for tone), `business-alignment` (goals-tying), `team-management` / `tech-ops` / `process-management` (source material). Falls back to generic professional voice when Personal OS is inactive.
- **Example tasks:**
  - "Draft the engineering section of this month's all-hands."
  - "Write the internal incident comms for yesterday's S1."
  - "Announce the reorg to the eng org — audience is ICs + managers."
  - "Quarterly progress-against-goals update — we're on track for 2 of 3."
- **Target state location:** `cto-os-data/modules/org-comms/state/`

<a id="board-comms"></a>
### Board Comms

- **Slug:** `board-comms`
- **Activation priority:** Strategic and periodic.
- **Scope:** How you communicate with the board. Strategic narrative at the highest altitude — where the business is, where it's going, what the risks are, what's changing. Quarterly board updates, pre-read decks, fundraising narrative, KPI reporting, risk and competitive context briefings.
- **Out of scope:** Operational internal comms (Org Comms); peer or investor relationships outside board meetings (External Network & Thought Leadership).
- **Frameworks:**
  - [Brad Feld & Mahendra Ramsinghani — *Startup Boards*](https://feld.com/category/books/startup-boards/) — board-director perspective; what they actually want from a CTO update.
  - [Amazon narrative format / 6-pager](https://www.amazon.com/Working-Backwards-Insights-Stories-Secrets/dp/1250267595) — argument-first structure for the pre-read.
- **Depends on:**
  - Required: `business-alignment` (goals), `process-management` (KPIs from value flow)
  - Optional: `tech-ops` (material incidents), `security-compliance` (material risks), `hiring` (exec-level changes), `budget` (financial position), `personal-os` (voice + show-up)
- **Example tasks:**
  - "Draft the CTO section of the Q2 board deck."
  - "Write the risk briefing for next week's board meeting."
  - "Fundraising prep — narrative for the technical due-diligence session."
  - "Capture the board's feedback from yesterday and distill follow-ups."
- **Target state location:** `cto-os-data/modules/board-comms/state/`
- **Sensitivity:** high (board-level material risks, financial posture, strategic shifts).

---

## People & execution

<a id="performance-development"></a>
### Performance & Development

- **Slug:** `performance-development`
- **Activation priority:** Strategic and periodic.
- **Scope:** Developing the people you've hired over the arc of their careers. Maintaining a clear view of individual performance, growth, and trajectory. Performance tracking over time, calibration and leveling, promotion recommendations, development plans, performance concerns / PIPs, succession planning.
- **Out of scope:** Pre-ramp hiring pipeline (Hiring); team-aggregate health (Team Management); day-to-day coaching (Managing Down).
- **Frameworks:**
  - [Kim Scott — *Radical Candor*](https://www.radicalcandor.com/) — feedback discipline; performance conversations grounded in specific behavior + impact.
  - [Carol Dweck — *Mindset* (growth mindset)](https://www.amazon.com/Mindset-Psychology-Carol-S-Dweck/dp/0345472322) — development framing: ability is cultivable; feedback targets behavior and learning, not identity.
- **Depends on:**
  - Required: `team-management`
  - Optional: `hiring` (ramp state transitions into ongoing performance), `managing-down` (1:1 signal feeds performance awareness)
- **Example tasks:**
  - "Draft a performance review for Jane — here's the cycle's input."
  - "Prep for calibration — where does Mike sit relative to his level?"
  - "Build a promotion case for Alex to senior staff."
  - "Draft a performance-improvement plan for [report] — here's the context."
- **Target state location:** `cto-os-data/modules/performance-development/state/`
- **Sensitivity:** high (performance records, PIPs, calibration).

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
