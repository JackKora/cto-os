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
- **Role-shape** (match the shape of the specific job): *(all four — Tech Ops, Technical Strategy, Hiring, Budget — are implemented.)*
- **Strategic and periodic** (low-frequency, high-leverage): *(all four — Org Design, Performance & Development, Board Comms, Organizational Communications — are implemented.)*
- **Optional by role**: External Network & Thought Leadership, Code Contribution Opportunities. *(Security & Compliance is already implemented.)*

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
