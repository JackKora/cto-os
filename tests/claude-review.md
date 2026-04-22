# Skill review checklist

Applied by the `skill-reviewer` subagent (`.claude/agents/skill-reviewer.md`) and the pre-commit hook (`hooks/pre-commit`).

Each item: **What** to check, **How** to check, **Fail when**.

---

## 1. No false-present-tense claims

**What:** `SKILL.md`, `CLAUDE.md`, and `docs/*.md` files do not describe features as "runs," "is configured," "gates," etc. when the referenced code, script, workflow, or file doesn't exist in the repo.

**How:** Grep the file for claims of the form "X runs Y," "Y is configured," "Z executes," "CI gates," "the hook runs." For each, verify the referenced artifact exists.

**Fail when:** A claim references a file, script, command, workflow, or CI action that does not exist in the repo. Aspirational intent is fine if clearly flagged ("Target:" / "Not yet implemented:" / "TODO").

---

## 2. Cross-reference accuracy

**What:** Every in-repo link or path mention resolves to an actual file. Applies to markdown links (`[x](path)`), inline code paths (`` `scripts/scan.py` ``), and layout tree entries.

**How:** Extract every relative-path reference. For each, check the target exists via `Read` or `Glob`.

**Fail when:** Any reference points to a non-existent path. External links (`http://`, `https://`) are out of scope.

**Exempt:**

