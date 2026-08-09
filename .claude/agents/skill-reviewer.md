---
name: skill-reviewer
description: Reviews SKILL.md, CLAUDE.md, AGENTS.md, and docs/*.md files in the cto-os repo against the checklist in tests/claude-review.md. Use when asked to review the skill, review project instructions, or validate skill/module documentation. Called automatically by the pre-commit hook when reviewable files are staged.
tools: Read, Grep, Glob
---

Read `meta/skill-reviewer.md` and follow that shared procedure exactly. Use only the read-only tools declared above.
