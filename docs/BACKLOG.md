# Module backlog

Scope, frameworks, and dependencies for modules not yet implemented. Each entry is the seed of what will become a `modules/{slug}/README.md` when the module lands.

**How to graduate a module out of this file:**

1. Create `modules/{slug}/` in the skill repo. Seed its `README.md` from this entry.
2. Write `modules/{slug}/SKILL.md` per [docs/SKILL_REPO.md → Per-module SKILL.md format](./SKILL_REPO.md#per-module-skillmd-format).
3. Add the module's type schemas to [meta/schema.md](../meta/schema.md).
4. Remove the entry from this file.
5. Move the module from "Planned" to "Implemented" in the root [README.md](../README.md).

---

## Status

**All PRD-defined modules are implemented.** The backlog is empty as of the completion of batch 6.

This file remains in the repo as the home for any future modules that get proposed — add an entry here first (scope, frameworks, deps, examples, target state location), then graduate it out following the procedure above.

---

## Activation priority tiers (PRD §6)

Kept for reference. All modules are implemented; per-module tiers are captured in each module's `SKILL.md` activation notes.

- **Foundations** (zero outbound dependencies; unlock most downstream capability): Personal OS, Process Management, Business Alignment.
- **Daily drivers** (high operational value, low dependency cost): Attention & Operations, Team Management, Managing Up / Down / Sideways.
- **Role-shape** (match the shape of the specific job): Tech Ops, Technical Strategy, Hiring, Budget.
- **Strategic and periodic** (low-frequency, high-leverage): Org Design, Performance & Development, Board Comms, Organizational Communications.
- **Optional by role**: External Network & Thought Leadership, Code Contribution Opportunities, Security & Compliance.
