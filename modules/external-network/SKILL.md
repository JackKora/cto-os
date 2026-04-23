---
name: external-network
description: "Activates for the user's external relationships and public presence as a senior engineering leader — peer CTOs, advisors, mentors, mentees, notable industry peers, plus conference speaking, public writing, podcast appearances, community engagement. Covers: maintaining contact records for external relationships (observable fields only, relationship context, last touchpoint); capturing touchpoints (coffees, calls, conference run-ins); tracking public commitments through their lifecycle (proposed → confirmed → preparing → delivered); logging delivered public artifacts (talks given, posts published); declaring overall public-presence posture (cadence, preferred venues, target audiences). Also activates on oblique phrasings like 'had coffee with Jane (peer CTO at AcmeCo),' 'submitting to QCon next year,' 'draft outline for my CNCF talk,' 'who should I reconnect with,' 'update my public-presence cadence,' 'log the post I published yesterday.' Does NOT activate on internal peer relationships (Managing Sideways); internal thought leadership like all-hands or eng-wide comms (Org Comms); upward or downward relationships inside the company (Managing Up / Managing Down); or technical positioning substance (Technical Strategy — this module handles *presence*, not *content*)."
requires: []
optional:
  - personal-os
  - attention-operations
---

# External Network & Thought Leadership

## Scope

External relationships and public presence as a senior engineering leader. Two related halves:

- **External network.** Peer CTOs, advisors, mentors, mentees, industry peers. People outside the user's current company who matter to their career, learning, hiring pipeline, or broader professional reputation. Light-touch relationship tracking — observable fields, last touchpoint, relationship context, nothing heavy.
- **Thought leadership / public presence.** Conference talks, public writing, podcast appearances, community engagement. Tracks commitments through their lifecycle and archives delivered artifacts.

Optional-by-role module. Meaningful for leaders investing in an external profile; skippable for leaders who don't.

## Out of scope

- **Internal peer relationships** — Managing Sideways.
- **Internal thought leadership** — Org Comms (audience is the internal org), Managing Down (audience is the user's reporting team).
- **Upward or downward internal relationships** — Managing Up, Managing Down.
- **Technical substance of what's being written or presented** — Technical Strategy. This module tracks *that you spoke at QCon on topic X*; the actual strategy content (what you'd say in the talk) draws from Technical Strategy state.
- **Recruiting-adjacent relationships** — Hiring. If an external contact becomes a candidate, they cross over into Hiring's domain; this module continues to track the relationship side.

## Frameworks