- References sitting under a heading whose text contains "planned," "not yet implemented," "forward-looking," or "TODO" (case-insensitive). These are placeholders for files that will land later; don't fail on them. The exemption applies until the nearest following `---` divider, a heading of equal or higher rank, or end of file.
- Paths starting with `cto-os-data/` — these are data-repo paths described in prose, not files that should resolve inside the skill repo. See [docs/MCP_TOOLS.md → Path handling](../docs/MCP_TOOLS.md#path-handling-applies-to-every-path-taking-tool).

---

## 3. Module layout invariants

**What:** Every directory under `modules/` contains both `SKILL.md` and `README.md`.

**How:** Glob `modules/*/`. For each, check both files exist.

**Fail when:** A module directory is missing either file. `N/A` if `modules/` is empty.

---

## 4. No user state in the skill repo

**What:** No user-specific values in `SKILL.md`, `CLAUDE.md`, or `docs/*.md` files. User-specific means: real people's names that aren't framed as placeholders, specific company names, concrete dated events tied to the user's history, stated personal goals.

**How:** Grep for proper names and real-looking dates. Distinguish placeholders (generic, e.g., `Jane`, `platform-team`, `Acme` in obvious example context) from user state (`Mike Johnson (CEO of CompanyName)`, `my Q3 goal is...`).

**Fail when:** User state is embedded outside a labeled example or placeholder.

---

## 5. Trigger phrase overlap across modules

**What:** Two sibling modules (both direct children of `modules/`) don't claim heavily overlapping trigger phrases in their `SKILL.md` frontmatter `description`.

**How:** Read each module `SKILL.md` frontmatter `description`. Pairwise-compare — would a single user phrasing plausibly match both? (Same verbs + same nouns for different capabilities = overlap.)

**Fail when:** Two sibling modules would plausibly both match the same user request. `N/A` if fewer than 2 modules exist.

---

## 6. Schema references resolve

**What:** Any `SKILL.md` that references a frontmatter field (e.g., `sensitivity`, `schema_version`, `active`) points to a field defined in `meta/schema.md`.

**How:** Read `meta/schema.md`. For each module `SKILL.md`, extract field mentions. Check each against the schema.

**Fail when:** A `SKILL.md` references a field not in `meta/schema.md`. `N/A` if `meta/schema.md` is empty (no schema defined yet means nothing to contradict).

---

## 7. README ↔ SKILL.md consistency

**What:** A module's `README.md` does not contradict its `SKILL.md` on scope, dependencies, or frameworks.

**How:** For each module, read both. Compare declared scope, required/optional dependency lists, and framework references.

**Fail when:** The two files disagree on a factual matter. Cite the specific contradiction.

---

## 8. Root CLAUDE.md layout matches reality

**What:** The "Layout" tree in the root `CLAUDE.md` lists only directories that exist in the repo.

**How:** Parse the tree in `CLAUDE.md`. For each named directory or file, check it exists.

**Fail when:** An entry is listed but missing from disk. (An entry exists but isn't listed is a warning; flag it in the report but don't fail.)

---

---

## 9. Every module SKILL.md declares Persistence

**What:** Every per-module `SKILL.md` (files at `modules/{slug}/SKILL.md`) contains a `Persistence` section (any heading level) that covers paths written, semantics (append / overwrite / upsert), path templates, and required frontmatter.

**How:** For each module `SKILL.md`, grep for a heading line matching `Persistence`. If found, read the section and check all four sub-points are present.

**Fail when:** A module `SKILL.md` exists but is missing the Persistence section, or the section is present but missing any of the four sub-points. `N/A` if there are no module `SKILL.md` files yet. Does not apply to root `SKILL.md`.

---

## 11. Per-module SKILL.md frontmatter

**What:** Every per-module `SKILL.md` has valid frontmatter with `name`, `description`, `requires`, and `optional` fields per `docs/SKILL_REPO.md` → "Per-module SKILL.md format."

**How:** For each module `SKILL.md`, parse YAML frontmatter. Check: `name` matches the directory slug exactly; `description` is non-empty; `requires` and `optional` are present and are lists (may be empty); list entries are plain slugs (no link syntax, no descriptions).

**Fail when:** Any required field is missing, `name` doesn't match the directory, `description` is empty, or `requires` / `optional` contain non-slug entries. `N/A` if no module SKILL.md files exist.

---

## 12. Per-module SKILL.md required sections

**What:** Every per-module `SKILL.md` contains the required body sections in the required order: `Scope`, `Out of scope`, `Frameworks`, `Triggers`, `Activation flow`, `Skills`, `Persistence`, `State location`.

**How:** For each module `SKILL.md`, extract all `## ` headings. Verify all eight required headings appear and in the specified order. Additional sections are allowed after `State location`.

**Fail when:** A required heading is missing, or the required headings appear out of order. `N/A` if no module SKILL.md files exist.

---

## 13. Activation flow steps have required fields

**What:** Each numbered step under `## Activation flow` in a per-module `SKILL.md` contains `Ask`, `Writes`, and `Expects` fields per the format in `docs/SKILL_REPO.md` → "Activation flow format."

**How:** For each module, parse the `## Activation flow` section. For each numbered step (`### N. ...` heading), check that `**Ask:**`, `**Writes:**`, and `**Expects:**` lines are present. `**Skip if:**` is optional.

**Fail when:** A step is missing any of Ask / Writes / Expects. `N/A` if no module SKILL.md files or no activation steps exist.

---

## 14. Skills ↔ Persistence ↔ Activation consistency (bidirectional)

**What:** The set of write paths declared in a module's `## Skills` section *plus* its `## Activation flow` section must equal the set of paths declared in `## Persistence`.

**How:** For each module `SKILL.md`:

1. Collect all paths from `**Writes:**` lines under `## Skills` (ignore entries marked `—`).
2. Collect all paths from `**Writes:**` lines under `## Activation flow`.
3. Collect all paths declared in `## Persistence`.
4. Compare the sets:
   - Every skill/activation write path must appear in Persistence (otherwise a write is happening without declared semantics).
   - Every Persistence path must appear in at least one skill or activation write (otherwise Persistence declares a dead path — documentation drift).

Paths with templated segments (e.g., `{YYYY-MM-DD}`, `{horizon}`) are compared structurally; an exact substitution match is not required.

**Fail when:** Either direction has a mismatch. Cite the offending path and which side it's missing from. `N/A` if no module SKILL.md files exist.

---

## 10. README inventory matches reality

**What:** If `README.md` exists and is non-empty, its module index and scripts inventory (if present) match what's in the repo on disk.

**How:** Read `README.md`. Extract listed modules from its module index section (headings or a bulleted list under a "Modules" heading). Extract listed scripts from its scripts section (bulleted list under "Scripts" or similar). Glob `modules/*/` and `scripts/*.py`. Compare.

**Fail when:** A module or script exists on disk but isn't in `README.md`, or is listed in `README.md` but doesn't exist on disk. `N/A` if `README.md` is empty or missing. Files explicitly marked as placeholders / not-yet-implemented in `README.md` count as "listed" — the point is presence, not implementation status.

---

## Notes

- Run every item top-to-bottom. Don't skip.
- `N/A` is not `PASS`. Use `N/A` when the item has nothing to evaluate.
- End the entire response with exactly one of: `REVIEW: PASS` or `REVIEW: FAIL`.
