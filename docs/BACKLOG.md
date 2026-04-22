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

- **Foundations** (zero outbound dependencies; unlock most downstream capability): Process Management, Business Alignment. *(Personal OS is already implemented.)*
- **Daily drivers** (high operational value, low dependency cost): Team Management, Managing Up, Managing Down, Managing Sideways. *(Attention & Operations is already implemented.)*
- **Role-shape** (match the shape of the specific job): Tech Ops, Technical Strategy, Hiring, Budget.
- **Strategic and periodic** (low-frequency, high-leverage): Org Design, Performance & Development, Board Comms, Organizational Communications.
- **Optional by role**: External Network & Thought Leadership, Code Contribution Opportunities, Security & Compliance.

---

## Stakeholder management

<a id="managing-up"></a>
### Managing Up

- **Slug:** `managing-up`
- **Activation priority:** Daily driver.
- **Scope:** Managing the relationship, narrative, and perception upward with whoever you report to. Translating your team's work into a story that resonates at higher altitude.
- **Out of scope:** Stakeholder-profile building for peers (Managing Sideways) or reports (Managing Down); external advisors and mentors (External Network & Thought Leadership).
- **Frameworks:**
  - [Andy Grove — *High Output Management*](https://www.amazon.com/High-Output-Management-Andrew-Grove/dp/0679762884) — managing-your-manager dynamics; executive altitude framing.
  - Stakeholder-needs analysis — observable preferences (communication channel, cadence, what they want first) per the cross-cutting stakeholder profile format.
- **Depends on:**
  - Required: none
  - Optional: `personal-os` (voice, show-up, stated intent), `business-alignment` (company goals context), `team-management` (reporting team progress upward), `attention-operations` (flags boss-originated items)
- **Example tasks:**
  - "Prep for my 1:1 with my manager tomorrow — here's what's top of mind."
  - "Draft an executive summary of this quarter's platform work for my boss."
  - "Help me sell the reorg idea upward before I pitch it formally."
  - "My boss pushed back on the hiring ask — help me reframe."
- **Target state location:** `cto-os-data/modules/managing-up/state/`

<a id="managing-down"></a>
### Managing Down

- **Slug:** `managing-down`
- **Activation priority:** Daily driver.
- **Scope:** Leading and developing the people who report to you directly. Maintaining leadership presence, clarity of direction, and the relationships that make a team work. 1:1s, coaching, delegation, team-wide communication.
- **Out of scope:** Individual-level performance tracking and calibration (Performance & Development); team-aggregate health (Team Management). This module is about the leadership relationship, not the administrative side of people management.
- **Frameworks:**
  - [Radical Candor (Kim Scott)](https://www.radicalcandor.com/) — feedback grounded in specific behavior; care personally, challenge directly.
  - [Andy Grove — *High Output Management*](https://www.amazon.com/High-Output-Management-Andrew-Grove/dp/0679762884) — 1:1 structure, delegation, task-relevant maturity.
- **Depends on:**
  - Required: none
  - Optional: `team-management` (who your reports are), `performance-development` (performance context for coaching), `personal-os` (voice, show-up), `attention-operations`
- **Example tasks:**
  - "Prep for my 1:1 with Jane — last time she raised scope concerns."
  - "Draft team-wide comms for the reorg announcement."
  - "Mike's been drifting — help me think through how to redirect him."
  - "Write a delegation note handing the roadmap to my staff engineer."
- **Target state location:** `cto-os-data/modules/managing-down/state/`
- **Sensitivity:** high (1:1 content, coaching notes).

<a id="managing-sideways"></a>
### Managing Sideways

- **Slug:** `managing-sideways`
- **Activation priority:** Daily driver.
- **Scope:** Building and maintaining the lateral relationships that make cross-functional work possible. Getting things done with peers where you have no reporting authority.
- **Out of scope:** External peer relationships outside the company (External Network & Thought Leadership); internal upward or downward relationships.
- **Frameworks:**
  - [Cohen & Bradford — *Influence Without Authority*](https://www.amazon.com/Influence-Without-Authority-Allan-Cohen/dp/0471463302) — currency-of-exchange thinking for peer negotiation.
  - [Fisher & Ury — *Getting to Yes*](https://www.amazon.com/Getting-Yes-Negotiating-Agreement-Without/dp/0143118757) — principled negotiation; separate people from problem.
- **Depends on:**
  - Required: none
  - Optional: `business-alignment` (shared goals context), `personal-os` (voice, show-up), `attention-operations`
- **Example tasks:**
  - "Prep for my 1:1 with the CPO — we're negotiating roadmap tradeoffs."
  - "Help me build the coalition for the SOC 2 push across eng, sales, and legal."
  - "Draft a peer-feedback note for the VP of Sales — the handoff process is breaking."
  - "I need something from Marketing but they keep deprioritizing — reframe the ask."
- **Target state location:** `cto-os-data/modules/managing-sideways/state/`

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

<a id="team-management"></a>
### Team Management

- **Slug:** `team-management`
- **Activation priority:** Daily driver.
- **Scope:** The ongoing health and performance of the teams in your org, at the team-aggregate level. How teams are doing against their goals, how they're staffed, how they're evolving.
- **Out of scope:** Individual-level performance and development (Performance & Development); strategic team structure changes (Org Design makes the decisions, Team Management tracks the current reality); 1:1 notes and direct-report work (Managing Down).
- **Frameworks:**
  - [Matthew Skelton & Manuel Pais — *Team Topologies*](https://teamtopologies.com/) — four team types (stream-aligned, enabling, complicated-subsystem, platform); team cognitive load.
  - [Patrick Lencioni — *The Five Dysfunctions of a Team*](https://www.tablegroup.com/product/dysfunctions/) — trust, conflict, commitment, accountability, results. Diagnostic lens for team health.
- **Depends on:**
  - Required: none
  - Optional: `hiring` (headcount changes, incoming ramps), `performance-development` (individual trends roll up to team view)
- **Example tasks:**
  - "How is the platform team trending over the last two quarters?"
  - "Log a team retro for the growth squad's Q2."
  - "We need to rebalance headcount — show me current team composition."
  - "Run the team-health rubric on infra-ops."
- **Target state location:** `cto-os-data/modules/team-management/state/`

<a id="tech-ops"></a>
### Tech Ops

- **Slug:** `tech-ops`
- **Activation priority:** Role-shape (for hands-on-tech CTOs).
- **Scope:** Running production reliably. The operational state of systems that serve customers — availability, performance, risk, readiness. Incident management, SLOs, on-call rotations, reliability engineering, postmortems.
- **Out of scope:** Strategic technical direction (Technical Strategy); SDLC and development flow (Process Management).
- **Frameworks:**
  - [Google — *Site Reliability Engineering*](https://sre.google/sre-book/table-of-contents/) — SLOs, error budgets, toil, on-call discipline.
  - [DORA](https://dora.dev/) — continuous delivery + reliability metrics (deploy frequency, lead time, change-fail rate, MTTR).
  - [John Allspaw — blameless postmortems](https://www.etsy.com/codeascraft/blameless-postmortems) — learning-oriented incident review.
- **Depends on:**
  - Required: none
  - Optional: `team-management` (who's on-call, team capacity for incident load), `technical-strategy` (platform constraints shape what's operationally possible)
- **Example tasks:**
  - "Write up the postmortem for yesterday's S1."
  - "How are we trending on our primary SLO this quarter?"
  - "On-call load is spiking — help me think through why."
  - "Draft the reliability section of this quarter's ops review."
- **Target state location:** `cto-os-data/modules/tech-ops/state/`

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

<a id="process-management"></a>
### Process Management

- **Slug:** `process-management`
- **Activation priority:** Foundation.
- **Scope:** How work moves through your organization from idea to customer. The operating flows that deliver value. Owns measurement and continuous improvement of these flows. Includes Product Management, SDLC, and Data Science as sub-flows.
- **Out of scope:** Specific project execution (happens inside the flows, owned by teams doing the work); reliability and incident response (Tech Ops).
- **Frameworks:**
  - [Donald Reinertsen — *The Principles of Product Development Flow*](https://www.amazon.com/Principles-Product-Development-Flow-Generation/dp/1935401009) — queues, batch sizes, WIP constraints, variability, cost of delay. Explicitly cited in the PRD as the foundational framework.
- **Depends on:**
  - Required: none (foundational)
  - Optional: none
- **Example tasks:**
  - "What's our current cycle-time trend across PM, SDLC, and DS?"
  - "Run a flow retro on the PM sub-flow for Q2."
  - "We have WIP creeping up in SDLC — help me identify the bottleneck."
  - "Decide whether to adopt a two-tier PR review."
- **Target state location:** `cto-os-data/modules/process-management/state/`

<a id="business-alignment"></a>
### Business Alignment

- **Slug:** `business-alignment`
- **Activation priority:** Foundation.
- **Scope:** The connection between what your organization does and what the business needs. Tracks company goals, pulls external signal from customer-facing teams, drives CTO-level customer engagement, and makes work-to-goals ties visible.
- **Out of scope:** Board-level strategic communication (Board Comms consumes this module's data); internal comms that report on goals progress (Org Comms consumes this module's data).
- **Frameworks:**
  - [Colin Bryar & Bill Carr — *Working Backwards*](https://www.amazon.com/Working-Backwards-Insights-Stories-Secrets/dp/1250267595) — customer-backwards thinking, press-release-first product definition, input/output metrics.
  - [Clayton Christensen — Jobs to be Done](https://hbr.org/2016/09/know-your-customers-jobs-to-be-done) — customer-need framing; the "job" the customer is hiring your product to do.
- **Depends on:**
  - Required: none (foundational)
  - Optional: none
- **Sub-areas:**
  - Company goals (tracked)
  - External signal inbound (from sales / marketing / support / onboarding)
  - Customer engagement outbound (CTO-level customer interactions — advisory boards, sales calls, exec sponsor relationships, customer escalations, industry events; cadence set at activation)
  - Work-to-goals ties (making alignment visible)
- **Example tasks:**
  - "Capture Q2 company goals and tie them to our engineering priorities."
  - "I had a customer advisory call — capture the signal."
  - "Show me the work-to-goals heatmap for this quarter."
  - "Draft the engineering update for the CEO's all-hands."
- **Target state location:** `cto-os-data/modules/business-alignment/state/`

<a id="technical-strategy"></a>
### Technical Strategy

- **Slug:** `technical-strategy`
- **Activation priority:** Role-shape.
- **Scope:** Setting the technical direction of the organization. Where the technology is going, what we build vs buy, what platforms we bet on, how we invest in R&D, how we manage tech debt.
- **Out of scope:** Process flow (Process Management); reliability and operations (Tech Ops); specific project execution.
- **Frameworks:**
  - [Will Larson — *An Elegant Puzzle: Systems of Engineering Management*](https://lethain.com/elegant-puzzle/) — modern CTO/VPE reference for strategy writing, platform thinking, and org-tech alignment.
  - [Michael Nygard — ADRs (Architecture Decision Records)](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions) — lightweight, durable format for capturing technical decisions (context, options, choice, consequences, review).
- **Depends on:**
  - Required: none
  - Optional: `business-alignment` (strategy should serve company goals), `budget` (cost context for build-vs-buy), `tech-ops` (current reliability constraints shape what's feasible), `process-management` (flow implications of strategic shifts)
- **Example tasks:**
  - "Draft an ADR for the messaging-platform decision: Kafka vs SQS vs Pulsar."
  - "Write up our platform strategy for the next 18 months."
  - "Build-or-buy analysis on the internal feature-flag system."
  - "Prioritize the tech debt backlog — what pays off now vs later?"
- **Target state location:** `cto-os-data/modules/technical-strategy/state/`

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

<a id="hiring"></a>
### Hiring

- **Slug:** `hiring`
- **Activation priority:** Role-shape (for growth-phase orgs).
- **Scope:** Bringing talented people into the organization. Owns the full hiring lifecycle from identifying a need through to the person being fully productive. Workforce planning, sourcing, interviewing, offer construction and negotiation, onboarding, ramp.
- **Out of scope:** Ongoing performance after ramp (Performance & Development); team-aggregate health (Team Management).
- **Frameworks:**
  - [Geoff Smart & Randy Street — *Who: The A Method for Hiring*](https://www.amazon.com/Who-Geoff-Smart/dp/0345504194) — scorecard-driven, structured, outcome-focused interviewing.
  - [Google structured interviewing (re:Work)](https://rework.withgoogle.com/guides/hiring-use-structured-interviewing/) — consistent questions, rubric scoring, reduced bias through structure.
- **Depends on:**
  - Required: none
  - Optional: `business-alignment` (hiring plan ties to company goals), `budget` (headcount cost), `team-management` (where new hires land)
- **Example tasks:**
  - "Open the requisition for the staff SRE role — write the scorecard."
  - "Prep the debrief for today's VP Eng candidate."
  - "Draft the offer for Jane — here's the comp ask."
  - "Design the first-30-days plan for Mike joining next week."
- **Target state location:** `cto-os-data/modules/hiring/state/`

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
