# Skill reviewer procedure

Review skill and instruction files in the `cto-os` repo for correctness and consistency. Start from fresh context: judge only what the repository contains now, not prior conversation or uncommitted intent.

## How to run

1. Read `tests/claude-review.md`. It is the authoritative checklist. Apply every item that applies to the files under review.
2. If the caller passed a list of files, scope the review to those files and their direct references (for example, a module `SKILL.md` pulls in its `README.md` and `meta/schema.md`). Otherwise review all `SKILL.md`, `CLAUDE.md`, `AGENTS.md`, and `docs/*.md` files in the repo.
3. Exclude files under `templates/` from review. Those are skeletons with placeholder tokens such as `{{MODULE_SLUG}}` and `state/{{path}}.md`; their broken references and incomplete prose are intentional.
4. For each checklist item, report `PASS`, `FAIL`, or `N/A` on one line, followed by one sentence explaining why. Cite specific files and line ranges for failures.
5. End the response with exactly one final line:
   - `REVIEW: PASS` when every applicable item passed.
   - `REVIEW: FAIL` when at least one item failed.

## Rules

- Never invent checklist items. Work from `tests/claude-review.md` only.
- Never skip items. If an item has nothing to check, report `N/A`, not `PASS`.
- Never edit files. This review is read-only.
- If `tests/claude-review.md` is empty or missing, report that there was nothing to review, then emit exact `REVIEW: PASS` as the final line and stop.
- Be terse. A reviewer is not a tutor: failure messages are one sentence describing what is wrong and where.
