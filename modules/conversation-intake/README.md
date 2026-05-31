# Conversation Intake

**Scope:** Turn raw meeting transcripts (Granola-style or plain text the user pastes) into structured records routed to the right modules. Extracts decisions, action items, observations, direct quotes, and open questions; applies an altitude-relative significance bar so only durable / strategic items are offered for saving (CTO OS is not a tactical decision log); routes capture-worthy decisions to native types where the target module owns one (`adr`, `design-decision`, `prioritization-decision`) and generic intake types everywhere else; cross-checks against existing module state for conflicts and opportunities; presents a confirmation summary that splits "to capture" from "everything else"; writes only after explicit user approval. First skill in the module is `transcript`; room for siblings (async-thread, voice-memo) later.

**Out of scope:** Real-time audio capture; Slack thread ingestion; loose user-jotted notes (use `working-note` instead); transcripts of meetings the user wasn't a participant in; storing the raw transcript itself (only structured records with light provenance — meeting date, time, attendees — are written).

**Frameworks:** None. Infrastructure-style design invariants instead: never write before user confirmation; never assume (ask for speaker labels, missing context, conflict resolution); decision and goal conflicts block the flow; no personal-life content or third-party PII; concerns and opportunities are theories with cited evidence, never facts.

**Depends on:**
- Required: none
- Optional: none (the skill dynamically scans whatever modules are active for routing and conflict-checking — no hard dependency on any specific module)

**Example tasks:**
- "Process this transcript." *(pasted Granola-style block follows)*
- "Pull the decisions and action items out of my meeting with Mike."
- "Here's what we covered in the board call — capture it."
- "Log my staff meeting from this morning."

**State location:** `cto-os-data/modules/conversation-intake/state/` — empty by design. Every captured record routes out to a target module: generic items to its `state/intake/` subtree (e.g., `cto-os-data/modules/managing-down/state/intake/action-items/2026-05-30-coach-mike.md`), and decisions routed to a module with a native decision type to that module's native path as a draft (e.g., `cto-os-data/modules/technical-strategy/state/adrs/dual-write-removal.md` with `status: proposed`).

**Sensitivity:** standard at the module level. Extracted records inherit the sensitivity of the target module — a decision routed to `performance-development` (high) becomes high-sensitivity automatically; one routed to `process-management` stays standard.
