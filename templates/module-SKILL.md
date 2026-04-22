---
name: {{MODULE_SLUG}}
description: "{{Activation trigger paragraph. Specific enough to avoid false matches on unrelated topics, broad enough to catch oblique phrasings users actually say. See docs/SKILL_REPO.md → Trigger specificity.}}"
requires: []
optional: []
---

# {{Module Name}}

## Scope

{{One paragraph. What this module does. Tight — a reader should understand the domain in 30 seconds.}}

## Out of scope

{{One paragraph. What this module doesn't do, and which sibling module owns it instead. Force clean boundaries — every overlap gets named.}}

## Frameworks

For each framework, decide: is it well-known (OKRs, DORA, SPACE, Radical Candor, Reinertsen's Flow, Andy Grove, Working Backwards, 4Ls retro, etc.)? If yes, name + link + application note below is sufficient. If **not** well-known, also create `frameworks/{slug}.md` at the skill repo root with a canonical summary and reference it in the application note. See [docs/SKILL_REPO.md → Per-module SKILL.md format](../../docs/SKILL_REPO.md#per-module-skillmd-format) for the full guidance.

- [{{Framework name}}]({{canonical link — book, paper, or authoritative site}}) — {{one sentence on what the module uses it for}}.
  - *How this module applies it:* {{2–5 lines — which flavor / variant, what's skipped, how it maps to state. Removes interpretation drift at runtime.}}

- [{{Framework name}}]({{canonical link}}) — {{one sentence}}.
  - *How this module applies it:* {{...}}

## Triggers

Example user phrasings that should activate this module. Used by the skill router and by the skill-reviewer's trigger-overlap check against sibling modules.

- "{{direct phrasing}}"
- "{{topical phrasing}}"
- "{{oblique phrasing — how the user actually talks about this when they're not using the module's formal name}}"

## Activation flow

Running this flow populates baseline state. Each step writes one concrete artifact, so resumption is implicit: if the target file exists and matches **Expects**, the step is done.

### 1. {{Step title}}

**Ask:** "{{Verbatim question Claude asks the user.}}"
**Writes:** `cto-os-data/modules/{{MODULE_SLUG}}/state/{{path}}.md` with `type: {{type-slug}}` frontmatter.
**Expects:** {{one sentence describing what a complete output looks like — e.g., "frontmatter `altitude` is one of director / vp / svp / c-level; body is empty"}}.

### 2. {{Next step title}}

**Ask:** "{{question}}"
**Writes:** `cto-os-data/modules/{{MODULE_SLUG}}/state/{{path}}.md`.
**Expects:** {{completeness criterion}}.
**Skip if:** {{optional — condition under which this step can be skipped, e.g., "required dependency `personal-os` already supplies `show-up`"}}.

## Skills

The named runtime tasks this module performs once activated.

### `{{skill-slug}}`

**Purpose:** {{one sentence — what this skill does}}.

**Triggers:**
- "{{user phrasing}}"
- "{{user phrasing}}"

**Reads:**
- `{{path or scan query}}`
- `{{path or scan query}}`

**Writes:** `cto-os-data/modules/{{MODULE_SLUG}}/state/{{path}}.md`, {{append | overwrite | upsert}}. (Use `—` if this skill doesn't write.)

### `{{next-skill-slug}}`

**Purpose:** {{...}}

**Triggers:**
- "{{...}}"

**Reads:**
- `{{...}}`

**Writes:** —

## Persistence

Paths this module writes to and their semantics. Every `**Writes:**` path in the Skills section above must appear here.

Design-time prompt: *"What's the thing that changes on its own?"* Make one file per independently-changing unit. See [docs/DATA_REPO.md → File granularity](../../docs/DATA_REPO.md#file-granularity--one-file-per-independently-changing-unit).

- **`cto-os-data/modules/{{MODULE_SLUG}}/state/{{path-template}}.md`** — append. Frontmatter: `type: {{type}}, slug: {{slug-template}}, updated: <date>`. {{One sentence describing what goes in the body.}}
- **`cto-os-data/modules/{{MODULE_SLUG}}/state/{{another-path}}.md`** — upsert frontmatter fields; body unchanged. Frontmatter: `{{required fields}}`. {{When and why an upsert is triggered.}}
- **`cto-os-data/modules/{{MODULE_SLUG}}/state/{{overwrite-path}}.md`** — overwrite, with prior versions preserved in the body as reverse-chronological snapshots. Frontmatter: `{{required fields}}`. {{When a new version is written.}}

**Overrides to the cross-cutting save rule** ([Persistence model](../../docs/ARCHITECTURE.md#persistence-model)): {{Describe any module-specific exceptions, or write "none — inherits the default." Examples of overrides: "always ask before writing anything under `state/reviews/` regardless of default behavior," or "silent writes are permitted for `state/journal.md` since the user is dictating."}}

## State location

`cto-os-data/modules/{{MODULE_SLUG}}/state/`