- [Mark Granovetter — *The Strength of Weak Ties*](https://www.jstor.org/stable/2776392) — weak network ties flow more novel information than strong ties.
  - *How this module applies it:* the relationship-tracking bar is low-touch by design. Don't over-engineer profiles for people you meet once a year — the value of a weak tie is that it exists at all and can be reactivated when needed. `last_touchpoint_date` is the most important frontmatter field for weak ties; a rough profile is fine. For closer relationships (mentors, advisors, recurring peers), deeper profile fields accrue naturally over time.

- [Dorie Clark — *Stand Out*](https://dorieclark.com/standout/) — thought-leadership posture, content cadence, platform choice.
  - *How this module applies it:* `public-posture` singleton captures what Clark calls the "platform" — what you're trying to be known for, where you show up, at what cadence. Commitments are tested against the posture: does this talk / post / appearance serve the stated public profile, or is it a distraction? Delivered artifacts accumulate as the body of work that proves the posture.

## Triggers

- "add [person] as an external contact"
- "log coffee with [person]" / "had a call with [person]"
- "submitting to [conference]" / "invited to speak at [venue]"
- "draft outline for my [conference/topic] talk"
- "update my public-posture" / "change my speaking cadence"
- "log the post I published" / "captured the talk I gave yesterday"
- "who should I reconnect with" / "show my network snapshot"
- "[peer CTO] changed jobs — update their record"
- Oblique: "I haven't been doing enough external stuff lately"
- Oblique: "[person] reached out — we haven't talked in a year"

## Activation flow

Each step writes a concrete artifact and appends its step number to `activation_completed` in `_module.md`.

### 1. Enumerate external network

**Ask:** "Walk me through the external contacts that matter to you. Typical categories: peer CTOs (same-stage, same-industry, or otherwise comparable), advisors (people you consult for career or technical perspective), mentors (people senior to you who invested in you), mentees (people you invest in), industry peers (visible in your space, useful to know), former colleagues who stayed valuable. For each: name, role/company, relationship type, short slug, last-touchpoint date if you remember, and a one-line relationship context (how you know them). This is a starter set — add more over time via `add-external-contact`."
**Writes:** one file per contact at `cto-os-data/modules/external-network/state/contacts/{person-slug}.md` with `type: external-contact`, `slug: <person-slug>`, `name`, `role`, `company`, `relationship_type`, `relationship_context`, `last_touchpoint_date`.
**Expects:** at least one contact file exists with the required fields. (Zero is valid — the module can activate with an empty network if the user is genuinely starting from scratch, though that's unusual for a senior leader.)

### 2. Declare public-presence posture

**Ask:** "What's your public-presence posture right now? Covers: (a) what you're trying to be known for — one or two themes, not a laundry list; (b) venues you show up at — conferences, publications, podcasts, your own blog; (c) target cadence — how often you aim to publish or speak; (d) who you're trying to reach — practitioners, other CTOs, the technical community broadly, hiring candidates. If you don't actively pursue a public presence today, we can capture that — 'explicitly low-profile, reactive only' is a legitimate posture."
**Writes:** `cto-os-data/modules/external-network/state/public-posture.md` with `type: public-posture`, `slug: current`, `themes`, `venues`, `cadence`, `target_audience`, `active: <bool>` (false if user is in low-profile mode).
**Expects:** frontmatter has `themes`, `venues`, and `cadence` set (or `active: false` with a brief rationale).

## Skills

### `add-external-contact`

**Purpose:** Add a new external contact post-activation.

**Triggers:**
- "add [person] as an external contact"
- "new peer CTO: [name] at [company]"
- "[person] invited me to be their mentor"

**Reads:** `cto-os-data/modules/external-network/state/contacts/` (slug collision check).

**Writes:** `cto-os-data/modules/external-network/state/contacts/{person-slug}.md`, append-new-file.

### `update-external-contact`

**Purpose:** Revise an external contact's record — role change, company change, relationship-type shift (mentee became peer), profile field updates.

**Triggers:**
- "update [person]'s record"
- "[person] changed jobs to [company]"
- "update [person]'s profile — they now focus on [X]"

**Reads:** `cto-os-data/modules/external-network/state/contacts/{person-slug}.md`.

**Writes:** `cto-os-data/modules/external-network/state/contacts/{person-slug}.md`, overwrite-with-history.

### `remove-external-contact`

**Purpose:** Handle a contact who's no longer relevant — retired from the field, lost touch permanently, or the relationship ended. File preserved; marked inactive.

**Triggers:**
- "remove [person]"
- "[person] retired"
- "lost touch with [person] — mark inactive"

**Reads:** `cto-os-data/modules/external-network/state/contacts/{person-slug}.md`.

**Writes:** `cto-os-data/modules/external-network/state/contacts/{person-slug}.md` — sets `active: false`, `departed_date`, reason in body.

### `log-external-touchpoint`

**Purpose:** Capture a meeting, call, coffee, conference run-in, or substantial email exchange with an external contact. Updates the contact's `last_touchpoint_date`.

**Triggers:**
- "log coffee with [person]"
- "had a call with [person]"
- "ran into [person] at [conference]"
- "[person] and I caught up on [topic]"

**Reads:**
- `cto-os-data/modules/external-network/state/contacts/{person-slug}.md`
- `cto-os-data/modules/external-network/state/touchpoints/{person-slug}/` (recent touchpoints for continuity)

**Writes:** `cto-os-data/modules/external-network/state/touchpoints/{person-slug}/{YYYY-MM-DD}.md`, append-new-file. Also updates the contact's `last_touchpoint_date` in frontmatter.

### `log-public-commitment`

**Purpose:** Capture a public-presence commitment — accepted talk, scheduled podcast, article due, invited keynote, community engagement.

**Triggers:**
- "submitting to [conference]"
- "accepted the [podcast] invitation"
- "article due to [publication] on [date]"
- "keynote at [event]"

**Reads:**
- `cto-os-data/modules/external-network/state/public-posture.md` (is this aligned with the posture?)
- `cto-os-data/modules/external-network/state/commitments/` (active commitments, for load check)

**Writes:** `cto-os-data/modules/external-network/state/commitments/{YYYY-MM-DD}-{commitment-slug}.md`, append-new-file with `status: confirmed` (or `proposed` if still pending acceptance).

### `update-public-commitment`

**Purpose:** Transition a commitment through its lifecycle — proposed → confirmed → preparing → delivered (or cancelled, postponed, withdrawn).

**Triggers:**
- "update [commitment] — accepted"
- "start prepping for [talk]"
- "[commitment] was cancelled"
- "mark [commitment] delivered"

**Reads:** `cto-os-data/modules/external-network/state/commitments/{commitment-slug}.md`.

**Writes:** `cto-os-data/modules/external-network/state/commitments/{commitment-slug}.md`, overwrite-with-history. When transitioning to `delivered`, prompts the user to also run `log-delivered-artifact`.

### `log-delivered-artifact`

**Purpose:** Archive a delivered public output — talk given (title + slides reference + video link if available), post published (URL + summary), podcast appearance (link + topics). Builds the body-of-work archive.

**Triggers:**
- "log the post I published yesterday"
- "captured the talk I gave at [conference]"
- "podcast appearance is live — log it"

**Reads:**
- `cto-os-data/modules/external-network/state/commitments/` (if this delivered-artifact fulfills a tracked commitment)
- `cto-os-data/modules/external-network/state/public-posture.md` (theme alignment)

**Writes:** `cto-os-data/modules/external-network/state/artifacts/{YYYY-MM-DD}-{artifact-slug}.md`, append-new-file.

### `update-public-posture`

**Purpose:** Revise declared public-presence posture — new theme, changed venues, adjusted cadence, shift in/out of active mode.

**Triggers:**
- "update my public posture"
- "change my speaking cadence to [frequency]"
- "I'm going low-profile for 6 months"
- "add [theme] to my public themes"

**Reads:** `cto-os-data/modules/external-network/state/public-posture.md`.

**Writes:** `cto-os-data/modules/external-network/state/public-posture.md`, overwrite-with-history.

### `show-network-snapshot`

**Purpose:** Assemble a read-time rollup — active contacts grouped by relationship type, last-touchpoint recency (who haven't you talked to in > 6 months?), upcoming public commitments, delivered-artifact count year-to-date.

**Triggers:**
- "show network snapshot"
- "who should I reconnect with"
- "network rollup"
- "public-presence rollup"

**Reads:**
- `scan(type=["external-contact"], where={"active": true}, fields=["slug", "name", "role", "company", "relationship_type", "last_touchpoint_date"])`
- `scan(type=["public-commitment"], where={"status": "confirmed"}, fields=["slug", "commitment_type", "scheduled_date"])`
- `scan(type=["public-artifact"], fields=["slug", "artifact_type", "delivered_date"])`

**Writes:** —

## Persistence

- **`cto-os-data/modules/external-network/state/contacts/{person-slug}.md`** — one file per contact, overwrite-with-history. Frontmatter: `type: external-contact, slug: <person-slug>, updated: <date>, active: <bool>, name: <string>, role: <string>, company: <string>, relationship_type: <peer-cto|advisor|mentor|mentee|industry-peer|former-colleague|other>, relationship_context: <string>, last_touchpoint_date: <date, optional>, departed_date: <date, optional>, communication_preferences: <string, optional>, mutual_interests: <list, optional>, notes: <string, optional>`. Body: narrative + `## History`.
- **`cto-os-data/modules/external-network/state/touchpoints/{person-slug}/{YYYY-MM-DD}.md`** — append-new-file per touchpoint. Frontmatter: `type: external-touchpoint, slug: <person-slug>-<YYYY-MM-DD>, updated: <date>, person: <person-slug>, touchpoint_type: <coffee|call|video|email|conference|other>, duration_minutes: <int, optional>`. Body: what was discussed, anything worth following up on.
- **`cto-os-data/modules/external-network/state/commitments/{YYYY-MM-DD}-{commitment-slug}.md`** — one file per commitment, overwrite-with-history. Frontmatter: `type: public-commitment, slug: <YYYY-MM-DD>-<commitment-slug>, updated: <date>, commitment_type: <talk|article|podcast|keynote|panel|other>, venue: <string>, title: <string>, scheduled_date: <date>, status: <proposed|confirmed|preparing|delivered|cancelled|postponed|withdrawn>, theme: <string, optional>`. Body: brief + `## History` of status transitions.
- **`cto-os-data/modules/external-network/state/artifacts/{YYYY-MM-DD}-{artifact-slug}.md`** — append-new-file per delivered artifact. Frontmatter: `type: public-artifact, slug: <YYYY-MM-DD>-<artifact-slug>, updated: <date>, artifact_type: <talk|article|podcast|keynote|panel|other>, venue: <string>, title: <string>, delivered_date: <date>, link: <string, optional>, fulfills_commitment: <commitment-slug, optional>`. Body: summary + notes on reception / follow-ups / what would change next time.
- **`cto-os-data/modules/external-network/state/public-posture.md`** — singleton (`slug: current`), overwrite-with-history. Frontmatter: `type: public-posture, slug: current, updated: <date>, active: <bool>, themes: <list>, venues: <list>, cadence: <string>, target_audience: <list>`. Body: rationale + `## History`.

**Overrides to the cross-cutting save rule** ([Persistence model](../../docs/ARCHITECTURE.md#persistence-model)): none — inherits the default. Touchpoints save without blocking when the user narrates a just-happened interaction. Contact / posture updates confirm when inferences are indirect.

**Sensitivity:** standard default at module level. Individual contact records touching sensitive content (private candid assessment of a visible peer, confidential info shared by an advisor) can be flagged `sensitivity: high` per-file.

## State location

`cto-os-data/modules/external-network/state/`
