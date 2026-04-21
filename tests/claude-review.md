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

**Fail when:** Any reference points to a non-existent path. External links (http://, https://) are out of scope.

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

## Notes

- Run every item top-to-bottom. Don't skip.
- `N/A` is not `PASS`. Use `N/A` when the item has nothing to evaluate.
- End the entire response with exactly one of: `REVIEW: PASS` or `REVIEW: FAIL`.
