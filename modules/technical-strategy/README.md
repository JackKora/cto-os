# Technical Strategy

**Scope:** Setting the technical direction of the organization. Where the technology is going, what to build vs. buy, what platforms we bet on, how we invest in R&D, how we track and pay down tech debt. Owns both strategy documents (Larson-style) and architecture decision records (Nygard ADRs). Role-shape module — important for CTOs/VPEs, weightier the larger and more technically complex the org.

**Out of scope:** Flow and process improvement (Process Management); reliability and production ops (Tech Ops); team structure decisions (Org Design); strategic hiring execution (Hiring); pure cost analysis (Budget).

**Frameworks:** [Will Larson — *An Elegant Puzzle*](https://lethain.com/elegant-puzzle/), [Michael Nygard — ADRs](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions).

**Depends on:**
- Required: none
- Optional: `business-alignment` (strategy should serve company goals), `budget` (cost context for build-vs-buy), `tech-ops` (current reliability constraints shape what's feasible), `process-management` (flow implications of strategic shifts)

**Example tasks:**
- "Write a platform strategy doc for the next 18 months."
- "ADR for the messaging-platform decision: Kafka vs SQS vs Pulsar."
- "Prioritize tech debt for this quarter."
- "Supersede the old monorepo ADR — we've reversed course."
- "We paid down the session-store debt — capture the resolution."

**State location:** `cto-os-data/modules/technical-strategy/state/`
